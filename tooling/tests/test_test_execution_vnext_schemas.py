"""Public Phase 8 schema, template and neutral example contracts."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "kits/test/schemas"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class TestExecutionVNextSchemaTests(unittest.TestCase):
    def test_all_v1_contract_files_are_well_formed_and_closed(self):
        names = (
            "environment-v1.schema.json", "execution-manifest-v1.schema.json", "command-evidence-v1.schema.json",
            "observation-v1.schema.json", "finding-v1.schema.json", "finding-classification-v1.schema.json",
            "defect-handoff-v1.schema.json", "ready-for-retest-v1.schema.json", "verified-handoff-v1.schema.json",
            "reopened-v1.schema.json",
        )
        for name in names:
            schema = load_json(SCHEMAS / name)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema", name)
            self.assertEqual(schema["type"], "object", name)
            self.assertFalse(schema["additionalProperties"], name)

    def test_environment_manifest_and_observation_do_not_duplicate_expected_prose(self):
        environment = load_json(SCHEMAS / "environment-v1.schema.json")
        manifest = load_json(SCHEMAS / "execution-manifest-v1.schema.json")
        observation = load_json(SCHEMAS / "observation-v1.schema.json")
        self.assertEqual(environment["properties"]["artifact_class"]["const"], "CANONICAL")
        self.assertIn("application_revisions", manifest["required"])
        self.assertIn("automation_repository", manifest["required"])
        self.assertNotIn("expected_result", manifest["properties"])
        self.assertEqual(observation["properties"]["oracle_locator"]["type"], "string")
        self.assertNotIn("expected_result", observation["properties"])
        self.assertEqual(observation["properties"]["actor"]["properties"]["role"]["const"], "TESTER")

    def test_finding_routes_and_terminal_ownership_are_closed_vocabularies(self):
        classification = load_json(SCHEMAS / "finding-classification-v1.schema.json")
        self.assertEqual(classification["properties"]["classification"]["enum"], [
            "DEFECT", "SPEC_GAP", "BUSINESS_DECISION_REQUIRED", "TEST_ISSUE", "ENVIRONMENT_ISSUE",
        ])
        verified = load_json(SCHEMAS / "verified-handoff-v1.schema.json")
        self.assertEqual(verified["properties"]["state"]["const"], "VERIFIED")
        self.assertEqual(verified["properties"]["verification_actor"]["properties"]["role"]["const"], "TESTER")
        ready = load_json(SCHEMAS / "ready-for-retest-v1.schema.json")
        self.assertEqual(ready["properties"]["verification_owner"]["const"], "TESTER")
        self.assertEqual(ready["properties"]["state"]["const"], "READY_FOR_RETEST")

    def test_defect_classification_schema_encodes_or_and_required_guards(self):
        schema = load_json(SCHEMAS / "finding-classification-v1.schema.json")
        proof = schema["properties"]["defect_proof"]
        properties = proof["properties"]
        self.assertEqual(properties["reproducible"], {"type": "boolean"})
        self.assertEqual(properties["deterministic"], {"type": "boolean"})
        self.assertEqual(proof["anyOf"], [
            {"properties": {"reproducible": {"const": True}}, "required": ["reproducible"]},
            {"properties": {"deterministic": {"const": True}}, "required": ["deterministic"]},
        ])
        self.assertEqual(properties["environment_root_cause_excluded"], {"const": True})
        self.assertEqual(properties["test_issue_excluded"], {"const": True})
        self.assertEqual(properties["mismatch_evidence_refs"]["minItems"], 1)
        defect_rule = next(rule for rule in schema["allOf"] if rule["if"]["properties"]["classification"]["const"] == "DEFECT")
        self.assertEqual(defect_rule["then"]["properties"]["target_repository_ids"]["minItems"], 1)
        for rule in schema["allOf"]:
            if rule["if"]["properties"]["classification"]["const"] != "DEFECT":
                self.assertEqual(rule["then"]["not"], {"required": ["defect_proof"]})

    def test_package_examples_are_neutral_and_templates_carry_no_receipts(self):
        for name in ("environment-v1.template.json", "execution-manifest-v1.template.json"):
            template = load_json(ROOT / "kits/test/templates" / name)
            self.assertNotIn("human_receipt", template)
            self.assertNotIn("approved_by", template)
        example = (ROOT / "kits/test/examples/vnext/neutral/execution-defect-retest/README.md").read_text(encoding="utf-8")
        for forbidden in ("Digital Wedding", "CR-DWC-", "PetClinic", "Appointment", "C:\\Users\\"):
            self.assertNotIn(forbidden.casefold(), example.casefold())


if __name__ == "__main__":
    unittest.main()
