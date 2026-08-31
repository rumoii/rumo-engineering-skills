#!/usr/bin/env python3
"""Resolve one private project profile without exposing credential values."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from profile_config import read_profiles_repo


SECTIONS = ("project", "frontend", "backend", "runtime", "data", "documents")
PROFILE_ID_RE = re.compile(r"^[a-z0-9]+(?:[-_][a-z0-9]+)*$")


def repository_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def git_value(repo: Path | None, *args: str) -> str:
    if repo is None:
        return ""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def profiles_root(explicit: Path | None) -> Path:
    if explicit:
        resolved = explicit.expanduser().resolve()
        if not (resolved / "profiles").is_dir():
            raise FileNotFoundError(
                f"Profiles repository must contain a profiles directory: {resolved}"
            )
        return resolved
    configured = os.environ.get("RUMO_SKILL_PROFILES_REPO")
    if configured:
        resolved = Path(configured).expanduser().resolve()
        if not (resolved / "profiles").is_dir():
            raise FileNotFoundError(
                f"Profiles repository must contain a profiles directory: {resolved}"
            )
        return resolved
    persisted = read_profiles_repo()
    if persisted:
        return persisted
    skill_repo = Path(__file__).resolve().parents[3]
    for candidate in (
        skill_repo.parent / "rumo-skill-profiles",
        Path.home() / ".rumo-skill-profiles",
    ):
        resolved = candidate.expanduser().resolve()
        if (resolved / "profiles").is_dir():
            return resolved
    raise FileNotFoundError("No project profiles repository was found")


def read_object(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return data


def safe_profile_path(profiles: Path, profile_id: str) -> Path:
    """Resolve one valid profile ID without following it outside profiles/."""
    if not PROFILE_ID_RE.fullmatch(profile_id):
        raise ValueError(
            "Profile id must contain only lowercase letters, digits, hyphens, and underscores"
        )
    profile = (profiles / profile_id).resolve()
    try:
        profile.relative_to(profiles.resolve())
    except ValueError as exc:
        raise ValueError("Profile must remain inside the profiles directory") from exc
    return profile


def profile_matches(profile: Path, repo_name: str, remote: str) -> bool:
    project_path = profile / "project.json"
    if not project_path.is_file():
        return False
    project = read_object(project_path)
    match = project.get("match", {})
    if not isinstance(match, dict):
        match = {}
    names = match.get("repository_names", [])
    remotes = match.get("remote_contains", [])
    if isinstance(names, list) and repo_name and repo_name in {str(item) for item in names}:
        return True
    if isinstance(remotes, list) and remote:
        return any(str(item) and str(item) in remote for item in remotes)
    repositories = project.get("repositories", [])
    if isinstance(repositories, list):
        return any(isinstance(item, dict) and item.get("name") == repo_name for item in repositories)
    return False


def resolve(args: argparse.Namespace) -> dict[str, object]:
    root = profiles_root(args.profiles_root)
    profiles = root / "profiles"
    requested = args.profile or os.environ.get("RUMO_PROJECT_PROFILE")
    if requested:
        profile = safe_profile_path(profiles, requested)
        if not profile.is_dir():
            raise FileNotFoundError(f"Profile not found: {requested}")
    else:
        repo = repository_root(args.cwd)
        repo_name = repo.name if repo else args.cwd.resolve().name
        remote = git_value(repo, "remote", "get-url", "origin")
        matches = [
            safe_profile_path(profiles, path.name)
            for path in profiles.iterdir()
            if path.is_dir()
            and PROFILE_ID_RE.fullmatch(path.name)
            and profile_matches(safe_profile_path(profiles, path.name), repo_name, remote)
        ]
        if not matches:
            raise LookupError("No project profile matched the current repository")
        if len(matches) > 1:
            raise LookupError("Multiple project profiles matched; specify --profile")
        profile = matches[0]

    project_path = profile / "project.json"
    if not project_path.is_file():
        raise FileNotFoundError(f"Required profile file not found: {project_path}")
    project = read_object(project_path)
    if project.get("id") != profile.name:
        raise ValueError("project.json id must match the profile directory name")

    result: dict[str, object] = {
        "profiles_root": str(root),
        "profile_id": profile.name,
        "profile_path": str(profile),
        "project": project,
        "credentials": {
            "path": str(profile / "credentials.md"),
            "available": (profile / "credentials.md").is_file(),
        },
    }
    if args.section:
        section_path = profile / f"{args.section}.json"
        result[args.section] = read_object(section_path) if section_path.is_file() else {}
    else:
        for section in SECTIONS[1:]:
            section_path = profile / f"{section}.json"
            if section_path.is_file():
                result[section] = read_object(section_path)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--profiles-root", type=Path)
    parser.add_argument("--profile")
    parser.add_argument("--section", choices=SECTIONS[1:])
    args = parser.parse_args()
    try:
        print(json.dumps(resolve(args), ensure_ascii=False, indent=2))
    except (FileNotFoundError, LookupError, ValueError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
