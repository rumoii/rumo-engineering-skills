from __future__ import annotations

import os
import tempfile
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from scripts.verify_skills import (
    FORBIDDEN_TERMS_ENV,
    load_forbidden_terms,
    validate_repository,
)


class VerifySkillsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        skill_dir = self.repo_root / "skills" / "rumo-example"
        (skill_dir / "agents").mkdir(parents=True)
        (self.repo_root / "README.md").write_text(
            "# 中文清单\n\n简体中文 | [English](README.en.md)\n\n"
            "- `rumo-example`: 示例。\n",
            encoding="utf-8",
        )
        (self.repo_root / "README.en.md").write_text(
            "# Catalog\n\n[简体中文](README.md) | English\n\n"
            "- `rumo-example`: example.\n",
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

    def replace_description(self, description: str) -> None:
        skill_path = self.repo_root / "skills" / "rumo-example" / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").replace(
                "description: Use when validating a concrete example skill.",
                f"description: {description}",
            ),
            encoding="utf-8",
        )

    def test_rejects_unquoted_values_that_are_not_yaml_plain_scalars(self) -> None:
        cases = {
            "Use when testing: a colon followed by a space.": "contains ': '",
            "Use when testing #comments after a space.": "contains ' #'",
            "[Use] when testing a leading bracket.": "starts with the YAML indicator '['",
            "- Use when testing a leading dash.": "starts with the YAML indicator '-'",
        }
        for description, expected in cases.items():
            with self.subTest(description=description):
                self.tearDown()
                self.setUp()
                self.replace_description(description)
                self.assert_error_contains(expected)

    def test_accepts_quoted_value_and_plain_colon_without_space(self) -> None:
        for description in (
            '"Use when testing: a quoted colon."',
            "Use when testing a ratio like 3:1 or a URL like https://example.com.",
        ):
            with self.subTest(description=description):
                self.tearDown()
                self.setUp()
                self.replace_description(description)
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

    def test_rejects_broken_link_in_root_document(self) -> None:
        (self.repo_root / "CONTRIBUTING.md").write_text(
            "# Contributing\n\nSee [the guide](missing.md).\n", encoding="utf-8"
        )
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
        readme_path = self.repo_root / "README.md"
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

    def write_terms(self, content: str) -> Path:
        terms_path = Path(self.temp_dir.name).parent / f"{self.repo_root.name}-terms.txt"
        terms_path.write_text(content, encoding="utf-8")
        self.addCleanup(terms_path.unlink)
        return terms_path

    def test_rejects_private_forbidden_term_without_echoing_it(self) -> None:
        (self.repo_root / "public-note.md").write_text(
            "Deployed by AcmeCorp to host 192.0.2.17.\n", encoding="utf-8"
        )
        terms_path = self.write_terms("# private\nacmecorp\n")
        with mock.patch.dict(os.environ, {FORBIDDEN_TERMS_ENV: str(terms_path)}):
            load_errors: list[str] = []
            terms = load_forbidden_terms(load_errors)
        self.assertEqual(load_errors, [])

        errors = validate_repository(self.repo_root, terms)

        self.assertTrue(any("matched a private forbidden term" in e for e in errors), errors)
        self.assertFalse(any("acmecorp" in e.lower() for e in errors), errors)

    def test_forbidden_regex_terms(self) -> None:
        (self.repo_root / "public-note.md").write_text(
            "Host 192.0.2.17 is internal.\n", encoding="utf-8"
        )
        terms_path = self.write_terms("re:\\b192\\.0\\.2\\.\\d{1,3}\\b\n")
        with mock.patch.dict(os.environ, {FORBIDDEN_TERMS_ENV: str(terms_path)}):
            terms = load_forbidden_terms([])

        errors = validate_repository(self.repo_root, terms)

        self.assertTrue(any("matched a private forbidden term" in e for e in errors), errors)

    def test_missing_explicit_terms_file_is_an_error(self) -> None:
        missing = Path(self.temp_dir.name) / "absent-terms.txt"
        errors: list[str] = []
        with mock.patch.dict(os.environ, {FORBIDDEN_TERMS_ENV: str(missing)}):
            self.assertEqual(load_forbidden_terms(errors), [])
        self.assertTrue(any("points to a missing file" in e for e in errors), errors)

    def test_rejects_overlong_description(self) -> None:
        skill_path = self.repo_root / "skills" / "rumo-example" / "SKILL.md"
        skill_path.write_text(
            skill_path.read_text(encoding="utf-8").replace(
                "description: Use when validating a concrete example skill.",
                "description: Use when " + "x" * 1030,
            ),
            encoding="utf-8",
        )
        self.assert_error_contains("description must contain at most 1024 characters")

    def set_manual_only(self, *, frontmatter: bool, metadata: bool) -> None:
        skill_dir = self.repo_root / "skills" / "rumo-example"
        if frontmatter:
            skill_path = skill_dir / "SKILL.md"
            skill_path.write_text(
                skill_path.read_text(encoding="utf-8").replace(
                    "name: rumo-example\n",
                    "name: rumo-example\ndisable-model-invocation: true\n",
                ),
                encoding="utf-8",
            )
        if metadata:
            metadata_path = skill_dir / "agents" / "openai.yaml"
            metadata_path.write_text(
                metadata_path.read_text(encoding="utf-8")
                + "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
            )

    def test_accepts_manual_only_in_both_clients(self) -> None:
        self.set_manual_only(frontmatter=True, metadata=True)
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_manual_only_only_in_frontmatter(self) -> None:
        self.set_manual_only(frontmatter=True, metadata=False)
        self.assert_error_contains("manual-only invocation must be set in both")

    def test_rejects_manual_only_only_in_metadata(self) -> None:
        self.set_manual_only(frontmatter=False, metadata=True)
        self.assert_error_contains("manual-only invocation must be set in both")

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

    def write_plugin(self, version: str, changelog: str | None) -> None:
        (self.repo_root / ".claude-plugin").mkdir()
        (self.repo_root / ".claude-plugin" / "plugin.json").write_text(
            f'{{"name": "fixture", "version": "{version}"}}\n', encoding="utf-8"
        )
        if changelog is not None:
            (self.repo_root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")

    def test_accepts_plugin_version_with_changelog_section(self) -> None:
        self.write_plugin("1.2.0", "# Changes\n\n## 1.2.0 - 2026-01-01\n\n- First.\n")
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_plugin_version_without_changelog_section(self) -> None:
        self.write_plugin("1.3.0", "# Changes\n\n## 1.2.0 - 2026-01-01\n\n- See 1.3.0 later.\n")
        self.assert_error_contains("add a '## 1.3.0' section")

    def test_rejects_plugin_version_without_changelog(self) -> None:
        self.write_plugin("1.3.0", None)
        self.assert_error_contains("add a '## 1.3.0' section")

    def test_rejects_non_semver_plugin_version(self) -> None:
        self.write_plugin("v1", "## v1\n")
        self.assert_error_contains("version must be a semantic version")

    def add_extra(self, name: str = "rumo-optional") -> Path:
        extra_dir = self.repo_root / "extras" / name
        extra_dir.mkdir(parents=True)
        (extra_dir / "SKILL.md").write_text(
            "---\n"
            f"name: {name}\n"
            "description: Use when validating an optional example skill.\n"
            "---\n\n"
            "# Optional\n",
            encoding="utf-8",
        )
        for readme in (
            self.repo_root / "README.md",
            self.repo_root / "README.en.md",
            self.repo_root / "skills" / "README.md",
        ):
            with readme.open("a", encoding="utf-8") as handle:
                handle.write(f"\n## Extras\n\n- `{name}`: optional.\n")
        return extra_dir

    def append_to_skill(self, text: str) -> None:
        skill_path = self.repo_root / "skills" / "rumo-example" / "SKILL.md"
        with skill_path.open("a", encoding="utf-8") as handle:
            handle.write(text)

    def test_accepts_optional_extra(self) -> None:
        self.add_extra()
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_extra_missing_from_inventory(self) -> None:
        self.add_extra()
        (self.repo_root / "README.md").write_text(
            "# Catalog\n\n- `rumo-example`: example.\n", encoding="utf-8"
        )
        self.assert_error_contains("missing skills: rumo-optional")

    def test_rejects_extra_listed_with_default_skills(self) -> None:
        self.add_extra()
        readme = self.repo_root / "skills" / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace("## Extras\n", ""),
            encoding="utf-8",
        )
        self.assert_error_contains(
            "lists optional skills outside the Extras section: rumo-optional"
        )

    def test_rejects_default_skill_listed_under_extras(self) -> None:
        self.add_extra()
        readme = self.repo_root / "README.md"
        readme.write_text(
            readme.read_text(encoding="utf-8").replace("- `rumo-example`: 示例。\n", "")
            + "- `rumo-example`: 示例。\n",
            encoding="utf-8",
        )
        self.assert_error_contains("lists default skills under Extras: rumo-example")

    def test_rejects_name_in_both_roots(self) -> None:
        self.add_extra("rumo-example")
        self.assert_error_contains("defined in both skills/ and extras/")

    def test_rejects_default_skill_link_to_extra(self) -> None:
        self.add_extra()
        self.append_to_skill("See [optional](../../extras/rumo-optional/SKILL.md).\n")
        self.assert_error_contains("must not link to optional extras")

    def test_rejects_license_file_inside_skill(self) -> None:
        (self.repo_root / "skills" / "rumo-example" / "LICENSE.vendor").write_text(
            "license text\n", encoding="utf-8"
        )
        self.assert_error_contains("do not ship separate license files")

    def test_rejects_oversized_default_skill(self) -> None:
        self.append_to_skill("line\n" * 150)
        self.assert_error_contains("keep it within 150")

    def test_allows_longer_extra_skill(self) -> None:
        extra_dir = self.add_extra()
        with (extra_dir / "SKILL.md").open("a", encoding="utf-8") as handle:
            handle.write("line\n" * 150)
        self.assertEqual(validate_repository(self.repo_root), [])


if __name__ == "__main__":
    unittest.main()
