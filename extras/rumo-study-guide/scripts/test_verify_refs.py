#!/usr/bin/env python3
"""Exercise reference verification through its command-line entry point."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("verify_refs.py")


class VerifyRefsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "source"
        self.root.mkdir()
        (self.root / "sample.py").write_text("# first\nprint('你好 & <world>')\n", encoding="utf-8")
        self.guide = self.base / "guide.html"

    def run_verify(self, html: str, *args: str) -> subprocess.CompletedProcess:
        self.guide.write_text(html, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.guide), "--root", str(self.root), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def assert_failure(self, html: str, reason: str) -> None:
        result = self.run_verify(html)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(reason, result.stdout)
        self.assertEqual(sum(line.startswith("FAIL ") for line in result.stdout.splitlines()), 1)
        self.assertIn("1 references checked, 1 failed", result.stdout)

    def test_all_elements_with_data_p_are_checked(self) -> None:
        result = self.run_verify(
            '<span data-p="sample.py" data-l="2" data-s="你好 &amp; &lt;world&gt;"></span>'
            '<input data-p="sample.py" data-l="1" data-s="first" />'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 references checked, 0 failed", result.stdout)

    def test_missing_file(self) -> None:
        self.assert_failure('<a data-p="absent.py" data-l="1" data-s="x"></a>', "file not found")

    def test_line_out_of_range(self) -> None:
        for line in ("0", "-1", "3"):
            with self.subTest(line=line):
                self.assert_failure(
                    f'<a data-p="sample.py" data-l="{line}" data-s="first"></a>', "line out of range"
                )

    def test_invalid_line_number(self) -> None:
        self.assert_failure('<a data-p="sample.py" data-l="two" data-s="x"></a>', "invalid line number")

    def test_symbol_not_on_line(self) -> None:
        self.assert_failure('<a data-p="sample.py" data-l="1" data-s="absent"></a>', "text not on line")

    def test_missing_attributes(self) -> None:
        for attrs in ('data-p="sample.py"', 'data-p="sample.py" data-l="1"',
                      'data-p="sample.py" data-s="first"', 'data-p="" data-l="1" data-s="first"'):
            with self.subTest(attrs=attrs):
                self.assert_failure(f"<div {attrs}></div>", "missing data-p/data-l/data-s")

    def test_empty_requires_allow_empty(self) -> None:
        result = self.run_verify("<p>No references</p>")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no references", result.stdout.lower())
        self.assertIn("0 references checked", result.stdout)
        allowed = self.run_verify("<p>No references</p>", "--allow-empty")
        self.assertEqual(allowed.returncode, 0, allowed.stderr)

    def test_repeated_aliases(self) -> None:
        folder = self.root / "nested"
        folder.mkdir()
        (folder / "other.txt").write_text("target\n", encoding="utf-8")
        result = self.run_verify(
            '<a data-p="X:other.txt" data-l="1" data-s="target"></a>'
            '<b data-p="Y:sample.py" data-l="1" data-s="first"></b>',
            "--alias", "X=nested/", "--alias", "Y=./",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 references checked, 0 failed", result.stdout)

    def test_parent_escape(self) -> None:
        (self.base / "outside.txt").write_text("outside\n", encoding="utf-8")
        self.assert_failure('<a data-p="../outside.txt" data-l="1" data-s="outside"></a>', "outside root")

    def test_alias_cannot_escape_root(self) -> None:
        (self.base / "outside.txt").write_text("outside\n", encoding="utf-8")
        result = self.run_verify('<a data-p="X:outside.txt" data-l="1" data-s="outside"></a>',
                                 "--alias", "X=../")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("outside root", result.stdout)

    def test_failures_are_collected(self) -> None:
        result = self.run_verify('<i data-p="absent" data-l="1" data-s="x"></i>'
                                 '<i data-p="sample.py" data-l="9" data-s="x"></i>')
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("2 references checked, 2 failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
