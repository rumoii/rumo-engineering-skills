#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email eval@example.invalid
git config user.name eval
mkdir -p api reports tests
cat > api/orders.py <<'PY'
def order_response(record):
    """Serialize one order for GET /api/orders; amount is in cents."""
    return {"id": record["id"], "amount": record["amount_cents"]}


def list_orders(records):
    return [order_response(record) for record in records]
PY
cat > reports/export.py <<'PY'
import csv
import io


def export_orders(orders):
    """Write the reconciliation CSV from /api/orders responses."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["id", "amount"])
    for order in orders:
        writer.writerow([order["id"], order["amount"]])
    return out.getvalue()
PY
touch api/__init__.py reports/__init__.py tests/__init__.py
cat > tests/test_orders.py <<'PY'
import unittest

from api.orders import order_response


class OrderResponseTest(unittest.TestCase):
    def test_amount_stays_in_cents(self):
        self.assertEqual(order_response({"id": 1, "amount_cents": 1250}), {"id": 1, "amount": 1250})


if __name__ == "__main__":
    unittest.main()
PY
cat > tests/test_export.py <<'PY'
import unittest

from reports.export import export_orders


class ExportTest(unittest.TestCase):
    def test_header_and_row(self):
        self.assertEqual(export_orders([{"id": 1, "amount": 1250}]), "id,amount\n1,1250\n")


if __name__ == "__main__":
    unittest.main()
PY
git add -A
git commit -qm "Add order API and export"
