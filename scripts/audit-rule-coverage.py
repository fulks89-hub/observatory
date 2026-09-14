#!/usr/bin/env python3
"""Audit declared rules and run their named tests in a reviewed repository."""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from observatory.rule_coverage import CoverageError, audit

if __name__ == "__main__":
    try:
        print(json.dumps(audit(Path.cwd()), indent=2))
    except (ValueError, OSError, RuntimeError, RecursionError, subprocess.SubprocessError,
            ET.ParseError) as error:
        # Detailed pytest output and local paths stay out of the public summary.
        detail = str(error) if isinstance(error, CoverageError) else type(error).__name__
        print(f"Coverage audit failed: {detail}", file=sys.stderr)
        raise SystemExit(1) from None
