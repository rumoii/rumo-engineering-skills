#!/usr/bin/env python3
"""Validate the shared Rumo skill catalog without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
README_SKILL_RE = re.compile(r"^[-|]\s*`(rumo-[a-z0-9-]+)`(?:\s*\||:)", re.MULTILINE)
OPENAI_STRING_RE = re.compile(
    r'^  (display_name|short_description|default_prompt):\s*("(?:[^"\\]|\\.)*")\s*$',
    re.MULTILINE,
)
MARKDOWN_EXCLUDED_DIRS = {"node_modules"}
FORMER_BRAND = bytes((117, 115, 103)).decode("ascii")
FORMER_PROJECT_MARKERS = (
    FORMER_BRAND,
    bytes((106, 115, 122, 99)).decode("ascii"),
    bytes((106, 115, 106, 100)).decode("ascii"),
    "技" + "术监督",
    "g" + "pdata",
)
FORBIDDEN_PROJECT_PATTERNS = (re.compile(r"\b10\.12\.\d{1,3}\.\d{1,3}\b"),)
FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:ghp|github_pat|glpat|sk)-[A-Za-z0-9_-]{20,}\b"),
)
FORBIDDEN_TRACKED_NAMES = {
    ".env",
    "credentials.env",
    "credentials.md",
    "id_ed25519",
    "id_rsa",
    "pwd.md",
    "secrets.env",
    "secrets.md",
}


def read_text(path: Path, errors: list[str]) -> str | None:
    """Read one UTF-8 text file and record file-level formatting errors."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read UTF-8 text: {exc}")
        return None

    if not text.endswith("\n"):
        errors.append(f"{path}: file must end with a newline")
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line != line.rstrip():
            errors.append(f"{path}:{line_number}: trailing whitespace")
    return text


def parse_frontmatter(path: Path, text: str, errors: list[str]) -> dict[str, str]:
    """Parse the scalar fields used by repository skill frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"{path}: SKILL.md must start with YAML frontmatter")
        return {}

    try:
        closing_index = lines.index("---", 1)
    except ValueError:
        errors.append(f"{path}: frontmatter is missing its closing delimiter")
        return {}

    fields: dict[str, str] = {}
    index = 1
    while index < closing_index:
        line = lines[index]
        match = re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*):(?:\s*(.*))?$", line)
        if not match:
            errors.append(f"{path}:{index + 1}: unsupported frontmatter syntax")
            index += 1
            continue

        key, raw_value = match.group(1), (match.group(2) or "").strip()
        if raw_value in {">", "|", ">-", "|-"}:
            block: list[str] = []
            index += 1
            while index < closing_index and (
                not lines[index] or lines[index][0].isspace()
            ):
                block.append(lines[index].strip())
                index += 1
            fields[key] = " ".join(part for part in block if part)
            continue

        if len(raw_value) >= 2 and raw_value[0] == raw_value[-1] and raw_value[0] in "\"'":
            raw_value = raw_value[1:-1]
        fields[key] = raw_value
        index += 1

    if closing_index + 1 >= len(lines) or lines[closing_index + 1] != "":
        errors.append(f"{path}: add one blank line after frontmatter")
    return fields


def validate_openai_metadata(
    path: Path, text: str, skill_name: str, errors: list[str]
) -> None:
    """Validate the repository's supported OpenAI interface metadata."""
    if not text.startswith("interface:\n"):
        errors.append(f"{path}: expected an interface mapping")

    values: dict[str, str] = {}
    for key, encoded_value in OPENAI_STRING_RE.findall(text):
        try:
            values[key] = json.loads(encoded_value)
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid quoted value for {key}: {exc}")

    required = {"display_name", "short_description", "default_prompt"}
    missing = sorted(required - values.keys())
    if missing:
        errors.append(f"{path}: missing quoted interface fields: {', '.join(missing)}")
        return

    display_name = values["display_name"]
    if not display_name.isascii() or not re.search(r"[A-Za-z]", display_name):
        errors.append(f"{path}: display_name must be English ASCII text")

    short_description = values["short_description"]
    if not 25 <= len(short_description) <= 64:
        errors.append(f"{path}: short_description must contain 25-64 characters")
    if not re.search(r"[\u3400-\u9fff]", short_description):
        errors.append(f"{path}: short_description must contain Chinese text")

    if f"${skill_name}" not in values["default_prompt"]:
        errors.append(f"{path}: default_prompt must mention ${skill_name}")


def validate_markdown_links(repo_root: Path, markdown_files: list[Path], errors: list[str]) -> None:
    """Check relative links in repository Markdown files."""
    for path in markdown_files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for target in MARKDOWN_LINK_RE.findall(text):
            target = target.strip().split("#", 1)[0]
            if not target or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE):
                continue
            if target.startswith("/") or "<" in target or ">" in target:
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(repo_root.resolve())
            except ValueError:
                errors.append(f"{path}: relative link escapes the repository: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path}: broken relative link: {target}")


def iter_skill_markdown(skills_root: Path) -> list[Path]:
    """Return owned skill Markdown while excluding vendored dependency trees."""
    return sorted(
        path
        for path in skills_root.glob("**/*.md")
        if not any(
            part in MARKDOWN_EXCLUDED_DIRS
            for part in path.relative_to(skills_root).parts
        )
    )


def validate_readme_inventory(
    path: Path, skill_names: set[str], errors: list[str]
) -> None:
    """Require a README inventory to contain every and only catalog skill."""
    text = read_text(path, errors)
    if text is None:
        return
    documented = set(README_SKILL_RE.findall(text))
    missing = sorted(skill_names - documented)
    stale = sorted(documented - skill_names)
    if missing:
        errors.append(f"{path}: missing skills: {', '.join(missing)}")
    if stale:
        errors.append(f"{path}: lists nonexistent skills: {', '.join(stale)}")


def validate_repository(repo_root: Path) -> list[str]:
    """Return every validation error found in one Rumo skills repository."""
    errors: list[str] = []
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return [f"{skills_root}: skills directory not found"]

    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not skill_dirs:
        return [f"{skills_root}: no skill directories found"]

    skill_names = {path.name for path in skill_dirs}
    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        if not SKILL_NAME_RE.fullmatch(skill_name):
            errors.append(f"{skill_dir}: directory name must use lowercase hyphen-case")
        if not skill_name.startswith("rumo-"):
            errors.append(f"{skill_dir}: shared skill names must use the rumo- namespace")

        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"{skill_path}: required file not found")
            continue

        text = read_text(skill_path, errors)
        if text is None:
            continue
        if "[TODO" in text or "TODO:" in text:
            errors.append(f"{skill_path}: unresolved template marker")

        frontmatter = parse_frontmatter(skill_path, text, errors)
        declared_name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if declared_name != skill_name:
            errors.append(
                f"{skill_path}: frontmatter name {declared_name!r} does not match {skill_name!r}"
            )
        if not description or description.startswith("["):
            errors.append(f"{skill_path}: description must be a concrete activation hint")

        metadata_path = skill_dir / "agents" / "openai.yaml"
        if metadata_path.exists():
            metadata_text = read_text(metadata_path, errors)
            if metadata_text is not None:
                if "[TODO" in metadata_text or "TODO:" in metadata_text:
                    errors.append(f"{metadata_path}: unresolved template marker")
                validate_openai_metadata(metadata_path, metadata_text, skill_name, errors)

    for readme_path in (repo_root / "README.md", skills_root / "README.md"):
        if not readme_path.is_file():
            errors.append(f"{readme_path}: required catalog inventory not found")
        else:
            validate_readme_inventory(readme_path, skill_names, errors)

    markdown_files = sorted(
        path
        for path in (repo_root / "README.md", skills_root / "README.md")
        if path.is_file()
    )
    markdown_files.extend(iter_skill_markdown(skills_root))
    validate_markdown_links(repo_root, markdown_files, errors)

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts:
            continue
        if path.name.lower() in FORBIDDEN_TRACKED_NAMES:
            errors.append(f"{path}: plaintext credential file must not be tracked")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        lowered_text = text.lower()
        for marker in FORMER_PROJECT_MARKERS:
            if marker.lower() in lowered_text:
                errors.append(f"{path}: contains a forbidden project-specific term")
                break
        for pattern in FORBIDDEN_PROJECT_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: contains a forbidden internal network address")
                break
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: contains a possible private key or access token")
                break
    return list(dict.fromkeys(errors))


def main() -> int:
    """Run repository validation and print a concise result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="rumo-engineering-skills repository root",
    )
    args = parser.parse_args()
    repo_root = args.repo_root.expanduser().resolve()
    errors = validate_repository(repo_root)
    if errors:
        print(f"Rumo skill validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    skill_count = sum(1 for path in (repo_root / "skills").iterdir() if path.is_dir())
    print(f"Rumo skill validation passed: {skill_count} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
