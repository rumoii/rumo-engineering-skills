#!/usr/bin/env python3
"""Print a bounded read-only SSH probe for a user-supplied environment."""

from __future__ import annotations

import argparse
import shlex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", default="${RUMO_SSH_USER:-$USER}")
    parser.add_argument("--root", default="")
    parser.add_argument("--log-dir", default="")
    parser.add_argument("--keyword", default="")
    args = parser.parse_args()
    commands = ["hostname", "date -Is", "uname -a", "ps -eo pid,ppid,user,%cpu,%mem,rss,etime,args --sort=-rss | head -40", "ss -lntp 2>/dev/null | head -120"]
    if args.root:
        root = shlex.quote(args.root)
        commands.extend([f"ls -lah {root}", f"find {root} -maxdepth 2 -type f -mmin -60 -print 2>/dev/null | sort"])
    if args.log_dir:
        log_dir = shlex.quote(args.log_dir)
        commands.append(f"find {log_dir} -maxdepth 2 -type f -mmin -60 -print 2>/dev/null | sort")
        if args.keyword:
            keyword = shlex.quote(args.keyword)
            commands.append(f"grep -RInF -- {keyword} {log_dir} 2>/dev/null | tail -120")
    remote = " ; ".join(commands)
    print("ssh", shlex.quote(f"{args.user}@{args.host}"), shlex.quote(remote))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
