#!/usr/bin/env python3
"""Run the repository Python suite and verify its artifact-bound receipt in CI."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from observatory.cli import main


def artifacts() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        check=True,
        capture_output=True,
    )
    return sorted(set(name.decode() for name in result.stdout.split(b"\0") if name))


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    paths = artifacts()
    common = [
        "--root",
        str(Path.cwd()),
        "--check",
        "repository-python-suite",
        "--receipt",
        str(args.receipt),
    ]
    for name in paths:
        common.extend(["--artifact", name])
    result = main(
        ["enforce", "check", *common, "--timeout", "600", "--", sys.executable, "-m", "pytest"]
    )
    if result:
        return result
    if artifacts() != paths:
        print("Artifact scope changed during the check", file=sys.stderr)
        return 1
    return main(["enforce", "completion", *common])


if __name__ == "__main__":
    raise SystemExit(run())
