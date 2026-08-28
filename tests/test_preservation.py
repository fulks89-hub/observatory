from __future__ import annotations

import subprocess
from pathlib import Path

from observatory.preservation import check


def git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def setup_repository(root: Path) -> None:
    (root / ".observatory").mkdir()
    (root / ".observatory/destructive-change-approvals.yaml").write_text(
        "version: 1\napprovals: []\n", encoding="utf-8"
    )
    git(root, "init", "-q")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")


def test_legacy_brain_approval_directory_is_readable(tmp_path):
    (tmp_path / ".brain").mkdir()
    (tmp_path / ".brain/destructive-change-approvals.yaml").write_text(
        "version: 1\napprovals: []\n", encoding="utf-8"
    )
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    base = commit(tmp_path, card())
    commit(tmp_path, card(body="# TL;DR\n\nStill durable.[^source]\n\n[^source]: Evidence.\n"))
    assert check(tmp_path, base).ok


def card(*, source: bool = True, verified: bool = True, body: str | None = None) -> str:
    content = body or "# TL;DR\n\nDurable claim.[^source]\n\n[^source]: Evidence.\n"
    source_yaml = (
        "sources:\n  - id: source\n    resource: https://example.invalid\n" if source else ""
    )
    verified_yaml = (
        "verified:\n  - by: process:test\n    at: 2026-01-01T00:00:00Z\n" if verified else ""
    )
    return (
        "---\ntype: Concept\ntitle: Test\ncustom_extension: keep-me\n"
        f"{source_yaml}{verified_yaml}---\n{content}"
    )


def commit(root: Path, content: str) -> str:
    (root / "concepts").mkdir(exist_ok=True)
    (root / "concepts/test.md").write_text(content, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture")
    return git(root, "rev-parse", "HEAD").strip()


def test_accepts_additive_edit_and_metadata(tmp_path):
    setup_repository(tmp_path)
    base = commit(tmp_path, card())
    enriched = card(
        body="# TL;DR\n\nDurable claim.[^source]\n\n# More\n\nAdded.\n\n[^source]: Evidence.\n"
    )
    enriched = enriched.replace(
        "resource: https://example.invalid", "resource: https://example.invalid\n    title: Example"
    )
    commit(tmp_path, enriched)
    assert check(tmp_path, base).ok


def test_rejects_metadata_source_verification_heading_and_footnote_loss(tmp_path):
    setup_repository(tmp_path)
    base = commit(tmp_path, card())
    replacement = "---\ntype: Concept\ntitle: Test\n---\nChanged without evidence.\n"
    commit(tmp_path, replacement)
    result = check(tmp_path, base)
    assert not result.ok
    rendered = "\n".join(result.violations)
    for kind in ("frontmatter", "sources", "verification", "headings", "footnotes"):
        assert kind in rendered


def test_rejects_durable_document_deletion(tmp_path):
    setup_repository(tmp_path)
    base = commit(tmp_path, card())
    (tmp_path / "concepts/test.md").unlink()
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "delete")
    result = check(tmp_path, base)
    assert not result.ok
    assert "durable document was deleted" in "\n".join(result.violations)
