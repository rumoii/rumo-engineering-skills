#!/usr/bin/env python3
"""Run focused helper-script tests that live with individual skills."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    node = shutil.which("node")
    if not node:
        print("Node.js is required for the auxiliary skill tests.", file=sys.stderr)
        return 2

    commands = (
        (node, "skills/rumo-engineering-topology-diagram/scripts/test-topology-skill.mjs"),
        (node, "skills/rumo-imagegen/scripts/generate.test.mjs"),
        (sys.executable, "skills/rumo-daily-report/scripts/test_daily_report.py"),
        (sys.executable, "skills/rumo-insight/scripts/test_analyze_sessions.py"),
        (sys.executable, "skills/rumo-insight/scripts/test_summarize_evidence.py"),
        (sys.executable, "skills/rumo-review-fix-loop/scripts/test_app_server_review.py"),
        (sys.executable, "skills/rumo-remote-memory-inspection/quick_validate.py"),
    )
    for command in commands:
        print(f"+ {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
