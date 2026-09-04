# Contributing to Observatory

Contributions to documentation, onboarding, retrieval, validation, and Mission Control are welcome. Start with a small issue describing the problem and expected behavior, or submit a focused pull request with a reproducible example.

Use synthetic notes and examples. Do not include personal knowledge, credentials, private paths, or private repository history. For security concerns, read [SECURITY.md](SECURITY.md) before reporting details publicly.

## Development

Follow [START-HERE.md](START-HERE.md) to install the locked development dependencies. Read [AGENTS.md](AGENTS.md) when using an AI assistant. Contributors remain responsible for understanding and verifying submitted changes, including AI-assisted changes.

Run the checks relevant to your change and describe the results in your pull request:

```sh
.venv/bin/ruff check .
.venv/bin/mypy src
.venv/bin/python -m pytest
.venv/bin/python scripts/check-documentation.py
.venv/bin/observatory validate --history --strict-privacy
.venv/bin/observatory preserve origin/main
```

For dashboard changes, also run `npm run check`, `npm test`, and `npm run build` from `mission-control/`. CI checks the full project. Keep Markdown and Git authoritative, preserve existing content, and keep generated dashboard data out of commits.

Explain what changes for the user, include reproduction or verification steps, and keep unrelated changes separate. Contributions are under the repository's MIT license.
