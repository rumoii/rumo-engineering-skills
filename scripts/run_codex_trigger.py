#!/usr/bin/env python3
"""Run the evals/ trigger cases through Codex without naming a skill; record which sample skills it reads."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
import tomllib
import uuid


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


# A model that can tell it is being graded behaves unlike one doing real work, so
# the path it works in names neither the case nor the evaluation.
BLIND_WORDS = {"baseline", "benchmark", "candidate", "eval", "evals", "evaluation", "fixture", "fixtures",
               "grader", "graders", "judge", "rubric", "test", "tests", "testing"}
SAMPLE_AUTHOR = ("-c", "user.name=Sam Lee", "-c", "user.email=sam@example.invalid")


def leaked_words(path: Path, case_names: object = ()) -> list[str]:
    """Evaluation words and case names that appear in a path the model can see."""
    tokens = {token for part in path.parts for token in re.split(r"[^a-z0-9]+", part.lower())}
    text = path.as_posix().lower()
    return sorted((tokens & BLIND_WORDS) | {name for name in case_names if name.lower() in text})


def blind_workspace(workspace_root: Path) -> Path:
    """Working copy under the workspace root, apart from the case's logs, named only by a random token."""
    return workspace_root / "w" / uuid.uuid4().hex[:8] / "project"


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


def run_turn(command: list[str], prompt: str, root: Path, prefix: Path, timeout: float, env: dict | None = None) -> tuple[int, bool]:
    """env replaces the child environment when given; it is never written to disk."""
    kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    if env is not None:
        kwargs["env"] = env
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


def normalized_path_text(text: str) -> str:
    return re.sub(r"/+", "/", text.replace("\\", "/")).lower()


def reads_sample_skill(command: str, root: Path, name: str) -> bool:
    """Accept the skill path relative to the sample or absolute under it, never a same-named copy elsewhere."""
    text = normalized_path_text(command)
    sample = normalized_path_text(str(root)).rstrip("/") + "/"
    for match in re.finditer(re.escape(f".agents/skills/{name}/skill.md"), text):
        before = text[:match.start()]
        if before.endswith(sample) or re.search(r"(?:^|[\s\"'=])(?:\./)?$", before):
            return True
    return False


def evidence(events: list[dict], root: Path, skills: list[str]) -> dict:
    completed = [e["item"] for e in events if e.get("type") == "item.completed" and isinstance(e.get("item"), dict)]
    commands = [item for item in completed if item.get("type") == "command_execution"]
    messages = [item.get("text", "") for item in completed if item.get("type") == "agent_message"]
    loaded = {
        name: any(
            item.get("status") == "completed" and item.get("exit_code") == 0
            and reads_sample_skill(item.get("command", ""), root, name)
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


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_ROOT = REPO_ROOT / "evals"
# Same rule as scripts/tests/test_trigger_evals.py: the skill name closes the grader's input_match.
SKILL_IN_PATTERN = re.compile(r"\)\?(rumo-[a-z0-9-]+)\"'?$")
# Claude does not load the baseline skill for a small edit (see CONTRIBUTING); flag a Codex pass separately.
EXPECTED_FAILURES = {"coding-baseline"}
# Neutral instructions: no skill names and no hints about tests or commands.
SAMPLE_AGENTS = (
    "# Local sample\nWork only inside this directory. Do not use network tools, "
    "credentials, or other projects. Do not install dependencies.\n"
)


def frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text:
        raise ValueError(f"{path}: missing frontmatter")
    head, body = text[4:].split("\n---\n", 1)
    fields = {}
    for line in head.splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, body.strip()


def load_cases(evals: Path = EVALS_ROOT) -> dict[str, dict]:
    """Read expectations from the graders; an unparseable grader is an error, never a silent skip."""
    cases = {}
    for case in sorted(path for path in evals.iterdir() if (path / "prompt.md").is_file()):
        fields, prompt = frontmatter(case / "prompt.md")
        if "trigger" not in fields.get("tags", ""):
            continue
        expect, avoid, no_rumo = set(), set(), False
        for grader in sorted((case / "graders").glob("*.md")):
            if grader.stem == "uses-no-rumo-skill":
                no_rumo = True
                continue
            match = SKILL_IN_PATTERN.search(frontmatter(grader)[0].get("input_match", ""))
            if not match or not grader.stem.startswith(("uses-", "skips-")):
                raise ValueError(f"{grader}: cannot read the expected skill")
            (expect if grader.stem.startswith("uses-") else avoid).add(match.group(1))
        if not (expect or avoid or no_rumo) or not prompt:
            raise ValueError(f"{case}: trigger case has no prompt or expectation")
        cases[case.name] = {"prompt": prompt, "expect": sorted(expect), "avoid": sorted(avoid), "no_rumo": no_rumo}
    return cases


def judge(case: dict, read: set[str]) -> bool:
    if case["no_rumo"]:
        return not read
    return set(case["expect"]) <= read and not read & set(case["avoid"])


def seed_trigger(root: Path, snapshot: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(snapshot / "skills", root / ".agents" / "skills")
    (root / ".gitignore").write_text(".agents/\n", encoding="utf-8")
    (root / "AGENTS.md").write_text(SAMPLE_AGENTS, encoding="utf-8")
    git(root, "init", "-q")
    git(root, *SAMPLE_AUTHOR, "add", ".")
    git(root, *SAMPLE_AUTHOR, "commit", "-qm", "Seed trigger sample")


def run_case(args: argparse.Namespace, name: str, case: dict, run: int, overrides: list[dict], settings: dict) -> dict:
    out = args.output_dir / name / f"run-{run}"
    out.mkdir(parents=True, exist_ok=False)
    root = blind_workspace(args.output_dir)
    seed_trigger(root, args.snapshot)
    skills = sorted(path.parent.name for path in (root / ".agents" / "skills").glob("rumo-*/SKILL.md"))
    command = [args.codex, "exec", "--json", "-c", toml_overrides(overrides), "-c", 'approval_policy="never"']
    if os.name == "nt":
        command += ["-c", 'windows.sandbox="unelevated"']
    for key, value in settings.items():
        command += ["-c", key + "=" + json.dumps(value)]
    command += ["--sandbox", "read-only", "--cd", str(root), "-"]
    code, timed_out = run_turn(command, case["prompt"], root, out / "turn-1", args.timeout)
    try:
        events, parse_error = read_events(out / "turn-1.jsonl"), None
    except (ValueError, OSError) as exc:
        events, parse_error = [], f"{type(exc).__name__}: execution trace is missing or malformed"
    observed = evidence(events, root, skills)
    read = {skill for skill, loaded in observed["loaded_skill_paths"].items() if loaded}
    valid = code == 0 and not timed_out and observed["turn_completed"] and not observed["errors"] and not parse_error
    verdict = "invalid" if not valid else "pass" if judge(case, read) else "fail"
    result = {
        "case": name, "run": run, "workspace": str(root), "verdict": verdict, "expected_failure": name in EXPECTED_FAILURES,
        "expect": case["expect"], "avoid": case["avoid"], "no_rumo": case["no_rumo"], "read": sorted(read),
        "exit_code": code, "timed_out": timed_out, "parse_error": parse_error, "errors": observed["errors"],
        "messages": observed["messages"],
    }
    if result["expected_failure"] and verdict == "pass":
        result["note"] = "Loaded the baseline that Claude skips on small edits; compare clients before reading it as a description change."
    write_json(out / "result.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    cases = load_cases()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Snapshot containing skills/.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New task-owned directory outside the skill checkout.")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--case", action="append", choices=sorted(cases))
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=300, help="Seconds per run.")
    args = parser.parse_args(argv)
    args.snapshot = args.snapshot.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.timeout <= 0 or args.runs <= 0 or not (args.snapshot / "skills").is_dir():
        parser.error("Use a positive timeout and run count, and a snapshot containing skills/.")
    if args.output_dir.is_relative_to(REPO_ROOT) or args.output_dir.is_relative_to(args.snapshot):
        parser.error("Evidence must be outside the source checkout and snapshot.")
    if leaked_words(args.output_dir, cases):
        parser.error(f"The model sees the output directory's path; rename it without: {', '.join(leaked_words(args.output_dir, cases))}.")
    if args.output_dir.exists():
        parser.error("Use a new output directory.")
    args.codex = shutil.which(args.codex) or args.codex
    overrides, settings = skill_overrides()
    args.output_dir.mkdir(parents=True)
    snapshot_state = file_state(args.snapshot)
    names = args.case or list(cases)
    write_json(args.output_dir / "run.json", {
        "snapshot": str(args.snapshot), "snapshot_files": snapshot_state,
        "codex_version": subprocess.check_output([args.codex, "--version"], text=True).strip(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "settings": settings, "cases": {name: cases[name] for name in names}, "runs": args.runs, "timeout": args.timeout,
    })
    results = []
    for name in names:
        for run in range(1, args.runs + 1):
            result = run_case(args, name, cases[name], run, overrides, settings)
            if file_state(args.snapshot) != snapshot_state:
                result["verdict"] = "invalid"
                result["snapshot_changed"] = True
            results.append(result)
            write_json(args.output_dir / "results.json", results)
            expected = "none" if result["no_rumo"] else ",".join(result["expect"]) or "-"
            print(f"{name:28} run {run}: {result['verdict']:7} expect={expected} avoid={','.join(result['avoid']) or '-'} "
                  f"read={','.join(result['read']) or '-'}{'  [' + result['note'] + ']' if 'note' in result else ''}", flush=True)
            if result["verdict"] == "invalid":
                print("Stopped: invalid runtime evidence; inspect the saved trace before another run.", flush=True)
                return 2
    failed = [r for r in results if r["verdict"] == "fail" and not r["expected_failure"]]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
