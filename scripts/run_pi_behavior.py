#!/usr/bin/env python3
"""Run read-only Codex behavior cases through pi to screen skill effects on another model."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import time
import uuid

try:
    from .codex_behavior_cases import CASES
    from .run_codex_behavior import file_state, git, load_manifest, normalized_path_text, read_events, run_turn, seed, seed_from_commit, write_json
except ImportError:
    from codex_behavior_cases import CASES
    from run_codex_behavior import file_state, git, load_manifest, normalized_path_text, read_events, run_turn, seed, seed_from_commit, write_json


# pi has no sandbox, so cases get file reads and searches only: no shell, no edits.
READ_ONLY_TOOLS = "read,grep,find,ls"
DEFAULT_MODEL = "xiaomi-token-plan-cn/mimo-v2.6-pro"
PROJECT_INSTRUCTIONS = re.compile(r'<project_instructions path="([^"]+)">')
SKILL_PATH = re.compile(r"rumo-[a-z0-9-]+/skill\.md")
SKILL_FRONTMATTER = re.compile(r"^name: rumo-", re.M)


def pi_command(pi: str, model: str, session_dir: Path, session_id: str) -> list[str]:
    """Discovery of installed skills, extensions, and templates is off; the prompt names sample skills."""
    return [
        pi, "-p", "--mode", "json", "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-themes",
        "--tools", READ_ONLY_TOOLS, "--model", model, "--session-dir", str(session_dir), "--session-id", session_id,
    ]


def text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    return "".join(part.get("text", "") for part in content or [] if isinstance(part, dict) and part.get("type") == "text")


def call_target(call: dict) -> str:
    args = call.get("args") or {}
    return " ".join(str(args[key]) for key in ("path", "pattern", "glob") if key in args)


def reads_sample_skill(call: dict, root: Path, name: str) -> bool:
    """Accept a successful read of the sample's copy only, never a same-named copy elsewhere."""
    if call.get("toolName") != "read" or call.get("isError"):
        return False
    raw = str((call.get("args") or {}).get("path", ""))
    path = Path(raw) if Path(raw).is_absolute() else root / raw
    expected = root / ".agents" / "skills" / name / "SKILL.md"
    output = text_of((call.get("result") or {}).get("content"))
    return normalized_path_text(str(path.resolve())) == normalized_path_text(str(expected.resolve())) and f"name: {name}" in output


def tool_calls(events: list[dict]) -> list[dict]:
    """Completed calls; the end event omits args, so take them from the matching start event."""
    args = {e.get("toolCallId"): e.get("args") for e in events if e.get("type") == "tool_execution_start"}
    return [{**e, "args": e.get("args") or args.get(e.get("toolCallId"))} for e in events if e.get("type") == "tool_execution_end"]


def evidence(events: list[dict], root: Path, skills: list[str]) -> dict:
    calls = tool_calls(events)
    messages = [e["message"] for e in events if e.get("type") == "message_end" and isinstance(e.get("message"), dict)]
    replies = [m for m in messages if m.get("role") == "assistant"]
    system = next((m for m in messages if m.get("role") == "system"), {})
    usage: dict[str, int] = {}
    for reply in replies:
        for key, value in (reply.get("usage") or {}).items():
            if isinstance(value, int):
                usage[key] = usage.get(key, 0) + value
    return {
        "turn_completed": any(e.get("type") == "agent_settled" for e in events),
        "errors": [e for e in events if e.get("type") == "auto_retry_end" and not e.get("success")]
        + [m for m in replies if m.get("stopReason") in {"error", "aborted"}],
        "loaded_skill_paths": {name: any(reads_sample_skill(call, root, name) for call in calls) for name in skills},
        # Same shape as the Codex runner's command items, so one dump script reads both.
        "commands": [{
            "command": f"{call.get('toolName')} {json.dumps(call.get('args'), ensure_ascii=False)}",
            "exit_code": 1 if call.get("isError") else 0,
            "aggregated_output": text_of((call.get("result") or {}).get("content")),
        } for call in calls],
        "file_changes": [],
        "messages": [text for text in (text_of(m.get("content")) for m in replies) if text.strip()],
        "usage": usage,
        "context_files": PROJECT_INSTRUCTIONS.findall(str((system.get("sections") or {}).get("project_context", ""))),
    }


def read_any_rumo_skill(events: list[dict]) -> bool:
    for call in tool_calls(events):
        if SKILL_PATH.search(normalized_path_text(call_target(call))):
            return True
        if SKILL_FRONTMATTER.search(text_of((call.get("result") or {}).get("content"))):
            return True
    return False


def run_case(args: argparse.Namespace, name: str) -> dict:
    case = getattr(args, "cases", CASES)[name]
    if not case["read_only"]:
        raise ValueError(f"{name} edits files; pi runs read-only cases only")
    out = args.output_dir / name
    out.mkdir(parents=True, exist_ok=False)
    root = out / "sample"
    with_skills = not getattr(args, "without_skills", False)
    (seed_from_commit if "repo" in case else seed)(root, args.snapshot, case, with_skills)
    before = file_state(root)
    head = git(root, "rev-parse", "HEAD")
    index = git(root, "diff", "--cached", "--binary")
    skills_before = file_state(root / ".agents" / "skills")
    session_id = str(uuid.uuid4())
    command = pi_command(args.pi, args.model, out / "sessions", session_id)
    all_events: list[dict] = []
    runs = []
    started = time.monotonic()
    for turn, question in enumerate(case["turns"], 1):
        if turn == 1 and with_skills:
            paths = "\n".join(str(root / ".agents" / "skills" / skill / "SKILL.md") for skill in case["skills"])
            prompt = f"Read and apply these exact skill files and their applicable references before acting:\n{paths}\n\n{question}"
        else:
            prompt = question
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
        runs.append({"turn": turn, "exit_code": code, "timed_out": timed_out, "completed": current["turn_completed"], "parse_error": parse_error})
        if code != 0 or timed_out or not current["turn_completed"] or current["errors"]:
            break
    observed = evidence(all_events, root, case["skills"] if with_skills else [])
    after = file_state(root)
    changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    protected_skills_unchanged = file_state(root / ".agents" / "skills") == skills_before
    valid = (len(runs) == len(case["turns"]) and all(r["exit_code"] == 0 and not r["timed_out"] and r["completed"] for r in runs)
             and all(observed["loaded_skill_paths"].values()) and not observed["errors"] and protected_skills_unchanged)
    checks = {
        "head_unchanged": git(root, "rev-parse", "HEAD") == head,
        "index_unchanged": git(root, "diff", "--cached", "--binary") == index,
        "skill_files_unchanged": protected_skills_unchanged,
        "sample_unchanged": not changed,
    }
    if not with_skills:
        # The baseline arm is valid only if no Rumo skill reached the model by any path.
        checks["no_rumo_skill_read"] = not read_any_rumo_skill(all_events)
    result = {
        "case": name, "snapshot": str(args.snapshot), "with_skills": with_skills, "model": args.model,
        "session_id": session_id, "runs": runs, "evidence_status": "valid" if valid else "invalid",
        "mechanical_checks": checks, "changed_files": changed, "before": before, "after": after,
        "observed": observed, "review_verdict": "pending", "acceptance": case["rubric"],
    }
    write_json(out / "result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Snapshot containing skills/.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New task-owned directory outside the skill checkout.")
    parser.add_argument("--pi", default="pi")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="pi model as provider/id.")
    parser.add_argument("--case", action="append", help="Read-only cases only; default: every manifest case, else every built-in one.")
    parser.add_argument("--manifest", type=Path, help="JSON list of replay cases from local repositories, kept outside this checkout.")
    parser.add_argument("--timeout", type=int, default=600, help="Overall seconds per case, across its turns.")
    parser.add_argument("--without-skills", action="store_true", help="Baseline arm: no skills in the sample or the prompt.")
    args = parser.parse_args()
    args.snapshot = args.snapshot.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.timeout <= 0 or not (args.snapshot / "skills").is_dir():
        parser.error("Use a positive timeout and a snapshot containing skills/.")
    repo = Path(__file__).resolve().parents[1]
    if args.output_dir.is_relative_to(repo) or args.output_dir.is_relative_to(args.snapshot):
        parser.error("Evidence must be outside the source checkout and snapshot.")
    try:
        replays = load_manifest(args.manifest, repo) if args.manifest else {}
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    args.cases = {**CASES, **replays}
    selected = args.case or sorted(replays) or sorted(name for name, case in CASES.items() if case["read_only"])
    unknown = [name for name in selected if name not in args.cases or not args.cases[name]["read_only"]]
    if unknown:
        parser.error(f"Not a read-only case: {', '.join(unknown)}")
    args.pi = shutil.which(args.pi) or args.pi
    args.output_dir.mkdir(parents=True, exist_ok=False)
    snapshot_state = file_state(args.snapshot)
    write_json(args.output_dir / "run.json", {
        "snapshot": str(args.snapshot), "snapshot_files": snapshot_state,
        "pi_version": subprocess.check_output([args.pi, "--version"], text=True).strip(), "model": args.model,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(Path(__file__).with_name("codex_behavior_cases.py").read_bytes()).hexdigest(),
        "manifest": str(args.manifest.resolve()) if args.manifest else None,
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest() if args.manifest else None,
        "cases": selected, "timeout": args.timeout, "with_skills": not args.without_skills,
    })
    results = []
    for name in selected:
        print(f"Running {name}", flush=True)
        result = run_case(args, name)
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
