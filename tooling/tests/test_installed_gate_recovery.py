"""Fresh package must run fixed gates without importing the source runtime."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tooling.lib import ba_kit


ROOT = Path(__file__).resolve().parents[2]


class InstalledGateRecoveryTests(unittest.TestCase):
    def test_isolated_installed_design_and_case_gate_recovery(self):
        with tempfile.TemporaryDirectory(prefix='installed-gates-') as temp:
            project = Path(temp)
            skills = project / '.agents/skills'
            ba_kit.install(ROOT, skills, 'test', project_root=project)
            script = project / 'acceptance.py'
            script.write_text('''
import json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from tooling.lib import test_kit_v1 as design, test_kit_v1_cases as cases, gate_persistence as persistence
installed, source, project = map(Path, sys.argv[1:4])
assert Path(design.__file__).resolve().is_relative_to(installed.resolve())
assert Path(cases.__file__).resolve().is_relative_to(installed.resolve())
assert Path(persistence.__file__).resolve().is_relative_to(installed.resolve())
bundle = design.adapt_ba_to_tea(source/'kits/ba/examples/CR-001/vi/05-engineering-handoff.yml')
raw = source/'benchmark/test-kit/petclinic/tea-test-design/raw-output/test-design/test-design-epic-1.md'
assert design.normalize_tea_output(raw, bundle.baseline).status == 'NORMALIZED'
snapshot = design.DesignSnapshot.create((design.CanonicalTestDesign(
    'TD-001', ('CR-001','P1'), 'Appointment behavior', 'A valid Appointment is saved as Scheduled.',
    tuple(sorted(bundle.baseline.ba_ids)),
    tuple(design.OpenQuestion(source,text) for source,text in bundle.baseline.unknown_clauses.items())),),
    artifact_id='CR-001-test-design',revision='1')
validation = design.validate_design(snapshot, bundle.baseline)
def receipt(gate, snapshot, refs, decision):
    return {'gate':gate,'decision':decision,'artifact_id':snapshot.artifact_id,
            'artifact_revision':snapshot.revision,'artifact_sha256':snapshot.sha256,
            'input_refs':refs,'actor_id':'human:installed-smoke','actor_role':'HUMAN',
            'decided_at':'2026-10-03T12:00:00Z','feedback':'Fixture change request'}
auth = lambda actor,_: design.AuthenticatedHumanActorContext(actor)
for decision in ['APPROVE','REQUEST_CHANGES']:
    run = project/decision
    state=design.submit_design_for_review(design.start_design_workflow(snapshot),snapshot,validation)
    design.persist_design_review(run,bundle,raw,snapshot,validation,state)
    value=receipt('DESIGN_REVIEW',snapshot,design.design_gate_input_refs(bundle.baseline,run),decision)
    apply=lambda: design.apply_design_decision(run,snapshot,bundle.baseline,value,
        human_actor_authenticator=auth,next_revision='2' if decision=='REQUEST_CHANGES' else None)
    atomic=persistence.atomic_workflow
    with patch.object(persistence,'atomic_workflow',side_effect=OSError('fault before state commit')):
        assert not apply().accepted
    assert apply().accepted
    assert apply().accepted
design_run=project/'APPROVE'
design_receipt=design_run/'design-gate/revisions/1/receipt.json'
import hashlib
row=cases.CanonicalTestcase('TC-001','Create appointment','Check creation','A valid Pet exists.','Pet A',
    (cases.CaseStep('Create appointment',None,'Appointment is saved as Scheduled.'),),'P1',('FR-001',),('TD-001',),(),'DRAFT')
case=cases.CaseSnapshot.create((row,),artifact_id='CR-001-testcases',revision='1')
case_validation=cases.validate_testcases(case,snapshot,bundle.baseline)
assert case_validation.status=='PASS',case_validation.findings
for decision in ['APPROVE','REQUEST_CHANGES']:
    run=project/('case-'+decision)
    state=cases.submit_cases_for_review(cases.start_case_workflow(case),case,case_validation,
        design_gate_receipt_mode='HUMAN_AUTHENTICATED',
        design_gate_receipt_evidence={'path':str(design_receipt),'sha256':hashlib.sha256(design_receipt.read_bytes()).hexdigest(),'mode':'HUMAN_AUTHENTICATED'},
        input_refs=cases.case_gate_input_refs(bundle.baseline,snapshot))
    norm=cases.CaseNormalizationResult('NORMALIZED','installed-smoke',case,(),())
    cases.persist_case_review(run,norm,case_validation,state)
    value=receipt('CASE_REVIEW',case,cases.case_gate_input_refs(bundle.baseline,snapshot),decision)
    apply=lambda: cases.apply_case_gate_decision(value,case,snapshot,bundle.baseline,state,
        workflow_dir=run,human_actor_authenticator=auth,next_revision='2' if decision=='REQUEST_CHANGES' else None)
    with patch.object(persistence,'atomic_workflow',side_effect=OSError('fault before state commit')):
        assert apply().status=='REJECTED'
    assert apply().status!='REJECTED'
    assert apply().status!='REJECTED'
print(json.dumps({'installed_runtime':str(design.__file__),'gate_transitions':4,'status':'PASS'}))
''', encoding='utf-8')
            result = subprocess.run([sys.executable, '-I', str(script), str(skills/'.test-kit'), str(ROOT), str(project)],
                                    cwd=project, capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['gate_transitions'], 4)
            self.assertEqual(report['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
