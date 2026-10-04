"""Golden G3 regressions: authenticated decisions survive persistence crashes."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from tooling.lib import test_kit_v1 as design, test_kit_v1_cases as cases
from tooling.tests import test_test_kit_v1 as design_fixtures
from tooling.tests import test_test_kit_v1_case_gate as case_fixtures


class DesignRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gate-recovery-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bundle = design.adapt_ba_to_tea(design_fixtures.HANDOFF)
        self.snapshot = design.normalize_tea_output(design_fixtures.BENCHMARK, self.bundle.baseline).snapshot
        self.validation = design.validate_design(self.snapshot, self.bundle.baseline)
        state = design.submit_design_for_review(design.start_design_workflow(self.snapshot), self.snapshot, self.validation)
        design.persist_design_review(self.root, self.bundle, design_fixtures.BENCHMARK, self.snapshot, self.validation, state)

    def receipt(self, decision='APPROVE'):
        return design_fixtures.TestKitV1Tests._design_receipt(
            self.snapshot, self.bundle.baseline, decision=decision,
            feedback='Human requests wording changes.' if decision == 'REQUEST_CHANGES' else '')

    def apply(self, receipt, next_revision=None):
        return design.apply_design_decision(self.root, self.snapshot, self.bundle.baseline, receipt,
            human_actor_authenticator=lambda actor, _: design.AuthenticatedHumanActorContext(actor),
            validation=self.validation, next_revision=next_revision)

    def test_exact_completed_approve_replay_is_success_without_mutation(self):
        receipt = self.receipt()
        self.assertTrue(self.apply(receipt).accepted)
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertTrue(self.apply(receipt).accepted)
        self.assertEqual(before, {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_legacy_partial_receipt_recovers_exact_request_changes(self):
        receipt = self.receipt('REQUEST_CHANGES')
        path = self.root / 'design-gate/revisions/1/receipt.json'
        path.parent.mkdir(parents=True)
        original = json.dumps(receipt, ensure_ascii=False, separators=(',', ':')).encode()
        path.write_bytes(original)
        result = self.apply(receipt, '2')
        self.assertTrue(result.accepted, result.finding)
        self.assertEqual(path.read_bytes(), original)
        workflow = json.loads((self.root / 'workflow-state.json').read_text())
        self.assertEqual(workflow['state'], 'DRAFT_DESIGN')
        self.assertEqual(sum(r.get('event') == 'HUMAN_REQUEST_CHANGES' for r in workflow['history']), 1)


class CaseRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = case_fixtures.TestKitV1CaseGateTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.snapshot, self.state, self.validation, self.refs = self.fixture._case_review()

    def test_exact_completed_case_approve_replay_is_success(self):
        f = self.fixture
        receipt = f._receipt(self.snapshot, decision='APPROVE')
        def apply():
            return cases.apply_case_gate_decision(receipt, self.snapshot, f.design, case_fixtures.BASELINE,
                self.state, workflow_dir=f.case_review_dir, human_actor_authenticator=f._human_authenticator,
                validation=self.validation, execution_contract_refs=self.refs)
        self.assertEqual(apply().status, 'STOP_V1')
        self.assertEqual(apply().status, 'STOP_V1')

    def test_persisted_policy_context_survives_legacy_review_caller(self):
        f = self.fixture
        run = f.root / 'policy-cases'
        context = design.persist_project_policy_context(run, f.root, 'CASES')
        normalization = cases.CaseNormalizationResult('NORMALIZED', 'policy-smoke', self.snapshot.project('DRAFT'), (), ())
        cases.persist_case_review(run, normalization, self.validation, self.state)
        workflow = json.loads((run/'workflow-state.json').read_text(encoding='utf-8'))
        self.assertEqual(workflow['project_policy_context'], context)
        self.assertIsNone(design.current_project_policy_ref(run, 'CASES'))


if __name__ == '__main__':
    unittest.main()
