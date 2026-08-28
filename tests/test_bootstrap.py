from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_bootstrap_requires_current_lock_on_both_platforms():
    shell = (ROOT / "scripts/bootstrap-observatory.sh").read_text()
    powershell = (ROOT / "scripts/bootstrap-observatory.ps1").read_text()
    for script in (shell, powershell):
        assert "0.12.7" in script
        assert "uv sync" in script
        assert "--locked" in script
        assert "--frozen" not in script
        assert "UV_PROJECT_ENVIRONMENT" in script


def test_shell_rejects_unknown_mode():
    result = subprocess.run(
        ["sh", "scripts/bootstrap-observatory.sh", "--unknown"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 64
    assert "usage:" in result.stderr


@pytest.mark.skipif(os.name == "nt", reason="POSIX bootstrap check")
def test_shell_check_is_read_only_with_safe_base_interpreter():
    base = str(Path(sys._base_executable).resolve())
    if any(part in {".venv", "venv", "tmp", "work"} for part in Path(base).parts):
        pytest.skip("test runner base interpreter is intentionally rejected by bootstrap")
    before = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    result = subprocess.run(
        ["sh", "scripts/bootstrap-observatory.sh", "--check"],
        cwd=ROOT,
        env={**os.environ, "OBSERVATORY_PYTHON": base},
        text=True,
        capture_output=True,
    )
    after = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    assert result.returncode == 0, result.stderr
    assert "status=ready" in result.stdout
    assert before == after
