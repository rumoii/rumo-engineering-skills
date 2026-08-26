from __future__ import annotations

import json
from pathlib import Path
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
