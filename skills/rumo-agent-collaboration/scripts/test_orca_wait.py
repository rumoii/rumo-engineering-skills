#!/usr/bin/env python3
"""Tests for orca_wait.py against scripted Orca replies and a fake orca program; Orca is never called."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "orca_wait.py"

spec = importlib.util.spec_from_file_location("orca_wait", SCRIPT)
orca_wait = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orca_wait)


def screen(*lines: str, status: str = "running") -> dict:
    return {"ok": True, "result": {"terminal": {"handle": "term_x", "status": status, "tail": list(lines)}}}


def failure(code: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": code}}


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class Orca:
    """Answers each `terminal read` with the next scripted reply and records every call."""

    def __init__(self, reads: list, waits: list | None = None, on_read=None) -> None:
        self.reads, self.waits, self.on_read, self.calls = list(reads), list(waits or []), on_read, []

    def __call__(self, args: list[str]) -> dict | None:
        self.calls.append(args)
        if args[:2] == ["terminal", "wait"]:
            return self.waits.pop(0)
        if self.on_read:
            self.on_read(len([c for c in self.calls if c[:2] == ["terminal", "read"]]))
        return self.reads.pop(0) if len(self.reads) > 1 else self.reads[0]


class WaitTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.report = Path(self.tmp.name) / "report.md"
        self.clock = Clock()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_wait(self, orca: Orca, report: Path | None = None, marker: str | None = None,
                 idle: float = 200, lost: float = 600, since: float | None = None) -> tuple[int, str]:
        return orca_wait.wait(lambda: orca_wait.observe(orca, "term_x"), report, marker, idle=idle, interval=30,
                              lost=lost, since=time.time() if since is None else since,
                              clock=self.clock, sleep=self.clock.sleep)

    def write_report(self, mtime: float | None = None) -> None:
        self.report.write_text("# report\n", encoding="utf-8")
        if mtime is not None:
            os.utime(self.report, (mtime, mtime))

    def test_done_needs_both_report_and_marker(self) -> None:
        # The agent quotes the marker while reading its brief; only the report written later ends the wait.
        def on_read(count: int) -> None:
            if count == 3:
                self.write_report(time.time() + 5)
        orca = Orca([screen("brief says: reply 1B 完成"), screen("working"), screen("1B 完成")], on_read=on_read)
        code, line = self.run_wait(orca, self.report, "1B 完成")
        self.assertEqual(code, orca_wait.EXIT_DONE)
        self.assertIn(str(self.report), line)
        self.assertEqual(len([c for c in orca.calls if c[:2] == ["terminal", "read"]]), 3)

    def test_marker_without_report_is_not_done(self) -> None:
        code, _ = self.run_wait(Orca([screen("1B 完成")]), self.report, "1B 完成")
        self.assertEqual(code, orca_wait.EXIT_IDLE)

    def test_report_written_before_the_wait_is_not_done(self) -> None:
        self.write_report(time.time() - 3600)
        code, _ = self.run_wait(Orca([screen("1B 完成")]), self.report, "1B 完成")
        self.assertEqual(code, orca_wait.EXIT_IDLE)

    def test_report_alone_counts_when_no_marker_is_given(self) -> None:
        self.write_report(time.time() + 5)
        code, _ = self.run_wait(Orca([screen("anything")]), self.report)
        self.assertEqual(code, orca_wait.EXIT_DONE)

    def test_idle_after_unchanged_screen_and_changes_reset_the_timer(self) -> None:
        reads = [screen("a")] * 5 + [screen("b")] + [screen("b")] * 10
        code, line = self.run_wait(Orca(reads), idle=200)
        self.assertEqual(code, orca_wait.EXIT_IDLE)
        # "b" first appeared after 5 polls (150 s); idle fires 200 s after that, not 200 s after the start.
        self.assertGreaterEqual(self.clock.now - 1000.0, 150 + 200)
        self.assertIn("200", line)

    def test_stale_handle_is_stopped(self) -> None:
        code, line = self.run_wait(Orca([failure("terminal_handle_stale")]))
        self.assertEqual(code, orca_wait.EXIT_STOPPED)
        self.assertIn("terminal list", line)

    def test_non_running_status_is_stopped_only_when_orca_confirms_exit(self) -> None:
        orca = Orca([screen("x", status="unknown-state"), screen("x", status="exited")],
                    waits=[failure("timeout"), {"ok": True, "result": {}}])
        code, _ = self.run_wait(orca)
        self.assertEqual(code, orca_wait.EXIT_STOPPED)
        self.assertEqual([c[:2] for c in orca.calls].count(["terminal", "wait"]), 2)

    def test_read_failures_are_retried_until_the_lost_deadline(self) -> None:
        orca = Orca([None, failure("transport"), None, screen("back")])
        code, _ = self.run_wait(orca, idle=200, lost=600)
        self.assertEqual(code, orca_wait.EXIT_IDLE)  # recovered after 90 s of failures, then went idle

        code, line = self.run_wait(Orca([None]), lost=600)
        self.assertEqual(code, orca_wait.EXIT_LOST)
        self.assertIn("600", line)

    def test_never_sends_input(self) -> None:
        orca = Orca([screen("x", status="other")], waits=[failure("timeout")] * 20)
        self.run_wait(orca)
        self.assertTrue(orca.calls)
        self.assertTrue(all(c[1] in ("read", "wait") for c in orca.calls), orca.calls)


FAKE_ORCA = textwrap.dedent(
    r'''
    import json, os, sys
    from pathlib import Path
    state = Path(os.environ["FAKE_STATE"])
    count = int(state.read_text()) + 1 if state.exists() else 1
    state.write_text(str(count))
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(sys.argv[1:]) + "\n")
    if count == 2:
        Path(os.environ["FAKE_REPORT"]).write_text("done", encoding="utf-8")
    tail = ["working"] if count < 2 else ["1B 完成"]
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps({"ok": True, "result": {"terminal": {"status": "running", "tail": tail}}}, ensure_ascii=False))
    '''
)


class CommandLineTest(unittest.TestCase):
    def test_runs_the_orca_program_and_reports_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake = root / "orca.py"
            fake.write_text(FAKE_ORCA, encoding="utf-8")
            env = {**os.environ, "FAKE_STATE": str(root / "state"), "FAKE_LOG": str(root / "log"),
                   "FAKE_REPORT": str(root / "report.md"), "PYTHONIOENCODING": "utf-8"}
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--terminal", "term_x", "--report", str(root / "report.md"),
                 "--marker", "1B 完成", "--interval", "0.05", "--orca", str(fake)],
                capture_output=True, text=True, encoding="utf-8", env=env, timeout=30)
            self.assertEqual(proc.returncode, orca_wait.EXIT_DONE, proc.stdout + proc.stderr)
            self.assertIn("done", proc.stdout)
            calls = [json.loads(line) for line in (root / "log").read_text(encoding="utf-8").splitlines()]
            self.assertTrue(all(c[:4] == ["terminal", "read", "--terminal", "term_x"] and "--json" in c for c in calls), calls)

    def test_rejects_bad_arguments(self) -> None:
        for extra in (["--idle", "0"], ["--interval", "-1"], ["--lost", "nan"], ["--orca", "missing-orca.py"]):
            proc = subprocess.run([sys.executable, str(SCRIPT), "--terminal", "term_x", *extra],
                                  capture_output=True, text=True, encoding="utf-8", timeout=30)
            self.assertEqual(proc.returncode, orca_wait.EXIT_USAGE, extra)


if __name__ == "__main__":
    unittest.main()
