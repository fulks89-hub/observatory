# Personal Operating Model

The **Personal Operating Model (POM)** is Observatory's optional, owner-controlled layer for durable knowledge about **how to work effectively with the owner**. It complements project memory and topic knowledge; it is not a personality profile, biography, or instruction to imitate or agree with the owner.

## Goal

A new authorized agent should be able to retrieve the small amount of owner-specific operating context that materially improves the current task: decision principles, working preferences, and reusable lessons. The agent should not need the whole model in context.

> The Personal Operating Model exists globally, but is retrieved locally.

Current system/developer instructions, the owner's current request, consent, security policy, and verified mutable state always outrank POM material.

## Canonical types

POM records use open OKF types and live under `personal-operating-model/`:

- `OperatingPrinciple` — a transferable decision principle supported by explicit owner direction or reviewed evidence.
- `OperatingPreference` — a contextual working preference, not a command. Preferences should carry scope and exceptions when relevant.
- `OperatingLesson` — a reusable lesson from outcomes, repeated failures, corrections, or reviewed experience.

Keep each record small and independently retrievable. Do not create one giant always-loaded profile.

Recommended metadata when useful:

```yaml
type: OperatingPreference
title: Prefer ranked recommendations
scope:
  domains: [planning, purchasing]
origin: owner-explicit
strength: default
status: stable
lifecycle:
  valid_from: 2026-08-27
supersedes: []
conflicts_with: []
```

`origin` is a local convention, not a trust score. Useful values are `owner-explicit`, `reviewed-observation`, and `owner-correction`. Inferred patterns remain staged until the owner reviews them.

## Retrieval contract

Do not inject the entire POM into ordinary prompts. During task preflight, ask whether owner-specific operating context could materially affect the task. If no, load zero POM records. If yes, retrieve metadata first and initially open at most three applicable POM records unless evidence is insufficient.

Before applying a record, check:

1. task/domain relevance;
2. current versus superseded/disputed lifecycle;
3. explicit scope and exceptions;
4. provenance/origin; and
5. conflict with current user instructions or stronger evidence.

A preference is decision evidence, not authority. Agents may and should explain when a current case warrants departing from a usual preference.

## First-run state

`.observatory/personal-operating-model.yaml` records onboarding state. A public or fresh Observatory can start as `uninitialized`.

When the POM is uninitialized, an agent may offer the optional Personal Model Interview **without blocking the user's task**. The offer should explain that the model can capture things such as desired agent autonomy, evidence standards, speed/rigor/cost tradeoffs, preferred recommendation style, challenge behavior, recurring lessons, and approaches not worth repeating.

Offer choices equivalent to:

- Start interview
- Build it gradually
- Not now
- Don't ask again

The owner may use Observatory indefinitely without creating a POM.

## Interview and gradual learning

Use `skills/personal-model-interview/SKILL.md` for a one-question-at-a-time bootstrap interview. Interview answers first become candidate records; they do not automatically become canonical knowledge.

During normal work, repeated or corrective observations may suggest a transferable POM lesson. Use `skills/observation-promotion/SKILL.md`: propose or stage the smallest evidence-linked pattern, preserve contradictions and temporal scope, and require owner review before canonical promotion.

Project-specific choices should remain project knowledge unless the evidence supports a genuinely transferable operating principle or lesson.

## Performance and safety failure modes

### Context pollution

Loading a whole personal profile can reduce effective context quality and raise token/latency cost. POM retrieval therefore follows Observatory's existing metadata-first progressive-disclosure contract.

### Stale preferences

Preferences change. Preserve `valid_from`, `valid_until`, `supersedes`, and `conflicts_with` when useful. Never silently overwrite a conflict. Current instructions win.

### Over-personalization and anchoring

Do not use the POM to suppress material evidence, safety requirements, or better-supported alternatives. The correct behavior may be: “Your usual preference points toward A, but this case differs because X.”

### Sycophancy

The POM models how decisions should be evaluated and communicated, not which conclusion the owner wants. It must never become a requirement to agree with the owner.

### Scope leakage

A preference learned in software architecture must not automatically affect unrelated domains. Scope records narrowly enough to prevent cross-domain leakage.

## Evaluation gate

Extend provider-neutral agent evaluations to check:

- relevant personalization improves or preserves task success;
- irrelevant POM records are not opened;
- current instructions beat stored preferences;
- newer/superseding evidence beats stale preferences;
- domain-scoped preferences do not leak;
- evidence can override a soft preference;
- known OperatingLessons prevent repeated failed approaches; and
- an uninitialized or disabled POM does not degrade normal Observatory use.

Track POM-attributable full-document opens, approximate tokens when available, retrieval latency, false-personalization rate, stale-memory application, and task-success delta. Do not broaden default POM retrieval until measured failures justify it.

## Relationship to interviews and Decision Frontier

The interview asks one consequential question at a time and persists only settled, reviewed understanding. Observatory does not depend on an external interview package.

For large foggy work, a **Decision Frontier** may complement `.ops/PROJECT_STATUS.md`: project status answers “what are we doing?”, while the frontier answers “what still needs to be decided?”. POM records may influence how a decision is evaluated, but unresolved project decisions remain project/operational state rather than POM data.

## External skills

POM is separate from the skill library. Reusable agent procedures live under `skills/` and are routed through `skills/CATALOG.md`. Third-party skill packs may be vendored or referenced there, but repository policy remains authoritative and external skill instructions never gain permission to override `AGENTS.md`, current user instructions, security policy, or consent.
