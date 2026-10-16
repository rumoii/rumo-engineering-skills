from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.verify_skills import parse_frontmatter


REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARIES = (
    (
        "rumo-review",
        "rumo-verify",
        r"(?:pre-handoff|before handoff).*checks|checks.*(?:handoff|ready)",
        r"code review|review",
    ),
    (
        "rumo-plan",
        "rumo-clarify",
        r"unclear.*(?:goal|requirement)|(?:goal|requirement).*unclear",
        r"spec|task breakdown|plan",
    ),
    (
        "rumo-test",
        "rumo-verify",
        r"(?:exact|finished).*(?:change|diff)|(?:checks|commands).*actually run",
        r"(?:test|evidence).*planning|planning.*(?:test|evidence)",
    ),
    (
        "rumo-remote-ops",
        "rumo-database-change-safety",
        r"database.*writes?",
        r"(?:remote|SSH|host).*(?:change|query)",
    ),
    (
        "rumo-debug",
        "rumo-database-change-safety",
        r"(?:write-capable|persistent).*database|database.*writes?",
        r"read-only.*(?:diagnosis|investigation)",
    ),
    (
        "rumo-filesystem-safety",
        "rumo-database-change-safety",
        r"database.*(?:cleanup|data)",
        r"(?:files?|directories).*(?:delet|clean)",
    ),
)


def read_description(path: Path) -> str:
    errors: list[str] = []
    fields = parse_frontmatter(path, path.read_text(encoding="utf-8"), errors)
    if errors:
        raise AssertionError("; ".join(errors))
    description = fields.get("description", "")
    if not description:
        raise AssertionError(f"{path}: missing frontmatter description")
    return description


def has_boundary(description: str, counterpart: str, scene_pattern: str) -> bool:
    if re.search(rf"(?<![\w-]){re.escape(counterpart)}(?![\w-])", description):
        return True
    for sentence in re.split(r"[.!?]\s*", description):
        if re.search(r"\bdo not (?:use|trigger|invoke)\b|\buse\b.+\binstead\b", sentence, re.I):
            if re.search(scene_pattern, sentence, re.I):
                return True
    return False


class SkillBoundariesTest(unittest.TestCase):
    def test_descriptions_state_pair_boundaries(self) -> None:
        for first, second, first_scene, second_scene in BOUNDARIES:
            with self.subTest(pair=f"{first} <-> {second}"):
                first_description = read_description(REPO_ROOT / "skills" / first / "SKILL.md")
                second_description = read_description(REPO_ROOT / "skills" / second / "SKILL.md")
                self.assertTrue(
                    has_boundary(first_description, second, first_scene)
                    or has_boundary(second_description, first, second_scene),
                    f"{first} <-> {second}: descriptions lack a pair-specific exclusion "
                    "or redirect (Do not use / Use ... instead), or an explicit "
                    "reference to the counterpart skill; add the confirmed boundary "
                    "to at least one frontmatter description.",
                )

    def test_accepts_counterpart_or_pair_specific_exclusion(self) -> None:
        self.assertTrue(has_boundary("Use rumo-verify instead.", "rumo-verify", "unused"))
        self.assertTrue(has_boundary("Do not use to run pre-handoff checks.", "rumo-verify", BOUNDARIES[0][2]))
        self.assertTrue(has_boundary("Use exact diff verification instead.", "rumo-verify", BOUNDARIES[2][2]))

    def test_rejects_missing_boundary_or_unrelated_exclusion(self) -> None:
        for description in (
            "Use for ordinary code reviews.",
            "Do not use for deleting files. Supports pre-handoff checks.",
        ):
            with self.subTest(description=description):
                self.assertFalse(has_boundary(description, "rumo-verify", BOUNDARIES[0][2]))


if __name__ == "__main__":
    unittest.main()
