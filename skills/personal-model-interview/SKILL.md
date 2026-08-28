---
name: personal-model-interview
description: Run an optional one-question-at-a-time interview that proposes a reviewable Personal Operating Model without blocking ordinary Observatory use.
---

# Personal Model Interview

Use this skill when the owner chooses to initialize or deepen the Personal Operating Model.

## Principles

- The interview is optional and must never block the owner's current task.
- Ask one meaningful question at a time.
- Prefer resolving an answer from existing owner-approved Observatory knowledge when practical rather than asking the owner to repeat known information.
- Explain examples when a question is abstract.
- Do not diagnose, psychoanalyze, or infer protected/sensitive identity traits.
- Capture working and decision patterns, not personality labels.
- Do not automatically promote answers into canonical POM records.

## Suggested interview areas

Adapt the sequence rather than treating this as a fixed questionnaire.

### Agent autonomy

Examples:

- When an ambiguity can be resolved by checking the repository or trusted sources, should the agent investigate rather than interrupt you?
- Which reversible choices may an agent make independently, and which choices should always come back for approval?

### Decision tradeoffs

Examples:

- When speed, rigor, cost, simplicity, and extensibility conflict, how do you usually want the tradeoff framed?
- For cheap reversible uncertainty, do you prefer a small experiment, more research, or a recommendation with explicit uncertainty?

### Evidence and uncertainty

Examples:

- What level of evidence should support a consequential recommendation?
- When should the agent label a claim as known, likely, or speculative?

### Communication

Examples:

- Do you prefer ranked recommendations, a neutral comparison, or both?
- How much implementation detail is useful before a decision versus after it?

### Challenge behavior

Examples:

- When your proposed approach conflicts with evidence or a prior lesson, how strongly should the agent challenge it?
- Should the agent surface a better alternative even when you asked for a specific implementation?

### Transferable lessons

Examples:

- Which agent behaviors have repeatedly wasted time?
- Which failed approaches should future agents recognize before trying again?
- What patterns from successful projects should transfer to new ones?

## Interview flow

1. Confirm that the owner wants to start or continue the interview.
2. Inspect existing POM candidates and relevant owner-approved context so questions do not duplicate settled information.
3. Ask one question.
4. Summarize the answer as one or more candidate records, including likely type, scope, and origin.
5. Continue only while the owner wants to continue.
6. At a natural checkpoint, present a compact batch of candidate records grouped as:
   - safe direct owner-explicit candidates;
   - project-specific items that should stay with a Project;
   - inferred or ambiguous patterns that should remain staged.
7. Offer review actions such as **Promote selected**, **Edit**, **Stage**, **Continue interview**, or **Stop here**.

## Persistence

During the interview, progress may be staged under `staging/` when the owner approves preserving the checkpoint. Staged interview notes are non-canonical.

For promotion:

- use `skills/personal-operating-model/SKILL.md`;
- use `skills/observatory-core/SKILL.md` for canonical writes;
- preserve source boundaries and temporal scope;
- never manufacture a human-review or external-verification event merely because the owner answered the interview question.

When the owner chooses gradual learning instead of an interview, update `.observatory/personal-operating-model.yaml` accordingly and rely on reviewable observation proposals rather than repeated onboarding prompts.

## Inspiration boundary

The one-question-at-a-time, durable-artifact approach follows a review-first interview pattern. This is an Observatory-native, provider-neutral procedure; external skills do not override repository policy and are not a runtime dependency.
