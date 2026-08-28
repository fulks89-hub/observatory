"""Guard durable knowledge against unapproved destructive changes."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from observatory import corpus

KNOWN_OKF_AND_LOCAL_FIELDS = frozenset(
    {
        "type",
        "title",
        "description",
        "tags",
        "aliases",
        "id",
        "sources",
        "generated",
        "verified",
        "status",
        "stale_after",
        "valid_from",
        "valid_until",
        "supersedes",
        "conflicts_with",
        "projects",
        "project_status",
        "created",
        "updated",
        "owners",
        "license",
    }
)


@dataclass(frozen=True, slots=True)
class PreservationResult:
    base: str
    head: str
    merge_base: str
    changed_count: int
    violations: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.violations


GitRunner = Callable[[Sequence[str]], str]


def _runner(root: Path) -> GitRunner:
    def run(arguments: Sequence[str]) -> str:
        completed = subprocess.run(
            ["git", "-C", str(root), *arguments], check=True, capture_output=True, text=True
        )
        return completed.stdout

    return run


def _flatten_keys(
    value: object, prefix: str | None = None, result: dict[str, Any] | None = None
) -> dict[str, Any]:
    flattened = {} if result is None else result
    if not isinstance(value, dict):
        return flattened
    for key, child in value.items():
        path = ".".join(item for item in (prefix, str(key)) if item)
        flattened[path] = child
        _flatten_keys(child, path, flattened)
    return flattened


def _source_identities(value: object) -> set[tuple[str, str]]:
    identities: set[tuple[str, str]] = set()
    for entry in value if isinstance(value, list) else []:
        if not isinstance(entry, dict):
            continue
        normalized = corpus.stringify_keys(entry)
        if normalized.get("id") is not None:
            identities.add(("id", str(normalized["id"])))
        else:
            identities.add(("resource", str(normalized.get("resource") or "")))
    return identities


def _verification_identities(value: object) -> set[tuple[str, str]]:
    entries = value if isinstance(value, list) else [value]
    return {
        (str(entry.get("by") or ""), str(entry.get("at") or ""))
        for entry in entries
        if isinstance(entry, dict)
    }


def _headings(body: str) -> set[str]:
    return {heading.strip() for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", body, re.MULTILINE)}


def _footnotes(body: str) -> set[str]:
    return set(re.findall(r"^\[\^([^\]]+)\]:", body, re.MULTILINE))


def check(root: Path, base_ref: str, *, git: GitRunner | None = None) -> PreservationResult:
    run = git or _runner(root)
    base = run(["rev-parse", f"{base_ref}^{{commit}}"]).strip()
    head = run(["rev-parse", "HEAD^{commit}"]).strip()
    merge_base = run(["merge-base", base, head]).strip()
    approval_path = root / ".observatory/destructive-change-approvals.yaml"
    if not approval_path.is_file():
        approval_path = root / ".brain/destructive-change-approvals.yaml"
    approval_data = yaml.safe_load(approval_path.read_text(encoding="utf-8")) or {}
    approvals = approval_data.get("approvals", []) if isinstance(approval_data, dict) else []
    warnings: list[str] = []
    violations: list[str] = []

    def approved(path: str, kind: str) -> bool:
        if not isinstance(approvals, list):
            return False
        for approval in approvals:
            if not isinstance(approval, dict):
                continue
            kinds = approval.get("kinds")
            if (
                approval.get("path") == path
                and approval.get("base_commit") == merge_base
                and isinstance(kinds, list)
                and kind in kinds
                and str(approval.get("approved_by") or "").startswith("human:")
                and bool(str(approval.get("reason") or "").strip())
            ):
                return True
        return False

    def report(path: str, kind: str, detail: str) -> None:
        message = f"{path}: {detail} ({kind})"
        if approved(path, kind):
            warnings.append(f"approved destructive change: {message}")
        else:
            violations.append(message)

    changed_lines = run(["diff", "--name-status", "--find-renames", merge_base, head]).splitlines()
    for line in changed_lines:
        fields = line.split("\t")
        status, file_paths = fields[0], fields[1:]
        before_path = file_paths[0]
        after_path = file_paths[1] if status.startswith("R") else before_path
        if before_path.split("/", 1)[0] not in corpus.CANONICAL_DIRS:
            continue
        if status == "D":
            report(before_path, "delete", "durable document was deleted")
            continue
        if status == "A":
            continue
        try:
            before_text = run(["show", f"{merge_base}:{before_path}"])
            after_file = root / after_path
            if not after_file.is_file():
                continue
            before = corpus.parse_document(before_text, path=Path("before.md"), root=Path("."))
            after = corpus.read(after_file, root=root)
        except corpus.CorpusError as error:
            violations.append(f"{after_path}: preservation comparison failed ({error})")
            continue

        before_keys = _flatten_keys(before.frontmatter)
        after_keys = _flatten_keys(after.frontmatter)
        for key in sorted(before_keys.keys() - after_keys.keys()):
            report(after_path, "frontmatter", f"frontmatter field {key!r} was removed")
        if before.frontmatter.get("id") and before.frontmatter.get("id") != after.frontmatter.get(
            "id"
        ):
            report(after_path, "frontmatter", "stable document id was changed")
        for key in before.frontmatter.keys() - KNOWN_OKF_AND_LOCAL_FIELDS:
            if key in after.frontmatter and before.frontmatter[key] != after.frontmatter[key]:
                report(after_path, "frontmatter", f"unknown extension field {key!r} was changed")
        for _identity in _source_identities(before.frontmatter.get("sources")) - _source_identities(
            after.frontmatter.get("sources")
        ):
            report(after_path, "sources", "a source entry was removed or changed")
        for _identity in _verification_identities(
            before.frontmatter.get("verified")
        ) - _verification_identities(after.frontmatter.get("verified")):
            report(after_path, "verification", "a verification event was removed or changed")
        for identifier in _footnotes(before.body) - _footnotes(after.body):
            report(after_path, "footnotes", f"claim footnote {identifier!r} was removed")
        for heading in _headings(before.body) - _headings(after.body):
            report(after_path, "headings", f"heading {heading!r} was removed")
        if len(before.body) >= 500 and len(after.body) < len(before.body) / 2:
            report(
                after_path,
                "body_reduction",
                f"body shrank from {len(before.body)} to {len(after.body)} bytes",
            )

    return PreservationResult(
        base=base,
        head=head,
        merge_base=merge_base,
        changed_count=len(changed_lines),
        violations=tuple(dict.fromkeys(violations)),
        warnings=tuple(dict.fromkeys(warnings)),
    )
