"""Spec Kit transports workflow choices; it never authenticates approval."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tooling.lib import dev_vnext_spec_kit as adapter


class SpecKitVNextTests(unittest.TestCase):
    def test_workflow_is_transport_with_one_consolidated_review(self):
        for high in (False, True):
            workflow = adapter.workflow_document(high_risk=high)
            self.assertEqual(workflow['requires']['speckit_version'], '==1.0.11')
            text = json.dumps(workflow)
            for command in adapter.FORBIDDEN_COMMANDS:
                self.assertNotIn(command, text)
            self.assertNotIn('spec.md', text)
            self.assertEqual(sum(step['id'] == 'consolidated-review' for step in workflow['steps']), 1)
            gates = [step for step in workflow['steps'] if step['type'] == 'gate']
            self.assertEqual(len(gates), int(high))
            if high:
                self.assertIn('authenticated', gates[0]['message'])
                self.assertIn('bind-technical-approval', text)

    def test_persisted_choice_is_only_orchestration_evidence_and_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / '.specify/workflows/runs/FLOW-1/state.json'
            path.parent.mkdir(parents=True)
            state = {'run_id':'FLOW-1','status':'paused','step_results':{
                'human-tech-lead-plan-gate':{'status':'completed','output':{'choice':'approve'}}}}
            path.write_text(json.dumps(state))
            ref = {'path':path.relative_to(root).as_posix(), 'revision':'FLOW-1', 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            observed = adapter.read_workflow_state(root, ref, 'FLOW-1')
            self.assertIs(observed['technical_authority'], False)
            self.assertEqual(observed['choice'], 'approve')
            with self.assertRaises(ValueError): adapter.read_workflow_state(root, ref, 'OTHER')
            path.write_text(json.dumps({**state, 'status':'completed'}))
            with self.assertRaises(ValueError): adapter.read_workflow_state(root, ref, 'FLOW-1')

    def test_only_pinned_workflow_transport_can_execute(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(adapter.subprocess, 'run', return_value=subprocess.CompletedProcess([],0,'specify 1.0.6','')):
                with self.assertRaisesRegex(ValueError, '1.0.11'):
                    adapter.SpecKitAdapter(temp, ['specify']).execute('status', 'FLOW-1')
            with patch.object(adapter.subprocess, 'run') as run:
                with self.assertRaises(ValueError): adapter.SpecKitAdapter(temp, ['specify']).execute('speckit.plan', 'FLOW-1')
                run.assert_not_called()

    def test_workflow_observation_survives_live_resume_and_rejects_other_dev_run(self):
        from tooling.tests.test_dev_vnext_runtime_acceptance import RuntimeAcceptanceTests
        fixture = RuntimeAcceptanceTests('test_gap_blocks_writes_and_resume_requires_reapproved_previous_baseline')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        fixture.runtime.start(fixture.request())
        root = fixture.root
        path = root/'.specify/workflows/runs/FLOW-1/state.json'
        path.parent.mkdir(parents=True)
        document = {'run_id':'FLOW-1','status':'paused','inputs':{'run_id':'OTHER'},'step_results':{}}
        path.write_text(json.dumps(document))
        transport = adapter.SpecKitAdapter(root,['specify'])
        with self.assertRaises(ValueError): transport.observe(fixture.runtime,fixture.runtime.reference(path),'FLOW-1')
        document['inputs']['run_id']='RUN-1'
        path.write_text(json.dumps(document))
        transport.observe(fixture.runtime,fixture.runtime.reference(path),'FLOW-1')
        frozen = fixture.runtime.metadata['workflow']['workflow_state_ref']
        document['status']='completed'
        path.write_text(json.dumps(document))
        self.assertEqual(fixture.new_runtime().load()['lifecycle'],'INTAKE')
        self.assertNotEqual(frozen['path'],path.relative_to(root).as_posix())
        transport.observe(fixture.runtime,fixture.runtime.reference(path),'FLOW-1')
        self.assertEqual(fixture.runtime.metadata['workflow']['status'],'completed')
        with patch.object(transport,'execute') as execute:
            with self.assertRaises(ValueError): transport.execute_runtime(fixture.runtime,'resume','UNBOUND')
            execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
