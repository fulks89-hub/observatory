# Public enhancement review — September 14, 2026

This update adds reusable delivery and verification capabilities to the public scaffold.
It preserves the existing private/local-only onboarding and synthetic examples. No
personal corpus, operating preferences, session records, evaluation traces, provider
configuration, or private Git history is part of this release.

## Capability review

| Capability | Public status |
| --- | --- |
| Project conductor | Included: reusable skill, blank planning/checkpoint templates, bounded delivery loop and recovery procedure |
| AI operating model | Included: scoped context, intent, delivery, optional decision records and model-guidance template |
| Agent discovery | Included: opt-in preview, hash-bound installation, idempotency and lossless uninstall; no global installation performed |
| Concise writing | Included: evidence-preserving writing guidance; detailed check procedures load only when relevant |
| Execution evidence | Included: strict structured-output checks, artifact-bound receipts and conservative uncertain-operation decisions |
| Python CI evidence | Included: full-suite check wrapper binds evidence to repository inputs before accepting completion |
| Cross-agent skill evaluation | Included: provider-isolated baseline/holdout procedure; no paid/native evaluations launched or unverified benchmark claims |
| Switchboard | Remains a [separate public application](https://github.com/fulks89-hub/observatory-switchboard); its deployment and adapters are not changed here |
| Third-party design extraction | Not activated or vendored; third-party tools require a separate source/security review before adoption |
| Personal runtime and research records | Intentionally excluded; reusable public workflows use blank or synthetic records |

## Review boundaries

The public onboarding flow, uninitialized Personal Operating Model, Mission Control
synthetic seeds, ignored generated exports, pinned Actions and locked dependencies
remain intact. The strict privacy gate is retained. No private-history merge, remote
visibility change, additional paid capacity, recurring automation, or global provider
configuration change is part of this update.

Discovery hashes detect a changed instruction target; they do not record human consent
or provide a hostile-writer lock. Evidence receipts require a trusted runner and complete
artifact scope; they cannot prove semantic quality or authorize retries by themselves.
The conductor is a procedure, not a continuously running service.

## Verification

The release gate requires Python lint/types/tests, documentation links, strict
current-tree/history privacy scanning, corpus validation, disposable catalog generation,
preservation against the public base, skill metadata checks, and Mission Control
checks/tests/build. GitHub Actions records results for the exact published revision.

The [public release policy](../public-release-safety.md#updating-an-existing-public-release)
now requires a capability review for future updates so private/public drift is explicit.
