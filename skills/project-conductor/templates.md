# Optional project structures

Reuse equivalent existing files and headings. These examples are schemas for missing information, not a required bundle of new files. Replace angle-bracket placeholders with real values; omit irrelevant fields.

## Product plan and roadmap

```markdown
# Product plan: <project>
- Status/date: <draft, authorized increment, launched; date>
- Users and problem: <who needs what, and why>
- Desired experience and value: <concrete before/after>
- Success measures: <observable product outcomes>
- Scope / non-goals: <included and excluded>
- Constraints: <privacy, compatibility, performance, cost, permissions>
- Risks / unresolved decisions: <links to existing decisions if needed>
- Acceptance: <checks tied to user outcomes>
- Launch readiness: <release, operations, rollback, support criteria>
- Post-launch learning: <feedback signals and review trigger>

## Roadmap
| ID | Priority | Outcome | Dependencies | State | Completion evidence |
| --- | --- | --- | --- | --- | --- |
| M1 | Now | <small useful increment> | <ids or none> | planned | <required evidence> |
| M2 | Next | <next outcome> | M1 | planned | <required evidence> |
| M3 | Later | <candidate value> | <unknown if unknown> | idea | <to define> |
```

## Add to the project's existing operational status

```markdown
## Conductor
- Project/repository: <canonical identity and location>
- Plan / roadmap / decisions: <authoritative file links>
- Name: <Project Name conductor>
- Provider and actual resume reference: <verified ID/link or uncreated>
- Ownership: <active or parked; owner; timestamp>
- Current authorized increment: <milestone, scope, acceptance>
- Git checkpoint: <branch, base/head, PR/CI when known>
- Execution bounds: <user budget/finite scope; unknown telemetry explicit>
- Automation: <none, or verified ID, stop condition, cancellation method>
- Latest handoff / next action: <link and short step>

## Work in progress
| Task / attempt | Owner | Owned paths / worktree | Dependencies | Base/head | State | Result consumed |
| --- | --- | --- | --- | --- | --- | --- |
| <id / n> | <real worker reference> | <bounded scope> | <ids> | <SHAs> | <state> | <evidence/ref or no> |
```

Worker states may be planned, running, blocked, ready-for-review, integrated, or parked. Use the runtime's native task registry when it already provides these fields; link to it instead of maintaining a competing table.

## Launch or recovery prompt

```text
Act as <Project Name conductor> for <verified repository/project>.
Read its instructions, then <plan>, <roadmap>, <status>, and the latest
relevant handoff. Verify live branch/session/worker state before acting.
Own product coherence, the next authorized increment, integration, checks,
and checkpoints. Reuse this named session for future feature enrichment.
Delegate only independent bounded tasks where permitted. Respect the
recorded scope, capacity, data destinations, and action approval boundaries.
Resume <specific next action>; do not restart completed work.
```

## Worker report

```text
Task ID / attempt / owner:
Outcome and milestone:
Base/head and changed paths:
Checks actually run and results:
Acceptance criteria met / unmet:
Decisions and rationale:
Defects, blockers, failed approaches:
Result location and recommended next action:
```
