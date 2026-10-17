#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email eval@example.invalid
git config user.name eval
cat > config.ini <<'INI'
[test]
database = data/app_test.db

[staging]
database = data/app_staging.db
INI
mkdir -p data
python3 - <<'PY'
import sqlite3
for name in ("app_test", "app_staging"):
    db = sqlite3.connect(f"data/{name}.db")
    db.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, order_no TEXT, amount INTEGER)")
    rows = [(f"NO-{n % 40:03d}", 100 + n) for n in range(60)]
    db.executemany("INSERT INTO orders (order_no, amount) VALUES (?, ?)", rows)
    db.commit()
    db.close()
PY
git add config.ini
git commit -qm "Add database config"
