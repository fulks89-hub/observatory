---
id: concept-graphrag
type: Concept
title: GraphRAG
description: Retrieval-augmented generation that uses graph structure alongside text retrieval.
tags: [ai, retrieval, graphs]
sources: []
generated: { by: openai-codex/gpt-5.6-sol, at: 2026-08-15T00:00:00Z }
status: draft
---

# TL;DR

GraphRAG uses relationships and neighborhoods to extend ordinary [RAG](retrieval-augmented-generation.md), potentially supporting multi-hop and whole-corpus synthesis.

# Why it matters

Observatory's Markdown [knowledge graph](knowledge-graphs.md) can later feed GraphRAG without making a particular graph or vector engine canonical.

# Open questions

- Which query failures demonstrate that a GraphRAG layer is necessary?
- How should answers return exact supporting Markdown/source paths?
