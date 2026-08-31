from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


RESOLVER = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "rumo-project-profile"
    / "scripts"
    / "resolve_profile.py"
)
INITIALIZER = RESOLVER.with_name("init_profile.py")
VALIDATOR = RESOLVER.with_name("verify_profile.py")
PROFILE_CONFIG = RESOLVER.with_name("profile_config.py")


class ProjectProfileResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.profiles = self.root / "profiles"
        self.profiles.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def add_profile(self, profile_id: str, repository_name: str) -> Path:
        profile = self.profiles / profile_id
        profile.mkdir()
        (profile / "project.json").write_text(
            json.dumps(
                {
                    "id": profile_id,
                    "match": {"repository_names": [repository_name]},
                }
            ),
            encoding="utf-8",
        )
        return profile

    def run_resolver(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RESOLVER), "--profiles-root", str(self.root), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_explicit_selection_reports_credential_availability_without_values(self) -> None:
        profile = self.add_profile("example", "unrelated")
        secret_marker = "test-secret-marker"
        (profile / "credentials.md").write_text(secret_marker, encoding="utf-8")

        result = self.run_resolver("--profile", "example")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["profile_id"], "example")
        self.assertTrue(payload["credentials"]["available"])
        self.assertNotIn(secret_marker, result.stdout)

    def test_matches_current_directory_name(self) -> None:
        project = self.root / "matched-repository"
        project.mkdir()
        self.add_profile("matched", project.name)

        result = self.run_resolver("--cwd", str(project))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["profile_id"], "matched")

    def test_rejects_ambiguous_match(self) -> None:
        project = self.root / "ambiguous-repository"
        project.mkdir()
        self.add_profile("first", project.name)
        self.add_profile("second", project.name)

        result = self.run_resolver("--cwd", str(project))

        self.assertEqual(result.returncode, 2)
        self.assertIn("Multiple project profiles matched", result.stderr)

    def test_reports_missing_match(self) -> None:
        project = self.root / "missing-repository"
        project.mkdir()
        self.add_profile("example", "different-repository")

        result = self.run_resolver("--cwd", str(project))

        self.assertEqual(result.returncode, 2)
        self.assertIn("No project profile matched", result.stderr)

    def test_rejects_profile_path_outside_profiles_directory(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "project.json").write_text(
            json.dumps({"id": "outside"}), encoding="utf-8"
        )

        result = self.run_resolver("--profile", "../outside")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Profile id must contain", result.stderr)

    def test_rejects_profile_symlink_outside_profiles_directory(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "project.json").write_text(
            json.dumps({"id": "linked"}), encoding="utf-8"
        )
        link = self.profiles / "linked"
        if os.name == "nt":
            powershell = shutil.which("powershell") or shutil.which("pwsh")
            if not powershell:
                self.skipTest("PowerShell is required to create a junction")
            link_arg = str(link).replace("'", "''")
            outside_arg = str(outside).replace("'", "''")
            completed = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-Command",
                    f"New-Item -ItemType Junction -Path '{link_arg}' -Target '{outside_arg}' | Out-Null",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        else:
            link.symlink_to(outside, target_is_directory=True)

        result = self.run_resolver("--profile", "linked")

        self.assertEqual(result.returncode, 2)
        self.assertIn("inside the profiles directory", result.stderr)

    def test_automatic_matching_rejects_symlink_outside_profiles_directory(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "project.json").write_text(
            json.dumps(
                {
                    "id": "linked",
                    "match": {"repository_names": ["matched-repository"]},
                }
            ),
            encoding="utf-8",
        )
        link = self.profiles / "linked"
        if os.name == "nt":
            powershell = shutil.which("powershell") or shutil.which("pwsh")
            if not powershell:
                self.skipTest("PowerShell is required to create a junction")
            link_arg = str(link).replace("'", "''")
            outside_arg = str(outside).replace("'", "''")
            completed = subprocess.run(
                [
                    powershell,
                    "-NoProfile",
                    "-Command",
                    f"New-Item -ItemType Junction -Path '{link_arg}' -Target '{outside_arg}' | Out-Null",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        else:
            link.symlink_to(outside, target_is_directory=True)
        project = self.root / "matched-repository"
        project.mkdir()

        result = self.run_resolver("--cwd", str(project))

        self.assertEqual(result.returncode, 2)
        self.assertIn("inside the profiles directory", result.stderr)


class ProjectProfileConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.home = self.root / "home"
        self.profiles_root = self.root / "private-profiles"
        profile = self.profiles_root / "profiles" / "configured"
        profile.mkdir(parents=True)
        (profile / "project.json").write_text(
            json.dumps({"id": "configured"}), encoding="utf-8"
        )
        self.environment = {
            **os.environ,
            "HOME": str(self.home),
            "USERPROFILE": str(self.home),
        }
        self.environment.pop("RUMO_SKILL_PROFILES_REPO", None)
        self.environment.pop("RUMO_PROJECT_PROFILE", None)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_persisted_profiles_repository_is_used_by_resolver(self) -> None:
        configured = subprocess.run(
            [
                sys.executable,
                str(PROFILE_CONFIG),
                "--profiles-repo",
                str(self.profiles_root),
            ],
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )
        resolved = subprocess.run(
            [sys.executable, str(RESOLVER), "--profile", "configured"],
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(configured.returncode, 0, configured.stderr)
        self.assertEqual(resolved.returncode, 0, resolved.stderr)
        payload = json.loads(resolved.stdout)
        self.assertEqual(Path(payload["profiles_root"]), self.profiles_root.resolve())
        config = json.loads(
            (self.home / ".rumo-engineering-skills" / "config.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(Path(config["profiles_repo"]), self.profiles_root.resolve())

    def test_corrupt_persisted_configuration_fails_without_fallback(self) -> None:
        config = self.home / ".rumo-engineering-skills" / "config.json"
        config.parent.mkdir(parents=True)
        config.write_text("{broken\n", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(RESOLVER), "--profile", "configured"],
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("configuration is invalid", result.stderr)

    def test_explicit_profiles_root_takes_precedence_over_persisted_config(self) -> None:
        persisted = subprocess.run(
            [
                sys.executable,
                str(PROFILE_CONFIG),
                "--profiles-repo",
                str(self.profiles_root),
            ],
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )
        explicit_root = self.root / "explicit-profiles"
        explicit_profile = explicit_root / "profiles" / "explicit"
        explicit_profile.mkdir(parents=True)
        (explicit_profile / "project.json").write_text(
            json.dumps({"id": "explicit"}), encoding="utf-8"
        )

        result = subprocess.run(
            [
                sys.executable,
                str(RESOLVER),
                "--profiles-root",
                str(explicit_root),
                "--profile",
                "explicit",
            ],
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(persisted.returncode, 0, persisted.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            Path(json.loads(result.stdout)["profiles_root"]), explicit_root.resolve()
        )


class ProjectProfileInitializerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name) / "profiles root with spaces"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_initializer(self, profile_id: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(INITIALIZER),
                "--profiles-root",
                str(self.root),
                "--profile",
                profile_id,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_creates_valid_empty_profile_without_existing_project(self) -> None:
        result = self.run_initializer("demo_01")

        self.assertEqual(result.returncode, 0, result.stderr)
        profile = self.root / "profiles" / "demo_01"
        expected = {
            "project.json",
            "frontend.json",
            "backend.json",
            "runtime.json",
            "data.json",
            "documents.json",
            "credentials.example.env",
            "README.md",
        }
        self.assertEqual({path.name for path in profile.iterdir() if path.is_file()}, expected)
        self.assertTrue((profile / "references").is_dir())
        project = json.loads((profile / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(project["id"], "demo_01")
        self.assertEqual(project["repositories"], [])

        validation = subprocess.run(
            [sys.executable, str(VALIDATOR), "--profiles-root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(validation.returncode, 0, validation.stderr)

        resolution = subprocess.run(
            [
                sys.executable,
                str(RESOLVER),
                "--profiles-root",
                str(self.root),
                "--profile",
                "demo_01",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(resolution.returncode, 0, resolution.stderr)
        self.assertEqual(json.loads(resolution.stdout)["profile_id"], "demo_01")

    def test_refuses_to_overwrite_existing_profile(self) -> None:
        first = self.run_initializer("demo-project")
        project_path = self.root / "profiles" / "demo-project" / "project.json"
        original = project_path.read_text(encoding="utf-8")

        second = self.run_initializer("demo-project")

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 2)
        self.assertIn("Profile already exists", second.stderr)
        self.assertEqual(project_path.read_text(encoding="utf-8"), original)

    def test_rejects_unsafe_profile_id(self) -> None:
        result = self.run_initializer("../demo")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Profile id must contain", result.stderr)
        self.assertFalse((self.root / "profiles").exists())

    def test_generated_files_contain_no_credential_values(self) -> None:
        result = self.run_initializer("empty-project")

        self.assertEqual(result.returncode, 0, result.stderr)
        content = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (self.root / "profiles" / "empty-project").iterdir()
            if path.is_file()
        )
        self.assertNotIn("test-secret-marker", content)
        for line in (self.root / "profiles" / "empty-project" / "credentials.example.env").read_text(
            encoding="utf-8"
        ).splitlines():
            if line and not line.startswith("#"):
                self.assertTrue(line.endswith("="), line)

    def test_validator_rejects_plaintext_secret_field(self) -> None:
        result = self.run_initializer("unsafe-project")
        runtime_path = self.root / "profiles" / "unsafe-project" / "runtime.json"
        runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
        runtime["api_token"] = "not-a-real-secret"
        runtime_path.write_text(json.dumps(runtime), encoding="utf-8")

        validation = subprocess.run(
            [sys.executable, str(VALIDATOR), "--profiles-root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("possible plaintext secret", validation.stderr)

    def test_validator_rejects_tracked_credential_file(self) -> None:
        result = self.run_initializer("tracked-project")
        credential = self.root / "profiles" / "tracked-project" / "credentials.md"
        credential.write_text("", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.root), "init", "--quiet"], check=True)
        subprocess.run(["git", "-C", str(self.root), "add", "profiles/tracked-project/credentials.md"], check=True)

        validation = subprocess.run(
            [sys.executable, str(VALIDATOR), "--profiles-root", str(self.root)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(validation.returncode, 1)
        self.assertIn("plaintext credential file must remain untracked", validation.stderr)


if __name__ == "__main__":
    unittest.main()
