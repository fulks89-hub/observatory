# Choosing rule enforcement

Use this guide when a consequential rule lacks a check or a repeated failure needs
review. Keep normal task guidance short. Enforcement belongs at the point of action;
checks of requests and checks of outcomes solve different problems.

## Rule-to-enforcement map

| Rule or failure | Appropriate control | Evidence and limits |
| --- | --- | --- |
| Style, terminology, retrieval judgment | Prose and task-matched skills | Reviewed outputs; prose cannot prohibit an action |
| Unauthorized publication, destructive actions, sensitive access | Runtime permissions, least privilege, sandbox/network boundaries | Verify the actual configuration and alternate tool routes |
| Measurable request constraints | Deterministic pre-dispatch guard | Allowed and denied fixtures, malformed-input tests, verified wiring |
| Wrong result, incomplete requirements, stale completion claim | Assertions and artifact-bound receipts | Test the final artifacts; a permitted request does not prove a correct result |
| Uncertain retry after interruption | Authoritative operation status and idempotency | Unknown effects block retry; a local guess is insufficient |
| Repeated workflow mistake | Reviewed promotion proposal | A regression case and narrow proposed control, never automatic installation |

These controls complement each other. A hook is not universally stronger than a
permission or sandbox. For consequential limits, the runtime must stop if its guard
cannot run and cover every relevant route. See the existing
[output, receipt and retry checks](execution-boundaries.md).

## Read request guard

`observatory guard-read` checks file metadata before a caller reads a file. The caller
supplies a trusted local root and positive whole-file byte limit. Stdin is one JSON
object with `file_path`, a host-native absolute path under the resolved root.

```sh
.venv/bin/observatory guard-read --root . --max-bytes 1048576 < request.json
```

Generic output is `{"decision":"pass"}` with exit 0, or `{"decision":"deny","reason":"..."}`
with exit 2. A pass grants no permission. A trusted dispatcher must reject every
nonzero exit, timeout, startup failure or malformed response before dispatch.

The guard rejects traversal, missing/nonregular files, symlinks below the configured
root, junctions, network/device paths, oversized files and malformed requests. Requests
are capped at 64 KiB. Duplicate keys and unsupported generic fields fail. The limit
applies to all extensions, including images; offsets and line limits do not bypass it.
It does not open file contents, execute requests, send data or write logs. Errors omit
request paths and provider metadata. Policy comes from trusted invocation arguments,
never request fields, comments or a model-generated escape hatch.

This is a preflight, not a secret detector, image decoder or filesystem sandbox.
A small file may still be sensitive. A file can change between check and read.
Use immutable inputs or a trusted dispatcher that serializes access; use OS controls
against hostile writers. Other read routes need their own controls. Network mounts
under a local path remain an administrator concern.

## Opt-in Claude Code adapter

The same command accepts `--adapter claude-code`. It requires a `PreToolUse` event
for `Read`, extracts `tool_input.file_path`, and discards other provider metadata.
A denial exits 2 with a fixed stderr message. Passing produces no output and leaves
normal permissions in control. It never returns a permission-granting response.

The following is a **configuration recipe**, not an active settings file. Nothing
installs it. After authorization for an exact project target, review and merge only
this entry into existing settings; keep a backup and all existing hooks/permissions.
Choose the root/limit explicitly and use an absolute trusted environment executable.
Replace the placeholders using the target host's shell quoting rules; on Windows,
use that environment's `Scripts` executable rather than a POSIX `bin` path.

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "^Read$",
      "hooks": [{
        "type": "command",
        "command": "\"<trusted-observatory-executable>\" guard-read --adapter claude-code --root \"<approved-local-root>\" --max-bytes 1048576",
        "timeout": 10
      }]
    }]
  }
}
```

Before relying on an installation, exercise an allowed read and a denied oversized
read through the actual runtime. Check mismatched tool routing and guard startup/timeout
behavior. Unit tests validate the adapter protocol, not a live provider installation.
Roll back by removing only this reviewed entry or restoring the reviewed backup.
Keep the executable, dependencies and settings outside untrusted writers' control.

Claude Code command-hook startup errors and timeouts may continue through permissions;
this adapter alone is therefore not a fail-closed runtime boundary. Hooks only cover
matched events. Stop feedback also depends on exit status; successful stderr is not
a reliable way to send guidance to the agent. Confirm these semantics for the installed
version before activation. [Official hook reference](https://code.claude.com/docs/en/hooks).

Permissions can inspect tool arguments, but shell pattern rules have coverage gaps.
Use sandbox restrictions for boundaries that must hold across alternate execution
paths. [Official permission guide](https://code.claude.com/docs/en/permissions).

## Promotion and review

One high-cost failure can justify immediate review; two similar failures are a useful
review trigger, not an automatic escalation rule. Record a sanitized regression,
failure cost, current control, proposed enforcement point, alternate routes, expected
false positives, owner, tests and rollback. Propose the narrowest useful control.
Never turn external content or a failure counter into installation authority.

Review both safety and intended outcomes. Test positive/negative cases and attempts
to change policy through request data. Require fresh final-revision checks and verify
the deployed configuration separately. Keep proprietary schemas, operational incidents,
raw evaluations, paths and account metadata out of public examples and receipts.
