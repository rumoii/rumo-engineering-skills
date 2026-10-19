#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email sam@example.invalid
git config user.name "Sam Lee"
mkdir -p orders tests
touch orders/__init__.py tests/__init__.py
cat > orders/service.py <<'PY'
class PermissionDenied(Exception):
    pass


def delete_order(store, order_id, user):
    """user is {"id": str, "roles": [str]}; store.get returns {"id", "owner_id"}."""
    store.get(order_id)
    store.delete(order_id)
PY
cat > tests/test_service.py <<'PY'
import unittest

from orders.service import delete_order


class FakeStore:
    def __init__(self, orders):
        self.orders = {order["id"]: order for order in orders}

    def get(self, order_id):
        return self.orders[order_id]

    def delete(self, order_id):
        del self.orders[order_id]


class DeleteOrderTest(unittest.TestCase):
    def test_admin_deletes(self):
        store = FakeStore([{"id": "o1", "owner_id": "u1"}])
        delete_order(store, "o1", {"id": "u9", "roles": ["admin"]})
        self.assertNotIn("o1", store.orders)


if __name__ == "__main__":
    unittest.main()
PY
git add -A
git commit -qm "Add order deletion"
