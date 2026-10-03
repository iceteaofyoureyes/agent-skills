"""FW-BAREF-COVERAGE-01: synthetic authority locators are not business IDs."""
import hashlib
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tooling.lib import test_kit_v1 as kit
from tooling.tests.test_dev_kit import _write_approved_baseline


RULE_IDS = {f"BR-DASH-{number:03d}" for number in range(1, 7)}
STRUCTURAL_SRS = "# SRS\nFeature metadata.\n\n## Business flow\n\n### Diagram\nNo diagram in scope.\n"
RULE_FIXTURE = Path(__file__).parent / "fixtures/approved-baseline-inline-ids/business-rules.md"


class BarefCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def baseline(self, srs=STRUCTURAL_SRS, rules=None):
        # Only synthetic fixture authority is created/hashed here.
        handoff = _write_approved_baseline(self.root)
        text = handoff.read_text(encoding="utf-8")
        for name, content in (("srs.md", srs), ("rules.md", rules or RULE_FIXTURE.read_text(encoding="utf-8"))):
            path = self.root / name
            old_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            path.write_text(content, encoding="utf-8")
            text = text.replace(old_hash, hashlib.sha256(path.read_bytes()).hexdigest())
        handoff.write_text(text, encoding="utf-8")
        return kit.load_approved_baseline(handoff)

    def snapshot(self, refs=RULE_IDS):
        records = [kit.CanonicalTestDesign(
            f"TD-{number:02d}", ("Epic 1", "Test Coverage Plan", "P1"),
            f"Scenario for {ref}", "Observable approved behavior.", (ref,), (),
        ) for number, ref in enumerate(sorted(refs), 1)]
        return kit.DesignSnapshot.create(records, artifact_id="CR-001-design", revision="1")

    def raw(self, refs, expected="Observable approved behavior."):
        return (
            "# Epic 1\n\n## Test Coverage Plan\n\n### P0\n\n### P1\n\n"
            "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| TD-01 | Scenario | Unit | R-001 | {';'.join(sorted(refs))} | {expected} |\n"
            "\n### P2\n\n### P3\n"
        )

    def codes(self, snapshot, baseline):
        return {finding.code for finding in kit.validate_design(snapshot, baseline).findings}

    def test_structural_srs_ids_are_authority_refs_but_not_mandatory_coverage(self):
        baseline = self.baseline()
        locators = {"BAREF:SRS:001", "BAREF:SRS:002", "BAREF:SRS:003"}
        self.assertEqual(baseline.requirement_ids, locators)
        self.assertEqual(baseline.authority_ref_ids, locators | RULE_IDS)
        self.assertEqual(baseline.ba_ids, baseline.authority_ref_ids)
        self.assertEqual(baseline.coverage_ids, RULE_IDS)
        self.assertEqual(kit.validate_design(self.snapshot(), baseline).status, "PASS")

    def test_metadata_and_heading_only_sections_need_no_fabricated_scenario(self):
        baseline = self.baseline()
        normalized = kit.normalize_tea_markdown(self.raw(RULE_IDS), baseline, source_path="synthetic.md")
        self.assertEqual(normalized.status, "NORMALIZED", normalized.findings)
        self.assertEqual(len(normalized.snapshot.records), 1)
        self.assertEqual(kit.validate_design(normalized.snapshot, baseline).status, "PASS")

    def test_missing_canonical_dash_rule_remains_a_coverage_failure(self):
        baseline = self.baseline()
        result = kit.validate_design(self.snapshot(RULE_IDS - {"BR-DASH-003"}), baseline)
        self.assertEqual(result.status, "FAIL")
        self.assertEqual([(f.code, f.message) for f in result.findings], [
            ("UNCOVERED_BA_REQUIREMENT", "approved BA ID has no Test Design or explicit UNKNOWN: BR-DASH-003"),
        ])

    def test_canonical_fr_ids_remain_mandatory(self):
        baseline = self.baseline("## `FR-ABC-001` — Search\nApproved search behavior.\n")
        self.assertEqual(baseline.coverage_ids, RULE_IDS | {"FR-ABC-001"})
        missing = kit.validate_design(self.snapshot(), baseline)
        self.assertEqual([f.message for f in missing.findings], [
            "approved BA ID has no Test Design or explicit UNKNOWN: FR-ABC-001",
        ])
        self.assertEqual(kit.validate_design(self.snapshot(RULE_IDS | {"FR-ABC-001"}), baseline).status, "PASS")

    def test_valid_srs_baref_is_still_accepted_by_normalizer_and_validator(self):
        baseline = self.baseline()
        normalized = kit.normalize_tea_markdown(self.raw(RULE_IDS | {"BAREF:SRS:001"}), baseline, source_path="synthetic.md")
        self.assertEqual(normalized.status, "NORMALIZED", normalized.findings)
        self.assertIn("BAREF:SRS:001", normalized.snapshot.records[0].requirement_refs)
        self.assertEqual(kit.validate_design(normalized.snapshot, baseline).status, "PASS")

    def test_structural_br_locators_are_valid_but_not_mandatory(self):
        baseline = self.baseline("## FR-001 — Search\nApproved search.\n", "# Rules\nRule source without a canonical ID.\n")
        self.assertEqual(baseline.coverage_ids, {"FR-001"})
        self.assertEqual(baseline.authority_ref_ids, {"FR-001", "BAREF:BR:001"})
        self.assertEqual(kit.validate_design(self.snapshot({"FR-001"}), baseline).status, "PASS")
        normalized = kit.normalize_tea_markdown(self.raw({"FR-001", "BAREF:BR:001"}), baseline, source_path="synthetic.md")
        self.assertEqual(normalized.status, "NORMALIZED", normalized.findings)
        self.assertEqual(kit.validate_design(normalized.snapshot, baseline).status, "PASS")

    def test_nonexistent_baref_is_orphan_and_cannot_normalize(self):
        baseline = self.baseline()
        invalid = self.snapshot(RULE_IDS | {"BAREF:SRS:999"})
        self.assertIn("ORPHAN_REQUIREMENT_REF", self.codes(invalid, baseline))
        normalized = kit.normalize_tea_markdown(self.raw(RULE_IDS | {"BAREF:SRS:999"}), baseline, source_path="synthetic.md")
        self.assertEqual(normalized.status, "CANNOT_NORMALIZE")

    def test_real_baref_unknown_is_preserved_and_validated(self):
        baseline = self.baseline("# SRS\nMaximum duration is UNKNOWN.\n")
        normalized = kit.normalize_tea_markdown(self.raw(RULE_IDS | {"BAREF:SRS:001"}, "UNKNOWN"), baseline, source_path="synthetic.md")
        self.assertEqual(normalized.status, "NORMALIZED", normalized.findings)
        question = normalized.snapshot.records[0].open_questions[0]
        self.assertEqual(question.source_ref, "BAREF:SRS:001")
        self.assertEqual(question.text, baseline.unknown_clauses[question.source_ref])
        self.assertIsNone(normalized.snapshot.records[0].expected_behavior)
        self.assertEqual(kit.validate_design(normalized.snapshot, baseline).status, "PASS")

    def test_omitted_baref_unknown_cannot_be_hidden_by_removing_coverage_obligation(self):
        baseline = self.baseline("# SRS\nMaximum duration is UNKNOWN.\n")
        normalized = kit.normalize_tea_markdown(self.raw(RULE_IDS), baseline, source_path="synthetic.md")
        self.assertEqual(normalized.status, "CANNOT_NORMALIZE")
        self.assertIn("UNKNOWN_NOT_PRESERVED", self.codes(self.snapshot(), baseline))

    def test_baref_unknown_text_drift_and_answer_leak_still_fail(self):
        baseline = self.baseline("# SRS\nMaximum duration is UNKNOWN.\n")
        normalized = kit.normalize_tea_markdown(self.raw(RULE_IDS | {"BAREF:SRS:001"}, "UNKNOWN"), baseline, source_path="synthetic.md")
        row = normalized.snapshot.records[0]
        altered = replace(row, open_questions=(replace(row.open_questions[0], text="Different UNKNOWN."),))
        snapshot = kit.DesignSnapshot.create((altered,), artifact_id="CR-001-design", revision="1")
        self.assertIn("UNKNOWN_TEXT_DRIFT", self.codes(snapshot, baseline))
        leak = replace(row, expected_behavior="Maximum duration is 30 minutes.")
        snapshot = kit.DesignSnapshot.create((leak,), artifact_id="CR-001-design", revision="1")
        self.assertIn("UNKNOWN_ASSERTION_LEAK", self.codes(snapshot, baseline))


if __name__ == "__main__":
    unittest.main()
