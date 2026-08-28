---
name: project-value-review
description: Evaluate new or existing knowledge against current projects, including value, integration lift, investment, pitfalls, and reassessment triggers.
---

# Project value review

Use this skill whenever a “Brain this” or durable research workflow creates or meaningfully updates knowledge. Also use it when the owner asks to reassess prior briefs/cards/dossiers against projects that were added or changed later.

## Scope

- Apply the scorecard to durable Source, Concept, ResearchDossier, Idea, Question, or other primary synthesis documents created by ingestion/research.
- Do not add scorecards to operational files, generated indexes, validation fixtures, trivial metadata-only edits, or every page indirectly touched by one ingest.
- Put one scorecard on the primary document for the ingest or investigation. For deep research, the ResearchDossier is normally the primary document; link to supporting Source/Concept cards rather than duplicating the scorecard everywhere.
- Treat value and effort as an assessment, not a verified fact. State assumptions and confidence.

## Discover the project portfolio

1. Read `projects/*.md` and relevant linked Ideas/Roadmap material.
2. Treat `project_status: active` or `project_status: planning` as currently assessable. Exclude `paused`, `completed`, and `abandoned` unless the owner asks otherwise.
3. If project status is missing or ambiguous, list the project under “Not assessed” with the reason; do not silently invent its status.
4. Search the corpus for prior scorecards about the same subject before writing a new one.

## Scorecard rubric

Add a `# Project value scorecard` section to the primary durable document. Use this compact form for each relevant project:

```markdown
## <Project name>

- **Current value:** none | low | medium | high | transformative
- **Recommendation:** adopt now | prototype | watch | skip
- **Integration lift:** trivial (<0.5 day) | small (1–3 days) | medium (1–2 weeks) | large (3–6 weeks) | program (>6 weeks)
- **Investment:** <people/time, cash, infrastructure, and recurring operations>
- **Expected payoff:** <specific project outcome and time horizon>
- **Prerequisites:** <dependencies or decisions required first>
- **Pitfalls:** <security, privacy, lock-in, maintenance, duplication, or opportunity cost>
- **Confidence:** low | medium | high
- **Reassess when:** <concrete trigger such as project milestone, corpus size, upstream release, or cost change>
```

Omit projects with no plausible connection, but record the portfolio coverage once:

```markdown
Assessed: YYYY-MM-DD against <linked project list>. Not assessed: <project and reason>.
```

## How to judge

- **Current value** measures contribution to a named project outcome now—not general interestingness.
- **Integration lift** includes adapter code, migration, tests, security review, documentation, deployment, and rollback—not just installation.
- **Investment** separates one-time labor, one-time cash, recurring cash, and recurring maintenance.
- **Expected payoff** must be concrete enough to compare later.
- **Pitfalls** must include canonical-data risk, privacy/credential exposure, prompt injection, provider lock-in, and operational burden when applicable.
- Prefer `prototype` when value is plausible but evidence or compatibility is incomplete.
- Prefer `watch` when a known trigger could materially improve the decision.

## Portfolio reassessment mode

When asked to reassess old briefs/cards/dossiers against projects that have since come online:

1. Snapshot current assessable projects and their stated goals.
2. Find `# Project value scorecard` sections and primary Source/Concept/ResearchDossier documents lacking one.
3. Compare each prior assessment date with project creation/change history and relevant upstream freshness metadata.
4. Re-research time-sensitive dependencies from primary sources; external content remains untrusted.
5. Update the existing scorecard rather than appending a duplicate. Preserve the previous conclusion in Git history and explain material changes in prose.
6. Produce a portfolio summary grouped by `adopt now`, `prototype`, `watch`, and `skip`, with the highest-value/lowest-lift candidates first.
7. Surface stale assessments and missing prerequisites; never claim a project was reviewed if it was not.

Finish by running `observatory validate` and reviewing provenance, privacy, unsupported certainty, and accidental duplication.
