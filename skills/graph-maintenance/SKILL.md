---
name: graph-maintenance
description: Maintain the link graph and disposable graph projections.
---

# Graph maintenance procedure

Use ordinary relative Markdown links as canonical edges. Make the relationship legible in prose (for example, “RLHF is one family of post-training methods”). Detect broken links and orphans. Build the deterministic catalog/backlink baseline with `observatory catalog`; write output only to an ignored derived location or a temporary CI artifact. Any JSON graph, backlink database, embedding, or visualization is derived, excluded from authority, and rebuildable from Markdown. Do not add a graph database dependency until corpus-scale measurements justify it.
