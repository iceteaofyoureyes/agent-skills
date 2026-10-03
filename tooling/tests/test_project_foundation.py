"""Foundation mechanics and public synthetic acceptance; receipts are test-only."""
import copy
from contextlib import redirect_stderr, redirect_stdout
import io
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


class IntegratedProducerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='foundation-integrated-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        shutil.copytree(FIXTURES/'synthetic-brownfield-foundation', self.root)
        self.topology, self.policy = self.config()
        self.run = w.start(self.root, 'integrated', 'BROWNFIELD_RECOVERY',
            w.exact_ref(self.root, '.sdlc/topology.json', 'R1'),
            w.exact_ref(self.root, '.sdlc/project-policy.yml', 'R1'))

    def config(self):
        from shared.sdlc.schema import read_document
        return (read_document((self.root/'.sdlc/topology.json').read_text()),
                read_document((self.root/'.sdlc/project-policy.yml').read_text()))

    def observation(self, topic, ident=None, path='module/config.json', statement='Observed configuration.'):
        return {'id': ident or topic.replace('_', '-'), 'topic': topic, 'statement': statement,
                'basis': 'OBSERVED', 'references': [w.exact_ref(self.root, path, 'R1')],
                'status': 'PARTIAL', 'questions': []}

    def test_semantic_producers_are_immutable_run_inputs_and_review_refs(self):
        ref = w.produce_semantic(self.root, 'integrated', 'architecture-discovery', 'architecture', 'R1',
            observations=[self.observation('context_scope', path='docs/architecture.md')])
        review = w.prepare(self.root, 'integrated', 'foundation', 'R1')
        self.assertEqual(review['semantic_artifacts'][0]['owner'], 'ENGINEERING')
        self.assertEqual(review['semantic_artifacts'][0]['producer_type'], 'architecture-discovery')
        self.assertEqual(review['semantic_artifacts'][0]['reference'], ref)
        self.assertIn('unknown-runtime', review['semantic_artifacts'][0]['unknowns'])
        self.assertTrue((self.root/ref['path']).is_file())
        self.assertIn({'area':'architecture','owner':'ENGINEERING','targets':[]}, review['routes'])

    def test_integrated_artifact_bytes_and_configuration_drift_fail_closed(self):
        ref = w.produce_semantic(self.root, 'integrated', 'domain-discovery', 'domain', 'R1',
            observations=[self.observation('entities', path='docs/domain.md')])
        (self.root/ref['path']).write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            w.prepare(self.root, 'integrated', 'foundation', 'R1')

    def test_existing_analysis_run_without_semantic_artifacts_remains_readable(self):
        path=self.root/'.sdlc/runs/foundation/integrated/run-state.json'
        state=json.loads(path.read_text()); state.pop('semantic_artifacts')
        path.write_bytes(w.semantic_bytes(state))
        self.assertNotIn('semantic_artifacts',w._load(self.root,'integrated')[0])
        review=w.prepare(self.root,'integrated','foundation','R1')
        self.assertEqual(review['semantic_artifacts'],[])

    def test_cross_producer_conflict_is_bound_and_blocks_human_acceptance(self):
        domain_ref = w.produce_semantic(self.root, 'integrated', 'domain-discovery', 'domain', 'R1',
            observations=[self.observation('entities', path='docs/domain.md', statement='A catalog is a business collection.')])
        architecture_ref = w.produce_semantic(self.root, 'integrated', 'architecture-discovery', 'architecture', 'R1',
            observations=[self.observation('context_scope', path='docs/architecture.md', statement='A catalog is a runtime service.')])
        review_ref = w.detect_semantic_conflicts(self.root, 'integrated',
            ['domain-discovery-domain-R1', 'architecture-discovery-architecture-R1'],
            [{'domain':'domain','claims':[
                {'producer':'domain-discovery','record_id':'entities'},
                {'producer':'architecture-discovery','record_id':'context-scope'}]}])
        review = w.prepare(self.root, 'integrated', 'foundation', 'R1')
        conflicts = json.loads((self.root/review_ref['path']).read_text())['conflicts']
        self.assertEqual(conflicts[0]['status'], 'UNRESOLVED')
        self.assertEqual(review['conflicts'], conflicts)
        self.assertEqual(len(review['semantic_artifacts']), 3)
        with self.assertRaisesRegex(ValueError, 'unresolved authority conflicts'):
            w.accept(self.root, 'integrated', None, human_actor_authenticator=lambda *_: True)
        self.assertEqual(w._load(self.root, 'integrated')[0]['state'], 'REVIEW_REQUIRED')

    def test_greenfield_producers_stay_proposed_until_exact_human_snapshot_review(self):
        root = self.root.parent/'greenfield'
        shutil.copytree(FIXTURES/'synthetic-greenfield-foundation', root)
        topology, policy = read_document((root/'.sdlc/topology.json').read_text()), read_document((root/'.sdlc/project-policy.yml').read_text())
        w.start(root,'green-run','GREENFIELD_BOOTSTRAP',w.exact_ref(root,'.sdlc/topology.json','R1'),
                w.exact_ref(root,'.sdlc/project-policy.yml','R1'))
        def proposed(ident,topic,statement='Synthetic target proposal.'):
            return {'id':ident,'topic':topic,'statement':statement,'basis':'PROPOSED','references':[],
                    'status':'PARTIAL','questions':[]}
        def produce(producer,ident,observations=(),**kw):
            return w.produce_semantic(root,'green-run',producer,ident,'R1',observations=observations,**kw)
        domain=produce('domain-discovery','domain',[proposed('goals','product_goals')])
        architecture=produce('architecture-discovery','architecture',[proposed('strategy','solution_strategy')])
        testing=produce('test-foundation','testing',[proposed('gates','quality_gates')])
        adr=produce('adr-management','adr',[proposed('decision','decision')],kind='PROPOSED')
        elements=[{'record':proposed('actor','c4_element'),'kind':'ACTOR'},
                  {'record':proposed('system','c4_element'),'kind':'SYSTEM'},
                  {'record':proposed('container','c4_element'),'kind':'CONTAINER','parent':'system'}]
        relationships=[{'record':proposed('uses','c4_relationship'),'source':'actor','target':'system','level':'CONTEXT'},
                       {'record':proposed('calls','c4_relationship'),'source':'actor','target':'container','level':'CONTAINER'}]
        c4=produce('c4-modeling','c4',elements=elements,relationships=relationships)
        keys=['domain-discovery-domain-R1','architecture-discovery-architecture-R1','test-foundation-testing-R1',
              'adr-management-adr-R1','c4-modeling-c4-R1']
        arc=w.project_arc42(root,'green-run',keys)
        self.assertEqual(json.loads((root/adr['path']).read_text())['decision_status'],'PROPOSED')
        self.assertEqual(json.loads((root/c4['path']).read_text())['artifact_class'],'RUNTIME')
        self.assertEqual(json.loads((root/arc['path']).read_text())['artifact_class'],'DERIVED')
        target=root/'docs/architecture.md'
        section={'solution_strategy':{'owner':'ENGINEERING','status':'COMPLETE','blocking':True,
            'evidence':'APPROVED_TARGET','references':[w.exact_ref(root,'docs/architecture.md','R1')]}}
        state,topology,policy=w._load(root,'green-run')
        manifest=w.candidate_manifest(root,state,topology,policy,'foundation','R1',sections=section)
        (root/'docs/decision.txt').write_text('Synthetic Human selection of exact target snapshot.')
        receipt={'schema_version':1,'decision':'APPROVE','actor_id':'synthetic-human','actor_role':'HUMAN',
            'artifact_id':'foundation','artifact_revision':'R1','manifest_sha256':manifest_sha256(manifest),
            'decision_ref':w.exact_ref(root,'docs/decision.txt','R1')}
        (root/'.sdlc/receipt.json').write_bytes(w.semantic_bytes(receipt))
        approval=w.exact_ref(root,'.sdlc/receipt.json','R1')
        auth=lambda actor,actual:actor=='synthetic-human' and actual==receipt
        with self.assertRaises(ValueError): w.prepare(root,'green-run','foundation','R1',sections=section)
        review=w.prepare(root,'green-run','foundation','R1',sections=section,approval=approval,
                         human_actor_authenticator=auth)
        architecture_review=next(row for row in review['semantic_artifacts'] if row['producer_type']=='architecture-discovery')
        self.assertIn('strategy',architecture_review['proposed_targets'])
        self.assertIn('ENGINEERING_REVIEW:architecture:strategy',review['required_owner_decisions'])
        w.accept(root,'green-run',approval,human_actor_authenticator=auth)
        state=w.promote(root,'green-run','docs/foundation/R1.json','docs/foundation/R1.provenance.json',
                        human_actor_authenticator=auth)
        self.assertEqual(state['state'],'PROJECT_FOUNDATION_READY')
        self.assertEqual(json.loads((root/'docs/foundation/R1.json').read_text())['sections']['solution_strategy']['evidence'],
                         'APPROVED_TARGET')
        self.assertEqual(json.loads((root/'docs/foundation/R1.json').read_text())['sections']['solution_strategy']['references'][0],
                         w.exact_ref(root,'docs/architecture.md','R1'))
        self.assertTrue((root/arc['path']).is_file())

    def test_semantic_drift_guard_keeps_wave_2_ownership_and_labels(self):
        from shared.sdlc.foundation import producers
        self.assertEqual(w.SECTION_DOMAINS['context_scope'], 'architecture')
        self.assertEqual(w.SECTION_DOMAINS['introduction_goals'], 'product')
        self.assertEqual(w.SECTION_DOMAINS['glossary'], 'domain')
        self.assertEqual(w.SECTION_DOMAINS['quality_requirements'], 'testing')
        self.assertEqual(w.SEMANTIC_OWNERS, {'product':'BA','domain':'BA','architecture':'ENGINEERING','testing':'TEST','features':'BA'})
        self.assertEqual(producers.PRODUCERS, {
            'domain-discovery':('BA',('product_goals','glossary','actors','entities','lifecycle','business_rule','gaps')),
            'architecture-discovery':('ENGINEERING',('constraints','context_scope','solution_strategy','architecture_pattern',
                'building_blocks','runtime','deployment','crosscutting','quality_facts','risks','decisions_inventory',
                'historical_rationale','gaps')),
            'test-foundation':('TEST',('test_levels','ownership','test_split','execution_topology','fixtures_data',
                'quality_gates','evidence_expectations','automation_role','gaps')),
            'adr-management':('ENGINEERING',('context','decision','rationale','consequences','alternative','gaps')),
            'c4-modeling':('ENGINEERING',('c4_element','c4_relationship'))})
        self.assertEqual(producers.LABELS, {'OBSERVED':'CURRENT_SYSTEM','INFERRED':'INFERRED','AUTHORITY':'CONFIRMED',
            'DECISION_EVIDENCE':'CURRENT_SYSTEM','PROPOSED':'PROPOSED','UNKNOWN':'UNKNOWN','DEFERRED':'DEFERRED',
            'APPROVED_TARGET':'APPROVED_TARGET'})
        self.assertEqual(w.MODES, ('BROWNFIELD_RECOVERY','GREENFIELD_BOOTSTRAP','FOUNDATION_REFRESH'))

    def test_operator_cli_exposes_integrated_producers_without_approval_flag(self):
        from shared.sdlc.foundation.cli import main
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(SystemExit) as help_exit:
            main(['--help'])
        self.assertEqual(help_exit.exception.code, 0)
        for command in ('domain-discovery','architecture-discovery','test-foundation','adr-management',
                        'c4-modeling','render-c4','arc42-projection','conflicts','prepare','doctor'):
            self.assertIn(command, output.getvalue())
        self.assertNotIn('--approve', output.getvalue())
        errors = io.StringIO()
        with redirect_stderr(errors), self.assertRaises(SystemExit) as invalid:
            main(['brownfield','--project-root',str(self.root),'--approve'])
        self.assertEqual(invalid.exception.code, 2)


class InstalledFoundationTests(unittest.TestCase):
    def test_installed_runtime_integrates_all_producers_without_checkout_imports(self):
        from tooling.prepare_agent_profile import prepare
        from tooling.install_dev_kit import install
        with tempfile.TemporaryDirectory(prefix='foundation-isolated-') as temp:
            base = Path(temp)
            prepare(ROOT, base/'profile', foundation=True)
            runtime = Path(install(ROOT, base/'dev')['runtime_root'])
            project = base/'project'
            shutil.copytree(FIXTURES/'synthetic-brownfield-foundation', project)
            code = r'''import json,pathlib,sys
sys.path.insert(0,sys.argv[1])
from shared.sdlc.foundation import workflow
from shared.sdlc.foundation.inventory import inventory
from shared.sdlc.schema import read_document
root=pathlib.Path(sys.argv[2])
topology=read_document((root/'.sdlc/topology.json').read_text())
policy=read_document((root/'.sdlc/project-policy.yml').read_text())
state=workflow.start(root,'installed-run','BROWNFIELD_RECOVERY',
 workflow.exact_ref(root,'.sdlc/topology.json','R1'),workflow.exact_ref(root,'.sdlc/project-policy.yml','R1'))
assert inventory(root,topology,policy)['schema_version']==1
def observation(ident,topic,path):
 return {'id':ident,'topic':topic,'statement':'Synthetic observed evidence.','basis':'OBSERVED',
  'references':[workflow.exact_ref(root,path,'R1')],'status':'PARTIAL','questions':[]}
def produce(producer,ident,observations=(),**kw):
 return workflow.produce_semantic(root,'installed-run',producer,ident,'R1',observations=observations,**kw)
business=observation('business-rule','business_rule','module/src/catalog.py')
domain=produce('domain-discovery','domain',[observation('actor','actors','docs/domain.md'),
 observation('entity','entities','docs/domain.md'),business])
inferred=observation('pattern','architecture_pattern','docs/architecture.md')
inferred.update(basis='INFERRED',statement='The observed components may follow a layered pattern.')
architecture=produce('architecture-discovery','architecture',[
 observation('scope','context_scope','docs/architecture.md'),inferred])
testing=produce('test-foundation','testing',[observation('levels','test_levels','docs/testing.md')])
adr=produce('adr-management','adr',[observation('decision','decision','docs/adr/record.md')],kind='RECOVERED')
elements=[{'record':observation('user','c4_element','docs/architecture.md'),'kind':'ACTOR'},
 {'record':observation('system','c4_element','docs/architecture.md'),'kind':'SYSTEM'},
 {'record':observation('container','c4_element','docs/architecture.md'),'kind':'CONTAINER','parent':'system'}]
edges=[{'record':observation('uses','c4_relationship','docs/architecture.md'),'source':'user','target':'system','level':'CONTEXT'},
 {'record':observation('calls','c4_relationship','docs/architecture.md'),'source':'user','target':'container','level':'CONTAINER'}]
c4=produce('c4-modeling','c4',elements=elements,relationships=edges)
keys=['domain-discovery-domain-R1','architecture-discovery-architecture-R1','test-foundation-testing-R1','adr-management-adr-R1','c4-modeling-c4-R1']
c4view=workflow.render_c4_candidate(root,'installed-run',keys[-1])
arc=workflow.project_arc42(root,'installed-run',keys)
domain_data=json.loads((root/domain['path']).read_text())
architecture_data=json.loads((root/architecture['path']).read_text())
testing_data=json.loads((root/testing['path']).read_text())
adr_data=json.loads((root/adr['path']).read_text())
assert domain_data['records'][0]['owner']=='BA'
assert next(row for row in domain_data['records'] if row['topic']=='business_rule')['evidence_label']=='CURRENT_SYSTEM'
assert not any(row['id'].upper().startswith(('BR-','FR-','BAREF')) for row in domain_data['records'])
assert architecture_data['records'][0]['owner']=='ENGINEERING'
assert next(row for row in architecture_data['records'] if row['topic']=='architecture_pattern')['evidence_label']=='INFERRED'
assert testing_data['source_producer']=='test-foundation'
assert not any(row['topic'] in ('test_design','testcase') for row in testing_data['records'])
assert next(row for row in adr_data['records'] if row['topic']=='rationale')['evidence_label']=='UNKNOWN'
assert json.loads((root/c4['path']).read_text())['artifact_class']=='RUNTIME'
assert json.loads((root/c4view['path']).read_text())['artifact_class']=='DERIVED'
assert json.loads((root/arc['path']).read_text())['artifact_class']=='DERIVED'
scope=next(row for row in architecture_data['records'] if row['topic']=='context_scope')
review=workflow.prepare(root,'installed-run','foundation','R1',sections={
 'context_scope':{
 'owner':'ENGINEERING','status':scope['status'],'blocking':False,'evidence':scope['evidence_label'],
 'references':scope['references']},
 'quality_requirements':{'owner':'TEST','status':'PARTIAL','blocking':False,'evidence':'CURRENT_SYSTEM',
 'references':[workflow.exact_ref(root,'docs/testing.md','R1')]}})
assert len(review['semantic_artifacts'])==7
assert workflow.doctor(root,'installed-run')['status']=='NOT_READY'
from shared.sdlc.foundation.contract import manifest_sha256
manifest=json.loads((root/'.sdlc/runs/foundation/installed-run/candidates/R1/manifest.json').read_text())
assert manifest['sections']['context_scope']['owner']=='ENGINEERING'
assert manifest['sections']['context_scope']['evidence']=='CURRENT_SYSTEM'
assert manifest['sections']['quality_requirements']['owner']=='TEST'
assert not any(row['evidence']=='APPROVED_TARGET' for row in manifest['sections'].values())
(root/'docs/decision.txt').write_text('Synthetic trusted-host review decision.')
receipt={'schema_version':1,'decision':'APPROVE','actor_id':'synthetic-human','actor_role':'HUMAN',
 'artifact_id':'foundation','artifact_revision':'R1','manifest_sha256':manifest_sha256(manifest),
 'decision_ref':workflow.exact_ref(root,'docs/decision.txt','R1')}
(root/'.sdlc/receipt.json').write_bytes(workflow.semantic_bytes(receipt))
approval=workflow.exact_ref(root,'.sdlc/receipt.json','R1')
auth=lambda actor,actual:actor=='synthetic-human' and actual==receipt
workflow.accept(root,'installed-run',approval,human_actor_authenticator=auth)
workflow.promote(root,'installed-run','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
assert workflow.doctor(root,'installed-run',human_actor_authenticator=auth)['status']=='PROJECT_FOUNDATION_READY'
assert (root/'docs/foundation/R1.json').is_file()
assert not (root/'docs/foundation/semantic').exists()
print('INSTALLED_FOUNDATION_ACCEPTED')
'''
            for source in (base/'profile/skills/project-foundation/scripts/shared-sdlc-core.zip', runtime):
                result = subprocess.run([sys.executable,'-I','-c',code,str(source),str(project)], cwd=base,
                    env={k:v for k,v in __import__('os').environ.items() if k != 'PYTHONPATH'},
                    capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('INSTALLED_FOUNDATION_ACCEPTED',result.stdout)
                shutil.rmtree(project/'.sdlc/runs/foundation/installed-run')

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
