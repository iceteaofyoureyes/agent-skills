import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest import mock

from tooling.lib import test_kit_v1 as v1
from tooling.lib import test_kit_v1_cases as v1_cases
from tooling.lib import test_kit_vnext as vnext
from tooling.tests import test_ba_vnext as ba_tests
from tooling.tests import test_dev_vnext as dev_tests
from shared.sdlc.foundation.impact import knowledge_impact


ROOT = Path(__file__).resolve().parents[2]


class TestKitVNextAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.ux_counter = 0
        self.ba = ba_tests.BAVNextTests("test_greenfield_exact_baseline_and_handoff")
        self.ba.setUp()
        self.addCleanup(self.ba.doCleanups)
        state, self.ba_auth = self.ba.approved()
        handoff = self.ba_module().make_handoff(state, self.ba.root, human_actor_authenticator=self.ba_auth)
        self.handoff_path = self.ba.root / "engineering-handoff-vnext.json"
        self.handoff_path.write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")

    def ba_module(self):
        import ba_vnext
        return ba_vnext

    def ux_request(self, contract_text=None):
        self.ux_counter += 1
        root = self.ba.root / f"approved-ux-{self.ux_counter}"
        shutil.copytree(ROOT / "tooling/tests/fixtures/delivery-ux-canonical", root)
        contract = root / "ux/ux-contract.md"
        if contract_text is not None:
            contract.write_text(contract_text, encoding="utf-8")
        receipt_path = root / "ux/approval-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["feature_id"] = "FEATURE-1"
        receipt["sources"]["ux/ux-contract.md"] = hashlib.sha256(contract.read_bytes()).hexdigest()
        receipt["semantic_snapshot_sha256"] = hashlib.sha256(
            json.dumps(receipt["sources"], sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        request = {
            "root": str(root),
            "contract": {
                "path": "ux/ux-contract.md", "revision": receipt["revision"],
                "sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
            },
            "approval_receipt": {
                "path": "ux/approval-receipt.json",
                "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            },
            "prototype": {
                "path": "ux/prototype.html",
                "sha256": hashlib.sha256((root / "ux/prototype.html").read_bytes()).hexdigest(),
                "authority": "REVIEW_EVIDENCE",
            },
        }
        return request, receipt, contract

    def write_test_only_receipt(self, path, fixture_type, receipt):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "fixture_type": fixture_type,
            "not_for_production": True,
            "receipt": receipt,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def ux_design(self, title="Submit control confirms the selection.", expected=None):
        expected = expected or "An eligible member submits a request and receives the business outcome."
        return v1.DesignSnapshot.create((
            v1.CanonicalTestDesign("TD-UX", ("P1",), title, expected, ("BR-001", "FR-001"), ()),
        ), artifact_id="FEATURE-1-design", revision="1")

    def authority(self, authenticator=None):
        return vnext.load_vnext_authority(
            self.handoff_path,
            project_root=self.ba.root,
            human_actor_authenticator=authenticator or self.ba_auth,
        )

    def test_exact_ba_vnext_handoff_is_the_test_authority(self):
        authority = self.authority()

        self.assertEqual(authority.mode, "VNEXT")
        self.assertTrue(authority.vnext_authority)
        self.assertEqual(authority.baseline.feature_id, "FEATURE-1")
        self.assertEqual(authority.baseline.coverage_ids, {"BR-001", "FR-001"})
        self.assertEqual(authority.baseline.requirement_ids, {"FR-001"})
        self.assertIn("BA:BASELINE_CANDIDATE", {ref["id"] for ref in authority.refs})
        self.assertIn("BA:APPROVAL_RECEIPT", {ref["id"] for ref in authority.refs})

    def test_persisted_authority_refs_cannot_drift_from_hashed_bytes(self):
        authority = self.authority()
        run_dir = self.ba.root / ".test-kit/runs/FEATURE-1/context-drift"
        record = vnext.write_vnext_authority_context(run_dir, authority)
        record["refs"] = [ref for ref in record["refs"] if ref["id"] != "BA:BASELINE_CANDIDATE"]
        (run_dir / vnext.AUTHORITY_CONTEXT_PATH).write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
        )

        with self.assertRaisesRegex(vnext.TestAuthorityError, "refs differ"):
            vnext.revalidate_vnext_authority(
                run_dir, human_actor_authenticator=self.ba_auth,
            )

    def test_ba_bytes_are_rechecked_after_trusted_human_callback(self):
        def drifting_host(actor_id, receipt):
            accepted = self.ba_auth(actor_id, receipt)
            source = self.ba.root / "srs.md"
            source.write_bytes(source.read_bytes() + b"\nchanged during authentication")
            return accepted

        with self.assertRaises(vnext.TestAuthorityError):
            self.authority(drifting_host)

    def test_canonical_design_trace_rejects_baref(self):
        authority = self.authority()
        snapshot = v1.DesignSnapshot.create(
            (
                v1.CanonicalTestDesign("TD-001", ("P1",), "Eligibility", "Only eligible members may submit.", ("BR-001",), ()),
                v1.CanonicalTestDesign("TD-002", ("P1",), "Submit request", "An eligible member receives the business outcome.", ("FR-001", "BAREF:SRS:001"), ()),
            ),
            artifact_id="FEATURE-1-design",
            revision="1",
        )

        result = vnext.validate_vnext_design(snapshot, authority)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("BAREF_CANONICAL_TRACE_FORBIDDEN", {finding.code for finding in result.findings})

    def test_canonical_case_trace_rejects_baref(self):
        authority = self.authority()
        design = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign("TD-001", ("P1",), "Submit request", "An eligible member receives the business outcome.", ("BR-001", "FR-001"), ()),
        ), artifact_id="FEATURE-1-design", revision="1")
        case = v1_cases.CanonicalTestcase(
            "TC-001", "Submit request", "Check outcome", "An eligible member exists.", None,
            (v1_cases.CaseStep("Submit request", None, "The member receives the business outcome."),),
            "P1", ("BR-001", "FR-001", "BAREF:SRS:001"), ("TD-001",), (),
        )

        result = vnext.validate_vnext_cases(
            v1_cases.CaseSnapshot.create((case,), artifact_id="FEATURE-1-cases", revision="1"),
            design, authority,
        )

        self.assertEqual(result.status, "FAIL")
        self.assertIn("BAREF_CANONICAL_TRACE_FORBIDDEN", {finding.code for finding in result.findings})

    def test_no_ux_design_reaches_human_review_and_approval(self):
        skill_dir = self.ba.root / ".agents/skills/bmad-testarch-test-design"
        shutil.copytree(ROOT / "kits/test/skills/bmad-testarch-test-design", skill_dir)
        policy_root = self.ba.root / ".test-kit"
        (policy_root / "rules").mkdir(parents=True)
        (policy_root / "project.yaml").write_text("""schema_version: 1
profile:
  id: synthetic-test-guidance
  revision: "1"
rules:
  common:
    - rules/common.md
  test_design:
    - rules/test-design.md
  testcases:
    - rules/testcases.md
templates: {}
""", encoding="utf-8")
        for name, text in (
            ("common.md", "Preserve unresolved business questions.\n"),
            ("test-design.md", "Prefer clear scenario names.\n"),
            ("testcases.md", "Keep manual actions concise.\n"),
        ):
            (policy_root / "rules" / name).write_text(text, encoding="utf-8")
        config = self.ba.root / "_bmad/tea/config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("output_folder: .test-kit/runtime\ntest_artifacts: .test-kit/runtime\n", encoding="utf-8")
        run_dir = self.ba.root / ".test-kit/runs/FEATURE-1/design-001"

        prepared = vnext.prepare_vnext_design(
            self.handoff_path, run_dir,
            project_root=self.ba.root,
            skill_dir=skill_dir,
            human_actor_authenticator=self.ba_auth,
        )
        raw = Path(prepared["raw_output_path"])
        raw.write_text("""# Test Design: Epic 1 — Collection requests
## Test Coverage Plan
### P0 — Critical
None.
### P1 — High
| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|
| TD-001 | Submit an eligible collection request | API | — | BR-001; FR-001 | An eligible member submits a request and receives the business outcome. |
### P2 — Medium
None.
### P3 — Low
None.
""", encoding="utf-8")

        finalized = vnext.finalize_vnext_design(
            self.handoff_path, run_dir,
            human_actor_authenticator=self.ba_auth,
        )

        self.assertEqual(finalized["status"], "DESIGN_REVIEW")
        for shortcut in ("CONTINUE", "REVIEW", "PASS", "ANSWER", "TEA_COMPLETE"):
            rejected = vnext.apply_vnext_design_decision(
                run_dir, {"gate": "DESIGN_REVIEW", "decision": shortcut},
                human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
                ba_human_actor_authenticator=self.ba_auth,
            )
            self.assertFalse(rejected.accepted, shortcut)
        for prose in ({"state": "APPROVED_DESIGN"}, {"gate": "DESIGN_REVIEW", "status": "APPROVED"}):
            rejected = vnext.apply_vnext_design_decision(
                run_dir, prose,
                human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
                ba_human_actor_authenticator=self.ba_auth,
            )
            self.assertFalse(rejected.accepted, prose)
        design_resume_script = (
            "import json,sys\n"
            "from pathlib import Path\n"
            "from tooling.lib.test_kit_vnext import resume_vnext_design\n"
            "root, run_dir = map(Path, sys.argv[1:3])\n"
            "receipt = json.loads((root/'receipt.json').read_text(encoding='utf-8'))\n"
            "auth = lambda actor, actual: actor == 'synthetic-human' and actual == receipt\n"
            "workflow, snapshot = resume_vnext_design(run_dir, ba_human_actor_authenticator=auth)\n"
            "print(json.dumps({'state': workflow['state'], 'sha256': snapshot.sha256}))\n"
        )
        design_resumed = subprocess.run(
            [sys.executable, "-c", design_resume_script, str(self.ba.root), str(run_dir)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(design_resumed.returncode, 0, design_resumed.stderr)
        self.assertIn('"state": "DESIGN_REVIEW"', design_resumed.stdout)
        snapshot = v1.load_persisted_design_snapshot(run_dir, require_state="DESIGN_REVIEW")
        authority = self.authority()
        with mock.patch.object(vnext.design, "load_approved_baseline") as legacy_reader:
            with self.assertRaisesRegex(vnext.TestAuthorityError, "already revalidated VNext baseline"):
                vnext.design_gate_input_refs(run_dir)
            legacy_reader.assert_not_called()
        receipt = {
            "gate": "DESIGN_REVIEW", "decision": "APPROVE",
            "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": vnext.design_gate_input_refs(run_dir, authority.baseline),
            "actor_id": "TEST_ONLY:synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-04T10:00:00Z", "feedback": "",
        }
        design_fixture = self.write_test_only_receipt(
            self.ba.root / "test-only-design-gate-fixture.json",
            "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT", receipt,
        )
        design_policy = policy_root / "rules/test-design.md"
        original_design_policy = design_policy.read_bytes()
        design_policy.write_bytes(original_design_policy + b"changed after review\n")
        stale_design = vnext.apply_vnext_design_decision(
            run_dir, receipt, human_actor_authenticator=None,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_fixture_path=design_fixture,
        )
        self.assertFalse(stale_design.accepted)
        design_policy.write_bytes(original_design_policy)
        approved = vnext.apply_vnext_design_decision(
            run_dir, receipt,
            human_actor_authenticator=None,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_fixture_path=design_fixture,
        )

        self.assertTrue(approved.accepted)
        self.assertEqual(approved.state.state, "APPROVED_DESIGN")
        design_workflow = json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))
        self.assertEqual(design_workflow["design_gate_receipt_mode"], "TEST_ONLY")
        xmind_projection = vnext.export_vnext_approved_design_xmind(
            run_dir, run_dir / "derived/xmind",
            human_actor_authenticator=None,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_receipt_fixture_path=design_fixture,
        )
        self.assertEqual(xmind_projection.semantic_diff.status, "PASS")
        xmind_manifest = json.loads(xmind_projection.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(xmind_manifest["authority"], "DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH")
        self.assertEqual(xmind_manifest["design_gate_receipt_mode"], "TEST_ONLY")
        self.assertEqual(xmind_manifest["canonical_semantic_sha256"], snapshot.sha256)

        katalon_skill = self.ba.root / ".agents/skills/create-test-cases"
        shutil.copytree(ROOT / "kits/test/skills/create-test-cases", katalon_skill)
        case_run = self.ba.root / ".test-kit/runs/FEATURE-1/cases-001"
        case_prepare = vnext.prepare_test_only_vnext_cases(
            self.handoff_path, run_dir, case_run,
            project_root=self.ba.root, skill_dir=katalon_skill,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_design_fixture_path=design_fixture,
        )
        case_raw = Path(case_prepare["raw_output_path"])
        case_raw.write_text("\n".join([
            "# Manual Test Cases", "", "## TC-001 Submit an eligible request", "",
            "- Mô tả: Verify an eligible member can submit a collection request.",
            "- Tiền điều kiện: An eligible member exists.",
            "- Bước và kết quả mong đợi:",
            "  1. Submit a collection request. → The eligible member receives the business outcome.",
            "- Test Data: Eligible member", "- Priority: P1.", "- Trace: BR-001; FR-001; TD-001", "",
        ]), encoding="utf-8")
        case_result = vnext.finalize_test_only_vnext_cases(
            self.handoff_path, case_run,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_design_fixture_path=design_fixture,
        )
        self.assertEqual(case_result.status, "CASE_REVIEW")
        self.assertEqual(case_result.workflow.terminal_state, "APPROVED_TESTWARE")
        rejected_case = vnext.apply_vnext_case_decision(
            case_run, {"gate": "CASE_REVIEW", "decision": "PASS"},
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            ba_human_actor_authenticator=self.ba_auth,
        )
        self.assertEqual(rejected_case.status, "REJECTED")
        for shortcut in ("CONTINUE", "REVIEW", "ANSWER", "KATALON_COMPLETE", "APPROVED_TESTWARE"):
            rejected_case = vnext.apply_vnext_case_decision(
                case_run, {"gate": "CASE_REVIEW", "decision": shortcut},
                human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
                ba_human_actor_authenticator=self.ba_auth,
            )
            self.assertEqual(rejected_case.status, "REJECTED", shortcut)
        rejected_state_prose = vnext.apply_vnext_case_decision(
            case_run, {"state": "APPROVED_TESTWARE"},
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            ba_human_actor_authenticator=self.ba_auth,
        )
        self.assertEqual(rejected_state_prose.status, "REJECTED")

        # Resume the persisted Case Review in a fresh Python process.
        script = (
            "import json,sys\n"
            "from pathlib import Path\n"
            "from tooling.lib.test_kit_vnext import resume_vnext_cases\n"
            "root, run_dir = map(Path, sys.argv[1:3])\n"
            "receipt = json.loads((root/'receipt.json').read_text(encoding='utf-8'))\n"
            "auth = lambda actor, actual: actor == 'synthetic-human' and actual == receipt\n"
            "workflow, snapshot, state = resume_vnext_cases(run_dir, ba_human_actor_authenticator=auth)\n"
            "print(json.dumps({'state': workflow['state'], 'sha256': snapshot.sha256, 'terminal': state.terminal_state}))\n"
        )
        resumed = subprocess.run(
            [sys.executable, "-c", script, str(self.ba.root), str(case_run)],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertIn('"state": "CASE_REVIEW"', resumed.stdout)
        self.assertIn('"terminal": "APPROVED_TESTWARE"', resumed.stdout)

        approved_design = v1.load_persisted_design_snapshot(run_dir, require_state="APPROVED_DESIGN")
        case_snapshot, _ = v1_cases.load_case_review_snapshot(
            case_run / "canonical/canonical-testcases.json",
            case_run / "workflow-state.json",
            case_run / "canonical/semantic-payload.json",
        )
        authority = self.authority()
        case_receipt = {
            "gate": "CASE_REVIEW", "decision": "APPROVE",
            "artifact_id": case_snapshot.artifact_id, "artifact_revision": case_snapshot.revision,
            "artifact_sha256": case_snapshot.sha256,
            "input_refs": v1_cases.case_gate_input_refs(authority.baseline, approved_design, run_dir=case_run),
            "actor_id": "TEST_ONLY:synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-04T10:05:00Z", "feedback": "",
        }
        case_fixture = self.write_test_only_receipt(
            self.ba.root / "test-only-case-gate-fixture.json",
            "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT", case_receipt,
        )
        case_policy = policy_root / "rules/testcases.md"
        original_case_policy = case_policy.read_bytes()
        case_policy.write_bytes(original_case_policy + b"changed after review\n")
        stale_case = vnext.apply_vnext_case_decision(
            case_run, case_receipt, human_actor_authenticator=None,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_fixture_path=case_fixture,
        )
        self.assertEqual(stale_case.status, "REJECTED")
        case_policy.write_bytes(original_case_policy)
        case_approval = vnext.apply_vnext_case_decision(
            case_run, case_receipt,
            human_actor_authenticator=None,
            ba_human_actor_authenticator=self.ba_auth,
            test_only_fixture_path=case_fixture,
        )
        self.assertEqual(case_approval.status, "APPROVED_TESTWARE", case_approval.finding)
        manifest = json.loads((case_run / "approved-testware-vnext.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["fixture_type"], "TEST_ONLY_APPROVED_TESTWARE_EVIDENCE")
        self.assertIs(manifest["not_for_production"], True)
        manifest = manifest["approved_testware"]
        self.assertEqual(manifest["artifact_class"], "HANDOFF_MANIFEST")
        self.assertEqual(manifest["state"], "APPROVED_TESTWARE")
        self.assertNotIn("expected_behavior", manifest)
        self.assertTrue({
            "schema_version", "feature_id", "testcase_collection", "approved_design",
            "design_gate_receipt", "case_gate_receipt", "ba_engineering_handoff",
            "ba_baseline", "ux_context", "dev_context", "execution_oracle_refs",
            "project_policy_context", "trace_summary", "state",
        }.issubset(manifest))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["trace_summary"]["requirement_ids"], ["BR-001", "FR-001"])
        self.assertTrue(all(ref.startswith(("BR-", "FR-")) for ref in manifest["trace_summary"]["requirement_ids"]))
        self.assertIsNone(manifest["ux_context"])
        self.assertIsNone(manifest["dev_context"])
        self.assertEqual(manifest["execution_oracle_refs"], [])
        self.assertIn(manifest["project_policy_context"], manifest["input_refs"])
        excel_workflow = json.loads((case_run / "case-gate/workflow-state.json").read_text(encoding="utf-8"))
        self.assertTrue(
            excel_workflow.get("review_status") == "APPROVED"
            and excel_workflow.get("validation_status") == "PASS"
            and excel_workflow.get("test_only") is True
            and excel_workflow.get("design_gate_receipt_mode") == "TEST_ONLY",
            excel_workflow,
        )
        excel_projection = vnext.export_vnext_approved_testware_excel(
            case_run, run_dir, case_run / "derived/excel",
            human_actor_authenticator=None,
            ba_human_actor_authenticator=self.ba_auth,
            project_root=self.ba.root,
            test_only_receipt_fixture_path=case_fixture,
        )
        self.assertEqual(excel_projection.semantic_diff.status, "PASS")
        excel_manifest = json.loads(excel_projection.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(excel_manifest["authority"], "DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH")
        self.assertIs(excel_manifest["test_only"], True)
        self.assertIs(excel_manifest["not_for_production"], True)
        self.assertEqual(excel_manifest["canonical_semantic_sha256"], case_snapshot.sha256)

    def test_v1_handoff_is_inspectable_but_cannot_authorize_vnext(self):
        legacy = vnext.read_legacy_compat(ROOT / "tooling/tests/fixtures/ba-v1-legacy-compat/05-engineering-handoff.yml")
        legacy_design = vnext.read_legacy_compat(run_dir=ROOT / "benchmark/test-kit/petclinic/foundation-v1-native-profiled")
        legacy_testware = vnext.read_legacy_compat(run_dir=ROOT / "benchmark/test-kit/petclinic/fixtures/test-only-approved-testware-v1")

        self.assertEqual(legacy["mode"], "LEGACY_COMPAT")
        self.assertFalse(legacy["vnext_authority"])
        self.assertFalse(legacy_design["vnext_authority"])
        self.assertFalse(legacy_testware["vnext_authority"])
        self.assertIn("approved-testware.json", legacy_testware["artifacts"])

    def test_explicit_ux_requirement_blocks_without_approved_context(self):
        authority = self.authority()
        authority = vnext.replace(authority, ux_required=True)

        result = vnext.validate_vnext_design(self.ux_design(), authority)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("UX_APPROVAL_REQUIRED", {finding.code for finding in result.findings})

    def test_ux_words_in_business_and_technical_prose_do_not_require_ux(self):
        authority = self.authority()
        for title, expected in (
            ("API response field contains the request ID", "API response field is returned"),
            ("Input payload includes a member name", "Input payload is retained"),
            ("Page number is preserved", "The requested page number is returned"),
        ):
            with self.subTest(title=title):
                result = vnext.validate_vnext_design(self.ux_design(title, expected), authority)
                self.assertEqual(result.status, "PASS", result.findings)

    def test_case_ux_words_do_not_require_context_unless_explicitly_required(self):
        authority = self.authority()
        design = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign(
                "TD-001", ("P1",), "Submit request",
                "An eligible member receives the business outcome.", ("BR-001", "FR-001"), (),
            ),
        ), artifact_id="FEATURE-1-design", revision="1")
        case = v1_cases.CanonicalTestcase(
            "TC-001", "Submit control confirms the selection", "Check request submission",
            "An eligible member exists.", None,
            (v1_cases.CaseStep("Submit request", None, "The member receives the business outcome."),),
            "P1", ("BR-001", "FR-001"), ("TD-001",), (),
        )
        snapshot = v1_cases.CaseSnapshot.create((case,), artifact_id="FEATURE-1-cases", revision="1")

        without_ux = vnext.validate_vnext_cases(snapshot, design, authority)
        self.assertEqual(without_ux.status, "PASS", without_ux.findings)

        required = vnext.validate_vnext_cases(snapshot, design, vnext.replace(authority, ux_required=True))
        self.assertEqual(required.status, "FAIL")
        self.assertIn("UX_APPROVAL_REQUIRED", {finding.code for finding in required.findings})
        request, receipt, _ = self.ux_request()
        approved_ux = vnext.load_approved_ux_context(
            request, feature_id="FEATURE-1",
            human_actor_authenticator=lambda actor, actual: actor == "Human" and actual == receipt,
        )
        approved = vnext.validate_vnext_cases(
            snapshot, design, vnext.replace(authority, ux_context=approved_ux, ux_required=False),
        )
        self.assertEqual(approved.status, "PASS", approved.findings)
        invented = v1_cases.CaseSnapshot.create((
            v1_cases.replace(case, name="Submit control changes to blue"),
        ), artifact_id="FEATURE-1-cases-blue", revision="1")
        human_review = vnext.validate_vnext_cases(
            invented, design, vnext.replace(authority, ux_context=approved_ux, ux_required=False),
        )
        self.assertEqual(human_review.status, "PASS", human_review.findings)

    def test_exact_approved_ux_context_supports_interaction_assertion(self):
        request, receipt, _ = self.ux_request()
        context = vnext.load_approved_ux_context(
            request, feature_id="FEATURE-1",
            human_actor_authenticator=lambda actor, actual: actor == "Human" and actual == receipt,
        )
        authority = vnext.replace(self.authority(), ux_context=context, ux_required=True)

        result = vnext.validate_vnext_design(self.ux_design(), authority)

        self.assertEqual(result.status, "PASS", result.findings)
        self.assertEqual(context["prototype_authority"], "REVIEW_EVIDENCE")

    def test_approved_ux_refs_bind_the_design_gate_and_stale_bytes_reject_projection(self):
        request, ux_receipt, contract = self.ux_request()
        ux_auth = lambda actor, actual: actor == "Human" and actual == ux_receipt
        skill_dir = self.ba.root / ".agents/skills/bmad-testarch-test-design"
        shutil.copytree(ROOT / "kits/test/skills/bmad-testarch-test-design", skill_dir)
        config = self.ba.root / "_bmad/tea/config.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("output_folder: .test-kit/runtime\ntest_artifacts: .test-kit/runtime\n", encoding="utf-8")
        run_dir = self.ba.root / ".test-kit/runs/FEATURE-1/design-ux"
        prepared = vnext.prepare_vnext_design(
            self.handoff_path, run_dir, project_root=self.ba.root, skill_dir=skill_dir,
            human_actor_authenticator=self.ba_auth,
            ux_context=request, ux_required=True,
            ux_human_actor_authenticator=ux_auth,
        )
        Path(prepared["raw_output_path"]).write_text("\n".join([
            "# Test Design: Epic 1 — Collection requests", "## Test Coverage Plan",
            "### P0 — Critical", "None.", "### P1 — High",
            "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |",
            "|---|---|---|---|---|---|",
            "| TD-UX | Submit control confirms the selection | API | — | BR-001; FR-001 | An eligible member submits a request and receives the business outcome. |",
            "### P2 — Medium", "None.", "### P3 — Low", "None.",
        ]), encoding="utf-8")
        finalized = vnext.finalize_vnext_design(
            self.handoff_path, run_dir, human_actor_authenticator=self.ba_auth,
            ux_human_actor_authenticator=ux_auth,
        )
        self.assertEqual(finalized["status"], "DESIGN_REVIEW")
        authority = vnext.revalidate_vnext_authority(
            run_dir, human_actor_authenticator=self.ba_auth,
            ux_human_actor_authenticator=ux_auth,
        )
        snapshot = v1.load_persisted_design_snapshot(run_dir, require_state="DESIGN_REVIEW")
        refs = vnext.design_gate_input_refs(run_dir, authority.baseline)
        self.assertIn("FEATURE-1:UX", {ref["id"] for ref in refs})
        receipt = {
            "gate": "DESIGN_REVIEW", "decision": "APPROVE",
            "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256, "input_refs": refs,
            "actor_id": "synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-04T10:10:00Z", "feedback": "",
        }
        approved = vnext.apply_vnext_design_decision(
            run_dir, receipt,
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            ba_human_actor_authenticator=self.ba_auth,
            ux_human_actor_authenticator=ux_auth,
        )
        self.assertTrue(approved.accepted)
        case_run = self.ba.root / ".test-kit/runs/FEATURE-1/cases-with-ux"
        vnext.copy_vnext_authority_context(run_dir, case_run)
        case_refs = v1_cases.case_gate_input_refs(authority.baseline, snapshot, run_dir=case_run)
        self.assertIn("FEATURE-1:UX", {ref["id"] for ref in case_refs})
        self.assertIn("FEATURE-1:UX_RECEIPT", {ref["id"] for ref in case_refs})
        contract.write_bytes(contract.read_bytes() + b"\nstale")
        with self.assertRaises(vnext.TestAuthorityError):
            vnext.revalidate_vnext_authority(
                run_dir, human_actor_authenticator=self.ba_auth,
                ux_human_actor_authenticator=ux_auth,
            )

    def test_prototype_alone_cannot_authorize_ux_semantics(self):
        request, _, _ = self.ux_request()
        with self.assertRaises(vnext.TestAuthorityError):
            vnext.load_approved_ux_context(
                {"root": request["root"], "prototype": request["prototype"]},
                feature_id="FEATURE-1", human_actor_authenticator=lambda *_: True,
            )

    def test_stale_ux_bytes_and_receipt_fail_closed(self):
        request, _, contract = self.ux_request()
        contract.write_bytes(contract.read_bytes() + b"\nchanged")
        with self.assertRaisesRegex(vnext.TestAuthorityError, "contract hash mismatch"):
            vnext.load_approved_ux_context(request, feature_id="FEATURE-1", human_actor_authenticator=lambda *_: True)

        request, _, _ = self.ux_request()
        receipt = Path(request["root"]) / request["approval_receipt"]["path"]
        receipt.write_bytes(receipt.read_bytes() + b"\n")
        with self.assertRaisesRegex(vnext.TestAuthorityError, "receipt bytes are stale"):
            vnext.load_approved_ux_context(request, feature_id="FEATURE-1", human_actor_authenticator=lambda *_: True)

    def test_ux_contract_and_receipt_bytes_are_rechecked_after_human_callback(self):
        for target in ("contract", "receipt"):
            with self.subTest(target=target):
                request, receipt, contract = self.ux_request()
                receipt_path = Path(request["root"]) / request["approval_receipt"]["path"]

                def drifting_host(actor, actual):
                    path = contract if target == "contract" else receipt_path
                    path.write_bytes(path.read_bytes() + b"\nchanged during authentication")
                    return actor == "Human" and actual == receipt

                with self.assertRaisesRegex(vnext.TestAuthorityError, "changed during trusted Human authentication"):
                    vnext.load_approved_ux_context(
                        request, feature_id="FEATURE-1", human_actor_authenticator=drifting_host,
                    )

    def test_unauthenticated_ux_human_fails(self):
        request, _, _ = self.ux_request()
        with self.assertRaisesRegex(vnext.TestAuthorityError, "trusted Human authentication"):
            vnext.load_approved_ux_context(request, feature_id="FEATURE-1", human_actor_authenticator=lambda *_: False)

    def test_free_form_ux_consistency_is_left_to_human_review(self):
        request, receipt, _ = self.ux_request("The submit control is disabled for eligible members.\n")
        context = vnext.load_approved_ux_context(
            request, feature_id="FEATURE-1",
            human_actor_authenticator=lambda actor, actual: actor == "Human" and actual == receipt,
        )
        authority = vnext.replace(self.authority(), ux_context=context, ux_required=True)
        result = vnext.validate_vnext_design(
            self.ux_design("Submit control enabled for eligible members."), authority,
        )
        self.assertEqual(result.status, "PASS", result.findings)

    def test_ba_unknown_stays_deferred_and_cannot_become_a_case_result(self):
        srs = self.ba.root / "srs.md"
        srs.write_text(
            "# Collection requests\n\n## FR-001 Submit request\n"
            "CONFIRMED: An eligible member submits a request and receives the business outcome.\n"
            "UNKNOWN: The maximum processing duration is UNKNOWN.\n",
            encoding="utf-8",
        )
        self.ba.sources["srs"] = self.ba.ref("srs.md")
        decisions = self.ba.load("decisions.json")
        decisions["decisions"][0]["implemented_sources"] = {
            role: self.ba.sources[role] for role in ("business_rules", "srs")
        }
        self.ba.put("decisions.json", decisions)
        self.ba.sources["decisions"] = self.ba.ref("decisions.json")
        candidate = self.ba_module().make_candidate(
            self.ba.root, feature={"id": "FEATURE-1", "title": "Collection requests"},
            baseline_id="BA-1", revision="R2", sources=self.ba.sources,
            business_identities=[
                {"id": "BR-001", "semantic_key": "eligibility", "status": "ACTIVE"},
                {"id": "FR-001", "semantic_key": "submit-request", "status": "ACTIVE"},
            ], knowledge=knowledge_impact(), non_blocking=["Processing duration remains UNKNOWN."],
        )
        self.ba.candidate = candidate
        self.ba.candidate_ref = self.ba.publish(candidate)
        self.ba.state = self.ba_module().select_candidate(
            self.ba_module().new_state(candidate["feature"], "GREENFIELD"),
            self.ba.candidate_ref, self.ba.root,
        )
        state, self.ba_auth = self.ba.approved()
        handoff = self.ba_module().make_handoff(state, self.ba.root, human_actor_authenticator=self.ba_auth)
        self.handoff_path.write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
        authority = self.authority()
        unknown_text = authority.baseline.unknown_clauses["FR-001"]
        design = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign("TD-001", ("P1",), "Submit request", "An eligible member receives the business outcome.", ("BR-001", "FR-001"), ()),
            v1.CanonicalTestDesign("TD-002", ("P2",), "Maximum duration remains deferred", None, ("FR-001",), (v1.OpenQuestion("FR-001", unknown_text),)),
        ), artifact_id="FEATURE-1-design", revision="1")
        design_result = vnext.validate_vnext_design(design, authority)
        self.assertEqual(design_result.status, "PASS", design_result.findings)
        case = v1_cases.CanonicalTestcase(
            "TC-001", "Check processing duration", "Check the approved duration",
            "An eligible member exists.", None,
            (v1_cases.CaseStep("Submit a request", None, "The maximum processing duration is five minutes."),),
            "P1", ("FR-001",), ("TD-001",), (),
        )
        result = vnext.validate_vnext_cases(
            v1_cases.CaseSnapshot.create((case,), artifact_id="FEATURE-1-cases", revision="1"),
            design, authority,
        )
        self.assertEqual(result.status, "FAIL")
        self.assertTrue({"UNKNOWN_ASSERTION_LEAK", "EXPECTED_RESULT_AUTHORITY_CONFLICT"} & {finding.code for finding in result.findings})

    def test_design_request_changes_preserves_reviewed_bytes_and_rejects_old_receipt(self):
        authority = self.authority()
        run_dir = self.ba.root / ".test-kit/runs/FEATURE-1/design-changes"
        saved = vnext.write_vnext_authority_context(run_dir, authority)
        bundle = v1.adapt_ba_to_tea(self.handoff_path, baseline=authority.baseline)
        bundle = v1.replace(bundle, authority_refs=tuple(saved["byte_refs"]))
        snapshot = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign("TD-001", ("P1",), "Submit request", "An eligible member receives the business outcome.", ("BR-001", "FR-001"), ()),
        ), artifact_id="FEATURE-1-design", revision="1")
        validation = vnext.validate_vnext_design(snapshot, authority)
        state = v1.submit_design_for_review(v1.start_design_workflow(snapshot), snapshot, validation)
        raw = run_dir / "raw-output/test-design.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("synthetic TEA evidence\n", encoding="utf-8")
        v1.persist_design_review(run_dir, bundle, raw, snapshot, validation, state)
        receipt = {
            "gate": "DESIGN_REVIEW", "decision": "REQUEST_CHANGES",
            "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": vnext.design_gate_input_refs(run_dir, authority.baseline),
            "actor_id": "synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-04T10:20:00Z", "feedback": "Clarify the test data boundary.",
        }

        result = vnext.apply_vnext_design_decision(
            run_dir, receipt,
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            ba_human_actor_authenticator=self.ba_auth,
            next_revision="2",
        )

        self.assertTrue(result.accepted)
        self.assertEqual(result.state.state, "DRAFT_DESIGN")
        self.assertEqual(result.next_snapshot.revision, "2")
        self.assertEqual(result.next_snapshot.sha256, snapshot.sha256)
        self.assertEqual((run_dir / "canonical/semantic-payload.json").read_bytes(), snapshot.payload_bytes)
        with self.assertRaises(ValueError):
            vnext.apply_vnext_design_decision(
                run_dir, receipt,
                human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
                ba_human_actor_authenticator=self.ba_auth,
                next_revision="3",
            )

    def test_case_request_changes_keeps_reviewed_snapshot_and_rejects_old_receipt(self):
        authority = self.authority()
        design_run = self.ba.root / ".test-kit/runs/FEATURE-1/design-for-case-changes"
        saved = vnext.write_vnext_authority_context(design_run, authority)
        bundle = v1.adapt_ba_to_tea(self.handoff_path, baseline=authority.baseline)
        bundle = v1.replace(bundle, authority_refs=tuple(saved["byte_refs"]))
        approved_design = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign("TD-001", ("P1",), "Submit request", "An eligible member receives the business outcome.", ("BR-001", "FR-001"), ()),
        ), artifact_id="FEATURE-1-design", revision="1")
        design_validation = vnext.validate_vnext_design(approved_design, authority)
        design_state = v1.submit_design_for_review(v1.start_design_workflow(approved_design), approved_design, design_validation)
        design_raw = design_run / "raw-output/test-design.md"
        design_raw.parent.mkdir(parents=True)
        design_raw.write_text("synthetic TEA evidence\n", encoding="utf-8")
        v1.persist_design_review(design_run, bundle, design_raw, approved_design, design_validation, design_state)
        design_receipt = {
            "gate": "DESIGN_REVIEW", "decision": "APPROVE",
            "artifact_id": approved_design.artifact_id, "artifact_revision": approved_design.revision,
            "artifact_sha256": approved_design.sha256,
            "input_refs": vnext.design_gate_input_refs(design_run, authority.baseline),
            "actor_id": "synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-04T10:25:00Z", "feedback": "",
        }
        self.assertTrue(vnext.apply_vnext_design_decision(
            design_run, design_receipt,
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            ba_human_actor_authenticator=self.ba_auth,
        ).accepted)
        persisted_design_receipt = design_run / "design-gate/revisions/1/receipt.json"
        case_run = self.ba.root / ".test-kit/runs/FEATURE-1/case-changes"
        vnext.copy_vnext_authority_context(design_run, case_run)
        raw = case_run / "raw-output/test-cases.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("\n".join([
            "# Manual Test Cases", "", "## TC-001 Submit an eligible request", "",
            "- Mô tả: Verify an eligible member can submit a collection request.",
            "- Tiền điều kiện: An eligible member exists.", "- Bước và kết quả mong đợi:",
            "  1. Submit a collection request. → The eligible member receives the business outcome.",
            "- Test Data: Eligible member", "- Priority: P1.", "- Trace: BR-001; FR-001; TD-001", "",
        ]), encoding="utf-8")
        raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
        policy_context = v1.persist_project_policy_context(case_run, self.ba.root, "CASES")
        manifest = {
            "mode": "SAME_SESSION", "status": "ARTIFACT_COMPLETE",
            "raw_output_path": str(raw), "raw_output_sha256": raw_hash,
            "receipt_mode": "HUMAN_AUTHENTICATED",
            "design_gate_receipt_evidence": {
                "mode": "HUMAN_AUTHENTICATED", "path": str(persisted_design_receipt),
                "sha256": hashlib.sha256(persisted_design_receipt.read_bytes()).hexdigest(),
            },
            "project_policy_context": policy_context,
        }
        integration = v1_cases._finish_case_integration(
            manifest, approved_design, authority.baseline, case_run,
            execution_contract_refs=(), artifact_id="FEATURE-1-testcases", revision="1",
            terminal_state="APPROVED_TESTWARE", vnext_authority=True,
        )
        self.assertEqual(integration.status, "CASE_REVIEW", integration.normalization.findings)
        self.assertIsNone(v1_cases._validate_design_gate_evidence(
            integration.workflow, approved_design, authority.baseline,
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            test_only=False,
        ))
        current_case_refs = v1_cases.case_gate_input_refs(authority.baseline, approved_design, run_dir=case_run)
        self.assertEqual(vnext._ref_signature(current_case_refs), tuple(sorted(integration.workflow.input_refs)))
        _, persisted_case_state = v1_cases.load_case_review_snapshot(
            case_run / "canonical/canonical-testcases.json", case_run / "workflow-state.json",
            case_run / "canonical/semantic-payload.json",
        )
        self.assertEqual(vnext._ref_signature(current_case_refs), tuple(sorted(persisted_case_state.input_refs)))
        self.assertEqual(persisted_case_state.design_gate_receipt_evidence, integration.workflow.design_gate_receipt_evidence)
        vnext.revalidate_vnext_authority(case_run, human_actor_authenticator=self.ba_auth)
        design_gate_receipt = json.loads(persisted_design_receipt.read_text(encoding="utf-8"))
        self.assertEqual(
            v1._design_receipt_refs(design_gate_receipt),
            tuple((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in v1.design_gate_input_refs(authority.baseline, design_run)),
        )
        snapshot = integration.normalization.snapshot
        receipt = {
            "gate": "CASE_REVIEW", "decision": "REQUEST_CHANGES",
            "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": v1_cases.case_gate_input_refs(authority.baseline, approved_design, run_dir=case_run),
            "actor_id": "synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-04T10:30:00Z", "feedback": "Clarify the observation step.",
        }

        result = vnext.apply_vnext_case_decision(
            case_run, receipt,
            human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
            ba_human_actor_authenticator=self.ba_auth,
            next_revision="2",
        )

        self.assertEqual(result.status, "DRAFT_CASES", result.finding)
        self.assertEqual(result.reviewed_snapshot.sha256, snapshot.sha256)
        self.assertEqual(result.next_snapshot.revision, "2")
        self.assertEqual(result.workflow.terminal_state, "APPROVED_TESTWARE")
        self.assertEqual((case_run / "canonical/semantic-payload.json").read_bytes(), snapshot.payload_bytes)
        with self.assertRaises(ValueError):
            vnext.apply_vnext_case_decision(
                case_run, receipt,
                human_actor_authenticator=lambda actor, _receipt: v1.AuthenticatedHumanActorContext(actor),
                ba_human_actor_authenticator=self.ba_auth,
            )

    def test_exact_dev_context_resolves_technical_dependency_without_changing_expected_behavior(self):
        dev = dev_tests.DevVNextTests("test_normal_contract_acceptance_keeps_ba_bytes_immutable")
        dev.setUp()
        self.addCleanup(dev.doCleanups)
        handoff = dev.finish()
        dev_path = dev.root / "dev-handoff-vnext.json"
        dev_path.write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
        authority = vnext.load_vnext_authority(
            dev.root / "handoff.json", project_root=dev.root,
            human_actor_authenticator=dev.ba_auth,
        )
        technical = vnext.load_dev_vnext_context(
            {"project_root": str(dev.root), "handoff_path": str(dev_path)}, authority,
            ba_human_actor_authenticator=dev.ba_auth,
        )
        authority = vnext.replace(authority, dev_context=technical)
        dev_case_run = self.ba.root / ".test-kit/runs/FEATURE-1/cases-with-dev"
        vnext.write_vnext_authority_context(dev_case_run, authority, dev_context=technical)
        design = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign(
                "TD-001", ("P1",), "Submit a collection request",
                "An eligible member submits a request and receives the business outcome.",
                ("BR-001", "FR-001"), (),
            ),
        ), artifact_id="FEATURE-1-design", revision="1")
        dependency = v1_cases.ExecutionDependency(
            "Use the approved interface to observe the saved request", "OBSERVABILITY",
            "RESOLVED", technical["technical_snapshot_ref"]["id"], required=True,
        )
        snapshot = v1_cases.CaseSnapshot.create((
            v1_cases.CanonicalTestcase(
                "TC-001", "Submit a collection request", "Check request submission",
                "An eligible member exists.", None,
                (v1_cases.CaseStep("Submit a collection request", None, "The member receives the business outcome."),),
                "P1", ("BR-001", "FR-001"), ("TD-001",), (dependency,),
            ),
        ), artifact_id="FEATURE-1-cases", revision="1")

        result = vnext.validate_vnext_cases(snapshot, design, authority)

        self.assertEqual(result.status, "PASS", result.findings)
        self.assertEqual(snapshot.records[0].steps[0].expected_result, "The member receives the business outcome.")
        dev_refs = v1_cases.case_gate_input_refs(
            authority.baseline, design, run_dir=dev_case_run,
            case_snapshot=snapshot, vnext_authority=True,
        )
        self.assertIn(technical["technical_snapshot_ref"]["id"], {ref["id"] for ref in dev_refs})
        unresolved = v1_cases.ExecutionDependency(
            dependency.need, dependency.kind, "OPEN", None, required=True,
        )
        blocked_case = v1_cases.CaseSnapshot.create((
            v1_cases.replace(snapshot.records[0], execution_dependencies=(unresolved,)),
        ), artifact_id="FEATURE-1-cases-open", revision="1")
        blocked = vnext.validate_vnext_cases(blocked_case, design, self.authority())
        self.assertEqual(blocked.status, "FAIL")
        self.assertIn("OPEN_REQUIRED_EXECUTION_DEPENDENCY", {finding.code for finding in blocked.findings})

    def test_case_gate_binds_only_resolved_vnext_execution_oracles(self):
        authority = self.authority()
        design = v1.DesignSnapshot.create((
            v1.CanonicalTestDesign("TD-001", ("P1",), "Submit request", "An eligible member receives the business outcome.", ("BR-001", "FR-001"), ()),
        ), artifact_id="FEATURE-1-design", revision="1")
        case_run = self.ba.root / ".test-kit/runs/FEATURE-1/case-oracle-refs"
        vnext.write_vnext_authority_context(case_run, authority)
        used = {"id": "EXECUTION:USED", "revision": "R1", "sha256": "a" * 64}
        unused = {"id": "EXECUTION:UNUSED", "revision": "R1", "sha256": "b" * 64}
        dependency = v1_cases.ExecutionDependency(
            "Use approved observable response", "OBSERVABILITY", "RESOLVED", used["id"], required=True,
        )
        snapshot = v1_cases.CaseSnapshot.create((
            v1_cases.CanonicalTestcase(
                "TC-001", "Submit request", "Check outcome", "An eligible member exists.", None,
                (v1_cases.CaseStep("Submit request", None, "The member receives the business outcome."),),
                "P1", ("BR-001", "FR-001"), ("TD-001",), (dependency,),
            ),
        ), artifact_id="FEATURE-1-cases", revision="1")

        refs = v1_cases.case_gate_input_refs(
            authority.baseline, design, run_dir=case_run,
            execution_contract_refs=(used, unused), case_snapshot=snapshot,
        )

        ids = {ref["id"] for ref in refs}
        self.assertIn(used["id"], ids)
        self.assertNotIn(unused["id"], ids)


if __name__ == "__main__":
    unittest.main()
