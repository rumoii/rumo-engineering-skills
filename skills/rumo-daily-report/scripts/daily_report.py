#!/usr/bin/env python3
"""Safely configure and append incremental date-based daily reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Iterator


NUMBER_RE = re.compile(r"^\s*(\d+)[.)、]\s*")


def codex_root() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def state_dir() -> Path:
    return codex_root() / "rumo-daily-report"


def config_path() -> Path:
    return state_dir() / "config.json"


def state_path() -> Path:
    return state_dir() / "state.json"


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


@contextmanager
def locked(path: Path) -> Iterator[None]:
    state_dir().mkdir(parents=True, exist_ok=True)
    lock_name = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest() + ".lock"
    lock_path = state_dir() / lock_name
    with open(lock_path, "a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_config() -> Path:
    try:
        raw = json.loads(config_path().read_text(encoding="utf-8"))
        report_dir = Path(raw["report_dir"]).expanduser()
    except FileNotFoundError as exc:
        raise RuntimeError("日报目录尚未配置，请先执行 configure") from exc
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RuntimeError(f"日报配置损坏，未写入任何文件: {exc}") from exc
    if not report_dir.is_absolute():
        raise RuntimeError("日报目录必须是绝对路径")
    return report_dir


def normalize_item(item: str) -> str:
    value = item.strip().replace("\r\n", "\n").replace("\r", "\n")
    value = NUMBER_RE.sub("", value, count=1)
    return value.strip()


def fingerprint(item: str) -> str:
    normalized = re.sub(r"\s+", "", normalize_item(item))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_state() -> dict:
    if not state_path().exists():
        return {"fingerprints": {}, "sessions": {}}
    try:
        state = json.loads(state_path().read_text(encoding="utf-8"))
        if not isinstance(state, dict) or not isinstance(state.get("fingerprints", {}), dict):
            raise ValueError("invalid state shape")
        state.setdefault("sessions", {})
        return state
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"日报去重状态损坏，未写入任何文件: {exc}") from exc


def parse_existing(text: str) -> tuple[int, set[str]]:
    maximum = 0
    existing: set[str] = set()
    current: list[str] = []
    numbers: list[int] = []
    for line in text.splitlines():
        match = NUMBER_RE.match(line)
        if match:
            if current:
                existing.add(fingerprint("\n".join(current)))
            current = [line]
            number = int(match.group(1))
            numbers.append(number)
            maximum = max(maximum, number)
        elif current and line.strip():
            current.append(line)
    if current:
        existing.add(fingerprint("\n".join(current)))
    if text.strip() and not numbers:
        raise RuntimeError("当天日报已有内容但无法识别编号，未写入")
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        raise RuntimeError("当天日报编号不连续或存在重复，未写入")
    return maximum, existing


def configure(report_dir: str, replace: bool = False) -> int:
    target = Path(report_dir).expanduser()
    if not target.is_absolute():
        raise RuntimeError("日报目录必须是绝对路径")
    target.mkdir(parents=True, exist_ok=True)
    current = None
    if config_path().exists():
        try:
            current = Path(json.loads(config_path().read_text(encoding="utf-8"))["report_dir"]).expanduser()
        except Exception as exc:  # noqa: BLE001 - convert to a safe user-facing error
            raise RuntimeError(f"日报配置损坏，未修改配置: {exc}") from exc
    if current is not None and current.resolve() != target.resolve() and not replace:
        raise RuntimeError("已存在固定日报目录；只有用户明确要求更换时才可使用 --replace")
    atomic_write(config_path(), json.dumps({"report_dir": str(target.resolve())}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"report_dir": str(target.resolve())}, ensure_ascii=False))
    return 0


def append_report(items_json: str, session_id: str, forced_date: str | None) -> int:
    report_dir = load_config()
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"items-json 不是有效 JSON: {exc}") from exc
    if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
        raise RuntimeError("items-json 必须是字符串数组")
    if forced_date:
        try:
            report_date = date.fromisoformat(forced_date)
        except ValueError as exc:
            raise RuntimeError("date 必须使用 YYYY-MM-DD") from exc
    else:
        report_date = datetime.now().astimezone().date()
    report_path = report_dir / f"{report_date.isoformat()}-日报.txt"
    normalized = [normalize_item(item) for item in items if normalize_item(item)]
    if any("\x00" in item for item in normalized):
        raise RuntimeError("日报内容包含非法字符，未写入")
    with locked(report_path):
        if report_path.exists():
            try:
                original = report_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise RuntimeError(f"当天日报无法以 UTF-8 读取，未覆盖原文件: {exc}") from exc
        else:
            original = ""
        maximum, file_fingerprints = parse_existing(original)
        state = load_state()
        date_prefix = f"{report_date.isoformat()}:"
        known = {
            key[len(date_prefix) :]
            for key in state["fingerprints"]
            if key.startswith(date_prefix)
        } | file_fingerprints
        added: list[tuple[int, str, str]] = []
        next_number = maximum + 1
        for item in normalized:
            digest = fingerprint(item)
            if digest in known:
                continue
            added.append((next_number, item, digest))
            known.add(digest)
            next_number += 1
        if added:
            chunks = []
            if original and not original.endswith("\n"):
                chunks.append("\n")
            for number, item, _ in added:
                chunks.append(f"{number}.{item}\n")
            atomic_write(report_path, original + "".join(chunks))
            timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
            for number, item, digest in added:
                state["fingerprints"][date_prefix + digest] = {"number": number}
            state.setdefault("sessions", {})[session_id] = {
                "updated_at": timestamp,
                "added": state.setdefault("sessions", {}).get(session_id, {}).get("added", 0) + len(added),
            }
            atomic_write(state_path(), json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        result = {
            "path": str(report_path),
            "date": report_date.isoformat(),
            "added": [{"number": number, "text": item} for number, item, _ in added],
            "skipped_duplicates": len(normalized) - len(added),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    config_parser = subparsers.add_parser("configure")
    config_parser.add_argument("--report-dir", required=True)
    config_parser.add_argument("--replace", action="store_true")
    append_parser = subparsers.add_parser("append")
    append_parser.add_argument("--items-json", required=True)
    append_parser.add_argument("--session-id", default="unknown-session")
    append_parser.add_argument("--date")
    args = parser.parse_args()
    try:
        if args.command == "configure":
            return configure(args.report_dir, args.replace)
        return append_report(args.items_json, args.session_id, args.date)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
