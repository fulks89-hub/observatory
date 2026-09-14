# Template roadmap

## First use

- Customize the brain name and repository policy.
- Replace the example project with a real project.
- Capture one source and synthesize one linked concept through a reviewable branch.
- Confirm CI, validation, catalog generation, and preservation checks.

## Add only when measured

- semantic retrieval after real lexical misses;
- graph assistance after real multi-hop misses;
- runtime memory after repeated cross-session failures;
- connectors only with explicit scopes, retention, and deletion rules.

Canonical Markdown remains portable regardless of which optional layers are added.

## Request enforcement increment — 2026-09-14

Users: maintainers and agents wiring Observatory into existing runtimes.
Value: catch measurable request violations before dispatch while keeping outcome
evidence separate. Scope: portable enforcement map, bounded file-read guard, opt-in
provider adapter and synthetic regressions. See [the guide](docs/rule-enforcement.md).

Acceptance: reject malformed requests, path/size violations and policy bypass attempts;
preserve native permissions; complete all repository gates on the integrated revision.
Launch readiness requires separate verification of repository integration and any
authorized runtime installation. No provider configuration is activated by this release.
Next: add specialized guards only after concrete failure evidence and reviewed scope.

## Coverage audit increment — 2026-09-14

Users: maintainers checking which rules have working controls. Value: expose gaps
without mistaking passing tests for live enforcement. Scope: five marked core rules,
a strict registry, a bounded named-test audit in CI, and a Git line-ending regression.

Acceptance: missing/stale mappings and failed/skipped tests block the audit; counts
declare their scope; runtime activation stays unverified; byte changes invalidate
receipts even when Git is clean. Full repository gates validate the final revision.
Launch readiness includes verified PR integration and post-merge checks. Follow-up
runtime verification needs separately authorized deployment evidence. See the
[coverage guide](docs/rule-enforcement.md#auditable-implementation-coverage).
