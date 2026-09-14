# Portable evaluation evidence

Record a stable suite identity and revision, baseline and candidate revisions,
provider/model or harness versions, tool permissions, case IDs and family IDs,
train/holdout membership, frozen prompts/checks, execution mode, and actual results.
Missing output is missing evidence; never substitute another provider's output.

## Execution modes

| Mode | What it establishes |
| --- | --- |
| Saved artifact | Named checks passed on previously captured output; no provider call |
| Model API | Behavior under the recorded model prompt and endpoint boundary |
| Native harness | Behavior using the recorded runtime's actual skill-loading and tools |

Valid JSON does not establish schema correctness. An HTML attribute does not establish
usability or accessibility quality. A passing artifact hash check does not establish
deployment or semantic task completion. Define checks for the actual acceptance criteria.

## Optional Switchboard use

[Observatory Switchboard](https://github.com/fulks89-hub/observatory-switchboard) is a
separate public application. Inspect its installed revision and supported import schema
before exchanging results. This procedure does not assert that any unreleased adapter,
cross-provider interchange format, or native evaluator is available in that application.

Keep raw traces, absolute paths, private prompts and owner-specific results in private
storage. Public reports should use reviewed synthetic cases and aggregates whose inputs
are authorized for sharing. Never export credentials, session identifiers or private
configuration as evaluation provenance.
