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
        semantic_contract = json.loads(
            (ROOT / "ba-workflow/evals/cr001-semantic-contract.json").read_text(encoding="utf-8")
        )
        full_case = semantic_contract["cases"]["cr001-semantic-regression"]
        self.assertEqual(set(BY_ID["cr001-semantic-regression"]["covers"]), set(full_case["check_ids"]))
        self.assertEqual(
            set(full_case["forbidden_ids"]),
            {
                "pet-context-entry-flow",
                "standalone-appointment-management-flow",
                "unsupported-screen-navigation",
                "api-shape",
                "database-schema",
                "locking-strategy",
                "transaction-strategy",
                "service-ownership",
            },
        )
        self.assertEqual(
            BY_ID["cr001-semantic-regression"]["artifact_evaluation"]["fixture"],
            "../../ba-workflow/evals/cr001-semantic-contract.json",
        )

    def test_srs_contract_requires_semantic_preservation_and_blocks_invention(self):
        self.assertIn("every CONFIRMED input semantic", SKILL)
        self.assertIn("navigation, entry points, screens, user flows", SKILL)
        self.assertIn("required, optional, nullable", (ROOT / "business-rule-extractor" / "SKILL.md").read_text(encoding="utf-8"))

    def test_cr001_fixture_drives_actual_artifact_evaluation(self):
        from tooling.lib import ba_semantic_evaluator

        business_rules = """BR-P1 Clinic Staff manages appointments.
BR-P2 Reason/Description is required and has length 1-255 characters.
BR-P3 Duration must be greater than 0; maximum Duration remains UNKNOWN.
BR-P4 States are Scheduled, Cancelled, Completed. Create starts Scheduled; only Scheduled can be edited, rescheduled, cancelled, or completed.
BR-P5 Cancellation releases the slot; there is no hard delete.
BR-P6 Completing a Scheduled appointment creates exactly one new Visit; an existing Visit is not reused.
"""
        srs = """When checking for scheduling conflicts while rescheduling an Appointment, exclude that Appointment from the conflict check.
Completing a Scheduled appointment creates exactly one new Visit.
An existing Visit shall not be linked or reused.
The maximum Duration remains UNKNOWN.
"""
        report = ba_semantic_evaluator.evaluate_artifacts(
            business_rules, srs, "srs-preservation-probe"
        )
        statuses = {(item["semantic_id"], item["artifact"]): item["status"] for item in report["results"]}
        self.assertEqual(statuses[("reschedule-excludes-itself", "srs")], "MATCH")
        self.assertEqual(statuses[("complete-exactly-one-new-visit", "srs")], "MATCH")
        self.assertEqual(statuses[("existing-visit-not-reused", "srs")], "MATCH")
        self.assertEqual(statuses[("maximum-duration-unknown", "srs")], "UNKNOWN_PRESERVED")

        missing = ba_semantic_evaluator.evaluate_artifacts(
            business_rules, "Only the maximum Duration remains UNKNOWN.", "srs-preservation-probe"
        )
        missing_statuses = {(item["semantic_id"], item["artifact"]): item["status"] for item in missing["results"]}
        self.assertEqual(missing_statuses[("reschedule-excludes-itself", "srs")], "MISSING_REQUIRED_BEHAVIOR")

        invented = ba_semantic_evaluator.evaluate_artifacts(
            business_rules,
            "Staff can create an appointment from the Pet profile.",
            "srs-invention-guard-probe",
        )
        self.assertIn("UNSUPPORTED_INVENTION", {item["status"] for item in invented["results"]})

        screen = ba_semantic_evaluator.evaluate_artifacts(
            business_rules,
            "## Thiết kế giao diện\n| Appointment Form | Enter Pet and time |",
            "srs-invention-guard-probe",
        )
        screen_statuses = {item["semantic_id"]: item["status"] for item in screen["results"]}
        self.assertEqual(screen_statuses["unsupported-screen-navigation"], "UNSUPPORTED_INVENTION")

        unresolved = ba_semantic_evaluator.evaluate_artifacts(
            business_rules,
            "Calendar view is out of scope. Database schema and API shape remain UNKNOWN.",
            "srs-invention-guard-probe",
        )
        self.assertTrue(unresolved["passed"])

    def test_business_rule_probe_rejects_optional_omitted_or_changed_description_bounds(self):
        from tooling.lib import ba_semantic_evaluator

        rules = """BR-P1 Clinic Staff manages appointments.
BR-P2 Reason/Description is required and has length 1-255 characters.
BR-P3 Duration must be greater than 0; maximum Duration remains UNKNOWN.
BR-P4 States are Scheduled, Cancelled, Completed. Create starts Scheduled; only Scheduled can be edited, rescheduled, cancelled, or completed.
BR-P5 Cancellation releases the slot; there is no hard delete.
BR-P6 Completing a Scheduled appointment creates exactly one new Visit; an existing Visit is not reused.
"""
        report = ba_semantic_evaluator.evaluate_artifacts(rules, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["description-required-1-255"], "MATCH")
        self.assertEqual(statuses["only-supplied-business-rules"], "MATCH")
        self.assertEqual(statuses["existing-visit-not-reused"], "MATCH")

        negative_delete = rules.replace("there is no hard delete", "an Appointment is not hard-deleted")
        report = ba_semantic_evaluator.evaluate_artifacts(negative_delete, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["no-hard-delete"], "MATCH")

        cannot_hard_delete = rules.replace("there is no hard delete", "an Appointment cannot be hard deleted")
        report = ba_semantic_evaluator.evaluate_artifacts(cannot_hard_delete, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["no-hard-delete"], "MATCH")

        optional = rules.replace("is required and has length 1-255", "is optional and has length 1-255")
        report = ba_semantic_evaluator.evaluate_artifacts(optional, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["description-required-1-255"], "CONTRADICTION")

        wrong_bounds = rules.replace("1-255", "1-200")
        report = ba_semantic_evaluator.evaluate_artifacts(wrong_bounds, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["description-required-1-255"], "CONTRADICTION")

        omitted = rules.replace("BR-P2 Reason/Description is required and has length 1-255 characters.\n", "")
        report = ba_semantic_evaluator.evaluate_artifacts(omitted, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["description-required-1-255"], "MISSING_REQUIRED_BEHAVIOR")

        extra_rule = rules + "BR-P7 Unconfirmed business rule.\n"
        report = ba_semantic_evaluator.evaluate_artifacts(extra_rule, "", "business-rule-completeness-probe")
        statuses = {item["semantic_id"]: item["status"] for item in report["results"] if item["artifact"] == "business_rules"}
        self.assertEqual(statuses["only-supplied-business-rules"], "UNSUPPORTED_INVENTION")

    def test_gap_review_fixture_checks_material_questions_in_generated_review(self):
        from tooling.lib import ba_semantic_evaluator

        gap_review = """Should rescheduling exclude the same Appointment from its conflict check?
When completing an Appointment, should the system create exactly one new Visit or reuse an existing Visit?
Which fields and actions belong in the appointment list, and which filters, sort order, and pagination are required?
"""
        complete = ba_semantic_evaluator.evaluate_artifacts("", "", "cr001-gap-review", gap_review=gap_review)
        self.assertTrue(complete["passed"])

        incomplete = ba_semantic_evaluator.evaluate_artifacts(
            "", "", "cr001-gap-review", gap_review="What states are needed?"
        )
        statuses = {item["semantic_id"]: item["status"] for item in incomplete["results"]}
        self.assertEqual(statuses["gap-reschedule-self-exclusion"], "MISSING_REQUIRED_BEHAVIOR")
        self.assertEqual(statuses["gap-visit-lifecycle"], "MISSING_REQUIRED_BEHAVIOR")
        self.assertEqual(statuses["gap-list-fields-actions"], "MISSING_REQUIRED_BEHAVIOR")


if __name__ == "__main__":
    unittest.main()
