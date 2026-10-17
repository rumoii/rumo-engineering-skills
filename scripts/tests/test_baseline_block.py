from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "rumo-coding-guidelines"
    / "scripts"
    / "baseline_block.py"
)
START = "<!-- rumo-engineering-skills:baseline:start -->"
END = "<!-- rumo-engineering-skills:baseline:end -->"


class BaselineBlockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.target = Path(self.temp_dir.name) / "CLAUDE.md"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--target", str(self.target), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def assert_action(self, expected: str, *args: str) -> None:
        result = self.run_script(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), expected)

    def test_install_creates_missing_file_with_snippet(self) -> None:
        self.assert_action("added", "--install")
        text = self.target.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(START + "\n"))
        self.assertTrue(text.endswith(END + "\n"))
        self.assertIn("rumo-verify", text)

    def test_install_appends_and_remove_restores_original_bytes(self) -> None:
        original = "# 个人规则\n\n- 默认用简体中文回答\n".encode("utf-8")
        self.target.write_bytes(original)
        self.assert_action("added", "--install")
        self.assertTrue(self.target.read_bytes().startswith(original))
        self.assert_action("removed", "--remove")
        self.assertEqual(self.target.read_bytes(), original)

    def test_repeat_install_is_unchanged(self) -> None:
        self.assert_action("added", "--install")
        before = self.target.read_bytes()
        self.assert_action("unchanged", "--install")
        self.assertEqual(self.target.read_bytes(), before)

    def test_stale_block_is_updated_in_place(self) -> None:
        self.target.write_text(f"intro\n\n{START}\n- old rule\n{END}\n\noutro\n", encoding="utf-8")
        self.assert_action("updated", "--refresh")
        text = self.target.read_text(encoding="utf-8")
        self.assertNotIn("- old rule", text)
        self.assertTrue(text.startswith("intro\n\n" + START))
        self.assertTrue(text.endswith(END + "\n\noutro\n"))

    def test_refresh_without_block_changes_nothing(self) -> None:
        self.assert_action("absent", "--refresh")
        self.assertFalse(self.target.exists())
        self.target.write_text("mine\n", encoding="utf-8")
        self.assert_action("absent", "--refresh")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "mine\n")

    def test_crlf_and_bom_are_preserved(self) -> None:
        original = b"\xef\xbb\xbf# rules\r\n- one\r\n"
        self.target.write_bytes(original)
        self.assert_action("added", "--install")
        data = self.target.read_bytes()
        self.assertTrue(data.startswith(original))
        self.assertNotIn(b"\n", data.replace(b"\r\n", b""))
        self.assert_action("removed", "--remove")
        self.assertEqual(self.target.read_bytes(), original)

    def test_broken_markers_fail_without_change(self) -> None:
        for text in (f"{START}\n- half\n", f"{END}\n{START}\n", f"{START}\n{END}\n{START}\n{END}\n"):
            with self.subTest(text=text):
                self.target.write_text(text, encoding="utf-8")
                result = self.run_script("--install")
                self.assertEqual(result.returncode, 2)
                self.assertEqual(self.target.read_text(encoding="utf-8"), text)

    def test_dry_run_reports_without_writing(self) -> None:
        self.assert_action("added", "--install", "--dry-run")
        self.assertFalse(self.target.exists())
        self.target.write_text("mine\n", encoding="utf-8")
        self.assert_action("added", "--install", "--dry-run")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "mine\n")

    def test_install_requires_existing_directory(self) -> None:
        self.target = Path(self.temp_dir.name) / "missing" / "CLAUDE.md"
        result = self.run_script("--install")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.target.parent.exists())


if __name__ == "__main__":
    unittest.main()
