from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.codex_behavior_cases import CASES
from scripts.run_pi_behavior import READ_ONLY_TOOLS, evidence, pi_command, run_case


def read_call(path: str, output: str, error: bool = False) -> list[dict]:
    """pi puts args on the start event only."""
    return [{"type": "tool_execution_start", "toolCallId": "c", "toolName": "read", "args": {"path": path}},
            {"type": "tool_execution_end", "toolCallId": "c", "toolName": "read",
             "result": {"content": [{"type": "text", "text": output}]}, "isError": error}]


def reply(text: str, stop: str = "stop") -> dict:
    return {"type": "message_end", "message": {"role": "assistant", "content": [{"type": "thinking", "thinking": "hidden"}, {"type": "text", "text": text}],
                                               "stopReason": stop, "usage": {"input": 10, "output": 2}}}


SETTLED = {"type": "agent_settled"}


class EvidenceTest(unittest.TestCase):
    def test_sample_skill_read_is_loaded_relative_or_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for path in (".agents/skills/rumo-review/SKILL.md", str(root / ".agents" / "skills" / "rumo-review" / "SKILL.md")):
                observed = evidence([*read_call(path, "---\nname: rumo-review\n"), SETTLED], root, ["rumo-review"])
                self.assertTrue(observed["loaded_skill_paths"]["rumo-review"], path)

    def test_same_named_skill_elsewhere_or_failed_read_is_not_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for event in (read_call(r"C:\Users\someone\.agents\skills\rumo-review\SKILL.md", "name: rumo-review"),
                          read_call(".agents/skills/rumo-review/SKILL.md", "name: rumo-review", error=True)):
                self.assertFalse(evidence([*event, SETTLED], root, ["rumo-review"])["loaded_skill_paths"]["rumo-review"])

    def test_completion_errors_replies_and_usage(self) -> None:
        root = Path(".")
        done = evidence([reply("found it"), reply("final"), SETTLED], root, [])
        self.assertTrue(done["turn_completed"])
        self.assertEqual(done["messages"], ["found it", "final"])
        self.assertEqual(done["usage"], {"input": 20, "output": 4})
        self.assertFalse(evidence([reply("partial")], root, [])["turn_completed"])
        self.assertTrue(evidence([reply("", stop="error"), SETTLED], root, [])["errors"])
        self.assertTrue(evidence([{"type": "auto_retry_end", "success": False}, SETTLED], root, [])["errors"])

    def test_command_is_read_only_without_installed_resources(self) -> None:
        command = pi_command("pi", "provider/model", Path("s"), "id")
        for flag in ("--no-skills", "--no-extensions", "--no-prompt-templates"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("--tools") + 1], READ_ONLY_TOOLS)
        self.assertNotIn("bash", READ_ONLY_TOOLS.split(","))


class RunCaseTest(unittest.TestCase):
    def run_with(self, events: list[dict], without_skills: bool) -> tuple[dict, list[str]]:
        prompts = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            (snapshot / "skills" / "rumo-review").mkdir(parents=True)
            (snapshot / "skills" / "rumo-review" / "SKILL.md").write_text("---\nname: rumo-review\n", encoding="utf-8")

            def fake_turn(command, prompt, sample, prefix, timeout):
                prompts.append(prompt)
                self.assertEqual(sample.name, "sample")
                prefix.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
                return 0, False

            args = argparse.Namespace(output_dir=root / "results", snapshot=snapshot, pi="not-invoked", model="m",
                                      timeout=10, without_skills=without_skills)
            with patch("scripts.run_pi_behavior.run_turn", side_effect=fake_turn):
                return run_case(args, "withdraw-existing"), prompts

    def test_with_skills_requires_the_named_skill_read(self) -> None:
        loaded = [*read_call(".agents/skills/rumo-review/SKILL.md", "name: rumo-review"), reply("report"), SETTLED]
        result, prompts = self.run_with(loaded, without_skills=False)
        self.assertEqual(result["evidence_status"], "valid")
        self.assertIn("rumo-review", prompts[0])
        self.assertEqual(self.run_with([reply("report"), SETTLED], without_skills=False)[0]["evidence_status"], "invalid")

    def test_baseline_prompt_has_no_skills_and_flags_any_skill_read(self) -> None:
        result, prompts = self.run_with([reply("report"), SETTLED], without_skills=True)
        self.assertEqual(prompts, [CASES["withdraw-existing"]["turns"][0]])
        self.assertTrue(result["mechanical_checks"]["no_rumo_skill_read"])
        leaked = [*read_call(r"C:\Users\someone\.agents\skills\rumo-review\SKILL.md", "---\nname: rumo-review\n"), reply("r"), SETTLED]
        self.assertFalse(self.run_with(leaked, without_skills=True)[0]["mechanical_checks"]["no_rumo_skill_read"])

    def test_editing_cases_are_refused(self) -> None:
        args = argparse.Namespace(output_dir=Path("unused"), snapshot=Path("unused"), pi="x", model="m", timeout=1)
        with self.assertRaises(ValueError):
            run_case(args, "auth-change-verify")

    def test_output_inside_checkout_is_rejected(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "skills").mkdir()
            proc = subprocess.run([sys.executable, str(repo / "scripts" / "run_pi_behavior.py"), "--snapshot", temp,
                                   "--output-dir", str(repo / "pi-evidence")], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("outside the source checkout", proc.stderr)
        self.assertFalse((repo / "pi-evidence").exists())


if __name__ == "__main__":
    unittest.main()
