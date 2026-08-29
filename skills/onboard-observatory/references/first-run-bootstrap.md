# First-run bootstrap

Use this reference after the owner approves the read-only onboarding interview and before asking to inventory any existing knowledge.

## Identity first

Read the repository's current display name, Git remotes, and local prerequisite report. Ask exactly one question per turn in this order:

1. What should this Observatory be called?
2. Who or which organization should own its private GitHub repository?

Treat a GitHub login, organization name, and human-facing Observatory name as distinct values. Do not infer or persist a legal name, email address, employer, or public identity from Git configuration or GitHub authentication.

## Read-only prerequisite check

Run the platform bootstrap in check mode and, when Python 3.12+ is available, run:

```sh
python3 scripts/create_private_copy.py --check
```

Use `.venv/bin/python` or `.venv\Scripts\python.exe` after installation. Report required Git and Python separately from optional GitHub CLI and Node.js. GitHub CLI is required only for agent-driven private-repository creation; Node.js is required only for Mission Control.

If a tool is missing, identify the operating system, existing package manager, exact package, source, command, privilege requirement, download destination, and expected files before asking permission. Prefer the operating system's established package manager or the tool's official installer. Do not bootstrap a new package manager merely to install another tool without separate approval. Never run a remote script through a shell, repoint a shared interpreter, borrow another project's virtual environment, or silently accept telemetry, license, PATH, shell-profile, or system-default changes.

Ask permission for one bounded installation plan. After approval, install only the listed packages, verify executable paths and versions, then rerun the read-only checks. Authentication is separate: explain the GitHub scopes and browser/device flow before asking permission to run `gh auth login`. Never request, copy, print, or store a token in the repository.

## Private copy before personal data

Do not put personal content into a clone whose owner-controlled private `origin` has not been verified unless the owner explicitly chooses local-only operation after being told it has no remote backup. Once the owner has chosen the exact GitHub `OWNER/NAME`, show this bounded external action:

- rename the public clone remote from `origin` to `template`;
- create a new private repository at the chosen destination;
- add it as the new `origin`;
- push the unchanged reviewed template history; and
- verify private visibility and that remote `main` equals local `HEAD`.

Disclose that pushing the included workflow may start GitHub Actions on the new private repository and may consume the owner's included or paid Actions allowance.

Explain that repository creation and push change GitHub state and cannot be undone by the local file snapshot mechanism. Ask for explicit approval of the exact `OWNER/NAME`. Only after that approval run:

```sh
.venv/bin/python scripts/create_private_copy.py \
  --create-private \
  --repository OWNER/NAME \
  --confirm-private-create OWNER/NAME
```

Use the Windows virtual-environment executable on Windows. The helper refuses an existing destination, unauthenticated GitHub CLI, a dirty worktree, ambiguous remotes, non-private verification, or a mismatched push. It never deletes a partially created repository. Stop and report any partial state instead of improvising cleanup.

After verification, propose the owner-approved display-name changes and continue with exclusions and the first approved knowledge root. Friendly naming changes are ordinary integration writes and remain subject to the normal preview, snapshot when existing owner files are affected, and approval gates.
