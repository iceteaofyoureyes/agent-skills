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
    "tooling/lib/dev_kit.py",
    "ba-workflow/scripts/contracts.py",
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
    manifest = {"schema_version": 1, "runtime": "dev-kit-v1", "files": {}}

    for relative in RUNTIME_FILES:
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
        "file_count": len(RUNTIME_FILES),
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
