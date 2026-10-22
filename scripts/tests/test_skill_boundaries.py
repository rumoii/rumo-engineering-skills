from __future__ import annotations

import re
import unittest
from pathlib import Path

from scripts.verify_skills import parse_frontmatter


REPO_ROOT = Path(__file__).resolve().parents[2]
BOUNDARIES = (
    (
        "rumo-review",
        "rumo-verify",
        r"(?:pre-handoff|before handoff).*checks|checks.*(?:handoff|ready)",
        r"code review|review",
    ),
    (
        "rumo-plan",
        "rumo-clarify",
        r"unclear.*(?:goal|requirement)|(?:goal|requirement).*unclear",
        r"spec|task breakdown|plan",
    ),
    (
        "rumo-test",
        "rumo-verify",
        r"(?:exact|finished).*(?:change|diff)|(?:checks|commands).*actually run",
        r"(?:test|evidence).*planning|planning.*(?:test|evidence)",
    ),
    (
        "rumo-remote-ops",
        "rumo-database-change-safety",
        r"database.*writes?",
        r"(?:remote|SSH|host).*(?:change|query)",
    ),
    (
        "rumo-debug",
        "rumo-database-change-safety",
        r"(?:write-capable|persistent).*database|database.*writes?",
        r"read-only.*(?:diagnosis|investigation)",
    ),
    (
        "rumo-filesystem-safety",
        "rumo-database-change-safety",
        r"database.*(?:cleanup|data)",
        r"(?:files?|directories).*(?:delet|clean)",
    ),
    (
        "rumo-debug",
        "rumo-test",
        r"(?:plan|writ).*tests?",
        r"root cause|existing defect",
    ),
)

# Each merged skill keeps one trigger phrase per mode in its description,
# because clients pick skills from the description alone.
MODE_TRIGGERS = {
    "rumo-plan": (r"task breakdown", r"decision record|ADR", r"executing an agreed plan"),
    "rumo-test": (r"existing tests are enough", r"test-driven", r"high-assurance"),
    "rumo-verify": (r"before claiming work is done", r"CI check|static verifier"),
    "rumo-review": (r"read-only code review", r"review-fix", r"simplification audit", r"review feedback from someone else"),
    "rumo-interface": (r"HTTP", r"event|queue message", r"configuration field"),
    "rumo-remote-ops": (r"remote Linux host", r"systemd|Docker Compose", r"backups? and restores?", r"deployment of selected application artifacts"),
    "rumo-debug": (r"stay read-only unless the request also asks for the fix",),
    "rumo-agent-collaboration": (r"external CLI review, also load rumo-review",),
}

# Rules that keep rumo-clarify light; each must stay in the description or body.
CLARIFY_DESCRIPTION_RULES = (
    r"Do not use when the request is already specific",
    r"for pure questions",
    r"for reviews",
    r"Group.*questions",
    r"newly exposed.*decisions",
)
CLARIFY_BODY_RULES = (
    r"Asking about a clear request is a failure",
    r"At most five numbered questions",
    r"recommended answer",
    r"accepts only the recommendations shown in this round",
    r"Critical.*do not default it",
    r"Follow up only when an earlier answer exposes a consequential decision",
    r"Do not repeat settled questions",
    r"end on the questions, not on a completion report",
    r"Answers to clarifying questions do not widen what the agent may do",
)

# The high-assurance gate fires without being named, but never widens authorization.
HIGH_ASSURANCE_BODY_RULES = (
    r"Apply this risk gate on your own",
    r"\*\*Enter directly\*\* when the change alters monetary calculations, authentication or authorization decisions, database migrations, or irreversible behavior",
    r"\*\*Rate first\*\* when it touches durable data, concurrency, or public interfaces, or when the risk is unclear",
    r"Review-only, read-only diagnosis, and evidence-plan requests keep their own boundaries",
    r"Spec approval authorizes implementation and local checks only",
)
HIGH_ASSURANCE_REFERENCE_RULES = (
    r"Entry follows the risk gate in SKILL\.md",
    r"already approved covers the whole task, reuse it",
    r"Get approval again only for scope or key decisions it does not cover",
    r"Do not let this workflow widen the user's authorization",
)
RISK_GATE_ENTRIES = (
    "rumo-coding-guidelines",
    "rumo-interface",
    "rumo-lifecycle-safety",
    "rumo-database-change-safety",
)


def read_description(path: Path) -> str:
    errors: list[str] = []
    fields = parse_frontmatter(path, path.read_text(encoding="utf-8"), errors)
    if errors:
        raise AssertionError("; ".join(errors))
    description = fields.get("description", "")
    if not description:
        raise AssertionError(f"{path}: missing frontmatter description")
    return description


def has_boundary(description: str, counterpart: str, scene_pattern: str) -> bool:
    if re.search(rf"(?<![\w-]){re.escape(counterpart)}(?![\w-])", description):
        return True
    for sentence in re.split(r"[.!?]\s*", description):
        if re.search(r"\bdo not (?:use|trigger|invoke)\b|\buse\b.+\binstead\b", sentence, re.I):
            if re.search(scene_pattern, sentence, re.I):
                return True
    return False


class SkillBoundariesTest(unittest.TestCase):
    def test_descriptions_state_pair_boundaries(self) -> None:
        for first, second, first_scene, second_scene in BOUNDARIES:
            with self.subTest(pair=f"{first} <-> {second}"):
                first_description = read_description(REPO_ROOT / "skills" / first / "SKILL.md")
                second_description = read_description(REPO_ROOT / "skills" / second / "SKILL.md")
                self.assertTrue(
                    has_boundary(first_description, second, first_scene)
                    or has_boundary(second_description, first, second_scene),
                    f"{first} <-> {second}: descriptions lack a pair-specific exclusion "
                    "or redirect (Do not use / Use ... instead), or an explicit "
                    "reference to the counterpart skill; add the confirmed boundary "
                    "to at least one frontmatter description.",
                )

    def test_failing_pull_request_checks_go_to_git_commit(self) -> None:
        # rumo-verify also owns "diagnosing a CI check", so it must hand an open
        # pull request's failing checks to rumo-git-commit and its pr-checks rules.
        verify = read_description(REPO_ROOT / "skills" / "rumo-verify" / "SKILL.md")
        self.assertRegex(verify, r"failing checks on an open pull request, use rumo-git-commit instead")
        commit = read_description(REPO_ROOT / "skills" / "rumo-git-commit" / "SKILL.md")
        self.assertRegex(commit, r"watch or fix the CI checks of an open pull request")

    def test_merged_skill_descriptions_cover_every_mode(self) -> None:
        for skill, patterns in MODE_TRIGGERS.items():
            description = read_description(REPO_ROOT / "skills" / skill / "SKILL.md")
            for pattern in patterns:
                with self.subTest(skill=skill, mode=pattern):
                    self.assertRegex(description, re.compile(pattern, re.I))

    def test_clarify_stays_light(self) -> None:
        path = REPO_ROOT / "skills" / "rumo-clarify" / "SKILL.md"
        description = read_description(path)
        body = path.read_text(encoding="utf-8").split("\n---\n", 1)[1]
        for pattern in CLARIFY_DESCRIPTION_RULES:
            with self.subTest(description_rule=pattern):
                self.assertRegex(description, re.compile(pattern, re.I))
        for pattern in CLARIFY_BODY_RULES:
            with self.subTest(body_rule=pattern):
                self.assertRegex(body, re.compile(pattern, re.I))

    def test_high_assurance_gate_is_automatic_but_bounded(self) -> None:
        skill = REPO_ROOT / "skills" / "rumo-test" / "SKILL.md"
        description = read_description(skill)
        self.assertRegex(description, r"unprompted")
        self.assertNotRegex(description, r"with an approved spec")
        body = skill.read_text(encoding="utf-8").split("\n---\n", 1)[1]
        for pattern in HIGH_ASSURANCE_BODY_RULES:
            with self.subTest(body_rule=pattern):
                self.assertRegex(body, pattern)
        reference = (REPO_ROOT / "skills" / "rumo-test" / "references" / "high-assurance.md").read_text(encoding="utf-8")
        for pattern in HIGH_ASSURANCE_REFERENCE_RULES:
            with self.subTest(reference_rule=pattern):
                self.assertRegex(reference, pattern)
        self.assertNotIn("**High:** money, authentication", reference)
        self.assertNotIn("Create one repository-native entry point", reference)
        self.assertNotIn("a user request for proof enter directly", reference)
        for skill_name in RISK_GATE_ENTRIES:
            with self.subTest(entry=skill_name):
                text = (REPO_ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                self.assertRegex(text, r"high-assurance risk gate[^.]*`rumo-test`|`rumo-test`[^.]*high-assurance risk gate")

    def test_reasoning_loops_have_no_default_round_limit(self) -> None:
        paths = (
            "skills/rumo-debug/SKILL.md",
            "skills/rumo-review/references/loop.md",
            "skills/rumo-test/references/high-assurance.md",
        )
        for relative in paths:
            with self.subTest(path=relative):
                text = (REPO_ROOT / relative).read_text(encoding="utf-8")
                for removed in ("After three hypotheses", "after two fix attempts", "five cycles have run", "Allow at most two rounds"):
                    self.assertNotIn(removed, text)

    def test_accepts_counterpart_or_pair_specific_exclusion(self) -> None:
        self.assertTrue(has_boundary("Use rumo-verify instead.", "rumo-verify", "unused"))
        self.assertTrue(has_boundary("Do not use to run pre-handoff checks.", "rumo-verify", BOUNDARIES[0][2]))
        self.assertTrue(has_boundary("Use exact diff verification instead.", "rumo-verify", BOUNDARIES[2][2]))

    def test_rejects_missing_boundary_or_unrelated_exclusion(self) -> None:
        for description in (
            "Use for ordinary code reviews.",
            "Do not use for deleting files. Supports pre-handoff checks.",
        ):
            with self.subTest(description=description):
                self.assertFalse(has_boundary(description, "rumo-verify", BOUNDARIES[0][2]))


if __name__ == "__main__":
    unittest.main()
