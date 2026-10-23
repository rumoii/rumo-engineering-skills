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
        (node, "extras/rumo-diagram/scripts/test-topology-skill.mjs"),
        (node, "extras/rumo-imagegen/scripts/generate.test.mjs"),
        (node, "scripts/tests/pi_workspace_guard.test.mjs"),
        (sys.executable, "extras/rumo-daily-report/scripts/test_daily_report.py"),
        (sys.executable, "skills/rumo-agent-collaboration/scripts/test_agent_run.py"),
        (sys.executable, "skills/rumo-agent-collaboration/scripts/test_agent_config.py"),
        (sys.executable, "skills/rumo-review/scripts/test_app_server_review.py"),
        (sys.executable, "extras/rumo-linux-inspect/scripts/remote_memory_inspection.py", "--dry-run", "--host", "<host>"),
    )
    for command in commands:
        print(f"+ {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
