"""Project Foundation orchestration. Shared contracts remain the semantic owner.

The trusted host supplies authenticators; this module never creates receipts.
All analysis writes are immutable runtime evidence. Publication is a separate gate.
"""
import copy
import hashlib
import json
from pathlib import Path

from shared.sdlc.approvals.gate_persistence import atomic_workflow
from shared.sdlc.foundation.contract import (FOUNDATION_MANIFEST_V1, SECTION_V1, _approval, foundation_readiness, manifest_sha256,
                                            validate_manifest, validate_transition)
from shared.sdlc.foundation.profiles import PROJECT_FOUNDATION_PROFILE_ARC42_V1 as PROFILE
from shared.sdlc.foundation.impact import knowledge_impact, refresh_outcome, routes
from shared.sdlc.foundation.inventory import declared_repository, inventory, safe_location
from shared.sdlc.policy.contract import AUTHORITY_DOMAINS, validate_policy
from shared.sdlc.promotion.immutable import promotion_record, publish_immutable
from shared.sdlc.provenance.runtime_paths import revision_component
from shared.sdlc.schema import REFERENCE, STRING, VERSION, identifier, object_schema, read_document, safe_file, validate_reference, validate_schema
from shared.sdlc.topology.contract import validate_topology

MODES = tuple(PROFILE['evidence_by_mode'])
STATES = ('ANALYSIS', 'REVIEW_REQUIRED', 'ACCEPTED_BASELINE', 'APPROVED_BASELINE',
          'PROJECT_FOUNDATION_READY')
SEMANTIC_OWNERS = {'product': 'BA', 'domain': 'BA', 'architecture': 'ENGINEERING',
                   'testing': 'TEST', 'features': 'BA'}
SECTION_DOMAINS = {name: 'architecture' for name in PROFILE['sections']}
SECTION_DOMAINS.update(introduction_goals='product', context_scope='domain', glossary='domain',
                      quality_requirements='testing')
RUN_STATE_V1 = object_schema({
    'schema_version': VERSION, 'run_id': STRING, 'project_id': STRING,
    'mode': {'type': 'string', 'enum': MODES},
    'foundation_profile': FOUNDATION_MANIFEST_V1['properties']['profile'],
    'topology_ref': REFERENCE, 'project_policy_ref': REFERENCE,
    'state': {'type': 'string', 'enum': STATES},
    'inputs': {'type': 'array', 'items': REFERENCE},
    'artifacts': {'type': 'object', 'additionalProperties': REFERENCE},
    'open_items': FOUNDATION_MANIFEST_V1['properties']['blockers'],
    'history': {'type': 'array', 'minItems': 1, 'items': object_schema({
        'from': {'enum': (None, *STATES)}, 'to': {'type': 'string', 'enum': STATES}})},
    'promotion': object_schema({'manifest': STRING, 'provenance': STRING})}, optional=('promotion',))


def semantic_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def exact_ref(root, relative, revision):
    revision_component(revision)
    path = safe_file(root, relative)
    return {'path': relative, 'revision': revision, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def _read(root, ref):
    path = validate_reference(ref, root, revision=True)
    return read_document(path.read_text(encoding='utf-8'))


def _publish(writes, transition):
    publish_immutable(writes, stage='FOUNDATION', transition=transition)


def _runtime_path(root, run_id, name):
    revision_component(run_id)
    return safe_location(root, f'.sdlc/runs/foundation/{run_id}/{name}')


def _state_path(root, run_id):
    return _runtime_path(root, run_id, 'run-state.json')


def _load(root, run_id):
    path = _state_path(root, run_id)
    state = read_document(path.read_text(encoding='utf-8'))
    validate_schema(state, RUN_STATE_V1)
    if state['run_id'] != run_id:
        raise ValueError('invalid Foundation run state')
    topology = validate_topology(_read(root, state['topology_ref']))
    policy = validate_policy(_read(root, state['project_policy_ref']))
    if topology['project']['id'] != state['project_id']:
        raise ValueError('run project identity drift')
    for ref in (*state['inputs'], *state['artifacts'].values()): validate_reference(ref, root, revision=True)
    return state, topology, policy


def _declared_ref(root, topology, ref):
    declared_repository(topology, ref['path'])
    if '/.sdlc/' in '/' + ref['path'] or any(part in ('logs', 'raw-output', 'prompts') for part in Path(ref['path']).parts):
        raise ValueError('runtime/raw prompts are not semantic authority inputs')
    return validate_reference(ref, root, revision=True)


def start(root, run_id, mode, topology_ref, project_policy_ref, *, level='MINIMAL'):
    root = Path(root).absolute()
    if mode not in MODES or level not in PROFILE['levels']:
        raise ValueError('unsupported Foundation mode/profile level')
    if project_policy_ref['path'] != '.sdlc/project-policy.yml':
        raise ValueError('canonical Project Policy entry point required')
    topology = validate_topology(_read(root, topology_ref))
    policy = validate_policy(_read(root, project_policy_ref))
    for relative in (*policy['authority'].values(), *policy['artifacts']['optional']):
        declared_repository(topology, relative)
        if '/.sdlc/' in '/' + relative:
            raise ValueError('runtime and durable authority must be separated')
    result = inventory(root, topology, policy)
    directory = _runtime_path(root, run_id, 'inventory.json')
    state = {'schema_version': 1, 'run_id': run_id, 'project_id': topology['project']['id'],
             'mode': mode, 'foundation_profile': {'id': PROFILE['id'], 'level': level},
             'topology_ref': topology_ref, 'project_policy_ref': project_policy_ref,
             'state': 'ANALYSIS', 'inputs': [topology_ref, project_policy_ref],
             'artifacts': {}, 'open_items': [], 'history': [{'from': None, 'to': 'ANALYSIS'}]}
    content = semantic_bytes(result)
    state['artifacts']['inventory'] = {'path': directory.relative_to(root).as_posix(),
                                     'revision': run_id, 'sha256': hashlib.sha256(content).hexdigest()}
    _publish([(directory, content), (_state_path(root, run_id), semantic_bytes(state))], 'START')
    return state


def candidate_manifest(root, state, topology, policy, manifest_id, revision, *, sections=None,
                       blockers=None, authority_authenticator=None):
    """Assemble a structural candidate, never approval or durable authority.

    Section inputs use SECTION_V1 verbatim. CONFIRMED additionally requires a
    trusted host to authenticate the exact canonical policy source references.
    """
    identifier(manifest_id); revision_component(revision)
    if sections is not None:
        validate_schema(sections, object_schema({name: SECTION_V1 for name in PROFILE['sections']},
                                               optional=PROFILE['sections']))
    if blockers is not None:
        validate_schema(blockers, FOUNDATION_MANIFEST_V1['properties']['blockers'])
    entry_points = {}
    gaps = copy.deepcopy(blockers or [])
    for domain in PROFILE['levels'][state['foundation_profile']['level']]['entry_points']:
        relative = policy['authority'].get(domain)
        if relative is None:
            # v1 Policy has no operations authority field; EXTENDED cannot guess it.
            raise ValueError('required Project Policy authority entry point unavailable: ' + domain)
        try:
            entry_points[domain] = exact_ref(root, relative, revision)
        except ValueError:
            gaps.append({'id': 'missing-' + domain, 'critical': True, 'resolved': False})
    defaults = {name: {'status': 'UNKNOWN', 'owner': SEMANTIC_OWNERS[SECTION_DOMAINS[name]],
                       'evidence': 'UNKNOWN', 'blocking': False, 'references': []}
                for name in PROFILE['sections']}
    for name, row in (sections or {}).items():
        if name not in defaults: raise ValueError('unknown Foundation section')
        if row.get('owner') != defaults[name]['owner']:
            raise ValueError('semantic section ownership cannot be reassigned')
        if name == 'architecture_decisions' and row.get('evidence') == 'INFERRED':
            raise ValueError('historical ADR rationale cannot be inferred')
        for ref in row.get('references', []):
            _declared_ref(root, topology, ref)
            if row.get('evidence') == 'CONFIRMED':
                domain = SECTION_DOMAINS[name]
                if ref['path'] != policy['authority'][domain] or not callable(authority_authenticator) or authority_authenticator(domain, ref) is not True:
                    raise ValueError('CONFIRMED requires authenticated exact policy authority')
        defaults[name] = copy.deepcopy(row)
    data = {'schema_version': 1, 'id': manifest_id, 'revision': revision,
            'profile': dict(state['foundation_profile']), 'mode': state['mode'],
            'authority': dict(SEMANTIC_OWNERS), 'entry_points': entry_points,
            'sections': defaults, 'blockers': gaps}
    return validate_manifest(data)


def _candidate(root, state, topology, policy):
    data = validate_manifest(_read(root, state['artifacts']['candidate']))
    if (data['mode'] != state['mode'] or data['profile'] != state['foundation_profile'] or
            data['authority'] != SEMANTIC_OWNERS):
        raise ValueError('candidate/run binding drift')
    for domain, ref in data['entry_points'].items():
        if ref['path'] != policy['authority'].get(domain):
            raise ValueError('conflicting authority entry point')
        _declared_ref(root, topology, ref)
    for name, row in data['sections'].items():
        if row['owner'] != SEMANTIC_OWNERS[SECTION_DOMAINS[name]]:
            raise ValueError('semantic section ownership drift')
        for ref in row['references']: _declared_ref(root, topology, ref)
    review = _read(root, state['artifacts']['review'])
    if review['candidate'] != {'id': data['id'], 'revision': data['revision'], 'sha256': manifest_sha256(data)}:
        raise ValueError('review/candidate exact binding mismatch')
    return data, review


def _previous(root, state, topology):
    ref = state['artifacts'].get('previous')
    if ref is None: return None
    _declared_ref(root, topology, ref)
    return validate_manifest(_read(root, ref))


def prepare(root, run_id, manifest_id, revision, *, sections=None, blockers=None, impact=None,
            previous_ref=None, authority_claims=(), contradictions=(), approval=None,
            human_actor_authenticator=None, authority_authenticator=None):
    root = Path(root).absolute()
    state, topology, policy = _load(root, run_id)
    if state['state'] != 'ANALYSIS':
        raise ValueError('new candidate requires a fresh analysis run')
    if sections is not None:
        validate_schema(sections, object_schema({name: SECTION_V1 for name in PROFILE['sections']},
                                               optional=PROFILE['sections']))
    if blockers is not None:
        validate_schema(blockers, FOUNDATION_MANIFEST_V1['properties']['blockers'])
    if type(authority_claims) not in (tuple, list) or type(contradictions) not in (tuple, list):
        raise ValueError('explicit authority claims/contradictions must be lists')
    previous = None
    if previous_ref is not None:
        _declared_ref(root, topology, previous_ref)
        previous = validate_manifest(_read(root, previous_ref))
    if state['mode'] == 'FOUNDATION_REFRESH' and previous is None:
        raise ValueError('refresh requires exact previous Foundation manifest')
    selected_sections = copy.deepcopy(previous['sections']) if state['mode'] == 'FOUNDATION_REFRESH' else {}
    selected_sections.update(sections or {})
    gaps = copy.deepcopy(previous['blockers'] if state['mode'] == 'FOUNDATION_REFRESH' and blockers is None else (blockers or []))
    conflicts = []
    claims = {}
    for claim in authority_claims:
        if set(claim) != {'domain', 'reference'} or claim['domain'] not in AUTHORITY_DOMAINS:
            raise ValueError('invalid authority claim')
        domain, ref = claim['domain'], claim['reference']
        _declared_ref(root, topology, ref)
        claims.setdefault(domain, []).append(ref)
    for domain, refs in sorted(claims.items()):
        if len(refs) > 1 or refs[0]['path'] != policy['authority'][domain]:
            conflicts.append({'id': 'authority-' + domain, 'kind': 'AUTHORITY_CONFLICT', 'references': refs})
    for index, contradiction in enumerate(contradictions):
        if set(contradiction) != {'domain', 'canonical', 'observed'} or contradiction['domain'] not in AUTHORITY_DOMAINS:
            raise ValueError('invalid source contradiction')
        if contradiction['canonical']['path'] != policy['authority'][contradiction['domain']]:
            raise ValueError('contradiction must name policy authority')
        for name in ('canonical', 'observed'): _declared_ref(root, topology, contradiction[name])
        conflicts.append({'id': 'contradiction-' + str(index + 1), 'kind': 'CURRENT_SYSTEM_CONTRADICTION',
                          'references': [contradiction['canonical'], contradiction['observed']]})
    gaps.extend({'id': row['id'], 'critical': True, 'resolved': False} for row in conflicts)
    data = candidate_manifest(root, state, topology, policy, manifest_id, revision,
                              sections=selected_sections, blockers=gaps, authority_authenticator=authority_authenticator)
    gaps = data['blockers']
    if previous is not None:
        validate_transition(previous, data, root, approval=approval,
                            human_actor_authenticator=human_actor_authenticator)
    if any(row['evidence'] == 'APPROVED_TARGET' for row in data['sections'].values()):
        _approval(data, root, approval, human_actor_authenticator, previous)
    change = copy.deepcopy(knowledge_impact(impact))
    for row in change['areas'].values():
        for target in row['targets']: declared_repository(topology, target)
    if previous is not None:
        for name, row in data['sections'].items():
            if row != previous['sections'][name]:
                change['areas'][SECTION_DOMAINS[name]]['affected'] = True
        for domain in change['areas']:
            if data['entry_points'].get(domain, {}).get('sha256') != previous['entry_points'].get(domain, {}).get('sha256'):
                change['areas'][domain]['affected'] = True
        if data['profile'] != previous['profile'] or data['blockers'] != previous['blockers']:
            change['areas']['architecture']['affected'] = True
    evidence = [{'section': name, 'label': row['evidence'], 'references': row['references'],
                 'owner': row['owner']} for name, row in data['sections'].items()]
    unknowns = [name for name, row in data['sections'].items() if row['evidence'] == 'UNKNOWN' and not row['blocking']]
    proposed = [name for name, row in data['sections'].items() if row['evidence'] == 'PROPOSED']
    critical = [row for row in gaps if row['critical'] and not row['resolved']]
    critical.extend({'id': 'section-' + name, 'critical': True, 'resolved': False}
                    for name, row in data['sections'].items() if row['blocking'] and row['status'] != 'COMPLETE')
    review = {'schema_version': 1, 'mode': state['mode'],
              'candidate': {'id': data['id'], 'revision': revision, 'sha256': manifest_sha256(data)},
              'critical_blockers': critical,
              'noncritical_unknowns': unknowns, 'conflicts': conflicts,
              'proposed_target_decisions': proposed, 'evidence_references': evidence,
              'knowledge_impact': change, 'routes': routes(change),
              'required_decisions': ['HUMAN_EXACT_SNAPSHOT_REVIEW'] + ['ENGINEERING_TARGET:' + name
                  for name in proposed if data['sections'][name]['blocking']],
              'refresh_outcome': refresh_outcome(change) if previous is not None else None,
              'human_approval': False}
    payloads = {'candidate': ('manifest.json', data), 'review': ('review-request.json', review),
                'evidence': ('evidence.json', evidence), 'gaps': ('gaps.json', gaps),
                'questions': ('questions.json', review['required_decisions']), 'impact': ('knowledge-impact.json', change)}
    after = copy.deepcopy(state)
    writes = []
    for key, (name, payload) in payloads.items():
        path = _runtime_path(root, run_id, f'candidates/{revision}/{name}')
        content = semantic_bytes(payload)
        writes.append((path, content))
        after['artifacts'][key] = {'path': path.relative_to(root).as_posix(), 'revision': revision,
                                   'sha256': hashlib.sha256(content).hexdigest()}
    if previous_ref is not None: after['artifacts']['previous'] = previous_ref
    after['inputs'].extend(data['entry_points'].values())
    after['inputs'].extend(ref for row in data['sections'].values() for ref in row['references'])
    after['open_items'] = gaps + [{'id': name, 'critical': False, 'resolved': False} for name in unknowns]
    _publish(writes, 'PREPARE_REVIEW')
    # State is the final publication point; replaying analysis resumes exact writes.
    after['state'] = 'REVIEW_REQUIRED'
    after['history'].append({'from': 'ANALYSIS', 'to': 'REVIEW_REQUIRED'})
    if _load(root, run_id)[0] != state: raise ValueError('Foundation state conflict')
    atomic_workflow(_state_path(root, run_id), after)
    return review


def _eligible(data, review):
    if review['conflicts'] or review['critical_blockers']:
        raise ValueError('unresolved authority conflicts/critical blockers')
    if any(row['blocking'] and row['evidence'] == 'PROPOSED' for row in data['sections'].values()):
        raise ValueError('material proposed target requires explicit approved target binding')


def accept(root, run_id, approval, *, human_actor_authenticator):
    root = Path(root).absolute()
    state, topology, policy = _load(root, run_id)
    if state['state'] not in ('REVIEW_REQUIRED', 'ACCEPTED_BASELINE', 'APPROVED_BASELINE'):
        raise ValueError('Human review required')
    data, review = _candidate(root, state, topology, policy)
    _eligible(data, review)
    previous = _previous(root, state, topology)
    _approval(data, root, approval, human_actor_authenticator, previous)
    foundation_readiness(data, root, approval=approval, previous=previous,
                         human_actor_authenticator=human_actor_authenticator)
    receipt_path = validate_reference(approval, root, revision=True)
    content = receipt_path.read_bytes()
    after = copy.deepcopy(state)
    target = _runtime_path(root, run_id, f'candidates/{data["revision"]}/human-receipt.json')
    _publish([(target, content)], 'HUMAN_REVIEW')
    after['artifacts']['approval'] = dict(approval)
    after['artifacts']['receipt_copy'] = {'path': target.relative_to(root).as_posix(),
                                        'revision': data['revision'], 'sha256': hashlib.sha256(content).hexdigest()}
    next_state = 'APPROVED_BASELINE' if any(row['evidence'] == 'APPROVED_TARGET' for row in data['sections'].values()) else 'ACCEPTED_BASELINE'
    if state['state'] != 'REVIEW_REQUIRED':
        if state['artifacts']['approval'] != approval: raise ValueError('different receipt replay')
        return state
    after['state'] = next_state
    after['history'].append({'from': state['state'], 'to': next_state})
    if _load(root, run_id)[0] != state: raise ValueError('Foundation state conflict')
    atomic_workflow(_state_path(root, run_id), after)
    return after


def promote(root, run_id, destination, provenance_destination, *, human_actor_authenticator):
    root = Path(root).absolute()
    state, topology, policy = _load(root, run_id)
    if state['state'] not in ('ACCEPTED_BASELINE', 'APPROVED_BASELINE', 'PROJECT_FOUNDATION_READY'):
        raise ValueError('promotion requires authenticated Human review')
    data, review = _candidate(root, state, topology, policy)
    _eligible(data, review)
    approval = state['artifacts']['approval']
    previous = _previous(root, state, topology)
    _approval(data, root, approval, human_actor_authenticator, previous)
    foundation_readiness(data, root, approval=approval, previous=previous,
                         human_actor_authenticator=human_actor_authenticator)
    allowed = policy['artifacts']['optional']
    for relative in (destination, provenance_destination):
        if relative not in allowed or relative in policy['authority'].values():
            raise ValueError('durable snapshot location must be explicitly declared in Project Policy artifacts.optional')
        declared_repository(topology, relative)
    if state['state'] == 'PROJECT_FOUNDATION_READY' and state.get('promotion') != {'manifest': destination, 'provenance': provenance_destination}:
        raise ValueError('different promotion replay')
    content = validate_reference(state['artifacts']['candidate'], root, revision=True).read_bytes()
    if content != semantic_bytes(data): raise ValueError('candidate semantic bytes drift')
    receipt_bytes = validate_reference(approval, root, revision=True).read_bytes()
    if validate_reference(state['artifacts']['receipt_copy'], root, revision=True).read_bytes() != receipt_bytes:
        raise ValueError('receipt copy drift')
    record = promotion_record({'id': data['id'], 'revision': data['revision'], 'sha256': manifest_sha256(data)},
                               content, approval, receipt_bytes)
    record.update(source_evidence=review['evidence_references'], mode=data['mode'],
                  knowledge_impact=review['knowledge_impact'], manifest_sha256=manifest_sha256(data))
    _publish([(safe_location(root, destination), content),
              (safe_location(root, provenance_destination), semantic_bytes(record))], 'PROMOTE')
    if state['state'] == 'PROJECT_FOUNDATION_READY': return state
    after = copy.deepcopy(state)
    after['artifacts']['durable_manifest'] = exact_ref(root, destination, data['revision'])
    after['artifacts']['durable_provenance'] = exact_ref(root, provenance_destination, data['revision'])
    after['promotion'] = {'manifest': destination, 'provenance': provenance_destination}
    after['state'] = 'PROJECT_FOUNDATION_READY'
    after['history'].append({'from': state['state'], 'to': after['state']})
    if _load(root, run_id)[0] != state: raise ValueError('Foundation state conflict')
    atomic_workflow(_state_path(root, run_id), after)
    return after


def doctor(root, run_id, *, human_actor_authenticator=None):
    try:
        root = Path(root).absolute()
        state, topology, policy = _load(root, run_id)
        if state['state'] == 'ANALYSIS': return {'status': 'NOT_READY', 'human_approval': False}
        data, review = _candidate(root, state, topology, policy)
        _eligible(data, review)
        previous = _previous(root, state, topology)
        if state['state'] == 'REVIEW_REQUIRED':
            # Structural validation/readiness is not completion of the Human Gate.
            if not any(row['evidence'] == 'APPROVED_TARGET' for row in data['sections'].values()):
                foundation_readiness(data, root, previous=previous)
            return {'status': 'NOT_READY', 'human_approval': False, 'reason': 'Human review required'}
        approval = state['artifacts']['approval']
        _approval(data, root, approval, human_actor_authenticator, previous)
        foundation_readiness(data, root, approval=approval, previous=previous,
                             human_actor_authenticator=human_actor_authenticator)
        if state['state'] != 'PROJECT_FOUNDATION_READY':
            return {'status': 'NOT_READY', 'human_approval': False, 'reason': 'promotion required'}
        if safe_file(root, state['promotion']['manifest']).read_bytes() != semantic_bytes(data):
            raise ValueError('durable approved snapshot drift')
        if state['artifacts']['durable_manifest']['path'] != state['promotion']['manifest'] or state['artifacts']['durable_provenance']['path'] != state['promotion']['provenance']:
            raise ValueError('durable publication reference drift')
        validate_reference(state['artifacts']['receipt_copy'], root, revision=True)
        return {'status': 'PROJECT_FOUNDATION_READY', 'human_approval': False, 'feature_ready': False}
    except (ValueError, OSError, KeyError, TypeError) as error:
        return {'status': 'BLOCKED', 'human_approval': False, 'reason': str(error)}
