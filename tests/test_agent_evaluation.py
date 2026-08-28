from __future__ import annotations

import json

from observatory.agent_evaluation import evaluate


def write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def test_agent_trace_passes_only_with_paths_assertions_evidence_and_metadata(tmp_path):
    fixture = tmp_path / "fixture.yaml"
    fixture.write_text(
        """version: 1
cases:
  - id: existing
    task: Find the existing card.
    expected_paths: [concepts/existing.md]
    assertions: [find_existing_before_create, cite_canonical_path]
""",
        encoding="utf-8",
    )
    trace = tmp_path / "trace.json"
    write_json(
        trace,
        {
            "case_id": "existing",
            "provider": "test",
            "model": "test-model",
            "corpus_commit": "abc123",
            "inspected_paths": ["concepts/existing.md"],
            "cited_paths": ["concepts/existing.md"],
            "created_paths": [],
            "assertion_results": {
                "find_existing_before_create": {
                    "status": "pass",
                    "evidence": "Updated the existing card.",
                },
                "cite_canonical_path": {
                    "status": "pass",
                    "evidence": "Returned the canonical path.",
                },
            },
        },
    )
    result = evaluate(fixture, trace)
    assert result.passed
    assert not result.failures


def test_agent_trace_fails_closed_on_missing_evidence_and_duplicate_creation(tmp_path):
    fixture = tmp_path / "fixture.yaml"
    fixture.write_text(
        """version: 1
cases:
  - id: existing
    task: Find the existing card.
    expected_paths: [concepts/existing.md]
    assertions: [find_existing_before_create]
""",
        encoding="utf-8",
    )
    trace = tmp_path / "trace.json"
    write_json(
        trace,
        {
            "case_id": "existing",
            "provider": "test",
            "model": "test-model",
            "corpus_commit": "abc123",
            "inspected_paths": [],
            "created_paths": ["concepts/duplicate.md"],
            "assertion_results": {},
        },
    )
    result = evaluate(fixture, trace)
    assert not result.passed
    assert any("not inspected" in failure for failure in result.failures)
    assert any("did not pass" in failure for failure in result.failures)
    assert any("new paths were created" in failure for failure in result.failures)
