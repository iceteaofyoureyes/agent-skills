"""Owner producer contracts using neutral public evidence and synthetic host gates."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from shared.sdlc.foundation import producers as p
from shared.sdlc.foundation import workflow as w
from shared.sdlc.foundation.contract import manifest_sha256
from shared.sdlc.schema import read_document

FIXTURES = Path(__file__).parent / 'fixtures'


class ProducerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'project'
        shutil.copytree(FIXTURES / 'synthetic-brownfield-foundation', self.root)
        self.topology = read_document((self.root / '.sdlc/topology.json').read_text())
        self.policy = read_document((self.root / '.sdlc/project-policy.yml').read_text())
        self.mode = 'BROWNFIELD_RECOVERY'

    def ref(self, path='module/config.json'):
        return w.exact_ref(self.root, path, 'R1')

    def observation(self, topic, basis='OBSERVED', path='module/config.json', statement='Local storage is configured.', id=None):
        return {'id': id or topic.replace('_', '-'), 'topic': topic, 'statement': statement,
                'basis': basis, 'references': [] if path is None else [self.ref(path)],
                'status': 'PARTIAL', 'questions': []}

    def produce(self, producer, observations, **kw):
        return p.produce(self.root, self.topology, self.policy, producer, 'candidate', 'R1',
                         self.mode, observations, **kw)

    def labels(self, data):
        return {row['topic']: row['evidence_label'] for row in data['records']}

    def approval(self, artifact, section='solution_strategy'):
        # Test host binds the ENTIRE semantic artifact inside an approved Foundation.
        target = self.root / 'docs/semantic.json'
        target.write_bytes(w.semantic_bytes(artifact))
        state = {'mode': artifact['mode'], 'foundation_profile': {'id': 'arc42-standard-v1', 'level': 'MINIMAL'}}
        manifest = w.candidate_manifest(self.root, state, self.topology, self.policy, 'foundation', 'R1',
            sections={section: {'owner': 'ENGINEERING', 'status': 'PARTIAL', 'blocking': False,
                               'evidence': 'APPROVED_TARGET', 'references': [self.ref('docs/semantic.json')]}})
        (self.root / 'docs/decision.md').write_text('Synthetic Engineering Human approval of exact snapshot.')
        receipt = {'schema_version': 1, 'decision': 'APPROVE', 'actor_id': 'synthetic-reviewer',
                   'actor_role': 'HUMAN', 'artifact_id': manifest['id'], 'artifact_revision': 'R1',
                   'manifest_sha256': manifest_sha256(manifest), 'decision_ref': self.ref('docs/decision.md')}
        (self.root / '.sdlc/receipt.json').write_bytes(w.semantic_bytes(receipt))
        return {'manifest': manifest, 'approval': self.ref('.sdlc/receipt.json'),
                'human_actor_authenticator': lambda actor, actual: actor == 'synthetic-reviewer' and actual == receipt}

    def test_domain_code_rule_is_candidate_and_terminology_inferred(self):
        data = self.produce('domain-discovery', [
            self.observation('business_rule', path='module/src/catalog.py', statement='Item count returns collection length.'),
            self.observation('glossary', 'INFERRED', statement='Catalog may mean an item collection.')])
        self.assertEqual(data['owner'], 'BA')
        self.assertEqual(data['artifact_class'], 'RUNTIME')
        self.assertEqual(self.labels(data)['business_rule'], 'CURRENT_SYSTEM')
        self.assertEqual(self.labels(data)['glossary'], 'INFERRED')
        self.assertNotIn('business_rules', data)
        self.assertNotIn('requirements', data)
        self.assertFalse(any(row['id'].startswith(('BR-', 'FR-')) for row in data['records']))
        self.assertTrue({'actors', 'entities', 'lifecycle', 'gaps'} <= self.labels(data).keys())

    def test_confirmed_requires_exact_domain_authority_and_trusted_host(self):
        row = self.observation('glossary', 'AUTHORITY', 'docs/domain.md')
        with self.assertRaises(ValueError): self.produce('domain-discovery', [row])
        auth = lambda domain, ref: domain == 'domain' and ref == self.ref('docs/domain.md')
        self.assertEqual(self.labels(self.produce('domain-discovery', [row], authority_authenticator=auth))['glossary'], 'CONFIRMED')
        row['references'] = [self.ref('module/src/catalog.py')]
        with self.assertRaises(ValueError): self.produce('domain-discovery', [row], authority_authenticator=lambda *_: True)

    def test_architecture_observations_patterns_and_unknown_rationale(self):
        data = self.produce('architecture-discovery', [self.observation(topic) for topic in
            ('building_blocks', 'runtime', 'deployment')] + [self.observation('solution_strategy', 'INFERRED')])
        for topic in ('building_blocks', 'runtime', 'deployment'):
            self.assertEqual(self.labels(data)[topic], 'CURRENT_SYSTEM')
        self.assertEqual(self.labels(data)['solution_strategy'], 'INFERRED')
        with self.assertRaises(ValueError):
            self.produce('architecture-discovery', [self.observation('historical_rationale', 'INFERRED')])

    def test_target_cannot_be_approved_by_generation_or_validator_success(self):
        self.mode = 'GREENFIELD_BOOTSTRAP'
        data = self.produce('architecture-discovery', [self.observation('solution_strategy', 'PROPOSED', None)])
        self.assertEqual(self.labels(data)['solution_strategy'], 'PROPOSED')
        approved = copy.deepcopy(data)
        row = next(row for row in approved['records'] if row['topic'] == 'solution_strategy')
        row.update(basis='APPROVED_TARGET', evidence_label='APPROVED_TARGET', references=[self.ref('docs/architecture.md')])
        with self.assertRaises(ValueError): p.validate_artifact(approved, self.root, self.topology, self.policy)
        binding = self.approval(approved)
        p.validate_artifact(approved, self.root, self.topology, self.policy, approval_context=binding)
        row['statement'] = 'A different material target.'
        with self.assertRaises(ValueError):
            p.validate_artifact(approved, self.root, self.topology, self.policy, approval_context=binding)

    def c4(self):
        elements = [{'record': self.observation('c4_element', id=name), 'kind': kind, **extra}
                    for name, kind, extra in [('reader', 'ACTOR', {}), ('catalog', 'SYSTEM', {}),
                                              ('service', 'CONTAINER', {'parent': 'catalog'})]]
        relationships = [{'record': self.observation('c4_relationship', id='uses'),
                          'source': 'reader', 'target': 'catalog', 'level': 'CONTEXT'},
                         {'record': self.observation('c4_relationship', id='requests'),
                          'source': 'reader', 'target': 'service', 'level': 'CONTAINER'}]
        return p.c4_model(self.root, self.topology, self.policy, 'catalog-c4', 'R1', self.mode, elements, relationships)

    def test_c4_context_container_deterministic_and_render_derived(self):
        data = self.c4()
        self.assertEqual(data, self.c4())
        self.assertEqual({row['level'] for row in data['relationships']}, {'CONTEXT', 'CONTAINER'})
        view = p.render_c4(data, self.root, self.topology, self.policy)
        self.assertEqual(view['artifact_class'], 'DERIVED')
        self.assertIn('flowchart', view['content'])
        self.assertEqual(view, p.render_c4(data, self.root, self.topology, self.policy))
        self.assertFalse(any(row['kind'] == 'COMPONENT' for row in data['elements']))

    def test_c4_invalid_relationship_duplicate_orphan_and_evidence_rejected(self):
        data = self.c4()
        mutations = [lambda d: d['relationships'][0].update(target='missing'),
                     lambda d: d['elements'].append(copy.deepcopy(d['elements'][0])),
                     lambda d: d['relationships'].clear(),
                     lambda d: d['records'][0].update(references=[])]
        for mutate in mutations:
            altered = copy.deepcopy(data); mutate(altered)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                p.validate_artifact(altered, self.root, self.topology, self.policy)

    def adr(self, kind='RECOVERED', basis='OBSERVED'):
        return p.adr(self.root, self.topology, self.policy, 'storage-decision', 'R1', self.mode, kind,
                     [self.observation('decision', basis)])

    def test_recovered_adr_unknown_rationale_and_no_invented_alternatives(self):
        data = self.adr()
        self.assertEqual(data['decision_status'], 'RECOVERED_CURRENT_SYSTEM')
        self.assertEqual(self.labels(data)['rationale'], 'UNKNOWN')
        self.assertFalse(any(row['topic'] == 'alternative' for row in data['records']))
        with self.assertRaises(ValueError):
            p.adr(self.root, self.topology, self.policy, 'adr', 'R1', self.mode, 'RECOVERED',
                  [self.observation('decision'), self.observation('rationale', 'INFERRED')])

    def test_proposed_adr_and_exact_approved_adr_binding(self):
        self.mode = 'GREENFIELD_BOOTSTRAP'
        data = self.adr('PROPOSED', 'PROPOSED')
        self.assertEqual(data['decision_status'], 'PROPOSED')
        approved = copy.deepcopy(data); approved['decision_status'] = 'APPROVED_TARGET'
        row = next(row for row in approved['records'] if row['topic'] == 'decision')
        row.update(basis='APPROVED_TARGET', evidence_label='APPROVED_TARGET')
        with self.assertRaises(ValueError): p.validate_artifact(approved, self.root, self.topology, self.policy)
        binding = self.approval(approved, 'architecture_decisions')
        p.validate_artifact(approved, self.root, self.topology, self.policy, approval_context=binding)
        binding['manifest']['sections']['architecture_decisions']['references'] = [self.ref('docs/architecture.md')]
        with self.assertRaises(ValueError):
            p.validate_artifact(approved, self.root, self.topology, self.policy, approval_context=binding)

    def test_test_foundation_observation_and_recommendation_no_feature_tests(self):
        data = self.produce('test-foundation', [self.observation('test_levels', path='docs/testing.md')])
        self.assertEqual(data['owner'], 'TEST')
        self.assertEqual(self.labels(data)['test_levels'], 'CURRENT_SYSTEM')
        self.assertEqual(data['automation_repository_role'], self.policy['testing']['automation_repository_role'])
        self.mode = 'GREENFIELD_BOOTSTRAP'
        data = self.produce('test-foundation', [self.observation('quality_gates', 'PROPOSED', None)])
        self.assertEqual(self.labels(data)['quality_gates'], 'PROPOSED')
        for topic in ('test_design', 'testcases', 'feature_test'):
            with self.assertRaises(ValueError): self.produce('test-foundation', [self.observation(topic, 'PROPOSED', None)])

    def test_arc42_all_sections_unknown_partial_and_determinism(self):
        artifacts = [self.produce('domain-discovery', [self.observation('business_rule'), self.observation('glossary', 'INFERRED')]),
                     self.produce('architecture-discovery', [self.observation('runtime')]), self.adr(),
                     self.produce('test-foundation', [self.observation('quality_gates')])]
        view = p.arc42(artifacts, self.root, self.topology, self.policy)
        self.assertEqual(view['artifact_class'], 'DERIVED')
        self.assertEqual(len(view['sections']), 12)
        self.assertIn('UNKNOWN', view['content']); self.assertIn('PARTIAL', view['content'])
        self.assertNotIn('business-rule', view['content'])
        self.assertIn('rationale', view['content'])
        self.assertEqual(view, p.arc42(list(reversed(artifacts)), self.root, self.topology, self.policy))

    def test_architecture_context_scope_integrates_with_foundation_manifest(self):
        artifact = self.produce('architecture-discovery', [self.observation('context_scope')])
        record = next(row for row in artifact['records'] if row['topic'] == 'context_scope')
        section = {'status': record['status'], 'owner': record['owner'], 'evidence': record['evidence_label'],
                   'blocking': False, 'references': record['references']}
        state = {'mode': self.mode, 'foundation_profile': {'id': 'arc42-standard-v1', 'level': 'MINIMAL'}}
        manifest = w.candidate_manifest(self.root, state, self.topology, self.policy, 'foundation', 'R1',
                                       sections={'context_scope': section})
        view = p.arc42([artifact], self.root, self.topology, self.policy, manifest=manifest)
        context = view['sections']['context_scope']
        self.assertEqual(manifest['sections']['context_scope']['owner'], 'ENGINEERING')
        self.assertEqual(context['owner'], 'ENGINEERING')
        self.assertIn(record['id'], [row['id'] for row in context['records']])

    def test_ba_actor_entity_inputs_keep_ba_owner_in_engineering_context_projection(self):
        artifact = self.produce('domain-discovery', [self.observation('actors', 'AUTHORITY', 'docs/domain.md'),
                                                  self.observation('entities', 'AUTHORITY', 'docs/domain.md')],
                                authority_authenticator=lambda domain, ref: domain == 'domain' and ref == self.ref('docs/domain.md'))
        auth = lambda domain, ref: domain == 'domain' and ref == self.ref('docs/domain.md')
        state = {'mode': self.mode, 'foundation_profile': {'id': 'arc42-standard-v1', 'level': 'MINIMAL'}}
        manifest = w.candidate_manifest(self.root, state, self.topology, self.policy, 'foundation', 'R1')
        for supplied_manifest in (None, manifest):
            with self.subTest(manifest=supplied_manifest is not None):
                context = p.arc42([artifact], self.root, self.topology, self.policy,
                                  manifest=supplied_manifest, authority_authenticator=auth)['sections']['context_scope']
                self.assertEqual(context['owner'], 'ENGINEERING')
                inputs = [row for row in context['records'] if row['topic'] in ('actors', 'entities')]
                self.assertEqual({row['topic'] for row in inputs}, {'actors', 'entities'})
                self.assertTrue(all(row['owner'] == 'BA' and row['evidence_label'] == 'CONFIRMED' for row in inputs))

    def test_cross_owner_and_same_owner_conflicts_stay_explicit(self):
        domain = self.produce('domain-discovery', [self.observation('entities', 'AUTHORITY', 'docs/domain.md', statement='Canonical collection meaning.')],
                              authority_authenticator=lambda *_: True)
        architecture = self.produce('architecture-discovery', [self.observation('context_scope', statement='Observed collection meaning.')])
        test = self.produce('test-foundation', [self.observation('test_levels', statement='Observed test split.')])
        auth = lambda *_: True
        conflicts = p.conflicts([domain, architecture, test], [{'claims': [
            {'producer': 'domain-discovery', 'record_id': 'entities'},
            {'producer': 'architecture-discovery', 'record_id': 'context-scope'}], 'domain': 'domain'}],
            self.root, self.topology, self.policy, authority_authenticator=auth)
        self.assertEqual(conflicts[0]['preferred_claim']['producer'], 'domain-discovery')
        self.assertEqual(conflicts[0]['status'], 'UNRESOLVED')
        self.assertEqual(len(conflicts[0]['references']), 2)
        same = self.produce('architecture-discovery', [self.observation('runtime', id='old'), self.observation('runtime', id='new', statement='Contradictory runtime.')])
        rows = [{'domain': 'architecture', 'claims': [{'producer': 'architecture-discovery', 'record_id': x} for x in ('old', 'new')]}]
        result = p.conflicts([same], rows, self.root, self.topology, self.policy)
        self.assertIsNone(result[0]['preferred_claim'])
        self.assertEqual(result, p.conflicts([same], rows, self.root, self.topology, self.policy))

    def test_schema_unknown_fields_secrets_owner_label_and_mode_fail_closed(self):
        data = self.produce('architecture-discovery', [self.observation('runtime')])
        for mutate in (lambda d: d.update(prompt='raw'), lambda d: d.update(schema_version=True),
                       lambda d: d['records'][0].update(owner='BA'),
                       lambda d: d['records'][0].update(evidence_label='CONFIRMED'),
                       lambda d: d['records'][0].update(statement='password=hidden'),
                       lambda d: d['records'][0].update(api_key='hidden'),
                       lambda d: d.update(mode='GREENFIELD_BOOTSTRAP')):
            altered = copy.deepcopy(data); mutate(altered)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                p.validate_artifact(altered, self.root, self.topology, self.policy)

    def test_exact_refs_hash_drift_external_paths_and_no_scan(self):
        with patch('os.walk', side_effect=AssertionError('producer must not scan')):
            data = self.produce('architecture-discovery', [self.observation('runtime')])
        for path in ('../outside', 'C:/outside', 'module/../../outside', 'undeclared/file'):
            altered = copy.deepcopy(data); altered['records'][0]['references'][0]['path'] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                p.validate_artifact(altered, self.root, self.topology, self.policy)
        (self.root / 'module/config.json').write_text('{"storage":"remote"}')
        with self.assertRaises(ValueError): p.arc42([data], self.root, self.topology, self.policy)

    def test_shared_policy_paths_valid_and_public_fixture(self):
        self.policy['authority']['domain'] = self.policy['authority']['architecture']
        (self.root / '.sdlc/project-policy.yml').write_bytes(w.semantic_bytes(self.policy))
        row = self.observation('glossary', 'AUTHORITY', 'docs/architecture.md')
        self.produce('domain-discovery', [row], authority_authenticator=lambda domain, ref: domain == 'domain')
        fixture = json.loads((FIXTURES / 'foundation-semantic-producers.json').read_text())
        artifacts = [self.produce(producer, observations) for producer, observations in fixture['brownfield'].items()]
        artifacts.append(p.adr(self.root, self.topology, self.policy, 'fixture-adr', 'R1', self.mode,
                               fixture['adr']['kind'], fixture['adr']['observations']))
        view = p.arc42(artifacts, self.root, self.topology, self.policy)
        self.assertEqual(len(view['sections']), fixture['arc42_expectations']['section_count'])
        for status in fixture['arc42_expectations']['visible_statuses']: self.assertIn(status, view['content'])
        self.mode = 'GREENFIELD_BOOTSTRAP'
        for producer, observations in fixture['greenfield'].items(): self.produce(producer, observations)
        model = p.c4_model(self.root, self.topology, self.policy, 'fixture-c4', 'R1', self.mode,
                           fixture['c4']['elements'], fixture['c4']['relationships'])
        self.assertEqual(p.render_c4(model, self.root, self.topology, self.policy)['artifact_class'], 'DERIVED')

    def test_policy_and_topology_snapshots_are_exact_and_drift_rejected(self):
        data = self.produce('test-foundation', [])
        self.assertEqual(data['project_policy_ref'], self.ref('.sdlc/project-policy.yml'))
        self.assertEqual(data['topology_ref'], self.ref('.sdlc/topology.json'))
        policy = copy.deepcopy(self.policy)
        policy['testing']['automation_repository_role'] = 'alternative_role'
        (self.root / '.sdlc/project-policy.yml').write_bytes(w.semantic_bytes(policy))
        with self.assertRaises(ValueError): p.validate_artifact(data, self.root, self.topology, policy)
        with self.assertRaises(ValueError): self.produce('test-foundation', [])

    def test_c4_optional_component_deployment_and_external_system(self):
        data = self.c4()
        for id, kind, parent in [('adapter', 'COMPONENT', 'service'), ('host', 'DEPLOYMENT_NODE', None),
                                 ('worker', 'INSTANCE', 'host'), ('remote', 'EXTERNAL_SYSTEM', None)]:
            record = self.observation('c4_element', id=id)
            record.update(owner='ENGINEERING', source_producer='c4-modeling', evidence_label='CURRENT_SYSTEM')
            data['records'].append(record)
            node = {'record_id': id, 'kind': kind}
            if parent: node['parent'] = parent
            data['elements'].append(node)
        for id, source, target, level in [('delegates', 'service', 'adapter', 'COMPONENT'),
                                          ('executes', 'host', 'worker', 'DEPLOYMENT'),
                                          ('external', 'service', 'remote', 'CONTAINER')]:
            record = self.observation('c4_relationship', id=id)
            record.update(owner='ENGINEERING', source_producer='c4-modeling', evidence_label='CURRENT_SYSTEM')
            data['records'].append(record)
            data['relationships'].append({'record_id': id, 'source': source, 'target': target, 'level': level})
        p.validate_artifact(data, self.root, self.topology, self.policy)
        data['elements'][-1]['parent'] = 'catalog'
        with self.assertRaises(ValueError): p.validate_artifact(data, self.root, self.topology, self.policy)

    def test_c4_missing_parent_cycle_and_level_mismatch_fail_closed(self):
        for mutate in (lambda d: d['elements'][2].update(parent='missing'),
                       lambda d: d['relationships'][0].update(level='DEPLOYMENT'),
                       lambda d: d['elements'][2].update(parent=d['elements'][2]['record_id'])):
            data = self.c4(); mutate(data)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                p.validate_artifact(data, self.root, self.topology, self.policy)

    def test_architecture_pattern_and_config_rationale_cannot_be_facts(self):
        with self.assertRaises(ValueError): self.produce('architecture-discovery', [self.observation('architecture_pattern')])
        with self.assertRaises(ValueError):
            self.produce('architecture-discovery', [self.observation('historical_rationale', 'DECISION_EVIDENCE')])
        data = self.produce('architecture-discovery', [self.observation('historical_rationale', 'DECISION_EVIDENCE', 'docs/adr/record.md')])
        self.assertEqual(self.labels(data)['historical_rationale'], 'CURRENT_SYSTEM')

    def test_unreviewed_manifest_does_not_approve_projection_or_claims(self):
        self.mode = 'GREENFIELD_BOOTSTRAP'
        data = self.produce('architecture-discovery', [self.observation('solution_strategy', 'PROPOSED')])
        state = {'mode': self.mode, 'foundation_profile': {'id': 'arc42-standard-v1', 'level': 'MINIMAL'}}
        manifest = w.candidate_manifest(self.root, state, self.topology, self.policy, 'foundation', 'R1')
        view = p.arc42([data], self.root, self.topology, self.policy, manifest=manifest)
        self.assertEqual(view['artifact_class'], 'DERIVED')
        self.assertIn('PROPOSED', view['content'])
        manifest['sections']['solution_strategy'].update(evidence='APPROVED_TARGET', references=[self.ref('docs/architecture.md')])
        with self.assertRaises(ValueError): p.arc42([data], self.root, self.topology, self.policy, manifest=manifest)

    def test_product_goals_link_authority_business_rules_stay_outside_arc42(self):
        data = self.produce('domain-discovery', [self.observation('product_goals', 'AUTHORITY', 'docs/product.md', statement='Unique product goal text.'),
                                                self.observation('business_rule', statement='Unique business rule text.')],
                            authority_authenticator=lambda domain, ref: domain == 'product')
        view = p.arc42([data], self.root, self.topology, self.policy, authority_authenticator=lambda *_: True)
        self.assertIn('docs/product.md', view['content'])
        self.assertNotIn('Unique product goal text.', view['content'])
        self.assertNotIn('Unique business rule text.', view['content'])

    def test_unknown_fields_nested_version_duplicate_id_and_raw_references(self):
        row = self.observation('runtime')
        for change in (lambda r: r.update(reasoning_trace='hidden'),
                       lambda r: r['references'][0].update(line=1),
                       lambda r: r['references'][0].pop('revision'),
                       lambda r: r.update(id='BR-001')):
            altered = copy.deepcopy(row); change(altered)
            with self.subTest(change=change), self.assertRaises(ValueError): self.produce('architecture-discovery', [altered])
        with self.assertRaises(ValueError): self.produce('architecture-discovery', [row, copy.deepcopy(row)])
        path = self.root / 'module/prompts/raw.txt'; path.parent.mkdir(); path.write_text('raw prompt')
        with self.assertRaises(ValueError): self.produce('architecture-discovery', [self.observation('runtime', path='module/prompts/raw.txt')])

    def test_reparse_and_symlink_escape_rejected(self):
        row = self.observation('runtime')
        original = Path.lstat
        def reparse(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if path == self.root / 'module':
                class Info:
                    st_mode = result.st_mode
                    st_file_attributes = 0x400
                return Info()
            return result
        with patch.object(Path, 'lstat', reparse), self.assertRaises(ValueError): self.produce('architecture-discovery', [row])
        outside = Path(self.temp.name) / 'external'; outside.write_text('external evidence')
        link = self.root / 'module/escape.txt'
        try: link.symlink_to(outside)
        except OSError as error: self.skipTest('symlink privilege unavailable: ' + str(error))
        row['references'][0]['path'] = 'module/escape.txt'
        with self.assertRaises(ValueError): self.produce('architecture-discovery', [row])

    def test_approved_binding_rejects_receipt_revision_hash_and_authentication_drift(self):
        self.mode = 'GREENFIELD_BOOTSTRAP'
        data = self.adr('PROPOSED', 'PROPOSED'); data['decision_status'] = 'APPROVED_TARGET'
        row = next(row for row in data['records'] if row['topic'] == 'decision')
        row.update(basis='APPROVED_TARGET', evidence_label='APPROVED_TARGET')
        binding = self.approval(data, 'architecture_decisions')
        for mutate in (lambda b: b.update(human_actor_authenticator=lambda *_: False),
                       lambda b: b['approval'].update(revision='R2'),
                       lambda b: b['manifest'].update(revision='R2'),
                       lambda b: b['manifest']['sections']['architecture_decisions'].update(evidence='PROPOSED')):
            altered = copy.deepcopy(binding); mutate(altered)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                p.validate_artifact(data, self.root, self.topology, self.policy, approval_context=altered)
        (self.root / '.sdlc/receipt.json').write_text('{}')
        with self.assertRaises(ValueError): p.validate_artifact(data, self.root, self.topology, self.policy, approval_context=binding)

    def test_refresh_retains_union_and_exact_prior_approval_binding(self):
        self.mode = 'FOUNDATION_REFRESH'
        data = self.adr('PROPOSED', 'PROPOSED')
        data['decision_status'] = 'APPROVED_TARGET'
        row = next(row for row in data['records'] if row['topic'] == 'decision')
        row.update(basis='APPROVED_TARGET', evidence_label='APPROVED_TARGET')
        binding = self.approval(data, 'architecture_decisions')
        previous = copy.deepcopy(binding['manifest'])
        previous['revision'] = 'R0'
        previous['sections']['architecture_decisions'].update(evidence='CURRENT_SYSTEM', references=[self.ref('module/config.json')])
        receipt = read_document((self.root / '.sdlc/receipt.json').read_text())
        receipt.update(previous_revision='R0', previous_manifest_sha256=manifest_sha256(previous))
        (self.root / '.sdlc/receipt.json').write_bytes(w.semantic_bytes(receipt))
        binding.update(approval=self.ref('.sdlc/receipt.json'), previous=previous,
                       human_actor_authenticator=lambda actor, actual: actor == 'synthetic-reviewer' and actual == receipt)
        p.validate_artifact(data, self.root, self.topology, self.policy, approval_context=binding)
        binding['previous']['revision'] = 'R9'
        with self.assertRaises(ValueError): p.validate_artifact(data, self.root, self.topology, self.policy, approval_context=binding)

    def test_test_recommendation_and_stale_architecture_conflicts_do_not_override(self):
        self.mode = 'FOUNDATION_REFRESH'
        architecture = self.produce('architecture-discovery', [
            self.observation('runtime', 'AUTHORITY', 'docs/architecture.md', statement='Documented runtime.', id='documented'),
            self.observation('runtime', statement='Observed different runtime.', id='observed')], authority_authenticator=lambda *_: True)
        test = self.produce('test-foundation', [self.observation('execution_topology', 'PROPOSED', None, statement='Recommend a separate runner.')])
        groups = [{'domain': 'architecture', 'claims': [{'producer': 'architecture-discovery', 'record_id': id} for id in ('documented', 'observed')]},
                  {'domain': 'testing', 'claims': [{'producer': 'architecture-discovery', 'record_id': 'observed'},
                                                   {'producer': 'test-foundation', 'record_id': 'execution-topology'}]}]
        results = p.conflicts([architecture, test], groups, self.root, self.topology, self.policy, authority_authenticator=lambda *_: True)
        self.assertEqual(len(results), 2)
        self.assertTrue(all(row['preferred_claim'] is None and row['status'] == 'UNRESOLVED' for row in results))
        self.assertEqual(results, p.conflicts([test, architecture], list(reversed(groups)), self.root, self.topology, self.policy,
                                             authority_authenticator=lambda *_: True))

    def test_deferred_unknown_and_empty_arc42_do_not_guess_revisions(self):
        self.mode = 'GREENFIELD_BOOTSTRAP'
        data = self.produce('architecture-discovery', [self.observation('deployment', 'DEFERRED', 'docs/architecture.md')])
        self.assertIn('DEFERRED', p.arc42([data], self.root, self.topology, self.policy)['content'])
        with self.assertRaises(ValueError): p.arc42([], self.root, self.topology, self.policy)
        view = p.arc42([], self.root, self.topology, self.policy, configuration_revision='R7')
        self.assertEqual(view['input_references']['topology_ref']['revision'], 'R7')
        self.assertEqual(len(view['sections']), 12)
        for malformed in ([], {'source_producer': []}, {'source_producer': 'unknown'}):
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                p.validate_artifact(malformed, self.root, self.topology, self.policy)

    def test_producer_calls_make_no_filesystem_writes_or_tool_specific_policy(self):
        before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        p.arc42([self.produce('test-foundation', []), self.adr(), self.c4()], self.root, self.topology, self.policy)
        after = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in self.root.rglob('*') if path.is_file()}
        self.assertEqual(before, after)
        source = Path(p.__file__).read_text(encoding='utf-8').lower()
        for tool in ('katalon', 'playwright', 'tea-test'): self.assertNotIn(tool, source)

    def test_final_tree_has_no_temporary_execution_spec(self):
        root = Path(__file__).resolve().parents[2]
        self.assertFalse((root / 'PHASE_3_WAVE_2A_FOUNDATION_SEMANTIC_PRODUCERS_SPEC.md').exists())


if __name__ == '__main__':
    unittest.main()
