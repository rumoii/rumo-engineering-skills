#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email sam@example.invalid
git config user.name "Sam Lee"
mkdir -p services
cat > services/refund.py <<'PY'
class RefundError(Exception):
    pass


def issue_refund(order, request, gateway):
    amount = request["amount"]
    if amount > order.paid_total:
        raise RefundError("refund exceeds the amount paid")
    return gateway.refund(order.id, amount)
PY
git add -A
git commit -qm "Add refund service"
cat > services/refund.py <<'PY'
class RefundError(Exception):
    pass


def issue_refund(order, request, gateway):
    amount = request["amount"]
    if amount <= 0:
        raise RefundError("refund must be positive")
    return gateway.refund(order.id, amount)
PY
