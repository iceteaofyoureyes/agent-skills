"""Fault every Human Gate persistence boundary using disposable review fixtures."""
import copy
import json
from contextlib import contextmanager
import unittest
from unittest.mock import patch

from tooling.lib import gate_persistence as persistence
from tooling.lib import test_kit_v1_cases as cases
from tooling.tests import test_gate_recovery as fixtures
from tooling.tests import test_test_kit_v1_case_gate as case_fixtures


def files(root):
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file()}


@contextmanager
def gate(kind, decision):
    fixture = fixtures.DesignRecoveryTests() if kind == 'design' else fixtures.CaseRecoveryTests()
    fixture.setUp()
    try:
        if kind == 'design':
            root = fixture.root
            receipt = fixture.receipt(decision)
            apply = lambda value: fixture.apply(value, '2' if decision == 'REQUEST_CHANGES' else None)
        else:
            f = fixture.fixture
            root = f.case_review_dir
            receipt = f._receipt(fixture.snapshot, decision=decision,
                                 feedback='Human requests wording changes.' if decision == 'REQUEST_CHANGES' else '')
            apply = lambda value: cases.apply_case_gate_decision(
                value, fixture.snapshot, f.design, case_fixtures.BASELINE, fixture.state,
                workflow_dir=root, human_actor_authenticator=f._human_authenticator,
                validation=fixture.validation, execution_contract_refs=fixture.refs,
                next_revision='2' if decision == 'REQUEST_CHANGES' else None)
        yield root, receipt, apply
    finally:
        fixture.doCleanups()


def successful(result):
    return result.accepted if hasattr(result, 'accepted') else result.status != 'REJECTED'


class GateFaultInjectionTests(unittest.TestCase):
    def assert_recovered(self, root, receipt, apply, decision):
        result = apply(receipt)
        self.assertTrue(successful(result), result)
        history = json.loads((root / 'workflow-state.json').read_text(encoding='utf-8'))['history']
        if history and isinstance(history[0], str):
            self.assertEqual(history.count('CHANGES_REQUESTED' if decision == 'REQUEST_CHANGES' else 'APPROVED_TESTWARE'), 1)
            self.assertEqual(len(history), len(set(history)))
            human = json.loads((root / 'workflow-state.json').read_text(encoding='utf-8'))['human_gate_history']
            self.assertEqual(sum(row['event'] == 'HUMAN_' + decision for row in human), 1)
        else:
            self.assertEqual(sum(row.get('event') == 'HUMAN_' + decision for row in history), 1)
        before = files(root)
        self.assertTrue(successful(apply(receipt)))
        self.assertEqual(files(root), before)
        other = copy.deepcopy(receipt)
        other['feedback'] = 'A different Human decision payload'
        rejected = apply(other)
        self.assertFalse(successful(rejected), rejected)
        self.assertEqual(files(root), before)

    def test_every_immutable_write_boundary_and_exact_recovery(self):
        for kind in ('design', 'case'):
            for decision in ('APPROVE', 'REQUEST_CHANGES'):
                with gate(kind, decision) as (_, receipt, apply):
                    observed = []
                    original = persistence.write_if_same_or_absent
                    def record(path, content):
                        observed.append(str(path))
                        return original(path, content)
                    with patch.object(persistence, 'write_if_same_or_absent', side_effect=record):
                        self.assertTrue(successful(apply(receipt)))
                for boundary in range(len(observed)):
                    for timing in ('before', 'after'):
                        with self.subTest(kind=kind, decision=decision, write=boundary, timing=timing), gate(kind, decision) as (root, receipt, apply):
                            call = [0]
                            def fail(path, content):
                                index = call[0]
                                call[0] += 1
                                if index == boundary and timing == 'before':
                                    raise OSError('injected before immutable write')
                                original(path, content)
                                if index == boundary and timing == 'after':
                                    raise OSError('injected after immutable write')
                            with patch.object(persistence, 'write_if_same_or_absent', side_effect=fail):
                                result = apply(receipt)
                            self.assertFalse(successful(result), result)
                            partial = files(root)
                            self.assert_recovered(root, receipt, apply, decision)
                            for path, content in partial.items():
                                if path != 'workflow-state.json':
                                    self.assertEqual(files(root)[path], content)

    def test_before_and_after_atomic_workflow_commit(self):
        original = persistence.atomic_workflow
        for kind in ('design', 'case'):
            for decision in ('APPROVE', 'REQUEST_CHANGES'):
                for timing in ('before', 'after'):
                    with self.subTest(kind=kind, decision=decision, timing=timing), gate(kind, decision) as (root, receipt, apply):
                        def fail(path, state):
                            if timing == 'after':
                                original(path, state)
                            raise OSError('injected workflow commit failure')
                        with patch.object(persistence, 'atomic_workflow', side_effect=fail):
                            self.assertFalse(successful(apply(receipt)))
                        self.assert_recovered(root, receipt, apply, decision)

    def test_preflight_failure_does_not_consume_receipt(self):
        for kind in ('design', 'case'):
            for decision in ('APPROVE', 'REQUEST_CHANGES'):
                with self.subTest(kind=kind, decision=decision), gate(kind, decision) as (root, receipt, apply):
                    before = files(root)
                    with patch.object(persistence, 'preflight_paths', side_effect=OSError('injected preflight failure')):
                        self.assertFalse(successful(apply(receipt)))
                    self.assertEqual(files(root), before)
                    self.assert_recovered(root, receipt, apply, decision)

    def test_completed_output_tampering_fails_closed_without_overwrite(self):
        for kind in ('design', 'case'):
            for decision in ('APPROVE', 'REQUEST_CHANGES'):
                with self.subTest(kind=kind, decision=decision), gate(kind, decision) as (root, receipt, apply):
                    self.assertTrue(successful(apply(receipt)))
                    journal_path = next(root.rglob('tx.json'))
                    transaction = json.loads(journal_path.read_text(encoding='utf-8'))
                    target = root / transaction['outputs'][0]['path']
                    target.write_bytes(b'tampered immutable output')
                    before = files(root)
                    self.assertFalse(successful(apply(receipt)))
                    self.assertEqual(files(root), before)

    def test_completed_workflow_tampering_fails_closed(self):
        for kind in ('design', 'case'):
            with self.subTest(kind=kind), gate(kind, 'APPROVE') as (root, receipt, apply):
                self.assertTrue(successful(apply(receipt)))
                path = root / 'workflow-state.json'
                workflow = json.loads(path.read_text(encoding='utf-8'))
                workflow['artifact_sha256'] = 'f' * 64
                path.write_text(json.dumps(workflow), encoding='utf-8')
                before = files(root)
                self.assertFalse(successful(apply(receipt)))
                self.assertEqual(files(root), before)

    def test_malformed_journal_fails_closed_without_crashing(self):
        for kind in ('design', 'case'):
            for payload in ({}, {'receipt_sha256': 'f' * 64}, []):
                with self.subTest(kind=kind, payload=payload), gate(kind, 'APPROVE') as (root, receipt, apply):
                    self.assertTrue(successful(apply(receipt)))
                    next(root.rglob('tx.json')).write_text(json.dumps(payload), encoding='utf-8')
                    before = files(root)
                    self.assertFalse(successful(apply(receipt)))
                    self.assertEqual(files(root), before)

    def test_immutable_primitive_rejects_symlink_without_touching_target(self):
        with gate('design', 'APPROVE') as (root, _, _):
            target = root / 'original.txt'
            target.write_bytes(b'original evidence')
            alias = root / 'alias.txt'
            try:
                alias.symlink_to(target)
            except OSError as error:
                self.skipTest(f'filesystem symlink permission unavailable: {error}')
            with self.assertRaises(persistence.GateConflict):
                persistence.write_if_same_or_absent(alias, b'original evidence')
            self.assertEqual(target.read_bytes(), b'original evidence')
