"""Compatibility adapter; implementation owner: shared.sdlc.authority.approved_baseline."""
import importlib as _importlib
from pathlib import Path as _Path
import sys as _sys

_runtime_root = _Path(__file__).resolve().parents[2]
_core_root = _runtime_root if (_runtime_root / "shared/sdlc/compatibility/__init__.py").is_file() else _Path(__file__).resolve().parent / "shared-sdlc-core.zip"
if not ((_core_root / "shared/sdlc/compatibility/__init__.py").is_file() or _core_root.is_file()):
    raise ImportError("Shared SDLC Core payload is missing from this kit installation")
if str(_core_root) not in _sys.path:
    _sys.path.insert(0, str(_core_root))
_core = _importlib.import_module('shared.sdlc.authority.approved_baseline')
_sys.modules[__name__] = _core
