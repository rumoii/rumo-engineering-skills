"""Parse repository YAML with a real parser; the validator only checks a subset of YAML rules."""

from __future__ import annotations

import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # CI installs PyYAML; local runs without it skip explicitly.
    yaml = None


REPO_ROOT = Path(__file__).resolve().parents[2]


def frontmatter(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{path}: missing frontmatter")
    return "\n".join(lines[1 : lines.index("---", 1)])


@unittest.skipIf(yaml is None, "PyYAML is not installed")
class YamlParsingTest(unittest.TestCase):
    def test_skill_frontmatter_parses_with_name_and_description(self) -> None:
        paths = sorted(REPO_ROOT.glob("skills/*/SKILL.md")) + sorted(REPO_ROOT.glob("extras/*/SKILL.md"))
        self.assertGreater(len(paths), 0)
        for path in paths:
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                data = yaml.safe_load(frontmatter(path))
                self.assertIsInstance(data, dict)
                self.assertEqual(data.get("name"), path.parent.name)
                self.assertIsInstance(data.get("description"), str)

    def test_eval_frontmatter_parses(self) -> None:
        paths = sorted(REPO_ROOT.glob("evals/**/*.md"))
        self.assertGreater(len(paths), 0)
        for path in paths:
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                self.assertIsInstance(yaml.safe_load(frontmatter(path)), dict)

    def test_openai_metadata_parses(self) -> None:
        paths = sorted(REPO_ROOT.glob("skills/*/agents/openai.yaml")) + sorted(REPO_ROOT.glob("extras/*/agents/openai.yaml"))
        self.assertGreater(len(paths), 0)
        for path in paths:
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
                self.assertIsInstance(data.get("interface"), dict)


if __name__ == "__main__":
    unittest.main()
