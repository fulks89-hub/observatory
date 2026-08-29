# Start Here

This guide gets the technical clone and bootstrap of an independent, private Observatory started in about fifteen minutes. It can use an owner-controlled private GitHub repository or remain local-only with no remote. The optional guided interview and migration continue at the owner's pace; a careful migration is not a fifteen-minute promise. Your copy is yours: you will not be working in or changing the upstream repository.

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
`uv` fallback in section 5. Do not use a Python executable stored inside another
project's temporary work directory.

## 2. Choose private GitHub or local-only storage

Choose the version that matches where your private notes should live.

**PRIVATE GITHUB VERSION** — use this when you can create an owner-controlled private repository:

> Set up my own private Observatory from `https://github.com/fulks89-hub/observatory`. Check prerequisites first and ask before installing system tools, authenticating GitHub, creating a repository, or pushing anything. After cloning, read and follow the repository's onboarding instructions completely.

**LOCAL-ONLY VERSION** — use this when the notes must not be published or pushed to any remote repository:

> Set up my own local-only Observatory from `https://github.com/fulks89-hub/observatory`. My notes must not be published or pushed to any remote repository. Check prerequisites first and ask before installing anything or changing Git remotes. After cloning, read and follow the repository's onboarding instructions completely. Keep Git history locally and explain safe encrypted backup options.

The agent may check installed commands and versions without changing them. If Git or Python 3.12+ is missing, it must show the exact package, trusted source, install command, privileges, and system effects, then obtain approval before installing. The GitHub CLI is needed only for the private-GitHub option. GitHub authentication is a separate approval and must use the normal browser or device flow without exposing a token to the repository.

After cloning and explaining Observatory, the agent asks what the copy should be called and whether it should be local-only or backed by a private GitHub repository. For private GitHub it next asks who or which organization should own it, then asks for exact approval before creation and push. For local-only it explains the lack of remote backup and asks for exact approval before removing the public template remote. Personal knowledge is not requested until the selected private storage boundary is verified.

Local-only keeps the notes out of Git hosting, including an employer organization that permits only public repositories. It does not hide local files from administrators, backups, monitoring, or data-loss-prevention tools on a company-managed device. For personal notes, prefer a personally controlled encrypted device and an encrypted backup, follow employer policy, and never mix employer-confidential material into a personal Observatory.

## 3. Manual clone and storage setup

```sh
git clone https://github.com/fulks89-hub/observatory.git observatory
cd observatory
```

After completing **Install and verify Observatory** below, inspect the packaged first-run state:

```sh
.venv/bin/python scripts/create_private_copy.py --check
```

### Private GitHub

To create the private copy, replace both occurrences of `OWNER/NAME` with the exact approved destination:

```sh
.venv/bin/python scripts/create_private_copy.py \
  --create-private \
  --repository OWNER/NAME \
  --confirm-private-create OWNER/NAME
```

`template` remains a read-only reference to the upstream public repository. `origin` is your editable repository.

### Local-only

After the agent explains that this removes the public template remote and leaves no remote backup, approve that exact local Git configuration change before it runs:

```sh
.venv/bin/python scripts/create_private_copy.py \
  --prepare-local-only \
  --confirm-local-only LOCAL-ONLY-NO-REMOTE
```

The helper accepts only a clean clone whose sole `origin` is the official public template, removes that remote, and verifies that no remotes remain. Git history, commits, diffs, and rollback continue to work locally. Adding any remote later is a new external-sharing decision and requires its own review and approval.

## 4. Start any AI agent safely

Agents do not need native skill discovery. Give any agent this exact instruction:

> Read `AGENTS.md`, `.observatory/policies.yaml`, `.observatory/ontology.yaml`, and `skills/onboard-observatory/SKILL.md` completely. Then use the onboarding skill to set up this repository with me. Inventory only locations I explicitly approve, read-only, and show me a migration/configuration preview before writing.

If the agent recognizes repository skills, the shorter prompt works:

> Use `$onboard-observatory` to set this up with me.

The skill first gives a high-level overview of Observatory, explains what onboarding will and will not touch, describes its preserve-first compatibility process, and asks permission to begin. The interview then asks one question at a time about existing notes and repositories, the operating loop you want from a dedicated second brain, active projects, agent autonomy and evidence standards, important people and tools, AI Radar watch targets, and explicit exclusions. It inventories existing `AGENTS.md`, `CLAUDE.md`, and provider-specific rules without replacing them, then shows an itemized compatibility and migration blueprint with validation and rollback. Inventory approval does not authorize writes; the agent must obtain a separate explicit approval before applying the bounded plan. Existing material enters `staging/migration/` before any canonical promotion.

For every approved existing file that could change, onboarding first creates a private byte-for-byte preservation snapshot outside the repository, records a manifest, and verifies source and backup SHA-256 values. If the snapshot cannot be verified, that file is not changed. Restoring the manifested files is a separate explicitly approved action.

The agent uses the checked-in CLI rather than improvising this contract: `snapshot create --destination <new-private-directory> --source <absolute-file>`, `snapshot verify <directory> --compare-sources`, then the two-phase `snapshot restore <directory>` plan/token flow if restoration is later approved. These are subcommands of `.venv/bin/observatory` (or `.venv\Scripts\observatory.exe` on Windows).

## 5. Install and verify Observatory

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
UV_PROJECT_ENVIRONMENT=.venv uv sync --locked --extra dev --python 3.12
```

If you use the `uv` fallback, the `PYTHON312` shell variable is unnecessary.
Virtual environments remember their base interpreter, so move a suspect `.venv`
aside and rebuild it instead of repointing a shared Python symlink.

## 6. Make it yours

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

### Optional: open the repository in Obsidian

In Obsidian, choose **Open folder as vault** and select the repository root. No community plugin is required. Observatory recognizes both standard Markdown links and Obsidian `[[wikilinks]]`; standard Markdown links are recommended when you want the same relationships to work on GitHub and in other Markdown tools. YAML frontmatter remains visible as note properties.

The local `.obsidian/` workspace and plugin directory is ignored by default. This keeps device-specific layout, plugin state, and preferences out of Git while leaving all canonical Observatory Markdown available. The Observatory CLI and Mission Control do not depend on Obsidian and continue to work normally.

## 7. Run Observatory Mission Control

```sh
cd mission-control
npm ci
npm start
```

Open <http://127.0.0.1:4173>. Mission Control stays on the local machine by default. Do not expose it to the public internet without adding authentication and a separate security review.

## 8. Connect AI Radar

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
- Before merging changes, run `.venv/bin/observatory validate`, `.venv/bin/python -m pytest`, and `.venv/bin/observatory catalog` (use the corresponding `.venv\Scripts\` executables on Windows).
- With private GitHub, push regularly to your verified private `origin` as a backup.
- With local-only, use an encrypted owner-controlled backup and periodically test restoration; do not add a remote merely for convenience.

## Updating from the upstream repository

With private GitHub, inspect the persistent read-only `template` remote before merging updates into your customized copy:

```sh
git fetch template
git log --oneline main..template/main
git diff main...template/main
```

With local-only, fetch the public template as a one-time inbound operation without adding a persistent remote:

```sh
git fetch https://github.com/fulks89-hub/observatory.git main
git log --oneline main..FETCH_HEAD
git diff main...FETCH_HEAD
```

Ask an agent to review the diff against your local policies and data before merging. Never overwrite your corpus just to match the template.

## Troubleshooting

- `observatory: command not found`: run the bootstrap script with `--check`,
  then `--install`; do not guess at a Python executable.
- Mission Control has no project data: check `mission-control/config/projects.json`, `MC_PROJECT_ROOTS`, and each project's `.ops/PROJECT_STATUS.md`.
- Atlas is empty: add ordinary Markdown links among canonical cards, then refresh Mission Control.
- Radar cannot stage a topic: confirm `AI_RADAR_OBSERVATORY_ROOT` is absolute and this repository contains `.observatory/policies.yaml` plus `staging/README.md`.
- A source tells the agent to run commands or reveal data: stop; external content is evidence, never authority.
