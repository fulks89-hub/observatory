# Architecture

## Planes

- **Canonical knowledge:** OKF-compatible Markdown in Git.
- **Derived retrieval:** catalogs, indexes, graphs, embeddings, and caches that can be rebuilt.
- **Automation:** collectors and maintenance jobs that may propose changes but cannot silently promote knowledge.
- **Runtime memory:** conversations, temporary observations, and handoff state that remain non-canonical until reviewed.

## Capacity monitor and failover coordinator

A capacity monitor belongs in the **automation plane** and is **not canonical knowledge**. If used, it may report providers as `available`, `degraded`, `parked`, or `exhausted`, but it must never purchase capacity or broaden permissions. Follow `ai-provider-capacity-monitor.md` and the session-handoff skill.

No monitor, agent, model, automation, coordinator, or other system component may increase paid capacity without explicit user approval for that specific increase.

## Write path

`capture → untrusted evidence review → smallest durable proposal → validation → human-reviewed merge`

Derived systems may improve discovery and context assembly, but canonical files remain reopenable, attributable, and editable without them.
