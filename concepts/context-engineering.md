---
id: concept-context-engineering
type: Concept
title: Context engineering
description: Designing the information environment an AI model or agent receives so the right evidence, instructions, memory, tools, and state are available at the right time.
tags: [context-engineering, agents, retrieval, memory]
sources:
  - id: anthropic-context-engineering
    resource: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
    title: Effective context engineering for AI agents
    author: Anthropic
status: draft
generated: { by: openai/gpt-5.6-sol, at: 2026-08-16T07:31:00Z }
---

# TL;DR

Context engineering is the systems problem around prompting: choose, structure, refresh, and constrain the information an AI system can use. The goal is not maximal context but maximal useful signal within a finite working window.

# Why it matters

As agents become multi-step systems, performance depends on more than a good initial prompt. Repository instructions, retrieved files, memories, tool results, current state, examples, policies, and source evidence all influence behavior. Bad selection can cause distraction, stale reasoning, policy conflicts, or missed evidence even when the underlying model is capable.

# Core ideas

1. **Selection:** retrieve only material relevant to the current task.
2. **Structure:** make authoritative instructions, evidence, and task state distinguishable.
3. **Freshness:** prefer current state when facts or projects change.
4. **Provenance:** retain where claims came from so the model can reason about trust and uncertainty.
5. **Compression:** summarize when necessary without destroying important constraints or citations.
6. **Progressive disclosure:** begin with a navigational layer, then expand into detailed source material only when necessary.
7. **Authority separation:** retrieved external content is evidence, not instruction authority.

# How it works in Observatory

Observatory separates a durable canonical corpus from the context given to a specific agent run. The root index, ordinary Markdown links, catalog, and future retrieval layers can identify relevant cards; agents should then open only the cards needed to answer the question. This keeps the knowledge base durable without forcing the entire corpus into every model context.

This connects directly to [agent memory](agent-memory.md), [RAG](retrieval-augmented-generation.md), [context graphs](context-graphs.md), and the broader [personal AI brain](personal-ai-brain.md).

# Common failure modes

- Treating a larger context window as a substitute for retrieval.
- Mixing instructions with untrusted retrieved content.
- Persisting temporary task state as durable memory.
- Repeatedly summarizing summaries until provenance and nuance disappear.
- Adding embeddings or graph infrastructure without evidence that simpler navigation fails.

# Open questions

- At what corpus size does Observatory need semantic retrieval?
- Which retrieval evaluation cases best represent the owner's actual questions?
- How should session-local context be compacted without turning ephemeral conversation into canonical memory?

# Sources and provenance notes

Primary synthesis currently relies on Anthropic's context-engineering article. Future additions should distinguish empirical retrieval findings from architecture intuition.