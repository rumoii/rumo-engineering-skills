#!/usr/bin/env python3
"""Exercise in-place source linking through its command-line entry point."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


SCRIPT = Path(__file__).with_name("link_refs.py")


class LinkRefsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # link_refs resolves paths; Windows runners give TEMP as an 8.3 short path.
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "source"
        self.root.mkdir()
        self.source = self.root / "sample.py"
        self.source.write_text("first\nsecond\n", encoding="utf-8")
        self.guide = self.base / "guide.html"

    def run_link(self, content: str | bytes, *args: str) -> subprocess.CompletedProcess:
        self.original = content.encode("utf-8") if isinstance(content, str) else content
        self.guide.write_bytes(self.original)
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.guide), "--root", str(self.root), *args],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def attributes(self) -> list[dict]:
        class Tags(HTMLParser):
            def handle_starttag(inner, tag, attrs):
                if tag == "a":
                    values.append(dict(attrs))
        values = []
        parser = Tags()
        parser.feed(self.guide.read_bytes().decode("utf-8"))
        return values

    def test_default_with_and_without_href(self) -> None:
        result = self.run_link('<a data-p="sample.py" data-l="2">源码</a>'
                               '<a href="#old" data-p="sample.py" data-l="1">old</a>')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ok: 2 links")
        for attrs, line in zip(self.attributes(), (2, 1)):
            self.assertEqual(attrs["href"], f"vscode://file/{self.source.as_posix()}:{line}")
            self.assertEqual(attrs["data-abs"], self.source.as_posix())

    def test_custom_template_alias_and_web(self) -> None:
        nested = self.root / "lib"
        nested.mkdir()
        (nested / "other.py").write_text("value\n", encoding="utf-8")
        result = self.run_link('<a data-p="X:other.py" data-l="1">alias</a>',
                               "--alias", "X=wrong/", "--alias", "X=lib/",
                               "--template", "cursor://file/{abs}:{line}",
                               "--web-template", "https://example.org/blob/{commit}/{path}#L{line}",
                               "--commit", "abc123")
        self.assertEqual(result.returncode, 0, result.stderr)
        attrs = self.attributes()[0]
        self.assertEqual(attrs["href"], f"cursor://file/{nested.as_posix()}/other.py:1")
        self.assertEqual(attrs["data-web"], "https://example.org/blob/abc123/lib/other.py#L1")

    def test_web_can_be_the_default_href(self) -> None:
        result = self.run_link('<a data-p="sample.py" data-l="1">source</a>',
                               "--template", "https://example.org/{commit}/{path}#L{line}",
                               "--commit", "fixed")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.attributes()[0]["href"], "https://example.org/fixed/sample.py#L1")

    def test_only_generated_attributes_change_bytes(self) -> None:
        prefix = b'\xef\xbb\xbf<!doctype html>\r\n<!-- <a data-p="absent"> -->\r\n<p>\xe4\xbd\xa0 &amp; hi</p>\r\n'
        tag = b"<A  class='ref' DATA-P='sample.py' data-l=1 href = '#old' data-abs='old' title='a > b' data-s='first'>"
        suffix = b"text &quot; <i>inner</i></A>\r\n<script>const x = '<a data-p=\"absent\">';</script>\r\n"
        result = self.run_link(prefix + tag + suffix)
        self.assertEqual(result.returncode, 0, result.stderr)
        absolute = self.source.as_posix().encode("utf-8")
        expected = tag.replace(b"href = '#old'", b'href="vscode://file/' + absolute + b':1"')
        expected = expected.replace(b"data-abs='old'", b'data-abs="' + absolute + b'"')
        self.assertEqual(self.guide.read_bytes(), prefix + expected + suffix)

    def test_escaping_self_closing_and_idempotence(self) -> None:
        source = self.root / "a & b.py"
        source.write_text("value\n", encoding="utf-8")
        result = self.run_link('<a data-p="a &amp; b.py" data-l="1" href/>',
                               "--web-template", "https://example.org/{path}?x=1&y=2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.attributes()[0]["data-abs"], source.as_posix())
        linked = self.guide.read_bytes()
        result = self.run_link(linked, "--web-template", "https://example.org/{path}?x=1&y=2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.guide.read_bytes(), linked)

    def test_failures_preserve_whole_file(self) -> None:
        (self.base / "outside.py").write_text("outside\n", encoding="utf-8")
        cases = [
            ('<a data-p="../outside.py" data-l="1">x</a>', (), "outside root"),
            ('<a data-p="X:outside.py" data-l="1">x</a>', ("--alias", "X=../"), "outside root"),
            ('<a data-p="absent.py" data-l="1">x</a>', (), "file not found"),
            ('<span data-p="sample.py" data-l="1">x</span>', (), "<span>"),
            ('<a data-p="sample.py" data-l="1">x</a>', ("--web-template", "https://example.org/{commit}/{path}"), "--commit"),
            ('<a data-p="sample.py" data-l="1">x</a>', ("--template", "https://example.org/{commit}/{path}"), "--commit"),
            ('<a data-p="sample.py" data-l="1">x</a>', ("--alias", "1bad=lib/"), "invalid alias"),
        ]
        for line in ("0", "-1", "two", "1.5", "", "1_0"):
            cases.append((f'<a data-p="sample.py" data-l="{line}">x</a>', (), "positive integer"))
        for bad, args, reason in cases:
            with self.subTest(reason=reason, bad=bad):
                # A valid earlier reference must not be partially written.
                result = self.run_link('<a data-p="sample.py" data-l="1">valid</a>\r\n' + bad, *args)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(reason, result.stderr)
                self.assertEqual(self.guide.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()
