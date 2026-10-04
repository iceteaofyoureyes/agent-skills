"""Run with isolated pinned Spec Kit Python; synthetic dispatch, real engine/state.

The expensive agent prompt seam is synthetic. Workflow loading, validation,
shell dispatch, pause and fresh-engine resume use the real pinned runtime.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tooling.lib.dev_vnext_spec_kit import SpecKitAdapter, read_workflow_state, workflow_document
from specify_cli.workflows.engine import WorkflowEngine
from specify_cli.workflows.step.prompt import PromptStep


def main():
    executable = sys.argv[1]
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        engine = WorkflowEngine(root)
        source = root/'.devkit/runs/RUN-1/workflow-vnext.yml'
        source.parent.mkdir(parents=True)
        for high in (False,True):
            source.write_text(json.dumps(workflow_document(high_risk=high)),encoding='utf-8')
            definition = engine.load_workflow(source)
            assert engine.validate(definition)==[]
        transport = root/('transport.cmd' if os.name=='nt' else 'transport')
        if os.name=='nt': transport.write_text('@echo off\n@echo {"required":true}\n',encoding='utf-8')
        else:
            transport.write_text('#!/bin/sh\nprintf \'{"required":true}\\n\'\n',encoding='utf-8')
            transport.chmod(0o755)
        inputs = {'run_id':'RUN-1','run_dir':str(source.parent),'devkit_command':str(transport),
            'integration':'synthetic','technical_receipt_ref':'receipt-ref.json','host':''}
        dispatched = {'exit_code':0,'stdout':'','stderr':''}
        with patch.object(PromptStep,'_try_dispatch',return_value=dispatched), patch('sys.stdin.isatty',return_value=False):
            state = engine.execute(definition,inputs,run_id='WORKFLOW-1')
            assert state.status.value=='paused'
            persisted = root/'.specify/workflows/runs/WORKFLOW-1/state.json'
            ref = {'path':persisted.relative_to(root).as_posix(),'revision':'WORKFLOW-1',
                'sha256':hashlib.sha256(persisted.read_bytes()).hexdigest()}
            observation = read_workflow_state(root,ref,'WORKFLOW-1')
            assert observation['choice'] is None and observation['technical_authority'] is False
            resumed = WorkflowEngine(root).resume('WORKFLOW-1',inputs={'technical_choice':'approve'})
            assert resumed.status.value=='completed'
            ref['sha256']=hashlib.sha256(persisted.read_bytes()).hexdigest()
            observed = read_workflow_state(root,ref,'WORKFLOW-1')
            assert observed['choice']=='approve' and observed['technical_authority'] is False
        result = SpecKitAdapter(root,[executable]).execute('status','WORKFLOW-1')
        assert result['exit_code']==0
        assert 'WORKFLOW-1' in result['output']
        assert not (root/'spec.md').exists()
        print(json.dumps({'SPEC_KIT_VERSION':'1.0.11','NORMAL_DEFINITION':'VALID',
            'HIGH_RISK_DEFINITION':'VALID','PAUSE':'PASS','FRESH_ENGINE_RESUME':'PASS',
            'PERSISTED_CHOICE_NON_AUTHORITATIVE':'PASS','LIVE_CLI_STATUS':'PASS'}))


if __name__=='__main__': main()
