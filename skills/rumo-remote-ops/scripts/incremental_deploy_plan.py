#!/usr/bin/env python3
"""Generate a non-executing incremental deployment plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_TEXT = (
    "id", "purpose", "host_env", "destination", "backup_rule", "restart_command",
    "rollback_command", "build_command", "build_workdir",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_deployment(profile: Path, destination: str) -> dict:
    path = profile / "runtime.json"
    try:
        runtime = json.loads(path.read_text(encoding="utf-8"))
        deployments = runtime["deployments"]
        if not isinstance(deployments, list):
            raise TypeError("deployments must be a list")
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ValueError(f"valid runtime.json with a deployments list is required: {exc}") from exc
    matches = [item for item in deployments if isinstance(item, dict) and item.get("destination") == destination]
    if len(matches) != 1:
        raise ValueError(f"expected one deployment for destination {destination!r}, found {len(matches)}")
    deployment = matches[0]
    missing = [name for name in REQUIRED_TEXT if not isinstance(deployment.get(name), str) or not deployment[name].strip()]
    if not isinstance(deployment.get("services"), list) or not all(isinstance(item, str) and item.strip() for item in deployment["services"]):
        missing.append("services")
    if not isinstance(deployment.get("verification_commands"), list) or not deployment["verification_commands"]:
        missing.append("verification_commands")
    elif not all(isinstance(item, str) and item.strip() for item in deployment["verification_commands"]):
        missing.append("verification_commands")
    if missing:
        raise ValueError(f"deployment {deployment.get('id') or '<unnamed>'} missing or invalid: {', '.join(missing)}")
    return deployment


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
    try:
        deployment = load_deployment(args.profile, args.destination)
    except ValueError as exc:
        parser.error(str(exc))
    artifacts = []
    for value in args.artifact:
        path = value.expanduser().resolve()
        if not path.is_file():
            parser.error(f"artifact not found: {path}")
        artifacts.append({"path": str(path), "size": path.stat().st_size, "sha256": sha256(path)})
    plan = {
        "mode": "dry-run",
        "profile": str(args.profile.resolve()),
        "deployment": deployment["id"],
        "purpose": deployment["purpose"],
        "build": {"command": deployment["build_command"], "workdir": deployment["build_workdir"]},
        "remote": {"host": args.host, "user": args.user, "destination": args.destination},
        "artifacts": artifacts,
        "services": args.service or deployment["services"],
        "backup": deployment["backup_rule"],
        "restart": deployment["restart_command"],
        "verification": args.verify_command or deployment["verification_commands"],
        "rollback": deployment["rollback_command"],
        "required_steps": ["build", "hash", "backup", "copy", "restart", "verify", "rollback-if-needed"],
        "executes_remote_writes": False,
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
