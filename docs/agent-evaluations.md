# Agent evaluation protocol

Observatory's deterministic tests protect structure; they do not prove that a model retrieves, synthesizes, or edits knowledge well. `tests/fixtures/agent_retrieval_cases.yaml` defines a small provider-neutral behavioral suite for periodic agent evaluation.

## How to run a behavioral evaluation

1. Use a clean disposable branch or corpus copy.
2. Give the agent only the repository entry instructions and one fixture task.
3. Record the provider/model, date, corpus commit, tools available, metadata candidates returned, full files or dossier sections inspected, citations returned, proposed diff, search/end-to-end elapsed time, and approximate Observatory-attributable input tokens when available.
4. Judge every named assertion and record pass, fail, or not applicable with a short reason.
5. Discard fixture edits. Do not add model-specific answers to the canonical corpus.
6. Compare results over time and add a new case when a real failure recurs.

Record each run as JSON and score it with:

```sh
.venv/bin/observatory evaluate-agent path/to/run.json --json
```

The trace must identify `case_id`, `provider`, `model`, `corpus_commit`, `inspected_paths`, `cited_paths`, `created_paths`, and `assertion_results`. Each assertion result uses `{"status": "pass|fail|not_applicable", "evidence": "..."}`. Missing evidence fails closed. The command exits nonzero when expected paths were not inspected/cited, a required assertion did not pass, or a find-existing case created a duplicate.

The scorer makes recorded model runs executable and comparable; it does not pretend deterministic code can judge semantic quality unaided. A human or trusted evaluation process still supplies concise assertion evidence, and fixture edits still run in a disposable branch/corpus.

## Core measures

- **Retrieval recall:** Did the agent inspect all expected canonical paths or find an equally valid alternative?
- **Retrieval precision:** How many unrelated full documents did it open?
- **Attribution:** Did it distinguish source evidence, synthesized concepts, owner ideas, and open questions?
- **Update discipline:** Did it update an existing subject rather than create a duplicate?
- **Preservation:** Did the proposal retain unknown fields, sources, verification events, footnotes, and useful sections?
- **Graph reasoning:** Did it follow relevant links without treating the derived catalog as authority?
- **Context efficiency:** Did it narrow candidates before opening full cards rather than loading the whole corpus?
- **Expansion value:** Did opening additional documents materially improve the result, or only add tokens and latency?

Use the same fixture and corpus commit for comparisons. Candidate count, full-document opens, context tokens, and latency are diagnostic measures; never optimize them by sacrificing expected-path recall, applicability, or citation accuracy. See the [context budget contract](context-budget-contract.md).

CI validates the fixture schema, exercises the scoring engine's pass/fail behavior, and runs deterministic canonical retrieval regressions. Periodic provider runs use the same scorer for the semantic behaviors that code cannot honestly certify by itself.
