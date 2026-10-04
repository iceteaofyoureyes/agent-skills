"""Pin project-owned Dev runtime payload without changing upstream provenance."""
import hashlib
import json
from pathlib import Path


def regenerate(root):
    from tooling.install_dev_kit import package_files
    root = Path(root)
    path = root / 'kits/dev/provenance.lock.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    # The payload map excludes only this lock to avoid a self-referential hash.
    names = tuple(name for name in package_files(root) if name != 'kits/dev/provenance.lock.json')
    files = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}
    record['runtime_payload'] = {
        'algorithm': 'DEV_RUNTIME_PACKAGE_SHA256_V2', 'runtime': 'dev-kit-v2',
        'self_excluded': 'kits/dev/provenance.lock.json', 'files': files,
        'sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
    }
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    return record['runtime_payload']['sha256']


if __name__ == '__main__':
    print(regenerate(Path(__file__).resolve().parents[1]))
