"""Neutral BA semantic acceptance. Human authenticators here are test hosts only."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ba-workflow/scripts'))
import ba_vnext as ba
import ba_contracts as compat
from shared.sdlc.foundation.impact import knowledge_impact, routes
from shared.sdlc.foundation.contract import foundation_readiness
from tooling.tests import test_project_foundation as foundation_tests


class BAVNextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT/'tooling/tests/fixtures/ba-vnext', self.root, dirs_exist_ok=True)
        self.sources = {role: self.ref(name) for role, name in
                        [('business_rules', 'business-rules.md'), ('srs', 'srs.md')]}
        decisions = self.load('decisions.json')
        decisions['decisions'][0]['implemented_sources'] = copy.deepcopy(self.sources)
        decisions['decisions'][0]['input_refs'] = [self.ref('human-answer.txt')]
        self.put('decisions.json', decisions)
        self.sources['decisions'] = self.ref('decisions.json')
        self.candidate = ba.make_candidate(self.root, feature={'id':'FEATURE-1','title':'Collection requests'},
            baseline_id='BA-1', revision='R1', sources=self.sources,
            business_identities=[{'id':'BR-001','semantic_key':'eligibility','status':'ACTIVE'},
                                 {'id':'FR-001','semantic_key':'submit-request','status':'ACTIVE'}],
            knowledge=knowledge_impact())
        self.candidate_ref = self.publish(self.candidate)
        self.state = ba.new_state(self.candidate['feature'], 'GREENFIELD')
        self.state = ba.select_candidate(self.state, self.candidate_ref, self.root)

    def put(self, name, value):
        (self.root/name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True), encoding='utf-8')

    def load(self, name):
        return json.loads((self.root/name).read_text(encoding='utf-8'))

    def ref(self, name, revision='R1'):
        return {'path':name,'revision':revision,'sha256':hashlib.sha256((self.root/name).read_bytes()).hexdigest()}

    def publish(self, candidate):
        return ba.publish_candidate(self.root, f"candidates/{candidate['revision']}.json", candidate)

    def host_receipt(self, candidate=None, candidate_ref=None, actor='synthetic-human'):
        candidate = candidate or self.candidate
        candidate_ref = candidate_ref or self.candidate_ref
        receipt = {'schema_version':1,'artifact_type':'BA_BASELINE','decision':'APPROVE',
            'actor_id':actor,'actor_role':'HUMAN','recorded_at':'2026-10-04T09:00:00Z',
            'feature_id':candidate['feature']['id'],'baseline_id':candidate['id'],
            'baseline_revision':candidate['revision'],'baseline_semantic_sha256':candidate['semantic_sha256'],
            'baseline_manifest':candidate_ref,'decision_ref':self.ref('human-approval.txt')}
        if 'previous_baseline' in candidate:
            previous = self.load(candidate['previous_baseline']['path'])
            receipt['previous_baseline'] = {k:previous[k] for k in ('id','revision','semantic_sha256')}
        self.put('receipt.json', receipt)
        expected = copy.deepcopy(receipt)
        return self.ref('receipt.json', candidate['revision']), lambda who, actual: who == 'synthetic-human' and actual == expected

    def approved(self, foundation_authenticator=None):
        state = ba.advance(self.state, 'VALIDATE', self.root, foundation_authenticator=foundation_authenticator)
        state = ba.advance(state, 'REQUEST_REVIEW', self.root, foundation_authenticator=foundation_authenticator)
        approval, auth = self.host_receipt()
        state = ba.advance(state, 'APPROVE', self.root, approval=approval, human_actor_authenticator=auth,
            foundation_authenticator=foundation_authenticator)
        return state, auth

    def test_greenfield_exact_baseline_and_handoff(self):
        state, auth = self.approved()
        handoff = ba.make_handoff(state, self.root, human_actor_authenticator=auth)
        self.assertEqual(state['lifecycle'], 'APPROVED_BASELINE')
        self.assertEqual(ba.validate_handoff(handoff, self.root, human_actor_authenticator=auth)['status'], 'APPROVED_BASELINE')
        self.assertEqual(handoff['authoritative_sources'], self.sources)
        self.assertEqual(handoff['knowledge_impact'], self.candidate['knowledge_impact'])
        self.assertEqual(ba.read_baseline(self.candidate_ref, self.root)['coverage_ids'], ['BR-001','FR-001'])

    def test_greenfield_proposals_then_named_human_answer_then_approval(self):
        decisions = self.load('decisions.json')
        decisions['decisions'][0]['status'] = 'PROPOSED'
        self.put('decisions.json',decisions)
        candidate = copy.deepcopy(self.candidate)
        candidate['sources']['decisions'] = self.ref('decisions.json')
        candidate['semantic_sha256'] = ba.candidate_hash(candidate)
        self.assertEqual(ba.validate_candidate(candidate,self.root,ready=False)['status'],'DRAFT')
        with self.assertRaises(ValueError): ba.validate_candidate(candidate,self.root)
        answer = copy.deepcopy(decisions['decisions'][0])
        answer.update(id='DEC-002',status='CONFIRMED',supersedes=['DEC-001'])
        expected = copy.deepcopy(answer)
        decisions = ba.record_answer(decisions,answer,self.root,
            human_actor_authenticator=lambda actor,row: actor == 'synthetic-human' and row == expected)
        self.put('decisions.json',decisions)
        candidate['sources']['decisions'] = self.ref('decisions.json')
        candidate['revision'] = 'R2'
        candidate['semantic_sha256'] = ba.candidate_hash(candidate)
        self.candidate = candidate
        self.candidate_ref = self.publish(candidate)
        self.state = ba.select_candidate(ba.new_state(candidate['feature'],'GREENFIELD'),self.candidate_ref,self.root)
        state, auth = self.approved()
        self.assertEqual(ba.validate_handoff(ba.make_handoff(state,self.root,human_actor_authenticator=auth),
            self.root,human_actor_authenticator=auth)['status'],'APPROVED_BASELINE')

    def test_brownfield_foundation_current_system_and_target_are_distinct(self):
        # Reuse the Foundation public API acceptance fixture, with its own trusted host.
        foundation = foundation_tests.FoundationTests('test_synthetic_brownfield_acceptance_preserves_current_inferred_unknown')
        foundation.setUp()
        try:
            data, foundation_approval, foundation_auth = foundation.promoted()
            self.assertEqual(foundation_readiness(data, foundation.root)['status'], 'PROJECT_FOUNDATION_READY')
            shutil.copytree(foundation.root, self.root/'foundation-project')
            # Portable references remain relative to the Foundation manifest's project root.
            foundation_ref = {'manifest':self.ref('foundation-project/docs/foundation/R1.json'),
                'provenance':self.ref('foundation-project/docs/foundation/R1.provenance.json'),
                'approval':self.ref('foundation-project/'+foundation_approval['path']),
                'root':'foundation-project'}
            self.candidate['project_foundation'] = foundation_ref
            self.candidate['mode'] = 'BROWNFIELD'
            self.candidate['evidence'] = [{'label':'CURRENT_SYSTEM','ref':self.ref('current-system.txt'),
                'topic':'eligibility','target_decision_id':'DEC-001'}]
            self.candidate['knowledge_impact']['areas']['domain'] = {'affected':True,'targets':['domain/requests.md']}
            self.candidate['knowledge_impact']['areas']['architecture'] = {'affected':True,'targets':['architecture/impact.md']}
            self.candidate['semantic_sha256'] = ba.candidate_hash(self.candidate)
            self.candidate['revision'] = 'R2'
            self.candidate['semantic_sha256'] = ba.candidate_hash(self.candidate)
            self.candidate_ref = self.publish(self.candidate)
            self.state = ba.select_candidate(ba.new_state(self.candidate['feature'], 'BROWNFIELD'), self.candidate_ref,
                self.root, foundation_authenticator=foundation_auth)
            self.assertEqual(self.state['lifecycle'], 'DRAFT')
            with self.assertRaises(ValueError): ba.make_handoff(self.state, self.root)
            state, auth = self.approved(foundation_auth)
            handoff = ba.make_handoff(state, self.root, human_actor_authenticator=auth,
                foundation_authenticator=foundation_auth)
            self.assertEqual(handoff['project_foundation'], foundation_ref)
            self.assertCountEqual([r['owner'] for r in routes(handoff['knowledge_impact'])], ['BA','ENGINEERING'])
            self.assertIn('eligible members', (self.root/'business-rules.md').read_text())
            self.assertIn('all visitors', (self.root/'current-system.txt').read_text())
            foundation_path = self.root/foundation_ref['manifest']['path']
            foundation_path.write_bytes(foundation_path.read_bytes()+b'\n')
            with self.assertRaises(ValueError): ba.validate_handoff(handoff, self.root, human_actor_authenticator=auth,
                foundation_authenticator=foundation_auth)
        finally:
            foundation.doCleanups()

    def test_structurally_ready_unpromoted_brownfield_foundation_is_rejected(self):
        foundation = foundation_tests.FoundationTests('test_synthetic_brownfield_acceptance_preserves_current_inferred_unknown')
        foundation.setUp()
        try:
            foundation.prepare()
            data = foundation.candidate()
            self.assertNotIn('APPROVED_TARGET', [section['evidence'] for section in data['sections'].values()])
            self.assertEqual(foundation_readiness(data, foundation.root)['status'], 'PROJECT_FOUNDATION_READY')
            shutil.copytree(foundation.root, self.root/'foundation-unpromoted')
            foundation_ref = {'manifest':self.ref(
                'foundation-unpromoted/.sdlc/runs/foundation/run-1/candidates/R1/manifest.json'),
                'root':'foundation-unpromoted'}
            candidate = copy.deepcopy(self.candidate)
            candidate['project_foundation'] = foundation_ref
            candidate['mode'] = 'BROWNFIELD'
            candidate['evidence'] = [{'label':'CURRENT_SYSTEM','ref':self.ref('current-system.txt'),
                'topic':'eligibility','target_decision_id':'DEC-001'}]
            candidate['knowledge_impact']['areas']['domain'] = {'affected':True,'targets':['domain/requests.md']}
            candidate['knowledge_impact']['areas']['architecture'] = {'affected':True,'targets':['architecture/impact.md']}
            candidate['revision'] = 'R2'
            candidate['semantic_sha256'] = ba.candidate_hash(candidate)
            with self.assertRaises(ValueError):
                ba.validate_candidate(candidate, self.root)
            approval, auth = foundation.receipt(data)
            foundation_tests.w.accept(foundation.root,'run-1',approval,human_actor_authenticator=auth)
            foundation_tests.w.promote(foundation.root,'run-1','docs/foundation/R1.json',
                'docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
            durable = json.loads((foundation.root/'docs/foundation/R1.json').read_text(encoding='utf-8'))
            self.assertEqual(durable,data)
            self.assertEqual(foundation_readiness(durable,foundation.root)['manifest_sha256'],
                foundation_readiness(data,foundation.root)['manifest_sha256'])
            shutil.copytree(foundation.root,self.root/'foundation-project')
            binding = {'root':'foundation-project',
                'manifest':self.ref('foundation-project/docs/foundation/R1.json'),
                'provenance':self.ref('foundation-project/docs/foundation/R1.provenance.json'),
                'approval':self.ref('foundation-project/'+approval['path'])}
            candidate['project_foundation'] = binding
            candidate['semantic_sha256'] = ba.candidate_hash(candidate)
            self.assertEqual(ba.validate_candidate(candidate,self.root,foundation_authenticator=auth)['status'],'VALIDATED')
        finally:
            foundation.doCleanups()

    def test_foundation_promotion_proof_mutations_fail_closed(self):
        foundation = foundation_tests.FoundationTests('test_synthetic_brownfield_acceptance_preserves_current_inferred_unknown')
        foundation.setUp()
        try:
            _, approval, auth = foundation.promoted()
            shutil.copytree(foundation.root, self.root/'foundation-project')
            binding = {'root':'foundation-project',
                'manifest':self.ref('foundation-project/docs/foundation/R1.json'),
                'provenance':self.ref('foundation-project/docs/foundation/R1.provenance.json'),
                'approval':self.ref('foundation-project/'+approval['path'])}
            def candidate_for(proof):
                candidate = copy.deepcopy(self.candidate)
                candidate['project_foundation'] = copy.deepcopy(proof)
                candidate['semantic_sha256'] = ba.candidate_hash(candidate)
                return candidate
            valid = candidate_for(binding)
            self.assertEqual(ba.validate_candidate(valid,self.root,foundation_authenticator=auth)['status'],'VALIDATED')
            for host in (None,lambda *_:False):
                with self.subTest(authenticator=host), self.assertRaises(ValueError):
                    ba.validate_candidate(valid,self.root,foundation_authenticator=host)
            missing = copy.deepcopy(binding); missing.pop('provenance')
            with self.assertRaises(ValueError): ba.validate_candidate(candidate_for(missing),self.root,foundation_authenticator=auth)

            provenance_path = self.root/binding['provenance']['path']
            original_provenance = provenance_path.read_bytes()
            original_receipt = (self.root/binding['approval']['path']).read_bytes()
            def changed_provenance(change):
                value = json.loads(original_provenance)
                change(value)
                provenance_path.write_text(json.dumps(value,sort_keys=True,separators=(',',':')),encoding='utf-8')
                proof = copy.deepcopy(binding)
                proof['provenance'] = self.ref('foundation-project/docs/foundation/R1.provenance.json')
                with self.assertRaises(ValueError):
                    ba.validate_candidate(candidate_for(proof),self.root,foundation_authenticator=auth)
                provenance_path.write_bytes(original_provenance)
            changed_provenance(lambda row: row.update(manifest_sha256='0'*64))
            changed_provenance(lambda row: row['source'].update(sha256='0'*64))
            changed_provenance(lambda row: row['source'].update(id='OTHER'))
            changed_provenance(lambda row: row['source'].update(revision='R2'))
            changed_provenance(lambda row: row.update(mode='GREENFIELD_BOOTSTRAP'))
            changed_provenance(lambda row: row.update(approval_receipt={'path':'other.json','revision':'R1','sha256':'0'*64}))
            changed_provenance(lambda row: row.update(schema_version=True))
            changed_provenance(lambda row: row.update(human_approval=0))
            changed_provenance(lambda row: row.update(source_evidence=[1]))
            changed_provenance(lambda row: row['knowledge_impact'].update(schema_version=99))
            escaped = copy.deepcopy(binding)
            escaped['manifest'] = self.ref('srs.md')
            with self.assertRaises(ValueError): ba.validate_candidate(candidate_for(escaped),self.root,foundation_authenticator=auth)
            receipt_path = self.root/binding['approval']['path']
            receipt_path.write_bytes(original_receipt+b'\nchanged')
            with self.assertRaises(ValueError): ba.validate_candidate(valid,self.root,foundation_authenticator=auth)
            receipt_path.write_bytes(original_receipt)
        finally:
            foundation.doCleanups()

    def test_nested_greenfield_foundation_approval_is_context_only(self):
        foundation = foundation_tests.FoundationTests('test_synthetic_greenfield_approved_target_requires_exact_trusted_receipt')
        foundation.setUp()
        try:
            foundation.greenfield()
            run = foundation.start()
            topology, policy = foundation.config()
            inputs = foundation.inputs()
            inputs['sections']['solution_strategy']['evidence'] = 'APPROVED_TARGET'
            data = foundation_tests.w.candidate_manifest(foundation.root,run,topology,policy,'foundation','R1',**inputs)
            approval, auth = foundation.receipt(data)
            foundation_tests.w.prepare(foundation.root,'run-1','foundation','R1',approval=approval,human_actor_authenticator=auth,**inputs)
            foundation_tests.w.accept(foundation.root,'run-1',approval,human_actor_authenticator=auth)
            foundation_tests.w.promote(foundation.root,'run-1','docs/foundation/R1.json','docs/foundation/R1.provenance.json',human_actor_authenticator=auth)
            shutil.copytree(foundation.root,self.root/'foundation-project')
            binding = {'root':'foundation-project','manifest':self.ref('foundation-project/docs/foundation/R1.json'),
                       'provenance':self.ref('foundation-project/docs/foundation/R1.provenance.json'),
                       'approval':self.ref('foundation-project/'+approval['path'])}
            candidate = copy.deepcopy(self.candidate)
            candidate.update(revision='R2',project_foundation=binding)
            candidate['semantic_sha256'] = ba.candidate_hash(candidate)
            result = ba.validate_candidate(candidate,self.root,foundation_authenticator=auth)
            self.assertEqual(result['status'],'VALIDATED')
            self.assertFalse(result['human_approval'])
            proof_path = self.root/binding['provenance']['path']
            proof_bytes = proof_path.read_bytes()
            proof_path.write_bytes(proof_bytes+b'\nchanged')
            tampered = copy.deepcopy(candidate)
            tampered['project_foundation']['provenance'] = self.ref(binding['provenance']['path'])
            tampered['semantic_sha256'] = ba.candidate_hash(tampered)
            with self.assertRaises(ValueError): ba.validate_candidate(tampered,self.root,foundation_authenticator=auth)
            proof_path.write_bytes(proof_bytes)
            receipt_path = self.root/binding['approval']['path']
            receipt_bytes = receipt_path.read_bytes()
            receipt_path.write_bytes(receipt_bytes+b'\nchanged')
            tampered = copy.deepcopy(candidate)
            tampered['project_foundation']['approval'] = self.ref(binding['approval']['path'])
            tampered['semantic_sha256'] = ba.candidate_hash(tampered)
            with self.assertRaises(ValueError): ba.validate_candidate(tampered,self.root,foundation_authenticator=auth)
            receipt_path.write_bytes(receipt_bytes)
            candidate = ba.make_candidate(self.root,feature=candidate['feature'],baseline_id='BA-1',revision='R2',
                sources=self.sources,business_identities=candidate['business_identities'],knowledge=knowledge_impact(),
                project_foundation=binding,foundation_authenticator=auth)
            state = ba.select_candidate(ba.new_state(candidate['feature'],'GREENFIELD'),self.publish(candidate),self.root,
                foundation_authenticator=auth)
            state = ba.advance(ba.advance(state,'VALIDATE',self.root,foundation_authenticator=auth),
                'REQUEST_REVIEW',self.root,foundation_authenticator=auth)
            self.assertEqual(state['lifecycle'],'HUMAN_REVIEW')
            with self.assertRaises(ValueError): ba.make_handoff(state,self.root,foundation_authenticator=auth)
        finally:
            foundation.doCleanups()

    def test_foundation_refresh_binding_requires_matching_prior_receipt(self):
        foundation = foundation_tests.FoundationTests('test_synthetic_brownfield_acceptance_preserves_current_inferred_unknown')
        foundation.setUp()
        try:
            previous, _, _ = foundation.promoted()
            previous_ref = foundation_tests.w.exact_ref(foundation.root,'docs/foundation/R1.json','R1')
            state = foundation.start('refresh',mode='FOUNDATION_REFRESH')
            topology, policy = foundation.config()
            inputs = foundation.inputs()
            inputs['sections']['runtime_view']['evidence'] = 'APPROVED_TARGET'
            data = foundation_tests.w.candidate_manifest(foundation.root,state,topology,policy,'foundation','R2',**inputs)
            approval, auth = foundation.receipt(data,previous=previous)
            foundation_tests.w.prepare(foundation.root,'refresh','foundation','R2',previous_ref=previous_ref,
                approval=approval,human_actor_authenticator=auth,**inputs)
            foundation_tests.w.accept(foundation.root,'refresh',approval,human_actor_authenticator=auth)
            foundation_tests.w.promote(foundation.root,'refresh','docs/foundation/R2.json',
                'docs/foundation/R2.provenance.json',human_actor_authenticator=auth)
            shutil.copytree(foundation.root,self.root/'foundation-project')
            binding = {'root':'foundation-project',
                'manifest':self.ref('foundation-project/docs/foundation/R2.json','R2'),
                'provenance':self.ref('foundation-project/docs/foundation/R2.provenance.json','R2'),
                'approval':self.ref('foundation-project/'+approval['path'],'R2'),
                'previous':self.ref('foundation-project/docs/foundation/R1.json')}
            candidate = copy.deepcopy(self.candidate)
            candidate['project_foundation'] = binding
            candidate['semantic_sha256'] = ba.candidate_hash(candidate)
            self.assertEqual(ba.validate_candidate(candidate,self.root,foundation_authenticator=auth)['status'],'VALIDATED')
            for prior in (None,self.ref('foundation-project/docs/foundation/R2.json')):
                changed = copy.deepcopy(candidate)
                if prior is None: changed['project_foundation'].pop('previous')
                else: changed['project_foundation']['previous'] = prior
                changed['semantic_sha256'] = ba.candidate_hash(changed)
                with self.subTest(previous=prior), self.assertRaises(ValueError):
                    ba.validate_candidate(changed,self.root,foundation_authenticator=auth)
        finally:
            foundation.doCleanups()

    def test_continue_answer_generation_and_validation_do_not_approve(self):
        for action in ('CONTINUE','ANSWER','GENERATED'):
            with self.subTest(action=action):
                result = ba.advance(self.state, action, self.root)
                self.assertEqual(result['lifecycle'], 'DRAFT')
                self.assertNotIn('approval', result['gates'])
        result = ba.advance(self.state, 'VALIDATE', self.root)
        self.assertEqual(result['lifecycle'], 'VALIDATED')
        with self.assertRaises(ValueError): ba.make_handoff(result, self.root)

    def test_approval_requires_human_review_and_host_authentication(self):
        approval, auth = self.host_receipt()
        with self.assertRaises(ValueError): ba.advance(self.state, 'APPROVE', self.root, approval=approval, human_actor_authenticator=auth)
        state = ba.advance(ba.advance(self.state, 'VALIDATE', self.root), 'REQUEST_REVIEW', self.root)
        for authenticator in (None, lambda *_: False, lambda *_: 1):
            with self.subTest(auth=authenticator), self.assertRaises(ValueError):
                ba.advance(state, 'APPROVE', self.root, approval=approval, human_actor_authenticator=authenticator)
        approval, auth = self.host_receipt(actor='agent')
        with self.assertRaises(ValueError): ba.advance(state, 'APPROVE', self.root, approval=approval, human_actor_authenticator=auth)

    def test_each_authority_byte_change_invalidates_handoff(self):
        state, auth = self.approved()
        handoff = ba.make_handoff(state, self.root, human_actor_authenticator=auth)
        for name in ('srs.md','business-rules.md','decisions.json','receipt.json','human-approval.txt','candidates/R1.json'):
            with self.subTest(name=name):
                path = self.root/name
                original = path.read_bytes()
                path.write_bytes(original+b'\nchanged')
                with self.assertRaises(ValueError): ba.validate_handoff(handoff, self.root, human_actor_authenticator=auth)
                path.write_bytes(original)

    def test_receipt_r1_cannot_approve_r2(self):
        approval, auth = self.host_receipt()
        candidate = copy.deepcopy(self.candidate)
        candidate['revision'] = 'R2'
        candidate['previous_baseline'] = self.candidate_ref
        candidate['semantic_sha256'] = ba.candidate_hash(candidate)
        state = ba.select_candidate(self.state, self.publish(candidate), self.root)
        state = ba.advance(ba.advance(state, 'VALIDATE', self.root), 'REQUEST_REVIEW', self.root)
        with self.assertRaises(ValueError): ba.advance(state, 'APPROVE', self.root, approval=approval, human_actor_authenticator=auth)

    def test_candidate_edit_requires_new_revision_and_clears_approval(self):
        state, _ = self.approved()
        changed = copy.deepcopy(self.candidate)
        changed['non_blocking'] = ['wording follow-up']
        changed['semantic_sha256'] = ba.candidate_hash(changed)
        self.put('changed.json', changed)
        with self.assertRaises(ValueError): ba.select_candidate(state, self.ref('changed.json'), self.root)
        changed['revision'] = 'R2'
        changed['previous_baseline'] = self.candidate_ref
        changed['semantic_sha256'] = ba.candidate_hash(changed)
        result = ba.select_candidate(state, self.publish(changed), self.root)
        self.assertEqual(result['lifecycle'], 'DRAFT')
        self.assertNotIn('approval', result['gates'])
        self.assertEqual(result['history'][:len(state['history'])], state['history'])

    def test_review_is_read_only_and_reject_returns_draft(self):
        before = copy.deepcopy(self.state)
        self.assertEqual(ba.advance(self.state, 'REVIEW', self.root), before)
        state, _ = self.approved()
        frozen = (self.root/'candidates/R1.json').read_bytes()
        for action in ('REJECT','REQUEST_CHANGES'):
            result = ba.advance(state, action, self.root)
            self.assertEqual(result['lifecycle'], 'DRAFT')
            self.assertNotIn('approval', result['gates'])
            self.assertEqual((self.root/'candidates/R1.json').read_bytes(), frozen)

    def test_duplicate_business_ids_fail(self):
        for name, text in [('business-rules.md','\n## BR-001 duplicate\nOther rule'), ('srs.md','\n## FR-001 duplicate\nOther behavior')]:
            with self.subTest(name=name):
                path = self.root/name
                original = path.read_bytes()
                path.write_bytes(original+text.encode())
                sources = copy.deepcopy(self.sources)
                sources['srs' if name == 'srs.md' else 'business_rules'] = self.ref(name)
                with self.assertRaises(ValueError):
                    ba.make_candidate(self.root, feature=self.candidate['feature'], baseline_id='BA-1', revision='R2',
                        sources=sources, business_identities=self.candidate['business_identities'], knowledge=knowledge_impact())
                path.write_bytes(original)

    def test_baref_is_locator_only_and_cannot_be_coverage(self):
        (self.root/'srs.md').write_text('# Context\nA structural description.\n', encoding='utf-8')
        self.sources['srs'] = self.ref('srs.md')
        decisions = self.load('decisions.json')
        decisions['decisions'][0]['affected_ids'] = ['BR-001']
        decisions['decisions'][0]['implemented_sources']['srs'] = self.sources['srs']
        self.put('decisions.json', decisions)
        self.sources['decisions'] = self.ref('decisions.json')
        candidate = ba.make_candidate(self.root, feature=self.candidate['feature'], baseline_id='BA-1', revision='R2',
            sources=self.sources, business_identities=self.candidate['business_identities'][:1], knowledge=knowledge_impact())
        self.assertEqual(candidate['coverage_ids'], ['BR-001'])
        candidate['coverage_ids'].append('BAREF:SRS:001')
        candidate['semantic_sha256'] = ba.candidate_hash(candidate)
        with self.assertRaises(ValueError): ba.validate_candidate(candidate, self.root)

    def test_blocking_unknown_proposed_and_contradiction_prevent_review(self):
        for field in ('blocking','contradictions'):
            changed = copy.deepcopy(self.candidate)
            changed[field] = ['unresolved question']
            changed['semantic_sha256'] = ba.candidate_hash(changed)
            with self.subTest(field=field), self.assertRaises(ValueError): ba.validate_candidate(changed, self.root)
        for status in ('PROPOSED','UNKNOWN'):
            decisions = self.load('decisions.json')
            decisions['decisions'][0]['status'] = status
            self.put('decisions.json', decisions)
            changed = copy.deepcopy(self.candidate)
            changed['sources']['decisions'] = self.ref('decisions.json')
            changed['semantic_sha256'] = ba.candidate_hash(changed)
            with self.subTest(status=status), self.assertRaises(ValueError): ba.validate_candidate(changed, self.root)

    def test_new_decision_cannot_leave_old_srs_authoritative(self):
        decisions = self.load('decisions.json')
        decisions['decisions'][0]['implemented_sources']['srs']['sha256'] = '0'*64
        self.put('decisions.json', decisions)
        changed = copy.deepcopy(self.candidate)
        changed['sources']['decisions'] = self.ref('decisions.json')
        changed['semantic_sha256'] = ba.candidate_hash(changed)
        with self.assertRaises(ValueError): ba.validate_candidate(changed, self.root)

    def test_ids_cannot_change_identity_or_reuse_retired_ids(self):
        for mutation in ('semantic_key','retired'):
            old = copy.deepcopy(self.candidate)
            changed = copy.deepcopy(self.candidate)
            changed['revision'] = 'R2'
            if mutation == 'semantic_key': changed['business_identities'][0]['semantic_key'] = 'different-business-item'
            else: old['business_identities'][0]['status'] = 'RETIRED'
            changed['semantic_sha256'] = ba.candidate_hash(changed)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): ba.validate_identity_transition(old, changed)

    def test_technical_design_fields_and_receipt_status_shortcuts_fail(self):
        state, auth = self.approved()
        handoff = ba.make_handoff(state, self.root, human_actor_authenticator=auth)
        for key in ('frontend_owner','backend_owner','service_owner','implementation_owner','api_design','db_design',
                    'event_schema','locking_strategy','transaction_strategy','architecture_decision','service_boundaries'):
            changed = copy.deepcopy(handoff)
            changed[key] = 'a technical solution'
            with self.subTest(key=key), self.assertRaises(ValueError): ba.validate_handoff(changed, self.root, human_actor_authenticator=auth)
        handoff['ba_baseline']['status'] = 'APPROVED_FOR_ENGINEERING'
        with self.assertRaises(ValueError): ba.validate_handoff(handoff, self.root, human_actor_authenticator=auth)

    def test_frozen_state_requires_exact_candidate_and_receipt(self):
        state, auth = self.approved()
        ba.validate_state(state, self.root, human_actor_authenticator=auth)
        for mutate in ('revision','knowledge','approval','input'):
            changed = copy.deepcopy(state)
            if mutate == 'revision': changed['candidate_revision'] = 'R2'
            if mutate == 'knowledge': changed['knowledge_impact']['areas']['testing']['affected'] = True
            if mutate == 'approval': changed['gates'] = {}
            if mutate == 'input': changed['authoritative_inputs'] = []
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): ba.validate_state(changed, self.root, human_actor_authenticator=auth)

    def test_unknown_schema_fields_secrets_evidence_and_hash_fail_closed(self):
        for key, value in [('schema_version',99), ('extra',True), ('password','private'), ('evidence',[{'label':'FACT'}]), ('semantic_sha256','0'*64)]:
            changed = copy.deepcopy(self.candidate)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): ba.validate_candidate(changed, self.root)
        changed = copy.deepcopy(self.state)
        changed['schema_version'] = 99
        self.assertTrue(compat.validate_state_data(changed))

    def test_ux_approval_and_agent_role_are_not_ba_approval(self):
        state = ba.advance(ba.advance(self.state,'VALIDATE',self.root),'REQUEST_REVIEW',self.root)
        approval, _ = self.host_receipt()
        for field, value in [('artifact_type','UX_BASELINE'),('actor_role','AGENT'),('decision','ANSWER'),('decision','CONTINUE')]:
            receipt = self.load('receipt.json')
            original = copy.deepcopy(receipt)
            receipt[field] = value
            self.put('receipt.json',receipt)
            with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                ba.advance(state,'APPROVE',self.root,approval=self.ref('receipt.json'),human_actor_authenticator=lambda *_: True)
            self.put('receipt.json',original)

    def test_host_records_named_answer_without_baseline_approval(self):
        before = self.load('decisions.json')
        answer = copy.deepcopy(before['decisions'][0])
        answer.update(id='DEC-002', text='Revised eligibility decision.', supersedes=['DEC-001'], implemented_sources={})
        expected = copy.deepcopy(answer)
        with self.assertRaises(ValueError): ba.record_answer(before,answer,self.root,human_actor_authenticator=lambda *_: False)
        after = ba.record_answer(before,answer,self.root,human_actor_authenticator=lambda actor,row: actor == 'synthetic-human' and row == expected)
        self.assertEqual(after['decisions'][0]['status'],'SUPERSEDED')
        self.assertEqual(after['decisions'][1]['status'],'CONFIRMED')
        self.assertEqual(before['decisions'][0]['status'],'CONFIRMED')
        self.put('decisions.json',after)
        changed = copy.deepcopy(self.candidate)
        changed['sources']['decisions'] = self.ref('decisions.json')
        changed['semantic_sha256'] = ba.candidate_hash(changed)
        with self.assertRaises(ValueError): ba.validate_candidate(changed,self.root)

    def test_named_answer_closes_only_its_question_and_blocks_old_candidate(self):
        state = copy.deepcopy(self.state)
        state['pending'] = ['eligibility','delivery-outcome']
        decisions = self.load('decisions.json')
        answer = copy.deepcopy(decisions['decisions'][0])
        answer.update(id='DEC-002',supersedes=['DEC-001'],text='Updated Human eligibility answer.')
        expected = copy.deepcopy(answer)
        auth = lambda actor,row: actor == 'synthetic-human' and row == expected
        decisions = ba.record_answer(decisions,answer,self.root,human_actor_authenticator=auth)
        self.put('latest-decisions.json',decisions)
        ref = self.ref('latest-decisions.json','D2')
        resolved = ba.resolve_question(state,'eligibility',ref,self.root,human_actor_authenticator=auth)
        self.assertEqual(resolved['pending'],['delivery-outcome'])
        self.assertEqual(resolved['lifecycle'],'DRAFT')
        self.assertNotIn('approval',resolved['gates'])
        self.put('state.json',state)
        ba.save_state(self.root,'state.json',state,resolved,human_actor_authenticator=auth)
        with self.assertRaises(ValueError):
            ba.resolve_question(state,'unrelated-question',ref,self.root,human_actor_authenticator=auth)
        # Even after other questions close, old candidate cannot ignore this new decision.
        resolved['pending'] = []
        with self.assertRaises(ValueError): ba.advance(resolved,'VALIDATE',self.root)
        with self.assertRaises(ValueError): ba.select_candidate(resolved,self.candidate_ref,self.root)

    def test_named_answer_requires_authenticated_human_and_preserves_review(self):
        state = copy.deepcopy(self.state)
        state['pending'] = ['eligibility']
        ref = self.ref('decisions.json')
        with self.assertRaises(ValueError):
            ba.resolve_question(state,'eligibility',ref,self.root,human_actor_authenticator=lambda *_: False)
        state['operation'] = 'REVIEW'
        with self.assertRaises(ValueError):
            ba.resolve_question(state,'eligibility',ref,self.root,human_actor_authenticator=lambda *_: True)

    def test_candidate_technical_design_and_derived_authority_are_rejected(self):
        for name in ('business-rules.md','srs.md'):
            original = (self.root/name).read_bytes()
            (self.root/name).write_bytes(original+b'\nfrontend_owner: portal\n')
            candidate = copy.deepcopy(self.candidate)
            candidate['sources']['srs' if name == 'srs.md' else 'business_rules'] = self.ref(name)
            candidate['semantic_sha256'] = ba.candidate_hash(candidate)
            with self.subTest(name=name), self.assertRaises(ValueError): ba.validate_candidate(candidate,self.root)
            (self.root/name).write_bytes(original)
        shutil.copyfile(self.root/'srs.md',self.root/'srs.docx')
        candidate = copy.deepcopy(self.candidate)
        candidate['sources']['srs'] = self.ref('srs.docx')
        candidate['semantic_sha256'] = ba.candidate_hash(candidate)
        with self.assertRaises(ValueError): ba.validate_candidate(candidate,self.root)

    def test_candidate_immutable_replay_and_changed_bytes_require_new_revision(self):
        self.assertEqual(self.publish(self.candidate),self.candidate_ref)
        changed = copy.deepcopy(self.candidate)
        changed['non_blocking'] = ['follow-up']
        changed['semantic_sha256'] = ba.candidate_hash(changed)
        with self.assertRaises(ValueError): self.publish(changed)
        self.assertEqual(self.load('candidates/R1.json'),self.candidate)

    def test_revision_receipt_binds_prior_identity(self):
        candidate = copy.deepcopy(self.candidate)
        candidate.update(revision='R2',previous_baseline=self.candidate_ref)
        candidate['semantic_sha256'] = ba.candidate_hash(candidate)
        ref = self.publish(candidate)
        state = ba.select_candidate(self.state,ref,self.root)
        state = ba.advance(ba.advance(state,'VALIDATE',self.root),'REQUEST_REVIEW',self.root)
        approval, auth = self.host_receipt(candidate,ref)
        approved = ba.advance(state,'APPROVE',self.root,approval=approval,human_actor_authenticator=auth)
        self.assertEqual(approved['candidate_revision'],'R2')
        receipt = self.load('receipt.json')
        receipt['previous_baseline']['revision'] = 'WRONG'
        self.put('receipt.json',receipt)
        with self.assertRaises(ValueError):
            ba.advance(state,'APPROVE',self.root,approval=self.ref('receipt.json','R2'),human_actor_authenticator=lambda *_: True)

    def test_legacy_readers_never_fabricate_vnext_approval(self):
        legacy = json.loads((ROOT/'ba-workflow/templates/workflow-state.json').read_text())
        if legacy['schema_version'] != 1:
            legacy = {'schema_version':1,'feature':{},'operation':'REVIEW','stage':'APPROVED_FOR_ENGINEERING',
                      'artifacts':{},'gates':{},'pending':[],'source_of_truth':{},'history':[]}
        legacy['stage'] = 'APPROVED_FOR_ENGINEERING'
        result = compat.read_state(legacy, self.root)
        self.assertEqual(result['mode'], 'LEGACY_COMPAT')
        self.assertFalse(result['vnext_approval'])
        with self.assertRaises(ValueError): ba.advance(legacy, 'APPROVE', self.root)

    def test_direct_cli_v1_v2_compatibility_and_no_cli_authentication_bypass(self):
        self.put('state.json', self.state)
        for script in ('ba-workflow/scripts/validate-state.py','tooling/lib/validate-state.py'):
            result = subprocess.run([sys.executable, str(ROOT/script), str(self.root/'state.json')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        state, auth = self.approved()
        self.put('handoff.json', ba.make_handoff(state, self.root, human_actor_authenticator=auth))
        result = subprocess.run([sys.executable, str(ROOT/'ba-workflow/scripts/validate-handoff.py'), str(self.root/'handoff.json')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('authenticated', result.stderr)

    def test_installed_ba_vnext_uses_colocated_core_and_host_gate(self):
        installed = self.root/'installed/ba-workflow'
        shutil.copytree(ROOT/'ba-workflow',installed)
        state, _ = self.approved()
        self.put('approved-state.json',state)
        # Synthetic external test host verifies its explicitly supplied known receipt.
        expected_receipt = self.load('receipt.json')
        script = """import json, pathlib, sys
sys.path.insert(0,sys.argv[1])
import ba_vnext as ba
import shared.sdlc.schema as schema
assert 'shared-sdlc-core.zip' in schema.__file__
root=pathlib.Path(sys.argv[2])
state=json.loads((root/'approved-state.json').read_text())
expected=json.loads(sys.argv[3])
auth=lambda actor,receipt: actor=='synthetic-human' and receipt==expected
handoff=ba.make_handoff(state,root,human_actor_authenticator=auth)
assert ba.validate_handoff(handoff,root,human_actor_authenticator=auth)['human_approval'] is True
print('INSTALLED_VNEXT_PASS')
"""
        result = subprocess.run([sys.executable,'-E','-c',script,str(installed/'scripts'),str(self.root),json.dumps(expected_receipt)],
            cwd=self.root,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('INSTALLED_VNEXT_PASS',result.stdout)

    def test_path_traversal_and_duplicate_json_keys_fail_closed(self):
        with self.assertRaises(ValueError): ba.publish_candidate(self.root,'../outside.json',self.candidate)
        self.assertFalse((self.root.parent/'outside.json').exists())
        self.assertTrue(compat.validate_handoff_text('{"schema_version":2,"schema_version":1}'))
        bad = copy.deepcopy(self.candidate_ref)
        bad['path'] = '../candidates/R1.json'
        with self.assertRaises(ValueError): ba.read_baseline(bad,self.root)

    def test_runtime_history_cannot_skip_review_or_change_prior_entries(self):
        state, auth = self.approved()
        changed = copy.deepcopy(state)
        changed['history'][-1]['from'] = 'VALIDATED'
        with self.assertRaises(ValueError): ba.validate_state(changed,self.root,human_actor_authenticator=auth)
        reviewed = copy.deepcopy(self.state)
        reviewed['operation'] = 'REVIEW'
        with self.assertRaises(ValueError): ba.select_candidate(reviewed,self.candidate_ref,self.root)
        with self.assertRaises(ValueError): ba.advance(reviewed,'VALIDATE',self.root)

    def test_edit_only_selected_scope_and_refresh_derived_routing(self):
        with self.assertRaises(ValueError): ba.new_state(self.candidate['feature'],'GREENFIELD','EDIT')
        state = copy.deepcopy(self.state)
        state.update(operation='EDIT',edit_scope=['non_blocking'])
        state['artifacts']['docx'] = self.ref('srs.md')
        changed = copy.deepcopy(self.candidate)
        changed.update(revision='R2',previous_baseline=self.candidate_ref,non_blocking=['follow-up'])
        changed['semantic_sha256'] = ba.candidate_hash(changed)
        new = ba.select_candidate(state,self.publish(changed),self.root)
        self.assertNotIn('docx',new['artifacts'])
        wrong = copy.deepcopy(self.candidate)
        wrong.update(revision='R3',previous_baseline=self.candidate_ref,knowledge_impact=knowledge_impact())
        wrong['knowledge_impact']['areas']['domain']['affected'] = True
        wrong['semantic_sha256'] = ba.candidate_hash(wrong)
        with self.assertRaises(ValueError): ba.select_candidate(state,self.publish(wrong),self.root)

    def test_exact_handoff_rechecks_bytes_after_host_authentication(self):
        state, auth = self.approved()
        handoff = ba.make_handoff(state,self.root,human_actor_authenticator=auth)
        def drifting_host(actor,receipt):
            accepted = auth(actor,receipt)
            (self.root/'srs.md').write_bytes((self.root/'srs.md').read_bytes()+b'\nchanged during authentication')
            return accepted
        with self.assertRaises(ValueError): ba.validate_handoff(handoff,self.root,human_actor_authenticator=drifting_host)

    def test_state_persistence_preserves_history_and_rejects_stale_writer(self):
        self.put('state.json', self.state)
        updated = ba.advance(self.state, 'VALIDATE', self.root)
        ba.save_state(self.root, 'state.json', self.state, updated)
        self.assertEqual(self.load('state.json'), updated)
        with self.assertRaises(ValueError): ba.save_state(self.root, 'state.json', self.state, updated)
        tampered = copy.deepcopy(updated)
        tampered['history'] = []
        with self.assertRaises(ValueError): ba.save_state(self.root, 'state.json', updated, tampered)


if __name__ == '__main__':
    unittest.main()
