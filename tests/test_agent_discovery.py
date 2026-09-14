from __future__ import annotations

import json
from pathlib import Path

import pytest

from observatory.agent_discovery import (
    IntegrationError,
    apply_change,
    plan_change,
    resolve_target,
)
from observatory.cli import main


def make_observatory(root: Path) -> Path:
    root.mkdir()
    (root / "AGENTS.md").write_text("# Instructions\n", encoding="utf-8")
    (root / ".observatory").mkdir()
    return root


def test_resolve_target_uses_provider_global_file(tmp_path: Path):
    assert resolve_target("codex", home=tmp_path) == tmp_path / ".codex/AGENTS.md"
    assert resolve_target("claude", home=tmp_path) == tmp_path / ".claude/CLAUDE.md"
    assert resolve_target("gemini", home=tmp_path) == tmp_path / ".gemini/GEMINI.md"
    assert (
        resolve_target("copilot", home=tmp_path)
        == tmp_path / ".copilot/copilot-instructions.md"
    )


def test_install_appends_managed_block_without_changing_existing_instructions(tmp_path: Path):
    target = tmp_path / "AGENTS.md"
    original = "# My instructions\n\n- Keep this exactly."
    target.write_text(original, encoding="utf-8")

    root = make_observatory(tmp_path / "trusted-observatory")
    preview = plan_change(target, root, action="install")
    assert preview.changed is True
    assert preview.before_sha256
    assert original in preview.after
    assert "BEGIN OBSERVATORY DISCOVERY" in preview.after
    assert str((tmp_path / "trusted-observatory").resolve()) in preview.after

    apply_change(preview, expected_sha256=preview.before_sha256)
    assert target.read_text(encoding="utf-8") == preview.after
    assert target.read_text(encoding="utf-8").startswith(original)


def test_install_is_idempotent(tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    root = make_observatory(tmp_path / "observatory")
    first = plan_change(target, root, action="install")
    apply_change(first, expected_sha256=first.before_sha256)

    second = plan_change(target, root, action="install")
    assert second.changed is False
    assert second.before == second.after


@pytest.mark.parametrize("original", ["", "one line", "one line\n", "one line\n\n"])
def test_uninstall_restores_original_bytes(tmp_path: Path, original: str):
    target = tmp_path / "GEMINI.md"
    target.write_text(original, encoding="utf-8")
    root = make_observatory(tmp_path / "observatory")
    install = plan_change(target, root, action="install")
    apply_change(install, expected_sha256=install.before_sha256)

    uninstall = plan_change(target, root, action="uninstall")
    apply_change(uninstall, expected_sha256=uninstall.before_sha256)
    assert target.read_text(encoding="utf-8") == original


def test_apply_refuses_when_file_changed_after_preview(tmp_path: Path):
    target = tmp_path / "AGENTS.md"
    target.write_text("original\n", encoding="utf-8")
    root = make_observatory(tmp_path / "observatory")
    preview = plan_change(target, root, action="install")
    target.write_text("changed elsewhere\n", encoding="utf-8")

    with pytest.raises(IntegrationError, match="changed since preview"):
        apply_change(preview, expected_sha256=preview.before_sha256)

    assert target.read_text(encoding="utf-8") == "changed elsewhere\n"


def test_malformed_or_duplicate_managed_markers_are_never_rewritten(tmp_path: Path):
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "<!-- BEGIN OBSERVATORY DISCOVERY v1; separator=0 -->\n"
        "broken without an end marker\n",
        encoding="utf-8",
    )
    root = make_observatory(tmp_path / "observatory")

    with pytest.raises(IntegrationError, match="managed markers"):
        plan_change(target, root, action="install")


def test_target_symlink_is_rejected(tmp_path: Path):
    real = tmp_path / "real.md"
    real.write_text("existing", encoding="utf-8")
    target = tmp_path / "AGENTS.md"
    target.symlink_to(real)
    root = make_observatory(tmp_path / "observatory")

    with pytest.raises(IntegrationError, match="symbolic link"):
        plan_change(target, root, action="install")


def test_non_observatory_root_is_rejected(tmp_path: Path):
    root = tmp_path / "ordinary-repository"
    root.mkdir()

    with pytest.raises(IntegrationError, match="no AGENTS.md"):
        plan_change(tmp_path / "global.md", root, action="install")


def test_new_target_is_removed_on_uninstall(tmp_path: Path):
    target = tmp_path / "new" / "AGENTS.md"
    root = make_observatory(tmp_path / "observatory")
    install = plan_change(target, root, action="install")
    apply_change(install, expected_sha256=install.before_sha256)

    uninstall = plan_change(target, root, action="uninstall")
    apply_change(uninstall, expected_sha256=uninstall.before_sha256)
    assert not target.exists()


def test_uninstall_preserves_content_added_outside_managed_block(tmp_path: Path):
    target = tmp_path / "AGENTS.md"
    target.write_text("before", encoding="utf-8")
    root = make_observatory(tmp_path / "observatory")
    install = plan_change(target, root, action="install")
    apply_change(install, expected_sha256=install.before_sha256)
    with target.open("a", encoding="utf-8") as handle:
        handle.write("after\n")

    uninstall = plan_change(target, root, action="uninstall")
    apply_change(uninstall, expected_sha256=uninstall.before_sha256)
    assert target.read_text(encoding="utf-8") == "beforeafter\n"


def test_cli_requires_preview_hash_and_round_trips_existing_file(tmp_path: Path, capsys):
    target = tmp_path / "global.md"
    original = "# Existing global instructions\n"
    target.write_text(original, encoding="utf-8")
    root = make_observatory(tmp_path / "observatory")

    assert (
        main(
            [
                "integrate-agent",
                "preview",
                "--target",
                str(target),
                "--root",
                str(root),
                "--json",
            ]
        )
        == 0
    )
    preview = json.loads(capsys.readouterr().out)
    assert preview["changed"] is True
    assert "BEGIN OBSERVATORY DISCOVERY" in preview["diff"]
    assert target.read_text(encoding="utf-8") == original

    assert (
        main(
            [
                "integrate-agent",
                "install",
                "--target",
                str(target),
                "--root",
                str(root),
            ]
        )
        == 2
    )
    assert "--expected-sha256 is required" in capsys.readouterr().err

    assert (
        main(
            [
                "integrate-agent",
                "install",
                "--target",
                str(target),
                "--root",
                str(root),
                "--expected-sha256",
                preview["before_sha256"],
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "integrate-agent",
                "preview",
                "--remove",
                "--target",
                str(target),
                "--root",
                str(root),
                "--json",
            ]
        )
        == 0
    )
    removal = json.loads(capsys.readouterr().out)
    assert (
        main(
            [
                "integrate-agent",
                "uninstall",
                "--target",
                str(target),
                "--root",
                str(root),
                "--expected-sha256",
                removal["before_sha256"],
            ]
        )
        == 0
    )
    assert target.read_text(encoding="utf-8") == original
