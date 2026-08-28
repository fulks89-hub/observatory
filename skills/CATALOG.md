# Observatory Skill Catalog

This is the lightweight routing index for reusable agent procedures in `skills/`. Read this catalog to identify a likely skill, then open only the matching `SKILL.md`. Do not preload the full skill library.

`AGENTS.md` and `.observatory/policies.yaml` remain authoritative. Skills are procedures, not permission sources, and they never override current user/system instructions, consent, security policy, or repository-wide rules.

## Core Observatory skills

| Skill | Use when | Path |
| --- | --- | --- |
| Onboard Observatory | Fresh-clone setup, instruction-safe migration, owner workflow interview, or second-brain adoption | `skills/onboard-observatory/SKILL.md` |
| Observatory Core | Editing canonical OKF knowledge | `skills/observatory-core/SKILL.md` |
| Ingest | Brain/add supplied material into durable knowledge | `skills/ingest/SKILL.md` |
| Research | Research is needed before durable ingest | `skills/research/SKILL.md` |
| Deep Research | Consequential multi-source investigation should be reusable later | `skills/deep-research/SKILL.md` |
| Observatory Navigation | Finding, comparing, or traversing existing knowledge | `skills/observatory-navigation/SKILL.md` |
| Observatory Review | Reviewing staged, stale, disputed, or unverified knowledge | `skills/observatory-review/SKILL.md` |
| Session Capture | Remember/brain a session or repository-wide rule request | `skills/session-capture/SKILL.md` |
| Session Handoff | Long-running work, provider/thread switches, context/capacity constraints, expensive reconstruction | `skills/session-handoff/SKILL.md` |
| Decision Frontier | Large/foggy work needs unresolved decisions and dependencies mapped before linear planning | `skills/decision-frontier/SKILL.md` |
| Observation Promotion | Repeated/corrective observations suggest a durable reviewed pattern | `skills/observation-promotion/SKILL.md` |
| Project Value Review | Assessing how durable knowledge affects active/planning projects | `skills/project-value-review/SKILL.md` |
| Source Verification | Verifying claims or source state | `skills/source-verification/SKILL.md` |
| Maintenance | Corpus cleanup, deduplication, lifecycle repair | `skills/maintenance/SKILL.md` |
| Graph Maintenance | Regenerating or maintaining derived relationship views | `skills/graph-maintenance/SKILL.md` |
| Narrated Progress Recording | Major app handoff or requested narrated demo/walkthrough | `skills/narrated-progress-recording/SKILL.md` |

## Personal Operating Model skills

| Skill | Use when | Path |
| --- | --- | --- |
| Personal Operating Model | Owner-specific decision principles, preferences, or lessons could materially affect a task | `skills/personal-operating-model/SKILL.md` |
| Personal Model Interview | Owner elects to initialize or deepen the Personal Operating Model | `skills/personal-model-interview/SKILL.md` |

## Triggering rules

1. Match the current task against this catalog before opening specialized skills.
2. Prefer the smallest applicable skill set.
3. Load only the matching `SKILL.md` plus explicit dependencies it names.
4. If no listed skill fits, continue under `AGENTS.md`; do not invent a mandatory workflow.
5. A skill's trigger description helps routing but does not outrank current instructions or evidence.
6. Avoid recursive skill loading. A skill may name a dependency; that does not mean every related skill must be loaded.

## Third-party skill packs

Observatory can store or reference external skill packs, including repositories such as `obra/superpowers`. Treat them as **versioned procedural dependencies**, not as a second policy layer.

Preferred layouts:

```text
skills/vendor/<publisher>/<pack>/<skill>/SKILL.md
```

or, when preserving an independently updated checkout is more useful, keep the upstream repository separately and register its canonical source/version here or in a future machine-generated catalog.

For every third-party pack record:

- source repository and upstream publisher;
- pinned commit/tag/version when practical;
- license and required attribution/notices;
- activation mode (`manual`, `task-matched`, or `provider-native`);
- any adapter/compatibility notes;
- review date; and
- known conflicts with Observatory policy or other skills.

Never blindly enable an external pack's bootstrap instructions. Review them first for prompt expansion, mandatory ceremony, tool/permission assumptions, provider-specific behavior, telemetry/network behavior, and conflicts with `AGENTS.md`.

### Superpowers compatibility note

`obra/superpowers` is a composable coding-skill framework and is MIT licensed upstream. Its current `using-superpowers` bootstrap intentionally invokes skills extremely aggressively, even before clarifying questions. That can be useful in a coding runtime but conflicts with Observatory's proportional-process and context-budget philosophy if made repository-global without adaptation.

Therefore a future Superpowers import should be **namespaced and pinned**, with individual useful skills discoverable through this catalog. Its bootstrap should not automatically replace Observatory's task routing unless the owner explicitly chooses that behavior after evaluation.

Upstream: https://github.com/obra/superpowers

## Catalog maintenance

When adding, renaming, or removing a skill, update this catalog in the same change. Keep entries concise enough that reading this file is cheaper than opening several candidate skills. If the skill library grows substantially, replace or supplement this hand-maintained catalog with a generated metadata index derived from each `SKILL.md` frontmatter while keeping the generated index non-authoritative.
