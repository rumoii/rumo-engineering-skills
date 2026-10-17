#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email eval@example.invalid
git config user.name eval
cat > cart.py <<'PY'
def total(items):
    return sum(item["price"] * item["qty"] for item in items)
PY
cat > test_cart.py <<'PY'
import unittest

from cart import total


class TotalTest(unittest.TestCase):
    def test_multiplies_price_by_quantity(self):
        self.assertEqual(total([{"price": 5, "qty": 3}, {"price": 2, "qty": 1}]), 17)


if __name__ == "__main__":
    unittest.main()
PY
git add -A
git commit -qm "Add cart total"
cat > cart.py <<'PY'
def total(items):
    """Sum the line prices of a cart."""
    return sum(item["price"] for item in items)
PY
