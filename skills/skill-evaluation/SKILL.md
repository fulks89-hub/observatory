---
name: skill-evaluation
description: Compare a reusable agent skill against a frozen baseline using realistic tasks, holdouts, and separate provider evidence. Use when evaluating or revising skills; distinguish native-harness runs from model-API and saved-artifact checks.
---

# Cross-agent skill evaluation

Measure what the skill contributes to the requested task, not just whether an agent
can finish it. This procedure does not call providers or install candidates by itself.

1. Define representative cases, acceptance checks and unseen holdouts before revising
   the skill. Keep related task families in one split. Use synthetic fixtures for
   shareable evaluations; real transcripts and personal records stay private.
2. Freeze the baseline revision, prompts, checks, fixture revisions, permissions and
   tool/network boundary. Candidate development may use training evidence only.
3. Compare baseline and candidate separately for each provider under comparable
   conditions. Record actual model/harness versions, parameters and execution mode.
   Native skill loading, model-API prompting and saved-output checks are different
   evidence classes; do not combine them into one native-compatibility claim.
4. Repeat nondeterministic runs within the authorized budget when needed to distinguish
   signal from one result. Prefer deterministic checks for observable requirements;
   record human or trusted-judge evidence for qualities those checks cannot establish.
5. Reject missing evidence, changed protected checks, policy mutations and regressions
   from a passing provider-specific baseline. Report success rates and contribution
   deltas separately, alongside limitations and observed usage or latency.
6. Treat results as evidence for review, not permission to install, publish, change
   settings or spend additional capacity. Use already-authorized resources within a
   finite run scope; checkpoint and park when approaching capacity limits.

Use an installed provider's supported evaluation mechanism only after confirming its
availability and boundaries. For native Codex or Claude runs, use an isolated checkout
with a thin provider entry file pointing to the same canonical skill. Do not alter the
owner's global configuration for an evaluation.

For recording or exchanging results, read [the portable evidence guide](references/portable-evidence.md).
