"""Generic exact-byte publication. Kit adapters validate their own approval gates."""
import hashlib
import os
from pathlib import Path
import stat
from shared.sdlc.approvals.gate_persistence import write_if_same_or_absent
from shared.sdlc.provenance.runtime_paths import preflight_paths
from shared.sdlc.schema import STRING, identifier, object_schema, portable_path, validate_reference, validate_schema


def publish_immutable(writes, *, stage, transition, writer=None):
    """Preflight all destinations/conflicts before any immutable publication.

    An interrupted write set is replayable; this does not commit workflow state.
    The writer hook retains adapter fault injection and must publish exact bytes.
    """
    writes = [(Path(path),content) for path,content in writes]
    seen = set()
    for path,content in writes:
        if type(content) is not bytes: raise ValueError('exact bytes required')
        if '..' in path.parts: raise ValueError('traversal destination forbidden')
        # Existing absolute roots may contain spaces/Unicode; new output names
        # and new directories must use the portable contract component profile.
        portable_path(path.name)
        for ancestor in (path,*path.parents):
            if ancestor != path and not ancestor.is_dir(): portable_path(ancestor.name)
            if os.path.lexists(ancestor):
                info = ancestor.lstat()
                if stat.S_ISLNK(info.st_mode) or bool(getattr(info,'st_file_attributes',0) & 0x400):
                    raise ValueError('unsafe symlink/reparse promotion destination')
        key = str(path.absolute()).casefold()
        if key in seen: raise ValueError('duplicate immutable destination')
        seen.add(key)
    targets = [path.absolute() for path,_ in writes]
    if any(str(parent).casefold() in seen for path in targets for parent in path.parents):
        raise ValueError('file/directory destination ownership conflict')
    preflight_paths([path for path,_ in writes],stage=stage,transition=transition)
    for path,content in writes:
        if path.exists() and path.read_bytes() != content:
            raise ValueError('promotion cannot overwrite a different approved snapshot')
    for path,content in writes:
        (writer or write_if_same_or_absent)(path,content)
    if any(path.read_bytes() != content for path,content in writes):
        raise ValueError('published immutable bytes drifted')


def promotion_record(source, content, approval_receipt, receipt_bytes):
    """Bind identity and receipt bytes; a receipt reference is not authentication."""
    validate_schema(source,object_schema({'id':STRING,'revision':STRING,
        'sha256':{'type':'string','pattern':r'[0-9a-f]{64}'}}))
    identifier(source['id']); identifier(source['revision']); validate_reference(approval_receipt)
    if type(content) is not bytes or type(receipt_bytes) is not bytes:
        raise ValueError('exact artifact/receipt bytes required')
    if (hashlib.sha256(content).hexdigest() != source['sha256'] or
            hashlib.sha256(receipt_bytes).hexdigest() != approval_receipt['sha256']):
        raise ValueError('promotion source/approval byte binding mismatch')
    return {'schema_version':1,'source':dict(source),'approval_receipt':dict(approval_receipt),
            'human_approval':False}
