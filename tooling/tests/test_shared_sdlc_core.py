"""Shared owner, vocabulary, and historical caller compatibility contracts."""
import hashlib
import importlib
import json
from pathlib import Path
import pickle
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from shared.sdlc.artifacts.classes import ArtifactClass
from shared.sdlc.readiness.vocabulary import Readiness
from shared.sdlc.findings.taxonomy import FindingKind
from shared.sdlc.approvals.invariants import AUTHORITY_PRECEDENCE, APPROVAL_INVARIANTS
from shared.sdlc.provenance.references import delivery_reference, checked_ref

ROOT = Path(__file__).resolve().parents[2]
OWNERS = (
    ('contracts', 'shared.sdlc.authority.contracts', 'validate_handoff_text'),
    ('approved_baseline', 'shared.sdlc.authority.approved_baseline', 'ApprovedBaseline'),
    ('delivery_manifest', 'shared.sdlc.artifacts.delivery_manifest', 'load_delivery_manifest'),
    ('tooling.lib.runtime_paths', 'shared.sdlc.provenance.runtime_paths', 'RuntimePathError'),
    ('tooling.lib.gate_persistence', 'shared.sdlc.approvals.gate_persistence', 'GateConflict'),
    ('tooling.lib.testware_promotion', 'shared.sdlc.promotion.testware_promotion', 'promote'),
    ('tooling.lib.execution_contract', 'shared.sdlc.findings.execution_contract', 'transition'),
)


class SharedVocabularyTests(unittest.TestCase):
    def test_artifact_values_are_exact(self):
        self.assertEqual([item.value for item in ArtifactClass],
                         ['CANONICAL', 'DERIVED', 'RUNTIME', 'EVIDENCE', 'HANDOFF_MANIFEST'])
        self.assertEqual(ArtifactClass.CANONICAL, 'CANONICAL')
        with self.assertRaises(ValueError):
            ArtifactClass('APPROVED')

    def test_readiness_values_are_exact(self):
        self.assertEqual([item.value for item in Readiness], [
            'PACKAGE_READY', 'PROJECT_CONFIG_READY', 'PROJECT_FOUNDATION_READY',
            'CAPABILITY_READY', 'FEATURE_READY', 'READY_FOR_TEST', 'EXECUTION_READY',
            'READY_FOR_RETEST', 'VERIFIED', 'READY_TO_MERGE'])
        with self.assertRaises(ValueError):
            Readiness('APPROVE')

    def test_finding_values_preserve_execution_routes(self):
        from shared.sdlc.findings.execution_contract import CLASSIFICATIONS
        self.assertEqual([item.value for item in FindingKind], [
            'DEFECT', 'SPEC_GAP', 'BUSINESS_DECISION_REQUIRED', 'TEST_ISSUE', 'ENVIRONMENT_ISSUE'])
        self.assertEqual(set(CLASSIFICATIONS), {item.value for item in FindingKind})
        self.assertEqual(CLASSIFICATIONS['DEFECT'], 'DEFECT_READY_FOR_DEV')
        self.assertEqual(CLASSIFICATIONS['SPEC_GAP'], 'BA_DECISION_REQUIRED')

    def test_authority_and_approval_invariants_are_exact(self):
        self.assertEqual(AUTHORITY_PRECEDENCE, (
            'Human-approved decisions', 'Shared SDLC invariants', 'Project Policy',
            'Kit / skill instructions', 'Runtime defaults'))
        self.assertEqual(APPROVAL_INVARIANTS, (
            'CONTINUE != APPROVE', 'ANSWER != APPROVE', 'validator PASS != APPROVE',
            'artifact generated != APPROVED', 'derived artifact != authority',
            'CURRENT_SYSTEM != approved target business rule', 'Dev fix PASS != Tester VERIFIED'))


class SharedCompatibilityTests(unittest.TestCase):
    def test_module_symbol_and_pickle_identity_in_both_import_orders(self):
        # A new process is required to genuinely exercise both first imports.
        code = '''import importlib, pathlib, pickle, sys
root = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / 'ba-workflow/scripts'))
owners = %r
for legacy, core, symbol in owners:
    first, second = (legacy, core) if sys.argv[2] == 'legacy' else (core, legacy)
    a, b = importlib.import_module(first), importlib.import_module(second)
    exec('import ' + legacy + ' as historical')
    assert historical is a
    if '.' in legacy:
        parent, _, child = legacy.rpartition('.')
        assert getattr(importlib.import_module(parent), child) is a
    assert a is b, (first, second)
    assert a.__name__ == legacy
    assert getattr(a, symbol) is getattr(b, symbol)
    assert pathlib.Path(a.__file__).is_relative_to(root / 'shared')
    assert a.__spec__.name == core
from approved_baseline import BaselineRow, BaselineError
row = BaselineRow('FR-001', 'Rule', 'source.md', 1)
assert BaselineRow.__module__ == 'approved_baseline'
assert pickle.loads(pickle.dumps(row)) == row
assert type(pickle.loads(pickle.dumps(BaselineError('invalid')))) is BaselineError
from tooling.lib.gate_persistence import GateConflict
assert GateConflict.__module__ == 'tooling.lib.gate_persistence'
assert type(pickle.loads(pickle.dumps(GateConflict('invalid')))) is GateConflict
''' % (OWNERS,)
        for order in ('legacy', 'core'):
            with self.subTest(order=order):
                result = subprocess.run([sys.executable, '-I', '-c', code, str(ROOT), order],
                                        cwd=ROOT.parent, capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_patched_legacy_globals_are_used_by_shared_gate(self):
        legacy = importlib.import_module('tooling.lib.gate_persistence')
        core = importlib.import_module('shared.sdlc.approvals.gate_persistence')
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            before, after = {'state': 'REVIEW'}, {'state': 'APPROVED'}
            (run / 'workflow-state.json').write_text(json.dumps(before))
            with patch.object(legacy, 'atomic_workflow', side_effect=OSError('fault injection')) as mocked:
                with self.assertRaisesRegex(OSError, 'fault injection'):
                    core.commit_gate(run, run/'gate/receipt.json', b'{}', [], before, after,
                                     stage='DESIGN', transition='APPROVE')
                mocked.assert_called_once()
            self.assertEqual(json.loads((run/'workflow-state.json').read_text()), before)
            core.commit_gate(run, run/'gate/receipt.json', b'{}', [], before, after,
                             stage='DESIGN', transition='APPROVE')
            self.assertEqual(json.loads((run/'workflow-state.json').read_text()), after)

    def test_private_parser_and_reference_symbols_remain_callable(self):
        old = importlib.import_module('contracts')
        shared = importlib.import_module('shared.sdlc.authority.contracts')
        self.assertIs(old._yaml_fields, shared._yaml_fields)
        text = 'schema_version: 1\nfeature:\n  id: CR-001\n'
        self.assertEqual(old._yaml_fields(text), shared._yaml_fields(text))
        self.assertIs(importlib.import_module('delivery_manifest')._reference, delivery_reference)
        self.assertIs(importlib.import_module('tooling.lib.execution_contract').checked_ref, checked_ref)

    def test_reference_profiles_keep_their_existing_path_syntax(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root/'source.json'
            path.write_bytes(b'{}')
            digest = hashlib.sha256(b'{}').hexdigest()
            self.assertEqual(delivery_reference(root, {'path':'source.json', 'sha256':digest, 'revision':'R1'}, revision=True), path)
            self.assertEqual(checked_ref({'path':str(path), 'sha256':digest}), path)
            for unsafe in ('../source.json', './source.json', str(path), 'a\\source.json', 'a//source.json'):
                with self.subTest(path=unsafe), self.assertRaises(ValueError):
                    delivery_reference(root, {'path':unsafe, 'sha256':digest})
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                delivery_reference(root, {'path':'source.json', 'sha256':'0'*64})
            with self.assertRaisesRegex(ValueError, 'immutable artifact revision'):
                delivery_reference(root, {'path':'source.json', 'sha256':digest}, revision=True)

    def test_direct_core_preserves_baref_coverage_boundary(self):
        from shared.sdlc.authority.approved_baseline import read_approved_baseline
        from tooling.tests.test_dev_kit import _write_approved_baseline
        with tempfile.TemporaryDirectory() as directory:
            handoff = _write_approved_baseline(Path(directory))
            baseline = read_approved_baseline(handoff)
            self.assertEqual(baseline.coverage_ids, set())
            self.assertTrue(baseline.authority_ref_ids)
            self.assertTrue(all(item.startswith('BAREF:') for item in baseline.authority_ref_ids))
            self.assertFalse(any(item.startswith('BAREF:') for item in baseline.coverage_ids))
            self.assertEqual(baseline, importlib.import_module('approved_baseline').read_approved_baseline(handoff))


class SharedInstalledRuntimeTests(unittest.TestCase):
    def _probe(self, runtime_root, ba_scripts, core_root):
        code = '''import importlib, pathlib, pickle, sys
runtime, scripts, core = map(pathlib.Path, sys.argv[1:])
sys.path.insert(0, str(runtime))
sys.path.insert(0, str(scripts))
# Deliberately import via the historical BA adapter before adding core to path.
from approved_baseline import BaselineRow
assert pathlib.Path(importlib.import_module('approved_baseline').__file__).is_relative_to(core)
from shared.sdlc.authority.approved_baseline import BaselineRow as SharedRow
assert BaselineRow is SharedRow
assert pickle.loads(pickle.dumps(BaselineRow('FR-001', 'Rule', 'srs.md', 1))).id == 'FR-001'
import contracts, delivery_manifest
assert importlib.import_module('shared.sdlc.authority.contracts') is contracts
assert importlib.import_module('shared.sdlc.artifacts.delivery_manifest') is delivery_manifest
from shared.sdlc.artifacts.classes import ArtifactClass
from shared.sdlc.readiness.vocabulary import Readiness
from shared.sdlc.findings.taxonomy import FindingKind
assert (len(ArtifactClass), len(Readiness), len(FindingKind)) == (5, 10, 5)
assert pathlib.Path(importlib.import_module('shared.sdlc.provenance.references').__file__).is_relative_to(core)
from shared.sdlc.provenance.runtime_paths import revision_component
from shared.sdlc.approvals.gate_persistence import json_bytes
assert revision_component('R1') == 'R1'
assert json_bytes({'decision':'ANSWER'}) == b'{\\n  "decision": "ANSWER"\\n}\\n'
from shared.sdlc.findings.execution_contract import CLASSIFICATIONS
assert CLASSIFICATIONS['DEFECT'] == 'DEFECT_READY_FOR_DEV'
'''
        result = subprocess.run([sys.executable, '-I', '-c', code, str(runtime_root), str(ba_scripts), str(core_root)],
                                cwd=runtime_root, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ba_installed_core_has_kit_scoped_ownership_and_imports(self):
        from tooling.lib import ba_kit
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'skills'
            ba_kit.install(ROOT, target, 'ba')
            core = target/'ba-workflow/scripts/shared-sdlc-core.zip'
            self._probe(target, target/'ba-workflow/scripts', core)
            record = json.loads((target/'.ba-kit-install.json').read_text())
            self.assertIn('ba-workflow/scripts/shared-sdlc-core.zip', record['managed_files'])
            self.assertIn('ba-workflow', record['skills'])
            self.assertNotIn('files', record)
            self.assertFalse((target/'shared').exists())
            ba_kit.uninstall(target, 'ba')
            self.assertFalse(core.exists())

    def test_test_installed_core_imports_without_checkout(self):
        from tooling.lib import ba_kit
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'skills'
            ba_kit.install(ROOT, target, 'test')
            runtime = target/'.test-kit'
            self._probe(runtime, runtime/'ba-workflow/scripts', runtime/'shared')
            code = '''import importlib, pathlib, sys
root = pathlib.Path(sys.argv[1]); sys.path.insert(0, str(root))
for legacy, core, symbol in %r:
    if legacy.startswith('tooling.'):
        a = importlib.import_module(core)
        b = importlib.import_module(legacy)
        exec('import ' + legacy + ' as historical')
        assert historical is a
        assert a is b and getattr(a, symbol) is getattr(b, symbol)
        assert pathlib.Path(a.__file__).is_relative_to(root/'shared')
''' % (OWNERS,)
            result = subprocess.run([sys.executable, '-I', '-c', code, str(runtime)], cwd=runtime,
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dev_installed_core_imports_without_checkout(self):
        from tooling.install_dev_kit import install
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(install(ROOT, Path(directory)/'dev-home')['runtime_root'])
            self._probe(runtime, runtime/'ba-workflow/scripts', runtime/'shared')
            record = json.loads((runtime/'install-manifest.json').read_text())
            self.assertIn('shared/sdlc/authority/approved_baseline.py', record['files'])

    def test_missing_shared_payload_fails_closed(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory)/'ba-workflow/scripts'
            scripts.mkdir(parents=True)
            shutil.copyfile(ROOT/'ba-workflow/scripts/approved_baseline.py', scripts/'approved_baseline.py')
            code = "import sys; sys.path.insert(0, sys.argv[1]); import approved_baseline"
            result = subprocess.run([sys.executable, '-I', '-c', code, str(scripts)], cwd=directory,
                                    capture_output=True, text=True, timeout=60)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Shared SDLC Core payload is missing', result.stderr)

    def test_ba_archive_exact_allowlist_bytes_and_deterministic_regeneration(self):
        import shutil
        import zipfile
        from tooling.regenerate_shared_sdlc_payload import regenerate, shared_runtime_files
        archive = ROOT/'ba-workflow/scripts/shared-sdlc-core.zip'
        names = shared_runtime_files(ROOT)
        self.assertEqual(set(names), {path.relative_to(ROOT).as_posix() for path in (ROOT/'shared').rglob('*.py')})
        with zipfile.ZipFile(archive) as payload:
            self.assertEqual(payload.namelist(), list(names))
            for name in names:
                self.assertEqual(payload.read(name), (ROOT/name).read_bytes(), name)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'shared', root/'shared', ignore=shutil.ignore_patterns('__pycache__'))
            (root/'ba-workflow/scripts').mkdir(parents=True)
            first = regenerate(root).read_bytes()
            self.assertEqual(first, archive.read_bytes())
            self.assertEqual(regenerate(root).read_bytes(), first)

    def test_standalone_installed_ba_validator_script(self):
        from tooling.lib import ba_kit
        from tooling.tests.test_dev_kit import _write_approved_baseline
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root/'skills'
            ba_kit.install(ROOT, target, 'ba')
            handoff = _write_approved_baseline(root/'project')
            result = subprocess.run([sys.executable, '-E', str(target/'ba-workflow/scripts/validate-handoff.py'), str(handoff)],
                                    cwd=root/'project', capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
