"""Small no-follow filesystem primitives used at trust boundaries."""

from __future__ import annotations

import os
import stat
from pathlib import Path


class UnsafePathError(OSError):
    """A path is not a stable regular file inside its declared boundary."""


def resolved_root(root: Path) -> Path:
    try:
        value = root.resolve(strict=True)
    except OSError as error:
        raise UnsafePathError(f"root is unavailable: {root}") from error
    if not value.is_dir():
        raise UnsafePathError(f"root is not a directory: {root}")
    return value


def ensure_contained(path: Path, root: Path) -> Path:
    boundary = resolved_root(root)
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(boundary)
    except (OSError, ValueError) as error:
        raise UnsafePathError(f"path escapes declared root: {path}") from error
    return resolved


def read_regular(path: Path, *, boundary: Path | None = None) -> bytes:
    """Read one stable regular file without following a final-component symlink."""
    try:
        before = path.lstat()
    except OSError as error:
        raise UnsafePathError(f"file is unavailable: {path}") from error
    if stat.S_ISLNK(before.st_mode):
        raise UnsafePathError(f"symbolic links are not allowed: {path}")
    if not stat.S_ISREG(before.st_mode):
        raise UnsafePathError(f"not a regular file: {path}")
    if boundary is not None:
        ensure_contained(path, boundary)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise UnsafePathError(f"could not open file safely: {path}") from error
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise UnsafePathError(f"not a regular file: {path}")
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise UnsafePathError(f"file changed while opening: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        signature_before = (opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns)
        signature_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
        if signature_before != signature_after:
            raise UnsafePathError(f"file changed while reading: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)
