#!/usr/bin/env python3
"""Add, refresh, or remove the always-on Rumo baseline block in an instruction file.

Only the text between the baseline markers is ever changed; everything else in
the target file is kept byte for byte. Prints one word: added, updated,
unchanged, removed, or absent.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path


START = "<!-- rumo-engineering-skills:baseline:start -->"
END = "<!-- rumo-engineering-skills:baseline:end -->"
BOM = b"\xef\xbb\xbf"
SNIPPET = Path(__file__).resolve().parent.parent / "references" / "agents-snippet.md"


class BaselineError(Exception):
    """The target or snippet cannot be changed safely."""


def snippet_lines() -> list[str]:
    """Return the lines of the snippet's fenced markdown block."""
    text = SNIPPET.read_text(encoding="utf-8")
    try:
        body = text.split("```markdown\n", 1)[1].split("```", 1)[0]
    except IndexError as exc:
        raise BaselineError(f"No markdown block found in {SNIPPET}") from exc
    return body.strip("\n").splitlines()


def build_block(newline: str) -> str:
    return newline.join([START, *snippet_lines(), END])


def find_block(text: str) -> tuple[int, int] | None:
    """Return the block's start and end offsets, or None when it is absent."""
    starts, ends = text.count(START), text.count(END)
    if starts == 0 and ends == 0:
        return None
    if starts != 1 or ends != 1:
        raise BaselineError("baseline markers are incomplete or repeated; fix the file by hand")
    start = text.index(START)
    end = text.index(END) + len(END)
    if end <= start:
        raise BaselineError("baseline end marker precedes the start marker; fix the file by hand")
    return start, end


def apply(text: str, mode: str) -> tuple[str, str]:
    """Return the new text and the action word for the requested mode."""
    newline = "\r\n" if "\r\n" in text else "\n"
    span = find_block(text)
    if mode == "remove":
        if span is None:
            return text, "absent"
        start, end = span
        before, after = text[:start], text[end:]
        if after.startswith(newline):
            after = after[len(newline):]
        if before.endswith(newline * 2):
            before = before[: -len(newline)]
        return before + after, "removed"
    block = build_block(newline)
    if span is None:
        if mode == "refresh":
            return text, "absent"
        if not text:
            prefix = ""
        elif text.endswith(newline):
            prefix = newline
        else:
            prefix = newline * 2
        return text + prefix + block + newline, "added"
    start, end = span
    if text[start:end] == block:
        return text, "unchanged"
    return text[:start] + block + text[end:], "updated"


def write_atomically(target: Path, data: bytes) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if target.exists():
            shutil.copymode(target, temporary)
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()


def run(target: Path, mode: str, dry_run: bool) -> str:
    # Write through a symlinked instruction file instead of replacing the link.
    target = Path(os.path.realpath(target))
    if target.exists():
        raw = target.read_bytes()
    elif mode == "install":
        if not target.parent.is_dir():
            # An installer dry run previews a client home it has not created yet.
            if dry_run:
                return "added"
            raise BaselineError(f"Directory does not exist: {target.parent}")
        raw = b""
    else:
        return "absent"
    bom = raw.startswith(BOM)
    try:
        text = raw[len(BOM) if bom else 0 :].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BaselineError(f"{target} is not UTF-8; it was left unchanged") from exc
    new_text, action = apply(text, mode)
    if action in ("added", "updated", "removed") and not dry_run:
        write_atomically(target, (BOM if bom else b"") + new_text.encode("utf-8"))
    return action


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True, help="CLAUDE.md, AGENTS.md, or another instruction file")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_const", const="install", dest="mode", help="add or update the block")
    mode.add_argument("--refresh", action="store_const", const="refresh", dest="mode", help="update the block only if present")
    mode.add_argument("--remove", action="store_const", const="remove", dest="mode", help="remove the block")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        action = run(Path(args.target).expanduser(), args.mode, args.dry_run)
    except (BaselineError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(action)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
