"""Portable checks at trusted workflow boundaries; no model or provider dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from observatory.safe_files import read_regular


class BoundaryError(ValueError):
    """A boundary cannot establish the required invariant."""


def strict_json(text: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise BoundaryError("duplicate JSON key")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise BoundaryError("non-finite JSON number")

    def number(value: str) -> float:
        result = float(value)
        if not math.isfinite(result):
            raise BoundaryError("non-finite JSON number")
        return result

    try:
        return json.loads(
            text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number
        )
    except (ValueError, RecursionError) as error:
        raise BoundaryError("invalid strict JSON") from error


def validate_output(value: Any, contract: Any, path: str = "$", depth: int = 0) -> None:
    """Validate a small closed contract dialect, explicitly not full JSON Schema.

    Every object field is required; extra fields are rejected. Supported keys:
    type, fields (object), items (array), min/max (array length or string length).
    """
    if depth == 0:
        validate_contract(contract)
    if depth > 50 or not isinstance(contract, dict):
        raise BoundaryError("invalid or overly nested contract")
    kind = contract.get("type")
    allowed = {
        "object": {"type", "fields"},
        "array": {"type", "items", "min", "max"},
        "string": {"type", "min", "max"},
        "integer": {"type"},
        "number": {"type"},
        "boolean": {"type"},
        "null": {"type"},
    }
    if not isinstance(kind, str) or kind not in allowed or set(contract) - allowed[kind]:
        raise BoundaryError("unsupported contract type or keyword")
    types: dict[str, Any] = {
        "object": dict,
        "array": list,
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "null": type(None),
    }
    if not isinstance(value, types[kind]) or (
        kind in {"integer", "number"} and isinstance(value, bool)
    ):
        raise BoundaryError(f"{path}: wrong type")
    if kind == "number" and isinstance(value, float) and not math.isfinite(value):
        raise BoundaryError(f"{path}: non-finite number")
    for bound in ("min", "max"):
        if bound in contract:
            n = contract[bound]
            if type(n) is not int or n < 0:
                raise BoundaryError("invalid length bound")
            if (bound == "min" and len(value) < n) or (bound == "max" and len(value) > n):
                raise BoundaryError(f"{path}: length outside contract")
    if contract.get("min", 0) > contract.get("max", sys.maxsize):
        raise BoundaryError("reversed length bounds")
    if kind == "object":
        fields = contract.get("fields")
        if not isinstance(fields, dict) or not all(isinstance(k, str) for k in fields):
            raise BoundaryError("object contract requires fields")
        if set(value) != set(fields):
            raise BoundaryError(f"{path}: missing or extra fields")
        for key, child in fields.items():
            validate_output(value[key], child, f"{path}.{key}", depth + 1)
    elif kind == "array":
        if "items" not in contract:
            raise BoundaryError("array contract requires items")
        # Validate item definitions even for empty arrays, using a separate schema walk.
        validate_contract(contract["items"], depth + 1)
        for index, item in enumerate(value):
            validate_output(item, contract["items"], f"{path}[{index}]", depth + 1)


def validate_contract(contract: Any, depth: int = 0) -> None:
    if depth > 50 or not isinstance(contract, dict):
        raise BoundaryError("invalid contract")
    allowed = {
        "object": {"type", "fields"},
        "array": {"type", "items", "min", "max"},
        "string": {"type", "min", "max"},
        "integer": {"type"},
        "number": {"type"},
        "boolean": {"type"},
        "null": {"type"},
    }
    kind = contract.get("type")
    if not isinstance(kind, str) or kind not in allowed or set(contract) - allowed[kind]:
        raise BoundaryError("unsupported contract type or keyword")
    for bound in ("min", "max"):
        if bound in contract and (type(contract[bound]) is not int or contract[bound] < 0):
            raise BoundaryError("invalid length bound")
    if contract.get("min", 0) > contract.get("max", sys.maxsize):
        raise BoundaryError("reversed length bounds")
    if kind == "object":
        fields = contract.get("fields")
        if not isinstance(fields, dict) or not all(isinstance(k, str) for k in fields):
            raise BoundaryError("object contract requires fields")
        for child in fields.values():
            validate_contract(child, depth + 1)
    elif kind == "array":
        validate_contract(contract.get("items"), depth + 1)


def fingerprint(value: Any) -> str:
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (ValueError, TypeError) as error:
        raise BoundaryError("request is not JSON data") from error
    return hashlib.sha256(data).hexdigest()


def artifact_hashes(root: Path, paths: list[str]) -> dict[str, str]:
    if not paths or len(set(paths)) != len(paths):
        raise BoundaryError("provide a nonempty unique artifact list")
    result = {}
    for name in sorted(paths):
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
            raise BoundaryError("artifact path must be normalized and relative")
        result[name] = hashlib.sha256(read_regular(root / path, boundary=root)).hexdigest()
    return result


def make_receipt(
    root: Path,
    paths: list[str],
    check: str,
    before: dict[str, str],
    passed: bool,
    details: dict[str, Any],
) -> dict[str, Any]:
    after = artifact_hashes(root, paths)
    return {
        "version": 1,
        "root": str(root.resolve()),
        "check": check,
        "at": datetime.now(UTC).isoformat(),
        "artifacts": after,
        "passed": passed is True and before == after,
        "stable": before == after,
        "details": details,
    }


def require_receipt(root: Path, paths: list[str], check: str, receipt: Any) -> None:
    if not isinstance(receipt, dict) or receipt.get("version") != 1:
        raise BoundaryError("missing or unsupported check receipt")
    if not check or receipt.get("check") != check or receipt.get("root") != str(root.resolve()):
        raise BoundaryError("receipt scope or check mismatch")
    if receipt.get("passed") is not True or receipt.get("stable") is not True:
        raise BoundaryError("check did not pass on stable artifacts")
    if receipt.get("artifacts") != artifact_hashes(root, paths):
        raise BoundaryError("stale receipt or different artifact scope")


def operation_decision(status: Any, operation_id: str, request_fingerprint: str) -> str:
    """Consume fresh trusted adapter state; never dispatch or change an operation."""
    if (
        not operation_id
        or len(request_fingerprint) != 64
        or any(c not in "0123456789abcdef" for c in request_fingerprint)
    ):
        raise BoundaryError("invalid expected operation identity")
    if (
        not isinstance(status, dict)
        or status.get("operation_id") != operation_id
        or (status.get("fingerprint") != request_fingerprint)
    ):
        raise BoundaryError("operation identity conflict")
    state = status.get("status")
    if state == "committed":
        return "already_complete"
    if state == "confirmed_not_applied":
        return "retry_permitted"
    raise BoundaryError("operation unresolved; inspect authoritative status before retry")


def add_parser(subparsers: Any) -> None:
    parser = subparsers.add_parser("enforce", help="Validate output, evidence, or retry state")
    subs = parser.add_subparsers(dest="boundary", required=True)
    output = subs.add_parser("output")
    output.add_argument("value", type=Path)
    output.add_argument("--contract", type=Path, required=True)
    for name in ("check", "completion"):
        command = subs.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        command.add_argument("--artifact", action="append", required=True)
        command.add_argument("--check", required=True)
        command.add_argument("--receipt", type=Path, required=True)
        if name == "check":
            command.add_argument("--timeout", type=float, default=120)
            command.add_argument("argv", nargs=argparse.REMAINDER)
    operation = subs.add_parser("operation")
    operation.add_argument("status", type=Path)
    operation.add_argument("--operation-id", required=True)
    operation.add_argument("--fingerprint", required=True)


def handle(args: argparse.Namespace) -> int:
    try:
        decision = "accepted"
        if args.boundary == "output":
            contract = strict_json(read_regular(args.contract).decode())
            validate_contract(contract)
            validate_output(strict_json(read_regular(args.value).decode()), contract)
        elif args.boundary == "operation":
            decision = operation_decision(
                strict_json(read_regular(args.status).decode()), args.operation_id, args.fingerprint
            )
        elif args.boundary == "completion":
            require_receipt(
                args.root,
                args.artifact,
                args.check,
                strict_json(read_regular(args.receipt).decode()),
            )
        else:
            argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
            if not argv or not 0 < args.timeout <= 3600 or not args.check:
                raise BoundaryError("check requires a command, name and bounded timeout")
            before = artifact_hashes(args.root, args.artifact)
            # Reserve a NEW receipt before executing; never leave an old passing receipt.
            with args.receipt.open("x", encoding="utf-8") as out:
                started = time.monotonic()
                try:
                    result = subprocess.run(
                        argv,
                        cwd=args.root,
                        timeout=args.timeout,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    details = {"returncode": result.returncode}
                    passed = result.returncode == 0
                except subprocess.TimeoutExpired:
                    details = {"timeout": True}
                    passed = False
                receipt = make_receipt(
                    args.root,
                    args.artifact,
                    args.check,
                    before,
                    passed,
                    {
                        **details,
                        "seconds": time.monotonic() - started,
                        "command_sha256": fingerprint(argv),
                    },
                )
                json.dump(receipt, out, indent=2)
            require_receipt(args.root, args.artifact, args.check, receipt)
        print(json.dumps({"ok": True, "decision": decision}))
        return 0
    except (BoundaryError, OSError, UnicodeError, RecursionError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
