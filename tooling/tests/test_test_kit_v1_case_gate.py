import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tooling.lib import test_kit_v1 as foundation
from tooling.lib import test_kit_v1_cases as cases


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "tooling/tests/fixtures/ba-v1-legacy-compat/05-engineering-handoff.yml"
BASELINE = foundation.load_approved_baseline(HANDOFF)
DESIGN = foundation.DesignSnapshot.create(
    (foundation.CanonicalTestDesign(
        "TD-001", ("CR-001", "P1"), "Create an appointment",
        "A valid Appointment is saved as Scheduled.", ("FR-001",), (), "APPROVED",
    ),),
    artifact_id="CR-001-test-design",
    revision="1",
)
class TestKitV1CaseGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-kit-case-gate-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        open_questions = tuple(
            foundation.OpenQuestion(source_id, text)
            for source_id, text in BASELINE.unknown_clauses.items()
        )
        record = foundation.CanonicalTestDesign(
            "TD-001", ("CR-001", "P1"), "Appointment behavior",
            "A valid Appointment is saved as Scheduled.",
            tuple(sorted(BASELINE.ba_ids)), open_questions,
        )
        self.design = foundation.DesignSnapshot.create(
            (record,), artifact_id="CR-001-test-design", revision="1",
        )
        self.design_root, self.design_receipt, self.design_fixture = self._persist_design(
            self.root / "approved-design", self.design, test_only=False,
        )
        self.test_only_design_root, self.test_only_design_receipt, self.test_only_design_fixture = self._persist_design(
            self.root / "test-only-design", self.design, test_only=True,
        )
        self.case_review_dir = None
        self.case_review_number = 0

    def _persist_design(self, run_dir, design, *, test_only):
        run_dir = Path(run_dir)
        validation = foundation.validate_design(design, BASELINE)
        if validation.status != "PASS":
            raise AssertionError(validation.findings)
        state = foundation.submit_design_for_review(
            foundation.start_design_workflow(design), design, validation,
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        raw = run_dir / "raw-output/test-design.md"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("# Test Design fixture\n", encoding="utf-8")
        foundation.persist_design_review(
            run_dir, foundation.adapt_ba_to_tea(HANDOFF), raw, design, validation, state,
        )
        refs = cases.baseline_receipt_refs(BASELINE)
        receipt = {
            "gate": "DESIGN_REVIEW", "decision": "APPROVE",
            "artifact_id": design.artifact_id, "artifact_revision": design.revision,
            "artifact_sha256": design.sha256, "input_refs": refs,
            "actor_id": "TEST_ONLY:design-human" if test_only else "human:design-gate",
            "actor_role": "HUMAN", "decided_at": "2026-09-25T12:00:00Z", "feedback": "",
        }
        if test_only:
            fixture = self.root / "test-only-design-receipt.json"
            fixture.write_text(json.dumps({
                "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT",
                "not_for_production": True, "receipt": receipt,
            }), encoding="utf-8")
            result = foundation.apply_test_only_design_decision(
                run_dir, design, BASELINE, fixture, validation=validation,
            )
            return run_dir, receipt, fixture
        result = foundation.apply_design_decision(
            run_dir, design, BASELINE, receipt,
            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
            validation=validation,
        )
        if not result.accepted:
            raise AssertionError(result.finding)
        return run_dir, receipt, None

    def _execution_ref(self, *, test_only=False):
        number = len(list(self.root.rglob("execution-*.json"))) + 1
        source_id = f"TEST_ONLY:EXECUTION:{number}" if test_only else f"EXEC:appointment-interface-{number}"
        revision = "fixture-v1" if test_only else "1"
        source_path = self.root / f"execution-{number}.json"
        source_document = {
            "fixture_type": "TEST_ONLY_EXECUTION_ORACLE_RESOLUTION" if test_only else "APPROVED_EXECUTION_ORACLE",
            "not_for_production": test_only,
            "content": "Approved test source backing this resolution.",
        }
        source_bytes = (json.dumps(source_document, indent=2) + "\n").encode("utf-8")
        source_path.write_bytes(source_bytes)
        source_hash = __import__("hashlib").sha256(source_bytes).hexdigest()
        approval_path = self.root / f"execution-{number}-approval.json"
        approval = {
            "fixture_type": "TEST_ONLY_EXECUTION_ORACLE_APPROVAL" if test_only else "EXECUTION_ORACLE_APPROVAL",
            "not_for_production": test_only,
            "decision": "APPROVE", "actor_id": "TEST_ONLY:execution-human" if test_only else "human:execution-oracle",
            "actor_role": "HUMAN", "source_id": source_id, "source_revision": revision,
            "source_sha256": source_hash,
        }
        approval_bytes = (json.dumps(approval, indent=2) + "\n").encode("utf-8")
        approval_path.write_bytes(approval_bytes)
        return {
            "id": source_id, "revision": revision, "sha256": source_hash, "approved": True,
            "path": str(source_path),
            "approval_evidence": {"path": str(approval_path), "sha256": __import__("hashlib").sha256(approval_bytes).hexdigest()},
            **({"test_only": True} if test_only else {}),
        }

    def test_approve_with_material_open_dependency_is_rejected_without_receipt(self):
        snapshot, state, validation, execution_refs = self._case_review(open_dependency=True)
        receipt = self._receipt(snapshot, decision="APPROVE")

        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation,
            execution_contract_refs=execution_refs,
        )

        self.assertEqual(result.finding.code, "OPEN_SEMANTIC_ORACLE")
        self.assertEqual(result.workflow, state)
        self.assertEqual(result.state_history, ("CASE_REVIEW", "APPROVAL_REJECTED", "CASE_REVIEW"))
        self.assertIsNone(result.receipt_bytes)
        self.assertIsNone(result.approved_testware)
        self.assertEqual(snapshot.sha256, result.reviewed_snapshot.sha256)

    def test_stale_case_design_ba_and_revision_receipts_are_rejected(self):
        snapshot, state, validation, execution_refs = self._case_review()
        mutations = (
            ("CASE_RECEIPT_BINDING_MISMATCH", lambda r: r.update(artifact_sha256="0" * 64)),
            ("CASE_RECEIPT_BINDING_MISMATCH", lambda r: r.update(artifact_revision="wrong")),
            ("CASE_RECEIPT_BINDING_MISMATCH", lambda r: r["input_refs"][-1].update(sha256="0" * 64)),
            ("CASE_RECEIPT_BINDING_MISMATCH", lambda r: r["input_refs"][0].update(sha256="0" * 64)),
        )
        for expected_code, mutate in mutations:
            with self.subTest(expected_code=expected_code):
                receipt = self._receipt(snapshot, decision="APPROVE")
                mutate(receipt)
                result = cases.apply_case_gate_decision(
                    receipt, snapshot, self.design, BASELINE, state,
                    workflow_dir=self.case_review_dir,
                    human_actor_authenticator=self._human_authenticator,
                    validation=validation,
                    execution_contract_refs=execution_refs,
                )
                self.assertEqual(result.finding.code, expected_code)
                self.assertIsNone(result.receipt_bytes)

    def test_changed_design_or_ba_snapshot_after_case_review_is_rejected(self):
        snapshot, state, validation, execution_refs = self._case_review()
        receipt = self._receipt(snapshot, decision="APPROVE")
        changed_design = foundation.DesignSnapshot.create(
            self.design.records, artifact_id=self.design.artifact_id, revision="2"
        )
        stale_design = cases.apply_case_gate_decision(
            receipt, snapshot, changed_design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )
        changed_baseline = replace(BASELINE, revision="changed-baseline")
        stale_ba = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, changed_baseline, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )

        self.assertEqual(stale_design.finding.code, "CASE_REVIEW_INPUTS_STALE")
        self.assertEqual(stale_ba.finding.code, "CASE_REVIEW_INPUTS_STALE")

    def test_changed_persisted_design_semantic_bytes_after_case_review_are_rejected(self):
        snapshot, state, validation, execution_refs = self._case_review()
        semantic_path = self.design_root / "canonical/semantic-payload.json"
        semantic_path.write_bytes(semantic_path.read_bytes() + b" ")
        receipt = self._receipt(snapshot, decision="APPROVE")

        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )

        self.assertEqual(result.status, "REJECTED")
        self.assertEqual(result.finding.code, "DESIGN_SEMANTIC_SNAPSHOT_STALE")
        self.assertIsNone(result.receipt_bytes)
        self.assertFalse((self.case_review_dir / "case-gate/receipt.json").exists())

    def test_agent_and_unauthenticated_actors_cannot_approve(self):
        snapshot, state, validation, execution_refs = self._case_review()
        agent_receipt = self._receipt(snapshot, decision="APPROVE")
        agent_receipt.update(actor_id="agent:fake-human", actor_role="AGENT")
        result = cases.apply_case_gate_decision(
            agent_receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )
        self.assertEqual(result.finding.code, "HUMAN_ACTOR_REQUIRED")

        unauthenticated = self._receipt(snapshot, decision="APPROVE")
        result = cases.apply_case_gate_decision(
            unauthenticated, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=lambda *_: None,
            validation=validation, execution_contract_refs=execution_refs,
        )
        self.assertEqual(result.finding.code, "HUMAN_ACTOR_NOT_AUTHENTICATED")

        receipt = self._receipt(snapshot, decision="APPROVE")
        for unverified in ("HUMAN", cases.TestOnlyHumanActorContext(receipt["actor_id"])):
            result = cases.apply_case_gate_decision(
                receipt, snapshot, self.design, BASELINE, state,
                workflow_dir=self.case_review_dir,
                human_actor_authenticator=lambda *_args, value=unverified: value,
                validation=validation, execution_contract_refs=execution_refs,
            )
            self.assertEqual(result.finding.code, "HUMAN_ACTOR_NOT_AUTHENTICATED")

    def test_replayed_receipt_cannot_be_reused_after_request_changes(self):
        snapshot, state, validation, execution_refs = self._case_review()
        receipt = self._receipt(snapshot, decision="REQUEST_CHANGES", feedback="Clarify the approved case wording.")
        first = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
            next_revision="2",
        )

        replay = cases.apply_case_gate_decision(
            receipt, first.next_snapshot, self.design, BASELINE, first.workflow,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            execution_contract_refs=execution_refs,
        )

        self.assertEqual(first.workflow.state, "DRAFT_CASES")
        self.assertEqual(replay.finding.code, "CASE_RECEIPT_BINDING_MISMATCH")
        self.assertIsNone(replay.receipt_bytes)

    def test_exact_approve_receipt_recovers_original_case_review(self):
        snapshot, state, validation, execution_refs = self._case_review()
        receipt = self._receipt(snapshot, decision="APPROVE")
        first = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )
        replay = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )

        self.assertEqual(first.status, "STOP_V1")
        self.assertEqual(replay.status, "STOP_V1")
        self.assertEqual(replay.workflow, first.workflow)

    def test_validator_failure_blocks_case_gate(self):
        snapshot, state, _, execution_refs = self._case_review()
        invalid = cases.CanonicalTestcase(
            "TC-001", "Create Appointment", "Check creation", "A valid Pet exists.", None,
            (cases.CaseStep("Create", None, "Appointment is Scheduled."),), "P1",
            ("FR-999",), ("TD-001",), (), "IN_REVIEW",
        )
        bad_snapshot = cases.CaseSnapshot.create((invalid,), artifact_id=snapshot.artifact_id, revision=snapshot.revision)
        bad_state = cases.CaseWorkflowState(
            "CASE_REVIEW", bad_snapshot.artifact_id, bad_snapshot.revision, bad_snapshot.sha256,
            "IN_REVIEW", "PASS", state.execution_contract_refs, state.design_gate_receipt_mode,
            state.design_gate_receipt_evidence, state.input_refs,
        )
        receipt = self._receipt(bad_snapshot, decision="APPROVE")

        result = cases.apply_case_gate_decision(
            receipt, bad_snapshot, self.design, BASELINE, bad_state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            execution_contract_refs=execution_refs,
        )

        self.assertEqual(result.finding.code, "CASE_RECEIPT_BINDING_MISMATCH")

    def test_continue_next_and_pass_are_not_gate_decisions(self):
        snapshot, state, validation, execution_refs = self._case_review()
        for wording in ("Continue", "Next", "PASS"):
            with self.subTest(wording=wording):
                receipt = self._receipt(snapshot, decision=wording)
                result = cases.apply_case_gate_decision(
                    receipt, snapshot, self.design, BASELINE, state,
                    workflow_dir=self.case_review_dir,
                    human_actor_authenticator=self._human_authenticator,
                    validation=validation, execution_contract_refs=execution_refs,
                )
                self.assertEqual(result.finding.code, "INVALID_GATE_RECEIPT")
                self.assertEqual(result.workflow, state)
                self.assertIsNone(result.receipt_bytes)

    def test_request_changes_requires_feedback_and_starts_fresh_revision(self):
        snapshot, state, validation, execution_refs = self._case_review()
        missing_feedback = self._receipt(snapshot, decision="REQUEST_CHANGES")
        rejected = cases.apply_case_gate_decision(
            missing_feedback, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
            next_revision="2",
        )
        self.assertEqual(rejected.finding.code, "INVALID_GATE_RECEIPT")
        self.assertIsNone(rejected.receipt_bytes)

        receipt = self._receipt(snapshot, decision="REQUEST_CHANGES", feedback="Add the missing observation detail.")
        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
            next_revision="2",
        )

        self.assertEqual(result.state_history, ("CASE_REVIEW", "CHANGES_REQUESTED", "DRAFT_CASES"))
        self.assertEqual(result.reviewed_snapshot.records[0].review_status, "CHANGES_REQUESTED")
        self.assertEqual(result.next_snapshot.revision, "2")
        self.assertEqual(result.next_snapshot.records[0].review_status, "DRAFT")
        self.assertEqual(result.next_snapshot.sha256, snapshot.sha256)
        self.assertEqual(json.loads(result.receipt_bytes)["feedback"], "Add the missing observation detail.")

    def test_request_changes_persistence_preserves_both_revisions_and_receipt(self):
        snapshot, state, validation, execution_refs = self._case_review()
        receipt = self._receipt(snapshot, decision="REQUEST_CHANGES", feedback="Please add an observation.")
        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
            next_revision="2",
        )
        root = self.case_review_dir
        self.assertTrue((root / "case-gate/receipt.json").is_file())
        self.assertTrue((root / "case-gate/changes.json").is_file())
        self.assertTrue((root / "revisions/2/canonical/cases.json").is_file())
        self.assertFalse((root / "approved-testware.json").exists())
        self.assertEqual(json.loads((root / "workflow-state.json").read_text(encoding="utf-8"))["state"], "DRAFT_CASES")

    def test_case_review_loader_restores_snapshot_and_gate_input_provenance(self):
        snapshot, state, validation, execution_refs = self._case_review(open_dependency=True)
        raw_snapshot = snapshot.project("DRAFT")
        normalization = cases.CaseNormalizationResult("NORMALIZED", "native-v1", raw_snapshot, (), ())
        input_manifest = {
            "receipt_mode": "HUMAN_AUTHENTICATED",
            "design_gate_receipt_evidence": {"path": "design-receipt.json", "sha256": "d" * 64},
            "design": {"artifact_id": self.design.artifact_id, "revision": self.design.revision, "sha256": self.design.sha256},
            "ba_input_refs": cases.baseline_receipt_refs(BASELINE),
            "execution_contract_refs": list(execution_refs),
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases.persist_case_review(root, normalization, validation, state)
            manifest_path = root / "inputs/input-manifest.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(json.dumps(input_manifest), encoding="utf-8")
            loaded, loaded_state = cases.load_case_review_snapshot(
                root / "canonical/canonical-testcases.json",
                root / "workflow-state.json",
                root / "canonical/semantic-payload.json",
                input_manifest_path=manifest_path,
            )

        self.assertEqual(loaded.sha256, snapshot.sha256)
        self.assertEqual(loaded_state.state, "CASE_REVIEW")
        self.assertEqual(loaded_state.input_refs, state.input_refs)
        self.assertEqual(loaded_state.execution_contract_refs, state.execution_contract_refs)
        self.assertEqual(loaded_state.design_gate_receipt_mode, "HUMAN_AUTHENTICATED")

    def test_test_only_resolved_case_fixture_approves_without_changing_semantics(self):
        execution_ref = self._execution_ref(test_only=True)
        snapshot, state, validation, execution_refs = self._case_review(
            open_dependency=False, execution_refs=(execution_ref,), test_only_design=True,
        )
        original_payload = snapshot.payload_bytes
        original_sha = snapshot.sha256
        receipt = self._receipt(snapshot, decision="APPROVE", actor_id="TEST_ONLY:human:case-gate")
        fixture = {
            "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT",
            "not_for_production": True,
            "receipt": receipt,
        }
        with tempfile.TemporaryDirectory(prefix="test-kit-case-gate-") as temp:
            fixture_path = Path(temp) / "case-gate-receipt.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            result = cases.apply_test_only_case_gate_decision(
                fixture_path, snapshot, self.design, BASELINE, state,
                workflow_dir=self.case_review_dir,
                validation=validation, execution_contract_refs=execution_refs,
            )
            artifact_path = self.case_review_dir / "approved-testware.json"
            persisted = json.loads(artifact_path.read_text(encoding="utf-8"))

        self.assertEqual(result.state_history, ("CASE_REVIEW", "APPROVED_TESTWARE", "STOP_V1"))
        self.assertEqual(result.workflow.state, "STOP_V1")
        self.assertEqual(result.workflow.review_status, "APPROVED")
        self.assertEqual(result.reviewed_snapshot.payload_bytes, original_payload)
        self.assertEqual(result.reviewed_snapshot.sha256, original_sha)
        self.assertTrue(all(row.review_status == "APPROVED" for row in result.reviewed_snapshot.records))
        self.assertEqual(persisted["fixture_type"], "TEST_ONLY_APPROVED_TESTWARE_EVIDENCE")
        self.assertNotIn("testcases", persisted["approved_testware"])
        self.assertEqual(persisted["approved_testware"]["testcase_collection"]["sha256"], original_sha)
        self.assertEqual(persisted["approved_testware"]["execution_oracle_refs"][0]["id"], execution_refs[0]["id"])
        evidence = {item["field"]: item for item in persisted["approved_testware"]["evidence_locations"]}
        for ref in cases.baseline_receipt_refs(BASELINE):
            source = ref["id"].removeprefix("BA:")
            path = BASELINE.handoff_path if source == "handoff" else BASELINE.source_paths[source]
            self.assertEqual(evidence[ref["id"]]["path"], str(path))
            self.assertEqual(evidence[ref["id"]]["sha256"], ref["sha256"])

    def test_test_only_actor_and_test_only_design_receipt_are_rejected_by_production(self):
        execution_ref = self._execution_ref(test_only=True)
        snapshot, state, validation, execution_refs = self._case_review(
            open_dependency=False, execution_refs=(execution_ref,), test_only_design=True,
        )
        receipt = self._receipt(snapshot, decision="APPROVE", actor_id="TEST_ONLY:human:case-gate")
        auth_calls = []
        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=lambda *args: auth_calls.append(args),
            validation=validation, execution_contract_refs=execution_refs,
        )

        self.assertEqual(result.finding.code, "TEST_ONLY_RECEIPT_NOT_PRODUCTION")
        self.assertEqual(auth_calls, [])
        self.assertIsNone(result.receipt_bytes)

    def test_stale_execution_oracle_revision_hash_invalidates_review(self):
        execution_ref = self._execution_ref()
        snapshot, state, validation, reviewed_refs = self._case_review(
            open_dependency=False, execution_refs=(execution_ref,),
        )
        changed_ref = {**execution_ref, "sha256": "c" * 64}
        receipt = self._receipt(snapshot, decision="APPROVE")

        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=(changed_ref,),
        )

        self.assertEqual(result.finding.code, "EXECUTION_ORACLE_REFS_STALE")

    def test_execution_oracle_source_change_after_review_blocks_approval(self):
        execution_ref = self._execution_ref()
        snapshot, state, validation, execution_refs = self._case_review(
            open_dependency=False, execution_refs=(execution_ref,),
        )
        Path(execution_ref["path"]).write_text("changed after review", encoding="utf-8")
        receipt = self._receipt(snapshot, decision="APPROVE")

        result = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )

        self.assertEqual(result.status, "REJECTED")
        self.assertEqual(result.finding.code, "CASE_VALIDATION_NOT_CURRENT")

    def test_case_gate_revalidates_execution_oracle_authority_scope(self):
        safe_ref = self._execution_ref()
        snapshot, state, validation, _ = self._case_review(
            open_dependency=False, execution_refs=(safe_ref,),
        )
        source_path = Path(safe_ref["path"])
        source_doc = json.loads(source_path.read_text(encoding="utf-8"))
        source_doc["content"] = "BR-005 maximum duration is 30 minutes."
        source_bytes = (json.dumps(source_doc, indent=2) + "\n").encode("utf-8")
        source_path.write_bytes(source_bytes)
        source_hash = __import__("hashlib").sha256(source_bytes).hexdigest()
        approval_path = Path(safe_ref["approval_evidence"]["path"])
        approval = json.loads(approval_path.read_text(encoding="utf-8"))
        approval["source_sha256"] = source_hash
        approval_bytes = (json.dumps(approval, indent=2) + "\n").encode("utf-8")
        approval_path.write_bytes(approval_bytes)
        changed_ref = {
            **safe_ref,
            "sha256": source_hash,
            "approval_evidence": {
                "path": str(approval_path),
                "sha256": __import__("hashlib").sha256(approval_bytes).hexdigest(),
            },
        }
        draft_snapshot = snapshot.project("DRAFT")
        current_state = cases.submit_cases_for_review(
            cases.start_case_workflow(draft_snapshot), draft_snapshot, validation,
            execution_contract_refs=(changed_ref,),
            design_gate_receipt_mode=state.design_gate_receipt_mode,
            design_gate_receipt_evidence=state.design_gate_receipt_evidence,
            input_refs=cases.case_gate_input_refs(BASELINE, self.design),
        )

        result = cases.validate_case_gate_receipt(
            self._receipt(snapshot, decision="APPROVE"), snapshot, self.design, BASELINE, current_state,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=(changed_ref,),
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "CASE_VALIDATION_NOT_CURRENT")
        self.assertIn("AUTHORITY_SCOPE_VIOLATION", {finding.code for finding in result.findings})

    def test_stop_v1_is_terminal(self):
        execution_ref = self._execution_ref()
        snapshot, state, validation, execution_refs = self._case_review(
            open_dependency=False, execution_refs=(execution_ref,),
        )
        receipt = self._receipt(snapshot, decision="APPROVE")
        approved = cases.apply_case_gate_decision(
            receipt, snapshot, self.design, BASELINE, state,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            validation=validation, execution_contract_refs=execution_refs,
        )
        follow_up = cases.apply_case_gate_decision(
            receipt, approved.reviewed_snapshot, self.design, BASELINE, approved.workflow,
            workflow_dir=self.case_review_dir,
            human_actor_authenticator=self._human_authenticator,
            execution_contract_refs=execution_refs,
        )

        self.assertEqual(approved.workflow.state, "STOP_V1")
        self.assertEqual(follow_up.status, "STOP_V1")
        self.assertEqual(follow_up.workflow, approved.workflow)

    def _case_review(self, *, open_dependency=False, execution_refs=(), test_only_design=False):
        execution_refs = tuple(execution_refs)
        dependencies = ()
        if open_dependency:
            dependencies = (cases.ExecutionDependency("Approved UI/action mapping is required", "SEMANTIC_ORACLE", "OPEN", None),)
        elif execution_refs:
            dependencies = (cases.ExecutionDependency("Approved UI/action mapping is required", "SEMANTIC_ORACLE", "RESOLVED", execution_refs[0]["id"]),)
        record = cases.CanonicalTestcase(
            "TC-001", "Create appointment", "Check creation", "A valid Pet exists.", "Pet A",
            (cases.CaseStep("Create appointment", None, "Appointment is saved as Scheduled."),), "P1",
            ("FR-001",), ("TD-001",), dependencies, "DRAFT",
        )
        snapshot = cases.CaseSnapshot.create((record,), artifact_id="CR-001-testcases", revision="1")
        validation = cases.validate_testcases(
            snapshot, self.design, BASELINE, execution_contract_refs=execution_refs,
            execution_oracle_authenticator=self._human_authenticator,
            allow_test_only_execution_oracles=test_only_design,
        )
        design_root = self.test_only_design_root if test_only_design else self.design_root
        receipt_path = design_root / "design-gate/revisions" / self.design.revision / "receipt.json"
        design_evidence = {
            "path": str(receipt_path),
            "sha256": __import__("hashlib").sha256(receipt_path.read_bytes()).hexdigest(),
            "mode": "TEST_ONLY" if test_only_design else "HUMAN_AUTHENTICATED",
        }
        if test_only_design:
            design_evidence["fixture"] = {
                "path": str(self.test_only_design_fixture),
                "sha256": __import__("hashlib").sha256(self.test_only_design_fixture.read_bytes()).hexdigest(),
            }
        state = cases.submit_cases_for_review(
            cases.start_case_workflow(snapshot), snapshot, validation,
            execution_contract_refs=execution_refs,
            design_gate_receipt_mode="TEST_ONLY" if test_only_design else "HUMAN_AUTHENTICATED",
            design_gate_receipt_evidence=design_evidence,
            input_refs=cases.case_gate_input_refs(BASELINE, self.design),
        )
        self.case_review_number += 1
        self.case_review_dir = self.root / f"case-review-{self.case_review_number}"
        normalization = cases.CaseNormalizationResult("NORMALIZED", "test-v1", snapshot, (), ())
        cases.persist_case_review(self.case_review_dir, normalization, validation, state)
        return snapshot.project("IN_REVIEW"), state, validation, tuple(execution_refs)

    def _receipt(self, snapshot, *, decision, feedback="", actor_id="human:case-gate"):
        return {
            "gate": "CASE_REVIEW",
            "decision": decision,
            "artifact_id": snapshot.artifact_id,
            "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": cases.case_gate_input_refs(BASELINE, self.design),
            "actor_id": actor_id,
            "actor_role": "HUMAN",
            "decided_at": "2026-09-25T12:00:00Z",
            "feedback": feedback,
        }

    @staticmethod
    def _human_authenticator(actor_id, _receipt):
        return cases.AuthenticatedHumanActorContext(actor_id)

    def _execution_ref(self, *, test_only=False, content="Approved source fixture."):
        number = len(list(self.root.glob("execution-*.json"))) + 1
        source_id = f"TEST_ONLY:EXECUTION:{number}" if test_only else f"EXEC:appointment-interface-{number}"
        revision = "fixture-v1" if test_only else "1"
        source_path = self.root / f"execution-{number}.json"
        source_bytes = (json.dumps({
            "fixture_type": "TEST_ONLY_EXECUTION_ORACLE_RESOLUTION" if test_only else "APPROVED_EXECUTION_ORACLE",
            "not_for_production": test_only,
            "content": content,
        }, indent=2) + "\n").encode("utf-8")
        source_path.write_bytes(source_bytes)
        source_hash = __import__("hashlib").sha256(source_bytes).hexdigest()
        approval_path = self.root / f"execution-{number}-approval.json"
        approval_bytes = (json.dumps({
            "fixture_type": "TEST_ONLY_EXECUTION_ORACLE_APPROVAL" if test_only else "EXECUTION_ORACLE_APPROVAL",
            "not_for_production": test_only,
            "decision": "APPROVE",
            "actor_id": "TEST_ONLY:execution-human" if test_only else "human:execution-oracle",
            "actor_role": "HUMAN", "source_id": source_id,
            "source_revision": revision, "source_sha256": source_hash,
        }, indent=2) + "\n").encode("utf-8")
        approval_path.write_bytes(approval_bytes)
        return {
            "id": source_id, "revision": revision, "sha256": source_hash,
            "approved": True, "path": str(source_path),
            "approval_evidence": {
                "path": str(approval_path),
                "sha256": __import__("hashlib").sha256(approval_bytes).hexdigest(),
            },
            **({"test_only": True} if test_only else {}),
        }


if __name__ == "__main__":
    unittest.main()
