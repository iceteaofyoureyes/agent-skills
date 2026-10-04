"""Artifact values; existing artifact formats are unchanged."""
from enum import Enum


class ArtifactClass(str, Enum):
    CANONICAL = 'CANONICAL'
    DERIVED = 'DERIVED'
    RUNTIME = 'RUNTIME'
    EVIDENCE = 'EVIDENCE'
    HANDOFF_MANIFEST = 'HANDOFF_MANIFEST'
