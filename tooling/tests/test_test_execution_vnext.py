"""Contract tests for Test Execution / Finding / Defect / Retest VNext."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from tooling.lib import test_execution_vnext as execution


SHA = "a" * 40
HASH = hashlib.sha256(b"exact synthetic bytes").hexdigest()


def ref(path="evidence/exact.json", artifact_id="ARTIFACT-1"):
    return {"id": artifact_id, "revision": "1", "sha256": HASH, "path": path}


def testcase_ref():
    return {"artifact_id": "APPROVED-TESTCASES", "revision": "1", "sha256": HASH, "path": "testware/cases.json"}


class EnvironmentAndManifestContracts(unittest.TestCase):
    def test_canonical_environment_is_portable_secret_free_and_project_neutral(self):
        descriptor = {
            "schema_version": 1,
            "artifact_class": "CANONICAL",
            "environment_id": "ENV-ACCEPTANCE-1",
            "profile": "PROFILE-SYNTHETIC-1",
            "configuration_refs": [],
            "evidence_refs": [],
        }
        self.assertEqual(execution.validate_environment_descriptor(descriptor), descriptor)
        for invalid in (
            {**descriptor, "configuration_refs": [{"id": "CONFIG-1", "revision": "1", "sha256": HASH, "path": "C:/private/config.json"}]},
            {**descriptor, "profile": "password=example-secret"},
        ):
            with self.assertRaises(ValueError):
                execution.validate_environment_descriptor(invalid)

    def test_environment_configuration_ref_must_resolve_to_secret_free_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / "config.json"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text('{"profile":"safe","access_token":"embedded-secret-value"}\n', encoding="utf-8")
            descriptor = {
                "schema_version": 1, "artifact_class": "CANONICAL", "environment_id": "ENV-CONFIG-1",
                "profile": "PROFILE-CONFIG-1", "configuration_refs": [{
                    "id": "CONFIG-1", "revision": "1", "sha256": hashlib.sha256(config.read_bytes()).hexdigest(), "path": "config.json",
                }], "evidence_refs": [],
            }
            with self.assertRaises(ValueError):
                execution.validate_environment_descriptor(descriptor, root)

    def test_manifest_binds_each_repository_without_expected_result_prose(self):
        manifest = {
            "schema_version": 1, "artifact_class": "CANONICAL", "execution_id": "EXEC-1", "feature_id": "FEATURE-1",
            "execution_ready_ref": ref("automation/execution-ready.json", "READY-1"),
            "environment_ref": ref("execution/environment.json", "ENV-1"),
            "approved_testware_ref": ref("testware/approved.json", "TESTWARE-1"),
            "automation_plan_ref": ref("automation/plan.json", "PLAN-1"),
            "application_revisions": {"core": SHA, "catalog": "b" * 40},
            "automation_repository": {"id": "quality", "role": "TEST_AUTOMATION", "repository": "example/quality", "path": "quality"},
            "automation_revision": "c" * 40,
            "automated_items": [{"aut_id": "AUT-001", "testcase_refs": ["TC-001"]}],
            "manual_testcases": [{"testcase_id": "TC-002", "testcase_collection_ref": testcase_ref()}],
            "dev_local_references": [{"testcase_id": "TC-003", "evidence_refs": [ref("app/test-evidence.json", "DEV-TEST-1")]}],
            "optional_blocked_testcases": [], "created_at": "2026-10-05T00:00:00Z",
        }
        self.assertEqual(execution.validate_execution_manifest(manifest), manifest)
        invalid = copy.deepcopy(manifest)
        invalid["expected_result"] = "copied expected behavior"
        with self.assertRaises(ValueError):
            execution.validate_execution_manifest(invalid)


class ObservationAndFindingContracts(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "evidence").mkdir()
        (self.root / "evidence/exact.json").write_bytes(b"exact synthetic bytes")

    def test_observation_points_to_exact_testcase_and_tester_actor(self):
        observation = {
            "observation_id": "OBS-001", "execution_id": "EXEC-1", "testcase_id": "TC-001", "aut_id": "AUT-001",
            "oracle_ref": testcase_ref(), "oracle_locator": "TC-001", "actual_summary": "Observed approved response fields.",
            "evidence_refs": [ref()], "actor": {"actor_id": "tester-1", "role": "TESTER"},
            "outcome": "PASS", "recorded_at": "2026-10-05T00:00:00Z",
        }
        self.assertEqual(execution.validate_observation(observation), observation)
        for change in (
            {"oracle_locator": "TC-002"},
            {"actor": {"actor_id": "developer-1", "role": "DEV"}},
            {"expected_result": "mutated oracle"},
        ):
            invalid = {**observation, **change}
            with self.assertRaises(ValueError):
                execution.validate_observation(invalid)

    def test_finding_classification_vocabulary_routes_and_defect_proof_are_frozen(self):
        for classification, route in execution.ROUTES.items():
            artifact = {
                "schema_version": 1, "artifact_class": "CANONICAL", "finding_ref": ref("evidence/finding.json", "FINDING-1"),
                "classification": classification, "actor": {"actor_id": "tester-1", "role": "TESTER"},
                "rationale": "The recorded evidence supports this route.", "evidence_refs": [ref()], "route": route,
                "target_repository_ids": [], "classified_at": "2026-10-05T00:00:00Z",
            }
            if classification == "DEFECT":
                artifact["target_repository_ids"] = ["core"]
                artifact["defect_proof"] = {
                    "reproducible": True, "deterministic": True, "environment_root_cause_excluded": True,
                    "test_issue_excluded": True, "mismatch_evidence_refs": [ref()],
                }
            self.assertEqual(execution.validate_classification(artifact), artifact)
        invalid = {
            "schema_version": 1, "artifact_class": "CANONICAL", "finding_ref": ref("evidence/finding.json", "FINDING-1"),
            "classification": "COMMAND_FAIL", "actor": {"actor_id": "tester-1", "role": "TESTER"},
            "rationale": "Exit code was nonzero.", "evidence_refs": [ref()], "route": "DEV",
            "target_repository_ids": ["core"], "classified_at": "2026-10-05T00:00:00Z",
        }
        with self.assertRaises(ValueError):
            execution.validate_classification(invalid)
        invalid["classification"] = "DEFECT"
        invalid["defect_proof"] = {"reproducible": True, "deterministic": False,
                                   "environment_root_cause_excluded": True, "test_issue_excluded": True,
                                   "mismatch_evidence_refs": [ref()]}
        with self.assertRaises(ValueError):
            execution.validate_classification(invalid)


if __name__ == "__main__":
    unittest.main()
