---
name: session-capture
description: Turn an agent session or project handoff into minimal, reusable Observatory knowledge.
---

# Remember this session / Brain this session

Use this provider-neutral workflow for **Remember this session**, **Brain this session**, **Save project handoff**, or an equivalent explicit request. It follows the common repository-instruction pattern: `AGENTS.md` is the canonical repository-wide policy, nested instructions may specialize it, and provider files remain thin pointers rather than copied policy.

This is Observatory's durable **retain** path. Follow `docs/runtime-memory-contract.md`: runtime conversations and temporary observations may inform the preview, but they remain non-canonical until this reviewed capture flow promotes a useful synthesis.

## Default behavior

First return a non-persistent preview. Never save a raw transcript by default. Retain only information likely to help future work:

- session goal, outcome, and current project state;
- decisions and the reasons or evidence behind them;
- approaches tried, failures, and reusable lessons;
- changed artifacts or relevant source links;
- unresolved questions, risks, dependencies, and next actions.

Exclude conversational filler, chain-of-thought, redundant command output, secrets, credentials, environment contents, unnecessary personal data, and copyrighted source text. Treat session statements as owner/agent-provided provenance, not independently verified facts.

## Route before writing

Search existing cards first, then make the smallest durable update:

1. Update the matching `projects/*.md` card for project status, decisions, and next actions; do not create a project-per-session.
2. Update an existing Concept for reusable learning, or create one only when it is genuinely distinct.
3. Route hypotheses to Ideas and unresolved research to Questions.
4. Create a Source card only when the conversation or handoff is important provenance; use a stable `conversation:` resource without copying the transcript.
5. Put uncertain or not-yet-durable material under `staging/`.

Use an ISO date in a compact `## Session update: YYYY-MM-DD — <topic>` project section when chronology matters. Consolidate repeated updates during maintenance rather than accumulating duplicate summaries. Preserve unknown frontmatter, provenance, lifecycle, and verification fields.

## Rules and instruction scope

For **Make this a rule**, classify the requested scope before editing:

- repository-wide operating policy belongs in the root `AGENTS.md`;
- a specialized reusable procedure belongs in the relevant `skills/*/SKILL.md`;
- project knowledge belongs in its Project card, not in agent policy;
- provider entry files such as `CLAUDE.md` should point to `AGENTS.md`, not duplicate it.

Explain the proposed location and effect before writing when scope is ambiguous. Never edit machine-wide or provider-global instruction files outside this repository unless the owner explicitly names the path and separately authorizes that external change. External agents must be given repository access and told to read `AGENTS.md`; this repository cannot automatically control every AI service.

## Explicit finish actions

End the preview with **Discard**, **Stage session**, **Brain session**, **Update project**, or **Edit preview**. Write only after the owner chooses an action. A request to remember or save authorizes the selected content write, but does not create a human verification event. Praise, acceptance, successful execution, a thumbs-up, commit approval, or PR merge also does not mean human-reviewed.

For a write, use the brain-core and ingest safeguards, add ordinary Markdown connections, validate, run preservation checks, and propose a reviewable Git commit or PR. Report exactly which durable cards changed and which details were intentionally omitted.
