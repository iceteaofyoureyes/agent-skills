"""BA-owned VNext semantics. Shared Core supplies schemas, refs, IDs and impact.

Functions return validated copies; trusted hosts supply Human receipts/authentication.
No generated output or mutable runtime flag establishes business approval.
"""
import copy
from datetime import datetime
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile

# Load the existing source/installed Shared Core bootstrap without changing its identity.
import contracts as legacy
from shared.sdlc.authority.approved_baseline import _parse_source_rows, _source_id_matches
from shared.sdlc.foundation.contract import foundation_readiness, manifest_sha256, validate_manifest, _approval as foundation_approval
from shared.sdlc.foundation.impact import KNOWLEDGE_IMPACT_V1, knowledge_impact
from shared.sdlc.foundation.inventory import safe_location
from shared.sdlc.promotion.immutable import promotion_record
from shared.sdlc.schema import (REFERENCE, STRING, identifier, object_schema,
    portable_path, read_document, reject_secrets, unique, validate_reference, validate_schema)

V1 = {'type':'integer','enum':(1,)}
V2 = {'type':'integer','enum':(2,)}
HASH = {'type':'string','pattern':r'[0-9a-f]{64}'}
STAMP = {'type':'string','pattern':r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'}
FEATURE = object_schema({'id':STRING,'title':STRING})
REFS = {'type':'array','items':REFERENCE}
STRINGS = {'type':'array','items':STRING}
MODES = ('BROWNFIELD','GREENFIELD','DOCUMENT_ONLY','VISUAL_ASSISTED')
LIFECYCLE = ('DRAFT','VALIDATED','HUMAN_REVIEW','APPROVED_BASELINE')
LABELS = ('CONFIRMED','CURRENT_SYSTEM','INFERRED','PROPOSED','UNKNOWN')
SOURCES = object_schema({role:REFERENCE for role in ('business_rules','srs','decisions')})
IMPLEMENTED = object_schema({role:REFERENCE for role in ('business_rules','srs')},
                            optional=('business_rules','srs'))
FOUNDATION = object_schema({'manifest':REFERENCE,'provenance':REFERENCE,'approval':REFERENCE,'root':STRING,
    'previous':REFERENCE}, optional=('previous',))
EVIDENCE = object_schema({'label':{'type':'string','enum':LABELS},'ref':REFERENCE,
    'topic':STRING,'target_decision_id':STRING}, optional=('target_decision_id',))
BUSINESS_ID = {'type':'string','pattern':r'(?:BR|FR)-(?:[A-Za-z0-9]+-)*\d+'}
IDENTITY = object_schema({'id':BUSINESS_ID,'semantic_key':STRING,
                         'status':{'type':'string','enum':('ACTIVE','RETIRED')}})
DECISION = object_schema({'id':STRING,'topic':STRING,'text':STRING,'actor_id':STRING,
    'actor_role':{'type':'string','enum':('HUMAN',)},'recorded_at':STAMP,'input_refs':REFS,
    'affected_ids':{'type':'array','items':BUSINESS_ID},
    'status':{'type':'string','enum':('CONFIRMED','SUPERSEDED','PROPOSED','UNKNOWN')},
    'supersedes':STRINGS,'superseded_by':STRINGS,'implemented_sources':IMPLEMENTED})
DECISIONS_V1 = object_schema({'schema_version':V1,'feature_id':STRING,
                              'decisions':{'type':'array','items':DECISION}})
CANDIDATE_V1 = object_schema({'schema_version':V1,
    'artifact_type':{'type':'string','enum':('BA_BASELINE_CANDIDATE',)},
    'feature':FEATURE,'id':STRING,'revision':STRING,'mode':{'type':'string','enum':MODES},
    'sources':SOURCES,'domain_refs':REFS,'blocking':STRINGS,'non_blocking':STRINGS,
    'contradictions':STRINGS,'evidence':{'type':'array','items':EVIDENCE},
    'business_identities':{'type':'array','items':IDENTITY},
    'coverage_ids':{'type':'array','items':BUSINESS_ID},'knowledge_impact':KNOWLEDGE_IMPACT_V1,
    'project_foundation':FOUNDATION,'previous_baseline':REFERENCE,'semantic_sha256':HASH},
    optional=('project_foundation','previous_baseline'))
RECEIPT_V1 = object_schema({'schema_version':V1,
    'artifact_type':{'type':'string','enum':('BA_BASELINE',)},
    'decision':{'type':'string','enum':('APPROVE',)},'actor_id':STRING,
    'actor_role':{'type':'string','enum':('HUMAN',)},'recorded_at':STAMP,'feature_id':STRING,
    'baseline_id':STRING,'baseline_revision':STRING,'baseline_semantic_sha256':HASH,
    'baseline_manifest':REFERENCE,'decision_ref':REFERENCE,
    'previous_baseline':object_schema({'id':STRING,'revision':STRING,'semantic_sha256':HASH})},
    optional=('previous_baseline',))
REF_MAP = {'type':'object','properties':{},'additionalProperties':REFERENCE}
EVENT = object_schema({'action':{'type':'string','enum':('SELECT_CANDIDATE','VALIDATE','REQUEST_REVIEW','APPROVE','REJECT','REQUEST_CHANGES','ANSWER')},'from':{'type':'string','enum':LIFECYCLE},
    'to':{'type':'string','enum':LIFECYCLE},'candidate_revision':STRING,'topic':STRING},optional=('topic',))
STATE_V2 = object_schema({'schema_version':V2,'artifact_class':{'type':'string','enum':('RUNTIME',)},
    'feature':FEATURE,'mode':{'type':'string','enum':MODES},
    'operation':{'type':'string','enum':('CREATE','EDIT','REVIEW','CONTINUE')},
    'lifecycle':{'type':'string','enum':LIFECYCLE},'activity':STRING,'candidate_revision':STRING,
    'artifacts':REF_MAP,'authoritative_inputs':REFS,'evidence':{'type':'array','items':EVIDENCE},
    'gaps':STRINGS,'gates':object_schema({'approval':REFERENCE},optional=('approval',)),
    'pending':STRINGS,'source_of_truth':object_schema({'semantic':{'type':'string','enum':('BA_DECISIONS_BR_SRS',)},
        'visual':{'type':'string','enum':('SEPARATE_UX_GATE',)},'delivery':{'type':'string','enum':('DERIVED',)}}),
    'project_foundation':FOUNDATION,'knowledge_impact':KNOWLEDGE_IMPACT_V1,
    'history':{'type':'array','items':EVENT},'edit_scope':STRINGS}, optional=('project_foundation','edit_scope'))
HANDOFF_V2 = object_schema({'schema_version':V2,'feature':FEATURE,
    'ba_baseline':object_schema({'status':{'type':'string','enum':('APPROVED_BASELINE',)},
        'id':STRING,'revision':STRING,'semantic_sha256':HASH,'manifest':REFERENCE}),
    'approval_receipt':REFERENCE,'authoritative_sources':SOURCES,
    'knowledge_impact':KNOWLEDGE_IMPACT_V1,'project_foundation':FOUNDATION,
    'open_items':object_schema({'blocking':STRINGS,'non_blocking':STRINGS}),
    'policy':object_schema({'downstream_may_change_business_semantics':{'type':'boolean','enum':(False,)},
        'downstream_may_make_technical_design_decisions':{'type':'boolean','enum':(True,)}}),
    'next_stage':object_schema({'capability':{'type':'string','enum':('engineering-impact-analysis',)}})},
    optional=('project_foundation',))


def semantic_bytes(data):
    return json.dumps(data, sort_keys=True, separators=(',',':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def candidate_hash(data):
    """BA_BASELINE_CANONICAL_JSON_V1 excludes only the hash field itself."""
    return hashlib.sha256(semantic_bytes({k:v for k,v in data.items() if k != 'semantic_sha256'})).hexdigest()


def _business_id(value):
    if not (_source_id_matches(value,'BR') or _source_id_matches(value,'FR')):
        raise ValueError('canonical FR/BR identity required; BAREF is locator only')


def _check(data, schema):
    validate_schema(data, schema)
    reject_secrets(data)


def _ref_data(ref, root):
    path = validate_reference(ref, Path(root), revision=True)
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != ref['sha256']:
        raise ValueError('reference bytes drifted before parsing')
    return read_document(content.decode('utf-8'))


def _foundation(binding, root, authenticator=None):
    validate_schema(binding, FOUNDATION)
    if binding['root'] != '.': portable_path(binding['root'])
    context_root = Path(root)/binding['root']
    if not context_root.is_dir() or context_root.is_symlink() or not context_root.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('unsafe Foundation project root')
    def local_ref(ref):
        outer_path = validate_reference(ref,Path(root),revision=True)
        try: relative = outer_path.resolve().relative_to(context_root.resolve()).as_posix()
        except ValueError as exc: raise ValueError('Foundation ref must be inside its declared project root') from exc
        return {**ref,'path':relative}

    manifest_ref = local_ref(binding['manifest'])
    provenance_ref = local_ref(binding['provenance'])
    approval_ref = local_ref(binding['approval'])
    data = _ref_data(binding['manifest'], root)
    if binding['manifest']['revision'] != data.get('revision'):
        raise ValueError('Foundation reference revision mismatch')
    previous = _ref_data(binding['previous'], root) if 'previous' in binding else None
    previous_ref = local_ref(binding['previous']) if 'previous' in binding else None
    if previous is not None and previous_ref['revision'] != previous.get('revision'):
        raise ValueError('previous Foundation reference revision mismatch')

    validate_manifest(data)
    if data['revision'] != manifest_ref['revision']:
        raise ValueError('Foundation reference revision mismatch')
    manifest_path = validate_reference(manifest_ref,context_root,revision=True)
    manifest_bytes = manifest_path.read_bytes()
    provenance_path = validate_reference(provenance_ref,context_root,revision=True)
    provenance_bytes = provenance_path.read_bytes()
    provenance = read_document(provenance_bytes.decode('utf-8'))
    receipt_path = validate_reference(approval_ref,context_root,revision=True)
    receipt_bytes = receipt_path.read_bytes()
    if provenance_ref['revision'] != data['revision'] or approval_ref['revision'] != data['revision']:
        raise ValueError('Foundation provenance/approval revision mismatch')
    if not isinstance(provenance,dict) or set(provenance) != {
        'schema_version','source','approval_receipt','human_approval','source_evidence','mode','knowledge_impact','manifest_sha256'}:
        raise ValueError('invalid Foundation promotion provenance shape')
    if type(provenance['schema_version']) is not int or type(provenance['human_approval']) is not bool:
        raise ValueError('invalid Foundation promotion provenance field types')
    expected = promotion_record(provenance['source'],manifest_bytes,approval_ref,receipt_bytes)
    if any(provenance.get(key) != value for key,value in expected.items()):
        raise ValueError('Foundation provenance does not bind exact manifest and approval bytes')
    if (provenance['source'].get('id') != data['id'] or
        provenance['source'].get('revision') != data['revision'] or
        provenance['source'].get('sha256') != hashlib.sha256(manifest_bytes).hexdigest() or
        provenance['manifest_sha256'] != manifest_sha256(data)):
        raise ValueError('Foundation provenance source identity/hash mismatch')
    if provenance['mode'] != data['mode']:
        raise ValueError('Foundation provenance mode mismatch')
    if (not isinstance(provenance['source_evidence'],list) or
        any(not isinstance(item,dict) for item in provenance['source_evidence'])):
        raise ValueError('Foundation provenance source evidence must be an array of records')
    knowledge_impact(provenance['knowledge_impact'])
    # This shared contract checks exact receipt bytes, manifest identity/hash,
    # trusted-host authentication, and any declared prior-manifest rules.
    foundation_approval(data,context_root,approval_ref,authenticator,previous)
    readiness = foundation_readiness(data,context_root,approval=approval_ref,previous=previous,
        human_actor_authenticator=authenticator)
    # Recheck all supplied refs after the trusted-host call.
    for ref in (manifest_ref,provenance_ref,approval_ref): validate_reference(ref,context_root,revision=True)
    if previous_ref is not None: validate_reference(previous_ref,context_root,revision=True)
    return readiness


def validate_decisions(data, root, feature_id, sources=None):
    _check(data, DECISIONS_V1)
    if data['feature_id'] != feature_id: raise ValueError('decisions feature mismatch')
    unique([row['id'] for row in data['decisions']], 'decision id')
    by_id = {row['id']:row for row in data['decisions']}
    for row in data['decisions']:
        identifier(row['id']); identifier(row['actor_id'])
        datetime.strptime(row['recorded_at'],'%Y-%m-%dT%H:%M:%SZ')
        unique(row['affected_ids'],'decision business ID')
        for field in ('supersedes','superseded_by'):
            unique(row[field],field)
            for other in row[field]:
                if other not in by_id or other == row['id']: raise ValueError('invalid decision supersession')
                inverse = 'superseded_by' if field == 'supersedes' else 'supersedes'
                if row['id'] not in by_id[other][inverse]: raise ValueError('supersession must be reciprocal')
        if row['superseded_by'] and row['status'] != 'SUPERSEDED':
            raise ValueError('superseded decision cannot remain current')
        if row['status'] == 'SUPERSEDED' and not row['superseded_by']:
            raise ValueError('superseded decision requires replacement')
        for ref in row['input_refs']: validate_reference(ref,Path(root),revision=True)
        if row['status'] == 'CONFIRMED':
            if not row['input_refs']: raise ValueError('confirmed decision requires exact Human evidence')
            if sources is not None and row['implemented_sources'] != {k:sources[k] for k in ('business_rules','srs')}:
                raise ValueError('latest confirmed decision requires updated exact BR/SRS binding')
        for ref in row['implemented_sources'].values(): validate_reference(ref,Path(root),revision=True)
    return data


def record_answer(decisions, answer, root, *, human_actor_authenticator):
    """Host authenticates supplied Human answer; recording it never approves a baseline."""
    _check(answer,DECISION)
    if answer['status'] != 'CONFIRMED' or not callable(human_actor_authenticator) or human_actor_authenticator(answer['actor_id'],copy.deepcopy(answer)) is not True:
        raise ValueError('confirmed ANSWER requires host-authenticated Human evidence')
    after = copy.deepcopy(decisions)
    if answer['id'] in {row['id'] for row in after['decisions']}:
        raise ValueError('decision ID already exists')
    for row in after['decisions']:
        if row['id'] in answer['supersedes']:
            row['status'] = 'SUPERSEDED'
            row['superseded_by'].append(answer['id'])
    after['decisions'].append(copy.deepcopy(answer))
    return validate_decisions(after,root,after['feature_id'])


def _decision_meaning(data):
    # Binding refresh is mechanical; supplied Human content/currentness is preserved.
    return [{k:v for k,v in row.items() if k != 'implemented_sources'} for row in data['decisions']]


def resolve_question(state, topic, decisions_ref, root, *, human_actor_authenticator, foundation_authenticator=None):
    """Resolve exactly one pending topic using a supplied authenticated Human answer."""
    _check(state,STATE_V2)
    if state['operation'] == 'REVIEW': raise ValueError('REVIEW cannot resolve questions')
    if topic not in state['pending']: raise ValueError('ANSWER must name a pending question')
    decisions = validate_decisions(_ref_data(decisions_ref,root),root,state['feature']['id'])
    answers = [row for row in decisions['decisions'] if row['topic'] == topic and row['status'] == 'CONFIRMED']
    if len(answers) != 1 or not callable(human_actor_authenticator) or human_actor_authenticator(answers[0]['actor_id'],copy.deepcopy(answers[0])) is not True:
        raise ValueError('named ANSWER requires host-authenticated Human decision')
    validate_reference(decisions_ref,Path(root),revision=True)
    after = copy.deepcopy(state)
    after.update(lifecycle='DRAFT',gates={},pending=[item for item in state['pending'] if item != topic])
    after['artifacts']['latest_decisions'] = copy.deepcopy(decisions_ref)
    _event(after,state,'ANSWER')
    after['history'][-1]['topic'] = topic
    validate_state(after,root,foundation_authenticator=foundation_authenticator)
    return after


def _rows(sources, root):
    result = []
    for role, prefix in (('business_rules','BR'),('srs','FR')):
        path = validate_reference(sources[role],Path(root),revision=True)
        result.extend(_parse_source_rows(path,prefix,3,source_path=sources[role]['path']))
    return result


def validate_identity_transition(previous, current):
    if previous['id'] != current['id'] or previous['feature'] != current['feature']:
        raise ValueError('baseline feature/identity changed')
    if previous != current and previous['revision'] == current['revision']:
        raise ValueError('changed candidate requires new revision')
    old = {row['id'].casefold():row for row in previous['business_identities']}
    new = {row['id'].casefold():row for row in current['business_identities']}
    if old.keys() - new.keys(): raise ValueError('removed IDs must remain in retired identity ledger')
    for key, row in old.items():
        replacement = new[key]
        if row['semantic_key'] != replacement['semantic_key'] or (row['status'] == 'RETIRED' and replacement['status'] != 'RETIRED'):
            raise ValueError('business ID cannot be reused for different meaning or after retirement')
    old_keys = {row['semantic_key']:row['id'].casefold() for row in old.values()}
    for row in new.values():
        if row['semantic_key'] in old_keys and old_keys[row['semantic_key']] != row['id'].casefold():
            raise ValueError('continuing semantic item must preserve its stable ID')


def validate_candidate(data, root, *, ready=True, foundation_authenticator=None):
    _check(data,CANDIDATE_V1)
    identifier(data['id']); identifier(data['revision']); identifier(data['feature']['id'])
    if candidate_hash(data) != data['semantic_sha256']: raise ValueError('candidate semantic hash mismatch')
    knowledge_impact(data['knowledge_impact'])
    for ref in [*data['sources'].values(),*data['domain_refs']]: validate_reference(ref,Path(root),revision=True)
    if len({ref['path'] for ref in data['sources'].values()}) != 3:
        raise ValueError('BA authority sources must be distinct')
    for role in ('business_rules','srs'):
        if not data['sources'][role]['path'].endswith('.md'):
            raise ValueError('canonical BR/SRS Markdown required; derived artifacts are not authority')
    rows = _rows(data['sources'],root)
    # Reject explicit technical ownership/design declarations in canonical BA text.
    # Narrative review remains necessary; this is a deterministic field boundary.
    technical = legacy.FORBIDDEN_HANDOFF_KEYS | {'service_boundaries','repository_owner'}
    for role in ('business_rules','srs'):
        text = validate_reference(data['sources'][role],Path(root),revision=True).read_text(encoding='utf-8')
        for line in text.splitlines():
            key = re.match(r'^\s*(?:[-*]\s+|\|\s*)?`?([a-zA-Z_]+)`?\s*(?::|\|)',line)
            if key and key.group(1).lower() in technical:
                raise ValueError('BA authority contains forbidden technical design field')
    canonical = sorted(row.id for row in rows if not row.id.startswith('BAREF:'))
    unique(canonical,'canonical business ID')
    unique(data['coverage_ids'],'coverage ID')
    if data['coverage_ids'] != canonical: raise ValueError('coverage_ids must match canonical FR/BR only')
    identities = data['business_identities']
    unique([row['id'] for row in identities],'business identity')
    unique([row['semantic_key'] for row in identities],'semantic key')
    if {r['id'] for r in identities if r['status'] == 'ACTIVE'} != set(canonical):
        raise ValueError('active business identities must match selected BR/SRS')
    decisions = validate_decisions(_ref_data(data['sources']['decisions'],root),root,data['feature']['id'],
                                  data['sources'] if ready else None)
    current = [row for row in decisions['decisions'] if row['status'] == 'CONFIRMED']
    if ready:
        if data['blocking'] or data['contradictions']: raise ValueError('blocking items/contradictions prevent review')
        if not current or any(row['status'] in ('PROPOSED','UNKNOWN') for row in decisions['decisions']):
            raise ValueError('target requires explicit confirmed Human decisions')
        for row in current:
            if set(row['affected_ids']) - set(canonical): raise ValueError('decision refers to missing canonical business IDs')
    current_by_id = {row['id']:row for row in current}
    for evidence in data['evidence']:
        validate_reference(evidence['ref'],Path(root),revision=True)
        if 'target_decision_id' in evidence and evidence['target_decision_id'] not in current_by_id:
            raise ValueError('CURRENT_SYSTEM/proposal cannot establish target without confirmed decision')
        if 'target_decision_id' in evidence and current_by_id[evidence['target_decision_id']]['topic'] != evidence['topic']:
            raise ValueError('ANSWER resolves only its named topic')
    if 'project_foundation' in data: _foundation(data['project_foundation'],root,foundation_authenticator)
    if 'previous_baseline' in data:
        previous = _ref_data(data['previous_baseline'],root)
        _check(previous,CANDIDATE_V1)
        if (candidate_hash(previous) != previous['semantic_sha256'] or
            data['previous_baseline']['revision'] != previous['revision']):
            raise ValueError('prior baseline identity/hash drift')
        validate_identity_transition(previous,data)
    return {'status':'VALIDATED' if ready else 'DRAFT','human_approval':False,
            'semantic_sha256':data['semantic_sha256'], 'coverage_ids':canonical,
            'authority_ref_ids':sorted(row.id for row in rows)}


def make_candidate(root, *, feature, baseline_id, revision, sources, business_identities, knowledge,
                   mode='GREENFIELD', domain_refs=(), blocking=(), non_blocking=(), contradictions=(),
                   evidence=(), project_foundation=None, previous_baseline=None, foundation_authenticator=None):
    rows = _rows(sources,root)
    data = {'schema_version':1,'artifact_type':'BA_BASELINE_CANDIDATE','feature':copy.deepcopy(feature),
        'id':baseline_id,'revision':revision,'mode':mode,'sources':copy.deepcopy(sources),
        'business_identities':copy.deepcopy(business_identities),
        'coverage_ids':sorted(row.id for row in rows if not row.id.startswith('BAREF:')),
        'domain_refs':list(domain_refs),'blocking':list(blocking),'non_blocking':list(non_blocking),
        'contradictions':list(contradictions),'evidence':list(evidence),'knowledge_impact':copy.deepcopy(knowledge)}
    if project_foundation is not None: data['project_foundation'] = copy.deepcopy(project_foundation)
    if previous_baseline is not None: data['previous_baseline'] = copy.deepcopy(previous_baseline)
    data['semantic_sha256'] = candidate_hash(data)
    validate_candidate(data,root,ready=False,foundation_authenticator=foundation_authenticator)
    return data


def publish_candidate(root, relative, data):
    """Immutable candidate bytes; replay is allowed only for byte-identical content."""
    _check(data,CANDIDATE_V1)
    if candidate_hash(data) != data['semantic_sha256']: raise ValueError('candidate hash mismatch')
    target = safe_location(root,relative)
    content = semantic_bytes(data)
    target.parent.mkdir(parents=True,exist_ok=True)
    safe_location(root,relative)
    try:
        with target.open('xb') as stream: stream.write(content)
    except FileExistsError:
        if target.read_bytes() != content: raise ValueError('immutable candidate already exists with different bytes')
    return {'path':relative,'revision':data['revision'],'sha256':hashlib.sha256(content).hexdigest()}


def read_baseline(ref, root, **kwargs):
    data = _ref_data(ref,root)
    if ref['revision'] != data.get('revision'): raise ValueError('candidate reference revision mismatch')
    return validate_candidate(data,root,**kwargs)


def validate_approval(candidate_ref, approval, root, *, human_actor_authenticator=None, foundation_authenticator=None):
    candidate = _ref_data(candidate_ref,root)
    read_baseline(candidate_ref,root,foundation_authenticator=foundation_authenticator)
    receipt = _ref_data(approval,root)
    _check(receipt,RECEIPT_V1)
    identifier(receipt['actor_id'])
    datetime.strptime(receipt['recorded_at'],'%Y-%m-%dT%H:%M:%SZ')
    validate_reference(receipt['decision_ref'],Path(root),revision=True)
    if (receipt['feature_id'] != candidate['feature']['id'] or receipt['baseline_id'] != candidate['id'] or
        receipt['baseline_revision'] != candidate['revision'] or approval['revision'] != candidate['revision'] or
        receipt['baseline_semantic_sha256'] != candidate['semantic_sha256'] or receipt['baseline_manifest'] != candidate_ref):
        raise ValueError('approval must bind exact baseline identity/revision/hash/manifest')
    previous = _ref_data(candidate['previous_baseline'],root) if 'previous_baseline' in candidate else None
    previous_identity = {k:previous[k] for k in ('id','revision','semantic_sha256')} if previous is not None else None
    if receipt.get('previous_baseline') != previous_identity:
        raise ValueError('receipt prior baseline identity must match selected prior manifest')
    if not callable(human_actor_authenticator) or human_actor_authenticator(receipt['actor_id'],copy.deepcopy(receipt)) is not True:
        raise ValueError('BA approval requires host-authenticated Human decision')
    # Recheck integrity after the trusted host call, which may take time.
    validate_reference(candidate_ref,Path(root),revision=True)
    validate_reference(approval,Path(root),revision=True)
    validate_reference(receipt['decision_ref'],Path(root),revision=True)
    for ref in [*candidate['sources'].values(),*candidate['domain_refs']]:
        validate_reference(ref,Path(root),revision=True)
    if 'previous_baseline' in candidate: validate_reference(candidate['previous_baseline'],Path(root),revision=True)
    if 'project_foundation' in candidate: _foundation(candidate['project_foundation'],root,foundation_authenticator)
    return candidate


def new_state(feature, mode, operation='CREATE', *, edit_scope=None):
    state = {'schema_version':2,'artifact_class':'RUNTIME','feature':copy.deepcopy(feature),'mode':mode,
        'operation':operation,'lifecycle':'DRAFT','activity':'REQUIREMENT_REVIEW','candidate_revision':'UNSELECTED',
        'artifacts':{},'authoritative_inputs':[],'evidence':[],'gaps':[],'gates':{},'pending':[],
        'source_of_truth':{'semantic':'BA_DECISIONS_BR_SRS','visual':'SEPARATE_UX_GATE','delivery':'DERIVED'},
        'knowledge_impact':knowledge_impact(),'history':[]}
    if edit_scope is not None: state['edit_scope'] = list(edit_scope)
    _check(state,STATE_V2)
    _check_edit_scope(state)
    return state


def _event(after, before, action):
    after['history'].append({'action':action,'from':before['lifecycle'],'to':after['lifecycle'],
                             'candidate_revision':after['candidate_revision']})
    return after


def select_candidate(state, candidate_ref, root, *, foundation_authenticator=None):
    _check(state,STATE_V2)
    if state['operation'] == 'REVIEW': raise ValueError('REVIEW cannot mutate candidate or lifecycle')
    candidate = _ref_data(candidate_ref,root)
    read_baseline(candidate_ref,root,ready=False,foundation_authenticator=foundation_authenticator)
    if state['feature'] != candidate['feature'] or state['mode'] != candidate['mode']:
        raise ValueError('candidate feature/mode mismatch')
    if 'latest_decisions' in state['artifacts']:
        latest = _ref_data(state['artifacts']['latest_decisions'],root)
        selected = _ref_data(candidate['sources']['decisions'],root)
        if _decision_meaning(latest) != _decision_meaning(selected):
            raise ValueError('candidate cannot ignore latest confirmed Human decisions')
    if 'candidate' in state['artifacts']:
        old = _ref_data(state['artifacts']['candidate'],root)
        validate_identity_transition(old,candidate)
        if state['operation'] == 'EDIT': validate_edit_scope(state,old,candidate,root)
        if state['artifacts']['candidate'] == candidate_ref: return copy.deepcopy(state)
        if old['revision'] == candidate['revision']: raise ValueError('changed candidate bytes require a new revision')
        if candidate.get('previous_baseline') != state['artifacts']['candidate']:
            raise ValueError('candidate revision must bind prior baseline manifest')
    after = copy.deepcopy(state)
    after.update(lifecycle='DRAFT',candidate_revision=candidate['revision'],gates={},
        authoritative_inputs=list(candidate['sources'].values())+candidate['domain_refs'],
        evidence=copy.deepcopy(candidate['evidence']),gaps=candidate['contradictions']+candidate['blocking'],
        knowledge_impact=copy.deepcopy(candidate['knowledge_impact']))
    # New candidate invalidates cached derived refs; their bytes/history are retained.
    after['artifacts'] = {'candidate':copy.deepcopy(candidate_ref)}
    after.pop('project_foundation',None)
    if 'project_foundation' in candidate: after['project_foundation'] = copy.deepcopy(candidate['project_foundation'])
    return _event(after,state,'SELECT_CANDIDATE')


def validate_state(state, root=None, *, human_actor_authenticator=None, foundation_authenticator=None):
    _check(state,STATE_V2)
    _check_edit_scope(state)
    identifier(state['feature']['id']); identifier(state['candidate_revision'])
    knowledge_impact(state['knowledge_impact'])
    for ref in [*state['artifacts'].values(),*state['authoritative_inputs'],*state['gates'].values()]:
        validate_reference(ref,Path(root) if root is not None else None,revision=True)
    for evidence in state['evidence']:
        validate_reference(evidence['ref'],Path(root) if root is not None else None,revision=True)
    for index,event in enumerate(state['history']):
        if index and event['from'] != state['history'][index-1]['to']: raise ValueError('history lifecycle chain drift')
        if not index and event['from'] != 'DRAFT': raise ValueError('history must start at DRAFT')
        _validate_event(event)
    if state['history'] and state['history'][-1]['to'] != state['lifecycle']: raise ValueError('history/state lifecycle mismatch')
    if state['history'] and state['history'][-1]['candidate_revision'] != state['candidate_revision']:
        raise ValueError('history/candidate revision mismatch')
    if state['lifecycle'] != 'DRAFT' and not state['history']: raise ValueError('lifecycle advancement requires history')
    if 'approval' in state['gates'] and state['lifecycle'] != 'APPROVED_BASELINE':
        raise ValueError('unapproved runtime state cannot carry approval claim')
    if 'candidate' not in state['artifacts']:
        if state['lifecycle'] != 'DRAFT' or state['candidate_revision'] != 'UNSELECTED': raise ValueError('candidate required')
        return state
    if root is None: raise ValueError('exact candidate validation requires project root')
    candidate_ref = state['artifacts']['candidate']
    candidate = _ref_data(candidate_ref,root)
    read_baseline(candidate_ref,root,ready=state['lifecycle'] != 'DRAFT',foundation_authenticator=foundation_authenticator)
    if (state['feature'] != candidate['feature'] or state['mode'] != candidate['mode'] or
        state['candidate_revision'] != candidate['revision'] or state['knowledge_impact'] != candidate['knowledge_impact'] or
        state['authoritative_inputs'] != list(candidate['sources'].values())+candidate['domain_refs'] or
        state.get('project_foundation') != candidate.get('project_foundation') or state['evidence'] != candidate['evidence']):
        raise ValueError('workflow state must bind exact candidate revision/inputs/impact/context')
    if state['lifecycle'] != 'DRAFT' and (state['gaps'] or state['pending']): raise ValueError('blocking pending work prevents review')
    if state['lifecycle'] != 'DRAFT' and 'latest_decisions' in state['artifacts']:
        latest = _ref_data(state['artifacts']['latest_decisions'],root)
        selected = _ref_data(candidate['sources']['decisions'],root)
        if _decision_meaning(latest) != _decision_meaning(selected): raise ValueError('latest Human decision requires a new candidate')
    if state['lifecycle'] == 'APPROVED_BASELINE':
        if 'approval' not in state['gates']: raise ValueError('APPROVED_BASELINE requires exact receipt')
        validate_approval(candidate_ref,state['gates']['approval'],root,
            human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
    return state


def _check_edit_scope(state):
    scope = state.get('edit_scope',[])
    unique(scope,'edit scope')
    if state['operation'] == 'EDIT' and not scope: raise ValueError('EDIT requires explicit target scope')
    fields = set(CANDIDATE_V1['properties']) - {'schema_version','artifact_type','feature','id','revision','semantic_sha256','sources','previous_baseline','coverage_ids','business_identities'}
    for item in scope:
        if item not in fields | {'srs','business_rules','decisions'}: _business_id(item)


def validate_edit_scope(state, previous, current, root):
    _check_edit_scope(state)
    scope = set(state['edit_scope'])
    old_rows = {row.id:row for row in _rows(previous['sources'],root)}
    new_rows = {row.id:row for row in _rows(current['sources'],root)}
    for identity in old_rows.keys() | new_rows.keys():
        old, new = old_rows.get(identity),new_rows.get(identity)
        role = (old or new).source_role
        if role not in scope and identity not in scope and (old is None or new is None or old.text != new.text):
            raise ValueError('EDIT changed business semantics outside target scope')
    old_decisions = _ref_data(previous['sources']['decisions'],root)
    new_decisions = _ref_data(current['sources']['decisions'],root)
    if 'decisions' not in scope:
        # Exact source-binding refresh is mechanical; Human decision content is preserved.
        if _decision_meaning(old_decisions) != _decision_meaning(new_decisions): raise ValueError('EDIT changed decisions outside target scope')
    for field in ('mode','domain_refs','blocking','non_blocking','contradictions','evidence','knowledge_impact','project_foundation'):
        if previous.get(field) != current.get(field) and field not in scope:
            raise ValueError('EDIT changed candidate field outside target scope: '+field)


def _validate_event(event):
    identifier(event['candidate_revision'])
    if event['action'] == 'ANSWER' and 'topic' not in event: raise ValueError('ANSWER history requires named topic')
    if event['action'] != 'ANSWER' and 'topic' in event: raise ValueError('topic is only valid for ANSWER')
    expected = {'VALIDATE':('DRAFT','VALIDATED'), 'REQUEST_REVIEW':('VALIDATED','HUMAN_REVIEW'),
                'APPROVE':('HUMAN_REVIEW','APPROVED_BASELINE')}
    if event['action'] in expected:
        if (event['from'],event['to']) != expected[event['action']]: raise ValueError('unsafe history transition')
    elif event['to'] != 'DRAFT': raise ValueError('candidate selection/rejection must return to DRAFT')


def advance(state, action, root, *, approval=None, human_actor_authenticator=None, foundation_authenticator=None):
    # Rejection/edit requests may invalidate the old approval without authenticating it again.
    _check(state,STATE_V2)
    if action == 'REVIEW':
        validate_state(state,root,human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
        return copy.deepcopy(state)
    if state['operation'] == 'REVIEW': raise ValueError('REVIEW cannot advance lifecycle')
    if action in ('CONTINUE','ANSWER','GENERATED'):
        validate_state(state,root,human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
        return copy.deepcopy(state)
    after = copy.deepcopy(state)
    if action in ('REJECT','REQUEST_CHANGES'):
        after['lifecycle'] = 'DRAFT'; after['gates'] = {}
    else:
        validate_state(state,root,human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
        if action == 'VALIDATE' and state['lifecycle'] == 'DRAFT':
            read_baseline(state['artifacts']['candidate'],root,foundation_authenticator=foundation_authenticator)
            if state['gaps'] or state['pending']: raise ValueError('blocking pending items prevent validation')
            after['lifecycle'] = 'VALIDATED'
        elif action == 'REQUEST_REVIEW' and state['lifecycle'] == 'VALIDATED': after['lifecycle'] = 'HUMAN_REVIEW'
        elif action == 'APPROVE' and state['lifecycle'] == 'HUMAN_REVIEW':
            validate_approval(state['artifacts']['candidate'],approval,root,
                human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
            after['lifecycle'] = 'APPROVED_BASELINE'; after['gates']['approval'] = copy.deepcopy(approval)
        else: raise ValueError('invalid BA lifecycle transition')
    _event(after,state,action)
    validate_state(after,root,human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
    return after


def save_state(root, relative, previous, current, **kwargs):
    """Atomic local persistence; caller must serialize concurrent writers (same as host gates)."""
    portable_path(relative)
    _check(previous,STATE_V2)
    validate_state(current,root,**kwargs)
    if current['history'][:len(previous['history'])] != previous['history']:
        raise ValueError('history must be append-only')
    if current != previous:
        if previous['operation'] == 'REVIEW': raise ValueError('REVIEW cannot persist mutation')
        if len(current['history']) != len(previous['history'])+1:
            raise ValueError('state change requires one appended transition')
        event = current['history'][-1]
        if event['from'] != previous['lifecycle'] or current['feature'] != previous['feature']:
            raise ValueError('state transition identity/history mismatch')
        if event['action'] == 'ANSWER':
            expected = resolve_question(previous,event['topic'],current['artifacts'].get('latest_decisions'),root,
                human_actor_authenticator=kwargs.get('human_actor_authenticator'),
                foundation_authenticator=kwargs.get('foundation_authenticator'))
            if current != expected: raise ValueError('ANSWER may resolve only its named question')
        old_ref = previous['artifacts'].get('candidate')
        new_ref = current['artifacts'].get('candidate')
        if old_ref != new_ref:
            if event['action'] != 'SELECT_CANDIDATE' or new_ref is None: raise ValueError('candidate change requires selection')
            if old_ref is not None:
                candidate = _ref_data(new_ref,root)
                validate_identity_transition(_ref_data(old_ref,root),candidate)
                if previous['operation'] == 'EDIT': validate_edit_scope(previous,_ref_data(old_ref,root),candidate,root)
                if candidate.get('previous_baseline') != old_ref: raise ValueError('prior candidate binding required')
    path = safe_location(root,relative)
    if path.exists() and read_document(path.read_text(encoding='utf-8')) != previous:
        raise ValueError('stale workflow writer')
    path.parent.mkdir(parents=True,exist_ok=True)
    safe_location(root,relative)
    handle, staging = tempfile.mkstemp(prefix='.ba-state-',dir=path.parent)
    try:
        with os.fdopen(handle,'wb') as stream: stream.write(semantic_bytes(current))
        os.replace(staging,path)
    finally:
        if Path(staging).exists(): Path(staging).unlink()


def make_handoff(state, root, *, human_actor_authenticator=None, foundation_authenticator=None):
    validate_state(state,root,human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
    if state['lifecycle'] != 'APPROVED_BASELINE': raise ValueError('handoff requires APPROVED_BASELINE')
    candidate = _ref_data(state['artifacts']['candidate'],root)
    data = {'schema_version':2,'feature':copy.deepcopy(candidate['feature']),
        'ba_baseline':{'status':'APPROVED_BASELINE','id':candidate['id'],'revision':candidate['revision'],
            'semantic_sha256':candidate['semantic_sha256'],'manifest':copy.deepcopy(state['artifacts']['candidate'])},
        'approval_receipt':copy.deepcopy(state['gates']['approval']),
        'authoritative_sources':copy.deepcopy(candidate['sources']),
        'knowledge_impact':copy.deepcopy(candidate['knowledge_impact']),
        'open_items':{'blocking':[],'non_blocking':copy.deepcopy(candidate['non_blocking'])},
        'policy':{'downstream_may_change_business_semantics':False,'downstream_may_make_technical_design_decisions':True},
        'next_stage':{'capability':'engineering-impact-analysis'}}
    if 'project_foundation' in candidate: data['project_foundation'] = copy.deepcopy(candidate['project_foundation'])
    validate_handoff(data,root,human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
    return data


def validate_handoff(data, root, *, human_actor_authenticator=None, foundation_authenticator=None):
    _check(data,HANDOFF_V2)
    candidate = validate_approval(data['ba_baseline']['manifest'],data['approval_receipt'],root,
        human_actor_authenticator=human_actor_authenticator,foundation_authenticator=foundation_authenticator)
    if (data['feature'] != candidate['feature'] or data['authoritative_sources'] != candidate['sources'] or
        data['knowledge_impact'] != candidate['knowledge_impact'] or
        data.get('project_foundation') != candidate.get('project_foundation') or
        data['open_items'] != {'blocking':[],'non_blocking':candidate['non_blocking']} or
        {k:data['ba_baseline'][k] for k in ('id','revision','semantic_sha256')} !=
        {k:candidate[k] for k in ('id','revision','semantic_sha256')}):
        raise ValueError('handoff must bind exact approved candidate sources/impact/open items')
    return {'status':'APPROVED_BASELINE','human_approval':True,'baseline':candidate}
