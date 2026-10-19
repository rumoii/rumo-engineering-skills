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
import subprocess

try:
    from .run_codex_behavior import SAMPLE_AUTHOR, blind_workspace, evidence, file_state, git, leaked_words, read_events, run_turn, skill_overrides, toml_overrides, write_json
except ImportError:
    from run_codex_behavior import SAMPLE_AUTHOR, blind_workspace, evidence, file_state, git, leaked_words, read_events, run_turn, skill_overrides, toml_overrides, write_json


REPO_ROOT = Path(__file__).resolve().parents[1]
EVALS_ROOT = REPO_ROOT / "evals"
# Same rule as scripts/tests/test_trigger_evals.py: the skill name closes the grader's input_match.
SKILL_IN_PATTERN = re.compile(r"\)\?(rumo-[a-z0-9-]+)\"'?$")
# Claude does not load the baseline skill for a small edit (see CONTRIBUTING); flag a Codex pass separately.
EXPECTED_FAILURES = {"coding-baseline"}
# Neutral instructions: no skill names and no hints about tests or commands.
SAMPLE_AGENTS = (
    "# Local sample\nWork only inside this directory. Do not use network tools, other agents, "
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
