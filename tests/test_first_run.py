from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/create_private_copy.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("create_private_copy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def completed(command, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(command, returncode, stdout, stderr)


def test_repository_identity_validation_and_exact_confirmation():
    helper = load_helper()
    assert helper.validate_repository("friend/my-observatory") == "friend/my-observatory"
    for invalid in ("owner", "/repo", "owner/", "owner name/repo", "owner/repo name"):
        with pytest.raises(helper.SetupError):
            helper.validate_repository(invalid)
    with pytest.raises(helper.SetupError, match="confirmation must exactly match"):
        helper.create_private_copy(ROOT, "friend/my-observatory", "friend/other")


def test_private_copy_creation_refuses_a_non_template_repository(tmp_path):
    helper = load_helper()
    with pytest.raises(helper.SetupError, match="only from the public template"):
        helper.create_private_copy(tmp_path, "friend/my-observatory", "friend/my-observatory")


def test_read_only_preflight_reports_tools_and_remotes(monkeypatch):
    helper = load_helper()
    monkeypatch.setattr(helper.shutil, "which", lambda name: f"/safe/{name}")
    monkeypatch.setattr(helper, "authenticated_login", lambda root: "friend")
    monkeypatch.setattr(
        helper,
        "version_output",
        lambda root, executable: "v22.12.0" if executable.endswith("node") else "ready 1.0",
    )
    monkeypatch.setattr(
        helper,
        "git_remote",
        lambda root, name: (
            "https://github.com/fulks89-hub/observatory.git" if name == "origin" else None
        ),
    )

    report = helper.preflight(ROOT)

    assert report["status"] == "ready"
    assert report["git"]["ready"] is True
    assert report["github_cli"]["authenticated_login"] == "friend"
    assert report["node_optional"]["ready"] is True
    assert report["remotes"]["origin"].endswith("/observatory.git")
    assert report["remotes"]["template"] is None


def test_private_copy_creation_is_exact_consent_gated_and_verified(monkeypatch, tmp_path):
    helper = load_helper()
    (tmp_path / "START-HERE.md").touch()
    (tmp_path / "TEMPLATE_CHECKLIST.md").touch()
    state = {
        "origin": "https://github.com/fulks89-hub/observatory.git",
        "template": None,
    }
    commands = []
    head = "a" * 40

    monkeypatch.setattr(helper.shutil, "which", lambda name: f"/safe/{name}")
    monkeypatch.setattr(helper, "authenticated_login", lambda root: "friend")
    monkeypatch.setattr(helper, "git_remote", lambda root, name: state[name])

    def fake_run(command, root, check=True):
        commands.append(command)
        if command[:3] == ["git", "status", "--porcelain"]:
            return completed(command)
        if command[:3] == ["gh", "api", "repos/friend/my-observatory"]:
            return completed(command, 1, stderr="HTTP 404: Not Found")
        if command[:4] == ["git", "remote", "rename", "origin"]:
            state["template"] = state["origin"]
            state["origin"] = None
            return completed(command)
        if command[:3] == ["gh", "repo", "create"]:
            assert "--private" in command
            assert "--push" in command
            state["origin"] = "https://github.com/friend/my-observatory.git"
            return completed(command)
        if command[:3] == ["gh", "repo", "view"]:
            return completed(
                command,
                stdout=json.dumps(
                    {
                        "isPrivate": True,
                        "visibility": "PRIVATE",
                        "url": "https://github.com/friend/my-observatory",
                        "nameWithOwner": "friend/my-observatory",
                    }
                ),
            )
        if command[:3] == ["git", "rev-parse", "HEAD"]:
            return completed(command, stdout=f"{head}\n")
        if command[:3] == ["git", "ls-remote", "origin"]:
            return completed(command, stdout=f"{head}\trefs/heads/main\n")
        raise AssertionError(command)

    monkeypatch.setattr(helper, "run", fake_run)
    result = helper.create_private_copy(tmp_path, "friend/my-observatory", "friend/my-observatory")

    assert result["status"] == "created-private"
    assert result["head"] == head
    assert state["template"].endswith("/fulks89-hub/observatory.git")
    assert state["origin"].endswith("/friend/my-observatory.git")
    assert not any("delete" in part for command in commands for part in command)


def test_local_only_setup_is_exact_consent_gated_and_removes_template_remote(
    monkeypatch, tmp_path
):
    helper = load_helper()
    (tmp_path / "START-HERE.md").touch()
    (tmp_path / "TEMPLATE_CHECKLIST.md").touch()
    state = {"origin": "https://github.com/fulks89-hub/observatory.git"}
    commands = []

    monkeypatch.setattr(helper.shutil, "which", lambda name: f"/safe/{name}")
    monkeypatch.setattr(helper, "git_remote", lambda root, name: state.get(name))
    monkeypatch.setattr(helper, "git_remote_names", lambda root: sorted(state))

    def fake_run(command, root, check=True):
        commands.append(command)
        if command[:3] == ["git", "status", "--porcelain"]:
            return completed(command)
        if command == ["git", "remote", "remove", "origin"]:
            del state["origin"]
            return completed(command)
        raise AssertionError(command)

    monkeypatch.setattr(helper, "run", fake_run)
    with pytest.raises(helper.SetupError, match="confirmation must exactly match"):
        helper.prepare_local_only(tmp_path, "yes")

    result = helper.prepare_local_only(tmp_path, helper.LOCAL_ONLY_CONFIRMATION)

    assert result["status"] == "prepared-local-only"
    assert result["remotes"] == []
    assert result["remote_backup"] is False
    assert ["git", "remote", "remove", "origin"] in commands


def test_first_run_skill_orders_identity_and_write_approvals():
    skill = (ROOT / "skills/onboard-observatory/SKILL.md").read_text()
    reference = (ROOT / "skills/onboard-observatory/references/first-run-bootstrap.md").read_text()
    assert "What should this Observatory be called?" in skill
    assert "Who or which organization should own" in reference
    assert "Would you prefer local-only storage or a private GitHub repository?" in skill
    assert "--confirm-local-only LOCAL-ONLY-NO-REMOTE" in reference
    assert skill.index("What should this Observatory be called?") < skill.index(
        "Which single knowledge or repository root should I inventory first?"
    )
    assert "--confirm-private-create OWNER/NAME" in reference
    assert "before asking permission to run `gh auth login`" in reference
    assert "cannot be undone by the local file snapshot mechanism" in reference
