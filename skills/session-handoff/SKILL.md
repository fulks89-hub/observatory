---
name: session-handoff
description: Preserve active work safely when a long agent session should be continued in a fresh context.
---

# Session handoff protocol

Use this workflow when a working session should be continued in a fresh model context without losing operational state.

## Three layers: live status, handoff snapshot, durable knowledge

Keep these distinct.

### 1. Live project status

Each actively developed repository should maintain a non-canonical operational file at `.ops/PROJECT_STATUS.md` when long-running agent work would benefit from continuity.

This file is a continuously updated working-state read model, not part of the durable knowledge corpus. It should be cheap to overwrite and should answer, in under two minutes of reading:

- What are we trying to accomplish right now?
- What is complete?
- What is currently in progress?
- What branch/PR/HEAD/CI state is authoritative?
- What did we already try that failed or proved misleading?
- What pitfalls should the next agent avoid?
- What decisions are currently active and why?
- What is blocked?
- What are the next ordered actions?

Use explicit sections such as:

```markdown
# Project status

## Current objective
## Current state
## Active branches / PRs / exact heads
## Decisions in force
## Tried / failed / do not repeat
## Validation and evidence
## Blockers / risks
## Next actions
## Last updated
```

When the work is large or foggy enough to require unresolved-decision mapping, maintain `.ops/DECISION_FRONTIER.md` using `skills/decision-frontier/SKILL.md`. Project status records execution state; the frontier records unresolved decisions and dependencies. Do not combine them into one giant status document.

Update operational state after material changes, especially after a failure, architectural decision, CI result, branch/PR change, completed milestone, or frontier decision resolution. Do not wait until context is nearly full to record a pitfall.

Operational files may summarize evidence but should link to canonical docs, issues, PRs, research, or benchmark outputs rather than becoming a second knowledge base.

### 2. Handoff snapshot

A handoff is a point-in-time transfer artifact created when a fresh context is useful. Build it primarily from the live project status, the Decision Frontier when present, plus the current session's unsaved operational details.

Capture the minimum state needed for another agent to resume correctly:

- objective and current scope;
- completed work;
- active repositories, branches, PR numbers, exact HEAD SHAs, and CI state when relevant;
- important architectural or product decisions and the reason for them;
- unresolved frontier decisions and dependencies when a Decision Frontier exists;
- commands/tests already run and their results;
- failures, false starts, and traps not to repeat;
- unresolved questions and dependencies;
- ordered next actions;
- user constraints/preferences that materially affect the active work;
- current working owner/session, intended paths or subsystem, and unresolved branch overlap;
- a concise restart prompt.

Exclude raw chain-of-thought, conversational filler, full transcripts, secrets, credentials, large tool logs, unnecessary personal information, and copied copyrighted material.

### 3. Durable knowledge

Only promote material into canonical `projects/`, `concepts/`, `research/`, `ideas/`, `questions/`, `sources/`, or reviewed `personal-operating-model/` records when it independently meets Observatory's ingest rules. Neither `.ops/PROJECT_STATUS.md`, `.ops/DECISION_FRONTIER.md`, nor a handoff may become a back door for dumping temporary state into canonical knowledge.

## Trigger conditions

Prepare a handoff proactively when one or more of these are true:

- the agent knows or reasonably suspects the active context is becoming constrained;
- a paid AI model or subscription reports, or the agent reasonably suspects, that a usage, context, rate, credit, or subscription limit is close enough to threaten completion;
- the conversation has accumulated enough parallel workstreams, tool state, branches, PRs, or unresolved decisions that reconstruction would be costly;
- the user asks to continue in another thread, model, machine, or provider;
- a long implementation/research phase reaches a natural checkpoint;
- repeated summarization or omitted earlier details indicate context quality may be degrading.

Do not invent a precise context-percentage meter when the provider does not expose one. Prefer an early clean handoff over waiting for context loss.

## Capacity-triggered handover and clean parking

When a paid-model capacity trigger fires, treat continuity as the current task. Do not begin another substantial action. Complete only an already-started atomic action when doing so is safer than leaving it partial; otherwise record the partial state explicitly.

1. Refresh `.ops/PROJECT_STATUS.md` with the current objective, current status, material decisions, validation evidence, blockers, pitfalls, and ordered next actions.
2. If `.ops/DECISION_FRONTIER.md` exists, refresh active decision states, dependencies, current frontier, and newly resolved outcomes before handoff.
3. Create or update one structured handoff under `.ops/handoffs/`. Include a `## Capacity / parking state` section that records the provider/model only when known, the kind of limit, the observed signal or reason for early handover, whether remaining capacity is unknown, and what work was deliberately not started.
4. Include `## Working ownership / overlap` using `docs/concurrency-contract.md`. Record the branch and exact head, intended path scope, active refs checked, and unresolved/reconciled overlap. Run `.venv/bin/observatory overlap` against known active refs before describing ownership as clean.
5. Exclude account identifiers, billing details, credentials, raw provider dashboards, and unverifiable capacity estimates. A provider warning may be summarized as operational provenance; it is not canonical knowledge.
6. Ensure no destructive or externally visible action is left half-complete. Record any transient resource that the next agent must verify or close. Do not merge, deploy, send, purchase, or broaden permissions merely to make the handoff look complete.
7. Report the handoff path and park cleanly: stop tool use and substantive work after the checkpoint. The agent or coordinator selecting a successor must use only an available, authorized model whose privacy and tool boundaries fit the task.
8. The successor must read `AGENTS.md`, `.ops/PROJECT_STATUS.md`, `.ops/DECISION_FRONTIER.md` when present, and the handoff; independently verify mutable state such as branches, exact heads, CI, external actions, overlap, current frontier, and current capacity; then mark the work resumed. Do not describe routing as successful failover until that verification and resumption occur.

If this repository is unavailable or unwritable, return the same structured handoff in chat. Do not claim that it was persisted to the Second Brain.

## Automatic staging rule

When repository write access exists and the owner has enabled this handoff protocol, the agent may maintain `.ops/PROJECT_STATUS.md`, `.ops/DECISION_FRONTIER.md` when applicable, and create/update a compact handoff under `.ops/handoffs/` on a reviewable branch without separately asking at the moment context becomes constrained.

These are operational artifacts, not human verification events and not canonical durable knowledge. Never auto-merge solely because a status/handoff was generated. If repository write access is unavailable, return the handoff in chat instead.

Prefer one active handoff per ongoing workstream and update it rather than accumulating a handoff for every conversation turn.

## Handoff format

Use this structure:

```markdown
# Handoff: <workstream>

## Resume objective
<one paragraph>

## Current state
- repositories / branches / PRs / exact heads
- what is complete
- what is still in progress

## Decisions that must survive
- decision — rationale

## Decision frontier
- unresolved actionable decisions / dependencies when applicable

## Validation / evidence
- tests, CI, research evidence, or checks already completed

## Known traps / do not repeat
- failed approaches or important caveats

## Capacity / parking state
- observed limit signal, uncertainty, deliberately unstarted work, and parked state

## Working ownership / overlap
- owner/session, branch and exact head, intended paths, refs checked, unresolved/reconciled overlap

## Next actions
1. ...
2. ...

## Restart prompt
<self-contained prompt telling the next agent what to read, what state to verify, and what to do next>
```

## Restart prompt requirements

The restart prompt must be self-contained enough that a fresh agent can begin without relying on invisible conversation history. It should:

1. name the relevant repository/repositories and workstream;
2. tell the agent to read `AGENTS.md`, `.ops/PROJECT_STATUS.md`, `.ops/DECISION_FRONTIER.md` when present, and relevant skills first;
3. identify active PRs/branches and require verification of current heads rather than trusting stale SHAs blindly;
4. summarize the current objective and constraints;
5. state the next concrete action;
6. tell the next agent not to merge or make destructive changes without the owner's normal authorization;
7. point to the handoff path when one exists.

## Handoff completion

After creating a handoff, tell the owner that a clean checkpoint exists and provide the restart prompt in chat. Do not force a new thread if the current context remains healthy; the handoff is insurance, not an interruption ritual.

When work resumes successfully, the newer agent should refresh `.ops/PROJECT_STATUS.md` and `.ops/DECISION_FRONTIER.md` when present; it may remove or replace the older handoff in a later reviewed maintenance change after any truly durable knowledge has been promoted appropriately.
