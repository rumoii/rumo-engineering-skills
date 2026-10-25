#!/usr/bin/env python3
"""List and condense this project's recent Claude Code, Codex, and Kimi Code sessions so a new session can pick up the work.

Read-only. Only sessions whose working directory is this project (the given
directory or its Git root) are opened; other projects' sessions are never read.
`show` keeps the user's messages, each turn's final reply, and the latest
compaction summary, and drops tool output and injected context.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

CODEX_SCAN_LIMIT = 500
# Tags whose blocks the client injects into user turns; they are not the user's words.
INJECTED_TAGS = ("system-reminder", "local-command-caveat", "local-command-stdout", "local-command-stderr",
                 "command-message", "task-notification", "user-prompt-submit-hook", "environment_context",
                 "user_instructions", "INSTRUCTIONS", "turn_aborted")
INJECTED_RE = re.compile(r"<(%s)\b[^>]*>.*?</\1>" % "|".join(INJECTED_TAGS), re.S)
# Tools whose results carry the user's own decision.
DECISION_TOOLS = ("AskUserQuestion", "ExitPlanMode")
SKILL_LOADED_RE = re.compile(r"<skill-loaded\b")
COMMAND_RE = re.compile(r"<command-name>(.*?)</command-name>(?:.*?<command-args>(.*?)</command-args>)?", re.S)


class DigestError(Exception):
    """The request cannot be answered from this project's sessions."""


def norm(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(path))).rstrip("\\/")


def project_roots(cwd: Path) -> set[str]:
    roots = {norm(cwd)}
    try:
        top = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=10)
        if top.returncode == 0 and top.stdout.strip():
            roots.add(norm(top.stdout.strip()))
    except (OSError, subprocess.TimeoutExpired):
        pass
    return roots


def home(env: str, default: str) -> Path:
    return Path(os.environ.get(env) or Path.home() / default)


def read_lines(path: Path):
    """Yield parsed JSON lines, skipping a partial or malformed line such as the one a live session is writing."""
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def clean(text: str) -> str:
    command = COMMAND_RE.search(text)
    text = INJECTED_RE.sub("", text)
    text = COMMAND_RE.sub("", text).replace("<command-args></command-args>", "").strip()
    if command and not text:
        return " ".join(part.strip() for part in command.groups() if part and part.strip())
    return text


def texts(content: object, kinds: tuple[str, ...]) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") in kinds)
    return ""


def decision_text(tool: object, result: str) -> str:
    """The user's answer to a question box or plan approval; these arrive as tool results, not user messages."""
    if tool == "ExitPlanMode":
        if "approved your plan" in result:
            saved = re.search(r"saved to: (.+)", result)
            return "plan approved" + (f": {saved.group(1).strip()}" if saved else "")
        return "plan not approved: " + result.strip().splitlines()[0] if result.strip() else "plan not approved"
    return result.strip()


def claude_files(roots: set[str]) -> list[Path]:
    projects = home("CLAUDE_CONFIG_DIR", ".claude") / "projects"
    if not projects.is_dir():
        return []
    wanted = {re.sub(r"[^A-Za-z0-9]", "-", root).lower() for root in roots}
    files = []
    for directory in projects.iterdir():
        if directory.is_dir() and directory.name.lower() in wanted:
            files += [path for path in directory.glob("*.jsonl") if path.is_file()]
    return files


def codex_files(roots: set[str], prefix: str | None = None, needed: int | None = None) -> tuple[list[Path], bool]:
    sessions = home("CODEX_HOME", ".codex") / "sessions"
    if not sessions.is_dir():
        return [], False
    newest = sorted(sessions.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    files = []
    truncated = False
    for index, path in enumerate(newest):
        if prefix is None and index >= CODEX_SCAN_LIMIT:
            truncated = True
            break
        try:
            with path.open(encoding="utf-8", errors="replace") as handle:
                first = json.loads(handle.readline() or "{}")
        except (OSError, json.JSONDecodeError):
            continue
        payload = first.get("payload") if first.get("type") == "session_meta" else None
        if not isinstance(payload, dict) or not payload.get("cwd") or norm(payload["cwd"]) not in roots:
            continue
        session_id = str(payload.get("id") or path.stem)
        if prefix is None or session_id.startswith(prefix):
            files.append(path)
            if needed is not None and len(files) >= needed:
                break
    return files, truncated


def kimi_files(roots: set[str], prefix: str | None = None) -> list[Path]:
    index = home("KIMI_CODE_HOME", ".kimi-code") / "session_index.jsonl"
    if not index.is_file():
        return []
    files = {}
    for record in read_lines(index):
        work_dir = record.get("workDir")
        session_dir = record.get("sessionDir")
        session_id = record.get("sessionId")
        if not isinstance(work_dir, str) or norm(work_dir) not in roots:
            continue
        if not isinstance(session_dir, str) or not isinstance(session_id, str):
            continue
        if prefix is not None and not session_id.startswith(prefix):
            continue
        wire = Path(session_dir) / "agents" / "main" / "wire.jsonl"
        if wire.is_file():
            files[norm(wire)] = wire
    return list(files.values())


def parse_claude(path: Path) -> dict:
    session = {"client": "claude", "id": path.stem, "title": None, "headless": False, "entries": []}
    entries, pending, cwds = session["entries"], [], set()
    decisions: dict[object, object] = {}  # open AskUserQuestion / ExitPlanMode calls by tool-use ID

    def flush() -> None:
        if pending:
            entries.append({"kind": "agent", "time": pending[-1][0], "text": "\n".join(text for _, text in pending)})
            pending.clear()

    for record in read_lines(path):
        kind = record.get("type")
        if kind == "ai-title":
            session["title"] = record.get("aiTitle")
        if record.get("isSidechain") or kind not in ("user", "assistant"):
            continue
        if record.get("cwd"):
            cwds.add(norm(record["cwd"]))
        if record.get("entrypoint") == "sdk-cli":
            session["headless"] = True
        content = (record.get("message") or {}).get("content")
        when = record.get("timestamp")
        if kind == "assistant":
            calls = [part for part in content if isinstance(part, dict) and part.get("type") == "tool_use"] if isinstance(content, list) else []
            if calls:
                pending.clear()
            decisions.update({call.get("id"): call.get("name") for call in calls if call.get("name") in DECISION_TOOLS})
            text = texts(content, ("text",)).strip()
            if text:
                pending.append((when, text))
            continue
        if record.get("isCompactSummary"):
            flush()
            entries.append({"kind": "summary", "time": when, "text": texts(content, ("text",)).strip()})
            continue
        if record.get("isMeta"):
            continue
        for part in content if isinstance(content, list) else []:
            tool = decisions.pop(part.get("tool_use_id"), None) if isinstance(part, dict) and part.get("type") == "tool_result" else None
            if tool:
                flush()
                entries.append({"kind": "decision", "time": when, "text": decision_text(tool, texts(part.get("content"), ("text",)))})
        text = clean(texts(content, ("text",)))
        if text:
            flush()
            entries.append({"kind": "user", "time": when, "text": text})
    flush()
    session["cwds"] = sorted(cwds)
    return session


def parse_codex(path: Path) -> dict:
    session = {"client": "codex", "id": None, "title": None, "headless": False, "entries": []}
    entries = session["entries"]
    pending: dict[str, tuple[str, str] | None] = {"final": None, "last": None}

    def flush() -> None:
        reply = pending["final"] or pending["last"]
        if reply:
            entries.append({"kind": "agent", "time": reply[0], "text": reply[1]})
        pending.update(final=None, last=None)

    for record in read_lines(path):
        payload = record.get("payload")
        if record.get("type") == "session_meta" and isinstance(payload, dict):
            session["id"] = payload.get("id")
            session["cwds"] = [norm(payload["cwd"])] if payload.get("cwd") else []
            session["headless"] = payload.get("source") == "exec" or "exec" in str(payload.get("originator", ""))
            continue
        if record.get("type") != "response_item" or not isinstance(payload, dict) or payload.get("type") != "message":
            continue
        when = record.get("timestamp")
        if payload.get("role") == "assistant":
            text = texts(payload.get("content"), ("output_text",)).strip()
            if text:
                pending["last"] = (when, text)
                if payload.get("phase") == "final_answer":
                    pending["final"] = (when, text)
        elif payload.get("role") == "user":
            parts = [clean(part.get("text", "")) for part in payload.get("content") or []
                     if isinstance(part, dict) and part.get("type") == "input_text"]
            text = "\n".join(part for part in parts if part and not part.startswith("# AGENTS.md instructions"))
            if text:
                flush()
                entries.append({"kind": "user", "time": when, "text": text})
    flush()
    session["id"] = session["id"] or path.stem
    return session


def kimi_time(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if not isinstance(value, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(value / 1000, timezone.utc).isoformat().replace("+00:00", "Z")
    except (OverflowError, OSError, ValueError):
        return None


def parse_kimi(path: Path) -> dict:
    session_dir = path.parents[2]
    try:
        state = json.loads((session_dir / "state.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        state = {}
    if not isinstance(state, dict):
        state = {}
    session = {"client": "kimi", "id": state.get("id") or session_dir.name, "title": state.get("title"),
               "headless": False, "entries": []}
    cwd = state.get("cwd")
    session["cwds"] = [norm(cwd)] if isinstance(cwd, str) and cwd else []
    entries = session["entries"]
    pending: dict[str, tuple[str, str] | None] = {"final": None, "last": None}

    def flush() -> None:
        reply = pending["final"] or pending["last"]
        if reply:
            entries.append({"kind": "agent", "time": reply[0], "text": reply[1]})
        pending.update(final=None, last=None)

    for record in read_lines(path):
        kind = record.get("type")
        when = kimi_time(record.get("time"))
        if kind == "context.apply_compaction":
            summary = record.get("summary")
            if isinstance(summary, str) and summary.strip():
                flush()
                entries.append({"kind": "summary", "time": when, "text": summary.strip()})
            continue
        if kind != "agent.message.appended":
            continue
        envelope = record.get("message")
        if not isinstance(envelope, dict):
            continue
        message = envelope.get("message")
        meta = envelope.get("meta")
        if not isinstance(message, dict) or not isinstance(meta, dict):
            continue
        role = message.get("role")
        if role == "assistant":
            text = texts(message.get("content"), ("text",)).strip()
            if text:
                pending["last"] = (when, text)
                finish = meta.get("finish")
                if isinstance(finish, dict) and finish.get("finishReason") == "completed":
                    pending["final"] = (when, text)
        elif role == "user":
            origin = meta.get("origin")
            if not isinstance(origin, dict) or origin.get("kind") != "user":
                continue
            raw_text = texts(message.get("content"), ("text",))
            # A loaded skill shares the meta of a message the user types mid-turn; only its element differs.
            if SKILL_LOADED_RE.search(raw_text):
                continue
            text = clean(raw_text)
            if text:
                flush()
                entries.append({"kind": "user", "time": kimi_time(meta.get("createdAt")) or when, "text": text})
    flush()
    return session


def sessions(cwd: Path, prefix: str | None = None, needed: int | None = None) -> tuple[list[dict], bool]:
    roots = project_roots(cwd)
    found = []
    codex, truncated = codex_files(roots, prefix, needed)
    kimi = kimi_files(roots, prefix)
    for files, parse in ((claude_files(roots), parse_claude), (codex, parse_codex), (kimi, parse_kimi)):
        for path in files:
            session = parse(path)
            if session.get("cwds") and not set(session["cwds"]) & roots:
                continue
            users = [entry for entry in session["entries"] if entry["kind"] == "user"]
            if not users:
                continue
            # Windows does not advance a file's mtime while a client keeps appending, so the last record counts too.
            stamps = [utc(entry["time"]) for entry in session["entries"]]
            moments = [datetime.fromtimestamp(path.stat().st_mtime, timezone.utc), *(stamp for stamp in stamps if stamp)]
            first = next((stamp for stamp in stamps if stamp), None)
            session.update(path=str(path), updated=max(moments).isoformat(timespec="seconds"),
                           started=first.isoformat(timespec="seconds") if first else None, user_turns=len(users))
            found.append(session)
    return sorted(found, key=lambda session: session["updated"], reverse=True), truncated


def utc(stamp: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone(timezone.utc) if stamp else None
    except ValueError:
        return None


def short(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit].rstrip() + f" …[+{len(text) - limit} chars]"


def cmd_list(args: argparse.Namespace) -> int:
    rows = []
    found, truncated = sessions(Path(args.cwd), needed=args.limit)
    for session in found[:args.limit]:
        users = [entry for entry in session["entries"] if entry["kind"] == "user"]
        rows.append({"client": session["client"], "id": session["id"], "title": session["title"], "headless": session["headless"],
                     "started": session["started"], "updated": session["updated"], "user_turns": session["user_turns"],
                     "first_user": short(users[0]["text"], 160), "last_user": short(users[-1]["text"], 160)})
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    if truncated:
        print(f"truncated: true; scanned at most {CODEX_SCAN_LIMIT} recent Codex sessions without finding enough from this project", file=sys.stderr)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    found, _ = sessions(Path(args.cwd), prefix=args.session)
    matches = [session for session in found if str(session["id"]).startswith(args.session)]
    if len(matches) != 1:
        raise DigestError(f"{len(matches)} sessions of this project match {args.session!r}; run list and pass a longer ID prefix")
    session = matches[0]
    entries = session["entries"]
    summaries = [index for index, entry in enumerate(entries) if entry["kind"] == "summary"]
    skipped = 0
    if summaries and not args.all:
        skipped, entries = summaries[-1], entries[summaries[-1]:]
    rendered = [f"[{entry['time'] or '?'}] {entry['kind']}: "
                + short(entry["text"], args.max_chars * (4 if entry["kind"] == "summary" else 1)) for entry in entries]
    while len(rendered) > 1 and sum(len(line) for line in rendered) > args.budget:
        rendered.pop(1 if entries[0]["kind"] == "summary" else 0)
        skipped += 1
    print(f"# {session['client']} session {session['id']}")
    print(f"title: {session['title'] or '-'}; started {session['started']}; updated {session['updated']}; {session['user_turns']} user turns")
    if skipped:
        print(f"({skipped} earlier entries omitted; pass --all or a larger --budget to include them)")
    print("\n\n".join(rendered))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", default=".", help="project directory (default: current directory)")
    sub = parser.add_subparsers(dest="command", required=True)
    listing = sub.add_parser("list", help="recent sessions of this project, newest first")
    listing.add_argument("--limit", type=int, default=5)
    showing = sub.add_parser("show", help="condensed timeline of one session")
    showing.add_argument("session", help="session ID or a unique prefix from list")
    showing.add_argument("--max-chars", type=int, default=1500, help="cap per message (summaries get four times this)")
    showing.add_argument("--budget", type=int, default=40000, help="cap on the whole timeline; the oldest entries go first")
    showing.add_argument("--all", action="store_true", help="include entries before the latest compaction summary")
    args = parser.parse_args()
    # Callers read the output as UTF-8; on Windows a piped stdout would otherwise use the ANSI code page.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        return cmd_list(args) if args.command == "list" else cmd_show(args)
    except (DigestError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
