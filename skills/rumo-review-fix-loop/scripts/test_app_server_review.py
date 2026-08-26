#!/usr/bin/env python3
from __future__ import annotations

import queue
import sys
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import importlib.util


SCRIPT_PATH = Path(__file__).with_name("app_server_review.py")
SPEC = importlib.util.spec_from_file_location("app_server_review", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
app_server_review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = app_server_review
SPEC.loader.exec_module(app_server_review)


def turn(turn_id: str, status: str, items: list[dict]) -> dict:
    return {
        "id": turn_id,
        "status": status,
        "itemsView": "full",
        "completedAt": 1 if status == "completed" else None,
        "items": items,
    }


def thread_response(*turns: dict) -> dict:
    return {"thread": {"status": {"type": "active"}, "turns": list(turns)}}


class FakeClient:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = queue.Queue()
        for response in responses:
            self.responses.put(response)
        self.notifications: queue.Queue[dict] = queue.Queue()
        self.proc = SimpleNamespace(poll=lambda: None)

    def request(self, method: str, params: dict | None = None) -> dict:
        if method != "thread/read":
            raise AssertionError(f"unexpected method: {method}")
        try:
            return self.responses.get_nowait()
        except queue.Empty:
            return thread_response(turn("review-turn", "inProgress", [{"id": "item-1", "type": "userMessage"}]))


class ExtractPollSnapshotTest(unittest.TestCase):
    def test_extracts_final_review_from_exact_turn(self) -> None:
        response = thread_response(
            turn("review-turn", "completed", [{"id": "item-1", "type": "exitedReviewMode", "review": "No findings."}])
        )

        snapshot = app_server_review.extract_poll_snapshot(response, "review-turn")

        self.assertEqual(snapshot.review, "No findings.")
        self.assertEqual(snapshot.final_turn["id"], "review-turn")
        self.assertTrue(snapshot.diagnostics["exactTurnMatched"])

    def test_uses_latest_turn_when_review_start_turn_id_is_not_in_history(self) -> None:
        response = thread_response(
            turn("old-turn", "completed", [{"id": "item-old", "type": "agentMessage", "text": "old"}]),
            turn("actual-review-turn", "inProgress", [{"id": "item-new", "type": "agentMessage", "text": "running"}]),
        )

        snapshot = app_server_review.extract_poll_snapshot(response, "review-start-turn")

        self.assertIsNone(snapshot.review)
        self.assertIsNone(snapshot.final_turn)
        self.assertFalse(snapshot.diagnostics["exactTurnMatched"])
        self.assertEqual(snapshot.diagnostics["polledTurnStatus"], "inProgress")

    def test_marks_latest_fallback_turn_final_only_when_latest_is_done(self) -> None:
        response = thread_response(
            turn("old-turn", "completed", [{"id": "item-old", "type": "agentMessage", "text": "old"}]),
            turn("actual-review-turn", "completed", [{"id": "item-new", "type": "agentMessage", "text": "done"}]),
        )

        snapshot = app_server_review.extract_poll_snapshot(response, "review-start-turn")

        self.assertEqual(snapshot.final_turn["id"], "actual-review-turn")
        self.assertFalse(snapshot.diagnostics["exactTurnMatched"])


class WaitForReviewTest(unittest.TestCase):
    def test_recovers_review_by_polling_when_notifications_do_not_complete(self) -> None:
        client = FakeClient(
            [
                thread_response(turn("review-turn", "inProgress", [{"id": "item-1", "type": "userMessage"}])),
                thread_response(
                    turn(
                        "review-turn",
                        "completed",
                        [{"id": "item-2", "type": "exitedReviewMode", "review": "No blocking findings."}],
                    )
                ),
            ]
        )

        review, final_turn = app_server_review.wait_for_review(
            client,
            "thread-1",
            "review-turn",
            timeout=5,
            idle_timeout=5,
            min_wait_before_idle=0,
            poll_interval=1,
            progress=False,
            progress_interval=1,
            show_intermediate=False,
            intermediate_max_chars=4000,
        )

        self.assertEqual(review, "No blocking findings.")
        self.assertEqual(final_turn["status"], "completed")

    def test_noise_notifications_do_not_reset_idle_timer(self) -> None:
        client = FakeClient([thread_response(turn("review-turn", "inProgress", [{"id": "item-1", "type": "userMessage"}]))])
        for _ in range(20):
            client.notifications.put({"method": "model/verification", "params": {"status": "ok"}})

        started = time.monotonic()
        with patch.object(app_server_review, "print_progress", lambda _message: None):
            with self.assertRaises(app_server_review.ReviewWaitError) as raised:
                app_server_review.wait_for_review(
                    client,
                    "thread-1",
                    "review-turn",
                    timeout=5,
                    idle_timeout=1,
                    min_wait_before_idle=0,
                    poll_interval=1,
                    progress=True,
                    progress_interval=1,
                    show_intermediate=False,
                    intermediate_max_chars=4000,
                )

        self.assertLess(time.monotonic() - started, 3)
        self.assertIn("no app-server review progress", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
