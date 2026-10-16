from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_ROOT = REPO_ROOT / "evals"
SKILL_IN_PATTERN = re.compile(r"\)\?(rumo-[a-z0-9-]+)\"'?$")


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise AssertionError(f"{path}: missing frontmatter")
    fields: dict[str, str] = {}
    for line in lines[1 : lines.index("---", 1)]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


class TriggerEvalsTest(unittest.TestCase):
    """Static checks for the claude plugin eval suite; running it calls a model."""

    def cases(self) -> list[Path]:
        return sorted(path for path in EVALS_ROOT.iterdir() if path.is_dir() and path.name != "results")

    def test_suite_exists(self) -> None:
        self.assertTrue((REPO_ROOT / ".claude-plugin" / "plugin.json").is_file())
        self.assertGreater(len(self.cases()), 0)

    def test_each_case_has_prompt_and_graders(self) -> None:
        for case in self.cases():
            with self.subTest(case=case.name):
                prompt = case / "prompt.md"
                self.assertTrue(prompt.is_file())
                body = prompt.read_text(encoding="utf-8").split("\n---\n", 1)[1]
                self.assertTrue(body.strip(), "prompt body is empty")
                self.assertTrue(list((case / "graders").glob("*.md")), "no graders")

    def test_graders_name_existing_default_skills(self) -> None:
        for grader in sorted(EVALS_ROOT.glob("*/graders/*.md")):
            with self.subTest(grader=f"{grader.parent.parent.name}/{grader.name}"):
                fields = frontmatter(grader)
                self.assertEqual(fields.get("type"), "tool_used")
                self.assertEqual(fields.get("tool"), "Skill")
                match = SKILL_IN_PATTERN.search(fields.get("input_match", ""))
                if match:
                    self.assertTrue((REPO_ROOT / "skills" / match.group(1) / "SKILL.md").is_file())
                else:
                    self.assertEqual(grader.name, "uses-no-rumo-skill.md")
                if grader.name.startswith(("skips-", "uses-no-")):
                    self.assertEqual((fields.get("min"), fields.get("max")), ("0", "0"))


if __name__ == "__main__":
    unittest.main()
