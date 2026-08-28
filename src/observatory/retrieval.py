"""Dependency-light sparse retrieval behind the stable retrieval contract."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from observatory import corpus

TOKEN = re.compile(r"[a-z0-9][a-z0-9_-]*", re.IGNORECASE)
INACTIVE_STATUSES = frozenset({"superseded", "deprecated", "archived", "rejected", "deleted"})
STRATEGY = "sparse-bm25-v2"


@dataclass(frozen=True, slots=True)
class Result:
    relative_path: str
    score: float
    strategy: str
    title: str
    type: str
    status: str
    matched_terms: tuple[str, ...]
    description: str
    source_ids: tuple[str, ...]
    projects: tuple[str, ...]
    stale_after: str | None
    valid_from: str | None
    valid_until: str | None
    applicability: str
    superseded_by: tuple[str, ...]
    conflicts_with: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.relative_path,
            "score": self.score,
            "strategy": self.strategy,
            "title": self.title,
            "type": self.type,
            "status": self.status,
            "matched_terms": list(self.matched_terms),
            "description": self.description,
            "source_ids": list(self.source_ids),
            "projects": list(self.projects),
            "stale_after": self.stale_after,
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "applicability": self.applicability,
            "superseded_by": list(self.superseded_by),
            "conflicts_with": list(self.conflicts_with),
            "warnings": list(self.warnings),
        }


def tokenize(value: object) -> list[str]:
    tokens: list[str] = []
    for token in TOKEN.findall(str(value).lower()):
        tokens.append(token)
        if "-" in token or "_" in token:
            tokens.extend(part for part in re.split(r"[-_]", token) if part)
    return tokens


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _acronym(value: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", value)
    return "".join(word[0] for word in words) if len(words) >= 2 else ""


def _date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


class SparseIndex:
    """Deterministic BM25-style index with field and applicability signals."""

    def __init__(self, documents: Iterable[corpus.Document]) -> None:
        self.documents = tuple(documents)
        self._superseded_by: dict[str, list[corpus.Document]] = defaultdict(list)
        for document in self.documents:
            for target in _strings(document.frontmatter.get("supersedes")):
                self._superseded_by[target].append(document)
        self._lengths: list[int] = []
        self._postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        self._build()

    @classmethod
    def from_root(cls, root: Path) -> SparseIndex:
        return cls(corpus.read(path, root=root) for path in corpus.paths(root))

    def _searchable_text(self, document: corpus.Document) -> str:
        metadata = document.frontmatter
        values = [
            metadata.get("id"),
            metadata.get("type"),
            metadata.get("title"),
            metadata.get("description"),
            " ".join(_strings(metadata.get("tags"))),
            " ".join(_strings(metadata.get("aliases"))),
            " ".join(_strings(metadata.get("projects"))),
            _acronym(str(metadata.get("title") or "")),
            " ".join(
                acronym
                for acronym in (_acronym(alias) for alias in _strings(metadata.get("aliases")))
                if acronym
            ),
        ]
        return " ".join(str(value) for value in values if value is not None) + "\n" + document.body

    def _build(self) -> None:
        for document_id, document in enumerate(self.documents):
            terms = tokenize(self._searchable_text(document))
            self._lengths.append(len(terms))
            for term, frequency in Counter(terms).items():
                self._postings[term].append((document_id, frequency))

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        include_inactive: bool = False,
        include_stale: bool = True,
        include_noncurrent: bool = False,
        type: str | None = None,
        project: str | None = None,
        source_id: str | None = None,
        as_of: date | None = None,
    ) -> list[Result]:
        query_terms = list(dict.fromkeys(tokenize(query)))
        if not query_terms:
            return []

        scores: dict[int, float] = defaultdict(float)
        matched: dict[int, set[str]] = defaultdict(set)
        document_count = len(self.documents)
        average_length = sum(self._lengths) / max(document_count, 1)

        for term in query_terms:
            rows = self._postings.get(term, [])
            if not rows:
                continue
            document_frequency = len(rows)
            inverse_frequency = math.log(
                1.0 + (document_count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            for document_id, frequency in rows:
                document_length = self._lengths[document_id]
                denominator = frequency + 1.5 * (
                    1.0 + 0.75 * document_length / max(average_length, 1e-9) - 0.75
                )
                scores[document_id] += inverse_frequency * (frequency * 2.5) / denominator
                matched[document_id].add(term)

        effective_date = as_of or date.today()
        normalized_query = query.lower().strip()
        results: list[Result] = []
        for document_id, base_score in scores.items():
            document = self.documents[document_id]
            metadata = document.frontmatter
            status = str(metadata.get("status") or "").lower()
            if not include_inactive and status in INACTIVE_STATUSES:
                continue
            if type and str(metadata.get("type") or "").lower() != type.lower():
                continue

            projects = tuple(_strings(metadata.get("projects")))
            if project and project not in projects:
                continue

            stale_date = _date(metadata.get("stale_after"))
            is_stale = stale_date is not None and stale_date < effective_date
            if is_stale and not include_stale:
                continue

            title = str(metadata.get("title") or "")
            aliases = _strings(metadata.get("aliases"))
            tags = _strings(metadata.get("tags"))
            score = base_score
            if title.lower() == normalized_query:
                score += 4.0
            if any(alias.lower() == normalized_query for alias in aliases):
                score += 2.25
            if normalized_query and normalized_query in title.lower():
                score += 1.25
            score += (
                sum(any(term in tokenize(tag) for tag in tags) for term in matched[document_id])
                * 0.35
            )
            field_tokens = {
                "id": set(tokenize(metadata.get("id") or "")),
                "aliases": {term for alias in aliases for term in tokenize(alias)},
                "projects": {term for item in projects for term in tokenize(item)},
            }
            for term in matched[document_id]:
                if term in field_tokens["id"]:
                    score += 1.0
                if term in field_tokens["aliases"]:
                    score += 0.65
                if term in field_tokens["projects"]:
                    score += 0.25
            sources = metadata.get("sources")
            source_ids = (
                tuple(
                    str(source["id"])
                    for source in sources
                    if isinstance(source, dict) and source.get("id") is not None
                )
                if isinstance(sources, list)
                else ()
            )
            if source_id and source_id not in source_ids:
                continue
            source_terms = {term for item in source_ids for term in tokenize(item)}
            score += sum(term in source_terms for term in matched[document_id]) * 0.5

            valid_from = _date(metadata.get("valid_from"))
            valid_until = _date(metadata.get("valid_until"))
            identifier = str(metadata.get("id") or "")
            superseders = tuple(
                sorted(
                    str(candidate.frontmatter.get("id") or candidate.relative_path)
                    for candidate in self._superseded_by.get(identifier, [])
                    if self._is_current(candidate, effective_date)
                )
            )
            if valid_from is not None and effective_date < valid_from:
                applicability = "future"
            elif valid_until is not None and effective_date > valid_until:
                applicability = "historical"
            elif superseders:
                applicability = "superseded"
            else:
                applicability = "current"
            if applicability != "current" and not include_noncurrent:
                continue

            conflicts = tuple(sorted(_strings(metadata.get("conflicts_with"))))
            warnings: list[str] = []
            if is_stale and stale_date:
                warnings.append(f"freshness review overdue since {stale_date.isoformat()}")
            if applicability == "future" and valid_from:
                warnings.append(f"not applicable until {valid_from.isoformat()}")
            if applicability == "historical" and valid_until:
                warnings.append(f"no longer applicable after {valid_until.isoformat()}")
            if superseders:
                warnings.append(f"superseded by {', '.join(superseders)}")
            if conflicts:
                warnings.append(f"declared conflict with {', '.join(conflicts)}")
            results.append(
                Result(
                    relative_path=document.relative_path,
                    score=round(score, 6),
                    strategy=STRATEGY,
                    title=title or document.relative_path,
                    type=str(metadata.get("type") or ""),
                    status=str(metadata.get("status") or ""),
                    matched_terms=tuple(sorted(matched[document_id])),
                    description=str(metadata.get("description") or ""),
                    source_ids=source_ids,
                    projects=projects,
                    stale_after=stale_date.isoformat() if stale_date else None,
                    valid_from=valid_from.isoformat() if valid_from else None,
                    valid_until=valid_until.isoformat() if valid_until else None,
                    applicability=applicability,
                    superseded_by=superseders,
                    conflicts_with=conflicts,
                    warnings=tuple(warnings),
                )
            )
        return sorted(results, key=lambda result: (-result.score, result.relative_path))[:limit]

    def _is_current(self, document: corpus.Document, as_of: date) -> bool:
        metadata = document.frontmatter
        if str(metadata.get("status") or "").lower() in INACTIVE_STATUSES:
            return False
        valid_from = _date(metadata.get("valid_from"))
        valid_until = _date(metadata.get("valid_until"))
        return not (
            (valid_from is not None and as_of < valid_from)
            or (valid_until is not None and as_of > valid_until)
        )
