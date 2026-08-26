from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path(__file__).with_name("analyze_sessions.py")


class AnalyzeSessionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.codex_home = Path(self.temp_dir.name) / ".codex"
        session_dir = self.codex_home / "sessions" / "2025" / "01" / "01"
        session_dir.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        self.now = now
        (self.codex_home / "history.jsonl").write_text(
            "\n".join(
                json.dumps({"session_id": "session-1", "ts": now.timestamp() + index, "text": text})
                for index, text in enumerate(("history one", "history two", "history three"))
            )
            + "\n", encoding="utf-8"
        )
        records = [
            {"timestamp": "2025-01-01T00:00:00Z", "type": "session_meta", "payload": {"id": "session-1", "timestamp": "2025-01-01T00:00:00Z", "cwd": "/workspace/example-app", "git": {"branch": "main"}}},
            self.task_started("turn-1", now),
            self.user_response("INJECTED-CONTROL-CONTENT", now),
            self.turn_context("turn-1", now),
            self.user_response("real user turn one", now),
            self.user_response("PLATFORM-SKILL-INJECTION", now),
            self.user_event("duplicate older-format message", now),
            self.assistant_response("assistant turn one", now),
            self.tool_call("shell_command", now),
            self.tool_output("Exit code: 1", now),
            self.task_complete("turn-1", now, 1200),
            self.task_started("turn-2", now + timedelta(seconds=1)),
            self.turn_context("turn-2", now + timedelta(seconds=1)),
            self.user_event("real user turn two", now + timedelta(seconds=1)),
            self.assistant_response("assistant turn two", now + timedelta(seconds=1)),
            self.task_complete("turn-2", now + timedelta(seconds=1), 800),
            self.task_started("turn-3", now + timedelta(seconds=2)),
            self.turn_context("turn-3", now + timedelta(seconds=2)),
            self.user_response("real user turn three", now + timedelta(seconds=2)),
            self.assistant_response("assistant turn three", now + timedelta(seconds=2)),
            self.task_complete("turn-3", now + timedelta(seconds=2), 600),
        ]
        self.session_path = session_dir / "rollout-session-1.jsonl"
        self.session_path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @staticmethod
    def timestamp(value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")

    def task_started(self, turn_id: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "event_msg", "payload": {"type": "task_started", "turn_id": turn_id, "started_at": self.timestamp(timestamp)}}

    def turn_context(self, turn_id: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "turn_context", "payload": {"turn_id": turn_id, "model": "gpt-test", "effort": "high"}}

    def user_response(self, text: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}

    def user_event(self, text: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "event_msg", "payload": {"type": "user_message", "message": text}}

    def assistant_response(self, text: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "response_item", "payload": {"type": "message", "role": "assistant", "phase": "final_answer", "content": [{"type": "output_text", "text": text}]}}

    def tool_call(self, name: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "response_item", "payload": {"type": "function_call", "name": name}}

    def tool_output(self, output: str, timestamp: datetime) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "response_item", "payload": {"type": "function_call_output", "output": output}}

    def task_complete(self, turn_id: str, timestamp: datetime, duration_ms: int) -> dict:
        return {"timestamp": self.timestamp(timestamp), "type": "event_msg", "payload": {"type": "task_complete", "turn_id": turn_id, "duration_ms": duration_ms}}

    def run_script(self, *extra: str) -> dict:
        completed = subprocess.run([sys.executable, str(SCRIPT), "--codex-home", str(self.codex_home), "--all-time", *extra], check=True, capture_output=True, text=True)
        return json.loads(completed.stdout)

    def run_raw(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), "--codex-home", str(self.codex_home), *extra], check=False, capture_output=True, text=True)

    def test_default_inventory_has_metrics_and_no_message_text(self) -> None:
        result = self.run_script()
        self.assertEqual(result["totals"]["history_messages"], 3)
        self.assertEqual(result["totals"]["structured_user_messages"], 3)
        self.assertEqual(result["totals"]["tool_calls"], 1)
        self.assertEqual(result["totals"]["tool_failure_signals"], 1)
        self.assertNotIn("interaction_evidence", result)
        encoded = json.dumps(result)
        self.assertNotIn("real user turn", encoded)
        self.assertNotIn("assistant turn", encoded)
        self.assertNotIn("INJECTED-CONTROL-CONTENT", encoded)
        self.assertNotIn("PLATFORM-SKILL-INJECTION", encoded)

    def test_lifecycle_candidate_index_is_text_free_and_one_per_session(self) -> None:
        result = self.run_script("--candidate-index-top", "10")
        candidates = result["lifecycle_candidate_index"]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["session_id"], "session-1")
        self.assertEqual(candidates[0]["turn_id"], "turn-3")
        self.assertEqual(candidates[0]["cwd"], "/workspace/example-app")
        self.assertFalse(any("text" in row for row in candidates))

    def test_lifecycle_candidate_index_excludes_active_sessions(self) -> None:
        with self.session_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(self.task_started("turn-active", self.now)) + "\n")
        result = self.run_script()
        self.assertEqual(result["lifecycle_candidate_index"], [])

    def test_structural_user_selection_excludes_injection_and_prefers_response_item(self) -> None:
        result = self.run_script("--session-id", "session-1", "--anchor-turn", "turn-1", "--turn-before", "0", "--turn-after", "0", "--include-interaction-evidence")
        turn = result["interaction_evidence"]["turns"][0]
        self.assertEqual(turn["user_message_source"], "response_item")
        self.assertEqual([item["text"] for item in turn["user_messages"]], ["real user turn one"])

    def test_selected_window_is_adjacent_and_bounded(self) -> None:
        result = self.run_script("--session-id", "session-1", "--anchor-turn", "turn-2", "--turn-before", "1", "--turn-after", "1", "--max-message-chars", "8", "--include-tool-details", "--include-interaction-evidence")
        turns = result["interaction_evidence"]["turns"]
        self.assertEqual([turn["turn_id"] for turn in turns], ["turn-1", "turn-2", "turn-3"])
        self.assertEqual(turns[0]["user_messages"][0]["text"], "real use")
        self.assertTrue(turns[0]["user_messages"][0]["truncated"])
        self.assertEqual(turns[0]["tool_outputs"][0]["output"], "Exit cod")
        self.assertTrue(turns[0]["tool_outputs"][0]["failed"])

    def test_interaction_evidence_requires_exact_selection(self) -> None:
        completed = self.run_raw("--all-time", "--include-interaction-evidence")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires exactly one --session-id and --anchor-turn", completed.stderr)

    def test_evidence_only_omits_repeated_inventory(self) -> None:
        result = self.run_script(
            "--session-id", "session-1", "--anchor-turn", "turn-2",
            "--include-interaction-evidence", "--evidence-only",
        )
        self.assertEqual(
            set(result),
            {"generated_at", "scope", "interaction_evidence", "data_quality"},
        )
        self.assertNotIn("turn_index", result)

    def test_evidence_only_requires_interaction_evidence(self) -> None:
        completed = self.run_raw("--all-time", "--evidence-only")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("requires --include-interaction-evidence", completed.stderr)

    def test_filters_project(self) -> None:
        result = self.run_script("--project", "example-app")
        self.assertEqual(result["totals"]["session_files"], 1)

    def test_rejects_invalid_explicit_date(self) -> None:
        completed = self.run_raw("--since", "not-a-date")
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("invalid --since value", completed.stderr)

    def test_until_date_includes_the_full_day(self) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        completed = self.run_raw("--since", today, "--until", today)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["totals"]["session_files"], 1)

    def test_recent_history_keeps_an_older_session_file_in_scope(self) -> None:
        completed = self.run_raw()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["totals"]["history_sessions"], 1)
        self.assertEqual(payload["totals"]["session_files"], 1)

    def test_ignores_nested_session_metadata(self) -> None:
        with self.session_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"type": "session_meta", "payload": {"id": "nested-session", "session_id": "session-1"}}) + "\n")
        result = self.run_script()
        self.assertEqual(result["session_index"][0]["session_id"], "session-1")


if __name__ == "__main__":
    unittest.main()
