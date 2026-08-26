#!/usr/bin/env python3
"""Create a local, generic project profile from the bundled templates."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path


PROFILE_ID_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")
TEMPLATE_FILES = (
    "frontend.json",
    "backend.json",
    "runtime.json",
    "data.json",
    "documents.json",
    "credentials.example.env",
    "README.md",
)


def templates_root() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def validate_profile_id(profile_id: str) -> None:
    if not PROFILE_ID_RE.fullmatch(profile_id):
        raise ValueError(
            "Profile id must contain only lowercase letters, digits, hyphens, and underscores "
            "and must not start or end with a separator"
        )


def write_project_json(path: Path, profile_id: str) -> None:
    data = {
        "id": profile_id,
        "description": "Project-specific profile created from the generic template.",
        "repositories": [],
        "languages": [],
        "frameworks": [],
        "default_output_language": "zh-CN",
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_profile(profile_id: str, profiles_root: Path) -> Path:
    validate_profile_id(profile_id)
    source = templates_root()
    required = [source / name for name in ("project.json", *TEMPLATE_FILES)]
    missing = [path for path in required if not path.is_file()]
    if missing:
        names = ", ".join(str(path) for path in missing)
        raise FileNotFoundError(f"Profile template file(s) not found: {names}")

    target = profiles_root.expanduser().resolve() / "profiles" / profile_id
    if target.exists():
        raise FileExistsError(f"Profile already exists: {target}")

    target.mkdir(parents=True)
    try:
        write_project_json(target / "project.json", profile_id)
        for name in TEMPLATE_FILES:
            shutil.copyfile(source / name, target / name)
        (target / "references").mkdir()
    except Exception:
        for path in sorted(target.rglob("*"), reverse=True):
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
        target.rmdir()
        raise
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True, help="new profile id, for example demo-project")
    parser.add_argument(
        "--profiles-root",
        type=Path,
        default=Path.home() / ".rumo-skill-profiles",
        help="profile root directory; profiles are created below its profiles/ child",
    )
    args = parser.parse_args()
    try:
        target = create_profile(args.profile, args.profiles_root)
    except (FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(f"Profile created: {target}")
    print("Fill in the JSON files as the project becomes available.")
    print(f"Use --profile {args.profile} or set RUMO_PROJECT_PROFILE={args.profile} to select it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
