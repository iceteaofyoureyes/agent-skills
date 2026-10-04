"""Dev VNext semantic contracts (Wave 1), independent of workflow orchestration.

BA owns WHAT; this module only binds technical artifacts to canonical BA proof.
All operations return copies. Trusted hosts authenticate receipts and supply
observed repository revisions; strings, validators and Doctor cannot approve.
The Wave 2 adapter must serialize persistence, observe Git/check execution and
use these contracts before source writes and downstream publication.
"""
import copy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

# Same source/installed dependency bootstrap as Dev V1; never reimplement BA.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ba-workflow/scripts'))
import ba_contracts
import ba_vnext as ba
from shared.sdlc.findings.taxonomy import FindingKind
from shared.sdlc.foundation.impact import KNOWLEDGE_IMPACT_V1, knowledge_impact
from shared.sdlc.schema import (STRING, REFERENCE, object_schema, identifier,
    portable_path, read_document, reject_secrets, unique, validate_reference, validate_schema)

V2 = {'type':'integer','enum':(2,)}
HASH = {'type':'string','pattern':r'[0-9a-f]{64}'}
STAMP = {'type':'string','pattern':r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'}
BUSINESS_ID = ba.BUSINESS_ID
ED_ID = {'type':'string','pattern':r'ED-(?:[A-Za-z0-9]+-)*\d+'}
STRINGS = {'type':'array','items':STRING}
REFS = {'type':'array','items':REFERENCE}
REF_MAP = {'type':'object','properties':{},'additionalProperties':REFERENCE}
STRING_MAP = {'type':'object','properties':{},'additionalProperties':STRING}
SCOPE = {'type':'object','properties':{},'additionalProperties':STRINGS}
# Shared's bounded schema vocabulary has no union types. Nullable refs are
# structurally checked here and semantically checked by _ref/_upstream below.
NULLABLE_REF = {'additionalProperties':True}
MODES = ('FEATURE_DELIVERY','TECHNICAL_MAINTENANCE')
LIFECYCLE = ('INTAKE','AUTHORITY_VALIDATED','IMPACT_ANALYZED','TECHNICAL_PLANNED',
    'IMPLEMENTATION_READY','IMPLEMENTING','ENGINEERING_REVIEW','VERIFYING','READY_FOR_TEST',
    'UPSTREAM_GAP','NEEDS_REPLAN','BLOCKED')
EXCEPTIONS = ('UPSTREAM_GAP','NEEDS_REPLAN','BLOCKED')
RISK_ORDER = {'TRIVIAL':0,'NORMAL':1,'HIGH_RISK':2}
GATE_CATEGORIES = ('PUBLIC_API','SECURITY','PERSISTENCE_SCHEMA','DESTRUCTIVE_MIGRATION',
    'DISTRIBUTED_TRANSACTION','CONCURRENCY','DESTRUCTIVE_DATA','DEPLOYMENT_TOPOLOGY',
    'CROSS_COMPONENT','CROSS_REPOSITORY','MAJOR_DEPENDENCY','PLATFORM','MATERIAL_DEVIATION')
FOUNDATION_CATEGORIES = ('SERVICE_BOUNDARY','DEPLOYMENT_TOPOLOGY','PLATFORM',
    'PUBLIC_INTEGRATION_STRATEGY','CROSS_PROJECT_ARCHITECTURE')
DECISION_CATEGORIES = tuple(dict.fromkeys((*GATE_CATEGORIES,*FOUNDATION_CATEGORIES,'LOCAL_DESIGN')))
CHECK_CATEGORIES = ('BUILD','STATIC','LINT','TYPECHECK','UNIT','COMPONENT','MODULE_LOCAL_INTEGRATION')
PLANNING_NAMES = ('dev-plan.md','dev-tasks.md')
REVIEW_LIMITS = {'full_reviews':1,'blocking_fix_waves':1,'scoped_rereviews':1}


def enum(values):
    return {'type':'string','enum':tuple(values)}


RISK = object_schema({'level':enum(RISK_ORDER),'categories':{'type':'array','items':enum(GATE_CATEGORIES)},'reasons':STRINGS})
REPOSITORY = object_schema({'id':STRING,'role':enum(('IMPLEMENTATION','READ_ONLY')),
    'base_revision':STRING,'allowed_write_paths':STRINGS,'read_only_evidence_paths':STRINGS})
REPOSITORIES = {'type':'array','items':REPOSITORY,'minItems':1}
CHECK = object_schema({'name':STRING,'repository_id':STRING,'category':enum(CHECK_CATEGORIES),
    'command':{'type':'array','items':STRING,'minItems':1}})
CHECKS = {'type':'array','items':CHECK,'minItems':1}
UNKNOWN = object_schema({'id':STRING,'description':STRING,'blocking':{'type':'boolean'}})
IMPACT_V2 = object_schema({'schema_version':V2,'change_id':STRING,'upstream_ref':NULLABLE_REF,
    'repository_base_revisions':STRING_MAP,'affected_repositories':REPOSITORIES,
    'affected_components':STRINGS,'affected_interfaces':STRINGS,'affected_data':STRINGS,
    'dependencies':STRINGS,'constraints':STRINGS,'risk':RISK,
    'technical_unknowns':{'type':'array','items':UNKNOWN},'upstream_gaps':REFS,
    'write_scope':SCOPE,'knowledge_impact':KNOWLEDGE_IMPACT_V1})
DECISION_V2 = object_schema({'schema_version':V2,'id':ED_ID,'change_id':STRING,'topic':STRING,
    'authority_scope':enum(('FEATURE_LOCAL',)),
    'category':enum(DECISION_CATEGORIES),'decision':STRING,'status':enum(('PROPOSED','APPROVED','SUPERSEDED')),
    'evidence_refs':{'type':'array','items':REFERENCE,'minItems':1},'upstream_refs':REFS,
    'affected_repositories':STRINGS,'affected_components':STRINGS,'affected_interfaces':STRINGS,
    'affected_data':STRINGS,'alternatives':STRINGS,'consequences':STRINGS,'risk':enum(RISK_ORDER),
    'materiality':enum(('MATERIAL',)),'approval_requirement':enum(('HUMAN',)),
    'approval_ref':REFERENCE,'supersedes':{'type':'array','items':ED_ID},
    'superseded_by':{'type':'array','items':ED_ID},'adr_ref':REFERENCE},optional=('approval_ref','adr_ref'))
GAP_V2 = object_schema({'schema_version':V2,'gap_id':STRING,
    'finding_kind':enum((FindingKind.SPEC_GAP.value,FindingKind.BUSINESS_DECISION_REQUIRED.value)),
    'feature_id':STRING,'engineering_handoff_ref':REFERENCE,
    'affected_business_ids':{'type':'array','items':BUSINESS_ID,'minItems':1},
    'evidence_refs':{'type':'array','items':REFERENCE,'minItems':1},'question':STRING,
    'blocking_scope':SCOPE,'discovered_at':STAMP,'status':enum(('OPEN','RESOLVED')),
    'resolution_ref':REFERENCE,'replacement_handoff_ref':REFERENCE},optional=('resolution_ref','replacement_handoff_ref'))
MAINTENANCE = object_schema({'kind':enum(('DOCUMENTATION','RENAME','MECHANICAL','TOOLING_CONFIG')),
    'evidence_refs':{'type':'array','items':REFERENCE,'minItems':1},
    'no_what_change':{'type':'boolean','enum':(True,)},'discovered_changes':STRINGS})
EVENT = object_schema({'from':enum(LIFECYCLE),'to':enum(LIFECYCLE),
    'action':enum(('ADVANCE','IMPACT','PLAN','FINALIZE','GAP','REPLAN','BLOCK','ESCALATE','APPROVAL','RESOLVE_GAP')),
    'before_sha256':HASH,'after_sha256':HASH})
BUDGET = object_schema({key:{'type':'integer'} for key in REVIEW_LIMITS})
GAP_BINDING = object_schema({'gap_ref':REFERENCE,'resolution_ref':REFERENCE,'replacement_handoff_ref':REFERENCE},
    optional=('gap_ref','resolution_ref','replacement_handoff_ref'))
STATE_V2 = object_schema({'schema_version':V2,'artifact_class':enum(('RUNTIME',)),
    'run_id':STRING,'change_id':STRING,'summary':STRING,'authority_mode':enum(MODES),'feature_id':STRING,
    'lifecycle':enum(LIFECYCLE),'risk':RISK,'upstream':NULLABLE_REF,'delivery':NULLABLE_REF,
    'repositories':REPOSITORIES,'checks':CHECKS,'artifacts':REF_MAP,'gates':REF_MAP,
    'open_items':STRINGS,'engineering_gap':GAP_BINDING,'history':{'type':'array','items':EVENT},
    'review_budget':BUDGET,'verification':REF_MAP,'maintenance':MAINTENANCE},optional=('feature_id','maintenance'))
SNAPSHOT_V2 = object_schema({'schema_version':V2,'artifact_class':enum(('RUNTIME',)),
    'run_id':STRING,'change_id':STRING,'revision':STRING,'authority_mode':enum(MODES),
    'upstream':NULLABLE_REF,'delivery':NULLABLE_REF,'engineering_impact':NULLABLE_REF,
    'engineering_decisions':REFS,'dev_plan':NULLABLE_REF,'dev_tasks':NULLABLE_REF,
    'repositories':REPOSITORIES,'repository_base_revisions':STRING_MAP,'write_scope':SCOPE,'risk':RISK,'checks':CHECKS})
TECHNICAL_RECEIPT_V2 = object_schema({'schema_version':V2,'artifact_type':enum(('DEV_TECHNICAL_APPROVAL',)),
    'decision':enum(('APPROVE',)),'actor_id':STRING,'actor_role':enum(('HUMAN','TECH_LEAD')),'recorded_at':STAMP,
    'run_id':STRING,'change_id':STRING,'snapshot_revision':STRING,'snapshot_sha256':HASH,
    'snapshot_ref':REFERENCE,'decision_evidence_ref':REFERENCE})
DECISION_RECEIPT_V2 = object_schema({'schema_version':V2,'artifact_type':enum(('ENGINEERING_DECISION_APPROVAL',)),
    'decision':enum(('APPROVE',)),'actor_id':STRING,'actor_role':enum(('HUMAN','TECH_LEAD')),'recorded_at':STAMP,
    'change_id':STRING,'engineering_decision_id':ED_ID,'decision_sha256':HASH,'decision_evidence_ref':REFERENCE})
COVERAGE_ROW = object_schema({'id':BUSINESS_ID,'status':enum(('COVERED',)),
    'code_refs':{'type':'array','items':REFERENCE,'minItems':1},'test_refs':{'type':'array','items':REFERENCE,'minItems':1}})
COVERAGE = {'type':'array','items':COVERAGE_ROW}
CHECK_RESULT = object_schema({**CHECK['properties'],'status':enum(('PASS','FAIL','NOT_RUN')),
    'exit_code':{'type':'integer'},'evidence_ref':REFERENCE})
VERIFICATION = object_schema({'snapshot_sha256':HASH,'repository_revisions':STRING_MAP,'recorded_at':STAMP,
    'checks':{'type':'array','items':CHECK_RESULT,'minItems':1}})
REVIEW = object_schema({'snapshot_sha256':HASH,'repository_revisions':STRING_MAP,'recorded_at':STAMP,
    'evidence_refs':{'type':'array','items':REFERENCE,'minItems':1},'blocking_findings':STRINGS,'budget':BUDGET})
IMPLEMENTATION_ROW = object_schema({'repository_id':STRING,'revision':STRING,'changed_paths':STRINGS,
    'evidence_refs':{'type':'array','items':REFERENCE,'minItems':1}})
FINAL_EVIDENCE = object_schema({'repository_revisions':STRING_MAP,'implementation':{'type':'array','items':IMPLEMENTATION_ROW},
    'requirements_coverage':COVERAGE,'review':REVIEW,'engineering_verification':VERIFICATION})
STATE_V2['properties']['verification'] = object_schema(FINAL_EVIDENCE['properties'],optional=tuple(FINAL_EVIDENCE['properties']))
HANDOFF_V2 = object_schema({'schema_version':V2,'artifact_class':enum(('HANDOFF_MANIFEST',)),
    'change_id':STRING,'authority_mode':enum(MODES),'feature':NULLABLE_REF,
    'upstream_engineering_handoff':NULLABLE_REF,'delivery_manifest':NULLABLE_REF,
    'engineering_impact':NULLABLE_REF,'engineering_decisions':REFS,'technical_approval':NULLABLE_REF,
    'technical_snapshot':REFERENCE,'repository_revisions':STRING_MAP,
    'implementation':{'type':'array','items':IMPLEMENTATION_ROW},'requirements_coverage':COVERAGE,
    'engineering_verification':VERIFICATION,'review':REVIEW,'known_risks':STRINGS,
    'knowledge_impact':KNOWLEDGE_IMPACT_V1,'state':enum(('READY_FOR_TEST',)),
    'run_state':STATE_V2})


def semantic_bytes(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(semantic_bytes(value)).hexdigest()


def _check(data, schema):
    validate_schema(data,schema)
    reject_secrets(data)


def _ref(ref, root=None):
    return validate_reference(ref,Path(root) if root is not None else None,revision=True)


def _data(ref, root):
    content = _ref(ref,root).read_bytes()
    if hashlib.sha256(content).hexdigest() != ref['sha256']:
        raise ValueError('reference drift before parsing')
    return read_document(content.decode('utf-8'))


def _stamp(value):
    return datetime.strptime(value,'%Y-%m-%dT%H:%M:%SZ')


def _bases(repositories):
    return {row['id']:row['base_revision'] for row in repositories}


def _scope(repositories):
    return {row['id']:row['allowed_write_paths'] for row in repositories}


def _risk(value):
    _check(value,RISK)
    unique(value['categories'],'risk category')
    if value['categories'] and value['level'] != 'HIGH_RISK':
        raise ValueError('mandatory technical risk cannot downgrade')


def _repositories(rows):
    _check(rows,REPOSITORIES)
    unique([row['id'] for row in rows],'repository identity')
    for row in rows:
        identifier(row['id']); identifier(row['base_revision'])
        for field in ('allowed_write_paths','read_only_evidence_paths'):
            unique(row[field],field)
            for path in row[field]: portable_path(path)
        if row['role'] == 'READ_ONLY' and row['allowed_write_paths']:
            raise ValueError('read-only repository cannot have write scope')
        if row['role'] == 'IMPLEMENTATION' and not row['allowed_write_paths']:
            raise ValueError('implementation repository requires explicit write scope')
        for path in row['allowed_write_paths']:
            if any(_overlap(path,other) for other in row['read_only_evidence_paths']):
                raise ValueError('write scope overlaps read-only evidence')


def _checks(checks, repositories):
    _check(checks,CHECKS)
    unique([row['name'] for row in checks],'engineering check')
    roles={row['id']:row['role'] for row in repositories}
    for row in checks:
        if roles.get(row['repository_id'])!='IMPLEMENTATION':
            raise ValueError('engineering check requires an implementation repository')


def _overlap(left, right):
    left,right = left.casefold(),right.casefold()
    return left == right or left.startswith(right+'/') or right.startswith(left+'/')


def _all_refs(value):
    if isinstance(value,dict):
        if {'path','sha256'} <= value.keys():
            yield value
        else:
            for item in value.values(): yield from _all_refs(item)
    elif isinstance(value,list):
        for item in value: yield from _all_refs(item)


def read_upstream(ref, root, *, ba_authenticator=None, foundation_authenticator=None, **_):
    """Dispatch V1 for inspection, V2 through the single canonical BA validator."""
    path = _ref(ref,root)
    text = path.read_text(encoding='utf-8')
    fields, _, _, _ = ba_contracts.legacy._yaml_fields(text)
    if fields.get(('schema_version',)) == '1':
        result = ba_contracts.read_handoff(path)
        _ref(ref,root)
        return {**result,'mode':'LEGACY_COMPAT','vnext_authority':False}
    data = read_document(text)
    result = ba.validate_handoff(data,root,human_actor_authenticator=ba_authenticator,
                                foundation_authenticator=foundation_authenticator)
    _ref(ref,root)  # Host callback may have taken time or changed bytes.
    if ref['revision'] != data['ba_baseline']['revision']:
        raise ValueError('Engineering Handoff revision must bind BA revision')
    return {'mode':'VNEXT','vnext_authority':True,'handoff':copy.deepcopy(data),**result}


def _upstream(state, root, **context):
    if state['authority_mode'] == 'TECHNICAL_MAINTENANCE':
        if state['upstream'] is not None or 'feature_id' in state:
            raise ValueError('maintenance cannot claim feature authority')
        proof = state.get('maintenance')
        _check(proof,MAINTENANCE)
        if proof['discovered_changes'] or state['risk']['level'] != 'TRIVIAL' or len(state['repositories']) != 1:
            raise ValueError('BLOCKED: require FEATURE_DELIVERY authority; maintenance fast path invalidated')
        for ref in proof['evidence_refs']: _ref(ref,root)
        return None
    if 'maintenance' in state: raise ValueError('feature delivery cannot use maintenance authority')
    result = read_upstream(state['upstream'],root,**context)
    if not result['vnext_authority']: raise ValueError('LEGACY_COMPAT cannot authorize VNext feature delivery')
    if state.get('feature_id',result['handoff']['feature']['id']) != result['handoff']['feature']['id']:
        raise ValueError('upstream feature identity mismatch')
    return result


def _protect_upstream(state, result, root):
    if result is None: return
    pending = [state['upstream'],*_all_refs(result['handoff']),*_all_refs(result['baseline'])]
    protected = set()
    foundation_root = result['handoff'].get('project_foundation',{}).get('root','.')
    # Protect transitive BA/receipt/Foundation dependencies too, including Human
    # decision evidence and prior baselines. Markdown remains opaque BA bytes.
    while pending:
        ref = pending.pop()
        if ref['path'].casefold() in protected: continue
        protected.add(ref['path'].casefold())
        path = validate_reference(ref,Path(root))
        try: document = read_document(path.read_text(encoding='utf-8'))
        except (ValueError,UnicodeError): continue
        children = list(_all_refs(document))
        if foundation_root != '.' and ref['path'].startswith(foundation_root+'/'):
            children = [{**child,'path':foundation_root+'/'+child['path']} for child in children]
        pending.extend(children)
    for repository in state['repositories']:
        for write in repository['allowed_write_paths']:
            if any(_overlap(write,path) for path in protected):
                raise ValueError('BA upstream paths are immutable; write scope overlaps authority')


def validate_impact(data, root, *, upstream=None, repositories=None, **context):
    _check(data,IMPACT_V2)
    identifier(data['change_id']); _repositories(data['affected_repositories']); _risk(data['risk'])
    if data['upstream_ref'] is not None: _ref(data['upstream_ref'],root)
    if upstream is not None and data['upstream_ref'] != upstream:
        raise ValueError('impact requires exact upstream ref')
    if repositories is not None and data['affected_repositories'] != repositories:
        raise ValueError('impact repository scope/base drift')
    if data['repository_base_revisions'] != _bases(data['affected_repositories']) or data['write_scope'] != _scope(data['affected_repositories']):
        raise ValueError('impact base/write-scope mismatch')
    if len(data['affected_repositories']) > 1 and data['risk']['level'] != 'HIGH_RISK':
        raise ValueError('cross-repository impact requires HIGH_RISK')
    unique([row['id'] for row in data['technical_unknowns']],'technical unknown')
    for ref in data['upstream_gaps']: _ref(ref,root)
    knowledge_impact(data['knowledge_impact'])
    return copy.deepcopy(data)


def decision_hash(data):
    """ED content approval excludes disposition/receipt and supersession backlink."""
    return digest({k:v for k,v in data.items() if k not in ('status','approval_ref','superseded_by')})


def _authenticate(receipt, authenticator):
    identifier(receipt['actor_id']); _stamp(receipt['recorded_at'])
    if not callable(authenticator) or authenticator(receipt['actor_id'],copy.deepcopy(receipt)) is not True:
        raise ValueError('exact approval requires trusted-host authenticated Human / Tech Lead proof')


def validate_decision(data, root, *, change_id, upstream, technical_authenticator=None):
    _check(data,DECISION_V2)
    if data['change_id'] != change_id or (upstream is not None and upstream not in data['upstream_refs']):
        raise ValueError('ED requires exact change/upstream traceability')
    identifier(data['id'])
    for field in ('affected_repositories','supersedes','superseded_by'):
        unique(data[field],field)
    for ref in [*data['upstream_refs'],*data['evidence_refs']]: _ref(ref,root)
    if data['category'] in FOUNDATION_CATEGORIES:
        if 'adr_ref' not in data:
            raise ValueError('ARCHITECTURE_DECISION_REQUIRED: project architecture routes to Foundation / Engineering ADR')
        _ref(data['adr_ref'],root)
        if data['adr_ref']['path'].startswith(('.devkit/','.sdlc/runs/')):
            raise ValueError('ARCHITECTURE_DECISION_REQUIRED: project ADR authority cannot live in Dev runtime')
    if data['category'] in GATE_CATEGORIES and data['risk'] != 'HIGH_RISK':
        raise ValueError('material category requires HIGH_RISK')
    if data['status'] == 'SUPERSEDED' and not data['superseded_by']:
        raise ValueError('superseded ED requires explicit replacement')
    if data['superseded_by'] and data['status'] != 'SUPERSEDED':
        raise ValueError('replaced ED cannot remain current')
    if data['status'] == 'APPROVED' or 'approval_ref' in data:
        receipt = _data(data.get('approval_ref'),root)
        _check(receipt,DECISION_RECEIPT_V2)
        if (receipt['change_id'] != change_id or receipt['engineering_decision_id'] != data['id'] or
            receipt['decision_sha256'] != decision_hash(data)):
            raise ValueError('ED approval content mismatch')
        _ref(receipt['decision_evidence_ref'],root)
        _authenticate(receipt,technical_authenticator)
        _ref(data['approval_ref'],root); _ref(receipt['decision_evidence_ref'],root)
        for ref in [*data['upstream_refs'],*data['evidence_refs']]: _ref(ref,root)
        if 'adr_ref' in data: _ref(data['adr_ref'],root)
    return copy.deepcopy(data)


def _decision_set(refs, root, state, **context):
    unique([ref['path'] for ref in refs],'ED artifact')
    rows = [validate_decision(_data(ref,root),root,change_id=state['change_id'],upstream=state['upstream'],
                             technical_authenticator=context.get('technical_authenticator')) for ref in refs]
    unique([row['id'] for row in rows],'ED identity')
    by_id = {row['id']:row for row in rows}
    for row in rows:
        if set(row['affected_repositories']) - _bases(state['repositories']).keys():
            raise ValueError('ED repository outside declared scope')
        for key,inverse in (('supersedes','superseded_by'),('superseded_by','supersedes')):
            for other in row[key]:
                if other == row['id'] or other not in by_id or row['id'] not in by_id[other][inverse]:
                    raise ValueError('ED supersession requires reciprocal exact identities')
        def visit(identity, ancestors):
            if identity in ancestors: raise ValueError('cyclic ED supersession')
            for parent in by_id[identity]['supersedes']: visit(parent,ancestors|{identity})
        visit(row['id'],set())
        if RISK_ORDER[row['risk']] > RISK_ORDER[state['risk']['level']]:
            raise ValueError('ED risk requires escalation and replan')
    return rows


def validate_gap(data, root, *, required_ids):
    _check(data,GAP_V2)
    identifier(data['gap_id']); identifier(data['feature_id']); _stamp(data['discovered_at'])
    unique(data['affected_business_ids'],'gap business ID')
    if set(data['affected_business_ids']) - set(required_ids): raise ValueError('gap contains unknown BR/FR')
    if not data['blocking_scope']: raise ValueError('gap requires exact blocking scope')
    for paths in data['blocking_scope'].values():
        if not paths: raise ValueError('gap blocking paths required')
        for path in paths: portable_path(path)
    for ref in [data['engineering_handoff_ref'],*data['evidence_refs']]: _ref(ref,root)
    if data['status'] == 'OPEN' and ('resolution_ref' in data or 'replacement_handoff_ref' in data):
        raise ValueError('open gap cannot claim resolution')
    if data['status'] == 'RESOLVED':
        for key in ('resolution_ref','replacement_handoff_ref'): _ref(data.get(key),root)
    return copy.deepcopy(data)


def validate_coverage(rows, required_ids, root):
    _check(rows,COVERAGE)
    unique(required_ids,'upstream coverage ID'); unique([row['id'] for row in rows],'coverage ID')
    for identity in required_ids: validate_schema(identity,BUSINESS_ID)
    if {row['id'] for row in rows} != set(required_ids):
        raise ValueError('coverage must equal exact approved BA FR/BR set; BAREF is locator only')
    for row in rows:
        for ref in [*row['code_refs'],*row['test_refs']]: _ref(ref,root)
    return copy.deepcopy(rows)


def _state_hash(state):
    return digest({key:value for key,value in state.items() if key != 'history'})


def _event(before, after, action):
    after['history'].append({'from':before['lifecycle'],'to':after['lifecycle'],'action':action,
        'before_sha256':_state_hash(before),'after_sha256':_state_hash(after)})
    return after


def _edge(before, after, mode, risk, action):
    if after in EXCEPTIONS:
        actions = {'UPSTREAM_GAP':('GAP',),'NEEDS_REPLAN':('REPLAN','ESCALATE'),'BLOCKED':('BLOCK',)}
        return before != 'READY_FOR_TEST' and action in actions[after]
    if before == after: return action == 'APPROVAL' and before == 'TECHNICAL_PLANNED'
    if action == 'RESOLVE_GAP': return before == 'UPSTREAM_GAP' and after == 'AUTHORITY_VALIDATED'
    if action == 'REPLAN': return before == 'NEEDS_REPLAN' and after == 'AUTHORITY_VALIDATED'
    specialized = {'IMPACT':('AUTHORITY_VALIDATED','IMPACT_ANALYZED'),
                   'PLAN':('IMPACT_ANALYZED','TECHNICAL_PLANNED'),'FINALIZE':('VERIFYING','READY_FOR_TEST')}
    if action in specialized: return (before,after) == specialized[action] and (action == 'FINALIZE' or mode == 'FEATURE_DELIVERY')
    if action != 'ADVANCE' or after in ('IMPACT_ANALYZED','TECHNICAL_PLANNED','READY_FOR_TEST'): return False
    order = LIFECYCLE[:9]
    if mode == 'TECHNICAL_MAINTENANCE' and risk == 'TRIVIAL':
        order = ('INTAKE','AUTHORITY_VALIDATED','IMPLEMENTATION_READY','IMPLEMENTING','VERIFYING','READY_FOR_TEST')
    return before in order and before != order[-1] and after == order[order.index(before)+1]


def validate_transition(previous, current):
    """Persistence adapters must call this against their stored prior state."""
    _check(previous,STATE_V2); _check(current,STATE_V2)
    if current['history'][:len(previous['history'])] != previous['history'] or len(current['history']) != len(previous['history'])+1:
        raise ValueError('transition history must append exactly one event')
    for key in ('run_id','change_id','summary','authority_mode','repositories','checks','delivery','maintenance'):
        if previous.get(key) != current.get(key): raise ValueError('immutable run contract changed: '+key)
    if 'feature_id' in previous and previous['feature_id'] != current.get('feature_id'):
        raise ValueError('immutable feature identity changed')
    if RISK_ORDER[current['risk']['level']] < RISK_ORDER[previous['risk']['level']]:
        raise ValueError('risk downgrade forbidden')
    if not set(previous['risk']['categories']) <= set(current['risk']['categories']):
        raise ValueError('risk category removal forbidden')
    event = current['history'][-1]
    if event['before_sha256'] != _state_hash(previous) or event['after_sha256'] != _state_hash(current):
        raise ValueError('transition snapshot mismatch')
    if event['from'] != previous['lifecycle'] or event['to'] != current['lifecycle'] or not _edge(
        event['from'],event['to'],current['authority_mode'],current['risk']['level'],event['action']):
        raise ValueError('unsafe lifecycle transition')
    if previous['upstream'] != current['upstream'] and event['action'] != 'RESOLVE_GAP':
        raise ValueError('upstream replacement requires first-class resolved gap')
    return copy.deepcopy(current)


def new_state(*, run_id, change_id, summary, authority_mode, repositories, checks,
              upstream=None, delivery=None, maintenance=None):
    repositories=copy.deepcopy(repositories)
    _repositories(repositories)
    implementation_repositories=[row for row in repositories if row['role']=='IMPLEMENTATION']
    checks=copy.deepcopy(checks)
    if len(implementation_repositories)==1 and isinstance(checks,list):
        for row in checks:
            if isinstance(row,dict) and 'repository_id' not in row:
                row['repository_id']=implementation_repositories[0]['id']
    data = {'schema_version':2,'artifact_class':'RUNTIME','run_id':run_id,'change_id':change_id,
        'summary':summary,'authority_mode':authority_mode,'lifecycle':'INTAKE',
        'risk':{'level':'TRIVIAL' if authority_mode == 'TECHNICAL_MAINTENANCE' else 'NORMAL','categories':[],'reasons':[]},
        'upstream':copy.deepcopy(upstream),'delivery':copy.deepcopy(delivery),'repositories':copy.deepcopy(repositories),
        'checks':copy.deepcopy(checks),'artifacts':{},'gates':{},'open_items':[],'engineering_gap':{},'history':[],
        'review_budget':{key:0 for key in REVIEW_LIMITS},'verification':{}}
    if maintenance is not None: data['maintenance'] = copy.deepcopy(maintenance)
    _check(data,STATE_V2); _checks(data['checks'],data['repositories'])
    identifier(run_id); identifier(change_id)
    if upstream is not None: _ref(upstream)
    if delivery is not None: _ref(delivery)
    return data


def _budget(value, *, completed=False):
    _check(value,BUDGET)
    for key,limit in REVIEW_LIMITS.items():
        if not 0 <= value[key] <= limit: raise ValueError('bounded engineering review budget exceeded')
    if completed and value['full_reviews'] != 1: raise ValueError('one consolidated full review required')
    if value['scoped_rereviews'] and not value['blocking_fix_waves']:
        raise ValueError('scoped rereview requires a blocking fix wave')
    if not value['full_reviews'] and (value['scoped_rereviews'] or value['blocking_fix_waves']):
        raise ValueError('fix/rereview requires consolidated review first')


def _gap_binding(state, result, root, **context):
    binding = state['engineering_gap']
    if not binding: return
    gap_data = _data(binding.get('gap_ref'),root)
    old_handoff = _data(gap_data['engineering_handoff_ref'],root)
    old_baseline = _data(old_handoff['ba_baseline']['manifest'],root)
    gap = validate_gap(gap_data,root,required_ids=old_baseline['coverage_ids'])
    if 'replacement_handoff_ref' not in binding:
        if state['lifecycle'] != 'UPSTREAM_GAP': raise ValueError('unresolved Engineering Gap blocks downstream work')
        if gap['engineering_handoff_ref'] != state['upstream']: raise ValueError('gap upstream mismatch')
    else:
        _ref(binding.get('resolution_ref'),root)
        if binding['replacement_handoff_ref'] != state['upstream'] or gap['engineering_handoff_ref'] == state['upstream']:
            raise ValueError('gap replacement must bind new exact upstream')
        old = _data(gap['engineering_handoff_ref'],root)
        if result['baseline'].get('previous_baseline') != old['ba_baseline']['manifest']:
            raise ValueError('gap replacement requires revised BA baseline linked to old authority')


def validate_state(state, root=None, **context):
    _check(state,STATE_V2)
    identifier(state['run_id']); identifier(state['change_id'])
    _risk(state['risk']); _repositories(state['repositories']); _checks(state['checks'],state['repositories']); _budget(state['review_budget'])
    for ref in [*state['artifacts'].values(),*state['gates'].values(),*_all_refs(state['verification'])]: _ref(ref,root)
    if state['upstream'] is not None: _ref(state['upstream'],root)
    if state['authority_mode'] == 'FEATURE_DELIVERY' and state['upstream'] is None:
        raise ValueError('FEATURE_DELIVERY requires Engineering Handoff VNext')
    if state['delivery'] is not None: _ref(state['delivery'],root)
    history = state['history']
    for index,event in enumerate(history):
        if not index and event['from'] != 'INTAKE': raise ValueError('history must start at INTAKE')
        if index and (history[index-1]['to'] != event['from'] or history[index-1]['after_sha256'] != event['before_sha256']):
            raise ValueError('append-only lifecycle history chain mismatch')
        # Historical TRIVIAL fast-path edges are recognized by authority mode.
        if not _edge(event['from'],event['to'],state['authority_mode'],state['risk']['level'],event['action']):
            raise ValueError('lifecycle history cannot jump')
    if history and (history[-1]['to'] != state['lifecycle'] or history[-1]['after_sha256'] != _state_hash(state)):
        raise ValueError('state/history exact snapshot drift')
    if not history and state['lifecycle'] != 'INTAKE': raise ValueError('lifecycle requires transition history')
    if state['lifecycle'] == 'INTAKE':
        if state['gates'] or state['artifacts'] or state['verification']: raise ValueError('INTAKE cannot claim authority artifacts')
        return copy.deepcopy(state)
    if root is None: raise ValueError('exact authority requires project root')
    result = _upstream(state,root,**context)
    _protect_upstream(state,result,root)
    if result is not None and 'feature_id' not in state: raise ValueError('validated feature identity required')
    if state['engineering_gap']:
        if result is None: raise ValueError('WHAT gap requires feature authority')
        _gap_binding(state,result,root,**context)
    if state['lifecycle'] in ('IMPACT_ANALYZED','TECHNICAL_PLANNED','IMPLEMENTATION_READY','IMPLEMENTING',
                              'ENGINEERING_REVIEW','VERIFYING','READY_FOR_TEST') and state['authority_mode'] == 'FEATURE_DELIVERY':
        impact = validate_impact(_data(state['artifacts'].get('impact'),root),root,
            upstream=state['upstream'],repositories=state['repositories'],**context)
        if impact['risk'] != state['risk']: raise ValueError('impact/state risk mismatch')
        if impact['change_id'] != state['change_id']: raise ValueError('impact change mismatch')
        for area in ('product','domain'):
            if impact['knowledge_impact']['areas'][area] != result['handoff']['knowledge_impact']['areas'][area]:
                raise ValueError('Dev cannot rewrite BA product/domain Knowledge Impact')
        if impact['upstream_gaps'] or any(row['blocking'] for row in impact['technical_unknowns']):
            raise ValueError('unresolved impact gaps/unknowns block planning and implementation')
    if state['lifecycle'] in ('TECHNICAL_PLANNED','IMPLEMENTATION_READY','IMPLEMENTING','ENGINEERING_REVIEW','VERIFYING','READY_FOR_TEST'):
        snapshot = validate_snapshot(state['artifacts'].get('snapshot'),root,state,**context)
        if 'technical_approval' in state['gates']:
            validate_technical_approval(state['gates']['technical_approval'],state['artifacts']['snapshot'],root,state,**context)
        if state['lifecycle'] != 'TECHNICAL_PLANNED' and _gate_required(snapshot,root,state,**context) and 'technical_approval' not in state['gates']:
            raise ValueError('required exact Human technical gate unresolved')
        if state['open_items']: raise ValueError('blocking engineering items prevent implementation')
    if state['lifecycle'] == 'READY_FOR_TEST':
        _check(state['verification'],FINAL_EVIDENCE)
        evidence = state['verification']
        _output_revisions(evidence['repository_revisions'],state['repositories'])
        validate_coverage(evidence['requirements_coverage'],result['baseline']['coverage_ids'] if result else [],root)
        _final_evidence(state,state['artifacts']['snapshot'],evidence['repository_revisions'],
                        evidence['review'],evidence['engineering_verification'],root)
        if state['review_budget'] != evidence['review']['budget']: raise ValueError('state review budget/evidence mismatch')
        _implementation(evidence['implementation'],evidence['repository_revisions'],state,root)
    if history and history[-1]['after_sha256'] != _state_hash(state):
        raise ValueError('state drift during trusted-host revalidation')
    return copy.deepcopy(state)


def analyze_impact(state, ref, root, **context):
    validate_state(state,root,**context)
    if state['lifecycle'] != 'AUTHORITY_VALIDATED' or state['authority_mode'] != 'FEATURE_DELIVERY':
        raise ValueError('impact analysis requires validated feature authority')
    impact = validate_impact(_data(ref,root),root,upstream=state['upstream'],repositories=state['repositories'],**context)
    if RISK_ORDER[impact['risk']['level']] < RISK_ORDER[state['risk']['level']]: raise ValueError('risk cannot downgrade')
    after = copy.deepcopy(state)
    after.update(lifecycle='IMPACT_ANALYZED',risk=copy.deepcopy(impact['risk']))
    after['artifacts']['impact'] = copy.deepcopy(ref)
    _event(state,after,'IMPACT')
    validate_transition(state,after); validate_state(after,root,**context)
    return after


def make_snapshot(state, root, *, revision, decisions, plan, tasks, **context):
    validate_state(state,root,**context)
    if state['lifecycle'] != 'IMPACT_ANALYZED': raise ValueError('technical planning requires analyzed impact')
    snapshot = {'schema_version':2,'artifact_class':'RUNTIME','run_id':state['run_id'],'change_id':state['change_id'],
        'revision':revision,'authority_mode':state['authority_mode'],'upstream':copy.deepcopy(state['upstream']),
        'delivery':copy.deepcopy(state['delivery']),'engineering_impact':copy.deepcopy(state['artifacts']['impact']),
        'engineering_decisions':copy.deepcopy(decisions),'dev_plan':copy.deepcopy(plan),'dev_tasks':copy.deepcopy(tasks),
        'repositories':copy.deepcopy(state['repositories']),'repository_base_revisions':_bases(state['repositories']),
        'write_scope':_scope(state['repositories']),'risk':copy.deepcopy(state['risk']),'checks':copy.deepcopy(state['checks'])}
    _validate_snapshot_data(snapshot,root,state,**context)
    return snapshot


def _validate_snapshot_data(data, root, state, **context):
    _check(data,SNAPSHOT_V2); identifier(data['revision'])
    for key in ('run_id','change_id','authority_mode','upstream','delivery','repositories','risk','checks'):
        if data[key] != state[key]: raise ValueError('technical snapshot drift: '+key)
    if data['repository_base_revisions'] != _bases(state['repositories']) or data['write_scope'] != _scope(state['repositories']):
        raise ValueError('snapshot base/write-scope drift')
    if state['authority_mode'] == 'FEATURE_DELIVERY':
        if data['engineering_impact'] != state['artifacts'].get('impact'): raise ValueError('snapshot impact mismatch')
        for key in ('engineering_impact','dev_plan','dev_tasks'): _ref(data[key],root)
        for key,name in zip(('dev_plan','dev_tasks'),PLANNING_NAMES):
            if Path(data[key]['path']).name != name: raise ValueError('canonical Dev runtime planning artifact required')
        decisions = _decision_set(data['engineering_decisions'],root,state,**context)
        impact = _data(data['engineering_impact'],root)
        for row in decisions:
            if row['category'] in FOUNDATION_CATEGORIES:
                architecture = impact['knowledge_impact']['areas']['architecture']
                if not architecture['affected'] or row['adr_ref']['path'] not in architecture['targets']:
                    raise ValueError('ARCHITECTURE_DECISION_REQUIRED: project architecture must route through exact Foundation / ADR impact')
    else:
        if any(data[key] is not None for key in ('engineering_impact','dev_plan','dev_tasks')) or data['engineering_decisions']:
            raise ValueError('TRIVIAL maintenance snapshot cannot claim feature planning')
    return data


def validate_snapshot(ref, root, state, **context):
    data = _data(ref,root)
    _validate_snapshot_data(data,root,state,**context)
    if ref['revision'] != data['revision']: raise ValueError('snapshot reference revision mismatch')
    return copy.deepcopy(data)


def plan(state, snapshot_ref, root, **context):
    validate_state(state,root,**context)
    if state['lifecycle'] != 'IMPACT_ANALYZED': raise ValueError('plan requires IMPACT_ANALYZED')
    validate_snapshot(snapshot_ref,root,state,**context)
    after = copy.deepcopy(state); after['lifecycle'] = 'TECHNICAL_PLANNED'
    after['artifacts']['snapshot'] = copy.deepcopy(snapshot_ref)
    _event(state,after,'PLAN'); validate_transition(state,after); validate_state(after,root,**context)
    return after


def _gate_required(snapshot, root, state, **context):
    # All HIGH_RISK runs and durable material ED proposals need Human technical
    # disposition. Routine local reversible choices need no ED record.
    decisions = _decision_set(snapshot['engineering_decisions'],root,state,**context)
    return state['risk']['level'] == 'HIGH_RISK' or any(row['status'] != 'SUPERSEDED' for row in decisions)


def validate_technical_approval(ref, snapshot_ref, root, state, **context):
    receipt = _data(ref,root)
    _check(receipt,TECHNICAL_RECEIPT_V2)
    snapshot = validate_snapshot(snapshot_ref,root,state,**context)
    if (receipt['run_id'] != state['run_id'] or receipt['change_id'] != state['change_id'] or
        receipt['snapshot_ref'] != snapshot_ref or receipt['snapshot_revision'] != snapshot['revision'] or
        ref['revision'] != snapshot['revision'] or receipt['snapshot_sha256'] != snapshot_ref['sha256']):
        raise ValueError('technical approval requires exact run/revision/snapshot binding; replay forbidden')
    _ref(receipt['decision_evidence_ref'],root)
    _authenticate(receipt,context.get('technical_authenticator'))
    _ref(ref,root); _ref(receipt['decision_evidence_ref'],root)
    validate_snapshot(snapshot_ref,root,state,**context)
    result = _upstream(state,root,**context); _protect_upstream(state,result,root)
    # The BA host is another callback. Recheck technical bytes after it too.
    _ref(ref,root); _ref(snapshot_ref,root); _ref(receipt['decision_evidence_ref'],root)
    for dependency in _all_refs(snapshot): _ref(dependency,root)
    for decision_ref in snapshot['engineering_decisions']:
        for dependency in _all_refs(_data(decision_ref,root)): _ref(dependency,root)
    return copy.deepcopy(receipt)


def bind_technical_approval(state, receipt_ref, root, **context):
    validate_state(state,root,**context)
    if state['lifecycle'] != 'TECHNICAL_PLANNED': raise ValueError('technical gate belongs to exact planned snapshot')
    validate_technical_approval(receipt_ref,state['artifacts']['snapshot'],root,state,**context)
    after = copy.deepcopy(state); after['gates']['technical_approval'] = copy.deepcopy(receipt_ref)
    _event(state,after,'APPROVAL'); validate_transition(state,after); validate_state(after,root,**context)
    return after


def _base_guard(state, current):
    if current != _bases(state['repositories']): raise ValueError('BLOCKED: exact repository base revision drift/missing observation')


def advance(state, target, root, *, current_base_revisions=None, **context):
    validate_state(state,root,**context)
    if target not in LIFECYCLE or not _edge(state['lifecycle'],target,state['authority_mode'],state['risk']['level'],'ADVANCE'):
        raise ValueError('invalid Dev lifecycle transition')
    if target in ('IMPACT_ANALYZED','TECHNICAL_PLANNED','READY_FOR_TEST'):
        raise ValueError('artifact-bound transition requires specialized contract operation')
    after = copy.deepcopy(state)
    if target == 'AUTHORITY_VALIDATED':
        result = _upstream(after,root,**context); _protect_upstream(after,result,root)
        if result is not None: after['feature_id'] = result['handoff']['feature']['id']
    if target == 'IMPLEMENTATION_READY':
        _base_guard(state,current_base_revisions)
        if state['authority_mode'] == 'TECHNICAL_MAINTENANCE':
            # Fast path still needs an immutable technical scope snapshot.
            raise ValueError('maintenance readiness requires prepare_maintenance with exact snapshot ref')
        snapshot = validate_snapshot(state['artifacts'].get('snapshot'),root,state,**context)
        if _gate_required(snapshot,root,state,**context):
            validate_technical_approval(state['gates'].get('technical_approval'),state['artifacts']['snapshot'],root,state,**context)
    after['lifecycle'] = target
    _event(state,after,'ADVANCE'); validate_transition(state,after); validate_state(after,root,**context)
    return after


def maintenance_snapshot(state, root, *, revision):
    validate_state(state,root)
    if state['authority_mode'] != 'TECHNICAL_MAINTENANCE' or state['lifecycle'] != 'AUTHORITY_VALIDATED':
        raise ValueError('maintenance snapshot requires validated non-behavioral evidence')
    return {'schema_version':2,'artifact_class':'RUNTIME','run_id':state['run_id'],'change_id':state['change_id'],
        'revision':revision,'authority_mode':state['authority_mode'],'upstream':None,'delivery':state['delivery'],
        'engineering_impact':None,'engineering_decisions':[],'dev_plan':None,'dev_tasks':None,
        'repositories':copy.deepcopy(state['repositories']),'repository_base_revisions':_bases(state['repositories']),
        'write_scope':_scope(state['repositories']),'risk':copy.deepcopy(state['risk']),'checks':copy.deepcopy(state['checks'])}


def prepare_maintenance(state, snapshot_ref, root, *, current_base_revisions):
    validate_state(state,root)
    if state['authority_mode'] != 'TECHNICAL_MAINTENANCE' or state['lifecycle'] != 'AUTHORITY_VALIDATED':
        raise ValueError('maintenance readiness requires validated non-behavioral evidence')
    _base_guard(state,current_base_revisions); validate_snapshot(snapshot_ref,root,state)
    after = copy.deepcopy(state); after['lifecycle'] = 'IMPLEMENTATION_READY'
    after['artifacts']['snapshot'] = copy.deepcopy(snapshot_ref)
    _event(state,after,'ADVANCE'); validate_transition(state,after); validate_state(after,root)
    return after


def authorize_source_mutation(state, root, repository_id, path, *, current_base_revisions, **context):
    """Per-write contract; host applies this before writes throughout IMPLEMENTING."""
    validate_state(state,root,**context)
    if state['lifecycle'] not in ('IMPLEMENTATION_READY','IMPLEMENTING'):
        raise ValueError('source mutation requires IMPLEMENTATION_READY authorization')
    _base_guard(state,current_base_revisions); portable_path(path)
    repositories = {row['id']:row for row in state['repositories']}
    row = repositories.get(repository_id)
    if row is None or row['role'] != 'IMPLEMENTATION' or not any(path == allowed or path.startswith(allowed+'/') for allowed in row['allowed_write_paths']):
        raise ValueError('BLOCKED: source path outside approved repository write scope')
    return {'authorized':True,'snapshot':copy.deepcopy(state['artifacts']['snapshot']),
            'repository_id':repository_id,'path':path}


def raise_gap(state, gap_ref, root, **context):
    validate_state(state,root,**context)
    result = _upstream(state,root,**context)
    if result is None or state['lifecycle'] in ('INTAKE','READY_FOR_TEST','UPSTREAM_GAP'):
        raise ValueError('upstream gap requires active feature delivery')
    gap = validate_gap(_data(gap_ref,root),root,required_ids=result['baseline']['coverage_ids'])
    if gap['status'] != 'OPEN' or gap['engineering_handoff_ref'] != state['upstream'] or gap['feature_id'] != state['feature_id']:
        raise ValueError('gap requires exact current upstream/feature binding')
    for repo,paths in gap['blocking_scope'].items():
        if repo not in _scope(state['repositories']) or any(not any(_overlap(path,scope) for scope in _scope(state['repositories'])[repo]) for path in paths):
            raise ValueError('gap blocking scope outside run')
    after = copy.deepcopy(state); after['lifecycle'] = 'UPSTREAM_GAP'; after['gates'] = {}
    after['engineering_gap'] = {'gap_ref':copy.deepcopy(gap_ref)}
    _event(state,after,'GAP'); validate_transition(state,after); validate_state(after,root,**context)
    return after


def resume_gap(state, replacement_ref, resolution_ref, root, **context):
    # Old approval may be revoked; only integrity of old evidence is required.
    _check(state,STATE_V2)
    if state['lifecycle'] != 'UPSTREAM_GAP': raise ValueError('resume requires first-class upstream gap')
    old = _data(state['upstream'],root)
    result = read_upstream(replacement_ref,root,**context)
    if not result['vnext_authority'] or replacement_ref == state['upstream'] or result['handoff']['feature']['id'] != state['feature_id']:
        raise ValueError('gap requires new exact authenticated Engineering Handoff')
    if result['baseline'].get('previous_baseline') != old['ba_baseline']['manifest']:
        raise ValueError('gap requires revised BA baseline bound to prior baseline')
    gap = _data(state['engineering_gap'].get('gap_ref'),root)
    validate_gap(gap,root,required_ids=read_document(_ref(old['ba_baseline']['manifest'],root).read_text(encoding='utf-8'))['coverage_ids'])
    _ref(resolution_ref,root)
    after = copy.deepcopy(state); after.update(upstream=copy.deepcopy(replacement_ref),lifecycle='AUTHORITY_VALIDATED',artifacts={},gates={},verification={},open_items=[])
    after['engineering_gap'].update(resolution_ref=copy.deepcopy(resolution_ref),replacement_handoff_ref=copy.deepcopy(replacement_ref))
    _event(state,after,'RESOLVE_GAP'); validate_transition(state,after); validate_state(after,root,**context)
    return after


def escalate_risk(state, risk):
    _check(state,STATE_V2); _risk(risk)
    if RISK_ORDER[risk['level']] < RISK_ORDER[state['risk']['level']] or not set(state['risk']['categories']) <= set(risk['categories']):
        raise ValueError('risk downgrade forbidden')
    if state['lifecycle'] == 'READY_FOR_TEST': raise ValueError('terminal handoff cannot be rewritten')
    after = copy.deepcopy(state)
    after.update(risk=copy.deepcopy(risk),lifecycle='NEEDS_REPLAN',artifacts={},gates={},verification={})
    _event(state,after,'ESCALATE'); validate_transition(state,after)
    return after


def replan(state, root, **context):
    validate_state(state,root,**context)
    if state['lifecycle'] != 'NEEDS_REPLAN': raise ValueError('replan requires NEEDS_REPLAN')
    after = copy.deepcopy(state); after.update(lifecycle='AUTHORITY_VALIDATED',artifacts={},gates={},verification={})
    _event(state,after,'REPLAN'); validate_transition(state,after); validate_state(after,root,**context)
    return after


def _output_revisions(revisions, repositories):
    _check(revisions,STRING_MAP)
    expected = {row['id'] for row in repositories if row['role'] == 'IMPLEMENTATION'}
    if set(revisions) != expected: raise ValueError('exact implementation revision per repository required')
    for revision in revisions.values(): identifier(revision)


def _final_evidence(state, snapshot_ref, revisions, review, verification, root):
    _check(review,REVIEW); _check(verification,VERIFICATION)
    _budget(review['budget'],completed=state['authority_mode'] == 'FEATURE_DELIVERY')
    for record in (review,verification):
        _stamp(record['recorded_at'])
        if record['snapshot_sha256'] != snapshot_ref['sha256'] or record['repository_revisions'] != revisions:
            raise ValueError('review/verification requires exact technical snapshot and implementation revisions')
    if review['blocking_findings']: raise ValueError('blocking engineering findings prevent READY_FOR_TEST')
    if _stamp(verification['recorded_at']) < _stamp(review['recorded_at']): raise ValueError('fresh verification required after engineering review')
    actual = [{k:row[k] for k in CHECK['properties']} for row in verification['checks']]
    if actual != state['checks']: raise ValueError('fresh required engineering check set must match exact planned checks')
    for row in verification['checks']:
        if row['status'] != 'PASS' or row['exit_code'] != 0: raise ValueError('fresh engineering verification must PASS')
        _ref(row['evidence_ref'],root)
    for ref in review['evidence_refs']: _ref(ref,root)


def make_handoff(state, root, *, repository_revisions, current_base_revisions, implementation,
                 coverage, review, verification, known_risks, **context):
    validate_state(state,root,**context)
    if state['lifecycle'] != 'VERIFYING': raise ValueError('READY_FOR_TEST requires VERIFYING and final evidence')
    _base_guard(state,current_base_revisions)
    result = _upstream(state,root,**context)
    snapshot = validate_snapshot(state['artifacts']['snapshot'],root,state,**context)
    required = result['baseline']['coverage_ids'] if result else []
    validate_coverage(coverage,required,root)
    _output_revisions(repository_revisions,state['repositories'])
    _final_evidence(state,state['artifacts']['snapshot'],repository_revisions,review,verification,root)
    after = copy.deepcopy(state); after['lifecycle'] = 'READY_FOR_TEST'; after['review_budget'] = copy.deepcopy(review['budget'])
    after['verification'] = copy.deepcopy({'repository_revisions':repository_revisions,'implementation':implementation,
        'requirements_coverage':coverage,'review':review,'engineering_verification':verification})
    _event(state,after,'FINALIZE'); validate_transition(state,after)
    impact = _data(snapshot['engineering_impact'],root) if result else None
    handoff = {'schema_version':2,'artifact_class':'HANDOFF_MANIFEST','change_id':state['change_id'],
        'authority_mode':state['authority_mode'],'feature':copy.deepcopy(result['handoff']['feature']) if result else None,
        'upstream_engineering_handoff':copy.deepcopy(state['upstream']),'delivery_manifest':copy.deepcopy(state['delivery']),
        'engineering_impact':snapshot['engineering_impact'],'engineering_decisions':snapshot['engineering_decisions'],
        'technical_approval':copy.deepcopy(state['gates'].get('technical_approval')),'technical_snapshot':copy.deepcopy(state['artifacts']['snapshot']),
        'repository_revisions':copy.deepcopy(repository_revisions),'implementation':copy.deepcopy(implementation),
        'requirements_coverage':copy.deepcopy(coverage),'engineering_verification':copy.deepcopy(verification),'review':copy.deepcopy(review),
        'known_risks':copy.deepcopy(known_risks),'knowledge_impact':copy.deepcopy(impact['knowledge_impact']) if impact else knowledge_impact(),
        'state':'READY_FOR_TEST','run_state':after}
    validate_handoff(handoff,root,current_base_revisions=current_base_revisions,**context)
    return handoff


def validate_handoff(data, root, *, current_base_revisions=None, **context):
    _check(data,HANDOFF_V2)
    state = data['run_state']; validate_state(state,root,**context)
    if state['lifecycle'] != 'READY_FOR_TEST': raise ValueError('handoff cannot fabricate READY_FOR_TEST')
    if current_base_revisions is not None: _base_guard(state,current_base_revisions)
    snapshot = validate_snapshot(data['technical_snapshot'],root,state,**context)
    result = _upstream(state,root,**context)
    expected = {'change_id':state['change_id'],'authority_mode':state['authority_mode'],
        'feature':result['handoff']['feature'] if result else None,'upstream_engineering_handoff':state['upstream'],
        'delivery_manifest':state['delivery'],'engineering_impact':snapshot['engineering_impact'],
        'engineering_decisions':snapshot['engineering_decisions'],'technical_approval':state['gates'].get('technical_approval'),
        'technical_snapshot':state['artifacts']['snapshot']}
    if any(data[key] != value for key,value in expected.items()): raise ValueError('handoff exact technical/upstream binding mismatch')
    impact = _data(snapshot['engineering_impact'],root) if result else None
    if data['knowledge_impact'] != (impact['knowledge_impact'] if impact else knowledge_impact()):
        raise ValueError('handoff Knowledge Impact drift')
    validate_coverage(data['requirements_coverage'],result['baseline']['coverage_ids'] if result else [],root)
    _output_revisions(data['repository_revisions'],state['repositories'])
    _final_evidence(state,data['technical_snapshot'],data['repository_revisions'],data['review'],data['engineering_verification'],root)
    for key in FINAL_EVIDENCE['properties']:
        if data[key] != state['verification'][key]: raise ValueError('handoff finalized state evidence mismatch')
    _implementation(data['implementation'],data['repository_revisions'],state,root)
    # Revalidate upstream and all exact downstream refs after trusted callbacks.
    _upstream(state,root,**context)
    for ref in _all_refs(data): _ref(ref,root)
    return copy.deepcopy(data)


def _implementation(rows, revisions, state, root):
    _check(rows,{'type':'array','items':IMPLEMENTATION_ROW})
    unique([row['repository_id'] for row in rows],'implementation repository')
    if {row['repository_id'] for row in rows} != set(revisions):
        raise ValueError('missing repository implementation evidence')
    for row in rows:
        if row['revision'] != revisions[row['repository_id']]: raise ValueError('implementation revision mismatch')
        allowed = _scope(state['repositories'])[row['repository_id']]
        unique(row['changed_paths'],'changed path')
        for path in row['changed_paths']:
            portable_path(path)
            if not any(path == scope or path.startswith(scope+'/') for scope in allowed): raise ValueError('unapproved implementation write-scope drift')
        for ref in row['evidence_refs']: _ref(ref,root)


def read_artifact(data, kind, root=None, **context):
    """Read-old only: historical state, impact and handoff never gain authority."""
    if not isinstance(data,dict) or type(data.get('schema_version')) is not int:
        raise ValueError('integer contract version required')
    if data['schema_version'] == 1:
        from tooling.lib import dev_kit as legacy
        if kind == 'impact': errors = legacy.validate_impact_manifest(data)
        elif kind == 'handoff': errors = legacy.validate_dev_handoff(data)
        elif kind == 'state':
            # V1 runtime has no standalone schema validator. Inspect its existing
            # readiness/status payload without promoting any historical claims.
            if not isinstance(data.get('state',data.get('status')),str): raise ValueError('legacy state/status required')
            errors = []
        else: raise ValueError('unsupported artifact kind')
        if errors: raise ValueError('; '.join(errors))
        return {'mode':'LEGACY_COMPAT','vnext_authority':False,'artifact':copy.deepcopy(data)}
    validators = {'impact':validate_impact,'handoff':validate_handoff,'state':validate_state}
    if kind not in validators: raise ValueError('unsupported artifact kind')
    checked = validators[kind](data,root,**context)
    return {'mode':'VNEXT','vnext_authority':kind == 'handoff' or
        (kind == 'state' and data['lifecycle'] != 'INTAKE'),'artifact':checked}
