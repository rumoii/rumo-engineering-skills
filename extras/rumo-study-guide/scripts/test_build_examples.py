#!/usr/bin/env python3
"""Exercise example embedding using only the current Python interpreter."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("build_examples.py")


class BuildExamplesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.template = self.root / "template.html"
        self.out = self.root / "guide.html"

    def source(self, name: str, text: str) -> Path:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def run_build(self, template: str, *args: str, timeout: str = "60") -> subprocess.CompletedProcess:
        self.template.write_text(template, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.template), "--out", str(self.out), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "BUILD_EXAMPLES_TIMEOUT": timeout},
        )

    def assert_failure(self, result: subprocess.CompletedProcess, filename: str, reason: str) -> None:
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(filename, result.stderr)
        self.assertIn(reason, result.stderr)
        self.assertFalse(self.out.exists())

    def test_code_and_snippet_are_escaped(self) -> None:
        self.source("example.py", '# <source> & "quoted"\n')
        self.source("fragment.sql", 'SELECT "<tag>&";\n')
        result = self.run_build("<!--CODE:example.py--><!--SNIPPET:fragment.sql-->")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.out.read_text(encoding="utf-8")
        self.assertIn('<figure class="code">', html)
        self.assertIn('<figure class="code snippet">', html)
        self.assertIn("Python", html)
        self.assertIn("SQL", html)
        self.assertIn("example.py", html)
        self.assertIn("fragment.sql", html)
        self.assertIn("片段 · 未运行", html)
        self.assertIn("&lt;source&gt; &amp;", html)
        self.assertIn("&lt;tag&gt;&amp;", html)
        self.assertNotIn("<!--CODE:", html)
        self.assertEqual(result.stdout.strip(), "ok: 1 code, 1 snippets, 0 outputs")

    def test_python_stdout_and_working_directory(self) -> None:
        self.source("examples/message.txt", "你好 <out> &\n")
        self.source("examples/run.py", "from pathlib import Path\nprint(Path('message.txt').read_text(encoding='utf-8'))\n")
        result = self.run_build("<!--OUT:examples/run.py--><!--BUILT_AT-->")
        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.out.read_text(encoding="utf-8")
        self.assertIn('<figure class="out">', html)
        self.assertIn("实际运行输出 · examples/run.py", html)
        self.assertIn("<pre>你好 &lt;out&gt; &amp;</pre>", html)
        self.assertNotIn("BUILT_AT", html)
        self.assertEqual(result.stdout.strip(), "ok: 0 code, 0 snippets, 1 outputs")

    def test_explicit_root(self) -> None:
        self.source("sources/demo.py", "print('from root')\n")
        result = self.run_build("<!--CODE:demo.py--><!--OUT:demo.py-->", "--root", str(self.root / "sources"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<pre>from root</pre>", self.out.read_text(encoding="utf-8"))

    def test_nonzero_exit_does_not_write_output(self) -> None:
        self.source("bad.py", "import sys\nprint('failure detail', file=sys.stderr)\nsys.exit(7)\n")
        result = self.run_build("<!--OUT:bad.py-->")
        self.assert_failure(result, "bad.py", "exit code 7")
        self.assertIn("failure detail", result.stderr)

    def test_failure_preserves_existing_output(self) -> None:
        self.source("bad.py", "raise SystemExit(3)\n")
        self.out.write_bytes(b"previous guide")
        result = self.run_build("<!--OUT:bad.py-->")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(self.out.read_bytes(), b"previous guide")

    def test_timeout_does_not_write_output(self) -> None:
        self.source("slow.py", "import time\ntime.sleep(30)\n")
        result = self.run_build("<!--OUT:slow.py-->", timeout="0.2")
        self.assert_failure(result, "slow.py", "timed out")

    def test_unknown_runner_extension(self) -> None:
        self.source("example.unknown", "text\n")
        result = self.run_build("<!--OUT:example.unknown-->")
        self.assert_failure(result, "example.unknown", "unsupported extension")

    def test_parent_escape(self) -> None:
        self.source("outside.py", "print('outside')\n")
        (self.root / "inside").mkdir()
        for kind in ("CODE", "SNIPPET", "OUT"):
            with self.subTest(kind=kind):
                result = self.run_build(f"<!--{kind}:../outside.py-->", "--root", str(self.root / "inside"))
                self.assert_failure(result, "../outside.py", "outside root")

    def test_source_does_not_become_a_placeholder(self) -> None:
        self.source("literal.py", '# <!--OUT:missing.py-->\n')
        result = self.run_build("<!--CODE:literal.py-->")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("&lt;!--OUT:missing.py--&gt;", self.out.read_text(encoding="utf-8"))

    def test_missing_source(self) -> None:
        result = self.run_build("<!--CODE:missing.py-->")
        self.assert_failure(result, "missing.py", "cannot read")

    def test_newlines_and_trailing_whitespace(self) -> None:
        self.source("newlines.py", "import sys\nsys.stdout.buffer.write(b'one\\r\\ntwo\\rthree  \\n')\n")
        result = self.run_build("<!--OUT:newlines.py-->")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<pre>one\ntwo\nthree</pre>", self.out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
