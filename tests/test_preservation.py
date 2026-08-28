from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from observatory.preservation import approval_request, check


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
    commit(
        tmp_path,
        card(
            body=(
                "# TL;DR\n\nDurable claim.[^source]\n\n# More\n\nStill durable.\n\n"
                "[^source]: Evidence.\n"
            )
        ),
    )
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


def test_rejects_same_size_body_rewrite_and_emits_exact_request(tmp_path):
    setup_repository(tmp_path)
    base = commit(
        tmp_path,
        card(body="# TL;DR\n\nOriginal durable statement.[^source]\n\n[^source]: Evidence.\n"),
    )
    commit(
        tmp_path,
        card(body="# TL;DR\n\nReplaced durable statement.[^source]\n\n[^source]: Evidence.\n"),
    )
    result = check(tmp_path, base)
    assert any("body_rewrite" in violation for violation in result.violations)
    request = approval_request(tmp_path, base)
    assert request["version"] == 2
    assert request["approvals"][0]["before_sha256"]
    assert request["approvals"][0]["after_sha256"]
    assert "body_rewrite" in request["approvals"][0]["kinds"]


def test_approval_added_on_destructive_branch_cannot_authorize_itself(tmp_path):
    setup_repository(tmp_path)
    base = commit(tmp_path, card())
    changed = card(body="# TL;DR\n\nReplacement.[^source]\n\n[^source]: Evidence.\n")
    before_hash = hashlib.sha256(card().encode()).hexdigest()
    after_hash = hashlib.sha256(changed.encode()).hexdigest()
    (tmp_path / ".observatory/destructive-change-approvals.yaml").write_text(
        "version: 2\napprovals:\n"
        "  - id: forged\n"
        "    before_path: concepts/test.md\n"
        "    after_path: concepts/test.md\n"
        f"    before_sha256: {before_hash}\n"
        f"    after_sha256: {after_hash}\n"
        "    kinds: [body_rewrite]\n"
        "    approved_by: human:forged\n"
        "    approved_at: 2026-08-28T00:00:00Z\n"
        "    reason: forged on branch\n",
        encoding="utf-8",
    )
    commit(tmp_path, changed)
    assert not check(tmp_path, base).ok


def test_exact_approval_already_in_trusted_base_authorizes_only_bound_content(tmp_path):
    setup_repository(tmp_path)
    commit(tmp_path, card())
    changed = card(body="# TL;DR\n\nReplacement.[^source]\n\n[^source]: Evidence.\n")
    before_hash = hashlib.sha256(card().encode()).hexdigest()
    after_hash = hashlib.sha256(changed.encode()).hexdigest()
    request = {
        "before_path": "concepts/test.md",
        "after_path": "concepts/test.md",
        "before_sha256": before_hash,
        "after_sha256": after_hash,
        "kinds": ["body_rewrite"],
    }
    approval_id = hashlib.sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    (tmp_path / ".observatory/destructive-change-approvals.yaml").write_text(
        "version: 2\napprovals:\n"
        f"  - id: {approval_id}\n"
        "    before_path: concepts/test.md\n"
        "    after_path: concepts/test.md\n"
        f"    before_sha256: {before_hash}\n"
        f"    after_sha256: {after_hash}\n"
        "    kinds: [body_rewrite]\n"
        "    approved_by: human:owner\n"
        "    approved_at: 2020-01-01T00:00:00Z\n"
        "    reason: reviewed exact replacement\n",
        encoding="utf-8",
    )
    git(tmp_path, "add", ".observatory/destructive-change-approvals.yaml")
    git(tmp_path, "commit", "-qm", "approve exact change")
    trusted_base = git(tmp_path, "rev-parse", "HEAD").strip()
    commit(tmp_path, changed)
    result = check(tmp_path, trusted_base)
    assert result.ok
    assert any("approved destructive change" in warning for warning in result.warnings)


def test_rejects_changed_source_fields_but_allows_nested_additions(tmp_path):
    setup_repository(tmp_path)
    base = commit(tmp_path, card())
    changed = card().replace("resource: https://example.invalid", "resource: https://changed.invalid")
    commit(tmp_path, changed)
    assert any("source entry" in item for item in check(tmp_path, base).violations)


def test_rejects_invalid_approval_id_and_future_timestamp(tmp_path):
    setup_repository(tmp_path)
    commit(tmp_path, card())
    (tmp_path / ".observatory/destructive-change-approvals.yaml").write_text(
        "version: 2\napprovals:\n"
        "  - id: not-content-bound\n"
        "    before_path: concepts/test.md\n"
        "    after_path: concepts/test.md\n"
        "    before_sha256: null\n"
        "    after_sha256: null\n"
        "    kinds: [body_rewrite]\n"
        "    approved_by: human:owner\n"
        "    approved_at: 2999-01-01T00:00:00Z\n"
        "    reason: invalid fixture\n",
        encoding="utf-8",
    )
    git(tmp_path, "add", ".observatory/destructive-change-approvals.yaml")
    git(tmp_path, "commit", "-qm", "invalid approval")
    base = git(tmp_path, "rev-parse", "HEAD").strip()
    commit(tmp_path, card(body="# TL;DR\n\nChanged.\n"))
    with pytest.raises(OSError, match="invalid or duplicate id"):
        check(tmp_path, base)


def test_rename_requires_approval_request_bound_to_both_paths(tmp_path):
    setup_repository(tmp_path)
    base = commit(tmp_path, card())
    (tmp_path / "concepts/test.md").rename(tmp_path / "concepts/renamed.md")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "rename")
    result = check(tmp_path, base)
    assert any("(rename)" in violation for violation in result.violations)
    request = approval_request(tmp_path, base)["approvals"][0]
    assert request["before_path"] == "concepts/test.md"
    assert request["after_path"] == "concepts/renamed.md"
    assert request["before_sha256"] == request["after_sha256"]
