#!/usr/bin/env python3
"""Validate a repository's docs/decisions lifecycle tree."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


LIFECYCLES = {"proposed", "implemented", "rejected"}
FILE_NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
PERSONAL_PATH_RE = re.compile(r"(?:/Users/[^/\s]+|[A-Za-z]:\\Users\\[^\\\s]+)")
REQUIRED_SECTIONS = {
    "proposed": (
        "Problem",
        "Proposal",
        "Alternatives considered",
        "Risks",
        "Verification",
        "Rollback",
    ),
    "implemented": (
        "Problem",
        "Decision",
        "Alternatives considered",
        "Consequences",
        "Verification",
        "Rollback",
    ),
    "rejected": (
        "Problem",
        "Proposal",
        "Alternatives considered",
        "Risks",
        "Verification",
        "Rollback",
    ),
}
FORBIDDEN_SECTIONS = {
    "proposed": {"Decision", "Consequences"},
    "implemented": {"Proposal", "Risks"},
    "rejected": {"Decision", "Consequences"},
}


def display_path(path: Path, repo_root: Path) -> str:
    """Return a stable repository-relative path when possible."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_text(path: Path, repo_root: Path, errors: list[str]) -> str | None:
    """Read one UTF-8 file and validate its line formatting."""
    label = display_path(path, repo_root)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{label}: cannot read UTF-8 text: {exc}")
        return None

    if not text.endswith("\n"):
        errors.append(f"{label}: file must end with a newline")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line != line.rstrip():
            errors.append(f"{label}:{line_number}: trailing whitespace")
    return text


def section_positions(lines: list[str]) -> dict[str, int]:
    """Return second-level heading positions."""
    positions: dict[str, int] = {}
    for index, line in enumerate(lines):
        if line.startswith("## "):
            positions[line[3:].strip()] = index
    return positions


def section_has_content(lines: list[str], start: int) -> bool:
    """Return whether a section contains non-heading content."""
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            return False
        if line.strip() and not line.lstrip().startswith("<!--"):
            return True
    return False


def validate_links(path: Path, text: str, repo_root: Path, errors: list[str]) -> None:
    """Validate relative Markdown links without checking URL fragments."""
    label = display_path(path, repo_root)
    for raw_target in LINK_RE.findall(text):
        target = raw_target.strip().split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
            continue
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError:
            errors.append(f"{label}: relative link escapes the repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{label}: broken relative link: {target}")


def validate_decision(path: Path, lifecycle: str, repo_root: Path, errors: list[str]) -> None:
    """Validate one lifecycle-owned decision record."""
    label = display_path(path, repo_root)
    if not FILE_NAME_RE.fullmatch(path.name):
        errors.append(f"{label}: filename must be yyyy-mm-dd-lowercase-topic.md")

    text = read_text(path, repo_root, errors)
    if text is None:
        return
    lines = text.splitlines()
    if len(lines) < 4:
        errors.append(f"{label}: decision record is incomplete")
        return

    if not lines[0].startswith("# Decision: ") or not lines[0][12:].strip():
        errors.append(f"{label}: first line must be '# Decision: <title>'")
    if lines[1] != "":
        errors.append(f"{label}: title must be followed by one blank line")

    status_line = lines[2]
    if lifecycle == "rejected":
        if not re.fullmatch(r"Status: rejected - \S.*", status_line):
            errors.append(f"{label}: rejected status must include a one-line reason")
    elif status_line != f"Status: {lifecycle}":
        errors.append(f"{label}: status must match the {lifecycle} directory")
    if lines[3] != "":
        errors.append(f"{label}: status must be followed by one blank line")

    positions = section_positions(lines)
    required = REQUIRED_SECTIONS[lifecycle]
    missing = [section for section in required if section not in positions]
    if missing:
        errors.append(f"{label}: missing sections: {', '.join(missing)}")
    else:
        ordered_positions = [positions[section] for section in required]
        if ordered_positions != sorted(ordered_positions):
            errors.append(f"{label}: required sections are out of order")
        for section in required:
            if not section_has_content(lines, positions[section]):
                errors.append(f"{label}: section '{section}' must contain content")

    forbidden = sorted(FORBIDDEN_SECTIONS[lifecycle] & positions.keys())
    if forbidden:
        errors.append(f"{label}: sections do not match {lifecycle}: {', '.join(forbidden)}")

    if "[TODO" in text or "TODO:" in text:
        errors.append(f"{label}: unresolved template marker")
    if PERSONAL_PATH_RE.search(text):
        errors.append(f"{label}: personal absolute path is not allowed")
    validate_links(path, text, repo_root, errors)


def validate_repository(repo_root: Path) -> list[str]:
    """Return all decision-tree validation errors for one repository."""
    repo_root = repo_root.resolve()
    decisions_root = repo_root / "docs" / "decisions"
    errors: list[str] = []
    readme_path = decisions_root / "README.md"
    if not decisions_root.is_dir():
        return ["docs/decisions: decision directory not found"]
    if not readme_path.is_file():
        errors.append("docs/decisions/README.md: required rules file not found")
    else:
        read_text(readme_path, repo_root, errors)

    for child in sorted(decisions_root.iterdir()):
        if child.name == "README.md":
            continue
        if not child.is_dir() or child.name not in LIFECYCLES:
            errors.append(
                f"{display_path(child, repo_root)}: only proposed, implemented, and rejected directories are allowed"
            )

    seen_names: dict[str, Path] = {}
    for lifecycle in sorted(LIFECYCLES):
        lifecycle_dir = decisions_root / lifecycle
        if not lifecycle_dir.exists():
            continue
        for path in sorted(lifecycle_dir.iterdir()):
            if not path.is_file() or path.suffix != ".md":
                errors.append(f"{display_path(path, repo_root)}: only Markdown decision files are allowed")
                continue
            previous = seen_names.get(path.name)
            if previous is not None:
                errors.append(
                    f"{display_path(path, repo_root)}: duplicate lifecycle record also exists at "
                    f"{display_path(previous, repo_root)}"
                )
            else:
                seen_names[path.name] = path
            validate_decision(path, lifecycle, repo_root, errors)

    if not seen_names:
        errors.append("docs/decisions: at least one decision record is required")
    return list(dict.fromkeys(errors))


def main() -> int:
    """Run decision validation and print a concise result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root")
    args = parser.parse_args()
    repo_root = args.root.expanduser().resolve()
    errors = validate_repository(repo_root)
    if errors:
        print(f"Decision validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    count = sum(1 for path in (repo_root / "docs" / "decisions").glob("*/*.md"))
    print(f"Decision validation passed: {count} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
