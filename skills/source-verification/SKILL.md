---
name: source-verification
description: Verify claims and encode OKF trust/provenance conservatively.
---

# Verification procedure

- **Unverified:** omit `verified` when content has not been independently checked.
- **Machine-confirmed:** add a real verification event such as `{ by: process:<id>, at: <ISO-8601> }` only after a deterministic process or agent actually checked the claim against identified evidence.
- **Human-reviewed:** add `{ by: human:<id>, at: <ISO-8601> }` only after that human explicitly reviewed it; an agent must never infer this.

These tiers are derived from `verified`; do not store a separate trust score or tier. Prefer primary sources, record conflicts rather than erasing them, and treat freshness separately from correctness. A source's existence does not prove every synthesized claim.
