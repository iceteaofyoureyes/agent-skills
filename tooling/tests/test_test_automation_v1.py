"""Focused Automation V1 contract tests."""
from types import SimpleNamespace
import unittest

from tooling.lib import test_automation_v1 as automation


def testcase(testcase_id, requirements=("BR-001", "FR-001"), designs=("TD-001",), dependencies=()):
    return SimpleNamespace(
        test_case_id=testcase_id,
        requirement_refs=requirements,
        test_design_refs=designs,
        execution_dependencies=dependencies,
    )


class AutomationV1ContractTests(unittest.TestCase):
    def setUp(self):
        self.testcases = [testcase("TC-001"), testcase("TC-002", ("FR-001",), ("TD-002",))]
        self.approved_ref = {
            "id": "FEATURE-1:APPROVED_TESTWARE",
            "revision": "1",
            "sha256": "a" * 64,
            "path": ".test-kit/runs/FEATURE-1/approved-testware-vnext.json",
        }

    def assessments(self, first="API", second="MANUAL_ONLY"):
        return [
            {"testcase_id": "TC-001", "classification": first, "required": True, "rationale": "Protocol mapping."},
            {"testcase_id": "TC-002", "classification": second, "required": True, "rationale": "Keep the exact case as a manual protocol."},
        ]

    def test_owner_map_is_closed_and_exact(self):
        expected = {
            "UNIT": "DEV_LOCAL_REFERENCE", "COMPONENT": "DEV_LOCAL_REFERENCE",
            "CONTRACT": "TEST_AUTOMATION", "DB_RUNTIME": "TEST_AUTOMATION",
            "API": "TEST_AUTOMATION", "INTEGRATION": "TEST_AUTOMATION",
            "E2E": "TEST_AUTOMATION", "ACCESSIBILITY": "TEST_AUTOMATION",
            "SYSTEM": "TEST_AUTOMATION", "MANUAL_ONLY": "MANUAL", "BLOCKED": "BLOCKED",
        }
        self.assertEqual({key: automation.owner_for(key) for key in expected}, expected)
        with self.assertRaises(ValueError):
            automation.owner_for("AI_CONFIDENCE")

    def test_suitability_accounts_for_each_testcase_once_without_copying_oracle_prose(self):
        artifact = automation.make_suitability(
            "FEATURE-1", self.approved_ref, self.testcases, self.assessments(), revision="1",
        )
        automation.validate_suitability(artifact, ["TC-001", "TC-002"])
        self.assertEqual([row["testcase_id"] for row in artifact["rows"]], ["TC-001", "TC-002"])
        self.assertNotIn("objective", str(artifact))
        self.assertNotIn("expected_result", str(artifact))

    def test_suitability_rejects_duplicate_missing_or_orphan_testcases(self):
        duplicate = self.assessments()
        duplicate.append(dict(duplicate[0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            automation.make_suitability("FEATURE-1", self.approved_ref, self.testcases, duplicate)
        with self.assertRaisesRegex(ValueError, "inventory"):
            automation.make_suitability("FEATURE-1", self.approved_ref, self.testcases, self.assessments()[:1])
        orphan = self.assessments()
        orphan[1]["testcase_id"] = "TC-ORPHAN"
        with self.assertRaisesRegex(ValueError, "inventory"):
            automation.make_suitability("FEATURE-1", self.approved_ref, self.testcases, orphan)

    def test_suitability_rejects_baref_and_invalid_dependency_resolution(self):
        bad_trace = [testcase("TC-001", ("BAREF:SRS:001",)), self.testcases[1]]
        with self.assertRaisesRegex(ValueError, "BAREF"):
            automation.make_suitability("FEATURE-1", self.approved_ref, bad_trace, self.assessments())
        bad_design_trace = [testcase("TC-001", designs=("TD-",)), self.testcases[1]]
        with self.assertRaisesRegex(ValueError, "Test Design refs"):
            automation.make_suitability("FEATURE-1", self.approved_ref, bad_design_trace, self.assessments())
        dependency = SimpleNamespace(kind="TOOLING", status="RESOLVED", required=True, resolution_ref=None)
        cases = [testcase("TC-001", dependencies=(dependency,)), self.testcases[1]]
        with self.assertRaisesRegex(ValueError, "resolution"):
            automation.make_suitability("FEATURE-1", self.approved_ref, cases, self.assessments())

    def test_suitability_preserves_typed_open_automation_dependencies(self):
        assessments = self.assessments()
        assessments[0]["dependency_refs"] = [{
            "kind": "ENVIRONMENT_ACCESS", "status": "OPEN", "required": True, "resolution_ref": None,
        }]
        artifact = automation.make_suitability(
            "FEATURE-1", self.approved_ref, self.testcases, assessments, revision="1",
        )
        dependency = artifact["rows"][0]["dependency_refs"][0]
        self.assertEqual(dependency["kind"], "ENVIRONMENT_ACCESS")
        self.assertEqual(dependency["status"], "OPEN")
        self.assertIs(dependency["required"], True)

    def test_plan_uses_stable_aut_ids_argv_arrays_and_no_framework_default(self):
        suitability = automation.make_suitability(
            "FEATURE-1", self.approved_ref, self.testcases, self.assessments(), revision="1",
        )
        specs = {
            "TC-001": {
                "suite": "api",
                "planned_paths": ["tests/api/test_resource.py"],
                "runner": "project-native",
                "execution_command": ["python", "-m", "pytest", "tests/api/test_resource.py"],
                "verification_commands": [{"category": "TEST_DISCOVERY", "argv": ["python", "-m", "pytest", "tests/api/test_resource.py", "--collect-only"]}],
            },
        }
        plan = automation.make_plan(suitability, self.testcases, "automation", specs, revision="1")
        self.assertEqual([item["aut_id"] for item in plan["items"]], ["AUT-0001"])
        self.assertEqual(plan["items"][0]["owner"], "TEST_AUTOMATION")
        self.assertEqual(plan["items"][0]["repository_id"], "automation")
        self.assertEqual(plan["items"][0]["execution_command"][0], "python")
        self.assertNotIn("playwright", str(plan).lower())
        self.assertEqual(plan["manual_testcases"], ["TC-002"])

    def test_replan_preserves_aut_identity_for_existing_testcase(self):
        suitability = automation.make_suitability(
            "FEATURE-1", self.approved_ref, self.testcases, self.assessments(), revision="1",
        )
        spec = {"suite": "api", "planned_paths": ["tests/api/test_resource.py"], "runner": "native",
                "execution_command": ["python", "-m", "pytest", "tests/api/test_resource.py"],
                "verification_commands": [{"category": "SYNTAX", "argv": ["python", "-m", "compileall", "-q", "tests/api"]}]}
        first = automation.make_plan(suitability, self.testcases, "automation", {"TC-001": spec}, revision="1")
        second = automation.make_plan(suitability, self.testcases, "automation", {"TC-001": spec},
                                      revision="2", previous_plan=first)
        self.assertEqual(first["items"][0]["aut_id"], second["items"][0]["aut_id"])
        candidate = dict(second)
        candidate["items"] = [dict(second["items"][0], execution_command=["python", "-m", "pytest", "other.py"])]
        with self.assertRaises(automation.AutomationV1Error) as caught:
            automation.assert_material_plan_unchanged(second, candidate)
        self.assertEqual(caught.exception.code, "NEEDS_REPLAN")

    def test_plan_rejects_shell_strings_wrong_item_set_and_scope_paths(self):
        suitability = automation.make_suitability(
            "FEATURE-1", self.approved_ref, self.testcases, self.assessments(), revision="1",
        )
        bad = {"suite": "api", "planned_paths": ["../app/test.py"], "runner": "native",
               "execution_command": "python -m pytest", "verification_commands": []}
        with self.assertRaises(ValueError):
            automation.make_plan(suitability, self.testcases, "automation", {"TC-001": bad})
        with self.assertRaisesRegex(ValueError, "coverage"):
            automation.make_plan(suitability, self.testcases, "automation", {})
        absolute = dict(bad, planned_paths=["tests/api/test_resource.py"],
                        execution_command=["python", "-m", "pytest", "C:\\Users\\person\\test.py"],
                        verification_commands=[{"category": "SYNTAX", "argv": ["python", "-m", "compileall", "-q", "tests"]}])
        with self.assertRaisesRegex(ValueError, "absolute paths"):
            automation.make_plan(suitability, self.testcases, "automation", {"TC-001": absolute})

    def test_plan_rejects_shell_and_code_string_modes_case_insensitively(self):
        suitability = automation.make_suitability(
            "FEATURE-1", self.approved_ref, self.testcases, self.assessments(), revision="1",
        )
        forbidden = (
            ["powershell.exe", "-CoMmAnD", "Write-Output unsafe"],
            ["cmd.exe", "/C", "python -m pytest"],
            ["python", "-C", "print('unsafe')"],
            ["node", "--EVAL", "process.exit(0)"],
        )
        for command in forbidden:
            for field in ("execution_command", "verification_commands"):
                spec = {
                    "suite": "api", "planned_paths": ["tests/api/test_resource.py"], "runner": "native",
                    "execution_command": ["python", "-m", "pytest", "tests/api/test_resource.py"],
                    "verification_commands": [{"category": "STATIC", "argv": ["git", "diff", "--check"]}],
                }
                if field == "execution_command":
                    spec[field] = command
                else:
                    spec[field] = [{"category": "STATIC", "argv": command}]
                with self.subTest(command=command, field=field), self.assertRaisesRegex(ValueError, "code-string"):
                    automation.make_plan(suitability, self.testcases, "automation", {"TC-001": spec})

    def test_verification_claim_contract_excludes_product_outcomes(self):
        self.assertEqual(set(automation.VERIFICATION_CATEGORIES), {
            "SYNTAX", "STATIC", "LINT", "TYPECHECK", "TEST_DISCOVERY", "TEST_LIST",
            "CONFIG_VALIDATE", "HARNESS_SELF_TEST", "FIXTURE_VALIDATE",
        })
        for claim in ("API PASS", "E2E PASS", "SYSTEM PASS", "feature PASS", "WCAG conformance", "VERIFIED"):
            with self.subTest(claim=claim), self.assertRaises(ValueError):
                automation.reject_execution_claims({"claim": claim})


if __name__ == "__main__":
    unittest.main()
