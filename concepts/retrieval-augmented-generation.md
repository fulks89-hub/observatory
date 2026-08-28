---
id: concept-rag
type: Concept
title: Retrieval-augmented generation
description: Supplying retrieved external knowledge to a model at generation time.
tags: [ai, retrieval, knowledge-systems]
sources: []
generated: { by: openai-codex/gpt-5.6-sol, at: 2026-08-15T00:00:00Z }
status: draft
---

# TL;DR

Retrieval-augmented generation (RAG) retrieves relevant material and places it in model context before an answer is generated. Retrieval can improve grounding, but retrieved chunks remain untrusted evidence.

# Connections

[GraphRAG](graphrag.md) adds graph-guided retrieval. [Agent memory](agent-memory.md) can use RAG, while a [personal AI brain](personal-ai-brain.md) must remain durable independently of its current retrieval index.

# Open questions

- At what corpus size does semantic retrieval outperform filename, full-text, and link traversal here?
