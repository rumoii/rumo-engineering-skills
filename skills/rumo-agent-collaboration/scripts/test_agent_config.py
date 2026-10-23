#!/usr/bin/env python3
"""Tests for agent_config.py against the bundled adapters and the fake CLI from test_agent_run; no model is called."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "agent_config.py"

spec = importlib.util.spec_from_file_location("test_agent_run", HERE / "test_agent_run.py")
assert spec and spec.loader
test_agent_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(test_agent_run)
agent_run = test_agent_run.agent_run
BUNDLED = test_agent_run.BUNDLED

spec = importlib.util.spec_from_file_location("agent_config", SCRIPT)
assert spec and spec.loader
agent_config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent_config)


class AgentConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "配置 目录"
        root.mkdir()
        self.config = root / "agents.json"
        self.runs = root / "runs"
        self.fake = root / "fake_cli.py"
        self.fake.write_text(test_agent_run.FAKE, encoding="utf-8")
        self.log = root / "fake.log"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_config(self, *args: str, cli: str = "codex", mode: str = "ok") -> subprocess.CompletedProcess:
        env = {**os.environ, "RUMO_AGENTS_CONFIG": str(self.config), "FAKE_CLI": cli, "FAKE_MODE": mode,
               "FAKE_DIALECT": test_agent_run.DIALECT[cli], "FAKE_LOG": str(self.log),
               "RUMO_AGENT_ADAPTERS_DIR": str(self.runs / "no-user-adapters")}
        env.pop("RUMO_AGENT_RUNS_DIR", None)
        return subprocess.run([sys.executable, str(SCRIPT), "--runs-dir", str(self.runs), *args],
                              env=env, capture_output=True, timeout=120)

    def test_missing_configuration_tells_the_user_to_run_setup(self) -> None:
        for args in (("show",), ("lanes", "review"), ("check",)):
            with self.subTest(args=args):
                result = self.run_config(*args)
                self.assertEqual(result.returncode, 3)
                self.assertIn("rumo-setup", result.stderr.decode("utf-8", "replace"))

    def test_set_role_keeps_other_roles_and_settings_byte_identical(self) -> None:
        self.assertEqual(self.run_config("set-role", "review", "--lane", "codex:gpt-6.1-sol@high", "--lane", "claude@max").returncode, 0)
        self.assertEqual(self.run_config("set-auto-panel", "allow").returncode, 0)
        self.assertEqual(self.run_config("set-role", "delegate", "--lane", "codex@medium").returncode, 0)
        before = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(self.run_config("set-role", "delegate", "--lane", "claude:opus@high").returncode, 0)
        after = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(after["roles"]["review"], before["roles"]["review"])
        self.assertEqual(after["auto_panel"], "allow")
        self.assertEqual(after["roles"]["delegate"], [{"cli": "claude", "model": "opus", "effort": "high"}])
        lanes = json.loads(self.run_config("lanes", "review").stdout)
        self.assertEqual([lane["label"] for lane in lanes["lanes"]], ["codex:gpt-6.1-sol@high", "claude@max"])
        self.assertEqual(lanes["auto_panel"], "allow")

    def test_invalid_lanes_are_refused_and_nothing_is_written(self) -> None:
        for lane in ("qwen@high", "claude@ultra", "nosuchcli", "gemini", "codex:@high", "Codex"):
            with self.subTest(lane=lane):
                result = self.run_config("set-role", "review", "--lane", lane)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(self.config.exists())
        self.assertEqual(self.run_config("set-role", "delegate", "--lane", "codex", "--lane", "claude").returncode, 2)
        self.assertEqual(self.run_config("set-role", "review", "--lane", "codex", "--executable", "claude=/x").returncode, 2)
        self.assertFalse(self.config.exists())

    def test_delegate_lanes_are_told_apart_by_use(self) -> None:
        result = self.run_config("set-role", "delegate", "--lane", "测试=claude:sonnet@medium", "--lane", "实现=codex@high")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        lanes = json.loads(self.run_config("lanes", "delegate").stdout)["lanes"]
        self.assertEqual([(lane["use"], lane["label"]) for lane in lanes],
                         [("测试", "测试=claude:sonnet@medium"), ("实现", "实现=codex@high")])
        for args in (("delegate", "--lane", "测试=claude", "--lane", "测试=codex"),
                     ("delegate", "--lane", "测试=claude", "--lane", "codex"),
                     ("review", "--lane", "测试=claude"),
                     ("delegate", "--lane", "=claude")):
            with self.subTest(args=args):
                self.assertEqual(self.run_config("set-role", *args).returncode, 2)
        self.assertEqual(json.loads(self.run_config("lanes", "delegate").stdout)["lanes"], lanes)

    def test_a_corrupt_or_unknown_configuration_fails_closed(self) -> None:
        for content in ("{", json.dumps({"version": 2, "roles": {}}),
                        json.dumps({"version": 1, "roles": {"swarm": []}}),
                        json.dumps({"version": 1, "auto_panel": "always", "roles": {}})):
            with self.subTest(content=content):
                self.config.write_text(content, encoding="utf-8")
                self.assertEqual(self.run_config("show").returncode, 2)
                self.assertEqual(self.run_config("set-auto-panel", "off").returncode, 2)
                self.assertEqual(self.config.read_text(encoding="utf-8"), content)

    def test_probe_runs_one_read_only_turn_per_distinct_lane(self) -> None:
        exe = f"codex={self.fake}"
        self.assertEqual(self.run_config("set-role", "review", "--lane", "codex@high", "--executable", exe).returncode, 0)
        self.assertEqual(self.run_config("set-role", "design", "--lane", "codex@high", "--executable", exe).returncode, 0)
        result = self.run_config("check", "--probe")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace") + result.stdout.decode())
        report = json.loads(result.stdout)
        self.assertEqual(len(report["lanes"]), 1)
        self.assertEqual(report["lanes"][0]["roles"], ["review", "design"])
        self.assertTrue(report["lanes"][0]["probe"]["ok"])
        calls = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(calls), 1)
        self.assertIn("read-only", calls[0]["argv"])
        self.assertIn('model_reasoning_effort="high"', calls[0]["argv"])

    def test_a_failed_probe_is_reported(self) -> None:
        result = self.run_config("check", "--probe", "--lane", "codex@low", "--executable", f"codex={self.fake}", mode="fail")
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertFalse(report["lanes"][0]["probe"]["ok"])
        self.assertIn("probe failed", report["lanes"][0]["problems"])



class ModelListingTest(unittest.TestCase):
    """Listing samples are constructed from the shapes codex, grok, and pi printed on 2026-10-23."""

    def listed(self, cli: str, stdout: str) -> list[dict]:
        result = subprocess.CompletedProcess([], 0, stdout.encode("utf-8"), b"")
        with patch.object(agent_config.subprocess, "run", return_value=result):
            return agent_config.list_models(BUNDLED[cli], ["fake"])["models"]

    def test_codex_catalog_keeps_visible_models_with_their_efforts(self) -> None:
        catalog = {"models": [
            {"slug": "gpt-6.1-sol", "visibility": "list", "default_reasoning_level": "low",
             "supported_reasoning_levels": [{"effort": "low"}, {"effort": "ultra"}]},
            {"slug": "codex-auto-review", "visibility": "hide", "supported_reasoning_levels": []},
            {"slug": "gpt-5.5", "visibility": "list", "supported_reasoning_levels": [{"effort": "high"}]},
        ]}
        self.assertEqual(self.listed("codex", json.dumps(catalog)), [
            {"id": "gpt-6.1-sol", "efforts": ["low", "ultra"], "default_effort": "low"},
            {"id": "gpt-5.5", "efforts": ["high"]},
        ])

    def test_text_listings_become_model_ids(self) -> None:
        grok = "You are logged in.\n\nDefault model: grok-4.7\n\nAvailable models:\n  * grok-4.7 (default)\n  * grok-4.7-mini\n"
        self.assertEqual([m["id"] for m in self.listed("grok", grok)], ["grok-4.7", "grok-4.7-mini"])
        pi = ("provider              model               context  max-out  thinking  images\n"
              "ollama                qwen:uncensored-4b  32.8K    512      no        no    \n"
              "deepseek              deepseek-v4-pro     1.0M     64K      yes       no    \n")
        self.assertEqual([m["id"] for m in self.listed("pi", pi)], ["ollama/qwen:uncensored-4b", "deepseek/deepseek-v4-pro"])

    def test_fixed_aliases_and_unlistable_clis_need_no_command(self) -> None:
        with patch.object(agent_config.subprocess, "run") as run:
            self.assertEqual([m["id"] for m in agent_config.list_models(BUNDLED["claude"], None)["models"]], ["fable", "opus", "sonnet"])
            self.assertEqual(agent_config.list_models(BUNDLED["qwen"], None)["models"], [])
            run.assert_not_called()

    def test_a_failed_listing_is_refused(self) -> None:
        result = subprocess.CompletedProcess([], 1, b"", b"not signed in")
        with patch.object(agent_config.subprocess, "run", return_value=result), self.assertRaises(agent_config.Refused):
            agent_config.list_models(BUNDLED["grok"], ["fake"])

    def test_malformed_models_entries_make_the_adapter_invalid(self) -> None:
        base = {**BUNDLED["claude"]}
        for models in ({"static": []}, {"args": ["models"], "format": "yaml"},
                       {"args": ["{cwd}"], "format": "json", "items": "m", "id": "id"},
                       {"args": ["ls"], "format": "text", "pattern": r"(?P<x>\S+)", "id": "{id}"},
                       {"args": ["--dangerously-skip-permissions"], "format": "text", "pattern": "(?P<id>.+)"}):
            with self.subTest(models=models):
                self.assertTrue(agent_run.validate_adapter({**base, "models": models}))
        for name, adapter in BUNDLED.items():
            with self.subTest(cli=name):
                self.assertEqual(agent_run.validate_adapter(adapter), [])


if __name__ == "__main__":
    unittest.main()
