# Second-brain operating-system interview

Use this reference for first-run onboarding or a deliberate redesign. Ask for exactly one answer per conversational turn and adapt the next follow-up to that answer. Keep unused topics in an internal queue for later turns; do not mention them as additional requested inputs. Do not turn the topic lists below into a questionnaire. Skip areas already answered by owner-approved knowledge.

## Interview method

- Start with a recent real workflow, not abstract preferences.
- Ask what triggers the workflow, what enters the system, what decision or output it should improve, and what currently breaks.
- Challenge vague words with: “What would that look like?”, “What should the agent do by default?”, or “When should that rule not apply?”
- Distinguish must-have constraints from preferences and experiments.
- Summarize every few questions and let the owner correct, pause, or redirect.
- Do not make the current task wait for a complete interview; preserve an approved checkpoint and continue later.

## Areas to cover

### Purpose and success

- Which decisions, projects, learning, relationships, or creative work should the Observatory improve?
- What would make the system obviously useful after thirty days? What would make it feel like overhead?
- Which current system behaviors must survive migration?

### Capture and trust

- What should be easy to capture, from which sources, and through which phrases or tools?
- What belongs as durable knowledge versus tasks, logs, bookmarks, or temporary working state?
- What provenance, verification, and uncertainty should be visible before the owner trusts a record?

### Retrieval and synthesis

- When should an agent search the Observatory, and how much context should it initially retrieve?
- Does the owner want a direct answer, ranked options, evidence first, or a compact recommendation with drill-down?
- When should multiple notes be synthesized, kept separate, or turned into deeper research?

### Projects and execution

- How are active projects, outcomes, next decisions, blockers, and handoffs represented today?
- What status becomes stale quickly, and what should remain durable across years?
- Which work domains must stay separate, especially personal, employer, client, or public material?

### Agent working relationship

- Which reversible actions may agents take independently, and which actions always require approval?
- How strongly should an agent challenge weak assumptions or conflict with prior lessons?
- What evidence, testing, cost, speed, and communication tradeoffs should govern consequential work?

### Review and maintenance

- Who reviews staged knowledge, on what cadence, and what is allowed to remain unresolved?
- How should duplicates, stale claims, conflicts, dead links, and abandoned projects be handled?
- What is the maximum acceptable maintenance burden, and which automation would earn that burden?

### Integrations, resilience, and exit

- Which repositories, note systems, task tools, feeds, or AI Radar sources are in scope?
- Which tools may read private material, write files, use the network, or spend money?
- What backup, portability, export, and provider-replacement guarantees matter?

## Output contract

Translate answers into a reviewable blueprint, not a personality profile. For each proposal record:

- observed need or owner statement;
- proposed behavior and scope;
- destination (`AGENTS.md`, provider rule, `.observatory` configuration, Project, POM candidate, Radar configuration, staging, or external system);
- exceptions and unresolved questions;
- provenance and confidence; and
- validation or reassessment trigger.

Keep direct owner statements distinct from agent inference. Project-specific decisions stay with their Project; transferable working principles may become POM candidates only through owner review.
