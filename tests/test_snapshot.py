from __future__ import annotations

import hashlib
import json
import os

import pytest

from observatory import snapshot
from observatory.snapshot import SnapshotError, create, restore, restore_plan, verify


def test_create_verify_and_two_phase_restore(tmp_path):
    source = tmp_path / "rules.md"
    source.write_bytes(b"original\n")
    os.chmod(source, 0o640)
    os.utime(source, ns=(1_700_000_000_123_456_789, 1_700_000_001_987_654_321))
    expected_times = (source.stat().st_atime_ns, source.stat().st_mtime_ns)
    destination = tmp_path / "snapshot"
    made = create(destination, [source])
    assert made.file_count == 1
    assert verify(destination, compare_sources=True).manifest_sha256 == made.manifest_sha256
    assert oct(destination.stat().st_mode & 0o777) == "0o700"
    assert oct((destination / "files/000000").stat().st_mode & 0o777) == "0o600"

    source.write_bytes(b"changed\n")
    plan = restore_plan(destination)
    with pytest.raises(SnapshotError, match="confirmation"):
        restore(destination, confirmation="wrong")
    restored = restore(destination, confirmation=plan.token)
    restored_metadata = source.stat()
    assert restored.file_count == 1
    assert source.read_bytes() == b"original\n"
    assert oct(restored_metadata.st_mode & 0o777) == "0o640"
    assert (restored_metadata.st_atime_ns, restored_metadata.st_mtime_ns) == expected_times


def test_refuses_existing_destination_duplicate_and_symlink_sources(tmp_path):
    source = tmp_path / "source"
    source.write_text("data", encoding="utf-8")
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(SnapshotError, match="destination"):
        create(existing, [source])
    with pytest.raises(SnapshotError, match="unique"):
        create(tmp_path / "duplicate", [source, source])
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(SnapshotError, match="non-symlink"):
        create(tmp_path / "linked", [link])


def test_detects_corrupt_backup_manifest_and_changed_source(tmp_path):
    source = tmp_path / "source"
    source.write_text("data", encoding="utf-8")
    destination = tmp_path / "snapshot"
    create(destination, [source])
    (destination / "files/000000").write_text("tampered", encoding="utf-8")
    with pytest.raises(SnapshotError, match="backup verification"):
        verify(destination)

    destination2 = tmp_path / "snapshot2"
    create(destination2, [source])
    source.write_text("new", encoding="utf-8")
    with pytest.raises(SnapshotError, match="source changed"):
        verify(destination2, compare_sources=True)


def test_rejects_manifest_traversal_and_stale_restore_plan(tmp_path):
    source = tmp_path / "source"
    source.write_text("original", encoding="utf-8")
    destination = tmp_path / "snapshot"
    create(destination, [source])
    source.write_text("first change", encoding="utf-8")
    stale = restore_plan(destination)
    source.write_text("second change", encoding="utf-8")
    with pytest.raises(SnapshotError, match="confirmation"):
        restore(destination, confirmation=stale.token)

    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["snapshot_path"] = "../escape"
    rendered = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    manifest_path.write_bytes(rendered)
    (destination / "manifest.sha256").write_text(
        hashlib.sha256(rendered).hexdigest() + "\n", encoding="utf-8"
    )
    with pytest.raises(SnapshotError, match="unsafe"):
        verify(destination)


def test_detects_source_mutation_during_copy(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.write_bytes(b"a" * (1024 * 1024 + 1))
    original_read = snapshot.os.read
    mutated = False

    def racing_read(descriptor, amount):
        nonlocal mutated
        chunk = original_read(descriptor, amount)
        if chunk and not mutated:
            mutated = True
            with source.open("ab") as stream:
                stream.write(b"changed")
        return chunk

    monkeypatch.setattr(snapshot.os, "read", racing_read)
    with pytest.raises(SnapshotError, match="changed while copying"):
        create(tmp_path / "snapshot", [source])
    assert not (tmp_path / "snapshot/manifest.json").exists()


def test_rejects_symlinked_source_and_snapshot_ancestors(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    source = real / "source"
    source.write_text("data", encoding="utf-8")
    linked = tmp_path / "linked"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(SnapshotError, match="non-symlink directory"):
        create(tmp_path / "snapshot", [linked / "source"])

    made = create(real / "snapshot", [source])
    assert made.file_count == 1
    snapshot_link = tmp_path / "snapshot-link"
    snapshot_link.symlink_to(real, target_is_directory=True)
    with pytest.raises(SnapshotError, match="non-symlink directory"):
        verify(snapshot_link / "snapshot")


def test_verify_detects_source_metadata_changes(tmp_path):
    source = tmp_path / "source"
    source.write_text("data", encoding="utf-8")
    os.chmod(source, 0o640)
    destination = tmp_path / "snapshot"
    create(destination, [source])
    os.chmod(source, 0o600)
    with pytest.raises(SnapshotError, match="metadata changed"):
        verify(destination, compare_sources=True)
