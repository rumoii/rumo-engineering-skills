#!/usr/bin/env python3
"""Check data-p/data-l/data-s references against UTF-8 files inside --root.

Usage: python verify_refs.py guide.html --root source --alias X=src/
"""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class References(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str | None, str | None, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if "data-p" in values:
            self.refs.append(tuple(values.get(key) for key in ("data-p", "data-l", "data-s")))


def check_reference(root: Path, path: str, line: str, symbol: str) -> str | None:
    try:
        target = (root / path.replace("\\", "/")).resolve()
        if not target.is_relative_to(root):
            return "path is outside root"
        if not target.is_file():
            return "file not found"
        try:
            number = int(line)
        except ValueError:
            return "invalid line number"
        lines = target.read_text(encoding="utf-8").splitlines()
        if number < 1 or number > len(lines):
            return f"line out of range (file has {len(lines)} lines)"
        if symbol not in lines[number - 1]:
            return "text not on line"
    except (OSError, ValueError, RuntimeError) as exc:
        return f"cannot read source: {exc}"
    return None


def one_line(value: str | None) -> str:
    return (value or "").replace("\r", "\\r").replace("\n", "\\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("guide", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--alias", action="append", default=[], metavar="X=prefix/")
    parser.add_argument("--allow-empty", action="store_true")
    args = parser.parse_args()
    aliases = {}
    for value in args.alias:
        key, separator, prefix = value.partition("=")
        if not separator or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key) or not prefix:
            print(f"FAIL invalid alias: {one_line(value)}; expected X=prefix/", file=sys.stderr)
            return 1
        aliases[key] = prefix

    refs = References()
    try:
        root = args.root.resolve()
        if not root.is_dir():
            raise ValueError("root is not a directory")
        refs.feed(args.guide.read_text(encoding="utf-8"))
        refs.close()
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL {one_line(str(args.guide))}: {one_line(str(exc))}")
        print("0 references checked, 1 failed")
        return 1

    failures = 0
    for path, line, symbol in refs.refs:
        expanded = path or ""
        key, separator, suffix = expanded.partition(":")
        if separator and key in aliases:
            expanded = aliases[key] + suffix
        if not path or not line or not symbol:
            problem = "missing data-p/data-l/data-s"
        else:
            problem = check_reference(root, expanded, line, symbol)
        if problem:
            failures += 1
            print(f"FAIL {one_line(expanded)}:{one_line(line)} [{one_line(symbol)}] {one_line(problem)}")

    if not refs.refs and not args.allow_empty:
        print("FAIL no references found; use --allow-empty to accept an empty guide")
    print(f"{len(refs.refs)} references checked, {failures} failed")
    return 1 if failures or (not refs.refs and not args.allow_empty) else 0


if __name__ == "__main__":
    raise SystemExit(main())
