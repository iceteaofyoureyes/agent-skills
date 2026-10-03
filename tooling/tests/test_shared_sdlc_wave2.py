"""Project contracts and dependency direction, independently of any project kit."""
import copy
import ast
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ('product', 'domain', 'architecture', 'testing', 'features')
SECTIONS = ('introduction_goals', 'constraints', 'context_scope', 'solution_strategy',
            'building_block_view', 'runtime_view', 'deployment_view', 'crosscutting_concepts',
            'architecture_decisions', 'quality_requirements', 'risks_technical_debt', 'glossary')


def topology():
    return {'schema_version': 1, 'project': {'id': 'example'}, 'repositories': [
        {'id': 'docs', 'path': 'docs', 'repository': 'owner/docs',
         'role': 'project_documentation_authority'},
        {'id': 'app', 'path': 'app', 'repository': 'owner/app',
         'role': 'application_implementation'}]}


def policy():
    return {'schema_version': 1, 'project': {'language': 'vi'},
            'foundation': {'profile': 'arc42-standard-v1'},
            'authority': {key: key + '.md' for key in DOMAINS},
            'workflow': {'feature_root': 'features', 'branch_convention': 'feature/{feature_id}'},
            'testing': {'automation_repository_role': 'project_test_automation'},
            'artifacts': {'optional': ['prototype.html']}}


def manifest(root, mode='BROWNFIELD_RECOVERY'):
    path = root/'foundation.md'
    path.write_bytes(b'Observed foundation\n')
    ref = {'path': 'foundation.md', 'revision': 'R1', 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'schema_version': 1, 'id': 'foundation', 'revision': 'R1',
            'profile': {'id': 'arc42-standard-v1', 'level': 'STANDARD'},
            'mode': mode, 'authority': {key: key.upper() for key in DOMAINS},
            'entry_points': {key: dict(ref) for key in DOMAINS},
            'sections': {key: {'status': 'UNKNOWN', 'owner': 'ARCHITECTURE',
                              'evidence': 'UNKNOWN', 'blocking': False, 'references': []}
                         for key in SECTIONS}, 'blockers': []}


class ProjectContractTests(unittest.TestCase):
    def module(self, name):
        try: spec = importlib.util.find_spec(name)
        except ModuleNotFoundError: spec = None
        self.assertIsNotNone(spec, 'required contract module missing: ' + name)
        return importlib.import_module(name)

    def test_topology_additional_services_and_semantic_roles(self):
        m = self.module('shared.sdlc.topology.contract')
        value = topology()
        value['repositories'].append({'id':'service', 'path':'services/api',
                                      'repository':'owner/service', 'role':'service_implementation'})
        self.assertEqual(m.validate_topology(value), value)

    def test_topology_duplicate_and_overlapping_locations_rejected(self):
        m = self.module('shared.sdlc.topology.contract')
        for field, value in [('id','docs'), ('path','DOCS'), ('path','docs/nested'),
                             ('repository','owner/docs'), ('repository','not-a-repository')]:
            data = topology(); data['repositories'][1][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                m.validate_topology(data)

    def test_all_contracts_reject_future_bool_and_string_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for module, function, data in [
                ('topology.contract','validate_topology',topology()),
                ('policy.contract','validate_policy',policy()),
                ('foundation.contract','validate_manifest',manifest(root))]:
                m = self.module('shared.sdlc.' + module)
                for version in (True, '1', 2, 1.0, None):
                    bad = copy.deepcopy(data); bad['schema_version'] = version
                    with self.subTest(module=module, version=version), self.assertRaises(ValueError):
                        getattr(m, function)(bad)

    def test_topology_paths_are_portable(self):
        m = self.module('shared.sdlc.topology.contract')
        for path in ('/root', '../x', 'a/../b', 'a//b', 'a\\b', 'C:/app', '.',
                     'CON', 'a.', 'a ', 'a?b', 'a#b', 'a%2fb'):
            bad = topology(); bad['repositories'][0]['path'] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                m.validate_topology(bad)

    def test_policy_valid_locations_are_project_data(self):
        m = self.module('shared.sdlc.policy.contract')
        self.assertEqual(m.validate_policy(policy()), policy())

    def test_policy_unknown_fields_cannot_weaken_invariants_or_supply_behavior(self):
        m = self.module('shared.sdlc.policy.contract')
        for key, value in [('invariants', []), ('approval', 'AUTO'), ('business_rules', ['invented']),
                           ('extensions', {'approval':False}), ('schema_version_extra',1)]:
            bad = policy(); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.validate_policy(bad)
        bad = policy(); bad['workflow']['human_gate_required'] = False
        with self.assertRaises(ValueError): m.validate_policy(bad)

    def test_policy_secret_values_and_malformed_nested_types_rejected(self):
        m = self.module('shared.sdlc.policy.contract')
        for value in ('https://user:password@example.org', 'Bearer abc',
                      '-----BEGIN PRIVATE KEY-----', 'sk-' + 'a'*32):
            bad = policy(); bad['workflow']['branch_convention'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): m.validate_policy(bad)
        for field, value in [('authority', []), ('testing', None), ('artifacts', {'optional':'a.md'})]:
            bad = policy(); bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): m.validate_policy(bad)

    def test_policy_relative_paths_and_duplicate_artifacts_rejected(self):
        m = self.module('shared.sdlc.policy.contract')
        for path in ('../product.md', '/product.md', 'C:/product.md', 'a\\b.md'):
            bad = policy(); bad['authority']['product'] = path
            with self.subTest(path=path), self.assertRaises(ValueError): m.validate_policy(bad)
        bad = policy(); bad['artifacts']['optional'] = ['a.md','A.md']
        with self.assertRaises(ValueError): m.validate_policy(bad)

    def test_json_and_yaml_reader_reject_duplicate_and_unsafe_syntax(self):
        m = self.module('shared.sdlc.schema')
        self.assertEqual(m.read_document('{"schema_version":1}'), {'schema_version':1})
        text = 'schema_version: 1\nproject:\n  id: example\nrepositories:\n  - id: docs\n    path: docs\n    repository: owner/docs\n    role: documentation\n'
        self.assertEqual(m.read_document(text)['repositories'][0]['path'], 'docs')
        for text in ('{"a":1,"a":2}', 'a: 1\na: 2\n', 'a: &anchor x\n',
                     'a: !custom x\n', 'a: *anchor\n', 'a:\n b: x\n',
                     'a: |\n  payload\n', 'a: .nan\n', '{"a":NaN}',
                     'a: {}\n  b: x\n', 'a: [unquoted]\n', 'a: yes\n',
                     'a: [NaN]\n', 'a: {"b": Infinity}\n'):
            with self.subTest(text=text), self.assertRaises(ValueError): m.read_document(text)

    def test_policy_reader_is_read_only_and_uses_canonical_location(self):
        m = self.module('shared.sdlc.policy.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'.sdlc').mkdir()
            path = root/'.sdlc/project-policy.yml'; path.write_text(json.dumps(policy()))
            before = path.read_bytes()
            self.assertEqual(m.read_policy(root), policy())
            self.assertEqual(path.read_bytes(), before)
            self.assertFalse((root/'.test-kit').exists())

    def test_foundation_profile_represents_all_sections_and_data_levels(self):
        m = self.module('shared.sdlc.foundation.profiles')
        p = m.PROJECT_FOUNDATION_PROFILE_ARC42_V1
        self.assertEqual(tuple(p['sections']), SECTIONS)
        self.assertEqual(set(p['levels']), {'MINIMAL','STANDARD','EXTENDED'})
        self.assertEqual(len(p['section_titles']), 12)
        with self.assertRaises(TypeError): p['id'] = 'changed'

    def test_foundation_levels_validate_declared_entry_points(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = manifest(root)
            data['profile']['level'] = 'MINIMAL'
            data['entry_points'] = {key:value for key,value in data['entry_points'].items()
                                    if key in ('product','architecture')}
            self.assertEqual(m.foundation_readiness(data,root)['status'],'PROJECT_FOUNDATION_READY')
            data['profile']['level'] = 'STANDARD'
            with self.assertRaises(ValueError): m.foundation_readiness(data,root)
            data = manifest(root); data['profile']['level'] = 'EXTENDED'
            with self.assertRaises(ValueError): m.foundation_readiness(data,root)
            data['entry_points']['operations'] = dict(data['entry_points']['architecture'])
            data['sections']['runtime_view'].update(status='COMPLETE',evidence='CONFIRMED',
                                                    references=[data['entry_points']['operations']])
            self.assertEqual(m.foundation_readiness(data,root)['status'],'PROJECT_FOUNDATION_READY')

    def test_foundation_supplied_prior_is_always_validated_for_non_target(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); prior = manifest(root)
            for mutate in (lambda d:d.update(id='different'),
                           lambda d:d['sections']['runtime_view'].update(status='PARTIAL')):
                current = copy.deepcopy(prior); mutate(current)
                with self.assertRaises(ValueError): m.foundation_readiness(current,root,previous=prior)
            bad = copy.deepcopy(prior); bad['schema_version'] = 2
            with self.assertRaises(ValueError): m.foundation_readiness(prior,root,previous=bad)
            current = copy.deepcopy(prior); current['revision'] = 'R2'
            current['sections']['runtime_view']['status'] = 'PARTIAL'
            self.assertEqual(m.foundation_readiness(current,root,previous=prior)['status'],'PROJECT_FOUNDATION_READY')

    def test_foundation_all_modes_and_statuses_with_nonblocking_unknown(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for mode in ('GREENFIELD_BOOTSTRAP','BROWNFIELD_RECOVERY','FOUNDATION_REFRESH'):
                data = manifest(root, mode)
                for status in ('PARTIAL','UNKNOWN','NOT_APPLICABLE','DEFERRED'):
                    data['sections']['runtime_view']['status'] = status
                    self.assertEqual(m.foundation_readiness(data, root)['status'], 'PROJECT_FOUNDATION_READY')

    def test_foundation_missing_sections_entry_points_and_owners_block(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for mutate in (lambda d: d['sections'].pop('glossary'),
                           lambda d: d['entry_points'].pop('product'),
                           lambda d: d['authority'].pop('testing'),
                           lambda d: d['sections']['runtime_view'].update(owner='UNDECLARED'),
                           lambda d: d['authority'].update(testing=['A','B'])):
                data = manifest(root); mutate(data)
                with self.assertRaises(ValueError): m.foundation_readiness(data, root)

    def test_foundation_invalid_status_evidence_and_complete_unknown_block(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for mode, evidence, status in [('BROWNFIELD_RECOVERY','PROPOSED','PARTIAL'),
                                           ('GREENFIELD_BOOTSTRAP','CURRENT_SYSTEM','PARTIAL'),
                                           ('BROWNFIELD_RECOVERY','UNKNOWN','COMPLETE'),
                                           ('BROWNFIELD_RECOVERY','INFERRED','APPROVED')]:
                data = manifest(root, mode)
                data['sections']['runtime_view'].update(status=status, evidence=evidence)
                with self.subTest(mode=mode, evidence=evidence), self.assertRaises(ValueError):
                    m.foundation_readiness(data, root)

    def test_foundation_blockers_and_section_blocking_fail_closed(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for blocker in ({'id':'risk-1','critical':True,'resolved':False},
                            {'id':'risk-1','critical':'false','resolved':False}):
                data = manifest(root); data['blockers'] = [blocker]
                with self.assertRaises(ValueError): m.foundation_readiness(data, root)
            data = manifest(root); data['sections']['runtime_view']['blocking'] = True
            with self.assertRaises(ValueError): m.foundation_readiness(data, root)
            data = manifest(root); data['blockers'] = [{'id':'risk-1','critical':False,'resolved':False}]
            self.assertEqual(m.foundation_readiness(data, root)['status'], 'PROJECT_FOUNDATION_READY')

    def test_foundation_drift_and_unsafe_references_fail(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = manifest(root)
            (root/'foundation.md').write_bytes(b'drift')
            with self.assertRaises(ValueError): m.foundation_readiness(data, root)
            for ref in ({'path':'../x','sha256':'0'*64}, {'path':'foundation.md','sha256':'bad'},
                        {'path':'foundation.md','sha256':'0'*64,'approval':True}):
                data = manifest(root); data['entry_points']['product'] = ref
                with self.assertRaises(ValueError): m.foundation_readiness(data, root)

    def test_current_system_cannot_claim_target_without_bound_human_decision(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); old = manifest(root)
            old['sections']['runtime_view'].update(evidence='CURRENT_SYSTEM', status='PARTIAL',
                                                    references=[old['entry_points']['architecture']])
            new = copy.deepcopy(old); new['mode'] = 'FOUNDATION_REFRESH'; new['revision'] = 'R2'
            new['sections']['runtime_view']['evidence'] = 'APPROVED_TARGET'
            with self.assertRaises(ValueError): m.validate_transition(old, new, root)
            before, after = m.manifest_sha256(old), m.manifest_sha256(new)
            receipt = {'schema_version':1,'decision':'APPROVE','actor_id':'reviewer','actor_role':'HUMAN',
                       'artifact_id':'foundation','artifact_revision':'R2','previous_revision':'R1',
                       'previous_manifest_sha256':before,'manifest_sha256':after,
                       'decision_ref':new['entry_points']['architecture']}
            (root/'approval.json').write_text(json.dumps(receipt))
            approval = {'path':'approval.json','revision':'R2','sha256':hashlib.sha256((root/'approval.json').read_bytes()).hexdigest()}
            auth = lambda actor, receipt: actor == 'reviewer'
            self.assertEqual(m.validate_transition(old,new,root,approval=approval,
                                                   human_actor_authenticator=auth), after)
            with self.assertRaises(ValueError): m.validate_transition(old,new,root,approval=approval)
            with self.assertRaises(ValueError):
                m.validate_transition(old,new,root,approval=approval,human_actor_authenticator=lambda *_:'yes')
            for field, value in [('decision','ANSWER'), ('actor_role','AGENT'),
                                 ('previous_manifest_sha256','0'*64), ('manifest_sha256','0'*64)]:
                bad = dict(receipt); bad[field] = value
                (root/'approval.json').write_text(json.dumps(bad))
                ref = {'path':'approval.json','revision':'R2','sha256':hashlib.sha256((root/'approval.json').read_bytes()).hexdigest()}
                with self.subTest(field=field), self.assertRaises(ValueError):
                    m.validate_transition(old,new,root,approval=ref,human_actor_authenticator=auth)

    def test_standalone_target_requires_approval_and_readiness_does_not_grant_it(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = manifest(root,'GREENFIELD_BOOTSTRAP')
            row = data['sections']['solution_strategy']
            row.update(status='COMPLETE',evidence='APPROVED_TARGET',references=[data['entry_points']['architecture']])
            with self.assertRaises(ValueError): m.foundation_readiness(data,root)
            data = manifest(root)
            result = m.foundation_readiness(data,root)
            self.assertFalse(result['human_approval'])
            self.assertFalse(result['feature_ready'])

    def test_target_receipt_drift_between_reference_check_and_parse_is_rejected(self):
        m = self.module('shared.sdlc.foundation.contract')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); data = manifest(root,'GREENFIELD_BOOTSTRAP')
            data['sections']['solution_strategy'].update(status='COMPLETE',evidence='APPROVED_TARGET',
                                                       references=[data['entry_points']['architecture']])
            receipt = {'schema_version':1,'decision':'APPROVE','actor_id':'reviewer','actor_role':'HUMAN',
                       'artifact_id':data['id'],'artifact_revision':data['revision'],
                       'manifest_sha256':m.manifest_sha256(data),'decision_ref':data['entry_points']['architecture']}
            path = root/'approval.json'; path.write_text(json.dumps(receipt))
            ref = {'path':'approval.json','revision':'R1','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            original = Path.read_bytes; changed = []
            def drift(candidate):
                content = original(candidate)
                if candidate == path and not changed:
                    changed.append(True); altered = dict(receipt); altered['actor_id'] = 'another-reviewer'
                    path.write_text(json.dumps(altered))
                return content
            with patch.object(Path,'read_bytes',new=drift), self.assertRaises(ValueError):
                m.foundation_readiness(data,root,approval=ref,human_actor_authenticator=lambda *_:True)

    def test_doctor_readiness_is_package_only(self):
        m = self.module('shared.sdlc.readiness.compatibility')
        for status, ready in [('READY',True),('DEGRADED',False),('FAIL',False)]:
            result = m.normalize_doctor(status)
            self.assertEqual(result['readiness'], 'PACKAGE_READY')
            self.assertEqual(result['ready'], ready)
            self.assertFalse(result['human_approval']); self.assertFalse(result['feature_ready'])
        for status in ('APPROVED','PACKAGE_READY','ready'):
            with self.assertRaises(ValueError): m.normalize_doctor(status)

    def test_generic_promotion_exact_replay_and_conflict_preflight(self):
        m = self.module('shared.sdlc.promotion.immutable')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            writes = [(root/'one',b'exact'),(root/'two',b'bound')]
            m.publish_immutable(writes,stage='GENERIC',transition='PROMOTE')
            m.publish_immutable(writes,stage='GENERIC',transition='PROMOTE')
            self.assertEqual((root/'one').read_bytes(),b'exact')
            (root/'two').write_bytes(b'conflict')
            with self.assertRaises(ValueError):
                m.publish_immutable([(root/'absent',b'new'),*writes],stage='GENERIC',transition='PROMOTE')
            self.assertFalse((root/'absent').exists())
            with self.assertRaises(ValueError):
                m.publish_immutable([(root/'one',b'exact'),(root/'one',b'different')],stage='X',transition='X')

    def test_generic_record_binds_identity_bytes_and_receipt_reference(self):
        m = self.module('shared.sdlc.promotion.immutable')
        source = {'id':'artifact','revision':'R1','sha256':hashlib.sha256(b'exact').hexdigest()}
        receipt = {'path':'approvals/receipt.json','sha256':hashlib.sha256(b'receipt').hexdigest()}
        result = m.promotion_record(source,b'exact',receipt,b'receipt')
        self.assertEqual(result['source'],source); self.assertEqual(result['approval_receipt'],receipt)
        self.assertFalse(result['human_approval'])
        with self.assertRaises(ValueError): m.promotion_record(source,b'drift',receipt,b'receipt')
        with self.assertRaises(ValueError): m.promotion_record(source,b'exact',receipt,b'drift')

    def test_generic_promotion_alias_and_ancestor_destinations_reject_before_writes(self):
        m = self.module('shared.sdlc.promotion.immutable')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for writes in ([(root/'one',b'a'),(root/'sub/../one',b'b')],
                           [(root/'one',b'a'),(root/'one/sub',b'b')],
                           [(root/'One',b'a'),(root/'one',b'b')]):
                with self.assertRaises(ValueError): m.publish_immutable(writes,stage='X',transition='X')
                self.assertEqual(list(root.iterdir()),[])

    def test_generic_promotion_unsafe_names_fail_before_any_publication(self):
        m = self.module('shared.sdlc.promotion.immutable')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'legitimate root with spaces'; root.mkdir()
            for name in ('trailing.','CON','NUL.json','file:stream','bad?name','bad*name',
                         'trailing ', 'unsafe/new:part', 'unsafe/COM1/result.json'):
                writes = [(root/'first',b'first'),(root/name,b'unsafe')]
                with self.subTest(name=name), self.assertRaises(ValueError):
                    m.publish_immutable(writes,stage='X',transition='X')
                self.assertEqual(list(root.iterdir()),[])
            m.publish_immutable([(root/'safe.json',b'approved')],stage='X',transition='X')
            self.assertEqual((root/'safe.json').read_bytes(),b'approved')

    def test_shared_core_imports_without_test_dependencies_including_dynamic_paths(self):
        names = [p.relative_to(ROOT).with_suffix('').as_posix().replace('/','.')
                 for p in (ROOT/'shared').rglob('*.py') if p.name != '__init__.py']
        code = '''import importlib, pathlib, sys
sys.path.insert(0,sys.argv[1])
class Block:
    def find_spec(self,name,path=None,target=None):
        if name.startswith(('tooling.lib.test_kit','tooling.lib.test_promotion','tooling.lib.testware_promotion','kits.test')):
            raise AssertionError('forbidden shared dependency: '+name)
sys.meta_path.insert(0,Block())
for name in sys.argv[2:]: importlib.import_module(name)
assert not any(n.startswith(('tooling.lib.test_kit','kits.test')) for n in sys.modules)
'''
        result = subprocess.run([sys.executable,'-I','-c',code,str(ROOT),*names],
                                cwd=ROOT.parent,capture_output=True,text=True,timeout=60)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_static_shared_source_has_no_test_imports_even_inside_functions(self):
        forbidden = ('tooling.lib.test_kit','tooling.lib.test_promotion','tooling.lib.testware_promotion','kits.test')
        for path in (ROOT/'shared').rglob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                names = []
                if isinstance(node,ast.Import): names = [alias.name for alias in node.names]
                if isinstance(node,ast.ImportFrom):
                    names = [node.module or ''] + [(node.module or '')+'.'+alias.name for alias in node.names]
                if isinstance(node,ast.Call):
                    name = getattr(node.func,'id',None) or getattr(node.func,'attr',None)
                    if name in ('import_module','__import__') and node.args and isinstance(node.args[0],ast.Constant):
                        names = [node.args[0].value]
                for name in names:
                    if isinstance(name,str): self.assertFalse(name.startswith(forbidden),f'{path}:{node.lineno}: {name}')


if __name__ == '__main__': unittest.main()
