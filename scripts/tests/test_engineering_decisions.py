from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "rumo-plan"
    / "scripts"
    / "verify_decisions.py"
)
SPEC = importlib.util.spec_from_file_location("verify_decisions", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_repository = MODULE.validate_repository
SUPERSEDED_STATUS_ERROR = (
    "superseded status must be 'Status: superseded - [<title>](<relative path>)' linking the replacing record"
)
SUPERSEDED_TARGET_ERROR = "superseded record must link a proposed, implemented, or superseded record"


IMPLEMENTED_NOTE = """# Decision: Example decision

Status: implemented

## Problem

The repository needs one durable choice.

## Decision

Keep the decision beside its owning source.

## Alternatives considered

**Central storage.** Rejected because it would lose branch ownership.

## Consequences

Changes carry their rationale in the same repository.

## Verification

Validate the record with the repository gate.

## Rollback

Remove the gate only after preserving existing records.
"""


class EngineeringDecisionValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        decisions = self.repo_root / "docs" / "decisions"
        (decisions / "implemented").mkdir(parents=True)
        (decisions / "README.md").write_text("# Decisions\n", encoding="utf-8")
        self.note_path = decisions / "implemented" / "2026-08-18-example-decision.md"
        self.note_path.write_text(IMPLEMENTED_NOTE, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def assert_error_contains(self, expected: str) -> None:
        errors = validate_repository(self.repo_root)
        self.assertTrue(any(expected in error for error in errors), errors)

    def write_superseded_record(self, status_line: str, name: str = "2026-08-17-previous-decision.md") -> Path:
        directory = self.note_path.parent.parent / "superseded"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text(IMPLEMENTED_NOTE.replace("Status: implemented", status_line), encoding="utf-8")
        return path

    def test_accepts_valid_implemented_record(self) -> None:
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_accepts_valid_proposed_record(self) -> None:
        proposed = self.repo_root / "docs" / "decisions" / "proposed"
        proposed.mkdir()
        proposed_note = proposed / self.note_path.name
        self.note_path.rename(proposed_note)
        proposed_note.write_text(
            IMPLEMENTED_NOTE.replace("Status: implemented", "Status: proposed")
            .replace("## Decision", "## Proposal")
            .replace("## Consequences", "## Risks"),
            encoding="utf-8",
        )
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_accepts_valid_rejected_record(self) -> None:
        rejected = self.repo_root / "docs" / "decisions" / "rejected"
        rejected.mkdir()
        rejected_note = rejected / self.note_path.name
        self.note_path.rename(rejected_note)
        rejected_note.write_text(
            IMPLEMENTED_NOTE.replace(
                "Status: implemented",
                "Status: rejected - deployment cost exceeds the benefit",
            )
            .replace("## Decision", "## Proposal")
            .replace("## Consequences", "## Risks"),
            encoding="utf-8",
        )
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_accepts_valid_superseded_record(self) -> None:
        proposed = self.note_path.parent.parent / "proposed"
        proposed.mkdir()
        proposed_note = proposed / "2026-12-01-new-topic.md"
        proposed_note.write_text(
            IMPLEMENTED_NOTE.replace("Status: implemented", "Status: proposed")
            .replace("## Decision", "## Proposal")
            .replace("## Consequences", "## Risks"),
            encoding="utf-8",
        )
        for replacement in (self.note_path, proposed_note):
            with self.subTest(lifecycle=replacement.parent.name):
                self.write_superseded_record(
                    f"Status: superseded - [replacement](../{replacement.parent.name}/{replacement.name})"
                )
                self.assertEqual(validate_repository(self.repo_root), [])

    def test_accepts_superseded_record_under_linked_decisions_root(self) -> None:
        decisions = self.note_path.parent.parent
        adr = self.repo_root / "adr"
        decisions.rename(adr)
        try:
            if os.name == "nt":
                from _winapi import CreateJunction

                CreateJunction(str(adr), str(decisions))
            else:
                decisions.symlink_to(adr, target_is_directory=True)
        except (ImportError, NotImplementedError, OSError) as exc:
            self.skipTest(f"Cannot create a directory link for docs/decisions: {exc}")

        self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{self.note_path.name})"
        )
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_superseded_status_without_relative_link(self) -> None:
        for status in (
            "Status: superseded",
            "Status: superseded [replacement](../implemented/record.md)",
            "Status: superseded - [replacement](https://example.com/record.md)",
        ):
            with self.subTest(status=status):
                self.write_superseded_record(status)
                self.assert_error_contains(SUPERSEDED_STATUS_ERROR)

    def test_rejects_superseded_chain_ending_at_rejected_record(self) -> None:
        rejected = self.note_path.parent.parent / "rejected"
        rejected.mkdir()
        rejected_note = rejected / "2026-08-19-declined-decision.md"
        rejected_note.write_text(
            IMPLEMENTED_NOTE.replace("Status: implemented", "Status: rejected - too costly")
            .replace("## Decision", "## Proposal")
            .replace("## Consequences", "## Risks"),
            encoding="utf-8",
        )
        intermediate = self.write_superseded_record(
            f"Status: superseded - [replacement](../rejected/{rejected_note.name})"
        )
        origin = self.write_superseded_record(
            f"Status: superseded - [replacement]({intermediate.name})",
            name="2026-08-16-earlier-decision.md",
        )
        self.assertCountEqual(
            validate_repository(self.repo_root),
            [
                f"{origin.relative_to(self.repo_root).as_posix()}: "
                "superseded chain must end at a proposed or implemented record "
                f"(reached {rejected_note.relative_to(self.repo_root).as_posix()})",
                f"{intermediate.relative_to(self.repo_root).as_posix()}: {SUPERSEDED_TARGET_ERROR}",
            ],
        )

    def test_accepts_superseded_link_to_superseded_record(self) -> None:
        superseded_note = self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{self.note_path.name})",
            name="2026-08-16-earlier-decision.md",
        )
        self.write_superseded_record(f"Status: superseded - [replacement]({superseded_note.name})")
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_accepts_superseded_chain_with_relative_path_and_fragment(self) -> None:
        intermediate = self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{self.note_path.name})"
        )
        self.write_superseded_record(
            f"Status: superseded - [replacement](../superseded/{intermediate.name}#decision)",
            name="2026-08-16-earlier-decision.md",
        )
        self.assertEqual(validate_repository(self.repo_root), [])

    def test_rejects_mutual_superseded_links(self) -> None:
        first_name = "2026-08-16-earlier-decision.md"
        second = self.write_superseded_record(f"Status: superseded - [replacement]({first_name})")
        first = self.write_superseded_record(
            f"Status: superseded - [replacement]({second.name})", name=first_name
        )
        self.assertCountEqual(
            validate_repository(self.repo_root),
            [
                f"{label}: superseded chain loops back to {label}"
                for label in (record.relative_to(self.repo_root).as_posix() for record in (first, second))
            ],
        )

    def test_rejects_superseded_link_to_itself(self) -> None:
        name = "2026-08-16-earlier-decision.md"
        path = self.write_superseded_record(
            f"Status: superseded - [replacement](../superseded/{name})", name=name
        )
        label = path.relative_to(self.repo_root).as_posix()
        self.assertEqual(validate_repository(self.repo_root), [f"{label}: superseded chain loops back to {label}"])

    def test_reports_malformed_intermediate_superseded_status_only_at_its_source(self) -> None:
        intermediate = self.write_superseded_record("Status: superseded")
        self.write_superseded_record(
            f"Status: superseded - [replacement]({intermediate.name})",
            name="2026-08-16-earlier-decision.md",
        )
        label = intermediate.relative_to(self.repo_root).as_posix()
        self.assertEqual(validate_repository(self.repo_root), [f"{label}: {SUPERSEDED_STATUS_ERROR}"])

    def test_rejects_superseded_chain_ending_at_directory(self) -> None:
        directory = self.note_path.parent / "2026-08-19-not-a-file.md"
        directory.mkdir()
        intermediate = self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{directory.name})"
        )
        origin = self.write_superseded_record(
            f"Status: superseded - [replacement]({intermediate.name})",
            name="2026-08-16-earlier-decision.md",
        )
        target_label = directory.relative_to(self.repo_root).as_posix()
        self.assertCountEqual(
            validate_repository(self.repo_root),
            [
                f"{target_label}: only Markdown decision files are allowed",
                f"{origin.relative_to(self.repo_root).as_posix()}: "
                "superseded chain must end at a proposed or implemented record "
                f"(reached {target_label})",
                f"{intermediate.relative_to(self.repo_root).as_posix()}: {SUPERSEDED_TARGET_ERROR}",
            ],
        )

    def test_rejects_superseded_chain_ending_at_non_record_file(self) -> None:
        target = self.note_path.parent / "notes.md"
        target.write_text("# Notes\n", encoding="utf-8")
        intermediate = self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{target.name})"
        )
        origin = self.write_superseded_record(
            f"Status: superseded - [replacement]({intermediate.name})",
            name="2026-08-16-earlier-decision.md",
        )
        target_label = target.relative_to(self.repo_root).as_posix()
        self.assertCountEqual(
            validate_repository(self.repo_root),
            [
                f"{target_label}: filename must be yyyy-mm-dd-lowercase-topic.md",
                f"{target_label}: decision record is incomplete",
                f"{origin.relative_to(self.repo_root).as_posix()}: "
                "superseded chain must end at a proposed or implemented record "
                f"(reached {target_label})",
                f"{intermediate.relative_to(self.repo_root).as_posix()}: {SUPERSEDED_TARGET_ERROR}",
            ],
        )

    def test_rejects_broken_superseded_link(self) -> None:
        target = "../implemented/2026-12-01-missing-decision.md"
        path = self.write_superseded_record(f"Status: superseded - [replacement]({target})")
        self.assertEqual(
            validate_repository(self.repo_root),
            [f"{path.relative_to(self.repo_root).as_posix()}: broken relative link: {target}"],
        )

    def test_rejects_proposal_and_risks_in_superseded_record(self) -> None:
        path = self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{self.note_path.name})"
        )
        path.write_text(
            path.read_text(encoding="utf-8").replace("## Decision", "## Proposal").replace("## Consequences", "## Risks"),
            encoding="utf-8",
        )
        self.assert_error_contains("missing sections: Decision, Consequences")
        self.assert_error_contains("sections do not match superseded: Proposal, Risks")

    def test_rejects_duplicate_superseded_record(self) -> None:
        self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{self.note_path.name})",
            name=self.note_path.name,
        )
        self.assert_error_contains("duplicate lifecycle record")

    def test_lists_all_allowed_lifecycle_directories(self) -> None:
        (self.note_path.parent.parent / "unknown").mkdir()
        self.assert_error_contains("only proposed, implemented, rejected, and superseded directories are allowed")

    def test_reports_superseded_lifecycle_file_as_disallowed(self) -> None:
        (self.note_path.parent.parent / "superseded").write_text("not a directory\n", encoding="utf-8")
        self.assertEqual(
            validate_repository(self.repo_root),
            [
                "docs/decisions/superseded: "
                "only proposed, implemented, rejected, and superseded directories are allowed"
            ],
        )

    def test_main_counts_superseded_record_under_explicit_root(self) -> None:
        self.write_superseded_record(
            f"Status: superseded - [replacement](../implemented/{self.note_path.name})"
        )
        output = StringIO()
        errors = StringIO()
        with patch.object(sys, "argv", [str(SCRIPT_PATH), "--root", str(self.repo_root)]):
            with redirect_stdout(output), redirect_stderr(errors):
                exit_code = MODULE.main()
        self.assertEqual(exit_code, 0, errors.getvalue())
        self.assertEqual(output.getvalue(), "Decision validation passed: 2 record(s)\n")
        self.assertEqual(errors.getvalue(), "")

    def test_rejects_status_directory_mismatch(self) -> None:
        self.note_path.write_text(
            IMPLEMENTED_NOTE.replace("Status: implemented", "Status: proposed"),
            encoding="utf-8",
        )
        self.assert_error_contains("status must match the implemented directory")

    def test_rejects_missing_section(self) -> None:
        self.note_path.write_text(
            IMPLEMENTED_NOTE.replace("## Rollback\n\nRemove the gate only after preserving existing records.\n", ""),
            encoding="utf-8",
        )
        self.assert_error_contains("missing sections: Rollback")

    def test_rejects_broken_relative_link(self) -> None:
        self.note_path.write_text(
            IMPLEMENTED_NOTE.replace(
                "Keep the decision beside its owning source.",
                "Keep the [decision](../missing.md) beside its owning source.",
            ),
            encoding="utf-8",
        )
        self.assert_error_contains("broken relative link")

    def test_rejects_personal_path(self) -> None:
        self.note_path.write_text(
            IMPLEMENTED_NOTE.replace(
                "Keep the decision beside its owning source.",
                "Keep it under /Users/example/workspace/project.",
            ),
            encoding="utf-8",
        )
        self.assert_error_contains("personal absolute path")

    def test_rejects_duplicate_lifecycle_record(self) -> None:
        proposed = self.repo_root / "docs" / "decisions" / "proposed"
        proposed.mkdir()
        (proposed / self.note_path.name).write_text(
            IMPLEMENTED_NOTE.replace("Status: implemented", "Status: proposed")
            .replace("## Decision", "## Proposal")
            .replace("## Consequences", "## Risks"),
            encoding="utf-8",
        )
        self.assert_error_contains("duplicate lifecycle record")


if __name__ == "__main__":
    unittest.main()
