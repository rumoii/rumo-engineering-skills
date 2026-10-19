#!/usr/bin/env bash
set -euo pipefail
git init -q
git config user.email sam@example.invalid
git config user.name "Sam Lee"
cat > loader.py <<'PY'
from pathlib import Path


def load_ids(path):
    return Path(path).read_text(encoding="utf-8").splitlines()
PY
printf '\xef\xbb\xbfalpha\nbeta\n' > ids.txt
cat > test_loader.py <<'PY'
import unittest

from loader import load_ids


class LoaderTest(unittest.TestCase):
    def test_first_id(self):
        self.assertEqual(load_ids("ids.txt")[0], "alpha")


if __name__ == "__main__":
    unittest.main()
PY
cat > ci.log <<'LOG'
test_first_id (test_loader.LoaderTest.test_first_id) ... FAIL

======================================================================
FAIL: test_first_id (test_loader.LoaderTest.test_first_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_loader.py", line 8, in test_first_id
    self.assertEqual(load_ids("ids.txt")[0], "alpha")
AssertionError: '\ufeffalpha' != 'alpha'
- \ufeffalpha
? -
+ alpha


----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
LOG
git add -A
git commit -qm "Add id loader"
