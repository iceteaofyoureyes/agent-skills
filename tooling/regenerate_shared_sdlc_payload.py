"""Build the deterministic, BA skill-owned Shared Core runtime archive.

The archive is derived package payload. Canonical source remains shared/**.
Existing skill tree hashes, installation ownership, and removal stay unchanged.
"""
from pathlib import Path
import zipfile


def shared_runtime_files(root):
    """Use the explicit Dev runtime allowlist for the shared payload closure."""
    from tooling.install_dev_kit import RUNTIME_FILES
    return tuple(sorted(name for name in RUNTIME_FILES if name.startswith('shared/')))


def regenerate(root):
    root = Path(root)
    archive = root / 'ba-workflow/scripts/shared-sdlc-core.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as output:
        for name in shared_runtime_files(root):
            path = root / name
            if not path.is_file() or path.is_symlink():
                raise ValueError(f'required regular Shared Core source missing: {path}')
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            output.writestr(entry, path.read_bytes())
    # Each skill owns its derived installation payload; shared/** owns semantics.
    foundation_scripts = root / 'project-foundation/scripts'
    if foundation_scripts.is_dir():
        (foundation_scripts / 'shared-sdlc-core.zip').write_bytes(archive.read_bytes())
    return archive


if __name__ == '__main__':
    print(regenerate(Path(__file__).resolve().parents[1]))
