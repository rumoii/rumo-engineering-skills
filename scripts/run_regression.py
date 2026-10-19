#!/usr/bin/env python3
"""Rerun the regression cases for a candidate skill snapshot against a baseline, through one behavior runner.

Runner-specific options go after `--`, for example the per-case timeout:
  run_regression.py --candidate SNAP --baseline without --output-dir OUT -- --timeout 1200
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import statistics
from pathlib import Path
import subprocess
import sys

try:
    from .codex_behavior_cases import CASES, REGRESSION
    from .run_codex_behavior import leaked_words
except ImportError:
    from codex_behavior_cases import CASES, REGRESSION
    from run_codex_behavior import leaked_words


SCRIPTS = Path(__file__).resolve().parent
RUNNERS = {"pi": "run_pi_behavior.py", "codex": "run_codex_behavior.py"}


def jobs(runner: str, cases: list[str], reps: int) -> list[tuple[str, int, str]]:
    """Every case in both arms, repetitions interleaved so an interrupted batch still leaves paired runs."""
    usable = [name for name in cases if runner != "pi" or CASES[name]["read_only"]]
    return [(arm, rep, name) for rep in range(1, reps + 1) for name in usable for arm in ("candidate", "baseline")]


def arm_options(arm: str, candidate: Path, baseline: str) -> list[str]:
    if arm == "candidate":
        return ["--snapshot", str(candidate)]
    if baseline == "without":
        return ["--snapshot", str(candidate), "--without-skills"]
    return ["--snapshot", str(Path(baseline).resolve())]


def run_dir(output_dir: Path, runner: str, job: tuple[str, int, str]) -> Path:
    arm, rep, name = job
    return output_dir / f"{runner}-{arm}-{rep}-{name}"


def invoke(command: list[str], log: Path) -> int:
    with log.open("wb") as out:
        return subprocess.run(command, stdout=out, stderr=subprocess.STDOUT, check=False).returncode


def load_result(directory: Path, name: str) -> dict | None:
    path = directory / name / "result.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def summarize(output_dir: Path, runner: str, planned: list[tuple[str, int, str]], codes: dict) -> tuple[dict, str]:
    table: dict[str, dict[str, dict]] = {}
    lines = [f"# Regression summary ({runner})", ""]
    for job in planned:
        arm, rep, name = job
        result = load_result(run_dir(output_dir, runner, job), name)
        cell = table.setdefault(name, {}).setdefault(arm, {"runs": 0, "valid": 0, "mechanical_pass": 0, "not_run": 0, "tokens": []})
        if job not in codes:
            cell["not_run"] += 1
            continue
        cell["runs"] += 1
        if result and result.get("evidence_status") == "valid":
            cell["valid"] += 1
            cell["mechanical_pass"] += all(result.get("mechanical_checks", {}).values())
            total = ((result.get("observed") or {}).get("usage") or {}).get("totalTokens")
            if isinstance(total, int):
                cell["tokens"].append(total)
    for name, arms in table.items():
        lines += [f"## {name}", "", f"Expected (with skills): {REGRESSION.get(name, CASES[name]['rubric'])}", ""]
        for arm, cell in arms.items():
            lines.append(f"- {arm}: {cell['valid']}/{cell['runs']} valid, {cell['mechanical_pass']} passed mechanical checks"
                         + (f", {cell['not_run']} not run" if cell["not_run"] else "")
                         + (f", median {int(statistics.median(cell['tokens']))} tokens" if cell["tokens"] else ""))
        lines += ["", "Final replies, for grading against the expectation:", ""]
        for job in planned:
            if job[2] != name or job not in codes:
                continue
            result = load_result(run_dir(output_dir, runner, job), name) or {}
            messages = (result.get("observed") or {}).get("messages") or []
            status = result.get("evidence_status", f"no result (exit {codes[job]})")
            lines += [f"### {job[0]} {job[1]} ({status})", "", "```text", (messages[-1] if messages else "(no reply)").replace("```", "'''"), "```", ""]
    return table, "\n".join(lines)


def main() -> int:
    argv = sys.argv[1:]
    passthrough = argv[argv.index("--") + 1:] if "--" in argv else []
    argv = argv[:argv.index("--")] if "--" in argv else argv
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidate", type=Path, required=True, help="Snapshot containing the skills under test.")
    parser.add_argument("--baseline", required=True, help="A snapshot to compare against, or `without` for no skills.")
    parser.add_argument("--runner", choices=sorted(RUNNERS), default="codex")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=3, help="Parallel runs.")
    parser.add_argument("--case", action="append", choices=sorted(REGRESSION), help="Default: the whole regression set.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New directory outside the skill checkout.")
    args = parser.parse_args(argv)
    args.candidate = args.candidate.resolve()
    args.output_dir = args.output_dir.resolve()
    repo = SCRIPTS.parent
    if args.output_dir.is_relative_to(repo):
        parser.error("Evidence must be outside the source checkout.")
    if leaked_words(args.output_dir, CASES):
        parser.error(f"Working copies go under the output directory, whose path the model sees; rename it without: {', '.join(leaked_words(args.output_dir, CASES))}.")
    if args.reps <= 0 or args.jobs <= 0 or not (args.candidate / "skills").is_dir():
        parser.error("Use positive --reps and --jobs and a candidate snapshot containing skills/.")
    if args.baseline != "without" and not (Path(args.baseline) / "skills").is_dir():
        parser.error("--baseline must be `without` or a snapshot containing skills/.")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    runner = [sys.executable, str(SCRIPTS / RUNNERS[args.runner])]
    planned = jobs(args.runner, args.case or list(REGRESSION), args.reps)
    codes: dict[tuple[str, int, str], int] = {}

    def one(job: tuple[str, int, str]) -> None:
        directory = run_dir(args.output_dir, args.runner, job)
        # Logs go to a directory named after the arm and case; the working copy stays under the neutral top level.
        command = [*runner, *arm_options(job[0], args.candidate, args.baseline), "--output-dir", str(directory),
                   "--workspace-root", str(args.output_dir), "--case", job[2], *passthrough]
        code = invoke(command, directory.with_suffix(".log"))
        codes[job] = code
        print(f"{directory.name}: exit {code}", flush=True)

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        list(pool.map(one, planned))
    table, text = summarize(args.output_dir, args.runner, planned, codes)
    (args.output_dir / "summary.md").write_text(text + "\n", encoding="utf-8")
    (args.output_dir / "summary.json").write_text(json.dumps(table, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Summary: {args.output_dir / 'summary.md'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
