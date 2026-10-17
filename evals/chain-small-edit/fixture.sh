#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email eval@example.invalid
git config user.name eval
mkdir -p web src
cat > web/login.html <<'HTML'
<form action="/session" method="post">
  <label>账号 <input name="account"></label>
  <label>密码 <input name="password" type="password"></label>
  <button type="submit">登录</button>
</form>
HTML
cat > src/auth.py <<'PY'
def may_admin(user):
    return "admin" in user.get("roles", ())
PY
git add -A
git commit -qm "Add login page"
