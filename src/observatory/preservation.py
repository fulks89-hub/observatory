"""Guard durable knowledge against unapproved destructive changes."""

from __future__ import annotations

import hashlib
import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
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


class PreservationError(OSError):
    """The preservation comparison could not be performed safely."""


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


def _source_entries(value: object) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for entry in value if isinstance(value, list) else []:
        if not isinstance(entry, dict):
            continue
        normalized = corpus.stringify_keys(entry)
        entries.append(normalized)
    return entries


def _mapping_is_additive(before: dict[str, Any], after: dict[str, Any]) -> bool:
    """Allow added source detail while preserving every prior nested value exactly."""
    for key, value in before.items():
        if key not in after:
            return False
        candidate = after[key]
        if isinstance(value, dict) and isinstance(candidate, dict):
            if not _mapping_is_additive(value, candidate):
                return False
        elif value != candidate:
            return False
    return True


def _removed_or_changed_sources(before: object, after: object) -> list[dict[str, Any]]:
    remaining = _source_entries(after)
    missing: list[dict[str, Any]] = []
    for expected in _source_entries(before):
        match = next(
            (
                index
                for index, candidate in enumerate(remaining)
                if _mapping_is_additive(expected, candidate)
            ),
            None,
        )
        if match is None:
            missing.append(expected)
        else:
            remaining.pop(match)
    return missing


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


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _is_additive(before: str, after: str) -> bool:
    retained = iter(line.strip() for line in after.splitlines() if line.strip())
    for expected in (line.strip() for line in before.splitlines() if line.strip()):
        if not any(candidate == expected for candidate in retained):
            return False
    return True


def _base_approvals(run: GitRunner, merge_base: str) -> tuple[list[object], list[str]]:
    warnings: list[str] = []
    rendered: str | None = None
    for candidate in (
        ".observatory/destructive-change-approvals.yaml",
        ".brain/destructive-change-approvals.yaml",
    ):
        try:
            rendered = run(["show", f"{merge_base}:{candidate}"])
            break
        except subprocess.CalledProcessError:
            continue
    if rendered is None:
        return [], warnings
    try:
        data = yaml.safe_load(rendered) or {}
    except yaml.YAMLError as error:
        raise PreservationError("trusted-base approval file is invalid YAML") from error
    if not isinstance(data, dict) or not isinstance(data.get("approvals", []), list):
        raise PreservationError("trusted-base approval file has an invalid schema")
    if data.get("version") == 1 and data.get("approvals"):
        warnings.append("version 1 destructive approvals cannot authorize exact-content changes")
        return [], warnings
    if data.get("version") not in {1, 2}:
        raise PreservationError("trusted-base approval schema version is unsupported")
    approvals = list(data.get("approvals", []))
    if data.get("version") == 2:
        trusted_at_text = run(["show", "-s", "--format=%cI", merge_base]).strip()
        try:
            trusted_at = datetime.fromisoformat(trusted_at_text.replace("Z", "+00:00"))
        except ValueError as error:
            raise PreservationError("trusted-base commit has an invalid timestamp") from error
        seen_ids: set[str] = set()
        for approval in approvals:
            if not isinstance(approval, dict):
                raise PreservationError("trusted-base approval entry must be a mapping")
            request_material = {
                name: approval.get(name)
                for name in (
                    "before_path",
                    "after_path",
                    "before_sha256",
                    "after_sha256",
                    "kinds",
                )
            }
            expected_id = hashlib.sha256(_canonical_request(request_material)).hexdigest()
            approval_id = approval.get("id")
            if approval_id != expected_id or approval_id in seen_ids:
                raise PreservationError("trusted-base approval has an invalid or duplicate id")
            seen_ids.add(expected_id)
            approved_by = str(approval.get("approved_by") or "")
            if (
                re.fullmatch(r"human:[^<>\s]+", approved_by) is None
                or not str(approval.get("reason") or "").strip()
            ):
                raise PreservationError(
                    "trusted-base approval lacks a valid human reviewer or reason"
                )
            approved_at_text = str(approval.get("approved_at") or "")
            try:
                approved_at = datetime.fromisoformat(approved_at_text.replace("Z", "+00:00"))
            except ValueError as error:
                raise PreservationError(
                    "trusted-base approval has an invalid ISO-8601 timestamp"
                ) from error
            if approved_at.tzinfo is None or approved_at > trusted_at:
                raise PreservationError(
                    "trusted-base approval timestamp must be timezone-aware and no later "
                    "than its commit"
                )
    return approvals, warnings


def check(root: Path, base_ref: str, *, git: GitRunner | None = None) -> PreservationResult:
    run = git or _runner(root)
    base = run(["rev-parse", f"{base_ref}^{{commit}}"]).strip()
    head = run(["rev-parse", "HEAD^{commit}"]).strip()
    merge_base = run(["merge-base", base, head]).strip()
    approvals, approval_warnings = _base_approvals(run, merge_base)
    warnings: list[str] = list(approval_warnings)
    violations: list[str] = []

    context: dict[str, str | None] = {}

    def approved(path: str, kind: str) -> bool:
        if not isinstance(approvals, list):
            return False
        for approval in approvals:
            if not isinstance(approval, dict):
                continue
            kinds = approval.get("kinds")
            if (
                approval.get("before_path") == context.get("before_path")
                and approval.get("after_path") == context.get("after_path")
                and approval.get("before_sha256") == context.get("before_sha256")
                and approval.get("after_sha256") == context.get("after_sha256")
                and isinstance(kinds, list)
                and kind in kinds
                and str(approval.get("approved_by") or "").startswith("human:")
                and bool(str(approval.get("approved_at") or "").strip())
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
            before_text = run(["show", f"{merge_base}:{before_path}"])
            context.clear()
            context.update(
                before_path=before_path,
                after_path=None,
                before_sha256=_sha256(before_text),
                after_sha256=None,
            )
            report(before_path, "delete", "durable document was deleted")
            continue
        if status == "A":
            continue
        try:
            before_text = run(["show", f"{merge_base}:{before_path}"])
            after_text = run(["show", f"{head}:{after_path}"])
            context.clear()
            context.update(
                before_path=before_path,
                after_path=after_path,
                before_sha256=_sha256(before_text),
                after_sha256=_sha256(after_text),
            )
            before = corpus.parse_document(before_text, path=Path("before.md"), root=Path("."))
            after = corpus.parse_document(after_text, path=Path(after_path), root=Path("."))
        except corpus.CorpusError as error:
            violations.append(f"{after_path}: preservation comparison failed ({error})")
            continue

        if status.startswith("R"):
            report(after_path, "rename", f"durable document moved from {before_path!r}")

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
        for _entry in _removed_or_changed_sources(
            before.frontmatter.get("sources"), after.frontmatter.get("sources")
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
        if not _is_additive(before.body, after.body):
            report(
                after_path,
                "body_rewrite",
                "existing substantive body content was changed or removed",
            )
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


def approval_request(root: Path, base_ref: str, *, git: GitRunner | None = None) -> dict[str, Any]:
    """Return an exact-content request suitable for separate trusted-base approval."""
    run = git or _runner(root)
    result = check(root, base_ref, git=run)
    path_mapping: dict[str, tuple[str, str | None]] = {}
    changed_lines = run(
        ["diff", "--name-status", "--find-renames", result.merge_base, result.head]
    ).splitlines()
    for line in changed_lines:
        fields = line.split("\t")
        status, paths = fields[0], fields[1:]
        if status.startswith("R"):
            path_mapping[paths[1]] = (paths[0], paths[1])
        elif status == "D":
            path_mapping[paths[0]] = (paths[0], None)
        elif paths:
            path_mapping[paths[0]] = (paths[0], paths[0])
    changes: dict[str, dict[str, Any]] = {}
    for violation in result.violations:
        path, _, detail = violation.partition(": ")
        kind_match = re.search(r" \(([^()]+)\)$", detail)
        if kind_match is None:
            continue
        kind = kind_match.group(1)
        before_path, after_path = path_mapping.get(path, (path, path))
        try:
            before_text = run(["show", f"{result.merge_base}:{before_path}"])
            before_hash: str | None = _sha256(before_text)
        except subprocess.CalledProcessError:
            before_hash = None
        try:
            if after_path is None:
                raise subprocess.CalledProcessError(1, ["git", "show"])
            after_text = run(["show", f"{result.head}:{after_path}"])
            after_hash: str | None = _sha256(after_text)
        except subprocess.CalledProcessError:
            after_path = None
            after_hash = None
        key = f"{before_path}\0{after_path}\0{before_hash}\0{after_hash}"
        entry = changes.setdefault(
            key,
            {
                "before_path": before_path,
                "after_path": after_path,
                "before_sha256": before_hash,
                "after_sha256": after_hash,
                "kinds": [],
            },
        )
        entry["kinds"].append(kind)
    rendered_changes: list[dict[str, Any]] = []
    for _key, entry in sorted(changes.items()):
        entry["kinds"] = sorted(set(entry["kinds"]))
        request_material = {
            name: entry[name]
            for name in ("before_path", "after_path", "before_sha256", "after_sha256", "kinds")
        }
        entry["id"] = hashlib.sha256(_canonical_request(request_material)).hexdigest()
        entry["approved_by"] = "human:<identifier>"
        entry["approved_at"] = "<ISO-8601 datetime>"
        entry["reason"] = "<why this exact destructive change is intentional>"
        rendered_changes.append(entry)
    return {
        "version": 2,
        "base_commit": result.merge_base,
        "head_commit": result.head,
        "approvals": rendered_changes,
    }


def _canonical_request(value: dict[str, Any]) -> bytes:
    import json

    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
