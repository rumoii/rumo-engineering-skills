from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("summarize_evidence.py")


class SummarizeEvidenceTest(unittest.TestCase):
    def test_renders_normalized_bounded_messages_without_inline_code(self) -> None:
        payload = {
            "interaction_evidence": {
                "selection": {"session_id": "session-1", "anchor_turn": "turn-1"},
                "turns": [
                    {
                        "turn_id": "turn-1",
                        "status": "completed",
                        "tool_calls": 2,
                        "tool_failure_signals": 1,
                        "user_messages": [
                            {"source_line": 7, "text": "first\n  second\\path", "truncated": False}
                        ],
                        "assistant_messages": [
                            {"source_line": 9, "text": "abcdefgh", "truncated": False}
                        ],
                    }
                ],
            }
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "case.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--max-chars", "5", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        self.assertIn("USER @7: first [truncated]", completed.stdout)
        self.assertIn("ASSISTANT @9: abcde [truncated]", completed.stdout)

    def test_rejects_non_evidence_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid.json"
            path.write_text("{}", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("missing interaction_evidence.turns", completed.stderr)


if __name__ == "__main__":
    unittest.main()
