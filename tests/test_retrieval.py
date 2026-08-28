from __future__ import annotations

from datetime import date

from conftest import write_card

from observatory.retrieval import STRATEGY, SparseIndex, tokenize


def build_corpus(root):
    write_card(
        root,
        "concepts/current.md",
        title="Context engineering",
        body="# TL;DR\n\nRetrieval should favor compact, applicable evidence.\n",
        extra=(
            "id: concept-context-engineering\n"
            "description: Selecting the right evidence and memory for an agent.\n"
            "tags: [context-engineering, agents, retrieval]\n"
            "aliases: [context design]\n"
            "status: stable\n"
            "stale_after: 2027-01-01\n"
            "sources:\n  - id: source-current\n    resource: https://example.com/current\n"
        ),
    )
    write_card(
        root,
        "concepts/stale.md",
        title="Old context engineering",
        body="# TL;DR\n\nThis old note is superseded.\n",
        extra="description: Superseded guidance.\nstatus: deprecated\n",
    )
    write_card(
        root,
        "concepts/old-decision.md",
        title="Historical runtime choice",
        body="# TL;DR\n\nUse the first runtime choice.\n",
        extra=(
            "id: decision-runtime-old\n"
            "description: Earlier runtime decision.\n"
            "status: stable\n"
            "valid_from: 2025-01-01\n"
            "conflicts_with: [decision-runtime-new]\n"
        ),
    )
    write_card(
        root,
        "concepts/new-decision.md",
        title="Current runtime choice",
        body="# TL;DR\n\nUse the current runtime choice.\n",
        extra=(
            "id: decision-runtime-new\n"
            "description: Current runtime decision.\n"
            "status: stable\n"
            "valid_from: 2026-01-01\n"
            "supersedes: [decision-runtime-old]\n"
            "conflicts_with: [decision-runtime-old]\n"
            "projects: [project-observatory]\n"
            "sources:\n  - id: source-decision\n    resource: https://example.invalid/decision\n"
        ),
    )
    write_card(
        root,
        "sources/context.md",
        title="Context engineering source",
        document_type="Source",
        body="# TL;DR\n\nSource about context engineering.\n",
        extra="status: stable\n",
    )


def test_sparse_search_ranking_metadata_and_provenance(tmp_path):
    build_corpus(tmp_path)
    result = SparseIndex.from_root(tmp_path).search("context engineering", limit=3)[0]
    assert result.relative_path == "concepts/current.md"
    assert result.strategy == STRATEGY
    assert result.source_ids == ("source-current",)
    assert result.projects == ()
    assert result.title == "Context engineering"
    assert result.description == "Selecting the right evidence and memory for an agent."
    assert result.matched_terms == ("context", "engineering")
    assert result.stale_after == "2027-01-01"
    assert result.valid_from is None
    assert result.valid_until is None
    assert result.applicability == "current"
    assert result.superseded_by == ()
    assert result.conflicts_with == ()
    assert result.warnings == ()


def test_inactive_and_type_filters(tmp_path):
    build_corpus(tmp_path)
    index = SparseIndex.from_root(tmp_path)
    default_paths = [
        result.relative_path for result in index.search("deprecated context", limit=10)
    ]
    assert "concepts/stale.md" not in default_paths
    inactive_paths = [
        result.relative_path
        for result in index.search("deprecated context", limit=10, include_inactive=True)
    ]
    assert "concepts/stale.md" in inactive_paths
    typed = index.search("context engineering", limit=10, type="Source")
    assert typed
    assert {result.type for result in typed} == {"Source"}


def test_exact_title_and_alias_boosts_are_preserved(tmp_path):
    build_corpus(tmp_path)
    index = SparseIndex.from_root(tmp_path)
    exact_title = index.search("context engineering", limit=10)
    exact_alias = index.search("context design", limit=10)
    assert exact_title[0].relative_path == "concepts/current.md"
    assert exact_alias[0].relative_path == "concepts/current.md"
    assert exact_title[0].score > next(
        result.score for result in exact_title if result.relative_path == "sources/context.md"
    )
    assert index.search("CE")[0].relative_path == "concepts/current.md"


def test_compound_tokenization_preserves_exact_and_component_terms():
    assert tokenize("retrieval-augmented_memory") == [
        "retrieval-augmented_memory",
        "retrieval",
        "augmented",
        "memory",
    ]


def test_wikilink_labels_remain_searchable(tmp_path):
    write_card(
        tmp_path,
        "concepts/source.md",
        title="Source",
        body="# TL;DR\n\nConnected to [[Rare Observatory Topic]].\n",
    )
    result = SparseIndex.from_root(tmp_path).search("rare observatory topic")
    assert result[0].relative_path == "concepts/source.md"


def test_stale_results_are_flagged_and_can_be_excluded(tmp_path):
    build_corpus(tmp_path)
    index = SparseIndex.from_root(tmp_path)
    stale = index.search("context engineering", as_of=date(2027, 1, 2))[0]
    assert stale.relative_path == "concepts/current.md"
    assert stale.applicability == "current"
    assert stale.warnings == ("freshness review overdue since 2027-01-01",)
    assert (
        index.search("context engineering", as_of=date(2027, 1, 2), include_stale=False)[
            0
        ].relative_path
        == "sources/context.md"
    )


def test_temporal_supersession_conflicts_and_scope_filters(tmp_path):
    build_corpus(tmp_path)
    index = SparseIndex.from_root(tmp_path)
    current = index.search("runtime choice", as_of=date(2026, 8, 17), limit=10)
    assert [result.relative_path for result in current] == ["concepts/new-decision.md"]
    assert current[0].conflicts_with == ("decision-runtime-old",)
    assert "declared conflict" in " ".join(current[0].warnings)

    historical = index.search(
        "runtime choice", as_of=date(2026, 8, 17), limit=10, include_noncurrent=True
    )
    old = next(
        result for result in historical if result.relative_path == "concepts/old-decision.md"
    )
    assert old.applicability == "superseded"
    assert old.superseded_by == ("decision-runtime-new",)

    scoped = index.search(
        "runtime choice", project="project-observatory", source_id="source-decision"
    )
    assert [result.relative_path for result in scoped] == ["concepts/new-decision.md"]
