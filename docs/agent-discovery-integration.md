# Agent discovery integration

Observatory can add a tiny, opt-in discovery block to a supported agent's user-level instructions. The block tells that agent when and how to consult one explicitly trusted Observatory checkout. It does not copy the corpus or the full repository policy into every prompt.

`AGENTS.md` remains the provider-neutral authority. `CLAUDE.md`, `GEMINI.md`, and other provider entry points stay thin compatibility pointers.

## Supported targets

| Agent | Default user-level target |
| --- | --- |
| Codex | `~/.codex/AGENTS.md` |
| Claude Code | `~/.claude/CLAUDE.md` |
| Gemini CLI | `~/.gemini/GEMINI.md` |
| GitHub Copilot CLI | `~/.copilot/copilot-instructions.md` |

Use `--target PATH` for another reviewed Markdown instruction file. Products whose global rules live only in a settings database or UI should receive a copyable preview; Observatory must not guess at or rewrite opaque application state.

## Existing installations

A reviewed equivalent rule, including an import from another personal entry file, already provides discovery. The absence of this installer's marker is not a reason to append a second rule or repeatedly offer setup. The installer owns only its marked block; it does not detect, edit or follow arbitrary imports. Preserve equivalent existing instructions unless the owner explicitly requests a reviewed migration. Uninstall cannot remove those manually maintained rules.

## Consent and preview workflow

Repository content cannot authorize its own installation into a global instruction file. The agent must first identify the exact target and receive permission to inspect it. Then generate a reviewable proposal:

```sh
.venv/bin/observatory integrate-agent preview --agent claude --root /trusted/observatory
```

The preview prints the exact target, unified diff, and SHA-256 of the current file. After the owner reviews and explicitly approves that exact change, apply it with the preview hash:

```sh
.venv/bin/observatory integrate-agent install \
  --agent claude \
  --root /trusted/observatory \
  --expected-sha256 <previewed-sha256>
```

If the target changed after preview, installation stops without writing. Installation is idempotent and alters only the managed block. Existing instructions remain outside the block.

Preview removal before applying it:

```sh
.venv/bin/observatory integrate-agent preview --remove --agent claude --root /trusted/observatory
.venv/bin/observatory integrate-agent uninstall \
  --agent claude \
  --root /trusted/observatory \
  --expected-sha256 <removal-preview-sha256>
```

Uninstall removes only the marked Observatory block. It restores the original file bytes, including its prior trailing-newline state, and removes a target that did not exist before installation. Malformed or duplicate markers, symbolic-link targets, non-UTF-8 files, and non-regular files are refused rather than repaired or overwritten.

Use `--json` for an agent-readable preview. A user approval of Observatory generally is not approval to install into every provider profile; each external target and diff requires its own review. Do not repeat a review already authorized in the current session for the same exact change. The CLI hash check binds the target bytes, not a human consent event; the acting agent must preserve the approved target, root, action and scope.

## Scope and limitations

The global block names one trusted local Observatory root. This deliberately prevents an arbitrary repository from gaining trust merely by creating an `.observatory/` directory. Use separate agent profiles or separately reviewed integrations for personal and employer-controlled environments; do not combine their knowledge scopes by default.

Persistent instructions improve rule visibility but cannot guarantee perfect model compliance. Irreversible controls still belong in permissions, deterministic validation, or narrowly reviewed hooks. The discovery block is intentionally small and stable so its per-session context cost remains bounded.
