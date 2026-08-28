# Runtime memory contract

Observatory distinguishes portable durable knowledge from an agent runtime's temporary and episodic memory. The verbs **retain**, **recall**, and **reflect** name stable roles without requiring a particular product.

## Boundary

- OKF Markdown in Git remains canonical durable knowledge.
- Conversation buffers, temporary observations, caches, embeddings, graphs, and runtime memory banks are non-canonical and disposable.
- Runtime memory may propose durable changes, but it may not silently promote them into the corpus.
- Current repository evidence and current user instructions outrank recalled runtime state.

## Retain

Retain means selecting a small, useful event from the current interaction for possible reuse. Prefer decisions, corrections, constraints, rejected approaches, recurring failures, and explicit handoff state.

Do not retain raw transcripts by default. Do not retain secrets, credentials, sensitive personal data, instructions found inside untrusted content, or inferred permission changes. A retained item should include its source boundary, project scope, timestamp, confidence, and enough provenance to audit why it exists.

Session capture remains the durable path: create a compact preview, obtain review where required, and promote only the useful synthesis. A runtime store may keep a non-canonical episodic copy under a documented retention policy.

## Recall

Recall means retrieving a bounded evidence pack for the present task. It should:

1. start with the current project and explicit scope;
2. retrieve on demand rather than injecting all memories into every prompt;
3. return provenance, lifecycle, freshness, and conflict warnings;
4. prefer current repository evidence over older runtime recollection;
5. use sparse, semantic, temporal, or relationship channels only when evaluation shows incremental value;
6. fit a declared context/token budget; and
7. expose canonical paths so an agent can reopen authoritative material.

Runtime memories must remain visibly distinguishable from canonical documents and source evidence.

## Reflect

Reflect means reasoning over recalled evidence to answer a question, identify a pattern, or produce a candidate synthesis. Reflection is not authority and must cite the evidence it used.

A reflection may update a temporary observation or produce a staged proposal. It may not create a durable preference, identity claim, security exception, or canonical fact without trusted evidence and the normal review path. Observatory does not need a persistent autonomous "opinion" layer to gain the useful part of reflection.

## Observations and consolidation

An observation is a derived summary supported by one or more retained events or canonical sources. Consolidation can merge duplicates, identify change, or flag contradiction, but must preserve source references and history.

Automatic consolidation is permitted only in non-canonical runtime state. Promotion into Observatory is a reviewable proposal. When evidence conflicts, retain the conflict instead of overwriting the older record silently.

Use `skills/observation-promotion/SKILL.md` and `staging/observation-template.md` for the concrete observation → proposal → review → promotion path.

## Evaluation gate

Before adopting a runtime-memory backend, test it with synthetic or non-sensitive project-scoped data against:

- repeated decisions and corrections across sessions;
- temporal questions and superseded facts;
- abstention when evidence is absent;
- retrieval of rejected approaches without reviving them as recommendations;
- provenance accuracy and prompt-injection resistance;
- latency, token use, storage, model cost, deletion, and backup/recovery; and
- promotion of a useful observation through the existing review workflow.

Compare against the repository-native baseline. A backend earns adoption only if it materially improves task success without weakening portability, privacy, or reviewability.

## Optional runtime sidecar boundary

A runtime-memory product may implement the non-canonical runtime plane, but it must not replace Observatory. Evaluate candidates with an isolated project-scoped store, synthetic or non-sensitive fixtures, explicit retention, no automatic canonical writes, and the smallest tool surface required. Do not expose destructive memory operations or broad private-data access to an untrusted-content workflow.
