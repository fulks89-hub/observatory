---
id: concept-okf
type: Concept
title: Open Knowledge Format
description: A Markdown-and-frontmatter interchange format for portable agent-readable knowledge.
tags: [knowledge-systems, portability, provenance]
sources:
  - id: google-knowledge-catalog
    resource: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f/okf/SPEC.md
    last_modified: 2026-08-14
generated: { by: openai-codex/gpt-5.6-sol, at: 2026-08-15T00:00:00Z }
verified: { by: process:template-source-audit, at: 2026-08-15T00:00:00Z }
status: stable
stale_after: 2026-11-15
---

# TL;DR

Open Knowledge Format (OKF) is Observatory's portability contract: readable Markdown plus YAML metadata, standard links, provenance, verification, and lifecycle context.

# Why it matters

It lets the [personal AI brain](personal-ai-brain.md) survive changes in model providers, editors, graph engines, and retrieval tools.

# Core ideas

OKF v0.2 represents a bundle as a directory tree of Markdown documents with YAML frontmatter. `type` is the only always-required key. Types are open, unknown extension fields are permitted, and consumers must tolerate broken links.[^google-knowledge-catalog]

- Every `sources` entry requires `resource`; optional stable IDs join claim footnotes to source metadata.
- `generated` identifies the producer and meaningful edit time.
- `verified` records actual confirmation events; it is independent of generation.
- Trust is derived from `verified`: absent, non-human verifier, or a `human:` verifier.
- `status` (`draft`, `stable`, or `deprecated`) and absolute `stale_after` represent lifecycle and freshness.
- `index.md` and `log.md` are reserved; a root index alone may declare `okf_version`.

# Connections

- Any external maintenance agent must preserve these v0.2 fields before proposing changes.
- [Knowledge graphs](knowledge-graphs.md) can be derived from standard Markdown links.

# Open questions

- Should Observatory eventually package its canonical directories beneath one dedicated bundle root for stricter whole-tree conformance tooling?

[^google-knowledge-catalog]: Google Knowledge Catalog `okf/SPEC.md`, audited at commit `fe3268a70e8ca5110a43a8f1dfdf6d1a458cf79f` on 2026-08-15.
