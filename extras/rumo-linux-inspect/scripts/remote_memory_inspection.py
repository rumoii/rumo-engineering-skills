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
{ ps -eo pid,ppid,user,stat,%cpu,%mem,rss,vsz,etime,comm,unit --sort=-rss 2>/dev/null || ps -eo pid,ppid,user,stat,%cpu,%mem,rss,vsz,etime,comm --sort=-rss 2>/dev/null || true; } | head -45
echo "===== process owners ====="
for pid in $(ps -eo pid= --sort=-rss 2>/dev/null | head -15); do
  owner=$(grep -m 1 -E '^0::|name=systemd' "/proc/$pid/cgroup" 2>/dev/null || true)
  echo "$pid ${owner:--}"
done
echo "===== process resources ====="
for pid in $(ps -eo pid= --sort=-rss 2>/dev/null | head -15); do
  threads=$(sed -n 's/^Threads:[[:space:]]*//p' "/proc/$pid/status" 2>/dev/null || true)
  if [ -r "/proc/$pid/fd" ] && [ -x "/proc/$pid/fd" ]; then
    fds=$(find "/proc/$pid/fd" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)
  else
    fds="not-collected"
  fi
  printf '%s threads=%s fds=%s\n' "$pid" "${threads:-not-collected}" "$fds"
done
echo "===== kernel oom ====="
dmesg -T 2>/dev/null | grep -Ei 'out of memory|oom|killed process|memory allocation failure' | tail -100 || true
echo "===== listeners ====="
ss -lntp 2>/dev/null | head -160 || true
echo "===== containers ====="
docker ps --format '{{.ID}} {{.Image}} {{.Names}} {{.Status}}' 2>/dev/null || true
docker stats --no-stream 2>/dev/null || true
'''

LOG_RISKS = r'''echo '===== log risks (file, category, count) ====='
if [ ! -d __LOG_DIR__ ]; then
  echo 'log directory missing or not a directory'
elif [ ! -r __LOG_DIR__ ] || [ ! -x __LOG_DIR__ ]; then
  echo 'log directory not readable'
else
  find __LOG_DIR__ -maxdepth 3 -type f -mmin -__WINDOW__ -print 2>/dev/null | sort | head -200 | {
    scanned=0; unreadable=0; hits=0
    while IFS= read -r file; do
      scanned=$((scanned + 1))
      if [ ! -r "$file" ]; then
        unreadable=$((unreadable + 1))
        printf '%s\tunreadable\n' "$file"
        continue
      fi
      for category in OutOfMemoryError 'Full GC' 'Cannot allocate memory' 'Killed process' timeout ERROR WARN; do
        count=$(grep -ciF -- "$category" "$file" 2>/dev/null || true)
        if [ "${count:-0}" -gt 0 ]; then
          hits=$((hits + 1))
          printf '%s\t%s\t%s\n' "$file" "$category" "$count"
        fi
      done
    done
    echo "files_scanned=$scanned unreadable=$unreadable matching_entries=$hits"
  }
fi
'''


def jvm_pid_files(profile: Path | None) -> list[tuple[str, str]]:
    if profile is None:
        return []
    runtime = json.loads((profile / "runtime.json").read_text(encoding="utf-8"))
    products = runtime.get("products", {})
    if not isinstance(products, dict):
        raise ValueError("runtime.json products must be an object")
    declared = []
    for name, product in sorted(products.items()):
        if isinstance(product, dict) and product.get("runtime") == "jvm":
            pid_file = product.get("pid_file")
            if not isinstance(pid_file, str) or not pid_file.strip():
                raise ValueError(f"JVM product {name} needs a pid_file")
            declared.append((name, pid_file))
    return declared


def remote_script(root: str, log_dir: str, window_minutes: int, jvm: list[tuple[str, str]] | None = None) -> str:
    """Build the read-only remote script; logs are summarized, never echoed."""
    extra = []
    if root:
        quoted = shlex.quote(root)
        extra.append(f"echo '===== root ====='; ls -lah {quoted}; find {quoted} -maxdepth 2 -type f -mmin -{window_minutes} -print 2>/dev/null | sort")
    if log_dir:
        quoted = shlex.quote(log_dir)
        extra.append(f"echo '===== recent logs ====='; find {quoted} -maxdepth 3 -type f -mmin -{window_minutes} -print 2>/dev/null | sort")
        extra.append(LOG_RISKS.replace("__LOG_DIR__", quoted).replace("__WINDOW__", str(window_minutes)))
    extra.append("echo '===== jvm ====='")
    if not jvm:
        extra.append("echo 'not collected: no JVM declared in profile'")
    for name, pid_file in jvm or []:
        extra.append(f"""echo {shlex.quote(name)}
if ! command -v jcmd >/dev/null 2>&1; then
  echo 'not collected: jcmd unavailable'
else
  pid=$(cat {shlex.quote(pid_file)} 2>/dev/null || true)
  case "$pid" in
    ''|*[!0-9]*) echo 'not collected: PID unavailable' ;;
    *)
      jcmd "$pid" GC.heap_info 2>&1 | head -80 || true
      jcmd "$pid" VM.native_memory summary 2>&1 | head -80 || true
      ;;
  esac
fi""")
    return REMOTE + "\n" + "\n".join(extra)


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
    parser.add_argument("--profile", type=Path)
    parser.add_argument("--window-minutes", type=int, default=30)
    parser.add_argument("--output-dir", type=Path, default=Path.home() / ".rumo-evidence" / "remote-memory")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        jvm = jvm_pid_files(args.profile)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    script = remote_script(args.root, args.log_dir, args.window_minutes, jvm)
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
