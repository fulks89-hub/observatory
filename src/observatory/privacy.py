"""Deterministic current-tree and locally reachable Git-history privacy scanning."""

from __future__ import annotations

import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from observatory.safe_files import UnsafePathError, read_regular

MAX_OBJECT_BYTES = 100_000_000
SECRET_PATTERNS = {
    "private key": re.compile(rb"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    "GitHub token": re.compile(rb"\b(?:gh[opusr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "GitLab token": re.compile(rb"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "Slack token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "Google API key": re.compile(rb"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "Stripe live key": re.compile(rb"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}\b"),
    "OpenAI or Anthropic key": re.compile(rb"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b"),
    "npm token": re.compile(rb"\bnpm_[A-Za-z0-9]{30,}\b"),
    "PyPI token": re.compile(rb"\bpypi-[A-Za-z0-9_-]{30,}\b"),
    "generic assigned secret": re.compile(
        rb"(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*[\"']?[A-Za-z0-9_/+.-]{20,}",
        re.IGNORECASE,
    ),
}
EMAIL = re.compile(rb"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
GITHUB_NOREPLY = re.compile(
    rb"(?:[0-9]+\+)?[A-Z0-9](?:[A-Z0-9-]{0,37})@users\.noreply\.github\.com",
    re.IGNORECASE,
)
LOCAL_PATH = re.compile(
    rb"(?:/" + rb"Users/[^/\s]+/|/" + rb"home/[^/\s]+/|[A-Z]:\\\\" + rb"Users\\\\[^\\\s]+\\\\)"
)


@dataclass(frozen=True, slots=True)
class Finding:
    location: str
    kind: str
    secret: bool


@dataclass(frozen=True, slots=True)
class ScanResult:
    findings: tuple[Finding, ...]
    scanned_count: int
    skipped: tuple[str, ...]


def _risky_filename(relative: str) -> str | None:
    name = PurePosixPath(relative).name.casefold()
    if (
        name == ".env"
        or name.startswith(".env.")
        and not name.endswith((".example", ".sample", ".template"))
    ):
        return "risky environment filename"
    if name in {"id_rsa", "id_ed25519", "credentials.json", "service-account.json"}:
        return "risky credential filename"
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return "risky key filename"
    return None


def _content_findings(content: bytes, location: str) -> list[Finding]:
    found = [
        Finding(location, label, True)
        for label, pattern in SECRET_PATTERNS.items()
        if pattern.search(content)
    ]
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = ""
    textual = (
        bool(text)
        and "\0" not in text
        and sum(character.isprintable() or character.isspace() for character in text) / len(text)
        >= 0.9
    )
    if textual:
        for match in EMAIL.findall(content):
            lowered = match.lower()
            _local, _separator, domain = lowered.rpartition(b"@")
            if (
                domain.endswith((b".invalid", b".test"))
                or domain in {b"example.com", b"example.org", b"example.net"}
                or lowered == b"noreply@github.com"
                or GITHUB_NOREPLY.fullmatch(lowered) is not None
            ):
                continue
            found.append(Finding(location, "email address", False))
            break
        if LOCAL_PATH.search(content):
            found.append(Finding(location, "local home-directory path", False))
    return found


def scan_current(
    root: Path, relatives: list[str], *, max_bytes: int = MAX_OBJECT_BYTES
) -> ScanResult:
    findings: list[Finding] = []
    skipped: list[str] = []
    scanned = 0
    for relative in sorted(set(relatives)):
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts:
            skipped.append(f"{relative}: unsafe tracked path")
            continue
        risky = _risky_filename(relative)
        if risky:
            findings.append(Finding(relative, risky, True))
        findings.extend(_content_findings(relative.encode("utf-8"), f"path:{relative}"))
        path = root / Path(*pure.parts)
        try:
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                content = path.readlink().as_posix().encode()
            elif not stat.S_ISREG(metadata.st_mode):
                skipped.append(f"{relative}: not a regular file")
                continue
            elif metadata.st_size > max_bytes:
                skipped.append(f"{relative}: object exceeds {max_bytes} bytes")
                continue
            else:
                content = read_regular(path, boundary=root)
        except (OSError, UnsafePathError) as error:
            skipped.append(f"{relative}: could not scan ({error})")
            continue
        scanned += 1
        findings.extend(_content_findings(content, relative))
    return ScanResult(tuple(dict.fromkeys(findings)), scanned, tuple(dict.fromkeys(skipped)))


def scan_history(root: Path, *, max_bytes: int = MAX_OBJECT_BYTES) -> ScanResult:
    listing = subprocess.Popen(
        ["git", "-C", str(root), "rev-list", "--objects", "--all"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if listing.stdout is None:
        raise subprocess.SubprocessError("could not read git object listing")
    objects: dict[str, set[str]] = {}
    for line in listing.stdout:
        line = line.rstrip("\n")
        object_id, _, path = line.partition(" ")
        objects.setdefault(object_id, set())
        if path:
            objects[object_id].add(path)
    listing_error = listing.stderr.read() if listing.stderr is not None else ""
    if listing.wait() != 0:
        raise subprocess.CalledProcessError(
            listing.returncode, listing.args, stderr=listing_error
        )
    ordered = sorted(objects)
    object_kinds: dict[str, tuple[str, int]] = {}
    for start in range(0, len(ordered), 512):
        chunk = ordered[start : start + 512]
        checked = subprocess.run(
            ["git", "-C", str(root), "cat-file", "--batch-check"],
            input=("\n".join(chunk) + "\n").encode(),
            check=True,
            capture_output=True,
        ).stdout.decode().splitlines()
        for line in checked:
            fields = line.split()
            if len(fields) == 3 and fields[1] in {"blob", "commit", "tag"}:
                object_kinds[fields[0]] = (fields[1], int(fields[2]))
    findings: list[Finding] = []
    skipped: list[str] = []
    selected: list[tuple[str, str]] = []
    for object_id, (kind, size) in sorted(object_kinds.items()):
        paths = sorted(objects[object_id])
        path_label = paths[0] if paths else "<metadata>"
        location = f"history:{kind}:{object_id}:{path_label}"
        if kind == "blob":
            for path in paths:
                path_location = f"history:path:{object_id}:{path}"
                risky = _risky_filename(path)
                if risky:
                    findings.append(Finding(path_location, risky, True))
                findings.extend(_content_findings(path.encode("utf-8"), path_location))
        if size > max_bytes:
            skipped.append(f"{location}: object exceeds {max_bytes} bytes")
            continue
        selected.append((object_id, kind))
    batch = subprocess.Popen(
        ["git", "-C", str(root), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if batch.stdin is None or batch.stdout is None:
        batch.kill()
        raise subprocess.SubprocessError("could not open git object stream")
    scanned = 0
    try:
        for expected_id, expected_kind in selected:
            batch.stdin.write((expected_id + "\n").encode())
            batch.stdin.flush()
            header = batch.stdout.readline().decode().split()
            if len(header) != 3 or header[0] != expected_id or header[1] != expected_kind:
                raise subprocess.SubprocessError("unexpected git cat-file batch response")
            size = int(header[2])
            content = bytearray()
            remaining = size
            while remaining:
                part = batch.stdout.read(min(remaining, 1024 * 1024))
                if not part:
                    raise subprocess.SubprocessError("truncated git cat-file batch response")
                content.extend(part)
                remaining -= len(part)
            if batch.stdout.read(1) != b"\n":
                raise subprocess.SubprocessError("truncated git cat-file batch response")
            paths = sorted(objects[expected_id])
            location = (
                f"history:{expected_kind}:{expected_id}:{paths[0] if paths else '<metadata>'}"
            )
            findings.extend(_content_findings(bytes(content), location))
            scanned += 1
    finally:
        batch.stdin.close()
    batch_error = batch.stderr.read().decode(errors="replace") if batch.stderr is not None else ""
    if batch.wait() != 0:
        raise subprocess.CalledProcessError(batch.returncode, batch.args, stderr=batch_error)
    return ScanResult(tuple(dict.fromkeys(findings)), scanned, tuple(dict.fromkeys(skipped)))
