import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = (ROOT / "srs-function-document" / "SKILL.md").read_text(encoding="utf-8")
CASES = json.loads(
    (ROOT / "srs-function-document" / "evals" / "contract-cases.json").read_text(encoding="utf-8")
)["cases"]
BY_ID = {case["id"]: case for case in CASES}


class SrsFunctionDocumentTests(unittest.TestCase):
    def test_unknown_maximum_stays_unresolved(self):
        case = BY_ID["unknown-maximum-preserved"]
        self.assertIn("Keep UNKNOWN values explicitly unresolved", SKILL)
        self.assertTrue(any("remains explicitly UNKNOWN" in item for item in case["pass_if"]))
        self.assertTrue(any("No numeric maximum" in item for item in case["pass_if"]))

    def test_current_system_evidence_is_not_a_target_requirement(self):
        case = BY_ID["current-system-not-promoted"]
        self.assertIn("Do not turn CURRENT_SYSTEM evidence into a target requirement.", SKILL)
        self.assertTrue(any("does not make 255 characters a target" in item for item in case["pass_if"]))

    def test_confirmed_business_rule_has_traceability(self):
        case = BY_ID["confirmed-rule-traceability"]
        self.assertIn("Business Rule → Functional Requirement → acceptance criteria or behavior", SKILL)
        self.assertTrue(any("traces to BR-053" in item for item in case["pass_if"]))

    def test_concurrency_outcome_does_not_choose_architecture(self):
        case = BY_ID["no-technical-architecture-invention"]
        self.assertIn("locking, transaction implementation", SKILL)
        self.assertTrue(any("Engineering decision" in item for item in case["pass_if"]))
        self.assertTrue(any("Redis lock" in item for item in case["fail_if"]))

    def test_srs_generation_does_not_approve_the_baseline(self):
        case = BY_ID["human-gate-separate"]
        self.assertIn("Do not set or imply APPROVED_FOR_ENGINEERING.", SKILL)
        self.assertTrue(any("Workflow approval remains unchanged" in item for item in case["pass_if"]))

    def test_update_mode_preserves_unaffected_confirmed_content(self):
        case = BY_ID["unrelated-update-preserves-confirmed-rule"]
        self.assertIn("Preserve every confirmed, unaffected requirement and its identifiers.", SKILL)
        self.assertTrue(any("BR-031 behavior and its traceability remain" in item for item in case["pass_if"]))

    def test_cr001_regression_case_covers_all_required_semantics(self):
        expected = {
            "clinic-staff-actor",
            "appointment-is-not-visit",
            "pet-veterinarian-start-duration-reason",
            "future-start-asia-ho-chi-minh",
            "duration-greater-than-zero",
            "maximum-duration-unknown",
            "same-veterinarian-scheduled-conflict",
            "half-open-start-end-interval",
            "touching-intervals-allowed",
            "reschedule-excludes-itself",
            "scheduled-cancelled-completed-states",
            "create-starts-scheduled",
            "only-scheduled-mutable-actionable",
            "cancel-releases-slot",
            "complete-creates-exactly-one-visit",
            "no-hard-delete",
            "list-filter-sort-pagination",
            "no-pet-overlap-rule",
            "concurrent-business-outcome-only",
        }
        self.assertEqual(set(BY_ID["cr001-semantic-regression"]["covers"]), expected)


if __name__ == "__main__":
    unittest.main()
