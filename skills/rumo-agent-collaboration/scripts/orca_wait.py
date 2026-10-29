#!/usr/bin/env python3
"""Wait for an agent in an Orca terminal to finish or stall, without ever writing to that terminal.

For any agent CLI. Run it as a background command in a client that reports
when a command exits; it polls `orca terminal read` and the agent state that
Orca's hooks publish in `orca worktree ps`, and ends with one line:

  0 done       the report file changed after the wait began and the screen shows the marker
  6 attention  Orca has shown the agent blocked on an approval or waiting on a question for --attention seconds
  3 idle       the screen has not changed for --idle seconds, or Orca has shown the turn ended for
               --attention seconds without done: finished, asking, or waiting for approval
  4 stopped    the terminal exited, or its handle is stale (after an Orca restart, list terminals again)
  5 lost       every read failed for --lost seconds
  2 usage error

Agents without Orca hooks, or with a lagging hook state, still end in idle.
The attention line names the prompt's start; pass it back as --seen to wait
again without reporting the same prompt, which then ends in idle if nobody
answers it. Without --marker the report alone means done, and without
--report the marker alone; with neither, done never ends the wait.
Interrupting the wait leaves the agent running.
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable


EXIT_DONE, EXIT_USAGE, EXIT_IDLE, EXIT_STOPPED, EXIT_LOST, EXIT_ATTENTION = 0, 2, 3, 4, 5, 6
STALE = {"terminal_handle_stale"}
# Orca's hook states for an approval prompt, a question or other UI prompt, and a finished turn.
TIMED = {"blocked", "waiting", "done"}
# A hung orca call counts as one failed read rather than blocking the wait.
CALL_TIMEOUT = 30

Orca = Callable[[list[str]], "dict | None"]


def orca_caller(executable: list[str]) -> Orca:
    def call(args: list[str]) -> dict | None:
        try:
            proc = subprocess.run(executable + args + ["--json"], capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=CALL_TIMEOUT)
            # Agent messages in `worktree ps` can carry raw control characters.
            data = json.loads(proc.stdout, strict=False)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return None
        return data if isinstance(data, dict) else None
    return call


def error_code(reply: dict | None) -> str | None:
    error = reply.get("error") if isinstance(reply, dict) else None
    return error.get("code") if isinstance(error, dict) else None


def observe(orca: Orca, handle: str) -> tuple[str, str]:
    """One poll: ("screen", text), ("stopped", reason), or ("error", reason)."""
    reply = orca(["terminal", "read", "--terminal", handle])
    if reply is None:
        return "error", "no readable reply from orca terminal read"
    if not reply.get("ok"):
        code = error_code(reply)
        return ("stopped", f"handle {code}") if code in STALE else ("error", f"orca terminal read failed: {code}")
    terminal = (reply.get("result") or {}).get("terminal") or {}
    if terminal.get("status", "running") != "running":
        # The status values are undocumented; only Orca's own exit wait decides that the terminal ended.
        exited = orca(["terminal", "wait", "--terminal", handle, "--for", "exit", "--timeout-ms", "1000"])
        if exited is not None and exited.get("ok"):
            return "stopped", "terminal exited"
        if error_code(exited) in STALE:
            return "stopped", f"handle {error_code(exited)}"
    tail = terminal.get("tail")
    if not isinstance(tail, list):
        return "error", "orca terminal read returned no screen"
    return "screen", "\n".join(str(line) for line in tail)


def pane_key(orca: Orca, handle: str) -> str | None:
    """The key `worktree ps` uses for this terminal's agent, or None when Orca does not say."""
    reply = orca(["terminal", "show", "--terminal", handle])
    if not isinstance(reply, dict) or not reply.get("ok"):
        return None
    terminal = (reply.get("result") or {}).get("terminal") or {}
    tab, leaf = terminal.get("tabId"), terminal.get("leafId")
    return f"{tab}:{leaf}" if tab and leaf else None


def agent_state(orca: Orca, pane: str) -> dict | None:
    """This pane's entry in `worktree ps`, or None when the call fails or the pane has no agent."""
    reply = orca(["worktree", "ps", "--limit", "1000"])
    result = reply.get("result") if isinstance(reply, dict) and reply.get("ok") else None
    rows = result.get("worktrees") if isinstance(result, dict) else None
    for row in rows if isinstance(rows, list) else []:
        for agent in (row.get("agents") or []) if isinstance(row, dict) else []:
            if isinstance(agent, dict) and agent.get("paneKey") == pane:
                return agent
    return None


def agent_probe(orca: Orca, handle: str) -> Callable[[], "dict | None"]:
    """Reads this terminal's agent state, resolving its pane key again until Orca answers."""
    pane = None

    def probe() -> dict | None:
        nonlocal pane
        pane = pane or pane_key(orca, handle)
        return agent_state(orca, pane) if pane else None
    return probe


def summary(value: object, limit: int = 200) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "…"


def finished(screen: str, report: Path | None, marker: str | None, since: float) -> bool:
    if report is None and marker is None:
        return False
    if marker is not None and marker not in screen:
        return False
    try:
        return report is None or report.stat().st_mtime > since
    except OSError:
        return False


def wait(poll: Callable[[], tuple[str, str]], report: Path | None, marker: str | None, *, idle: float,
         interval: float, lost: float, since: float, agent: Callable[[], "dict | None"] | None = None,
         attention: float = 60, seen: str | None = None, clock: Callable[[], float] = time.monotonic,
         sleep: Callable[[float], None] = time.sleep) -> tuple[int, str]:
    last_screen, changed_at, last_ok, last_error = None, clock(), clock(), ""
    # The prompt being timed and when this script first saw it; Orca's own timestamps are only compared.
    prompt, prompt_since = None, 0.0
    while True:
        kind, value = poll()
        now = clock()
        if kind == "stopped":
            hint = "; after an Orca restart, run `orca terminal list` for the new handle" if "handle" in value else ""
            return EXIT_STOPPED, f"stopped / 已停止: {value}{hint}"
        if kind == "error":
            last_error = value
            if now - last_ok >= lost:
                return EXIT_LOST, f"lost / 失联: every read failed for {lost:g}s; last: {last_error}"
        else:
            last_ok = now
            if value != last_screen:
                last_screen, changed_at = value, now
            if finished(value, report, marker, since):
                return EXIT_DONE, f"done / 已完成: {report if report else 'marker ' + repr(marker)}"
            state = agent() if agent else None
            # No reply or no matching pane says nothing about the prompt, so it keeps the timer running.
            if state and state.get("state") in TIMED:
                started = str(state.get("stateStartedAt") or "")
                if prompt != (state["state"], started):
                    prompt, prompt_since = (state["state"], started), now
                if now - prompt_since >= attention and not (seen is not None and started == seen):
                    if state["state"] == "done":
                        return EXIT_IDLE, (f"idle / 停住了: Orca has shown the turn ended for {attention:g}s without "
                                           "the report and marker / 这一轮已结束，但报告或暗号没到")
                    tool = summary(state.get("toolName") or "")
                    detail = summary(state.get("toolInput") or "")
                    again = f"; after telling the user, wait again with --seen {started}" if started else ""
                    return EXIT_ATTENTION, f"attention / 等你处理: {state['state']} {tool} {detail}{again}"
            elif state:
                prompt = None
            if now - changed_at >= idle:
                return EXIT_IDLE, (f"idle / 停住了: screen unchanged for {idle:g}s; it finished, asked a question, "
                                   "or waits for approval / 可能已做完、在提问或在等审批")
        sleep(interval)


def positive(text: str) -> float:
    value = float(text)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return value


def resolve_orca(override: str | None) -> list[str] | None:
    if override:
        path = Path(override).resolve()
        if not path.is_file():
            return None
        return [sys.executable, str(path)] if path.suffix.lower() == ".py" else [str(path)]
    found = shutil.which("orca")
    return [found] if found else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--terminal", required=True, help="the agent's terminal handle from the Orca launch")
    parser.add_argument("--report", type=Path, help="the report file the brief tells the agent to write")
    parser.add_argument("--marker", help="the line the brief tells the agent to print when done")
    parser.add_argument("--idle", type=positive, default=200, help="seconds of unchanged screen before reporting idle")
    parser.add_argument("--interval", type=positive, default=30, help="seconds between reads")
    parser.add_argument("--lost", type=positive, default=600, help="seconds of failed reads before giving up")
    parser.add_argument("--attention", type=positive, default=60,
                        help="seconds an approval or question prompt must last before reporting attention")
    parser.add_argument("--seen", help="the prompt start from an earlier attention line, so it is not reported again")
    parser.add_argument("--orca", help="orca executable to use instead of the one on PATH")
    args = parser.parse_args(argv)
    executable = resolve_orca(args.orca)
    if executable is None:
        print(f"orca not found: {args.orca or 'orca is not on PATH'}", file=sys.stderr)
        return EXIT_USAGE
    sys.stdout.reconfigure(encoding="utf-8")
    orca = orca_caller(executable)
    try:
        code, line = wait(lambda: observe(orca, args.terminal), args.report, args.marker, idle=args.idle,
                          interval=args.interval, lost=args.lost, since=time.time(),
                          agent=agent_probe(orca, args.terminal), attention=args.attention, seen=args.seen)
    except KeyboardInterrupt:
        return 130
    print(line)
    return code


if __name__ == "__main__":
    sys.exit(main())
