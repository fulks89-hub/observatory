"""Opt-in, metadata-only read preflight; not a sandbox or content classifier."""

from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path
from typing import Any

from observatory.enforcement import strict_json

MAX_REQUEST_BYTES = 64 * 1024


class GuardError(ValueError):
    """A fixed, non-sensitive reason to stop the request."""


def check_read(file_path: object, *, root: Path, max_bytes: int) -> None:
    """Check host-native absolute paths without opening file contents.

    The trusted caller owns root/limit and must serialize check and actual read.
    No permission is granted by a successful preflight.
    """
    if type(max_bytes) is not int or max_bytes <= 0:
        raise GuardError("read guard: configure a positive byte limit")
    if not isinstance(file_path, str) or not file_path or "\x00" in file_path:
        raise GuardError("read guard: expected an absolute file path")
    path = Path(file_path)
    if not path.is_absolute() or ".." in path.parts:
        raise GuardError("read guard: absolute path without traversal required")
    # Reject network/device namespaces before any filesystem lookup.
    if path.anchor.startswith(("//", "\\\\")) or root.anchor.startswith(("//", "\\\\")):
        raise GuardError("read guard: network and device paths are unsupported")
    try:
        boundary = root.resolve(strict=True)
        if not boundary.is_dir():
            raise GuardError("read guard: configured root is not a directory")
        relative = path.relative_to(boundary)
        if not relative.parts:
            raise GuardError("read guard: expected a regular file")
        current = boundary
        for part in relative.parts:
            # Windows alternate streams and reserved device names are not files here.
            if sys.platform == "win32" and (":" in part or Path(part).is_reserved()):
                raise GuardError("read guard: unsupported file name")
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or current.is_junction():
                raise GuardError("read guard: links and junctions are unsupported")
        if not stat.S_ISREG(metadata.st_mode):
            raise GuardError("read guard: expected a regular file")
        if metadata.st_size > max_bytes:
            raise GuardError("read guard: file exceeds configured byte limit")
    except GuardError:
        raise
    except (OSError, ValueError, RuntimeError) as from_error:
        raise GuardError("read guard: path unavailable or outside configured root") from from_error


def inspect_request(raw: bytes, *, root: Path, max_bytes: int, adapter: str) -> None:
    """Discard provider metadata; request data cannot set policy or bypass a denial."""
    if len(raw) > MAX_REQUEST_BYTES:
        raise GuardError("read guard: request exceeds input limit")
    try:
        request = strict_json(raw.decode("utf-8"))
    except (ValueError, UnicodeError, RecursionError):
        raise GuardError("read guard: malformed request") from None
    if not isinstance(request, dict):
        raise GuardError("read guard: expected a request object")
    if adapter == "claude-code":
        if request.get("hook_event_name") != "PreToolUse" or request.get("tool_name") != "Read":
            raise GuardError("read guard: adapter requires PreToolUse Read")
        request = request.get("tool_input")
        if not isinstance(request, dict):
            raise GuardError("read guard: expected tool input")
        # Read offsets/limits do not relax the whole-file byte limit. Other provider
        # metadata is ignored, never logged or interpreted as policy.
    elif adapter != "generic" or set(request) != {"file_path"}:
        raise GuardError("read guard: unsupported request fields or adapter")
    check_read(request.get("file_path"), root=root, max_bytes=max_bytes)


def add_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("guard-read", help="Preflight a bounded local file read")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, required=True)
    parser.add_argument("--adapter", choices=("generic", "claude-code"), default="generic")


def handle(args: argparse.Namespace) -> int:
    try:
        raw = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        inspect_request(raw, root=args.root, max_bytes=args.max_bytes, adapter=args.adapter)
    except (GuardError, OSError, ValueError, RecursionError) as error:
        reason = str(error) if isinstance(error, GuardError) else "read guard: input unavailable"
        if args.adapter == "generic":
            print(json.dumps({"decision": "deny", "reason": reason}))
        else:
            # PreToolUse exit 2 blocks; do not mix provider JSON with exit signaling.
            print(reason, file=sys.stderr)
        return 2
    if args.adapter == "generic":
        print(json.dumps({"decision": "pass"}))
    # No Claude allow response: leave native permission checks in control.
    return 0
