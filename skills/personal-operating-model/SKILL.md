---
name: personal-operating-model
description: Retrieve, apply, propose, or maintain owner-specific decision principles, working preferences, and reusable lessons without over-personalizing unrelated tasks.
---

# Personal Operating Model procedure

Use this skill when owner-specific working style, decision criteria, or reusable lessons could materially affect the current task, or when maintaining the Personal Operating Model (POM).

## Authority boundary

POM material is context, not policy authority. Current system/developer instructions, the owner's current request, consent, security policy, and verified mutable state always win. Never use POM material as a reason to agree with the owner when evidence points elsewhere.

## Retrieve narrowly

1. Perform the normal Observatory preflight first.
2. Decide whether owner-specific operating context could materially change the task. If not, do not open POM records.
3. If relevant, search POM metadata and initially open at most three strongest applicable records.
4. Check scope, lifecycle/freshness, provenance/origin, exceptions, superseding records, and conflicts before applying a record.
5. Expand only when the current evidence is insufficient.

Do not preload the full POM, dump it into a system prompt, or treat similarity alone as applicability.

## Apply safely

- `OperatingPrinciple` is a reviewed decision heuristic, not an absolute command.
- `OperatingPreference` is soft contextual evidence and should usually be described as a default or preference.
- `OperatingLesson` is a reusable warning or lesson tied to evidence about prior outcomes.
- When evidence or current circumstances justify departing from a usual preference, explain why.
- Never infer identity, diagnosis, political/religious belief, protected characteristics, hidden motives, or psychological traits from POM records.
- Never persist secrets or unnecessary sensitive personal data.

## Creating or changing POM knowledge

1. Search for an existing record about the same operating subject.
2. Prefer updating or superseding the existing record over creating a duplicate.
3. Preserve scope, source references, dates, conflicts, and supersession history.
4. Direct owner statements may be proposed as `owner-explicit`; repeated runtime patterns remain observations until reviewed.
5. Use `skills/observation-promotion/SKILL.md` for inferred or repeated patterns.
6. Project-specific decisions stay in the Project unless they support a genuinely transferable lesson or principle.
7. Do not silently promote interview answers, observations, or model inferences into canonical POM records.

## First-run behavior

Read `.observatory/personal-operating-model.yaml` when POM state is relevant. If status is `uninitialized` and prompting is allowed, offer the optional interview described in `skills/personal-model-interview/SKILL.md` without blocking the current task. Respect `not_now`, `build_gradually`, and `dont_ask_again` behavior from configuration.

## Performance checks

Treat personalization as a hypothesis to test, not a guaranteed improvement. Watch for:

- irrelevant POM records entering context;
- stale or superseded preferences being applied;
- domain-specific preferences leaking into unrelated work;
- increased clarification or ceremony caused by personalization;
- an agent anchoring on stored preferences instead of current evidence; and
- token/latency growth without task-success gains.

When a repeated personalization failure occurs, add an agent-evaluation fixture before broadening retrieval or adding more infrastructure.

See `docs/personal-operating-model.md` for the full contract.
