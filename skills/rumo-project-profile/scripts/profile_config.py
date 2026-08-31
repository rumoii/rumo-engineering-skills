#!/usr/bin/env python3
"""Persist the optional private Rumo project-profiles repository path."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


CONFIG_DIR = ".rumo-engineering-skills"
CONFIG_NAME = "config.json"


def config_path() -> Path:
    """Return the user-level configuration path."""
    return Path.home() / CONFIG_DIR / CONFIG_NAME


def validate_profiles_repo(value: str) -> Path:
    """Resolve and validate a profiles checkout without reading credentials."""
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise ValueError("profiles repository path must be absolute")
    resolved = candidate.resolve()
    if not (resolved / "profiles").is_dir():
        raise FileNotFoundError(
            f"Profiles repository must contain a profiles directory: {resolved}"
        )
    return resolved


def read_profiles_repo() -> Path | None:
    """Read the persisted profiles checkout, failing closed on corruption."""
    path = config_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        value = data["profiles_repo"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"Rumo skill configuration is invalid: {path}: {exc}") from exc
    if not isinstance(value, str):
        raise RuntimeError(
            f"Rumo skill configuration has an invalid profiles_repo: {path}"
        )
    try:
        return validate_profiles_repo(value)
    except (FileNotFoundError, ValueError) as exc:
        raise RuntimeError(str(exc)) from exc


def write_profiles_repo(value: str) -> Path:
    """Atomically persist a validated profiles checkout path."""
    resolved = validate_profiles_repo(value)
    target = config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(
                {"profiles_repo": str(resolved)},
                handle,
                ensure_ascii=False,
                indent=2,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-repo", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        resolved = validate_profiles_repo(args.profiles_repo)
        if not args.dry_run:
            write_profiles_repo(str(resolved))
    except (FileNotFoundError, OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    action = "validated" if args.dry_run else "configured"
    print(f"Profiles repository {action}: {resolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
