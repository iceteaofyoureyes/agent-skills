"""Guard public Test VNext schema surfaces against the executable authority boundaries."""
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class TestKitVNextSchemaTests(unittest.TestCase):
    def test_authority_context_schema_tracks_explicit_ux_and_exact_refs(self):
        schema = json.loads((ROOT / "kits/test/schemas/test-authority-context-vnext.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["artifact_class"]["const"], "RUNTIME")
        self.assertEqual(schema["properties"]["mode"]["const"], "VNEXT")
        self.assertIn("ux_required", schema["required"])
        self.assertEqual(schema["properties"]["ux_required"]["type"], "boolean")
        self.assertIn("byte_refs", schema["required"])
        self.assertIn("refs", schema["required"])
        self.assertEqual(schema["$defs"]["uxContext"]["properties"]["prototype_authority"]["const"], "REVIEW_EVIDENCE")

    def test_approved_testware_schema_is_manual_terminal_with_br_fr_trace_only(self):
        schema = json.loads((ROOT / "kits/test/schemas/approved-testware-vnext-handoff-manifest.schema.json").read_text(encoding="utf-8"))

        self.assertEqual(schema["properties"]["artifact_class"]["const"], "HANDOFF_MANIFEST")
        self.assertEqual(schema["properties"]["state"]["const"], "APPROVED_TESTWARE")
        self.assertNotIn("EXECUTION_READY", json.dumps(schema))
        self.assertNotIn("VERIFIED", json.dumps(schema))
        self.assertIn("^(BR|FR)-", schema["properties"]["trace_summary"]["properties"]["requirement_ids"]["items"]["pattern"])
        self.assertNotIn("BAREF", schema["properties"]["trace_summary"]["properties"]["requirement_ids"]["items"]["pattern"])

    def test_operator_template_cannot_be_used_as_an_approval_receipt(self):
        template = json.loads((ROOT / "kits/test/templates/ux-context-request.template.json").read_text(encoding="utf-8"))

        self.assertEqual(set(template), {"root", "contract", "approval_receipt", "prototype"})
        self.assertNotIn("approved_by", template)
        self.assertNotIn("decision", template)
        self.assertEqual(template["prototype"], None)


if __name__ == "__main__":
    unittest.main()
