"""Synthetic local multi-repository Phase 8 acceptance, including real Dev VNext fixes."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tooling.lib import dev_vnext_runtime
from tooling.lib import test_execution_vnext as execution
from tooling.tests import test_test_automation_v1_acceptance as phase7


class TestExecutionVNextAcceptance(unittest.TestCase):
    def setUp(self):
        self.fixture = phase7.TestAutomationV1Acceptance("test_api_e2e_shift_left_dev_local_manual_review_verify_and_fresh_resume")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self._install_ignores_before_phase8()
        self.tester_auth = lambda actor, request: (
            {"authenticated": True, "actor_id": actor, "role": "TESTER"}
            if actor == "synthetic-tester" and request.get("role") == "TESTER" else
            {"authenticated": True, "actor_id": actor, "role": "DEV"}
            if actor == "synthetic-dev" else None
        )

    def _install_ignores_before_phase8(self):
        (self.fixture.app_root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
        self.fixture.app_revision = self.fixture._commit(self.fixture.app_root, "ignore local interpreter output")
        (self.fixture.automation_root / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n", encoding="utf-8")
        self.fixture._commit(self.fixture.automation_root, "ignore local test runner output")
        self.fixture.dev_handoff_path = self.fixture._ready_for_test_handoff()

    def _automation_ready(self, run_id):
        runtime = self.fixture._runtime(run_id)
        state = runtime.start(self.fixture.test_run_dir)
        state = runtime.analyze_suitability(self.fixture._assessments())
        specs = self.fixture._plan_specs()
        for case_id, item in specs.items():
            item["execution_command"] = ["python", "-m", "pytest", item["planned_paths"][0], "-q"]
        state = runtime.plan(specs)
        state = runtime.begin_implementation()
        app_test = f"# Synthetic automation revision {run_id}\n" + """from pathlib import Path
import sys
project = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project / "app" / "src"))
from request import submit

def test_approved_request_outcome():
    payload = {"request_id": "synthetic-1"}
    assert submit(payload) == {"saved": payload, "accepted": True}
"""
        smoke_test = f"# Synthetic automation revision {run_id}\ndef test_local_synthetic_smoke():\n    assert True\n"
        source_by_aut = {"AUT-0001": app_test, "AUT-0002": smoke_test}
        plan = runtime._read_artifact_ref(state["plan_ref"])
        for item in plan["items"]:
            source = source_by_aut[item["aut_id"]]
            runtime.write_source(item["aut_id"], item["repository_id"], item["planned_paths"][0], source, base_revision=state["implementation_base_revision"])
        self.fixture._commit(self.fixture.automation_root, f"commit synthetic automation {run_id}")
        state = runtime.record_implementation()
        state = runtime.record_review(self.fixture._review())
        state = runtime.verify()
        ready_state = runtime.finalize(self.fixture.dev_handoff_path)
        self.assertEqual(ready_state["lifecycle"], "EXECUTION_READY")
        handoff = runtime.revalidate_handoff()
        self.assertEqual(handoff["application_revisions"]["core"], self.fixture.app_revision)
        if run_id.endswith("DEFECT"):
            self.initial_phase7_ready = copy.deepcopy(handoff)
            self.initial_dev_handoff = json.loads((self.root / handoff["dev_handoff"]["path"]).read_text(encoding="utf-8"))
        return runtime, handoff

    def _execution(self, automation_run_id, execution_id):
        return execution.ExecutionRuntime(
            self.root, self.root / f".test-kit/automation/runs/{automation_run_id}", execution_id,
            tester_authenticator=self.tester_auth,
            human_actor_authenticator=self.fixture.human_test_auth,
            ba_human_actor_authenticator=self.fixture.ba_auth,
            repository_roots={"core": self.fixture.app_root, "quality": self.fixture.automation_root},
        )

    def _environment(self):
        return {
            "schema_version": 1, "artifact_class": "CANONICAL", "environment_id": "ENV-SYNTHETIC-1",
            "profile": "PROFILE-LOCAL-ACCEPTANCE-1", "configuration_refs": [], "evidence_refs": [],
        }

    def _evidence_ref(self, label):
        path = self.root / "test-evidence" / f"{label}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"evidence": label}, sort_keys=True) + "\n", encoding="utf-8")
        return {"id": f"EVIDENCE-{label}", "revision": "1", "sha256": execution._sha(path.read_bytes()), "path": path.relative_to(self.root).as_posix()}

    def _assert_stale_start(self, run_id, execution_id):
        attempt = self._execution(run_id, execution_id)
        with self.assertRaises(execution.ExecutionVNextError) as caught:
            attempt.start(self._environment())
        self.assertEqual(caught.exception.code, "EXECUTION_STALE")

    def _dev_fix(self, defect_id, run_id, result_source):
        original_dev = self.initial_dev_handoff
        repository = copy.deepcopy(original_dev["run_state"]["repositories"])
        current_base = self.fixture._run_git(self.fixture.app_root, "rev-parse", "HEAD")
        for row in repository:
            row["base_revision"] = current_base
        fix_evidence = self.root / f"{run_id}-review-evidence.json"
        fix_evidence.write_text(json.dumps({"review": "consolidated exact fix review"}), encoding="utf-8")
        check = {
            "name": "fixed-contract", "repository_id": "core", "category": "UNIT",
            "command": (["python", "tests/phase8_fix_check.py"] if result_source is not None else ["python", "-m", "compileall", "-q", "src"]),
        }
        runtime = dev_vnext_runtime.DevRuntime(self.root, ba_authenticator=self.fixture.ba_auth)
        request = {
            "run_id": run_id, "change_id": defect_id, "summary": "Fix the observed synthetic request behavior",
            "authority_mode": "FEATURE_DELIVERY", "repositories": repository,
            "repository_roots": {"core": str(self.fixture.app_root)}, "checks": [check],
            "upstream": original_dev["upstream_engineering_handoff"],
        }
        state = runtime.start(request)
        state = runtime.validate_authority()
        impact = runtime.impact_template()
        impact.update({
            "affected_components": ["request handling"], "affected_interfaces": ["request result"],
            "technical_unknowns": [], "upstream_gaps": [],
        })
        state = runtime.impact(impact)
        plan = self.root / f"{run_id}-plan.md"
        tasks = self.root / f"{run_id}-tasks.md"
        plan.write_text("Preserve approved behavior while repairing the implementation.\n", encoding="utf-8")
        tasks.write_text("Update the targeted source and run fresh verification.\n", encoding="utf-8")
        state = runtime.plan(plan, tasks, revision=f"PLAN-{run_id}")
        state = runtime.implementation_ready()
        state = runtime.begin_implementation()
        if result_source is not None:
            runtime.write_source("core", "src/request.py", result_source)
            check_source = "from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nfrom src.request import submit\nassert isinstance(submit({'request_id': 'synthetic-1'}), dict)\n"
            if not (self.fixture.app_root / "tests/phase8_fix_check.py").exists():
                runtime.write_source("core", "tests/phase8_fix_check.py", check_source)
            self.fixture._commit(self.fixture.app_root, f"Dev VNext fix cycle {run_id}")
        runtime.record_review([runtime.reference(fix_evidence)])
        verification = runtime.verify()
        check_evidence = json.loads((runtime.run_directory / "evidence/checks/fixed-contract-0.json").read_text(encoding="utf-8"))
        self.assertEqual(verification["checks"][0]["status"], "PASS", check_evidence)
        coverage = copy.deepcopy(original_dev["requirements_coverage"])
        for row in coverage:
            row["code_refs"] = [runtime.reference("app/src/request.py")]
            row["test_refs"] = [runtime.reference("app/tests/test_request.py")]
        handoff = runtime.finalize(coverage)
        self.assertEqual(handoff["state"], "READY_FOR_TEST")
        handoff_path = runtime.run_directory / "dev-handoff.json"
        self.assertEqual(json.loads(handoff_path.read_text(encoding="utf-8"))["change_id"], defect_id)
        return handoff_path

    def test_both_paths_real_dev_fix_reopen_and_nondefect_routes(self):
        # Preserve the exact old Dev Handoff bytes before creating the Phase 7 authority.
        self.fixture.dev_handoff_path = self.fixture._ready_for_test_handoff(self.root / "initial-dev-handoff.json")
        phase7_runtime, phase7_ready = self._automation_ready("PHASE8-DEFECT")
        # Runtime state text alone, dirty worktrees, wrong SHAs and edited handoff bytes cannot authorize.
        state_only_dir = self.root / ".test-kit/automation/runs/STATE-ONLY"
        state_only_dir.mkdir(parents=True, exist_ok=True)
        (state_only_dir / "workflow-state.json").write_text(json.dumps({"lifecycle": "EXECUTION_READY"}), encoding="utf-8")
        state_only = execution.ExecutionRuntime(
            self.root, state_only_dir, "EXEC-STATE-ONLY", tester_authenticator=self.tester_auth,
            human_actor_authenticator=self.fixture.human_test_auth,
            ba_human_actor_authenticator=self.fixture.ba_auth,
            repository_roots={"core": self.fixture.app_root, "quality": self.fixture.automation_root},
        )
        with self.assertRaises(execution.ExecutionVNextError):
            state_only.start(self._environment())

        app_source = self.fixture.app_root / "src/request.py"
        app_bytes = app_source.read_bytes()
        app_source.write_bytes(app_bytes + b"\n# dirty app\n")
        self._assert_stale_start("PHASE8-DEFECT", "EXEC-APP-DIRTY")
        app_source.write_bytes(app_bytes)
        unexpected = self.fixture.automation_root / "unplanned-local-file"
        unexpected.write_text("dirty automation worktree\n", encoding="utf-8")
        self._assert_stale_start("PHASE8-DEFECT", "EXEC-AUT-DIRTY")
        unexpected.unlink()

        ready_path = self.root / phase7_runtime.status()["handoff_ref"]["path"]
        ready_bytes = ready_path.read_bytes()
        stale_ready = json.loads(ready_bytes)
        stale_ready["application_revisions"]["core"] = "f" * 40
        ready_path.write_text(json.dumps(stale_ready), encoding="utf-8")
        self._assert_stale_start("PHASE8-DEFECT", "EXEC-READY-STALE")
        ready_path.write_bytes(ready_bytes)

        original_app_sha = phase7_ready["application_revisions"]["core"]
        (self.fixture.app_root / ".phase8-revision-drift").write_text("wrong app revision\n", encoding="utf-8")
        self.fixture._commit(self.fixture.app_root, "temporary wrong app revision for acceptance")
        self._assert_stale_start("PHASE8-DEFECT", "EXEC-APP-WRONG-REVISION")
        self.fixture._run_git(self.fixture.app_root, "reset", "--hard", original_app_sha)
        original_automation_sha = phase7_ready["automation_revision"]
        (self.fixture.automation_root / ".phase8-revision-drift").write_text("wrong automation revision\n", encoding="utf-8")
        self.fixture._commit(self.fixture.automation_root, "temporary wrong automation revision for acceptance")
        self._assert_stale_start("PHASE8-DEFECT", "EXEC-AUT-WRONG-REVISION")
        self.fixture._run_git(self.fixture.automation_root, "reset", "--hard", original_automation_sha)

        defect_attempt = self._execution("PHASE8-DEFECT", "EXEC-DEFECT")
        defect_attempt.start(self._environment())
        defect_attempt.execute_automated()
        self.assertEqual(defect_attempt.state["finding_refs"], {})
        plan = phase7_runtime._read_artifact_ref(phase7_runtime.status()["plan_ref"])
        api_aut = next(row["aut_id"] for row in plan["items"] if row["testcase_refs"] == ["TC-001"])
        failed_command_ref = defect_attempt.state["command_evidence_refs"][api_aut]
        failed_command = defect_attempt._read_artifact(failed_command_ref)
        self.assertEqual(failed_command["status"], "COMMAND_FAIL")
        first_finding = defect_attempt.record_observation(
            testcase_id="TC-001", aut_id=api_aut, outcome="FINDING",
            actual_summary="The approved request outcome was not observed in the returned result.",
            evidence_refs=[failed_command_ref], actor_id="synthetic-tester",
        )
        defect_attempt.record_observation(
            testcase_id="TC-004", aut_id="AUT-0002", outcome="PASS", actual_summary="Local smoke observation passed.",
            evidence_refs=[defect_attempt.state["command_evidence_refs"]["AUT-0002"]], actor_id="synthetic-tester",
        )
        manual_evidence = self._evidence_ref("manual-defect-attempt")
        defect_attempt.record_observation(
            testcase_id="TC-002", outcome="PASS", actual_summary="Manual request path completed as approved.",
            evidence_refs=[manual_evidence], actor_id="synthetic-tester",
        )
        actual_finding_id = next(iter(defect_attempt.state["finding_refs"]))
        self.assertFalse(defect_attempt.state["classification_refs"])
        self.assertFalse(defect_attempt.state["defect_handoffs"])
        proof = {
            "reproducible": True, "deterministic": False, "environment_root_cause_excluded": True,
            "test_issue_excluded": True, "mismatch_evidence_refs": [failed_command_ref],
        }
        with self.assertRaises(execution.ExecutionVNextError) as non_tester:
            defect_attempt.classify_finding(
                actual_finding_id, "DEFECT", actor_id="synthetic-dev", rationale="not a Tester",
                evidence_refs=[failed_command_ref], target_repository_ids=["core"], defect_proof=proof,
            )
        self.assertEqual(non_tester.exception.code, "AUTHENTICATION_FAILED")
        with self.assertRaises(execution.ExecutionVNextError) as wrong_target:
            defect_attempt.classify_finding(
                actual_finding_id, "DEFECT", actor_id="synthetic-tester", rationale="wrong target",
                evidence_refs=[failed_command_ref], target_repository_ids=["not-in-topology"], defect_proof=proof,
            )
        self.assertEqual(wrong_target.exception.code, "DEFECT_PROOF_REQUIRED")
        classified = defect_attempt.classify_finding(
            actual_finding_id, "DEFECT", actor_id="synthetic-tester",
            rationale="The exact approved oracle and repeatable mismatch are evidenced; the environment and test issue are excluded.",
            evidence_refs=[failed_command_ref], target_repository_ids=["core"],
            defect_proof=proof,
        )
        defect_id = defect_attempt._read_artifact(classified["defect_handoff_ref"])["defect_id"]
        self.assertTrue(defect_id.startswith("DEF-"))
        with self.assertRaises(execution.ExecutionVNextError) as stale_original_dev:
            defect_attempt.accept_dev_fix(defect_id, self.fixture.dev_handoff_path)
        self.assertEqual(stale_original_dev.exception.code, "DEV_FIX_CHANGE_ID_MISMATCH")

        no_change_handoff = self._dev_fix(defect_id, "DEVFIX-NO-CHANGE", None)
        with self.assertRaises(execution.ExecutionVNextError) as no_target_revision:
            defect_attempt.accept_dev_fix(defect_id, no_change_handoff)
        self.assertEqual(no_target_revision.exception.code, "DEV_FIX_NO_TARGET_REVISION_CHANGE")

        dev_fix_1 = self._dev_fix(
            defect_id, "DEVFIX-1", 'def submit(payload):\n    return {"saved": payload}\n',
        )
        valid_fix_data = json.loads(dev_fix_1.read_text(encoding="utf-8"))
        for label, mutate in (
            ("wrong-change", lambda data: data.update(change_id="WRONG-CHANGE")),
            ("wrong-ba", lambda data: data.update(upstream_engineering_handoff={**data["upstream_engineering_handoff"], "sha256": "0" * 64})),
            ("failed-verification", lambda data: data["engineering_verification"]["checks"][0].update(status="FAIL")),
        ):
            invalid = copy.deepcopy(valid_fix_data)
            mutate(invalid)
            invalid_path = self.root / f"{label}-dev-handoff.json"
            invalid_path.write_text(json.dumps(invalid), encoding="utf-8")
            with self.assertRaises(execution.ExecutionVNextError):
                defect_attempt.accept_dev_fix(defect_id, invalid_path)
        retest_ready_1 = defect_attempt.accept_dev_fix(defect_id, dev_fix_1)
        self.assertEqual(defect_attempt._read_artifact(retest_ready_1["ready_for_retest_ref"])["state"], "READY_FOR_RETEST")
        with self.assertRaises(execution.ExecutionVNextError):
            defect_attempt.accept_dev_fix(defect_id, self.fixture.dev_handoff_path)
        ready_file = self.root / retest_ready_1["ready_for_retest_ref"]["path"]
        ready_bytes = ready_file.read_bytes()
        invalid_ready = json.loads(ready_bytes)
        invalid_ready["fixed_application_revisions"]["core"] = "e" * 40
        ready_file.write_text(json.dumps(invalid_ready), encoding="utf-8")
        with self.assertRaises(execution.ExecutionVNextError):
            defect_attempt.execute_retest(defect_id)
        ready_file.write_bytes(ready_bytes)
        failed_retest = defect_attempt.execute_retest(defect_id)
        self.assertEqual(failed_retest["command_status"], "COMMAND_FAIL")
        reopened = defect_attempt.record_retest_observation(
            defect_id, outcome="FINDING", actual_summary="The original approved testcase still fails after the first fix.",
            evidence_refs=[failed_retest["command_evidence_ref"]], actor_id="synthetic-tester",
        )
        self.assertEqual(reopened["state"], "REOPENED")
        reopened_doc = defect_attempt._read_artifact(reopened["reopened_ref"])
        self.assertEqual(reopened_doc["defect_id"], defect_id)
        self.assertEqual(reopened_doc["reopen_count"], 1)

        next_cycle = defect_attempt.prepare_reopened_defect_handoff(defect_id)
        self.assertEqual(next_cycle["defect_id"], defect_id)
        dev_fix_2 = self._dev_fix(
            defect_id, "DEVFIX-2", 'def submit(payload):\n    return {"saved": payload, "accepted": True}\n',
        )
        retest_ready_2 = defect_attempt.accept_dev_fix(defect_id, dev_fix_2)
        retest_command = defect_attempt.execute_retest(defect_id)
        self.assertEqual(retest_command["command_status"], "COMMAND_PASS")
        closed = defect_attempt.record_retest_observation(
            defect_id, outcome="PASS", actual_summary="The original approved testcase passed at the exact fixed revision.",
            evidence_refs=[retest_command["command_evidence_ref"]], actor_id="synthetic-tester",
        )
        self.assertEqual(closed["state"], "VERIFIED")
        verified_after_fix = defect_attempt.revalidate_verified()
        self.assertEqual(verified_after_fix["state"], "VERIFIED")
        self.assertEqual(verified_after_fix["application_revisions"]["core"], retest_ready_2["ready_for_retest_ref"] and self.fixture._run_git(self.fixture.app_root, "rev-parse", "HEAD"))

        # The repaired application gets a new Dev Handoff and a new exact Phase 7 attempt.
        self.fixture.app_revision = self.fixture._run_git(self.fixture.app_root, "rev-parse", "HEAD")
        self.fixture.dev_handoff_path = self.fixture._ready_for_test_handoff(self.root / "post-fix-dev-handoff.json")
        pass_phase7, _ = self._automation_ready("PHASE8-STRAIGHT")
        straight = self._execution("PHASE8-STRAIGHT", "EXEC-STRAIGHT")
        straight.start(self._environment())
        straight.execute_automated()
        self.assertEqual(straight.state["status"], "EXECUTION_COMPLETE")
        command_refs = straight.state["command_evidence_refs"]
        for testcase_id, aut_id in (("TC-001", "AUT-0001"), ("TC-004", "AUT-0002")):
            straight.record_observation(
                testcase_id=testcase_id, aut_id=aut_id, outcome="PASS", actual_summary="Exact approved automated testcase passed.",
                evidence_refs=[command_refs[aut_id]], actor_id="synthetic-tester",
            )
        straight.record_observation(
            testcase_id="TC-002", outcome="PASS", actual_summary="Exact approved manual testcase passed.",
            evidence_refs=[self._evidence_ref("manual-straight-pass")], actor_id="synthetic-tester",
        )
        try:
            straight.finalize_verified(actor_id="synthetic-dev")
        except execution.ExecutionVNextError as error:
            self.assertEqual(error.code, "AUTHENTICATION_FAILED")
        else:
            self.fail("Dev actor authenticated final VERIFIED")
        verified = straight.finalize_verified(actor_id="synthetic-tester")
        self.assertEqual(verified["state"], "VERIFIED")
        self.assertEqual(straight.revalidate_verified()["state"], "VERIFIED")
        self.assertFalse(straight.state["finding_refs"])

        for index, (classification, route) in enumerate(execution.ROUTES.items(), start=1):
            attempt = self._execution("PHASE8-STRAIGHT", f"EXEC-ROUTE-{index}")
            attempt.start(self._environment())
            observation = attempt.record_observation(
                testcase_id="TC-002", outcome="FINDING", actual_summary="The approved manual observation is incomplete.",
                evidence_refs=[self._evidence_ref(f"route-{index}")], actor_id="synthetic-tester",
            )
            finding_id = next(iter(attempt.state["finding_refs"]))
            result = attempt.classify_finding(
                finding_id, classification, actor_id="synthetic-tester", rationale="Tester selected the supported route from exact evidence.",
                evidence_refs=[], target_repository_ids=([] if classification != "DEFECT" else ["core"]),
                defect_proof=(None if classification != "DEFECT" else {
                    "reproducible": True, "deterministic": False, "environment_root_cause_excluded": True,
                    "test_issue_excluded": True, "mismatch_evidence_refs": [self._evidence_ref(f"defect-route-{index}")],
                }),
            )
            self.assertEqual(result.get("route", "DEV"), route)
            self.assertIsNone(result.get("verified")) if classification == "DEFECT" else self.assertFalse(result["verified"])
            if classification != "DEFECT":
                self.assertFalse(attempt.state["defect_handoffs"])
                with self.assertRaises(execution.ExecutionVNextError):
                    attempt.finalize_verified(actor_id="synthetic-tester")

        # Exact VERIFIED revalidation is revision-sensitive.
        with (self.fixture.app_root / "src/request.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# post-verification drift\n")
        with self.assertRaises(execution.ExecutionVNextError) as stale:
            straight.revalidate_verified()
        self.assertEqual(stale.exception.code, "EXECUTION_STALE")


if __name__ == "__main__":
    unittest.main()
