#!/usr/bin/env python3
"""Render bounded interaction-evidence JSON as readable, source-linked text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def normalize_text(value: Any, max_chars: int) -> tuple[str, bool]:
    text = value if isinstance(value, str) else ""
    normalized = " ".join(text.split())
    return normalized[:max_chars], len(normalized) > max_chars


def render_file(path: Path, max_chars: int) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read evidence JSON {path}: {exc}") from exc
    evidence = payload.get("interaction_evidence")
    if not isinstance(evidence, dict) or not isinstance(evidence.get("turns"), list):
        raise ValueError(f"missing interaction_evidence.turns in {path}")
    selection = evidence.get("selection") if isinstance(evidence.get("selection"), dict) else {}
    lines = [
        f"=== {path.name} session={selection.get('session_id', 'unknown')} "
        f"anchor={selection.get('anchor_turn', 'unknown')} ==="
    ]
    for turn in evidence["turns"]:
        if not isinstance(turn, dict):
            continue
        lines.append(
            f"TURN {turn.get('turn_id', 'unknown')} status={turn.get('status', 'unknown')} "
            f"tools={turn.get('tool_calls', 0)} failures={turn.get('tool_failure_signals', 0)}"
        )
        for role, key in (("USER", "user_messages"), ("ASSISTANT", "assistant_messages")):
            messages = turn.get(key)
            if not isinstance(messages, list):
                continue
            for message in messages:
                if not isinstance(message, dict):
                    continue
                text, locally_truncated = normalize_text(message.get("text"), max_chars)
                truncated = bool(message.get("truncated")) or locally_truncated
                suffix = " [truncated]" if truncated else ""
                lines.append(
                    f"{role} @{message.get('source_line', 'unknown')}: {text}{suffix}"
                )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Evidence-only JSON files to render.")
    parser.add_argument("--max-chars", type=int, default=2500, help="Maximum rendered characters per message.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.max_chars < 1:
        parser.error("--max-chars must be at least 1")
    try:
        sections = [render_file(path.expanduser().resolve(), args.max_chars) for path in args.paths]
    except ValueError as exc:
        parser.error(str(exc))
    sys.stdout.write("\n\n".join("\n".join(section) for section in sections) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
