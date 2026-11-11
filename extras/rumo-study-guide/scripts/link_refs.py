#!/usr/bin/env python3
"""Add source links to data-p anchors without serializing the document."""

from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ATTRIBUTE = re.compile(r'''[^\s=/>]+(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?''')


def rewrite_tag(tag: str, values: dict[str, str]) -> str:
    """Preserve spacing, spelling and quoting of every unrelated attribute."""
    start = re.match(r"<[^\s/>]+", tag).end()
    end = re.search(r"/?>$", tag).start()
    edits = []
    found = set()
    for match in ATTRIBUTE.finditer(tag, start, end):
        name = re.match(r"[^\s=/>]+", match.group()).group().lower()
        if name in values:
            edits.append((match.start(), match.end(), f'{name}="{html.escape(values[name], quote=True)}"'))
            found.add(name)
    missing = ''.join(f' {name}="{html.escape(value, quote=True)}"'
                      for name, value in values.items() if name not in found)
    edits.append((end, end, missing))
    for left, right, replacement in reversed(edits):
        tag = tag[:left] + replacement + tag[right:]
    return tag


class Links(HTMLParser):
    def __init__(self, content: str, root: Path, aliases: dict, template: str,
                 web_template: str | None, commit: str | None) -> None:
        super().__init__()
        self.root, self.aliases = root, aliases
        self.template, self.web_template, self.commit = template, web_template, commit
        self.offsets = [0] + [match.end() for match in re.finditer("\n", content)]
        self.edits: list[tuple[int, int, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs)
        if "data-p" not in attrs:
            return
        if tag != "a":
            raise ValueError(f"data-p must be on <a>, found <{tag}>")
        path = attrs["data-p"] or ""
        key, separator, suffix = path.partition(":")
        if separator and key in self.aliases:
            path = self.aliases[key] + suffix
        if not path:
            raise ValueError("missing data-p path")
        target = (self.root / path.replace("\\", "/")).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError(f"{path}: path is outside root")
        if not target.is_file():
            raise ValueError(f"{path}: file not found")
        line = attrs.get("data-l") or ""
        if not re.fullmatch(r"[0-9]+", line) or int(line) < 1:
            raise ValueError(f"{path}: data-l must be a positive integer")
        fields = dict(abs=target.as_posix(), path=target.relative_to(self.root).as_posix(),
                      line=str(int(line)))
        if self.commit is not None:
            fields["commit"] = self.commit
        values = {"href": self.template.format(**fields), "data-abs": target.as_posix()}
        if self.web_template is not None:
            values["data-web"] = self.web_template.format(**fields)
        raw = self.get_starttag_text()
        row, column = self.getpos()
        start = self.offsets[row - 1] + column
        self.edits.append((start, start + len(raw), rewrite_tag(raw, values)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("guide", type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--alias", action="append", default=[], metavar="X=prefix/")
    parser.add_argument("--template", default="vscode://file/{abs}:{line}")
    parser.add_argument("--web-template")
    parser.add_argument("--commit")
    args = parser.parse_args()
    try:
        aliases = {}
        # Match verify_refs.py: concatenate prefixes; later aliases win.
        for value in args.alias:
            key, separator, prefix = value.partition("=")
            if not separator or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key) or not prefix:
                raise ValueError(f"invalid alias: {value}; expected X=prefix/")
            aliases[key] = prefix
        fields = dict(abs="", path="", line="1")
        if args.commit is not None:
            fields["commit"] = args.commit
        for template in (args.template, args.web_template):
            if template is not None:
                template.format(**fields)
        root = args.root.resolve()
        if not root.is_dir():
            raise ValueError("root is not a directory")
        # Decode bytes directly to preserve BOM and CRLF during round trips.
        content = args.guide.read_bytes().decode("utf-8")
        links = Links(content, root, aliases, args.template, args.web_template, args.commit)
        links.feed(content)
        links.close()
        for start, end, replacement in reversed(links.edits):
            content = content[:start] + replacement + content[end:]
        args.guide.write_bytes(content.encode("utf-8"))
    except KeyError as exc:
        message = "template requires --commit" if exc.args[0] == "commit" else f"unknown template field: {exc}"
        print(f"FAIL {message}", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(f"ok: {len(links.edits)} links")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
