from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.codex_behavior_cases import CASES, REGRESSION
from scripts.run_regression import arm_options, jobs, main, summarize


class PlanTest(unittest.TestCase):
    def test_regression_cases_exist(self) -> None:
        self.assertTrue(set(REGRESSION) <= set(CASES))

    def test_jobs_pair_both_arms_per_case_and_rep(self) -> None:
        planned = jobs("codex", ["withdraw-existing", "commit-prepare"], 2)
        self.assertEqual(len(planned), 8)
        self.assertEqual(planned[:2], [("candidate", 1, "withdraw-existing"), ("baseline", 1, "withdraw-existing")])

    def test_pi_skips_cases_that_edit_files(self) -> None:
        self.assertEqual({name for _, _, name in jobs("pi", list(REGRESSION), 1)}, {n for n in REGRESSION if CASES[n]["read_only"]})

    def test_without_baseline_reuses_the_candidate_without_skills(self) -> None:
        self.assertEqual(arm_options("baseline", Path("C:/snap"), "without"), ["--snapshot", str(Path("C:/snap")), "--without-skills"])
        self.assertEqual(arm_options("candidate", Path("C:/snap"), "without"), ["--snapshot", str(Path("C:/snap"))])
        self.assertNotIn("--without-skills", arm_options("baseline", Path("C:/snap"), "C:/old"))


class SummaryTest(unittest.TestCase):
    def test_counts_valid_invalid_and_not_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            planned = jobs("codex", ["withdraw-existing"], 2)
            for (arm, rep, name), status in zip(planned[:3], ("valid", "invalid", "valid")):
                case = out / f"codex-{arm}-{rep}-{name}" / name
                case.mkdir(parents=True)
                case.joinpath("result.json").write_text(json.dumps({
                    "evidence_status": status, "mechanical_checks": {"sample_unchanged": True},
                    "observed": {"messages": ["first", f"reply {arm} {rep}"]}}), encoding="utf-8")
            table, text = summarize(out, "codex", planned, {job: 0 for job in planned[:3]})
        self.assertEqual(table["withdraw-existing"]["candidate"], {"runs": 2, "valid": 2, "mechanical_pass": 2, "not_run": 0, "tokens": []})
        self.assertEqual(table["withdraw-existing"]["baseline"], {"runs": 1, "valid": 0, "mechanical_pass": 0, "not_run": 1, "tokens": []})
        self.assertIn("reply candidate 2", text)
        self.assertNotIn("first", text)
        self.assertIn(REGRESSION["withdraw-existing"], text)


class CliTest(unittest.TestCase):
    def test_output_inside_checkout_is_rejected(self) -> None:
        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "skills").mkdir()
            proc = subprocess.run([sys.executable, str(repo / "scripts" / "run_regression.py"), "--candidate", temp, "--baseline", "without",
                                   "--output-dir", str(repo / "regression-evidence")], capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("outside the source checkout", proc.stderr)
        self.assertFalse((repo / "regression-evidence").exists())

    def test_runs_every_job_through_the_codex_runner(self) -> None:
        calls = []

        def fake_invoke(command, log):
            calls.append(command)
            return 1

        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / "snap" / "skills").mkdir(parents=True)
            argv = ["run_regression.py", "--candidate", str(Path(temp) / "snap"), "--baseline", "without", "--reps", "1",
                    "--output-dir", str(Path(temp) / "out"), "--", "--timeout", "60"]
            with patch.object(sys, "argv", argv), patch("scripts.run_regression.invoke", side_effect=fake_invoke), \
                 contextlib.redirect_stdout(io.StringIO()):
                code = main()
            self.assertEqual(code, 0)
            self.assertEqual(len(calls), 2 * len(REGRESSION))
            self.assertTrue(all(c[1].endswith("run_codex_behavior.py") and c[-2:] == ["--timeout", "60"] for c in calls))
            self.assertTrue((Path(temp) / "out" / "summary.md").is_file())


if __name__ == "__main__":
    unittest.main()
