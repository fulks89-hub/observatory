---
id: source-knowledge-graphs-foundations
type: Source
title: Knowledge Graphs — foundations and survey
description: Primary literature grounding Observatory's knowledge-graph concepts in representation, context, identity, schema, extraction, quality, and applications.
tags: [knowledge-graphs, research, provenance]
sources:
  - id: hogan-knowledge-graphs
    resource: https://arxiv.org/abs/2003.02320
    title: Knowledge Graphs
    author: Aidan Hogan et al.
  - id: ji-knowledge-graph-survey
    resource: https://arxiv.org/abs/2002.00388
    title: "A Survey on Knowledge Graphs: Representation, Acquisition and Applications"
    author: Shaoxiong Ji et al.
status: stable
generated: { by: openai/gpt-5.6-sol, at: 2026-08-16T07:37:00Z }
---

# TL;DR

Knowledge graphs represent entities and relationships in a form that supports traversal, integration, inference, and querying. The useful lesson for Observatory is not that every note should be pushed into a graph database; it is that identity, relationship semantics, provenance, temporal context, and quality become increasingly important as knowledge grows.

# Durable ideas

- A graph is useful when relationships themselves carry information that flat document search misses.
- Identity resolution matters: two pages or names may refer to the same real-world entity, and duplicate nodes can fragment retrieval.
- Schema provides consistency but can also become a maintenance burden; open or lightweight schemas are often better early in a personal system.
- Knowledge acquisition can combine human-authored facts, extraction, linking, and inference, but each path introduces different uncertainty.
- Temporal and contextual qualifiers matter because relationships and facts can change.
- Quality requires provenance, contradiction handling, freshness, and explicit uncertainty—not merely more edges.

# Observatory implication

The current Markdown-link design is a reasonable canonical layer. A future graph should be a projection from files and links, not a competing source of truth. Typed edges or graph extraction become worthwhile when measured questions require multi-hop traversal that ordinary links/search fail to answer reliably.

# Project value

- **Value:** High as design grounding; moderate as immediate infrastructure.
- **Lift:** Low to learn the concepts, potentially high to maintain a production graph.
- **Investment:** Delay graph-database work until retrieval evaluations show need.
- **Pitfalls:** Premature ontology design, duplicate entities, stale inferred edges, and losing source context when reducing prose to triples.
- **Confidence:** High in the foundational literature; lower in whether a graph is currently worth deploying for this small corpus.
- **Reassess when:** Multi-hop questions repeatedly fail with Markdown links/catalog search.

# Connections

- [Knowledge graphs](../concepts/knowledge-graphs.md)
- [Context graphs](../concepts/context-graphs.md)
- [GraphRAG](../concepts/graphrag.md)
- [Example project](../projects/example-project.md)
