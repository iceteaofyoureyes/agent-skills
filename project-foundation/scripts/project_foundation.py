"""Invoke only the co-located, installed Shared SDLC payload or source tree."""
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
payload = Path(__file__).resolve().parent / 'shared-sdlc-core.zip'
core = root if (root / 'shared/sdlc/foundation/cli.py').is_file() else payload
if not core.exists():
    raise SystemExit('Shared SDLC Project Foundation payload is missing')
sys.path.insert(0, str(core))
from shared.sdlc.foundation.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
