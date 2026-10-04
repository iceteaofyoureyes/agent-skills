"""Public Dev CLI defaults to V2; historical runtime is inspection only."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from tooling.lib import dev_kit


class DevVNextCLITests(unittest.TestCase):
    def invoke(self, *argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = dev_kit.main(list(argv))
        return result, stdout.getvalue(), stderr.getvalue()

    def test_start_rejects_v1_request_without_creating_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = root / 'request.json'
            request.write_text(json.dumps({'schema_version': 1, 'change_id': 'CHANGE-1'}))
            code, _, error = self.invoke('--project-root', str(root), 'start', '--request', str(request))
            self.assertEqual(code, 2)
            self.assertIn('VNext', error)
            self.assertFalse((root / '.devkit').exists())

    def test_delivery_routing_cannot_create_feature_authority(self):
        code, _, error = self.invoke('route', '--delivery', 'delivery.json', '--summary', 'feature')
        self.assertEqual(code, 2)
        self.assertIn('DEFERRED_NON_AUTHORITATIVE', error)

    def test_legacy_artifact_inspection_has_no_vnext_authority(self):
        with tempfile.TemporaryDirectory() as temp:
            artifact = Path(temp) / 'state.json'
            artifact.write_text(json.dumps({'schema_version': 1, 'status': 'READY_FOR_TEST'}))
            code, output, _ = self.invoke('legacy', 'inspect', '--kind', 'state', str(artifact))
            self.assertEqual(code, 0)
            result = json.loads(output)
            self.assertEqual(result['mode'], 'LEGACY_COMPAT')
            self.assertIs(result['vnext_authority'], False)

    def test_spec_kit_choice_is_not_a_technical_receipt(self):
        code, _, error = self.invoke('gate-approved', '--choice', 'approve', '--workflow-run-id', 'FLOW-1')
        self.assertEqual(code, 2)
        self.assertIn('authenticated', error)

    def test_schema2_default_start_and_status_reload_through_installed_launcher(self):
        from tooling import install_dev_kit
        from tooling.tests.test_dev_vnext_runtime import DevRuntimePersistenceTests
        fixture = DevRuntimePersistenceTests('test_reload_only_persisted_state_and_reject_state_tampering')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        installed = install_dev_kit.install(Path(__file__).resolve().parents[2],fixture.root/'installed')
        request_path = fixture.root/'request.json'
        request_path.write_text(json.dumps({'schema_version':2,**fixture.request}))
        command = ['powershell','-NoProfile','-File',installed['launcher']] if os.name == 'nt' else [installed['launcher']]
        start = subprocess.run([*command,'start','--request',str(request_path)],cwd=fixture.root,capture_output=True,text=True)
        self.assertEqual(start.returncode,0,start.stderr)
        state = json.loads(start.stdout)
        self.assertEqual(state['schema_version'],2)
        self.assertEqual(state['lifecycle'],'INTAKE')
        self.assertEqual((fixture.repo/'src/note.txt').read_text(),'before\n')
        status = subprocess.run([*command,'status'],cwd=fixture.root,capture_output=True,text=True)
        self.assertEqual(status.returncode,0,status.stderr)
        self.assertEqual(json.loads(status.stdout)['state']['run_id'],fixture.request['run_id'])

    def test_cli_failure_status_is_nonzero(self):
        from tooling.tests.test_dev_vnext_runtime import DevRuntimePersistenceTests
        fixture = DevRuntimePersistenceTests('test_reload_only_persisted_state_and_reject_state_tampering')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.ready()
        changes = fixture.root/'discovery.json'
        changes.write_text(json.dumps(['security']))
        code,output,_ = self.invoke('--project-root',str(fixture.root),'maintenance-discovery','--changes',str(changes))
        self.assertEqual(code,1)
        self.assertEqual(json.loads(output)['lifecycle'],'BLOCKED')

    def test_gap_resume_cli_revalidates_replacement_when_previous_approval_is_revoked(self):
        from tooling.tests.test_dev_vnext_runtime_acceptance import RuntimeAcceptanceTests
        from tooling.tests import test_ba_vnext as ba_tests
        fixture = RuntimeAcceptanceTests('test_gap_blocks_writes_and_resume_requires_reapproved_previous_baseline')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.planned()
        fixture.runtime.raise_gap({'schema_version':2,'gap_id':'GAP-001','finding_kind':'SPEC_GAP',
            'feature_id':'FEATURE-1','engineering_handoff_ref':fixture.upstream,'affected_business_ids':['FR-001'],
            'evidence_refs':[fixture.ba.ref('review-evidence.json')],'question':'Clarify outcome',
            'blocking_scope':{'core':['src']},'discovered_at':'2026-10-04T10:00:00Z','status':'OPEN'})
        old_receipt = (fixture.root/'receipt.json').read_bytes()
        candidate = copy.deepcopy(fixture.ba.candidate)
        candidate.update(revision='R2',previous_baseline=fixture.ba.candidate_ref)
        candidate['semantic_sha256'] = ba_tests.ba.candidate_hash(candidate)
        fixture.ba.candidate = candidate
        fixture.ba.candidate_ref = fixture.ba.publish(candidate)
        fixture.ba.state = ba_tests.ba.select_candidate(ba_tests.ba.new_state(candidate['feature'],'GREENFIELD'),fixture.ba.candidate_ref,fixture.root)
        approved,auth = fixture.ba.approved()
        handoff = ba_tests.ba.make_handoff(approved,fixture.root,human_actor_authenticator=auth)
        (fixture.root/'receipt-r2.json').write_bytes((fixture.root/'receipt.json').read_bytes())
        handoff['approval_receipt'] = fixture.ba.ref('receipt-r2.json','R2')
        (fixture.root/'receipt.json').write_bytes(old_receipt)
        fixture.ba.put('replacement-handoff.json',handoff)
        replacement = fixture.root/'replacement-ref.json'
        resolution = fixture.root/'resolution-ref.json'
        replacement.write_text(json.dumps(fixture.ba.ref('replacement-handoff.json','R2')))
        resolution.write_text(json.dumps(fixture.ba.ref('review-evidence.json')))
        host = types.ModuleType('synthetic_gap_host')
        host.ba_authenticator = auth
        with patch.dict(sys.modules,{'synthetic_gap_host':host}):
            code,output,error = self.invoke('--project-root',str(fixture.root),'--host','synthetic_gap_host',
                'resume-gap','--replacement-ref',str(replacement),'--resolution-ref',str(resolution))
        self.assertEqual(code,0,error)
        self.assertEqual(json.loads(output)['lifecycle'],'AUTHORITY_VALIDATED')


if __name__ == '__main__':
    unittest.main()
