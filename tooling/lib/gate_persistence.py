"""Recoverable Human Gate writes. Immutable journal; workflow is the final commit."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from .runtime_paths import preflight_paths


class GateConflict(ValueError):
    code = 'IMMUTABLE_ARTIFACT_CONFLICT'


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write_if_same_or_absent(path, content):
    path = Path(path)
    if path.is_symlink():
        raise GateConflict(f'unsafe evidence symlink: {path}')
    if path.exists():
        if path.read_bytes() != content:
            raise GateConflict(f'refusing to overwrite different immutable evidence: {path}')
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.i', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp, path)  # Publish a complete file without replacing an existing one.
        except FileExistsError:
            if path.read_bytes() != content:
                raise GateConflict(f'conflicting concurrent evidence: {path}')
    finally:
        temp.unlink(missing_ok=True)


def atomic_workflow(path, workflow):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.w', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(json_bytes(workflow))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def review_state(run_dir, receipt_path, receipt_bytes):
    """Read the original review, including on exact replay; never waive validation."""
    run_dir, receipt_path = Path(run_dir), Path(receipt_path)
    current = json.loads((run_dir / 'workflow-state.json').read_text(encoding='utf-8'))
    if not isinstance(current, dict):
        raise GateConflict('workflow state must be an object')
    if receipt_path.exists() and receipt_path.read_bytes() != receipt_bytes:
        error = GateConflict('different receipt already bound to this gate')
        error.code = 'RECEIPT_REPLAY'
        raise error
    journal = receipt_path.parent / 'tx.json'
    if not journal.exists():
        return current  # Also allows a legacy partial receipt in unchanged REVIEW state.
    try:
        transaction = json.loads(journal.read_text(encoding='utf-8'))
    except (ValueError, OSError) as error:
        raise GateConflict(f'unreadable gate transaction: {journal}') from error
    if (not isinstance(transaction, dict) or
            set(transaction) != {'schema_version', 'receipt_sha256', 'before', 'after', 'outputs'} or
            transaction['schema_version'] != 1 or
            not isinstance(transaction['receipt_sha256'], str) or
            not re.fullmatch('[0-9a-f]{64}', transaction['receipt_sha256']) or
            not isinstance(transaction['before'], dict) or not isinstance(transaction['after'], dict) or
            not isinstance(transaction['outputs'], list) or
            any(not isinstance(row, dict) or set(row) != {'path', 'sha256'} or
                not isinstance(row['path'], str) or not isinstance(row['sha256'], str) or
                not re.fullmatch('[0-9a-f]{64}', row['sha256']) or
                not (run_dir / row['path']).resolve().is_relative_to(run_dir.resolve())
                for row in transaction['outputs'])):
        raise GateConflict('malformed gate transaction journal')
    if transaction['receipt_sha256'] != hashlib.sha256(receipt_bytes).hexdigest():
        error = GateConflict('different receipt conflicts with the gate transaction')
        error.code = 'RECEIPT_REPLAY'
        raise error
    if current not in (transaction['before'], transaction['after']):
        raise GateConflict('workflow drifted from both transaction endpoints')
    return transaction['before']


def commit_gate(run_dir, receipt_path, receipt_bytes, artifacts, before, after, *, stage, transition):
    """Preflight every write, then resume immutable writes and commit state once."""
    run_dir, receipt_path = Path(run_dir), Path(receipt_path)
    workflow_path = run_dir / 'workflow-state.json'
    journal_path = receipt_path.parent / 'tx.json'
    artifacts = [(Path(path), content) for path, content in artifacts]
    transaction = {'schema_version': 1, 'receipt_sha256': hashlib.sha256(receipt_bytes).hexdigest(),
                   'before': before, 'after': after,
                   'outputs': [{'path': str(path.relative_to(run_dir)),
                                'sha256': hashlib.sha256(content).hexdigest()}
                               for path, content in artifacts]}
    writes = [(journal_path, json_bytes(transaction)), (receipt_path, receipt_bytes), *artifacts]
    preflight_paths([workflow_path, *(path for path, _ in writes)], stage=stage, transition=transition)
    for path, content in writes:
        if path.exists() and path.read_bytes() != content:
            raise GateConflict(f'immutable transition output conflicts: {path}')
    current = json.loads(workflow_path.read_text(encoding='utf-8'))
    if current not in (before, after):
        raise GateConflict('workflow changed before transaction commit')
    for path, content in writes:
        write_if_same_or_absent(path, content)
    if current != after:
        atomic_workflow(workflow_path, after)
    # Exact completed replay must validate outputs too, not merely trust terminal state.
    if any(path.read_bytes() != content for path, content in writes):
        raise GateConflict('transition output changed during commit')
    if json.loads(workflow_path.read_text(encoding='utf-8')) != after:
        raise GateConflict('workflow commit did not bind expected transition')
