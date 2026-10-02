"""Fresh synthetic end-to-end fixtures. Never uses the Digital Wedding CR."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.lib import ba_kit, dev_kit as dev, dev_router, test_kit_v1 as design, test_kit_v1_cases as cases
from tooling.lib import execution_contract as execution, testware_promotion as promotion
from tooling.tests.test_sdlc_contracts import delivery_fixture
from tooling.tests.test_dev_kit import _planning_text, _advance_high_risk_to_plan_gate
from tooling import install_dev_kit, prepare_agent_profile
from tooling.sdlc_suite import check_runtime_ignores

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ref(path)


def ref(path):
    return {"path": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def git(project, *args):
    return subprocess.check_output(["git", "-C", str(project), *args], text=True, stderr=subprocess.DEVNULL).strip()


def init(project, lane):
    project.mkdir(parents=True, exist_ok=True)
    git(project, "init", "-b", "synthetic-readiness")
    git(project, "config", "user.name", "Synthetic Acceptance")
    git(project, "config", "user.email", "synthetic@example.invalid")
    ignores = ".test-kit/runs/\n.test-kit/runtime/\ntest-runs/\n.agents/skills/\n" if lane == "docs" else ".devkit/\n.specify/workflows/runs/\n__pycache__/\n"
    (project / ".gitignore").write_text(ignores, encoding="utf-8")
    (project / "AGENTS.md").write_text("# Synthetic fixture\nDev implements approved scope. Reviewer is read-only. Tester owns VERIFIED. Human gates are never inferred.\n", encoding="utf-8")


def receipt(snapshot, refs, gate):
    return {"gate": gate, "decision": "APPROVE", "artifact_id": snapshot.artifact_id,
            "artifact_revision": snapshot.revision, "artifact_sha256": snapshot.sha256,
            "input_refs": refs, "actor_id": "human:synthetic-fixture", "actor_role": "HUMAN",
            "decided_at": "2026-10-02T00:00:00Z", "feedback": "Synthetic contract fixture only"}


def fixture_actor(actor_id, _receipt):
    return design.AuthenticatedHumanActorContext(actor_id)


class FreshSyntheticAcceptance(unittest.TestCase):
    def test_same_session_no_ids_gates_promotion_and_clean_docs(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-test-") as temp:
            docs = Path(temp) / "docs"
            init(docs, "docs")
            feature = docs / "features/CR-001"
            feature.mkdir(parents=True)
            manifest, _ = delivery_fixture(feature)
            handoff = feature / "engineering-handoff.yml"
            skills = docs / ".agents/skills"
            for kit in ("ba", "test"):
                ba_kit.install(ROOT, skills, kit, project_root=docs)
                self.assertEqual(ba_kit.doctor(ROOT, skills, kit, project_root=docs)["status"], "READY")
            git(docs, "add", ".")
            git(docs, "commit", "-m", "Synthetic inputs and stable team configuration")
            config = ref(docs / "_bmad/tea/config.yaml")
            run = docs / ".test-kit/runs/CR-001/design-synthetic"
            prepared = design.prepare_same_session_design(handoff, run, project_root=docs,
                       skill_dir=skills / "bmad-testarch-test-design", delivery_path=manifest)
            # This current session supplies deterministic native-profile fixture output.
            raw = Path(prepared["raw_output_path"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("# Test Design: Epic 1 — CR-001\n\n## Test Coverage Plan\n\n### P0\nNone\n\n### P1\n\n"
                           "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |\n"
                           "|---|---|---|---|---|---|\n"
                           "| 1.0-UNIT-001 | Synthetic authority | UNIT | None | BAREF:SRS:001; BAREF:BR:001 | Approved synthetic result is observable. |\n\n### P2\nNone\n\n### P3\nNone\n", encoding="utf-8")
            self.assertEqual(design.finalize_same_session_design(handoff, run)["status"], "DESIGN_REVIEW")
            baseline = design.load_approved_baseline(handoff)
            snapshot = design.load_persisted_design_snapshot(run)
            gate = receipt(snapshot, design.design_gate_input_refs(baseline, run), "DESIGN_REVIEW")
            decision = design.apply_design_decision(run, snapshot, baseline, gate, human_actor_authenticator=fixture_actor)
            self.assertTrue(decision.accepted, decision.finding)
            promoted = promotion.promote(run, feature, baseline, stage="design", human_actor_authenticator=fixture_actor)
            self.assertEqual(promoted["semantic_sha256"], snapshot.sha256)
            case_run = docs / ".test-kit/runs/CR-001/cases-synthetic"
            prepared = cases.prepare_same_session_cases(handoff, run, case_run, project_root=docs,
                       skill_dir=skills / "create-test-cases", delivery_path=manifest)
            raw = Path(prepared["raw_output_path"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("## TC-001 Synthetic authority\n- Mô tả: Observe approved synthetic result\n"
                           "- Tiền điều kiện: OPEN execution dependencies: [ENVIRONMENT_ACCESS] synthetic staging address.\n"
                           "- Bước và kết quả mong đợi:\n  1. Perform approved synthetic operation. → Approved synthetic result is observable.\n"
                           "- Test Data: None\n- Priority: P1\n- Trace: BAREF:SRS:001, BAREF:BR:001; 1.0-UNIT-001\n", encoding="utf-8")
            finalized = cases.finalize_same_session_cases(handoff, case_run)
            self.assertEqual(finalized.status, "CASE_REVIEW")
            case_snapshot, state = cases.load_case_review_snapshot(case_run / "canonical/canonical-testcases.json", case_run / "workflow-state.json", case_run / "canonical/semantic-payload.json")
            design_snapshot, _, _ = cases._load_persisted_design_authorization(run, baseline)
            gate = receipt(case_snapshot, cases.case_gate_input_refs(baseline, design_snapshot, run_dir=case_run), "CASE_REVIEW")
            result = cases.apply_case_gate_decision(gate, case_snapshot, design_snapshot, baseline, state,
                       workflow_dir=case_run, human_actor_authenticator=fixture_actor)
            self.assertEqual(result.status, "STOP_V1", result.finding)
            promoted = promotion.promote(case_run, feature, baseline, stage="cases", human_actor_authenticator=fixture_actor)
            self.assertEqual(promoted["semantic_sha256"], case_snapshot.sha256)
            self.assertEqual((feature / "test/cases/testcases.json").read_bytes(), case_snapshot.payload_bytes)
            self.assertEqual(config, ref(docs / "_bmad/tea/config.yaml"))
            self.assertEqual(check_runtime_ignores(docs, "docs"), "PASS")
            git(docs, "add", "features/CR-001/test")
            git(docs, "commit", "-m", "Synthetic approved testware promotion")
            self.assertEqual(git(docs, "status", "--short"), "")
            # Exact old receipts and approved bytes cannot make drift healthy.
            (feature / "ux-contract.md").write_text("Changed UX", encoding="utf-8")
            with self.assertRaises(ValueError):
                design.current_delivery_refs(run)

    def test_natural_dev_router_normal_and_high_risk_boundary(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-dev-") as temp:
            root = Path(temp)
            app = root / "app"
            init(app, "app")
            git(app, "remote", "add", "origin", "https://github.com/fixture/app.git")
            (app / "selfcheck.py").write_text("assert sum([1, 2, 3]) == 6\n", encoding="utf-8")
            write_json(app / "quality-gate.json", {"checks": [
                {"name": "build", "category": "build", "argv": [sys.executable, "-m", "py_compile", "selfcheck.py"]},
                {"name": "tests", "category": "tests", "argv": [sys.executable, "selfcheck.py"]}]})
            git(app, "add", "."); git(app, "commit", "-m", "Synthetic application quality gate")
            docs = root / "feature"
            docs.mkdir()
            manifest, data = delivery_fixture(docs, False)
            data["targets"][0]["base_revision"] = git(app, "rev-parse", "HEAD")
            write_json(manifest, data)
            started = dev_router.start_from_delivery(app, manifest, "Implement synthetic local summary")
            self.assertEqual(started["route"]["risk_level"], "NORMAL")
            self.assertEqual(dev_router.start_from_delivery(app, manifest, "Resume synthetic") ["status"], "RESUMED")
            run = Path(started["run_dir"])
            inputs = dev._read_json(run / "input.json")
            dev.write_artifact(run / "spec-readiness.json", {"status": "READY_FOR_PLANNING", "business_ambiguities": []})
            dev.preflight(app)
            for filename in ("dev-plan.md", "dev-tasks.md"):
                (run / filename).write_text(_planning_text(inputs), encoding="utf-8")
            dev.validate_planning_artifacts(app)
            dev.assert_implementation_allowed(app, "normal")
            self.assertEqual(dev.run_checks(app, "fresh")["status"], "PASS")
            self.assertEqual(check_runtime_ignores(app, "app"), "PASS")
            self.assertEqual(git(app, "status", "--short"), "")
            data["delivery_revision"] = "CR-001-DELIVERY-002"
            write_json(manifest, data)
            with self.assertRaises(ValueError): dev._load_run(app)
            # Separate throwaway target for HIGH_RISK; no Human gate is approved.
            high = root / "high"
            init(high, "app")
            handoff = docs / "engineering-handoff.yml"
            checks = inputs["checks"]
            started = dev.start_run(high, "SYNTHETIC-HIGH", "feature", "Change synthetic authorization", baseline=handoff, checks=checks)
            self.assertTrue(started["route"]["human_gate_required"])
            paused = _advance_high_risk_to_plan_gate(high, Path(started["run_dir"]))
            self.assertNotEqual(paused.returncode, 0)
            self.assertFalse(dev._read_json(Path(started["run_dir"]) / "lifecycle.json")["human_gate"]["resolved"])

    def test_execution_classification_fix_retest_and_lane_guards(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-execution-") as temp:
            root = Path(temp)
            manifest, _ = delivery_fixture(root, False)
            testcase = write_json(root / "testcases.json", [{"testcase_id": "TC-SYNTHETIC", "expected": "3"}])
            receipt_ref = write_json(root / "receipt.json", {"fixture": "SYNTHETIC_ONLY"})
            approved = write_json(root / "promotion.json", {"stage": "cases", "approval_mode": "HUMAN_AUTHENTICATED",
                                  "semantic_sha256": testcase["sha256"], "approval_receipt_sha256": receipt_ref["sha256"]})
            handoff = write_json(root / "handoff.json", {"state": "READY_FOR_TEST", "implementation": {"commits": ["a" * 40]}})
            for kind in execution.DEPENDENCY_TYPES:
                state = execution.begin(approved, handoff, ref(manifest), [{"kind": kind, "status": "OPEN", "required": True}])
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    execution.transition(state, "READY", actor_role="TESTER")
            state = execution.begin(approved, handoff, ref(manifest), [])
            state = execution.transition(state, "READY", actor_role="TESTER")
            state = execution.transition(state, "EXECUTE", actor_role="TESTER")
            broken_add = lambda a, b: a - b
            observation = write_json(root / "observed.json", {"actual": str(broken_add(1, 2)), "expected": "3"})
            failed = write_json(root / "failed.json", {"status": "FAIL", "implementation_commit": "a" * 40, "testcase_id": "TC-SYNTHETIC",
                                "expected": "3", "actual": str(broken_add(1, 2)), "oracle_ref": testcase, "observation_ref": observation})
            state = execution.transition(state, "FAIL", actor_role="TESTER", evidence=failed)
            classify = write_json(root / "classification.json", {"implementation_commit": "a" * 40,
                                   "approved_expected": True, "reproducible": True, "test_environment_excluded": True})
            for classification, expected in execution.CLASSIFICATIONS.items():
                classified = execution.transition(state, "CLASSIFY", actor_role="TESTER", evidence=classify, classification=classification)
                self.assertEqual(execution.transition(classified, "ROUTE", actor_role="TESTER")["state"], expected)
            state = execution.transition(state, "CLASSIFY", actor_role="TESTER", evidence=classify, classification="DEFECT")
            state = execution.transition(state, "ROUTE", actor_role="TESTER")
            fixed_add = lambda a, b: a + b
            self.assertEqual(fixed_add(1, 2), 3)
            verified = write_json(root / "fresh-verification.json", {"actual": fixed_add(1, 2), "status": "PASS"})
            fix = write_json(root / "fix.json", {"implementation_commit": "b" * 40, "verification": "PASS", "verification_ref": verified})
            state = execution.transition(state, "FIX", actor_role="DEV", evidence=fix)
            ready = write_json(root / "retest-handoff.json", {"implementation_commit": "b" * 40, "state": "READY_FOR_RETEST"})
            state = execution.transition(state, "HANDOFF", actor_role="DEV", evidence=ready)
            state = execution.transition(state, "RETEST", actor_role="TESTER")
            observation = write_json(root / "reobserved.json", {"actual": str(fixed_add(1, 2)), "expected": "3"})
            passed = write_json(root / "passed.json", {"status": "PASS", "implementation_commit": "b" * 40, "testcase_id": "TC-SYNTHETIC",
                                "expected": "3", "actual": str(fixed_add(1, 2)), "oracle_ref": testcase, "observation_ref": observation})
            with self.assertRaises(ValueError): execution.transition(state, "PASS", actor_role="DEV", evidence=passed)
            self.assertEqual(execution.transition(state, "PASS", actor_role="TESTER", evidence=passed)["state"], "VERIFIED")
            with self.assertRaises(ValueError): execution.transition(state, "FAIL", actor_role="TESTER", evidence=failed)
            repeated = json.loads(Path(failed["path"]).read_text(encoding="utf-8"))
            repeated["implementation_commit"] = "b" * 40
            reopened = write_json(root / "reopened.json", repeated)
            self.assertEqual(execution.transition(state, "FAIL", actor_role="TESTER", evidence=reopened)["state"], "REOPENED")

    def test_profile_and_installed_dev_doctor(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-profile-") as temp:
            root = Path(temp)
            profile = root / "codex-home"
            prepare_agent_profile.prepare(ROOT, profile)
            app = root / "app"
            init(app, "app")
            purity = dev.inspect_context_purity(app, root, "benchmark", codex_home=profile)
            self.assertEqual(purity["context_purity"], "CLEAN", purity)
            installed = install_dev_kit.install(ROOT, root / "runtime-home")
            self.assertTrue((Path(installed["runtime_root"]) / "dev-kit/SKILL.md").is_file())
            # Hook contamination in the dedicated profile cannot be hidden by the global-home override.
            (profile / "config.toml").write_text('hooks = "unrelated methodology"\n', encoding="utf-8")
            purity = dev.inspect_context_purity(app, root, "benchmark", codex_home=profile)
            self.assertNotEqual(purity["context_purity"], "CLEAN")
