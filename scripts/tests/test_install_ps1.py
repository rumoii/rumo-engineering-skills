from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "PowerShell is not available")
class InstallPowerShellTests(unittest.TestCase):
    def run_installer(
        self,
        homes: dict[str, Path],
        *extra: str,
        environment: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(REPO_ROOT / "install.ps1"),
            "-Repo",
            str(REPO_ROOT),
            "-NoPull",
        ]
        for parameter, home in homes.items():
            command.extend((f"-{parameter}", str(home)))
        command.extend(extra)
        return subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            check=False,
        )

    def create_junction(self, link: Path, target: Path) -> None:
        link.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir(parents=True, exist_ok=True)
        link_arg = str(link).replace("'", "''")
        target_arg = str(target).replace("'", "''")
        result = subprocess.run(
            [
                POWERSHELL,
                "-NoProfile",
                "-Command",
                f"New-Item -ItemType Junction -Path '{link_arg}' -Target '{target_arg}' | Out-Null",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_links_rumo_skills_and_preserves_unrelated_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            for home in homes.values():
                preserved = home / "skills" / "third-party-skill"
                preserved.mkdir(parents=True)
                (preserved / "SKILL.md").write_text(
                    "# Third Party\n", encoding="utf-8"
                )

            result = self.run_installer(homes)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            skill_names = sorted(
                path.name
                for path in (REPO_ROOT / "skills").iterdir()
                if path.is_dir() and path.name.startswith("rumo-")
            )
            self.assertEqual(len(skill_names), 30)
            for home in homes.values():
                for name in skill_names:
                    self.assertTrue(
                        os.path.samefile(
                            home / "skills" / name, REPO_ROOT / "skills" / name
                        ),
                        name,
                    )
                self.assertTrue((home / "skills" / "third-party-skill").is_dir())

    def test_foreign_link_stops_all_clients_before_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            foreign = temp_root / "personal-skills" / "rumo-code-review"
            conflict = homes["ClaudeHome"] / "skills" / "rumo-code-review"
            self.create_junction(conflict, foreign)

            result = self.run_installer(homes)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Skill link preflight failed", result.stdout + result.stderr)
            self.assertTrue(os.path.samefile(conflict, foreign))
            self.assertFalse(
                (homes["CodexHome"] / "skills" / "rumo-coding-guidelines").exists()
            )

    def test_explicit_flag_replaces_foreign_link(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            foreign = temp_root / "personal-skills" / "rumo-code-review"
            conflict = homes["CodexHome"] / "skills" / "rumo-code-review"
            self.create_junction(conflict, foreign)

            result = self.run_installer(homes, "-ReplaceForeignLinks")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                os.path.samefile(conflict, REPO_ROOT / "skills" / "rumo-code-review")
            )

    def test_real_directory_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            conflict = homes["CodexHome"] / "skills" / "rumo-code-review"
            conflict.mkdir(parents=True)
            marker = conflict / "keep.txt"
            marker.write_text("keep\n", encoding="utf-8")

            result = self.run_installer(homes, "-ReplaceForeignLinks")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("real file or directory", result.stdout + result.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep\n")
            self.assertFalse(
                (homes["ClaudeHome"] / "skills" / "rumo-coding-guidelines").exists()
            )

    def test_profiles_repo_parameter_persists_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {"CodexHome": temp_root / "codex"}
            profiles_repo = temp_root / "private-profiles"
            (profiles_repo / "profiles").mkdir(parents=True)
            user_home = temp_root / "user-home"
            environment = {
                **os.environ,
                "HOME": str(user_home),
                "USERPROFILE": str(user_home),
            }

            result = self.run_installer(
                homes,
                "-ProfilesRepo",
                str(profiles_repo),
                environment=environment,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            config = json.loads(
                (user_home / ".rumo-engineering-skills" / "config.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(Path(config["profiles_repo"]), profiles_repo.resolve())

    def test_invalid_profiles_repo_stops_before_link_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            invalid = temp_root / "missing-profiles"
            invalid.mkdir()
            user_home = temp_root / "user-home"
            environment = {
                **os.environ,
                "HOME": str(user_home),
                "USERPROFILE": str(user_home),
            }

            result = self.run_installer(
                homes,
                "-ProfilesRepo",
                str(invalid),
                environment=environment,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must contain a profiles directory", result.stdout + result.stderr)
            self.assertFalse((homes["CodexHome"] / "skills").exists())
            self.assertFalse(
                (user_home / ".rumo-engineering-skills" / "config.json").exists()
            )

    def test_dry_run_does_not_persist_profiles_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {"CodexHome": temp_root / "codex"}
            profiles_repo = temp_root / "private-profiles"
            (profiles_repo / "profiles").mkdir(parents=True)
            user_home = temp_root / "user-home"
            environment = {
                **os.environ,
                "HOME": str(user_home),
                "USERPROFILE": str(user_home),
            }

            result = self.run_installer(
                homes,
                "-ProfilesRepo",
                str(profiles_repo),
                "-DryRun",
                environment=environment,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(
                (user_home / ".rumo-engineering-skills" / "config.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
