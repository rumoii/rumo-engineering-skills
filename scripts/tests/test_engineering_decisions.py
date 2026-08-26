from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "rumo-engineering-decision"
    / "scripts"
    / "verify_decisions.py"
)
SPEC = importlib.util.spec_from_file_location("verify_decisions", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {SCRIPT_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate_repository = MODULE.validate_repository


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
