#!/usr/bin/env python3
"""Run one Codex app-server review pass and print the review text.

This script intentionally performs review only. The calling Codex instance should
apply fixes, run verification, and invoke this script again.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


BLOCKING_RE = re.compile(r"\bP[0-2]\b|严重|阻断|block(?:er|ing)?|critical", re.IGNORECASE)
DEFAULT_OPT_OUT_NOTIFICATIONS = [
    "account/updated",
    "account/rateLimits/updated",
    "app/list/updated",
    "mcpServer/startupStatus/updated",
    "model/verification",
    "model/rerouted",
]


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{seconds:02d}s"
    if minutes:
        return f"{minutes}m{seconds:02d}s"
    return f"{seconds}s"


def print_progress(message: str) -> None:
    print(f"[rumo-review-fix-loop] {message}", file=sys.stderr, flush=True)


def extract_visible_text(value: Any, *, parent_key: str = "") -> list[str]:
    if isinstance(value, str):
        if parent_key in {"content", "message", "output", "summary", "text"}:
            text = value.strip()
            return [text] if text else []
        return []
    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(extract_visible_text(item, parent_key=parent_key))
        return texts
    if isinstance(value, dict):
        texts: list[str] = []
        for key, nested in value.items():
            key_name = str(key)
            texts.extend(extract_visible_text(nested, parent_key=key_name))
        return texts
    return []


def extract_intermediate_text_from_item(item: dict[str, Any]) -> str | None:
    item_type = item.get("type")
    item_type_text = item_type if isinstance(item_type, str) else ""
    if item_type_text == "exitedReviewMode":
        return None
    item_type_lower = item_type_text.lower()
    if "reasoning" in item_type_lower or "tool" in item_type_lower:
        return None

    texts = []
    seen = set()
    for text in extract_visible_text(item):
        if text not in seen:
            seen.add(text)
            texts.append(text)
    return "\n".join(texts) if texts else None


def print_intermediate_text(item_type: str, text: str, max_chars: int) -> None:
    text = text.strip()
    if not text:
        return
    truncated = text[:max_chars]
    print_progress(f"intermediate visible text item={item_type or '-'} chars={len(text)}")
    print(truncated, file=sys.stderr, flush=True)
    if len(text) > max_chars:
        print(f"[rumo-review-fix-loop] intermediate text truncated at {max_chars} chars", file=sys.stderr, flush=True)


@dataclass
class RpcResult:
    result: dict[str, Any] | None
    error: dict[str, Any] | None


@dataclass
class PollSnapshot:
    review: str | None
    final_turn: dict[str, Any] | None
    latest_visible_text: str
    diagnostics: dict[str, Any]


class ReviewWaitError(RuntimeError):
    def __init__(self, message: str, diagnostics: dict[str, Any]) -> None:
        super().__init__(message)
        self.diagnostics = diagnostics


class AppServerClient:
    def __init__(self, proc: subprocess.Popen[str], timeout: float, verbose: bool) -> None:
        self.proc = proc
        self.timeout = timeout
        self.verbose = verbose
        self.next_id = 1
        self.pending: dict[int, queue.Queue[RpcResult]] = {}
        self.notifications: queue.Queue[dict[str, Any]] = queue.Queue()
        self.stderr_lines: list[str] = []
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.err_reader = threading.Thread(target=self._read_stderr, daemon=True)
        self.reader.start()
        self.err_reader.start()

    def _read_stdout(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            if self.verbose:
                print(f"< {line}", file=sys.stderr)
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                self.stderr_lines.append(f"non-json stdout: {line}")
                continue
            if "id" in message:
                try:
                    msg_id = int(message["id"])
                except (TypeError, ValueError):
                    continue
                slot = self.pending.get(msg_id)
                if slot is not None:
                    slot.put(RpcResult(message.get("result"), message.get("error")))
            else:
                self.notifications.put(message)

    def _read_stderr(self) -> None:
        assert self.proc.stderr is not None
        for line in self.proc.stderr:
            self.stderr_lines.append(line.rstrip())

    def request(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        msg_id = self.next_id
        self.next_id += 1
        slot: queue.Queue[RpcResult] = queue.Queue(maxsize=1)
        self.pending[msg_id] = slot
        message: dict[str, Any] = {"method": method, "id": msg_id}
        if params is not None:
            message["params"] = params
        self._send(message)
        try:
            reply = slot.get(timeout=self.timeout)
        except queue.Empty as exc:
            raise TimeoutError(f"timed out waiting for {method}") from exc
        finally:
            self.pending.pop(msg_id, None)
        if reply.error is not None:
            raise RuntimeError(f"{method} failed: {json.dumps(reply.error, ensure_ascii=False)}")
        return reply.result or {}

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        message: dict[str, Any] = {"method": method}
        if params is not None:
            message["params"] = params
        self._send(message)

    def _send(self, message: dict[str, Any]) -> None:
        line = json.dumps(message, ensure_ascii=False)
        if self.verbose:
            print(f"> {line}", file=sys.stderr)
        assert self.proc.stdin is not None
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()


def build_target(args: argparse.Namespace) -> dict[str, Any]:
    if args.target == "uncommittedChanges":
        return {"type": "uncommittedChanges"}
    if args.target == "baseBranch":
        if not args.branch:
            raise SystemExit("--branch is required with --target baseBranch")
        return {"type": "baseBranch", "branch": args.branch}
    if args.target == "commit":
        if not args.sha:
            raise SystemExit("--sha is required with --target commit")
        target: dict[str, Any] = {"type": "commit", "sha": args.sha}
        if args.title:
            target["title"] = args.title
        return target
    if args.target == "custom":
        if not args.instructions:
            raise SystemExit("--instructions is required with --target custom")
        return {"type": "custom", "instructions": args.instructions}
    raise SystemExit(f"unsupported target: {args.target}")


def extract_text_from_item(item: dict[str, Any]) -> str | None:
    if item.get("type") == "exitedReviewMode":
        review = item.get("review")
        return review if isinstance(review, str) else None
    return None


def item_fingerprint(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        item.get("id"),
        item.get("type"),
        item.get("status"),
        item.get("exitCode"),
        len(str(item.get("review") or item.get("text") or item.get("aggregatedOutput") or "")),
    )


def fingerprint_turn(turn: dict[str, Any]) -> tuple[Any, ...]:
    items = turn.get("items")
    item_fingerprints: list[tuple[Any, ...]] = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                item_fingerprints.append(item_fingerprint(item))
    return (
        turn.get("id"),
        turn.get("status"),
        turn.get("itemsView"),
        turn.get("completedAt"),
        len(item_fingerprints),
        tuple(item_fingerprints),
    )


def read_review_thread(
    client: AppServerClient,
    thread_id: str,
    turn_id: str | None,
) -> PollSnapshot:
    response = client.request("thread/read", {"threadId": thread_id, "includeTurns": True})
    return extract_poll_snapshot(response, turn_id)


def extract_poll_snapshot(response: dict[str, Any], turn_id: str | None) -> PollSnapshot:
    thread = response.get("thread") or {}
    turns = thread.get("turns") or []
    matching_turns: list[dict[str, Any]] = []
    exact_turn_matched = False
    if isinstance(turns, list):
        for turn in turns:
            if isinstance(turn, dict) and (turn_id is None or turn.get("id") == turn_id):
                matching_turns.append(turn)
                exact_turn_matched = True
    if not matching_turns and isinstance(turns, list):
        matching_turns = [turn for turn in turns if isinstance(turn, dict)]

    latest_visible_text = ""
    latest_review: str | None = None
    final_turn: dict[str, Any] | None = None
    latest_turn = matching_turns[-1] if matching_turns else None
    for turn in matching_turns:
        items = turn.get("items") or []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    intermediate_text = extract_intermediate_text_from_item(item)
                    if intermediate_text:
                        latest_visible_text = intermediate_text
                    review = extract_text_from_item(item)
                    if review is not None:
                        latest_review = review
                        final_turn = turn
        if exact_turn_matched and turn.get("status") in {"completed", "failed", "interrupted"}:
            final_turn = final_turn or turn
    if not exact_turn_matched and isinstance(latest_turn, dict) and latest_turn.get("status") in {"completed", "failed", "interrupted"}:
        final_turn = final_turn or latest_turn

    diagnostics = {
        "threadStatus": thread.get("status"),
        "turnCount": len(turns) if isinstance(turns, list) else None,
        "matchedTurnCount": len(matching_turns),
        "exactTurnMatched": exact_turn_matched,
        "polledTurnStatus": latest_turn.get("status") if isinstance(latest_turn, dict) else None,
        "polledItems": len(latest_turn.get("items") or []) if isinstance(latest_turn, dict) else None,
        "polledItemsView": latest_turn.get("itemsView") if isinstance(latest_turn, dict) else None,
        "fingerprint": fingerprint_turn(latest_turn) if isinstance(latest_turn, dict) else None,
    }
    return PollSnapshot(latest_review, final_turn, latest_visible_text, diagnostics)


def is_transient_thread_read_error(error: Exception) -> bool:
    message = str(error)
    return (
        "is not materialized yet" in message
        or "includeTurns is unavailable before first user message" in message
        or "ephemeral threads do not support includeTurns" in message
    )


def wait_for_review(
    client: AppServerClient,
    review_thread_id: str,
    turn_id: str | None,
    timeout: float,
    idle_timeout: float,
    *,
    min_wait_before_idle: float,
    poll_interval: float,
    progress: bool,
    progress_interval: float,
    show_intermediate: bool,
    intermediate_max_chars: int,
) -> tuple[str, dict[str, Any] | None]:
    started_at = time.monotonic()
    deadline = time.monotonic() + timeout
    next_progress_at = started_at + max(1.0, progress_interval)
    idle_timeout = max(0.0, idle_timeout)
    min_wait_before_idle = max(0.0, min_wait_before_idle)
    poll_interval = max(1.0, poll_interval)
    next_poll_at = started_at
    last_activity_at = started_at
    final_turn: dict[str, Any] | None = None
    latest_review = ""
    latest_visible_text = ""
    latest_poll_diagnostics: dict[str, Any] = {}
    latest_fingerprint: tuple[Any, ...] | None = None
    seen_item_fingerprints: dict[str, tuple[Any, ...]] = {}
    reported_final_review = False
    notification_count = 0
    item_count = 0
    poll_count = 0
    shown_intermediate: set[str] = set()
    last_event = "review/start"
    last_item_type = "-"
    while time.monotonic() < deadline:
        now = time.monotonic()
        if now >= next_poll_at:
            try:
                snapshot = read_review_thread(client, review_thread_id, turn_id)
                poll_count += 1
                latest_poll_diagnostics = snapshot.diagnostics
                fingerprint = snapshot.diagnostics.get("fingerprint")
                if isinstance(fingerprint, tuple) and fingerprint != latest_fingerprint:
                    latest_fingerprint = fingerprint
                    last_activity_at = time.monotonic()
                if snapshot.latest_visible_text:
                    latest_visible_text = snapshot.latest_visible_text
                if snapshot.final_turn is not None:
                    final_turn = snapshot.final_turn
                if snapshot.review is not None:
                    latest_review = snapshot.review
                    if progress and not reported_final_review:
                        print_progress(
                            "received final review text from thread/read "
                            f"(elapsed={format_duration(time.monotonic() - started_at)}, "
                            f"chars={len(snapshot.review)})"
                        )
                    break
            except Exception as exc:
                latest_poll_diagnostics = {"pollError": str(exc)}
                if not is_transient_thread_read_error(exc):
                    latest_poll_diagnostics["pollErrorType"] = type(exc).__name__
            next_poll_at = time.monotonic() + poll_interval
            now = time.monotonic()
        idle_check_enabled = idle_timeout and now - started_at >= min_wait_before_idle
        if idle_check_enabled and now - last_activity_at >= idle_timeout:
            break
        next_deadline = deadline
        if idle_check_enabled:
            next_deadline = min(next_deadline, last_activity_at + idle_timeout)
        next_deadline = min(next_deadline, next_poll_at)
        remaining = max(0.1, min(1.0, next_deadline - now))
        try:
            message = client.notifications.get(timeout=remaining)
        except queue.Empty:
            if client.proc.poll() is not None:
                break
            now = time.monotonic()
            idle_check_enabled = idle_timeout and now - started_at >= min_wait_before_idle
            if idle_check_enabled and now - last_activity_at >= idle_timeout:
                break
            if progress and now >= next_progress_at:
                print_progress(
                    "waiting for final review "
                    f"(elapsed={format_duration(now - started_at)}, "
                    f"remaining={format_duration(deadline - now)}, "
                    f"idle={format_duration(now - last_activity_at)}, "
                    f"notifications={notification_count}, items={item_count}, polls={poll_count}, "
                    f"last_event={last_event}, last_item={last_item_type})"
                )
                next_progress_at = now + max(1.0, progress_interval)
            continue
        method = message.get("method")
        if isinstance(method, str):
            notification_count += 1
            last_event = method
        params = message.get("params") or {}
        item = params.get("item")
        if isinstance(item, dict):
            item_count += 1
            item_id = item.get("id")
            fingerprint = item_fingerprint(item)
            if isinstance(item_id, str) and seen_item_fingerprints.get(item_id) != fingerprint:
                seen_item_fingerprints[item_id] = fingerprint
                last_activity_at = time.monotonic()
            item_type = item.get("type")
            last_item_type = item_type if isinstance(item_type, str) else "-"
            if show_intermediate:
                intermediate_text = extract_intermediate_text_from_item(item)
                if intermediate_text and intermediate_text not in shown_intermediate:
                    shown_intermediate.add(intermediate_text)
                    print_intermediate_text(last_item_type, intermediate_text, intermediate_max_chars)
            intermediate_text = extract_intermediate_text_from_item(item)
            if intermediate_text:
                latest_visible_text = intermediate_text
            review = extract_text_from_item(item)
            if review is not None:
                latest_review = review
                if progress and not reported_final_review:
                    print_progress(
                        "received final review text "
                        f"(elapsed={format_duration(time.monotonic() - started_at)}, "
                        f"chars={len(review)})"
                    )
                    reported_final_review = True
        if method == "turn/completed":
            turn = params.get("turn")
            if isinstance(turn, dict) and (turn_id is None or turn.get("id") == turn_id):
                last_activity_at = time.monotonic()
                final_turn = turn
                for item in turn.get("items") or []:
                    if isinstance(item, dict):
                        if show_intermediate:
                            item_type = item.get("type")
                            item_type_text = item_type if isinstance(item_type, str) else "-"
                            intermediate_text = extract_intermediate_text_from_item(item)
                            if intermediate_text and intermediate_text not in shown_intermediate:
                                shown_intermediate.add(intermediate_text)
                                print_intermediate_text(item_type_text, intermediate_text, intermediate_max_chars)
                        intermediate_text = extract_intermediate_text_from_item(item)
                        if intermediate_text:
                            latest_visible_text = intermediate_text
                        review = extract_text_from_item(item)
                        if review is not None:
                            latest_review = review
                            if progress and not reported_final_review:
                                print_progress(
                                    "received final review text from completed turn "
                                    f"(elapsed={format_duration(time.monotonic() - started_at)}, "
                                    f"chars={len(review)})"
                                )
                                reported_final_review = True
                break
    if not latest_review:
        idle_for = time.monotonic() - last_activity_at
        if final_turn:
            reason = "turn completed without an exitedReviewMode review"
        elif idle_timeout and time.monotonic() - started_at >= min_wait_before_idle and idle_for >= idle_timeout:
            reason = f"no app-server review progress for {format_duration(idle_timeout)}"
        else:
            reason = "timed out waiting for an exitedReviewMode review"
        diagnostics: dict[str, Any] = {
            "reason": reason,
            "elapsed": format_duration(time.monotonic() - started_at),
            "idleFor": format_duration(idle_for),
            "idleTimeout": format_duration(idle_timeout) if idle_timeout else None,
            "minWaitBeforeIdle": format_duration(min_wait_before_idle),
            "notifications": notification_count,
            "items": item_count,
            "polls": poll_count,
            "latestPoll": latest_poll_diagnostics,
            "lastEvent": last_event,
            "lastItem": last_item_type,
            "turnStatus": final_turn.get("status") if isinstance(final_turn, dict) else None,
            "latestVisibleText": latest_visible_text[-4000:] if latest_visible_text else "",
        }
        raise ReviewWaitError(reason, diagnostics)
    return latest_review, final_turn


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one Codex app-server review pass.")
    parser.add_argument("--cwd", default=os.getcwd(), help="Repository working directory for the review thread.")
    parser.add_argument("--target", choices=["uncommittedChanges", "baseBranch", "commit", "custom"], default="uncommittedChanges")
    parser.add_argument("--branch", help="Base branch for --target baseBranch.")
    parser.add_argument("--sha", help="Commit SHA for --target commit.")
    parser.add_argument("--title", help="Optional commit title for --target commit.")
    parser.add_argument("--instructions", help="Custom review instructions for --target custom.")
    parser.add_argument("--delivery", choices=["inline", "detached"], default="inline")
    parser.add_argument("--model", help="Optional model override for thread/start.")
    parser.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        default="workspace-write",
        help="Sandbox mode for the review thread. workspace-write is the default because review needs git diff access and some shells create temporary files.",
    )
    parser.add_argument("--timeout", type=float, default=2700.0, help="Overall review wait timeout in seconds.")
    parser.add_argument(
        "--idle-timeout",
        type=float,
        default=600.0,
        help="Abort when no app-server notifications or thread/read state changes arrive for this many seconds. Use 0 to disable.",
    )
    parser.add_argument(
        "--min-wait-before-idle",
        type=float,
        default=300.0,
        help="Do not enforce --idle-timeout until at least this many seconds have elapsed.",
    )
    parser.add_argument("--poll-interval", type=float, default=30.0, help="Seconds between active thread/read polls.")
    parser.add_argument("--rpc-timeout", type=float, default=60.0, help="Per-request timeout in seconds.")
    parser.add_argument("--progress-interval", type=float, default=60.0, help="Progress heartbeat interval in seconds.")
    parser.add_argument("--quiet-progress", action="store_true", help="Suppress progress heartbeat messages on stderr.")
    parser.add_argument(
        "--no-opt-out-noise",
        action="store_true",
        help="Do not ask app-server to suppress unrelated status notifications.",
    )
    parser.add_argument("--show-intermediate", action="store_true", help="Print visible intermediate review messages to stderr.")
    parser.add_argument("--intermediate-max-chars", type=int, default=4000, help="Maximum characters per intermediate text block.")
    parser.add_argument(
        "--ephemeral",
        action="store_true",
        help="Create an ephemeral review thread. This disables active thread/read recovery because ephemeral threads do not persist turns.",
    )
    parser.add_argument(
        "--keep-review-thread",
        action="store_true",
        help="Keep the temporary non-ephemeral review thread visible instead of archiving it at exit.",
    )
    parser.add_argument("--json", action="store_true", help="Print structured JSON instead of review text.")
    parser.add_argument("--verbose", action="store_true", help="Print JSON-RPC traffic to stderr.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cwd = str(Path(args.cwd).expanduser().resolve())
    target = build_target(args)
    thread_id: str | None = None
    proc = subprocess.Popen(
        ["codex", "app-server", "--stdio"],
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    client = AppServerClient(proc, args.rpc_timeout, args.verbose)
    try:
        client.request(
            "initialize",
            {
                "clientInfo": {"name": "rumo-review-fix-loop", "version": "1.0.0", "title": "Rumo Review Fix Loop"},
                "capabilities": {
                    "experimentalApi": False,
                    "requestAttestation": False,
                    "optOutNotificationMethods": [] if args.no_opt_out_noise else DEFAULT_OPT_OUT_NOTIFICATIONS,
                },
            },
        )
        client.notify("initialized")
        thread_params: dict[str, Any] = {
            "cwd": cwd,
            "sandbox": args.sandbox,
            "approvalPolicy": "never",
            "serviceName": "rumo_review_fix_loop",
            "threadSource": "user",
            "ephemeral": bool(args.ephemeral),
        }
        if args.model:
            thread_params["model"] = args.model
        thread_result = client.request("thread/start", thread_params)
        thread = thread_result.get("thread") or {}
        thread_id = thread.get("id")
        if not isinstance(thread_id, str) or not thread_id:
            raise RuntimeError(f"thread/start did not return a thread id: {thread_result!r}")
        if not args.quiet_progress:
            print_progress(
                f"started review thread={thread_id} target={json.dumps(target, ensure_ascii=False)} "
                f"timeout={format_duration(args.timeout)}"
            )
        review_result = client.request(
            "review/start",
            {"threadId": thread_id, "delivery": args.delivery, "target": target},
        )
        turn = review_result.get("turn") or {}
        turn_id = turn.get("id") if isinstance(turn, dict) else None
        if not args.quiet_progress:
            review_thread_id = review_result.get("reviewThreadId")
            print_progress(
                f"review started turn={turn_id or '-'} reviewThread={review_thread_id or '-'} "
                "waiting for final review text"
            )
        review_thread_id = review_result.get("reviewThreadId")
        if not isinstance(review_thread_id, str) or not review_thread_id:
            review_thread_id = thread_id
        review_text, final_turn = wait_for_review(
            client,
            review_thread_id,
            turn_id if isinstance(turn_id, str) else None,
            args.timeout,
            args.idle_timeout,
            min_wait_before_idle=args.min_wait_before_idle,
            poll_interval=args.poll_interval,
            progress=not args.quiet_progress,
            progress_interval=args.progress_interval,
            show_intermediate=args.show_intermediate,
            intermediate_max_chars=args.intermediate_max_chars,
        )
        has_blocking = bool(BLOCKING_RE.search(review_text))
        if args.json:
            print(
                json.dumps(
                    {
                        "target": target,
                        "threadId": thread_id,
                        "reviewThreadId": review_result.get("reviewThreadId"),
                        "turnId": turn_id,
                        "hasBlockingFinding": has_blocking,
                        "review": review_text,
                        "turnStatus": final_turn.get("status") if isinstance(final_turn, dict) else None,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(review_text)
            print(f"\n[rumo-review-fix-loop] blocking finding detected: {'yes' if has_blocking else 'no'}", file=sys.stderr)
        return 2 if has_blocking else 0
    except ReviewWaitError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "target": target,
                        "hasBlockingFinding": None,
                        "review": "",
                        "error": "missingExitedReviewMode",
                        "diagnostics": exc.diagnostics,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        print(f"app_server_review.py: {exc}", file=sys.stderr)
        latest_visible_text = exc.diagnostics.get("latestVisibleText")
        if isinstance(latest_visible_text, str) and latest_visible_text:
            print("latest visible text before failure:", file=sys.stderr)
            print(latest_visible_text, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"app_server_review.py: {exc}", file=sys.stderr)
        if client.stderr_lines:
            print("app-server stderr:", file=sys.stderr)
            for line in client.stderr_lines[-20:]:
                print(line, file=sys.stderr)
        return 1
    finally:
        if thread_id and not args.ephemeral and not args.keep_review_thread:
            try:
                client.request("thread/archive", {"threadId": thread_id})
                if not args.quiet_progress:
                    print_progress(f"archived temporary review thread={thread_id}")
            except Exception as exc:
                if not args.quiet_progress:
                    print_progress(f"failed to archive temporary review thread={thread_id}: {exc}")
        try:
            if proc.stdin:
                proc.stdin.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
