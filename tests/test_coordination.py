from __future__ import annotations

import subprocess

from observatory.coordination import check_overlap


def git(root, *arguments):
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_overlap_detects_worktree_and_other_branch_conflict(tmp_path):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    write(tmp_path / "concepts/shared.md", "base\n")
    write(tmp_path / "concepts/current-only.md", "base\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "base")
    base = git(tmp_path, "rev-parse", "HEAD")

    git(tmp_path, "switch", "-qc", "other")
    write(tmp_path / "concepts/shared.md", "other\n")
    write(tmp_path / "docs/other.md", "other\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "other")

    git(tmp_path, "switch", "-q", "main")
    write(tmp_path / "concepts/shared.md", "current\n")
    write(tmp_path / "concepts/current-only.md", "current\n")
    result = check_overlap(tmp_path, base, "other")
    assert not result.ok
    assert result.overlaps == ("concepts/shared.md",)
    assert result.high_risk == ("concepts/shared.md",)
    assert "concepts/current-only.md" in result.current_paths
    assert "docs/other.md" in result.other_paths
