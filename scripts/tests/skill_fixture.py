"""Build a minimal skills repository for installer tests."""

from __future__ import annotations

from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parents[2]
CORE_SKILLS = ("rumo-alpha", "rumo-beta")
EXTRA_SKILLS = ("rumo-delta", "rumo-gamma")


def write_skill(skill_dir: Path, description: str) -> None:
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {skill_dir.name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"# {skill_dir.name}\n",
        encoding="utf-8",
    )


def build_fixture_repo(root: Path) -> Path:
    """Create a valid repository with two default skills and two extras."""
    repo = root / "fixture-repo"
    (repo / "scripts").mkdir(parents=True)
    for name in ("install.ps1", "install.sh"):
        shutil.copy2(REPO_ROOT / name, repo / name)
    shutil.copy2(REPO_ROOT / "scripts" / "verify_skills.py", repo / "scripts")

    for name in CORE_SKILLS:
        write_skill(repo / "skills" / name, f"Use when testing default skill {name}.")
    for name in EXTRA_SKILLS:
        write_skill(repo / "extras" / name, f"Use when testing optional skill {name}.")

    core = "".join(f"- `{name}`: fixture.\n" for name in CORE_SKILLS)
    extras = "".join(f"- `{name}`: fixture.\n" for name in EXTRA_SKILLS)
    for readme in (repo / "README.md", repo / "README.en.md", repo / "skills" / "README.md"):
        readme.write_text(f"# Fixture\n\n{core}\n## Extras\n\n{extras}", encoding="utf-8")
    return repo


def promote_extra(repo: Path, name: str) -> None:
    """Move one fixture extra into the default catalog, leaving old links dangling."""
    source = (repo / "extras" / name).resolve()
    target = (repo / "skills" / name).resolve()
    assert source.is_relative_to(repo.resolve()) and target.is_relative_to(repo.resolve())
    assert not target.exists()
    source.rename(target)
    row = f"- `{name}`: fixture.\n"
    for readme in (repo / "README.md", repo / "README.en.md", repo / "skills" / "README.md"):
        core, separator, extras = readme.read_text(encoding="utf-8").partition("## Extras\n")
        assert separator and row in extras
        readme.write_bytes((core + row + "\n" + separator + extras.replace(row, "")).encode("utf-8"))
