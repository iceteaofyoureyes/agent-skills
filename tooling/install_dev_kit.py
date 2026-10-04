"""Install a self-contained Dev Kit VNext runtime into user scope."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import uuid


RUNTIME_FILES = (
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
    "shared/__init__.py",
    "shared/sdlc/__init__.py",
    "shared/sdlc/approvals/__init__.py",
    "shared/sdlc/approvals/gate_persistence.py",
    "shared/sdlc/approvals/invariants.py",
    "shared/sdlc/artifacts/__init__.py",
    "shared/sdlc/artifacts/classes.py",
    "shared/sdlc/artifacts/delivery_manifest.py",
    "shared/sdlc/authority/__init__.py",
    "shared/sdlc/authority/approved_baseline.py",
    "shared/sdlc/authority/contracts.py",
    "shared/sdlc/compatibility/__init__.py",
    "shared/sdlc/findings/__init__.py",
    "shared/sdlc/findings/execution_contract.py",
    "shared/sdlc/findings/taxonomy.py",
    "shared/sdlc/promotion/__init__.py",
    "shared/sdlc/promotion/immutable.py",
    "shared/sdlc/provenance/__init__.py",
    "shared/sdlc/provenance/references.py",
    "shared/sdlc/provenance/runtime_paths.py",
    "shared/sdlc/readiness/__init__.py",
    "shared/sdlc/readiness/vocabulary.py",
    "shared/sdlc/readiness/compatibility.py",
    "shared/sdlc/schema.py",
    "shared/sdlc/topology/__init__.py",
    "shared/sdlc/topology/contract.py",
    "shared/sdlc/policy/__init__.py",
    "shared/sdlc/policy/contract.py",
    "shared/sdlc/foundation/__init__.py",
    "shared/sdlc/foundation/contract.py",
    "shared/sdlc/foundation/profiles.py",
    "shared/sdlc/foundation/inventory.py",
    "shared/sdlc/foundation/impact.py",
    "shared/sdlc/foundation/workflow.py",
    "shared/sdlc/foundation/producers.py",
    "shared/sdlc/foundation/cli.py",
    "tooling/__init__.py",
    "tooling/lib/__init__.py",
    "tooling/lib/dev_kit.py",
    "tooling/lib/dev_router.py",
    "tooling/lib/dev_vnext.py",
    "tooling/lib/dev_vnext_runtime.py",
    "tooling/lib/dev_vnext_cli.py",
    "tooling/lib/dev_vnext_spec_kit.py",
    "tooling/lib/dev_vnext_doctor.py",
    "ba-workflow/scripts/contracts.py",
    "ba-workflow/scripts/approved_baseline.py",
    "ba-workflow/scripts/delivery_manifest.py",
    "ba-workflow/scripts/ba_contracts.py",
    "ba-workflow/scripts/ba_vnext.py",
    ".agents/plugins/marketplace.json",
)

RUNTIME_DIRECTORIES = (
    "kits/dev",
    "requirements-gap-auditor",
    "verification-before-completion",
    "dev-kit",
    "project-foundation",
)
RUNTIME_NAME = "dev-kit-v2"


def _reparse_or_symlink(path):
    try:
        info = Path(path).lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _assert_no_reparse_ancestors(path):
    path = Path(os.path.abspath(path))
    for candidate in reversed((path, *path.parents)):
        if _reparse_or_symlink(candidate):
            raise ValueError(f"unsafe symlink/reparse path: {candidate}")


def _mkdir_safe(path):
    path = Path(os.path.abspath(path))
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    _assert_no_reparse_ancestors(current)
    for candidate in reversed(missing):
        candidate.mkdir()
        _assert_no_reparse_ancestors(candidate)


def package_files(source_root):
    """Return the exact runtime payload paths, excluding caches and bytecode."""
    source_root = Path(source_root).resolve()
    files = set(RUNTIME_FILES)
    for directory in RUNTIME_DIRECTORIES:
        base = source_root / directory
        if not base.is_dir() or base.is_symlink():
            raise ValueError(f"required runtime directory is missing or unsafe: {base}")
        files.update(
            path.relative_to(source_root).as_posix()
            for path in base.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
        )
    for relative in files:
        source = source_root / relative
        if not source.is_file() or _reparse_or_symlink(source):
            raise ValueError(f"required regular runtime file is missing or unsafe: {source}")
        _assert_no_reparse_ancestors(source.parent)
    return sorted(files)


def _launcher_contents(runtime_script, python):
    runtime_script = Path(runtime_script)
    if os.name == "nt":
        quote_ps = lambda value: "'" + str(value).replace("'", "''") + "'"
        return {
            "devkit.cmd": f'@echo off\r\n"{python}" -I -B "{runtime_script}" %*\r\nexit /b %ERRORLEVEL%\r\n',
            "devkit.ps1": f"& {quote_ps(python)} -I -B {quote_ps(runtime_script)} @args\nexit $LASTEXITCODE\n",
        }
    import shlex

    return {"devkit": f"#!/bin/sh\nexec {shlex.quote(str(python))} -I -B {shlex.quote(str(runtime_script))} \"$@\"\n"}


def install(source_root, install_home):
    source_root = Path(source_root).resolve()
    install_home = Path(os.path.abspath(Path(install_home).expanduser()))
    _assert_no_reparse_ancestors(install_home)
    _mkdir_safe(install_home)
    runtime_parent = install_home / "runtime"
    _mkdir_safe(runtime_parent)
    bin_dir = install_home / "bin"
    _mkdir_safe(bin_dir)

    runtime_root = runtime_parent / "v2"
    _assert_no_reparse_ancestors(runtime_root)
    kit = json.loads((source_root / "kits/dev/kit.yaml").read_text(encoding="utf-8"))
    kit_version = kit["version"]
    files = package_files(source_root)
    stage = Path(tempfile.mkdtemp(prefix=".v2-stage-", dir=runtime_parent))
    backup = runtime_parent / (".v2-old-" + uuid.uuid4().hex)
    old_moved = False
    runtime_installed = False
    staged_launchers = {}
    old_launchers = {}
    try:
        digests = {}
        for relative in files:
            source = source_root / relative
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            digests[relative] = hashlib.sha256(destination.read_bytes()).hexdigest()

        launcher_names = _launcher_contents(runtime_root / "tooling/lib/dev_kit.py", sys.executable)
        launcher_names = tuple(launcher_names)
        launcher_name = "devkit.ps1" if os.name == "nt" else "devkit"
        workflow_command_name = "devkit.cmd" if os.name == "nt" else "devkit"
        manifest = {
            "schema_version": 2,
            "runtime": RUNTIME_NAME,
            "kit_version": kit_version,
            "files": digests,
            "python": sys.executable,
            "launcher": str(bin_dir / launcher_name),
        }
        (stage / "install-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
        )

        for name, content in _launcher_contents(runtime_root / "tooling/lib/dev_kit.py", sys.executable).items():
            staged = bin_dir / ("." + name + "." + uuid.uuid4().hex + ".stage")
            destination = bin_dir / name
            if _reparse_or_symlink(destination):
                raise ValueError(f"unsafe existing launcher path: {destination}")
            old_launchers[name] = (destination.read_bytes(), stat.S_IMODE(destination.stat().st_mode)) if destination.is_file() else None
            staged.write_text(content, encoding="utf-8", newline="\n")
            if os.name != "nt":
                staged.chmod(0o755)
            staged_launchers[name] = staged

        if runtime_root.exists():
            if _reparse_or_symlink(runtime_root):
                raise ValueError(f"unsafe existing V2 runtime path: {runtime_root}")
            runtime_root.rename(backup)
            old_moved = True
        stage.rename(runtime_root)
        runtime_installed = True
        for name, staged in staged_launchers.items():
            os.replace(staged, bin_dir / name)
        if old_moved:
            shutil.rmtree(backup)
        return {
            "runtime_root": str(runtime_root),
            "bin_dir": str(bin_dir),
            "launcher": str(bin_dir / launcher_name),
            "workflow_command": str(bin_dir / workflow_command_name),
            "workflow_normal": str(runtime_root / "kits/dev/plugin/workflows/dev-normal.workflow.yml"),
            "workflow_high_risk": str(runtime_root / "kits/dev/plugin/workflows/dev-high-risk.workflow.yml"),
            "manifest": str(runtime_root / "install-manifest.json"),
            "file_count": len(files),
        }
    except Exception:
        for name, previous in old_launchers.items():
            destination = bin_dir / name
            if previous is None:
                destination.unlink(missing_ok=True)
            else:
                content, mode = previous
                restore = bin_dir / ("." + name + "." + uuid.uuid4().hex + ".restore")
                restore.write_bytes(content)
                restore.chmod(mode)
                os.replace(restore, destination)
        if runtime_installed and runtime_root.exists():
            shutil.rmtree(runtime_root)
        if old_moved and backup.exists():
            backup.rename(runtime_root)
        raise
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        for path in staged_launchers.values():
            path.unlink(missing_ok=True)


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Install the self-contained Dev Kit VNext runtime")
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-home", type=Path, default=Path.home() / ".devkit")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(install(args.source_root, args.install_home), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Dev Kit VNext installation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
