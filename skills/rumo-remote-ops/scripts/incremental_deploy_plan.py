#!/usr/bin/env python3
"""Generate a non-executing incremental deployment plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, action="append", required=True)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", default="root")
    parser.add_argument("--destination", required=True)
    parser.add_argument("--service", action="append", default=[])
    parser.add_argument("--verify-command", action="append", default=[])
    args = parser.parse_args()
    if not args.profile.is_dir():
        parser.error("--profile must be an existing directory")
    artifacts = []
    for value in args.artifact:
        path = value.expanduser().resolve()
        if not path.is_file():
            parser.error(f"artifact not found: {path}")
        artifacts.append({"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)})
    plan = {
        "mode": "dry-run",
        "profile": str(args.profile.resolve()),
        "remote": {"host": args.host, "user": args.user, "destination": args.destination},
        "artifacts": artifacts,
        "services": args.service,
        "verification": args.verify_command,
        "required_steps": ["build", "hash", "backup", "copy", "restart", "verify", "rollback-if-needed"],
        "executes_remote_writes": False,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
