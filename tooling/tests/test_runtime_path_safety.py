import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tooling.lib import runtime_paths as paths, gate_persistence as persistence
from tooling.lib import test_kit_v1 as design, testware_promotion
from tooling.tests import test_gate_recovery_faults as faults


class RuntimePathSafetyTests(unittest.TestCase):
    def test_budget_error_has_portable_evidence_and_supported_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / ('a' * 170) / ('b' * 80) / 'changes.json'
            with self.assertRaises(paths.RuntimePathError) as caught:
                paths.preflight_paths([target], stage='DESIGN_GATE', transition='REQUEST_CHANGES',
                                      windows=True, long_paths=False)
            detail = json.loads(str(caught.exception))
            self.assertEqual(detail['code'], 'WINDOWS_PATH_BUDGET_EXCEEDED')
            self.assertEqual(detail['actual_length'], len(str(target.absolute())))
            self.assertEqual(detail['safe_budget'], 259)
            self.assertEqual(detail['transition'], 'REQUEST_CHANGES')
            paths.preflight_paths([target], stage='DESIGN_GATE', transition='REQUEST_CHANGES',
                                  windows=True, long_paths=True)

    def test_legacy_filename_fails_before_receipt_and_compact_gate_fits_golden_path(self):
        for kind in ('design', 'case'):
            for decision in ('APPROVE', 'REQUEST_CHANGES'):
                with self.subTest(kind=kind, decision=decision), faults.gate(kind, decision) as (source, receipt, _):
                    owned = tempfile.TemporaryDirectory(prefix='gate-path-')
                    self.addCleanup(owned.cleanup)
                    parent = Path(owned.name)
                    target_length = 216
                    root = parent / ('g' * (target_length - len(str(parent)) - 1))
                    shutil.copytree(source, root)
                    # Reconstruct only through runtime inputs: copied immutable review evidence.
                    if kind == 'design':
                        snapshot = design.load_persisted_design_snapshot(root, require_state='DESIGN_REVIEW')
                        baseline = faults.fixtures.design_fixtures.TestKitV1Tests()
                        baseline.setUp()
                        apply = lambda: design.apply_design_decision(root, snapshot, baseline.baseline, receipt,
                            human_actor_authenticator=lambda actor, _: design.AuthenticatedHumanActorContext(actor),
                            next_revision='2' if decision == 'REQUEST_CHANGES' else None)
                    else:
                        cases = faults.cases
                        snapshot, state = cases.load_case_review_snapshot(root/'canonical/canonical-testcases.json',
                            root/'workflow-state.json', root/'canonical/semantic-payload.json')
                        design_snapshot = design.load_persisted_design_snapshot(source.parent/'approved-design', require_state='APPROVED_DESIGN')
                        apply = lambda: cases.apply_case_gate_decision(receipt, snapshot, design_snapshot,
                            faults.case_fixtures.BASELINE, state, workflow_dir=root,
                            human_actor_authenticator=lambda actor, _: cases.AuthenticatedHumanActorContext(actor),
                            next_revision='2' if decision == 'REQUEST_CHANGES' else None)
                    legacy = root / 'design-gate/revisions/1/canonical-test-design-changes-requested.json'
                    self.assertGreater(len(str(legacy)), 259)
                    def unsupported(targets, **kwargs):
                        return paths.preflight_paths(targets, **kwargs, windows=True, long_paths=False)
                    with patch.object(persistence, 'preflight_paths', side_effect=unsupported):
                        result = apply()
                    self.assertTrue(faults.successful(result), result)
                    self.assertLessEqual(max(len(str(p)) for p in root.rglob('*') if p.is_file()), 259)
                    self.assertTrue(faults.successful(apply()))

    def test_gate_path_preflight_rejects_too_long_destination_without_consumption(self):
        for kind in ('design', 'case'):
            with self.subTest(kind=kind), faults.gate(kind, 'REQUEST_CHANGES') as (root, receipt, apply):
                before = faults.files(root)
                def tiny_budget(targets, **kwargs):
                    return paths.preflight_paths(targets, **kwargs, windows=True, long_paths=False, budget=30)
                with patch.object(persistence, 'preflight_paths', side_effect=tiny_budget):
                    result = apply(receipt)
                self.assertFalse(faults.successful(result))
                self.assertEqual(result.finding.code, 'WINDOWS_PATH_BUDGET_EXCEEDED')
                self.assertEqual(faults.files(root), before)

    def test_prepare_finalize_catalog_rejects_unsupported_paths(self):
        original = paths.preflight_paths
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / ('x' * 200)
            for lane in ('DESIGN', 'CASES'):
                for transition in ('PREPARE', 'FINALIZE'):
                    with self.subTest(lane=lane, transition=transition):
                        def unsupported(targets, **kwargs):
                            return original(targets, **kwargs, windows=True, long_paths=False)
                        with patch.object(paths, 'preflight_paths', side_effect=unsupported):
                            with self.assertRaises(paths.RuntimePathError):
                                paths.preflight_runtime_layout(root, lane, transition)

    def test_promotion_partial_replay_and_late_conflict_are_fail_closed(self):
        with faults.gate('design', 'APPROVE') as (root, receipt, apply):
            self.assertTrue(faults.successful(apply(receipt)))
            baseline = faults.fixtures.design_fixtures.TestKitV1Tests()
            baseline.setUp()
            feature = root / 'exports' / baseline.baseline.feature_id
            invoke = lambda: testware_promotion.promote(root, feature, baseline.baseline, stage='design',
                human_actor_authenticator=lambda actor, _: design.AuthenticatedHumanActorContext(actor))
            original = testware_promotion._copy_exact
            calls = []
            def crash(path, content):
                original(path, content)
                calls.append(path)
                if len(calls) == 2:
                    raise OSError('crash after semantic and markdown publication')
            with patch.object(testware_promotion, '_copy_exact', side_effect=crash):
                with self.assertRaises(OSError):
                    invoke()
            record = invoke()
            before = faults.files(feature)
            self.assertEqual(invoke(), record)
            self.assertEqual(faults.files(feature), before)
            (feature/'test/approvals/design-promotion.json').write_bytes(b'conflict')
            conflicted = faults.files(feature)
            with self.assertRaises(ValueError):
                invoke()
            self.assertEqual(faults.files(feature), conflicted)

    def test_revision_cannot_escape_runtime_directory(self):
        for revision in ('../2', '..', '.', r'folder\2', 'x/y', '', 'CON', 'NUL.json', '2.'):
            with self.subTest(revision=revision), self.assertRaises(paths.RuntimePathError):
                paths.revision_component(revision)

    def test_conflicting_legacy_aliases_are_not_silently_selected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'semantic.json').write_bytes(b'new')
            (root/'semantic-payload.json').write_bytes(b'old')
            with self.assertRaises(paths.RuntimePathError):
                paths.internal_artifact(root, 'semantic.json', 'semantic-payload.json')


if __name__ == '__main__':
    unittest.main()
