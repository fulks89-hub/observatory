"""Verified, non-overwriting preservation snapshots and bounded restoration."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from observatory.safe_files import UnsafePathError, read_regular

SCHEMA = "observatory-preservation-snapshot"
VERSION = 1


class SnapshotError(OSError):
    """A snapshot could not be created, verified, or restored safely."""


@dataclass(frozen=True, slots=True)
class SnapshotResult:
    root: Path
    manifest_sha256: str
    file_count: int


@dataclass(frozen=True, slots=True)
class RestorePlan:
    token: str
    files: tuple[dict[str, Any], ...]


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def _write_all(descriptor: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        written = os.write(descriptor, view)
        view = view[written:]


def _has_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def _restore_open_file_times(
    path: Path, descriptor: int, *, atime_ns: int, mtime_ns: int
) -> None:
    """Restore timestamps through the open file identity, with a checked fallback."""
    if os.utime in os.supports_fd:
        os.utime(descriptor, ns=(atime_ns, mtime_ns))
        return
    opened = os.fstat(descriptor)
    before = path.lstat()
    if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
        raise SnapshotError(f"file changed before timestamp restoration: {path}")
    os.utime(path, ns=(atime_ns, mtime_ns), follow_symlinks=False)
    after = path.lstat()
    if (opened.st_dev, opened.st_ino) != (after.st_dev, after.st_ino):
        raise SnapshotError(f"file changed during timestamp restoration: {path}")


def _directory_identity(path: Path) -> tuple[tuple[str, int, int], ...]:
    """Reject symlinked ancestors and bind an absolute directory chain to its inodes."""
    if not path.is_absolute():
        raise SnapshotError(f"directory path must be absolute: {path}")
    current = Path(path.anchor)
    identities: list[tuple[str, int, int]] = []
    for part in path.parts[1:]:
        current /= part
        try:
            metadata = current.lstat()
        except OSError as error:
            raise SnapshotError(f"directory ancestor is unavailable: {current}") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise SnapshotError(f"directory ancestor must be a non-symlink directory: {current}")
        identities.append((str(current), metadata.st_dev, metadata.st_ino))
    return tuple(identities)


def _git_identity(source: Path) -> dict[str, str] | None:
    try:
        root = Path(
            subprocess.run(
                ["git", "-C", str(source.parent), "rev-parse", "--show-toplevel"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        relative = source.resolve(strict=True).relative_to(root.resolve(strict=True)).as_posix()
        commit = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD^{commit}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        blob = subprocess.run(
            ["git", "-C", str(root), "rev-parse", f"HEAD:{relative}"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None
    return {"root": str(root), "path": relative, "commit": commit, "blob": blob}


def _copy_stable(source: Path, destination: Path) -> tuple[os.stat_result, str, int]:
    source_parent = _directory_identity(source.parent)
    destination_parent = _directory_identity(destination.parent)
    before = source.lstat()
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise SnapshotError(f"source must be a non-symlink regular file: {source}")
    read_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    source_fd = os.open(source, read_flags)
    try:
        destination_fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except BaseException:
        os.close(source_fd)
        raise
    digest = hashlib.sha256()
    size = 0
    try:
        opened = os.fstat(source_fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise SnapshotError(f"source changed while opening: {source}")
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                view = view[written:]
        os.fsync(destination_fd)
        _restore_open_file_times(
            source,
            source_fd,
            atime_ns=before.st_atime_ns,
            mtime_ns=before.st_mtime_ns,
        )
        after = os.fstat(source_fd)

        def signature(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
            return (
                value.st_dev,
                value.st_ino,
                value.st_size,
                stat.S_IMODE(value.st_mode),
                value.st_atime_ns,
                value.st_mtime_ns,
            )

        if signature(opened) != signature(after) or size != after.st_size:
            raise SnapshotError(f"source changed while copying: {source}")
    finally:
        os.close(source_fd)
        os.close(destination_fd)
    if _directory_identity(source.parent) != source_parent:
        raise SnapshotError(f"source parent changed while copying: {source.parent}")
    if _directory_identity(destination.parent) != destination_parent:
        raise SnapshotError(f"snapshot parent changed while copying: {destination.parent}")
    copied = read_regular(destination, boundary=destination.parent.parent)
    if _digest(copied) != digest.hexdigest() or len(copied) != size:
        raise SnapshotError(f"backup verification failed: {source}")
    return before, digest.hexdigest(), size


def create(destination: Path, sources: list[Path]) -> SnapshotResult:
    if (
        not destination.is_absolute()
        or not sources
        or any(not source.is_absolute() for source in sources)
        or _has_control(str(destination))
        or any(_has_control(str(source)) for source in sources)
    ):
        raise SnapshotError("snapshot destination and every source must be absolute")
    normalized = [Path(os.path.abspath(source)) for source in sources]
    if len(set(normalized)) != len(normalized):
        raise SnapshotError("snapshot sources must be unique")
    destination_parent = _directory_identity(destination.parent)
    for source in normalized:
        _directory_identity(source.parent)
    try:
        destination.mkdir(mode=0o700, parents=False, exist_ok=False)
        os.chmod(destination, 0o700)
        files_dir = destination / "files"
        files_dir.mkdir(mode=0o700)
    except OSError as error:
        raise SnapshotError(f"could not create new snapshot destination: {destination}") from error
    if _directory_identity(destination.parent) != destination_parent:
        raise SnapshotError(f"snapshot destination parent changed: {destination.parent}")
    entries: list[dict[str, Any]] = []
    for index, source in enumerate(sorted(normalized, key=str)):
        relative = f"files/{index:06d}"
        metadata, sha256, size = _copy_stable(source, destination / relative)
        entry: dict[str, Any] = {
            "source_path": str(source),
            "snapshot_path": relative,
            "sha256": sha256,
            "size": size,
            "mode": stat.S_IMODE(metadata.st_mode),
            "atime_ns": metadata.st_atime_ns,
            "mtime_ns": metadata.st_mtime_ns,
        }
        identity = _git_identity(source)
        if identity is not None:
            entry["git"] = identity
        entries.append(entry)
    manifest = {
        "schema": SCHEMA,
        "version": VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "files": entries,
    }
    rendered = _canonical(manifest)
    checksum = _digest(rendered)
    for name, content in (
        ("manifest.json", rendered),
        ("manifest.sha256", (checksum + "\n").encode()),
    ):
        temporary = destination / f".{name}.tmp"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            _write_all(descriptor, content)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, destination / name)
    verified = verify(destination, compare_sources=True)
    return SnapshotResult(destination, verified.manifest_sha256, verified.file_count)


def _load(root: Path) -> tuple[dict[str, Any], str]:
    root_identity = _directory_identity(root)
    if root.is_symlink() or not root.is_dir():
        raise SnapshotError("snapshot root must be a non-symlink directory")
    try:
        rendered = read_regular(root / "manifest.json", boundary=root)
        expected = read_regular(root / "manifest.sha256", boundary=root).decode().strip()
    except (UnsafePathError, UnicodeDecodeError) as error:
        raise SnapshotError(f"could not read snapshot manifest safely: {error}") from error
    actual = _digest(rendered)
    if expected != actual:
        raise SnapshotError("snapshot manifest checksum mismatch")
    try:
        value = json.loads(rendered)
    except json.JSONDecodeError as error:
        raise SnapshotError("snapshot manifest is invalid JSON") from error
    if (
        not isinstance(value, dict)
        or value.get("schema") != SCHEMA
        or value.get("version") != VERSION
    ):
        raise SnapshotError("unsupported snapshot manifest schema")
    if _directory_identity(root) != root_identity:
        raise SnapshotError("snapshot root changed while reading its manifest")
    return value, actual


def verify(root: Path, *, compare_sources: bool = False) -> SnapshotResult:
    manifest, checksum = _load(root)
    root_identity = _directory_identity(root)
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise SnapshotError("snapshot manifest must contain files")
    sources: set[str] = set()
    backups: set[str] = set()
    for raw in entries:
        if not isinstance(raw, dict):
            raise SnapshotError("snapshot file entry must be a mapping")
        source = raw.get("source_path")
        backup = raw.get("snapshot_path")
        if (
            not isinstance(source, str)
            or not Path(source).is_absolute()
            or _has_control(source)
            or source in sources
        ):
            raise SnapshotError("snapshot contains an invalid or duplicate source path")
        if not isinstance(backup, str):
            raise SnapshotError("snapshot contains an invalid backup path")
        backup_text = backup
        pure = Path(backup_text)
        if (
            pure.is_absolute()
            or ".." in pure.parts
            or _has_control(backup_text)
            or backup_text in backups
        ):
            raise SnapshotError("snapshot contains an unsafe or duplicate backup path")
        sources.add(source)
        backups.add(backup_text)
        if (
            not isinstance(raw.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", raw["sha256"]) is None
            or not isinstance(raw.get("size"), int)
            or raw["size"] < 0
            or not isinstance(raw.get("mode"), int)
            or not 0 <= raw["mode"] <= 0o7777
            or not isinstance(raw.get("atime_ns"), int)
            or raw["atime_ns"] < 0
            or not isinstance(raw.get("mtime_ns"), int)
            or raw["mtime_ns"] < 0
        ):
            raise SnapshotError("snapshot contains invalid file metadata")
        content = read_regular(root / pure, boundary=root)
        if _directory_identity(root) != root_identity:
            raise SnapshotError("snapshot root changed during verification")
        if len(content) != raw.get("size") or _digest(content) != raw.get("sha256"):
            raise SnapshotError(f"snapshot backup verification failed: {backup}")
        if compare_sources:
            source_path = Path(source)
            source_parent = _directory_identity(source_path.parent)
            before = source_path.lstat()
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
                raise SnapshotError(f"snapshot source is no longer a regular file: {source}")
            current = read_regular(source_path)
            after_read = source_path.lstat()
            if (before.st_dev, before.st_ino) != (after_read.st_dev, after_read.st_ino):
                raise SnapshotError(f"snapshot source changed while verifying: {source}")
            os.utime(
                source_path,
                ns=(before.st_atime_ns, before.st_mtime_ns),
                follow_symlinks=False,
            )
            after = source_path.lstat()
            if _directory_identity(source_path.parent) != source_parent:
                raise SnapshotError(f"snapshot source parent changed: {source_path.parent}")
            if len(current) != raw.get("size") or _digest(current) != raw.get("sha256"):
                raise SnapshotError(f"snapshot source changed: {source}")
            if (
                stat.S_IMODE(after.st_mode) != raw.get("mode")
                or after.st_atime_ns != raw.get("atime_ns")
                or after.st_mtime_ns != raw.get("mtime_ns")
            ):
                raise SnapshotError(f"snapshot source metadata changed: {source}")
    return SnapshotResult(root, checksum, len(entries))


def restore_plan(root: Path) -> RestorePlan:
    verified = verify(root)
    manifest, _ = _load(root)
    files: list[dict[str, Any]] = []
    for entry in manifest["files"]:
        target = Path(entry["source_path"])
        parent_identity = _directory_identity(target.parent)
        if target.exists() or target.is_symlink():
            current = read_regular(target)
            metadata = target.stat()
            state: dict[str, Any] = {
                "exists": True,
                "sha256": _digest(current),
                "size": len(current),
                "mode": stat.S_IMODE(metadata.st_mode),
                "mtime_ns": metadata.st_mtime_ns,
            }
        else:
            state = {
                "exists": False,
                "sha256": None,
                "size": None,
                "mode": None,
                "mtime_ns": None,
            }
        files.append(
            {
                "source_path": str(target),
                "parent_identity": parent_identity,
                "current": state,
                "restore_sha256": entry["sha256"],
            }
        )
    payload = {"manifest_sha256": verified.manifest_sha256, "files": files}
    return RestorePlan(_digest(_canonical(payload)), tuple(files))


def restore(root: Path, *, confirmation: str) -> SnapshotResult:
    plan = restore_plan(root)
    if confirmation != plan.token:
        raise SnapshotError("restore confirmation does not match the current restore plan")
    manifest, checksum = _load(root)
    for entry in manifest["files"]:
        target = Path(entry["source_path"])
        _directory_identity(target.parent)
    for entry, planned in zip(manifest["files"], plan.files, strict=True):
        target = Path(entry["source_path"])
        if _directory_identity(target.parent) != tuple(planned["parent_identity"]):
            raise SnapshotError(f"restore parent changed after confirmation: {target.parent}")
        current_exists = target.exists() or target.is_symlink()
        if current_exists:
            current = read_regular(target)
            metadata = target.stat()
            if (
                _digest(current) != planned["current"]["sha256"]
                or stat.S_IMODE(metadata.st_mode) != planned["current"]["mode"]
                or metadata.st_mtime_ns != planned["current"]["mtime_ns"]
            ):
                raise SnapshotError(f"restore target changed after confirmation: {target}")
        elif planned["current"]["exists"]:
            raise SnapshotError(f"restore target changed after confirmation: {target}")
        content = read_regular(root / entry["snapshot_path"], boundary=root)
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".observatory-restore-", dir=target.parent
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            _write_all(descriptor, content)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = -1
            os.replace(temporary, target)
            os.chmod(target, int(entry["mode"]))
            if _digest(read_regular(target)) != entry["sha256"]:
                raise SnapshotError(f"restored file verification failed: {target}")
            os.utime(target, ns=(int(entry["atime_ns"]), int(entry["mtime_ns"])))
            restored = target.lstat()
            if (
                stat.S_IMODE(restored.st_mode) != entry["mode"]
                or restored.st_atime_ns != entry["atime_ns"]
                or restored.st_mtime_ns != entry["mtime_ns"]
            ):
                raise SnapshotError(f"restored file metadata verification failed: {target}")
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            if temporary.exists():
                temporary.unlink()
    return SnapshotResult(root, checksum, len(manifest["files"]))
