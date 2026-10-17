from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "rumo-debug" / "scripts" / "remote_probe.py"
SPEC = importlib.util.spec_from_file_location("remote_probe", SCRIPT)
assert SPEC and SPEC.loader
REMOTE_PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REMOTE_PROBE)


class RemoteProbeTests(unittest.TestCase):
    def test_probe_collects_no_process_command_lines(self) -> None:
        remote = " ; ".join(REMOTE_PROBE.remote_commands("/srv/app", "/var/log/app", "order-42"))

        self.assertNotRegex(remote, r"\bargs\b|cmdline")
        self.assertIn("comm", remote)

    def test_keyword_search_is_bounded_and_redacted(self) -> None:
        search = REMOTE_PROBE.remote_commands("", "/var/log/app", "order-42")[-1]

        self.assertIn("-m 20", search)
        self.assertIn("tail -40", search)
        self.assertIn("sed -E", search)

    def test_no_keyword_means_no_log_content(self) -> None:
        remote = " ; ".join(REMOTE_PROBE.remote_commands("", "/var/log/app", ""))

        self.assertNotIn("grep", remote)

    def test_default_target_leaves_user_to_ssh(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--host", "example.test"], capture_output=True, text=True, check=False
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(shlex.split(completed.stdout)[:2], ["ssh", "example.test"])

    def test_explicit_user_prefixes_host(self) -> None:
        self.assertEqual(REMOTE_PROBE.ssh_target("ops", "example.test"), "ops@example.test")

    @unittest.skipUnless(os.name == "posix" and shutil.which("sh") and shutil.which("sed"), "needs a POSIX shell and sed")
    def test_redaction_masks_common_secret_shapes_and_keeps_context(self) -> None:
        sample = "\n".join(
            [
                "ERROR login failed password=FAKE1 user=bob",
                'db.password: "FAKE2", DB_PASSWORD=FAKE3&x=1',
                "Authorization: Bearer FAKE4abc",
                "url jdbc:mysql://admin:FAKE5@db:3306/app",
                "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.FAKE6sig",
                '{"apiKey":"FAKE7","api_key": "FAKE8"} token expired for order 42',
                "-Dsecret.value=FAKE9 order_id=123",
                'password="FAKE10 FAKE10_SUFFIX" retry=3',
                "{'token': 'FAKE11_VALUE'}",
                "secret='FAKE12 a b c' status=open",
                "client_secret = 'FAKE13'",
            ]
        )
        command = "sed -E " + " ".join(f"-e {shlex.quote(expression)}" for expression in REMOTE_PROBE.redact_expressions())

        completed = subprocess.run(["sh", "-c", command], input=sample, text=True, capture_output=True, timeout=30, check=False)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("FAKE", completed.stdout)
        self.assertIn("token expired for order 42", completed.stdout)
        self.assertIn("order_id=123", completed.stdout)
        self.assertIn("user=bob", completed.stdout)
        self.assertIn("retry=3", completed.stdout)
        self.assertIn("status=open", completed.stdout)


if __name__ == "__main__":
    unittest.main()
