#!/usr/bin/env python3
"""Tests for agent_run.py and the bundled adapters against a fake CLI; no model is called."""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "agent_run.py"
FIXTURES = HERE / "fixtures"
PROMPT = 'Check "this"; rm -rf / & $(whoami) `id` 中文提示 %PATH%\nsecond line\n'

spec = importlib.util.spec_from_file_location("agent_run", SCRIPT)
agent_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_run)
BUNDLED = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(agent_run.BUNDLED_ADAPTERS.glob("*.json"))}

# How each bundled adapter's CLI prints events; the fake CLI below speaks each dialect.
DIALECT = {
    "codex": "codex", "claude": "claude", "qwen": "claude", "grok": "claude", "cursor": "claude",
    "pi": "pi", "gemini": "gemini", "opencode": "opencode",
    "copilot": "copilot", "aider": "text", "cline": "cline", "goose": "goose",
}

# FAKE_DIALECT picks the event format, FAKE_MODE the behavior; FAKE_LOG receives argv, prompt, and env per call.
FAKE = textwrap.dedent(
    r'''
    import json, os, sys, time, subprocess
    sys.stdout.reconfigure(encoding="utf-8")  # real CLIs emit UTF-8 regardless of the console code page
    dialect, mode, argv = os.environ["FAKE_DIALECT"], os.environ.get("FAKE_MODE", "ok"), sys.argv[1:]
    cli = os.environ.get("FAKE_CLI", "claude" if dialect == "claude" else dialect)
    flags = {
        "codex": "-c --config --json --sandbox --cd --model",
        "claude": "-p --print --output-format --verbose --permission-mode --session-id --resume --model --name",
        "pi": "-p --print --mode --tools --session-id --session --model --no-mcp --no-extensions --name",
        "qwen": "-o --output-format --approval-mode --session-id --resume --model --prompt-interactive",
        "grok": "-s --session-id --prompt-file --output-format --no-subagents --permission-mode --resume --model",
        "cursor": "-p --print --output-format --mode --sandbox --trust --resume --model",
        "gemini": "-o --output-format --approval-mode --resume --model",
        "opencode": "--format --session --model --title",
        "copilot": "--output-format --available-tools --deny-tool --allow-tool --session-id --model --no-auto-update",
        "cline": "--json --plan --model",
        "goose": "--instructions --output-format --no-session --model",
        "aider": "--message-file --chat-mode --model --no-auto-commits --no-dirty-commits --no-auto-lint --no-auto-test "
                 "--no-suggest-shell-commands --no-gitignore --no-check-update --no-show-release-notes --no-pretty "
                 "--input-history-file --chat-history-file",
    }
    FLAGS = flags.get(cli, flags["claude"])
    if argv == ["--version"]:
        print("fake 9.9.9"); sys.exit(0)
    if "--help" in argv:
        if cli == "codex" and argv not in (["exec", "--help"], ["exec", "resume", "--help"]):
            sys.exit(2)
        if cli in ("opencode", "goose") and argv != ["run", "--help"]:
            sys.exit(2)
        print("" if mode == "nohelp" else FLAGS); sys.exit(9 if mode == "badhelp" else 0)
    if "--fake-interactive" in argv:
        with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
            log.write(json.dumps({"argv": argv, "cwd": os.getcwd(), "interactive": True}, ensure_ascii=False) + "\n")
        sys.exit(0)
    for token in argv:
        if token.startswith("-") and token != "-" and token.split("=", 1)[0] not in FLAGS.split():
            sys.stderr.write("unknown option: " + token); sys.exit(2)
    choices = {"--sandbox": ("read-only", "workspace-write", "enabled"), "--permission-mode": ("plan", "acceptEdits"),
               "--approval-mode": ("plan", "auto-edit"), "--chat-mode": ("ask", "code")}
    for flag, allowed in choices.items():
        if flag in argv and argv[argv.index(flag) + 1] not in allowed:
            sys.stderr.write("invalid value: " + flag); sys.exit(2)
    if mode == "unread":
        time.sleep(120)
    if "--prompt-file" in argv or "--message-file" in argv:
        flag = "--prompt-file" if "--prompt-file" in argv else "--message-file"
        prompt = open(argv[argv.index(flag) + 1], encoding="utf-8").read()
    else:
        prompt = sys.stdin.buffer.read().decode("utf-8")
    with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"argv": argv, "prompt": prompt, "cwd": os.getcwd(),
                              "opencode_config": os.environ.get("OPENCODE_CONFIG_CONTENT"),
                              "goose_mode": os.environ.get("GOOSE_MODE")}, ensure_ascii=False) + "\n")
    def emit(event):
        print(json.dumps(event, ensure_ascii=False), flush=True)
    def after(*flags):
        for flag in flags:
            if flag in argv:
                return argv[argv.index(flag) + 1]
        return None
    reply = "done: " + prompt.splitlines()[0]
    if dialect == "text":
        print(reply); sys.exit(0)
    if dialect == "codex":
        session = argv[-2] if "resume" in argv else "thread-1"  # resume argv ends with <id> -
        emit({"type": "thread.started", "thread_id": session})
    elif dialect == "claude":
        session = after("--session-id", "-s", "--resume") or "chat-1"
        emit({"type": "system", "subtype": "init", "session_id": session})
    elif dialect == "pi":
        session = after("--session-id")
        emit({"type": "session", "id": session})
        emit({"type": "message_end", "message": {"role": "user", "content": [{"type": "text", "text": prompt}]}})
        emit({"type": "tool_execution_start", "toolName": "read", "args": {"path": "README.md"}})
    elif dialect == "gemini":
        session = after("--resume") or "gem-1"
        emit({"type": "init", "session_id": session})
    elif dialect == "opencode":
        session = after("--session") or "ses_1"
        emit({"type": "step_start", "sessionID": session})
    elif dialect == "copilot":
        session = after("--session-id")
        emit({"type": "session.start", "data": {"sessionId": session}})
    if mode == "tree":
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
        open(os.environ["FAKE_CHILD_PID"], "w").write(str(child.pid))
    if mode in ("hang", "tree"):
        time.sleep(120)
    if mode == "slow":
        time.sleep(3)
    if mode == "malformed":
        print("not json {", flush=True); sys.exit(0)
    if mode == "fail":
        sys.stderr.write("auth failed\n"); sys.exit(4)
    if dialect == "codex":
        emit({"type": "item.completed", "item": {"type": "agent_message", "text": reply}})
        emit({"type": "turn.completed"})
    elif dialect == "claude":
        emit({"type": "assistant", "session_id": session, "message": {"content": [{"type": "text", "text": reply}]}})
        emit({"type": "result", "subtype": "success", "is_error": False, "result": reply, "session_id": session})
    elif dialect == "pi":
        emit({"type": "message_end", "message": {"role": "assistant", "content": [{"type": "text", "text": reply}]}})
    elif dialect == "gemini":
        half = len(reply) // 2
        emit({"type": "message", "role": "assistant", "content": reply[:half], "delta": True})
        emit({"type": "message", "role": "assistant", "content": reply[half:], "delta": True})
        emit({"type": "result", "status": "success"})
    elif dialect == "opencode":
        emit({"type": "text", "sessionID": session, "part": {"type": "text", "text": reply}})
        emit({"type": "step_finish", "sessionID": session})
    elif dialect == "copilot":
        emit({"type": "assistant.message", "data": {"content": reply}})
        emit({"type": "session.idle", "data": {}})
    elif dialect == "cline":
        emit({"type": "run_result", "finishReason": "completed", "text": reply})
    elif dialect == "goose":
        emit({"type": "message", "message": {"role": "assistant", "content": [{"type": "text", "text": reply}]}})
        emit({"type": "complete", "total_tokens": 1})
    '''
)


class Harness(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "运行 目录"
        self.cwd = root / "工作 区"
        self.cwd.mkdir(parents=True)
        self.runs = root / "runs"
        self.user_adapters = root / "adapters"
        self.fake = root / "fake_cli.py"
        self.fake.write_text(FAKE, encoding="utf-8")
        self.log = root / "fake.log"
        self.prompt = root / "提示.md"
        self.prompt.write_text(PROMPT, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def env(self, dialect: str, mode: str = "ok") -> dict:
        env = {**os.environ, "FAKE_DIALECT": dialect, "FAKE_MODE": mode, "FAKE_LOG": str(self.log)}
        env["RUMO_AGENT_ADAPTERS_DIR"] = str(self.user_adapters)
        env.pop("RUMO_AGENT_RUNS_DIR", None)
        return env

    def run_script(self, *args: str, dialect: str = "codex", mode: str = "ok", env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
        if args and args[0] in ("start", "resume") and "--window" not in args:
            args = (*args, "--no-window")
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args], env=env or self.env(dialect, mode), cwd=cwd, capture_output=True, timeout=120,
        )

    def start(self, cli: str = "codex", mode: str = "ok", access: str = "read-only", *extra: str) -> subprocess.CompletedProcess:
        return self.run_script(
            "start", cli, "--cwd", str(self.cwd), "--prompt-file", str(self.prompt), "--access", access,
            "--executable", str(self.fake), "--runs-dir", str(self.runs), *extra,
            env={**self.env(DIALECT.get(cli, "claude"), mode), "FAKE_CLI": cli},
        )

    def resume(self, run_id: str, cli: str = "codex") -> subprocess.CompletedProcess:
        return self.run_script("resume", run_id, "--prompt-file", str(self.prompt), "--runs-dir", str(self.runs),
                               env={**self.env(DIALECT.get(cli, "claude")), "FAKE_CLI": cli})

    def calls(self) -> list[dict]:
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def only_run(self) -> Path:
        runs = list(self.runs.iterdir())
        self.assertEqual(len(runs), 1)
        return runs[0]

    def meta(self, run_dir: Path) -> dict:
        return json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))

    def write_adapter(self, adapter: dict) -> None:
        self.user_adapters.mkdir(exist_ok=True)
        (self.user_adapters / f"{adapter['name']}.json").write_text(json.dumps(adapter), encoding="utf-8")


class BundledAdapterTest(unittest.TestCase):
    def test_every_bundled_adapter_is_valid_and_offers_read_only(self) -> None:
        self.assertEqual(set(BUNDLED), set(DIALECT))
        for name, adapter in BUNDLED.items():
            with self.subTest(cli=name):
                self.assertEqual(agent_run.validate_adapter(adapter), [])
                self.assertIn("read-only", adapter["access"])
                self.assertIn(adapter["prompt"], ("stdin", "file"))

    def test_unverified_status_is_not_promoted_when_development_is_declared(self) -> None:
        for name, adapter in BUNDLED.items():
            if adapter.get("verified") is None:
                with self.subTest(cli=name):
                    self.assertIn("read-only", adapter["access"])
                    if name in ("copilot", "aider", "cline", "goose"):
                        self.assertIn("native-write", adapter["access"])

    def test_documented_adapters_offer_distinct_development_modes(self) -> None:
        for name in ("copilot", "aider", "cline", "goose"):
            with self.subTest(cli=name):
                adapter = BUNDLED[name]
                ro = agent_run.render(adapter, "start", "read-only", "/w", None, "sid", "/p.md")
                rw = agent_run.render(adapter, "start", "native-write", "/w", None, "sid", "/p.md")
                self.assertNotEqual((ro, adapter.get("access_env", {}).get("read-only")),
                                    (rw, adapter.get("access_env", {}).get("native-write")))
                self.assertIsNone(adapter["verified"])
                self.assertIn("https://", adapter["notes"])

    def test_access_levels_render_each_cli_limit(self) -> None:
        for cli, access, expected in (
            ("codex", "read-only", ["--sandbox", "read-only"]),
            ("codex", "workspace-write", ["--sandbox", "workspace-write"]),
            ("claude", "read-only", ["--permission-mode", "plan"]),
            ("claude", "workspace-write", ["--permission-mode", "acceptEdits"]),
            ("pi", "read-only", ["--tools", "read,grep,find,ls"]),
            ("pi", "workspace-write", ["--tools", "read,grep,find,ls,edit,write"]),
            ("qwen", "read-only", ["--approval-mode", "plan"]),
            ("qwen", "workspace-write", ["--approval-mode", "auto-edit"]),
            ("grok", "read-only", ["--permission-mode", "plan"]),
            ("cursor", "read-only", ["--mode", "ask", "--sandbox", "enabled"]),
            ("gemini", "read-only", ["--approval-mode", "plan"]),
        ):
            with self.subTest(cli=cli, access=access):
                argv = agent_run.render(BUNDLED[cli], "start", access, "/w", None, "sid", "/p.md")
                index = argv.index(expected[0])
                self.assertEqual(argv[index:index + len(expected)], expected)

    def test_levels_an_adapter_does_not_offer_are_refused(self) -> None:
        for cli in ("grok", "cursor", "gemini", "opencode"):
            with self.subTest(cli=cli), self.assertRaises(agent_run.Refused):
                agent_run.render(BUNDLED[cli], "start", "workspace-write", "/w", None, "sid", "/p.md")

    def test_model_flag_appears_only_when_a_model_is_named(self) -> None:
        for name, adapter in BUNDLED.items():
            with self.subTest(cli=name):
                without = agent_run.render(adapter, "start", "read-only", "/w", None, "sid", "/p.md")
                named = agent_run.render(adapter, "start", "read-only", "/w", "provider/m-1", "sid", "/p.md")
                self.assertNotIn("provider/m-1", without)
                self.assertIn("provider/m-1", named)

    def test_codex_resume_keeps_the_sandbox_level(self) -> None:
        argv = agent_run.render(BUNDLED["codex"], "resume", "read-only", "/w", None, "thread-1", None)
        self.assertIn('sandbox_mode="read-only"', argv)
        self.assertEqual(argv[-2:], ["thread-1", "-"])

    def test_pi_disables_mcp_and_extensions_on_both_turns(self) -> None:
        for kind in ("start", "resume"):
            argv = agent_run.render(BUNDLED["pi"], kind, "read-only", "/w", None, "sid", None)
            self.assertIn("--no-mcp", argv)
            self.assertIn("--no-extensions", argv)

    def test_access_environment_only_changes_the_child(self) -> None:
        adapter = BUNDLED["goose"]
        with patch.dict(os.environ, {"GOOSE_MODE": "auto"}):
            self.assertEqual(agent_run.child_environment(adapter, "read-only")["GOOSE_MODE"], "chat")
            self.assertEqual(agent_run.child_environment(adapter, "native-write")["GOOSE_MODE"], "approve")
            self.assertEqual(os.environ["GOOSE_MODE"], "auto")

    def test_opencode_read_only_comes_from_a_deny_by_default_config(self) -> None:
        config = json.loads(BUNDLED["opencode"]["env"]["OPENCODE_CONFIG_CONTENT"])
        self.assertEqual(config["permission"]["*"], "deny")
        self.assertEqual(config["share"], "disabled")
        self.assertNotIn("edit", config["permission"])
        self.assertNotIn("shell", config["permission"])


class ParserFixtureTest(unittest.TestCase):
    """qwen and grok-error come from live runs; the others are constructed from each CLI's known or documented format."""

    CASES = (
        ("codex", "codex.jsonl", None, {"session": "thread-abc", "final": "final answer", "error": None}),
        ("codex", "codex-failed.jsonl", None, {"session": "thread-abc", "final": None, "error": "usage limit reached"}),
        ("claude", "claude.jsonl", "pre", {"session": "pre", "final": "final answer", "error": None}),
        ("pi", "pi.jsonl", "pre", {"session": "pre", "final": "final answer", "error": None}),
        ("qwen", "qwen.jsonl", "pre", {"session": "pre", "final": "OK", "error": None}),
        ("cursor", "cursor.jsonl", None, {"session": "chat-1", "final": "final answer", "error": None}),
        ("gemini", "gemini.jsonl", None, {"session": "gem-1", "final": "final answer", "error": None}),
        ("opencode", "opencode.jsonl", None, {"session": "ses_1", "final": "final answer", "error": None}),
        ("copilot", "copilot.jsonl", "pre", {"session": "pre", "final": "final answer", "error": None}),
        ("cline", "cline.jsonl", None, {"session": None, "final": "final answer", "error": None}),
        ("goose", "goose.jsonl", None, {"session": None, "final": "final answer", "error": None}),
    )

    def events(self, name: str) -> list[dict]:
        return [json.loads(line) for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines()]

    def test_fixtures_parse_to_the_expected_reply_session_and_error(self) -> None:
        for cli, fixture, preassigned, expected in self.CASES:
            with self.subTest(cli=cli, fixture=fixture):
                self.assertEqual(agent_run.parse_output(BUNDLED[cli], self.events(fixture), "", preassigned), expected)

    def test_grok_unauthenticated_run_reports_the_error(self) -> None:
        parsed = agent_run.parse_output(BUNDLED["grok"], self.events("grok-error.jsonl"), "", "pre")
        self.assertIsNone(parsed["final"])
        self.assertIn("Not signed in", parsed["error"])

    def test_aider_text_fixture(self) -> None:
        text = (FIXTURES / "aider.txt").read_text(encoding="utf-8")
        self.assertEqual(agent_run.parse_output(BUNDLED["aider"], [], text, None),
                         {"session": None, "final": "final answer", "error": None})

    def test_new_dialects_report_errors_instead_of_partial_success(self) -> None:
        for cli, error in (
            ("copilot", {"type": "session.error", "data": {"message": "denied"}}),
            ("cline", {"type": "run_aborted", "reason": "denied"}),
            ("goose", {"type": "error", "error": "denied"}),
        ):
            with self.subTest(cli=cli):
                parsed = agent_run.parse_output(BUNDLED[cli], [*self.events(f"{cli}.jsonl"), error], "", "pre")
                self.assertEqual(parsed["error"], "denied")


class RunTest(Harness):
    def test_development_levels_reach_the_child_without_promoting_verification(self) -> None:
        for cli in ("copilot", "aider", "cline", "goose"):
            with self.subTest(cli=cli):
                self.runs = self.runs.with_name(f"dev-{cli}")
                self.log.unlink(missing_ok=True)
                result = self.start(cli, "ok", "native-write")
                self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
                info = json.loads(result.stdout)
                self.assertEqual(info["access"], "native-write")
                self.assertIsNone(info["verified"])
                self.assertEqual(self.calls()[0]["prompt"], PROMPT)
                self.assertNotIn(PROMPT.splitlines()[0], " ".join(self.calls()[0]["argv"]))
                if cli == "goose":
                    self.assertEqual(self.calls()[0]["goose_mode"], "approve")

    def test_timeout_covers_a_child_that_never_reads_a_large_prompt(self) -> None:
        self.prompt.write_bytes(("中文" * 500000).encode("utf-8"))
        result = self.start("codex", "unread", "read-only", "--timeout", "0.4")
        self.assertEqual(result.returncode, 3, result.stderr.decode("utf-8", "replace"))
        info = json.loads(result.stdout)
        turn = self.meta(self.runs / info["run_id"])["turns"][0]
        self.assertFalse(agent_run.owned_and_alive(turn))

    def test_invalid_timeout_refuses_before_creating_a_run(self) -> None:
        for value in ("nan", "inf", "0", "-1"):
            with self.subTest(value=value):
                result = self.start("codex", "ok", "read-only", "--timeout", value)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.runs.exists())

    def test_records_and_markdown_are_utf8_lf(self) -> None:
        result = self.start("grok")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        root = self.only_run()
        for name in ("meta.json", "turns/1/prompt.md", "turns/1/final.md"):
            raw = (root / name).read_bytes()
            self.assertNotIn(b"\r\n", raw)
            raw.decode("utf-8")

    def test_timeout_stops_descendants_as_well_as_the_cli(self) -> None:
        pid_file = self.log.with_suffix(".pid")
        env = {**self.env("codex", "tree"), "FAKE_CLI": "codex", "FAKE_CHILD_PID": str(pid_file)}
        result = self.run_script(
            "start", "codex", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt), "--access", "read-only",
            "--executable", str(self.fake), "--runs-dir", str(self.runs), "--timeout", "1", env=env,
        )
        self.assertEqual(result.returncode, 3, result.stderr.decode("utf-8", "replace"))
        self.assertTrue(pid_file.is_file(), "fake CLI did not create its descendant")
        pid = int(pid_file.read_text())
        self.assertIsNone(agent_run.start_marker(pid), "descendant outlived the timeout")

    def test_concurrent_record_commands_preserve_every_outcome(self) -> None:
        info = json.loads(self.start().stdout)
        children = [subprocess.Popen(
            [sys.executable, str(SCRIPT), "record", info["run_id"], "--outcome", "note", "--note", str(n),
             "--runs-dir", str(self.runs)], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ) for n in range(8)]
        for child in children:
            out, err = child.communicate(timeout=30)
            self.assertEqual(child.returncode, 0, err.decode("utf-8", "replace"))
            self.assertIn("outcomes", json.loads(out))
        self.assertEqual({n["note"] for n in self.meta(self.only_run())["outcomes"]}, {str(n) for n in range(8)})

    def test_resume_validates_the_saved_adapter_without_replacing_it(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        meta["adapter"]["start"].append("--yolo")
        agent_run.write_json(root / "meta.json", meta)
        result = self.resume(info["run_id"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("recorded adapter is invalid", result.stderr.decode("utf-8"))
        self.assertEqual(len(self.calls()), 1)

    def test_a_new_adapter_file_does_not_change_a_saved_run(self) -> None:
        info = json.loads(self.start().stdout)
        adapter = copy.deepcopy(BUNDLED["codex"])
        adapter["start"].append("--yolo")
        self.write_adapter(adapter)
        result = self.resume(info["run_id"])
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertNotIn("--yolo", self.calls()[1]["argv"])

    def test_failed_stop_does_not_claim_cancellation(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        marker = agent_run.start_marker(os.getpid())
        self.assertIsNotNone(marker)
        meta["turns"][0].update(state="launched", pid=os.getpid(), pid_started=marker)
        agent_run.write_json(root / "meta.json", meta)
        args = argparse.Namespace(run_id=info["run_id"], runs_dir=str(self.runs))
        with patch.object(agent_run, "stop_tree", side_effect=agent_run.Refused("test stop failed")):
            with self.assertRaises(agent_run.Refused):
                agent_run.cmd_cancel(args)
        turn = self.meta(root)["turns"][0]
        self.assertEqual(turn["state"], "launched")
        self.assertIn("test stop failed", turn["cancel_error"])
        self.assertTrue(agent_run.owned_and_alive(turn))

    def test_stale_cancelling_record_can_be_reconciled(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        # A valid PID occupied by a different strong identity proves this recorded process is gone.
        meta["turns"][0].update(state="cancelling", pid=os.getpid(), pid_started=agent_run.start_marker(os.getpid()) + "1")
        agent_run.write_json(root / "meta.json", meta)
        result = self.run_script("cancel", info["run_id"], "--runs-dir", str(self.runs))
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(self.meta(root)["turns"][0]["state"], "abandoned")

    def test_relative_runs_directory_is_made_absolute_for_prompt_files(self) -> None:
        self.runs = self.cwd.parent / "relative-runs"
        result = self.run_script(
            "start", "grok", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt), "--access", "read-only",
            "--executable", str(self.fake), "--runs-dir", "relative-runs",
            env={**self.env("claude"), "FAKE_CLI": "grok"}, cwd=self.cwd.parent,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(self.calls()[0]["prompt"], PROMPT)

    def test_each_bundled_adapter_runs_and_resumes_where_supported(self) -> None:
        for cli in sorted(BUNDLED):
            with self.subTest(cli=cli):
                self.runs = self.runs.with_name(f"runs-{cli}")
                self.log.unlink(missing_ok=True)
                first = self.start(cli)
                if BUNDLED[cli].get("disabled_reason"):
                    self.assertEqual(first.returncode, 2)
                    self.assertIn(BUNDLED[cli]["disabled_reason"], first.stderr.decode())
                    self.assertFalse(self.log.exists())
                    self.assertFalse(self.runs.exists())
                    continue
                self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", "replace"))
                summary = json.loads(first.stdout)
                self.assertEqual(summary["state"], "exited")
                self.assertEqual(Path(summary["final_file"]).read_text(encoding="utf-8"), "done: " + PROMPT.splitlines()[0])
                if cli == "goose":
                    self.assertEqual(self.calls()[0]["goose_mode"], "chat")
                if BUNDLED[cli]["session"]["source"] == "none":
                    self.assertIsNone(summary["session_id"])
                    self.assertEqual(self.resume(summary["run_id"], cli).returncode, 2)
                    self.assertEqual(self.calls()[0]["prompt"], PROMPT)
                    continue
                self.assertTrue(summary["session_id"])
                self.assertEqual(summary["interactive_resume"]["cwd"], str(self.cwd.resolve()))

                second = self.resume(summary["run_id"], cli)
                self.assertEqual(second.returncode, 0, second.stderr.decode("utf-8", "replace"))
                self.assertEqual(json.loads(second.stdout)["turn"], 2)
                self.assertEqual(json.loads(second.stdout)["session_id"], summary["session_id"])

                calls = self.calls()
                self.assertEqual(len(calls), 2)
                for call in calls:
                    self.assertEqual(call["prompt"], PROMPT)
                    self.assertNotIn(PROMPT.splitlines()[0], " ".join(call["argv"]))
                    self.assertEqual(Path(call["cwd"]).resolve(), self.cwd.resolve())
                    self.assertEqual(call["opencode_config"] is not None, cli == "opencode")
                self.assertIn(summary["session_id"], calls[1]["argv"])

    def test_show_prints_the_command_without_running_it(self) -> None:
        result = self.run_script("show", "grok", "--access", "read-only", "--runs-dir", str(self.runs))
        self.assertEqual(result.returncode, 0)
        shown = json.loads(result.stdout)
        self.assertEqual(shown["start"][0], "grok")
        self.assertIn("--prompt-file", shown["start"])
        self.assertFalse(self.log.exists())
        refused = self.run_script("show", "cursor", "--access", "workspace-write", "--runs-dir", str(self.runs))
        self.assertEqual(refused.returncode, 2)

    def test_list_marks_source_verification_and_levels(self) -> None:
        rows = {row["cli"]: row for row in json.loads(self.run_script("list", "--runs-dir", str(self.runs)).stdout)}
        self.assertEqual(rows["qwen"]["verified"]["live_run"], True)
        self.assertIsNone(rows["cursor"]["verified"])
        self.assertEqual(rows["cursor"]["access"], ["read-only"])
        for row in rows.values():
            self.assertEqual(row["usable"], not bool(BUNDLED[row["cli"]].get("disabled_reason")))

    def test_missing_cli_or_flag_refuses_before_creating_a_run(self) -> None:
        missing = self.run_script(
            "start", "codex", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt), "--access", "read-only",
            "--executable", str(self.cwd / "absent.exe"), "--runs-dir", str(self.runs),
        )
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(self.start("codex", "nohelp").returncode, 2)
        self.assertFalse(self.runs.exists())
        check = self.run_script("check", "claude", "--executable", str(self.fake), dialect="claude", mode="nohelp")
        self.assertEqual(check.returncode, 2)
        self.assertIn("--session-id", check.stdout.decode("utf-8"))

    def test_unknown_cli_and_unoffered_level_are_refused(self) -> None:
        self.assertEqual(self.start("no-such-cli").returncode, 2)
        self.assertEqual(self.start("grok", "ok", "workspace-write").returncode, 2)
        self.assertEqual(self.start("codex", "ok", "danger-full-access").returncode, 2)
        self.assertFalse(self.runs.exists())

    def test_failed_or_malformed_turn_is_not_reported_as_done(self) -> None:
        failed = self.start("claude", "fail")
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(json.loads(failed.stdout)["exit_code"], 4)
        self.assertEqual(json.loads(failed.stdout)["state"], "failed")

        self.runs = self.runs.with_name("runs-malformed")
        malformed = self.start("codex", "malformed")
        self.assertEqual(malformed.returncode, 1)
        turn = self.meta(self.only_run())["turns"][0]
        self.assertEqual((turn["state"], turn["malformed_lines"], turn["final_found"]), ("failed", 1, False))

    def test_timeout_stops_the_turn_and_keeps_the_session(self) -> None:
        result = self.start("codex", "hang", "read-only", "--timeout", "3")
        self.assertEqual(result.returncode, 3)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["state"], "timed-out")
        self.assertEqual(summary["session_id"], "thread-1")

    def test_cancel_stops_only_a_running_owned_turn_and_resume_waits(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, str(SCRIPT), "start", "claude", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt),
             "--access", "read-only", "--executable", str(self.fake), "--runs-dir", str(self.runs), "--no-window"],
            env=self.env("claude", "hang"), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                if self.runs.exists() and any(self.runs.iterdir()):
                    run_dir = self.only_run()
                    if (run_dir / "meta.json").is_file():
                        with agent_run.record_lock(run_dir):
                            meta = self.meta(run_dir)
                        if meta["turns"] and meta["turns"][0].get("state") == "session-known":
                            break
                time.sleep(0.2)
            else:
                self.fail("the mock turn did not publish its session before the deadline")
            run_id = self.only_run().name
            busy = self.resume(run_id, "claude")
            self.assertEqual(busy.returncode, 2)
            self.assertIn("still running", busy.stderr.decode("utf-8"))

            cancel = self.run_script("cancel", run_id, "--runs-dir", str(self.runs), dialect="claude")
            self.assertEqual(cancel.returncode, 0, cancel.stderr.decode("utf-8", "replace"))
            proc.wait(timeout=60)
            self.assertEqual(self.meta(self.only_run())["turns"][0]["state"], "cancelled")
        finally:
            if proc.poll() is None:
                proc.kill()
            proc.communicate(timeout=60)

    def test_unreconciled_turn_blocks_resume_until_marked_abandoned(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        run_dir = self.runs / summary["run_id"]
        meta = self.meta(run_dir)
        # A turn whose recorder died: no end, and a PID that is not ours.
        marker = agent_run.start_marker(os.getpid())
        self.assertIsNotNone(marker)
        meta["turns"].append({"number": 2, "state": "launched", "pid": os.getpid(), "pid_started": marker + "1"})
        (run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

        blocked = self.resume(summary["run_id"])
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("no recorded end", blocked.stderr.decode("utf-8"))

        self.assertEqual(self.run_script("cancel", summary["run_id"], "--runs-dir", str(self.runs)).returncode, 0)
        self.assertEqual(self.meta(run_dir)["turns"][1]["state"], "abandoned")
        resumed = self.resume(summary["run_id"])
        self.assertEqual(resumed.returncode, 0, resumed.stderr.decode("utf-8", "replace"))

    def test_codex_turn_without_a_session_cannot_be_resumed(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        run_dir = self.runs / summary["run_id"]
        meta = self.meta(run_dir)
        meta["session_id"] = None
        (run_dir / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        result = self.resume(summary["run_id"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("start a new run", result.stderr.decode("utf-8"))

    def test_record_appends_the_callers_decision(self) -> None:
        summary = json.loads(self.start("pi").stdout)
        result = self.run_script("record", summary["run_id"], "--outcome", "transferred", "--note", "交给 B", "--runs-dir", str(self.runs), dialect="pi")
        self.assertEqual(result.returncode, 0)
        outcomes = self.meta(self.runs / summary["run_id"])["outcomes"]
        self.assertEqual((outcomes[0]["outcome"], outcomes[0]["note"]), ("transferred", "交给 B"))

    def test_runs_dir_falls_back_to_the_environment(self) -> None:
        env = {**self.env("codex"), "RUMO_AGENT_RUNS_DIR": str(self.runs)}
        result = self.run_script(
            "start", "codex", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt),
            "--access", "read-only", "--executable", str(self.fake), env=env,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertTrue(self.only_run().is_dir())


class DetachWatchTest(Harness):
    def detached(self, *args: str, cli: str = "pi", mode: str = "ok") -> subprocess.CompletedProcess:
        return self.run_script(*args, "--detach", "--runs-dir", str(self.runs), env={**self.env(DIALECT[cli], mode), "FAKE_CLI": cli})

    def start_detached(self, cli: str = "pi", mode: str = "ok") -> dict:
        result = self.detached("start", cli, "--cwd", str(self.cwd), "--prompt-file", str(self.prompt),
                               "--access", "read-only", "--executable", str(self.fake), cli=cli, mode=mode)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        return json.loads(result.stdout)

    def wait_for_recorder(self, info: dict, number: int) -> dict:
        run_dir = Path(info["run_dir"])
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            with agent_run.record_lock(run_dir):
                turns = self.meta(run_dir)["turns"]
            recorder = {"pid": info["recorder_pid"], "pid_started": info["recorder_pid_started"]}
            if turns[number - 1].get("state") in agent_run.TERMINAL and agent_run.process_status(recorder) in ("gone", "foreign"):
                return turns[number - 1]
            time.sleep(0.2)
        self.fail("the detached recorder did not finish before the deadline")

    def test_detached_start_returns_while_the_turn_runs_and_the_recorder_finishes_it(self) -> None:
        info = self.start_detached(mode="slow")
        self.assertTrue(info["detached"])
        self.assertIn(info["state"], agent_run.RUNNING)
        self.assertIn(info["survives_caller"], (True, False) if os.name == "nt" else (None,))
        self.assertEqual(info["watch"][2:4], ["watch", info["run_id"]])
        turn = self.wait_for_recorder(info, 1)
        self.assertEqual(turn["state"], "exited")
        final = Path(info["run_dir"]) / "turns" / "1" / "final.md"
        self.assertEqual(final.read_text(encoding="utf-8"), "done: " + PROMPT.splitlines()[0])
        self.assertEqual(self.calls()[0]["prompt"], PROMPT)

    def test_watch_follows_progress_without_echoing_the_brief(self) -> None:
        info = self.start_detached(mode="slow")
        watched = self.run_script("watch", info["run_id"], "--runs-dir", str(self.runs), dialect="pi")
        self.wait_for_recorder(info, 1)
        out = watched.stdout.decode("utf-8")
        self.assertEqual(watched.returncode, 0, out + watched.stderr.decode("utf-8", "replace"))
        self.assertIn("[tool read] README.md", out)
        self.assertIn("[reply] done: " + PROMPT.splitlines()[0], out)
        self.assertNotIn(PROMPT.splitlines()[1], out)
        self.assertIn("turn 1 exited", out)

    def test_detached_resume_waits_for_the_running_turn_then_continues(self) -> None:
        info = self.start_detached(mode="hang")
        busy = self.detached("resume", info["run_id"], "--prompt-file", str(self.prompt))
        self.assertEqual(busy.returncode, 2)
        self.assertIn("still running", busy.stderr.decode("utf-8"))
        cancel = self.run_script("cancel", info["run_id"], "--runs-dir", str(self.runs), dialect="pi")
        self.assertEqual(cancel.returncode, 0, cancel.stderr.decode("utf-8", "replace"))
        self.assertEqual(self.wait_for_recorder(info, 1)["state"], "cancelled")

        resumed = self.detached("resume", info["run_id"], "--prompt-file", str(self.prompt))
        self.assertEqual(resumed.returncode, 0, resumed.stderr.decode("utf-8", "replace"))
        second = json.loads(resumed.stdout)
        self.assertEqual(second["turn"], 2)
        self.assertEqual(self.wait_for_recorder(second, 2)["state"], "exited")
        self.assertEqual(self.calls()[1]["argv"][self.calls()[1]["argv"].index("--session-id") + 1], info["session_id"])

    def test_watch_reports_a_running_record_whose_process_is_gone(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        run_dir = self.runs / summary["run_id"]
        meta = self.meta(run_dir)
        marker = agent_run.start_marker(os.getpid())
        self.assertIsNotNone(marker)
        meta["turns"].append({"number": 2, "state": "launched", "pid": os.getpid(), "pid_started": marker + "1"})
        agent_run.write_json(run_dir / "meta.json", meta)
        out = io.StringIO()
        with patch.object(agent_run, "WATCH_GRACE", 0), contextlib.redirect_stdout(out):
            code = agent_run.cmd_watch(argparse.Namespace(run_id=summary["run_id"], turn=None, hold=False, runs_dir=str(self.runs)))
        self.assertEqual(code, 2)
        self.assertIn("process is gone", out.getvalue())

    def test_watch_of_a_finished_turn_replays_it_and_returns_its_code(self) -> None:
        failed = json.loads(self.start("claude", "fail").stdout)
        watched = self.run_script("watch", failed["run_id"], "--runs-dir", str(self.runs), dialect="claude")
        self.assertEqual(watched.returncode, 1)
        self.assertIn("turn 1 failed", watched.stdout.decode("utf-8"))


class TurnSelectionTest(Harness):
    def watch(self, run_id: str, **overrides) -> tuple[int, str]:
        out = io.StringIO()
        args = argparse.Namespace(**{"run_id": run_id, "turn": None, "hold": False, "runs_dir": str(self.runs), **overrides})
        with contextlib.redirect_stdout(out):
            code = agent_run.cmd_watch(args)
        return code, out.getvalue()

    def test_turn_zero_and_a_turn_that_never_appears_are_refused(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        zero = self.run_script("watch", summary["run_id"], "--turn", "0", "--runs-dir", str(self.runs))
        self.assertEqual(zero.returncode, 2)
        self.assertIn("turn numbers start at 1", zero.stderr.decode("utf-8"))
        with patch.object(agent_run, "DETACH_WAIT", 0):
            with self.assertRaisesRegex(agent_run.Refused, "run has no turn 2"):
                agent_run.select_turn(self.runs / summary["run_id"], 2)

    def test_watch_waits_for_a_turn_that_starts_later(self) -> None:
        summary = json.loads(self.start("claude", "ok").stdout)
        later = threading.Timer(1.0, lambda: self.resume(summary["run_id"], "claude"))
        later.start()
        try:
            code, out = self.watch(summary["run_id"], turn=2)
        finally:
            later.join()
        self.assertEqual(code, 0, out)
        self.assertIn("turn 2 exited", out)

    def test_a_turn_created_but_never_launched_is_reported(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        run_dir = self.runs / summary["run_id"]
        meta = self.meta(run_dir)
        meta["turns"].append({"number": 2, "state": "created"})
        agent_run.write_json(run_dir / "meta.json", meta)
        with patch.object(agent_run, "WATCH_GRACE", 0):
            code, out = self.watch(summary["run_id"])
        self.assertEqual(code, 2)
        self.assertIn("was created but never launched", out)

    def test_detached_recorder_that_stops_at_created_is_refused_with_its_log(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        run_dir = self.runs / summary["run_id"]

        class Recorder:
            pid = os.getpid()

            def poll(self):
                return 0

        def fake_popen(argv, **kwargs):
            kwargs["stdout"].write(b"recorder crashed here")
            meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
            meta["turns"].append({"number": 2, "state": "created"})
            agent_run.write_json(run_dir / "meta.json", meta)
            return Recorder()

        with patch.object(agent_run.subprocess, "Popen", side_effect=fake_popen):
            with self.assertRaisesRegex(agent_run.Refused, "did not launch turn 2.*recorder crashed here"):
                agent_run.run_detached(run_dir, "resume", str(self.prompt), 60, {})


class WindowTest(Harness):
    @unittest.skipUnless(os.name == "nt", "Windows window launcher")
    def test_windows_terminal_tab_is_preferred_and_semicolons_fall_back_to_a_console(self) -> None:
        argv = [sys.executable, "watch.py", "run-1"]
        with patch.object(agent_run.shutil, "which", return_value="wt.exe"), \
                patch.object(agent_run.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run, \
                patch.object(agent_run.subprocess, "Popen") as popen:
            self.assertEqual(agent_run.open_window(argv, str(self.cwd), "pi run-1")["via"], "wt-tab")
            self.assertEqual(run.call_args.args[0], ["wt.exe", "-w", "rumo-agents", "new-tab", "--title", "pi run-1", "-d", str(self.cwd), *argv])
            popen.assert_not_called()
            result = agent_run.open_window([*argv, "a;b"], str(self.cwd), "pi run-1")
            self.assertEqual(result["via"], "console")
            self.assertEqual(run.call_count, 1)
            self.assertTrue(popen.call_args.kwargs["creationflags"] & subprocess.CREATE_NEW_CONSOLE)

    def test_linux_without_a_display_reports_why_no_window_opened(self) -> None:
        with patch.object(agent_run.os, "name", "posix"), patch.object(agent_run.sys, "platform", "linux"), \
                patch.dict(os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}), \
                patch.object(agent_run.shutil, "which", return_value="/usr/bin/x-terminal-emulator"):
            result = agent_run.open_window(["watch"], "/tmp", "t")
        self.assertFalse(result["opened"])
        self.assertIn("DISPLAY", result["reason"])

    def test_start_and_resume_open_a_window_unless_told_not_to(self) -> None:
        seen = []
        with patch.object(agent_run, "cmd_start", side_effect=lambda a: seen.append(a.window) or 0), \
                patch.object(agent_run, "cmd_resume", side_effect=lambda a: seen.append(a.window) or 0):
            agent_run.main(["start", "pi", "--cwd", ".", "--prompt-file", "p.md", "--access", "read-only"])
            agent_run.main(["start", "pi", "--cwd", ".", "--prompt-file", "p.md", "--access", "read-only", "--no-window"])
            agent_run.main(["resume", "run-1", "--prompt-file", "p.md"])
            agent_run.main(["resume", "run-1", "--prompt-file", "p.md", "--no-window"])
        self.assertEqual(seen, [True, False, True, False])

    def test_start_window_opens_a_held_watch_of_the_new_turn(self) -> None:
        args = argparse.Namespace(cli="claude", cwd=str(self.cwd), prompt_file=str(self.prompt), access="read-only", model=None,
                                  timeout=60, executable=str(self.fake), runs_dir=str(self.runs), detach=False, window=True)
        out = io.StringIO()
        opened = {"opened": True, "via": "test", "reason": None}
        with patch.dict(os.environ, {**self.env("claude"), "FAKE_CLI": "claude"}), \
                patch.object(agent_run, "open_window", return_value=opened) as window, contextlib.redirect_stdout(out):
            code = agent_run.cmd_start(args)
        self.assertEqual(code, 0)
        argv = window.call_args.args[0]
        self.assertEqual(argv[2], "watch")
        self.assertEqual(argv[argv.index("--turn") + 1], "1")
        self.assertIn("--hold", argv)
        self.assertEqual(json.loads(out.getvalue())["window"], opened)

    def test_watch_hold_waits_for_enter_only_on_a_terminal(self) -> None:
        summary = json.loads(self.start("codex").stdout)
        args = argparse.Namespace(run_id=summary["run_id"], turn=None, hold=True, runs_dir=str(self.runs))
        for tty in (True, False):
            with self.subTest(tty=tty), patch.object(agent_run.sys.stdin, "isatty", return_value=tty), \
                    patch("builtins.input") as prompt, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(agent_run.cmd_watch(args), 0)
            self.assertEqual(prompt.called, tty)

    def test_wait_is_silent_and_returns_the_turn_code(self) -> None:
        failed = json.loads(self.start("claude", "fail").stdout)
        result = self.run_script("wait", failed["run_id"], "--runs-dir", str(self.runs), dialect="claude")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["state"], "failed")

    def test_runs_lists_newest_first_filters_active_and_reports_broken_records(self) -> None:
        first = json.loads(self.start("codex").stdout)
        time.sleep(1.1)
        second = json.loads(self.start("codex").stdout)
        running_dir = self.runs / second["run_id"]
        meta = self.meta(running_dir)
        meta["turns"].append({"number": 2, "state": "launched", "pid": os.getpid(), "pid_started": agent_run.start_marker(os.getpid())})
        agent_run.write_json(running_dir / "meta.json", meta)
        broken = self.runs / "00000000-000000-codex-broken"
        broken.mkdir()
        (broken / "meta.json").write_text("{", encoding="utf-8")
        rows = json.loads(self.run_script("runs", "--runs-dir", str(self.runs)).stdout)
        self.assertEqual([row["run_id"] for row in rows], [second["run_id"], first["run_id"], broken.name])
        self.assertIn("error", rows[2])
        self.assertIn("watch", rows[0])
        active = json.loads(self.run_script("runs", "--active", "--runs-dir", str(self.runs)).stdout)
        self.assertEqual([row["run_id"] for row in active if "error" not in row], [second["run_id"]])


class InteractiveTest(Harness):
    def interactive_adapter(self) -> dict:
        adapter = copy.deepcopy(BUNDLED["claude"])
        adapter.update(name="inter", interactive_start=["--fake-interactive", *BUNDLED["claude"]["interactive_start"]])
        return adapter

    def open_args(self, cli: str = "inter") -> argparse.Namespace:
        return argparse.Namespace(cli=cli, cwd=str(self.cwd), prompt_file=str(self.prompt), access="read-only",
                                  model=None, executable=str(self.fake), runs_dir=str(self.runs))

    def run_host(self, argv: list[str], cwd: str, title: str) -> dict:
        # Stands in for the window: run the host to completion without a terminal.
        host = subprocess.run(argv, cwd=cwd, env=self.environment, stdin=subprocess.DEVNULL, capture_output=True, timeout=60)
        self.assertEqual(host.returncode, 0, host.stdout.decode("utf-8", "replace") + host.stderr.decode("utf-8", "replace"))
        return {"opened": True, "via": "test", "reason": None}

    def test_open_runs_the_cli_through_the_host_and_the_report_is_resumed_headless(self) -> None:
        self.write_adapter(self.interactive_adapter())
        self.environment = {**self.env("claude"), "FAKE_CLI": "claude"}
        out = io.StringIO()
        with patch.dict(os.environ, self.environment), patch.object(agent_run, "open_window", side_effect=self.run_host), \
                contextlib.redirect_stdout(out):
            code = agent_run.cmd_open(self.open_args())
        info = json.loads(out.getvalue())
        self.assertEqual(code, 0, info)
        self.assertEqual((info["mode"], info["state"]), ("interactive", "closed"))
        self.assertEqual(info["wait"][2], "wait")
        call = self.calls()[0]
        prompt_path = Path(info["run_dir"]) / "turns" / "1" / "prompt.md"
        self.assertEqual(prompt_path.read_text(encoding="utf-8"), PROMPT)
        self.assertIn(f"Read the brief at {prompt_path} and follow it.", call["argv"][-1])
        self.assertNotIn(PROMPT.splitlines()[0], " ".join(call["argv"]))
        self.assertEqual(call["argv"][call["argv"].index("--name") + 1], info["run_id"])
        self.assertEqual(call["argv"][call["argv"].index("--session-id") + 1], info["session_id"])
        self.assertIn("plan", call["argv"])
        turn = self.meta(Path(info["run_dir"]))["turns"][0]
        self.assertEqual((turn["closed_by"], turn["exit_code"]), ("cli-exit", 0))

        report = self.run_script("resume", info["run_id"], "--prompt-file", str(self.prompt), "--runs-dir", str(self.runs),
                                 env=self.environment)
        self.assertEqual(report.returncode, 0, report.stderr.decode("utf-8", "replace"))
        self.assertIn(info["session_id"], self.calls()[1]["argv"])

    def test_window_close_is_recorded_before_the_cli_exit(self) -> None:
        self.write_adapter(self.interactive_adapter())
        environment = {**self.env("claude"), "FAKE_CLI": "claude"}
        opened = {"opened": True, "via": "test", "reason": None}
        with patch.dict(os.environ, environment), patch.object(agent_run, "open_window", return_value=opened), \
                patch.object(agent_run, "DETACH_WAIT", 0), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(agent_run.cmd_open(self.open_args()), 2)
        run_dir = self.only_run()
        callbacks = []

        class Cli:
            pid = 1

            def wait(self):
                callbacks[0]("window")
                return 0

        with patch.object(agent_run, "on_window_close", side_effect=callbacks.append), \
                patch.object(agent_run.signal, "signal"), patch.object(agent_run.subprocess, "Popen", return_value=Cli()), \
                patch.object(agent_run.sys.stdin, "isatty", return_value=False), contextlib.redirect_stdout(io.StringIO()):
            agent_run.cmd_host(argparse.Namespace(run_id=run_dir.name, runs_dir=str(self.runs)))
        turn = self.meta(run_dir)["turns"][0]
        self.assertEqual((turn["state"], turn["closed_by"]), ("closed", "window"))

    def test_a_cli_without_an_interactive_template_is_refused(self) -> None:
        result = self.run_script("open", "codex", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt), "--access",
                                 "read-only", "--executable", str(self.fake), "--runs-dir", str(self.runs))
        self.assertEqual(result.returncode, 2)
        self.assertIn("no interactive_start template", result.stderr.decode("utf-8"))
        self.assertFalse(self.runs.exists())

    def test_interactive_templates_are_validated(self) -> None:
        base = copy.deepcopy(BUNDLED["claude"])
        cases = {
            "unknown placeholder ['{run_name}'] in '{run_name}'": {**base, "start": [*base["start"], "{run_name}"]},
            "interactive_start must include {access}, {session}, and {opening}": {**base, "interactive_start": ["{access}", "--session-id", "{session}"]},
            "{opening} must occupy a whole argv token in interactive_start": {**base, "interactive_start": ["{access}", "{session}", "{opening}", "x{opening}"]},
            "interactive_start requires a preassigned session": {**copy.deepcopy(BUNDLED["codex"]), "interactive_start": ["{access}", "{session}", "{opening}"]},
            "contains a sandbox or approval bypass ('yolo')": {**base, "interactive_start": [*base["interactive_start"], "--yolo"]},
        }
        for expected, adapter in cases.items():
            with self.subTest(expected=expected):
                self.assertIn(expected, agent_run.validate_adapter(adapter))

    def test_bundled_interactive_templates_keep_the_access_flags(self) -> None:
        for cli in ("claude", "qwen", "pi", "grok"):
            with self.subTest(cli=cli):
                argv = agent_run.render(BUNDLED[cli], "interactive_start", "read-only", ".", None, "sid", None,
                                        opening="Read the brief at x.md and follow it.", run_name="run-1")
                self.assertEqual(argv[-1], "Read the brief at x.md and follow it.")
                for token in BUNDLED[cli]["access"]["read-only"]:
                    self.assertIn(token, argv)
                self.assertIn("sid", argv)


class ProgressRuleTest(unittest.TestCase):
    FIXTURES = {"pi": "pi.jsonl", "codex": "codex.jsonl", "claude": "claude.jsonl", "qwen": "qwen.jsonl",
                "cursor": "cursor.jsonl", "copilot": "copilot.jsonl", "goose": "goose.jsonl"}

    def lines(self, cli: str) -> list[str]:
        events = [json.loads(line) for line in (FIXTURES / self.FIXTURES[cli]).read_text(encoding="utf-8").splitlines()]
        return [line for event in events for line in agent_run.progress_lines(BUNDLED[cli]["progress"], event)]

    def test_every_bundled_progress_rule_set_renders_its_fixture(self) -> None:
        self.assertEqual({cli for cli, adapter in BUNDLED.items() if "progress" in adapter}, set(self.FIXTURES))
        for cli in self.FIXTURES:
            with self.subTest(cli=cli):
                lines = self.lines(cli)
                self.assertIn("[reply] final answer" if cli != "qwen" else "[reply] OK", lines)
                self.assertFalse([line for line in lines if "question" in line], "a user message was rendered")
        self.assertIn("[tool read] README.md", self.lines("pi"))
        self.assertIn("[tool failed] powershell", self.lines("pi"))

    def test_progress_lines_are_single_bounded_lines(self) -> None:
        rule = {"label": "reply", "match": {"type": "m"}, "field": "text"}
        [line] = agent_run.progress_lines([rule], {"type": "m", "text": "a\n  b" + "x" * 1000})
        self.assertTrue(line.startswith("[reply] a b"))
        self.assertEqual(len(line), len("[reply] ") + agent_run.PROGRESS_WIDTH)
        self.assertEqual(agent_run.progress_lines([rule], {"type": "other", "text": "a"}), [])

    def test_malformed_progress_rules_are_refused(self) -> None:
        for progress in ({"label": "x"}, [{"field": "text"}], [{"label": " ", "field": "text"}],
                         [{"label": "x", "field": "text", "label_field": 3}]):
            with self.subTest(progress=progress):
                adapter = {**copy.deepcopy(BUNDLED["pi"]), "progress": progress}
                self.assertIn("progress must be a list of extraction rules, each with a label", agent_run.validate_adapter(adapter))


class UserAdapterTest(Harness):
    PLAIN = {
        "name": "plain-cli", "executable": "plain-cli", "verified": None,
        "help": [{"args": ["--help"], "flags": ["--print"]}],
        "prompt": "stdin",
        "access": {"read-only": ["--permission-mode", "plan"]},
        "start": ["-p", "{access}"],
        "session": {"source": "none"},
        "output": {"format": "text"},
    }

    def test_a_user_adapter_adds_a_cli_without_code_changes(self) -> None:
        self.write_adapter(self.PLAIN)
        result = self.start("plain-cli")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        final = Path(json.loads(result.stdout)["final_file"]).read_text(encoding="utf-8")
        self.assertIn("rm -rf / & $(whoami) `id` 中文提示", final)  # text format keeps the whole stdout
        refused = self.resume(json.loads(result.stdout)["run_id"], "plain-cli")
        self.assertEqual(refused.returncode, 2)
        self.assertIn("one turn only", refused.stderr.decode("utf-8"))

    def test_a_user_adapter_replacing_a_bundled_one_is_flagged(self) -> None:
        self.write_adapter({**BUNDLED["qwen"]})
        rows = {row["cli"]: row for row in json.loads(self.run_script("list").stdout)}
        self.assertEqual(rows["qwen"]["source"], "user")
        self.assertTrue(rows["qwen"]["overrides_bundled"])

    def test_list_survives_invalid_executable_types(self) -> None:
        self.write_adapter({**self.PLAIN, "executable": ["not", "a", "program"]})
        result = self.run_script("list")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        row = next(row for row in json.loads(result.stdout) if row["cli"] == "plain-cli")
        self.assertFalse(row["usable"])
        self.assertFalse(row["installed"])

    def test_relative_executable_is_resolved_before_changing_working_directory(self) -> None:
        relative = os.path.relpath(self.fake, self.cwd.parent)
        result = self.run_script(
            "start", "claude", "--cwd", str(self.cwd), "--prompt-file", str(self.prompt), "--access", "read-only",
            "--executable", relative, "--runs-dir", str(self.runs), dialect="claude", cwd=self.cwd.parent,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))

    def test_unsafe_or_incomplete_adapters_are_refused(self) -> None:
        cases = {
            "bypass": {**self.PLAIN, "name": "bypass", "start": ["-p", "--dangerously-skip-permissions", "{access}"]},
            "yolo-env": {**self.PLAIN, "name": "yolo-env", "env": {"MODE": "yolo"}},
            "no-read-only": {**self.PLAIN, "name": "no-read-only", "access": {"workspace-write": ["--edit"]}},
            "prompt-arg": {**self.PLAIN, "name": "prompt-arg", "prompt": "arg"},
            "bad-placeholder": {**self.PLAIN, "name": "bad-placeholder", "start": ["-p", "{prompt}"]},
            "no-resume": {**self.PLAIN, "name": "no-resume", "session": {"source": "preassign"}},
        }
        for adapter in cases.values():
            self.write_adapter(adapter)
        rows = {row["cli"]: row for row in json.loads(self.run_script("list").stdout)}
        for name in cases:
            with self.subTest(adapter=name):
                self.assertFalse(rows[name]["usable"])
                self.assertEqual(self.start(name).returncode, 2)
        self.assertFalse(self.runs.exists())


class DisabledAdapterTest(Harness):
    def test_disabled_declaration_is_visible_but_never_executed(self) -> None:
        adapter = copy.deepcopy(BUNDLED["codex"])
        adapter["disabled_reason"] = "permission boundary is not established"
        self.write_adapter(adapter)
        shown = self.run_script("show", "codex", "--access", "read-only")
        self.assertEqual(shown.returncode, 0, shown.stderr.decode())
        self.assertEqual(json.loads(shown.stdout)["disabled_reason"], adapter["disabled_reason"])
        rows = {r["cli"]: r for r in json.loads(self.run_script("list").stdout)}
        self.assertFalse(rows["codex"]["usable"])
        self.assertEqual(rows["codex"]["disabled_reason"], adapter["disabled_reason"])
        checked = self.run_script("check", "codex", "--executable", str(self.fake), dialect="codex")
        self.assertEqual(checked.returncode, 2)
        self.assertIn(adapter["disabled_reason"], checked.stderr.decode())
        self.assertEqual(self.start().returncode, 2)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.runs.exists())

    def test_disabling_current_adapter_blocks_old_snapshot_without_replacing_it(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        before = (root / "meta.json").read_bytes()
        adapter = copy.deepcopy(BUNDLED["codex"])
        adapter["disabled_reason"] = "permission boundary is not established"
        self.write_adapter(adapter)
        result = self.resume(info["run_id"])
        self.assertEqual(result.returncode, 2)
        self.assertIn(adapter["disabled_reason"], result.stderr.decode())
        self.assertEqual((root / "meta.json").read_bytes(), before)
        self.assertEqual(len(self.calls()), 1)
        status = json.loads(self.run_script("status", info["run_id"], "--runs-dir", str(self.runs)).stdout)
        self.assertEqual(status["disabled_reason"], adapter["disabled_reason"])
        self.assertNotIn("interactive_resume", status)
        self.assertEqual(self.run_script("record", info["run_id"], "--outcome", "note", "--note", "inspect",
                                         "--runs-dir", str(self.runs)).returncode, 0)

    def test_saved_disabled_adapter_cannot_be_reenabled_by_a_new_file(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        meta["adapter"]["disabled_reason"] = "saved boundary is unsafe"
        agent_run.write_json(root / "meta.json", meta)
        self.write_adapter(copy.deepcopy(BUNDLED["codex"]))
        self.assertEqual(self.resume(info["run_id"]).returncode, 2)
        self.assertEqual(len(self.calls()), 1)

    def test_disabled_reason_must_be_a_nonempty_string(self) -> None:
        for reason in (None, "", "  ", False, [], "bad\0reason"):
            with self.subTest(reason=reason):
                self.assertTrue(agent_run.validate_adapter({**BUNDLED["codex"], "disabled_reason": reason}))

    def test_disabled_check_does_not_even_resolve_or_invoke_the_cli(self) -> None:
        self.write_adapter({**BUNDLED["codex"], "disabled_reason": "unsafe boundary"})
        args = argparse.Namespace(cli="codex", runs_dir=str(self.runs), executable=str(self.fake))
        with patch.dict(os.environ, self.env("codex")), patch.object(agent_run, "resolve_executable") as resolve, \
             patch.object(agent_run.subprocess, "run") as invoke:
            with self.assertRaisesRegex(agent_run.Refused, "unsafe boundary"):
                agent_run.cmd_check(args)
            resolve.assert_not_called()
            invoke.assert_not_called()

    def test_disabled_run_can_still_cancel_a_confirmed_dead_turn(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        meta["turns"][0].update(state="launched", pid=os.getpid(), pid_started=agent_run.start_marker(os.getpid()) + "1")
        agent_run.write_json(root / "meta.json", meta)
        self.write_adapter({**BUNDLED["codex"], "disabled_reason": "unsafe boundary"})
        result = self.run_script("cancel", info["run_id"], "--runs-dir", str(self.runs))
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(json.loads(result.stdout)["state"], "abandoned")
        self.assertEqual(len(self.calls()), 1)

    def test_bundled_permission_gaps_are_disabled(self) -> None:
        for cli in ("gemini", "opencode"):
            with self.subTest(cli=cli):
                self.assertTrue(BUNDLED[cli].get("disabled_reason"))
                self.assertEqual(self.start(cli).returncode, 2)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.runs.exists())


class ProcessIdentityTest(Harness):
    def test_linux_identity_handles_parentheses_and_distinguishes_boots_and_ticks(self) -> None:
        proc_root = self.cwd / "proc"
        process = proc_root / "321"
        process.mkdir(parents=True)
        boot = proc_root / "sys/kernel/random/boot_id"
        boot.parent.mkdir(parents=True)
        boot_id = "12345678-1234-1234-1234-123456789abc"
        boot.write_bytes(boot_id.encode())
        stat = process / "stat"
        stat.write_bytes(("321 (name ) with spaces) S " + "0 " * 18 + "12345 0").encode())
        self.assertEqual(agent_run.linux_process_identity(321, proc_root), ("alive", f"linux:{boot_id}:12345"))
        boot.write_bytes(b"22345678-1234-1234-1234-123456789abc")
        self.assertNotEqual(agent_run.linux_process_identity(321, proc_root)[1], f"linux:{boot_id}:12345")
        stat.write_bytes(("321 (mock) S " + "0 " * 18 + "12346 0").encode())
        self.assertTrue(agent_run.linux_process_identity(321, proc_root)[1].endswith(":12346"))
        stat.write_bytes(("321 (mock) Z " + "0 " * 18 + "12346 0").encode())
        self.assertEqual(agent_run.linux_process_identity(321, proc_root)[0], "gone")
        stat.write_bytes(b"invalid stat")
        self.assertEqual(agent_run.linux_process_identity(321, proc_root), ("unknown", None))
        stat.write_bytes(b"\xff")
        self.assertEqual(agent_run.linux_process_identity(321, proc_root), ("unknown", None))
        stat.unlink()
        self.assertEqual(agent_run.linux_process_identity(321, proc_root), ("gone", None))
        boot.unlink()
        self.assertEqual(agent_run.linux_process_identity(321, proc_root), ("unknown", None))

    def test_read_failure_is_unknown_instead_of_dead(self) -> None:
        with patch.object(Path, "read_text", side_effect=PermissionError("test denied")):
            self.assertEqual(agent_run.linux_process_identity(321, self.cwd), ("unknown", None))

    def test_identity_status_separates_reused_unknown_and_dead_processes(self) -> None:
        marker = "linux:12345678-1234-1234-1234-123456789abc:12345"
        turn = {"pid": 321, "pid_started": marker}
        with patch.object(agent_run, "probe_process", return_value=("alive", marker)):
            self.assertEqual(agent_run.process_status(turn), "owned")
            self.assertEqual(agent_run.process_status({**turn, "pid_started": "Mon Oct 19 10:00:00 2026"}), "unknown")
        with patch.object(agent_run, "probe_process", return_value=("alive", marker + "6")):
            self.assertEqual(agent_run.process_status(turn), "foreign")
        with patch.object(agent_run, "probe_process", return_value=("gone", None)):
            self.assertEqual(agent_run.process_status(turn), "gone")
            self.assertEqual(agent_run.process_status({**turn, "pid_started": "legacy seconds"}), "unknown")
        with patch.object(agent_run, "probe_process", return_value=("unknown", None)):
            self.assertEqual(agent_run.process_status(turn), "unknown")

    def test_unsupported_platform_refuses_before_launch(self) -> None:
        with patch.object(agent_run, "probe_process", return_value=("unknown", None)), \
             patch.object(agent_run.subprocess, "Popen") as spawn:
            args = argparse.Namespace(cli="codex", runs_dir=str(self.runs), timeout=1, access="read-only")
            with self.assertRaisesRegex(agent_run.Refused, "process identity"):
                agent_run.cmd_start(args)
            spawn.assert_not_called()
        self.assertFalse(self.runs.exists())

    def test_unknown_identity_cancel_leaves_record_unchanged(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        meta["turns"][0].update(state="launched", pid=os.getpid(), pid_started="legacy seconds")
        agent_run.write_json(root / "meta.json", meta)
        before = (root / "meta.json").read_bytes()
        resumed = self.resume(info["run_id"])
        self.assertEqual(resumed.returncode, 2)
        self.assertIn("identity", resumed.stderr.decode())
        with patch.object(agent_run, "process_status", return_value="unknown", create=True), \
             patch.object(agent_run, "stop_tree") as stop:
            with self.assertRaisesRegex(agent_run.Refused, "identity"):
                agent_run.cmd_cancel(argparse.Namespace(run_id=info["run_id"], runs_dir=str(self.runs)))
            stop.assert_not_called()
            status = agent_run.summary(root)
        self.assertEqual(status["process_status"], "unknown")
        self.assertIsNone(status["process_alive"])
        self.assertEqual((root / "meta.json").read_bytes(), before)

    def test_stop_never_signals_a_foreign_or_unknown_process(self) -> None:
        with patch.object(agent_run.subprocess, "run") as taskkill, \
             patch.object(agent_run.os, "killpg", create=True) as killpg:
            with patch.object(agent_run, "process_status", return_value="unknown"):
                with self.assertRaisesRegex(agent_run.Refused, "identity"):
                    agent_run.stop_tree(os.getpid(), "legacy")
            for status in ("gone", "foreign"):
                with patch.object(agent_run, "process_status", return_value=status):
                    agent_run.stop_tree(os.getpid(), "legacy")
            taskkill.assert_not_called()
            killpg.assert_not_called()

    def test_identity_lost_after_stop_is_not_successful_cancellation(self) -> None:
        info = json.loads(self.start().stdout)
        root = self.only_run()
        meta = self.meta(root)
        meta["turns"][0].update(state="launched", pid=os.getpid(), pid_started=agent_run.start_marker(os.getpid()))
        agent_run.write_json(root / "meta.json", meta)
        with patch.object(agent_run, "process_status", side_effect=["owned", "unknown", "unknown"]), \
             patch.object(agent_run, "stop_tree"):
            with self.assertRaisesRegex(agent_run.Refused, "cancellation failed"):
                agent_run.cmd_cancel(argparse.Namespace(run_id=info["run_id"], runs_dir=str(self.runs)))
        turn = self.meta(root)["turns"][0]
        self.assertEqual(turn["state"], "launched")
        self.assertIn("unknown", turn["cancel_error"])


class LifecycleBoundaryTest(Harness):
    def prepare(self) -> tuple[Path, dict]:
        root = self.runs / "case"
        root.mkdir(parents=True)
        meta = {"run_id": "case", "cli": "claude", "adapter": copy.deepcopy(BUNDLED["claude"]),
                "executable": [sys.executable, str(self.fake)], "cwd": str(self.cwd), "access": "read-only",
                "session_id": "00000000-0000-4000-8000-000000000001", "model": None, "turns": []}
        agent_run.write_json(root / "meta.json", meta)
        return root, meta

    def test_cancel_waits_for_pid_publication_and_never_abandons_a_starting_child(self) -> None:
        root, meta = self.prepare()
        entering_spawn, release_spawn, cancelling, cancelled = (threading.Event() for _ in range(4))
        errors, results = [], []
        real_popen = subprocess.Popen

        def pause_spawn(argv, *args, **kwargs):
            if str(self.fake) in argv:
                entering_spawn.set()
                if not release_spawn.wait(10):
                    raise RuntimeError("fixture launch was not released")
            return real_popen(argv, *args, **kwargs)

        def run():
            try:
                results.append(agent_run.run_turn(root, meta, "start", PROMPT, 10))
            except BaseException as exc:
                errors.append(exc)

        def cancel():
            try:
                cancelling.set()
                agent_run.cmd_cancel(argparse.Namespace(run_id="case", runs_dir=str(self.runs)))
            except BaseException as exc:
                errors.append(exc)
            finally:
                cancelled.set()

        with patch.dict(os.environ, self.env("claude", "hang")), patch.object(agent_run.subprocess, "Popen", side_effect=pause_spawn), patch("builtins.print"):
            runner = threading.Thread(target=run)
            canceller = threading.Thread(target=cancel)
            runner.start()
            try:
                self.assertTrue(entering_spawn.wait(10))
                canceller.start()
                self.assertTrue(cancelling.wait(10))
                self.assertFalse(cancelled.wait(0.2), "cancel crossed the launch/PID publication boundary")
            finally:
                release_spawn.set()
                runner.join(20)
                if canceller.ident is not None:
                    canceller.join(20)
        self.assertFalse(runner.is_alive())
        self.assertFalse(canceller.is_alive())
        self.assertFalse(errors, errors)
        self.assertEqual(results, [1])
        turn = self.meta(root)["turns"][0]
        self.assertEqual(turn["state"], "cancelled")
        self.assertFalse(agent_run.owned_and_alive(turn))

    def test_interruption_stops_and_reaps_the_owned_child(self) -> None:
        root, meta = self.prepare()
        real_sleep = time.sleep

        def interrupt_wait(seconds):
            if seconds == 0.1:
                raise KeyboardInterrupt()
            real_sleep(seconds)

        with patch.dict(os.environ, self.env("claude", "hang")), patch.object(agent_run.time, "sleep", side_effect=interrupt_wait):
            with self.assertRaises(KeyboardInterrupt):
                agent_run.run_turn(root, meta, "start", PROMPT, 10)
        turn = self.meta(root)["turns"][0]
        self.assertEqual(turn["state"], "interrupted")
        self.assertFalse(agent_run.owned_and_alive(turn))

    def test_launch_failure_records_a_terminal_error(self) -> None:
        root, meta = self.prepare()
        with patch.object(agent_run.subprocess, "Popen", side_effect=OSError("fixture launch failure")):
            self.assertEqual(agent_run.run_turn(root, meta, "start", PROMPT, 10), 1)
        turn = self.meta(root)["turns"][0]
        self.assertEqual(turn["state"], "launch-failed")
        self.assertIn("fixture launch failure", turn["error"])
        self.assertNotIn("pid", turn)

    def test_stale_turn_snapshot_cannot_launch_a_duplicate(self) -> None:
        root, stale = self.prepare()
        fresh = copy.deepcopy(stale)
        fresh["turns"] = [{"number": 1, "state": "exited"}]
        agent_run.write_json(root / "meta.json", fresh)
        with patch.object(agent_run.subprocess, "Popen") as launch:
            with self.assertRaises(agent_run.Refused):
                agent_run.run_turn(root, stale, "start", PROMPT, 10)
            launch.assert_not_called()

    def test_summary_waits_for_a_record_writer(self) -> None:
        root, meta = self.prepare()
        started, done = threading.Event(), threading.Event()
        snapshots = []

        def read():
            started.set()
            snapshots.append(agent_run.summary(root))
            done.set()

        reader = threading.Thread(target=read)
        try:
            with agent_run.record_lock(root):
                reader.start()
                self.assertTrue(started.wait(5))
                self.assertFalse(done.wait(0.2), "reader ignored the metadata lock")
                meta["outcomes"] = [{"outcome": "note", "note": "published"}]
                agent_run.write_json(root / "meta.json", meta)
        finally:
            reader.join(5)
        self.assertTrue(done.is_set())
        self.assertEqual(snapshots[0]["outcomes"][0]["note"], "published")


class SafetyRegressionTest(unittest.TestCase):
    def adapter(self, **fields) -> dict:
        return {**copy.deepcopy(UserAdapterTest.PLAIN), **fields}

    def test_malformed_schema_is_reported_without_crashing(self) -> None:
        for fields in ({"session": "bad"}, {"output": None}, {"name": []}, {"help": [{}]},
                       {"resume_access": {"read-only": "bad"}}, {"output": {"format": "jsonl", "final": {}}}):
            with self.subTest(fields=fields):
                self.assertTrue(agent_run.validate_adapter(self.adapter(**fields)))

    def test_help_and_per_access_environment_cannot_hide_bypass_flags(self) -> None:
        for fields in (
            {"help": [{"args": ["--dangerously-skip-permissions"], "flags": []}]},
            {"help": [{"args": ["run"], "flags": []}]},
            {"access_env": {"read-only": {"MODE": "YoLo"}}},
            {"env": {"CONFIG": '{"mode":"yo\\u006co"}'}},
            {"start": ["--approval-mode=YOLO", "{access}"]},
            {"start": ["--allow-all-tools", "{access}"]},
            {"start": ["--no-sandbox", "{access}"]},
            {"start": ["--sandbox", "disabled", "{access}"]},
            {"start": ["-y", "{access}"]},
            {"env": {"COPILOT_ALLOW_ALL": "true"}},
            {"env": {"CONFIG": '{"skipPermissions":true}'}},
            {"start": ["{access}", "prefix{access}"]},
            {"start": ["--print"]},
        ):
            with self.subTest(fields=fields):
                self.assertTrue(agent_run.validate_adapter(self.adapter(**fields)))

    def test_documented_native_write_is_available_without_claiming_verification(self) -> None:
        adapter = self.adapter(access={"read-only": ["--plan"], "native-write": ["--edit"]})
        self.assertEqual(agent_run.validate_adapter(adapter), [])
        self.assertEqual(agent_run.render(adapter, "start", "native-write", "/w", None, None, None), ["-p", "--edit"])

    def test_render_rejects_option_injection_and_does_not_expand_inserted_values(self) -> None:
        adapter = copy.deepcopy(BUNDLED["codex"])
        with self.assertRaises(agent_run.Refused):
            agent_run.render(adapter, "resume", "read-only", "/w", None, "--dangerously-bypass-approvals-and-sandbox", None)
        with self.assertRaises(agent_run.Refused):
            agent_run.render(adapter, "start", "read-only", "/w", "--yolo", "sid", None)
        argv = agent_run.render(adapter, "start", "read-only", "/w/{model}", "chosen", "sid", None)
        self.assertIn("/w/{model}", argv)

    def test_model_template_cannot_build_a_forbidden_option(self) -> None:
        for template, model in ((["--approval-mode={model}"], "yolo"), (["--sandbox", "{model}"], "disabled"),
                                (["-{model}"], "y")):
            with self.subTest(template=template):
                adapter = self.adapter(model=template, start=["{access}", "{model}"])
                with self.assertRaises(agent_run.Refused):
                    agent_run.render(adapter, "start", "read-only", "/w", model, None, None)

    def test_embedded_model_placeholders_and_unpassed_sessions_are_invalid(self) -> None:
        for fields in (
            {"start": ["{access}", "--model={model}"]},
            {"session": {"source": "preassign"}, "resume": ["{access}"]},
            {"model": ["--model", "{cwd}"]},
        ):
            with self.subTest(fields=fields):
                self.assertTrue(agent_run.validate_adapter(self.adapter(**fields)))

    def test_failed_help_is_not_a_successful_preflight(self) -> None:
        entry = {"adapter": self.adapter(), "path": "test", "source": "test", "overrides_bundled": False}
        results = [subprocess.CompletedProcess([], 0, b"v1", b""), subprocess.CompletedProcess([], 7, b"--print", b"")]
        with patch.object(agent_run.subprocess, "run", side_effect=results):
            self.assertFalse(agent_run.check(entry, ["fake"])["ok"])

    def test_extract_skips_empty_text_parts_and_non_text_payloads(self) -> None:
        events = [{"blocks": [{"type": "thinking"}], "fallback": "answer"}]
        self.assertEqual(agent_run.extract(events, {"field": ["blocks", "fallback"]}), "answer")
        self.assertIsNone(agent_run.extract([{"x": [{"type": "text", "text": 7}]}], {"field": "x"}))

    def test_cancel_cannot_be_lost_between_record_read_and_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            agent_run.write_json(root / "meta.json", {"turns": [{"state": "launched"}]})
            loaded, release, cancelling, cancelled = (threading.Event() for _ in range(4))
            original = agent_run.load_meta
            errors = []

            def controlled_load(path):
                meta = original(path)
                if threading.current_thread().name == "finish":
                    loaded.set()
                    if not release.wait(5):
                        raise RuntimeError("test did not release the writer")
                return meta

            def update(state):
                try:
                    if state == "cancelled":
                        cancelling.set()
                    agent_run.update_turn(root, 1, state=state)
                except Exception as exc:
                    errors.append(exc)
                finally:
                    if state == "cancelled":
                        cancelled.set()

            with patch.object(agent_run, "load_meta", side_effect=controlled_load):
                finish = threading.Thread(target=update, args=("exited",), name="finish")
                cancel = threading.Thread(target=update, args=("cancelled",), name="cancel")
                finish.start()
                try:
                    self.assertTrue(loaded.wait(5))
                    cancel.start()
                    self.assertTrue(cancelling.wait(5))
                    # The writer holding the lock must publish before another update can read.
                    self.assertFalse(cancelled.wait(0.2), "record updates interleaved")
                finally:
                    release.set()
                    finish.join(5)
                    if cancel.ident is not None:
                        cancel.join(5)
            self.assertFalse(errors)
            self.assertEqual(original(root)["turns"][0]["state"], "exited")
            agent_run.write_json(root / "meta.json", {"turns": [{"state": "cancelling"}]})
            agent_run.update_turn(root, 1, state="session-known")
            self.assertEqual(original(root)["turns"][0]["state"], "cancelling")
            agent_run.update_turn(root, 1, state="cancelled")
            agent_run.update_turn(root, 1, state="exited")
            self.assertEqual(original(root)["turns"][0]["state"], "cancelled")


if __name__ == "__main__":
    unittest.main()
