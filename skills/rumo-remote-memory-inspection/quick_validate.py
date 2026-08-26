#!/usr/bin/env python3
"""Validate the rumo-remote-memory-inspection skill package."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent
SCRIPT = SKILL_DIR / "scripts" / "remote_memory_inspection.py"
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
TARGETS_EXAMPLE = SKILL_DIR / "references" / "targets.example.tsv"


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    for path in (SCRIPT, SKILL_MD, OPENAI_YAML, TARGETS_EXAMPLE):
        require(path.is_file(), f"missing required file: {path}")

    skill_text = SKILL_MD.read_text(encoding="utf-8")
    require(skill_text.startswith("---\n"), "SKILL.md must start with YAML frontmatter")
    require("name: rumo-remote-memory-inspection" in skill_text, "SKILL.md frontmatter name mismatch")
    require("description:" in skill_text, "SKILL.md frontmatter description missing")

    openai_text = OPENAI_YAML.read_text(encoding="utf-8")
    short_match = re.search(r'short_description:\s*"([^"]+)"', openai_text)
    require(short_match is not None, "openai.yaml short_description missing")
    short_description = short_match.group(1)
    require(25 <= len(short_description) <= 64, "short_description must be 25-64 characters")
    require('display_name: "Rumo Remote Memory Inspection"' in openai_text, "display_name mismatch")

    run([sys.executable, "-m", "py_compile", str(SCRIPT)])
    run([sys.executable, str(SCRIPT), "--dry-run", "--host", "<host>"])
    first_target = next(
        line.split("\t", 1)[0]
        for line in TARGETS_EXAMPLE.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )
    run([sys.executable, str(SCRIPT), "--dry-run", "--host", first_target])

    print("rumo-remote-memory-inspection skill is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
