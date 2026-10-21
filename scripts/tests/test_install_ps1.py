from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.tests.skill_fixture import CORE_SKILLS, build_fixture_repo, promote_extra


REPO_ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
BASELINE_START = "<!-- rumo-engineering-skills:baseline:start -->"


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
            self.assertIn("rumo-filesystem-safety", skill_names)
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
            foreign = temp_root / "personal-skills" / "rumo-git-commit"
            conflict = homes["ClaudeHome"] / "skills" / "rumo-git-commit"
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
            foreign = temp_root / "personal-skills" / "rumo-git-commit"
            conflict = homes["CodexHome"] / "skills" / "rumo-git-commit"
            self.create_junction(conflict, foreign)

            result = self.run_installer(homes, "-ReplaceForeignLinks")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                os.path.samefile(conflict, REPO_ROOT / "skills" / "rumo-git-commit")
            )

    def test_real_directory_is_never_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            conflict = homes["CodexHome"] / "skills" / "rumo-git-commit"
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

    def isolated_environment(self, user_home: Path) -> dict[str, str]:
        """Hide installed clients so detection depends only on the test inputs."""
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() not in {"CODEX_HOME", "CLAUDE_HOME", "AGENTS_HOME", "PATH"}
        }
        tool_dirs = {
            str(Path(shutil.which("git")).parent),
            str(Path(sys.executable).parent),
            str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"),
        }
        environment.update(
            {
                "HOME": str(user_home),
                "USERPROFILE": str(user_home),
                "PATH": os.pathsep.join(sorted(tool_dirs)),
            }
        )
        return environment

    def test_skips_undetected_codex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            user_home = temp_root / "user-home"
            user_home.mkdir()
            homes = {"ClaudeHome": temp_root / "claude"}

            result = self.run_installer(
                homes, environment=self.isolated_environment(user_home)
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Codex was not detected; skipping.", result.stdout)
            self.assertFalse((user_home / ".codex").exists())
            self.assertTrue(
                os.path.samefile(
                    homes["ClaudeHome"] / "skills" / "rumo-git-commit",
                    REPO_ROOT / "skills" / "rumo-git-commit",
                )
            )

    def test_existing_shared_agents_home_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            user_home = Path(temp_dir) / "user-home"
            (user_home / ".agents").mkdir(parents=True)

            result = self.run_installer(
                {}, environment=self.isolated_environment(user_home)
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                os.path.samefile(
                    user_home / ".agents" / "skills" / "rumo-git-commit",
                    REPO_ROOT / "skills" / "rumo-git-commit",
                )
            )
            self.assertFalse((user_home / ".codex").exists())
            self.assertFalse((user_home / ".claude").exists())

    def test_no_detected_client_stops_without_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            user_home = Path(temp_dir) / "user-home"
            user_home.mkdir()

            result = self.run_installer(
                {}, environment=self.isolated_environment(user_home)
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "No supported agent client was detected", result.stdout + result.stderr
            )
            for client_home in (".codex", ".claude", ".agents"):
                self.assertFalse((user_home / client_home).exists(), client_home)

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

    def test_baseline_flags_add_keep_and_remove_the_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            user_home = temp_root / "user-home"
            user_home.mkdir()
            homes = {
                "CodexHome": temp_root / "codex",
                "ClaudeHome": temp_root / "claude",
                "AgentsHome": temp_root / "agents",
            }
            claude_md = homes["ClaudeHome"] / "CLAUDE.md"
            codex_md = homes["CodexHome"] / "AGENTS.md"
            homes["ClaudeHome"].mkdir()
            claude_md.write_bytes(b"# mine\n")
            environment = self.isolated_environment(user_home)

            def install(*extra: str) -> subprocess.CompletedProcess[str]:
                return self.run_installer(homes, *extra, environment=environment)

            result = install()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("rerun with -Baseline", result.stdout)
            self.assertEqual(claude_md.read_bytes(), b"# mine\n")
            self.assertFalse(codex_md.exists())

            result = install("-Baseline", "-DryRun")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Would update baseline (added)", result.stdout)
            self.assertEqual(claude_md.read_bytes(), b"# mine\n")
            self.assertFalse(codex_md.exists())

            result = install("-Baseline")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            installed = claude_md.read_text(encoding="utf-8")
            self.assertTrue(installed.startswith("# mine\n\n" + BASELINE_START))
            self.assertIn(BASELINE_START, codex_md.read_text(encoding="utf-8"))
            self.assertIn("paste skills", result.stdout)

            result = install()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn("rerun with -Baseline", result.stdout)
            self.assertEqual(claude_md.read_text(encoding="utf-8"), installed)

            result = install("-Baseline", "-RemoveBaseline")
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(claude_md.read_text(encoding="utf-8"), installed)

            result = install("-RemoveBaseline")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(claude_md.read_bytes(), b"# mine\n")
            self.assertNotIn(BASELINE_START, codex_md.read_text(encoding="utf-8"))

            self.assertEqual(install("-Baseline").returncode, 0)
            result = install("-Uninstall")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(claude_md.read_bytes(), b"# mine\n")
            self.assertNotIn(BASELINE_START, codex_md.read_text(encoding="utf-8"))
            self.assertFalse(any((homes["ClaudeHome"] / "skills").iterdir()))


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "PowerShell is not available")
class InstallPowerShellExtrasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temp_dir.name)
        self.repo = build_fixture_repo(self.temp_root)
        # Name every client home so detection never reaches the real user profile.
        self.homes = {
            "CodexHome": self.temp_root / "codex",
            "ClaudeHome": self.temp_root / "claude",
            "AgentsHome": self.temp_root / "agents",
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_installer(
        self, *extra: str, pull: bool = False, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        command = [
            POWERSHELL,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.repo / "install.ps1"),
            "-Repo",
            str(self.repo),
        ]
        if not pull:
            command.append("-NoPull")
        for parameter, home in self.homes.items():
            command.extend((f"-{parameter}", str(home)))
        command.extend(extra)
        return subprocess.run(
            command,
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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

    def create_dangling_junction(self, link: Path, target: Path) -> None:
        self.create_junction(link, target)
        target.rmdir()

    def installed(self, home: str) -> list[str]:
        skills = self.homes[home] / "skills"
        return sorted(path.name for path in skills.iterdir()) if skills.is_dir() else []

    def assert_links_to(self, home: str, name: str, root: str) -> None:
        self.assertTrue(
            os.path.samefile(self.homes[home] / "skills" / name, self.repo / root / name),
            name,
        )

    def test_default_install_links_only_default_skills(self) -> None:
        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for home in self.homes:
            self.assertEqual(self.installed(home), sorted(CORE_SKILLS))

    def test_list_extras_changes_nothing(self) -> None:
        result = self.run_installer("-ListExtras")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("rumo-gamma  Use when testing optional skill rumo-gamma.", result.stdout)
        self.assertIn("rumo-delta", result.stdout)
        for home in self.homes.values():
            self.assertFalse(home.exists())

    def test_help_prints_usage_without_changes(self) -> None:
        for flag in ("-Help", "-h", "--help"):
            result = self.run_installer(flag)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("-Extras", result.stdout)
            self.assertIn("List optional skills without changing anything.", result.stdout)
            for home in self.homes.values():
                self.assertFalse(home.exists())

    def test_positional_argument_fails_without_changes(self) -> None:
        result = self.run_installer("stray")

        self.assertNotEqual(result.returncode, 0)
        for home in self.homes.values():
            self.assertFalse(home.exists())

    def test_list_extras_does_not_require_git(self) -> None:
        path = os.pathsep.join(
            entry
            for entry in os.environ.get("PATH", "").split(os.pathsep)
            if entry and not (Path(entry) / "git.exe").exists()
        )
        result = self.run_installer("-ListExtras", env={**os.environ, "PATH": path})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("rumo-gamma", result.stdout)

    def test_extras_are_installed_preserved_and_removed(self) -> None:
        result = self.run_installer("-Extras", "rumo-gamma,rumo-delta")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assert_links_to("CodexHome", "rumo-gamma", "extras")
        self.assert_links_to("ClaudeHome", "rumo-delta", "extras")

        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            self.installed("ClaudeHome"), sorted((*CORE_SKILLS, "rumo-delta", "rumo-gamma"))
        )

        result = self.run_installer("-RemoveExtras", "rumo-gamma")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Removed optional skill rumo-gamma.", result.stdout)
        self.assertEqual(self.installed("CodexHome"), sorted((*CORE_SKILLS, "rumo-delta")))

    def test_unknown_extra_fails_before_any_change(self) -> None:
        for name in ("rumo-missing", "rumo-delta rumo-gamma", "rumo-delta\trumo-gamma"):
            result = self.run_installer("-Extras", name)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unknown optional skill", result.stdout + result.stderr)
            for home in self.homes.values():
                self.assertFalse(home.exists())

    def test_unknown_extra_fails_before_pull(self) -> None:
        (self.repo / ".git").mkdir()
        result = self.run_installer("-Extras", "rumo-missing", "-DryRun", pull=True)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown optional skill: rumo-missing", result.stdout + result.stderr)
        self.assertNotIn("pull --ff-only", result.stdout)

    def test_same_name_in_extras_and_remove_extras_fails(self) -> None:
        result = self.run_installer("-Extras", "rumo-gamma", "-RemoveExtras", "rumo-gamma")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("passed to both", result.stdout + result.stderr)
        for home in self.homes.values():
            self.assertFalse(home.exists())

    def test_stale_repository_links_are_removed(self) -> None:
        for home in self.homes.values():
            skills = home / "skills"
            self.create_dangling_junction(
                skills / "rumo-old-alpha", self.repo / "skills" / "rumo-old-alpha"
            )
            self.create_dangling_junction(
                skills / "rumo-gamma", self.repo / "skills" / "rumo-gamma"
            )

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Removed stale link rumo-old-alpha.", result.stdout)
        self.assertIn("rumo-gamma is optional now", result.stdout)
        for home in self.homes:
            self.assertEqual(self.installed(home), sorted(CORE_SKILLS))

    def test_upgrade_moves_same_name_skill_to_requested_extra(self) -> None:
        for home in self.homes.values():
            self.create_dangling_junction(
                home / "skills" / "rumo-gamma", self.repo / "skills" / "rumo-gamma"
            )

        result = self.run_installer("-Extras", "rumo-gamma")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for home in self.homes:
            self.assert_links_to(home, "rumo-gamma", "extras")

    def test_upgrade_promotes_extra_to_default_without_flags(self) -> None:
        result = self.run_installer("-Extras", "rumo-gamma")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        promote_extra(self.repo, "rumo-gamma")
        for _ in range(2):
            result = self.run_installer()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for home in self.homes:
                self.assert_links_to(home, "rumo-gamma", "skills")
                self.assertEqual(self.installed(home), sorted((*CORE_SKILLS, "rumo-gamma")))
        listed = self.run_installer("-ListExtras")
        self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)
        self.assertNotIn("rumo-gamma", listed.stdout)
        self.assertIn("rumo-delta", listed.stdout)

    def test_promoted_default_preserves_foreign_link_and_stops_all_clients(self) -> None:
        promote_extra(self.repo, "rumo-gamma")
        foreign = self.temp_root / "personal" / "rumo-gamma"
        self.create_junction(self.homes["ClaudeHome"] / "skills" / "rumo-gamma", foreign)
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Skill link preflight failed", result.stdout + result.stderr)
        self.assertTrue(os.path.samefile(self.homes["ClaudeHome"] / "skills" / "rumo-gamma", foreign))
        self.assertFalse(self.homes["CodexHome"].exists())
        self.assertFalse(self.homes["AgentsHome"].exists())

    def test_foreign_extra_link_stops_all_clients(self) -> None:
        foreign = self.temp_root / "personal" / "rumo-gamma"
        self.create_junction(self.homes["ClaudeHome"] / "skills" / "rumo-gamma", foreign)

        result = self.run_installer("-Extras", "rumo-gamma")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Skill link preflight failed", result.stdout + result.stderr)
        self.assertTrue(
            os.path.samefile(self.homes["ClaudeHome"] / "skills" / "rumo-gamma", foreign)
        )
        self.assertFalse(self.homes["CodexHome"].exists())

    def test_dry_run_with_extras_changes_nothing(self) -> None:
        result = self.run_installer("-Extras", "rumo-gamma", "-DryRun")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("rumo-gamma", result.stdout)
        self.assertIn("Dry run finished; nothing was changed.", result.stdout)
        self.assertNotIn("installation completed", result.stdout)
        for home in self.homes.values():
            self.assertFalse(home.exists())

    def test_baseline_without_helper_fails_before_any_change(self) -> None:
        result = self.run_installer("-Baseline")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Baseline helper not found", result.stdout + result.stderr)
        for home in self.homes.values():
            self.assertFalse(home.exists())

    def test_uninstall_removes_only_this_repository_links(self) -> None:
        result = self.run_installer("-Extras", "rumo-gamma")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"3 skills linked in {self.homes['ClaudeHome'] / 'skills'}", result.stdout)
        self.assertIn("Next: start a new agent session", result.stdout)
        skills = self.homes["ClaudeHome"] / "skills"
        self.create_junction(skills / "rumo-foreign", self.temp_root / "personal" / "rumo-foreign")
        (skills / "rumo-real").mkdir()
        (skills / "other-skill").mkdir()

        result = self.run_installer("-Uninstall", "-DryRun")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"3 skill links would be removed from {skills}", result.stdout)
        self.assertEqual(self.installed("CodexHome"), sorted((*CORE_SKILLS, "rumo-gamma")))

        result = self.run_installer("-Uninstall")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Rumo skills uninstalled.", result.stdout)
        self.assertEqual(self.installed("CodexHome"), [])
        self.assertEqual(self.installed("ClaudeHome"), ["other-skill", "rumo-foreign", "rumo-real"])
        for name in CORE_SKILLS:
            self.assertTrue((self.repo / "skills" / name / "SKILL.md").is_file(), name)
        self.assertTrue((self.repo / "extras" / "rumo-gamma" / "SKILL.md").is_file())

    def test_uninstall_rejects_install_options(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        for extra in (("-Baseline",), ("-Extras", "rumo-gamma"), ("-ReplaceForeignLinks",)):
            result = self.run_installer("-Uninstall", *extra)

            self.assertNotEqual(result.returncode, 0, extra)
            self.assertIn("-Uninstall cannot be combined", result.stdout + result.stderr)
            self.assertEqual(self.installed("ClaudeHome"), sorted(CORE_SKILLS))

    def test_uninstall_does_not_require_git(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        path = os.pathsep.join(
            entry
            for entry in os.environ.get("PATH", "").split(os.pathsep)
            if entry and not (Path(entry) / "git.exe").exists()
        )
        result = self.run_installer("-Uninstall", env={**os.environ, "PATH": path})

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for home in self.homes:
            self.assertEqual(self.installed(home), [])


if __name__ == "__main__":
    unittest.main()
