from __future__ import annotations

import json
import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import daily_report


class DailyReportScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name) / "home"
        self.codex = Path(self.temp.name) / "codex"
        self.reports = Path(self.temp.name) / "reports"
        self.previous = {
            name: os.environ.get(name) for name in ("HOME", "USERPROFILE", "CODEX_HOME")
        }
        os.environ["HOME"] = os.environ["USERPROFILE"] = str(self.home)
        os.environ["CODEX_HOME"] = str(self.codex)
        with redirect_stdout(io.StringIO()):
            daily_report.configure(str(self.reports))

    def tearDown(self) -> None:
        for name, value in self.previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        self.temp.cleanup()

    def append(self, items: list[str], session: str, day: str) -> None:
        with redirect_stdout(io.StringIO()):
            daily_report.append_report(json.dumps(items, ensure_ascii=False), session, day)

    def test_continuous_numbering_and_deduplication(self) -> None:
        self.append(
            [
                "解决了第一个问题，原因是数据未同步，解决方案是补充同步处理。",
                "推进了性能测试工作，目前已完成接口准备。",
            ],
            "thread-a",
            "2026-08-27",
        )
        self.append(
            ["解决了第二个问题，原因是参数错误，解决方案是完成参数适配。"],
            "thread-b",
            "2026-08-27",
        )
        self.append(
            ["解决了第一个问题，原因是数据未同步，解决方案是补充同步处理。"],
            "thread-a",
            "2026-08-27",
        )
        content = (self.reports / "2026-08-27-日报.txt").read_text(encoding="utf-8")
        self.assertTrue(content.startswith("1.解决了第一个问题"))
        self.assertIn("2.推进了性能测试工作", content)
        self.assertIn("3.解决了第二个问题", content)
        self.assertEqual(content.count("第一个问题"), 1)

    def test_next_date_uses_new_file(self) -> None:
        self.append(["完成了当天工作。"], "thread-a", "2026-08-28")
        self.assertTrue((self.reports / "2026-08-28-日报.txt").exists())
        self.assertFalse((self.reports / "2026-08-27-日报.txt").exists())

    def test_same_text_is_allowed_on_another_date(self) -> None:
        item = "推进了例行检查工作，目前已完成当天检查。"
        self.append([item], "thread-a", "2026-08-27")
        self.append([item], "thread-b", "2026-08-28")
        self.assertIn(item, (self.reports / "2026-08-27-日报.txt").read_text(encoding="utf-8"))
        self.assertIn(item, (self.reports / "2026-08-28-日报.txt").read_text(encoding="utf-8"))

    def test_rejects_broken_existing_numbering(self) -> None:
        report = self.reports / "2026-08-27-日报.txt"
        report.write_text("1.第一项。\n3.第三项。\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "编号不连续"):
            self.append(["新的工作。"], "thread-a", "2026-08-27")
        self.assertEqual(report.read_text(encoding="utf-8"), "1.第一项。\n3.第三项。\n")

    def test_requires_explicit_replace_to_change_directory(self) -> None:
        replacement = Path(self.temp.name) / "replacement"
        with self.assertRaisesRegex(RuntimeError, "--replace"):
            daily_report.configure(str(replacement))
        with redirect_stdout(io.StringIO()):
            daily_report.configure(str(replacement), replace=True)
        configured = json.loads(daily_report.config_path().read_text(encoding="utf-8"))
        self.assertEqual(Path(configured["report_dir"]), replacement.resolve())

    def test_replaced_directory_has_an_independent_deduplication_scope(self) -> None:
        item = "完成了需要在两个目录分别记录的工作。"
        self.append([item], "thread-a", "2026-08-27")
        replacement = Path(self.temp.name) / "replacement"
        with redirect_stdout(io.StringIO()):
            daily_report.configure(str(replacement), replace=True)

        self.append([item], "thread-b", "2026-08-27")

        report = replacement / "2026-08-27-日报.txt"
        self.assertTrue(report.is_file())
        self.assertIn(item, report.read_text(encoding="utf-8"))

    def test_state_lives_outside_client_homes(self) -> None:
        self.assertEqual(
            daily_report.config_path(),
            self.home / ".rumo-engineering-skills" / "daily-report" / "config.json",
        )
        self.assertFalse(self.codex.exists())

    def test_migrates_legacy_codex_state_once(self) -> None:
        shutil.rmtree(daily_report.state_dir())
        legacy = self.codex / "rumo-daily-report"
        legacy.mkdir(parents=True)
        legacy_reports = Path(self.temp.name) / "legacy-reports"
        (legacy / "config.json").write_text(
            json.dumps({"report_dir": str(legacy_reports)}), encoding="utf-8"
        )
        (legacy / "state.json").write_text('{"marker": true}', encoding="utf-8")

        with redirect_stderr(io.StringIO()) as notice:
            daily_report.migrate_legacy_state()

        self.assertIn("config.json, state.json", notice.getvalue())
        self.assertEqual(daily_report.load_config(), legacy_reports)
        self.assertTrue((legacy / "config.json").is_file())

        (legacy / "config.json").write_text(
            json.dumps({"report_dir": str(self.reports)}), encoding="utf-8"
        )
        with redirect_stderr(io.StringIO()) as second_notice:
            daily_report.migrate_legacy_state()
        self.assertEqual(second_notice.getvalue(), "")
        self.assertEqual(daily_report.load_config(), legacy_reports)


if __name__ == "__main__":
    unittest.main()
