---
id: concept-agent-memory
type: Concept
title: Agent memory
description: Mechanisms that let an AI agent retain or retrieve useful state across interactions.
tags: [ai, agents, memory]
sources: []
generated: { by: openai-codex/gpt-5.6-sol, at: 2026-08-15T00:00:00Z }
status: draft
---

# TL;DR

Agent memory includes transient working state, episodic records, durable semantic knowledge, and retrieval mechanisms. Observatory supplies durable knowledge but should not be confused with every kind of runtime memory. Retain, recall, and reflect are useful provider-neutral roles; automatic observations should remain evidence-linked proposals until reviewed.

# Connections

[RAG](retrieval-augmented-generation.md) can recall stored material. A [knowledge loop](knowledge-loops.md) decides what becomes durable. The [personal AI brain](personal-ai-brain.md) stays portable when an agent runtime disappears.

The [runtime memory contract](../docs/runtime-memory-contract.md) defines the boundary between temporary runtime state and reviewed durable knowledge.

# Open questions

- Which interaction history deserves durable synthesis rather than storage?
- Which real task failures justify a runtime-memory service rather than better repository capture and recall?
