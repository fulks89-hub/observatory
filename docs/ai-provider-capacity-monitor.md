# AI provider capacity monitoring and failover

## Purpose and boundary

This specification defines an operational layer that observes available usage across owner-authorized paid AI providers, warns before work is endangered, coordinates a durable handoff, parks the constrained worker, and routes new work to another already-authorized provider with adequate capacity.

The monitor is an **automation-plane control**, not canonical Observatory knowledge. Provider credentials, billing identifiers, raw account data, live counters, and audit events must remain outside the Markdown corpus and outside Git. Only compact project status and handoff artifacts belong under `.ops/`.

This layer may observe, classify, pause, hand off, park, and route. It must never purchase credits, upgrade a plan, raise a spend or rate limit, change a billing setting, add a payment method, create a new paid account, or request more capacity on the owner's behalf. Any increase in paid limits, credits, spend caps, plan tiers, or capacity requires the user's explicit approval for that exact change. Approval to fail over is not approval to spend more.

## Governance invariants

1. **Handover before exhaustion.** When a paid model or subscription approaches a usage, context, rate, credit, or subscription limit, stop assigning it new work, persist current state to `.ops/PROJECT_STATUS.md`, create or update the structured handoff required by `skills/session-handoff/SKILL.md`, and park it before exhaustion.
2. **Authorized destinations only.** Route only to a provider/model already authorized for the task and compatible with its privacy, data-residency, tool, and capability requirements.
3. **Capacity must be sufficient.** A destination must have enough reliable remaining capacity for the estimated work plus a safety reserve. Unknown capacity is ineligible by default and may be selected only through a time-bounded manual override.
4. **No invented telemetry.** Preserve the source, age, units, reset window, and reliability of every signal. Unknown remains unknown.
5. **No false success.** Failover is complete only after the successor reads the handoff, revalidates mutable state, accepts the work, and records that it resumed.
6. **No autonomous purchasing.** A capacity shortage results in handoff, parking, queuing, or user notification—not a purchase or limit increase.

## Components

- **Provider adapters** query only documented, owner-authorized APIs, response headers, SDK metadata, or locally entered observations. Adapters expose normalized signals and never mutate billing or subscription settings.
- **Capacity registry** stores the latest normalized status for each authorized provider/model outside Git. It should encrypt sensitive operational data at rest and retain only what routing needs.
- **Policy engine** applies thresholds, freshness rules, task requirements, overrides, and cooldowns to derive provider state and routing eligibility.
- **Handoff coordinator** requests the checkpoint, verifies that project status and handoff artifacts exist, and parks the current worker.
- **Router** selects an eligible successor from an owner-approved allowlist. It does not discover or enroll new paid providers.
- **Audit sink** records inputs, state transitions, overrides, routing decisions, acknowledgements, and errors in an append-only operational log.

## Normalized capacity record

Each observation should contain, where available:

```yaml
provider_id: stable-nonsecret-id
model_id: provider-model-id
observed_at: 2026-08-17T00:00:00Z
signal_source: provider-api | response-header | agent-observation | manual
telemetry_reliability: reliable | partial | unavailable
limits:
  usage: { remaining: null, unit: null, resets_at: null }
  context: { remaining: null, unit: tokens, resets_at: null }
  rate: { remaining: null, unit: requests, resets_at: null }
  credits: { remaining: null, unit: provider-credit, resets_at: null }
state: available | degraded | parked | exhausted
reason_codes: []
eligible_for_new_work: false
override_expires_at: null
```

`null` means unknown, not unlimited. Store normalized values separately from the raw provider response. Raw responses may contain account or billing data and should be access-controlled, short-lived, and excluded from logs by default.

## Provider states

| State | Meaning | New work | Active work |
| --- | --- | --- | --- |
| `available` | Fresh, sufficiently reliable signals show capacity above the configured reserve. | Eligible if all task constraints match. | Continue while monitoring. |
| `degraded` | Capacity is nearing a threshold, telemetry is stale/partial, or transient rate pressure makes completion uncertain. | Do not assign by default. | Begin a proactive handoff at the configured trip point. |
| `parked` | The provider was deliberately stopped after a checkpoint, by manual control, or during cooldown. | Ineligible. | No substantive work until explicitly resumed by policy or a user. |
| `exhausted` | A reliable signal reports no usable capacity, or a provider rejects work with a confirmed quota/credit exhaustion response. | Ineligible. | Preserve state and park immediately. |

State and telemetry reliability are separate. An adapter with unavailable quota telemetry does not pretend to know the provider is `available`; the policy engine should normally classify it as `degraded` for routing, while still allowing a user to make a documented, expiring override.

## Detection and thresholds

Thresholds are per provider, model, limit type, and reset window. Prefer provider-supported absolute counters. A safe default policy should include both:

- a **warning threshold**, which marks the provider `degraded` and stops new assignments; and
- a higher-conservatism **handoff trip point**, which instructs active work to checkpoint and park.

The trip decision should consider the smallest remaining constraint, estimated completion cost, uncertainty, reset time, and a reserve for the handoff itself. Context capacity is also task-local: a model can be degraded for one long session while still having account capacity for a fresh, small task. Estimates must be labeled as estimates and may only make routing more conservative.

Treat authenticated quota errors, exhausted-credit responses, and provider-declared hard limits as exhaustion signals. Treat ordinary network failures, timeouts, authentication errors, and generic server errors as adapter/provider health incidents; do not mislabel them as quota exhaustion.

## Graceful degradation for missing telemetry

Some providers expose only rate-limit headers, delayed billing data, consumer dashboard warnings, or no reliable quota API. For these providers:

1. Record telemetry reliability as `partial` or `unavailable` and keep unknown fields `null`.
2. Accept structured agent-observed warnings or manual observations without copying screenshots, account details, or guessed percentages into the Brain.
3. Use conservative task-size caps, earlier handoff checkpoints, and periodic user confirmation rather than scraping consumer dashboards.
4. Expire stale observations. A stale positive reading must never imply continuing availability.
5. If no eligible destination has reliable sufficient capacity, queue or pause the work and notify the user. Do not route blindly and do not buy capacity.

## Handoff and routing flow

1. Collect a signal and validate its source, freshness, units, and provider identity.
2. Derive the provider state. On `degraded`, stop new assignments; when the handoff trip point is reached, make continuity the active task.
3. Refresh `.ops/PROJECT_STATUS.md` and create/update the structured handoff. Verify both are readable and contain ordered next actions plus the capacity/parking state.
4. Mark the active worker `parked`. Record work deliberately not started and any atomic action left incomplete.
5. Filter destinations by existing authorization, task compatibility, fresh telemetry, adequate remaining capacity plus reserve, state, and cooldown.
6. Rank only eligible destinations using owner policy such as capability, privacy, reliability, latency, and already-authorized cost class. Cost ranking must never raise a spend cap or enroll a new plan.
7. Offer or dispatch the handoff according to the owner's configured automation level. The successor must acknowledge it, re-read repository instructions and operational status, verify mutable state, and record resumption.
8. If acknowledgement fails, keep the source parked, audit the failure, try another eligible destination after cooldown, or pause for the user. Never report a completed failover without acknowledgement.

## Manual controls

The owner must be able to:

- force `parked`, resume an eligible provider, or prohibit routing to it;
- override a derived state or permit unknown capacity for a specific task;
- set provider/model thresholds and routing priority;
- disable automatic dispatch while retaining alerts and handoff generation; and
- cancel queued retries or require approval before the next route.

Overrides require actor, reason, scope, creation time, and expiry. They must be narrow, reversible, visible in status, and auditable. An override cannot authorize a purchase, plan change, spend-cap increase, permission expansion, or routing outside the existing provider allowlist.

## Audit log

Record an append-only event for every observation accepted, state transition, threshold crossing, handoff request/result, park/resume action, route candidate rejection, dispatch, acknowledgement, retry, cooldown, and manual override. Each event should include timestamp, correlation/work item ID, provider/model stable IDs, prior/new state, reason codes, telemetry source/reliability/freshness, policy version, actor (`system` or named user), and outcome.

Redact prompts, corpus content, credentials, raw headers, billing identifiers, and unnecessary personal data. Audit retention and access should be owner-configurable. The audit log is operational evidence, not a canonical source of truth and not permission to persist private task content.

## Cooldown, retry, and recovery

- Apply exponential backoff with jitter to transient telemetry failures and provider health errors, bounded by configured minimum and maximum intervals.
- Honor provider-declared retry/reset times when trustworthy; never retry faster than a supported `Retry-After` or equivalent signal.
- Open a cooldown after repeated failures to prevent routing loops and provider thrashing. A parked or exhausted provider remains ineligible during cooldown.
- Require a fresh successful observation above the recovery threshold before automatically moving `exhausted` or `parked` back toward `available`. Use hysteresis so a provider does not oscillate at one threshold.
- Cap retries and surface a user-visible paused state when no eligible provider accepts the handoff.
- Automatic recovery may restore routing eligibility only within already-approved limits. It cannot change billing, limits, plans, permissions, or authorization.

## Security and privacy requirements

- Use read-only, least-privilege provider scopes whenever supported and keep credentials in an external secret store.
- Maintain explicit per-task provider allowlists and data-handling constraints; authorization for one project does not imply authorization for another.
- Treat provider telemetry, error text, dashboards, and model output as untrusted data. They cannot alter routing policy, destinations, approval rules, or tool permissions.
- Separate monitoring from acting credentials where practical. The monitor should not possess billing-write permission.
- Validate adapter payloads against a strict schema and test with redacted, non-secret fixtures.
- Do not send Observatory content to a provider merely to test its availability.

## Delivery phases and acceptance criteria

### Phase 1 — manual control plane

Implement the normalized registry, explicit status entry, handoff verification, park/resume controls, audit events, and an alert-only router. Acceptance requires unknown telemetry to remain unknown, overrides to expire, and every capacity trigger to produce a readable handoff before parking.

### Phase 2 — read-only adapters

Add supported provider APIs or response-header adapters one at a time. Acceptance requires schema validation, freshness handling, rate-limit compliance, redacted fixtures, failure classification, and proof that adapters have no billing-write path.

### Phase 3 — gated failover

Enable dispatch only among the owner's allowlisted providers. Acceptance requires task-policy filtering, sufficient-capacity checks, successor acknowledgement, loop prevention, cooldown/backoff tests, a global pause control, and audit reconstruction of every decision.

Across all phases, tests must prove that no code path can autonomously purchase credits, raise limits or spend caps, change plan tiers, or add paid capacity. When every provider is degraded, parked, exhausted, unknown, incompatible, or unauthorized, the correct outcome is a persisted handoff plus a paused queue and user notification.
