#!/usr/bin/env python3
"""Run the evals/ trigger cases through pi without naming a skill; record which sample skills it reads."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import uuid

try:
    from .run_codex_behavior import blind_workspace, file_state, leaked_words, read_events, run_turn, write_json
    from .run_codex_trigger import EXPECTED_FAILURES, REPO_ROOT, judge, load_cases, seed_trigger
    from .run_pi_behavior import DEFAULT_MODEL, READ_ONLY_TOOLS, WORKSPACE_GUARD, evidence
except ImportError:
    from run_codex_behavior import blind_workspace, file_state, leaked_words, read_events, run_turn, write_json
    from run_codex_trigger import EXPECTED_FAILURES, REPO_ROOT, judge, load_cases, seed_trigger
    from run_pi_behavior import DEFAULT_MODEL, READ_ONLY_TOOLS, WORKSPACE_GUARD, evidence


def pi_command(pi: str, model: str, session_dir: Path, session_id: str, skill_dirs: list[Path]) -> list[str]:
    """Only the sample's skills load. Context files are off because pi also reads the user's and parent
    directories' AGENTS.md, MCP is off because --tools does not remove MCP tools, and the workspace
    guard keeps the read-only tools inside the sample."""
    command = [
        pi, "-p", "--mode", "json", "--no-extensions", "-e", str(WORKSPACE_GUARD), "--no-skills", "--no-prompt-templates", "--no-themes",
        "--no-mcp", "--no-context-files", "--tools", READ_ONLY_TOOLS, "--model", model,
        "--session-dir", str(session_dir), "--session-id", session_id,
    ]
    for skill_dir in skill_dirs:
        command += ["--skill", str(skill_dir)]
    return command


def run_case(args: argparse.Namespace, name: str, case: dict, run: int) -> dict:
    out = args.output_dir / name / f"run-{run}"
    out.mkdir(parents=True, exist_ok=False)
    root = blind_workspace(args.workspace_root)
    seed_trigger(root, args.snapshot)
    skill_dirs = sorted(path.parent for path in (root / ".agents" / "skills").glob("rumo-*/SKILL.md"))
    skills = [path.name for path in skill_dirs]
    command = pi_command(args.pi, args.model, out / "sessions", str(uuid.uuid4()), skill_dirs)
    code, timed_out = run_turn(command, case["prompt"], root, out / "turn-1", args.timeout)
    try:
        events, parse_error = read_events(out / "turn-1.jsonl"), None
    except (ValueError, OSError) as exc:
        events, parse_error = [], f"{type(exc).__name__}: execution trace is missing or malformed"
    observed = evidence(events, root, skills)
    read = {skill for skill, loaded in observed["loaded_skill_paths"].items() if loaded}
    valid = (code == 0 and not timed_out and observed["turn_completed"] and not observed["errors"]
             and not parse_error and not observed["context_files"]
             and all(escape["blocked"] for escape in observed["workspace_escapes"]))
    verdict = "invalid" if not valid else "pass" if judge(case, read) else "fail"
    result = {
        "case": name, "run": run, "workspace": str(root), "verdict": verdict, "expected_failure": name in EXPECTED_FAILURES,
        "expect": case["expect"], "avoid": case["avoid"], "no_rumo": case["no_rumo"], "read": sorted(read),
        "exit_code": code, "timed_out": timed_out, "parse_error": parse_error, "errors": observed["errors"],
        "context_files": observed["context_files"], "workspace_escapes": observed["workspace_escapes"],
        "messages": observed["messages"], "usage": observed["usage"],
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
    parser.add_argument("--workspace-root", type=Path, help="Where working copies go; default --output-dir. The model sees this path.")
    parser.add_argument("--pi", default="pi")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="pi model as provider/id.")
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
    args.workspace_root = (args.workspace_root or args.output_dir).resolve()
    if leaked_words(args.workspace_root, cases):
        parser.error(f"The model sees the workspace root's path; rename it without: {', '.join(leaked_words(args.workspace_root, cases))}.")
    if args.output_dir.exists():
        parser.error("Use a new output directory.")
    args.pi = shutil.which(args.pi) or args.pi
    args.output_dir.mkdir(parents=True)
    snapshot_state = file_state(args.snapshot)
    names = args.case or list(cases)
    write_json(args.output_dir / "run.json", {
        "snapshot": str(args.snapshot), "snapshot_files": snapshot_state,
        "pi_version": subprocess.check_output([args.pi, "--version"], text=True).strip(), "model": args.model,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": {name: cases[name] for name in names}, "runs": args.runs, "timeout": args.timeout,
    })
    results = []
    for name in names:
        for run in range(1, args.runs + 1):
            result = run_case(args, name, cases[name], run)
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
