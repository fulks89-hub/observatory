"""Synthetic request-guard regressions; no provider access or installation."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from observatory.request_guard import MAX_REQUEST_BYTES, GuardError, check_read, inspect_request


def invoke(root, request, *, adapter="generic", limit=4):
    return subprocess.run(
        [sys.executable, "-m", "observatory", "guard-read", "--root", str(root),
         "--max-bytes", str(limit), "--adapter", adapter],
        input=request if isinstance(request, bytes) else json.dumps(request).encode(),
        capture_output=True, timeout=10,
    )


def test_cli_allows_exact_limit_without_reading_contents(tmp_path):
    path = tmp_path / "sample.png"
    path.write_bytes(b"data")
    result = invoke(tmp_path, {"file_path": str(path)})
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"decision": "pass"}
    assert result.stderr == b""


@pytest.mark.parametrize("name", ["sample.png", "sample.txt", "without-extension"])
def test_size_guard_cannot_be_bypassed_by_extension(tmp_path, name):
    path = tmp_path / name
    path.write_bytes(b"12345")
    result = invoke(tmp_path, {"file_path": str(path)})
    assert result.returncode == 2
    assert json.loads(result.stdout)["decision"] == "deny"
    assert str(tmp_path).encode() not in result.stdout


@pytest.mark.parametrize("raw", [
    b"", b"[]", b"null", b"{}", b"{", b"\xff", b"{} trailing",
    b'{"file_path":"a","file_path":"b"}', b'{"file_path":NaN}',
    b"[" * 2000 + b"]" * 2000, b" " * (MAX_REQUEST_BYTES + 1),
])
def test_invalid_input_blocks_without_echo(tmp_path, raw):
    result = invoke(tmp_path, raw, adapter="claude-code")
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.startswith(b"read guard:")
    assert len(result.stderr) < 100


@pytest.mark.parametrize("path", [None, 1, True, "", "relative.txt", "a/../b", "\x00"])
def test_invalid_path(tmp_path, path):
    with pytest.raises(GuardError):
        check_read(path, root=tmp_path, max_bytes=4)


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_policy(tmp_path, limit):
    with pytest.raises(GuardError):
        check_read(str(tmp_path / "missing"), root=tmp_path, max_bytes=limit)


def test_outside_missing_directory_traversal_and_network(tmp_path):
    root = tmp_path / "allowed"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"a")
    for path in [outside, root / "missing", root, root / ".." / "outside"]:
        with pytest.raises(GuardError):
            check_read(str(path), root=root, max_bytes=4)
    for path in ["//example.invalid/share/file", r"\\example.invalid\share\file"]:
        with pytest.raises(GuardError):
            check_read(path, root=root, max_bytes=4)


def test_symlink_and_parent_symlink(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    file = target / "small"
    file.write_bytes(b"a")
    link = tmp_path / "link"
    parent = tmp_path / "parent"
    try:
        link.symlink_to(file)
        parent.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    for path in [link, parent / "small"]:
        with pytest.raises(GuardError, match="links"):
            check_read(str(path), root=tmp_path, max_bytes=4)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX FIFO")
def test_fifo_rejected_without_opening(tmp_path):
    path = tmp_path / "pipe"
    os.mkfifo(path)
    result = invoke(tmp_path, {"file_path": str(path)})
    assert result.returncode == 2


def test_claude_metadata_is_discarded_and_never_grants_permission(tmp_path):
    path = tmp_path / "small"
    path.write_bytes(b"a")
    request = {
        "hook_event_name": "PreToolUse", "tool_name": "Read",
        "tool_input": {"file_path": str(path), "offset": 1, "limit": 1},
        "transcript_path": "SYNTHETIC_DO_NOT_READ", "session_id": "SYNTHETIC_DO_NOT_LOG",
        "cwd": "SYNTHETIC_UNTRUSTED_ROOT",
    }
    result = invoke(tmp_path, request, adapter="claude-code")
    assert (result.returncode, result.stdout, result.stderr) == (0, b"", b"")
    path.write_bytes(b"12345")
    request["tool_input"]["allow"] = True
    request["max_bytes"] = 100000
    result = invoke(tmp_path, request, adapter="claude-code")
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr == b"read guard: file exceeds configured byte limit\n"


@pytest.mark.parametrize("payload", [
    {"hook_event_name": "Stop", "tool_name": "Read", "tool_input": {}},
    {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {}},
    {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": None},
])
def test_wrong_event_or_tool_blocks(tmp_path, payload):
    assert invoke(tmp_path, payload, adapter="claude-code").returncode == 2


def test_generic_request_cannot_override_policy(tmp_path):
    file = tmp_path / "small"
    file.write_bytes(b"a")
    for field in ["root", "max_bytes", "allow", "comment"]:
        request = {"file_path": str(file), field: "allow"}
        with pytest.raises(GuardError, match="unsupported"):
            inspect_request(json.dumps(request).encode(), root=tmp_path,
                            max_bytes=4, adapter="generic")


def test_check_never_opens_target(tmp_path, monkeypatch):
    file = tmp_path / "small"
    file.write_bytes(b"a")

    def forbidden(*args, **kwargs):
        pytest.fail("guard must not open file contents")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(os, "open", forbidden)
    check_read(str(file), root=tmp_path, max_bytes=4)
