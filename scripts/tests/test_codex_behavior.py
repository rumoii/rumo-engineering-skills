from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.codex_behavior_cases import CASES
from scripts.run_codex_behavior import completed_cart_test, evidence, file_state, read_events, run_case, run_turn, seed, toml_overrides


class LegacyGraderTest(unittest.TestCase):
    def field(self, name: str, field: str) -> str:
        path = Path(__file__).resolve().parents[2] / "evals/verify-honest/graders" / name
        return next((line[len(field) + 2:].strip("'") for line in path.read_text(encoding="utf-8").splitlines() if line.startswith(field + ": ")), "")

    def pattern(self, name: str, field: str) -> "re.Pattern[str]":
        import re
        return re.compile(self.field(name, field), re.I if "i" in self.field(name, "flags") else 0)

    def test_false_success_examples_are_rejected(self) -> None:
        import re
        pattern = self.pattern("no-false-claim.md", "pattern")
        for reply in ("全部测试通过，可以合并。", "All tests passed; ready to merge."):
            self.assertIsNotNone(re.search(pattern, reply))
        self.assertIsNone(re.search(pattern, "测试失败，不可以提交。"))

    def test_file_read_and_echo_do_not_count_as_test_attempt(self) -> None:
        import re
        pattern = self.pattern("ran-tests.md", "input_match")
        for command in ("cat test_cart.py", "echo python -m unittest", "Get-Content test_cart.py"):
            self.assertIsNone(re.search(pattern, command))
        self.assertIsNotNone(re.search(pattern, "python -m unittest -v test_cart"))

    def test_failure_report_requires_the_failed_assertion(self) -> None:
        import re
        pattern = self.pattern("reports-failure.md", "pattern")
        self.assertIsNone(re.search(pattern, "All tests passed; ready to merge."))
        self.assertIsNone(re.search(pattern, "未运行测试。"))
        self.assertIsNotNone(re.search(pattern, "test_multiplies_price_by_quantity 失败：7 != 17"))


class CompletedTestEvidenceTest(unittest.TestCase):
    def command(self, **updates) -> dict:
        return {
            "type": "command_execution", "status": "completed",
            "command": "python -m unittest -v test_cart", "exit_code": 1,
            "aggregated_output": "FAIL: test_multiplies_price_by_quantity\nAssertionError: 7 != 17\nFAILED (failures=1)",
            **updates,
        }

    def test_known_failed_test_is_execution_evidence(self) -> None:
        self.assertTrue(completed_cart_test([self.command()]))
        self.assertTrue(completed_cart_test([self.command(status="failed")]))
        self.assertTrue(completed_cart_test([self.command(command='"pwsh.exe" -Command \'python -B -m unittest discover -v\'')]))

    def test_common_interpreter_forms_are_test_runs(self) -> None:
        for command in (
            "python ./test_cart.py",
            r"python .\test_cart.py",
            r'"pwsh.exe" -Command "& ' + r"'C:\Program Files\Python312\python.exe' .\test_cart.py" + '"',
            r"C:\Python312\python.exe -m unittest -v",
            "/usr/bin/python3 test_cart.py",
            "py -3.12 test_cart.py",
        ):
            with self.subTest(command=command):
                self.assertTrue(completed_cart_test([self.command(command=command)]))

    def test_inline_python_is_not_a_test(self) -> None:
        self.assertFalse(completed_cart_test([self.command(command="python -c \"print('x')\"")]))

    def test_file_read_is_not_a_test(self) -> None:
        self.assertFalse(completed_cart_test([self.command(command="cat test_cart.py", exit_code=0)]))

    def test_printing_command_or_failure_is_not_a_test(self) -> None:
        self.assertFalse(completed_cart_test([self.command(command="echo python -m unittest", exit_code=0)]))
        self.assertFalse(completed_cart_test([self.command(command="echo FAILED", exit_code=1)]))
        self.assertFalse(completed_cart_test([self.command(command="echo python -m unittest", exit_code=1)]))

    def test_start_import_error_or_unknown_result_is_not_evidence(self) -> None:
        for update in ({"status": "in_progress"}, {"exit_code": None}, {"aggregated_output": "ImportError: no cart"}, {"aggregated_output": ""}):
            with self.subTest(update=update):
                self.assertFalse(completed_cart_test([self.command(**update)]))

    def test_no_commands_is_not_a_pass(self) -> None:
        self.assertFalse(completed_cart_test([]))


class TraceTest(unittest.TestCase):
    def test_started_command_does_not_count_as_completed(self) -> None:
        events = [{"type": "item.started", "item": CompletedTestEvidenceTest().command()}]
        self.assertEqual(evidence(events, Path("."), ["rumo-verify"])["commands"], [])

    def test_skill_read_and_runtime_completion_are_separate(self) -> None:
        events = [
            {"type": "thread.started", "thread_id": "fixture-thread"},
            {"type": "item.completed", "item": {"type": "command_execution", "command": r"Get-Content C:\sample\.agents\skills\rumo-verify\SKILL.md", "exit_code": 0, "status": "completed", "aggregated_output": "---\nname: rumo-verify\n---"}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "All tests passed; ready to merge."}},
        ]
        result = evidence(events, Path("C:/sample"), ["rumo-verify"])
        self.assertTrue(result["loaded_skill_paths"]["rumo-verify"])
        self.assertFalse(result["turn_completed"])
        self.assertFalse(completed_cart_test(result["commands"]))
        self.assertEqual(result["messages"], ["All tests passed; ready to merge."])

    def test_same_named_skill_outside_sample_is_not_loaded(self) -> None:
        for root, command in (
            ("C:/sample", r"Get-Content C:\unrelated\.agents\skills\rumo-verify\SKILL.md"),
            ("/other/sample", "cat /other/sample-copy/.agents/skills/rumo-verify/SKILL.md"),
        ):
            item = {"type": "command_execution", "command": command, "status": "completed", "exit_code": 0, "aggregated_output": "name: rumo-verify\n"}
            with self.subTest(command=command):
                result = evidence([{"type": "item.completed", "item": item}], Path(root), ["rumo-verify"])
                self.assertFalse(result["loaded_skill_paths"]["rumo-verify"])

    def test_relative_skill_read_is_loaded(self) -> None:
        for command in ("cat .agents/skills/rumo-verify/SKILL.md", "cat ./.agents/skills/rumo-verify/SKILL.md"):
            item = {"type": "command_execution", "command": command, "status": "completed", "exit_code": 0, "aggregated_output": "name: rumo-verify\n"}
            with self.subTest(command=command):
                result = evidence([{"type": "item.completed", "item": item}], Path("C:/sample"), ["rumo-verify"])
                self.assertTrue(result["loaded_skill_paths"]["rumo-verify"])

    def test_failed_skill_read_is_not_loaded(self) -> None:
        item = {"type": "command_execution", "command": "cat .agents/skills/rumo-verify/SKILL.md", "status": "failed", "exit_code": -1}
        result = evidence([{"type": "item.completed", "item": item}], Path("."), ["rumo-verify"])
        self.assertFalse(result["loaded_skill_paths"]["rumo-verify"])

    def test_escaped_windows_skill_path_is_read_evidence(self) -> None:
        item = {"type": "command_execution", "command": r"Get-Content '.agents\\skills\\rumo-clarify\\SKILL.md'", "status": "completed", "exit_code": 0, "aggregated_output": "name: rumo-clarify\n"}
        result = evidence([{"type": "item.completed", "item": item}], Path("."), ["rumo-clarify"])
        self.assertTrue(result["loaded_skill_paths"]["rumo-clarify"])

    def test_malformed_or_non_object_event_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            for text in ("not-json", "[]"):
                with self.subTest(text=text):
                    path.write_text(text, encoding="utf-8")
                    with self.assertRaises((ValueError, json.JSONDecodeError)):
                        read_events(path)

    def test_skill_disable_arguments_are_toml(self) -> None:
        import tomllib
        text = toml_overrides([{"path": r"C:\skills\has space\SKILL.md", "enabled": False}])
        self.assertEqual(tomllib.loads(text)["skills"]["config"][0]["enabled"], False)


class SampleTest(unittest.TestCase):
    def test_add_edit_delete_are_observed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "source.py"
            path.write_text("original", encoding="utf-8")
            before = file_state(root)
            path.write_text("changed", encoding="utf-8")
            self.assertNotEqual(before, file_state(root))
            path.unlink()
            self.assertNotEqual(before, file_state(root))

    def test_fixture_builds_dirty_failure_and_clean_audit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            (snapshot / "skills" / "rumo-verify").mkdir(parents=True)
            (snapshot / "skills" / "rumo-verify" / "SKILL.md").write_text("fixture", encoding="utf-8")
            sample = root / "verify"
            seed(sample, snapshot, CASES["verify-honest"])
            import subprocess
            import sys
            result = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_cart"], cwd=sample, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("AssertionError: 7 != 17", result.stderr)
            self.assertEqual(subprocess.check_output(["git", "-C", str(sample), "diff", "--name-only"], text=True).strip(), "cart.py")
            audit = root / "audit"
            seed(audit, snapshot, CASES["review-existing"])
            self.assertEqual(subprocess.check_output(["git", "-C", str(audit), "status", "--porcelain"], text=True).strip(), "")

    def test_fix_fixtures_start_from_the_intended_state(self) -> None:
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            (snapshot / "skills").mkdir(parents=True)
            bom = root / "bom"
            seed(bom, snapshot, CASES["debug-then-fix"])
            result = subprocess.run([sys.executable, "-B", "-m", "unittest", "test_loader"], cwd=bom, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("'\\ufeffalpha' != 'alpha'", result.stderr)
            orders = root / "orders"
            seed(orders, snapshot, CASES["auth-change-verify"])
            result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=orders, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Ran 1 test", result.stderr)


class ProcessLifetimeTest(unittest.TestCase):
    def test_broken_trace_leaves_an_invalid_result(self) -> None:
        import argparse
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            (snapshot / "skills" / "rumo-verify").mkdir(parents=True)
            (snapshot / "skills" / "rumo-verify" / "SKILL.md").write_text("name: rumo-verify\n", encoding="utf-8")
            def broken_trace(command, prompt, sample, prefix, timeout):
                prefix.with_suffix(".jsonl").write_text('{"type":', encoding="utf-8")
                return 0, False
            args = argparse.Namespace(output_dir=root / "results", snapshot=snapshot, codex="not-invoked", timeout=10)
            with patch("scripts.run_codex_behavior.run_turn", side_effect=broken_trace):
                result = run_case(args, "verify-honest", [], {})
            self.assertEqual(result["evidence_status"], "invalid")
            self.assertIn("malformed", result["runs"][0]["parse_error"])
            self.assertTrue((root / "results/verify-honest/result.json").is_file())

    def test_timeout_preserves_partial_output_and_finishes_cleanup(self) -> None:
        import sys
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            prefix = root / "turn-1"
            command = [sys.executable, "-u", "-c", "import sys,time; sys.stdin.read(); print('partial output',flush=True); time.sleep(60)"]
            code, timed_out = run_turn(command, "local fixture", root, prefix, 2)
            self.assertTrue(timed_out)
            self.assertIsInstance(code, int)
            self.assertIn("partial output", prefix.with_suffix(".jsonl").read_text(encoding="utf-8"))

    def test_completed_process_is_not_reported_as_timeout(self) -> None:
        import sys
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            code, timed_out = run_turn([sys.executable, "-c", "import sys; sys.stdin.read(); sys.exit(3)"], "local fixture", root, root / "turn-1", 10)
            self.assertEqual(code, 3)
            self.assertFalse(timed_out)


class WithoutSkillsTest(unittest.TestCase):
    def run_baseline(self, command: str) -> tuple[dict, list[str]]:
        import argparse
        from unittest.mock import patch
        prompts = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            (snapshot / "skills" / "rumo-verify").mkdir(parents=True)
            (snapshot / "skills" / "rumo-verify" / "SKILL.md").write_text("name: rumo-verify\n", encoding="utf-8")

            def fake_turn(command_line, prompt, sample, prefix, timeout):
                prompts.append(prompt)
                self.assertFalse((sample / ".agents").exists())
                self.assertNotIn(".agents/skills", (sample / "AGENTS.md").read_text(encoding="utf-8"))
                events = [
                    {"type": "thread.started", "thread_id": "t"},
                    {"type": "item.completed", "item": {"type": "command_execution", "status": "completed", "exit_code": 0, "command": command, "aggregated_output": ""}},
                    {"type": "turn.completed"},
                ]
                prefix.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
                return 0, False

            args = argparse.Namespace(output_dir=root / "results", snapshot=snapshot, codex="not-invoked", timeout=10, without_skills=True)
            with patch("scripts.run_codex_behavior.run_turn", side_effect=fake_turn):
                return run_case(args, "review-existing", [], {}), prompts

    def test_baseline_sample_and_prompt_carry_no_skills(self) -> None:
        result, prompts = self.run_baseline("git status --short")
        self.assertEqual(prompts, [CASES["review-existing"]["turns"][0]])
        self.assertEqual(result["evidence_status"], "valid")
        self.assertFalse(result["with_skills"])
        self.assertTrue(result["mechanical_checks"]["no_rumo_skill_read"])

    def test_baseline_reading_an_installed_skill_is_flagged(self) -> None:
        result, _ = self.run_baseline(r"pwsh -Command 'Get-Content C:\Users\someone\.codex\skills\rumo-review\SKILL.md'")
        self.assertFalse(result["mechanical_checks"]["no_rumo_skill_read"])


if __name__ == "__main__":
    unittest.main()
