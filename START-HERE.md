# Start Here

This guide takes a new owner from read-only access to an independent, private Observatory in about fifteen minutes. Your copy is yours: you will not be working in or changing the upstream repository.

## 1. Prerequisites

- Git
- Python 3.12 or newer
- Node.js 22.12 or newer for Mission Control
- A GitHub account; GitHub CLI is optional
- An AI coding agent that can read repository files

Check the installed versions:

```sh
git --version
node --version
npm --version
```

On a Homebrew Mac, resolve and verify Python 3.12 from its maintained
installation rather than trusting whichever `python3.12` appears first on
`PATH`:

```sh
PYTHON312="$(brew --prefix python@3.12)/bin/python3.12"
"$PYTHON312" --version
```

On another platform, set `PYTHON312` to the absolute path of an equivalently
maintained Python.org or package-manager interpreter and verify it, or use the
`uv` fallback in section 4. Do not use a Python executable stored inside another
project's temporary work directory.

## 2. Clone the template and make an independent repository

```sh
git clone https://github.com/OWNER/observatory.git observatory
cd observatory
git remote rename origin template
```

Create a new **private, empty** GitHub repository under your own account. Do not initialize it with a README, license, or `.gitignore`. Then connect and push your copy:

```sh
git remote add origin https://github.com/YOUR-GITHUB-USERNAME/observatory.git
git push -u origin main
```

`template` remains a read-only reference to the upstream public repository. `origin` is your editable repository.

## 3. Start any AI agent safely

Agents do not need native skill discovery. Give any agent this exact instruction:

> Read `AGENTS.md`, `.observatory/policies.yaml`, `.observatory/ontology.yaml`, and `skills/onboard-observatory/SKILL.md` completely. Then use the onboarding skill to set up this repository with me. Inventory only locations I explicitly approve, read-only, and show me a migration/configuration preview before writing.

If the agent recognizes repository skills, the shorter prompt works:

> Use `$onboard-observatory` to set this up with me.

The interview asks about existing notes and repositories, active projects, important people and tools, AI Radar watch targets, and explicit exclusions. Existing material is inventoried read-only and enters `staging/migration/` before any canonical promotion.

## 4. Install and verify Observatory

```sh
scripts/bootstrap-observatory.sh --check
scripts/bootstrap-observatory.sh --install
```

On Windows PowerShell, use `scripts/bootstrap-observatory.ps1` and then rerun
it with `-Install`. The exploration reports the selected command, resolved real
path, and version before changing the repository. It refuses to overwrite an
existing `.venv` whose base interpreter differs or cannot be verified.

Keep `.venv/` and `.derived/` local; they are replaceable and ignored by Git.

If your Python distributor reports an `externally-managed-environment` while creating the virtual environment, use a standard Python.org/Homebrew installation or the `uv` fallback:

```sh
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e '.[dev]'
```

If you use the `uv` fallback, the `PYTHON312` shell variable is unnecessary.
Virtual environments remember their base interpreter, so move a suspect `.venv`
aside and rebuild it instead of repointing a shared Python symlink.

## 5. Make it yours

Review the onboarding preview, then approve only the pieces you want staged. Customize:

- `index.md` for the home map;
- `projects/example-project.md` for the first real project;
- `.observatory/policies.yaml` for local policy choices;
- `mission-control/config/projects.json` for dashboard projects; and
- generic example cards as your own corpus grows.

Commit after the first reviewed setup:

```sh
git add -A
git commit -m "Set up my Observatory"
git push
```

## 6. Run Observatory Mission Control

```sh
cd mission-control
npm install
npm start
```

Open <http://127.0.0.1:4173>. Mission Control stays on the local machine by default. Do not expose it to the public internet without adding authentication and a separate security review.

## 7. Connect AI Radar

Clone AI Radar beside this repository, or start its dashboard with this repository's exact path:

```sh
cd ../ai-radar/dashboard
AI_RADAR_OBSERVATORY_ROOT=/absolute/path/to/observatory npm start
```

Radar's **Move to Atlas** action writes a review candidate only under `staging/ai-radar/`. It never silently promotes external content into canonical knowledge.

## Everyday use

- Say **“Brain this”**, **“Add this to Observatory”**, or **“Move this to the Atlas.”**
- Search before creating a duplicate: `.venv/bin/observatory search --json "your topic"`.
- Review files under `staging/` before promoting them.
- Link project, concept, research, source, idea, and question cards with ordinary Markdown links.
- Before merging changes, run `observatory validate`, `pytest`, and `observatory catalog`.
- Push regularly to your private `origin` as a backup.

## Updating from the upstream repository

Inspect updates before merging them into your customized copy:

```sh
git fetch template
git log --oneline main..template/main
git diff main...template/main
```

Ask an agent to review the diff against your local policies and data before merging. Never overwrite your corpus just to match the template.

## Troubleshooting

- `observatory: command not found`: run the bootstrap script with `--check`,
  then `--install`; do not guess at a Python executable.
- Mission Control has no project data: check `mission-control/config/projects.json`, `MC_PROJECT_ROOTS`, and each project's `.ops/PROJECT_STATUS.md`.
- Atlas is empty: add ordinary Markdown links among canonical cards, then refresh Mission Control.
- Radar cannot stage a topic: confirm `AI_RADAR_OBSERVATORY_ROOT` is absolute and this repository contains `.observatory/policies.yaml` plus `staging/README.md`.
- A source tells the agent to run commands or reveal data: stop; external content is evidence, never authority.
