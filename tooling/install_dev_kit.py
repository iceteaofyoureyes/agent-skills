"""Install the small Dev Kit runtime outside a target project using stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


RUNTIME_FILES = (
    'shared/__init__.py',
    'shared/sdlc/__init__.py',
    'shared/sdlc/approvals/__init__.py',
    'shared/sdlc/approvals/gate_persistence.py',
    'shared/sdlc/approvals/invariants.py',
    'shared/sdlc/artifacts/__init__.py',
    'shared/sdlc/artifacts/classes.py',
    'shared/sdlc/artifacts/delivery_manifest.py',
    'shared/sdlc/authority/__init__.py',
    'shared/sdlc/authority/approved_baseline.py',
    'shared/sdlc/authority/contracts.py',
    'shared/sdlc/compatibility/__init__.py',
    'shared/sdlc/findings/__init__.py',
    'shared/sdlc/findings/execution_contract.py',
    'shared/sdlc/findings/taxonomy.py',
    'shared/sdlc/promotion/__init__.py',
    'shared/sdlc/promotion/immutable.py',
    'shared/sdlc/provenance/__init__.py',
    'shared/sdlc/provenance/references.py',
    'shared/sdlc/provenance/runtime_paths.py',
    'shared/sdlc/readiness/__init__.py',
    'shared/sdlc/readiness/vocabulary.py',
    'shared/sdlc/readiness/compatibility.py',
    'shared/sdlc/schema.py',
    'shared/sdlc/topology/__init__.py',
    'shared/sdlc/topology/contract.py',
    'shared/sdlc/policy/__init__.py',
    'shared/sdlc/policy/contract.py',
    'shared/sdlc/foundation/__init__.py',
    'shared/sdlc/foundation/contract.py',
    'shared/sdlc/foundation/profiles.py',
    'shared/sdlc/foundation/inventory.py',
    'shared/sdlc/foundation/impact.py',
    'shared/sdlc/foundation/workflow.py',
    'shared/sdlc/foundation/producers.py',
    'shared/sdlc/foundation/cli.py',

    "tooling/__init__.py",
    "tooling/lib/__init__.py",
    "tooling/lib/dev_kit.py",
    "tooling/lib/dev_router.py",
    "kits/dev/kit.yaml",
    "kits/dev/plugin/plugin.json",
    "kits/dev/provenance.lock.json",
    ".agents/plugins/marketplace.json",
    "THIRD_PARTY_NOTICES.md",
    "tooling/tests/fixtures/dev/impact-manifest.valid.json",
    "tooling/tests/fixtures/dev/impact-manifest.invalid.json",
    "tooling/tests/fixtures/dev/dev-handoff.valid.json",
    "tooling/tests/fixtures/dev/dev-handoff.invalid.json",
    "ba-workflow/scripts/contracts.py",
    "ba-workflow/scripts/approved_baseline.py",
    "ba-workflow/scripts/delivery_manifest.py",
    "kits/dev/schemas/start-request.schema.json",
    "kits/dev/schemas/impact-manifest.schema.json",
    "kits/dev/schemas/dev-handoff.schema.json",
    "kits/dev/templates/start-request.template.json",
    "kits/dev/templates/impact-manifest.template.json",
    "kits/dev/templates/dev-handoff.template.json",
    "kits/dev/plugin/workflows/dev-normal.workflow.yml",
    "kits/dev/plugin/workflows/dev-high-risk.workflow.yml",
)


def install(source_root, install_home):
    source_root = Path(source_root).resolve()
    install_home = Path(install_home).expanduser().resolve()
    runtime_root = install_home / "runtime" / "v1"
    bin_dir = install_home / "bin"
    kit_version = json.loads((source_root / "kits/dev/kit.yaml").read_text(encoding="utf-8"))["version"]
    manifest = {"schema_version": 1, "runtime": "dev-kit-v1", "kit_version": kit_version, "files": {}}

    source_files = list(RUNTIME_FILES)
    for directory in ("kits/dev/plugin", "requirements-gap-auditor", "verification-before-completion", "dev-kit", "project-foundation"):
        source_files.extend(p.relative_to(source_root).as_posix() for p in (source_root / directory).rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    source_files = sorted(set(source_files))
    for relative in source_files:
        source = source_root / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"required regular runtime file is missing: {source}")
        destination = runtime_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        manifest["files"][relative] = digest

    runtime_script = runtime_root / "tooling/lib/dev_kit.py"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        launcher = bin_dir / "devkit.cmd"
        launcher.write_text(
            f'@echo off\r\n"{sys.executable}" "{runtime_script}" %*\r\nexit /b %ERRORLEVEL%\r\n',
            encoding="utf-8",
        )
        powershell = bin_dir / "devkit.ps1"
        quote_ps = lambda value: "'" + str(value).replace("'", "''") + "'"
        powershell.write_text(
            f"& {quote_ps(sys.executable)} {quote_ps(runtime_script)} @args\nexit $LASTEXITCODE\n",
            encoding="utf-8",
        )
    else:
        launcher = bin_dir / "devkit"
        import shlex

        launcher.write_text(
            f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(runtime_script))} \"$@\"\n",
            encoding="utf-8",
        )
        launcher.chmod(0o755)

    manifest["python"] = sys.executable
    manifest["launcher"] = str(launcher)
    manifest_path = runtime_root / "install-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "runtime_root": str(runtime_root),
        "bin_dir": str(bin_dir),
        "launcher": str(bin_dir / "devkit.ps1" if os.name == "nt" else launcher),
        "workflow_command": str(bin_dir / "devkit.cmd" if os.name == "nt" else launcher),
        "workflow_normal": str(runtime_root / "kits/dev/plugin/workflows/dev-normal.workflow.yml"),
        "workflow_high_risk": str(runtime_root / "kits/dev/plugin/workflows/dev-high-risk.workflow.yml"),
        "manifest": str(manifest_path),
        "file_count": len(source_files),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install the Dev Kit runtime into a user-scope directory")
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--install-home", type=Path, default=Path.home() / ".devkit")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(install(args.source_root, args.install_home), indent=2))
        return 0
    except (OSError, ValueError) as error:
        print(f"Dev Kit runtime installation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
