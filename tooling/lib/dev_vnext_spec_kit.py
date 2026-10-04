"""Pinned Spec Kit workflow transport, independent of requirements authority.

Workflow state records pause/resume and choices. Only the Dev runtime can bind
authenticated technical receipts or authorize a source mutation.
"""
import json
from pathlib import Path
import re
import subprocess

from shared.sdlc.schema import identifier, validate_reference


FORBIDDEN_COMMANDS = ('speckit.specify','speckit.plan','speckit.tasks','speckit.analyze','speckit.converge')


def workflow_document(*, high_risk=False):
    """JSON is valid YAML; generated workflows never create requirements specs."""
    shell = '"{{ inputs.devkit_command }}" --host "{{ inputs.host }}" --run-id "{{ inputs.run_id }}"'
    def command(name, arguments):
        return {'id':name,'type':'shell','run':f'{shell} {arguments}'}
    def prompt(name, text):
        return {'id':name,'type':'prompt','integration':'{{ inputs.integration }}','prompt':text}
    steps = [
        command('validate-authority','validate-authority'),
        prompt('engineering-impact',
            'Inspect source and the exact Engineering Handoff VNext. Create Engineering Impact V2 at impact.json inside the active run. '
            'Record technical facts, knowledge impact, unknowns, repository base revisions and explicit write paths. '
            'Do not fabricate answers or decide WHAT. A WHAT gap must use raise-gap and route BA/Human.'),
        command('bind-impact','impact --artifact "{{ inputs.run_dir }}/impact.json"'),
        prompt('technical-plan',
            'Write dev-plan.md and dev-tasks.md in the active run, referencing upstream authority and engineering impact. '
            'Use incremental slices, focused tests and regression-first TDD. Record active material ED exact refs. '
            'Write engineering-decision-refs.json as an array of exact ED refs (empty when no material ED). '
            'Do not duplicate BR/FR business prose or expand repository/write scope.'),
        command('bind-plan','plan --plan "{{ inputs.run_dir }}/dev-plan.md" --tasks "{{ inputs.run_dir }}/dev-tasks.md" --decision-refs "{{ inputs.run_dir }}/engineering-decision-refs.json"'),
    ]
    technical_gate = [
            {'id':'human-tech-lead-plan-gate','type':'gate',
             'message':'Review the exact impact, ED set, plan/tasks, repository bases, write scope and risk. '
                 'This choice is only workflow transport. Supply an exact authenticated Human/Tech Lead receipt through the trusted host before implementation.',
             'options':['approve','reject'],'on_reject':'abort','verdict_input':'technical_choice'},
            command('bind-authenticated-technical-receipt','bind-technical-approval --artifact "{{ inputs.technical_receipt_ref }}"'),
        ]
    if high_risk:
        steps += technical_gate
    else:
        gate_required = command('technical-gate-requirement','technical-gate-required')
        gate_required['output_format'] = 'json'
        steps += [gate_required,{'id':'conditional-technical-gate','type':'if',
            'condition':'{{ steps.technical-gate-requirement.output.data.required }}','then':technical_gate,'else':[]}]
    steps += [
        command('implementation-ready','implementation-ready'),
        command('begin-implementation','begin-implementation'),
        prompt('implementation',
            'Implement only the bound technical plan, with focused tests for incremental slices. '
            'Every runtime-controlled write must use write-source or authorize-write for its exact repository/path. '
            'Stop and raise-gap for WHAT ambiguity; use escalate-risk/replan for new material risk. '
            'Stop before the single consolidated review.'),
        prompt('consolidated-review',
            'Perform exactly one consolidated full review against exact upstream authority, snapshot and implementation revisions. '
            'Write review-evidence.json and review-ref.json inside the run. Record blocking findings in blocking-findings.json. '
            'WHAT/spec findings require an Engineering Gap artifact, never a code-first workaround. '
            'For blockers use one begin-fix-wave followed by at most one scoped rereview; never another full review.'),
        command('record-consolidated-review','review --evidence-ref "{{ inputs.run_dir }}/review-ref.json" --findings "{{ inputs.run_dir }}/blocking-findings.json"'),
        prompt('bounded-blocking-resolution',
            'If blocking findings exist, claim begin-fix-wave once, fix only those findings through the mutation guard, '
            'and submit one scoped review with exact evidence and remaining blockers. If no blockers, do no work. '
            'No second full review or unapproved scope expansion.'),
        command('fresh-engineering-verification','verify'),
        prompt('coverage',
            'Write coverage.json mapping every exact approved BR/FR ID to code and test evidence. '
            'Do not invent requirement IDs, claim downstream acceptance or modify the final handoff directly.'),
        command('canonical-dev-handoff','finalize --coverage "{{ inputs.run_dir }}/coverage.json"'),
    ]
    return {'schema_version':'1.0','workflow':{
        'id':'dev-vnext-high-risk' if high_risk else 'dev-vnext-normal',
        'name':'Dev VNext Runtime','version':'2.0.0','author':'Agent Skills Dev Kit',
        'description':'Workflow transport for exact Engineering Handoff authority; terminal Dev state READY_FOR_TEST.'},
        'requires':{'speckit_version':'==1.0.11'},
        'inputs':{name:{'type':'string','default':default} for name,default in (
            ('devkit_command','devkit'),('integration','auto'),('run_dir',''),('run_id',''),('host',''),('technical_choice',''),('technical_receipt_ref',''))},
        'steps':steps}


def read_workflow_state(root, ref, workflow_run_id):
    identifier(workflow_run_id)
    path = validate_reference(ref,root,revision=True)
    expected = Path(root).resolve()/'.specify/workflows/runs'/workflow_run_id/'state.json'
    if path.resolve() != expected.resolve():
        raise ValueError('Spec Kit state path does not bind workflow run identity')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('run_id') != workflow_run_id:
        raise ValueError('Spec Kit persisted run identity mismatch')
    results = data.get('step_results',{})
    if not isinstance(results,dict): raise ValueError('Spec Kit step results must be an object')
    gate = results.get('human-tech-lead-plan-gate',{})
    choice = None
    if not isinstance(gate,dict): raise ValueError('invalid Spec Kit gate evidence')
    if gate and gate.get('status') != 'paused':
        if gate.get('status') != 'completed' or not isinstance(gate.get('output'),dict):
            raise ValueError('Spec Kit gate evidence is incomplete')
        choice = gate['output'].get('choice')
        if choice not in ('approve','reject'): raise ValueError('unsupported Spec Kit gate choice')
    return {'workflow_run_id':workflow_run_id,'workflow_state_ref':ref,
        'status':data.get('status'),'choice':choice,'technical_authority':False}


class SpecKitAdapter:
    def __init__(self, root, executable):
        self.root = Path(root).resolve()
        self.executable = list(executable)
        if not self.executable or any(not isinstance(part,str) or not part for part in self.executable):
            raise ValueError('Spec Kit executable must be a non-empty argv')

    def execute(self, action, source, *, inputs=()):
        if action not in ('run','resume','status'):
            raise ValueError('Spec Kit supports workflow transport operations only')
        if any(forbidden in str(source) for forbidden in FORBIDDEN_COMMANDS):
            raise ValueError('Spec Kit requirements commands are disabled')
        if action == 'run':
            path = Path(source).resolve()
            if not path.is_relative_to(self.root/'.devkit/runs'):
                raise ValueError('Spec Kit run must use the generated VNext workflow')
            document = json.loads(path.read_text(encoding='utf-8'))
            if document not in (workflow_document(high_risk=False),workflow_document(high_risk=True)):
                raise ValueError('Spec Kit workflow definition is not canonical VNext transport')
        if action != 'run': identifier(source)
        version = subprocess.run([*self.executable,'--version'],cwd=self.root,capture_output=True,text=True,encoding='utf-8',errors='replace',check=False,timeout=30)
        if version.returncode != 0 or not re.fullmatch(r'specify\s+1\.0\.11',version.stdout.strip()):
            raise ValueError('Spec Kit runtime must be pinned to 1.0.11')
        command = [*self.executable,'workflow',action,str(source)]
        if action in ('run','resume'):
            for key,value in inputs:
                if key not in ('devkit_command','integration','run_dir','run_id','host','technical_choice','technical_receipt_ref'):
                    raise ValueError('unsupported workflow transport input')
                command += ['--input',f'{key}={value}']
            command += ['--json']
        result = subprocess.run(command,cwd=self.root,capture_output=True,text=True,encoding='utf-8',errors='replace',check=False,timeout=3600)
        if result.returncode != 0:
            raise ValueError(f'Spec Kit workflow transport failed (exit {result.returncode}): {result.stderr.strip()}')
        return {'command':command,'exit_code':result.returncode,'output':result.stdout,'technical_authority':False}

    def execute_runtime(self, runtime, action, workflow_run_id=None, *, devkit_command='devkit', technical_receipt_ref='', integration='auto', host='', choice=''):
        state = runtime.load()
        if state['authority_mode'] != 'FEATURE_DELIVERY':
            raise ValueError('TRIVIAL maintenance uses the direct runtime fast path')
        inputs = [('devkit_command',devkit_command),('integration',integration),
            ('run_dir',str(self.root/'.devkit/runs'/state['run_id'])),('run_id',state['run_id']),('host',host),('technical_choice',choice),('technical_receipt_ref',technical_receipt_ref)]
        if action == 'run':
            if runtime.metadata['workflow']:
                raise ValueError('active Dev run already has a workflow; use resume')
            high = state['risk']['level'] == 'HIGH_RISK'
            source = self.root/'.devkit/runs'/state['run_id']/'workflow-vnext.yml'
            if source.is_symlink() or source.parent.resolve() != source.parent:
                raise ValueError('unsafe workflow artifact path')
            document = workflow_document(high_risk=high)
            payload = (json.dumps(document,indent=2)+'\n').encode()
            if source.exists() and source.read_bytes() != payload:
                raise ValueError('persisted VNext workflow definition drift')
            from .dev_vnext_runtime import _atomic
            _atomic(source,payload)
        else:
            if not workflow_run_id: raise ValueError('workflow-run-id required for resume/status')
            if runtime.metadata['workflow'].get('workflow_run_id') != workflow_run_id:
                raise ValueError('Spec Kit workflow run is not bound to the active Dev run')
            source = workflow_run_id
        result = self.execute(action,source,inputs=inputs)
        if action in ('run','resume'):
            payload = json.loads(result['output'])
            workflow_run_id = payload.get('run_id')
            identifier(workflow_run_id)
            state_path = self.root/'.specify/workflows/runs'/workflow_run_id/'state.json'
            observed = read_workflow_state(self.root,runtime.reference(state_path),workflow_run_id)
            workflow_data = json.loads(state_path.read_text(encoding='utf-8'))
            if workflow_data.get('inputs',{}).get('run_id') != state['run_id']:
                raise ValueError('Spec Kit state inputs do not bind the active Dev run')
            runtime.record_workflow(observed)
            result['workflow'] = observed
        return result

    def observe(self, runtime, ref, workflow_run_id):
        runtime.load()
        observed = read_workflow_state(self.root,ref,workflow_run_id)
        workflow_data = json.loads(validate_reference(ref,self.root,revision=True).read_text(encoding='utf-8'))
        if workflow_data.get('inputs',{}).get('run_id') != runtime.state['run_id']:
            raise ValueError('Spec Kit state inputs do not bind the active Dev run')
        previous = runtime.metadata['workflow'].get('workflow_run_id')
        if previous is not None and previous != workflow_run_id:
            raise ValueError('Spec Kit workflow identity replacement is not allowed')
        runtime.record_workflow(observed)
        return observed
