import json
import os
import subprocess
import sys

import pytest

from observatory import enforcement as e
from observatory.cli import main


@pytest.mark.parametrize(
    "text", ['{"x":1}}', '{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', "{}\n{}"]
)
def test_malformed_outputs(text):
    with pytest.raises(e.BoundaryError):
        e.strict_json(text)


@pytest.mark.parametrize("value", [{}, {"ready": True, "extra": 1}, {"ready": 1}])
def test_closed_contract(value):
    with pytest.raises(e.BoundaryError):
        e.validate_output(value, {"type": "object", "fields": {"ready": {"type": "boolean"}}})


@pytest.mark.parametrize(
    "contract",
    [
        {"type": "string", "min": -1},
        {"type": "array"},
        {"type": "object"},
        {"type": "array", "items": {"type": "unknown"}},
        {"type": "integer", "minimum": 1},
        {"type": "array", "items": {"type": "string"}, "min": 2, "max": 1},
    ],
)
def test_invalid_contract(contract):
    with pytest.raises(e.BoundaryError):
        e.validate_contract(contract)


def test_valid_nested_contract():
    contract = {
        "type": "object",
        "fields": {"ids": {"type": "array", "items": {"type": "integer"}, "min": 1, "max": 2}},
    }
    e.validate_output({"ids": [1, 2]}, contract)
    with pytest.raises(e.BoundaryError):
        e.validate_output({"ids": [True]}, contract)


def receipt(root):
    (root / "code.py").write_text("original")
    before = e.artifact_hashes(root, ["code.py"])
    return e.make_receipt(root, ["code.py"], "smoke", before, True, {})


def test_stale_evidence_and_wrong_scope(tmp_path):
    r = receipt(tmp_path)
    e.require_receipt(tmp_path, ["code.py"], "smoke", r)
    for changes in [
        {"check": "other"},
        {"passed": False},
        {"passed": 1},
        {"stable": False},
        {"root": "/elsewhere"},
        {"artifacts": {}},
    ]:
        with pytest.raises(e.BoundaryError):
            e.require_receipt(tmp_path, ["code.py"], "smoke", {**r, **changes})
    (tmp_path / "code.py").write_text("changed after test")
    with pytest.raises(e.BoundaryError):
        e.require_receipt(tmp_path, ["code.py"], "smoke", r)


def test_mutation_during_check_and_symlinks(tmp_path):
    receipt(tmp_path)
    before = e.artifact_hashes(tmp_path, ["code.py"])
    (tmp_path / "code.py").write_text("changed")
    assert not e.make_receipt(tmp_path, ["code.py"], "smoke", before, True, {})["passed"]
    (tmp_path / "link.py").symlink_to(tmp_path / "code.py")
    for paths in [["../escape"], ["link.py"], [], ["code.py", "code.py"]]:
        with pytest.raises((e.BoundaryError, OSError)):
            e.artifact_hashes(tmp_path, paths)


@pytest.mark.parametrize("state", ["unknown", "in_progress", "not_found", "failed", ""])
def test_uncertain_retry_blocked(state):
    fp = e.fingerprint({"scope": "local", "payload": 1})
    with pytest.raises(e.BoundaryError):
        e.operation_decision({"operation_id": "x", "fingerprint": fp, "status": state}, "x", fp)


def test_replay_and_conflict():
    fp = e.fingerprint({"payload": 1, "scope": "local"})
    assert fp == e.fingerprint({"scope": "local", "payload": 1})
    status = {"operation_id": "x", "fingerprint": fp, "status": "committed"}
    assert e.operation_decision(status, "x", fp) == "already_complete"
    assert e.operation_decision({**status, "status": "confirmed_not_applied"}, "x", fp) == (
        "retry_permitted"
    )
    with pytest.raises(e.BoundaryError):
        e.operation_decision(status, "x", e.fingerprint({"payload": 2}))
    with pytest.raises(e.BoundaryError):
        e.operation_decision(status, "other-operation", fp)


def test_cli_runs_real_check_and_rejects_old_receipt(tmp_path):
    artifact = tmp_path / "code.py"
    artifact.write_text("print(1)")
    target = tmp_path / "receipt.json"
    args = [
        "--root",
        str(tmp_path),
        "--artifact",
        "code.py",
        "--check",
        "smoke",
        "--receipt",
        str(target),
    ]
    command = ["enforce", "check", *args, "--", sys.executable, "-c", "pass"]
    assert main(command) == 0
    assert main(["enforce", "completion", *args]) == 0
    assert main(command) == 1  # Existing receipt cannot silently stand for another run.
    artifact.write_text("print(2)")
    assert main(["enforce", "completion", *args]) == 1
    assert json.loads(target.read_text())["passed"]


@pytest.mark.parametrize(
    "code,timeout", [("raise SystemExit(2)", "2"), ("import time; time.sleep(1)", "0.01")]
)
def test_failed_and_timed_out_commands(tmp_path, code, timeout):
    (tmp_path / "code.py").write_text("x")
    target = tmp_path / "receipt.json"
    args = [
        "--root",
        str(tmp_path),
        "--artifact",
        "code.py",
        "--check",
        "smoke",
        "--receipt",
        str(target),
    ]
    assert (
        main(["enforce", "check", *args, "--timeout", timeout, "--", sys.executable, "-c", code])
        == 1
    )
    assert main(["enforce", "completion", *args]) == 1


def test_cli_output(tmp_path):
    value, contract = tmp_path / "v.json", tmp_path / "c.json"
    value.write_text('{"ready":true}')
    contract.write_text('{"type":"object","fields":{"ready":{"type":"boolean"}}}')
    args = ["enforce", "output", str(value), "--contract", str(contract)]
    assert main(args) == 0
    value.write_text('{"ready":true}}')
    assert main(args) == 1


def test_number_contract_accepts_large_finite_json_integer():
    value = e.strict_json("1" + "0" * 400)
    e.validate_output(value, {"type": "number"})


def test_clean_git_tree_can_have_changed_receipt_bytes(tmp_path):
    """Checkout normalization can preserve Git cleanliness but invalidate evidence."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)

    def git(*args):
        return subprocess.check_output(
            ["git", "-c", "core.autocrlf=true", "-c", "core.safecrlf=false",
             "-c", "core.attributesFile=" + os.devnull,
             "-c", "core.hooksPath=" + str(tmp_path / "empty-hooks"),
             "-c", "commit.gpgSign=false", "-c", "user.name=Synthetic Fixture",
             "-c", "user.email=fixture@example.invalid", *args],
            cwd=tmp_path, env=env, stderr=subprocess.PIPE, timeout=10,
        )

    git("init", "-q")
    path = tmp_path / "sample.txt"
    original = b"alpha\nbeta\n"
    path.write_bytes(original)
    git("add", "sample.txt")
    git("commit", "-qm", "Synthetic line-ending fixture")
    assert path.read_bytes() == original
    before = e.artifact_hashes(tmp_path, ["sample.txt"])
    record = e.make_receipt(tmp_path, ["sample.txt"], "fixture-bytes", before, True, {})
    e.require_receipt(tmp_path, ["sample.txt"], "fixture-bytes", record)

    path.unlink()
    git("checkout", "--", "sample.txt")
    assert path.read_bytes() == b"alpha\r\nbeta\r\n"
    assert git("status", "--porcelain") == b""
    assert e.artifact_hashes(tmp_path, ["sample.txt"]) != before
    with pytest.raises(e.BoundaryError):
        e.require_receipt(tmp_path, ["sample.txt"], "fixture-bytes", record)
