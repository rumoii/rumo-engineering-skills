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


class ReplayTest(unittest.TestCase):
    def make_repo(self, root: Path) -> tuple[Path, str, str]:
        from scripts.run_codex_behavior import git
        repo = root / "source"
        (repo / "src").mkdir(parents=True)
        (repo / "src" / "keep.py").write_text("base\n", encoding="utf-8")
        (repo / "src" / "gone.py").write_text("old\n", encoding="utf-8")
        (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
        git(repo, "init", "-q")
        commit = ["-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qam"]
        git(repo, "add", ".")
        git(repo, *commit, "base")
        base = git(repo, "rev-parse", "HEAD")
        (repo / "src" / "keep.py").write_text("edited\n", encoding="utf-8")
        (repo / "src" / "gone.py").unlink()
        (repo / "src" / "new.py").write_text("added\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, *commit, "dirty")
        return repo, base, git(repo, "rev-parse", "HEAD")

    def test_commit_seed_with_dirty_overlay(self) -> None:
        from scripts.run_codex_behavior import git, seed_from_commit
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, dirty = self.make_repo(root)
            (root / "snap" / "skills" / "rumo-review").mkdir(parents=True)
            (root / "snap" / "skills" / "rumo-review" / "SKILL.md").write_text("name: rumo-review\n", encoding="utf-8")
            sample = root / "sample"
            seed_from_commit(sample, root / "snap", {"repo": str(repo), "commit": base, "dirty_commit": dirty})
            self.assertEqual(git(sample, "show", "HEAD:src/keep.py"), "base")
            self.assertEqual((sample / "src" / "keep.py").read_text(encoding="utf-8"), "edited\n")
            self.assertFalse((sample / "src" / "gone.py").exists())
            self.assertTrue((sample / "src" / "new.py").exists())
            self.assertIn(".agents/", (sample / ".gitignore").read_text(encoding="utf-8"))
            self.assertNotIn(".agents", git(sample, "status", "--short", "--untracked-files=all"))

    def test_manifest_must_stay_outside_checkout_and_be_complete(self) -> None:
        from scripts.run_codex_behavior import load_manifest
        repo = Path(__file__).resolve().parents[2]
        with self.assertRaises(ValueError):
            load_manifest(repo / "replays.json", repo)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "replays.json"
            path.write_text(json.dumps([{"name": "r", "repo": "x", "commit": "c", "turns": ["q"], "skills": []}]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_manifest(path, repo)
            path.write_text(json.dumps([{"name": "r", "repo": "x", "commit": "c", "turns": ["q"], "skills": [], "rubric": "x"}]), encoding="utf-8")
            self.assertTrue(load_manifest(path, repo)["r"]["read_only"])

    def test_replay_case_runs_from_its_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, base, _ = self.make_repo(root)
            (root / "snap" / "skills").mkdir(parents=True)
            case = {"repo": str(repo), "commit": base, "turns": ["review src"], "skills": [], "rubric": "r", "read_only": True}

            def fake_turn(command, prompt, sample, prefix, timeout):
                self.assertTrue((sample / "src" / "gone.py").exists())
                prefix.with_suffix(".jsonl").write_text("\n".join(json.dumps(e) for e in [reply("ok"), SETTLED]), encoding="utf-8")
                return 0, False

            args = argparse.Namespace(output_dir=root / "out", snapshot=root / "snap", pi="x", model="m", timeout=10,
                                      without_skills=True, cases={"replay": case})
            with patch("scripts.run_pi_behavior.run_turn", side_effect=fake_turn):
                result = run_case(args, "replay")
            self.assertEqual(result["evidence_status"], "valid")
            self.assertTrue(result["mechanical_checks"]["sample_unchanged"])


if __name__ == "__main__":
    unittest.main()
