#!/usr/bin/env python3
"""Collect bounded read-only Linux memory evidence over SSH."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
from pathlib import Path


REMOTE = r'''set -eu
echo "===== identity ====="
hostname
date -Is 2>/dev/null || date
uname -a
uptime || true
echo "===== memory ====="
free -m || true
sed -n '1,80p' /proc/meminfo || true
echo "===== processes ====="
ps -eo pid,ppid,user,stat,%cpu,%mem,rss,vsz,etime,args --sort=-rss | head -45 || true
echo "===== kernel oom ====="
dmesg -T 2>/dev/null | grep -Ei 'out of memory|oom|killed process|memory allocation failure' | tail -100 || true
echo "===== listeners ====="
ss -lntp 2>/dev/null | head -160 || true
echo "===== containers ====="
docker ps 2>/dev/null || true
docker stats --no-stream 2>/dev/null || true
'''


def output_path(output_dir: Path, host: str, stamp: str) -> Path:
    """Build a host-labelled evidence directory that cannot escape output_dir."""
    root = output_dir.expanduser().resolve()
    label = (re.sub(r"[^A-Za-z0-9_-]+", "_", host).strip("_") or "host")[:80]
    digest = hashlib.sha256(host.encode("utf-8")).hexdigest()[:10]
    candidate = root / f"{label}-{digest}-{stamp}"
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Evidence output path escaped the output directory") from exc
    return candidate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", default="root")
    parser.add_argument("--root", default="")
    parser.add_argument("--log-dir", default="")
    parser.add_argument("--window-minutes", type=int, default=30)
    parser.add_argument("--output-dir", type=Path, default=Path.home() / ".rumo-evidence" / "remote-memory")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    extra = []
    if args.root:
        root = shlex.quote(args.root)
        extra.append(f"echo '===== root ====='; ls -lah {root}; find {root} -maxdepth 2 -type f -mmin -{args.window_minutes} -print 2>/dev/null | sort")
    if args.log_dir:
        log_dir = shlex.quote(args.log_dir)
        extra.append(f"echo '===== recent logs ====='; find {log_dir} -maxdepth 3 -type f -mmin -{args.window_minutes} -print 2>/dev/null | sort")
        extra.append(f"echo '===== log risks ====='; find {log_dir} -maxdepth 3 -type f -mmin -{args.window_minutes} -print0 2>/dev/null | xargs -0 -r grep -nEi 'OutOfMemoryError|Full GC|Cannot allocate memory|Killed process|timeout|ERROR|WARN' 2>/dev/null | tail -300 || true")
    script = REMOTE + "\n" + "\n".join(extra)
    target = f"{args.user}@{args.host}"
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", target, "sh", "-s"]
    if args.dry_run:
        print(json.dumps({"command": command, "root": args.root, "log_dir": args.log_dir, "window_minutes": args.window_minutes, "writes_remote": False}, indent=2))
        return 0
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    output = output_path(args.output_dir, args.host, stamp)
    output.mkdir(parents=True, exist_ok=False)
    completed = subprocess.run(command, input=script, text=True, capture_output=True, timeout=args.timeout, check=False)
    (output / "remote-output.txt").write_text(completed.stdout, encoding="utf-8", errors="replace")
    (output / "remote-stderr.txt").write_text(completed.stderr, encoding="utf-8", errors="replace")
    (output / "manifest.json").write_text(json.dumps({"host": args.host, "user": args.user, "returncode": completed.returncode, "writes_remote": False}, indent=2) + "\n", encoding="utf-8")
    print(output)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
