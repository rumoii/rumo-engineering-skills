from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.run_codex_trigger import REPO_ROOT, load_cases
from scripts.run_pi_behavior import READ_ONLY_TOOLS, WORKSPACE_GUARD
from scripts.run_pi_trigger import main, pi_command, run_case


SETTLED = {"type": "agent_settled"}


def read_call(path: str, output: str) -> list[dict]:
    """pi puts args on the start event only."""
    return [{"type": "tool_execution_start", "toolCallId": path, "toolName": "read", "args": {"path": path}},
            {"type": "tool_execution_end", "toolCallId": path, "toolName": "read",
             "result": {"content": [{"type": "text", "text": output}]}, "isError": False}]


def read_skill(name: str) -> list[dict]:
    return read_call(f".agents/skills/{name}/SKILL.md", f"---\nname: {name}\n")


class CommandTest(unittest.TestCase):
    def test_only_sample_skills_load_without_context_files_or_mcp(self) -> None:
        skill_dirs = [Path("w/.agents/skills/rumo-debug"), Path("w/.agents/skills/rumo-test")]
        command = pi_command("pi", "provider/model", Path("s"), "id", skill_dirs)
        for flag in ("--no-skills", "--no-extensions", "--no-prompt-templates", "--no-mcp", "--no-context-files"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("--tools") + 1], READ_ONLY_TOOLS)
        self.assertEqual(command[command.index("-e") + 1], str(WORKSPACE_GUARD))
        self.assertEqual([command[i + 1] for i, part in enumerate(command) if part == "--skill"], [str(p) for p in skill_dirs])


class RunCaseTest(unittest.TestCase):
    def run_with(self, name: str, events: list[dict]) -> tuple[dict, list[str]]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            for skill in ("rumo-debug", "rumo-test", "rumo-coding-guidelines"):
                (snapshot / "skills" / skill).mkdir(parents=True)
                (snapshot / "skills" / skill / "SKILL.md").write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")
            commands = []

            def fake_turn(command, prompt, sample, prefix, timeout):
                commands.append(command)
                prefix.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
                return 0, False

            args = argparse.Namespace(output_dir=root / "results", workspace_root=root / "work", snapshot=snapshot,
                                      pi="not-invoked", model="provider/model", timeout=10)
            with patch("scripts.run_pi_trigger.run_turn", side_effect=fake_turn):
                return run_case(args, name, load_cases()[name], 1), commands[0]

    def test_expected_skill_read_passes_and_every_sample_skill_is_offered(self) -> None:
        result, command = self.run_with("debug-readonly", [*read_skill("rumo-debug"), SETTLED])
        self.assertEqual((result["verdict"], result["read"]), ("pass", ["rumo-debug"]))
        offered = [Path(command[i + 1]).name for i, part in enumerate(command) if part == "--skill"]
        self.assertEqual(offered, ["rumo-coding-guidelines", "rumo-debug", "rumo-test"])

    def test_avoided_skill_read_fails(self) -> None:
        result, _ = self.run_with("debug-readonly", [*read_skill("rumo-debug"), *read_skill("rumo-test"), SETTLED])
        self.assertEqual(result["verdict"], "fail")

    def test_installed_copy_elsewhere_is_not_a_trigger(self) -> None:
        # The workspace guard blocks the read; the runner must still not count it.
        elsewhere = read_call(r"C:\Users\someone\.pi\agent\skills\rumo-debug\SKILL.md", "---\nname: rumo-debug\n")
        elsewhere[1]["isError"] = True
        result, _ = self.run_with("debug-readonly", [*elsewhere, SETTLED])
        self.assertEqual((result["verdict"], result["read"]), ("fail", []))

    def test_unsettled_turn_is_invalid_not_fail(self) -> None:
        result, _ = self.run_with("debug-readonly", read_skill("rumo-debug"))
        self.assertEqual(result["verdict"], "invalid")

    def test_unblocked_read_outside_the_sample_is_invalid_and_a_blocked_one_is_recorded(self) -> None:
        outside = str(Path.home() / "notes.txt")
        leaked, _ = self.run_with("debug-readonly", [*read_skill("rumo-debug"), *read_call(outside, "private"), SETTLED])
        self.assertEqual(leaked["verdict"], "invalid")
        blocked_call = read_call(outside, "blocked")
        blocked_call[1]["isError"] = True
        blocked, _ = self.run_with("debug-readonly", [*read_skill("rumo-debug"), *blocked_call, SETTLED])
        self.assertEqual(blocked["verdict"], "pass")
        self.assertEqual(blocked["workspace_escapes"], [{"tool": "read", "target": outside, "blocked": True}])

    def test_loaded_context_file_is_invalid(self) -> None:
        system = {"type": "message_end", "message": {"role": "system", "sections": {
            "project_context": '<project_instructions path="C:/Users/someone/.pi/agent/AGENTS.md">'}}}
        result, _ = self.run_with("debug-readonly", [system, *read_skill("rumo-debug"), SETTLED])
        self.assertEqual(result["verdict"], "invalid")


class ArgumentTest(unittest.TestCase):
    def test_output_inside_checkout_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "skills").mkdir()
            with self.assertRaises(SystemExit) as raised, patch("sys.stderr"):
                main(["--snapshot", temp, "--output-dir", str(REPO_ROOT / "pi-trigger-evidence")])
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse((REPO_ROOT / "pi-trigger-evidence").exists())

    def test_workspace_root_with_evaluation_words_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            snapshot = Path(temp) / "snap"
            (snapshot / "skills").mkdir(parents=True)
            output = Path(temp) / "out"
            stderr = io.StringIO()
            with self.assertRaises(SystemExit) as raised, patch("sys.stderr", stderr):
                main(["--snapshot", str(snapshot), "--output-dir", str(output), "--workspace-root", str(Path(temp) / "eval-work")])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("workspace root", stderr.getvalue())
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
