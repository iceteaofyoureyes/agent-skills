"""Arc42 semantic sections and readiness rules as immutable versioned data."""
from types import MappingProxyType


def _freeze(value):
    if isinstance(value,dict): return MappingProxyType({key:_freeze(entry) for key,entry in value.items()})
    if isinstance(value,list): return tuple(_freeze(entry) for entry in value)
    return value


PROJECT_FOUNDATION_PROFILE_ARC42_V1 = _freeze({
    'id':'arc42-standard-v1', 'schema_version':1,
    'sections':('introduction_goals','constraints','context_scope','solution_strategy',
                'building_block_view','runtime_view','deployment_view','crosscutting_concepts',
                'architecture_decisions','quality_requirements','risks_technical_debt','glossary'),
    'section_titles':('01 Introduction & Goals','02 Constraints','03 Context & Scope',
        '04 Solution Strategy','05 Building Block View','06 Runtime View','07 Deployment View',
        '08 Crosscutting Concepts','09 Architecture Decisions','10 Quality Requirements',
        '11 Risks & Technical Debt','12 Glossary'),
    'statuses':('COMPLETE','PARTIAL','UNKNOWN','NOT_APPLICABLE','DEFERRED'),
    'evidence_by_mode':{
        'BROWNFIELD_RECOVERY':('CURRENT_SYSTEM','CONFIRMED','INFERRED','UNKNOWN'),
        'GREENFIELD_BOOTSTRAP':('APPROVED_TARGET','PROPOSED','DEFERRED','UNKNOWN'),
        'FOUNDATION_REFRESH':('CURRENT_SYSTEM','CONFIRMED','INFERRED','APPROVED_TARGET','PROPOSED','DEFERRED','UNKNOWN')},
    'levels':{
        'MINIMAL':{'entry_points':('product','architecture'),
                   'allowed_nonblocking_statuses':('PARTIAL','UNKNOWN','NOT_APPLICABLE','DEFERRED')},
        'STANDARD':{'entry_points':('product','domain','architecture','testing','features'),
                    'allowed_nonblocking_statuses':('PARTIAL','UNKNOWN','NOT_APPLICABLE','DEFERRED')},
        'EXTENDED':{'entry_points':('product','domain','architecture','testing','features','operations'),
                    'allowed_nonblocking_statuses':('PARTIAL','UNKNOWN','NOT_APPLICABLE','DEFERRED')}}})
