"""Deterministic disposable catalog generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from observatory import corpus


def _present(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if value is not None}


def build(root: Path) -> dict[str, Any]:
    documents = [corpus.read(path, root=root) for path in corpus.paths(root)]
    known_paths = {document.relative_path for document in documents}
    incoming: dict[str, list[str]] = {path: [] for path in known_paths}
    edges: list[dict[str, str]] = []
    nodes: list[dict[str, Any]] = []

    for document in documents:
        targets = corpus.internal_targets(document, root=root)
        outgoing = [target for target in targets if target in known_paths]
        for target in outgoing:
            edges.append({"from": document.relative_path, "to": target})
            incoming[target].append(document.relative_path)
        metadata = document.frontmatter
        stale_after = metadata.get("stale_after")
        nodes.append(
            _present(
                {
                    "path": document.relative_path,
                    "id": metadata.get("id"),
                    "title": metadata.get("title"),
                    "type": metadata.get("type"),
                    "description": metadata.get("description"),
                    "tags": metadata.get("tags") if isinstance(metadata.get("tags"), list) else [],
                    "status": metadata.get("status"),
                    "project_status": metadata.get("project_status"),
                    "projects": (
                        metadata.get("projects")
                        if isinstance(metadata.get("projects"), list)
                        else []
                    ),
                    "stale_after": str(stale_after) if stale_after is not None else None,
                    "valid_from": (
                        str(metadata["valid_from"])
                        if metadata.get("valid_from") is not None
                        else None
                    ),
                    "valid_until": (
                        str(metadata["valid_until"])
                        if metadata.get("valid_until") is not None
                        else None
                    ),
                    "supersedes": (
                        metadata.get("supersedes")
                        if isinstance(metadata.get("supersedes"), list)
                        else []
                    ),
                    "conflicts_with": (
                        metadata.get("conflicts_with")
                        if isinstance(metadata.get("conflicts_with"), list)
                        else []
                    ),
                    "outgoing": outgoing,
                }
            )
        )

    for node in nodes:
        node_incoming = sorted(set(incoming[str(node["path"])]))
        node["incoming"] = node_incoming
        node["orphan"] = not node_incoming and not node["outgoing"]

    unique_edges = {(edge["from"], edge["to"]) for edge in edges}
    return {
        "format": "observatory-catalog-v1",
        "legacy_formats": ["observatory-catalog-v1"],
        "canonical": False,
        "nodes": sorted(nodes, key=lambda node: str(node["path"])),
        "edges": [{"from": source, "to": target} for source, target in sorted(unique_edges)],
    }
