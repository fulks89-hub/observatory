# Template checklist

- [ ] Run `$onboard-observatory`; choose greenfield setup or approve a read-only inventory of exact existing knowledge/project locations.
- [ ] Review the proposed migration mapping and exclusions before allowing any staged copy.
- [ ] Approve the exact existing files and private local destination for the preservation snapshot before any integration write.
- [ ] Verify that the snapshot manifest records byte-for-byte copies and independently matching SHA-256 values; keep the snapshot and manifest outside Git and shared storage.
- [ ] Treat approval of the snapshot, approval of the bounded integration, and approval of any later restoration as three separate decisions.
- [ ] Interview for AI Radar projects, people, organizations, tools, repositories, sources, core ideas, and explicit noise exclusions.
- [ ] Rename the repository and customize `.observatory/policies.yaml`.
- [ ] Replace `projects/example-project.md` and update `index.md`.
- [ ] Choose repository visibility and add an appropriate license.
- [ ] Configure branch protection and required CI checks.
- [ ] Keep secrets in a dedicated secret store, never in Markdown or `.env` commits.
- [ ] Review seed cards and remove examples you do not want.
- [ ] Customize `mission-control/config/projects.json` or remove Mission Control if it is not wanted.
- [ ] Run `.venv/bin/observatory validate`, `.venv/bin/python -m pytest`, and `.venv/bin/observatory catalog` before the first push (use `.venv\Scripts\` on Windows).
