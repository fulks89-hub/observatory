"""Typed access to canonical OKF Markdown documents."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml
from yaml.tokens import AliasToken

CANONICAL_DIRS = (
    "concepts",
    "sources",
    "research",
    "people",
    "ideas",
    "questions",
    "projects",
    "personal-operating-model",
)
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
WIKILINK = re.compile(r"!?\[\[([^\]]+)\]\]")

type Frontmatter = dict[str, Any]


class CorpusError(ValueError):
    """A canonical document could not be parsed safely."""


@dataclass(frozen=True, slots=True)
class Document:
    path: Path
    relative_path: str
    frontmatter: Frontmatter
    body: str
    text: str


def paths(root: Path) -> list[Path]:
    """Return canonical Markdown paths in deterministic order."""
    discovered: list[Path] = []
    for directory in CANONICAL_DIRS:
        start = root / directory
        if start.is_symlink():
            raise CorpusError(f"{directory}: symbolic-link corpus directories are not allowed")
        if not start.exists():
            continue
        for current, directories, files in os.walk(start, followlinks=False):
            current_path = Path(current)
            for name in list(directories):
                child = current_path / name
                if child.is_symlink():
                    relative = child.relative_to(root).as_posix()
                    raise CorpusError(f"{relative}: symbolic-link directories are not allowed")
            for name in files:
                child = current_path / name
                mode = child.lstat().st_mode
                if stat.S_ISLNK(mode):
                    relative = child.relative_to(root).as_posix()
                    raise CorpusError(f"{relative}: symbolic-link corpus entries are not allowed")
                if not name.endswith(".md"):
                    continue
                if not stat.S_ISREG(mode):
                    raise CorpusError(
                        f"{child.relative_to(root).as_posix()}: Markdown must be a regular file"
                    )
                try:
                    child.resolve(strict=True).relative_to(root.resolve(strict=True))
                except (OSError, ValueError) as error:
                    raise CorpusError(
                        f"{child.relative_to(root).as_posix()}: path escapes the corpus root"
                    ) from error
                discovered.append(child)
    return sorted(discovered)


def stringify_keys(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): stringify_keys(child) for key, child in value.items()}
    if isinstance(value, list):
        return [stringify_keys(child) for child in value]
    return value


def _load_yaml(source: str) -> Frontmatter:
    try:
        if any(isinstance(token, AliasToken) for token in yaml.scan(source)):
            raise CorpusError("invalid YAML (aliases are not allowed)")
        value = yaml.safe_load(source)
    except CorpusError:
        raise
    except yaml.YAMLError as error:
        first_line = str(error).splitlines()[0]
        raise CorpusError(f"invalid YAML ({first_line})") from error
    if not isinstance(value, dict):
        raise CorpusError("frontmatter must be a mapping")
    return cast(Frontmatter, stringify_keys(value))


def parse_document(text: str, *, path: Path, root: Path) -> Document:
    match = FRONTMATTER.match(text)
    if match is None:
        raise CorpusError("missing YAML frontmatter")
    frontmatter = _load_yaml(match.group(1))
    return Document(
        path=path,
        relative_path=path.relative_to(root).as_posix(),
        frontmatter=frontmatter,
        body=text[match.end() :],
        text=text,
    )


def read(path: Path, *, root: Path) -> Document:
    from observatory.safe_files import UnsafePathError, read_regular

    try:
        text = read_regular(path, boundary=root).decode("utf-8")
    except (UnsafePathError, UnicodeDecodeError) as error:
        raise CorpusError(str(error)) from error
    return parse_document(text, path=path, root=root)


@dataclass(frozen=True, slots=True)
class LinkResolution:
    targets: tuple[str, ...]
    broken: tuple[str, ...]
    ambiguous: tuple[str, ...]
    escaped: tuple[str, ...]


def _linkable_markdown(body: str) -> str:
    """Remove Markdown regions whose link-shaped text is literal, not navigational."""
    without_comments = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    visible: list[str] = []
    fence: tuple[str, int] | None = None
    for line in without_comments.splitlines(keepends=True):
        marker = re.match(r"^[ \t]{0,3}(`{3,}|~{3,})", line)
        if marker is not None:
            run = marker.group(1)
            kind = run[0]
            if fence is None:
                fence = (kind, len(run))
            elif fence[0] == kind and len(run) >= fence[1]:
                fence = None
            visible.append("\n" if line.endswith("\n") else "")
            continue
        if fence is None:
            visible.append(line)
        else:
            visible.append("\n" if line.endswith("\n") else "")
    text = "".join(visible)
    return re.sub(r"(`+)(?:(?!\1)[\s\S])*?\1", "", text)


def _raw_links(body: str) -> list[tuple[str, bool]]:
    text = _linkable_markdown(body)
    links = [(target, False) for target in MARKDOWN_LINK.findall(text)]
    for value in WIKILINK.findall(text):
        links.append((value.split("|", 1)[0], True))
    return links


def resolve_links(document: Document, *, root: Path, known_paths: set[str]) -> LinkResolution:
    targets: set[str] = set()
    broken: set[str] = set()
    ambiguous: set[str] = set()
    escaped: set[str] = set()
    resolved_root = root.resolve()
    by_stem: dict[str, list[str]] = {}
    by_path: dict[str, list[str]] = {}
    for known in known_paths:
        key = Path(known).stem.casefold()
        by_stem.setdefault(key, []).append(known)
        by_path.setdefault(known.casefold(), []).append(known)
    for raw, wiki in _raw_links(document.body):
        if not wiki and re.match(r"\A(?:https?:|mailto:|#)", raw, re.IGNORECASE):
            continue
        clean = raw.split("#", 1)[0].split("^", 1)[0].strip()
        if not clean:
            continue
        if wiki and "/" not in clean and "\\" not in clean:
            matches = by_stem.get(Path(clean).stem.casefold(), [])
            if len(matches) == 1:
                targets.add(matches[0])
            elif len(matches) > 1:
                ambiguous.add(raw)
            else:
                broken.add(raw)
            continue
        normalized = clean.replace("\\", "/")
        if wiki and not normalized.lower().endswith(".md"):
            normalized += ".md"
        if normalized.startswith("/") or (wiki and not normalized.startswith(("./", "../"))):
            candidate = resolved_root / normalized.removeprefix("/")
        else:
            candidate = document.path.parent / normalized
        try:
            relative = candidate.resolve(strict=False).relative_to(resolved_root).as_posix()
        except ValueError:
            escaped.add(raw)
            continue
        matches = by_path.get(relative.casefold(), [])
        if len(matches) == 1:
            targets.add(matches[0])
        elif len(matches) > 1:
            ambiguous.add(raw)
        elif not wiki and candidate.exists() and not candidate.is_symlink():
            # Repository-operational documents may be linked from canonical cards,
            # but only canonical Markdown becomes a catalog relationship edge.
            continue
        else:
            broken.add(raw)
    return LinkResolution(
        tuple(sorted(targets)),
        tuple(sorted(broken)),
        tuple(sorted(ambiguous)),
        tuple(sorted(escaped)),
    )


def internal_targets(
    document: Document, *, root: Path, known_paths: set[str] | None = None
) -> list[str]:
    known = known_paths or {path.relative_to(root).as_posix() for path in paths(root)}
    return list(resolve_links(document, root=root, known_paths=known).targets)
