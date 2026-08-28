---
name: observatory-core
description: Safely edit the canonical Observatory OKF Markdown corpus.
---

# Observatory core procedure

1. Read `AGENTS.md`, `.observatory/policies.yaml`, `.observatory/ontology.yaml`, `.observatory/schema.yaml`, and `skills/CATALOG.md`.
2. Classify the artifact or synthesis as Source, Concept, ResearchDossier, Person, Idea, Question, Project, OperatingPrinciple, OperatingPreference, or OperatingLesson. Never turn a user hypothesis into an externally verified claim, and never turn an inferred working pattern into an owner-approved Personal Operating Model record without review.
3. Search filenames, titles, tags, aliases, and body text before creating a file.
4. Update an existing page when it represents the same durable subject. Preserve every unknown frontmatter key and all provenance, generated, verified, lifecycle, scope, conflict, and supersession records.
5. Write only durable synthesis. Keep captured artifact details in `sources/`; keep compact topic synthesis in `concepts/`; use `research/` for consequential multi-source depth; keep active initiative maps in `projects/`; and use `personal-operating-model/` only for reviewed transferable operating principles, scoped preferences, and reusable lessons. Link these layers rather than duplicating the same prose.
6. Use relative ordinary Markdown links with meaningful surrounding prose.
7. Represent uncertainty in prose and provenance. `human-reviewed` may only record an explicit human review event.
8. For POM edits, also read `skills/personal-operating-model/SKILL.md`. Project-specific decisions stay with the Project unless they support a genuinely transferable reviewed lesson or principle.
9. Run `observatory validate`, the complete repository tests, `observatory catalog` to a disposable output, and `observatory preserve <base-ref>` against the intended PR base. Inspect the diff before proposing review.
10. Treat the validation state as tied to the exact branch head. Any subsequent edit makes the previous green result stale and requires the checks to run again before merge readiness is claimed.
11. Use a reviewable branch/PR for autonomous work. If the current environment cannot execute the required checks, do not claim validation or merge readiness. A draft PR may be used only to trigger CI when necessary and remains blocked until the checks pass.

OKF v0.2 field rules: keep `type` open; write every `sources` item as a mapping with `resource`; use `{ by, at }` for `generated` and verification events; derive trust from `verified` rather than storing a score; use only `draft`, `stable`, or `deprecated` for `status`. Broken links are navigation warnings, while malformed standard field families are errors.

`ResearchDossier`, `OperatingPrinciple`, `OperatingPreference`, and `OperatingLesson` are local OKF-compatible open types, not replacements for the upstream format. Their files remain ordinary human-readable Markdown with the same provenance, verification, lifecycle, Git-history, and relationship conventions as other durable documents.

Do not write derived graph/search state into canonical directories. Do not delete durable content without explicit owner authorization. Do not bypass preservation failures caused by heading removal/renaming, provenance loss, verification loss, or substantial body loss merely because the intended replacement seems semantically equivalent; preserve the old structure or obtain explicit destructive-change approval.

For a large corpus, retrieve progressively: inspect `index.md`, `skills/CATALOG.md`, or the disposable catalog, narrow candidates by type/title/alias/tag/project/source/scope, open only relevant canonical cards or dossiers, follow links when the question requires more context, and expand again only when evidence is insufficient. Cite canonical files, not catalog records. Report material uncertainty and search gaps.
