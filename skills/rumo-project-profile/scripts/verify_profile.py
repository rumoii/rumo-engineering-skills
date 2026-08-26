#!/usr/bin/env python3
"""Validate local project profiles without reading credential values."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REQUIRED_FILES = ("project.json", "frontend.json", "backend.json", "runtime.json", "data.json")
SECRET_FIELD_NAMES = {"password", "token", "secret", "private_key", "api_key"}
SECRET_FIELD_SUFFIXES = ("_password", "_token", "_secret", "_private_key", "_api_key")
FORBIDDEN_TRACKED_NAMES = {"credentials.md", "credentials.env", "secrets.env", "pwd.md"}


def _secret_value_errors(value: object, key: str, path: Path, errors: list[str]) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _secret_value_errors(child_value, str(child_key), path, errors)
        return
    if isinstance(value, list):
        for item in value:
            _secret_value_errors(item, key, path, errors)
        return
    if not isinstance(value, str) or not value.strip():
        return
    normalized = key.lower()
    if normalized.endswith("_env") or normalized.endswith("_file"):
        return
    if normalized in SECRET_FIELD_NAMES or normalized.endswith(SECRET_FIELD_SUFFIXES):
        errors.append(f"{path}: possible plaintext secret in field {key!r}")


def validate_profile(profile: Path) -> list[str]:
    errors: list[str] = []
    project_path = profile / "project.json"
    if not project_path.is_file():
        return [f"{project_path}: required file not found"]

    objects: dict[str, dict[str, object]] = {}
    for name in REQUIRED_FILES + ("documents.json",):
        path = profile / name
        if not path.is_file():
            if name != "documents.json":
                errors.append(f"{path}: required file not found")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid UTF-8 JSON: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{path}: top-level JSON value must be an object")
            continue
        objects[name] = data
        _secret_value_errors(data, "", path, errors)
        references = data.get("references")
        if isinstance(references, str) and references:
            reference_path = (profile / references).resolve()
            try:
                reference_path.relative_to(profile.resolve())
            except ValueError:
                errors.append(f"{path}: references path must stay inside the profile: {references}")
                continue
            if not reference_path.exists():
                errors.append(f"{path}: references path not found: {references}")

    project = objects.get("project.json", {})
    if project.get("id") != profile.name:
        errors.append(f"{project_path}: id must match directory name {profile.name!r}")
    return errors


def validate_root(root: Path) -> list[str]:
    profiles = root / "profiles"
    if not profiles.is_dir():
        return [f"{profiles}: profiles directory not found"]
    errors: list[str] = []
    for profile in sorted(path for path in profiles.iterdir() if path.is_dir()):
        errors.extend(validate_profile(profile))
    try:
        tracked = subprocess.run(
            ["git", "-C", str(root), "ls-files"],
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError:
        tracked = None
    if tracked is not None and tracked.returncode == 0:
        for relative in tracked.stdout.splitlines():
            if Path(relative).name.lower() in FORBIDDEN_TRACKED_NAMES:
                errors.append(f"{root / relative}: plaintext credential file must remain untracked")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.profiles_root.expanduser().resolve()
    errors = validate_root(root)
    if errors:
        print(f"Profile validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    count = sum(1 for path in (root / "profiles").iterdir() if path.is_dir())
    print(f"Profile validation passed: {count} profile(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
