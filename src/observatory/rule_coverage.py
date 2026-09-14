"""Audit an explicitly scoped rule inventory; never infer live runtime enforcement."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from observatory.enforcement import artifact_hashes, strict_json
from observatory.safe_files import read_regular

SOURCES = ("AGENTS.md", "docs/execution-boundaries.md", "docs/rule-enforcement.md")
REGISTRY = ".observatory/rule-coverage.json"
ID = r"[a-z][a-z0-9-]{1,63}"
MARKER = re.compile(rf"<!-- (/?rule): ({ID}) -->")
NODE = re.compile(r"(tests/test_[a-z0-9_]+\.py)::(test_[a-z0-9_]+)")
STATES = ("implemented", "partial", "planned", "prose_by_design")


class CoverageError(ValueError):
    """The inventory or evidence does not support a coverage claim."""


def fields(value: Any, expected: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise CoverageError("invalid or unsupported registry fields")


def strings(value: Any, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
        raise CoverageError("expected a list of nonempty strings")
    if len(value) != len(set(value)) or (nonempty and not value):
        raise CoverageError("duplicate or missing list entries")
    return value


def local_file(root: Path, name: str) -> bytes:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
        raise CoverageError("file reference must be normalized and repository-relative")
    return read_regular(root / path, boundary=root)


def marked_rules(root: Path) -> dict[str, tuple[str, str]]:
    found: dict[str, tuple[str, str]] = {}
    for source in SOURCES:
        # Source mappings ignore platform line endings; evidence still hashes raw bytes.
        text = local_file(root, source).decode("utf-8").replace("\r\n", "\n")
        active: str | None = None
        body: list[str] = []
        for line in text.splitlines(keepends=True):
            marker = MARKER.fullmatch(line.rstrip("\n"))
            if marker:
                closing, identifier = marker.groups()
                if closing == "rule":
                    if active is not None or identifier in found:
                        raise CoverageError("duplicate or nested rule marker")
                    active, body = identifier, []
                else:
                    if active is None or active != identifier or not "".join(body).strip():
                        raise CoverageError("unmatched or empty rule marker")
                    digest = hashlib.sha256("".join(body).encode()).hexdigest()
                    found[identifier] = (source, digest)
                    active = None
            elif "<!-- rule" in line or "<!-- /rule" in line:
                raise CoverageError("malformed rule marker")
            elif active is not None:
                body.append(line)
        if active is not None:
            raise CoverageError("unclosed rule marker")
    return found


def inspect_registry(root: Path) -> dict[str, Any]:
    registry = strict_json(local_file(root, REGISTRY).decode("utf-8"))
    fields(registry, {"version", "scope", "exclusions", "rules"})
    if type(registry["version"]) is not int or registry["version"] != 1:
        raise CoverageError("unsupported registry version")
    if set(strings(registry["scope"])) != set(SOURCES):
        raise CoverageError("declared source scope differs from the audited scope")
    strings(registry["exclusions"], nonempty=True)
    rules = registry["rules"]
    if not isinstance(rules, list) or not rules:
        raise CoverageError("expected a nonempty rule inventory")
    source_rules = marked_rules(root)
    identifiers: set[str] = set()
    tests: set[str] = set()
    referenced_files = {REGISTRY, *SOURCES}
    counts: Counter[str] = Counter()
    for rule in rules:
        fields(rule, {"id", "source", "source_sha256", "implementation", "controls",
                      "tests", "activation", "why", "gaps", "enforcement_scope"})
        identifier = rule["id"]
        if not isinstance(identifier, str) or not re.fullmatch(ID, identifier):
            raise CoverageError("invalid rule ID")
        if identifier in identifiers:
            raise CoverageError("duplicate registry ID")
        identifiers.add(identifier)
        if source_rules.get(identifier) != (rule["source"], rule["source_sha256"]):
            raise CoverageError(f"missing or changed source mapping: {identifier}")
        state = rule["implementation"]
        if not isinstance(state, str) or state not in STATES:
            raise CoverageError("unsupported implementation state")
        for field in ("why", "enforcement_scope"):
            if not isinstance(rule[field], str) or not rule[field].strip():
                raise CoverageError("every rule needs a rationale and enforcement scope")
        # No in-repository assertion can supply independent runtime verification.
        expected_activation = "not_applicable" if state == "prose_by_design" else "unverified"
        if rule["activation"] != expected_activation:
            raise CoverageError("unsupported or unverified runtime activation claim")
        controls = strings(rule["controls"])
        nodes = strings(rule["tests"])
        strings(rule["gaps"], nonempty=state != "prose_by_design")
        if state in {"implemented", "partial"}:
            if not controls or not nodes:
                raise CoverageError("implemented controls require files and named tests")
        elif controls or nodes:
            raise CoverageError("unimplemented or prose rules cannot claim controls/tests")
        for name in controls:
            local_file(root, name)
            referenced_files.add(name)
        for node in nodes:
            match = NODE.fullmatch(node)
            if not match:
                raise CoverageError("tests must be explicit top-level pytest function references")
            local_file(root, match[1])
            referenced_files.add(match[1])
            tests.add(node)
        counts[state] += 1
    missing = source_rules.keys() - identifiers
    if missing:
        raise CoverageError("unregistered rule IDs: " + ", ".join(sorted(missing)))
    return {"scope": list(SOURCES), "exclusions": registry["exclusions"],
            "counts": {state: counts[state] for state in STATES}, "total": len(rules),
            "tests": sorted(tests), "artifact_files": sorted(referenced_files),
            "runtime_activation": "not_verified_by_this_audit"}


def passed_nodes(report: bytes, requested: list[str]) -> int:
    document = ET.fromstring(report)
    cases = list(document.iter("testcase"))
    observed: set[str] = set()
    if not cases:
        raise CoverageError("no test cases reported")
    for case in cases:
        if any(case.find(tag) is not None for tag in ("failure", "error", "skipped")):
            raise CoverageError("a claimed test failed or was skipped")
        name = case.get("name", "").split("[", 1)[0]
        observed.add(case.get("file", "") + "::" + name)
    if observed != set(requested):
        raise CoverageError("test report does not match requested tests")
    return len(cases)


def snapshot(root: Path) -> dict[str, str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, check=True, capture_output=True, timeout=30,
    )
    paths = sorted(set(p.decode() for p in result.stdout.split(b"\0") if p))
    return artifact_hashes(root, paths)


def audit(root: Path) -> dict[str, Any]:
    before = snapshot(root)
    inventory = inspect_registry(root)
    if not set(inventory.pop("artifact_files")).issubset(before):
        raise CoverageError("referenced files are missing from the repository artifact scope")
    requested = inventory.pop("tests")
    count = 0
    if requested:
        with tempfile.TemporaryDirectory(prefix="observatory-rule-audit-") as tmp:
            report = Path(tmp) / "tests.xml"
            env = dict(os.environ, PYTEST_ADDOPTS="", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
            # The registry cannot supply a command, shell fragment, plugin or option.
            run = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-o", "addopts=",
                 "-o", "junit_family=xunit1", "--junitxml", str(report), *requested],
                cwd=root, env=env, capture_output=True, timeout=120,
            )
            if run.returncode != 0:
                raise CoverageError("claimed tests failed; run named tests for diagnostics")
            count = passed_nodes(read_regular(report), requested)
    if snapshot(root) != before:
        raise CoverageError("repository artifacts changed during the audit")
    fingerprint = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
    return {**inventory, "named_tests_passed": count, "artifacts_sha256": fingerprint,
            "claim": "scoped implementation evidence; live enforcement is unverified"}
