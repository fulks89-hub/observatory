# Multi-agent ownership and overlap contract

Git records concurrent changes but does not decide whether two agents' edits are semantically compatible. Observatory therefore treats same-path overlap as a review gate, especially for canonical knowledge, policy, schema, and skills.

## Ownership rules

1. Every autonomous workstream uses its own reviewable branch or worktree.
2. Before substantive edits, the active status or handoff should name the branch, exact starting head, intended paths or subsystem, and current agent/session owner.
3. Ownership is advisory, not a lock. Another agent may inspect the same files but should not write them without coordinating or explicitly accepting a later reconciliation step.
4. Before handoff, integration, or PR readiness, compare the workstream with every active overlapping branch using `observatory overlap <other-ref> --base-ref <base-ref>`.
5. Any same-path overlap requires inspection. Canonical and policy overlap is high risk and must never be resolved mechanically with an unconditional "ours" or "theirs" choice.
6. Reconciliation must preserve both branches' provenance, verification records, unknown metadata, durable headings, and independently useful intent. Run the preservation and complete validation gates after reconciliation.

## Semantic conflict handling

A clean Git merge is not evidence of semantic compatibility. Review overlapping claims for:

- contradictory decisions or temporal scope;
- one branch reviving a superseded approach;
- duplicated concepts or sources;
- changed verification or provenance;
- policy changes with different intended scopes; and
- operational status that became stale while another branch progressed.

When both claims remain useful, represent the conflict or temporal succession explicitly instead of erasing one. Use stable document IDs with `supersedes` or `conflicts_with` only when the relationship is supported and intentional.

## Handoff ownership block

Every handoff for active repository work should include:

```markdown
## Working ownership / overlap
- owner: <agent/session identifier>
- branch and exact head: <branch> @ <sha>
- intended paths/subsystem: <small explicit scope>
- other active refs checked: <refs or unknown>
- overlap result: <none, unresolved paths, or reconciled paths>
```

The successor rechecks mutable refs rather than trusting the recorded result indefinitely.
