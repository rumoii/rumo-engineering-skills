#!/usr/bin/env python3
"""Print a read-only frontend repository inventory."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repo = args.repo.resolve()
    manifests = sorted(str(path.relative_to(repo)) for path in repo.glob("**/package.json") if "node_modules" not in path.parts)[:80]
    source_roots = [name for name in ("src", "apps", "packages", "frontend", "web", "ui") if (repo / name).exists()]
    lockfiles = [name for name in ("pnpm-lock.yaml", "yarn.lock", "package-lock.json", "bun.lockb") if (repo / name).is_file()]
    print(json.dumps({"repo": str(repo), "manifests": manifests, "source_roots": source_roots, "lockfiles": lockfiles}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
