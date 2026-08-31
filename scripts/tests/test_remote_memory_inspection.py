from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "rumo-remote-memory-inspection"
    / "scripts"
    / "remote_memory_inspection.py"
)
SPEC = importlib.util.spec_from_file_location("remote_memory_inspection", SCRIPT)
assert SPEC and SPEC.loader
REMOTE_MEMORY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REMOTE_MEMORY)


class RemoteMemoryOutputPathTests(unittest.TestCase):
    def test_host_path_characters_cannot_escape_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "evidence"
            output = REMOTE_MEMORY.output_path(root, "../escaped", "20260831-120000")

            self.assertEqual(output.parent, root.resolve())
            self.assertNotIn("..", output.name)
            self.assertNotIn("/", output.name)
            self.assertNotIn("\\", output.name)

    def test_ipv6_host_produces_cross_platform_directory_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = REMOTE_MEMORY.output_path(
                Path(temp_dir), "2001:db8::1", "20260831-120000"
            )

            self.assertNotIn(":", output.name)
            self.assertRegex(output.name, r"^[A-Za-z0-9_-]+$")


if __name__ == "__main__":
    unittest.main()
