from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILLS = Path(__file__).resolve().parents[2] / "skills"
CALVER = SKILLS / "rumo-git-commit" / "scripts" / "calver.py"
DEPLOY_PLAN = SKILLS / "rumo-remote-ops" / "scripts" / "incremental_deploy_plan.py"
FRONTEND_PROBE = SKILLS / "rumo-frontend" / "scripts" / "probe_frontend_ui.py"

SPEC = importlib.util.spec_from_file_location("calver", CALVER)
assert SPEC and SPEC.loader
CALVER_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CALVER_MODULE)


def run_script(script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *arguments], capture_output=True, text=True, check=False
    )


class CalverTests(unittest.TestCase):
    def test_no_calver_tags_start_at_zero(self) -> None:
        self.assertEqual(CALVER_MODULE.find_max_micro([]), 0)
        self.assertEqual(CALVER_MODULE.find_max_micro(["v0.3.1", "release-1"]), 0)

    def test_micro_is_global_maximum_across_weeks(self) -> None:
        tags = ["26.40.7", "26.41.12", "26.42.3", "v26.42.99"]

        self.assertEqual(CALVER_MODULE.find_max_micro(tags), 12)


class IncrementalDeployPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.profile = self.root / "profile"
        self.profile.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_plan_hashes_artifacts_without_remote_writes(self) -> None:
        artifact = self.root / "app.jar"
        artifact.write_bytes(b"artifact-bytes")
        result = run_script(
            DEPLOY_PLAN,
            "--profile", str(self.profile),
            "--artifact", str(artifact),
            "--host", "example.test",
            "--destination", "/srv/app",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["mode"], "dry-run")
        self.assertIs(plan["executes_remote_writes"], False)
        self.assertEqual(plan["artifacts"][0]["sha256"], hashlib.sha256(b"artifact-bytes").hexdigest())
        self.assertEqual(plan["artifacts"][0]["size"], len(b"artifact-bytes"))

    def test_missing_artifact_is_rejected(self) -> None:
        result = run_script(
            DEPLOY_PLAN,
            "--profile", str(self.profile),
            "--artifact", str(self.root / "missing.jar"),
            "--host", "example.test",
            "--destination", "/srv/app",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("artifact not found", result.stderr)


class FrontendProbeTests(unittest.TestCase):
    def test_inventory_skips_node_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            (repo / "package.json").write_text("{}", encoding="utf-8")
            (repo / "apps" / "web").mkdir(parents=True)
            (repo / "apps" / "web" / "package.json").write_text("{}", encoding="utf-8")
            (repo / "node_modules" / "dep").mkdir(parents=True)
            (repo / "node_modules" / "dep" / "package.json").write_text("{}", encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "pnpm-lock.yaml").write_text("", encoding="utf-8")

            result = run_script(FRONTEND_PROBE, "--repo", str(repo))

        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        manifests = [Path(path).as_posix() for path in inventory["manifests"]]
        self.assertEqual(sorted(manifests), ["apps/web/package.json", "package.json"])
        self.assertEqual(inventory["source_roots"], ["src", "apps"])
        self.assertEqual(inventory["lockfiles"], ["pnpm-lock.yaml"])


if __name__ == "__main__":
    unittest.main()
