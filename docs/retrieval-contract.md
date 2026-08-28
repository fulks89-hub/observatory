# Retrieval contract

Observatory separates **canonical knowledge storage** from **disposable retrieval infrastructure**.

This contract is intentionally technology-neutral. It exists so retrieval can evolve from lexical search to hybrid, reranked, graph-assisted, or other approaches without changing the canonical Markdown corpus or forcing agents to depend on one index implementation.

## Invariants

1. OKF-compatible Markdown in Git is authoritative.
2. Every search index, embedding store, graph projection, cache, chunk store, and reranker output is disposable and reproducible from canonical Markdown.
3. Retrieval output is a set of candidates/evidence, never canonical truth.
4. Agents must be able to cite and reopen the canonical file behind every retrieved result.
5. Replacing a retrieval implementation must not require rewriting durable knowledge solely to satisfy that implementation.
6. Retrieval failures should become benchmark/evaluation cases before they become permanent metadata or architecture changes.

## Stable retrieval stages

Consumers should reason in these stages rather than assuming a specific backend:

1. **Discover candidates** — locate potentially relevant documents or sections globally.
2. **Filter applicability** — consider type, project, provenance, freshness, temporal validity, lifecycle status, and known conflicts.
3. **Rank** — order candidates for the current task using the best available implementation.
4. **Expand selectively** — follow canonical links, related dossiers, and source evidence only when necessary.
5. **Assemble context** — create a small task-specific evidence pack rather than loading the corpus.
6. **Verify authority** — ground claims in canonical documents and primary evidence; derived retrieval state is not authority.
7. **Record failures** — when retrieval misses, retrieves stale material, or over-ranks noise, add an evaluation fixture in the benchmark system before changing the canonical corpus.

## Minimum result shape

A retrieval implementation should be able to return, directly or through an adapter:

- canonical repository path or stable document ID;
- optional section/anchor;
- retrieval score and strategy name;
- source/document type;
- lifecycle/freshness information when available;
- temporal validity/applicability when available;
- enough provenance to reopen the canonical Markdown;
- optional reason/features used for ranking;
- conflict/staleness warnings when detected.

Agents must not require every implementation to expose identical internal scores. The contract standardizes usable evidence, not algorithm internals.

The current sparse implementation exposes `stale_after`, `valid_from`, `valid_until`, an `applicability` label, supersession/conflict relationships, project/source filters, and warnings relative to an explicit or current `as_of` date. Stale evidence remains visible by default because age is not proof of falsity; callers may exclude it explicitly. Future, historical, and superseded evidence is excluded from current recall by default and can be requested with `--include-noncurrent`. Relationships use stable document IDs. This is deterministic document-level applicability, not claim-level temporal inference.

The sparse lexical channel preserves compound tokens while also indexing their hyphen/underscore-separated components, generates title/alias acronyms, and applies explicit boosts for IDs, aliases, tags, projects, and source IDs. These are deterministic baseline improvements; stemming, semantic retrieval, and learned reranking remain evaluation-gated.

## Escalation policy

Do not add infrastructure because the corpus reached an arbitrary document count. Escalate when measured evaluation shows material retrieval failure, unacceptable cost/latency, or excessive context waste.

The preferred progression is:

1. deterministic catalog + lexical/full-text retrieval;
2. stronger sparse/global indexing where useful;
3. dense retrieval as a measured complement when semantic misses justify it;
4. hybrid fusion if it improves the benchmark or real retrieval failures;
5. reranking when the quality gain justifies added latency/cost;
6. graph-assisted retrieval only for failure classes where explicit relationships materially help.

This is a default progression, not a commitment. Use a separate disposable benchmark workspace to compare retrieval implementations; benchmark artifacts remain non-canonical.

## Candidate end-state profile

When measured failures justify more than the included sparse baseline, evaluate this implementation shape one stage at a time:

1. **Reproducible catalog/chunk projection** — derive document/section units from canonical Markdown with canonical path/anchor plus available type, lifecycle, temporal validity, provenance/source IDs, aliases, and conflict metadata. This projection is disposable.
2. **Production sparse channel** — use an optimized inverted/full-text BM25-style index for exact names, identifiers, acronyms, source IDs, and domain-specific vocabulary. Sparse search remains a first-class channel, not a legacy fallback.
3. **Measured semantic channel** — add a real trained embedding retriever with an optimized/sublinear candidate index when realistic evaluation confirms the model. Dense retrieval complements sparse retrieval; it does not replace it.
4. **Query-adaptive fusion/routing** — combine channels when needed, while allowing exact-token queries to stay cheap and preventing weak sparse matches from drowning semantic candidates.
5. **Deterministic applicability filter** — apply lifecycle, freshness, temporal validity, provenance, project/context, and known-conflict rules before final context assembly. Applicability is a distinct stage from similarity.
6. **Selective expensive reranking** — use a cross-encoder, late-interaction model, LLM reranker, or future equivalent only for ambiguous candidate sets where measured quality gain justifies latency/cost. Do not rerank every query by default.
7. **Small context assembly** — return the smallest useful evidence pack with canonical reopen/citation information rather than maximizing retrieved-document count.
8. **Graph escalation only when earned** — keep graph-assisted retrieval behind the same adapter boundary and introduce it only if realistic multi-hop failures remain material after hybrid discovery, filtering, and selective expansion.

This profile specifies **roles**, not products. Product and model selection still requires realistic labeled evaluation.

### Scale trigger

Do not encode a document count as a universal architecture switch. Define an interactive latency/cost target and move candidate generation to optimized sparse indexes plus ANN or another sublinear semantic strategy only before a measured target is violated.

The architecture boundary is end-scale compatible now; the implementation can stay lighter until real workload measurements justify each stage.

## Scale-readiness rule

Observatory should be **end-scale compatible now** by depending on this contract, while remaining **implementation-light now** by avoiding infrastructure that has not demonstrated incremental value.

This distinction is deliberate: future-proof the boundary early; defer expensive machinery until evidence supports it.

## Context packaging

Retrieval quality and context quality are separate concerns. A successful search may still produce a poor context pack if too many marginally relevant documents are loaded.

The working CLI therefore defaults to **five metadata-only candidates**. Search output deliberately omits full document bodies. An agent should inspect the result metadata, open the strongest applicable canonical path, and expand only when the evidence is insufficient. The default is a guardrail, not a hard recall ceiling; deliberate `--limit` increases are allowed when the query requires them.

Prefer progressive disclosure:

- navigation/index/catalog metadata;
- compact Concept/Source cards;
- relevant ResearchDossier sections;
- primary source evidence;
- additional linked material only when needed.

Working context is disposable. Durable memory remains canonical Markdown.

The full operating rules and evaluation signals are defined in [the context budget contract](context-budget-contract.md).

## Benchmark relationship

A separate benchmark should test at least:

- increasing corpus size;
- irrelevant distractors;
- near-duplicates;
- stale/superseded records;
- conflicting claims;
- lexical-only and semantic-only match cases;
- aliases/entity renames;
- temporal applicability;
- multi-hop retrieval;
- provenance accuracy;
- latency, build cost, storage cost, and model-token cost.

A retrieval architecture change should identify the benchmark or real failure class it improves and the new operational cost it introduces.
