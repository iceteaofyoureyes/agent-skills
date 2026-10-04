"""Fresh installed BA runtime acceptance; test host approval is synthetic."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tooling.lib import ba_kit
from tooling.lib import package
from tooling.tests import test_project_foundation


ROOT = Path(__file__).resolve().parents[2]


class InstalledBAVNextAcceptance(unittest.TestCase):
    def test_install_doctor_vnext_host_gate_handoff_and_v1_compatibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            target = temporary / "installed-skills"
            project = temporary / "project"
            project.mkdir()
            shutil.copytree(ROOT / "tooling/tests/fixtures/ba-vnext", project, dirs_exist_ok=True)
            foundation = test_project_foundation.FoundationTests("runTest")
            foundation.setUp()
            self.addCleanup(foundation.doCleanups)
            foundation.promoted()
            shutil.copytree(foundation.root, project / "foundation")

            install_cmd = [sys.executable, "-I", str(ROOT / "tooling/lib/ba_kit.py"), "install", "ba", "--agent", "generic", "--target", str(target)]
            install_result = subprocess.run(install_cmd, cwd=temporary, capture_output=True, text=True, timeout=60)
            self.assertEqual(install_result.returncode, 0, install_result.stderr)
            self.assertIn("Installed or verified", install_result.stdout)
            before = ba_kit.tree_hash(target)
            repeated = subprocess.run(install_cmd, cwd=temporary, capture_output=True, text=True, timeout=60)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(before, ba_kit.tree_hash(target))
            doctor_cmd = [sys.executable, "-I", str(ROOT / "tooling/lib/ba_kit.py"), "doctor", "ba", "--agent", "generic", "--target", str(target)]
            doctor_result = subprocess.run(doctor_cmd, cwd=temporary, capture_output=True, text=True, timeout=60)
            self.assertEqual(doctor_result.returncode, 0, doctor_result.stderr)
            self.assertIn("STATUS: READY", doctor_result.stdout)
            report = ba_kit.doctor(ROOT, target)
            self.assertEqual(report["status"], "READY")
            vnext_check = next(check for check in report["checks"] if check[0] == "BA VNext installed capability")
            self.assertTrue(vnext_check[1])
            inventory = package.package_inventory(target, source_root=ROOT, manifest=ba_kit.load_manifest(ROOT))
            self.assertFalse([entry["path"] for entry in inventory if entry["classification"] == "UNDECLARED_FILE"])
            with tempfile.TemporaryDirectory() as output_dir:
                inventory_path = Path(output_dir) / "ba-package.csv"
                package.write_package_inventory(inventory_path, inventory)
                self.assertTrue(inventory_path.is_file())

            runtime = target / "ba-workflow" / "scripts"
            script = r'''import copy, hashlib, json, pathlib, sys
scripts=pathlib.Path(sys.argv[1]).resolve(); root=pathlib.Path(sys.argv[2]).resolve()
sys.path.insert(0,str(scripts))
import ba_vnext as ba, ba_contracts as compat
import shared.sdlc.schema as schema
assert pathlib.Path(ba.__file__).resolve().is_relative_to(scripts)
assert pathlib.Path(compat.__file__).resolve().is_relative_to(scripts)
assert str((scripts/'shared-sdlc-core.zip').resolve()).lower() in str(pathlib.Path(schema.__file__).resolve()).lower()
def ref(name, revision='R1'):
    data=(root/name).read_bytes()
    return {'path':name,'revision':revision,'sha256':hashlib.sha256(data).hexdigest()}
foundation_receipt=json.loads((root/'foundation/.sdlc/receipts/R1.json').read_text(encoding='utf-8'))
foundation_binding={'manifest':ref('foundation/docs/foundation/R1.json'),
    'provenance':ref('foundation/docs/foundation/R1.provenance.json'),
    'approval':ref('foundation/.sdlc/receipts/R1.json'),'root':'foundation'}
foundation_auth=lambda actor,actual: actor=='synthetic-human' and actual==foundation_receipt
decisions=json.loads((root/'decisions.json').read_text(encoding='utf-8'))
sources={role:ref(name) for role,name in [('business_rules','business-rules.md'),('srs','srs.md')]}
decisions['decisions'][0]['implemented_sources']=copy.deepcopy(sources)
decisions['decisions'][0]['input_refs']=[ref('human-answer.txt')]
(root/'decisions.json').write_text(json.dumps(decisions,sort_keys=True),encoding='utf-8')
sources['decisions']=ref('decisions.json')
from shared.sdlc.foundation.impact import knowledge_impact
candidate=ba.make_candidate(root,feature={'id':'FEATURE-1','title':'Collection requests'},baseline_id='BA-1',revision='R1',sources=sources,
    business_identities=[{'id':'BR-001','semantic_key':'eligibility','status':'ACTIVE'},{'id':'FR-001','semantic_key':'submit-request','status':'ACTIVE'}],knowledge=knowledge_impact(),
    project_foundation=foundation_binding,foundation_authenticator=foundation_auth)
assert candidate['business_identities'][0]['id']=='BR-001' and candidate['business_identities'][1]['id']=='FR-001'
assert candidate['coverage_ids']==['BR-001','FR-001']
bad_coverage=copy.deepcopy(candidate); bad_coverage['coverage_ids'].append('BAREF:source-location'); bad_coverage['semantic_sha256']=ba.candidate_hash(bad_coverage)
try:
    ba.validate_candidate(bad_coverage,root,foundation_authenticator=foundation_auth)
except ValueError:
    pass
else:
    raise AssertionError('BAREF locator was accepted as canonical coverage')
bad_how=copy.deepcopy(candidate); bad_how['architecture']='layered'; bad_how['semantic_sha256']=ba.candidate_hash(bad_how)
try:
    ba.validate_candidate(bad_how,root,foundation_authenticator=foundation_auth)
except ValueError:
    pass
else:
    raise AssertionError('BA candidate accepted technical HOW')
next_identity=copy.deepcopy(candidate); next_identity['revision']='R2'; next_identity['business_identities'][0]['id']='BR-009'
try:
    ba.validate_identity_transition(candidate,next_identity)
except ValueError:
    pass
else:
    raise AssertionError('continuing BR identity was changed')
candidate_ref=ba.publish_candidate(root,'candidates/R1.json',candidate)
initial=ba.new_state(candidate['feature'],'GREENFIELD')
state=ba.select_candidate(initial,candidate_ref,root,foundation_authenticator=foundation_auth)
ba.save_state(root,'workflow-state-vnext.json',initial,state,foundation_authenticator=foundation_auth)
state=ba.read_document((root/'workflow-state-vnext.json').read_text(encoding='utf-8'))
ba.validate_state(state,root,foundation_authenticator=foundation_auth)
state=ba.advance(state,'VALIDATE',root,foundation_authenticator=foundation_auth)
assert state['lifecycle']=='VALIDATED'
state=ba.advance(state,'REQUEST_REVIEW',root,foundation_authenticator=foundation_auth)
assert state['lifecycle']=='HUMAN_REVIEW'
try:
    ba.advance(state,'APPROVE',root,foundation_authenticator=foundation_auth)
except ValueError:
    pass
else:
    raise AssertionError('approval succeeded without a host receipt/authenticator')
receipt={'schema_version':1,'artifact_type':'BA_BASELINE','decision':'APPROVE','actor_id':'synthetic-human','actor_role':'HUMAN',
    'recorded_at':'2026-10-04T09:00:00Z','feature_id':candidate['feature']['id'],'baseline_id':candidate['id'],
    'baseline_revision':candidate['revision'],'baseline_semantic_sha256':candidate['semantic_sha256'],
    'baseline_manifest':candidate_ref,'decision_ref':ref('human-approval.txt')}
(root/'receipt.json').write_text(json.dumps(receipt,sort_keys=True),encoding='utf-8')
approval=ref('receipt.json','R1')
auth=lambda actor,actual: actor=='synthetic-human' and actual==receipt
state=ba.advance(state,'APPROVE',root,approval=approval,human_actor_authenticator=auth,foundation_authenticator=foundation_auth)
assert state['lifecycle']=='APPROVED_BASELINE'
handoff=ba.make_handoff(state,root,human_actor_authenticator=auth,foundation_authenticator=foundation_auth)
(root/'engineering-handoff.json').write_text(json.dumps(handoff,sort_keys=True),encoding='utf-8')
reloaded=json.loads((root/'engineering-handoff.json').read_text(encoding='utf-8'))
assert ba.validate_handoff(reloaded,root,human_actor_authenticator=auth,foundation_authenticator=foundation_auth)['human_approval'] is True
legacy=json.loads((scripts.parent/'templates/workflow-state.json').read_text(encoding='utf-8'))
legacy.update(feature={'id':'FEATURE-1','title':'Collection requests'},operation='REVIEW',stage='APPROVED_FOR_ENGINEERING')
legacy_state=compat.read_state(legacy,root)
assert legacy_state['mode']=='LEGACY_COMPAT' and legacy_state['vnext_approval'] is False
sources_v1={}
for name,content in [('rules-v1.md','rules'),('srs-v1.md','srs'),('decisions-v1.md','decisions')]:
    (root/name).write_text(content,encoding='utf-8')
    sources_v1[name]=hashlib.sha256(content.encode()).hexdigest()
legacy_handoff="""schema_version: 1
feature:
  id: FEATURE-1
  title: Collection requests
ba_baseline:
  status: APPROVED_FOR_ENGINEERING
  revision: R1
authoritative_sources:
  business_rules:
    path: rules-v1.md
    sha256: {rules}
  srs:
    path: srs-v1.md
    sha256: {srs}
  decisions:
    path: decisions-v1.md
    sha256: {decisions}
open_items:
  blocking: []
  non_blocking: []
policy:
  downstream_may_change_business_semantics: false
  downstream_may_make_technical_design_decisions: true
next_stage:
  capability: engineering-impact-analysis
""".format(rules=sources_v1['rules-v1.md'],srs=sources_v1['srs-v1.md'],decisions=sources_v1['decisions-v1.md'])
(root/'legacy-handoff.yml').write_text(legacy_handoff,encoding='utf-8')
legacy_result=compat.read_handoff(root/'legacy-handoff.yml')
assert legacy_result['mode']=='LEGACY_COMPAT' and legacy_result['vnext_approval'] is False
print('FRESH_INSTALLED_BA_VNEXT_PASS')
'''
            result = subprocess.run(
                [sys.executable, "-I", "-c", script, str(runtime), str(project)],
                cwd=project,
                capture_output=True,
                text=True,
                timeout=60,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
            )
            self.assertEqual(result.returncode, 0, result.stderr + "\n" + result.stdout)
            self.assertIn("FRESH_INSTALLED_BA_VNEXT_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
