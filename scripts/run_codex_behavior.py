#!/usr/bin/env python3
"""Run isolated Codex skill-body cases; keep mechanical evidence separate from review verdicts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import time
import tomllib

try:
    from .codex_behavior_cases import CASES
except ImportError:
    from codex_behavior_cases import CASES


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def file_state(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file() and not any(part in {".git", ".agents", "__pycache__"} for part in p.relative_to(root).parts)
        and p.suffix != ".pyc"
    }


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, encoding="utf-8").strip()


def seed(root: Path, snapshot: Path, case: dict) -> None:
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(snapshot / "skills", root / ".agents" / "skills")
    files = {**case["files"], **case.get("committed", {})}
    files[".gitignore"] = ".agents/\n__pycache__/\n*.pyc\n"
    files["AGENTS.md"] = (
        "# Local sample\nUse only this sample and its .agents/skills. Do not access network tools, "
        "other agents, credentials, or other projects. A Python unittest is the maintained "
        "check where a test_*.py exists. Do not install dependencies.\n"
    )
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    for name in case.get("databases", []):
        with sqlite3.connect(root / name) as db:
            db.execute("CREATE TABLE jobs (id INTEGER PRIMARY KEY, created_at TEXT)")
            db.execute("INSERT INTO jobs VALUES (1, '2025-01-01')")
    git(root, "init", "-q")
    git(root, "-c", "user.name=Behavior fixture", "-c", "user.email=fixture@example.invalid", "add", ".")
    git(root, "-c", "user.name=Behavior fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Seed local sample")
    for name, content in case.get("dirty", {}).items():
        (root / name).write_text(content, encoding="utf-8")


def skill_overrides() -> tuple[list[dict], dict]:
    """Preserve other overrides and auth; disable installed Rumo copies for this process only."""
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_path = home / "config.toml"
    config = tomllib.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    overrides = list(config.get("skills", {}).get("config", []))
    paths: set[str] = set()
    for root in (home / "skills", Path.home() / ".agents/skills", Path.home() / ".codex/skills"):
        for skill in root.glob("rumo-*/SKILL.md"):
            for path in (skill, skill.parent, skill.resolve(), skill.parent.resolve()):
                paths.add(str(path))
    overrides.extend({"path": path, "enabled": False} for path in sorted(paths))
    settings = {k: config[k] for k in ("model", "model_reasoning_effort", "model_provider") if k in config}
    return overrides, settings


def toml_overrides(entries: list[dict]) -> str:
    return "skills.config=[" + ",".join(
        "{path=" + json.dumps(entry["path"]) + ",enabled=" + str(entry.get("enabled", True)).lower() + "}"
        for entry in entries
    ) + "]"


def stop_owned_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True, timeout=20, check=False)
    else:
        os.killpg(proc.pid, signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=10)


def run_turn(command: list[str], prompt: str, root: Path, prefix: Path, timeout: float) -> tuple[int, bool]:
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    (prefix.with_suffix(".prompt.txt")).write_text(prompt, encoding="utf-8")
    write_json(prefix.with_suffix(".command.json"), command)
    with prefix.with_suffix(".jsonl").open("wb") as out, prefix.with_suffix(".stderr.txt").open("wb") as err:
        proc = subprocess.Popen(command, cwd=root, stdin=subprocess.PIPE, stdout=out, stderr=err, **kwargs)
        started = time.monotonic()
        timed_out = False
        try:
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()
            while proc.poll() is None:
                if time.monotonic() - started >= timeout:
                    timed_out = True
                    break
                try:
                    proc.wait(timeout=min(30, max(0.01, timeout - (time.monotonic() - started))))
                except subprocess.TimeoutExpired:
                    print(f"  waiting {int(time.monotonic() - started)}s: {root.name}", flush=True)
        finally:
            stop_owned_process(proc)
        return proc.returncode, timed_out


def read_events(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("Expected a JSON event object")
            events.append(value)
    return events


def evidence(events: list[dict], root: Path, skills: list[str]) -> dict:
    completed = [e["item"] for e in events if e.get("type") == "item.completed" and isinstance(e.get("item"), dict)]
    commands = [item for item in completed if item.get("type") == "command_execution"]
    messages = [item.get("text", "") for item in completed if item.get("type") == "agent_message"]
    loaded = {
        name: any(
            item.get("status") == "completed" and item.get("exit_code") == 0
            and f".agents/skills/{name}/skill.md" in re.sub(r"/+", "/", item.get("command", "").replace("\\", "/")).lower()
            and f"name: {name}" in item.get("aggregated_output", "")
            for item in commands
        ) for name in skills
    }
    return {
        "turn_completed": any(e.get("type") == "turn.completed" for e in events),
        "errors": [e for e in events if e.get("type") in {"error", "turn.failed"}],
        "loaded_skill_paths": loaded,
        "commands": commands,
        "file_changes": [item for item in completed if item.get("type") == "file_change"],
        "messages": messages,
        "thread_id": next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), None),
    }


def completed_cart_test(commands: list[dict]) -> bool:
    """Require a completed test process and its known assertion, never a command mention alone."""
    for item in commands:
        command = item.get("command", "")
        script = re.split(r"\s-(?:Command|lc|c)\s+", command, maxsplit=1, flags=re.I)[-1].strip()
        if len(script) >= 2 and script[0] == script[-1] and script[0] in "\"'":
            script = script[1:-1]
        invoked = re.match(r"^\s*(?:python(?:3(?:\.\d+)?)?|py(?:\s+-3)?)\s+(?:-B\s+)?(?:-m\s+(?:unittest|pytest)\b|test_cart\.py\b)", script)
        output = item.get("aggregated_output", "")
        if (item.get("status") in {"completed", "failed"} and item.get("exit_code") == 1
                and "test_multiplies_price_by_quantity" in output and "AssertionError: 7 != 17" in output
                and "FAILED (failures=1)" in output and invoked):
            return True
    return False


def run_case(args: argparse.Namespace, name: str, overrides: list[dict], settings: dict) -> dict:
    case = CASES[name]
    out = args.output_dir / name
    out.mkdir(parents=True, exist_ok=False)
    root = out / "sample"
    seed(root, args.snapshot, case)
    before = file_state(root)
    head = git(root, "rev-parse", "HEAD")
    index = git(root, "diff", "--cached", "--binary")
    skills_before = file_state(root / ".agents" / "skills")
    base = [args.codex, "exec", "--json", "-c", toml_overrides(overrides), "-c", 'approval_policy="never"']
    if os.name == "nt":
        base += ["-c", 'windows.sandbox="unelevated"']
    for key, value in settings.items():
        base += ["-c", key + "=" + json.dumps(value)]
    all_events: list[dict] = []
    runs = []
    started = time.monotonic()
    thread = None
    for turn, question in enumerate(case["turns"], 1):
        if turn == 1:
            paths = "\n".join(str(root / ".agents" / "skills" / name / "SKILL.md") for name in case["skills"])
            prompt = f"Read and apply these exact skill files and their applicable references before acting:\n{paths}\n\n{question}"
            command = [*base, "--sandbox", "workspace-write", "--cd", str(root), "-"]
        else:
            if not thread:
                break
            prompt = question
            command = [*base, "resume", thread, "-"]
        prefix = out / f"turn-{turn}"
        remaining = args.timeout - (time.monotonic() - started)
        code, timed_out = run_turn(command, prompt, root, prefix, max(0.01, remaining))
        parse_error = None
        try:
            events = read_events(prefix.with_suffix(".jsonl"))
        except (ValueError, OSError) as exc:
            events = []
            parse_error = f"{type(exc).__name__}: execution trace is missing or malformed"
        all_events.extend(events)
        current = evidence(events, root, [])
        thread = current["thread_id"] or thread
        runs.append({"turn": turn, "exit_code": code, "timed_out": timed_out, "completed": current["turn_completed"], "parse_error": parse_error})
        if code != 0 or timed_out or not current["turn_completed"] or current["errors"]:
            break
    observed = evidence(all_events, root, case["skills"])
    after = file_state(root)
    changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    protected_skills_unchanged = file_state(root / ".agents" / "skills") == skills_before
    valid = (len(runs) == len(case["turns"]) and all(r["exit_code"] == 0 and not r["timed_out"] and r["completed"] for r in runs)
             and all(observed["loaded_skill_paths"].values()) and not observed["errors"] and protected_skills_unchanged)
    checks = {"head_unchanged": git(root, "rev-parse", "HEAD") == head, "index_unchanged": git(root, "diff", "--cached", "--binary") == index, "skill_files_unchanged": protected_skills_unchanged}
    if case["read_only"]:
        checks["sample_unchanged"] = not changed
    if name == "verify-honest":
        checks["completed_failing_test"] = completed_cart_test(observed["commands"])
    if name == "risk-proportionate":
        checks["only_login_copy_changed"] = changed == ["login.html"] and (root / "login.html").read_text(encoding="utf-8") == '<button type="submit">进入工作台</button>\n'
    result = {
        "case": name, "snapshot": str(args.snapshot), "settings": settings, "runs": runs,
        "evidence_status": "valid" if valid else "invalid", "mechanical_checks": checks,
        "changed_files": changed, "before": before, "after": after,
        "observed": observed, "review_verdict": "pending", "acceptance": case["rubric"],
    }
    write_json(out / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Snapshot containing skills/.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New task-owned directory outside the skill checkout.")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--case", action="append", choices=sorted(CASES))
    parser.add_argument("--timeout", type=int, default=600, help="Overall seconds per case, across its turns.")
    args = parser.parse_args()
    args.snapshot = args.snapshot.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.timeout <= 0 or not (args.snapshot / "skills").is_dir():
        parser.error("Use a positive timeout and a snapshot containing skills/.")
    repo = Path(__file__).resolve().parents[1]
    if args.output_dir.is_relative_to(repo) or args.output_dir.is_relative_to(args.snapshot):
        parser.error("Evidence must be outside the source checkout and snapshot.")
    args.codex = shutil.which(args.codex) or args.codex
    overrides, settings = skill_overrides()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    snapshot_state = file_state(args.snapshot)
    write_json(args.output_dir / "run.json", {
        "snapshot": str(args.snapshot), "snapshot_files": snapshot_state,
        "codex_version": subprocess.check_output([args.codex, "--version"], text=True).strip(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(Path(__file__).with_name("codex_behavior_cases.py").read_bytes()).hexdigest(),
        "settings": settings, "cases": args.case or list(CASES), "timeout": args.timeout,
    })
    results = []
    for name in args.case or CASES:
        print(f"Running {name}", flush=True)
        result = run_case(args, name, overrides, settings)
        if file_state(args.snapshot) != snapshot_state:
            result["evidence_status"] = "invalid"
            result["snapshot_changed"] = True
            write_json(args.output_dir / name / "result.json", result)
        results.append(result)
        write_json(args.output_dir / "results.json", results)
        print(f"  {result['evidence_status']}; mechanical checks: {result['mechanical_checks']}; review verdict pending", flush=True)
        if result["evidence_status"] != "valid":
            print("Stopped: invalid runtime or skill-loading evidence; inspect the saved trace before another run.", flush=True)
            return 2
    return 0 if all(all(r["mechanical_checks"].values()) for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
