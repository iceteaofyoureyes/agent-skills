"""Foundation mechanics and public synthetic acceptance; receipts are test-only."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from shared.sdlc.foundation import workflow as w
from shared.sdlc.foundation.contract import foundation_readiness, manifest_sha256
from shared.sdlc.foundation.impact import knowledge_impact, refresh_outcome, routes
from shared.sdlc.foundation.inventory import classify, inventory, safe_location
from shared.sdlc.schema import read_document

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'tooling/tests/fixtures'


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='foundation-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        shutil.copytree(FIXTURES/'synthetic-brownfield-foundation', self.root)
        self.mode = 'BROWNFIELD_RECOVERY'

    def greenfield(self):
        shutil.rmtree(self.root)
        shutil.copytree(FIXTURES/'synthetic-greenfield-foundation', self.root)
        self.mode = 'GREENFIELD_BOOTSTRAP'

    def config(self):
        return (read_document((self.root/'.sdlc/topology.json').read_text()),
                read_document((self.root/'.sdlc/project-policy.yml').read_text()))

    def inputs(self, conflicts=False):
        data = read_document((self.root/'analysis.json').read_text())
        if not conflicts: data.pop('authority_claims', None)
        return data

    def start(self, run='run-1', mode=None, **kw):
        return w.start(self.root, run, mode or self.mode,
            w.exact_ref(self.root,'.sdlc/topology.json','R1'),
            w.exact_ref(self.root,'.sdlc/project-policy.yml','R1'), **kw)

    def prepare(self, run='run-1', revision='R1', **kw):
        self.start(run)
        return w.prepare(self.root, run, 'foundation', revision, **(kw or self.inputs()))

    def candidate(self, run='run-1', revision='R1'):
        return read_document((self.root/f'.sdlc/runs/foundation/{run}/candidates/{revision}/manifest.json').read_text())

    def receipt(self, data, *, previous=None, actor='synthetic-human', decision='APPROVE'):
        # Trusted test host injects evidence. Production workflow emits no receipt.
        decision_path = self.root/'docs/decision.txt'
        decision_path.write_text('Synthetic test-only Human decision evidence.\n')
        receipt = {'schema_version':1,'decision':decision,'actor_id':actor,'actor_role':'HUMAN',
                   'artifact_id':data['id'],'artifact_revision':data['revision'],
                   'manifest_sha256':manifest_sha256(data),
                   'decision_ref':w.exact_ref(self.root,'docs/decision.txt',data['revision'])}
        if previous is not None:
            receipt.update(previous_revision=previous['revision'],previous_manifest_sha256=manifest_sha256(previous))
        path = self.root/f'.sdlc/receipts/{data["revision"]}.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(w.semantic_bytes(receipt))
        expected = copy.deepcopy(receipt)
        return w.exact_ref(self.root,path.relative_to(self.root).as_posix(),data['revision']), lambda actor_id, actual: actor_id == 'synthetic-human' and actual == expected

    def accepted(self):
        self.prepare()
        data = self.candidate()
        approval, auth = self.receipt(data)
        w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        return data, approval, auth

    def promoted(self):
        data, approval, auth = self.accepted()
        w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
        return data, approval, auth

    def test_synthetic_brownfield_conflict_is_explicit_and_not_approved(self):
        self.prepare(**self.inputs(conflicts=True))
        review = read_document((self.root/'.sdlc/runs/foundation/run-1/candidates/R1/review-request.json').read_text())
        self.assertEqual(review['conflicts'][0]['kind'],'AUTHORITY_CONFLICT')
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'BLOCKED')
        approval, auth = self.receipt(self.candidate())
        with self.assertRaisesRegex(ValueError,'conflicts'):
            w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        self.assertFalse((self.root/'docs/foundation').exists())

    def test_policy_may_explicitly_share_exact_authority_path_across_domains(self):
        policy_path = self.root/'.sdlc/project-policy.yml'
        policy = read_document(policy_path.read_text())
        shared = 'docs/project-knowledge.md'
        (self.root/shared).write_text('# Shared project knowledge\n',encoding='utf-8')
        policy['authority']['product'] = shared
        policy['authority']['domain'] = shared
        policy_path.write_text(json.dumps(policy),encoding='utf-8')
        self.start(level='STANDARD')
        review = w.prepare(self.root,'run-1','foundation','R1',**self.inputs())
        candidate = self.candidate()
        self.assertEqual(candidate['entry_points']['product']['path'],shared)
        self.assertEqual(candidate['entry_points']['domain']['path'],shared)
        self.assertEqual(review['conflicts'],[])
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'NOT_READY')

    def test_explicit_shared_policy_path_does_not_hide_same_domain_competitors(self):
        policy_path = self.root/'.sdlc/project-policy.yml'
        policy = read_document(policy_path.read_text())
        shared = 'docs/project-knowledge.md'
        (self.root/shared).write_text('# Shared project knowledge\n',encoding='utf-8')
        policy['authority']['product'] = shared
        policy['authority']['domain'] = shared
        policy_path.write_text(json.dumps(policy),encoding='utf-8')
        claims = [{'domain':'product','reference':w.exact_ref(self.root,shared,'R1')},
                  {'domain':'product','reference':w.exact_ref(self.root,'module/product.md','R1')},
                  {'domain':'domain','reference':w.exact_ref(self.root,shared,'R1')}]
        self.start()
        review = w.prepare(self.root,'run-1','foundation','R1',authority_claims=claims,**self.inputs())
        self.assertEqual([item['kind'] for item in review['conflicts']],['AUTHORITY_CONFLICT'])
        self.assertEqual(review['conflicts'][0]['references'][0]['path'],shared)

    def test_synthetic_brownfield_acceptance_preserves_current_inferred_unknown(self):
        data, _, auth = self.promoted()
        self.assertEqual(data['sections']['runtime_view']['evidence'],'CURRENT_SYSTEM')
        self.assertEqual(data['sections']['solution_strategy']['evidence'],'INFERRED')
        self.assertEqual(data['sections']['architecture_decisions']['evidence'],'UNKNOWN')
        durable = read_document((self.root/'docs/foundation/R1.json').read_text())
        self.assertEqual(durable, data)
        self.assertEqual((self.root/'docs/foundation/R1.json').read_bytes(), w.semantic_bytes(data))
        result = w.doctor(self.root,'run-1',human_actor_authenticator=auth)
        self.assertEqual(result['status'],'PROJECT_FOUNDATION_READY')
        self.assertFalse(result['human_approval']); self.assertFalse(result['feature_ready'])
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'BLOCKED')

    def test_synthetic_greenfield_proposal_stops_at_engineering_human_gate(self):
        self.greenfield(); self.prepare()
        data = self.candidate()
        self.assertEqual(data['sections']['solution_strategy']['evidence'],'PROPOSED')
        self.assertEqual(data['sections']['deployment_view']['evidence'],'DEFERRED')
        approval, auth = self.receipt(data)
        with self.assertRaisesRegex(ValueError,'material proposed'):
            w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        self.assertFalse((self.root/'docs/foundation').exists())
        self.assertFalse(list((self.root/'.sdlc/runs/foundation/run-1').rglob('human-receipt.json')))

    def test_synthetic_greenfield_approved_target_requires_exact_trusted_receipt(self):
        self.greenfield(); state = self.start()
        topology, policy = self.config()
        inputs = self.inputs(); inputs['sections']['solution_strategy']['evidence'] = 'APPROVED_TARGET'
        data = w.candidate_manifest(self.root,state,topology,policy,'foundation','R1',**inputs)
        with self.assertRaisesRegex(ValueError,'host-authenticated'):
            w.prepare(self.root,'run-1','foundation','R1',**inputs)
        self.assertFalse((self.root/'.sdlc/runs/foundation/run-1/candidates').exists())
        approval, auth = self.receipt(data)
        w.prepare(self.root,'run-1','foundation','R1',approval=approval,human_actor_authenticator=auth,**inputs)
        w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        state = w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
        self.assertEqual(state['state'],'PROJECT_FOUNDATION_READY')
        self.assertIn('APPROVED_BASELINE',[row['to'] for row in state['history']])

    def test_agent_receipt_and_false_host_authentication_rejected(self):
        self.prepare(); data = self.candidate()
        approval, auth = self.receipt(data,actor='agent')
        with self.assertRaisesRegex(ValueError,'authentication'):
            w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        approval, _ = self.receipt(data)
        with self.assertRaises(ValueError):
            w.accept(self.root,'run-1',approval,human_actor_authenticator=lambda *_: 'true')
        with self.assertRaises(ValueError):
            w.accept(self.root,'run-1',approval,human_actor_authenticator=None)

    def test_answer_continue_validator_pass_and_generation_are_not_approval(self):
        self.prepare(); data = self.candidate()
        self.assertEqual(foundation_readiness(data,self.root)['status'],'PROJECT_FOUNDATION_READY')
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'NOT_READY')
        for decision in ('ANSWER','CONTINUE','PASS'):
            approval, auth = self.receipt(data,decision=decision)
            with self.subTest(decision=decision), self.assertRaises(ValueError):
                w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        with self.assertRaises(ValueError):
            w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=lambda *_: True)

    def test_current_system_target_transition_requires_receipt_binding_prior(self):
        old, _, _ = self.promoted()
        state = self.start('refresh',mode='FOUNDATION_REFRESH')
        inputs = self.inputs(); inputs['sections']['runtime_view']['evidence'] = 'APPROVED_TARGET'
        topology, policy = self.config()
        data = w.candidate_manifest(self.root,state,topology,policy,'foundation','R2',**inputs)
        previous_ref = w.exact_ref(self.root,'docs/foundation/R1.json','R1')
        with self.assertRaises(ValueError):
            w.prepare(self.root,'refresh','foundation','R2',previous_ref=previous_ref,**inputs)
        approval, auth = self.receipt(data)
        with self.assertRaisesRegex(ValueError,'prior'):
            w.prepare(self.root,'refresh','foundation','R2',previous_ref=previous_ref,approval=approval,human_actor_authenticator=auth,**inputs)
        approval, auth = self.receipt(data,previous=old)
        w.prepare(self.root,'refresh','foundation','R2',previous_ref=previous_ref,approval=approval,human_actor_authenticator=auth,**inputs)
        w.accept(self.root,'refresh',approval,human_actor_authenticator=auth)
        w.promote(self.root,'refresh','docs/foundation/R2.json','docs/foundation/R2.provenance.json',human_actor_authenticator=auth)
        self.assertEqual(read_document((self.root/'docs/foundation/R1.json').read_text()),old)

    def test_critical_blocker_blocks_noncritical_unknown_can_remain_ready(self):
        self.prepare(blockers=[{'id':'critical','critical':True,'resolved':False}])
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'BLOCKED')
        self.prepare(run='noncritical',blockers=[{'id':'bounded-gap','critical':False,'resolved':False}])
        data = self.candidate('noncritical'); approval, auth = self.receipt(data)
        w.accept(self.root,'noncritical',approval,human_actor_authenticator=auth)
        w.promote(self.root,'noncritical','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
        self.assertEqual(w.doctor(self.root,'noncritical',human_actor_authenticator=auth)['status'],'PROJECT_FOUNDATION_READY')

    def test_runtime_and_durable_separation_and_policy_declared_promotion(self):
        before = {p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.prepare()
        for name,content in before.items(): self.assertEqual((self.root/name).read_bytes(),content)
        new = {p.relative_to(self.root).as_posix() for p in self.root.rglob('*') if p.is_file()} - before.keys()
        self.assertTrue(new); self.assertTrue(all(name.startswith('.sdlc/runs/foundation/') for name in new))
        approval,auth = self.receipt(self.candidate()); w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        for destination in ('docs/product.md','docs/arbitrary.json','.sdlc/runs/new.json','../outside.json'):
            with self.subTest(destination=destination), self.assertRaises(ValueError):
                w.promote(self.root,'run-1',destination,'docs/foundation/R1.provenance.json',human_actor_authenticator=auth)

    def test_different_existing_snapshot_refused_before_any_write(self):
        _,_,auth = self.accepted()
        target = self.root/'docs/foundation/R1.provenance.json'
        target.parent.mkdir(parents=True); target.write_bytes(b'different approved bytes')
        with self.assertRaises(ValueError):
            w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
        self.assertFalse((self.root/'docs/foundation/R1.json').exists())
        self.assertEqual(target.read_bytes(),b'different approved bytes')

    def test_immutable_replay_and_promotion_recovery_after_state_write_fault(self):
        _,approval,auth = self.accepted()
        state = w.accept(self.root,'run-1',approval,human_actor_authenticator=auth)
        self.assertEqual(state['state'],'ACCEPTED_BASELINE')
        with patch.object(w,'atomic_workflow',side_effect=OSError('state fault')):
            with self.assertRaises(OSError):
                w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
        self.assertEqual(w.doctor(self.root,'run-1',human_actor_authenticator=auth)['status'],'NOT_READY')
        state = w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
        self.assertEqual(w.promote(self.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth),state)

    def test_candidate_source_receipt_policy_and_durable_drift_block(self):
        data, approval,auth = self.promoted()
        paths = ['docs/foundation/R1.json','docs/foundation/R1.provenance.json','docs/architecture.md',approval['path'],
                 '.sdlc/project-policy.yml','.sdlc/runs/foundation/run-1/candidates/R1/manifest.json',
                 '.sdlc/runs/foundation/run-1/candidates/R1/human-receipt.json']
        for relative in paths:
            path = self.root/relative; content = path.read_bytes(); path.write_bytes(b'drift')
            with self.subTest(path=relative): self.assertEqual(w.doctor(self.root,'run-1',human_actor_authenticator=auth)['status'],'BLOCKED')
            path.write_bytes(content)

    def test_exact_approval_hash_revision_identity_rejected_on_drift(self):
        self.prepare(); data = self.candidate()
        approval,auth = self.receipt(data)
        for field,value in [('artifact_revision','R9'),('artifact_id','wrong'),('manifest_sha256','0'*64),('actor_role','AGENT')]:
            receipt = read_document((self.root/approval['path']).read_text()); receipt[field] = value
            (self.root/approval['path']).write_bytes(w.semantic_bytes(receipt))
            altered = w.exact_ref(self.root,approval['path'],'R1')
            with self.subTest(field=field),self.assertRaises(ValueError):
                w.accept(self.root,'run-1',altered,human_actor_authenticator=auth)
            approval,auth = self.receipt(data)

    def test_missing_policy_authority_and_weakened_policy_fail_closed(self):
        path = self.root/'.sdlc/project-policy.yml'; content = path.read_bytes()
        for mutate in (lambda d:d.update(approval='AUTO'),
                       lambda d:d['authority'].update(product='outside/product.md')):
            data = read_document(content.decode()); mutate(data); path.write_bytes(w.semantic_bytes(data))
            with self.assertRaises(ValueError): self.start()
            self.assertFalse((self.root/'.sdlc/runs').exists()); path.write_bytes(content)

    def test_missing_entrypoint_surfaces_gap_without_fabrication(self):
        (self.root/'docs/product.md').unlink()
        self.prepare()
        self.assertIn({'id':'missing-product','critical':True,'resolved':False},self.candidate()['blockers'])
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'BLOCKED')
        review = read_document((self.root/'.sdlc/runs/foundation/run-1/candidates/R1/review-request.json').read_text())
        self.assertIn({'id':'missing-product','critical':True,'resolved':False},review['critical_blockers'])

    def test_confirmed_requires_authenticated_canonical_authority(self):
        self.start(); ref = w.exact_ref(self.root,'docs/architecture.md','R1')
        sections = {'runtime_view':{'status':'PARTIAL','owner':'ENGINEERING','evidence':'CONFIRMED','blocking':False,'references':[ref]}}
        with self.assertRaisesRegex(ValueError,'authenticated'):
            w.prepare(self.root,'run-1','foundation','R1',sections=sections)
        w.prepare(self.root,'run-1','foundation','R1',sections=sections,authority_authenticator=lambda domain,actual: domain=='architecture' and actual==ref)
        self.assertEqual(self.candidate()['sections']['runtime_view']['evidence'],'CONFIRMED')

    def test_context_scope_defaults_to_engineering_preserving_other_owners(self):
        state = self.start()
        data = w.candidate_manifest(self.root, state, *self.config(), 'foundation', 'R1')
        self.assertEqual(data['sections']['context_scope']['owner'], 'ENGINEERING')
        for name, owner in [('introduction_goals', 'BA'), ('glossary', 'BA'), ('quality_requirements', 'TEST')]:
            self.assertEqual(data['sections'][name]['owner'], owner)

    def test_context_scope_rejects_ba_section_owner(self):
        state = self.start()
        row = {'status': 'UNKNOWN', 'owner': 'BA', 'evidence': 'UNKNOWN', 'blocking': False, 'references': []}
        with self.assertRaisesRegex(ValueError, 'ownership'):
            w.candidate_manifest(self.root, state, *self.config(), 'foundation', 'R1', sections={'context_scope': row})

    def test_confirmed_context_scope_requires_exact_architecture_authority(self):
        state = self.start()
        topology, policy = self.config()
        architecture = w.exact_ref(self.root, policy['authority']['architecture'], 'R1')
        domain = w.exact_ref(self.root, policy['authority']['domain'], 'R1')
        row = {'status': 'PARTIAL', 'owner': 'ENGINEERING', 'evidence': 'CONFIRMED',
               'blocking': False, 'references': [architecture]}
        def candidate(auth):
            return w.candidate_manifest(self.root, state, topology, policy, 'foundation', 'R1',
                sections={'context_scope': row}, authority_authenticator=auth)
        with self.assertRaises(ValueError): candidate(None)
        with self.assertRaises(ValueError): candidate(lambda area, ref: area == 'domain' and ref == domain)
        calls = []
        def authenticate(area, ref):
            calls.append((area, ref))
            return area == 'architecture' and ref == architecture
        data = candidate(authenticate)
        self.assertEqual(data['sections']['context_scope']['evidence'], 'CONFIRMED')
        self.assertEqual(calls, [('architecture', architecture)])
        row['references'] = [domain]
        # Even a trusted callback approving every ref cannot substitute domain bytes.
        with self.assertRaises(ValueError): candidate(lambda *_: True)

    def test_refresh_context_scope_changes_route_only_to_architecture(self):
        self.promoted()
        previous = w.exact_ref(self.root, 'docs/foundation/R1.json', 'R1')
        self.start('context-refresh', mode='FOUNDATION_REFRESH')
        row = {'status': 'PARTIAL', 'owner': 'ENGINEERING', 'evidence': 'CURRENT_SYSTEM',
               'blocking': False, 'references': [w.exact_ref(self.root, 'module/config.json', 'R1')]}
        review = w.prepare(self.root, 'context-refresh', 'foundation', 'R2', previous_ref=previous,
                           sections={'context_scope': row})
        self.assertEqual(review['refresh_outcome'], 'FOUNDATION_UPDATE_REQUIRED')
        self.assertTrue(review['knowledge_impact']['areas']['architecture']['affected'])
        self.assertFalse(review['knowledge_impact']['areas']['domain']['affected'])
        self.assertEqual(review['routes'], [{'area': 'architecture', 'owner': 'ENGINEERING', 'targets': []}])

    def test_historical_adr_inference_and_owner_reassignment_rejected(self):
        for name, owner in [('architecture_decisions','ENGINEERING'),('runtime_view','BA')]:
            self.start(name)
            row = {'status':'PARTIAL','owner':owner,'evidence':'INFERRED','blocking':False,
                   'references':[w.exact_ref(self.root,'module/config.json','R1')]}
            with self.assertRaises(ValueError): w.prepare(self.root,name,'foundation','R1',sections={name:row})

    def test_explicit_current_system_contradiction_blocks(self):
        self.prepare(contradictions=[{'domain':'architecture','canonical':w.exact_ref(self.root,'docs/architecture.md','R1'),
                                    'observed':w.exact_ref(self.root,'module/config.json','R1')}])
        self.assertEqual(w.doctor(self.root,'run-1')['status'],'BLOCKED')

    def test_refresh_no_change_and_incremental_owner_routes_never_approve(self):
        self.promoted(); previous = w.exact_ref(self.root,'docs/foundation/R1.json','R1')
        self.start('unchanged',mode='FOUNDATION_REFRESH')
        review = w.prepare(self.root,'unchanged','foundation','R2',previous_ref=previous,**self.inputs())
        self.assertEqual(review['refresh_outcome'],'NO_FOUNDATION_CHANGE')
        self.assertFalse(review['human_approval'])
        self.start('changed',mode='FOUNDATION_REFRESH')
        change = knowledge_impact(); change['areas']['testing'] = {'affected':True,'targets':['docs/testing.md']}
        review = w.prepare(self.root,'changed','foundation','R2',previous_ref=previous,impact=change,**self.inputs())
        self.assertEqual(review['refresh_outcome'],'FOUNDATION_UPDATE_REQUIRED')
        self.assertEqual(review['routes'],[{'area':'testing','owner':'TEST','targets':['docs/testing.md']}])
        self.assertEqual(w.doctor(self.root,'changed')['status'],'NOT_READY')

    def test_refresh_requires_exact_previous_and_does_not_guess_version(self):
        self.start(mode='FOUNDATION_REFRESH')
        with self.assertRaises(ValueError): w.prepare(self.root,'run-1','foundation','R2')
        change = knowledge_impact(); change['schema_version'] = 2
        with self.assertRaises(ValueError): refresh_outcome(change)
        change = knowledge_impact(); change['areas']['product']['affected'] = 'false'
        with self.assertRaises(ValueError): routes(change)

    def test_refresh_partial_input_preserves_unaffected_sections_and_gaps(self):
        self.promoted(); previous = w.exact_ref(self.root,'docs/foundation/R1.json','R1')
        self.start('partial',mode='FOUNDATION_REFRESH')
        review = w.prepare(self.root,'partial','foundation','R2',previous_ref=previous,
                           sections={'glossary':{'status':'UNKNOWN','owner':'BA','evidence':'UNKNOWN','blocking':False,'references':[]}})
        data = self.candidate('partial','R2')
        self.assertEqual(data['sections']['runtime_view'],self.candidate()['sections']['runtime_view'])
        self.assertEqual(review['refresh_outcome'],'NO_FOUNDATION_CHANGE')

    def test_standard_profile_and_review_package_are_deterministic(self):
        for run in ('one','two'):
            self.start(run,level='STANDARD')
            w.prepare(self.root,run,'foundation','R1',**self.inputs())
        first = (self.root/'.sdlc/runs/foundation/one/candidates/R1/review-request.json').read_bytes()
        second = (self.root/'.sdlc/runs/foundation/two/candidates/R1/review-request.json').read_bytes()
        self.assertEqual(first,second)
        self.assertEqual(set(self.candidate('one')['entry_points']),{'product','domain','architecture','testing','features'})

    def test_run_state_schema_versions_fail_closed(self):
        self.start(); path = self.root/'.sdlc/runs/foundation/run-1/run-state.json'
        original = path.read_bytes()
        for version in (True, '1', 2):
            data = read_document(original.decode()); data['schema_version'] = version
            path.write_bytes(w.semantic_bytes(data))
            self.assertEqual(w.doctor(self.root,'run-1')['status'],'BLOCKED')

    def test_malformed_section_inputs_reject_before_candidate_publication(self):
        self.start()
        for sections in ([], {'runtime_view':None}, {'runtime_view':{'evidence':'CURRENT_SYSTEM'}}, {'unknown':{}}):
            with self.subTest(sections=sections), self.assertRaises(ValueError):
                w.prepare(self.root,'run-1','foundation','R1',sections=sections)
        self.assertFalse((self.root/'.sdlc/runs/foundation/run-1/candidates').exists())

    def test_inventory_deterministic_metadata_only_and_declared_roots(self):
        topology,policy = self.config()
        (self.root/'outside.txt').write_text('password=do-not-capture')
        (self.root/'module/.env').write_text('password=do-not-capture')
        result = inventory(self.root,topology,policy)
        self.assertEqual(result,inventory(self.root,topology,policy))
        encoded = json.dumps(result)
        self.assertNotIn('do-not-capture',encoded); self.assertNotIn('outside.txt',encoded)
        self.assertEqual({row['repository_id'] for row in result['artifacts']},{'docs','module'})
        for row in result['artifacts']:
            self.assertEqual(len(row['sha256']),64); self.assertNotIn('content',row)

    def test_inventory_classifies_all_required_categories(self):
        _,policy = self.config()
        paths = ('docs/product.md','docs/domain.md','docs/architecture.md','docs/adr/record.md','docs/testing.md',
                 'module/automation-architecture.md','module/config.json','docs/features.md','module/src/catalog.py',
                 'module/.sdlc/runs/example/log.txt','module/evidence/check.txt','docs/history/old.md','module/unknown.bin')
        categories = {classify(path,policy)[1] for path in paths}
        from shared.sdlc.foundation.inventory import KNOWLEDGE_CLASSES
        self.assertEqual(categories,set(KNOWLEDGE_CLASSES))

    def test_traversal_and_outside_references_rejected(self):
        for relative in ('../outside','docs/../../outside','C:/outside','docs/CON'):
            with self.subTest(path=relative),self.assertRaises(ValueError): safe_location(self.root,relative)
        self.start()
        (self.root/'outside.txt').write_text('evidence')
        row = self.inputs()['sections']['runtime_view']; row['references'] = [w.exact_ref(self.root,'outside.txt','R1')]
        with self.assertRaises(ValueError): w.prepare(self.root,'run-1','foundation','R1',sections={'runtime_view':row})

    def test_symlink_escape_rejected_where_supported(self):
        outside = Path(self.temp.name)/'outside'; outside.mkdir(); (outside/'file').write_text('outside')
        try: (self.root/'module/escape').symlink_to(outside,target_is_directory=True)
        except OSError as error: self.skipTest('symlink privilege unavailable: '+str(error))
        with self.assertRaises(ValueError): inventory(self.root,*self.config())
        with self.assertRaises(ValueError): safe_location(self.root,'module/escape/new.json')

    def test_windows_reparse_escape_guard_without_symlink_privilege(self):
        original = Path.lstat
        def reparse(path, *args, **kwargs):
            result = original(path,*args,**kwargs)
            if path == self.root/'module':
                class Info:
                    st_mode = result.st_mode
                    st_file_attributes = 0x400
                return Info()
            return result
        with patch.object(Path,'lstat',reparse),self.assertRaisesRegex(ValueError,'reparse'):
            inventory(self.root,*self.config())

    def test_raw_prompt_or_runtime_cannot_enter_semantic_manifest(self):
        (self.root/'module/prompts').mkdir(); (self.root/'module/prompts/raw.txt').write_text('raw')
        for relative in ('module/prompts/raw.txt','module/.sdlc/runs/example/log.txt'):
            run = 'raw-' + str(len(relative)); self.start(run)
            row = self.inputs()['sections']['runtime_view']; row['references'] = [w.exact_ref(self.root,relative,'R1')]
            with self.assertRaises(ValueError): w.prepare(self.root,run,'foundation','R1',sections={'runtime_view':row})

    def test_final_tree_has_no_bootstrap_spec_or_domain_leaks(self):
        self.assertFalse((ROOT/'PHASE_3_WAVE_1_PROJECT_FOUNDATION_WORKFLOW_SPEC.md').exists())
        forbidden = ('digital wedding','digital-wedding','petclinic','appointment','cr-dwc-','fr-dash-', 'c:/users/')
        for directory in (ROOT/'project-foundation',ROOT/'shared/sdlc/foundation'):
            for path in directory.rglob('*'):
                if path.suffix in ('.py','.md'):
                    text = path.read_text(encoding='utf-8').lower()
                    for word in forbidden: self.assertNotIn(word,text,str(path))


class InstalledFoundationTests(unittest.TestCase):
    def test_profile_and_dev_install_use_only_installed_payload_for_both_modes(self):
        from tooling.prepare_agent_profile import prepare
        from tooling.install_dev_kit import install
        with tempfile.TemporaryDirectory(prefix='foundation-installed-') as temp:
            base = Path(temp)
            prepare(ROOT,base/'profile',foundation=True)
            runtime = Path(install(ROOT,base/'dev')['runtime_root'])
            for home,skill,core in ((base/'profile',base/'profile/skills/project-foundation',None),
                                   (runtime,runtime/'project-foundation',runtime/'shared')):
                payload = skill/'scripts/shared-sdlc-core.zip'
                self.assertTrue(payload.is_file())
                with zipfile.ZipFile(payload) as archive:
                    for name in archive.namelist(): self.assertEqual(archive.read(name),(ROOT/name).read_bytes())
                for kind in ('greenfield','brownfield'):
                    project = base/(home.name+'-'+kind)
                    shutil.copytree(FIXTURES/('synthetic-'+kind+'-foundation'),project)
                    result = subprocess.run([sys.executable,'-I',str(skill/'scripts/project_foundation.py'),kind,
                        '--project-root',str(project),'--input','analysis.json'],cwd=base,capture_output=True,text=True,timeout=60)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertFalse(json.loads(result.stdout)['human_approval'])
                    self.assertFalse((project/'docs/foundation').exists())
                code = '''import pathlib,sys
sys.path.insert(0,sys.argv[1])
from shared.sdlc.foundation import workflow
assert pathlib.Path(workflow.__file__).as_posix().startswith(sys.argv[1].replace('\\\\','/')),workflow.__file__
assert not any('tooling.lib.test_kit' in name for name in sys.modules)
print(workflow.__file__)
'''
                source = str(runtime) if core else str(payload)
                code += '''
import json
from shared.sdlc.foundation.contract import manifest_sha256
for name in sys.argv[2:]:
    root=pathlib.Path(name)
    inputs=json.loads((root/'analysis.json').read_text())
    inputs.pop('authority_claims',None)  # Explicit synthetic host resolution of duplicate claim.
    green='greenfield' in root.name
    mode='GREENFIELD_BOOTSTRAP' if green else 'BROWNFIELD_RECOVERY'
    if green: inputs['sections']['solution_strategy']['evidence']='APPROVED_TARGET'
    topology=json.loads((root/'.sdlc/topology.json').read_text())
    policy=json.loads((root/'.sdlc/project-policy.yml').read_text())
    state=workflow.start(root,'host-run',mode,workflow.exact_ref(root,'.sdlc/topology.json','R1'),workflow.exact_ref(root,'.sdlc/project-policy.yml','R1'))
    data=workflow.candidate_manifest(root,state,topology,policy,'foundation','R1',**inputs)
    decision=root/'docs/decision.txt'; decision.write_text('Synthetic trusted-host fixture only.')
    receipt={'schema_version':1,'decision':'APPROVE','actor_id':'synthetic-human','actor_role':'HUMAN','artifact_id':'foundation','artifact_revision':'R1','manifest_sha256':manifest_sha256(data),'decision_ref':workflow.exact_ref(root,'docs/decision.txt','R1')}
    path=root/'.sdlc/receipt.json'; path.write_bytes(workflow.semantic_bytes(receipt))
    approval=workflow.exact_ref(root,'.sdlc/receipt.json','R1')
    auth=lambda actor,actual:actor=='synthetic-human' and actual==receipt
    workflow.prepare(root,'host-run','foundation','R1',approval=approval if green else None,human_actor_authenticator=auth,**inputs)
    assert workflow.doctor(root,'host-run')['status']=='NOT_READY'
    workflow.accept(root,'host-run',approval,human_actor_authenticator=auth)
    workflow.promote(root,'host-run','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
    assert workflow.doctor(root,'host-run',human_actor_authenticator=auth)['status']=='PROJECT_FOUNDATION_READY'
    assert (root/'docs/foundation/R1.json').read_bytes()==workflow.semantic_bytes(data)
    assert workflow.doctor(root,'host-run')['status']=='BLOCKED'
'''
                result = subprocess.run([sys.executable,'-I','-c',code,source,str(base/(home.name+'-greenfield')),str(base/(home.name+'-brownfield'))],cwd=base,capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_missing_payload_does_not_fall_back_to_checkout(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp)/'skills/project-foundation/scripts/project_foundation.py'
            script.parent.mkdir(parents=True); shutil.copyfile(ROOT/'project-foundation/scripts/project_foundation.py',script)
            result = subprocess.run([sys.executable,'-I',str(script),'--help'],cwd=ROOT,capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0); self.assertIn('payload is missing',result.stderr)


if __name__ == '__main__':
    unittest.main()
