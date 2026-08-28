# Context budget contract

Observatory is a canonical knowledge repository, not a prompt to preload. The operating rule is: **always consult, never indiscriminately inject**.

This contract governs how agents turn durable Observatory knowledge into disposable working context. It complements the [retrieval contract](retrieval-contract.md), [runtime memory contract](runtime-memory-contract.md), and [agent evaluation protocol](agent-evaluations.md).

## Why this exists

Large context windows do not guarantee reliable use of every token. Long-context studies report sensitivity to evidence position, degradation as distractors and task complexity increase, and material gaps between advertised and effective context.[^lost-middle][^ruler] LongMemEval found that reading an entire interaction history could perform substantially worse than reading oracle evidence, while its better memory designs separated indexing, retrieval, and reading.[^longmemeval]

Retrieval is not universally superior either. A 2024 comparison found that sufficiently resourced long-context reading could outperform RAG on average, while RAG retained a large cost advantage; its hybrid router preserved most long-context performance at lower cost.[^rag-vs-long-context] The correct policy is therefore query-adaptive and measured, not “always retrieve everything” or “always send everything.”

## Mandatory preflight

For ordinary tasks:

1. Form a short task-specific query from the current request.
2. Run `observatory search --json --limit 5 "<task terms>"`.
3. Inspect result metadata: title, type, description, project, provenance, freshness, applicability, conflicts, and canonical path.
4. Open only the strongest applicable card or project map first.
5. Expand to another card, a relevant dossier section, a primary source, or linked neighbors only when the current evidence is insufficient.
6. Stop expanding when the answer or implementation is adequately grounded.

The search JSON is intentionally metadata-only. Full Markdown bodies do not enter the initial candidate response. Five is a conservative default candidate count, not a universal truth; expand explicitly when recall would otherwise be inadequate.

## Progressive context ladder

Use the smallest layer that can answer the task:

1. repository instructions and current user request;
2. search/catalog metadata;
3. one compact Project, Concept, or Source card;
4. the relevant section of a ResearchDossier;
5. primary evidence needed to verify a material claim;
6. additional linked or conflicting records;
7. broad or whole-corpus review only when the task explicitly requires corpus-wide analysis, migration, maintenance, or preservation checking.

Do not open every search result merely because it ranked. Do not load a whole dossier when one section answers the question. Do not turn generated catalogs, Atlas nodes, embeddings, runtime summaries, or search output into authority.

## Assembly rules

- Keep authoritative instructions and the current task easy to distinguish from retrieved evidence.
- Prefer current, project-applicable, attributable evidence over similarity alone.
- Put the highest-value evidence early and restate decisive constraints near the point of action; relevant information can be harder for models to use when buried in long middle sections.[^lost-middle]
- Preserve canonical paths and source IDs so compressed notes remain reopenable.
- Use extractive notes or compact synthesis before lossy recursive summarization.
- Treat prompt compression as an optional evaluated optimization. LongLLMLingua showed large benchmark-specific token, cost, and latency gains, but those results do not justify silently compressing away provenance or constraints.[^longllmlingua]
- For long-running API workflows, use provider-supported compaction after meaningful milestones when available; do not compact every turn or treat opaque compaction as canonical memory.[^openai-compaction]

## Runtime memory boundary

Conversation history, temporary observations, tool output, caches, and compacted state are disposable working memory. Retain only decisions, corrections, constraints, failures, and handoff state that have durable value. Recall them through the same scoped, provenance-aware process; reflection may propose a durable update but cannot silently promote it.

## Measurement and escalation

Periodic agent evaluations should record candidate count, full canonical paths opened, approximate Observatory input tokens when available, search/end-to-end latency, retrieval recall and precision, stale or wrong-project evidence, answer success, and citation accuracy.

Compare changes against the same representative tasks and corpus commit. Do not claim that a larger model window, embeddings, reranking, graphs, or compression reduced waste without measuring both quality and operational cost. A real miss or repeated bloat event should become a benchmark fixture before changing defaults.

Escalate retrieval only when measured failures justify it: stronger sparse indexing, then a semantic complement, adaptive fusion, applicability filtering, selective reranking, and graph assistance only for remaining multi-hop failures. Preserve a cheap exact-name path.

## Current conclusion

Observatory's architecture is compatible with token-efficient use because canonical storage and working context are separated, search is metadata-first, candidate count is bounded, detailed layers are opened progressively, and derived context is disposable. It cannot guarantee zero overhead or zero model degradation. The safeguards are effective only if agents follow this contract and the system continues to measure real tasks.

[^lost-middle]: [Liu et al., “Lost in the Middle,” TACL 2024](https://aclanthology.org/2024.tacl-1.9/)
[^ruler]: [Hsieh et al., “RULER,” COLM 2024](https://arxiv.org/abs/2404.06654)
[^longmemeval]: [Wu et al., “LongMemEval,” ICLR 2025](https://arxiv.org/abs/2410.10813)
[^rag-vs-long-context]: [Li et al., “Retrieval Augmented Generation or Long-Context LLMs?,” EMNLP 2024](https://aclanthology.org/2024.emnlp-industry.66/)
[^longllmlingua]: [Jiang et al., “LongLLMLingua,” ACL 2024](https://aclanthology.org/2024.acl-long.91/)
[^openai-compaction]: [Official OpenAI model guidance — compaction](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-5.2#4-compaction-extending-effective-context)
