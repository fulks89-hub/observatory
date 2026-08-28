"""OKF profile and likely-secret validation."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from observatory import corpus, privacy
from observatory.safe_files import UnsafePathError, read_regular

LOCAL_TYPES = frozenset(
    {
        "Concept",
        "Source",
        "ResearchDossier",
        "Person",
        "Idea",
        "Question",
        "Project",
        "OperatingPrinciple",
        "OperatingPreference",
        "OperatingLesson",
    }
)
RESERVED = frozenset({"index.md", "log.md"})
STATUS_VALUES = frozenset({"draft", "stable", "deprecated"})
PROJECT_STATUS_VALUES = frozenset({"planning", "active", "paused", "completed", "abandoned"})
ACTOR = re.compile(r"\A(?:human:[^\s]+|process:[^\s]+|[^\s/]+/[^\s/]+)\Z")


@dataclass(frozen=True, slots=True)
class ValidationResult:
    document_count: int
    tracked_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    scanned_count: int = 0
    skipped_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


TrackedFiles = Callable[[Path], Iterable[str]]


def _mapping(value: object) -> dict[str, Any] | None:
    return corpus.stringify_keys(value) if isinstance(value, dict) else None


def _valid_datetime(value: object) -> bool:
    if isinstance(value, dt.datetime):
        return True
    if not isinstance(value, str):
        return False
    try:
        dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return "T" in value


def _valid_date(value: object) -> bool:
    if isinstance(value, dt.datetime):
        return False
    if isinstance(value, dt.date):
        return True
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _validate_event(value: object, label: str, relative: str, errors: list[str]) -> None:
    event = _mapping(value)
    if event is None:
        errors.append(f"{relative}: {label} must be a mapping")
        return
    actor = event.get("by")
    if not isinstance(actor, str) or ACTOR.fullmatch(actor) is None:
        errors.append(f"{relative}: {label}.by must use the OKF actor convention")
    if not _valid_datetime(event.get("at")):
        errors.append(f"{relative}: {label}.at must be an ISO 8601 datetime")


def git_tracked_files(root: Path) -> Iterable[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return sorted(set(completed.stdout.decode().split("\0")) - {""})


def validate(
    root: Path,
    *,
    tracked_files: TrackedFiles = git_tracked_files,
    history: bool = False,
    strict_privacy: bool = False,
) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    identifiers: dict[str, str] = {}
    relationship_targets: list[tuple[str, str, str]] = []
    try:
        files = corpus.paths(root)
    except corpus.CorpusError as error:
        return ValidationResult(0, 0, (str(error),), (), 0, 0)
    known_paths = {path.relative_to(root).as_posix() for path in files}

    for path in files:
        relative = path.relative_to(root).as_posix()
        try:
            document = corpus.read(path, root=root)
        except corpus.CorpusError as error:
            errors.append(f"{relative}: {error}")
            continue
        data = document.frontmatter
        document_type = data.get("type")
        if not isinstance(document_type, str) or not document_type.strip():
            errors.append(f"{relative}: missing non-empty type")
        elif document_type not in LOCAL_TYPES:
            warnings.append(
                f"{relative}: type {document_type!r} is outside the local ontology "
                "(valid OKF extension)"
            )
        if path.name in RESERVED:
            errors.append(f"{relative}: reserved filename may not be a concept document")

        tags = data.get("tags")
        if tags is not None and (
            not isinstance(tags, list)
            or any(not isinstance(tag, str) or not tag.strip() for tag in tags)
        ):
            errors.append(f"{relative}: tags must be a sequence of non-empty strings")

        sources = data.get("sources")
        if sources is not None:
            if not isinstance(sources, list):
                errors.append(f"{relative}: sources must be a YAML sequence")
            source_ids: set[object] = set()
            for index, source_value in enumerate(sources if isinstance(sources, list) else []):
                source = _mapping(source_value)
                if source is None:
                    errors.append(f"{relative}: sources[{index}] must be a mapping")
                    continue
                resource = source.get("resource")
                if not isinstance(resource, str) or not resource.strip():
                    errors.append(f"{relative}: sources[{index}].resource is required")
                source_id = source.get("id")
                if source_id is not None:
                    if source_id in source_ids:
                        errors.append(f"{relative}: duplicate source id {source_id!r}")
                    source_ids.add(source_id)

        if "generated" in data:
            _validate_event(data["generated"], "generated", relative, errors)
        if "verified" in data:
            verified = (
                data["verified"] if isinstance(data["verified"], list) else [data["verified"]]
            )
            if not verified:
                errors.append(f"{relative}: verified must not be an empty list")
            for index, event in enumerate(verified):
                _validate_event(event, f"verified[{index}]", relative, errors)
        if "status" in data and data["status"] not in STATUS_VALUES:
            errors.append(f"{relative}: status must be draft, stable, or deprecated")
        if "project_status" in data and (
            document_type != "Project" or data["project_status"] not in PROJECT_STATUS_VALUES
        ):
            errors.append(
                f"{relative}: project_status is only valid on Project documents and must use a "
                "configured portfolio status"
            )
        if "stale_after" in data and not _valid_date(data["stale_after"]):
            errors.append(f"{relative}: stale_after must be YYYY-MM-DD")
        for field in ("valid_from", "valid_until"):
            if field in data and not _valid_date(data[field]):
                errors.append(f"{relative}: {field} must be YYYY-MM-DD")
        valid_from = data.get("valid_from")
        valid_until = data.get("valid_until")
        if _valid_date(valid_from) and _valid_date(valid_until):
            start = dt.date.fromisoformat(str(valid_from))
            end = dt.date.fromisoformat(str(valid_until))
            if end < start:
                errors.append(f"{relative}: valid_until must not precede valid_from")

        if data.get("id") is not None:
            identifier = str(data["id"])
            if identifier in identifiers:
                errors.append(
                    f"{relative}: duplicate id {identifier!r} (also {identifiers[identifier]})"
                )
            identifiers[identifier] = relative

        for field in ("supersedes", "conflicts_with"):
            value = data.get(field)
            if value is None:
                continue
            if not isinstance(value, list) or any(
                not isinstance(target, str) or not target.strip() for target in value
            ):
                errors.append(f"{relative}: {field} must be a sequence of non-empty document ids")
                continue
            if len(value) != len(set(value)):
                errors.append(f"{relative}: {field} must not contain duplicate document ids")
            for target in value:
                relationship_targets.append((relative, field, target))
                if data.get("id") == target:
                    errors.append(f"{relative}: {field} must not reference the document itself")

        links = corpus.resolve_links(document, root=root, known_paths=known_paths)
        warnings.extend(f"{relative}: broken internal link {target!r}" for target in links.broken)
        warnings.extend(f"{relative}: ambiguous wikilink {target!r}" for target in links.ambiguous)
        warnings.extend(
            f"{relative}: internal link escapes repository {target!r}" for target in links.escaped
        )

    for relative, field, target in relationship_targets:
        if target not in identifiers:
            warnings.append(f"{relative}: {field} references unknown document id {target!r}")

    index_path = root / "index.md"
    if index_path.exists() or index_path.is_symlink():
        try:
            index_text = read_regular(index_path, boundary=root).decode("utf-8")
        except (UnsafePathError, UnicodeDecodeError) as error:
            errors.append(f"index.md: could not read safely ({error})")
            index_text = ""
        match = corpus.FRONTMATTER.match(index_text)
        if match is not None:
            try:
                index_data = yaml.safe_load(match.group(1))
            except yaml.YAMLError as error:
                errors.append(f"index.md: invalid YAML ({str(error).splitlines()[0]})")
            else:
                if not isinstance(index_data, dict) or {str(key) for key in index_data} - {
                    "okf_version"
                }:
                    errors.append("index.md: root index frontmatter may contain only okf_version")
                if not isinstance(index_data, dict) or str(index_data.get("okf_version")) != "0.2":
                    errors.append('index.md: okf_version must be "0.2"')

    tracked = list(tracked_files(root))
    scans = [privacy.scan_current(root, tracked)]
    if history:
        scans.append(privacy.scan_history(root))
    for scan in scans:
        for finding in scan.findings:
            message = f"{finding.location}: possible {finding.kind}"
            (errors if finding.secret or strict_privacy else warnings).append(message)
        errors.extend(f"privacy scan incomplete: {item}" for item in scan.skipped)

    return ValidationResult(
        document_count=len(files),
        tracked_count=len(tracked),
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
        scanned_count=sum(scan.scanned_count for scan in scans),
        skipped_count=sum(len(scan.skipped) for scan in scans),
    )
