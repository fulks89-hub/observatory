"""Implementation-neutral Observatory command-line contract."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import yaml

from observatory import agent_evaluation, catalog, coordination, preservation, validation
from observatory.retrieval import STRATEGY, SparseIndex


def _root(value: str) -> Path:
    return Path(value).resolve()


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected YYYY-MM-DD") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="observatory", description="Observatory tooling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search = subparsers.add_parser("search", help="Search canonical knowledge")
    search.add_argument("query", nargs="+")
    search.add_argument("-n", "--limit", type=int, default=5)
    search.add_argument("--json", action="store_true")
    search.add_argument("--include-inactive", action="store_true")
    search.add_argument("--exclude-stale", action="store_true")
    search.add_argument("--include-noncurrent", action="store_true")
    search.add_argument("--as-of", type=_date)
    search.add_argument("--type")
    search.add_argument("--project")
    search.add_argument("--source-id")
    search.add_argument("--root", type=_root, default=Path.cwd())

    validate = subparsers.add_parser("validate", help="Validate OKF and likely secrets")
    validate.add_argument("--root", type=_root, default=Path.cwd())

    catalog_parser = subparsers.add_parser("catalog", help="Build a disposable catalog")
    catalog_parser.add_argument("--root", type=_root, default=Path.cwd())
    catalog_parser.add_argument("--output", type=Path)

    preserve = subparsers.add_parser("preserve", help="Guard durable knowledge preservation")
    preserve.add_argument(
        "base_ref",
        nargs="?",
        default=os.getenv("OBSERVATORY_BASE_REF") or os.getenv("BRAIN_BASE_REF"),
    )
    preserve.add_argument("--root", type=_root, default=Path.cwd())

    evaluate = subparsers.add_parser("evaluate-agent", help="Score a recorded agent run")
    evaluate.add_argument("trace", type=Path)
    evaluate.add_argument("--fixture", type=Path)
    evaluate.add_argument("--root", type=_root, default=Path.cwd())
    evaluate.add_argument("--json", action="store_true")

    overlap = subparsers.add_parser("overlap", help="Detect overlapping agent branch changes")
    overlap.add_argument("other_ref")
    overlap.add_argument("--base-ref", default="origin/main")
    overlap.add_argument("--root", type=_root, default=Path.cwd())
    overlap.add_argument("--json", action="store_true")
    return parser


def _search(arguments: argparse.Namespace) -> int:
    if arguments.limit <= 0:
        print("--limit must be positive", file=sys.stderr)
        return 2
    query = " ".join(arguments.query).strip()
    index = SparseIndex.from_root(arguments.root)
    results = index.search(
        query,
        limit=arguments.limit,
        include_inactive=arguments.include_inactive,
        include_stale=not arguments.exclude_stale,
        include_noncurrent=arguments.include_noncurrent,
        type=arguments.type,
        project=arguments.project,
        source_id=arguments.source_id,
        as_of=arguments.as_of,
    )
    if arguments.json:
        print(
            json.dumps(
                {
                    "query": query,
                    "strategy": STRATEGY,
                    "canonical_root": str(arguments.root),
                    "as_of": (arguments.as_of or date.today()).isoformat(),
                    "results": [result.as_dict() for result in results],
                },
                indent=2,
            )
        )
        return 0
    if not results:
        print(f"No canonical matches for {query!r}.")
        return 1
    for number, result in enumerate(results, 1):
        print(f"{number:2d}. {result.score:<7.3f} {result.relative_path}")
        print(f"    {result.title} [{result.type} / {result.status}]")
        if result.description:
            print(f"    {result.description}")
        print(f"    matched: {', '.join(result.matched_terms)}")
        for warning in result.warnings:
            print(f"    warning: {warning}")
    return 0


def _validate(arguments: argparse.Namespace) -> int:
    result = validation.validate(arguments.root)
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if result.ok:
        print(
            f"OK: validated {result.document_count} durable Markdown files and scanned "
            f"{result.tracked_count} tracked files for likely secrets "
            f"({len(result.warnings)} warning(s))"
        )
        return 0
    print(f"Validation failed with {len(result.errors)} error(s):", file=sys.stderr)
    for error in result.errors:
        print(f"- {error}", file=sys.stderr)
    return 1


def _catalog(arguments: argparse.Namespace) -> int:
    rendered = json.dumps(catalog.build(arguments.root), indent=2) + "\n"
    if arguments.output is None:
        print(rendered, end="")
    else:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(rendered, encoding="utf-8")
    return 0


def _preserve(arguments: argparse.Namespace) -> int:
    if not arguments.base_ref:
        print("Usage: observatory preserve BASE_REF", file=sys.stderr)
        return 2
    result = preservation.check(arguments.root, arguments.base_ref)
    for warning in result.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    if result.ok:
        print(
            f"OK: preservation check compared {result.merge_base[:12]}..{result.head[:12]} "
            f"({result.changed_count} changed path(s))"
        )
        return 0
    print(
        f"Preservation check failed with {len(result.violations)} destructive change(s):",
        file=sys.stderr,
    )
    for violation in result.violations:
        print(f"- {violation}", file=sys.stderr)
    print(
        "Record explicit human approval in .observatory/destructive-change-approvals.yaml when "
        "destruction is intentional.",
        file=sys.stderr,
    )
    return 1


def _evaluate_agent(arguments: argparse.Namespace) -> int:
    fixture = arguments.fixture or arguments.root / "tests/fixtures/agent_retrieval_cases.yaml"
    try:
        result = agent_evaluation.evaluate(fixture, arguments.trace)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as error:
        print(f"Agent evaluation failed: {error}", file=sys.stderr)
        return 2
    if arguments.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        label = "PASS" if result.passed else "FAIL"
        print(f"{label}: agent evaluation case {result.case_id}")
        for check in result.checks:
            print(f"  check: {check}")
        for failure in result.failures:
            print(f"  failure: {failure}")
    return 0 if result.passed else 1


def _overlap(arguments: argparse.Namespace) -> int:
    try:
        result = coordination.check_overlap(arguments.root, arguments.base_ref, arguments.other_ref)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() if error.stderr else str(error)
        print(f"Overlap check failed: {detail}", file=sys.stderr)
        return 2
    payload = {
        "base_ref": result.base_ref,
        "other_ref": result.other_ref,
        "current_paths": list(result.current_paths),
        "other_paths": list(result.other_paths),
        "overlaps": list(result.overlaps),
        "high_risk": list(result.high_risk),
        "ok": result.ok,
    }
    if arguments.json:
        print(json.dumps(payload, indent=2))
    elif result.ok:
        print(f"OK: no overlapping paths with {result.other_ref}")
    else:
        print(f"Conflict: {len(result.overlaps)} overlapping path(s) with {result.other_ref}")
        for path in result.overlaps:
            label = " [canonical/policy]" if path in result.high_risk else ""
            print(f"- {path}{label}")
    return 0 if result.ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    handlers = {
        "search": _search,
        "validate": _validate,
        "catalog": _catalog,
        "preserve": _preserve,
        "evaluate-agent": _evaluate_agent,
        "overlap": _overlap,
    }
    return handlers[arguments.command](arguments)
