"""Project Policy v1 declares locations and conventions, never business meaning."""
from shared.sdlc.schema import STRING, VERSION, identifier, object_schema, portable_path, read_document, reject_secrets, safe_file, unique, validate_schema

AUTHORITY_DOMAINS = ('product','domain','architecture','testing','features')
PROJECT_POLICY_V1 = object_schema({
    'schema_version':VERSION, 'project':object_schema({'language':STRING}),
    'foundation':object_schema({'profile':{'type':'string','enum':('arc42-standard-v1',)}}),
    'authority':object_schema({name:STRING for name in AUTHORITY_DOMAINS}),
    'workflow':object_schema({'feature_root':STRING,'branch_convention':STRING}),
    'testing':object_schema({'automation_repository_role':STRING}),
    'artifacts':object_schema({'optional':{'type':'array','items':STRING}})})


def validate_policy(data):
    validate_schema(data,PROJECT_POLICY_V1); reject_secrets(data)
    identifier(data['project']['language']); identifier(data['testing']['automation_repository_role'])
    for path in (*data['authority'].values(), data['workflow']['feature_root'], *data['artifacts']['optional']):
        portable_path(path)
    unique(data['artifacts']['optional'],'optional artifact')
    return data


def read_policy(project_root):
    path = safe_file(project_root,'.sdlc/project-policy.yml')
    return validate_policy(read_document(path.read_text(encoding='utf-8')))
