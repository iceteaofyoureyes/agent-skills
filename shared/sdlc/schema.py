"""Versioned contract validation and a deliberately bounded JSON/YAML reader.

Schema definitions use the JSON Schema vocabulary implemented below, without
an optional runtime dependency. Unknown versions are never migrated implicitly.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import stat


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate mapping key: ' + key)
        result[key] = value
    return result


def _json(text):
    def reject_constant(value):
        raise ValueError('non-finite JSON constant: ' + value)
    def finite_float(raw):
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError('non-finite JSON number: ' + raw)
        return value
    return json.loads(text,object_pairs_hook=_pairs,parse_constant=reject_constant,parse_float=finite_float)


def _single_quoted_yaml(raw):
    if not re.fullmatch(r"'(?:[^']|'')*'",raw):
        raise ValueError('unmatched or unescaped single quote in YAML scalar')
    # YAML only escapes an apostrophe by doubling it. Backslashes are literal.
    return raw[1:-1].replace("''", "'")


def read_document(text):
    """Read JSON or two-space YAML mappings/sequences; reject YAML extensions."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError('nonempty UTF-8 document required')
    if text.lstrip().startswith(('{', '[')):
        return _json(text)
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if '\t' in line:
            raise ValueError('tabs are not supported')
        indent = len(line) - len(line.lstrip())
        if indent % 2:
            raise ValueError('two-space YAML indentation required')
        rows.append((indent, line.strip()))

    def scalar(raw):
        if raw.startswith(('"', "'")):
            if raw.startswith('"'):
                value = _json(raw)
            else:
                value = _single_quoted_yaml(raw)
            if not isinstance(value, str):
                raise ValueError('quoted YAML value must be a string')
            return value
        if raw.startswith(('[', '{')):
            return _json(raw)
        if raw in ('true', 'false', 'null'):
            return {'true':True, 'false':False, 'null':None}[raw]
        if re.fullmatch(r'-?(0|[1-9][0-9]*)', raw):
            return int(raw)
        if (not raw or raw[0] in '&*!|>@`' or '#' in raw or ': ' in raw or
                raw.lower() in ('yes','no','on','off','~','.nan','.inf','-.inf') or
                re.fullmatch(r'[-+]?[0-9].*', raw)):
            raise ValueError('unsupported/ambiguous YAML scalar; quote strings')
        return raw

    def mapping_entry(text):
        match = re.fullmatch(r'([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?', text)
        if not match:
            raise ValueError('YAML mapping key/value required')
        return match.group(1), match.group(2)

    def block(entries, index, indent):
        is_list = entries[index][1].startswith('- ')
        result = [] if is_list else {}
        while index < len(entries) and entries[index][0] == indent:
            text = entries[index][1]
            if is_list:
                if not text.startswith('- '):
                    raise ValueError('mixed mapping/sequence')
                raw = text[2:]
                if re.match(r'[A-Za-z_][A-Za-z0-9_-]*:', raw):
                    stop = index + 1
                    while stop < len(entries) and entries[stop][0] > indent:
                        stop += 1
                    item_entries = [(indent+2, raw), *entries[index+1:stop]]
                    item, used = block(item_entries, 0, indent+2)
                    if used != len(item_entries):
                        raise ValueError('invalid sequence item indentation')
                    result.append(item); index = stop
                else:
                    result.append(scalar(raw)); index += 1
            else:
                if text.startswith('- '):
                    raise ValueError('mixed mapping/sequence')
                key, raw = mapping_entry(text)
                if key in result:
                    raise ValueError('duplicate mapping key: ' + key)
                index += 1
                if raw is None:
                    if index >= len(entries) or entries[index][0] != indent+2:
                        raise ValueError('empty mapping value; declare {} or [] explicitly')
                    result[key], index = block(entries, index, indent+2)
                else:
                    result[key] = scalar(raw)
            if index < len(entries) and entries[index][0] > indent:
                raise ValueError('unexpected nested content after scalar')
        return result, index

    if not rows or rows[0][0] != 0:
        raise ValueError('root mapping/sequence required')
    result, used = block(rows, 0, 0)
    if used != len(rows):
        raise ValueError('invalid document indentation')
    return result


def object_schema(properties, optional=()):
    return {'type':'object', 'properties':properties,
            'required':tuple(key for key in properties if key not in optional), 'additionalProperties':False}


STRING = {'type':'string', 'minLength':1}
VERSION = {'type':'integer', 'enum':(1,)}
BOOLEAN = {'type':'boolean'}
REFERENCE = object_schema({'path':STRING, 'sha256':{'type':'string','pattern':r'[0-9a-f]{64}'},
                           'revision':STRING}, optional=('revision',))


def validate_schema(value, schema, location='$'):
    types = {'object':dict, 'array':list, 'string':str, 'integer':int, 'boolean':bool}
    expected = schema.get('type')
    if expected and type(value) is not types[expected]:
        raise ValueError(location + ': expected ' + expected)
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError(location + ': unsupported value/version')
    if isinstance(value, str):
        if len(value) < schema.get('minLength',0) or value != value.strip():
            raise ValueError(location + ': nonempty trimmed string required')
        if 'pattern' in schema and not re.fullmatch(schema['pattern'],value):
            raise ValueError(location + ': malformed string')
    if isinstance(value, dict):
        properties = schema.get('properties',{})
        if set(schema.get('required',())) - value.keys():
            raise ValueError(location + ': required fields missing')
        for key, entry in value.items():
            if not isinstance(key,str): raise ValueError(location + ': string keys required')
            child = properties.get(key, schema.get('additionalProperties',False))
            if child is False: raise ValueError(location + ': unknown field ' + key)
            if child is not True: validate_schema(entry,child,location+'.'+key)
    if isinstance(value,list):
        if len(value) < schema.get('minItems',0): raise ValueError(location + ': empty list')
        for index,entry in enumerate(value): validate_schema(entry,schema['items'],f'{location}[{index}]')
    return value


def identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}',value):
        raise ValueError('stable identifier required')
    return value


def portable_path(value):
    if not isinstance(value,str) or not value or value.startswith('/'):
        raise ValueError('portable relative path required')
    reserved = {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}
    for part in value.split('/'):
        if (part in ('','.','..') or not re.fullmatch(r'[A-Za-z0-9_.-]+',part) or
                part.endswith('.') or part.split('.')[0].upper() in reserved):
            raise ValueError('unsafe/nonportable relative path')
    return value


def unique(values, label):
    folded = [value.casefold() for value in values]
    if len(set(folded)) != len(folded): raise ValueError('duplicate ' + label)


def safe_file(root, relative):
    portable_path(relative)
    root = Path(root).absolute()
    target = root / relative
    for path in (root, *target.parents, target):
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or bool(getattr(info,'st_file_attributes',0) & 0x400):
                raise ValueError('symlink/reparse reference forbidden')
    if not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
        raise ValueError('reference missing or outside project root')
    return target


def validate_reference(ref, root=None, *, revision=False):
    validate_schema(ref, REFERENCE)
    portable_path(ref['path'])
    if revision and 'revision' not in ref: raise ValueError('immutable reference revision required')
    if 'revision' in ref: identifier(ref['revision'])
    if root is not None:
        path = safe_file(root,ref['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != ref['sha256']:
            raise ValueError('reference SHA-256 mismatch')
        return path
    return ref


def reject_secrets(value):
    """Forbid credential fields and recognizable credential transport formats."""
    if isinstance(value,dict):
        for key,entry in value.items():
            if re.search(r'(password|secret|credential|api[_-]?key|access[_-]?token|private[_-]?key)',key,re.I):
                raise ValueError('credentials/secrets forbidden')
            reject_secrets(entry)
    elif isinstance(value,list):
        for entry in value: reject_secrets(entry)
    elif isinstance(value,str) and re.search(
            r'(?i)(://[^/\s]+:[^/\s]+@|\bBearer\s+\S+|BEGIN .*PRIVATE KEY|\bsk-[A-Za-z0-9_-]{20,}|'
            r'(password|secret|api[_-]?key|access[_-]?token)\s*[:=])',value):
        raise ValueError('credential value forbidden')
