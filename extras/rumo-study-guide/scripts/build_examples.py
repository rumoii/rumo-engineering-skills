#!/usr/bin/env python3
"""Embed UTF-8 source files and actual stdout in an HTML template.

Usage: python build_examples.py template.html --out guide.html [--root examples]
BUILD_EXAMPLES_TIMEOUT overrides the per-example timeout (default: 60 seconds).
Only OUT placeholders execute files; CODE and SNIPPET only display source.
"""

from __future__ import annotations

import argparse
import html
import math
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path, PureWindowsPath


PLACEHOLDER = re.compile(r"<!--(?:(CODE|SNIPPET|OUT):(.+?)|BUILT_AT)-->")
LANGUAGES = {".py": "Python", ".js": "JavaScript", ".mjs": "JavaScript",
             ".java": "Java", ".ts": "TypeScript", ".sql": "SQL", ".json": "JSON",
             ".html": "HTML", ".css": "CSS", ".sh": "Shell", ".ps1": "PowerShell"}


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip()


def source_path(root: Path, rel: str) -> Path:
    if Path(rel).is_absolute() or PureWindowsPath(rel).drive or PureWindowsPath(rel).root:
        raise ValueError(f"{rel}: expected a relative path inside root")
    path = (root / rel.replace("\\", "/")).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{rel}: path is outside root")
    return path


def run_example(path: Path, rel: str, timeout: float) -> str:
    filename = "./" + path.name
    runners = {".py": [sys.executable, filename], ".js": ["node", filename],
               ".mjs": ["node", filename], ".java": ["java", filename]}
    command = runners.get(path.suffix.lower())
    if command is None:
        raise ValueError(f"{rel}: unsupported extension {path.suffix or '(none)'}")
    try:
        result = subprocess.run(
            command, cwd=path.parent, capture_output=True, text=True, encoding="utf-8",
            timeout=timeout, check=False, env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except FileNotFoundError as exc:
        raise ValueError(f"{rel}: command not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError(f"{rel}: timed out after {timeout:g} seconds") from exc
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"{rel}: cannot execute: {exc}") from exc
    if result.returncode:
        raise ValueError(f"{rel}: exit code {result.returncode}: {normalize(result.stderr)}")
    return normalize(result.stdout)


def build(template: str, root: Path, timeout: float) -> tuple[str, dict[str, int]]:
    counts = {"CODE": 0, "SNIPPET": 0, "OUT": 0}
    built_at = datetime.now().astimezone().isoformat(timespec="seconds")

    def replace(match: re.Match) -> str:
        kind, rel = match.groups()
        if kind is None:
            return built_at
        path = source_path(root, rel)
        if kind == "OUT":
            if not path.is_file():
                raise ValueError(f"{rel}: cannot read example file")
            content = run_example(path, rel, timeout)
            caption = "实际运行输出 · " + html.escape(rel)
            figure = f'<figure class="out"><figcaption>{caption}</figcaption><pre>{html.escape(content)}</pre></figure>'
        else:
            try:
                content = normalize(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                raise ValueError(f"{rel}: cannot read source: {exc}") from exc
            language = LANGUAGES.get(path.suffix.lower(), path.suffix.lstrip(".") or "text")
            label = " 片段 · 未运行" if kind == "SNIPPET" else ""
            css = "code snippet" if kind == "SNIPPET" else "code"
            caption = f"{html.escape(language)}{label} · <code>{html.escape(rel)}</code>"
            figure = f'<figure class="{css}"><figcaption>{caption}</figcaption><pre><code>{html.escape(content)}</code></pre></figure>'
        counts[kind] += 1
        return figure

    return PLACEHOLDER.sub(replace, template), counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    try:
        timeout = float(os.environ.get("BUILD_EXAMPLES_TIMEOUT", "60"))
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("BUILD_EXAMPLES_TIMEOUT must be a positive finite number")
        root = (args.root if args.root is not None else args.template.resolve().parent).resolve()
        if not root.is_dir():
            raise ValueError(f"{root}: root is not a directory")
        rendered, counts = build(args.template.read_text(encoding="utf-8"), root, timeout)
        args.out.write_text(rendered, encoding="utf-8", newline="\n")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"FAIL {args.template}: {exc}", file=sys.stderr)
        return 1
    print(f"ok: {counts['CODE']} code, {counts['SNIPPET']} snippets, {counts['OUT']} outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
