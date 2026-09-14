# Execution boundary checks

For authors wiring or troubleshooting workflow checks. Task agents use configured tools
and fresh receipts; this guide is not routine prerequisite reading. Open the relevant
section when a check is missing, rejects output/evidence, or cannot resolve a retry.

Use `observatory enforce` where a workflow consumes structured output, accepts
completion, or decides whether to retry. These provider-neutral checks extend the
existing CLI; they do not install global hooks or change Mission Control/Switchboard.
The root [writing standard](../AGENTS.md#writing-standard) governs prose. There is
no word-count rejection or automatic rewriting of durable knowledge.

## Structured output

```sh
.venv/bin/observatory enforce output response.json --contract contract.json
```

The small **contract dialect** is not JSON Schema. Supported types: object, array,
string, integer, number, boolean, null. An object has `fields`; every named field
is required and extra fields fail. Arrays require `items`. Arrays and strings
accept nonnegative `min`/`max` lengths. Unsupported keywords fail closed.
Example contract: `{"type":"object","fields":{"ready":{"type":"boolean"}}}`.
Duplicate keys, trailing output, non-finite numbers, wrong types and missing fields
fail. A consumer must stop before acting when the command exits nonzero. Semantic
correctness still needs task-specific assertions, including requirement coverage.

## Evidence tied to artifacts

Run the relevant smoke/acceptance command through the check wrapper, then use its
receipt at completion. A smoke check should exercise real output and its contract.
Choose checks proportional to the change; a process starting successfully is not
sufficient evidence for a data contract or business requirement.

```sh
.venv/bin/observatory enforce check --root . --artifact src/observatory/enforcement.py --artifact tests/test_enforcement.py --check enforcement --receipt /tmp/enforcement-new-receipt.json -- .venv/bin/python -m pytest tests/test_enforcement.py
.venv/bin/observatory enforce completion --root . --artifact src/observatory/enforcement.py --artifact tests/test_enforcement.py --check enforcement --receipt /tmp/enforcement-new-receipt.json
```

The receipt must be a new file. The wrapper executes the caller's explicit argument
vector without a shell, with a bounded timeout, and records the actual exit result,
UTC time, command fingerprint and before/after artifact hashes. Output is suppressed;
run a failed check directly when its diagnostic output is needed. Bind **every
relevant source, test, configuration and input file**, not only one changed file.
Changed files, missing evidence, failed checks and a different root/check/scope block
completion. Files must be regular, inside the declared root; final symlinks fail.

A receipt proves only that the named check passed on the listed files under the
trusted runner. It does not prove adequate test coverage, deployment, remote CI,
human review, or an honest runner. Store receipts outside participant write access.
The calling runtime must serialize check/use, recheck immediately before acting,
and use immutable snapshots for hostile concurrent writers. This CLI is not a
sandbox; only run authorized commands in the appropriate execution environment.

## Uncertain operations

```sh
.venv/bin/observatory enforce operation status.json --operation-id example-042 --fingerprint <sha256-of-canonical-request>
```

A trusted adapter supplies fresh status with `operation_id`, `fingerprint` and
`status`. Compute the fingerprint with `enforcement.fingerprint` over the request
including action, destination, scope and artifact identity. Matching `committed`
returns `already_complete`: consume the result without redispatch. Only matching
`confirmed_not_applied` returns `retry_permitted`. Unknown, in-progress, not-found,
failed-with-unknown-effects and identity conflicts block. “Not found” alone may
reflect eventual consistency and is deliberately insufficient.

This decision helper never executes an operation or grants new permission. The
adapter must obtain authoritative state, honor cancellation and retry limits, and
use an atomic idempotency key or transaction at the real destination. A model-written
status file is not authoritative. A stale read followed by an unguarded dispatch
cannot guarantee exactly-once execution.

## Integration and evaluation

The Python functions expose the same checks for trusted adapters; the CLI supplies
machine-readable results and nonzero failure exits. CI uses `scripts/check-with-evidence.py` to run the complete Python suite,
record a new receipt covering tracked and unignored repository files, and reject stale
evidence or a changed file list before accepting the test job. Existing applications need explicit adapter wiring before these
checks can gate their actions; repository prose cannot enforce external services.

Receipts include the resolved local root and may identify private artifacts. Keep them in an external temporary or private directory; do not commit or publish them.
