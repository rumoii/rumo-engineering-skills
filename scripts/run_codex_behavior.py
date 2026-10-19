#!/usr/bin/env python3
"""Run isolated Codex skill-body cases; keep mechanical evidence separate from review verdicts."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import tarfile
import time
import tomllib
import uuid

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


def seed(root: Path, snapshot: Path, case: dict, with_skills: bool = True) -> None:
    root.mkdir(parents=True, exist_ok=False)
    if with_skills:
        shutil.copytree(snapshot / "skills", root / ".agents" / "skills")
    files = {**case["files"], **case.get("committed", {})}
    files[".gitignore"] = ".agents/\n__pycache__/\n*.pyc\n"
    files["AGENTS.md"] = (
        "# Local sample\nUse only this sample" + (" and its .agents/skills" if with_skills else "") + ". Do not access network tools, "
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
    for name, script in case.get("sqlite", {}).items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(root / name)
        try:
            db.executescript(script)
        finally:
            db.close()
    git(root, "init", "-q")
    git(root, *SAMPLE_AUTHOR, "add", ".")
    git(root, *SAMPLE_AUTHOR, "commit", "-qm", "Seed local sample")
    for name, content in case.get("dirty", {}).items():
        (root / name).write_text(content, encoding="utf-8")
    for link, target in case.get("links", {}).items():
        make_dir_link(root / link, root / target)


def make_dir_link(link: Path, target: Path) -> None:
    """A junction on Windows (no admin rights needed), a symlink elsewhere."""
    link.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, check=True)
    else:
        link.symlink_to(target, target_is_directory=True)


def seed_from_commit(root: Path, snapshot: Path, case: dict, with_skills: bool = True) -> None:
    """Seed from a local repository commit; files changed by dirty_commit become uncommitted edits."""
    root.mkdir(parents=True, exist_ok=False)
    tree = subprocess.run(["git", "-C", case["repo"], "archive", "--format=tar", case["commit"]], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tree)) as archive:
        archive.extractall(root, filter="data")
    if with_skills:
        shutil.copytree(snapshot / "skills", root / ".agents" / "skills")
    ignore = root / ".gitignore"
    ignore.write_text((ignore.read_text(encoding="utf-8") + "\n" if ignore.exists() else "") + ".agents/\n", encoding="utf-8")
    git(root, "init", "-q")
    git(root, *SAMPLE_AUTHOR, "add", ".")
    git(root, *SAMPLE_AUTHOR, "commit", "-qm", f"Seed {case['commit']}")
    if not case.get("dirty_commit"):
        return
    changes = git(Path(case["repo"]), "diff", "--no-renames", "--name-status", "-z", case["commit"], case["dirty_commit"]).split("\0")
    for status, name in zip(changes[::2], changes[1::2]):
        path = root / name
        if status == "D":
            path.unlink()
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(subprocess.run(["git", "-C", case["repo"], "show", f"{case['dirty_commit']}:{name}"], capture_output=True, check=True).stdout)


def load_manifest(path: Path, repo: Path) -> dict[str, dict]:
    """Replay cases for private repositories live outside this checkout, in a JSON list."""
    path = path.resolve()
    if path.is_relative_to(repo):
        raise ValueError("Keep replay manifests outside the skill checkout")
    cases = {}
    for item in json.loads(path.read_text(encoding="utf-8")):
        missing = {"name", "repo", "commit", "turns", "skills", "rubric"} - item.keys()
        if missing or item["name"] in CASES or item["name"] in cases:
            raise ValueError(f"Replay case {item.get('name')!r}: missing {sorted(missing)} or duplicate name")
        cases[item["name"]] = {"read_only": True, **item}
    return cases


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


PYTHON_EXE = r"(?:python(?:3(?:\.\d+)?)?|py)(?:\.exe)?"
# A bare, path-qualified, or quoted interpreter; no -c, so inline code cannot fake test output.
TEST_INVOCATION = re.compile(
    rf"""^\s*(?:&\s*)?(?:"(?:[^"]*/)?{PYTHON_EXE}"|'(?:[^']*/)?{PYTHON_EXE}'|(?:[^\s"']*/)?{PYTHON_EXE})"""
    r"(?:\s+-(?:3(?:\.\d+)?|b|u))*\s+(?:-m\s+(?:unittest|pytest)\b|(?:\./)?test_cart\.py\b)"
)


def completed_cart_test(commands: list[dict]) -> bool:
    """Require a completed test process and its known assertion, never a command mention alone."""
    for item in commands:
        command = item.get("command", "")
        script = re.split(r"\s-(?:Command|lc|c)\s+", command, maxsplit=1, flags=re.I)[-1].strip()
        if len(script) >= 2 and script[0] == script[-1] and script[0] in "\"'":
            script = script[1:-1]
        invoked = TEST_INVOCATION.match(normalized_path_text(script))
        output = item.get("aggregated_output", "")
        if (item.get("status") in {"completed", "failed"} and item.get("exit_code") == 1
                and "test_multiplies_price_by_quantity" in output and "AssertionError: 7 != 17" in output
                and "FAILED (failures=1)" in output and invoked):
            return True
    return False


def commit_checks(root: Path, base: str) -> dict:
    """Commit scope and message checks for commit-prepare; the push decision is left to review."""
    commits = git(root, "rev-list", f"{base}..HEAD").split()
    committed = set(git(root, "diff", "--name-only", base, "HEAD").split()) if commits else set()
    messages = [git(root, "log", "-1", "--format=%B", commit) for commit in commits]
    return {
        "committed_task": "cart.py" in committed,
        "only_task_committed": committed <= {"cart.py", "test_cart.py"},
        "unrelated_preserved": all((root / name).exists() for name in (".env.local", "notes.md", "debug.log")),
        "message_format": bool(messages) and all(
            re.match(r"[a-z]+(\([^)]+\))?: .*[一-鿿]", message) and "\n\n" in message for message in messages),
        "no_ai_signature": not any(re.search(r"co-authored-by|generated with", message, re.I) for message in messages),
        "no_remote_added": git(root, "remote") == "",
    }


def run_case(args: argparse.Namespace, name: str, overrides: list[dict], settings: dict) -> dict:
    case = CASES[name]
    out = args.output_dir / name
    out.mkdir(parents=True, exist_ok=False)
    root = blind_workspace(getattr(args, "workspace_root", None) or args.output_dir)
    with_skills = not getattr(args, "without_skills", False)
    seed(root, args.snapshot, case, with_skills)
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
            prompt = f"Read and apply these exact skill files and their applicable references before acting:\n{paths}\n\n{question}" if with_skills else question
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
    observed = evidence(all_events, root, case["skills"] if with_skills else [])
    after = file_state(root)
    changed = sorted(key for key in before.keys() | after.keys() if before.get(key) != after.get(key))
    protected_skills_unchanged = file_state(root / ".agents" / "skills") == skills_before
    valid = (len(runs) == len(case["turns"]) and all(r["exit_code"] == 0 and not r["timed_out"] and r["completed"] for r in runs)
             and all(observed["loaded_skill_paths"].values()) and not observed["errors"] and protected_skills_unchanged)
    checks = {"head_unchanged": git(root, "rev-parse", "HEAD") == head, "index_unchanged": git(root, "diff", "--cached", "--binary") == index, "skill_files_unchanged": protected_skills_unchanged}
    if not with_skills:
        # The baseline arm is valid only if no Rumo skill reached the model by any path.
        checks["no_rumo_skill_read"] = not any(
            re.search(r"rumo-[a-z-]+[/\\]skill\.md", normalized_path_text(item.get("command", "")))
            for item in observed["commands"]
        )
    case_checks(checks, name, case, root, changed, head, observed["commands"])
    result = {
        "case": name, "workspace": str(root), "snapshot": str(args.snapshot), "with_skills": with_skills, "settings": settings, "runs": runs,
        "evidence_status": "valid" if valid else "invalid", "mechanical_checks": checks,
        "changed_files": changed, "before": before, "after": after,
        "observed": observed, "review_verdict": "pending", "acceptance": case["rubric"],
    }
    write_json(out / "result.json", result)
    return result


def case_checks(checks: dict, name: str, case: dict, root: Path, changed: list[str], head: str, commands: list[dict]) -> None:
    """Per-case mechanical checks shared by every runner; commands use the Codex command-item shape."""
    if case["read_only"]:
        checks["sample_unchanged"] = not changed
    if name == "verify-honest":
        checks["completed_failing_test"] = completed_cart_test(commands)
    if name == "risk-proportionate":
        checks["only_login_copy_changed"] = changed == ["login.html"] and (root / "login.html").read_text(encoding="utf-8") == '<button type="submit">进入工作台</button>\n'
    if name == "auth-change-verify":
        checks["only_service_and_tests_changed"] = set(changed) <= {"orders/service.py", "tests/test_service.py"}
    if name == "debug-then-fix":
        checks["only_loader_changed"] = changed == ["loader.py"]
    if name == "timeout-cancel":
        checks["only_export_and_tests_changed"] = set(changed) <= {"export.py", "test_export.py"}
    if name == "duplicate-through-link":
        checks["original_preserved"] = (root / "profile/agents/skills/playwright-cli/SKILL.md").is_file()
        checks["links_preserved"] = all(
            os.path.realpath(root / link) == os.path.realpath(root / target) for link, target in case["links"].items())
    if name == "commit-prepare":
        # Committing is the task here, so a moved HEAD is expected.
        del checks["head_unchanged"], checks["index_unchanged"]
        checks.update(commit_checks(root, head))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True, help="Snapshot containing skills/.")
    parser.add_argument("--output-dir", type=Path, required=True, help="New task-owned directory outside the skill checkout.")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--case", action="append", choices=sorted(CASES))
    parser.add_argument("--timeout", type=int, default=600, help="Overall seconds per case, across its turns.")
    parser.add_argument("--without-skills", action="store_true", help="Baseline arm: no skills in the sample or the prompt.")
    parser.add_argument("--workspace-root", type=Path, help="Where working copies go; default --output-dir. The model sees this path.")
    args = parser.parse_args()
    args.snapshot = args.snapshot.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.timeout <= 0 or not (args.snapshot / "skills").is_dir():
        parser.error("Use a positive timeout and a snapshot containing skills/.")
    repo = Path(__file__).resolve().parents[1]
    if args.output_dir.is_relative_to(repo) or args.output_dir.is_relative_to(args.snapshot):
        parser.error("Evidence must be outside the source checkout and snapshot.")
    args.workspace_root = (args.workspace_root or args.output_dir).resolve()
    if leaked_words(args.workspace_root, CASES):
        parser.error(f"The model sees the workspace root's path; rename it without: {', '.join(leaked_words(args.workspace_root, CASES))}.")
    args.codex = shutil.which(args.codex) or args.codex
    overrides, settings = skill_overrides()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    snapshot_state = file_state(args.snapshot)
    write_json(args.output_dir / "run.json", {
        "snapshot": str(args.snapshot), "snapshot_files": snapshot_state,
        "codex_version": subprocess.check_output([args.codex, "--version"], text=True).strip(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases_sha256": hashlib.sha256(Path(__file__).with_name("codex_behavior_cases.py").read_bytes()).hexdigest(),
        "settings": settings, "cases": args.case or list(CASES), "timeout": args.timeout, "with_skills": not args.without_skills,
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
