# Rule coverage audit — 2026-09-14

| Capability | Scope and status |
| --- | --- |
| Rule inventory | Five marked rules with stable IDs, source fingerprints, scopes and gaps |
| Implementation audit | Validates mappings/control files and executes named regressions; failed, missing or skipped cases block |
| Evidence freshness | Compares complete repository artifact hashes and file lists before/after the audit |
| Honest activation status | Implementation evidence is separate from unverified runtime activation |
| Git normalization regression | Demonstrates stale receipts rejected after a Git-clean LF-to-CRLF rewrite |
| CI integration | Coverage audit runs alongside existing validation and preservation checks |
| Excluded | Global settings, live installation, private evidence, automatic promotion and claims of complete rule coverage |

This extends the [request-guard release](2026-09-14-request-guards.md).
See the [coverage guide](../rule-enforcement.md#auditable-implementation-coverage)
for the declared scope, trust requirements and limitations.
