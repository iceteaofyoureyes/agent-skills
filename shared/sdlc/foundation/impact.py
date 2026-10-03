"""Versioned, generic change-impact routing; outcomes never imply approval."""
from shared.sdlc.schema import BOOLEAN, STRING, VERSION, object_schema, portable_path, unique, validate_schema

AREAS = ('product', 'domain', 'architecture', 'testing')
KNOWLEDGE_IMPACT_V1 = object_schema({'schema_version': VERSION,
    'areas': object_schema({area: object_schema({'affected': BOOLEAN,
        'targets': {'type': 'array', 'items': STRING}}) for area in AREAS})})


def knowledge_impact(data=None):
    if data is None:
        data = {'schema_version': 1, 'areas': {area: {'affected': False, 'targets': []} for area in AREAS}}
    validate_schema(data, KNOWLEDGE_IMPACT_V1)
    for row in data['areas'].values():
        unique(row['targets'], 'impact target')
        for target in row['targets']: portable_path(target)
        if row['targets'] and not row['affected']:
            raise ValueError('unaffected area cannot name affected targets')
    return data


def refresh_outcome(data):
    knowledge_impact(data)
    return 'FOUNDATION_UPDATE_REQUIRED' if any(row['affected'] for row in data['areas'].values()) else 'NO_FOUNDATION_CHANGE'


def routes(data):
    knowledge_impact(data)
    owners = {'product': 'BA', 'domain': 'BA', 'architecture': 'ENGINEERING', 'testing': 'TEST'}
    return [{'area': area, 'owner': owners[area], 'targets': row['targets']}
            for area, row in data['areas'].items() if row['affected']]
