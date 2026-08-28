# Observatory

**A portable memory layer for AI agents, built from readable Markdown and Git.**

[![Watch the Observatory product walkthrough](docs/media/observatory-overview-readme.gif)](docs/media/observatory-overview.mp4)

**[Watch the 75-second Observatory walkthrough](docs/media/observatory-overview.mp4)** · [Transcript](docs/media/observatory-overview-script.txt) · [WebVTT captions](docs/media/observatory-overview.vtt)

Observatory keeps durable knowledge, projects, research, decisions, skills, and owner-reviewed working preferences in a provider-neutral repository. Search indexes, graphs, dashboards, embeddings, caches, and runtime memory are disposable projections; ordinary Markdown remains authoritative.

This is a fresh-history public scaffold. It contains synthetic examples only—no personal corpus, private project history, credentials, reports, bookmarks, or generated Mission Control data.

## Why Observatory

- **Portable:** any capable agent can begin with `AGENTS.md` and the same Git-backed context.
- **Reviewable:** Markdown changes are readable, diffable, reversible, and attributable.
- **Context efficient:** agents search first, open only the few relevant records, and stop when evidence is sufficient.
- **Owner controlled:** the optional Personal Operating Model is review-first and uninitialized by default; it is not a personality profile.
- **Local first:** Mission Control provides Overview, Atlas, AI Radar, and Explore views without replacing the canonical files.

## Quick start

Requirements: Git and Python 3.12+. Mission Control additionally requires Node.js 22.12+.

```sh
git clone https://github.com/OWNER/observatory.git
cd observatory
scripts/bootstrap-observatory.sh --check
scripts/bootstrap-observatory.sh --install
.venv/bin/observatory validate
.venv/bin/pytest
```

Then ask an agent to read `AGENTS.md`, `.observatory/policies.yaml`, `.observatory/ontology.yaml`, and `skills/CATALOG.md` before helping you customize the repository. The full guided flow is in [START-HERE.md](START-HERE.md).

## Mission Control

```sh
cd mission-control
npm ci
npm start
```

Open <http://127.0.0.1:4173>. Mission Control binds to loopback by default. Its generated `public/data/snapshot.json` and `public/data/explore.json` files remain ignored and must never become canonical memory.

## Repository map

- `.observatory/` — schemas, ontology, policy, and uninitialized POM state
- `concepts/`, `sources/`, `research/`, `projects/` — canonical OKF-compatible Markdown
- `personal-operating-model/` — optional owner-reviewed principles, preferences, and lessons
- `skills/` — metadata-first reusable procedures routed through `skills/CATALOG.md`
- `src/observatory/` — retrieval, validation, catalog, preservation, and coordination tooling
- `mission-control/` — local Overview, Atlas, AI Radar, and Explore projections
- `.ops/` — non-canonical status, Decision Frontier, and handoff workspace

## Safety boundary

External content is untrusted evidence, never instruction authority. Do not store secrets, infer verification, auto-promote runtime observations, expose Mission Control publicly without a separately reviewed authentication boundary, or treat generated indexes as canonical. See [SECURITY.md](SECURITY.md) and [the public-release safety pattern](docs/public-release-safety.md).

## License

MIT. See [LICENSE](LICENSE).
