"""Runtime persistence and host guards use actual Git repositories."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tooling.lib.dev_vnext_runtime import DevRuntime


class DevRuntimePersistenceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / 'implementation'
        self.repo.mkdir()
        self.git('init')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        self.git('config', 'user.name', 'Synthetic Runtime')
        (self.repo / 'src').mkdir()
        (self.repo / 'src' / 'note.txt').write_text('before\n')
        self.git('add', '.')
        self.git('commit', '-m', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip()
        (self.root / 'evidence.txt').write_text('mechanical rename evidence')
        self.runtime = DevRuntime(self.root)
        self.request = dict(run_id='RUN-1', change_id='CHANGE-1', summary='Mechanical edit',
            authority_mode='TECHNICAL_MAINTENANCE',
            repositories=[dict(id='core', role='IMPLEMENTATION', base_revision=self.base,
                allowed_write_paths=['src'], read_only_evidence_paths=[])],
            repository_roots={'core':str(self.repo)},
            checks=[dict(name='unit', category='UNIT', command=[sys.executable,'-c','print("fresh")'])],
            maintenance=dict(kind='MECHANICAL', no_what_change=True, discovered_changes=[],
                evidence_refs=[self.runtime.reference('evidence.txt', 'EVIDENCE-1')]))

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, text=True)
        if result.returncode: raise AssertionError(result.stderr)
        return result.stdout

    def ready(self):
        self.runtime.start(self.request)
        self.runtime.validate_authority()
        return self.runtime.implementation_ready()

    def test_reload_only_persisted_state_and_reject_state_tampering(self):
        self.ready()
        resumed = DevRuntime(self.root)
        self.assertEqual(resumed.load()['lifecycle'], 'IMPLEMENTATION_READY')
        path = self.root / '.devkit/runs/RUN-1/state.json'
        state = json.loads(path.read_text())
        state['repositories'][0]['allowed_write_paths'].append('outside')
        path.write_text(json.dumps(state))
        with self.assertRaises(ValueError): resumed.load()

    def test_truncated_state_and_schema_and_history_are_rejected(self):
        self.runtime.start(self.request)
        path = self.root / '.devkit/runs/RUN-1/state.json'
        original = path.read_bytes()
        for changed in (b'{', json.dumps({**json.loads(original), 'schema_version':99}).encode(),
                        json.dumps({**json.loads(original), 'lifecycle':'IMPLEMENTING'}).encode()):
            path.write_bytes(changed)
            with self.assertRaises(ValueError): DevRuntime(self.root).load()
        path.write_bytes(original)

    def test_guard_scope_base_and_actual_write(self):
        self.runtime.start(self.request)
        with self.assertRaises(ValueError): self.runtime.write_source('core','src/note.txt','blocked')
        self.runtime.validate_authority()
        self.runtime.implementation_ready()
        for path in ('outside.txt','../evidence.txt','.git/config'):
            with self.assertRaises(ValueError): self.runtime.write_source('core',path,'blocked')
        self.runtime.write_source('core','src/note.txt','after\n')
        self.assertEqual((self.repo/'src/note.txt').read_text(),'after\n')
        self.assertEqual(self.runtime.load()['lifecycle'],'IMPLEMENTING')

    def test_atomic_commit_recovery_from_previous_valid_state(self):
        initial = self.runtime.start(self.request)
        self.runtime.validate_authority()
        path = self.root / '.devkit/runs/RUN-1/state.json'
        path.write_text(json.dumps(initial))
        resumed = DevRuntime(self.root)
        self.assertEqual(resumed.load()['lifecycle'],'AUTHORITY_VALIDATED')
        self.assertEqual(json.loads(path.read_text())['lifecycle'],'AUTHORITY_VALIDATED')

    def test_fresh_process_checks_and_final_revision(self):
        self.ready()
        self.runtime.write_source('core','src/note.txt','after\n')
        self.git('add','src/note.txt')
        self.git('commit','-m','mechanical change')
        verification = self.runtime.verify()
        self.assertEqual(verification['checks'][0]['status'],'PASS')
        handoff = self.runtime.finalize([])
        self.assertEqual(handoff['state'],'READY_FOR_TEST')
        self.assertEqual(handoff['repository_revisions']['core'],self.git('rev-parse','HEAD').strip())
        self.assertEqual(DevRuntime(self.root).load()['lifecycle'],'READY_FOR_TEST')

    def test_ambiguous_identity_and_wrong_intake_base_fail(self):
        bad = copy.deepcopy(self.request)
        bad['repositories'][0]['base_revision']='a'*40
        with self.assertRaises(ValueError): self.runtime.start(bad)
        bad = copy.deepcopy(self.request)
        bad['repository_roots']['core']=str(self.repo/'src')
        with self.assertRaises(ValueError): self.runtime.start(bad)

    def test_selected_run_does_not_switch_to_current_run(self):
        self.runtime.start(self.request)
        other=copy.deepcopy(self.request)
        other['run_id']='RUN-2'
        DevRuntime(self.root).start(other)
        selected=DevRuntime(self.root)
        selected.load('RUN-1')
        self.assertEqual(selected.validate_authority()['run_id'],'RUN-1')

    def test_runtime_discovery_durably_invalidates_maintenance(self):
        self.ready()
        blocked=self.runtime.discover_maintenance_change(['SECURITY'])
        self.assertEqual(blocked['lifecycle'],'BLOCKED')
        resumed=DevRuntime(self.root)
        self.assertEqual(resumed.load()['lifecycle'],'BLOCKED')
        with self.assertRaises(ValueError): resumed.write_source('core','src/note.txt','blocked')

    def test_check_names_cannot_escape_evidence_directory(self):
        request=copy.deepcopy(self.request)
        request['checks'][0]['name']='../../../authority'
        with self.assertRaises(ValueError): self.runtime.start(request)

    def test_pre_ready_repository_commits_are_not_an_observed_base(self):
        self.runtime.start(self.request)
        self.runtime.validate_authority()
        (self.repo/'src/note.txt').write_text('changed before authorization\n')
        self.git('add','src/note.txt')
        self.git('commit','-m','unauthorized pre-readiness change')
        with self.assertRaises(ValueError): self.runtime.implementation_ready()

    def test_mutable_workflow_transport_is_captured_as_immutable_evidence(self):
        self.ready()
        path=self.root/'.specify/workflows/runs/FLOW-1/state.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(dict(run_id='FLOW-1',status='paused')))
        self.runtime.record_workflow(dict(workflow_run_id='FLOW-1',workflow_state_ref=self.runtime.reference(path),technical_authority=False))
        observed=self.runtime.metadata['workflow']['workflow_state_ref']
        path.write_text(json.dumps(dict(run_id='FLOW-1',status='completed')))
        resumed=DevRuntime(self.root)
        self.assertEqual(resumed.load()['lifecycle'],'IMPLEMENTATION_READY')
        self.assertEqual(resumed.metadata['workflow']['workflow_state_ref'],observed)
        resumed.record_workflow(dict(workflow_run_id='FLOW-1',workflow_state_ref=resumed.reference(path),technical_authority=False))
        self.assertNotEqual(resumed.metadata['workflow']['workflow_state_ref'],observed)


if __name__ == '__main__':
    unittest.main()
