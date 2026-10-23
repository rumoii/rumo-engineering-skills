#!/usr/bin/env python3
"""Run another agent CLI for one non-interactive turn, record it, and resume it by session ID.

Each CLI is described by an adapter file (JSON): the bundled ones live in
../adapters/, and user adapters in $RUMO_AGENT_ADAPTERS_DIR, else
<runs-dir>/adapters/, where a user adapter replaces a bundled one of the same
name. Subcommands: list, show, check, start, resume, status, cancel, record,
watch, wait, runs, and open (an interactive CLI in a window the user can see).

Each run lives in <runs-dir>/<run-id>/ with meta.json and one folder per turn.
The prompt travels on stdin or in a file the adapter names, never on the
command line. The caller picks read-only, workspace-write, or native-write;
an adapter that offers a level maps it to that CLI's own limits, and adapters
that contain sandbox- or approval-bypassing flags are refused.

Exit codes: 0 turn finished with a final reply; 1 the turn failed or produced
no reply; 2 refused (usage, missing CLI, adapter, level or flag, run busy or
unreconciled); 3 the turn hit the timeout and was stopped. With --detach,
start and resume return once the turn is launched (exit 0) and a detached
recorder finishes it; `watch` follows the turn and exits with the turn's code.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACCESS_LEVELS = ("read-only", "workspace-write", "native-write")
RUNNING = ("launched", "session-known", "cancelling", "interactive")
TERMINAL = ("exited", "failed", "launch-failed", "timed-out", "cancelled", "abandoned", "interrupted", "closed")
RUNS_DIR_ENV = "RUMO_AGENT_RUNS_DIR"
ADAPTERS_DIR_ENV = "RUMO_AGENT_ADAPTERS_DIR"
BUNDLED_ADAPTERS = Path(__file__).resolve().parent.parent / "adapters"
PLACEHOLDERS = {"{access}", "{session}", "{model}", "{prompt_file}", "{cwd}"}
# Only interactive_start may use these: {opening} is the script's one-line pointer to the brief file.
INTERACTIVE_PLACEHOLDERS = {"{opening}", "{run_name}"}
WINDOW_GROUP = "rumo-agents"
# How long a detached start waits for the turn to launch, and how long watch tolerates a running
# record whose process is gone before reporting it unreconciled.
DETACH_WAIT = 60
WATCH_GRACE = 60
PROGRESS_WIDTH = 300
# Substrings that mark a flag or setting which bypasses a CLI's sandbox, approvals, or tool limits.
FORBIDDEN = ("dangerous", "bypass", "yolo", "danger-full", "skip-permission", "skip_permissions", "--force", "auto-approve", "always-approve", "approve-mcps", "--allow-all", "--no-sandbox")


class Refused(Exception):
    """The requested operation cannot safely continue."""


# --- Adapters ---------------------------------------------------------------

def adapter_dirs(runs_dir: str | None) -> list[tuple[str, Path]]:
    user = Path(os.environ[ADAPTERS_DIR_ENV]) if os.environ.get(ADAPTERS_DIR_ENV) else runs_root(runs_dir) / "adapters"
    return [("bundled", BUNDLED_ADAPTERS), ("user", user)]


def forbidden_values(value: object) -> list[str]:
    """Scan templates and JSON-encoded settings, including escaped JSON strings."""
    if isinstance(value, dict):
        found = [word for item in (*value.keys(), *value.values()) for word in forbidden_values(item)]
        for key, setting in value.items():
            key = re.sub(r"[^a-z]", "", str(key).lower())
            if any(key.endswith(suffix) for suffix in ("allowall", "autoapprove", "skippermissions", "disablesandbox")) and str(setting).strip().lower() in ("true", "1", "yes", "on", "y"):
                found.append("automatic approval setting")
        return found
    if isinstance(value, list):
        found = [word for item in value for word in forbidden_values(item)]
        for index, token in enumerate(value):
            if isinstance(token, str) and token.lower().split("=", 1)[0] in ("-y", "-f", "--yes", "--yes-always"):
                found.append("automatic approval alias")
            if isinstance(token, str) and token.lower() == "--sandbox" and index + 1 < len(value) and str(value[index + 1]).lower() in ("false", "off", "disabled", "none"):
                found.append("disabled sandbox")
            if isinstance(token, str) and token.lower() in ("--sandbox=false", "--sandbox=off", "--sandbox=disabled", "--sandbox=none"):
                found.append("disabled sandbox")
        return found
    if not isinstance(value, str):
        return []
    found = [word for word in FORBIDDEN if word in value.lower()]
    try:
        decoded = json.loads(value)
    except (ValueError, RecursionError):
        return found
    if decoded != value:
        found += forbidden_values(decoded)
    return found


def string_list(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(t, str) and "\0" not in t for t in value)


def valid_rule(rule: object) -> bool:
    if not isinstance(rule, dict):
        return False
    fields = rule.get("field")
    fields = fields if isinstance(fields, list) else [fields]
    match = rule.get("match", {})
    return bool(fields) and all(isinstance(f, str) and all(f.split(".")) for f in fields) and (
        isinstance(match, dict) and all(isinstance(k, str) and all(k.split(".")) for k in match)
        and rule.get("pick", "last") in ("last", "join")
        and rule.get("transform", "text_parts") == "text_parts"
    )


def validate_adapter(adapter: object) -> list[str]:
    """Validate the declaration; this does not sandbox an arbitrary executable."""
    if not isinstance(adapter, dict):
        return ["adapter must be a JSON object"]
    problems = []
    for key in ("name", "executable", "help", "prompt", "access", "start", "session", "output"):
        if key not in adapter:
            problems.append(f"missing {key}")
    if problems:
        return problems
    if "disabled_reason" in adapter and (not isinstance(adapter["disabled_reason"], str)
            or not adapter["disabled_reason"].strip() or "\0" in adapter["disabled_reason"]):
        problems.append("disabled_reason must be a nonempty string without NUL")
    if not isinstance(adapter["name"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", adapter["name"]):
        problems.append("name must be lowercase letters, digits, or hyphens")
    if not isinstance(adapter["executable"], str) or not adapter["executable"] or any(c in adapter["executable"] for c in "\0\r\n"):
        problems.append("executable must be a nonempty program name or path")
    if adapter["prompt"] not in ("stdin", "file"):
        problems.append("prompt must be stdin or file; a prompt on the command line is not allowed")
    access = adapter["access"]
    if not isinstance(access, dict) or "read-only" not in access:
        problems.append("access must define read-only")
    elif set(access) - set(ACCESS_LEVELS):
        problems.append(f"unknown access levels: {sorted(set(access) - set(ACCESS_LEVELS))}")
    session, output = adapter["session"], adapter["output"]
    if not isinstance(session, dict) or not isinstance(output, dict):
        return problems + ["session and output must be objects"]
    source = session.get("source")
    if source not in ("preassign", "event", "none"):
        problems.append("session.source must be preassign, event, or none")
    if source != "none" and "resume" not in adapter:
        problems.append("resume is required unless session.source is none")
    if source == "event" and not valid_rule(session):
        problems.append("session event rule is invalid")
    if output.get("format") not in ("jsonl", "text"):
        problems.append("output.format must be jsonl or text")
    if output.get("format") == "text" and source == "event":
        problems.append("event sessions require jsonl output")
    if output.get("format") == "jsonl" and not valid_rule(output.get("final")):
        problems.append("output.final must be an extraction rule for jsonl")
    errors = output.get("error", [])
    errors = errors if isinstance(errors, list) else [errors]
    if not all(valid_rule(rule) for rule in errors):
        problems.append("output.error rules are invalid")
    progress = adapter.get("progress", [])
    if not isinstance(progress, list) or not all(
        valid_rule(rule) and isinstance(rule.get("label"), str) and rule["label"].strip()
        and (rule.get("label_field") is None or isinstance(rule["label_field"], str) and all(rule["label_field"].split(".")))
        for rule in progress
    ):
        problems.append("progress must be a list of extraction rules, each with a label")
    verified = adapter.get("verified")
    if verified is not None and (not isinstance(verified, dict) or not all(
        isinstance(verified.get(k), str) and verified[k] for k in ("version", "on")
    ) or not isinstance(verified.get("live_run"), bool)):
        problems.append("verified must be null or contain version, on, and boolean live_run")

    argv_parts = [adapter["start"], adapter.get("resume", []), adapter.get("model", []), adapter.get("interactive", [])]
    resume_access = adapter.get("resume_access", {})
    if not isinstance(resume_access, dict) or (resume_access and isinstance(access, dict) and set(resume_access) != set(access)):
        problems.append("resume_access must cover the same levels as access")
    for table in (access, resume_access):
        if isinstance(table, dict):
            argv_parts += list(table.values())
    for part in argv_parts:
        if not string_list(part):
            problems.append("argv templates must be lists of strings")
            continue
        for token in part:
            unknown = set(re.findall(r"\{[^{}]*\}", token)) - PLACEHOLDERS
            if unknown:
                problems.append(f"unknown placeholder {sorted(unknown)} in {token!r}")
            if "{access}" in token and token != "{access}":
                problems.append("{access} must occupy a whole argv token")
    for kind in ("start", "resume"):
        if kind not in adapter or not string_list(adapter[kind]):
            continue
        if "{access}" not in adapter[kind]:
            problems.append(f"{kind} must include {{access}}")
        if any("{model}" in t and t != "{model}" for t in adapter[kind]):
            problems.append(f"{kind} must use {{model}} as a whole token for optional model flags")
        if (source == "preassign" or kind == "resume" and source == "event") and not any("{session}" in t for t in adapter[kind]):
            problems.append(f"{kind} must pass {{session}} for this session source")
    if string_list(adapter.get("model", [])) and any(
        placeholder != "{model}" for token in adapter.get("model", []) for placeholder in re.findall(r"\{[^{}]*\}", token)
    ):
        problems.append("model flags may substitute only {model}")
    for table in (access, resume_access):
        if isinstance(table, dict) and any("{" in t or "}" in t for p in table.values() if string_list(p) for t in p):
            problems.append("access flags must be literal tokens")
    envs = [adapter.get("env", {})]
    access_env = adapter.get("access_env", {})
    if not isinstance(access_env, dict) or (isinstance(access, dict) and set(access_env) - set(access)):
        problems.append("access_env must map offered access levels to environments")
    elif isinstance(access_env, dict):
        envs += list(access_env.values())
    for env in envs:
        if not isinstance(env, dict) or not all(
            isinstance(k, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", k)
            and isinstance(v, str) and "\0" not in v for k, v in env.items()
        ):
            problems.append("env and access_env entries must map environment names to strings")
    help_items = adapter["help"]
    if not isinstance(help_items, list) or not help_items:
        problems.append("help must be a nonempty list")
        help_items = []
    for item in help_items:
        if not isinstance(item, dict) or not string_list(item.get("args")) or not string_list(item.get("flags")):
            problems.append("each help entry needs args and flags lists")
            continue
        args = item["args"]
        if not args or args[-1] != "--help" or any(not re.fullmatch(r"[a-z0-9][a-z0-9-]*", t) for t in args[:-1]):
            problems.append("help args must be literal subcommands followed by --help")
        argv_parts.append(args)
    interactive_start = adapter.get("interactive_start")
    if interactive_start is not None:
        if not string_list(interactive_start):
            problems.append("interactive_start must be a list of strings")
            interactive_start = []
        for token in interactive_start:
            unknown = set(re.findall(r"\{[^{}]*\}", token)) - PLACEHOLDERS - INTERACTIVE_PLACEHOLDERS
            if unknown:
                problems.append(f"unknown placeholder {sorted(unknown)} in {token!r}")
            for placeholder in ("{access}", "{model}", *INTERACTIVE_PLACEHOLDERS):
                if placeholder in token and token != placeholder:
                    problems.append(f"{placeholder} must occupy a whole argv token in interactive_start")
        if interactive_start and not {"{access}", "{opening}", "{session}"} <= set(interactive_start):
            problems.append("interactive_start must include {access}, {session}, and {opening}")
        if interactive_start and source != "preassign":
            # The report is read back by resuming the same session headlessly after the window closes.
            problems.append("interactive_start requires a preassigned session")
    for word in sorted(set(forbidden_values([argv_parts, envs, interactive_start or []]))):
        problems.append(f"contains a sandbox or approval bypass ({word!r})")
    if adapter["prompt"] == "file":
        for name in ("start", "resume"):
            if name in adapter and string_list(adapter[name]) and not any("{prompt_file}" in t for t in adapter[name]):
                problems.append(f"{name} must pass {{prompt_file}} when prompt is file")
    return problems


def load_adapters(runs_dir: str | None) -> dict[str, dict]:
    """Every adapter by name, later sources replacing earlier ones; invalid ones carry their problems."""
    found: dict[str, dict] = {}
    for source, directory in adapter_dirs(runs_dir):
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            try:
                adapter = json.loads(path.read_text(encoding="utf-8"))
                problems = validate_adapter(adapter)
            except (ValueError, OSError, RecursionError) as exc:
                adapter, problems = {}, [f"invalid JSON: {exc}"]
            name = adapter.get("name") if isinstance(adapter, dict) else None
            name = name if isinstance(name, str) and name else path.stem
            if not isinstance(adapter, dict):
                adapter = {}
            found[name] = {
                "adapter": adapter, "problems": problems, "source": source, "path": str(path),
                "overrides_bundled": source == "user" and found.get(name, {}).get("source") == "bundled",
            }
    return found


def disabled_reason(adapter: dict) -> str | None:
    if "disabled_reason" not in adapter:
        return None
    reason = adapter["disabled_reason"]
    return reason.strip() if isinstance(reason, str) and reason.strip() and "\0" not in reason else "invalid disabled_reason"


def run_disabled_reason(meta: dict, run_dir: Path) -> str | None:
    # Only the current disable decision applies to snapshots, never new argv or access settings.
    saved = disabled_reason(meta["adapter"])
    current = load_adapters(str(run_dir.parent)).get(meta["cli"])
    return saved or (disabled_reason(current["adapter"]) if current else None)


def get_adapter(name: str, runs_dir: str | None, *, allow_disabled: bool = False) -> dict:
    entry = load_adapters(runs_dir).get(name)
    if entry is None:
        raise Refused(f"no adapter named {name!r}; see references/adapters.md to add one")
    if entry["problems"]:
        raise Refused(f"adapter {entry['path']} is unusable: {'; '.join(entry['problems'])}")
    if not allow_disabled and (reason := disabled_reason(entry["adapter"])):
        raise Refused(f"adapter {name!r} is disabled: {reason}")
    return entry


def render(adapter: dict, kind: str, access: str, cwd: str, model: str | None, session: str | None, prompt_file: str | None,
           opening: str | None = None, run_name: str | None = None) -> list[str]:
    """Expand an argv template; {access} and {model} expand to whole token lists."""
    if access not in adapter["access"]:
        offered = ", ".join(adapter["access"])
        raise Refused(f"{adapter['name']} does not offer {access}; it offers {offered}")
    if kind == "resume" and adapter.get("resume_access"):
        access_tokens = adapter["resume_access"][access]
    else:
        access_tokens = adapter["access"][access]
    for name, value in (("model", model), ("session", session)):
        if value is not None and (not isinstance(value, str) or not value.strip() or value.startswith("-") or any(c in value for c in '\0\r\n"&|^%!')):
            raise Refused(f"{name} must be a nonempty identifier, not an option")
    values = {"{session}": session or "", "{cwd}": cwd, "{prompt_file}": prompt_file or "", "{model}": model or "", "{run_name}": run_name or ""}
    argv: list[str] = []
    for token in adapter[kind]:
        if token == "{access}":
            argv += access_tokens
        elif token == "{model}":
            argv += [t.replace("{model}", model) for t in adapter.get("model", [])] if model else []
        elif token == "{opening}":
            argv.append(opening or "")
        else:
            argv.append(re.sub(r"\{(?:session|cwd|prompt_file|model|run_name)\}", lambda m: values[m[0]], token))
    # Paths and model IDs are data: do not reject innocent words inside them as bypass flags.
    if any("\0" in t for t in argv):
        raise Refused("argv contains a NUL character")
    if any(forbidden_values(argv[i:i + 2] if t.lower() == "--sandbox" else [t]) for i, t in enumerate(argv) if t.startswith("-")):
        raise Refused("rendered argv contains a sandbox or approval bypass")
    return argv


def child_environment(adapter: dict, access: str) -> dict[str, str]:
    overrides = {**adapter.get("env", {}), **adapter.get("access_env", {}).get(access, {})}
    if os.name == "nt":
        overrides = {key.upper(): value for key, value in overrides.items()}
    return {**os.environ, **overrides}


# --- Output parsing ---------------------------------------------------------

def dig(event: object, path: str) -> object:
    for key in path.split("."):
        if not isinstance(event, dict) or key not in event:
            return None
        event = event[key]
    return event


def text_of(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        if all(isinstance(v, str) for v in value):
            return "\n".join(value)
        return "".join(p["text"] for p in value if isinstance(p, dict) and p.get("type") == "text" and isinstance(p.get("text"), str))
    if value is None:
        return ""
    return json.dumps(value, ensure_ascii=False)


def matches(event: dict, rule: dict) -> bool:
    return all(dig(event, path) == expected for path, expected in rule.get("match", {}).items())


def field_text(event: dict, rule: dict) -> str | None:
    """Text of the first candidate `field` that is present and nonblank."""
    for field in rule["field"] if isinstance(rule["field"], list) else [rule["field"]]:
        value = dig(event, field)
        if value not in (None, "", []):
            text = text_of(value)
            if text.strip():
                return text
    return None


def extract(events: list[dict], rule: dict) -> str | None:
    """Values of `field` (first present candidate) from events matching every `match` path."""
    values = [v for v in (field_text(e, rule) for e in events if matches(e, rule)) if v]
    if not values:
        return None
    return "".join(values) if rule.get("pick") == "join" else values[-1]


def parse_output(adapter: dict, events: list[dict], stdout_text: str, preassigned: str | None) -> dict:
    output, session_rule = adapter["output"], adapter["session"]
    if output["format"] == "text":
        final = stdout_text.strip() or None
        return {"session": preassigned if final else None, "final": final, "error": None}
    session = preassigned if events and session_rule["source"] == "preassign" else None
    if session_rule["source"] == "event":
        session = extract(events, session_rule)
    rules = output.get("error") or []
    errors = [e for e in (extract(events, r) for r in (rules if isinstance(rules, list) else [rules])) if e]
    return {"session": session, "final": extract(events, output["final"]), "error": errors[-1] if errors else None}


def progress_lines(rules: list[dict], event: dict) -> list[str]:
    """One `[label] text` line per matching progress rule, collapsed to a single line."""
    lines = []
    for rule in rules:
        text = field_text(event, rule) if matches(event, rule) else None
        if text is None:
            continue
        label, name = rule["label"], dig(event, rule["label_field"]) if rule.get("label_field") else None
        if isinstance(name, str) and name.strip():
            label += " " + name.strip()
        text = " ".join(text.split())
        lines.append(f"[{label}] {text if len(text) <= PROGRESS_WIDTH else text[:PROGRESS_WIDTH - 1] + '…'}")
    return lines


# --- Records ----------------------------------------------------------------

def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def runs_root(value: str | None) -> Path:
    root = Path(value or os.environ.get(RUNS_DIR_ENV) or Path.home() / ".rumo-agent-runs")
    return root.expanduser().resolve()


def write_json(path: Path, data: object) -> None:
    tmp = path.with_name(path.name + f".{os.getpid()}.{secrets.token_hex(4)}.tmp")
    try:
        tmp.write_bytes((json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


@contextmanager
def record_lock(run_dir: Path):
    """OS-owned lock: a crashed writer releases it without deleting a lock file."""
    if not (run_dir / "meta.json").is_file():
        raise Refused(f"no run record at {run_dir}")
    with (run_dir / ".lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        deadline = time.monotonic() + 45
        while True:
            try:
                if os.name == "nt":
                    import msvcrt
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise Refused("run record is busy; inspect status before retrying")
                time.sleep(0.02)
        try:
            yield
        finally:
            if os.name == "nt":
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_meta(run_dir: Path) -> dict:
    path = run_dir / "meta.json"
    if not path.is_file():
        raise Refused(f"no run record at {run_dir}")
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise Refused(f"cannot read run record at {run_dir}: {exc}") from exc
    if not isinstance(meta, dict) or not isinstance(meta.get("turns"), list):
        raise Refused(f"invalid run record at {run_dir}")
    return meta


def update_turn(run_dir: Path, number: int, **fields: object) -> dict:
    with record_lock(run_dir):
        meta = load_meta(run_dir)
        turn = meta["turns"][number - 1]
        if turn.get("state") in TERMINAL or (turn.get("state") == "cancelling" and fields.get("state") not in ("cancelled", "launched")):
            fields.pop("state", None)
        turn.update(fields)
        if fields.get("session_id") and number == len(meta["turns"]):
            meta["session_id"] = fields["session_id"]
        write_json(run_dir / "meta.json", meta)
        return meta


def read_events(path: Path) -> tuple[list[dict], int, str]:
    events, malformed = [], 0
    if not path.is_file():
        return events, malformed, ""
    text = path.read_bytes().decode("utf-8", errors="replace")
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except ValueError:
            malformed += 1
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            malformed += 1
    return events, malformed, text


# --- Processes --------------------------------------------------------------

def resolve_executable(adapter: dict, override: str | None) -> list[str]:
    if override:
        path = Path(override).resolve()
        if not path.is_file():
            raise Refused(f"executable not found: {override}")
        return [sys.executable, str(path)] if path.suffix.lower() == ".py" else [str(path)]
    found = shutil.which(adapter["executable"])
    if not found:
        raise Refused(f"{adapter['executable']} is not installed or not on PATH")
    return [str(Path(found).resolve())]


def linux_process_identity(pid: int, proc_root: Path = Path("/proc")) -> tuple[str, str | None]:
    """Read kernel identity without inspecting arguments or environment."""
    try:
        boot = str(uuid.UUID((proc_root / "sys/kernel/random/boot_id").read_text(encoding="ascii").strip()))
    except (OSError, ValueError, UnicodeError):
        return "unknown", None
    try:
        stat = (proc_root / str(pid) / "stat").read_text(encoding="utf-8")
    except (FileNotFoundError, ProcessLookupError):
        return "gone", None
    except (OSError, UnicodeError):
        return "unknown", None
    try:
        # comm can contain spaces and parentheses; fields after its last ')' start at field 3.
        prefix, separator, suffix = stat.rpartition(")")
        fields = suffix.split()
        if not separator or int(prefix.partition(" (")[0]) != pid or len(fields) < 20:
            return "unknown", None
        state, ticks = fields[0], fields[19]
        if state not in ("R", "S", "D", "Z", "T", "t", "W", "X", "x", "K", "P", "I") or not ticks.isdecimal():
            return "unknown", None
        if state in ("Z", "X", "x"):
            return "gone", None
        return "alive", f"linux:{boot}:{ticks}"
    except (OSError, ValueError, UnicodeError):
        return "unknown", None


def probe_process(pid: int) -> tuple[str, str | None]:
    """Return alive/gone/unknown and a strong creation identity when available."""
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return "unknown", None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE, *([ctypes.POINTER(wintypes.FILETIME)] * 4)]
        kernel32.GetProcessTimes.restype = wintypes.BOOL
        kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle.restype = wintypes.BOOL
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return ("gone", None) if ctypes.get_last_error() == 87 else ("unknown", None)
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel32.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                return "unknown", None
            code = wintypes.DWORD()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return "unknown", None
            if code.value != 259:  # STILL_ACTIVE
                return "gone", None
            return "alive", str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
        finally:
            kernel32.CloseHandle(handle)
    if sys.platform == "linux":
        return linux_process_identity(pid)
    return "unknown", None


def start_marker(pid: int) -> str | None:
    state, marker = probe_process(pid)
    return marker if state == "alive" else None


def process_status(turn: dict) -> str:
    pid, saved = turn.get("pid"), turn.get("pid_started")
    # Legacy ps timestamps are never upgraded or used to abandon a recorded turn.
    if not isinstance(saved, str) or not (re.fullmatch(r"[0-9]+", saved)
            or re.fullmatch(r"linux:[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}:[0-9]+", saved)):
        return "unknown"
    state, current = probe_process(pid)
    if state == "gone":
        return "gone"
    if state != "alive":
        return "unknown"
    if saved.startswith("linux:") != bool(current and current.startswith("linux:")):
        return "unknown"
    return "owned" if saved == current else "foreign"


def require_process_identity() -> None:
    if start_marker(os.getpid()) is None:
        raise Refused("reliable process identity is unavailable on this platform; cannot start or resume a turn")


def owned_and_alive(turn: dict) -> bool:
    return process_status(turn) == "owned"


def stop_tree(pid: int, marker: str | None) -> None:
    status = process_status({"pid": pid, "pid_started": marker})
    if status == "unknown":
        raise Refused("process identity is unknown; cannot stop this process tree")
    if status != "owned":
        return
    if os.name == "nt":
        result = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=30, check=False)
        if result.returncode and process_status({"pid": pid, "pid_started": marker}) not in ("gone", "foreign"):
            raise Refused("could not stop the owned process tree; inspect status before retrying")
        return
    try:
        os.killpg(pid, signal.SIGTERM)
        time.sleep(2)
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def refuse_batch_shell_syntax(executable: list[str], argv: list[str]) -> None:
    # Windows executes batch launchers through cmd even with shell=False.
    if Path(executable[0]).suffix.lower() in (".cmd", ".bat") and any(
        re.search(r'[&|<>^%!"\r\n]', token) for token in argv
    ):
        raise Refused("batch launcher arguments contain shell syntax; use a direct executable instead")


def run_turn(run_dir: Path, meta: dict, kind: str, prompt: str, timeout: float) -> int:
    if not math.isfinite(timeout) or timeout <= 0:
        raise Refused("timeout must be finite and greater than zero")
    adapter = meta["adapter"]
    problems = validate_adapter(adapter)
    if problems:
        raise Refused("recorded adapter is invalid: " + "; ".join(problems))
    if reason := run_disabled_reason(meta, run_dir):
        raise Refused(f"adapter {meta['cli']!r} is disabled: {reason}")
    require_process_identity()
    number = len(meta["turns"]) + 1
    turn_dir = run_dir / "turns" / str(number)
    prompt_path = turn_dir / "prompt.md"
    argv = [*meta["executable"], *render(
        adapter, kind, meta["access"], meta["cwd"], meta.get("model"), meta.get("session_id"), str(prompt_path),
    )]
    refuse_batch_shell_syntax(meta["executable"], argv)

    kwargs: dict[str, Any] = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    kwargs["env"] = child_environment(adapter, meta["access"])
    stdout_path = turn_dir / ("events.jsonl" if adapter["output"]["format"] == "jsonl" else "stdout.txt")
    preassigned = meta.get("session_id") if adapter["session"]["source"] == "preassign" else None
    proc, pid_started = None, None
    started, timed_out, session = time.monotonic(), False, None
    try:
        # Reservation and PID publication share the lock with cancel and resume.
        with record_lock(run_dir):
            fresh = load_meta(run_dir)
            if len(fresh["turns"]) != number - 1:
                raise Refused("run changed while preparing the turn; inspect status before retrying")
            if fresh["turns"] and fresh["turns"][-1].get("state") not in TERMINAL:
                raise Refused("previous turn has no recorded end; inspect status before retrying")
            turn_dir.mkdir(parents=True)
            prompt_path.write_bytes(prompt.encode("utf-8"))
            fresh["turns"].append({"number": number, "argv": argv, "state": "created", "created_at": now()})
            write_json(run_dir / "meta.json", fresh)
            # A file-backed stdin cannot block the recorder while sending a large prompt.
            with prompt_path.open("rb") as input_file, stdout_path.open("wb") as out, (turn_dir / "stderr.log").open("wb") as err:
                try:
                    proc = subprocess.Popen(
                        argv, cwd=meta["cwd"], stdin=input_file if adapter["prompt"] == "stdin" else subprocess.DEVNULL,
                        stdout=out, stderr=err, **kwargs,
                    )
                except OSError as exc:
                    fresh["turns"][-1].update(state="launch-failed", error=str(exc), ended_at=now())
                    write_json(run_dir / "meta.json", fresh)
                    return 1
            pid_started = start_marker(proc.pid)
            fresh["turns"][-1].update(state="launched", pid=proc.pid, pid_started=pid_started, started_at=now())
            write_json(run_dir / "meta.json", fresh)

        while proc.poll() is None:
            if time.monotonic() - started >= timeout:
                timed_out = True
                stop_tree(proc.pid, pid_started)
                break
            if session is None:
                events, _, text = read_events(stdout_path)
                if events or (text.strip() and adapter["output"]["format"] == "text"):
                    session = preassigned or (extract(events, adapter["session"]) if adapter["session"]["source"] == "event" else None)
                    if session:
                        update_turn(run_dir, number, state="session-known", session_id=session)
            time.sleep(0.1)
        try:
            code = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            stop_tree(proc.pid, pid_started)
            code = proc.wait(timeout=30)
    except BaseException as exc:
        if proc is not None:
            cleanup_error = None
            try:
                if proc.poll() is None:
                    stop_tree(proc.pid, pid_started)
                proc.wait(timeout=30)
            except (OSError, subprocess.TimeoutExpired, Refused) as cleanup:
                cleanup_error = str(cleanup)
            update_turn(
                run_dir, number, state="interrupted" if not cleanup_error else "launched",
                error=str(exc) or type(exc).__name__, cleanup_error=cleanup_error,
                **({"ended_at": now()} if not cleanup_error else {}),
            )
        raise

    events, malformed, text = read_events(stdout_path)
    if adapter["output"]["format"] == "text":
        malformed = 0
    parsed = parse_output(adapter, events, text, preassigned)
    session = parsed["session"] or session
    if parsed["final"] is not None:
        (turn_dir / "final.md").write_bytes(parsed["final"].encode("utf-8"))
    if timed_out:
        state, result = "timed-out", 3
    elif code == 0 and parsed["final"] is not None and not parsed["error"]:
        state, result = "exited", 0
    else:
        state, result = "failed", 1
    final_meta = update_turn(
        run_dir, number, state=state, exit_code=code, ended_at=now(), malformed_lines=malformed,
        final_found=parsed["final"] is not None, error=parsed["error"], **({"session_id": session} if session else {}),
    )
    return result if final_meta["turns"][number - 1]["state"] == state else 1


def interactive_argv(meta: dict, session: str) -> list[str]:
    template = meta["adapter"].get("interactive")
    if not template:
        return []
    return [meta["adapter"]["executable"], *(t.replace("{session}", session) for t in template)]


def summary(run_dir: Path) -> dict:
    with record_lock(run_dir):
        meta = load_meta(run_dir)
    turn = meta["turns"][-1] if meta["turns"] else {}
    final = run_dir / "turns" / str(turn.get("number", 0)) / "final.md"
    session = meta.get("session_id")
    reason = run_disabled_reason(meta, run_dir)
    info = {
        "run_id": meta["run_id"], "run_dir": str(run_dir), "cli": meta["cli"], "verified": meta["adapter"].get("verified"),
        "mode": meta.get("mode", "headless"), "created_at": meta.get("created_at"), "cwd": meta["cwd"], "access": meta["access"], "model": meta.get("model"), "session_id": session,
        "turn": turn.get("number"), "state": turn.get("state"), "exit_code": turn.get("exit_code"),
        "error": turn.get("error"), "final_file": str(final) if final.is_file() else None,
    }
    if turn.get("state") in RUNNING or turn.get("state") == "created":
        info["process_status"] = process_status(turn)
        info["process_alive"] = None if info["process_status"] == "unknown" else info["process_status"] == "owned"
    if reason:
        info["disabled_reason"] = reason
    if session and not reason and interactive_argv(meta, session):
        info["interactive_resume"] = {"cwd": meta["cwd"], "argv": interactive_argv(meta, session)}
    if meta.get("outcomes"):
        info["outcomes"] = meta["outcomes"]
    return info


# --- Commands ---------------------------------------------------------------

def check(entry: dict, exe: list[str]) -> dict:
    adapter = entry["adapter"]
    version = subprocess.run([*exe, "--version"], capture_output=True, timeout=60)
    missing, failed_help = [], []
    for item in adapter["help"]:
        out = subprocess.run([*exe, *item["args"]], capture_output=True, timeout=60)
        text = (out.stdout + out.stderr).decode("utf-8", errors="replace")
        if out.returncode:
            failed_help.append({"args": item["args"], "exit_code": out.returncode})
        missing += [f"{' '.join(item['args'])}: {flag}" for flag in item["flags"] if not re.search(
            r"(?<![\w-])" + re.escape(flag) + r"(?![\w-])", text,
        )]
    lines = (version.stdout + version.stderr).decode("utf-8", errors="replace").strip().splitlines()
    installed = lines[0].strip() if lines else ""
    verified = adapter.get("verified")
    report = {
        "cli": adapter["name"], "adapter": entry["path"], "source": entry["source"], "executable": exe[-1],
        "version": installed, "verified": verified, "missing_flags": missing,
        "failed_help": failed_help, "ok": version.returncode == 0 and not missing and not failed_help,
    }
    if verified and verified.get("version") and verified["version"] not in installed:
        report["version_drift"] = f"adapter verified on {verified['version']}; installed {installed}"
    if entry["overrides_bundled"]:
        report["overrides_bundled"] = True
    return report


def read_prompt(path: str) -> str:
    prompt = Path(path).read_text(encoding="utf-8")
    if not prompt.strip():
        raise Refused(f"prompt file is empty: {path}")
    return prompt


def cmd_list(args: argparse.Namespace) -> int:
    rows = []
    for name, entry in sorted(load_adapters(args.runs_dir).items()):
        adapter = entry["adapter"]
        rows.append({
            "cli": name, "source": entry["source"], "path": entry["path"],
            "usable": not entry["problems"] and not disabled_reason(adapter), "disabled_reason": disabled_reason(adapter),
            "problems": entry["problems"] or None, "verified": adapter.get("verified"),
            "access": sorted(adapter.get("access", {})) if isinstance(adapter.get("access"), dict) else None,
            "installed": bool(isinstance(adapter.get("executable"), str) and adapter["executable"] and shutil.which(adapter["executable"])),
            "overrides_bundled": entry["overrides_bundled"],
        })
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    entry = get_adapter(args.cli, args.runs_dir, allow_disabled=True)
    adapter = entry["adapter"]
    exe = [adapter["executable"]]
    cwd = str(Path(args.cwd).resolve()) if args.cwd else "<cwd>"
    result = {
        "cli": args.cli, "adapter": entry["path"], "source": entry["source"], "verified": adapter.get("verified"),
        "disabled_reason": disabled_reason(adapter), "usable": not disabled_reason(adapter),
        "prompt": "stdin" if adapter["prompt"] == "stdin" else "file <turn>/prompt.md",
        "access": args.access,
        "write_boundary": "CLI native permissions; no directory isolation promised" if args.access == "native-write" else args.access,
        "env": sorted(set(adapter.get("env", {})) | set(adapter.get("access_env", {}).get(args.access, {}))) or None,
        "start": [*exe, *render(adapter, "start", args.access, cwd, args.model, "<session-id>", "<prompt-file>")],
    }
    if adapter["session"]["source"] != "none":
        result["resume"] = [*exe, *render(adapter, "resume", args.access, cwd, args.model, "<session-id>", "<prompt-file>")]
    if adapter.get("notes"):
        result["notes"] = adapter["notes"]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    entry = get_adapter(args.cli, args.runs_dir)
    report = check(entry, resolve_executable(entry["adapter"], args.executable))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def cmd_start(args: argparse.Namespace) -> int:
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise Refused("timeout must be finite and greater than zero")
    require_process_identity()
    entry = get_adapter(args.cli, args.runs_dir)
    adapter = entry["adapter"]
    if args.access not in adapter["access"]:
        raise Refused(f"{args.cli} does not offer {args.access}; it offers {', '.join(adapter['access'])}")
    exe = resolve_executable(adapter, args.executable)
    report = check(entry, exe)
    if not report["ok"]:
        raise Refused(f"{args.cli} failed the preflight check: {json.dumps(report, ensure_ascii=False)}")
    cwd = Path(args.cwd).resolve()
    if not cwd.is_dir():
        raise Refused(f"working directory not found: {cwd}")
    if args.model and args.model.startswith("-"):
        raise Refused("model must not start with '-'")
    prompt = read_prompt(args.prompt_file)
    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{args.cli}-{secrets.token_hex(3)}"
    run_dir = runs_root(args.runs_dir) / run_id
    run_dir.mkdir(parents=True)
    meta = {
        "run_id": run_id, "cli": args.cli, "adapter_path": entry["path"], "adapter": adapter, "executable": exe,
        "version": report["version"], "cwd": str(cwd), "access": args.access, "model": args.model,
        "session_id": str(uuid.uuid4()) if adapter["session"]["source"] == "preassign" else None,
        "created_at": now(), "turns": [], "outcomes": [],
    }
    write_json(run_dir / "meta.json", meta)
    extra = {"window": open_watch_window(run_dir, 1)} if args.window else {}
    if args.detach:
        return run_detached(run_dir, "start", args.prompt_file, args.timeout, extra)
    code = run_turn(run_dir, meta, "start", prompt, args.timeout)
    print(json.dumps({**summary(run_dir), **extra}, ensure_ascii=False, indent=2))
    return code


def cmd_resume(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    with record_lock(run_dir):
        meta = load_meta(run_dir)
    if reason := run_disabled_reason(meta, run_dir):
        raise Refused(f"adapter {meta['cli']!r} is disabled: {reason}")
    require_process_identity()
    last = meta["turns"][-1] if meta["turns"] else {}
    if last.get("state") in RUNNING or last.get("state") == "created":
        status = process_status(last)
        if status == "owned":
            raise Refused(f"turn {last['number']} is still running; wait for it or cancel it")
        if status == "unknown":
            raise Refused("process identity is unknown; inspect the session manually, without automatic cancellation or recovery")
        raise Refused(
            f"turn {last.get('number')} has no recorded end; check the backend session, "
            "then run `cancel` to mark it abandoned before resuming"
        )
    if meta["adapter"]["session"]["source"] == "none":
        raise Refused(f"{meta['cli']} runs one turn only; start a new run")
    if not meta.get("session_id"):
        raise Refused("no session ID was recorded, so there is nothing to resume; start a new run")
    prompt = read_prompt(args.prompt_file)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise Refused("timeout must be finite and greater than zero")
    extra = {"window": open_watch_window(run_dir, len(meta["turns"]) + 1)} if args.window else {}
    if args.detach:
        return run_detached(run_dir, "resume", args.prompt_file, args.timeout, extra)
    code = run_turn(run_dir, meta, "resume", prompt, args.timeout)
    print(json.dumps({**summary(run_dir), **extra}, ensure_ascii=False, indent=2))
    return code


def run_detached(run_dir: Path, kind: str, prompt_file: str, timeout: float, extra: dict) -> int:
    """Hand the turn to a recorder outside the caller's process group, and return once the turn launches."""
    with record_lock(run_dir):
        number = len(load_meta(run_dir)["turns"]) + 1
    script = str(Path(__file__).resolve())
    argv = [
        sys.executable, script, "_turn", run_dir.name, "--kind", kind,
        "--prompt-file", str(Path(prompt_file).resolve()), "--timeout", repr(timeout), "--runs-dir", str(run_dir.parent),
    ]
    survives: bool | None = None
    with (run_dir / "recorder.log").open("ab") as log:
        options: dict[str, Any] = {"cwd": str(run_dir), "stdin": subprocess.DEVNULL, "stdout": log, "stderr": log}
        if os.name == "nt":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            try:
                recorder = subprocess.Popen(argv, creationflags=flags | subprocess.CREATE_BREAKAWAY_FROM_JOB, **options)
                survives = True
            except OSError:
                # The caller's job forbids breakaway, so closing that job may also end the recorder.
                recorder = subprocess.Popen(argv, creationflags=flags, **options)
                survives = False
        else:
            # A new session outlives the caller's process group and terminal, not a cgroup or container teardown.
            recorder = subprocess.Popen(argv, start_new_session=True, **options)
    recorder_started = start_marker(recorder.pid)
    deadline = time.monotonic() + DETACH_WAIT
    while True:
        with record_lock(run_dir):
            turns = load_meta(run_dir)["turns"]
        state = turns[number - 1].get("state") if len(turns) >= number else None
        if state not in (None, "created") or recorder.poll() is not None or time.monotonic() >= deadline:
            break
        time.sleep(0.1)
    if state in (None, "created"):
        tail = (run_dir / "recorder.log").read_bytes().decode("utf-8", errors="replace")[-2000:].strip()
        raise Refused(f"the detached recorder did not launch turn {number}; see {run_dir / 'recorder.log'}: {tail}")
    info = summary(run_dir)
    info.update(
        detached=True, recorder_pid=recorder.pid, recorder_pid_started=recorder_started, survives_caller=survives,
        watch=watch_argv(run_dir), **extra,
    )
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if state in RUNNING else turn_code(state)


def cmd_turn(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    with record_lock(run_dir):
        meta = load_meta(run_dir)
    code = run_turn(run_dir, meta, args.kind, read_prompt(args.prompt_file), args.timeout)
    print(json.dumps(summary(run_dir), ensure_ascii=False, indent=2))
    return code


def turn_code(state: str | None) -> int:
    return 0 if state in ("exited", "closed") else 3 if state == "timed-out" else 1


def select_turn(run_dir: Path, requested: int | None) -> int:
    """The requested turn, else the latest; waits up to DETACH_WAIT for a turn not yet recorded."""
    if requested is not None and requested < 1:
        raise Refused("turn numbers start at 1")
    deadline = time.monotonic() + DETACH_WAIT
    while True:
        with record_lock(run_dir):
            turns = load_meta(run_dir)["turns"]
        number = requested or len(turns) or 1
        if number <= len(turns):
            return number
        if time.monotonic() >= deadline:
            raise Refused(f"run has no turn {number}")
        time.sleep(0.2)


def follow_turn(run_dir: Path, number: int, stream: Path | None, consume=None) -> tuple[dict, str | None]:
    """Poll the record until the turn ends or stalls, passing new output bytes to `consume`.

    Returns the last turn record and, for a stall, the message explaining it.
    """
    offset, stalled_since = 0, None
    while True:
        with record_lock(run_dir):
            turn = load_meta(run_dir)["turns"][number - 1]
        # Read after the state so that a terminal state also covers every byte written before it.
        if stream is not None and stream.is_file():
            with stream.open("rb") as handle:
                handle.seek(offset)
                chunk = handle.read()
            offset += len(chunk)
            if chunk and consume:
                consume(chunk)
        state = turn.get("state")
        if state in TERMINAL:
            return turn, None
        if state == "created" and "pid" not in turn:
            problem = f"turn {number} was created but never launched; inspect status"
        elif process_status(turn) in ("gone", "foreign"):
            problem = f"turn {number} is still {state} but its process is gone; run status, then cancel to reconcile"
        else:
            problem = None
        if problem is None:
            stalled_since = None
        else:
            stalled_since = stalled_since or time.monotonic()
            if time.monotonic() - stalled_since >= WATCH_GRACE:
                return turn, problem
        if consume:
            consume(b"")
        time.sleep(0.5)


def cmd_watch(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    number = select_turn(run_dir, args.turn)
    with record_lock(run_dir):
        meta = load_meta(run_dir)
    adapter = meta["adapter"]
    rules = adapter.get("progress")
    if rules is None:
        # Progress rules only render output, so the current adapter may supply them for an older snapshot.
        current = load_adapters(str(run_dir.parent)).get(meta["cli"])
        rules = current["adapter"].get("progress") if current and not current["problems"] else None
    rules = rules or []
    text_output = adapter["output"]["format"] == "text"
    turn_dir = run_dir / "turns" / str(number)
    stream = turn_dir / ("stdout.txt" if text_output else "events.jsonl")
    pending, seen, heartbeat = b"", 0, time.monotonic()

    def show(line: bytes) -> None:
        nonlocal seen
        text = line.decode("utf-8", errors="replace").rstrip("\r")
        if text_output:
            print(text, flush=True)
            return
        try:
            event = json.loads(text)
        except ValueError:
            return
        if isinstance(event, dict):
            seen += 1
            for out in progress_lines(rules, event):
                print(out, flush=True)

    def consume(chunk: bytes) -> None:
        nonlocal pending, heartbeat
        *lines, pending = (pending + chunk).split(b"\n")
        for line in lines:
            show(line)
        if not rules and not text_output and time.monotonic() - heartbeat >= 10:
            print(f"... {seen} events so far", flush=True)
            heartbeat = time.monotonic()

    print(f"watching {meta['cli']} run {meta['run_id']} turn {number}; Ctrl+C stops watching, not the run", flush=True)
    turn, problem = follow_turn(run_dir, number, stream, consume)
    if problem:
        print(problem, flush=True)
        code = 2
    else:
        if pending.strip():
            show(pending)
        final = turn_dir / "final.md"
        if not rules and not text_output and final.is_file():
            for line in final.read_text(encoding="utf-8", errors="replace").splitlines()[:20]:
                print(line, flush=True)
        print(f"turn {number} {turn['state']}; final reply: {final if final.is_file() else 'none'}", flush=True)
        code = turn_code(turn["state"])
    if args.hold:
        hold_window("press Enter to close")
    return code


def cmd_wait(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    number = select_turn(run_dir, args.turn)
    turn, problem = follow_turn(run_dir, number, None)
    info = summary(run_dir)
    if problem:
        info["problem"] = problem
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 2 if problem else turn_code(turn["state"])


def open_window(argv: list[str], cwd: str, title: str) -> dict:
    """Run argv in a terminal window the user can see, without building a shell command string."""
    if os.name == "nt":
        wt = shutil.which("wt")
        # Windows Terminal splits its own command line on ';', so such argv falls back to a console window.
        if wt and not any(";" in token for token in (title, cwd, *argv)):
            try:
                tab = subprocess.run(
                    [wt, "-w", WINDOW_GROUP, "new-tab", "--title", title, "-d", cwd, *argv],
                    stdin=subprocess.DEVNULL, capture_output=True, timeout=30,
                )
                if tab.returncode == 0:
                    return {"opened": True, "via": "wt-tab", "reason": None}
            except (OSError, subprocess.TimeoutExpired):
                pass
        flags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        for extra in (subprocess.CREATE_BREAKAWAY_FROM_JOB, 0):
            try:
                subprocess.Popen(argv, cwd=cwd, creationflags=flags | extra)
                return {"opened": True, "via": "console", "reason": None}
            except OSError as exc:
                error = str(exc)
        return {"opened": False, "via": None, "reason": f"could not open a console window: {error}"}
    if sys.platform == "linux":
        terminal = shutil.which("x-terminal-emulator")
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) or not terminal:
            return {"opened": False, "via": None, "reason": "no graphical terminal: DISPLAY/WAYLAND_DISPLAY is unset or x-terminal-emulator is missing"}
        try:
            subprocess.Popen([terminal, "-e", *argv], cwd=cwd, start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as exc:
            return {"opened": False, "via": None, "reason": f"could not start x-terminal-emulator: {exc}"}
        return {"opened": True, "via": "x-terminal-emulator", "reason": None}
    return {"opened": False, "via": None, "reason": "windows open only on Windows and Linux desktops"}


def watch_argv(run_dir: Path, number: int | None = None, hold: bool = False) -> list[str]:
    turn = ["--turn", str(number)] if number else []
    return [sys.executable, str(Path(__file__).resolve()), "watch", run_dir.name, *turn,
            *(["--hold"] if hold else []), "--runs-dir", str(run_dir.parent)]


def open_watch_window(run_dir: Path, number: int) -> dict:
    with record_lock(run_dir):
        cli = load_meta(run_dir)["cli"]
    return open_window(watch_argv(run_dir, number, hold=True), str(run_dir), f"{cli} {run_dir.name}")


def cmd_runs(args: argparse.Namespace) -> int:
    root = runs_root(args.runs_dir)
    run_dirs = sorted((p for p in root.iterdir() if (p / "meta.json").is_file()), reverse=True) if root.is_dir() else []
    rows = []
    for run_dir in run_dirs:
        if len(rows) >= args.limit:
            break
        try:
            info = summary(run_dir)
        except Refused as exc:
            rows.append({"run_id": run_dir.name, "error": str(exc)})
            continue
        active = info["state"] in RUNNING or info["state"] == "created"
        if args.active and not active:
            continue
        row = {key: info.get(key) for key in ("run_id", "cli", "model", "mode", "access", "created_at", "turn", "state", "process_status")}
        if active and info["mode"] == "headless":
            row["watch"] = watch_argv(run_dir)
        elif not active and info.get("interactive_resume"):
            row["interactive_resume"] = info["interactive_resume"]
        rows.append(row)
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


def cmd_open(args: argparse.Namespace) -> int:
    require_process_identity()
    entry = get_adapter(args.cli, args.runs_dir)
    adapter = entry["adapter"]
    if not adapter.get("interactive_start"):
        raise Refused(f"{args.cli} has no interactive_start template; run it headless with start instead")
    if args.access not in adapter["access"]:
        raise Refused(f"{args.cli} does not offer {args.access}; it offers {', '.join(adapter['access'])}")
    exe = resolve_executable(adapter, args.executable)
    report = check(entry, exe)
    if not report["ok"]:
        raise Refused(f"{args.cli} failed the preflight check: {json.dumps(report, ensure_ascii=False)}")
    cwd = Path(args.cwd).resolve()
    if not cwd.is_dir():
        raise Refused(f"working directory not found: {cwd}")
    if args.model and args.model.startswith("-"):
        raise Refused("model must not start with '-'")
    prompt = read_prompt(args.prompt_file)
    run_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{args.cli}-{secrets.token_hex(3)}"
    run_dir = runs_root(args.runs_dir) / run_id
    prompt_path = run_dir / "turns" / "1" / "prompt.md"
    session = str(uuid.uuid4())
    # Only this pointer travels on the command line; the brief itself stays in the recorded file.
    opening = f"Read the brief at {prompt_path} and follow it. When you finish, give your final report and stop."
    argv = [*exe, *render(adapter, "interactive_start", args.access, str(cwd), args.model, session, None,
                          opening=opening, run_name=run_id)]
    refuse_batch_shell_syntax(exe, argv)
    prompt_path.parent.mkdir(parents=True)
    write_json(run_dir / "meta.json", {
        "run_id": run_id, "cli": args.cli, "adapter_path": entry["path"], "adapter": adapter, "executable": exe,
        "version": report["version"], "cwd": str(cwd), "access": args.access, "model": args.model, "mode": "interactive",
        "session_id": session, "created_at": now(), "outcomes": [],
        "turns": [{"number": 1, "kind": "interactive", "argv": argv, "state": "created", "created_at": now()}],
    })
    prompt_path.write_bytes(prompt.encode("utf-8"))
    host = [sys.executable, str(Path(__file__).resolve()), "_host", run_id, "--runs-dir", str(run_dir.parent)]
    window = open_window(host, str(cwd), f"{args.cli} {run_id}")
    if not window["opened"]:
        update_turn(run_dir, 1, state="launch-failed", error=window["reason"], ended_at=now())
        print(json.dumps({**summary(run_dir), "window": window}, ensure_ascii=False, indent=2))
        return 1
    deadline = time.monotonic() + DETACH_WAIT
    while True:
        with record_lock(run_dir):
            state = load_meta(run_dir)["turns"][0].get("state")
        if state != "created" or time.monotonic() >= deadline:
            break
        time.sleep(0.2)
    info = {**summary(run_dir), "window": window,
            "wait": [sys.executable, str(Path(__file__).resolve()), "wait", run_id, "--runs-dir", str(run_dir.parent)]}
    if state == "created":
        info["problem"] = "the window opened but its host did not start; check the window"
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if state in RUNNING else 2 if state == "created" else turn_code(state)


def hold_window(message: str) -> None:
    """Keep a window readable until the user presses Enter; do nothing without a terminal."""
    if sys.stdin.isatty():
        try:
            input(message)
        except EOFError:
            pass


_CLOSE_HANDLERS: list[Any] = []


def on_window_close(callback) -> None:
    """Best effort: record the turn before the terminal kills this process."""
    if os.name == "nt":
        import ctypes

        @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)
        def handler(event: int) -> bool:
            if event in (2, 5, 6):  # CTRL_CLOSE_EVENT, CTRL_LOGOFF_EVENT, CTRL_SHUTDOWN_EVENT
                callback("window")
            return False

        _CLOSE_HANDLERS.append(handler)  # ctypes callbacks must stay referenced
        ctypes.WinDLL("kernel32").SetConsoleCtrlHandler(handler, True)
    else:
        def hangup(*_: object) -> None:
            callback("window")
            os._exit(129)

        signal.signal(signal.SIGHUP, hangup)


def cmd_host(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    with record_lock(run_dir):
        meta = load_meta(run_dir)
        turn = meta["turns"][-1]
        if turn.get("state") != "created":
            raise Refused(f"turn {turn.get('number')} is already {turn.get('state')}")
        number = turn["number"]
        turn.update(state="interactive", pid=os.getpid(), pid_started=start_marker(os.getpid()), started_at=now())
        write_json(run_dir / "meta.json", meta)

    def record_closed(by: str, **fields: object) -> None:
        # The first ending wins: a window close recorded first is not overwritten by the CLI's exit.
        try:
            with record_lock(run_dir):
                meta = load_meta(run_dir)
                turn = meta["turns"][number - 1]
                if turn.get("state") not in TERMINAL:
                    turn.update(state="closed", ended_at=now(), closed_by=by, **fields)
                    write_json(run_dir / "meta.json", meta)
        except (Refused, OSError):
            pass

    on_window_close(record_closed)
    # Ctrl+C belongs to the CLI in this console; a Python handler, unlike SIG_IGN, is not inherited.
    signal.signal(signal.SIGINT, lambda *_: None)
    try:
        cli = subprocess.Popen(turn["argv"], cwd=meta["cwd"], env=child_environment(meta["adapter"], meta["access"]))
    except OSError as exc:
        update_turn(run_dir, number, state="launch-failed", error=str(exc), ended_at=now())
        print(f"could not start {meta['cli']}: {exc}", flush=True)
        code = 1
    else:
        update_turn(run_dir, number, cli_pid=cli.pid)
        exit_code = cli.wait()
        record_closed("cli-exit", exit_code=exit_code)
        print(f"\n{meta['cli']} exited with code {exit_code}; run {meta['run_id']} is recorded as closed.", flush=True)
        code = 0
    hold_window("press Enter to close this window")
    return code


def cmd_cancel(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    with record_lock(run_dir):
        meta = load_meta(run_dir)
        last = meta["turns"][-1] if meta["turns"] else {}
        if last.get("state") == "cancelling" and last.get("cancel_owner"):
            owner_status = process_status(last["cancel_owner"])
            if owner_status in ("owned", "unknown"):
                raise Refused("cancellation has no recorded end or its owner identity is unknown; inspect before retrying")
        if last.get("state") not in RUNNING and last.get("state") != "created":
            raise Refused(f"turn {last.get('number')} already ended as {last.get('state')}; nothing to cancel")
        status = process_status(last)
        if status == "unknown":
            raise Refused("process identity is unknown; inspect the session manually before any cancellation or recovery")
        alive = status == "owned"
        owner_marker = start_marker(os.getpid()) if alive else None
        if alive and owner_marker is None:
            raise Refused("cancellation owner identity is unknown; inspect before retrying")
        last.update(state="cancelling" if alive else "abandoned")
        if alive:
            last["cancel_owner"] = {"pid": os.getpid(), "pid_started": owner_marker}
        if not alive:
            last["abandoned_at"] = now()
        write_json(run_dir / "meta.json", meta)
    if alive:
        try:
            # Check the marker again after releasing the metadata lock.
            stop_tree(last["pid"], last["pid_started"])
            deadline = time.monotonic() + 5
            while process_status(last) == "owned" and time.monotonic() < deadline:
                time.sleep(0.05)
            if process_status(last) not in ("gone", "foreign"):
                raise Refused("process still exists or its identity is unknown after cancellation")
        except (OSError, subprocess.TimeoutExpired, Refused) as exc:
            update_turn(run_dir, last["number"], state="launched", cancel_error=str(exc))
            raise Refused("cancellation failed; inspect status before retrying") from exc
        update_turn(run_dir, last["number"], state="cancelled", cancelled_at=now())
    print(json.dumps(summary(run_dir), ensure_ascii=False, indent=2))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    run_dir = run_path(args)
    with record_lock(run_dir):
        meta = load_meta(run_dir)
        meta.setdefault("outcomes", []).append({"at": now(), "outcome": args.outcome, "note": args.note})
        write_json(run_dir / "meta.json", meta)
    print(json.dumps(summary(run_dir), ensure_ascii=False, indent=2))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    print(json.dumps(summary(run_path(args)), ensure_ascii=False, indent=2))
    return 0


def run_path(args: argparse.Namespace) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", args.run_id):
        raise Refused("run ID must be a directory name, not a path")
    return runs_root(args.runs_dir) / args.run_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="List adapters with their source, verification, access levels, and whether the CLI is installed.")
    p.add_argument("--runs-dir")

    p = sub.add_parser("show", help="Print the exact command a run would execute, without running it.")
    p.add_argument("cli")
    p.add_argument("--access", required=True, choices=ACCESS_LEVELS)
    p.add_argument("--model")
    p.add_argument("--cwd")
    p.add_argument("--runs-dir")

    p = sub.add_parser("check", help="Confirm the CLI is installed and its help lists every flag the adapter uses.")
    p.add_argument("cli")
    p.add_argument("--executable", help="Path to the CLI when it is not on PATH.")
    p.add_argument("--runs-dir")

    p = sub.add_parser("start", help="Create a run and send its first turn.")
    p.add_argument("cli")
    p.add_argument("--cwd", required=True)
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--access", required=True, choices=ACCESS_LEVELS)
    p.add_argument("--model")
    p.add_argument("--timeout", type=float, default=1800)
    p.add_argument("--executable")
    p.add_argument("--detach", action="store_true", help="Return once the turn launches; a detached recorder finishes it.")
    p.add_argument("--window", action="store_true", help="Also open a terminal window that watches the turn.")
    p.add_argument("--runs-dir")

    p = sub.add_parser("open", help="Start the CLI interactively in a terminal window the user can see and type into.")
    p.add_argument("cli")
    p.add_argument("--cwd", required=True)
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--access", required=True, choices=ACCESS_LEVELS)
    p.add_argument("--model")
    p.add_argument("--executable")
    p.add_argument("--runs-dir")

    p = sub.add_parser("resume", help="Send another turn to the recorded session.")
    p.add_argument("run_id")
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--timeout", type=float, default=1800)
    p.add_argument("--detach", action="store_true", help="Return once the turn launches; a detached recorder finishes it.")
    p.add_argument("--window", action="store_true", help="Also open a terminal window that watches the turn.")
    p.add_argument("--runs-dir")

    p = sub.add_parser("watch", help="Follow a turn's progress until it ends; exits with the turn's code.")
    p.add_argument("run_id")
    p.add_argument("--turn", type=int, help="Turn number; defaults to the latest.")
    p.add_argument("--hold", action="store_true", help="Wait for Enter before exiting, so a window stays open.")
    p.add_argument("--runs-dir")

    p = sub.add_parser("wait", help="Wait silently for a turn to end, then print the summary; exits with the turn's code.")
    p.add_argument("run_id")
    p.add_argument("--turn", type=int, help="Turn number; defaults to the latest.")
    p.add_argument("--runs-dir")

    p = sub.add_parser("runs", help="List recorded runs, newest first.")
    p.add_argument("--active", action="store_true", help="Only runs whose last turn is still running.")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--runs-dir")

    p = sub.add_parser("_host", help=argparse.SUPPRESS)
    p.add_argument("run_id")
    p.add_argument("--runs-dir")

    p = sub.add_parser("_turn", help=argparse.SUPPRESS)
    p.add_argument("run_id")
    p.add_argument("--kind", required=True, choices=("start", "resume"))
    p.add_argument("--prompt-file", required=True)
    p.add_argument("--timeout", type=float, required=True)
    p.add_argument("--runs-dir")

    for name, text in (("status", "Print the run record summary."), ("cancel", "Stop the run's own process tree, or mark a dead turn abandoned.")):
        p = sub.add_parser(name, help=text)
        p.add_argument("run_id")
        p.add_argument("--runs-dir")

    p = sub.add_parser("record", help="Append the caller's acceptance decision or note to the run.")
    p.add_argument("run_id")
    p.add_argument("--outcome", required=True, choices=("accepted", "rejected", "transferred", "note"))
    p.add_argument("--note", default="")
    p.add_argument("--runs-dir")

    args = parser.parse_args(argv)
    # Callers parse the JSON as UTF-8; on Windows a piped stdout would otherwise use the ANSI code page.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    commands = {
        "list": cmd_list, "show": cmd_show, "check": cmd_check, "start": cmd_start, "resume": cmd_resume,
        "status": cmd_status, "cancel": cmd_cancel, "record": cmd_record, "watch": cmd_watch, "_turn": cmd_turn,
        "wait": cmd_wait, "runs": cmd_runs, "open": cmd_open, "_host": cmd_host,
    }
    try:
        return commands[args.command](args)
    except (Refused, OSError, subprocess.TimeoutExpired) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        # Stopping a watch leaves the run alone; every other command keeps its interruption handling.
        if args.command not in ("watch", "wait"):
            raise
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
