---
name: deep-research
description: Build durable, multi-source research dossiers for subjects that warrant long-term depth beyond source and concept cards.
---

# Deep research dossier

Use this skill when the owner asks for **deep research**, **deep brain**, **learn this deeply**, **understand this**, a robust treatment of a subject, or when a subject has high current project value and the work is clearly an investigation rather than simple capture.

The purpose of a dossier is durable depth. Do not optimize it for brevity. A dossier should preserve enough of the research that the owner or a future agent can reuse the work months later without redoing the entire investigation.

## Depth model

Observatory uses complementary layers:

1. **Source card (`sources/`)** — fast orientation to a specific artifact: what it is, its main claims, provenance, and why it matters.
2. **Concept card (`concepts/`)** — compact, evolving synthesis of durable understanding across sources.
3. **Research dossier (`research/`)** — long-form, multi-source investigation with evidence, disagreement, implementation detail, failure modes, alternatives, and project implications.

Do not replace compact cards with dossiers. Cards are retrieval/navigation layers; dossiers are depth layers. Link them to one another.

## When a dossier is warranted

Create or meaningfully update a dossier when one or more apply:

- the owner explicitly asks for deep research or equivalent depth;
- the subject is being seriously considered for adoption, implementation, purchase, architecture, or long-term learning;
- the subject materially affects an active project and shallow notes would likely require re-research later;
- multiple strong sources disagree or need synthesis;
- the topic has important mechanisms, tradeoffs, failure modes, security/privacy implications, or implementation choices that a short card cannot preserve;
- a prior source/concept card has become a frequently reused hub and deeper evidence would improve future reasoning.

Do not create a dossier for every bookmark, passing curiosity, trivial fact, or source whose durable value is fully captured in a compact card.

## Research standard

1. Define the research questions before gathering sources.
2. Search the existing brain first; reuse and update prior work rather than duplicating it.
3. Prefer primary literature, official documentation, first-party engineering reports, standards, and original talks/papers. Use strong secondary sources for synthesis, criticism, and discovery.
4. Research **beyond the supplied artifact**. A dossier is not an expanded summary of one source.
5. Seek corroboration, counterevidence, competing approaches, known failures, and unresolved questions.
6. Separate source claims, corroborated conclusions, inference, owner ideas, and uncertainty.
7. Preserve stable provenance and use claim-level source IDs/footnotes where attribution materially affects trust.
8. For changing subjects, record freshness and reassessment triggers.
9. For technical subjects, cover mechanism, architecture, prerequisites, implementation patterns, evaluation methods, operational burden, security/privacy, failure modes, and alternatives when applicable.
10. For learning subjects, include prerequisite knowledge, a recommended sequence, exercises/implementation opportunities, and tests for genuine understanding rather than passive familiarity.

## Expected dossier shape

Adapt headings to the subject, but robust dossiers normally include:

- `# Executive TL;DR`
- `# Research questions`
- `# Background and definitions`
- `# Mental model / how it works`
- `# Evidence and key findings`
- `# Competing approaches or interpretations`
- `# Failure modes and limitations`
- `# Implementation / application` when relevant
- `# Evaluation: how to know it works`
- `# Security, privacy, operational, or maintenance implications` when relevant
- `# Connections to existing Observatory concepts`
- `# Project implications and project-value scorecard`
- `# Open questions and unresolved disagreements`
- `# Recommended next actions`
- `# Sources and provenance notes`

There is no fixed word count. Depth should be proportional to the topic. Several thousand words is normal for a consequential technical investigation; do not pad simple subjects to meet a target.

## Storage and identity

- Store durable dossiers under `research/` with `type: ResearchDossier`.
- One dossier should represent one coherent research question/topic, not one source.
- Use a stable `id` and descriptive title.
- Link to relevant Source and Concept cards in prose.
- Source cards remain the canonical representation of individual artifacts; do not paste entire copyrighted sources into dossiers.
- Update an existing dossier when new work extends the same research question. Let Git history preserve earlier conclusions.

## Evaluation before declaring depth complete

Before finishing, ask:

- Could a future agent understand the important mechanisms without reopening every source?
- Are important claims attributable?
- Did the research look for disagreement and failure, not only supporting evidence?
- Are implementation implications concrete rather than generic?
- Is it clear what remains uncertain?
- Could the owner avoid redoing most of this research six months from now?

If the answer to several is no, the dossier is not deep enough.

Run repository validation and preservation checks before proposing the change. Never auto-merge a research dossier.