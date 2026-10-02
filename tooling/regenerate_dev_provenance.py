"""Pin project-owned Dev runtime payload without changing upstream provenance."""
import hashlib
import json
from pathlib import Path


def regenerate(root):
    root = Path(root)
    path = root / 'kits/dev/provenance.lock.json'
    record = json.loads(path.read_text(encoding='utf-8'))
    # Upstream skills retain their existing blob locks; full installs record exact file hashes.
    files = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in (
        'tooling/lib/dev_kit.py', 'tooling/lib/dev_router.py', 'kits/dev/kit.yaml', 'kits/dev/plugin/plugin.json')}
    record['runtime_payload'] = {
        'algorithm': 'DEV_RUNTIME_CORE_SHA256_V1', 'files': files,
        'sha256': hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
    }
    path.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    return record['runtime_payload']['sha256']


if __name__ == '__main__':
    print(regenerate(Path(__file__).resolve().parents[1]))
