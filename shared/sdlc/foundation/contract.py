"""Foundation v1 structure, exact references and pure readiness validation."""
import hashlib
import json
from shared.sdlc.foundation.profiles import PROJECT_FOUNDATION_PROFILE_ARC42_V1 as PROFILE
from shared.sdlc.policy.contract import AUTHORITY_DOMAINS
from shared.sdlc.schema import BOOLEAN, REFERENCE, STRING, VERSION, identifier, object_schema, read_document, reject_secrets, unique, validate_reference, validate_schema

SECTION_V1 = object_schema({
    'status':{'type':'string','enum':PROFILE['statuses']}, 'owner':STRING,
    'evidence':{'type':'string','enum':tuple(dict.fromkeys(e for values in PROFILE['evidence_by_mode'].values() for e in values))},
    'blocking':BOOLEAN, 'references':{'type':'array','items':REFERENCE}})
FOUNDATION_MANIFEST_V1 = object_schema({
    'schema_version':VERSION,'id':STRING,'revision':STRING,
    'profile':object_schema({'id':{'type':'string','enum':(PROFILE['id'],)},
                             'level':{'type':'string','enum':tuple(PROFILE['levels'])}}),
    'mode':{'type':'string','enum':tuple(PROFILE['evidence_by_mode'])},
    'authority':object_schema({key:STRING for key in AUTHORITY_DOMAINS}),
    'entry_points':{'type':'object','properties':{key:REFERENCE for key in (*AUTHORITY_DOMAINS,'operations')},
                    'additionalProperties':False},
    'sections':object_schema({key:SECTION_V1 for key in PROFILE['sections']}),
    'blockers':{'type':'array','items':object_schema({'id':STRING,'critical':BOOLEAN,'resolved':BOOLEAN})}})
APPROVAL_RECEIPT_V1 = object_schema({
    'schema_version':VERSION,'decision':{'type':'string','enum':('APPROVE',)},
    'actor_id':STRING,'actor_role':{'type':'string','enum':('HUMAN',)},
    'artifact_id':STRING,'artifact_revision':STRING,
    'manifest_sha256':{'type':'string','pattern':r'[0-9a-f]{64}'},
    'previous_manifest_sha256':{'type':'string','pattern':r'[0-9a-f]{64}'},
    'previous_revision':STRING,'decision_ref':REFERENCE},
    optional=('previous_manifest_sha256','previous_revision'))


def validate_manifest(data):
    validate_schema(data,FOUNDATION_MANIFEST_V1); reject_secrets(data)
    identifier(data['id']); identifier(data['revision'])
    for owner in data['authority'].values(): identifier(owner)
    for ref in data['entry_points'].values(): validate_reference(ref,revision=True)
    unique([entry['id'] for entry in data['blockers']],'blocker id')
    for blocker in data['blockers']: identifier(blocker['id'])
    for section in data['sections'].values():
        if section['owner'] not in data['authority'].values():
            raise ValueError('section owner is missing/ambiguous in declared authority')
        if section['evidence'] not in PROFILE['evidence_by_mode'][data['mode']]:
            raise ValueError('evidence is invalid for foundation mode')
        if section['status'] == 'COMPLETE' and (section['evidence'] == 'UNKNOWN' or not section['references']):
            raise ValueError('COMPLETE requires known referenced evidence')
        if section['evidence'] != 'UNKNOWN' and not section['references']:
            raise ValueError('known evidence requires exact references')
        paths = [ref['path'] for ref in section['references']]
        unique(paths,'section reference')
        for ref in section['references']: validate_reference(ref,revision=True)
    return data


def read_manifest(text):
    return validate_manifest(read_document(text))


def manifest_sha256(data):
    """Explicit FOUNDATION_MANIFEST_CANONICAL_JSON_V1 semantic identity."""
    validate_manifest(data)
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False,
                                    allow_nan=False).encode('utf-8')).hexdigest()


def _references(data,root):
    for ref in data['entry_points'].values(): validate_reference(ref,root,revision=True)
    for section in data['sections'].values():
        for ref in section['references']: validate_reference(ref,root,revision=True)


def _approval(data, root, approval, authenticator, previous=None):
    if approval is None or not callable(authenticator):
        raise ValueError('APPROVED_TARGET requires explicit host-authenticated Human approval')
    path = validate_reference(approval,root,revision=True)
    receipt_bytes = path.read_bytes()
    if hashlib.sha256(receipt_bytes).hexdigest() != approval['sha256']:
        raise ValueError('approval receipt bytes drifted before parsing')
    receipt = read_document(receipt_bytes.decode('utf-8'))
    validate_schema(receipt,APPROVAL_RECEIPT_V1)
    validate_reference(receipt['decision_ref'],root,revision=True)
    if (receipt['artifact_id'] != data['id'] or receipt['artifact_revision'] != data['revision'] or
            approval['revision'] != data['revision'] or receipt['manifest_sha256'] != manifest_sha256(data)):
        raise ValueError('approval does not bind exact foundation identity/revision/hash')
    if previous is not None:
        if (receipt.get('previous_manifest_sha256') != manifest_sha256(previous) or
                receipt.get('previous_revision') != previous['revision'] or previous['id'] != data['id']):
            raise ValueError('decision does not bind prior observed foundation')
    elif 'previous_manifest_sha256' in receipt or 'previous_revision' in receipt:
        raise ValueError('approval names prior evidence that was not supplied')
    # Caller-supplied trusted host verification; never trust actor_role or a hash alone.
    if authenticator(receipt['actor_id'],receipt) is not True:
        raise ValueError('Human authentication rejected')


def validate_transition(previous, current, root, *, approval=None, human_actor_authenticator=None):
    validate_manifest(previous); validate_manifest(current)
    _references(previous,root); _references(current,root)
    if current['id'] != previous['id']:
        raise ValueError('foundation identity changed')
    if current != previous and current['revision'] == previous['revision']:
        raise ValueError('changed foundation requires a new immutable revision')
    if any(row['evidence'] == 'APPROVED_TARGET' for row in current['sections'].values()):
        _approval(current,root,approval,human_actor_authenticator,previous)
    return manifest_sha256(current)


def foundation_readiness(data, root, *, approval=None, previous=None, human_actor_authenticator=None):
    """No writes, discovery, generation, Human approval or workflow transitions."""
    validate_manifest(data); _references(data,root)
    rules = PROFILE['levels'][data['profile']['level']]
    if set(rules['entry_points']) - data['entry_points'].keys():
        raise ValueError('required foundation entry points missing')
    if any(row['critical'] and not row['resolved'] for row in data['blockers']):
        raise ValueError('critical unresolved foundation blocker')
    for row in data['sections'].values():
        if row['status'] != 'COMPLETE' and (row['blocking'] or row['status'] not in rules['allowed_nonblocking_statuses']):
            raise ValueError('blocking/ineligible incomplete section')
    if previous is not None:
        validate_transition(previous,data,root,approval=approval,
                            human_actor_authenticator=human_actor_authenticator)
    elif any(row['evidence'] == 'APPROVED_TARGET' for row in data['sections'].values()):
        _approval(data,root,approval,human_actor_authenticator)
    return {'status':'PROJECT_FOUNDATION_READY','manifest_sha256':manifest_sha256(data),
            'human_approval':False,'feature_ready':False}
