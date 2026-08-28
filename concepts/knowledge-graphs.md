---
id: concept-knowledge-graphs
type: Concept
title: Knowledge graphs
description: Entities and meaningful relationships represented as a traversable graph.
tags: [knowledge-systems, graphs]
sources: []
generated: { by: openai-codex/gpt-5.6-sol, at: 2026-08-15T00:00:00Z }
status: draft
---

# TL;DR

A knowledge graph represents subjects as nodes and relationships as edges. Observatory starts with Markdown pages and contextual links rather than a canonical graph database.

# Core ideas

Link context matters: “A technique belongs to a broader method family” says more than an unlabeled edge. A [context graph](context-graphs.md) additionally foregrounds who asserted a relationship, when, from which source, and with what trust/freshness. [GraphRAG](graphrag.md) can later traverse a disposable projection.

# Open questions

- When will corpus size make an explicit typed-edge projection worthwhile?
