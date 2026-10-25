from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS_ROOT = REPO_ROOT / "evals"
SKILL_IN_PATTERN = re.compile(r"\)\?(rumo-[a-z0-9-]+)\"'?$")
# Behavior cases stay on graders computed from the transcript; judge-model
# graders cost money on every run and drift between judges.
FREE_GRADER_TYPES = {"regex", "tool_used", "tool_order", "file_exists"}


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        raise AssertionError(f"{path}: missing frontmatter")
    fields: dict[str, str] = {}
    for line in lines[1 : lines.index("---", 1)]:
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def tags(case: Path) -> str:
    return frontmatter(case / "prompt.md").get("tags", "")


class TriggerEvalsTest(unittest.TestCase):
    """Static checks for the claude plugin eval suite; running it calls a model."""

    def cases(self) -> list[Path]:
        return sorted(path for path in EVALS_ROOT.iterdir() if path.is_dir() and path.name != "results")

    def behavior_cases(self) -> list[Path]:
        return [case for case in self.cases() if "behavior" in tags(case)]

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

    def test_each_case_is_trigger_or_behavior(self) -> None:
        for case in self.cases():
            with self.subTest(case=case.name):
                self.assertNotEqual("trigger" in tags(case), "behavior" in tags(case))

    def test_graders_name_existing_skills(self) -> None:
        behavior = set(self.behavior_cases())
        available = {
            path.parent.name
            for root in ("skills", "extras")
            for path in (REPO_ROOT / root).glob("*/SKILL.md")
        }
        for grader in sorted(EVALS_ROOT.glob("*/graders/*.md")):
            if grader.parent.parent in behavior:
                continue
            with self.subTest(grader=f"{grader.parent.parent.name}/{grader.name}"):
                fields = frontmatter(grader)
                self.assertEqual(fields.get("type"), "tool_used")
                self.assertEqual(fields.get("tool"), "Skill")
                match = SKILL_IN_PATTERN.search(fields.get("input_match", ""))
                if match:
                    self.assertIn(match.group(1), available)
                else:
                    self.assertEqual(grader.name, "uses-no-rumo-skill.md")
                if grader.name.startswith(("skips-", "uses-no-")):
                    self.assertEqual((fields.get("min"), fields.get("max")), ("0", "0"))

    def test_every_model_invoked_skill_has_a_trigger_case(self) -> None:
        covered = set()
        for case in self.cases():
            if "trigger" not in tags(case):
                continue
            for grader in (case / "graders").glob("uses-*.md"):
                match = SKILL_IN_PATTERN.search(frontmatter(grader).get("input_match", ""))
                if match:
                    covered.add(match.group(1))
        skills = {
            path.parent.name
            for root in ("skills", "extras")
            for path in (REPO_ROOT / root).glob("*/SKILL.md")
            if frontmatter(path).get("disable-model-invocation") != "true"
        }
        self.assertEqual(sorted(skills - covered), [], "add a trigger case whose uses-* grader names each skill")

    def test_behavior_cases_scaffold_a_workspace_and_use_free_graders(self) -> None:
        self.assertTrue(self.behavior_cases())
        for case in self.behavior_cases():
            with self.subTest(case=case.name):
                spec = (case / "case.yaml").read_text(encoding="utf-8")
                match = re.search(r"^\s+scaffold_script:\s*(\S+)", spec, re.M)
                self.assertTrue(match, "behavior case needs context.scaffold_script")
                self.assertTrue((case / match.group(1)).is_file())
                types = {frontmatter(grader).get("type") for grader in (case / "graders").glob("*.md")}
                self.assertTrue(types)
                self.assertLessEqual(types, FREE_GRADER_TYPES)

    def test_database_stop_disallows_shell_execution(self) -> None:
        prompt = frontmatter(EVALS_ROOT / "database-stop" / "prompt.md")
        self.assertIn("Bash", prompt["allowed_tools"])
        grader = frontmatter(EVALS_ROOT / "database-stop" / "graders" / "no-shell.md")
        self.assertEqual(grader["tool"], "Bash")
        self.assertEqual(grader["input_match"], r"'[\s\S]*'")
        self.assertEqual((grader["min"], grader["max"]), ("0", "0"))

    def test_regex_graders_pass_flags_separately(self) -> None:
        # Graders compile patterns as JavaScript RegExp, which rejects a leading
        # inline group such as (?i); the grader reports it as a failed check.
        for grader in sorted(EVALS_ROOT.glob("*/graders/*.md")):
            fields = frontmatter(grader)
            if fields.get("type") != "regex":
                continue
            with self.subTest(grader=f"{grader.parent.parent.name}/{grader.name}"):
                self.assertNotRegex(fields.get("pattern", ""), r"\(\?[a-z]+\)")

    def test_unverified_report_accepts_plain_admissions(self) -> None:
        # Observed replies missed by an earlier, narrower pattern.
        raw = frontmatter(EVALS_ROOT / "chain-auth-change" / "graders" / "reports-unverified.md")["pattern"]
        pattern = re.compile(raw[1:-1].replace("''", "'"), re.I)
        for reply in ("但测试没有跑：我这边没有能执行命令的工具。", "测试没法跑", "Tests were not run.", "I can't run the tests here."):
            self.assertRegex(reply, pattern)
        for reply in ("测试全部通过。", "All tests passed."):
            self.assertNotRegex(reply, pattern)

    def test_review_finding_must_name_the_lost_bound(self) -> None:
        raw = frontmatter(EVALS_ROOT / "review-readonly" / "graders" / "finds-bug.md")["pattern"]
        pattern = re.compile(raw[1:-1], re.I)
        for reply in (
            "删掉了 paid_total 上限校验",
            "退款金额可以超过已付金额",
            "退款金额没有上限（`refund.py:7`）：没跟订单金额比较",
            "A refund can exceed the amount paid.",
        ):
            self.assertRegex(reply, pattern)
        self.assertNotRegex("services/refund.py:7 缺少正数校验以外的问题未发现。", pattern)



class BlindCasesTest(unittest.TestCase):
    """What the model sees must not reveal that it is being graded."""

    WORDS = re.compile(r"\b(?:benchmark|evals?|evaluation|fixtures?|graders?|judge|rubric)\b", re.I)

    def test_prompts_name_no_evaluation(self) -> None:
        for prompt in sorted(EVALS_ROOT.glob("*/prompt.md")):
            with self.subTest(case=prompt.parent.name):
                body = prompt.read_text(encoding="utf-8").split("\n---\n", 1)[1]
                self.assertIsNone(self.WORDS.search(body))

    def test_scaffold_git_metadata_names_no_evaluation(self) -> None:
        for script in sorted(EVALS_ROOT.glob("*/fixture.sh")):
            with self.subTest(case=script.parent.name):
                for line in script.read_text(encoding="utf-8").splitlines():
                    if re.match(r"\s*git (?:config user\.|commit)", line):
                        self.assertIsNone(self.WORDS.search(line), line)


if __name__ == "__main__":
    unittest.main()
