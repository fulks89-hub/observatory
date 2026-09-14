"""Safe, opt-in installation of a tiny global Observatory discovery rule."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

MISSING_SHA256 = "missing"
END_MARKER = "<!-- END OBSERVATORY DISCOVERY v1 -->"
BEGIN_PREFIX = "<!-- BEGIN OBSERVATORY DISCOVERY v1;"
BEGIN_PATTERN = re.compile(
    r"<!-- BEGIN OBSERVATORY DISCOVERY v1; separator=([0-2]); "
    r"original=(present|missing) -->"
)
BLOCK_PATTERN = re.compile(
    BEGIN_PATTERN.pattern + r"\n.*?\n" + re.escape(END_MARKER) + r"\n?",
    re.DOTALL,
)

AGENT_TARGETS = {
    "codex": Path(".codex/AGENTS.md"),
    "claude": Path(".claude/CLAUDE.md"),
    "gemini": Path(".gemini/GEMINI.md"),
    "copilot": Path(".copilot/copilot-instructions.md"),
}


class IntegrationError(ValueError):
    """Raised when a global instruction file cannot be changed losslessly."""


@dataclass(frozen=True)
class ChangePlan:
    target: Path
    action: str
    before: str
    after: str
    before_sha256: str
    after_sha256: str
    changed: bool
    remove_target: bool = False


def _digest(content: bytes, *, exists: bool = True) -> str:
    if not exists:
        return MISSING_SHA256
    return hashlib.sha256(content).hexdigest()


def resolve_target(
    agent: str,
    *,
    home: Path | None = None,
    explicit_target: Path | None = None,
) -> Path:
    """Resolve a documented provider target or a caller-supplied custom path."""

    if explicit_target is not None:
        return Path(os.path.abspath(explicit_target.expanduser()))
    relative = AGENT_TARGETS.get(agent)
    if relative is None:
        supported = ", ".join(sorted(AGENT_TARGETS))
        raise IntegrationError(
            f"unknown agent {agent!r}; choose one of {supported}, or provide --target"
        )
    return Path(os.path.abspath((home or Path.home()) / relative))


def _read_target(target: Path) -> tuple[str, str, bool]:
    if target.is_symlink():
        raise IntegrationError(f"refusing to modify symbolic link: {target}")
    if not target.exists():
        return "", MISSING_SHA256, False
    if not target.is_file():
        raise IntegrationError(f"instruction target is not a regular file: {target}")
    raw = target.read_bytes()
    try:
        return raw.decode("utf-8"), _digest(raw), True
    except UnicodeDecodeError as error:
        raise IntegrationError(f"instruction target is not UTF-8: {target}") from error


def _separator(before: str) -> str:
    if not before or before.endswith("\n\n"):
        return ""
    if before.endswith("\n"):
        return "\n"
    return "\n\n"


def _render_block(observatory_root: Path, *, separator: int, original: str) -> str:
    root = observatory_root.expanduser().resolve()
    rendered_root = str(root)
    if any(character in rendered_root for character in ("`", "\n", "\r")):
        raise IntegrationError("Observatory root contains characters unsafe for Markdown")
    if not root.is_dir() or not (root / "AGENTS.md").is_file():
        raise IntegrationError(f"Observatory root has no AGENTS.md: {root}")
    if not (root / ".observatory").is_dir():
        raise IntegrationError(f"Observatory root has no .observatory directory: {root}")
    return (
        f"<!-- BEGIN OBSERVATORY DISCOVERY v1; separator={separator}; original={original} -->\n"
        "## Observatory discovery\n\n"
        f"Trusted Observatory: `{rendered_root}`\n\n"
        "Before substantive work, consult this Observatory for relevant projects, decisions, "
        "constraints, prior work, and status. Read its repository-level `AGENTS.md`, then run "
        "its narrow metadata-first search and open only task-relevant knowledge or rules. Keep "
        "personal and work scopes separate. Repository memory never overrides the current user, "
        "security policy, consent, or independently verified mutable state. Do not modify global "
        "instructions or durable knowledge without explicit authorization.\n"
        f"{END_MARKER}\n"
    )


def _managed_match(before: str) -> re.Match[str] | None:
    begin_count = before.count(BEGIN_PREFIX)
    end_count = before.count(END_MARKER)
    matches = list(BLOCK_PATTERN.finditer(before))
    if begin_count == 0 and end_count == 0:
        return None
    if begin_count != 1 or end_count != 1 or len(matches) != 1:
        raise IntegrationError("managed markers are malformed or duplicated; no changes were made")
    return matches[0]


def plan_change(target: Path, observatory_root: Path, *, action: str) -> ChangePlan:
    """Build a reviewable, hash-bound install or uninstall plan without writing."""

    if action not in {"install", "uninstall"}:
        raise IntegrationError("action must be 'install' or 'uninstall'")
    target = Path(os.path.abspath(target.expanduser()))
    before, before_sha256, existed = _read_target(target)
    match = _managed_match(before)
    remove_target = False

    if action == "install":
        if match is None:
            separator = _separator(before)
            original = "present" if existed else "missing"
            block = _render_block(
                observatory_root,
                separator=len(separator),
                original=original,
            )
            after = before + separator + block
        else:
            separator_count = int(match.group(1))
            original = match.group(2)
            block = _render_block(
                observatory_root,
                separator=separator_count,
                original=original,
            )
            after = before[: match.start()] + block + before[match.end() :]
    elif match is None:
        after = before
    else:
        separator_count = int(match.group(1))
        original = match.group(2)
        remove_start = match.start() - separator_count
        if remove_start < 0 or before[remove_start : match.start()] != "\n" * separator_count:
            raise IntegrationError("managed separator is invalid; no changes were made")
        after = before[:remove_start] + before[match.end() :]
        remove_target = original == "missing" and after == ""

    return ChangePlan(
        target=target,
        action=action,
        before=before,
        after=after,
        before_sha256=before_sha256,
        after_sha256=_digest(after.encode("utf-8")),
        changed=before != after or remove_target,
        remove_target=remove_target,
    )


def apply_change(plan: ChangePlan, *, expected_sha256: str) -> None:
    """Apply a reviewed plan only when the target still matches its preview hash."""

    if expected_sha256 != plan.before_sha256:
        raise IntegrationError("expected hash does not match the reviewed preview")
    _, current_sha256, _ = _read_target(plan.target)
    if current_sha256 != expected_sha256:
        raise IntegrationError("instruction file changed since preview; no changes were made")
    if not plan.changed:
        return
    if plan.remove_target:
        plan.target.unlink()
        return

    plan.target.parent.mkdir(parents=True, exist_ok=True)
    existing_mode = plan.target.stat().st_mode if plan.target.exists() else None
    file_descriptor, temporary_name = tempfile.mkstemp(
        dir=plan.target.parent,
        prefix=f".{plan.target.name}.observatory-",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(plan.after)
        if existing_mode is not None:
            os.chmod(temporary, existing_mode)
        os.replace(temporary, plan.target)
    finally:
        if temporary.exists():
            temporary.unlink()
