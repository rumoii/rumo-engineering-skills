from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import daily_report


class DailyReportScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.codex = Path(self.temp.name) / "codex"
        self.reports = Path(self.temp.name) / "reports"
        self.previous = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(self.codex)
        with redirect_stdout(io.StringIO()):
            daily_report.configure(str(self.reports))

    def tearDown(self) -> None:
        if self.previous is None:
            os.environ.pop("CODEX_HOME", None)
        else:
            os.environ["CODEX_HOME"] = self.previous
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


if __name__ == "__main__":
    unittest.main()


