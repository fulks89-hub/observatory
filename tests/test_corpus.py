from __future__ import annotations

import pytest
from conftest import write_card

from observatory import corpus


def test_rejects_markdown_symlink_inside_or_outside_root(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-private.md"
    outside.write_text("private", encoding="utf-8")
    (tmp_path / "concepts").mkdir()
    (tmp_path / "concepts/leak.md").symlink_to(outside)
    with pytest.raises(corpus.CorpusError, match="symbolic-link corpus"):
        corpus.paths(tmp_path)


def test_rejects_symlinked_canonical_directory(tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (tmp_path / "concepts").symlink_to(outside, target_is_directory=True)
    with pytest.raises(corpus.CorpusError, match="symbolic-link corpus"):
        corpus.paths(tmp_path)


def test_resolves_wikilinks_embeds_aliases_and_reports_ambiguity(tmp_path):
    source = write_card(
        tmp_path,
        "concepts/source.md",
        title="Source",
        body="See [[Target|label]], ![[concepts/folder/Embed]], and [[Duplicate]].",
    )
    write_card(tmp_path, "concepts/target.md", title="Target")
    write_card(tmp_path, "concepts/folder/embed.md", title="Embed")
    write_card(tmp_path, "concepts/a/duplicate.md", title="Duplicate A")
    write_card(tmp_path, "concepts/b/duplicate.md", title="Duplicate B")
    known = {path.relative_to(tmp_path).as_posix() for path in corpus.paths(tmp_path)}
    resolved = corpus.resolve_links(
        corpus.read(source, root=tmp_path), root=tmp_path, known_paths=known
    )
    assert resolved.targets == ("concepts/folder/embed.md", "concepts/target.md")
    assert resolved.ambiguous == ("Duplicate",)


def test_link_extraction_ignores_frontmatter_code_and_comments(tmp_path):
    source = write_card(
        tmp_path,
        "concepts/source.md",
        title="Source",
        body=(
            "Real [[Target]].\n\n"
            "`[[InlineMissing]]`\n\n"
            "```markdown\n[[FencedMissing]]\n```\n\n"
            "~~~\n[also missing](../missing.md)\n~~~\n\n"
            "<!-- [[CommentMissing]] -->\n"
        ),
    )
    write_card(tmp_path, "concepts/target.md", title="Target")
    known = {path.relative_to(tmp_path).as_posix() for path in corpus.paths(tmp_path)}
    resolved = corpus.resolve_links(
        corpus.read(source, root=tmp_path), root=tmp_path, known_paths=known
    )
    assert resolved.targets == ("concepts/target.md",)
    assert not resolved.broken


def test_link_extraction_does_not_treat_frontmatter_values_as_links(tmp_path):
    source = write_card(tmp_path, "concepts/source.md", title="[[Not A Link]]")
    known = {path.relative_to(tmp_path).as_posix() for path in corpus.paths(tmp_path)}
    resolved = corpus.resolve_links(
        corpus.read(source, root=tmp_path), root=tmp_path, known_paths=known
    )
    assert not resolved.targets
    assert not resolved.broken
