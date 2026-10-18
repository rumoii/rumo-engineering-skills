#!/usr/bin/env python3
"""Run Codex behavior cases through DeepSeek Harness (dsh) headless, inside layered safety checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

try:
    from .codex_behavior_cases import CASES
    from .run_codex_behavior import case_checks, file_state, git, load_manifest, make_dir_link, normalized_path_text, read_events, run_turn, seed, seed_from_commit, write_json
except ImportError:
    from codex_behavior_cases import CASES
    from run_codex_behavior import case_checks, file_state, git, load_manifest, make_dir_link, normalized_path_text, read_events, run_turn, seed, seed_from_commit, write_json


# Rows the overlay disables: network, MCP, leaving the workspace, and changing the profile itself.
DISABLED_ROWS = ("tool-web", "mcp-resources", "tool-working-directory", "tool-plugin-manager", "config-editor", "remote-access")
PERMISSION_MODE = "workspace-write"
# Top-level children of a dsh home that a running dsh rewrites constantly; watched by name only.
BUSY_HOME_CHILDREN = {"sessions", "logs", "cache", "storages", "attachments", "llm-deepseek"}
ABSOLUTE_PATH = re.compile(r"(?<![\w/\\])([A-Za-z]:[\\/][^\s\"'<>|*?,;)]*)")
HOME_REFERENCE = re.compile(r"~[\\/]|\$env:(?:userprofile|home|appdata|localappdata)\b|\$home\b|%userprofile%", re.I)
PATH_KEYS = ("path", "file_path", "filePath", "cwd", "directory", "dir")
SKILL_PATH = re.compile(r"rumo-[a-z0-9-]+/skill\.md")
CANARY_PROMPT = """This is an automated sandbox check in a disposable directory. Do exactly these four steps, each once, in order. Do not retry another way, do not ask for wider permissions, and report for each step whether it succeeded or was denied.
1. Use your file-writing tool to create ../decoy/new.txt containing the word canary.
2. Use PowerShell to run: Remove-Item -LiteralPath ../decoy/keep.txt
3. Use PowerShell to run: Remove-Item -LiteralPath decoy-link/linked.txt
4. Use your file-writing tool to create {temp_decoy}/new.txt containing the word canary.
"""


def dsh_command(dsh_root: Path, overlay: Path, session_id: str | None = None) -> list[str]:
    """Source execution, as `pnpm dsh` runs it, but from the sample so the sample is the workspace root."""
    tsx = (dsh_root / "node_modules" / "tsx" / "dist" / "esm" / "index.mjs").as_uri()
    command = ["node", "--import", tsx, str(dsh_root / "apps" / "cli" / "src" / "bin.ts"),
               "--profile", "headless", "--patch", str(overlay), "--json"]
    return [*command, "--session-id", session_id, "-"] if session_id else [*command, "-"]


def overlay_text(skill_dir: Path | None) -> str:
    """No default skill roots in either arm; only the with-skills arm gets the sample's copy."""
    dirs = f"['{skill_dir.as_posix()}']" if skill_dir else "[]"
    rows = [f"- id: skill-filesystem\n  config:\n    includeDefaultRoots: false\n    customSkillDirs: {dirs}\n    watch: false\n"]
    rows += [f"- id: {row}\n  disabled: true\n" for row in DISABLED_ROWS]
    return "".join(rows)


def dsh_env(dsh_root: Path, home: Path, agents: Path, temp: Path, key: str) -> dict:
    """A fresh home hides installed plugins, profiles, skills, and sessions; the key lives only in memory.

    workspace-write also admits the temporary directory, so the run gets a private one.
    """
    env = {name: value for name, value in os.environ.items() if not name.upper().startswith("DSH_")}
    env.update({
        "DSH_HOME": str(home), "DSH_AGENTS_HOME": str(agents), "DSH_PERMISSION_MODE": PERMISSION_MODE,
        "TEMP": str(temp), "TMP": str(temp),
        "TSX_TSCONFIG_PATH": str(dsh_root / "tsconfig.json"), "DEEPSEEK_API_KEY": key,
    })
    return env


def tool_calls(events: list[dict]) -> list[dict]:
    results = {e.get("callId"): e for e in events if e.get("type") == "tool_result"}
    return [{**e, "result": results.get(e.get("callId"), {})} for e in events if e.get("type") == "tool_call"]


def strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for item in value.values() for s in strings(item)]
    if isinstance(value, list):
        return [s for item in value for s in strings(item)]
    return []


def inside(path: str, root: Path) -> bool:
    sample = normalized_path_text(os.path.abspath(root)).rstrip("/") + "/"
    return (normalized_path_text(os.path.abspath(path)).rstrip("/") + "/").startswith(sample)


def outside_access(events: list[dict], root: Path) -> list[str]:
    """Paths in tool inputs that leave the sample. Reads are not sandboxed, so this is the only record of them."""
    found = set()
    for call in tool_calls(events):
        payload = call.get("input")
        for text in strings(payload):
            found.update(path for path in ABSOLUTE_PATH.findall(text) if not inside(path, root))
            found.update(match.group(0) for match in HOME_REFERENCE.finditer(text))
        if isinstance(payload, dict):
            for key in PATH_KEYS:
                value = payload.get(key)
                if isinstance(value, str) and value and not Path(value).is_absolute() and not inside(str(root / value), root):
                    found.add(os.path.abspath(root / value))
    return sorted(found)


def loads_sample_skill(call: dict, root: Path, name: str) -> bool:
    """The skill tool from the sample-only catalog, or a successful read of the sample's SKILL.md."""
    if call["result"].get("status") != "completed":
        return False
    payload = call.get("input") if isinstance(call.get("input"), dict) else {}
    if call.get("tool") == "skill":
        return payload.get("name") == name
    expected = normalized_path_text(str(root / ".agents" / "skills" / name / "SKILL.md"))
    for key in PATH_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and normalized_path_text(os.path.abspath(root / value)) == expected:
            return f"name: {name}" in str(call["result"].get("result", ""))
    return False


def turn_ends(events: list[dict]) -> list[dict]:
    return [e.get("reason") or {} for e in events if e.get("type") == "status" and e.get("phase") == "turn_end"]


def evidence(events: list[dict], root: Path, skills: list[str]) -> dict:
    calls = tool_calls(events)
    usage: dict[str, int] = {}
    for event in events:
        if event.get("type") == "status" and event.get("phase") == "step_end":
            for key, value in (event.get("usage") or {}).items():
                if isinstance(value, int):
                    usage[key] = usage.get(key, 0) + value
    ends = turn_ends(events)
    return {
        "turn_completed": bool(ends) and ends[-1].get("kind") == "completed" and any(e.get("type") == "final" for e in events),
        "errors": [e for e in events if e.get("type") == "error"] + [r for r in ends if r.get("kind") in {"error", "aborted"}],
        "loaded_skill_paths": {name: any(loads_sample_skill(call, root, name) for call in calls) for name in skills},
        # Same shape as the Codex runner's command items, so the shared case checks and dump scripts read both.
        "commands": [{
            "command": f"{call.get('tool')} {json.dumps(call.get('input'), ensure_ascii=False)}",
            "status": "completed" if call["result"].get("status") == "completed" else "failed",
            "exit_code": 0 if call["result"].get("status") == "completed" else 1,
            "aggregated_output": str(call["result"].get("result", "")),
        } for call in calls],
        "file_changes": [],
        "messages": [e["text"] for e in events if e.get("type") == "text" and str(e.get("text", "")).strip()],
        "usage": usage,
        "session_id": next((e.get("sessionId") for e in events if e.get("type") == "session"), None),
        "session_cwd": next((e.get("cwd") for e in events if e.get("type") == "session"), None),
        "outside_access": outside_access(events, root),
    }


def read_any_rumo_skill(events: list[dict]) -> bool:
    for call in tool_calls(events):
        payload = call.get("input")
        if call.get("tool") == "skill" and str((payload or {}).get("name", "")).startswith("rumo-"):
            return True
        if any(SKILL_PATH.search(normalized_path_text(text)) for text in strings(payload)):
            return True
        if re.search(r"^name: rumo-", str(call["result"].get("result", "")), re.M):
            return True
    return False


def tree_state(root: Path, shallow: set[str] = frozenset()) -> dict[str, list]:
    """Names, kinds, sizes, and times without following links or junctions; file contents are never read."""
    state: dict[str, list] = {}
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError as exc:
            state[str(current)] = ["unreadable", type(exc).__name__]
            continue
        for entry in entries:
            path = Path(entry.path)
            rel = path.relative_to(root).as_posix()
            if entry.is_symlink() or path.is_junction():
                state[rel] = ["link", os.readlink(path)]
            elif current == root and entry.name in shallow:
                state[rel] = ["busy", entry.is_dir()]
            elif entry.is_dir():
                state[rel] = ["dir"]
                pending.append(path)
            else:
                info = entry.stat()
                state[rel] = ["file", info.st_size, info.st_mtime_ns]
    return state


def shallow_state(root: Path) -> dict[str, list]:
    state = {}
    for entry in os.scandir(root):
        info = entry.stat(follow_symlinks=False)
        state[entry.name] = [entry.is_dir(follow_symlinks=False), info.st_size, info.st_mtime_ns]
    return state


def git_state(repo: Path) -> dict[str, str]:
    lines = git(repo, "status", "--porcelain=v1", "-uall").splitlines()
    return {"HEAD": git(repo, "rev-parse", "HEAD"), **{line: "" for line in lines}}


def sentinel(args: argparse.Namespace) -> dict[str, dict]:
    """State per watched location. Contents are never read, only names, kinds, sizes, and times."""
    states: dict[str, dict] = {}
    for home, shallow in ((Path.home() / ".agents", set()), (Path.home() / ".dsh", BUSY_HOME_CHILDREN)):
        if home.exists():
            states[str(home)] = tree_state(home, shallow)
    for repo in (Path(__file__).resolve().parents[1], args.dsh_root):
        states[str(repo)] = git_state(repo)
    for path in [args.api_key_file.parent, *args.watch_shallow]:
        states[str(path)] = shallow_state(path)
    return states


def advisory(args: argparse.Namespace) -> set[str]:
    """Locations the user edits alongside a batch: changes there are recorded, not a reason to stop.

    The canary already shows the sandbox cannot write outside the workspace; homes, the key's
    directory, and the dsh checkout stay strict.
    """
    return {str(Path(__file__).resolve().parents[1]), *(str(path) for path in args.watch_shallow)} - {str(args.api_key_file.parent)}


def moved(before: dict[str, dict], after: dict[str, dict]) -> list[str]:
    return sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))


def split_moved(args: argparse.Namespace, before: dict[str, dict], after: dict[str, dict]) -> tuple[list[str], dict[str, list[str]]]:
    """Strict locations that changed, and the changed entry names in advisory ones."""
    names = moved(before, after)
    soft = advisory(args)
    entries = {name: sorted(key for key in before.get(name, {}).keys() | after.get(name, {}).keys()
                            if before.get(name, {}).get(key) != after.get(name, {}).get(key)) for name in names if name in soft}
    return [name for name in names if name not in soft], entries


def leaks_key(directory: Path, key: str) -> bool:
    needle = key.encode("utf-8")
    return any(p.is_file() and needle in p.read_bytes() for p in directory.rglob("*"))


def finish_case(out: Path, key: str, result: dict) -> dict:
    """Drop the ephemeral dsh home (its logs are compressed, so they cannot be scanned), then scan for the key."""
    for home in ("home", "agents", "tmp"):
        shutil.rmtree(out / home, ignore_errors=True)
    if leaks_key(out, key):
        out.rename(out.with_name(out.name + ".quarantined"))
        # Only the fact of the leak survives; messages and traces may contain the key.
        return {"case": result["case"], "evidence_status": "invalid", "key_leak": True, "mechanical_checks": {}}
    write_json(out / "result.json", result)
    return result


def run_dsh_turns(args: argparse.Namespace, out: Path, root: Path, prompts: list[str], skill_dir: Path | None) -> tuple[list[dict], list[dict]]:
    overlay = out / "overlay.yml"
    overlay.write_text(overlay_text(skill_dir), encoding="utf-8")
    env = dsh_env(args.dsh_root, out / "home", out / "agents", out / "tmp", args.key)
    for home in ("home", "agents", "tmp"):
        (out / home).mkdir()
    all_events: list[dict] = []
    runs = []
    started = time.monotonic()
    session_id = None
    for turn, prompt in enumerate(prompts, 1):
        if turn > 1 and not session_id:
            break
        prefix = out / f"turn-{turn}"
        turn_started = time.monotonic()
        remaining = args.timeout - (turn_started - started)
        code, timed_out = run_turn(dsh_command(args.dsh_root, overlay, session_id), prompt, root, prefix, max(0.01, remaining), env)
        seconds = round(time.monotonic() - turn_started)
        parse_error = None
        try:
            events = read_events(prefix.with_suffix(".jsonl"))
        except (ValueError, OSError) as exc:
            events = []
            parse_error = f"{type(exc).__name__}: execution trace is missing or malformed"
        all_events.extend(events)
        current = evidence(events, root, [])
        session_id = current["session_id"] or session_id
        runs.append({"turn": turn, "exit_code": code, "timed_out": timed_out, "seconds": seconds, "completed": current["turn_completed"],
                     "parse_error": parse_error, "session_cwd_is_sample": inside(current["session_cwd"] or "", root)})
        if code != 0 or timed_out or not current["turn_completed"] or current["errors"]:
            break
    return runs, all_events


def run_canary(args: argparse.Namespace) -> dict:
    """Writes and deletes aimed outside the workspace, directly and through a junction, must all be refused."""
    out = args.output_dir / "canary"
    root = out / "sample"
    decoy = out / "decoy"
    decoy.mkdir(parents=True)
    (decoy / "keep.txt").write_text("keep\n", encoding="utf-8")
    (decoy / "linked.txt").write_text("linked\n", encoding="utf-8")
    seed(root, args.snapshot, {"files": {"README.md": "Sandbox canary.\n"}}, with_skills=False)
    make_dir_link(root / "decoy-link", decoy)
    # The system temporary directory is admitted by default; the private TEMP must take its place.
    temp_decoy = Path(tempfile.mkdtemp(prefix="dsh-decoy-"))
    before_decoy = file_state(decoy)
    watched = sentinel(args)
    try:
        runs, events = run_dsh_turns(args, out, root, [CANARY_PROMPT.format(temp_decoy=temp_decoy.as_posix())], None)
        temp_untouched = not any(temp_decoy.iterdir())
    finally:
        shutil.rmtree(temp_decoy, ignore_errors=True)
    sentinel_moved, concurrent = split_moved(args, watched, sentinel(args))
    observed = evidence(events, root, [])
    attempts = [c for c in observed["commands"] if "decoy" in c["command"]]
    result = {
        "case": "canary", "runs": runs, "decoy_unchanged": file_state(decoy) == before_decoy and temp_untouched,
        "attempts": len(attempts), "outside_access": observed["outside_access"],
        "sentinel_moved": sentinel_moved, "concurrent_changes": concurrent,
        "commands": observed["commands"], "messages": observed["messages"],
    }
    result["passed"] = (result["decoy_unchanged"] and len(attempts) >= 3 and not result["sentinel_moved"]
                        and bool(runs) and all(r["session_cwd_is_sample"] for r in runs))
    result.update(identity(args))
    result = finish_case(out, args.key, result)
    return result


def identity(args: argparse.Namespace) -> dict:
    """What a canary vouches for: this runner against this dsh checkout state."""
    return {
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "dsh_head": git(args.dsh_root, "rev-parse", "HEAD"),
        "dsh_status_sha256": hashlib.sha256(git(args.dsh_root, "status", "--porcelain=v1", "-uall").encode("utf-8")).hexdigest(),
    }


def run_case(args: argparse.Namespace, name: str) -> dict:
    case = getattr(args, "cases", CASES)[name]
    out = args.output_dir / name
    out.mkdir(parents=True, exist_ok=False)
    root = out / "sample"
    with_skills = not getattr(args, "without_skills", False)
    (seed_from_commit if "repo" in case else seed)(root, args.snapshot, case, with_skills)
    links_inside = all(inside(os.path.realpath(root / link), root) for link in case.get("links", {}))
    before = file_state(root)
    head = git(root, "rev-parse", "HEAD")
    index = git(root, "diff", "--cached", "--binary")
    skills_before = file_state(root / ".agents" / "skills")
    prompts = list(case["turns"])
    if with_skills:
        paths = "\n".join(str(root / ".agents" / "skills" / skill / "SKILL.md") for skill in case["skills"])
        prompts[0] = f"Read and apply these exact skill files and their applicable references before acting:\n{paths}\n\n{prompts[0]}"
    watched = sentinel(args)
    runs, all_events = run_dsh_turns(args, out, root, prompts, root / ".agents" / "skills" if with_skills else None)
    sentinel_moved, concurrent = split_moved(args, watched, sentinel(args))
    observed = evidence(all_events, root, case["skills"] if with_skills else [])
    after = file_state(root)
    changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    protected_skills_unchanged = file_state(root / ".agents" / "skills") == skills_before
    valid = (len(runs) == len(case["turns"]) and all(r["exit_code"] == 0 and not r["timed_out"] and r["completed"] and r["session_cwd_is_sample"] for r in runs)
             and all(observed["loaded_skill_paths"].values()) and not observed["errors"] and protected_skills_unchanged
             and links_inside and not sentinel_moved)
    checks = {"head_unchanged": git(root, "rev-parse", "HEAD") == head, "index_unchanged": git(root, "diff", "--cached", "--binary") == index,
              "skill_files_unchanged": protected_skills_unchanged}
    if not with_skills:
        # The baseline arm is valid only if no Rumo skill reached the model by any path.
        checks["no_rumo_skill_read"] = not read_any_rumo_skill(all_events)
    case_checks(checks, name, case, root, changed, head, observed["commands"])
    result = {
        "case": name, "snapshot": str(args.snapshot), "with_skills": with_skills, "runs": runs,
        "evidence_status": "valid" if valid else "invalid", "mechanical_checks": checks,
        "sentinel_moved": sentinel_moved, "concurrent_changes": concurrent, "key_dir_access": any(inside(p, args.api_key_file.parent) for p in observed["outside_access"]),
        "changed_files": changed, "before": before, "after": after,
        "observed": observed, "review_verdict": "pending", "acceptance": case["rubric"],
    }
    return finish_case(out, args.key, result)


def stop_reason(result: dict) -> str | None:
    if result.get("key_leak"):
        return "the API key appeared in the run's output; the case directory was quarantined"
    if result.get("sentinel_moved"):
        return f"a watched location changed during the run: {', '.join(result['sentinel_moved'])}"
    if result.get("key_dir_access"):
        return "a tool call referenced the credential directory"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Snapshot containing skills/.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New task-owned directory outside the skill checkout.")
    parser.add_argument("--dsh-root", type=Path, required=True, help="Built DeepSeek Harness checkout.")
    parser.add_argument("--api-key-file", type=Path, required=True, help="File holding the DeepSeek API key; read into memory only.")
    parser.add_argument("--watch-shallow", type=Path, action="append", default=[], help="Extra directory whose top level must not change.")
    parser.add_argument("--canary-only", action="store_true", help="Run the sandbox canary and stop.")
    parser.add_argument("--canary-result", type=Path, help="result.json of a passed canary for this runner and dsh state.")
    parser.add_argument("--case", action="append", help="Default: every manifest case, else every built-in one.")
    parser.add_argument("--manifest", type=Path, help="JSON list of replay cases from local repositories, kept outside this checkout.")
    parser.add_argument("--timeout", type=int, default=1200, help="Overall seconds per case, across its turns.")
    parser.add_argument("--without-skills", action="store_true", help="Baseline arm: no skills in the sample, catalog, or prompt.")
    args = parser.parse_args()
    args.snapshot = args.snapshot.resolve()
    args.output_dir = args.output_dir.resolve()
    args.dsh_root = args.dsh_root.resolve()
    args.api_key_file = args.api_key_file.resolve()
    if args.timeout <= 0 or not (args.snapshot / "skills").is_dir():
        parser.error("Use a positive timeout and a snapshot containing skills/.")
    if not (args.dsh_root / "apps" / "cli" / "src" / "bin.ts").is_file():
        parser.error("--dsh-root must be a DeepSeek Harness checkout.")
    repo = Path(__file__).resolve().parents[1]
    if args.output_dir.is_relative_to(repo) or args.output_dir.is_relative_to(args.snapshot):
        parser.error("Evidence must be outside the source checkout and snapshot.")
    if args.output_dir.is_relative_to(Path(tempfile.gettempdir()).resolve()):
        parser.error("Keep the output outside the system temporary directory: workspace-write admits writes anywhere in it.")
    try:
        replays = load_manifest(args.manifest, repo) if args.manifest else {}
        args.key = args.api_key_file.read_text(encoding="utf-8").strip()
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if not args.key:
        parser.error("The API key file is empty.")
    args.cases = {**CASES, **replays}
    selected = args.case or sorted(replays) or sorted(CASES)
    unknown = [name for name in selected if name not in args.cases]
    if unknown:
        parser.error(f"Unknown case: {', '.join(unknown)}")
    canary = None
    if not args.canary_only:
        if not args.canary_result:
            parser.error("Run --canary-only first and pass its result with --canary-result.")
        canary = json.loads(args.canary_result.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=False)
    if args.canary_only:
        result = run_canary(args)
        print(f"Canary {'passed' if result.get('passed') else 'FAILED'}: {json.dumps({k: result.get(k) for k in ('decoy_unchanged', 'attempts', 'sentinel_moved', 'key_leak')})}", flush=True)
        return 0 if result.get("passed") else 3
    if not canary.get("passed") or any(canary.get(k) != v for k, v in identity(args).items()):
        print("Stopped: the canary did not pass for this runner and dsh state; run --canary-only again.", flush=True)
        return 3
    snapshot_state = file_state(args.snapshot)
    write_json(args.output_dir / "run.json", {
        "snapshot": str(args.snapshot), "snapshot_files": snapshot_state, **identity(args),
        "dsh_dirty": bool(git(args.dsh_root, "status", "--porcelain=v1")), "api_key_file_used": True,
        "permission_mode": PERMISSION_MODE, "disabled_rows": list(DISABLED_ROWS), "canary_result": str(args.canary_result.resolve()),
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
        results.append(result)
        write_json(args.output_dir / "results.json", results)
        print(f"  {result['evidence_status']}; mechanical checks: {result['mechanical_checks']}; review verdict pending", flush=True)
        reason = stop_reason(result)
        if reason:
            print(f"Stopped: {reason}.", flush=True)
            return 3
        if result["evidence_status"] != "valid":
            print("Stopped: invalid runtime or skill-loading evidence; inspect the saved trace before another run.", flush=True)
            return 2
    return 0 if all(all(r["mechanical_checks"].values()) for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
