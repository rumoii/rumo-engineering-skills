#!/usr/bin/env python3
"""Collect deterministic, privacy-bounded metrics from local Codex sessions."""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable


FAILURE_PATTERNS = (
    re.compile(r"\bexit code:\s*[1-9]\d*\b", re.IGNORECASE),
    re.compile(r"\bprocess exited with code\s+[1-9]\d*\b", re.IGNORECASE),
    re.compile(r"\bscript failed\b", re.IGNORECASE),
    re.compile(r"\bcommand timed out\b", re.IGNORECASE),
    re.compile(r'"isError"\s*:\s*true', re.IGNORECASE),
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return parse_timestamp(float(text))
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed_date = date.fromisoformat(text)
        except ValueError:
            return None
        parsed = datetime.combine(parsed_date, datetime.min.time(), timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat().replace("+00:00", "Z") if value else None


def parse_boundary(value: str | None, end_of_day: bool = False) -> datetime | None:
    parsed = parse_timestamp(value)
    if parsed and end_of_day and value and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.strip()):
        return parsed + timedelta(days=1) - timedelta(microseconds=1)
    return parsed


def load_json_lines(path: Path, errors: list[str]) -> Iterable[dict[str, Any]]:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"{path}:{line_number}: invalid JSON")
                    continue
                if isinstance(value, dict):
                    value["_source_line"] = line_number
                    yield value
    except OSError as exc:
        errors.append(f"{path}: cannot read: {exc}")


def flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(flatten_text(item) for item in value)
    if isinstance(value, dict):
        preferred = [value.get(key) for key in ("text", "output", "message")]
        return "\n".join(flatten_text(item) for item in preferred if item is not None)
    return ""


def message_text(payload: dict[str, Any]) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        return flatten_text(content)
    return "\n".join(
        item.get("text", "")
        for item in content
        if isinstance(item, dict) and item.get("type") in {"input_text", "output_text"}
    ).strip()


def has_failure_signal(output: Any) -> bool:
    text = flatten_text(output)
    return any(pattern.search(text) for pattern in FAILURE_PATTERNS)


def in_interval(value: datetime | None, since: datetime | None, until: datetime | None) -> bool:
    if value is None:
        return True
    if since and value < since:
        return False
    if until and value > until:
        return False
    return True


def matches_project(cwd: str | None, filters: list[str]) -> bool:
    if not filters:
        return True
    if not cwd:
        return False
    candidate = os.path.normcase(os.path.normpath(os.path.expanduser(cwd)))
    basename = os.path.basename(candidate)
    for raw_filter in filters:
        normalized = os.path.normcase(os.path.normpath(os.path.expanduser(raw_filter)))
        if candidate == normalized or basename == normalized:
            return True
        try:
            if os.path.commonpath([candidate, normalized]) == normalized:
                return True
        except ValueError:
            continue
    return False


def relative_source(path: Path, codex_home: Path) -> str:
    try:
        return str(path.resolve().relative_to(codex_home.resolve()))
    except (OSError, ValueError):
        return str(path)


def session_path_date(path: Path, sessions_dir: Path) -> date | None:
    try:
        relative = path.relative_to(sessions_dir)
    except ValueError:
        return None
    if len(relative.parts) < 4:
        return None
    try:
        return date(int(relative.parts[0]), int(relative.parts[1]), int(relative.parts[2]))
    except ValueError:
        return None


@dataclass
class TurnStats:
    turn_id: str
    started_at: datetime | None = None
    status: str = "started"
    context_ready: bool = False
    user_source: str | None = None
    response_user_count: int = 0
    event_user_count: int = 0
    assistant_message_count: int = 0
    user_messages: list[dict[str, Any]] = field(default_factory=list)
    assistant_messages: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: int = 0
    failure_signals: int = 0
    duration_ms: int | None = None
    tool_events: list[dict[str, Any]] = field(default_factory=list)
    tool_outputs: list[dict[str, Any]] = field(default_factory=list)
    event_source_lines: list[int] = field(default_factory=list)


@dataclass
class SessionStats:
    source: str
    session_id: str = ""
    timestamp: datetime | None = None
    cwd: str | None = None
    branch: str | None = None
    tools: Counter[str] = field(default_factory=Counter)
    models: Counter[str] = field(default_factory=Counter)
    efforts: Counter[str] = field(default_factory=Counter)
    completed_turns: int = 0
    aborted_turns: int = 0
    failure_signals: int = 0
    durations_ms: list[int] = field(default_factory=list)
    total_tokens: dict[str, int] = field(default_factory=dict)
    turns: list[TurnStats] = field(default_factory=list)

    @property
    def tool_calls(self) -> int:
        return sum(self.tools.values())


def parse_session(
    path: Path,
    codex_home: Path,
    since: datetime | None,
    until: datetime | None,
    errors: list[str],
    capture_interaction_text: bool = False,
    capture_tool_outputs: bool = False,
    max_capture_chars: int = 2000,
) -> SessionStats:
    session = SessionStats(source=relative_source(path, codex_home))
    current_turn: TurnStats | None = None
    turns_by_id: dict[str, TurnStats] = {}
    for record in load_json_lines(path, errors):
        record_type = record.get("type")
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue

        if record_type == "session_meta":
            if not session.session_id:
                session.session_id = str(payload.get("id") or payload.get("session_id") or path.stem)
                session.timestamp = parse_timestamp(payload.get("timestamp")) or session.timestamp
                session.cwd = payload.get("cwd") if isinstance(payload.get("cwd"), str) else session.cwd
                git = payload.get("git")
                if isinstance(git, dict):
                    session.branch = git.get("branch") if isinstance(git.get("branch"), str) else None
            continue

        record_timestamp = parse_timestamp(record.get("timestamp"))
        if record_timestamp and not in_interval(record_timestamp, since, until):
            continue

        if record_type == "turn_context":
            turn_id = payload.get("turn_id")
            if isinstance(turn_id, str) and turn_id:
                current_turn = turns_by_id.get(turn_id, current_turn)
            if current_turn:
                current_turn.context_ready = True
            model = payload.get("model")
            effort = payload.get("effort")
            if isinstance(model, str) and model:
                session.models[model] += 1
            if isinstance(effort, str) and effort:
                session.efforts[effort] += 1
            continue

        nested_type = payload.get("type")
        if record_type == "event_msg" and nested_type == "task_started":
            turn_id = str(payload.get("turn_id") or f"synthetic-{len(session.turns) + 1}")
            current_turn = TurnStats(
                turn_id=turn_id,
                started_at=parse_timestamp(payload.get("started_at")) or record_timestamp,
                event_source_lines=[record.get("_source_line")],
            )
            session.turns.append(current_turn)
            turns_by_id[turn_id] = current_turn
            continue
        if record_type == "response_item" and nested_type == "message":
            role = payload.get("role")
            if role == "user":
                if (
                    current_turn
                    and current_turn.context_ready
                    and current_turn.response_user_count == 0
                ):
                    text = message_text(payload)
                    if text:
                        current_turn.response_user_count += 1
                        if capture_interaction_text:
                            current_turn.user_messages.append(
                                {
                                    "text": text[:max_capture_chars],
                                    "timestamp": iso_or_none(record_timestamp),
                                    "source_line": record.get("_source_line"),
                                    "truncated": len(text) > max_capture_chars,
                                }
                            )
            elif role == "assistant" and current_turn and current_turn.context_ready:
                text = message_text(payload)
                if text:
                    current_turn.assistant_message_count += 1
                    if capture_interaction_text:
                        current_turn.assistant_messages.append(
                            {
                                "phase": payload.get("phase"),
                                "text": text[:max_capture_chars],
                                "source_line": record.get("_source_line"),
                                "truncated": len(text) > max_capture_chars,
                            }
                        )
            continue
        if record_type == "event_msg" and nested_type == "user_message":
            text = payload.get("message")
            if isinstance(text, str) and text:
                if current_turn is None or current_turn.status != "started":
                    turn_id = str(payload.get("turn_id") or f"synthetic-{len(session.turns) + 1}")
                    current_turn = TurnStats(turn_id=turn_id, started_at=record_timestamp)
                    session.turns.append(current_turn)
                    turns_by_id[turn_id] = current_turn
                current_turn.event_user_count += 1
                if capture_interaction_text:
                    current_turn.user_messages.append(
                        {
                            "text": text[:max_capture_chars],
                            "timestamp": iso_or_none(record_timestamp),
                            "source_line": record.get("_source_line"),
                            "source": "event_msg",
                            "truncated": len(text) > max_capture_chars,
                        }
                    )
            continue
        if record_type == "response_item" and nested_type in {"function_call", "custom_tool_call"}:
            name = payload.get("name")
            tool_name = name if isinstance(name, str) and name else "unknown"
            session.tools[tool_name] += 1
            if current_turn:
                current_turn.tool_calls += 1
                current_turn.event_source_lines.append(record.get("_source_line"))
                current_turn.tool_events.append(
                    {
                        "name": tool_name,
                        "source_line": record.get("_source_line"),
                    }
                )
        elif record_type == "response_item" and nested_type in {"function_call_output", "custom_tool_call_output"}:
            raw_output = payload.get("output")
            failed = has_failure_signal(raw_output)
            if current_turn and capture_tool_outputs:
                output = flatten_text(raw_output)
                current_turn.tool_outputs.append(
                    {
                        "source_line": record.get("_source_line"),
                        "failed": failed,
                        "output": output[:max_capture_chars],
                        "truncated": len(output) > max_capture_chars,
                    }
                )
            if failed:
                session.failure_signals += 1
                if current_turn:
                    current_turn.failure_signals += 1
                    current_turn.event_source_lines.append(record.get("_source_line"))
        elif record_type == "event_msg" and nested_type == "task_complete":
            session.completed_turns += 1
            turn_id = payload.get("turn_id")
            target_turn = turns_by_id.get(turn_id) if isinstance(turn_id, str) else current_turn
            duration = payload.get("duration_ms")
            if target_turn:
                target_turn.status = "completed"
                target_turn.duration_ms = int(duration) if isinstance(duration, (int, float)) and duration >= 0 else None
                target_turn.event_source_lines.append(record.get("_source_line"))
            if isinstance(duration, (int, float)) and duration >= 0:
                session.durations_ms.append(int(duration))
        elif record_type == "event_msg" and nested_type == "turn_aborted":
            session.aborted_turns += 1
            turn_id = payload.get("turn_id")
            target_turn = turns_by_id.get(turn_id) if isinstance(turn_id, str) else current_turn
            duration = payload.get("duration_ms")
            if target_turn:
                target_turn.status = "aborted"
                target_turn.duration_ms = int(duration) if isinstance(duration, (int, float)) and duration >= 0 else None
                target_turn.event_source_lines.append(record.get("_source_line"))
            if isinstance(duration, (int, float)) and duration >= 0:
                session.durations_ms.append(int(duration))
        elif record_type == "event_msg" and nested_type == "token_count":
            info = payload.get("info")
            totals = info.get("total_token_usage") if isinstance(info, dict) else None
            if isinstance(totals, dict):
                session.total_tokens = {
                    key: int(value)
                    for key, value in totals.items()
                    if isinstance(value, (int, float)) and value >= 0
                }
    if not session.session_id:
        session.session_id = path.stem
    for turn in session.turns:
        response_messages = [item for item in turn.user_messages if item.get("source") != "event_msg"]
        if turn.response_user_count:
            turn.user_messages = response_messages
            turn.user_source = "response_item"
        elif turn.event_user_count:
            turn.user_source = "event_msg"
    return session


def collect_history(
    path: Path,
    since: datetime | None,
    until: datetime | None,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    if not path.is_file():
        errors.append(f"{path}: history source not found")
        return sessions

    for record in load_json_lines(path, errors):
        session_id = record.get("session_id")
        timestamp = parse_timestamp(record.get("ts"))
        if not isinstance(session_id, str) or not in_interval(timestamp, since, until):
            continue
        entry = sessions.setdefault(
            session_id,
            {"count": 0, "first": None, "last": None, "dates": set()},
        )
        entry["count"] += 1
        if timestamp:
            entry["dates"].add(timestamp.date().isoformat())
            if entry["first"] is None or timestamp < entry["first"]:
                entry["first"] = timestamp
            if entry["last"] is None or timestamp > entry["last"]:
                entry["last"] = timestamp
    return sessions


def turn_summary(session: SessionStats, turn: TurnStats) -> dict[str, Any]:
    user_message_count = turn.response_user_count or turn.event_user_count
    return {
        "session_id": session.session_id,
        "session_source": session.source,
        "cwd": session.cwd,
        "branch": session.branch,
        "turn_id": turn.turn_id,
        "started_at": iso_or_none(turn.started_at),
        "status": turn.status,
        "context_ready": turn.context_ready,
        "user_message_count": user_message_count,
        "assistant_message_count": turn.assistant_message_count,
        "tool_calls": turn.tool_calls,
        "tool_failure_signals": turn.failure_signals,
        "duration_ms": turn.duration_ms,
        "source_lines": sorted({line for line in turn.event_source_lines if isinstance(line, int)}),
    }


def build_turn_index(parsed_sessions: list[SessionStats], top: int) -> list[dict[str, Any]]:
    minimum_time = datetime.min.replace(tzinfo=timezone.utc)
    rows = [turn_summary(session, turn) for session in parsed_sessions for turn in session.turns]
    rows.sort(
        key=lambda item: parse_timestamp(item["started_at"]) or minimum_time,
        reverse=True,
    )
    return rows[:top]


def build_lifecycle_candidate_index(
    parsed_sessions: list[SessionStats], top: int
) -> list[dict[str, Any]]:
    minimum_time = datetime.min.replace(tzinfo=timezone.utc)
    rows: list[dict[str, Any]] = []
    for session in parsed_sessions:
        if any(turn.status == "started" for turn in session.turns):
            continue
        candidates = [
            turn
            for turn in session.turns
            if turn.status == "completed"
            and (turn.response_user_count or turn.event_user_count)
            and turn.assistant_message_count
        ]
        if not candidates:
            continue
        anchor = max(candidates, key=lambda turn: turn.started_at or minimum_time)
        rows.append(
            {
                **turn_summary(session, anchor),
                "session_completed_turns": session.completed_turns,
                "session_aborted_turns": session.aborted_turns,
            }
        )
    rows.sort(
        key=lambda item: parse_timestamp(item["started_at"]) or minimum_time,
        reverse=True,
    )
    return rows[:top]


def select_turn_window(
    session: SessionStats, anchor_turn_id: str, before: int, after: int
) -> list[TurnStats]:
    for index, turn in enumerate(session.turns):
        if turn.turn_id == anchor_turn_id:
            return session.turns[max(0, index - before) : index + after + 1]
    raise ValueError(f"anchor turn not found in selected session: {anchor_turn_id}")


def bounded_text_item(item: dict[str, Any], max_chars: int) -> dict[str, Any]:
    text = item.get("text", "")
    return {
        **{key: value for key, value in item.items() if key != "text"},
        "text": text[:max_chars],
        "truncated": bool(item.get("truncated")) or len(text) > max_chars,
    }


def build_interaction_evidence(
    session: SessionStats,
    anchor_turn_id: str,
    before: int,
    after: int,
    max_message_chars: int,
    include_tool_details: bool,
) -> dict[str, Any]:
    window = select_turn_window(session, anchor_turn_id, before, after)
    return {
        "selection": {
            "session_id": session.session_id,
            "session_source": session.source,
            "anchor_turn": anchor_turn_id,
            "turns_before": before,
            "turns_after": after,
            "boundary_note": "This is an adjacent turn window, not a machine-inferred task boundary.",
        },
        "turns": [
            {
                **turn_summary(session, turn),
                "user_message_source": turn.user_source,
                "user_messages": [bounded_text_item(item, max_message_chars) for item in turn.user_messages],
                "assistant_messages": [
                    bounded_text_item(item, max_message_chars) for item in turn.assistant_messages
                ],
                "tool_events": turn.tool_events,
                **(
                    {
                        "tool_outputs": [
                            {
                                "source_line": item["source_line"],
                                "failed": item["failed"],
                                "output": item["output"][:max_message_chars],
                                "truncated": bool(item.get("truncated"))
                                or len(item["output"]) > max_message_chars,
                            }
                            for item in turn.tool_outputs
                        ]
                    }
                    if include_tool_details
                    else {}
                ),
            }
            for turn in window
        ],
    }


def counter_rows(counter: Counter[str], top: int) -> list[dict[str, Any]]:
    total = sum(counter.values())
    return [
        {"name": name, "count": count, "share": round(count / total, 4) if total else 0}
        for name, count in counter.most_common(top)
    ]


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * fraction)
    return ordered[index]


def analyze(args: argparse.Namespace) -> dict[str, Any]:
    codex_home = Path(args.codex_home).expanduser().resolve()
    history_path = codex_home / "history.jsonl"
    sessions_dir = codex_home / "sessions"
    errors: list[str] = []

    since = None
    if args.since:
        since = parse_boundary(args.since)
        if since is None:
            raise ValueError(f"invalid --since value: {args.since}")
    elif not args.all_time:
        since = utc_now() - timedelta(days=args.since_days)
    until = parse_boundary(args.until, end_of_day=True) if args.until else None
    if args.until and until is None:
        raise ValueError(f"invalid --until value: {args.until}")
    if since and until and since > until:
        raise ValueError("--since must not be later than --until")

    history = collect_history(history_path, since, until, errors)
    requested_session_ids = set(args.session_id)

    parsed_sessions: list[SessionStats] = []
    if sessions_dir.is_dir():
        history_session_suffixes = tuple(f"{session_id}.jsonl" for session_id in history)
        requested_session_suffixes = tuple(f"{session_id}.jsonl" for session_id in requested_session_ids)
        for path in sorted(sessions_dir.glob("**/*.jsonl")):
            path_date = session_path_date(path, sessions_dir)
            requested_session_in_path = bool(requested_session_suffixes) and path.name.endswith(
                requested_session_suffixes
            )
            history_session_in_path = bool(history_session_suffixes) and path.name.endswith(
                history_session_suffixes
            )
            if (
                path_date
                and since
                and path_date < since.date() - timedelta(days=1)
                and not history_session_in_path
                and not requested_session_in_path
            ):
                continue
            if (
                path_date
                and until
                and path_date > until.date() + timedelta(days=1)
                and not history_session_in_path
                and not requested_session_in_path
            ):
                continue
            parse_since = None if requested_session_in_path else since
            parse_until = None if requested_session_in_path else until
            capture_interaction = bool(
                args.include_interaction_evidence and requested_session_in_path
            )
            session = parse_session(
                path,
                codex_home,
                parse_since,
                parse_until,
                errors,
                capture_interaction_text=capture_interaction,
                capture_tool_outputs=capture_interaction and args.include_tool_details,
                max_capture_chars=args.max_message_chars,
            )
            fallback_time = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
            if (
                not in_interval(session.timestamp or fallback_time, since, until)
                and session.session_id not in history
                and session.session_id not in requested_session_ids
            ):
                continue
            if requested_session_ids and session.session_id not in requested_session_ids:
                continue
            if matches_project(session.cwd, args.project):
                parsed_sessions.append(session)
    else:
        errors.append(f"{sessions_dir}: session source not found")

    selected_ids = {session.session_id for session in parsed_sessions}
    if args.project or requested_session_ids:
        selected_history = {key: value for key, value in history.items() if key in selected_ids}
    else:
        selected_history = history

    project_counter: Counter[str] = Counter()
    tool_counter: Counter[str] = Counter()
    model_counter: Counter[str] = Counter()
    effort_counter: Counter[str] = Counter()
    branch_counter: Counter[str] = Counter()
    durations: list[int] = []
    token_totals: Counter[str] = Counter()
    active_dates: set[str] = set()

    for session in parsed_sessions:
        project_counter[session.cwd or "unknown"] += 1
        tool_counter.update(session.tools)
        model_counter.update(session.models)
        effort_counter.update(session.efforts)
        branch_counter[session.branch or "unknown"] += 1
        durations.extend(session.durations_ms)
        token_totals.update(session.total_tokens)
        if session.timestamp and in_interval(session.timestamp, since, until):
            active_dates.add(session.timestamp.date().isoformat())
    for item in selected_history.values():
        active_dates.update(item["dates"])

    history_times = [
        item[key]
        for item in selected_history.values()
        for key in ("first", "last")
        if item[key] is not None
    ]
    history_times.extend(
        session.timestamp
        for session in parsed_sessions
        if session.timestamp is not None and in_interval(session.timestamp, since, until)
    )
    session_index = []
    minimum_time = datetime.min.replace(tzinfo=timezone.utc)
    ordered_sessions = sorted(
        parsed_sessions,
        key=lambda item: (item.tool_calls, item.timestamp or minimum_time),
        reverse=True,
    )
    for session in ordered_sessions[: args.top]:
        history_entry = selected_history.get(session.session_id, {})
        session_index.append(
            {
                "session_id": session.session_id,
                "source": session.source,
                "timestamp": iso_or_none(session.timestamp),
                "cwd": session.cwd,
                "branch": session.branch,
                "history_messages": history_entry.get("count", 0),
                "tool_calls": session.tool_calls,
                "tool_failure_signals": session.failure_signals,
                "completed_turns": session.completed_turns,
                "aborted_turns": session.aborted_turns,
                "duration_ms": sum(session.durations_ms),
                "total_tokens": session.total_tokens.get("total_tokens"),
                "top_tools": counter_rows(session.tools, 5),
            }
        )

    structured_user_messages = sum(
        turn.response_user_count or turn.event_user_count
        for session in parsed_sessions
        for turn in session.turns
    )
    result: dict[str, Any] = {
        "generated_at": iso_or_none(utc_now()),
        "scope": {
            "codex_home": str(codex_home),
            "since": iso_or_none(since),
            "until": iso_or_none(until),
            "all_time": args.all_time,
            "project_filters": args.project,
            "selected_session_full_context": bool(requested_session_ids),
            "interaction_evidence_included": args.include_interaction_evidence,
            "tool_output_scanned_for_failure_signals": True,
        },
        "sources": {
            "history": str(history_path),
            "sessions": str(sessions_dir),
            "session_files_analyzed": len(parsed_sessions),
        },
        "totals": {
            "history_messages": sum(item["count"] for item in selected_history.values()),
            "history_sessions": len(selected_history),
            "session_files": len(parsed_sessions),
            "active_dates": len(active_dates),
            "first_activity": iso_or_none(min(history_times)) if history_times else None,
            "last_activity": iso_or_none(max(history_times)) if history_times else None,
            "tool_calls": sum(session.tool_calls for session in parsed_sessions),
            "tool_failure_signals": sum(session.failure_signals for session in parsed_sessions),
            "completed_turns": sum(session.completed_turns for session in parsed_sessions),
            "aborted_turns": sum(session.aborted_turns for session in parsed_sessions),
            "structured_user_messages": structured_user_messages,
            "history_and_structured_message_difference": (
                sum(item["count"] for item in selected_history.values()) - structured_user_messages
            ),
            "duration_ms": sum(durations),
            "median_turn_duration_ms": int(statistics.median(durations)) if durations else None,
            "p90_turn_duration_ms": percentile(durations, 0.9),
            "tokens": dict(sorted(token_totals.items())),
        },
        "breakdowns": {
            "projects": counter_rows(project_counter, args.top),
            "tools": counter_rows(tool_counter, args.top),
            "models": counter_rows(model_counter, args.top),
            "efforts": counter_rows(effort_counter, args.top),
            "branches": counter_rows(branch_counter, args.top),
        },
        "session_index": session_index,
        "turn_index": build_turn_index(parsed_sessions, args.turn_index_top),
        "lifecycle_candidate_index": build_lifecycle_candidate_index(
            parsed_sessions, args.candidate_index_top
        ),
        "data_quality": {
            "issue_count": len(errors),
            "issues": errors[: args.top],
            "issues_truncated": len(errors) > args.top,
            "failure_signal_note": "Signals require session inspection; expected negative tests and recovered commands can match.",
            "token_note": "Token records are cumulative per session and can include usage before the selected interval when a session spans the boundary.",
            "selected_session_scope_note": (
                "Exact --session-id selections are parsed as complete sessions so adjacent turns "
                "remain available even when they cross the inventory interval. Selected-session "
                "totals and turn_index can therefore include activity outside that interval."
                if requested_session_ids
                else None
            ),
            "message_source_note": (
                "history.jsonl provides coverage counts only. The analyzer does not match its text "
                "to session records. Selected interaction evidence uses structurally associated user "
                "messages after turn_context, or event_msg.user_message for older session formats."
            ),
        },
    }
    if args.include_interaction_evidence:
        if len(requested_session_ids) != 1 or not args.anchor_turn:
            raise ValueError("--include-interaction-evidence requires exactly one --session-id and --anchor-turn")
        selected_session = next(
            (session for session in parsed_sessions if session.session_id in requested_session_ids), None
        )
        if selected_session is None:
            raise ValueError(f"selected session not found: {next(iter(requested_session_ids))}")
        result["interaction_evidence"] = build_interaction_evidence(
            selected_session,
            args.anchor_turn,
            args.turn_before,
            args.turn_after,
            args.max_message_chars,
            args.include_tool_details,
        )
    if args.evidence_only:
        return {
            "generated_at": result["generated_at"],
            "scope": result["scope"],
            "interaction_evidence": result["interaction_evidence"],
            "data_quality": result["data_quality"],
        }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Codex data directory; defaults to CODEX_HOME or the current user's .codex directory.",
    )
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--since", help="Inclusive ISO date or timestamp lower bound.")
    scope.add_argument("--all-time", action="store_true", help="Analyze all available history.")
    parser.add_argument("--since-days", type=int, default=1, help="Default inventory lookback when --since and --all-time are absent.")
    parser.add_argument("--until", help="Inclusive ISO date or timestamp upper bound.")
    parser.add_argument("--project", action="append", default=[], help="Working-directory path or basename filter; repeatable.")
    parser.add_argument("--session-id", action="append", default=[], help="Exact session identifier; repeatable for inventory filtering.")
    parser.add_argument("--anchor-turn", help="Exact turn identifier used as the center of an interaction-evidence window.")
    parser.add_argument(
        "--include-interaction-evidence",
        action="store_true",
        help="Include bounded adjacent turns around --anchor-turn for Codex semantic review.",
    )
    parser.add_argument("--evidence-only", action="store_true", help="Return only the selected interaction window and data-quality notes.")
    parser.add_argument("--include-tool-details", action="store_true", help="Include bounded tool outputs in the selected interaction window.")
    parser.add_argument("--turn-before", type=int, default=3, help="Adjacent turns before the selected anchor.")
    parser.add_argument("--turn-after", type=int, default=2, help="Adjacent turns after the selected anchor.")
    parser.add_argument("--turn-index-top", type=int, default=50, help="Maximum recent text-free turn rows in the inventory.")
    parser.add_argument("--candidate-index-top", type=int, default=30, help="Maximum text-free lifecycle candidates, with at most one completed anchor per session.")
    parser.add_argument("--max-message-chars", type=int, default=2000, help="Maximum characters per message or tool output in selected evidence.")
    parser.add_argument("--top", type=int, default=10, help="Maximum rows per breakdown and session index.")
    parser.add_argument("--output", type=Path, help="Write JSON to this path instead of standard output.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.since_days < 1:
        parser.error("--since-days must be at least 1")
    if args.max_message_chars < 1:
        parser.error("--max-message-chars must be at least 1")
    if args.top < 1:
        parser.error("--top must be at least 1")
    if args.turn_before < 0 or args.turn_after < 0:
        parser.error("--turn-before and --turn-after must be nonnegative")
    if args.turn_index_top < 1:
        parser.error("--turn-index-top must be at least 1")
    if args.candidate_index_top < 1:
        parser.error("--candidate-index-top must be at least 1")
    if args.evidence_only and not args.include_interaction_evidence:
        parser.error("--evidence-only requires --include-interaction-evidence")
    try:
        result = analyze(args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
