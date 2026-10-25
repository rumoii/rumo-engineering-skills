#!/usr/bin/env python3
"""Tests for session_digest.py against small constructed Claude Code, Codex, and Kimi Code session files; no model is called."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent / "session_digest.py"


def claude_line(kind: str, content: object, time: str, cwd: str, **extra: object) -> dict:
    return {"type": kind, "message": {"role": kind, "content": content}, "timestamp": time, "cwd": cwd,
            "entrypoint": "cli", "isSidechain": False, **extra}


def codex_message(role: str, text: str, time: str, phase: str | None = None) -> dict:
    kind = "output_text" if role == "assistant" else "input_text"
    payload = {"type": "message", "role": role, "content": [{"type": kind, "text": text}]}
    if phase:
        payload["phase"] = phase
    return {"type": "response_item", "timestamp": time, "payload": payload}


def kimi_message(role: str, text: str, time: str, final: bool = False) -> dict:
    content = [{"type": "text", "text": text}]
    message = {"role": role, "content": content}
    if role == "user":
        meta = {"createdAt": time, "origin": {"kind": "user"}}
    else:
        content.insert(0, {"type": "think", "think": "KIMI PRIVATE THOUGHT"})
        meta = {"finish": {"finishReason": "completed" if final else "tool_calls"}}
    moment = datetime.fromisoformat(time.replace("Z", "+00:00")).timestamp()
    return {"type": "agent.message.appended", "time": int(moment * 1000),
            "message": {"message": message, "meta": meta}}


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Write the records and date the file by its last timestamp, as a client that stopped writing then would."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8")
    stamps = [record["timestamp"] for record in records if record.get("timestamp")]
    if stamps:
        moment = datetime.fromisoformat(max(stamps).replace("Z", "+00:00")).timestamp()
        os.utime(path, (moment, moment))


class SessionDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.project = root / "work" / "my_app"
        self.other = root / "work" / "other-app"
        self.project.mkdir(parents=True)
        self.other.mkdir(parents=True)
        self.claude_home = root / "claude home"
        self.codex_home = root / "codex home"
        self.kimi_home = root / "kimi home"
        self.env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.claude_home), "CODEX_HOME": str(self.codex_home),
                    "KIMI_CODE_HOME": str(self.kimi_home)}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def claude_dir(self, project: Path) -> Path:
        return self.claude_home / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project))

    def run_digest(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), "--cwd", str(self.project), *args],
                              capture_output=True, text=True, encoding="utf-8", env=self.env, timeout=60)

    def listing(self) -> list[dict]:
        result = self.run_digest("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def seed_claude(self) -> None:
        cwd = str(self.project)
        write_jsonl(self.claude_dir(self.project) / "aaaa1111.jsonl", [
            {"type": "ai-title", "aiTitle": "add-export"},
            claude_line("user", "<local-command-caveat>ignore</local-command-caveat>", "2026-10-20T01:00:00Z", cwd),
            claude_line("user", "Add a CSV export.<system-reminder>injected</system-reminder>", "2026-10-20T01:00:01Z", cwd),
            claude_line("assistant", [{"type": "text", "text": "I will read the code first."}], "2026-10-20T01:00:02Z", cwd),
            claude_line("assistant", [{"type": "tool_use", "id": "t1", "name": "Read", "input": {}}], "2026-10-20T01:00:03Z", cwd),
            claude_line("user", [{"type": "tool_result", "tool_use_id": "t1", "content": "SECRET FILE BODY"}], "2026-10-20T01:00:04Z", cwd),
            claude_line("assistant", [{"type": "text", "text": "Export added; tests pass."}], "2026-10-20T01:00:05Z", cwd),
            claude_line("assistant", [{"type": "text", "text": "side task"}], "2026-10-20T01:00:06Z", cwd, isSidechain=True),
            claude_line("user", "meta note", "2026-10-20T01:00:07Z", cwd, isMeta=True),
            claude_line("user", "<command-name>/compact</command-name><command-args>keep the plan</command-args>", "2026-10-20T01:00:08Z", cwd),
            claude_line("user", [{"type": "text", "text": "Summary: export done, docs pending."}], "2026-10-20T01:00:09Z", cwd, isCompactSummary=True),
            claude_line("user", "Now write the docs.", "2026-10-20T01:00:10Z", cwd),
            claude_line("assistant", [{"type": "tool_use", "id": "q1", "name": "AskUserQuestion", "input": {}}], "2026-10-20T01:00:10Z", cwd),
            claude_line("user", [{"type": "tool_result", "tool_use_id": "q1", "content": 'The user answered: "Format?"="Markdown"'}], "2026-10-20T01:00:10Z", cwd),
            claude_line("user", [{"type": "tool_result", "tool_use_id": "q1", "content": 'The user answered: "Format?"="Markdown"'}], "2026-10-20T01:00:10Z", cwd),
            claude_line("assistant", [{"type": "tool_use", "id": "p1", "name": "ExitPlanMode", "input": {}}], "2026-10-20T01:00:10Z", cwd),
            claude_line("user", [{"type": "tool_result", "tool_use_id": "p1", "content": "User has approved your plan.\n\nYour plan has been saved to: C:\\plans\\docs.md\nmore"}], "2026-10-20T01:00:10Z", cwd),
            claude_line("assistant", [{"type": "text", "text": "Docs written."}], "2026-10-20T01:00:11Z", cwd),
            {"type": "partial"},
        ])
        session = self.claude_dir(self.project) / "aaaa1111.jsonl"
        moment = session.stat().st_mtime
        with session.open("a", encoding="utf-8") as handle:
            handle.write('{"type": "user", "message": {"content": "half a li')
        os.utime(session, (moment, moment))
        write_jsonl(self.claude_dir(self.other) / "bbbb2222.jsonl", [
            claude_line("user", "Other project secret plan", "2026-10-20T02:00:00Z", str(self.other)),
        ])

    def seed_codex(self) -> None:
        day = self.codex_home / "sessions" / "2026" / "10" / "21"
        write_jsonl(day / "rollout-a.jsonl", [
            {"type": "session_meta", "payload": {"id": "cccc3333", "cwd": str(self.project).upper() if os.name == "nt" else str(self.project),
                                                 "originator": "codex-tui", "source": "cli"}},
            codex_message("user", "# AGENTS.md instructions for x\n\n<INSTRUCTIONS>rules</INSTRUCTIONS>", "2026-10-21T01:00:00Z"),
            codex_message("user", "<environment_context>cwd</environment_context>", "2026-10-21T01:00:01Z"),
            codex_message("user", "Review the export.", "2026-10-21T01:00:02Z"),
            codex_message("assistant", "Reading the diff.", "2026-10-21T01:00:03Z", "commentary"),
            codex_message("assistant", "One P2 finding.", "2026-10-21T01:00:04Z", "final_answer"),
            {"type": "response_item", "timestamp": "2026-10-21T01:00:05Z", "payload": {"type": "function_call_output", "output": "TOOL NOISE"}},
        ])
        write_jsonl(day / "rollout-b.jsonl", [
            {"type": "session_meta", "payload": {"id": "dddd4444", "cwd": str(self.project), "originator": "codex_exec", "source": "exec"}},
            codex_message("user", "Perform a read-only review.", "2026-10-21T02:00:00Z"),
            codex_message("assistant", "No findings.", "2026-10-21T02:00:01Z"),
        ])
        write_jsonl(day / "rollout-c.jsonl", [
            {"type": "session_meta", "payload": {"id": "eeee5555", "cwd": str(self.other), "originator": "codex-tui", "source": "cli"}},
            codex_message("user", "Other project secret plan", "2026-10-21T03:00:00Z"),
        ])

    def seed_kimi(self) -> None:
        session_id = "session_gggg7777"
        session_dir = self.kimi_home / "sessions" / "wd_my_app_hash" / session_id
        wire = session_dir / "agents" / "main" / "wire.jsonl"
        write_jsonl(wire, [
            {"type": "profile.bind", "systemPrompt": "KIMI SYSTEM PROMPT", "environmentDisclosure": {"cwd": str(self.project)}},
            kimi_message("user", "Review the Kimi export.", "2026-10-22T01:00:00Z"),
            kimi_message("assistant", "Reading the Kimi diff.", "2026-10-22T01:00:01Z"),
            kimi_message("assistant", "One Kimi finding.", "2026-10-22T01:00:02Z", final=True),
            {"type": "agent.message.appended", "time": 1767229203000,
             "message": {"message": {"role": "user", "content": [{"type": "text", "text": "KIMI INJECTED CONTEXT"}]},
                         "meta": {"origin": {"kind": "injection"}}}},
            # Kimi records a loaded skill and a message the user types mid-turn with the same meta;
            # only the skill-loaded element tells them apart, whatever sentence precedes it.
            {"type": "agent.message.appended", "time": 1767229203500,
             "message": {"message": {"role": "user", "content": [{"type": "text",
                                     "text": "KIMI SKILL PREAMBLE\n<skill-loaded name=\"rumo-review\" trigger=\"model-tool\">KIMI SKILL INSTRUCTIONS</skill-loaded>"}]},
                         "meta": {"origin": {"kind": "user", "inTurn": True}}}},
            {"type": "context.apply_compaction", "summary": "Summary: Kimi export done, docs pending.",
             "time": 1767229204000},
            kimi_message("user", "Now write the Kimi docs.", "2026-10-22T01:00:05Z"),
            {"type": "agent.message.appended", "time": 1767229205500,
             "message": {"message": {"role": "user", "content": [{"type": "text", "text": "Keep the header row."}]},
                         "meta": {"origin": {"kind": "user", "inTurn": True}}}},
            kimi_message("assistant", "Kimi docs written.", "2026-10-22T01:00:06Z", final=True),
            {"type": "agent.message.appended", "time": 1767229207000,
             "message": {"message": {"role": "tool", "content": [{"type": "text", "text": "KIMI TOOL NOISE"}]}}},
            {"type": "partial"},
        ])
        state = {"id": session_id, "cwd": str(self.project), "title": "kimi-export"}
        (session_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        write_jsonl(self.kimi_home / "session_index.jsonl", [
            {"sessionId": session_id, "sessionDir": str(session_dir), "workDir": str(self.project)},
            {"sessionId": "session_hhhh8888", "sessionDir": str(self.kimi_home / "missing-other"),
             "workDir": str(self.other)},
        ])

    def test_lists_only_this_projects_sessions_newest_first(self) -> None:
        self.seed_claude()
        self.seed_codex()
        self.seed_kimi()
        rows = self.listing()
        self.assertEqual([row["id"] for row in rows], ["session_gggg7777", "dddd4444", "cccc3333", "aaaa1111"])
        self.assertNotIn("Other project", json.dumps(rows))
        by_id = {row["id"]: row for row in rows}
        self.assertTrue(by_id["dddd4444"]["headless"])
        self.assertFalse(by_id["cccc3333"]["headless"])
        self.assertEqual(by_id["aaaa1111"]["title"], "add-export")
        self.assertEqual(by_id["session_gggg7777"]["title"], "kimi-export")
        self.assertEqual(by_id["session_gggg7777"]["user_turns"], 3)
        self.assertEqual(by_id["aaaa1111"]["first_user"], "Add a CSV export.")
        self.assertEqual(by_id["aaaa1111"]["last_user"], "Now write the docs.")

    def test_claude_timeline_starts_at_the_latest_summary_and_drops_tool_output(self) -> None:
        self.seed_claude()
        result = self.run_digest("show", "aaaa")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        self.assertIn("summary: Summary: export done, docs pending.", out)
        self.assertIn("user: Now write the docs.", out)
        self.assertIn("agent: Docs written.", out)
        self.assertIn("3 earlier entries omitted", out)
        self.assertEqual(out.count('decision: The user answered: "Format?"="Markdown"'), 1)
        self.assertIn("decision: plan approved: C:\\plans\\docs.md", out)
        for noise in ("SECRET FILE BODY", "injected", "side task", "meta note", "ignore"):
            self.assertNotIn(noise, out)

    def test_all_keeps_each_turns_final_reply_only(self) -> None:
        self.seed_claude()
        out = self.run_digest("show", "aaaa", "--all").stdout
        self.assertIn("user: Add a CSV export.", out)
        self.assertIn("agent: Export added; tests pass.", out)
        self.assertNotIn("I will read the code first.", out)
        self.assertIn("user: /compact keep the plan", out)

    def test_codex_timeline_prefers_the_final_answer_and_skips_injected_context(self) -> None:
        self.seed_codex()
        out = self.run_digest("show", "cccc").stdout
        self.assertIn("user: Review the export.", out)
        self.assertIn("agent: One P2 finding.", out)
        for noise in ("Reading the diff.", "AGENTS.md", "environment_context", "TOOL NOISE"):
            self.assertNotIn(noise, out)

    def test_kimi_timeline_starts_at_the_latest_summary_and_drops_internal_records(self) -> None:
        self.seed_kimi()
        result = self.run_digest("show", "session_g")
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        self.assertIn("# kimi session session_gggg7777", out)
        self.assertIn("summary: Summary: Kimi export done, docs pending.", out)
        self.assertIn("user: Now write the Kimi docs.", out)
        self.assertIn("user: Keep the header row.", out)
        self.assertIn("agent: Kimi docs written.", out)
        self.assertNotIn("user: Review the Kimi export.", out)
        for noise in ("KIMI SYSTEM PROMPT", "KIMI PRIVATE THOUGHT", "KIMI INJECTED CONTEXT", "KIMI TOOL NOISE",
                      "KIMI SKILL INSTRUCTIONS", "KIMI SKILL PREAMBLE", "Reading the Kimi diff."):
            self.assertNotIn(noise, out)

    def test_kimi_all_keeps_each_turns_final_reply_only(self) -> None:
        self.seed_kimi()
        out = self.run_digest("show", "session_g", "--all").stdout
        self.assertIn("user: Review the Kimi export.", out)
        self.assertIn("agent: One Kimi finding.", out)
        self.assertNotIn("Reading the Kimi diff.", out)
        self.assertNotIn("KIMI SKILL INSTRUCTIONS", out)
        self.assertNotIn("KIMI SKILL PREAMBLE", out)

    def test_long_messages_and_timelines_are_capped(self) -> None:
        cwd = str(self.project)
        records = []
        for turn in range(30):
            records.append(claude_line("user", f"question {turn} " + "x" * 3000, f"2026-10-20T01:{turn:02d}:00Z", cwd))
            records.append(claude_line("assistant", [{"type": "text", "text": f"answer {turn}"}], f"2026-10-20T01:{turn:02d}:30Z", cwd))
        write_jsonl(self.claude_dir(self.project) / "ffff6666.jsonl", records)
        out = self.run_digest("show", "ffff", "--max-chars", "200", "--budget", "3000").stdout
        self.assertLess(len(out), 4000)
        self.assertIn("answer 29", out)
        self.assertNotIn("question 0 ", out)
        self.assertIn("chars]", out)
        self.assertRegex(out, r"\(\d+ earlier entries omitted")

    def test_another_projects_session_cannot_be_shown(self) -> None:
        self.seed_claude()
        self.seed_codex()
        self.seed_kimi()
        for prefix in ("bbbb", "eeee", "hhhh"):
            result = self.run_digest("show", prefix)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Other project", result.stdout + result.stderr)

    def test_show_bypasses_global_scan_limit_and_list_reports_truncation(self) -> None:
        self.seed_codex()
        day = self.codex_home / "sessions" / "2026" / "10" / "22"
        for index in range(500):
            write_jsonl(day / f"rollout-other-{index}.jsonl", [
                {"type": "session_meta", "payload": {"id": f"other-{index}", "cwd": str(self.other), "source": "cli"}},
                codex_message("user", "Other project private text", f"2026-10-22T{index // 60:02d}:{index % 60:02d}:00Z"),
            ])
        shown = self.run_digest("show", "cccc")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("agent: One P2 finding.", shown.stdout)
        listed = self.run_digest("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertIn("truncated: true", listed.stderr)
        self.assertNotIn("Other project private text", listed.stdout + listed.stderr)

    def test_missing_client_homes_give_an_empty_list(self) -> None:
        self.assertEqual(self.listing(), [])


if __name__ == "__main__":
    unittest.main()
