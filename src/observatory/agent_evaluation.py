"""Executable scoring for provider-neutral agent behavior traces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    case_id: str
    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "checks": list(self.checks),
            "failures": list(self.failures),
        }


def _strings(value: object) -> set[str]:
    return {str(item) for item in value} if isinstance(value, list) else set()


def evaluate(fixture: Path, trace: Path) -> EvaluationResult:
    fixture_data = yaml.safe_load(fixture.read_text(encoding="utf-8"))
    trace_data = json.loads(trace.read_text(encoding="utf-8"))
    if not isinstance(fixture_data, dict) or not isinstance(trace_data, dict):
        raise ValueError("fixture and trace must be mappings")

    case_id = str(trace_data.get("case_id") or "")
    cases = fixture_data.get("cases")
    case = (
        next(
            (
                item
                for item in cases
                if isinstance(item, dict) and str(item.get("id") or "") == case_id
            ),
            None,
        )
        if isinstance(cases, list)
        else None
    )
    if case is None:
        raise ValueError(f"unknown evaluation case {case_id!r}")

    checks: list[str] = []
    failures: list[str] = []
    for field in ("provider", "model", "corpus_commit"):
        if not str(trace_data.get(field) or "").strip():
            failures.append(f"missing run metadata: {field}")
    if not failures:
        checks.append("run metadata recorded")

    expected = _strings(case.get("expected_paths"))
    inspected = _strings(trace_data.get("inspected_paths"))
    missing_paths = sorted(expected - inspected)
    if missing_paths:
        failures.append(f"expected paths not inspected: {', '.join(missing_paths)}")
    else:
        checks.append("expected paths inspected")

    assertions = _strings(case.get("assertions"))
    assertion_results = trace_data.get("assertion_results")
    assertion_results = assertion_results if isinstance(assertion_results, dict) else {}
    for assertion in sorted(assertions):
        result = assertion_results.get(assertion)
        if not isinstance(result, dict) or result.get("status") != "pass":
            failures.append(f"assertion did not pass: {assertion}")
        elif not str(result.get("evidence") or "").strip():
            failures.append(f"assertion lacks evidence: {assertion}")
        else:
            checks.append(f"assertion passed: {assertion}")

    if "cite_canonical_path" in assertions:
        missing_citations = sorted(expected - _strings(trace_data.get("cited_paths")))
        if missing_citations:
            failures.append(f"expected paths not cited: {', '.join(missing_citations)}")
        else:
            checks.append("expected canonical paths cited")

    if "find_existing_before_create" in assertions and _strings(trace_data.get("created_paths")):
        failures.append("new paths were created despite find-existing requirement")

    return EvaluationResult(
        case_id=case_id,
        passed=not failures,
        checks=tuple(checks),
        failures=tuple(failures),
    )
