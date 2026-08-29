#!/usr/bin/env python3
"""Inspect or create an owner-controlled private GitHub copy of Observatory."""

from __future__ import annotations

import argparse
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

NAME_PATTERN = r"[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98}[A-Za-z0-9])?"
REPOSITORY_RE = re.compile(rf"^{NAME_PATTERN}/{NAME_PATTERN}$")


class SetupError(RuntimeError):
    """A bounded first-run setup check failed."""


def run(command: list[str], root: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, check=check, capture_output=True, text=True)


def git_remote(root: Path, name: str) -> str | None:
    result = run(["git", "remote", "get-url", name], root, check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def authenticated_login(root: Path) -> str | None:
    if shutil.which("gh") is None:
        return None
    status = run(["gh", "auth", "status"], root, check=False)
    if status.returncode != 0:
        return None
    login = run(["gh", "api", "user", "--jq", ".login"], root, check=False)
    return login.stdout.strip() if login.returncode == 0 else None


def version_output(root: Path, executable: str | None) -> str | None:
    if executable is None:
        return None
    result = run([executable, "--version"], root, check=False)
    text = (result.stdout or result.stderr).strip().splitlines()
    return text[0] if result.returncode == 0 and text else None


def node_is_current(version: str | None) -> bool:
    if not version:
        return False
    match = re.search(r"v?(\d+)\.(\d+)", version)
    return bool(match and (int(match.group(1)), int(match.group(2))) >= (22, 12))


def is_public_template(root: Path) -> bool:
    return (root / "START-HERE.md").is_file() and (root / "TEMPLATE_CHECKLIST.md").is_file()


def preflight(root: Path) -> dict[str, object]:
    git = shutil.which("git")
    gh = shutil.which("gh")
    node = shutil.which("node")
    git_version = version_output(root, git)
    gh_version = version_output(root, gh)
    node_version = version_output(root, node)
    return {
        "status": "ready" if git and sys.version_info >= (3, 12) else "missing-required-tools",
        "repository_root": str(root),
        "public_template": is_public_template(root),
        "platform": platform.system(),
        "package_managers": [
            name for name in ("brew", "winget", "apt-get", "dnf", "pacman") if shutil.which(name)
        ],
        "python": {
            "ready": sys.version_info >= (3, 12),
            "version": ".".join(str(part) for part in sys.version_info[:3]),
            "executable": str(Path(sys.executable).resolve()),
        },
        "git": {
            "ready": git is not None,
            "executable": git,
            "version": git_version,
        },
        "github_cli": {
            "ready": gh is not None,
            "executable": gh,
            "version": gh_version,
            "authenticated_login": authenticated_login(root),
        },
        "node_optional": {
            "ready": node_is_current(node_version),
            "executable": node,
            "version": node_version,
            "minimum": "22.12",
        },
        "remotes": {
            "origin": git_remote(root, "origin") if git else None,
            "template": git_remote(root, "template") if git else None,
        },
    }


def validate_repository(value: str) -> str:
    if not REPOSITORY_RE.fullmatch(value):
        raise SetupError("repository must be an exact OWNER/NAME using GitHub-safe characters")
    owner, name = value.split("/", 1)
    if owner in {".", ".."} or name in {".", ".."}:
        raise SetupError("repository owner and name cannot be dot paths")
    return value


def ensure_target_absent(root: Path, repository: str) -> None:
    result = run(["gh", "api", f"repos/{repository}"], root, check=False)
    if result.returncode == 0:
        raise SetupError(f"GitHub repository {repository} already exists; refusing to reuse it")
    combined = f"{result.stdout}\n{result.stderr}".lower()
    if "not found" not in combined and "http 404" not in combined:
        raise SetupError("could not prove the requested GitHub repository name is unused")


def create_private_copy(root: Path, repository: str, confirmation: str | None) -> dict[str, object]:
    repository = validate_repository(repository)
    if confirmation != repository:
        raise SetupError(f"confirmation must exactly match {repository}")
    if not is_public_template(root):
        raise SetupError("private-copy creation is available only from the public template clone")
    if shutil.which("git") is None or shutil.which("gh") is None:
        raise SetupError("Git and authenticated GitHub CLI are required")
    if authenticated_login(root) is None:
        raise SetupError(
            "GitHub CLI is not authenticated; authenticate only with the owner's approval"
        )
    if run(["git", "status", "--porcelain"], root).stdout.strip():
        raise SetupError(
            "working tree is not clean; review or preserve changes before repository setup"
        )

    origin = git_remote(root, "origin")
    template = git_remote(root, "template")
    if origin and template:
        raise SetupError(
            "both origin and template already exist; refusing to guess remote ownership"
        )
    if not origin and not template:
        raise SetupError("no clone source remote exists; refusing to create an untraceable copy")

    ensure_target_absent(root, repository)
    renamed = False
    if origin:
        run(["git", "remote", "rename", "origin", "template"], root)
        renamed = True
    try:
        created = run(
            [
                "gh",
                "repo",
                "create",
                repository,
                "--private",
                "--source",
                str(root),
                "--remote",
                "origin",
                "--push",
            ],
            root,
            check=False,
        )
        if created.returncode != 0:
            raise SetupError("GitHub did not create and push the private repository")
    except Exception:
        if renamed and git_remote(root, "origin") is None and git_remote(root, "template"):
            run(["git", "remote", "rename", "template", "origin"], root, check=False)
        raise

    details_result = run(
        ["gh", "repo", "view", repository, "--json", "isPrivate,url,visibility,nameWithOwner"],
        root,
        check=False,
    )
    if details_result.returncode != 0:
        raise SetupError("private repository was created, but its visibility could not be verified")
    details = json.loads(details_result.stdout)
    if details.get("isPrivate") is not True or details.get("visibility") != "PRIVATE":
        raise SetupError("repository creation returned without verified private visibility")

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    remote_head = run(["git", "ls-remote", "origin", "refs/heads/main"], root, check=False)
    remote_fields = remote_head.stdout.split(maxsplit=1)
    if remote_head.returncode != 0 or not remote_fields or remote_fields[0] != head:
        raise SetupError("private repository exists, but pushed main does not match local HEAD")
    return {"status": "created-private", "repository": details, "head": head}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Check first-run tools or create an explicitly approved private Observatory copy."
        )
    )
    mode = result.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check", action="store_true", help="read-only local prerequisite and remote check"
    )
    mode.add_argument(
        "--create-private",
        action="store_true",
        help="create and verify a new private GitHub copy",
    )
    result.add_argument("--repository", help="exact GitHub OWNER/NAME for the new copy")
    result.add_argument(
        "--confirm-private-create",
        metavar="OWNER/NAME",
        help="exact confirmation token; required for the external create-and-push operation",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        if args.check:
            print(json.dumps(preflight(root), indent=2, sort_keys=True))
            return 0
        if not args.repository:
            raise SetupError("--repository OWNER/NAME is required with --create-private")
        result = create_private_copy(root, args.repository, args.confirm_private_create)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (SetupError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(f"setup blocked: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
