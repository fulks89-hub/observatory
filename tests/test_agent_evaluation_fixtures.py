from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/agent_retrieval_cases.yaml"
REQUIRED_ASSERTIONS = {
    "find_existing_before_create",
    "distinguish_source_from_concept",
    "follow_multiple_links",
    "distinguish_idea_from_verified_claim",
    "scorecard_on_primary_document_only",
}


def test_fixture_schema_and_references():
    data = yaml.safe_load(FIXTURE.read_text())
    assert data["version"] == 1
    cases = data["cases"]
    identifiers = [entry["id"] for entry in cases]
    assert len(identifiers) == len(set(identifiers))
    for entry in cases:
        assert entry["task"]
        assert entry["assertions"]
        for relative in entry["expected_paths"]:
            assert (ROOT / relative).is_file(), f"missing fixture path {relative}"
    covered = {assertion for entry in cases for assertion in entry["assertions"]}
    assert REQUIRED_ASSERTIONS <= covered
