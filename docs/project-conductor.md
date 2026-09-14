# Project conductor workflow

The [project-conductor skill](../skills/project-conductor/SKILL.md) connects product planning, a prioritized roadmap, bounded execution, verification, and later feature development. It applies to substantial project work; straightforward tasks stay lightweight.

The lead is a persistent, user-addressable session named `Project Name conductor`, established when the owner launches that named project. The plan and status live in the product repository. Observatory's Project card points to them. Workers are replaceable, and a successor can recover the lead role from verified files if its original session is unavailable. No always-running agent or scheduler is implied.

## Fit with the existing system

| Existing component | Role in this workflow |
| --- | --- |
| Product plan / roadmap | User value, product outcomes, priority, acceptance and release readiness |
| Project card | Compact map to authoritative product and execution records |
| [Decision Frontier](../skills/decision-frontier/SKILL.md) | Unresolved choices only when uncertainty warrants it |
| [Concurrency contract](concurrency-contract.md) | Worker ownership, isolated changes and integration review |
| [Session handoff](../skills/session-handoff/SKILL.md) | Checkpoint, park, resume and provider transition |
| [Context budget](context-budget-contract.md) | Small, relevant context rather than accumulated transcripts |
| [Capacity contract](ai-provider-capacity-monitor.md) | Stop before exhaustion; no autonomous spending increases |

Reuse an existing PRD, intent document, backlog or status file rather than installing parallel copies. The [optional templates](../skills/project-conductor/templates.md) only fill missing structures. The [AI operating model](ai-operating-model.md) supplies the broader intent/context contract. The [opt-in discovery integration](agent-discovery-integration.md) helps a provider find the trusted repository. These components share this workflow rather than creating competing plans or policy authorities.

## Personal provider entry points

Keep the global instruction short: route substantial planning/launch/resume/enrichment work to the skill and require a product plan, roadmap, one named lead, and verified checkpoints. The full procedure loads on demand.

The canonical skill source is this repository's `skills/project-conductor/` package. A reviewed personal installation can copy that package to `~/.agents/skills/project-conductor/` and expose the same package to Claude Code at `~/.claude/skills/project-conductor/`. Record the source revision and package hashes outside the instruction body; compare before replacing an installed version. Do not change an existing installation with unexplained local edits.

Personal provider configuration is local installation state. Keep its paths, session references, hashes, and backups in the owner-controlled private installation. Publishing this skill does not authorize a global installation or copy any existing personal configuration.

Codex and Claude Code have different session, delegation and scheduling tools. Use supported runtime mechanisms after checking availability. Claude web chat does not automatically inherit a local `CLAUDE.md`; provide the project context explicitly there. Instruction files guide behavior; deterministic tests, supported runtime limits, and action permissions provide enforcement.

## Scope and limitations

This is a reusable workflow, not evidence that multiple agents always outperform one.
Use a single agent when that is simpler. Runtime capabilities and current authorization
control session creation, delegation, recurring execution, and release actions.

The public template contains no active conductor, provider session ID, personal setup
record, or automatic heartbeat. Create project-specific records only in the verified
private destination established during onboarding.
