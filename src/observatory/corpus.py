"""Typed access to canonical OKF Markdown documents."""

from __future__ import annotations

import re
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
    return sorted(
        path for directory in CANONICAL_DIRS for path in (root / directory).glob("**/*.md")
    )


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
    return parse_document(path.read_text(encoding="utf-8"), path=path, root=root)


def internal_targets(document: Document, *, root: Path) -> list[str]:
    targets: set[str] = set()
    resolved_root = root.resolve()
    for target in MARKDOWN_LINK.findall(document.text):
        if re.match(r"\A(?:https?:|mailto:|#)", target, re.IGNORECASE):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        candidate = (
            resolved_root / clean.removeprefix("/")
            if clean.startswith("/")
            else document.path.parent / clean
        )
        try:
            relative = candidate.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        targets.add(relative.as_posix())
    return sorted(targets)
