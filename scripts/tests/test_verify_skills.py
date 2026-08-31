from __future__ import annotations

import tempfile
import subprocess
import unittest
from pathlib import Path

from scripts.verify_skills import validate_repository


class VerifySkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        skill_dir = self.repo_root / "skills" / "rumo-example"
        (skill_dir / "agents").mkdir(parents=True)
        (self.repo_root / "README.md").write_text(
            "# Catalog\n\nEnglish | [简体中文](README.zh-CN.md)\n\n"
            "- `rumo-example`: example.\n",
            encoding="utf-8",
        )
        (self.repo_root / "README.zh-CN.md").write_text(
            "# 中文清单\n\n[English](README.md) | 简体中文\n\n"
            "- `rumo-example`: 示例。\n",
            encoding="utf-8",
        )
        (self.repo_root / "skills" / "README.md").write_text(
            "# Skills\n\n| Skill | Purpose |\n| --- | --- |\n"
            "| `rumo-example` | Example |\n",
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: rumo-example\n"
            "description: Use when validating a concrete example skill.\n"
            "---\n\n"
            "# Rumo Example\n\n"
            "Read [the reference](reference.md).\n",
            encoding="utf-8",
        )
        (skill_dir / "reference.md").write_text("# Reference\n", encoding="utf-8")
        (skill_dir / "agents" / "openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Rumo Example"\n'
            '  short_description: "验证一个用于测试目录结构和元数据规则的 Rumo 示例技能"\n'
            '  default_prompt: "Use $rumo-example to validate this example."\n',
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def assert_error_contains(self, expected: str) -> None:
        errors = validate_repository(self.repo_root)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_accepts_valid_repository(self) -> None:
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_accepts_folded_description(self) -> None:
        skill_path = self.repo_root / "skills" / "rumo-example" / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").replace(
                "description: Use when validating a concrete example skill.",
                "description: >\n  Use when validating a concrete example skill.",
            ),
            encoding="utf-8",
        )
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_frontmatter_name_mismatch(self) -> None:
        skill_path = self.repo_root / "skills" / "rumo-example" / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").replace(
                "name: rumo-example", "name: rumo-other"
            ),
            encoding="utf-8",
        )
        self.assert_error_contains("does not match")

    def test_rejects_broken_relative_link(self) -> None:
        (self.repo_root / "skills" / "rumo-example" / "reference.md").unlink()
        self.assert_error_contains("broken relative link")

    def test_ignores_broken_links_in_vendored_dependencies(self) -> None:
        dependency_skill = (
            self.repo_root
            / "skills"
            / "rumo-example"
            / "node_modules"
            / "third-party"
            / "SKILL.md"
        )
        dependency_skill.parent.mkdir(parents=True)
        dependency_skill.write_text(
            "# Third-party skill\n\n[missing](missing.md)\n", encoding="utf-8"
        )
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_stale_readme_inventory(self) -> None:
        readme_path = self.repo_root / "skills" / "README.md"
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8")
            + "| `rumo-missing` | Missing |\n",
            encoding="utf-8",
        )
        self.assert_error_contains("lists nonexistent skills")

    def test_rejects_stale_chinese_readme_inventory(self) -> None:
        readme_path = self.repo_root / "README.zh-CN.md"
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8")
            + "- `rumo-missing`: 不存在的技能。\n",
            encoding="utf-8",
        )
        self.assert_error_contains("lists nonexistent skills")

    def test_rejects_invalid_openai_metadata(self) -> None:
        metadata_path = (
            self.repo_root / "skills" / "rumo-example" / "agents" / "openai.yaml"
        )
        metadata_path.write_text(
            metadata_path.read_text(encoding="utf-8").replace(
                "$rumo-example", "$wrong-skill"
            ),
            encoding="utf-8",
        )
        self.assert_error_contains("default_prompt must mention $rumo-example")

    def test_rejects_skill_without_final_newline(self) -> None:
        skill_path = self.repo_root / "skills" / "rumo-example" / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").rstrip("\n"), encoding="utf-8"
        )
        self.assert_error_contains("file must end with a newline")

    def test_rejects_forbidden_project_marker(self) -> None:
        marker = "u" + "sg"
        (self.repo_root / "public-note.md").write_text(
            f"This note must not mention {marker}.\n", encoding="utf-8"
        )
        self.assert_error_contains("forbidden project-specific term")

    def test_rejects_private_key_material(self) -> None:
        private_key_marker = "-----BEGIN " + "PRIVATE KEY-----"
        (self.repo_root / "leaked.txt").write_text(
            f"{private_key_marker}\nredacted\n-----END PRIVATE KEY-----\n",
            encoding="utf-8",
        )
        self.assert_error_contains("possible private key or access token")

    def test_rejects_plaintext_credential_filename(self) -> None:
        (self.repo_root / "credentials.md").write_text("redacted\n", encoding="utf-8")
        self.assert_error_contains("plaintext credential file must not be tracked")

    def test_ignores_ignored_plaintext_credential_filename(self) -> None:
        (self.repo_root / ".gitignore").write_text("credentials.md\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo_root), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(self.repo_root), "add", "."], check=True)
        (self.repo_root / "credentials.md").write_text("local-only\n", encoding="utf-8")

        self.assertEqual(validate_repository(self.repo_root), [])

        subprocess.run(
            ["git", "-C", str(self.repo_root), "add", "-f", "credentials.md"],
            check=True,
        )
        self.assert_error_contains("plaintext credential file must not be tracked")

    def test_rejects_invalid_json_file(self) -> None:
        invalid = self.repo_root / "skills" / "rumo-example" / "settings.json"
        invalid.write_text('{"broken":\n', encoding="utf-8")
        self.assert_error_contains("invalid UTF-8 JSON")


if __name__ == "__main__":
    unittest.main()
