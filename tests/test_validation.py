from __future__ import annotations

from conftest import write_card

from observatory.validation import validate


def tracked(_root):
    return []


def test_accepts_okf_frontmatter_and_open_extension_types(tmp_path):
    write_card(
        tmp_path,
        "concepts/valid.md",
        title="Valid",
        document_type="CustomType",
        extra=(
            "id: unique\n"
            "generated: {by: process:test, at: 2026-01-01T00:00:00Z}\n"
            "stale_after: 2027-01-01\n"
            "valid_from: 2026-01-01\n"
            "valid_until: 2026-12-31\n"
            "supersedes: [older]\n"
            "conflicts_with: [alternative]\n"
        ),
    )
    result = validate(tmp_path, tracked_files=tracked)
    assert result.ok
    assert len(result.warnings) == 3
    assert "outside the local ontology" in result.warnings[0]
    assert any("unknown document id 'older'" in warning for warning in result.warnings)


def test_accepts_personal_operating_model_types_in_canonical_root(tmp_path):
    write_card(
        tmp_path,
        "personal-operating-model/ranked-recommendations.md",
        title="Prefer ranked recommendations",
        document_type="OperatingPreference",
        extra=(
            "id: pom-ranked-recommendations\n"
            "origin: owner-explicit\n"
            "valid_from: 2026-08-27\n"
        ),
    )
    write_card(
        tmp_path,
        "personal-operating-model/reversible-tests.md",
        title="Prefer reversible tests for cheap uncertainty",
        document_type="OperatingPrinciple",
        extra="id: pom-reversible-tests\n",
    )
    write_card(
        tmp_path,
        "personal-operating-model/failed-handoff-pattern.md",
        title="Keep handoffs compact",
        document_type="OperatingLesson",
        extra="id: pom-compact-handoffs\n",
    )

    result = validate(tmp_path, tracked_files=tracked)

    assert result.ok
    assert result.document_count == 3
    assert not any("outside the local ontology" in warning for warning in result.warnings)


def test_rejects_invalid_frontmatter_contracts(tmp_path):
    write_card(
        tmp_path,
        "concepts/bad.md",
        title="Bad",
        extra=(
            "tags: [valid, '']\n"
            "sources:\n  - id: same\n  - id: same\n    resource: ''\n"
            "generated: {by: invalid actor/value, at: yesterday}\n"
            "verified: []\n"
            "status: active\n"
            "project_status: active\n"
            "stale_after: next-week\n"
            "valid_from: 2027-01-01\n"
            "valid_until: 2026-01-01\n"
            "supersedes: [same, same]\n"
            "conflicts_with: invalid\n"
        ),
    )
    result = validate(tmp_path, tracked_files=tracked)
    assert not result.ok
    rendered = "\n".join(result.errors)
    for expected in (
        "tags must be",
        "resource is required",
        "duplicate source id",
        "generated.by",
        "generated.at",
        "verified must not be an empty list",
        "status must be",
        "project_status is only valid",
        "stale_after must be",
        "valid_until must not precede valid_from",
        "supersedes must not contain duplicate",
        "conflicts_with must be a sequence",
    ):
        assert expected in rendered


def test_rejects_duplicate_document_ids_and_broken_yaml(tmp_path):
    write_card(tmp_path, "concepts/a.md", title="A", extra="id: duplicate\n")
    write_card(tmp_path, "concepts/b.md", title="B", extra="id: duplicate\n")
    broken = tmp_path / "concepts/broken.md"
    broken.write_text("---\ntype: [\n---\n", encoding="utf-8")
    result = validate(tmp_path, tracked_files=tracked)
    rendered = "\n".join(result.errors)
    assert "duplicate id" in rendered
    assert "invalid YAML" in rendered
