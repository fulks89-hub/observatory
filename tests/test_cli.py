from __future__ import annotations

import json

from conftest import write_card

from observatory.cli import main


def test_search_json_contract(tmp_path, capsys):
    write_card(
        tmp_path,
        "concepts/test.md",
        title="Test retrieval",
        extra=(
            "description: JSON contract fixture.\n"
            "status: stable\n"
            "sources:\n  - id: source-id\n    resource: https://example.invalid\n"
        ),
    )
    assert (
        main(
            [
                "search",
                "--root",
                str(tmp_path),
                "--json",
                "--as-of",
                "2026-08-17",
                "test retrieval",
            ]
        )
        == 0
    )
    payload = json.loads(capsys.readouterr().out)
    assert set(payload) == {"query", "strategy", "canonical_root", "as_of", "results"}
    assert payload["as_of"] == "2026-08-17"
    assert payload["strategy"] == "sparse-bm25-v2"
    assert payload["results"][0] == {
        "path": "concepts/test.md",
        "score": payload["results"][0]["score"],
        "strategy": "sparse-bm25-v2",
        "title": "Test retrieval",
        "type": "Concept",
        "status": "stable",
        "matched_terms": ["retrieval", "test"],
        "description": "JSON contract fixture.",
        "source_ids": ["source-id"],
        "projects": [],
        "stale_after": None,
        "valid_from": None,
        "valid_until": None,
        "applicability": "current",
        "superseded_by": [],
        "conflicts_with": [],
        "warnings": [],
    }


def test_search_text_prints_freshness_warning(tmp_path, capsys):
    write_card(
        tmp_path,
        "concepts/test.md",
        title="Old retrieval",
        extra="status: stable\nstale_after: 2026-01-01\n",
    )
    assert main(["search", "--root", str(tmp_path), "--as-of", "2026-08-17", "old retrieval"]) == 0
    assert "freshness review overdue since 2026-01-01" in capsys.readouterr().out


def test_search_text_no_results_exit_code(tmp_path, capsys):
    write_card(tmp_path, "concepts/test.md", title="Known")
    assert main(["search", "--root", str(tmp_path), "missing"]) == 1
    assert "No canonical matches" in capsys.readouterr().out


def test_search_defaults_to_a_small_metadata_only_candidate_set(tmp_path, capsys):
    for number in range(7):
        write_card(
            tmp_path,
            f"concepts/card-{number}.md",
            title=f"Shared retrieval topic {number}",
            body=f"# TL;DR\n\nDistinct full body {number} that must not enter search output.\n",
        )
    assert main(["search", "--root", str(tmp_path), "--json", "shared retrieval topic"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["results"]) == 5
    assert all("body" not in result for result in payload["results"])
    assert "Distinct full body" not in json.dumps(payload)


def test_evaluate_agent_cli_returns_nonzero_for_failed_trace(tmp_path, capsys):
    fixture = tmp_path / "fixture.yaml"
    fixture.write_text(
        """version: 1
cases:
  - id: case
    task: Inspect the card.
    expected_paths: [concepts/card.md]
    assertions: [cite_canonical_path]
""",
        encoding="utf-8",
    )
    trace = tmp_path / "trace.json"
    trace.write_text(
        json.dumps(
            {
                "case_id": "case",
                "provider": "test",
                "model": "test",
                "corpus_commit": "abc",
                "inspected_paths": [],
                "cited_paths": [],
                "assertion_results": {},
            }
        ),
        encoding="utf-8",
    )
    assert main(["evaluate-agent", str(trace), "--fixture", str(fixture), "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["passed"] is False
    assert any("not inspected" in failure for failure in payload["failures"])
