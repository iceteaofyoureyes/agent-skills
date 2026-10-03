"""Topology v1: repository ownership is declared data, never discovered here."""
import re
from shared.sdlc.schema import STRING, VERSION, identifier, object_schema, portable_path, read_document, unique, validate_schema, reject_secrets

PROJECT_TOPOLOGY_V1 = object_schema({
    'schema_version':VERSION, 'project':object_schema({'id':STRING}),
    'repositories':{'type':'array','minItems':1,'items':object_schema({
        'id':STRING,'path':STRING,'repository':STRING,'role':STRING})}})


def validate_topology(data):
    validate_schema(data,PROJECT_TOPOLOGY_V1); reject_secrets(data)
    identifier(data['project']['id'])
    rows = data['repositories']
    for row in rows:
        identifier(row['id']); portable_path(row['path']); identifier(row['role'])
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*',row['repository']):
            raise ValueError('repository must be owner/name')
    for field in ('id','path','repository'): unique([row[field] for row in rows],field)
    paths = [row['path'].casefold() for row in rows]
    if any(a.startswith(b+'/') for a in paths for b in paths if a != b):
        raise ValueError('overlapping repository roots are ambiguous')
    return data


def read_topology(text):
    return validate_topology(read_document(text))
