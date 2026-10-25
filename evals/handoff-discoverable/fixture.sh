#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email sam@example.invalid
git config user.name "Sam Lee"
mkdir -p docs notes/tasks/csv-export
cat > AGENTS.md <<'MD'
# Workspace Guide

Read `docs/INDEX.md` before starting or continuing a task. Store task handoffs at `notes/tasks/<task-key>/HANDOVER.md`.
MD
cat > docs/INDEX.md <<'MD'
# Project Documentation

- [CSV export status](EXPORT.md)
MD
cat > docs/EXPORT.md <<'MD'
# CSV Export

Task key: `csv-export`.

The CSV export implementation is complete. `python -m unittest test_export` passed. User-facing documentation is not written yet. Do not commit unless the user asks.
MD
cat > export.py <<'PY'
def rows(records):
    return ((record["name"], record["total"]) for record in records)
PY
git add -A
git commit -qm "Add CSV export"
