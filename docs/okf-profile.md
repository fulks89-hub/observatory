# Observatory OKF v0.2 profile

This profile was reconciled against the normative [OKF v0.2 specification at commit `fe3268a`](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f/okf/SPEC.md) on 2026-08-15.

## Normative baseline

- A concept is UTF-8 Markdown with YAML frontmatter; `type` is the only universally required key.
- Types are open strings. Observatory recommends `Concept`, `Source`, `ResearchDossier`, `Person`, `Idea`, `Question`, and `Project`, but a conforming consumer must tolerate other values.
- Unknown frontmatter keys are extensions and must not be rejected; round-tripping consumers should preserve them.
- Each `sources` entry is a mapping with required `resource`; `id` is the stable join key for claim-level Markdown footnotes.
- `generated` is a mapping with `by` and `at`. `verified` is either one event mapping or a list of events. Trust is derived from `verified`, not stored as a separate score or tier.
- Lifecycle uses `status: draft | stable | deprecated` and optional absolute `stale_after: YYYY-MM-DD`.
- The local open-extension profile uses `valid_from` / `valid_until` dates plus `supersedes` and `conflicts_with` document-ID lists for deterministic temporal applicability. These fields do not alter upstream OKF and are preserved by generic readers.
- `index.md` and `log.md` are reserved. Only the bundle-root index may have frontmatter, and then only `okf_version`.
- Broken Markdown links do not make an OKF bundle nonconformant. Observatory reports them as navigation warnings rather than errors.

## Local profile and bundle boundary

The repository contains operational documentation and Skills as well as knowledge. The OKF bundle validated by `.venv/bin/observatory validate` is the durable corpus in `concepts/`, `sources/`, `research/`, `people/`, `ideas/`, `questions/`, and `projects/`, with the root `index.md` as its navigation entry point. Files such as `README.md`, `SECURITY.md`, and `skills/*/SKILL.md` are repository operations material, not OKF concept documents.

Observatory adds optional `id` values for duplicate detection and applies a local type-to-directory ontology. `ResearchDossier` is one such local open type: it denotes a long-form multi-source investigation under `research/`. This is an organizational convention, not a claim that upstream OKF defines a dossier type or a `research/` directory. Dossier files remain ordinary OKF v0.2-compatible Markdown and must preserve unknown fields like any other durable document.

The depth distinction is intentionally local and semantic:

- `Source` identifies and summarizes a specific artifact.
- `Concept` holds compact evolving synthesis for frequent retrieval.
- `ResearchDossier` preserves a consequential investigation in substantially greater multi-source depth.

These layers may link to one another using ordinary Markdown; no proprietary relationship syntax is required.

## Enforcement boundary

The validator hard-fails deterministic local safety and structural problems: malformed YAML, missing `type`, malformed standard field families, duplicate local IDs, reserved filenames used as concepts, and likely committed credentials. Unknown types and broken links are warnings because the normative specification requires permissive consumption. A passing run means the local profile passed; it is not a certification by Google or a complete general-purpose OKF conformance suite.
