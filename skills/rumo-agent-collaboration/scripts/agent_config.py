#!/usr/bin/env python3
"""Read, check, and change the user's agent lanes: which CLI, model, and effort each role uses.

The configuration lives in $RUMO_AGENTS_CONFIG, else
~/.rumo-engineering-skills/agents.json. Only scripts read it, so it costs no
context until a skill asks for a role's lanes. Roles:

  review    extra reviewers in a multi-model review; the current agent also reviews
  delegate  the lanes used when the user hands work off without naming a CLI

A file that still has the retired design role loads without it, and the next
write drops it.

A lane is written cli[:model][@effort], for example codex:gpt-6.1-sol@high or
claude@max; a lane with no model or effort uses the CLI's own default. A
delegate lane may start with a use label, such as tests=pi:deepseek/v4@high;
several delegate lanes need distinct labels, and work that matches none goes
to the first.
auto_panel says what the agent may do when it judges, on its own, that a
multi-model review is worth it: ask (default), allow, or off.

Subcommands: show, lanes, models (what a CLI offers), check (with --probe,
one tiny read-only turn per lane), set-role, set-auto-panel. Exit codes: 0 ok;
2 refused (invalid lane, unusable adapter, failed check or probe); 3 not
configured (run rumo-setup).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


CONFIG_ENV = "RUMO_AGENTS_CONFIG"
ROLES = ("review", "delegate")
RETIRED_ROLES = ("design",)
USE_ROLES = ("delegate",)
AUTO_PANEL = ("ask", "allow", "off")
# Raising VERSION when the file's shape changes requires adding, in load(), an in-memory
# upgrade of older files; the next write saves the new shape. A newer file is refused, never rewritten.
VERSION = 1
NOT_CONFIGURED = 3
RUNNER = Path(__file__).resolve().parent / "agent_run.py"
LANE_KEYS = {"use", "cli", "model", "effort", "executable"}

_spec = importlib.util.spec_from_file_location("agent_run", RUNNER)
assert _spec and _spec.loader
agent_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agent_run)
Refused = agent_run.Refused


class NotConfigured(Exception):
    """No configuration, or no lane for the requested role."""


def config_path() -> Path:
    value = os.environ.get(CONFIG_ENV)
    return Path(value).expanduser() if value else Path.home() / ".rumo-engineering-skills" / "agents.json"


def parse_lane(text: str) -> dict:
    """[use=]cli[:model][@effort] -> lane; the model may contain '/' or ':' but not '@'."""
    use, sep, rest = text.strip().partition("=")
    if not sep:
        use, rest = "", use
    match = re.fullmatch(r"([a-z0-9][a-z0-9-]*)(?::([^@\s]+))?(?:@([a-z0-9][a-z0-9-]*))?", rest.strip())
    if not match or (sep and not use.strip()):
        raise Refused(f"lane {text!r} must look like [use=]cli[:model][@effort], for example tests=codex:gpt-6.1-sol@high")
    cli, model, effort = match.groups()
    return {**({"use": use.strip()} if use.strip() else {}), "cli": cli,
            **({"model": model} if model else {}), **({"effort": effort} if effort else {})}


def with_executables(lanes: list[dict], pairs: list[str] | None) -> list[dict]:
    """Attach --executable cli=path values to every lane of that CLI."""
    paths = {}
    for pair in pairs or []:
        cli, sep, path = pair.partition("=")
        if not sep or not cli or not path:
            raise Refused(f"--executable {pair!r} must look like cli=path")
        paths[cli] = path
    unused = set(paths) - {lane["cli"] for lane in lanes}
    if unused:
        raise Refused(f"--executable names a CLI with no lane: {', '.join(sorted(unused))}")
    return [{**lane, "executable": paths[lane["cli"]]} if lane["cli"] in paths else lane for lane in lanes]


def lane_label(lane: dict) -> str:
    return (f"{lane['use']}=" if lane.get("use") else "") + lane["cli"] + (f":{lane['model']}" if lane.get("model") else "") + (f"@{lane['effort']}" if lane.get("effort") else "")


def lane_problems(lane: object, runs_dir: str | None = None) -> list[str]:
    """Static problems: unknown keys, missing or disabled adapter, effort the adapter does not offer."""
    if not isinstance(lane, dict) or not isinstance(lane.get("cli"), str):
        return ["each lane must be an object with a cli"]
    problems = [f"unknown lane key {key!r}" for key in sorted(set(lane) - LANE_KEYS)]
    for key in ("use", "model", "effort", "executable"):
        if key in lane and (not isinstance(lane[key], str) or not lane[key].strip()):
            problems.append(f"{key} must be a nonempty string")
    entry = agent_run.load_adapters(runs_dir).get(lane["cli"])
    if entry is None:
        return problems + [f"no adapter named {lane['cli']!r}"]
    if entry["problems"]:
        return problems + [f"adapter {lane['cli']!r} is unusable: {'; '.join(entry['problems'])}"]
    if reason := agent_run.disabled_reason(entry["adapter"]):
        return problems + [f"adapter {lane['cli']!r} is disabled: {reason}"]
    try:
        agent_run.render(entry["adapter"], "start", "read-only", "/w", lane.get("model"), "sid", "/p.md",
                         effort=lane.get("effort"))
    except Refused as exc:
        problems.append(str(exc))
    return problems


def validate(config: object, runs_dir: str | None = None, roles_to_check: tuple[str, ...] | None = None) -> list[str]:
    """Check the file's shape, and the lanes of roles_to_check (every role when None)."""
    if not isinstance(config, dict):
        return ["configuration must be a JSON object"]
    problems = [f"unknown key {key!r}" for key in sorted(set(config) - {"version", "auto_panel", "roles"})]
    version = config.get("version")
    if type(version) is int and version > VERSION:
        problems.append(f"version {version} was written by a newer rumo-engineering-skills; update the skills before changing it")
    elif version != VERSION:
        problems.append(f"version must be {VERSION}")
    if config.get("auto_panel", "ask") not in AUTO_PANEL:
        problems.append(f"auto_panel must be one of {', '.join(AUTO_PANEL)}")
    roles = config.get("roles", {})
    if not isinstance(roles, dict):
        return problems + ["roles must be an object"]
    for role, lanes in roles.items():
        if role not in ROLES:
            problems.append(f"unknown role {role!r}; roles are {', '.join(ROLES)}")
            continue
        if not isinstance(lanes, list):
            problems.append(f"{role} must be a list of lanes")
            continue
        if roles_to_check is not None and role not in roles_to_check:
            continue
        uses = [lane.get("use") for lane in lanes if isinstance(lane, dict) and isinstance(lane.get("use"), (str, type(None)))]
        if role not in USE_ROLES and any(uses):
            problems.append(f"{role} lanes take no use label; only {', '.join(USE_ROLES)} lanes do")
        if role in USE_ROLES and len(lanes) > 1 and (not all(uses) or len(set(uses)) != len(uses)):
            problems.append(f"several {role} lanes each need a distinct use label")
        problems += [f"{role}: {p}" for lane in lanes for p in lane_problems(lane, runs_dir)]
    return problems


def load(runs_dir: str | None = None, roles_to_check: tuple[str, ...] | None = None) -> dict:
    path = config_path()
    if not path.is_file():
        raise NotConfigured(f"agents are not configured ({path} does not exist); run the rumo-setup skill")
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Refused(f"cannot read {path}: {exc}") from exc
    if isinstance(config, dict) and isinstance(config.get("roles"), dict):
        for role in RETIRED_ROLES:
            config["roles"].pop(role, None)
    if problems := validate(config, runs_dir, roles_to_check):
        raise Refused(f"{path} is invalid: " + "; ".join(problems))
    return config


def write(config: dict, runs_dir: str | None = None, roles_to_check: tuple[str, ...] | None = None) -> Path:
    """Validate, then replace the file atomically; unrelated keys keep their order and values.

    A set command checks only the role it changes, so a lane that went stale in
    another role (an adapter dropped an effort, say) never blocks the repair.
    """
    if problems := validate(config, runs_dir, roles_to_check):
        raise Refused("refusing to write an invalid configuration: " + "; ".join(problems))
    target = config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            json.dump(config, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return target


def load_or_new(runs_dir: str | None) -> dict:
    try:
        return load(runs_dir, roles_to_check=())
    except NotConfigured:
        return {"version": VERSION, "auto_panel": "ask", "roles": {}}


def dotted(value: object, path: str) -> object:
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    return value


def list_models(adapter: dict, exe: list[str] | None) -> dict:
    """Models the CLI offers, read from its listing command or the adapter's fixed aliases."""
    spec = adapter.get("models")
    if not spec:
        return {"source": None, "models": [], "note": "this CLI cannot list its models; enter a model ID or keep the CLI default"}
    note = {"note": spec["note"]} if spec.get("note") else {}
    if "static" in spec:
        return {"source": "adapter", "models": [{"id": m} for m in spec["static"]], **note}
    if exe is None:
        raise Refused(f"{adapter['executable']} is not installed or not on PATH")
    out = subprocess.run([*exe, *spec["args"]], capture_output=True, timeout=120)
    if out.returncode:
        raise Refused(f"listing models failed with exit {out.returncode}: {out.stderr.decode('utf-8', 'replace').strip()[-500:]}")
    text = out.stdout.decode("utf-8", errors="replace")
    models = []
    if spec["format"] == "json":
        try:
            items = dotted(json.loads(text), spec["items"])
        except json.JSONDecodeError as exc:
            raise Refused(f"model listing is not JSON: {exc}") from exc
        for item in items if isinstance(items, list) else []:
            if any(dotted(item, path) == value for path, value in spec.get("skip", {}).items()):
                continue
            model_id = dotted(item, spec["id"])
            if not isinstance(model_id, str):
                continue
            row: dict = {"id": model_id}
            if spec.get("efforts"):
                levels = dotted(item, spec["efforts"]["list"])
                row["efforts"] = [e for e in (dotted(level, spec["efforts"]["field"]) if isinstance(level, dict) else level
                                              for level in (levels if isinstance(levels, list) else [])) if isinstance(e, str)]
            if spec.get("default_effort") and isinstance(dotted(item, spec["default_effort"]), str):
                row["default_effort"] = dotted(item, spec["default_effort"])
            models.append(row)
    else:
        pattern = re.compile(spec["pattern"])
        for line in text.splitlines():
            if match := pattern.search(line):
                models.append({"id": spec.get("id", "{id}").format(**match.groupdict())})
    return {"source": " ".join(spec["args"]), "models": models, **note}


def probe(lane: dict, runs_dir: str | None, timeout: float) -> subprocess.Popen:
    """Start one tiny read-only turn that must echo a marker; the caller drains it."""
    marker = f"RUMO-PROBE-{secrets.token_hex(4)}"
    work = Path(tempfile.mkdtemp(prefix="rumo-probe-"))
    # Some CLIs, such as codex, refuse to run outside a Git repository.
    subprocess.run(["git", "init", "-q", str(work)], capture_output=True)
    prompt = work / "probe.md"
    prompt.write_text(f"Reply with exactly {marker} and nothing else. Do not read files or run tools.\n", encoding="utf-8")
    argv = [sys.executable, str(RUNNER), "start", lane["cli"], "--cwd", str(work), "--prompt-file", str(prompt),
            "--access", "read-only", "--no-window", "--timeout", repr(timeout)]
    for key in ("model", "effort", "executable"):
        if lane.get(key):
            argv += [f"--{key}", lane[key]]
    if runs_dir:
        argv += ["--runs-dir", runs_dir]
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.marker, proc.work = marker, work  # type: ignore[attr-defined]
    return proc


def probe_result(proc: subprocess.Popen) -> dict:
    out, err = proc.communicate()
    shutil.rmtree(proc.work, ignore_errors=True)  # type: ignore[attr-defined]
    try:
        summary = json.loads(out.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "error": err.decode("utf-8", errors="replace").strip()[-2000:] or f"exit {proc.returncode}"}
    final = summary.get("final_file")
    text = Path(final).read_text(encoding="utf-8", errors="replace") if final and Path(final).is_file() else ""
    ok = proc.returncode == 0 and proc.marker in text  # type: ignore[attr-defined]
    result = {"ok": ok, "run_id": summary.get("run_id"), "state": summary.get("state")}
    if not ok:
        stderr = Path(summary.get("run_dir", "")) / "turns" / str(summary.get("turn")) / "stderr.log"
        tail = stderr.read_text(encoding="utf-8", errors="replace").strip()[-500:] if stderr.is_file() else ""
        result["error"] = summary.get("error") or tail or f"reply did not contain the probe marker: {text.strip()[:300]!r}"
    return result


def cmd_show(args: argparse.Namespace) -> int:
    config = load(args.runs_dir)
    print(json.dumps({"path": str(config_path()), **config}, ensure_ascii=False, indent=2))
    return 0


def cmd_lanes(args: argparse.Namespace) -> int:
    config = load(args.runs_dir)
    lanes = config.get("roles", {}).get(args.role) or []
    if not lanes:
        raise NotConfigured(f"role {args.role!r} has no lanes; run the rumo-setup skill to choose them")
    print(json.dumps({"role": args.role, "auto_panel": config.get("auto_panel", "ask"),
                      "lanes": [{**lane, "label": lane_label(lane)} for lane in lanes]}, ensure_ascii=False, indent=2))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    if args.lane:
        targets = [("candidate", lane) for lane in with_executables([parse_lane(t) for t in args.lane], args.executable)]
    else:
        # Stale lanes are reported per row below instead of refusing the whole check.
        config = load(args.runs_dir, roles_to_check=())
        stored = [(role, lane) for role, lanes in config.get("roles", {}).items() for lane in lanes]
        if not stored:
            raise NotConfigured("no lanes are configured; run the rumo-setup skill to choose them")
        lanes = with_executables([lane for _, lane in stored], args.executable)
        targets = [(role, lane) for (role, _), lane in zip(stored, lanes)]
    report, seen = [], {}
    for role, lane in targets:
        # The use label only routes work; the same CLI, model, and effort need one probe.
        key = json.dumps({k: v for k, v in lane.items() if k != "use"}, sort_keys=True)
        if key in seen:
            seen[key]["roles"].append(role)
            continue
        row = {"lane": lane_label(lane), "roles": [role], "problems": lane_problems(lane, args.runs_dir)}
        if not row["problems"]:
            entry = agent_run.get_adapter(lane["cli"], args.runs_dir)
            try:
                preflight = agent_run.check(entry, agent_run.resolve_executable(entry["adapter"], lane.get("executable")))
                row["version"] = preflight["version"]
                row["live_run_verified"] = bool((entry["adapter"].get("verified") or {}).get("live_run"))
                if not preflight["ok"]:
                    row["problems"].append(
                        f"preflight failed: version {preflight['version']!r}, missing flags {preflight['missing_flags']}, "
                        f"failed help {preflight['failed_help']}")
            except Refused as exc:
                row["problems"].append(str(exc))
        seen[key] = row
        report.append((lane, row))
    if args.probe:
        running = [(row, probe(lane, args.runs_dir, args.timeout)) for lane, row in report if not row["problems"]]
        for row, proc in running:
            row["probe"] = probe_result(proc)
            if not row["probe"]["ok"]:
                row["problems"].append("probe failed")
    rows = [row for _, row in report]
    ok = bool(rows) and not any(row["problems"] for row in rows)
    print(json.dumps({"ok": ok, "config": str(config_path()), "lanes": rows}, ensure_ascii=False, indent=2))
    return 0 if ok else 2


def cmd_models(args: argparse.Namespace) -> int:
    entry = agent_run.get_adapter(args.cli, args.runs_dir)
    adapter = entry["adapter"]
    spec = adapter.get("models") or {}
    exe = None if "static" in spec or not spec else agent_run.resolve_executable(adapter, args.executable)
    print(json.dumps({"cli": args.cli, "efforts": adapter.get("efforts") or [], **list_models(adapter, exe)}, ensure_ascii=False, indent=2))
    return 0


def cmd_set_role(args: argparse.Namespace) -> int:
    lanes = with_executables([parse_lane(text) for text in args.lane], args.executable)
    config = load_or_new(args.runs_dir)
    config.setdefault("roles", {})[args.role] = lanes
    path = write(config, args.runs_dir, roles_to_check=(args.role,))
    print(json.dumps({"path": str(path), "role": args.role, "lanes": [lane_label(lane) for lane in lanes]}, ensure_ascii=False))
    return 0


def cmd_set_auto_panel(args: argparse.Namespace) -> int:
    config = load_or_new(args.runs_dir)
    config["auto_panel"] = args.value
    path = write(config, args.runs_dir, roles_to_check=())
    print(json.dumps({"path": str(path), "auto_panel": args.value}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-dir", help="agent_run.py runs directory, where user adapters and probe runs live.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("show", help="Print the configuration and its path.")

    p = sub.add_parser("lanes", help="Print one role's lanes and the auto_panel setting.")
    p.add_argument("role", choices=ROLES)

    p = sub.add_parser("models", help="List the models a CLI offers, with per-model efforts when the CLI reports them.")
    p.add_argument("cli")
    p.add_argument("--executable", help="Path to the CLI when it is not on PATH.")

    p = sub.add_parser("check", help="Check configured lanes, or candidate --lane values before writing them.")
    p.add_argument("--lane", action="append", help="Check this lane instead of the configuration; repeatable.")
    p.add_argument("--executable", action="append", help="cli=path for a CLI that is not on PATH; repeatable.")
    p.add_argument("--probe", action="store_true", help="Also run one tiny read-only turn per lane; spends a little quota.")
    p.add_argument("--timeout", type=float, default=300)

    p = sub.add_parser("set-role", help="Replace one role's lanes; other roles and settings are kept.")
    p.add_argument("role", choices=ROLES)
    p.add_argument("--lane", action="append", required=True, help="[use=]cli[:model][@effort]; repeatable, in order.")
    p.add_argument("--executable", action="append", help="cli=path for a CLI that is not on PATH; repeatable.")

    p = sub.add_parser("set-auto-panel", help="Set what the agent may do when it judges a multi-model panel worth it.")
    p.add_argument("value", choices=AUTO_PANEL)

    args = parser.parse_args(argv)
    # Callers parse the JSON as UTF-8; on Windows a piped stdout would otherwise use the ANSI code page.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    handlers = {"show": cmd_show, "lanes": cmd_lanes, "check": cmd_check, "models": cmd_models,
                "set-role": cmd_set_role, "set-auto-panel": cmd_set_auto_panel}
    try:
        return handlers[args.command](args)
    except NotConfigured as exc:
        print(f"not configured: {exc}", file=sys.stderr)
        return NOT_CONFIGURED
    except (Refused, OSError, subprocess.TimeoutExpired) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
