"""Portable runtime paths: reject impossible writes before consuming decisions."""
from shared.sdlc.compatibility import retain_legacy_identity as _retain_legacy_identity
import json
import os
from pathlib import Path
import re
import sys
import tempfile

_retain_legacy_identity(__name__, 'tooling.lib.runtime_paths')


class RuntimePathError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__(json.dumps({'code': code, **detail}, ensure_ascii=False))


def windows_long_paths_supported():
    if sys.platform != 'win32':
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                           r'SYSTEM\CurrentControlSet\Control\FileSystem') as key:
            return winreg.QueryValueEx(key, 'LongPathsEnabled')[0] == 1
    except OSError:
        return False


def revision_component(value):
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if (not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}', value)
            or value.endswith('.') or value.split('.')[0].upper() in reserved):
        raise RuntimePathError('INVALID_NEXT_REVISION', {'revision': value})
    return value


def internal_artifact(root, compact, legacy):
    """Read/resume legacy evidence in place; new runtime outputs use compact names."""
    root = Path(root)
    if (root / compact).is_file() and (root / legacy).is_file() and (root / compact).read_bytes() != (root / legacy).read_bytes():
        raise RuntimePathError('IMMUTABLE_ARTIFACT_CONFLICT', {'compact': str(root / compact), 'legacy': str(root / legacy)})
    return root / legacy if (root / legacy).exists() else root / compact


RUNTIME_LAYOUT = {
    'DESIGN': ('workflow-state.json', 'canonical/semantic-payload.json',
               'canonical/canonical-test-design.json', 'canonical/approved.json',
               'inputs/tea-runtime-config.yaml', 'inputs/project-policy-context.json',
               'inputs/approved-ux-contract.md', 'inputs/adapter/epic-1.md',
               'inputs/adapter/business-rules.md', 'inputs/adapter/open-decisions.md',
               'raw-output/same-session-instructions.md', 'raw-output/test-design-epic-1.md',
               'evidence/input-manifest.json', 'evidence/tea-raw-output.md'),
    'CASES': ('workflow-state.json', 'canonical/semantic-payload.json',
              'canonical/canonical-testcases.json', 'inputs/approved-test-design.md',
              'inputs/project-policy-context.json', 'raw-output/same-session-instructions.md',
              'raw-output/test-cases.md', 'evidence/katalon-raw-output.md',
              'evidence/invocation-manifest.json', 'evidence/input-manifest.json'),
}
COMMON_LAYOUT = ('evidence/delivery-input.json', 'evidence/same-session-prepare.json',
                 'evidence/same-session-finalize.json', 'evidence/normalization-map.json',
                 'evidence/normalization-results.json', 'evidence/validator-results.json')


def preflight_runtime_layout(run_dir, lane, transition, extra=()):
    preflight_paths([Path(run_dir) / name for name in (*RUNTIME_LAYOUT[lane], *COMMON_LAYOUT, *extra)],
                    stage=lane, transition=transition)


def preflight_paths(paths, *, stage, transition, windows=None, long_paths=None, budget=259):
    windows = sys.platform == 'win32' if windows is None else windows
    long_paths = windows_long_paths_supported() if long_paths is None else long_paths
    parents = set()
    length = lambda path: len(str(path).encode('utf-16-le')) // 2 if windows else len(str(path))
    for raw in paths:
        path = Path(raw).absolute()
        detail = {'path': str(path), 'actual_length': length(path), 'safe_budget': budget,
                  'stage': stage, 'transition': transition, 'platform': 'win32' if windows else sys.platform}
        # Include the bounded ten-character temp name used by atomic writes.
        if windows and not long_paths and (length(path) > budget or
                length(path.parent) > 247 or length(path.parent / '.t12345678') > budget):
            raise RuntimePathError('WINDOWS_PATH_BUDGET_EXCEEDED', detail)
        ancestor = path
        while not ancestor.exists():
            ancestor = ancestor.parent
        if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
            raise RuntimePathError('UNSAFE_RUNTIME_PATH', detail)
        parent = ancestor if ancestor.is_dir() else ancestor.parent
        if ancestor == path and path.is_dir():
            raise RuntimePathError('RUNTIME_DESTINATION_CONFLICT', detail)
        parents.add(parent)
    for parent in parents:
        try:
            with tempfile.TemporaryFile(dir=parent):
                pass
        except OSError as error:
            raise RuntimePathError('RUNTIME_NOT_WRITABLE', {'path': str(parent), 'stage': stage,
                                   'transition': transition, 'error': str(error)}) from error
