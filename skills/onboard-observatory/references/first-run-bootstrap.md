# First-run bootstrap

Use this reference after the owner approves the read-only onboarding interview and before asking to inventory any existing knowledge.

## Identity first

Read the repository's current display name, Git remotes, and local prerequisite report. Ask exactly one question per turn in this order:

1. What should this Observatory be called?
2. Would you prefer local-only storage or a private GitHub repository?
3. If private GitHub is selected, ask: Who or which organization should own its private GitHub repository?

Treat a GitHub login, organization name, and human-facing Observatory name as distinct values. Do not infer or persist a legal name, email address, employer, or public identity from Git configuration or GitHub authentication.

Explain the storage choice before asking for it. Local-only means no Git remote and no remote backup; private GitHub means a separately created owner-controlled private repository. If the owner mentions an employer or organization that permits only public repositories, do not place personal notes there. Explain that local-only avoids Git-host visibility but does not prevent access by administrators, backups, monitoring, or data-loss-prevention tools on a company-managed device. Recommend a personally controlled encrypted device for personal notes, require compliance with employer policy, and keep employer-confidential material separate.

## Read-only prerequisite check

Run the platform bootstrap in check mode and, when Python 3.12+ is available, run:

```sh
python3 scripts/create_private_copy.py --check
```

Use `.venv/bin/python` or `.venv\Scripts\python.exe` after installation. Report required Git and Python separately from optional GitHub CLI and Node.js. GitHub CLI is required only for agent-driven private-repository creation; Node.js is required only for Mission Control.

If a tool is missing, identify the operating system, existing package manager, exact package, source, command, privilege requirement, download destination, and expected files before asking permission. Prefer the operating system's established package manager or the tool's official installer. Do not bootstrap a new package manager merely to install another tool without separate approval. Never run a remote script through a shell, repoint a shared interpreter, borrow another project's virtual environment, or silently accept telemetry, license, PATH, shell-profile, or system-default changes.

Ask permission for one bounded installation plan. After approval, install only the listed packages, verify executable paths and versions, then rerun the read-only checks. Authentication is separate: explain the GitHub scopes and browser/device flow before asking permission to run `gh auth login`. Never request, copy, print, or store a token in the repository.

## Private storage before personal data

Do not put personal content into the clone until either an owner-controlled private `origin` is verified or local-only operation is established after the owner acknowledges that it has no remote backup.

### Private GitHub

Once the owner has chosen the exact GitHub `OWNER/NAME`, show this bounded external action:

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

### Local-only

Explain that the bounded local action removes the public template remote, so ordinary commits and history remain but no `git push` destination or remote backup exists. Recommend an encrypted owner-controlled backup and a tested restore routine. Ask for explicit approval of the exact remote-removal action. Only after that approval run:

```sh
.venv/bin/python scripts/create_private_copy.py \
  --prepare-local-only \
  --confirm-local-only LOCAL-ONLY-NO-REMOTE
```

Use the Windows virtual-environment executable on Windows. The helper refuses a dirty worktree, a non-template repository, an unexpected remote, or anything other than the official public template as the sole `origin`. It removes that remote and verifies that none remain. Stop on any mismatch instead of removing or rewriting a remote by hand. Adding a remote later is a new external-sharing decision that requires a fresh approval and privacy review.

After verification, propose the owner-approved display-name changes and continue with exclusions and the first approved knowledge root. Local-only is a storage boundary, not permission to inspect unrelated local files.
