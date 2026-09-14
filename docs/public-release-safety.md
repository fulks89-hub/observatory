# Safe public release pattern

The personal Observatory and working AIRadar repositories must **not** be made public in place. A visibility change exposes repository history and may expose historical personal data even after the current tree is sanitized. Public distributions should be created as **fresh-history repositories** from reviewed scaffolding only.

## Public Observatory

The public repository may contain:

- provider-neutral `AGENTS.md` and policy scaffolding;
- blank/generic canonical folders and example records;
- the Personal Operating Model schema, interview skill, and an uninitialized/empty POM;
- `skills/` and `skills/CATALOG.md` with reviewed reusable procedures;
- Observatory CLI/corpus/retrieval/validation code;
- Mission Control, Atlas, and Explore source code;
- generic Mission Control seed/demo data;
- public-safe documentation and demo media.

It must not contain:

- the owner's canonical personal corpus;
- personal POM records;
- real project status/handoffs;
- personal watchlists or saved posts;
- private AI Radar reports;
- local paths, account identifiers, OAuth data, credentials, tokens, or billing/account details;
- copied Git history from the personal repository.

## Public AIRadar

Publish AIRadar as a separate fresh-history scaffold containing collectors, ranking/reporting logic, dashboard source, example configuration, and synthetic/example reports only. Keep owner Share Sheet captures, X bookmarks, private reports, OAuth material, and personal watchlists out of both the working tree and history.

## Safest practical GitHub permissions

For a repository intended to be publicly cloneable but not directly editable by other people:

1. Set repository visibility to **public**.
2. Do not grant outside users `write`, `maintain`, or `admin` access.
3. Protect the default branch (`main`) with a ruleset/branch protection rule.
4. Require pull requests before changes reach `main`.
5. Require the repository's validation checks to pass before merge.
6. Block force pushes and branch deletion for `main`.
7. Keep GitHub Actions default token permissions read-only; grant narrower write permissions only to a workflow that demonstrably needs them.
8. Do not expose repository or environment secrets to pull-request workflows from untrusted forks.
9. Prefer owner-only merges. Public users may fork/clone and propose pull requests, but proposal authority is not write authority.
10. Enable secret scanning/dependency alerts where the account/repository supports them.
11. Enable private vulnerability reporting and document the Security-tab route without publishing a personal email address.
12. Pin every GitHub Action to a full commit SHA and require locked dependency installation.

A public repository cannot prevent other people from creating their own forks or proposing changes, but they cannot modify the canonical repository without an explicitly granted write path or an accepted merge.

## Mission Control public/template boundary

Mission Control source can be public. Personal Mission Control **data** cannot.

The public scaffold must ship generic `config/projects.json` and `config/seed.json`. Generated `public/data/snapshot.json` and `public/data/explore.json` remain ignored. In a private personal installation, `MC_READ_ONLY=1` must fail closed: Explore hides personal index/resource/rule/POM details unless a later explicit, separately reviewed sharing policy authorizes them.

## Publication gate

Before creating either public repository, run a release audit over the exact exported directory and the new Git history:

- search for names, emails, usernames, local filesystem paths, account IDs, project names, employer/customer names, personal source URLs, X bookmarks, private reports, secrets, API keys, tokens, OAuth values, `.env` files, private keys, and known personal identifiers;
- inspect all tracked JSON/YAML/Markdown fixtures and examples;
- verify ignored/generated data is absent from `git ls-files`;
- create the public repo from an empty/new repository so its first commit contains only the sanitized scaffold;
- inspect the resulting public GitHub tree after push before announcing it.

Do not solve a failed privacy audit by deleting the file in a later public commit. Fix the export before the first public commit or recreate the public repository with clean history.

## Updating an existing public release

Review reusable code, tests, procedures and blank templates against the public base.
Transfer only an explicit reviewed file list into a branch whose history descends from
the public repository. Never merge, cherry-pick, push or attach private history, private
review notes, raw evaluations, personal session IDs, local paths or source identifiers.
Keep personal corpus and operational records out of the public working tree entirely.

Preserve the public starter's onboarding, uninitialized POM, synthetic dashboard seeds,
ignored generated data, documentation checks, and strict current-tree/history privacy
validation. A private repository's passing checks do not validate a public export.
Run the complete public gates on the exact exported revision before publication.

Maintain a dated capability table in `docs/releases/` for each enhancement update:
what shipped, what remains a separate public component, and what was intentionally
excluded. Public release notes must explain capabilities without revealing private
source records. Check this table during future enhancement work to catch drift; this
is a review step, not an automatic private-to-public sync or publishing permission.
