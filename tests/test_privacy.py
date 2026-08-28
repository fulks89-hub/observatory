from __future__ import annotations

import subprocess

from observatory.privacy import scan_current, scan_history


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout


def test_scans_large_current_files_and_risky_names(tmp_path):
    (tmp_path / ".env").write_text("safe placeholder", encoding="utf-8")
    large = tmp_path / "large.bin"
    large.write_bytes(b"x" * 2_100_000 + b" github_pat_" + b"A" * 45)
    result = scan_current(tmp_path, [".env", "large.bin"])
    assert result.scanned_count == 2
    assert not result.skipped
    assert {finding.kind for finding in result.findings} >= {
        "risky environment filename",
        "GitHub token",
    }


def test_reports_oversized_objects_instead_of_silently_skipping(tmp_path):
    (tmp_path / "large").write_bytes(b"abc")
    result = scan_current(tmp_path, ["large"], max_bytes=2)
    assert result.scanned_count == 0
    assert "exceeds 2 bytes" in result.skipped[0]


def test_history_scan_finds_removed_secret(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    path = tmp_path / "old.txt"
    path.write_text("glpat-" + "A" * 24, encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "secret")
    path.unlink()
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "remove")
    result = scan_history(tmp_path)
    assert any(finding.kind == "GitLab token" for finding in result.findings)
    limited = scan_history(tmp_path, max_bytes=2)
    assert limited.skipped


def test_scans_current_and_historical_path_names(tmp_path):
    named = "person" + "@private.example.txt"
    (tmp_path / named).write_text("safe", encoding="utf-8")
    current = scan_current(tmp_path, [named])
    assert any(finding.location.startswith("path:") for finding in current.findings)

    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "path fixture")
    historical = scan_history(tmp_path)
    assert any(finding.location.startswith("history:path:") for finding in historical.findings)


def test_history_scans_commit_and_tag_identity_with_exact_noreply_allowlist(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "user.email", "12345+fixture@users.noreply.github.com")
    (tmp_path / "safe.txt").write_text("safe", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "safe noreply")
    git(tmp_path, "tag", "-a", "safe-tag", "-m", "safe tag")
    safe = scan_history(tmp_path)
    assert not any(finding.kind == "email address" for finding in safe.findings)

    git(tmp_path, "config", "user.email", "private.person" + "@real.example")
    (tmp_path / "private.txt").write_text("still safe content", encoding="utf-8")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "private identity")
    git(tmp_path, "tag", "-a", "private-tag", "-m", "private tag metadata")
    exposed = scan_history(tmp_path)
    metadata = [
        finding
        for finding in exposed.findings
        if finding.kind == "email address" and ":<metadata>" in finding.location
    ]
    assert metadata
