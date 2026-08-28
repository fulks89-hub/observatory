#!/usr/bin/env python3
"""Check local documentation links, setup commands, and release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
NPM_INSTALL_RE = re.compile(r"^\s*npm install\s*$", re.MULTILINE)
BARE_COMMAND_RE = re.compile(r"^\s*(observatory|pytest|ruff|mypy)(?:\s|$)", re.MULTILINE)
BARE_INLINE_COMMAND_RE = re.compile(
    r"`(?:observatory|pytest|ruff|mypy)\s+(?:search|validate|catalog|preserve|"
    r"preserve-request|evaluate-agent|overlap|snapshot|check|src)\b"
)
MANIFEST_ARTIFACTS = {
    "docs/media/observatory-overview.mp4",
    "docs/media/observatory-overview-readme.gif",
    "docs/media/observatory-overview-script.txt",
    "docs/media/observatory-overview.vtt",
}


def tracked_markdown(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.md"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    paths = [Path(line) for line in result.stdout.splitlines() if line]
    user_docs = {"README.md", "START-HERE.md", "SECURITY.md", "TEMPLATE_CHECKLIST.md", "ROADMAP.md"}
    return [
        root / path
        for path in paths
        if path.as_posix() in user_docs
        or path.as_posix() in {"AGENTS.md", "CLAUDE.md"}
        or path.parts[0] == "docs"
        or path.as_posix() == "mission-control/README.md"
        or path.parts[:2] == ("scripts", "demo")
        or path.parts[0] == "skills"
    ]


def without_fenced_code(text: str) -> str:
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            output.append("")
        elif fence is None:
            output.append(line)
        else:
            output.append("")
    return "\n".join(output)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_regular(path: Path, root: Path) -> Path:
    metadata = path.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise OSError("expected a non-symlink regular file")
    resolved = path.resolve(strict=True)
    resolved.relative_to(root)
    return resolved


def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    text = without_fenced_code(path.read_text(encoding="utf-8"))
    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.MULTILINE):
        slug = re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")
        slug = re.sub(r"-+", "-", slug).strip("-")
        duplicate = counts.get(slug, 0)
        counts[slug] = duplicate + 1
        anchors.add(slug if duplicate == 0 else f"{slug}-{duplicate}")
    return anchors


def check(root: Path) -> list[str]:
    errors: list[str] = []
    root = root.resolve()
    markdown = tracked_markdown(root)

    for path in markdown:
        try:
            safe_regular(path, root)
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError) as error:
            errors.append(f"{path.relative_to(root)}: could not read safely ({error})")
            continue
        prose = without_fenced_code(text)
        for raw_target in LINK_RE.findall(prose):
            target = raw_target.strip().strip("<>").split()[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            path_part, separator, fragment = target.partition("#")
            relative = unquote(path_part)
            resolved = path.resolve() if not relative else (path.parent / relative).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(f"{path.relative_to(root)}: link escapes repository: {target}")
                continue
            if not resolved.exists() and not resolved.is_symlink():
                errors.append(f"{path.relative_to(root)}: missing link target: {target}")
            elif separator and fragment and resolved.suffix.lower() == ".md":
                anchor = unquote(fragment).lower()
                try:
                    safe_regular(resolved, root)
                    anchors = markdown_anchors(resolved)
                except (OSError, UnicodeDecodeError, ValueError) as error:
                    errors.append(
                        f"{path.relative_to(root)}: unsafe heading target {target!r} ({error})"
                    )
                    continue
                if anchor not in anchors:
                    errors.append(f"{path.relative_to(root)}: missing heading target: {target}")

        if NPM_INSTALL_RE.search(text):
            errors.append(f"{path.relative_to(root)}: use npm ci for a locked installation")
        if BARE_COMMAND_RE.search(text) or BARE_INLINE_COMMAND_RE.search(text):
            errors.append(f"{path.relative_to(root)}: run Python tools through the project .venv")

        lines = text.splitlines()
        for index, line in enumerate(lines):
            if "github.com/OWNER/observatory" not in line:
                continue
            context = "\n".join(lines[max(0, index - 4) : index])
            if "Replace OWNER" not in context:
                errors.append(
                    f"{path.relative_to(root)}:{index + 1}: "
                    "OWNER placeholder lacks substitution instruction"
                )

    mission_readme = root / "mission-control/README.md"
    if mission_readme.is_file() and "ngrok-policy.example.yml" in mission_readme.read_text():
        example = root / "mission-control/config/ngrok-policy.example.yml"
        if not example.is_file():
            errors.append("mission-control/README.md references a missing ngrok policy example")
        local_ignore = root / "mission-control/.gitignore"
        if (
            not local_ignore.is_file()
            or "config/ngrok-policy.local.yml" not in local_ignore.read_text()
        ):
            errors.append("mission-control local ngrok policy must be ignored")

    manifest_path = root / "docs/media/observatory-overview-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            artifacts = manifest["artifacts"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            errors.append(f"{manifest_path.relative_to(root)}: invalid manifest: {error}")
        else:
            if not isinstance(artifacts, dict) or set(artifacts) != MANIFEST_ARTIFACTS:
                errors.append("demo manifest artifact allowlist is invalid")
                artifacts = {}
            for relative, metadata in artifacts.items():
                artifact = root / relative
                try:
                    safe_regular(artifact, root)
                except (OSError, ValueError):
                    errors.append(f"manifest artifact is missing: {relative}")
                    continue
                if not isinstance(metadata, dict):
                    errors.append(f"manifest artifact metadata is invalid: {relative}")
                elif metadata.get("sha256") != sha256(artifact):
                    errors.append(f"manifest SHA-256 mismatch: {relative}")
                elif metadata.get("bytes") != artifact.stat().st_size:
                    errors.append(f"manifest size mismatch: {relative}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = check(args.root)
    if errors:
        print("Documentation validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
