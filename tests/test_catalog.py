from __future__ import annotations

from conftest import write_card

from observatory.catalog import build


def test_builds_deterministic_nodes_edges_backlinks_and_orphans(tmp_path):
    write_card(tmp_path, "concepts/a.md", title="A", body="# TL;DR\n\nSee [B](b.md).\n")
    write_card(tmp_path, "concepts/b.md", title="B")
    write_card(tmp_path, "concepts/orphan.md", title="Orphan")

    first = build(tmp_path)
    assert first == build(tmp_path)
    assert first["edges"] == [{"from": "concepts/a.md", "to": "concepts/b.md"}]
    nodes = {node["path"]: node for node in first["nodes"]}
    assert nodes["concepts/b.md"]["incoming"] == ["concepts/a.md"]
    assert nodes["concepts/orphan.md"]["orphan"] is True
    assert nodes["concepts/a.md"]["orphan"] is False
    assert first["format"] == "observatory-catalog-v1"
    assert "observatory-catalog-v1" in first["legacy_formats"]
    assert first["canonical"] is False


def test_handles_a_thousand_cards(tmp_path):
    for index in range(1_000):
        link = "" if index == 0 else f"See [previous](card-{index - 1}.md)."
        write_card(
            tmp_path,
            f"concepts/card-{index}.md",
            title=f"Card {index}",
            body=f"# TL;DR\n\n{link}\n",
        )
    catalog = build(tmp_path)
    assert len(catalog["nodes"]) == 1_000
    assert len(catalog["edges"]) == 999


def test_catalog_projects_temporal_and_relationship_metadata(tmp_path):
    write_card(
        tmp_path,
        "concepts/current.md",
        title="Current",
        extra=(
            "id: current\n"
            "valid_from: 2026-01-01\n"
            "valid_until: 2026-12-31\n"
            "supersedes: [old]\n"
            "conflicts_with: [alternative]\n"
        ),
    )
    node = build(tmp_path)["nodes"][0]
    assert node["valid_from"] == "2026-01-01"
    assert node["valid_until"] == "2026-12-31"
    assert node["supersedes"] == ["old"]
    assert node["conflicts_with"] == ["alternative"]


def test_catalog_builds_wikilink_and_embed_edges(tmp_path):
    write_card(tmp_path, "concepts/a.md", title="A", body="See [[B]] and ![[concepts/folder/C]].")
    write_card(tmp_path, "concepts/b.md", title="B")
    write_card(tmp_path, "concepts/folder/c.md", title="C")
    assert build(tmp_path)["edges"] == [
        {"from": "concepts/a.md", "to": "concepts/b.md"},
        {"from": "concepts/a.md", "to": "concepts/folder/c.md"},
    ]
