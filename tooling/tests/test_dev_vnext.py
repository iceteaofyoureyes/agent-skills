"""Wave 1 semantic acceptance; authenticators are synthetic trusted hosts only."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tooling.tests import test_ba_vnext as ba_tests
from tooling.lib import dev_vnext as dev

ROOT = Path(__file__).resolve().parents[2]
STAMP = '2026-10-04T10:00:00Z'


class DevVNextTests(unittest.TestCase):
    def setUp(self):
        self.ba = ba_tests.BAVNextTests('test_greenfield_exact_baseline_and_handoff')
        self.ba.setUp()
        self.addCleanup(self.ba.doCleanups)
        self.root = self.ba.root
        state, self.ba_auth = self.ba.approved()
        self.handoff = ba_tests.ba.make_handoff(state, self.root, human_actor_authenticator=self.ba_auth)
        self.ba.put('handoff.json', self.handoff)
        self.upstream = self.ba.ref('handoff.json')
        self.repos = [{'id':'core','role':'IMPLEMENTATION','base_revision':'a'*40,
                       'allowed_write_paths':['src','tests'], 'read_only_evidence_paths':['docs']}]
        self.checks = [{'name':'unit','repository_id':'core','category':'UNIT','command':['python','-m','unittest']}]
        self.context = {'ba_authenticator':self.ba_auth}
        self.produced = {'core':'b'*40}
        self.ba.put('code.json', {'example':'synthetic implementation'})
        self.ba.put('test.json', {'example':'synthetic unit evidence'})
        self.ba.put('review.json', {'example':'consolidated review evidence'})

    def start(self, repos=None, maintenance=False, checks=None):
        return dev.new_state(run_id='RUN-1', change_id='CHANGE-1', summary='Collection request implementation',
            authority_mode='TECHNICAL_MAINTENANCE' if maintenance else 'FEATURE_DELIVERY',
            repositories=repos or self.repos, checks=self.checks if checks is None else checks,
            upstream=None if maintenance else self.upstream,
            maintenance={'kind':'MECHANICAL','evidence_refs':[self.ba.ref('review.json')],
                         'no_what_change':True,'discovered_changes':[]} if maintenance else None)

    def test_checks_require_an_implementation_repository_and_canonicalize_single_repo(self):
        unscoped = [{'name':'unit','category':'UNIT','command':['python','-m','unittest']}]
        self.assertEqual(self.start(checks=unscoped)['checks'][0]['repository_id'], 'core')

        with self.assertRaises(ValueError):
            self.start(checks=[dict(unscoped[0], repository_id='unknown')])

        read_only = self.repos + [{'id':'docs','role':'READ_ONLY','base_revision':'c'*40,
            'allowed_write_paths':[],'read_only_evidence_paths':['docs']}]
        with self.assertRaises(ValueError):
            self.start(repos=read_only, checks=[dict(unscoped[0], repository_id='docs')])

        multiple = self.repos + [{'id':'client','role':'IMPLEMENTATION','base_revision':'c'*40,
            'allowed_write_paths':['client'],'read_only_evidence_paths':[]}]
        with self.assertRaises(ValueError):
            self.start(repos=multiple, checks=unscoped)

    def test_snapshot_binds_the_exact_check_repository(self):
        repositories = self.repos + [{'id':'client','role':'IMPLEMENTATION','base_revision':'c'*40,
            'allowed_write_paths':['client'],'read_only_evidence_paths':[]}]
        checks = [dict(self.checks[0]), {'name':'client-unit','repository_id':'client',
            'category':'UNIT','command':['python','-m','unittest']}]
        state = self.planned(repos=repositories, checks=checks)
        snapshot = dev._data(state['artifacts']['snapshot'], self.root)
        snapshot['checks'][0]['repository_id'] = 'client'
        self.ba.put('snapshot-check-rebind.json', snapshot)
        rebound = self.ba.ref('snapshot-check-rebind.json', state['artifacts']['snapshot']['revision'])
        with self.assertRaises(ValueError):
            dev.validate_snapshot(rebound, self.root, state, **self.context)

    def impact(self, state, risk='NORMAL', categories=None):
        return {'schema_version':2,'change_id':state['change_id'], 'upstream_ref':state['upstream'],
            'repository_base_revisions':{r['id']:r['base_revision'] for r in state['repositories']},
            'affected_repositories':copy.deepcopy(state['repositories']),
            'affected_components':['request module'],'affected_interfaces':[], 'affected_data':[],
            'dependencies':[], 'constraints':[], 'risk':{'level':risk,'categories':categories or [],'reasons':[]},
            'technical_unknowns':[], 'upstream_gaps':[],
            'write_scope':{r['id']:r['allowed_write_paths'] for r in state['repositories']},
            'knowledge_impact':copy.deepcopy(self.handoff['knowledge_impact'])}

    def decision(self, category='PUBLIC_API', status='PROPOSED'):
        return {'schema_version':2,'id':'ED-001','change_id':'CHANGE-1','topic':'Response compatibility',
            'authority_scope':'FEATURE_LOCAL',
            'category':category,'decision':'Preserve existing response shape','status':status,
            'evidence_refs':[self.ba.ref('review.json')],'upstream_refs':[self.upstream],
            'affected_repositories':['core'],'affected_components':['request module'],
            'affected_interfaces':['response'],'affected_data':[], 'alternatives':['new version'],
            'consequences':['compatibility retained'],'risk':'HIGH_RISK','materiality':'MATERIAL',
            'approval_requirement':'HUMAN','supersedes':[],'superseded_by':[]}

    def planned(self, high=False, repos=None, checks=None):
        state = dev.advance(self.start(repos, checks=checks), 'AUTHORITY_VALIDATED', self.root, **self.context)
        data = self.impact(state, 'HIGH_RISK' if high or repos else 'NORMAL',
                           ['PUBLIC_API'] if high else (['CROSS_REPOSITORY'] if repos else []))
        self.ba.put('impact.json', data)
        state = dev.analyze_impact(state, self.ba.ref('impact.json'), self.root, **self.context)
        decisions = []
        if high:
            self.ba.put('ed.json', self.decision())
            decisions = [self.ba.ref('ed.json')]
        for name in ('dev-plan.md','dev-tasks.md'):
            (self.root/name).write_text('Technical runtime planning; exact bindings live in snapshot.', encoding='utf-8')
        snapshot = dev.make_snapshot(state, self.root, revision='TECH-1', decisions=decisions,
            plan=self.ba.ref('dev-plan.md'), tasks=self.ba.ref('dev-tasks.md'), **self.context)
        self.ba.put('snapshot.json', snapshot)
        return dev.plan(state, self.ba.ref('snapshot.json','TECH-1'), self.root, **self.context)

    def technical_receipt(self, state):
        receipt = {'schema_version':2,'artifact_type':'DEV_TECHNICAL_APPROVAL','decision':'APPROVE',
            'actor_id':'technical-human','actor_role':'TECH_LEAD','recorded_at':STAMP,
            'run_id':state['run_id'],'change_id':state['change_id'],
            'snapshot_revision':'TECH-1','snapshot_sha256':state['artifacts']['snapshot']['sha256'],
            'snapshot_ref':state['artifacts']['snapshot'],'decision_evidence_ref':self.ba.ref('review.json')}
        self.ba.put('technical-receipt.json',receipt)
        expected = copy.deepcopy(receipt)
        return self.ba.ref('technical-receipt.json','TECH-1'), lambda actor,row: actor == 'technical-human' and row == expected

    def ready(self, state=None, high=False):
        state = state or self.planned(high)
        if state['risk']['level'] == 'HIGH_RISK':
            receipt, auth = self.technical_receipt(state)
            self.context['technical_authenticator'] = auth
            state = dev.bind_technical_approval(state,receipt,self.root,**self.context)
        return dev.advance(state,'IMPLEMENTATION_READY',self.root,
            current_base_revisions={r['id']:r['base_revision'] for r in state['repositories']}, **self.context)

    def verification(self, state, revisions):
        return {'snapshot_sha256':state['artifacts']['snapshot']['sha256'],
            'repository_revisions':revisions,'recorded_at':STAMP,
            'checks':[{'name':'unit','repository_id':'core','category':'UNIT','command':self.checks[0]['command'],
                       'status':'PASS','exit_code':0,'evidence_ref':self.ba.ref('test.json')}]}

    def review(self, state, revisions):
        return {'snapshot_sha256':state['artifacts']['snapshot']['sha256'],
            'repository_revisions':revisions,'recorded_at':STAMP,'evidence_refs':[self.ba.ref('review.json')],
            'blocking_findings':[], 'budget':{'full_reviews':1,'blocking_fix_waves':0,'scoped_rereviews':0}}

    def coverage(self):
        return [{'id':identity,'status':'COVERED','code_refs':[self.ba.ref('code.json')],
                 'test_refs':[self.ba.ref('test.json')]} for identity in ('BR-001','FR-001')]

    def finish(self, state=None, revisions=None):
        state = state or self.ready()
        revisions = revisions or self.produced
        state = dev.advance(state,'IMPLEMENTING',self.root, **self.context)
        state = dev.advance(state,'ENGINEERING_REVIEW',self.root, **self.context)
        state = dev.advance(state,'VERIFYING',self.root, **self.context)
        return dev.make_handoff(state,self.root, repository_revisions=revisions,
            current_base_revisions={r['id']:r['base_revision'] for r in state['repositories']},
            implementation=[{'repository_id':r['id'],'revision':revisions[r['id']],
                'changed_paths':[r['allowed_write_paths'][0]+'/request.py'],'evidence_refs':[self.ba.ref('code.json')]} for r in state['repositories']],
            coverage=self.coverage(),review=self.review(state,revisions),
            verification=self.verification(state,revisions),known_risks=[],**self.context)

    def test_normal_contract_acceptance_keeps_ba_bytes_immutable(self):
        refs = [self.upstream,self.handoff['ba_baseline']['manifest'],self.handoff['approval_receipt'],
                *self.handoff['authoritative_sources'].values()]
        before = {r['path']:(self.root/r['path']).read_bytes() for r in refs}
        handoff = self.finish()
        self.assertEqual(handoff['state'],'READY_FOR_TEST')
        self.assertEqual(handoff['artifact_class'],'HANDOFF_MANIFEST')
        self.assertNotIn('VERIFIED',dev.LIFECYCLE)
        self.assertEqual(before,{p:(self.root/p).read_bytes() for p in before})
        self.assertFalse((self.root/'spec.md').exists())

    def test_high_risk_requires_exact_authenticated_gate(self):
        state = self.planned(True)
        bases = {'core':'a'*40}
        with self.assertRaises(ValueError): dev.advance(state,'IMPLEMENTATION_READY',self.root,current_base_revisions=bases,**self.context)
        with self.assertRaises(ValueError): dev.bind_technical_approval(state,'approve',self.root,**self.context)
        receipt, auth = self.technical_receipt(state)
        with self.assertRaises(ValueError): dev.bind_technical_approval(state,receipt,self.root,technical_authenticator=lambda *_:False,**self.context)
        self.context['technical_authenticator'] = auth
        state = dev.bind_technical_approval(state,receipt,self.root,**self.context)
        self.assertEqual(dev.advance(state,'IMPLEMENTATION_READY',self.root,current_base_revisions=bases,**self.context)['lifecycle'],'IMPLEMENTATION_READY')
        self.assertEqual(self.ba.load('ed.json')['status'],'PROPOSED')  # validation never promotes a record

    def test_every_technical_snapshot_input_drift_revokes_gate(self):
        for name in ('dev-plan.md','dev-tasks.md','ed.json','impact.json','snapshot.json','technical-receipt.json'):
            with self.subTest(name=name):
                state = self.ready(high=True)
                path = self.root/name
                original = path.read_bytes()
                path.write_bytes(original+b'\n')
                with self.assertRaises(ValueError): dev.authorize_source_mutation(state,self.root,'core','src/request.py',current_base_revisions={'core':'a'*40},**self.context)
                path.write_bytes(original)

    def test_upstream_authentication_and_every_ba_byte_drift_fail_closed(self):
        state = self.start()
        for auth in (None,lambda *_:False,lambda *_:'true'):
            with self.subTest(auth=auth), self.assertRaises(ValueError):
                dev.advance(state,'AUTHORITY_VALIDATED',self.root,ba_authenticator=auth)
        for ref in [self.upstream,self.handoff['ba_baseline']['manifest'],self.handoff['approval_receipt'],
                    *self.handoff['authoritative_sources'].values()]:
            with self.subTest(ref=ref):
                path = self.root/ref['path']; original = path.read_bytes(); path.write_bytes(original+b'\n')
                with self.assertRaises(ValueError): dev.advance(state,'AUTHORITY_VALIDATED',self.root,**self.context)
                path.write_bytes(original)
        fake = copy.deepcopy(self.handoff); fake['open_items']['blocking'] = ['unresolved']
        self.ba.put('fake.json',fake)
        with self.assertRaises(ValueError): dev.read_upstream(self.ba.ref('fake.json'),self.root,**self.context)
        self.ba.put('fake.json',{'schema_version':2,'status':'APPROVED_BASELINE'})
        with self.assertRaises(ValueError): dev.read_upstream(self.ba.ref('fake.json'),self.root,**self.context)

    def test_v1_readers_have_no_vnext_authority(self):
        legacy = ba_tests.ROOT/'tooling/tests/fixtures/dev'
        from tooling.tests.test_dev_kit import _write_approved_baseline
        path = _write_approved_baseline(self.root/'legacy')
        ref = {'path':'legacy/engineering-handoff.yml','revision':'old','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        self.assertEqual(dev.read_upstream(ref,self.root)['mode'],'LEGACY_COMPAT')
        self.assertFalse(dev.read_upstream(ref,self.root)['vnext_authority'])
        state = self.start(); state['upstream'] = ref
        with self.assertRaises(ValueError): dev.advance(state,'AUTHORITY_VALIDATED',self.root,**self.context)
        impact = json.loads((legacy/'impact-manifest.valid.json').read_text())
        self.assertFalse(dev.read_artifact(impact,'impact')['vnext_authority'])

    def test_lifecycle_cannot_skip_or_mutate_before_ready(self):
        state = self.start()
        for lifecycle in ('IMPACT_ANALYZED','IMPLEMENTATION_READY','IMPLEMENTING','READY_FOR_TEST','VERIFIED'):
            with self.subTest(lifecycle=lifecycle),self.assertRaises(ValueError): dev.advance(state,lifecycle,self.root,**self.context)
        with self.assertRaises(ValueError): dev.authorize_source_mutation(state,self.root,'core','src/request.py',current_base_revisions={'core':'a'*40},**self.context)
        ready = self.ready()
        dev.authorize_source_mutation(ready,self.root,'core','src/request.py',current_base_revisions={'core':'a'*40},**self.context)
        after = dev.advance(ready,'IMPLEMENTING',self.root,**self.context)
        dev.validate_transition(ready,after)
        changed = copy.deepcopy(after); changed['history'][0]['to'] = 'IMPLEMENTATION_READY'
        with self.assertRaises(ValueError): dev.validate_state(changed,self.root,**self.context)
        changed = copy.deepcopy(after); changed['history'].pop(0)
        with self.assertRaises(ValueError): dev.validate_transition(ready,changed)

    def test_base_scope_and_upstream_write_guards(self):
        state = self.ready()
        for path in ('business-rules.md','srs.md','decisions.json','../src/request.py','docs/truth.md','SRC/../srs.md'):
            with self.subTest(path=path),self.assertRaises(ValueError): dev.authorize_source_mutation(state,self.root,'core',path,current_base_revisions={'core':'a'*40},**self.context)
        with self.assertRaises(ValueError): dev.authorize_source_mutation(state,self.root,'core','src/request.py',current_base_revisions={'core':'c'*40},**self.context)
        bad = self.start(); bad['repositories'][0]['allowed_write_paths'] = ['src','tests','business-rules.md']
        with self.assertRaises(ValueError): dev.advance(bad,'AUTHORITY_VALIDATED',self.root,**self.context)
        bad = copy.deepcopy(state); bad['repositories'][0]['allowed_write_paths'].append('extra')
        with self.assertRaises(ValueError): dev.authorize_source_mutation(bad,self.root,'core','extra/a.py',current_base_revisions={'core':'a'*40},**self.context)

    def test_gap_blocks_and_requires_exact_reapproved_replacement(self):
        state = self.ready()
        gap = {'schema_version':2,'gap_id':'GAP-001','finding_kind':'SPEC_GAP',
            'feature_id':'FEATURE-1','engineering_handoff_ref':self.upstream,
            'affected_business_ids':['FR-001'],'evidence_refs':[self.ba.ref('review.json')],
            'question':'Which outcome applies to an ambiguous request?',
            'blocking_scope':{'core':['src']},'discovered_at':STAMP,'status':'OPEN'}
        self.ba.put('gap.json',gap)
        blocked = dev.raise_gap(state,self.ba.ref('gap.json'),self.root,**self.context)
        self.assertEqual(blocked['lifecycle'],'UPSTREAM_GAP')
        with self.assertRaises(ValueError): dev.authorize_source_mutation(blocked,self.root,'core','src/request.py',current_base_revisions={'core':'a'*40},**self.context)
        with self.assertRaises(ValueError): dev.resume_gap(blocked,self.upstream,self.ba.ref('review.json'),self.root,**self.context)
        replacement = copy.deepcopy(self.ba.candidate)
        replacement.update(revision='R2',previous_baseline=self.ba.candidate_ref)
        replacement['semantic_sha256'] = ba_tests.ba.candidate_hash(replacement)
        self.ba.candidate = replacement; self.ba.candidate_ref = self.ba.publish(replacement)
        self.ba.state = ba_tests.ba.select_candidate(ba_tests.ba.new_state(replacement['feature'],'GREENFIELD'),self.ba.candidate_ref,self.root)
        approved, auth = self.ba.approved()
        handoff = ba_tests.ba.make_handoff(approved,self.root,human_actor_authenticator=auth)
        self.ba.put('replacement.json',handoff)
        resumed = dev.resume_gap(blocked,self.ba.ref('replacement.json','R2'),self.ba.ref('review.json'),self.root,ba_authenticator=auth)
        self.assertEqual(resumed['lifecycle'],'AUTHORITY_VALIDATED')
        self.assertEqual(resumed['engineering_gap']['replacement_handoff_ref'],self.ba.ref('replacement.json','R2'))
        self.assertNotIn('snapshot',resumed['artifacts'])

    def test_gap_cannot_use_baref_unknown_ids_or_unproven_resolution(self):
        for identity in ('BAREF:table-1','FR-999'):
            gap = {'schema_version':2,'gap_id':'GAP-001','finding_kind':'SPEC_GAP',
                'feature_id':'FEATURE-1','engineering_handoff_ref':self.upstream,
                'affected_business_ids':[identity],'evidence_refs':[self.ba.ref('review.json')],
                'question':'Which outcome?', 'blocking_scope':{'core':['src']},'discovered_at':STAMP,'status':'OPEN'}
            with self.subTest(identity=identity),self.assertRaises(ValueError): dev.validate_gap(gap,self.root,required_ids=['BR-001','FR-001'])

    def test_coverage_is_exact_business_set_with_code_and_test_evidence(self):
        valid = self.coverage()
        dev.validate_coverage(valid,['BR-001','FR-001'],self.root)
        variants = [valid[:1],valid+[valid[0]],valid+[dict(valid[0],id='BAREF:table-1')],
                    [dict(valid[0],id='FR-999'),valid[1]], [dict(valid[0],code_refs=[]),valid[1]],
                    [dict(valid[0],test_refs=[]),valid[1]]]
        for rows in variants:
            with self.subTest(rows=rows),self.assertRaises(ValueError): dev.validate_coverage(rows,['BR-001','FR-001'],self.root)

    def test_review_verification_coverage_and_output_revisions_block_handoff(self):
        handoff = self.finish()
        for field, alter in (
            ('requirements_coverage',lambda _:self.coverage()[:1]),
            ('review',lambda value:{**value,'blocking_findings':['must fix']}),
            ('review',lambda value:{**value,'budget':{'full_reviews':2,'blocking_fix_waves':0,'scoped_rereviews':0}}),
            ('engineering_verification',lambda value:{**value,'checks':[dict(value['checks'][0],status='FAIL',exit_code=1)]}),
            ('engineering_verification',lambda value:{**value,'repository_revisions':{'core':'c'*40}}),
            ('repository_revisions',lambda _:{'core':'c'*40}),
            ('state',lambda _:'VERIFIED')):
            bad = copy.deepcopy(handoff); bad[field] = alter(bad[field])
            with self.subTest(field=field),self.assertRaises(ValueError): dev.validate_handoff(bad,self.root,**self.context)
        (self.root/'business-rules.md').write_bytes(b'changed upstream')
        with self.assertRaises(ValueError): dev.validate_handoff(handoff,self.root,**self.context)

    def test_multi_repo_requires_high_risk_and_exact_output_revisions(self):
        repos = self.repos+[{'id':'client','role':'IMPLEMENTATION','base_revision':'c'*40,
                            'allowed_write_paths':['client'], 'read_only_evidence_paths':[]}]
        state = self.planned(repos=repos)
        self.assertEqual(state['risk']['level'],'HIGH_RISK')
        state = self.ready(state)
        handoff = self.finish(state,{'core':'b'*40,'client':'d'*40})
        self.assertEqual(set(handoff['repository_revisions']),{'core','client'})
        self.assertEqual(handoff['implementation'][1]['revision'],'d'*40)

    def test_maintenance_fast_path_cannot_bypass_behavior_or_risk(self):
        state = dev.advance(self.start(maintenance=True),'AUTHORITY_VALIDATED',self.root)
        self.assertEqual(state['risk']['level'],'TRIVIAL')
        snapshot = dev.maintenance_snapshot(state,self.root,revision='TECH-1')
        self.ba.put('snapshot.json',snapshot)
        state = dev.prepare_maintenance(state,self.ba.ref('snapshot.json','TECH-1'),self.root,current_base_revisions={'core':'a'*40})
        self.assertIsNone(state['upstream'])
        for change in ('BUSINESS_BEHAVIOR','PUBLIC_CONTRACT','DATA_SEMANTICS','USER_VISIBLE_OUTCOME','SECURITY','CROSS_REPOSITORY'):
            bad = self.start(maintenance=True); bad['maintenance']['discovered_changes'] = [change]
            with self.subTest(change=change),self.assertRaises(ValueError): dev.advance(bad,'AUTHORITY_VALIDATED',self.root)

    def test_risk_never_downgrades_and_escalation_invalidates_plan(self):
        state = self.ready()
        escalated = dev.escalate_risk(state,{'level':'HIGH_RISK','categories':['SECURITY'],'reasons':['new boundary']})
        self.assertEqual(escalated['lifecycle'],'NEEDS_REPLAN')
        self.assertEqual(escalated['gates'],{})
        with self.assertRaises(ValueError): dev.escalate_risk(escalated,{'level':'NORMAL','categories':[],'reasons':[]})
        with self.assertRaises(ValueError): dev.authorize_source_mutation(escalated,self.root,'core','src/request.py',current_base_revisions={'core':'a'*40},**self.context)

    def test_engineering_decision_identity_materiality_and_foundation_routing(self):
        decision = self.decision()
        dev.validate_decision(decision,self.root,change_id='CHANGE-1',upstream=self.upstream)
        self.assertEqual(decision['status'],'PROPOSED')
        for updates in ({'id':'BR-002'},{'id':'ADR-001'},{'status':'APPROVED'},
                        {'approval_requirement':'NONE'},{'category':'SERVICE_BOUNDARY'}):
            with self.subTest(updates=updates),self.assertRaises(ValueError): dev.validate_decision(dict(decision,**updates),self.root,change_id='CHANGE-1',upstream=self.upstream)

    def test_unknown_fields_and_versions_fail_closed(self):
        for data in (dict(self.start(),schema_version=99),dict(self.start(),doctor='READY'),dict(self.start(),approved=True)):
            with self.assertRaises(ValueError): dev.validate_state(data,self.root,**self.context)
        impact = self.impact(self.start())
        with self.assertRaises(ValueError): dev.validate_impact(dict(impact,br_content='rewritten'),self.root)

    def test_spec_kit_and_doctor_do_not_supply_feature_authority(self):
        self.assertNotIn('spec.md',dev.PLANNING_NAMES)
        from tooling.lib import dev_kit
        self.assertEqual(dev_kit.validate_workflow_package(ROOT),[])
        state = self.planned(True)
        self.ba.put('doctor.json',{'status':'READY','choice':'approve'})
        with self.assertRaises(ValueError): dev.bind_technical_approval(state,self.ba.ref('doctor.json'),self.root,**self.context)
        (self.root/'current-system.txt').write_text('Everyone may submit; current implementation differs.',encoding='utf-8')
        handoff = self.finish()
        self.assertEqual([r['id'] for r in handoff['requirements_coverage']],['BR-001','FR-001'])

    def test_foundation_durable_proof_is_revalidated_through_ba(self):
        foundation = ba_tests.foundation_tests.FoundationTests('test_synthetic_brownfield_acceptance_preserves_current_inferred_unknown')
        foundation.setUp()
        self.addCleanup(foundation.doCleanups)
        _, approval, auth = foundation.promoted()
        import shutil
        shutil.copytree(foundation.root,self.root/'foundation-project')
        candidate = copy.deepcopy(self.ba.candidate)
        candidate['project_foundation'] = {'root':'foundation-project',
            'manifest':self.ba.ref('foundation-project/docs/foundation/R1.json'),
            'provenance':self.ba.ref('foundation-project/docs/foundation/R1.provenance.json'),
            'approval':self.ba.ref('foundation-project/'+approval['path'])}
        candidate['revision'] = 'R2'
        candidate['semantic_sha256'] = ba_tests.ba.candidate_hash(candidate)
        self.ba.candidate = candidate; self.ba.candidate_ref = self.ba.publish(candidate)
        self.ba.state = ba_tests.ba.select_candidate(ba_tests.ba.new_state(candidate['feature'],'GREENFIELD'),
            self.ba.candidate_ref,self.root,foundation_authenticator=auth)
        approved, self.ba_auth = self.ba.approved(auth)
        handoff = ba_tests.ba.make_handoff(approved,self.root,human_actor_authenticator=self.ba_auth,foundation_authenticator=auth)
        self.ba.put('foundation-handoff.json',handoff)
        self.upstream = self.ba.ref('foundation-handoff.json','R2')
        context = {'ba_authenticator':self.ba_auth,'foundation_authenticator':auth}
        state = dev.advance(self.start(),'AUTHORITY_VALIDATED',self.root,**context)
        self.assertEqual(state['lifecycle'],'AUTHORITY_VALIDATED')
        with self.assertRaises(ValueError): dev.advance(self.start(),'AUTHORITY_VALIDATED',self.root,ba_authenticator=self.ba_auth)
        for ref in (candidate['project_foundation'][key] for key in ('manifest','provenance','approval')):
            with self.subTest(ref=ref):
                path = self.root/ref['path']; content = path.read_bytes(); path.write_bytes(content+b'\n')
                with self.assertRaises(ValueError): dev.advance(self.start(),'AUTHORITY_VALIDATED',self.root,**context)
                path.write_bytes(content)

    def test_technical_receipt_replay_and_host_side_drift_fail(self):
        state = self.planned(True)
        receipt, auth = self.technical_receipt(state)
        wrong = self.ba.load('technical-receipt.json'); wrong['run_id'] = 'RUN-2'
        self.ba.put('replayed.json',wrong)
        with self.assertRaises(ValueError): dev.bind_technical_approval(state,self.ba.ref('replayed.json','TECH-1'),self.root,technical_authenticator=lambda *_:True,**self.context)
        for name in ('snapshot.json','dev-plan.md','impact.json','ed.json','receipt.json','business-rules.md'):
            with self.subTest(name=name):
                path = self.root/name; content = path.read_bytes()
                def drifting_host(actor,row):
                    path.write_bytes(content+b'\n')
                    return auth(actor,row)
                with self.assertRaises(ValueError): dev.bind_technical_approval(state,receipt,self.root,technical_authenticator=drifting_host,**self.context)
                path.write_bytes(content)

    def test_approved_ed_requires_its_own_authenticated_content_receipt(self):
        decision = self.decision(status='APPROVED')
        receipt = {'schema_version':2,'artifact_type':'ENGINEERING_DECISION_APPROVAL','decision':'APPROVE',
            'actor_id':'lead','actor_role':'TECH_LEAD','recorded_at':STAMP,'change_id':'CHANGE-1',
            'engineering_decision_id':'ED-001','decision_sha256':dev.decision_hash(decision),
            'decision_evidence_ref':self.ba.ref('review.json')}
        self.ba.put('ed-receipt.json',receipt)
        decision['approval_ref'] = self.ba.ref('ed-receipt.json')
        for auth in (None,lambda *_:False):
            with self.subTest(auth=auth),self.assertRaises(ValueError): dev.validate_decision(decision,self.root,
                change_id='CHANGE-1',upstream=self.upstream,technical_authenticator=auth)
        expected = copy.deepcopy(receipt)
        auth = lambda actor,row: actor == 'lead' and row == expected
        self.assertEqual(dev.validate_decision(decision,self.root,change_id='CHANGE-1',upstream=self.upstream,
            technical_authenticator=auth)['status'],'APPROVED')
        changed = dict(decision,decision='Alter response shape')
        with self.assertRaises(ValueError): dev.validate_decision(changed,self.root,change_id='CHANGE-1',upstream=self.upstream,technical_authenticator=auth)

    def test_upstream_transitive_human_evidence_paths_are_protected(self):
        for path in ('human-answer.txt','human-approval.txt','candidates'):
            state = self.start(); state['repositories'][0]['allowed_write_paths'].append(path)
            with self.subTest(path=path),self.assertRaises(ValueError): dev.advance(state,'AUTHORITY_VALIDATED',self.root,**self.context)

    def test_ready_for_test_cannot_be_fabricated_in_state(self):
        state = self.ready()
        state = dev.advance(state,'IMPLEMENTING',self.root,**self.context)
        state = dev.advance(state,'ENGINEERING_REVIEW',self.root,**self.context)
        state = dev.advance(state,'VERIFYING',self.root,**self.context)
        fake = copy.deepcopy(state); fake['lifecycle'] = 'READY_FOR_TEST'
        dev._event(state,fake,'FINALIZE')
        with self.assertRaises(ValueError): dev.validate_state(fake,self.root,**self.context)

    def test_maintenance_contract_can_finish_without_ba_or_feature_coverage(self):
        state = dev.advance(self.start(maintenance=True),'AUTHORITY_VALIDATED',self.root)
        self.ba.put('snapshot.json',dev.maintenance_snapshot(state,self.root,revision='TECH-1'))
        state = dev.prepare_maintenance(state,self.ba.ref('snapshot.json','TECH-1'),self.root,current_base_revisions={'core':'a'*40})
        state = dev.advance(state,'IMPLEMENTING',self.root)
        state = dev.advance(state,'VERIFYING',self.root)
        review = self.review(state,self.produced); review['budget']['full_reviews'] = 0
        handoff = dev.make_handoff(state,self.root,repository_revisions=self.produced,current_base_revisions={'core':'a'*40},
            implementation=[{'repository_id':'core','revision':'b'*40,'changed_paths':['src/request.py'],
                'evidence_refs':[self.ba.ref('code.json')]}],coverage=[],review=review,
            verification=self.verification(state,self.produced),known_risks=[])
        self.assertEqual(handoff['state'],'READY_FOR_TEST')
        self.assertIsNone(handoff['feature'])
        self.assertEqual(handoff['requirements_coverage'],[])

    def test_engineering_evidence_never_claims_system_acceptance(self):
        state = self.ready()
        review = self.review(state,self.produced)
        verification = self.verification(state,self.produced)
        for category in ('SYSTEM_E2E','BROWSER_GOLDEN_JOURNEY','TESTER_ACCEPTANCE','DB_RLS_SYSTEM'):
            bad = copy.deepcopy(verification); bad['checks'][0]['category'] = category
            with self.subTest(category=category),self.assertRaises(ValueError): dev._final_evidence(state,
                state['artifacts']['snapshot'],self.produced,review,bad,self.root)
        verification['recorded_at'] = '2026-10-04T09:59:59Z'
        with self.assertRaises(ValueError): dev._final_evidence(state,state['artifacts']['snapshot'],self.produced,review,verification,self.root)

    def test_ba_product_domain_knowledge_cannot_be_refined_by_dev(self):
        state = dev.advance(self.start(),'AUTHORITY_VALIDATED',self.root,**self.context)
        impact = self.impact(state)
        impact['knowledge_impact']['areas']['domain'] = {'affected':True,'targets':['docs/domain.md']}
        self.ba.put('impact.json',impact)
        with self.assertRaises(ValueError): dev.analyze_impact(state,self.ba.ref('impact.json'),self.root,**self.context)

    def test_contract_version_and_nested_unknown_fields(self):
        state = self.start()
        for updates in ({'risk':dict(state['risk'],approved=True)},
                        {'upstream':{'path':'handoff.json','revision':'R1','sha256':'0'*64,'approved':True}},
                        {'authority_mode':'CURRENT_SYSTEM'}, {'schema_version':True}):
            with self.subTest(updates=updates),self.assertRaises(ValueError): dev.validate_state(dict(state,**updates),self.root,**self.context)

    def test_legacy_state_and_handoff_remain_inspection_only(self):
        data = json.loads((ROOT/'tooling/tests/fixtures/dev/dev-handoff.valid.json').read_text())
        self.assertEqual(dev.read_artifact(data,'handoff')['mode'],'LEGACY_COMPAT')
        self.assertFalse(dev.read_artifact(data,'handoff')['vnext_authority'])
        state = {'schema_version':1,'change_id':'OLD','status':'READY_FOR_TEST',
            'human_gate':{'resolved':True,'choice':'approve'}}
        self.assertFalse(dev.read_artifact(state,'state')['vnext_authority'])
        with self.assertRaises(ValueError): dev.validate_state(state,self.root,**self.context)
        impact = self.impact(self.start())
        self.assertFalse(dev.read_artifact(impact,'impact',self.root)['vnext_authority'])

    def test_project_architecture_requires_external_adr_and_foundation_impact(self):
        row = self.decision('SERVICE_BOUNDARY')
        self.ba.put('adr.json',{'authority':'external project architecture evidence'})
        row['adr_ref'] = self.ba.ref('adr.json')
        dev.validate_decision(row,self.root,change_id='CHANGE-1',upstream=self.upstream)
        self.ba.put('ed.json',row)
        state = self.planned(True)
        self.ba.put('ed.json',row)
        # New ED bytes cannot fit the old snapshot. A new snapshot also needs
        # explicit architecture Knowledge Impact, beyond an ADR-shaped locator.
        state = dev.escalate_risk(state,state['risk'])
        state = dev.replan(state,self.root,**self.context)
        impact = self.impact(state,'HIGH_RISK',['PUBLIC_API'])
        self.ba.put('impact.json',impact)
        state = dev.analyze_impact(state,self.ba.ref('impact.json'),self.root,**self.context)
        with self.assertRaises(ValueError): dev.make_snapshot(state,self.root,revision='TECH-2',
            decisions=[self.ba.ref('ed.json')],plan=self.ba.ref('dev-plan.md'),tasks=self.ba.ref('dev-tasks.md'),**self.context)
        impact['knowledge_impact']['areas']['architecture'] = {'affected':True,'targets':['adr.json']}
        # Re-analyze on a validated-authority state; immutable snapshots are not rewritten.
        state = dev.escalate_risk(state,state['risk']); state = dev.replan(state,self.root,**self.context)
        self.ba.put('impact.json',impact)
        state = dev.analyze_impact(state,self.ba.ref('impact.json'),self.root,**self.context)
        snapshot = dev.make_snapshot(state,self.root,revision='TECH-2',decisions=[self.ba.ref('ed.json')],
            plan=self.ba.ref('dev-plan.md'),tasks=self.ba.ref('dev-tasks.md'),**self.context)
        self.assertEqual(snapshot['engineering_decisions'],[self.ba.ref('ed.json')])
        (self.root/'.devkit').mkdir()
        self.ba.put('.devkit/adr.json',{'authority':'runtime'})
        row['adr_ref'] = self.ba.ref('.devkit/adr.json')
        with self.assertRaises(ValueError): dev.validate_decision(row,self.root,change_id='CHANGE-1',upstream=self.upstream)

    def test_gap_schema_must_have_shared_kind_and_exact_evidence(self):
        gap = {'schema_version':2,'gap_id':'GAP-001','finding_kind':'SPEC_GAP','feature_id':'FEATURE-1',
            'engineering_handoff_ref':self.upstream,'affected_business_ids':['BR-001'],
            'evidence_refs':[self.ba.ref('review.json')],'question':'Which outcome?',
            'blocking_scope':{'core':['src']},'discovered_at':STAMP,'status':'OPEN'}
        for updates in ({'finding_kind':'UPSTREAM_REQUIREMENT_GAP'},{'evidence_refs':[]},
                        {'blocking_scope':{}},{'status':'RESOLVED'}, {'affected_business_ids':['BR-001','BR-001']}):
            with self.subTest(updates=updates),self.assertRaises(ValueError): dev.validate_gap(dict(gap,**updates),self.root,required_ids=['BR-001','FR-001'])

    def test_approved_material_ed_still_requires_exact_whole_snapshot_gate(self):
        state = dev.advance(self.start(),'AUTHORITY_VALIDATED',self.root,**self.context)
        self.ba.put('impact.json',self.impact(state))
        state = dev.analyze_impact(state,self.ba.ref('impact.json'),self.root,**self.context)
        row = self.decision('LOCAL_DESIGN','APPROVED'); row['risk'] = 'NORMAL'
        receipt = {'schema_version':2,'artifact_type':'ENGINEERING_DECISION_APPROVAL','decision':'APPROVE',
            'actor_id':'lead','actor_role':'HUMAN','recorded_at':STAMP,'change_id':'CHANGE-1',
            'engineering_decision_id':'ED-001','decision_sha256':dev.decision_hash(row),
            'decision_evidence_ref':self.ba.ref('review.json')}
        self.ba.put('ed-receipt.json',receipt); row['approval_ref'] = self.ba.ref('ed-receipt.json')
        expected = copy.deepcopy(receipt)
        self.context['technical_authenticator'] = lambda actor,data: actor == 'lead' and data == expected
        self.ba.put('ed.json',row)
        for name in ('dev-plan.md','dev-tasks.md'): (self.root/name).write_text('Technical runtime plan',encoding='utf-8')
        snapshot = dev.make_snapshot(state,self.root,revision='TECH-1',decisions=[self.ba.ref('ed.json')],
            plan=self.ba.ref('dev-plan.md'),tasks=self.ba.ref('dev-tasks.md'),**self.context)
        self.ba.put('snapshot.json',snapshot)
        state = dev.plan(state,self.ba.ref('snapshot.json','TECH-1'),self.root,**self.context)
        with self.assertRaises(ValueError): dev.advance(state,'IMPLEMENTATION_READY',self.root,current_base_revisions={'core':'a'*40},**self.context)

    def test_escalation_replan_requires_new_exact_technical_authorization(self):
        state = dev.escalate_risk(self.ready(),{'level':'HIGH_RISK','categories':['SECURITY'],'reasons':['new boundary']})
        state = dev.replan(state,self.root,**self.context)
        impact = self.impact(state,'HIGH_RISK',['SECURITY']); impact['risk']['reasons'] = ['new boundary']
        self.ba.put('impact.json',impact)
        state = dev.analyze_impact(state,self.ba.ref('impact.json'),self.root,**self.context)
        snapshot = dev.make_snapshot(state,self.root,revision='TECH-1',decisions=[],
            plan=self.ba.ref('dev-plan.md'),tasks=self.ba.ref('dev-tasks.md'),**self.context)
        self.ba.put('snapshot.json',snapshot)
        state = dev.plan(state,self.ba.ref('snapshot.json','TECH-1'),self.root,**self.context)
        with self.assertRaises(ValueError): dev.advance(state,'IMPLEMENTATION_READY',self.root,current_base_revisions={'core':'a'*40},**self.context)
        self.assertEqual(self.ready(state)['lifecycle'],'IMPLEMENTATION_READY')

    def test_ed_supersession_requires_reciprocal_acyclic_durable_records(self):
        state = self.start(); state['risk'] = {'level':'HIGH_RISK','categories':['PUBLIC_API'],'reasons':[]}
        old = self.decision(status='SUPERSEDED'); old['superseded_by'] = ['ED-002']
        new = self.decision(); new.update(id='ED-002',supersedes=['ED-001'])
        self.ba.put('old-ed.json',old); self.ba.put('new-ed.json',new)
        refs = [self.ba.ref('old-ed.json'),self.ba.ref('new-ed.json')]
        self.assertEqual(len(dev._decision_set(refs,self.root,state,**self.context)),2)
        new['supersedes'] = []; self.ba.put('new-ed.json',new)
        with self.assertRaises(ValueError): dev._decision_set([refs[0],self.ba.ref('new-ed.json')],self.root,state,**self.context)
        new.update(status='SUPERSEDED',supersedes=['ED-001'],superseded_by=['ED-001'])
        old['supersedes'] = ['ED-002']
        self.ba.put('old-ed.json',old); self.ba.put('new-ed.json',new)
        with self.assertRaises(ValueError): dev._decision_set([self.ba.ref('old-ed.json'),self.ba.ref('new-ed.json')],self.root,state,**self.context)

    def test_final_ba_callback_cannot_drift_technical_snapshot_before_source_write(self):
        state = self.ready(high=True)
        for name in ('snapshot.json','review.json'):
            with self.subTest(name=name):
                path = self.root/name; content = path.read_bytes(); calls = []
                def ba_host(actor,row):
                    calls.append(actor)
                    if len(calls) == 2: path.write_bytes(content+b'\n')
                    return self.ba_auth(actor,row)
                context = {**self.context,'ba_authenticator':ba_host}
                with self.assertRaises(ValueError): dev.authorize_source_mutation(state,self.root,'core','src/request.py',
                    current_base_revisions={'core':'a'*40},**context)
                self.assertGreaterEqual(len(calls),2)
                path.write_bytes(content)


if __name__ == '__main__':
    unittest.main()
