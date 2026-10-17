from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.run_codex_trigger import REPO_ROOT, load_cases, main, run_case


def read_skill(name: str, command: str | None = None) -> dict:
    return {"type": "item.completed", "item": {
        "type": "command_execution", "status": "completed", "exit_code": 0,
        "command": command or f"pwsh -Command 'Get-Content .agents/skills/{name}/SKILL.md'",
        "aggregated_output": f"---\nname: {name}\n",
    }}


class CaseParsingTest(unittest.TestCase):
    def test_every_trigger_case_has_an_expectation(self) -> None:
        cases = load_cases()
        self.assertIn("debug-readonly", cases)
        for name, case in cases.items():
            with self.subTest(case=name):
                self.assertTrue(case["prompt"])
                self.assertTrue(case["expect"] or case["avoid"] or case["no_rumo"])
        self.assertEqual(cases["no-skill-general-question"]["expect"], [])
        self.assertTrue(cases["no-skill-general-question"]["no_rumo"])
        self.assertEqual((cases["debug-readonly"]["expect"], cases["debug-readonly"]["avoid"]), (["rumo-debug"], ["rumo-test"]))

    def test_unreadable_grader_is_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            case = Path(temp) / "broken"
            (case / "graders").mkdir(parents=True)
            (case / "prompt.md").write_text("---\ntags: [trigger]\n---\n\nprompt\n", encoding="utf-8")
            (case / "graders" / "uses-expected-skill.md").write_text("---\ntype: tool_used\ninput_match: 'anything'\n---\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_cases(Path(temp))


class RunCaseTest(unittest.TestCase):
    def run_with(self, name: str, events: list[dict]) -> dict:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            for skill in ("rumo-debug", "rumo-test", "rumo-coding-guidelines"):
                (snapshot / "skills" / skill).mkdir(parents=True)
                (snapshot / "skills" / skill / "SKILL.md").write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")

            def fake_turn(command, prompt, sample, prefix, timeout):
                prefix.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
                return 0, False

            args = argparse.Namespace(output_dir=root / "results", snapshot=snapshot, codex="not-invoked", timeout=10)
            with patch("scripts.run_codex_trigger.run_turn", side_effect=fake_turn):
                return run_case(args, name, load_cases()[name], 1, [], {})

    def test_expected_skill_read_passes(self) -> None:
        result = self.run_with("debug-readonly", [read_skill("rumo-debug"), {"type": "turn.completed"}])
        self.assertEqual((result["verdict"], result["read"]), ("pass", ["rumo-debug"]))

    def test_avoided_skill_read_fails(self) -> None:
        result = self.run_with("debug-readonly", [read_skill("rumo-debug"), read_skill("rumo-test"), {"type": "turn.completed"}])
        self.assertEqual(result["verdict"], "fail")

    def test_installed_copy_elsewhere_is_not_a_trigger(self) -> None:
        elsewhere = read_skill("rumo-debug", "pwsh -Command 'Get-Content C:/Users/someone/.codex/skills/rumo-debug/SKILL.md'")
        result = self.run_with("debug-readonly", [elsewhere, {"type": "turn.completed"}])
        self.assertEqual((result["verdict"], result["read"]), ("fail", []))

    def test_unfinished_turn_is_invalid_not_fail(self) -> None:
        result = self.run_with("debug-readonly", [read_skill("rumo-debug")])
        self.assertEqual(result["verdict"], "invalid")

    def test_known_baseline_failure_is_flagged_when_it_passes(self) -> None:
        result = self.run_with("coding-baseline", [read_skill("rumo-coding-guidelines"), {"type": "turn.completed"}])
        self.assertEqual(result["verdict"], "pass")
        self.assertTrue(result["expected_failure"])
        self.assertIn("note", result)


class ArgumentTest(unittest.TestCase):
    def test_output_inside_checkout_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "skills").mkdir()
            with self.assertRaises(SystemExit) as raised, patch("sys.stderr"):
                main(["--snapshot", temp, "--output-dir", str(REPO_ROOT / "trigger-evidence")])
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse((REPO_ROOT / "trigger-evidence").exists())


if __name__ == "__main__":
    unittest.main()
