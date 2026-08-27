from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
SH = shutil.which("sh")


@unittest.skipUnless(SH and os.name != "nt", "POSIX sh is not available on this host")
class InstallShellTests(unittest.TestCase):
    def run_installer(
        self,
        temp_root: Path,
        codex_home: Path,
        claude_home: Path,
        agents_home: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                SH,
                str(REPO_ROOT / "install.sh"),
                "--repo",
                str(REPO_ROOT),
                "--codex-home",
                str(codex_home),
                "--claude-home",
                str(claude_home),
                "--agents-home",
                str(agents_home),
                "--no-pull",
                *extra,
            ],
            cwd=REPO_ROOT,
            env={**os.environ, "HOME": str(temp_root)},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_links_rumo_skills_for_codex_claude_and_grok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex"
            claude_home = temp_root / "claude"
            agents_home = temp_root / "agents"

            for home in (claude_home, agents_home):
                preserved = home / "skills" / "third-party-skill"
                preserved.mkdir(parents=True)
                (preserved / "SKILL.md").write_text(
                    "# Third Party\n", encoding="utf-8"
                )

            result = self.run_installer(
                temp_root, codex_home, claude_home, agents_home
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            repo_skills = sorted(
                path.name for path in (REPO_ROOT / "skills").iterdir() if path.is_dir()
            )
            rumo_skills = [name for name in repo_skills if name.startswith("rumo-")]

            self.assert_link_targets(codex_home / "skills", repo_skills)
            self.assert_link_targets(claude_home / "skills", rumo_skills)
            self.assert_link_targets(agents_home / "skills", rumo_skills)
            self.assertTrue((claude_home / "skills" / "third-party-skill").is_dir())
            self.assertTrue((agents_home / "skills" / "third-party-skill").is_dir())

    def test_foreign_link_stops_all_clients_before_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex"
            claude_home = temp_root / "claude"
            agents_home = temp_root / "agents"
            foreign = temp_root / "personal-skills" / "rumo-code-review"
            foreign.mkdir(parents=True)
            conflict = claude_home / "skills" / "rumo-code-review"
            conflict.parent.mkdir(parents=True)
            conflict.symlink_to(foreign, target_is_directory=True)

            result = self.run_installer(
                temp_root, codex_home, claude_home, agents_home
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Skill link preflight failed", result.stderr)
            self.assertEqual(conflict.resolve(), foreign.resolve())
            self.assertFalse(
                (codex_home / "skills" / "rumo-coding-guidelines").exists()
            )

    def test_explicit_flag_replaces_foreign_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex"
            claude_home = temp_root / "claude"
            agents_home = temp_root / "agents"
            foreign = temp_root / "personal-skills" / "rumo-code-review"
            foreign.mkdir(parents=True)
            conflict = codex_home / "skills" / "rumo-code-review"
            conflict.parent.mkdir(parents=True)
            conflict.symlink_to(foreign, target_is_directory=True)

            result = self.run_installer(
                temp_root,
                codex_home,
                claude_home,
                agents_home,
                "--replace-foreign-links",
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                conflict.resolve(), (REPO_ROOT / "skills" / "rumo-code-review").resolve()
            )

    def test_real_directory_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex"
            claude_home = temp_root / "claude"
            agents_home = temp_root / "agents"
            conflict = codex_home / "skills" / "rumo-code-review"
            conflict.mkdir(parents=True)
            marker = conflict / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")

            result = self.run_installer(
                temp_root,
                codex_home,
                claude_home,
                agents_home,
                "--replace-foreign-links",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("real file or directory", result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse(
                (claude_home / "skills" / "rumo-coding-guidelines").exists()
            )

    def test_skips_absent_optional_clients(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            codex_home = temp_root / "codex"
            bin_dir = temp_root / "bin"
            bin_dir.mkdir()
            for command in (
                "basename",
                "dirname",
                "git",
                "ln",
                "mkdir",
                "python3",
                "readlink",
                "rm",
                "sh",
            ):
                source = shutil.which(command)
                self.assertIsNotNone(source, command)
                (bin_dir / command).symlink_to(source)

            result = subprocess.run(
                [
                    SH,
                    str(REPO_ROOT / "install.sh"),
                    "--repo",
                    str(REPO_ROOT),
                    "--codex-home",
                    str(codex_home),
                    "--no-pull",
                ],
                cwd=REPO_ROOT,
                env={"HOME": str(temp_root), "PATH": str(bin_dir)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((codex_home / "skills").is_dir())
            self.assertFalse((temp_root / ".claude").exists())
            self.assertFalse((temp_root / ".agents").exists())
            self.assertIn("Claude Code was not detected; skipping.", result.stdout)
            self.assertIn(
                "A shared agent client was not detected; skipping.", result.stdout
            )

            explicit_claude = temp_root / "explicit-claude"
            explicit_agents = temp_root / "explicit-agents"
            forced_result = subprocess.run(
                [
                    SH,
                    str(REPO_ROOT / "install.sh"),
                    "--repo",
                    str(REPO_ROOT),
                    "--codex-home",
                    str(codex_home),
                    "--claude-home",
                    str(explicit_claude),
                    "--agents-home",
                    str(explicit_agents),
                    "--no-pull",
                ],
                cwd=REPO_ROOT,
                env={"HOME": str(temp_root), "PATH": str(bin_dir)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                forced_result.returncode,
                0,
                forced_result.stdout + forced_result.stderr,
            )
            self.assert_link_targets(
                explicit_claude / "skills",
                [
                    path.name
                    for path in (REPO_ROOT / "skills").iterdir()
                    if path.is_dir() and path.name.startswith("rumo-")
                ],
            )
            self.assert_link_targets(
                explicit_agents / "skills",
                [
                    path.name
                    for path in (REPO_ROOT / "skills").iterdir()
                    if path.is_dir() and path.name.startswith("rumo-")
                ],
            )

    def assert_link_targets(self, skills_dir: Path, expected_names: list[str]) -> None:
        for name in expected_names:
            link = skills_dir / name
            self.assertTrue(link.is_symlink(), link)
            self.assertEqual(link.resolve(), (REPO_ROOT / "skills" / name).resolve())


if __name__ == "__main__":
    unittest.main()
