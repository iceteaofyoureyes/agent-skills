"""Deterministic metadata inventory of explicitly declared repository roots."""
import hashlib
import os
from pathlib import Path
import stat

from shared.sdlc.artifacts.classes import ArtifactClass
from shared.sdlc.policy.contract import validate_policy
from shared.sdlc.schema import portable_path, safe_file
from shared.sdlc.topology.contract import validate_topology

KNOWLEDGE_CLASSES = ('PRODUCT', 'DOMAIN', 'ARCHITECTURE', 'ADR', 'TEST_STRATEGY',
                     'AUTOMATION_ARCHITECTURE', 'OPERATIONS', 'FEATURE', 'MODULE_LOCAL',
                     'RUNTIME', 'EVIDENCE', 'HISTORICAL', 'UNKNOWN')
OWNERS = {'PRODUCT': 'BA', 'DOMAIN': 'BA', 'FEATURE': 'BA', 'ARCHITECTURE': 'ENGINEERING',
          'ADR': 'ENGINEERING', 'OPERATIONS': 'ENGINEERING', 'MODULE_LOCAL': 'ENGINEERING',
          'TEST_STRATEGY': 'TEST', 'AUTOMATION_ARCHITECTURE': 'TEST'}
DOMAIN_CLASSES = {'product': 'PRODUCT', 'domain': 'DOMAIN', 'architecture': 'ARCHITECTURE',
                  'testing': 'TEST_STRATEGY', 'features': 'FEATURE'}


def safe_location(root, relative):
    """Validate even absent write destinations and Windows reparse ancestors."""
    portable_path(relative)
    root = Path(root).absolute()
    path = root / relative
    for ancestor in (path, *path.parents):
        if os.path.lexists(ancestor):
            info = ancestor.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise ValueError('symlink/reparse escape forbidden')
            if ancestor != path and not stat.S_ISDIR(info.st_mode):
                raise ValueError('non-directory ancestor')
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('outside project root')
    return path


def declared_repository(topology, relative):
    portable_path(relative)
    matches = [row for row in topology['repositories']
               if relative == row['path'] or relative.startswith(row['path'] + '/')]
    if len(matches) != 1:
        raise ValueError('missing/ambiguous declared repository ownership')
    return matches[0]


def classify(relative, policy):
    for domain, path in policy['authority'].items():
        if relative == path:
            return ArtifactClass.CANONICAL.value, DOMAIN_CLASSES[domain], 'DOCUMENT'
    path = Path(relative)
    tokens = set(part.lower() for part in path.parts)
    name = path.stem.lower().replace('_', '-')
    if '.sdlc' in tokens or 'runs' in tokens:
        return ArtifactClass.RUNTIME.value, 'RUNTIME', 'RUNTIME'
    if tokens & {'history', 'historical', 'archive'}:
        return ArtifactClass.EVIDENCE.value, 'HISTORICAL', 'DOCUMENT'
    if tokens & {'evidence', 'logs', 'raw-output', 'prompts'}:
        return ArtifactClass.EVIDENCE.value, 'EVIDENCE', 'EVIDENCE'
    for keyword, category in (('automation', 'AUTOMATION_ARCHITECTURE'), ('adr', 'ADR'),
                              ('product', 'PRODUCT'), ('domain', 'DOMAIN'),
                              ('architecture', 'ARCHITECTURE'), ('test', 'TEST_STRATEGY'),
                              ('operations', 'OPERATIONS'), ('feature', 'FEATURE')):
        if keyword in tokens or keyword in name:
            return ArtifactClass.DERIVED.value, category, 'DOCUMENT'
    if path.suffix.lower() in ('.py', '.js', '.ts', '.java', '.go', '.rs', '.cs'):
        return ArtifactClass.EVIDENCE.value, 'MODULE_LOCAL', 'CODE'
    if path.suffix.lower() in ('.json', '.toml', '.yml', '.yaml', '.ini', '.env') or '.github' in tokens:
        return ArtifactClass.EVIDENCE.value, 'OPERATIONS', 'CONFIG'
    return ArtifactClass.EVIDENCE.value, 'UNKNOWN', 'UNKNOWN'


def inventory(root, topology, policy):
    validate_topology(topology); validate_policy(policy)
    root = Path(root).absolute()
    rows = []
    def inaccessible(error):
        raise error
    for repository in sorted(topology['repositories'], key=lambda row: row['id']):
        directory = safe_location(root, repository['path'])
        if not directory.is_dir():
            raise ValueError('declared repository root missing')
        for current, directories, files in os.walk(directory, followlinks=False, onerror=inaccessible):
            directories[:] = sorted(name for name in directories if name not in ('.git', '__pycache__'))
            for name in directories:
                safe_location(root, (Path(current) / name).relative_to(root).as_posix())
            for name in sorted(files):
                if name == '.git':
                    continue
                relative = (Path(current) / name).relative_to(root).as_posix()
                path = safe_file(root, relative)
                artifact, knowledge, source = classify(relative, policy)
                content = path.read_bytes()
                rows.append({'repository_id': repository['id'], 'relative_path': relative,
                             'artifact_class': artifact, 'candidate_knowledge_class': knowledge,
                             'sha256': hashlib.sha256(content).hexdigest(), 'size_bytes': len(content),
                             'source_kind': source, 'owner_candidate': OWNERS.get(knowledge, 'UNKNOWN')})
    return {'schema_version': 1, 'project_id': topology['project']['id'],
            'artifacts': sorted(rows, key=lambda row: (row['repository_id'], row['relative_path']))}
