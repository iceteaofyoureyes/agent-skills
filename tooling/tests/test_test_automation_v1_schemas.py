"""Public Automation V1 schema and template contract tests."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "kits/test/schemas"


def load(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


class AutomationV1SchemaTests(unittest.TestCase):
    def test_suitability_schema_accounts_one_authoritative_testcase_row(self):
        schema = load("automation-suitability-v1.schema.json")
        self.assertEqual(schema["properties"]["artifact_class"]["const"], "CANONICAL")
        self.assertEqual(schema["$defs"]["row"]["required"], [
            "testcase_id", "classification", "owner", "required", "rationale", "dependency_refs",
        ])
        self.assertEqual(schema["$defs"]["row"]["additionalProperties"], False)
        self.assertEqual(schema["$defs"]["dependency"]["properties"]["status"]["enum"], ["OPEN", "RESOLVED", "NOT_REQUIRED"])

    def test_plan_commands_are_argv_arrays_and_framework_is_not_fixed(self):
        schema = load("automation-plan-v1.schema.json")
        item = schema["$defs"]["item"]
        self.assertEqual(item["properties"]["execution_command"]["$ref"], "#/$defs/argv")
        self.assertEqual(item["properties"]["verification_commands"]["type"], "array")
        self.assertEqual(item["properties"]["runner"]["type"], "string")
        self.assertNotIn("shell", json.dumps(schema).lower())
        self.assertNotIn("playwright", json.dumps(schema).lower())
        self.assertEqual(item["additionalProperties"], False)

    def test_execution_ready_handoff_has_no_execution_result_or_phase8_state(self):
        schema = load("execution-ready-v1-handoff.schema.json")
        self.assertEqual(schema["properties"]["state"]["const"], "EXECUTION_READY")
        self.assertNotIn("PASS", json.dumps(schema))
        self.assertNotIn("FINDING", json.dumps(schema))
        self.assertNotIn("DEFECT", json.dumps(schema))
        self.assertNotIn("VERIFIED", json.dumps(schema))
        self.assertIn("application_revisions", schema["required"])
        self.assertIn("blocked_testcases", schema["required"])
        self.assertIn("dev_local_references", schema["required"])

    def test_verification_schema_explicitly_says_product_was_not_run(self):
        schema = load("automation-verification-v1.schema.json")
        self.assertEqual(schema["properties"]["product_execution"]["const"], "NOT_RUN")
        self.assertEqual(schema["properties"]["claims"]["maxItems"], 0)
        self.assertEqual(set(schema["$defs"]) if "$defs" in schema else set(), set())

    def test_operator_templates_do_not_fabricate_human_receipts(self):
        for name in ("automation-suitability-v1.template.json", "automation-plan-v1.template.json"):
            template = json.loads((ROOT / "kits/test/templates" / name).read_text(encoding="utf-8"))
            self.assertNotIn("human_gate", template)
            self.assertNotIn("approval_receipt", template)
            self.assertNotIn("approved_by", template)


if __name__ == "__main__":
    unittest.main()
