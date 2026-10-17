#!/usr/bin/env python3
"""Print a bounded read-only SSH probe for a user-supplied environment."""

from __future__ import annotations

import argparse
import shlex


PROCESSES = (
    "{ ps -eo pid,ppid,user,%cpu,%mem,rss,etime,comm,unit --sort=-rss 2>/dev/null"
    " || ps -eo pid,ppid,user,%cpu,%mem,rss,etime,comm --sort=-rss; } | head -40"
)
SECRET_KEYS = ("password", "passwd", "pwd", "secret", "token", "api[-_]?key", "access[-_]?key", "private[-_]?key", "credential", "authorization")


def any_case(pattern: str) -> str:
    """Spell letters as [Aa] classes so the filter works without GNU sed's I flag."""
    return "".join(f"[{char.upper()}{char.lower()}]" if char.isalpha() else char for char in pattern)


def redact_expressions() -> list[str]:
    """Best-effort sed -E expressions that mask common secret shapes in log lines."""
    keys = "|".join(any_case(key) for key in SECRET_KEYS)
    prefix = "((" + keys + ")[A-Za-z0-9_.-]*[\"']?[[:space:]]*[=:][[:space:]]*)"
    return [
        "s#(" + any_case("bearer") + "|" + any_case("basic") + ")[[:space:]]+[^[:space:]\",;]+#\\1 ***#g",
        "s#" + prefix + "\"[^\"]*\"#\\1\"***\"#g",
        "s#" + prefix + "'[^']*'#\\1'***'#g",
        "s#" + prefix + "[^[:space:]\"',;&]+#\\1***#g",
        "s#://[^/@[:space:]:]+:[^/@[:space:]]+@#://***:***@#g",
        "s#eyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+#***#g",
    ]


def remote_commands(root: str, log_dir: str, keyword: str) -> list[str]:
    commands = ["hostname", "date -Is", "uname -a", PROCESSES, "ss -lntp 2>/dev/null | head -120"]
    if root:
        quoted = shlex.quote(root)
        commands.extend([f"ls -lah {quoted}", f"find {quoted} -maxdepth 2 -type f -mmin -60 -print 2>/dev/null | sort"])
    if log_dir:
        quoted = shlex.quote(log_dir)
        commands.append(f"find {quoted} -maxdepth 2 -type f -mmin -60 -print 2>/dev/null | sort")
        if keyword:
            redact = " ".join(f"-e {shlex.quote(expression)}" for expression in redact_expressions())
            commands.append(f"grep -RInF -m 20 -- {shlex.quote(keyword)} {quoted} 2>/dev/null | tail -40 | sed -E {redact}")
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--user", default="${RUMO_SSH_USER:-$USER}")
    parser.add_argument("--root", default="")
    parser.add_argument("--log-dir", default="")
    parser.add_argument("--keyword", default="")
    args = parser.parse_args()
    remote = " ; ".join(remote_commands(args.root, args.log_dir, args.keyword))
    print("ssh", shlex.quote(f"{args.user}@{args.host}"), shlex.quote(remote))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
