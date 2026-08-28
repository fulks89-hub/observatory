from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check-documentation.py"
SPEC = importlib.util.spec_from_file_location("check_documentation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def fixture_repo(tmp_path: Path, readme: str) -> Path:
    subprocess.run(["git", "init", "-q", tmp_path], check=True)
    (tmp_path / "README.md").write_text(readme, encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    return tmp_path


def test_accepts_existing_link_and_ignores_fenced_example(tmp_path: Path):
    root = fixture_repo(tmp_path, "[Guide](guide.md#guide)\n\n```md\n[Example](absent.md)\n```\n")
    (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
    subprocess.run(["git", "add", "guide.md"], cwd=root, check=True)
    assert MODULE.check(root) == []


def test_rejects_missing_link_and_unlocked_npm_command(tmp_path: Path):
    root = fixture_repo(tmp_path, "[Missing](missing.md)\n\n```sh\nnpm install\n```\n")
    errors = MODULE.check(root)
    assert any("missing link target" in error for error in errors)
    assert any("npm ci" in error for error in errors)


def test_owner_placeholder_requires_nearby_substitution_instruction(tmp_path: Path):
    root = fixture_repo(tmp_path, "git clone https://github.com/OWNER/observatory.git\n")
    assert any("substitution instruction" in error for error in MODULE.check(root))


def test_rejects_missing_heading_and_bare_project_command(tmp_path: Path):
    root = fixture_repo(tmp_path, "[Guide](guide.md#absent)\n\n```sh\npytest\n```\n")
    (root / "guide.md").write_text("# Guide\n", encoding="utf-8")
    subprocess.run(["git", "add", "guide.md"], cwd=root, check=True)
    errors = MODULE.check(root)
    assert any("missing heading target" in error for error in errors)
    assert any("project .venv" in error for error in errors)


def test_demo_requires_review_and_scans_before_publication():
    builder = (SCRIPT.parent / "demo/build-walkthrough.py").read_text()
    publish_block = builder.split("if args.publish_reviewed:", 1)[1].split("demo_venv =", 1)[0]
    assert "--publish-reviewed" in builder
    assert publish_block.index("denylist_scan(") < publish_block.index("atomic_publish(")


def test_checks_agent_and_skill_markdown_for_bare_commands(tmp_path: Path):
    root = fixture_repo(tmp_path, "# Project\n")
    (root / "AGENTS.md").write_text("Run `observatory validate`.\n", encoding="utf-8")
    skill = root / "skills/example/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("Run `observatory preserve main`.\n", encoding="utf-8")
    subprocess.run(["git", "add", "AGENTS.md", "skills/example/SKILL.md"], cwd=root, check=True)
    errors = MODULE.check(root)
    assert sum("project .venv" in error for error in errors) == 2


def test_rejects_manifest_artifact_path_outside_allowlist(tmp_path: Path):
    root = fixture_repo(tmp_path, "# Project\n")
    media = root / "docs/media"
    media.mkdir(parents=True)
    (media / "observatory-overview-manifest.json").write_text(
        '{"artifacts":{"/etc/hosts":{"sha256":"x","bytes":1}}}', encoding="utf-8"
    )
    subprocess.run(
        ["git", "add", "docs/media/observatory-overview-manifest.json"],
        cwd=root,
        check=True,
    )
    assert any("artifact allowlist" in error for error in MODULE.check(root))
