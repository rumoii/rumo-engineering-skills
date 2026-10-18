#!/usr/bin/env python3
"""Validate the shared Rumo skill catalog without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
README_SKILL_RE = re.compile(r"^[-|]\s*`(rumo-[a-z0-9-]+)`(?:\s*\||:)", re.MULTILINE)
OPENAI_STRING_RE = re.compile(
    r'^  (display_name|short_description|default_prompt):\s*("(?:[^"\\]|\\.)*")\s*$',
    re.MULTILINE,
)
OPENAI_MANUAL_ONLY_RE = re.compile(
    r"^policy:\n(?:  .*\n)*?  allow_implicit_invocation:\s*false\s*$", re.MULTILINE
)
MARKDOWN_EXCLUDED_DIRS = {"node_modules"}
SKILL_ROOTS = ("skills", "extras")
EXTRAS_HEADINGS = {"extras", "optional extras", "可选扩展"}
H2_RE = re.compile(r"^## +(.+?)\s*$", re.MULTILINE)
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_DEFAULT_SKILL_LINES = 150
FORBIDDEN_TERMS_ENV = "RUMO_FORBIDDEN_TERMS_FILE"
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


def default_forbidden_terms_file() -> Path:
    """Return the per-user private forbidden-terms file location."""
    return Path.home() / ".rumo-engineering-skills" / "forbidden-terms.txt"


def load_forbidden_terms(errors: list[str]) -> list[re.Pattern[str]]:
    """Load private terms that must not appear in this public repository.

    Each non-empty line not starting with ``#`` is a case-insensitive literal,
    or a regular expression when prefixed with ``re:``. A missing default file
    disables the check; a missing explicitly configured file is an error.
    """
    configured = os.environ.get(FORBIDDEN_TERMS_ENV)
    path = Path(configured).expanduser() if configured else default_forbidden_terms_file()
    if not path.is_file():
        if configured:
            errors.append(f"{FORBIDDEN_TERMS_ENV} points to a missing file: {path}")
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{path}: cannot read forbidden terms: {exc}")
        return []

    patterns: list[re.Pattern[str]] = []
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("re:"):
            try:
                patterns.append(re.compile(line[3:]))
            except re.error as exc:
                errors.append(f"{path}:{line_number}: invalid regular expression: {exc}")
        else:
            patterns.append(re.compile(re.escape(line), re.IGNORECASE))
    return patterns


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


def plain_scalar_problem(value: str) -> str:
    """Return why an unquoted value is not a valid YAML plain scalar, or an empty string."""
    if not value:
        return ""
    if value[0] in "-?:" and (len(value) == 1 or value[1].isspace()):
        return f"starts with the YAML indicator {value[0]!r}"
    if value[0] in ",[]{}#&*!|>'\"%@`":
        return f"starts with the YAML indicator {value[0]!r}"
    if ": " in value or value.endswith(":"):
        return "contains ': ', which YAML reads as a nested mapping"
    if " #" in value:
        return "contains ' #', which YAML reads as a comment"
    return ""


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
        else:
            problem = plain_scalar_problem(raw_value)
            if problem:
                errors.append(f"{path}:{index + 1}: unquoted {key} {problem}; quote the value or reword it")
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
            elif _is_within(path, repo_root / "skills") and _is_within(
                resolved, repo_root / "extras"
            ):
                errors.append(
                    f"{path}: default skills must not link to optional extras: {target}"
                )


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


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
    path: Path, core_names: set[str], extra_names: set[str], errors: list[str]
) -> None:
    """Require a README inventory to list every skill once, in the right group.

    Skills listed under an Extras heading must be optional extras; every other
    listed skill must be a default skill.
    """
    text = read_text(path, errors)
    if text is None:
        return
    documented_core: set[str] = set()
    documented_extras: set[str] = set()
    headings = list(H2_RE.finditer(text))
    starts = [0, *(match.start() for match in headings)]
    titles = ["", *(match.group(1) for match in headings)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(text)
        names = set(README_SKILL_RE.findall(text[start:end]))
        if titles[index].strip().lower() in EXTRAS_HEADINGS:
            documented_extras |= names
        else:
            documented_core |= names
    skill_names = core_names | extra_names
    documented = documented_core | documented_extras
    missing = sorted(skill_names - documented)
    stale = sorted(documented - skill_names)
    core_as_extra = sorted(documented_extras & core_names)
    extra_as_core = sorted(documented_core & extra_names)
    if missing:
        errors.append(f"{path}: missing skills: {', '.join(missing)}")
    if stale:
        errors.append(f"{path}: lists nonexistent skills: {', '.join(stale)}")
    if core_as_extra:
        errors.append(f"{path}: lists default skills under Extras: {', '.join(core_as_extra)}")
    if extra_as_core:
        errors.append(
            f"{path}: lists optional skills outside the Extras section: {', '.join(extra_as_core)}"
        )


def validate_repository(
    repo_root: Path, forbidden_terms: list[re.Pattern[str]] | None = None
) -> list[str]:
    """Return every validation error found in one Rumo skills repository."""
    errors: list[str] = []
    forbidden_terms = forbidden_terms or []
    skills_root = repo_root / "skills"
    if not skills_root.is_dir():
        return [f"{skills_root}: skills directory not found"]

    skill_dirs = list_skill_dirs(repo_root)
    if not any(path.parent == skills_root for path in skill_dirs):
        return [f"{skills_root}: no skill directories found"]

    skill_names: set[str] = set()
    for skill_dir in skill_dirs:
        if skill_dir.name in skill_names:
            errors.append(f"{skill_dir}: skill name is defined in both skills/ and extras/")
        skill_names.add(skill_dir.name)
    core_names = {path.name for path in skill_dirs if path.parent == skills_root}
    extra_names = skill_names - core_names
    candidate_files, tracked_files = repository_files(repo_root)
    for skill_dir in skill_dirs:
        skill_name = skill_dir.name
        if not SKILL_NAME_RE.fullmatch(skill_name):
            errors.append(f"{skill_dir}: directory name must use lowercase hyphen-case")
        if not skill_name.startswith("rumo-"):
            errors.append(f"{skill_dir}: shared skill names must use the rumo- namespace")
        for license_path in sorted(skill_dir.rglob("LICENSE*")):
            if "node_modules" not in license_path.parts:
                errors.append(
                    f"{license_path}: skills are covered by the repository license; "
                    "do not ship separate license files"
                )

        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            errors.append(f"{skill_path}: required file not found")
            continue

        text = read_text(skill_path, errors)
        if text is None:
            continue
        if "[TODO" in text or "TODO:" in text:
            errors.append(f"{skill_path}: unresolved template marker")
        line_count = len(text.splitlines())
        if skill_dir.parent.name == "skills" and line_count > MAX_DEFAULT_SKILL_LINES:
            errors.append(
                f"{skill_path}: default skill has {line_count} lines; keep it within "
                f"{MAX_DEFAULT_SKILL_LINES} and move detail into references/"
            )

        frontmatter = parse_frontmatter(skill_path, text, errors)
        declared_name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if declared_name != skill_name:
            errors.append(
                f"{skill_path}: frontmatter name {declared_name!r} does not match {skill_name!r}"
            )
        if not description or description.startswith("["):
            errors.append(f"{skill_path}: description must be a concrete activation hint")
        if len(declared_name) > MAX_NAME_LENGTH:
            errors.append(f"{skill_path}: name must contain at most {MAX_NAME_LENGTH} characters")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            errors.append(
                f"{skill_path}: description must contain at most {MAX_DESCRIPTION_LENGTH} characters"
            )

        manual_in_frontmatter = frontmatter.get("disable-model-invocation", "").lower() == "true"
        manual_in_metadata = False
        metadata_path = skill_dir / "agents" / "openai.yaml"
        if metadata_path.exists():
            metadata_text = read_text(metadata_path, errors)
            if metadata_text is not None:
                if "[TODO" in metadata_text or "TODO:" in metadata_text:
                    errors.append(f"{metadata_path}: unresolved template marker")
                validate_openai_metadata(metadata_path, metadata_text, skill_name, errors)
                manual_in_metadata = bool(OPENAI_MANUAL_ONLY_RE.search(metadata_text))
        if manual_in_frontmatter != manual_in_metadata:
            errors.append(
                f"{skill_path}: manual-only invocation must be set in both SKILL.md "
                "(disable-model-invocation: true) and agents/openai.yaml "
                "(policy.allow_implicit_invocation: false)"
            )

    readme_paths = (
        repo_root / "README.md",
        repo_root / "README.en.md",
        skills_root / "README.md",
    )
    for readme_path in readme_paths:
        if not readme_path.is_file():
            errors.append(f"{readme_path}: required catalog inventory not found")
        else:
            validate_readme_inventory(readme_path, core_names, extra_names, errors)

    markdown_files = sorted(
        {path for path in readme_paths if path.is_file()} | set(repo_root.glob("*.md"))
    )
    for root_name in SKILL_ROOTS:
        if (repo_root / root_name).is_dir():
            markdown_files.extend(iter_skill_markdown(repo_root / root_name))
    validate_markdown_links(repo_root, markdown_files, errors)

    validate_json_files(candidate_files, errors)

    for path in candidate_files:
        if not path.is_file() or ".git" in path.parts or "node_modules" in path.parts:
            continue
        relative = path.relative_to(repo_root).as_posix().lower()
        if path.name.lower() in FORBIDDEN_TRACKED_NAMES and relative in tracked_files:
            errors.append(f"{path}: plaintext credential file must not be tracked")
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        if any(pattern.search(text) for pattern in forbidden_terms):
            errors.append(f"{path}: matched a private forbidden term")
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path}: contains a possible private key or access token")
                break
    return list(dict.fromkeys(errors))


def list_skill_dirs(repo_root: Path) -> list[Path]:
    """Return default skill directories followed by optional extras."""
    skill_dirs: list[Path] = []
    for root_name in SKILL_ROOTS:
        root = repo_root / root_name
        if root.is_dir():
            skill_dirs.extend(sorted(path for path in root.iterdir() if path.is_dir()))
    return skill_dirs


def repository_files(repo_root: Path) -> tuple[list[Path], set[str]]:
    """Return tracked and non-ignored files, plus normalized tracked paths."""
    try:
        tracked = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
        candidates = subprocess.run(
            [
                "git",
                "-C",
                str(repo_root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            capture_output=True,
            check=False,
        )
    except OSError:
        tracked = candidates = None
    if (
        tracked is not None
        and candidates is not None
        and tracked.returncode == 0
        and candidates.returncode == 0
    ):
        tracked_paths = {
            os.fsdecode(value).replace("\\", "/").lower()
            for value in tracked.stdout.split(b"\0")
            if value
        }
        candidate_paths = [
            repo_root / os.fsdecode(value)
            for value in candidates.stdout.split(b"\0")
            if value
        ]
        return sorted(candidate_paths), tracked_paths

    fallback = [path for path in sorted(repo_root.rglob("*")) if path.is_file()]
    return fallback, {
        path.relative_to(repo_root).as_posix().lower() for path in fallback
    }


def validate_json_files(candidate_files: list[Path], errors: list[str]) -> None:
    """Validate repository-owned JSON files, including profile templates."""
    for path in sorted(path for path in candidate_files if path.suffix.lower() == ".json"):
        if ".git" in path.parts or "node_modules" in path.parts:
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: invalid UTF-8 JSON: {exc}")


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
    errors: list[str] = []
    forbidden_terms = load_forbidden_terms(errors)
    errors.extend(validate_repository(repo_root, forbidden_terms))
    if errors:
        print(f"Rumo skill validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    skill_dirs = list_skill_dirs(repo_root)
    extra_count = sum(1 for path in skill_dirs if path.parent.name == "extras")
    print(
        f"Rumo skill validation passed: {len(skill_dirs) - extra_count} skills, "
        f"{extra_count} extras"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
