"""Neutral runtime acceptance: real repositories, commits and native checks.

The only synthetic boundary is the trusted Human host, which authenticates an
exact receipt supplied by the fixture. Workflow choices never authenticate it.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tooling.lib import dev_vnext as contracts
from tooling.lib.dev_vnext_runtime import DevRuntime
from tooling.tests import test_ba_vnext as ba_tests


NATIVE_CHECK = '''import ast
import importlib.util
import pathlib
import py_compile
import subprocess
import sys

path = pathlib.Path('src/module.py')
source = path.read_text(encoding='utf-8')
category = sys.argv[1]
if category == 'BUILD':
    py_compile.compile(str(path), doraise=True)
elif category == 'STATIC':
    assert isinstance(ast.parse(source), ast.Module)
elif category == 'LINT':
    assert all(line == line.rstrip() for line in source.splitlines())
elif category == 'MODULE_LOCAL_INTEGRATION':
    subprocess.run([sys.executable, '-c', 'from src.module import result; assert result() == 2'], check=True)
else:
    spec = importlib.util.spec_from_file_location('module', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if category == 'TYPECHECK':
        assert isinstance(module.result(), int)
    else:
        assert module.result() == 2
print('NATIVE_CHECK_PASS:' + category)
'''


class RuntimeAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.ba = ba_tests.BAVNextTests('test_greenfield_exact_baseline_and_handoff')
        self.ba.setUp()
        self.addCleanup(self.ba.doCleanups)
        self.root = self.ba.root
        approved, self.ba_auth = self.ba.approved()
        self.handoff = ba_tests.ba.make_handoff(approved, self.root,
            human_actor_authenticator=self.ba_auth)
        self.ba.put('handoff.json', self.handoff)
        self.upstream = self.ba.ref('handoff.json')
        self.ba.put('review-evidence.json', {'scope':'one consolidated implementation review'})
        self.ba.put('maintenance-evidence.json', {'scope':'mechanical source formatting'})
        self.repositories = []
        self.repository_roots = {}
        self.add_repository('core')
        self.runtime = self.new_runtime()

    def new_runtime(self, technical_authenticator=None):
        return DevRuntime(self.root, ba_authenticator=self.ba_auth,
            technical_authenticator=technical_authenticator)

    def git(self, repo_id, *argv):
        process = subprocess.run(['git', '-C', str(self.repository_roots[repo_id]), *argv],
            capture_output=True, text=True, check=True)
        return process.stdout.strip()

    def add_repository(self, repo_id):
        root = self.root/'repositories'/repo_id
        (root/'src').mkdir(parents=True)
        (root/'tests').mkdir()
        (root/'src/module.py').write_text('def result():\n    return 1\n', encoding='utf-8')
        (root/'tests/check_native.py').write_text(NATIVE_CHECK, encoding='utf-8')
        (root/'.gitignore').write_text('__pycache__/\n', encoding='utf-8')
        self.repository_roots[repo_id] = str(root)
        self.git(repo_id, 'init', '--quiet')
        self.git(repo_id, 'config', 'user.name', 'Runtime Fixture')
        self.git(repo_id, 'config', 'user.email', 'runtime-fixture@example.invalid')
        self.git(repo_id, 'config', 'core.autocrlf', 'false')
        self.git(repo_id, 'add', '.')
        self.git(repo_id, 'commit', '--quiet', '-m', 'Neutral baseline')
        self.repositories.append({'id':repo_id, 'role':'IMPLEMENTATION',
            'base_revision':self.git(repo_id, 'rev-parse', 'HEAD'),
            'allowed_write_paths':['src', 'tests'], 'read_only_evidence_paths':[]})

    def request(self, *, maintenance=False, risk=None, run_id='RUN-1', checks=None):
        data = {'run_id':run_id, 'change_id':'CHANGE-1',
            'summary':'Implement neutral module result',
            'authority_mode':'TECHNICAL_MAINTENANCE' if maintenance else 'FEATURE_DELIVERY',
            'repositories':copy.deepcopy(self.repositories),
            'repository_roots':copy.deepcopy(self.repository_roots),
            'checks':copy.deepcopy(checks) if checks is not None else [{'name':category.lower(), 'repository_id':'core', 'category':category,
                'command':[sys.executable, 'tests/check_native.py', category]}
                for category in contracts.CHECK_CATEGORIES],
            'upstream':None if maintenance else self.upstream}
        if maintenance:
            data['maintenance'] = {'kind':'MECHANICAL', 'no_what_change':True,
                'evidence_refs':[self.ba.ref('maintenance-evidence.json')],
                'discovered_changes':[]}
        if risk is not None:
            data['risk'] = risk
        return data

    def impact_document(self, state):
        return {'schema_version':2, 'change_id':state['change_id'],
            'upstream_ref':state['upstream'],
            'repository_base_revisions':{r['id']:r['base_revision'] for r in state['repositories']},
            'affected_repositories':copy.deepcopy(state['repositories']),
            'affected_components':['neutral module'], 'affected_interfaces':[],
            'affected_data':[], 'dependencies':[], 'constraints':[],
            'risk':copy.deepcopy(state['risk']), 'technical_unknowns':[], 'upstream_gaps':[],
            'write_scope':{r['id']:r['allowed_write_paths'] for r in state['repositories']},
            'knowledge_impact':copy.deepcopy(self.handoff['knowledge_impact'])}

    def planned(self, *, high=False, material_ed=False, run_id='RUN-1', checks=None):
        risk = {'level':'HIGH_RISK', 'categories':['PUBLIC_API'], 'reasons':['public response boundary']} if high else None
        state = self.runtime.start(self.request(risk=risk, run_id=run_id, checks=checks))
        self.assertEqual(state['lifecycle'], 'INTAKE')
        state = self.runtime.validate_authority()
        self.assertEqual(state['lifecycle'], 'AUTHORITY_VALIDATED')
        state = self.runtime.impact(self.impact_document(state))
        self.assertEqual(state['lifecycle'], 'IMPACT_ANALYZED')
        (self.root/'technical-plan-input.md').write_text('Change only module HOW; upstream retains WHAT.\n', encoding='utf-8')
        (self.root/'technical-tasks-input.md').write_text('Implement result and run native checks.\n', encoding='utf-8')
        decisions = []
        if high or material_ed:
            decision = {'schema_version':2, 'id':'ED-001', 'change_id':'CHANGE-1',
                'topic':'Module response compatibility', 'authority_scope':'FEATURE_LOCAL',
                'category':'PUBLIC_API' if high else 'LOCAL_DESIGN',
                'decision':'Preserve approved module interface', 'status':'PROPOSED',
                'evidence_refs':[self.ba.ref('review-evidence.json')], 'upstream_refs':[self.upstream],
                'affected_repositories':['core'], 'affected_components':['neutral module'],
                'affected_interfaces':['module response'], 'affected_data':[],
                'alternatives':['new response version'], 'consequences':['existing call sites preserved'],
                'risk':'HIGH_RISK' if high else 'NORMAL', 'materiality':'MATERIAL',
                'approval_requirement':'HUMAN', 'supersedes':[], 'superseded_by':[]}
            self.ba.put('engineering-decision.json', decision)
            decisions = [self.ba.ref('engineering-decision.json')]
        state = self.runtime.plan('technical-plan-input.md', 'technical-tasks-input.md',
            decisions=decisions, revision='TECH-1')
        self.assertEqual(state['lifecycle'], 'TECHNICAL_PLANNED')
        return state

    def receipt(self, state, name='technical-receipt.json'):
        snapshot = state['artifacts']['snapshot']
        document = {'schema_version':2, 'artifact_type':'DEV_TECHNICAL_APPROVAL',
            'decision':'APPROVE', 'actor_id':'technical-human', 'actor_role':'TECH_LEAD',
            'recorded_at':'2026-10-04T10:00:00Z', 'run_id':state['run_id'],
            'change_id':state['change_id'], 'snapshot_revision':snapshot['revision'],
            'snapshot_sha256':snapshot['sha256'], 'snapshot_ref':snapshot,
            'decision_evidence_ref':self.ba.ref('review-evidence.json')}
        self.ba.put(name, document)
        expected = copy.deepcopy(document)
        authenticator = lambda actor, row: actor == 'technical-human' and row == expected
        return self.ba.ref(name, snapshot['revision']), authenticator

    def approve(self, state):
        receipt, auth = self.receipt(state)
        self.runtime = self.new_runtime(auth)
        self.runtime.bind_technical_approval(receipt)
        return self.runtime.implementation_ready()

    def implement(self, *, maintenance=False):
        self.runtime.begin_implementation()
        for row in self.repositories:
            repo_id = row['id']
            source = ('# Mechanical documentation correction.\n' if maintenance else '') + 'def result():\n    return 2\n'
            self.runtime.write_source(repo_id, 'src/module.py', source)
            self.git(repo_id, 'add', 'src/module.py')
            self.git(repo_id, 'commit', '--quiet', '-m', 'Implement neutral module')

    def coverage(self):
        code = self.ba.ref('repositories/core/src/module.py')
        test = self.ba.ref('repositories/core/tests/check_native.py')
        return [{'id':identity, 'status':'COVERED', 'code_refs':[code], 'test_refs':[test]}
                for identity in ('BR-001', 'FR-001')]

    def finish(self, *, maintenance=False, coverage=None):
        if not maintenance:
            self.runtime.record_review([self.ba.ref('review-evidence.json')])
        self.runtime.verify()
        self.assertEqual(self.runtime.load()['lifecycle'], 'VERIFYING')
        if not maintenance:
            self.assertIn('ENGINEERING_REVIEW', [event['to'] for event in self.runtime.load()['history']])
        return self.runtime.finalize([] if maintenance else (coverage if coverage is not None else self.coverage()))

    def test_normal_full_runtime_path_keeps_ba_authority_bytes_unchanged(self):
        protected = [self.upstream, self.handoff['ba_baseline']['manifest'],
            self.handoff['approval_receipt'], *self.handoff['authoritative_sources'].values(),
            self.ba.ref('human-answer.txt'), self.ba.ref('human-approval.txt')]
        before = {ref['path']:(self.root/ref['path']).read_bytes() for ref in protected}
        self.planned()
        self.runtime.implementation_ready()
        self.assertEqual(self.runtime.load()['lifecycle'], 'IMPLEMENTATION_READY')
        self.implement()
        self.assertEqual(self.runtime.load()['lifecycle'], 'IMPLEMENTING')
        self.runtime = self.new_runtime()  # Crash/resume uses persisted state only.
        handoff = self.finish()
        self.assertEqual(handoff['state'], 'READY_FOR_TEST')
        self.assertEqual(self.runtime.load()['lifecycle'], 'READY_FOR_TEST')
        self.assertEqual(handoff['review']['budget']['full_reviews'], 1)
        self.assertEqual([row['id'] for row in handoff['requirements_coverage']], ['BR-001', 'FR-001'])
        self.assertEqual(handoff['repository_revisions'], {'core':self.git('core', 'rev-parse', 'HEAD')})
        checks = handoff['engineering_verification']['checks']
        self.assertEqual({row['category'] for row in checks}, set(contracts.CHECK_CATEGORIES))
        for row in checks:
            self.assertEqual((row['status'], row['exit_code']), ('PASS', 0))
            contracts._ref(row['evidence_ref'], self.root)
            self.assertIn('NATIVE_CHECK_PASS', (self.root/row['evidence_ref']['path']).read_text(encoding='utf-8'))
        self.assertEqual(before, {path:(self.root/path).read_bytes() for path in before})
        self.assertEqual(list((self.root/'.devkit').rglob('spec.md')), [])
        contracts.validate_handoff(handoff, self.root, ba_authenticator=self.ba_auth)

    def test_high_risk_rejects_fake_and_speckit_only_approval_then_exact_gate_works(self):
        state = self.planned(high=True)
        with self.assertRaises(ValueError):
            self.runtime.implementation_ready()
        self.ba.put('speckit-choice.json', {'choice':'approve', 'resolved':True})
        with self.assertRaises(ValueError):
            self.runtime.bind_technical_approval(self.ba.ref('speckit-choice.json'))
        receipt, auth = self.receipt(state)
        for authenticator in (None, lambda *_:False):
            with self.subTest(authenticator=authenticator), self.assertRaises(ValueError):
                self.new_runtime(authenticator).bind_technical_approval(receipt)
        replay = json.loads((self.root/receipt['path']).read_text())
        replay['run_id'] = 'RUN-OTHER'
        self.ba.put('replayed-receipt.json', replay)
        with self.assertRaises(ValueError):
            self.new_runtime(lambda *_:True).bind_technical_approval(self.ba.ref('replayed-receipt.json'))
        self.runtime = self.new_runtime(auth)
        self.runtime.bind_technical_approval(receipt)
        self.runtime.implementation_ready()
        snapshot = json.loads((self.root/state['artifacts']['snapshot']['path']).read_text())
        bound_refs = [state['artifacts']['snapshot'], snapshot['dev_plan'], snapshot['dev_tasks'],
            snapshot['engineering_impact'], *snapshot['engineering_decisions'], receipt]
        for ref in bound_refs:
            with self.subTest(drift=ref['path']):
                path = self.root/ref['path']
                original = path.read_bytes()
                path.write_bytes(original+b'\n')
                try:
                    with self.assertRaises(ValueError):
                        self.new_runtime(auth).write_source('core', 'src/module.py', 'unauthorized drift')
                    self.assertEqual((Path(self.repository_roots['core'])/'src/module.py').read_text(), 'def result():\n    return 1\n')
                finally:
                    path.write_bytes(original)
        self.implement()
        self.assertEqual(self.finish()['state'], 'READY_FOR_TEST')

    def test_normal_risk_with_active_material_ed_still_requires_whole_snapshot_gate(self):
        state = self.planned(material_ed=True)
        self.assertEqual(state['risk']['level'], 'NORMAL')
        with self.assertRaises(ValueError):
            self.runtime.implementation_ready()
        self.approve(state)
        self.implement()
        self.assertEqual(self.finish()['state'], 'READY_FOR_TEST')

    def test_risk_escalation_discards_gate_and_rejects_stale_receipt_replay(self):
        state = self.planned(high=True)
        stale_receipt, old_auth = self.receipt(state)
        self.runtime = self.new_runtime(old_auth)
        self.runtime.bind_technical_approval(stale_receipt)
        self.runtime.implementation_ready()
        risk = {'level':'HIGH_RISK', 'categories':['PUBLIC_API', 'SECURITY'],
            'reasons':['new security boundary discovered']}
        escalated = self.runtime.escalate_risk(risk)
        self.assertEqual(escalated['lifecycle'], 'NEEDS_REPLAN')
        self.assertEqual(escalated['gates'], {})
        with self.assertRaises(ValueError):
            self.runtime.write_source('core', 'src/module.py', 'stale authorization')
        with self.assertRaises(ValueError):
            self.runtime.escalate_risk({'level':'NORMAL', 'categories':[], 'reasons':[]})
        state = self.runtime.replan()
        self.assertEqual(state['lifecycle'], 'AUTHORITY_VALIDATED')
        state = self.runtime.impact(self.impact_document(state))
        state = self.runtime.plan('technical-plan-input.md', 'technical-tasks-input.md',
            decisions=[self.ba.ref('engineering-decision.json')], revision='TECH-2')
        with self.assertRaises(ValueError):
            self.runtime.bind_technical_approval(stale_receipt)
        with self.assertRaises(ValueError):
            self.runtime.implementation_ready()
        receipt, auth = self.receipt(state, 'technical-receipt-r2.json')
        self.runtime = self.new_runtime(auth)
        self.runtime.bind_technical_approval(receipt)
        self.assertEqual(self.runtime.implementation_ready()['lifecycle'], 'IMPLEMENTATION_READY')

    def test_gap_blocks_writes_and_resume_requires_reapproved_previous_baseline(self):
        state = self.planned(high=True)
        self.approve(state)
        gap = {'schema_version':2, 'gap_id':'GAP-001', 'finding_kind':'SPEC_GAP',
            'feature_id':'FEATURE-1', 'engineering_handoff_ref':self.upstream,
            'affected_business_ids':['FR-001'], 'evidence_refs':[self.ba.ref('review-evidence.json')],
            'question':'Which approved outcome applies?', 'blocking_scope':{'core':['src']},
            'discovered_at':'2026-10-04T10:00:00Z', 'status':'OPEN'}
        blocked = self.runtime.raise_gap(gap)
        self.assertEqual(blocked['lifecycle'], 'UPSTREAM_GAP')
        contracts.validate_gap(json.loads((self.root/blocked['engineering_gap']['gap_ref']['path']).read_text()),
            self.root, required_ids=['BR-001', 'FR-001'])
        with self.assertRaises(ValueError):
            self.runtime.write_source('core', 'src/module.py', 'blocked')
        with self.assertRaises(ValueError):
            self.runtime.resume_gap(self.upstream, self.ba.ref('review-evidence.json'))
        old_approval = (self.root/'receipt.json').read_bytes()
        old_auth = self.ba_auth
        replacement = copy.deepcopy(self.ba.candidate)
        replacement.update(revision='R2', previous_baseline=self.ba.candidate_ref)
        replacement['semantic_sha256'] = ba_tests.ba.candidate_hash(replacement)
        self.ba.candidate = replacement
        self.ba.candidate_ref = self.ba.publish(replacement)
        self.ba.state = ba_tests.ba.select_candidate(ba_tests.ba.new_state(replacement['feature'], 'GREENFIELD'),
            self.ba.candidate_ref, self.root)
        approved, replacement_auth = self.ba.approved()
        handoff = ba_tests.ba.make_handoff(approved, self.root, human_actor_authenticator=replacement_auth)
        (self.root/'receipt-r2.json').write_bytes((self.root/'receipt.json').read_bytes())
        handoff['approval_receipt'] = self.ba.ref('receipt-r2.json', 'R2')
        (self.root/'receipt.json').write_bytes(old_approval)
        self.ba.put('replacement-handoff.json', handoff)
        self.ba_auth = lambda actor, row: old_auth(actor, row) or replacement_auth(actor, row)
        self.runtime = self.new_runtime()
        resumed = self.runtime.resume_gap(self.ba.ref('replacement-handoff.json', 'R2'),
            self.ba.ref('review-evidence.json'))
        self.assertEqual(resumed['lifecycle'], 'AUTHORITY_VALIDATED')
        self.assertNotIn('snapshot', resumed['artifacts'])
        self.assertNotIn('impact', resumed['artifacts'])
        self.assertEqual(resumed['gates'], {})
        with self.assertRaises(ValueError):
            self.runtime.write_source('core', 'src/module.py', 'stale plan cannot authorize')
        self.assertEqual(self.new_runtime().load()['lifecycle'], 'AUTHORITY_VALIDATED')

    def test_multi_repo_is_high_risk_with_exact_scope_base_and_output_revisions(self):
        self.add_repository('client')
        state = self.planned()
        self.assertEqual(state['risk']['level'], 'HIGH_RISK')
        self.assertIn('CROSS_REPOSITORY', state['risk']['categories'])
        self.assertEqual({row['id']:row['base_revision'] for row in state['repositories']},
            {repo_id:self.git(repo_id, 'rev-parse', 'HEAD') for repo_id in self.repository_roots})
        self.approve(state)
        with self.assertRaises(ValueError):
            self.runtime.write_source('client', 'outside/module.py', 'not in write scope')
        with self.assertRaises(ValueError):
            self.runtime.write_source('unknown', 'src/module.py', 'ambiguous repository')
        self.implement()
        handoff = self.finish()
        revisions = {repo_id:self.git(repo_id, 'rev-parse', 'HEAD') for repo_id in self.repository_roots}
        self.assertEqual(handoff['repository_revisions'], revisions)
        self.assertEqual({row['repository_id']:row['revision'] for row in handoff['implementation']}, revisions)
        self.assertTrue(all(row['changed_paths'] == ['src/module.py'] for row in handoff['implementation']))

    def test_heterogeneous_multi_repo_checks_only_execute_in_their_bound_repository(self):
        self.add_repository('api')
        checks = [
            {'name':'core-unit','repository_id':'core','category':'UNIT',
             'command':[sys.executable,'-c',"from pathlib import Path; assert Path.cwd().name == 'core'"]},
            {'name':'api-component','repository_id':'api','category':'COMPONENT',
             'command':[sys.executable,'-c',"from pathlib import Path; assert Path.cwd().name == 'api'"]},
        ]
        state = self.planned(checks=checks, run_id='RUN-HETEROGENEOUS')
        self.assertEqual([row['repository_id'] for row in state['checks']], ['core','api'])
        self.approve(state)
        self.implement()
        handoff = self.finish()
        self.assertEqual(handoff['state'], 'READY_FOR_TEST')
        self.assertEqual(set(handoff['repository_revisions']), {'core','api'})
        rows = {row['name']:row for row in handoff['engineering_verification']['checks']}
        for name, repository_id in (('core-unit','core'),('api-component','api')):
            row = rows[name]
            self.assertEqual(row['repository_id'], repository_id)
            self.assertEqual((row['status'],row['exit_code']), ('PASS',0))
            evidence = json.loads((self.root/row['evidence_ref']['path']).read_text(encoding='utf-8'))
            self.assertEqual(evidence['repository_id'], repository_id)
            self.assertEqual(evidence['command'], row['command'])
            self.assertEqual((evidence['status'],evidence['exit_code']), ('PASS',0))
            self.assertEqual(evidence['snapshot_sha256'], handoff['technical_snapshot']['sha256'])
            self.assertEqual(evidence['implementation_revision'], handoff['repository_revisions'][repository_id])
            self.assertEqual([execution['repository_id'] for execution in evidence['executions']], [repository_id])

    def test_failing_scoped_check_in_one_repository_blocks_handoff(self):
        self.add_repository('api')
        checks = [
            {'name':'core-unit','repository_id':'core','category':'UNIT',
             'command':[sys.executable,'-c',"from pathlib import Path; assert Path.cwd().name == 'core'"]},
            {'name':'api-component','repository_id':'api','category':'COMPONENT',
             'command':[sys.executable,'-c','raise SystemExit(7)']},
        ]
        self.planned(checks=checks, run_id='RUN-SCOPED-FAILURE')
        self.approve(self.runtime.state)
        self.implement()
        self.runtime.record_review([self.ba.ref('review-evidence.json')])
        verification = self.runtime.verify()
        self.assertEqual([row['status'] for row in verification['checks']], ['PASS','FAIL'])
        with self.assertRaises(ValueError):
            self.runtime.finalize(self.coverage())

    def test_maintenance_fast_path_finishes_without_ba_or_feature_coverage(self):
        # The fixture's maintenance baseline already has the correct behavior;
        # the controlled change below only adds a source comment.
        (Path(self.repository_roots['core'])/'src/module.py').write_text('def result():\n    return 2\n', encoding='utf-8')
        self.git('core', 'add', 'src/module.py')
        self.git('core', 'commit', '--quiet', '-m', 'Correct maintenance baseline')
        self.repositories[0]['base_revision'] = self.git('core', 'rev-parse', 'HEAD')
        self.runtime = DevRuntime(self.root)
        self.runtime.start(self.request(maintenance=True))
        state = self.runtime.validate_authority()
        self.assertEqual(state['risk']['level'], 'TRIVIAL')
        self.runtime.implementation_ready()
        self.implement(maintenance=True)
        handoff = self.finish(maintenance=True)
        self.assertIsNone(handoff['upstream_engineering_handoff'])
        self.assertEqual(handoff['requirements_coverage'], [])
        self.assertEqual(handoff['review']['budget']['full_reviews'], 0)
        self.assertEqual(handoff['state'], 'READY_FOR_TEST')

    def test_maintenance_invalidating_discoveries_cannot_authorize_source(self):
        for category in ('BUSINESS_BEHAVIOR', 'SECURITY', 'PUBLIC_CONTRACT', 'CROSS_REPOSITORY'):
            with self.subTest(category=category):
                runtime = DevRuntime(self.root)
                request = self.request(maintenance=True, run_id='RUN-'+category)
                request['maintenance']['discovered_changes'] = [category]
                try:
                    runtime.start(request)
                except ValueError:
                    continue
                with self.assertRaises(ValueError):
                    runtime.validate_authority()
                with self.assertRaises(ValueError):
                    runtime.write_source('core', 'src/module.py', 'invalid maintenance discovery')

    def test_discovery_after_maintenance_ready_blocks_and_requires_feature_authority(self):
        for category in ('BUSINESS_BEHAVIOR', 'SECURITY', 'PUBLIC_CONTRACT', 'CROSS_REPOSITORY'):
            with self.subTest(category=category):
                runtime = DevRuntime(self.root)
                runtime.start(self.request(maintenance=True, run_id='DISCOVERY-'+category))
                runtime.validate_authority()
                runtime.implementation_ready()
                blocked = runtime.discover_maintenance_change([category])
                self.assertEqual(blocked['lifecycle'], 'BLOCKED')
                resumed = DevRuntime(self.root)
                self.assertEqual(resumed.load()['lifecycle'], 'BLOCKED')
                with self.assertRaises(ValueError):
                    resumed.write_source('core', 'src/module.py', 'invalid maintenance discovery')

    def test_new_process_can_resume_normal_run_from_persisted_refs(self):
        self.planned()
        script = """import json, sys
from tooling.lib.dev_vnext_runtime import DevRuntime
from pathlib import Path
root = Path(sys.argv[1])
expected = json.loads((root/'receipt.json').read_text())
runtime = DevRuntime(root, ba_authenticator=lambda actor,row: actor == 'synthetic-human' and row == expected)
state = runtime.implementation_ready()
print(state['lifecycle'])
"""
        result = subprocess.run([sys.executable, '-c', script, str(self.root)],
            cwd=str(Path(__file__).resolve().parents[2]), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('IMPLEMENTATION_READY', result.stdout)
        self.assertEqual(self.runtime.load()['lifecycle'], 'IMPLEMENTATION_READY')

    def test_failing_native_checks_cannot_publish_handoff(self):
        self.planned()
        self.runtime.implementation_ready()
        self.implement()
        self.runtime.write_source('core', 'src/module.py', 'def result():\n    return 3\n')
        self.git('core', 'add', 'src/module.py')
        self.git('core', 'commit', '--quiet', '-m', 'Deliberate failing implementation')
        self.runtime.record_review([self.ba.ref('review-evidence.json')])
        try:
            self.runtime.verify()
        except ValueError:
            pass
        with self.assertRaises(ValueError):
            self.runtime.finalize(self.coverage())
        self.assertNotEqual(self.runtime.load()['lifecycle'], 'READY_FOR_TEST')
        self.assertEqual(list((self.root/'.devkit').rglob('dev-handoff.json')), [])

    def test_review_budget_allows_one_blocking_fix_wave_and_scoped_rereview(self):
        self.planned()
        self.runtime.implementation_ready()
        self.implement()
        self.runtime.record_review([self.ba.ref('review-evidence.json')], blocking_findings=['correct implementation comment'])
        self.runtime.begin_fix_wave()
        self.runtime.write_source('core', 'src/module.py', '# Reviewed implementation.\ndef result():\n    return 2\n')
        self.git('core', 'add', 'src/module.py')
        self.git('core', 'commit', '--quiet', '-m', 'Single blocking fix wave')
        self.runtime.record_review([self.ba.ref('review-evidence.json')], kind='scoped')
        with self.assertRaises(ValueError):
            self.runtime.record_review([self.ba.ref('review-evidence.json')])
        with self.assertRaises(ValueError):
            self.runtime.begin_fix_wave()
        with self.assertRaises(ValueError):
            self.runtime.record_review([self.ba.ref('review-evidence.json')], kind='scoped')
        self.runtime.verify()
        handoff = self.runtime.finalize(self.coverage())
        self.assertEqual(handoff['review']['budget'],
            {'full_reviews':1, 'blocking_fix_waves':1, 'scoped_rereviews':1})
        self.assertEqual(handoff['review']['blocking_findings'], [])

    def test_delivery_metadata_cannot_supply_authority_or_expand_write_scope(self):
        self.ba.put('delivery-metadata.json', {'targets':[{'id':'unapproved', 'write_scope':['outside']} ]})
        request = self.request()
        request['delivery'] = self.ba.ref('delivery-metadata.json')
        request['upstream'] = None
        try:
            self.runtime.start(request)
        except ValueError:
            pass
        else:
            with self.assertRaises(ValueError):
                self.runtime.validate_authority()
        request['run_id'] = 'RUN-METADATA'
        request['upstream'] = self.upstream
        state = self.runtime.start(request)
        self.assertEqual(state['delivery'], self.ba.ref('delivery-metadata.json'))
        state = self.runtime.validate_authority()
        state = self.runtime.impact(self.impact_document(state))
        (self.root/'plan-input.md').write_text('Exact local implementation HOW.', encoding='utf-8')
        (self.root/'tasks-input.md').write_text('Implement the local module.', encoding='utf-8')
        self.runtime.plan('plan-input.md', 'tasks-input.md', revision='TECH-METADATA')
        self.runtime.implementation_ready()
        with self.assertRaises(ValueError):
            self.runtime.write_source('core', 'outside/module.py', 'not authorized by delivery')
        with self.assertRaises(ValueError):
            self.runtime.write_source('unapproved', 'src/module.py', 'unknown repository')
        self.implement()
        handoff = self.finish()
        self.assertEqual(handoff['delivery_manifest'], self.ba.ref('delivery-metadata.json'))

    def test_repository_alias_identity_is_rejected(self):
        self.add_repository('client')
        request = self.request()
        request['repository_roots']['client'] = request['repository_roots']['core']
        request['repositories'][1]['base_revision'] = request['repositories'][0]['base_revision']
        with self.assertRaises(ValueError):
            self.runtime.start(request)

    def test_repository_base_drift_during_authentication_blocks_source_write(self):
        state = self.planned(high=True)
        self.approve(state)
        self.runtime.begin_implementation()
        original = (Path(self.repository_roots['core'])/'src/module.py').read_bytes()
        receipt = json.loads((self.root/'technical-receipt.json').read_text())
        authenticated = lambda actor, row: actor == 'technical-human' and row == receipt
        calls = 0
        drifted = False

        def drifting_authenticator(actor, row):
            nonlocal calls, drifted
            calls += 1
            valid = authenticated(actor, row)
            if calls >= 3 and not drifted:
                self.git('core', 'checkout', '--quiet', '--orphan', 'replacement-base')
                self.git('core', 'add', '.')
                self.git('core', 'commit', '--quiet', '-m', 'Unrelated replacement base')
                drifted = True
            return valid

        self.runtime = DevRuntime(self.root, ba_authenticator=self.ba_auth,
            technical_authenticator=drifting_authenticator)
        with self.assertRaises(ValueError):
            self.runtime.write_source('core', 'src/module.py', 'UNAUTHORIZED WRITE\n')
        self.assertTrue(drifted)
        self.assertEqual((Path(self.repository_roots['core'])/'src/module.py').read_bytes(), original)

    def test_interrupted_planning_resumes_only_when_partial_bytes_match(self):
        self.runtime.start(self.request())
        self.runtime.validate_authority()
        self.runtime.impact(self.impact_document(self.runtime.state))
        plan = self.root/'technical-plan-input.md'
        tasks = self.root/'technical-tasks-input.md'
        plan.write_text('Exact local implementation plan.\n', encoding='utf-8')
        tasks.write_text('Run the native checks.\n', encoding='utf-8')
        from tooling.lib import dev_vnext_runtime as runtime_module
        write = runtime_module._atomic
        calls = 0

        def fail_second_write(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('synthetic interruption between plan artifacts')
            return write(path, content)

        with patch.object(runtime_module, '_atomic', side_effect=fail_second_write):
            with self.assertRaisesRegex(OSError, 'synthetic interruption'):
                self.runtime.plan(plan, tasks, revision='TECH-RESUME')
        resumed = DevRuntime(self.root, ba_authenticator=self.ba_auth)
        self.assertEqual(resumed.load()['lifecycle'], 'IMPACT_ANALYZED')
        original_plan = plan.read_bytes()
        plan.write_text('Changed after interruption.\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'immutable'):
            resumed.plan(plan, tasks, revision='TECH-RESUME')
        plan.write_bytes(original_plan)
        planned = resumed.plan(plan, tasks, revision='TECH-RESUME')
        self.assertEqual(planned['lifecycle'], 'TECHNICAL_PLANNED')


if __name__ == '__main__':
    unittest.main()
