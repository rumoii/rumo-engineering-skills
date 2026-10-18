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
from scripts.run_dsh_behavior import (DISABLED_ROWS, dsh_command, dsh_env, evidence, finish_case, moved, outside_access,
                                      overlay_text, run_case, tree_state)


def call(tool: str, payload: dict, result: str = "", status: str = "completed", call_id: str = "c") -> list[dict]:
    return [{"type": "tool_call", "callId": call_id, "tool": tool, "input": payload},
            {"type": "tool_result", "callId": call_id, "status": status, "result": result}]


def done(cwd: str, text: str = "report", kind: str = "completed") -> list[dict]:
    return [{"type": "text", "text": text},
            {"type": "status", "phase": "step_end", "turn": 1, "step": 1, "usage": {"inputTokens": 10, "outputTokens": 2}},
            {"type": "status", "phase": "turn_end", "turn": 1, "reason": {"kind": kind}},
            {"type": "final", "text": text}]


def session(cwd: str, session_id: str = "session-1") -> dict:
    return {"type": "session", "sessionId": session_id, "cwd": cwd}


class EvidenceTest(unittest.TestCase):
    def test_skill_tool_or_sample_read_counts_as_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for events in (call("skill", {"name": "rumo-review"}),
                           call("read", {"file_path": ".agents/skills/rumo-review/SKILL.md"}, "---\nname: rumo-review\n")):
                observed = evidence([session(temp), *events, *done(temp)], root, ["rumo-review"])
                self.assertTrue(observed["loaded_skill_paths"]["rumo-review"], events)

    def test_failed_load_or_copy_elsewhere_is_not_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for events in (call("skill", {"name": "rumo-review"}, status="error"),
                           call("read", {"file_path": r"C:\Users\someone\.agents\skills\rumo-review\SKILL.md"}, "name: rumo-review")):
                self.assertFalse(evidence([*events, *done(temp)], root, ["rumo-review"])["loaded_skill_paths"]["rumo-review"])

    def test_completion_errors_usage_and_session(self) -> None:
        root = Path(".")
        observed = evidence([session("C:/s"), *done("C:/s", "final")], root, [])
        self.assertTrue(observed["turn_completed"])
        self.assertEqual((observed["messages"], observed["usage"], observed["session_id"]), (["final"], {"inputTokens": 10, "outputTokens": 2}, "session-1"))
        self.assertFalse(evidence(done("C:/s")[:-1], root, [])["turn_completed"])
        self.assertTrue(evidence(done("C:/s", kind="error"), root, [])["errors"])
        self.assertTrue(evidence([{"type": "error", "message": "boom"}], root, [])["errors"])

    def test_outside_access_flags_absolute_relative_and_home_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sample"
            events = [*call("read", {"file_path": str(root / "a.py")}, call_id="1"),
                      *call("read", {"file_path": "src/b.py"}, call_id="2"),
                      *call("read", {"file_path": "../../key/x.txt"}, call_id="3"),
                      *call("pwsh", {"command": r"Get-Content D:\Workspace\Other\notes.md"}, call_id="4"),
                      *call("pwsh", {"command": "Get-ChildItem ~/.ssh"}, call_id="5")]
            found = outside_access(events, root)
        self.assertEqual(len(found), 3)
        self.assertTrue(any(path.endswith("x.txt") for path in found))
        self.assertIn(r"D:\Workspace\Other\notes.md", found)
        self.assertIn("~/", found)


class IsolationTest(unittest.TestCase):
    def test_overlay_disables_default_roots_and_risky_rows_in_both_arms(self) -> None:
        for skill_dir in (Path("C:/s/.agents/skills"), None):
            text = overlay_text(skill_dir)
            self.assertIn("includeDefaultRoots: false", text)
            for row in ("tool-web", "mcp-resources", "tool-working-directory", "config-editor"):
                self.assertIn(f"- id: {row}\n  disabled: true", text)
        self.assertIn("customSkillDirs: ['C:/s/.agents/skills']", overlay_text(Path("C:/s/.agents/skills")))
        self.assertIn("customSkillDirs: []", overlay_text(None))
        self.assertTrue(set(DISABLED_ROWS) >= {"tool-web", "tool-working-directory"})

    def test_environment_isolates_homes_temp_and_permission_mode(self) -> None:
        with patch.dict("os.environ", {"DSH_PERMISSION_MODE": "danger-full-access", "DSH_HOME": "C:/real"}):
            env = dsh_env(Path("C:/dsh"), Path("C:/o/home"), Path("C:/o/agents"), Path("C:/o/tmp"), "k")
        self.assertEqual((env["DSH_HOME"], env["DSH_AGENTS_HOME"], env["DSH_PERMISSION_MODE"]), (str(Path("C:/o/home")), str(Path("C:/o/agents")), "workspace-write"))
        self.assertEqual((env["TEMP"], env["TMP"]), (str(Path("C:/o/tmp")),) * 2)

    def test_command_never_carries_the_key_and_resumes_by_session(self) -> None:
        command = dsh_command(Path("C:/dsh"), Path("C:/o/overlay.yml"), "session-1")
        self.assertEqual(command[command.index("--profile") + 1], "headless")
        self.assertEqual(command[-3:], ["--session-id", "session-1", "-"])
        self.assertLess(command.index("--patch"), command.index("--json"))

    def test_key_in_output_quarantines_the_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "case"
            out.mkdir()
            (out / "turn-1.jsonl").write_text('{"text": "sk-fake-123"}', encoding="utf-8")
            result = finish_case(out, "sk-fake-123", {"case": "x", "observed": {"messages": ["sk-fake-123"]}})
            self.assertTrue(result["key_leak"])
            self.assertNotIn("observed", result)
            self.assertFalse(out.exists())
            self.assertTrue(out.with_name("case.quarantined").exists())

    def test_tree_state_records_links_without_following_them(self) -> None:
        from scripts.run_codex_behavior import make_dir_link
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "target").mkdir()
            (root / "target" / "f.txt").write_text("x", encoding="utf-8")
            make_dir_link(root / "home" / "skills", root / "target")
            state = tree_state(root / "home")
            self.assertEqual(state["skills"][0], "link")
            self.assertNotIn("skills/f.txt", state)
            self.assertEqual(moved({"a": "1", "b": "2"}, {"a": "1", "b": "3"}), ["b"])


class RunCaseTest(unittest.TestCase):
    def run_with(self, make_events, name: str, without_skills: bool, moves: bool = False) -> tuple[dict, list]:
        calls = []
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "snapshot"
            for skill in CASES[name]["skills"]:
                (snapshot / "skills" / skill).mkdir(parents=True)
                (snapshot / "skills" / skill / "SKILL.md").write_text(f"---\nname: {skill}\n", encoding="utf-8")

            def fake_turn(command, prompt, sample, prefix, timeout, env):
                calls.append((command, prompt, env))
                events = make_events(sample)
                prefix.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
                return 0, False

            states = iter([{"x": "1"}, {"x": "2" if moves else "1"}])
            args = argparse.Namespace(output_dir=root / "results", snapshot=snapshot, dsh_root=root / "dsh", key="sk-fake",
                                      api_key_file=root / "key" / "k.txt", timeout=10, without_skills=without_skills)
            with patch("scripts.run_dsh_behavior.run_turn", side_effect=fake_turn), \
                 patch("scripts.run_dsh_behavior.sentinel", side_effect=lambda _: next(states)):
                return run_case(args, name), calls

    def test_with_skills_requires_a_load_and_mounts_only_the_sample(self) -> None:
        def loaded(sample):
            return [session(str(sample)), *call("skill", {"name": "rumo-review"}), *done(str(sample))]
        result, calls = self.run_with(loaded, "withdraw-existing", without_skills=False)
        self.assertEqual(result["evidence_status"], "valid")
        self.assertIn("rumo-review", calls[0][1])
        self.assertNotIn("sk-fake", json.dumps(calls[0][0]))
        unloaded = self.run_with(lambda s: [session(str(s)), *done(str(s))], "withdraw-existing", without_skills=False)[0]
        self.assertEqual(unloaded["evidence_status"], "invalid")

    def test_baseline_flags_any_rumo_skill(self) -> None:
        result, calls = self.run_with(lambda s: [session(str(s)), *done(str(s))], "withdraw-existing", without_skills=True)
        self.assertEqual(calls[0][1], CASES["withdraw-existing"]["turns"][0])
        self.assertTrue(result["mechanical_checks"]["no_rumo_skill_read"])
        leaked = self.run_with(lambda s: [session(str(s)), *call("skill", {"name": "rumo-review"}), *done(str(s))], "withdraw-existing", without_skills=True)[0]
        self.assertFalse(leaked["mechanical_checks"]["no_rumo_skill_read"])

    def test_session_outside_sample_or_moved_sentinel_is_invalid(self) -> None:
        elsewhere = self.run_with(lambda s: [session("C:/elsewhere"), *done("C:/elsewhere")], "withdraw-existing", without_skills=True)[0]
        self.assertEqual(elsewhere["evidence_status"], "invalid")
        result = self.run_with(lambda s: [session(str(s)), *done(str(s))], "withdraw-existing", without_skills=True, moves=True)[0]
        self.assertEqual((result["evidence_status"], result["sentinel_moved"]), ("invalid", ["x"]))

    def test_shared_case_checks_apply(self) -> None:
        result = self.run_with(lambda s: [session(str(s)), *call("skill", {"name": "rumo-filesystem-safety"}), *done(str(s))],
                               "duplicate-through-link", without_skills=False)[0]
        self.assertTrue(result["mechanical_checks"]["links_preserved"])
        self.assertTrue(result["mechanical_checks"]["original_preserved"])


class CliTest(unittest.TestCase):
    def test_output_in_system_temp_is_rejected(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "snap" / "skills").mkdir(parents=True)
            (Path(temp) / "dsh" / "apps" / "cli" / "src").mkdir(parents=True)
            (Path(temp) / "dsh" / "apps" / "cli" / "src" / "bin.ts").write_text("", encoding="utf-8")
            proc = subprocess.run([sys.executable, str(repo / "scripts" / "run_dsh_behavior.py"), "--snapshot", str(Path(temp) / "snap"),
                                   "--output-dir", str(Path(temp) / "out"), "--dsh-root", str(Path(temp) / "dsh"),
                                   "--api-key-file", str(Path(temp) / "k.txt"), "--canary-only"], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("system temporary directory", proc.stderr)


if __name__ == "__main__":
    unittest.main()
