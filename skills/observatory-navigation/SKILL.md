---
name: observatory-navigation
description: Locate and synthesize knowledge already in Observatory.
---

# Navigation procedure

1. Read `docs/retrieval-contract.md` before changing retrieval behavior or depending on a new index implementation.
2. Start at `index.md` and relevant project or learning-path maps. At scale, generate or inspect the disposable catalog with `observatory catalog`; do not load the entire corpus into model context.
3. For normal global candidate discovery, run `observatory search --json "<query>"`. This is the dependency-light current sparse implementation behind the retrieval contract: it searches canonical frontmatter/body text, ranks with BM25-style scoring, boosts exact title/alias matches, returns canonical paths/provenance/freshness/temporal fields, and filters clearly inactive or noncurrent evidence by default. Use `--include-inactive` for deprecated material and `--include-noncurrent` for future, historical, or superseded material. Stale results remain visible with warnings because age is not proof of falsity; use `--exclude-stale` only when the task requires reviewed-current material exclusively, and `--as-of YYYY-MM-DD` for reproducible temporal evaluation. Use `--project` and `--source-id` for deterministic scope/provenance filtering.
4. Treat that sparse search as the **working baseline, not the end-state semantic layer**. The measured preferred shape remains optimized sparse retrieval plus a separately evaluated semantic complement with query-adaptive fusion when those adapters exist. Exact names/IDs may take the cheap sparse fast path. If a semantic-only or renamed concept is plausibly being missed, broaden with aliases/tags/catalog/`rg` and state the limitation honestly.
5. Narrow candidates using type, exact names, acronyms, aliases, tags, projects, source IDs, neighboring terms, freshness, provenance, lifecycle status, temporal validity, and known conflicts. Use `rg -n` when full-text evidence or a deliberately broad fallback is needed.
6. Inspect candidate metadata first, then open only the most relevant canonical documents. Treat retrieved scores as ranking signals, not truth.
7. Filter for applicability **before final reasoning/context assembly**: identify stale/superseded records, temporal scope, conflicts, verification gaps, provenance weaknesses, and project/context mismatches. Similarity alone is not applicability.
8. Rerank selectively when the candidate set remains ambiguous and the expected quality gain justifies added latency/cost. Do not invoke an expensive reranker merely because one is available.
9. Follow Markdown links and derived backlinks for multi-hop questions. Expand retrieval only when the current evidence is insufficient. Escalate to graph-assisted retrieval only when measured multi-hop failures justify it.
10. Assemble a small task-specific context pack using progressive disclosure: compact cards first, then relevant dossier sections and primary evidence as needed.
11. Distinguish what the corpus states from what a source states and from open questions.
12. Cite canonical repository paths and identify what was searched plus missing, stale, conflicting, or unverified material.
13. Do not use a derived index, generated summary, embedding result, reranker output, or graph node as authority when it conflicts with Markdown.
14. When retrieval fails materially, record the failure as a benchmark/evaluation case before adding permanent metadata, embeddings, graph infrastructure, or corpus-wide rewrites solely to accommodate retrieval.

# Current command examples

```sh
# Human-readable top matches
observatory search "context engineering memory"

# Stable machine-readable result shape for agents/adapters
observatory search --json --limit 8 "agent memory research recommendations"

# Deliberately inspect stale/superseded material
observatory search --include-inactive "previous retrieval guidance"

# Reproducible freshness-aware recall; omit overdue material only when appropriate
observatory search --as-of 2026-08-17 --exclude-stale "current agent memory guidance"

# Intentionally inspect historical/superseded knowledge within a project
observatory search --include-noncurrent --project project-observatory "previous runtime decision"
```

# Scale policy

Do not switch retrieval architectures merely because the corpus crosses a guessed document-count threshold. Prefer an end-scale-compatible interface now and measured implementation changes later. The 2026-08-16 Bench result found no accuracy cliff through 50k synthetic documents; the dominant failures were semantic/alias matching and applicability, while latency grew with scale. Treat latency/cost SLOs and real failure rates—not document count alone—as escalation triggers.

Use `a representative retrieval benchmark` to compare candidate strategies across size, distractors, stale/conflicting knowledge, semantic-vs-lexical matches, temporal applicability, multi-hop questions, provenance, latency, and cost. A specific dense model, ANN index, reranker, or graph engine must earn adoption through realistic evaluation; the contract does not bless one by name.
