"""Synthetic inventory failures and actual test-run evidence; no live provider access."""

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from observatory import rule_coverage as c


@pytest.fixture
def inventory(tmp_path):
    body = "A bounded synthetic rule.\n"
    for source in c.SOURCES:
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Synthetic instructions\n")
    (tmp_path / c.SOURCES[0]).write_text("<!-- rule: sample -->\n" + body +
                                       "<!-- /rule: sample -->\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_sample.py").write_text("def test_ok():\n    assert True\n")
    (tmp_path / "guard.py").write_text("# Synthetic gate\n")
    (tmp_path / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, timeout=10)
    registry = {
        "version": 1, "scope": list(c.SOURCES), "exclusions": ["Unmarked prose excluded."],
        "rules": [{"id": "sample", "source": c.SOURCES[0],
                   "source_sha256": hashlib.sha256(body.encode()).hexdigest(),
                   "implementation": "implemented", "controls": ["guard.py"],
                   "tests": ["tests/test_sample.py::test_ok"], "activation": "unverified",
                   "why": "Synthetic example.", "enforcement_scope": "Synthetic caller.",
                   "gaps": ["No live wiring verified."]}],
    }
    save(tmp_path, registry)
    return tmp_path, registry


def save(root, registry):
    path = root / c.REGISTRY
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(registry))


def test_actual_audit_reports_tests_without_claiming_activation(inventory):
    root, _ = inventory
    report = c.audit(root)
    assert report["counts"]["implemented"] == 1
    assert report["named_tests_passed"] == 1
    assert report["runtime_activation"] == "not_verified_by_this_audit"
    assert len(report["artifacts_sha256"]) == 64
    assert str(root) not in json.dumps(report)


@pytest.mark.parametrize("change", [
    {"activation": "verified"}, {"implementation": "guarded"}, {"why": ""},
    {"enforcement_scope": ""}, {"controls": []}, {"tests": []}, {"gaps": []},
    {"controls": ["missing.py"]}, {"controls": ["../outside"]},
    {"tests": ["--override-ini=bad"]}, {"tests": ["tests/../bad.py::test_ok"]},
    {"source_sha256": "0" * 64}, {"source": "missing.md"},
    {"implementation": "planned"}, {"activation": {"status": "verified"}},
])
def test_invalid_claims_fail(inventory, change):
    root, registry = inventory
    registry["rules"][0].update(change)
    save(root, registry)
    with pytest.raises((ValueError, OSError)):
        c.inspect_registry(root)


@pytest.mark.parametrize("change", [
    {"version": True}, {"version": 2}, {"scope": ["AGENTS.md"]},
    {"exclusions": []}, {"rules": []}, {"unknown": "ignored?"},
])
def test_invalid_registry_structure(inventory, change):
    root, registry = inventory
    registry.update(change)
    save(root, registry)
    with pytest.raises(c.CoverageError):
        c.inspect_registry(root)


def test_duplicate_json_and_registry_ids(inventory):
    root, registry = inventory
    (root / c.REGISTRY).write_text('{"version":1,"version":2}')
    with pytest.raises(ValueError):
        c.inspect_registry(root)
    registry["rules"].append(copy.deepcopy(registry["rules"][0]))
    save(root, registry)
    with pytest.raises(c.CoverageError, match="duplicate"):
        c.inspect_registry(root)


@pytest.mark.parametrize("text", [
    "<!-- rule: new-rule -->\nNew rule.\n<!-- /rule: new-rule -->\n",
    "<!-- rule: broken -->\nUnclosed rule.\n",
    "<!-- rule: bad ID -->\nInvalid marker.\n",
    "<!-- /rule: missing -->\n",
    "<!-- rule: sample -->\nDuplicate.\n<!-- /rule: sample -->\n",
])
def test_unregistered_and_malformed_markers(inventory, text):
    root, _ = inventory
    with (root / c.SOURCES[1]).open("a") as out:
        out.write(text)
    with pytest.raises(c.CoverageError):
        c.inspect_registry(root)


def test_source_edits_and_removed_markers_fail_but_crlf_mapping_is_stable(inventory):
    root, _ = inventory
    path = root / c.SOURCES[0]
    original = path.read_bytes()
    path.write_bytes(original.replace(b"\n", b"\r\n"))
    assert c.inspect_registry(root)["total"] == 1
    path.write_bytes(original.replace(b"bounded", b"unbounded"))
    with pytest.raises(c.CoverageError, match="changed source"):
        c.inspect_registry(root)
    path.write_text("Rule deleted.\n")
    with pytest.raises(c.CoverageError):
        c.inspect_registry(root)


@pytest.mark.parametrize("code", [
    "def test_ok():\n    assert False\n",
    "import pytest\ndef test_ok():\n    pytest.skip('synthetic')\n",
    "def test_other():\n    pass\n",
    "from pathlib import Path\ndef test_ok():\n    Path('guard.py').write_text('changed')\n",
])
def test_actual_failed_skipped_missing_and_mutating_tests_fail(inventory, code):
    root, _ = inventory
    (root / "tests/test_sample.py").write_text(code)
    with pytest.raises(c.CoverageError):
        c.audit(root)


def test_test_timeout_does_not_become_a_success(inventory, monkeypatch):
    root, _ = inventory
    run = c.subprocess.run

    def timeout(*args, **kwargs):
        if "pytest" in args[0]:
            raise subprocess.TimeoutExpired("pytest", 120)
        return run(*args, **kwargs)

    monkeypatch.setattr(c.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        c.audit(root)


def test_symlink_control_is_rejected(inventory):
    root, registry = inventory
    try:
        (root / "alias.py").symlink_to(root / "guard.py")
    except OSError:
        pytest.skip("symlink creation unavailable")
    registry["rules"][0]["controls"] = ["alias.py"]
    save(root, registry)
    with pytest.raises(OSError):
        c.inspect_registry(root)


def test_ignored_control_cannot_escape_evidence_scope(inventory):
    root, _ = inventory
    with (root / ".gitignore").open("a") as out:
        out.write("guard.py\n")
    with pytest.raises(c.CoverageError, match="artifact scope"):
        c.audit(root)


def test_partial_planned_and_prose_states(inventory):
    root, registry = inventory
    rule = registry["rules"][0]
    rule["implementation"] = "partial"
    save(root, registry)
    assert c.inspect_registry(root)["counts"]["partial"] == 1
    rule.update(implementation="planned", controls=[], tests=[])
    save(root, registry)
    assert c.inspect_registry(root)["counts"]["planned"] == 1
    rule.update(implementation="prose_by_design", activation="not_applicable", gaps=[])
    save(root, registry)
    assert c.inspect_registry(root)["counts"]["prose_by_design"] == 1


def test_junit_report_must_cover_exact_requested_nodes():
    with pytest.raises(c.CoverageError):
        c.passed_nodes(b"<testsuites/>", ["tests/test_sample.py::test_ok"])
    report = b'<testsuites><testcase file="tests/test_other.py" name="test_ok"/></testsuites>'
    with pytest.raises(c.CoverageError):
        c.passed_nodes(report, ["tests/test_sample.py::test_ok"])


def test_current_repository_registry_has_real_mappings():
    report = c.inspect_registry(Path(__file__).resolve().parents[1])
    assert report["tests"]
    assert report["runtime_activation"] == "not_verified_by_this_audit"
