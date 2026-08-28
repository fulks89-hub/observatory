from __future__ import annotations

from pathlib import Path


def write_card(
    root: Path,
    relative: str,
    *,
    title: str,
    body: str = "# TL;DR\n\nFixture.\n",
    document_type: str = "Concept",
    extra: str = "",
) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: {document_type}\ntitle: {title}\ntags: [test]\n{extra}---\n{body}",
        encoding="utf-8",
    )
    return path
