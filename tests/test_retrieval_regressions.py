from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from observatory.retrieval import SparseIndex

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/retrieval_regression_cases.yaml"


def test_canonical_retrieval_regressions():
    data = yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    assert data["version"] == 1
    index = SparseIndex.from_root(ROOT)
    for case in data["cases"]:
        results = index.search(
            case["query"],
            limit=case["top_k"],
            as_of=date.fromisoformat(str(case["as_of"])),
        )
        paths = {result.relative_path for result in results}
        assert set(case["expected_paths"]) <= paths, (
            f"{case['id']} expected {case['expected_paths']} within top {case['top_k']}, "
            f"got {[result.relative_path for result in results]}"
        )
