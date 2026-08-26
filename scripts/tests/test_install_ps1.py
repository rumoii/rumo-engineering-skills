from __future__ import annotations

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

            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            skill_names = sorted(
                path.name
                for path in (REPO_ROOT / "skills").iterdir()
                if path.is_dir() and path.name.startswith("rumo-")
            )
            self.assertEqual(len(skill_names), 27)
            for home in homes.values():
                for name in skill_names:
                    self.assertTrue(
                        os.path.samefile(
                            home / "skills" / name, REPO_ROOT / "skills" / name
                        ),
                        name,
                    )
                self.assertTrue((home / "skills" / "third-party-skill").is_dir())


if __name__ == "__main__":
    unittest.main()
