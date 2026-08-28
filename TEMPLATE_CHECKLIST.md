# Template checklist

- [ ] Run `$onboard-observatory`; choose greenfield setup or approve a read-only inventory of exact existing knowledge/project locations.
- [ ] Review the proposed migration mapping and exclusions before allowing any staged copy.
- [ ] Interview for AI Radar projects, people, organizations, tools, repositories, sources, core ideas, and explicit noise exclusions.
- [ ] Rename the repository and customize `.observatory/policies.yaml`.
- [ ] Replace `projects/example-project.md` and update `index.md`.
- [ ] Choose repository visibility and add an appropriate license.
- [ ] Configure branch protection and required CI checks.
- [ ] Keep secrets in a dedicated secret store, never in Markdown or `.env` commits.
- [ ] Review seed cards and remove examples you do not want.
- [ ] Customize `mission-control/config/projects.json` or remove Mission Control if it is not wanted.
- [ ] Run `observatory validate`, `pytest`, and `observatory catalog` before the first push.
