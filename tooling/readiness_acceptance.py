"""Compatibility alias for the public Phase 9 conformance runner."""
from __future__ import annotations

from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tooling import public_conformance


def main(argv=None):
    return public_conformance.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
