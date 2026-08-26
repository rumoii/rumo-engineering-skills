#!/usr/bin/env python3
"""Calculate the next CalVer version tag (YY.WW.MICRO).

- YY: ISO year % 100 (no leading zero)
- WW: ISO week number (no leading zero)
- MICRO: globally incrementing integer starting from 1
"""

import datetime
import re
import subprocess
import sys


def get_all_tags():
    """Run `git tag -l` and return a list of tag strings."""
    result = subprocess.run(
        ["git", "tag", "-l"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error running git tag: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def find_max_micro(tags):
    """Scan all CalVer tags and return the maximum MICRO value, or 0 if none."""
    pattern = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d+)$")
    max_micro = 0
    for tag in tags:
        m = pattern.match(tag)
        if m:
            micro = int(m.group(3))
            if micro > max_micro:
                max_micro = micro
    return max_micro


def main():
    tags = get_all_tags()
    max_micro = find_max_micro(tags)
    today = datetime.date.today()
    iso_year, iso_week, _ = today.isocalendar()
    yy = iso_year % 100
    ww = iso_week
    next_micro = max_micro + 1
    print(f"{yy}.{ww}.{next_micro}")


if __name__ == "__main__":
    main()