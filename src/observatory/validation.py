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

from observatory import corpus

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
SECRET_PATTERNS = {
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"\bgh[opusr]_[A-Za-z0-9]{30,}\b"),
    "AWS access key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "generic assigned secret": re.compile(
        rb"(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[A-Za-z0-9_/+.-]{20,}",
        re.IGNORECASE,
    ),
}


@dataclass(frozen=True, slots=True)
class ValidationResult:
    document_count: int
    tracked_count: int
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

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


def validate(root: Path, *, tracked_files: TrackedFiles = git_tracked_files) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    identifiers: dict[str, str] = {}
    relationship_targets: list[tuple[str, str, str]] = []
    files = corpus.paths(root)

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

        for target in corpus.MARKDOWN_LINK.findall(document.text):
            if re.match(r"\A(?:https?:|mailto:|#)", target, re.IGNORECASE):
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            resolved = (
                root / clean.removeprefix("/") if clean.startswith("/") else path.parent / clean
            )
            if not resolved.exists():
                warnings.append(f"{relative}: broken internal link {target!r}")

    for relative, field, target in relationship_targets:
        if target not in identifiers:
            warnings.append(f"{relative}: {field} references unknown document id {target!r}")

    index_path = root / "index.md"
    if index_path.exists():
        match = corpus.FRONTMATTER.match(index_path.read_text(encoding="utf-8"))
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
    for relative in tracked:
        path = root / relative
        if not path.is_file() or path.stat().st_size >= 2_000_000:
            continue
        content = path.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                errors.append(f"{relative}: possible {label}")

    return ValidationResult(
        document_count=len(files),
        tracked_count=len(tracked),
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
    )
