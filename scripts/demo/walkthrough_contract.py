"""Safety and provenance contract for the public Observatory walkthrough."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

ARTIFACT_PATHS = (
    "docs/media/observatory-overview.mp4",
    "docs/media/observatory-overview-readme.gif",
    "docs/media/observatory-overview-script.txt",
    "docs/media/observatory-overview.vtt",
)
SOURCE_PREFIXES = ("mission-control/", "scripts/demo/")
RECEIPT_SCHEMA_VERSION = 1


class ContractError(RuntimeError):
    """Raised when an artifact violates the release contract."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _inside(path: Path, boundary: Path) -> Path:
    resolved = path.resolve(strict=True)
    try:
        relative = resolved.relative_to(boundary.resolve(strict=True))
    except ValueError as error:
        raise ContractError(f"path escapes approved boundary: {path}") from error
    current = boundary.resolve(strict=True)
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ContractError(f"symbolic links are not allowed: {path}")
    return resolved


def read_regular(path: Path, *, boundary: Path | None = None) -> bytes:
    try:
        before = path.lstat()
    except OSError as error:
        raise ContractError(f"could not inspect regular file: {path}") from error
    if stat.S_ISLNK(before.st_mode):
        raise ContractError(f"symbolic links are not allowed: {path}")
    if not stat.S_ISREG(before.st_mode):
        raise ContractError(f"expected a non-symlink regular file: {path}")
    resolved = _inside(path, boundary) if boundary is not None else path.resolve(strict=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(resolved, flags)
        try:
            opened = os.fstat(descriptor)
            if not stat.S_ISREG(opened.st_mode):
                raise ContractError(f"expected a regular file: {path}")
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise ContractError(f"file changed while it was being opened: {path}")
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                content = handle.read()
        finally:
            if descriptor >= 0:
                os.close(descriptor)
    except OSError as error:
        raise ContractError(f"could not read regular file: {path}") from error
    after = path.lstat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise ContractError(f"file changed while it was being read: {path}")
    return content


def sha256_regular(path: Path, *, boundary: Path | None = None) -> str:
    return hashlib.sha256(read_regular(path, boundary=boundary)).hexdigest()


def file_metadata(path: Path, *, boundary: Path | None = None) -> dict[str, Any]:
    content = read_regular(path, boundary=boundary)
    return {"sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}


def source_inventory(root: Path) -> tuple[str, dict[str, str]]:
    root = root.resolve(strict=True)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", *SOURCE_PREFIXES],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if untracked:
        raise ContractError(
            "untracked demo source inputs are not provenance-bound: " + ", ".join(untracked)
        )
    listing = subprocess.run(
        ["git", "ls-files", "--cached", *SOURCE_PREFIXES],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    entries: dict[str, str] = {}
    for relative in sorted(listing):
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            raise ContractError(f"unsafe source input path: {relative}")
        entries[relative] = sha256_regular(root / Path(*pure.parts), boundary=root)
    digest = hashlib.sha256()
    for relative, value in entries.items():
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(value.encode())
        digest.update(b"\n")
    return digest.hexdigest(), entries


def receipt_token(receipt_without_token: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(receipt_without_token)).hexdigest()


def build_receipt(
    root: Path,
    *,
    model: Path,
    voices: Path,
    audio: Path,
    mp4: Path,
    gif: Path,
    tools: dict[str, str],
) -> dict[str, Any]:
    source_digest, source_files = source_inventory(root)
    source_revision = subprocess.run(
        ["git", "rev-parse", "HEAD^{commit}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "status": "built-awaiting-human-review",
        "source_revision": source_revision,
        "source_input_tree_sha256": source_digest,
        "source_files": source_files,
        "narration": {
            "engine": "kokoro-onnx",
            "version": "0.4.9",
            "voice": "af_heart",
            "model": file_metadata(model),
            "voices": file_metadata(voices),
            "audio": file_metadata(audio, boundary=root),
            "generator_sha256": sha256_regular(
                root / "scripts/demo/generate-kokoro-narration.py", boundary=root
            ),
            "requirements_sha256": sha256_regular(
                root / "scripts/demo/requirements-kokoro.txt", boundary=root
            ),
        },
        "inputs": {
            "script": file_metadata(
                root / "docs/media/observatory-overview-script.txt", boundary=root
            ),
            "captions": file_metadata(
                root / "docs/media/observatory-overview.vtt", boundary=root
            ),
            "scenes": file_metadata(root / "scripts/demo/scenes.json", boundary=root),
        },
        "candidates": {
            "mp4": file_metadata(mp4, boundary=root),
            "gif": file_metadata(gif, boundary=root),
        },
        "tools": tools,
    }
    receipt["review_token"] = receipt_token(receipt)
    return receipt


def load_receipt(path: Path, *, boundary: Path) -> dict[str, Any]:
    try:
        receipt = json.loads(read_regular(path, boundary=boundary))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ContractError(f"invalid build receipt: {path}") from error
    if not isinstance(receipt, dict):
        raise ContractError("build receipt must be a JSON object")
    return receipt


def validate_receipt(
    root: Path,
    receipt: dict[str, Any],
    *,
    model: Path,
    voices: Path,
    mp4: Path,
    gif: Path,
    review_token_value: str,
) -> None:
    if receipt.get("schema_version") != RECEIPT_SCHEMA_VERSION:
        raise ContractError("unsupported build receipt schema")
    stored_token = receipt.get("review_token")
    unsigned = {key: value for key, value in receipt.items() if key != "review_token"}
    if not isinstance(stored_token, str) or stored_token != receipt_token(unsigned):
        raise ContractError("build receipt checksum is invalid")
    if review_token_value != stored_token:
        raise ContractError("review token does not match the exact built candidates")
    expected_narration = receipt.get("narration", {})
    if (
        expected_narration.get("engine") != "kokoro-onnx"
        or expected_narration.get("version") != "0.4.9"
        or expected_narration.get("voice") != "af_heart"
    ):
        raise ContractError("receipt does not identify the required Kokoro narration")
    checks = (
        (model, expected_narration.get("model"), None),
        (voices, expected_narration.get("voices"), None),
        (mp4, receipt.get("candidates", {}).get("mp4"), root),
        (gif, receipt.get("candidates", {}).get("gif"), root),
        (
            root / "docs/media/observatory-overview-script.txt",
            receipt.get("inputs", {}).get("script"),
            root,
        ),
        (
            root / "docs/media/observatory-overview.vtt",
            receipt.get("inputs", {}).get("captions"),
            root,
        ),
        (root / "scripts/demo/scenes.json", receipt.get("inputs", {}).get("scenes"), root),
    )
    for path, expected, boundary in checks:
        if not isinstance(expected, dict) or file_metadata(path, boundary=boundary) != expected:
            raise ContractError(f"receipt-bound input changed after build: {path}")
    source_digest, source_files = source_inventory(root)
    if (
        receipt.get("source_input_tree_sha256") != source_digest
        or receipt.get("source_files") != source_files
    ):
        raise ContractError("demo source tree changed after the candidate was built")
    current_revision = subprocess.run(
        ["git", "rev-parse", "HEAD^{commit}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if receipt.get("source_revision") != current_revision:
        raise ContractError("source revision changed after the candidate was built")


def verify_manifest(root: Path, manifest: dict[str, Any]) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_PATHS):
        raise ContractError("manifest artifact allowlist is invalid")
    for relative in ARTIFACT_PATHS:
        expected = artifacts[relative]
        if not isinstance(expected, dict):
            raise ContractError(f"invalid artifact metadata: {relative}")
        actual = file_metadata(root / relative, boundary=root)
        if actual != {"sha256": expected.get("sha256"), "bytes": expected.get("bytes")}:
            raise ContractError(f"artifact metadata mismatch: {relative}")


def atomic_publish(replacements: dict[Path, Path]) -> None:
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path] = {}
    replaced: list[Path] = []
    try:
        for source, destination in replacements.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                prefix=f".{destination.name}.",
                suffix=".staged",
                dir=destination.parent,
                delete=False,
            ) as handle:
                stage = Path(handle.name)
                handle.write(read_regular(source))
                handle.flush()
                os.fsync(handle.fileno())
            staged[destination] = stage
            if destination.exists():
                with tempfile.NamedTemporaryFile(
                    prefix=f".{destination.name}.",
                    suffix=".backup",
                    dir=destination.parent,
                    delete=False,
                ) as handle:
                    backup = Path(handle.name)
                    handle.write(read_regular(destination))
                    handle.flush()
                    os.fsync(handle.fileno())
                backups[destination] = backup
        for destination, stage in staged.items():
            os.replace(stage, destination)
            replaced.append(destination)
        if os.name != "nt":
            for destination in {path.parent for path in replacements.values()}:
                descriptor = os.open(destination, os.O_RDONLY)
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
    except BaseException:
        for destination in reversed(replaced):
            backup = backups.get(destination)
            if backup and backup.exists():
                os.replace(backup, destination)
            elif destination.exists():
                destination.unlink()
        raise
    finally:
        for path in (*staged.values(), *backups.values()):
            path.unlink(missing_ok=True)
