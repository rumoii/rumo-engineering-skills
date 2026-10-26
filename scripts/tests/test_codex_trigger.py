from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.run_codex_trigger import REPO_ROOT, SAMPLE_AUTHOR, blind_workspace, evidence, leaked_words, load_cases, main, read_events, run_case, run_turn, toml_overrides


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


class TraceTest(unittest.TestCase):
    def test_started_command_does_not_count_as_completed(self) -> None:
        events = [{"type": "item.started", "item": {"type": "command_execution", "command": "python -m unittest", "status": "in_progress"}}]
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


class RunTurnTest(unittest.TestCase):
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


class BlindingTest(unittest.TestCase):
    def test_output_paths_that_name_an_evaluation_are_flagged(self) -> None:
        self.assertEqual(leaked_words(Path("D:/work/skill-evals/run-1")), ["evals"])
        self.assertEqual(leaked_words(Path("/tmp/judge_test")), ["judge", "test"])
        self.assertEqual(leaked_words(Path("C:/Users/x/AppData/Local/Temp/latest-runs")), [])
        self.assertEqual(leaked_words(Path("D:/evidence/run/codex-candidate-1-withdraw-existing"), ("withdraw-existing",)), ["candidate", "withdraw-existing"])

    def test_workspace_path_names_no_case_and_sits_apart_from_logs(self) -> None:
        output = Path("/evidence/run")
        workspace = blind_workspace(output)
        self.assertEqual(leaked_words(workspace.relative_to(output)), [])
        self.assertNotEqual(workspace.parent.parent, output / "verify-honest")
        self.assertNotIn(output / "verify-honest", workspace.parents)
        self.assertNotEqual(workspace, blind_workspace(output))
        self.assertEqual(leaked_words(Path(" ".join(SAMPLE_AUTHOR))), [])


if __name__ == "__main__":
    unittest.main()
