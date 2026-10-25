from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "extras"
    / "rumo-linux-inspect"
    / "scripts"
    / "remote_memory_inspection.py"
)
SPEC = importlib.util.spec_from_file_location("remote_memory_inspection", SCRIPT)
assert SPEC and SPEC.loader
REMOTE_MEMORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REMOTE_MEMORY)


class RemoteMemoryOutputPathTests(unittest.TestCase):
    def test_host_path_characters_cannot_escape_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "evidence"
            output = REMOTE_MEMORY.output_path(root, "../escaped", "20260831-120000")

            self.assertEqual(output.parent, root.resolve())
            self.assertNotIn("..", output.name)
            self.assertNotIn("/", output.name)
            self.assertNotIn("\\", output.name)

    def test_ipv6_host_produces_cross_platform_directory_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = REMOTE_MEMORY.output_path(
                Path(temp_dir), "2001:db8::1", "20260831-120000"
            )

            self.assertNotIn(":", output.name)
            self.assertRegex(output.name, r"^[A-Za-z0-9_-]+$")


class RemoteMemoryScriptTests(unittest.TestCase):
    def test_script_collects_no_command_lines_or_raw_log_lines(self) -> None:
        script = REMOTE_MEMORY.remote_script("/srv/app", "/var/log/app", 30)

        self.assertNotRegex(script, r"\bargs\b|cmdline")
        self.assertIn("comm", script)
        self.assertNotRegex(script, r"grep -[a-zA-Z]*n")
        self.assertIn("grep -ciF", script)
        self.assertIn("===== process resources =====", script)
        self.assertIn("/proc/$pid/status", script)
        self.assertIn("/proc/$pid/fd", script)
        self.assertIn("not collected: no JVM declared in profile", script)

    def test_jvm_requires_a_declaration_and_uses_only_bounded_read_only_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            profile = Path(temp_dir)
            (profile / "runtime.json").write_text(json.dumps({"products": {}}), encoding="utf-8")
            self.assertEqual(REMOTE_MEMORY.jvm_pid_files(profile), [])
            (profile / "runtime.json").write_text(json.dumps({
                "products": {"application": {"runtime": "jvm", "pid_file": "/run/application.pid"}}
            }), encoding="utf-8")
            declared = REMOTE_MEMORY.jvm_pid_files(profile)
            self.assertEqual(declared, [("application", "/run/application.pid")])
            script = REMOTE_MEMORY.remote_script("", "", 30, declared)
            self.assertIn("jcmd \"$pid\" GC.heap_info", script)
            self.assertIn("jcmd \"$pid\" VM.native_memory summary", script)
            self.assertIn("head -80", script)
            self.assertNotIn("jcmd \"$pid\" Thread.print", script)

    @unittest.skipUnless(os.name == "posix" and shutil.which("sh"), "needs a POSIX shell")
    def test_log_summary_reports_counts_without_log_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs = Path(temp_dir) / "logs"
            logs.mkdir()
            (logs / "app.log").write_text(
                "ERROR login failed token=FAKE-LOG-SECRET\nERROR again password=FAKE-LOG-SECRET\nWARN slow\n",
                encoding="utf-8",
            )
            (logs / "quiet.log").write_text("all good\n", encoding="utf-8")
            locked = logs / "locked.log"
            locked.write_text("ERROR FAKE-LOG-SECRET\n", encoding="utf-8")
            locked.chmod(0)

            output = self.run_script(REMOTE_MEMORY.remote_script("", str(logs), 30))

            self.assertNotIn("FAKE-LOG-SECRET", output)
            self.assertRegex(output, r"app\.log\tERROR\t2")
            self.assertRegex(output, r"app\.log\tWARN\t1")
            self.assertNotRegex(output, r"quiet\.log\t")
            if os.geteuid() != 0:
                self.assertRegex(output, r"locked\.log\tunreadable")
                self.assertIn("files_scanned=3 unreadable=1", output)

    @unittest.skipUnless(os.name == "posix" and shutil.which("sh"), "needs a POSIX shell")
    def test_missing_log_directory_is_reported_not_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = self.run_script(REMOTE_MEMORY.remote_script("", str(Path(temp_dir) / "absent"), 30))

        self.assertIn("log directory missing or not a directory", output)
        self.assertNotIn("files_scanned=", output)

    def run_script(self, script: str) -> str:
        completed = subprocess.run(["sh", "-s"], input=script, text=True, capture_output=True, timeout=60, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return completed.stdout


if __name__ == "__main__":
    unittest.main()
