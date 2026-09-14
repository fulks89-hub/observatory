# Request guards and enforcement review — 2026-09-14

| Capability | Status and boundary |
| --- | --- |
| Rule-to-enforcement map | Portable guidance for prose, permissions, request guards and outcome evidence |
| Bounded read preflight | CLI with explicit root/size policy, strict input and metadata-only checks |
| Claude Code adapter | Opt-in PreToolUse Read protocol and configuration recipe; no active installation |
| Regression coverage | Allowed/denied reads, malformed input, traversal, links, size and policy bypass attempts |
| Reviewed promotion | Failure evidence informs a narrow proposal; no automatic rule changes |
| Existing outcome checks | Output contracts, artifact-bound receipts and conservative retries remain available |
| Specialized integrations | Domain-specific query guards and runtime deployment require separate evidence and review |
| Excluded | Personal data, private history, raw correspondence, global settings and automatic memory mirroring |

See [rule enforcement](../rule-enforcement.md) for use, scope, rollback and runtime
limitations. This increment extends the [previous enhancement release](2026-09-14-enhancements.md).
Repository validation does not establish live hook coverage or improved model outcomes.
