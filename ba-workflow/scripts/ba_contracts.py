"""BA reader compatibility: V1 stays readable; VNext requires its exact proof."""
from pathlib import Path
import contracts as legacy
import ba_vnext as vnext
from shared.sdlc.schema import read_document, validate_schema


def validate_state_data(data, root=None, **kwargs):
    if isinstance(data,dict) and type(data.get('schema_version')) is int and data['schema_version'] == 1:
        return legacy.validate_state_data(data)
    try:
        vnext.validate_state(data,root,**kwargs)
        return []
    except (ValueError,OSError,KeyError,TypeError) as error:
        return ['schema_version/BA VNext state: '+str(error)]


def read_state(data, root=None, **kwargs):
    errors = validate_state_data(data,root,**kwargs)
    if errors: raise ValueError('; '.join(errors))
    if data['schema_version'] == 1:
        return {'mode':'LEGACY_COMPAT','vnext_approval':False,'state':data,
                'reason':'insufficient evidence for VNext baseline approval'}
    return {'mode':'VNEXT','vnext_approval':data['lifecycle'] == 'APPROVED_BASELINE','state':data}


def validate_handoff_text(text, allow_placeholders=False):
    # Keep the old parser for old placeholder/list syntax; dispatch by schema only.
    fields, _, _, _ = legacy._yaml_fields(text)
    if fields.get(('schema_version',)) == '1':
        return legacy.validate_handoff_text(text,allow_placeholders)
    try:
        data = read_document(text)
        if isinstance(data,dict) and type(data.get('schema_version')) is int and data['schema_version'] == 1:
            raise ValueError('legacy handoff requires legacy YAML representation')
        validate_schema(data,vnext.HANDOFF_V2)
        return []
    except (ValueError,TypeError) as error: return [str(error)]


def read_handoff(path, **kwargs):
    path = Path(path)
    text = path.read_text(encoding='utf-8')
    fields, _, _, _ = legacy._yaml_fields(text)
    if fields.get(('schema_version',)) == '1':
        errors = legacy.validate_handoff_file(path)
        if errors: raise ValueError('; '.join(errors))
        return {'mode':'LEGACY_COMPAT','vnext_approval':False,
                'reason':'insufficient evidence for VNext baseline approval'}
    result = vnext.validate_handoff(read_document(text),path.parent,**kwargs)
    return {'mode':'VNEXT','vnext_approval':True,**result}


def validate_handoff_file(path, **kwargs):
    try:
        read_handoff(path,**kwargs)
        return []
    except (ValueError,OSError,KeyError,TypeError) as error: return [str(error)]
