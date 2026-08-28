"""Detect overlapping branch/worktree ownership before agent handoff or merge."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from observatory import corpus

POLICY_PREFIXES = (".observatory/", ".brain/", "skills/")
POLICY_PATHS = frozenset({"AGENTS.md", "SECURITY.md"})


@dataclass(frozen=True, slots=True)
class OverlapResult:
    base_ref: str
    other_ref: str
    current_paths: tuple[str, ...]
    other_paths: tuple[str, ...]
    overlaps: tuple[str, ...]
    high_risk: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.overlaps


def _git(root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _lines(value: str) -> set[str]:
    return {line for line in value.splitlines() if line}


def _ref_changes(root: Path, base_ref: str, ref: str) -> set[str]:
    merge_base = _git(root, "merge-base", base_ref, ref).strip()
    return _lines(_git(root, "diff", "--name-only", merge_base, ref))


def check_overlap(root: Path, base_ref: str, other_ref: str) -> OverlapResult:
    current = _ref_changes(root, base_ref, "HEAD")
    current |= _lines(_git(root, "diff", "--name-only", "HEAD"))
    current |= _lines(_git(root, "ls-files", "--others", "--exclude-standard"))
    other = _ref_changes(root, base_ref, other_ref)
    overlaps = current & other
    high_risk = {
        path
        for path in overlaps
        if path.split("/", 1)[0] in corpus.CANONICAL_DIRS
        or path in POLICY_PATHS
        or path.startswith(POLICY_PREFIXES)
    }
    return OverlapResult(
        base_ref=base_ref,
        other_ref=other_ref,
        current_paths=tuple(sorted(current)),
        other_paths=tuple(sorted(other)),
        overlaps=tuple(sorted(overlaps)),
        high_risk=tuple(sorted(high_risk)),
    )
