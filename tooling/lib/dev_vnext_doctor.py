"""Package and capability Doctor for the installed Dev Kit VNext runtime."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SPEC_KIT_VERSION = (1, 0, 11)
MODULES = (
    "tooling.lib.dev_kit",
    "tooling.lib.dev_router",
    "tooling.lib.dev_vnext",
    "tooling.lib.dev_vnext_runtime",
    "tooling.lib.dev_vnext_cli",
    "tooling.lib.dev_vnext_spec_kit",
    "tooling.lib.dev_vnext_doctor",
    "ba_contracts",
    "ba_vnext",
    "approved_baseline",
    "shared.sdlc.schema",
    "shared.sdlc.authority.approved_baseline",
    "shared.sdlc.findings.taxonomy",
    "shared.sdlc.foundation.contract",
    "shared.sdlc.foundation.impact",
    "shared.sdlc.foundation.inventory",
    "shared.sdlc.foundation.profiles",
    "shared.sdlc.foundation.workflow",
    "shared.sdlc.foundation.producers",
)
V2_SCHEMAS = {
    "start-request-v2.schema.json": "START_REQUEST_V2",
    "engineering-impact-v2.schema.json": "IMPACT_V2",
    "engineering-gap-v2.schema.json": "GAP_V2",
    "engineering-decision-v2.schema.json": "DECISION_V2",
    "dev-state-v2.schema.json": "STATE_V2",
    "technical-approval-v2.schema.json": "TECHNICAL_RECEIPT_V2",
    "dev-handoff-v2.schema.json": "HANDOFF_V2",
}
V2_TEMPLATES = (
    "start-request-v2.template.json",
    "engineering-impact-v2.template.json",
    "engineering-gap-v2.template.json",
    "engineering-decision-v2.template.json",
    "technical-approval-v2.boundary.md",
    "dev-handoff-v2.shape.md",
)
V1_ARTIFACTS = (
    "schemas/start-request.schema.json",
    "schemas/impact-manifest.schema.json",
    "schemas/dev-handoff.schema.json",
    "templates/start-request.template.json",
    "templates/impact-manifest.template.json",
    "templates/dev-handoff.template.json",
)
FORBIDDEN_SPEC_KIT_COMMANDS = (
    "speckit.specify", "speckit.plan", "speckit.tasks", "speckit.analyze", "speckit.converge"
)


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _is_reparse(path):
    try:
        info = Path(path).lstat()
    except OSError:
        return False
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _module_paths(root):
    paths = {}
    errors = []
    root = Path(root).resolve()
    for name in MODULES:
        try:
            module = importlib.import_module(name)
            path = Path(module.__file__).resolve()
            if not path.is_relative_to(root):
                errors.append(f"{name} resolved outside installed runtime/v2: {path}")
            paths[name] = str(path)
        except (ImportError, OSError, AttributeError) as error:
            errors.append(f"{name} cannot be imported: {error}")
    return paths, errors


def _version(value):
    import re

    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value or "")
    return tuple(map(int, match.groups())) if match else None


def _manifest_errors(root, kit):
    root = Path(root).resolve()
    errors = []
    manifest_path = root / "install-manifest.json"
    try:
        manifest = _read_json(manifest_path)
    except (OSError, ValueError) as error:
        return [f"V2 install manifest is missing or invalid: {error}"]
    if not isinstance(manifest, dict):
        return ["V2 install manifest must be a JSON object"]
    if (manifest.get("schema_version"), manifest.get("runtime"), manifest.get("kit_version")) != (
        2, "dev-kit-v2", kit.get("version")
    ):
        errors.append("V2 install manifest identity/version differs from kit.yaml")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        return errors + ["V2 install manifest has no exact file inventory"]
    actual_paths = set()
    for path in root.rglob("*"):
        if path.is_file():
            if _is_reparse(path):
                errors.append(f"installed runtime contains a symlink/reparse file: {path.relative_to(root)}")
                continue
            relative = path.relative_to(root).as_posix()
            if "__pycache__" in Path(relative).parts or Path(relative).suffix == ".pyc":
                continue
            if relative != "install-manifest.json":
                actual_paths.add(relative)
    if actual_paths != set(files):
        errors.append("V2 installed file inventory differs from install-manifest.json")
    for relative, expected in files.items():
        path = root / relative
        try:
            if Path(relative).is_absolute() or ".." in Path(relative).parts or _is_reparse(path):
                raise ValueError("unsafe path")
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != expected:
                errors.append(f"installed file hash mismatch: {relative}")
        except (OSError, ValueError, TypeError):
            errors.append(f"installed file is missing or unsafe: {relative}")
    launcher = manifest.get("launcher")
    if not isinstance(launcher, str) or not Path(launcher).is_file() or _is_reparse(launcher):
        errors.append("installed V2 launcher is missing or unsafe")
    else:
        try:
            text = Path(launcher).read_text(encoding="utf-8")
            if "-I" not in text or "-B" not in text or str(root / "tooling/lib/dev_kit.py") not in text:
                errors.append("installed launcher does not isolate Python, suppress bytecode, or target runtime/v2")
        except OSError as error:
            errors.append(f"cannot read installed V2 launcher: {error}")
    if not isinstance(manifest.get("python"), str) or not manifest["python"]:
        errors.append("install manifest has no Python executable")
    return errors


def _contract_errors(root):
    errors = []
    from tooling.lib import dev_vnext as contract

    schema_dir = Path(root) / "kits/dev/schemas"
    for filename, name in V2_SCHEMAS.items():
        try:
            actual = _read_json(schema_dir / filename)
            expected = json.loads(json.dumps(getattr(contract, name)))
            if actual != expected:
                errors.append(f"V2 schema drift from executable contract: {filename}")
        except (OSError, ValueError, AttributeError, TypeError) as error:
            errors.append(f"V2 schema missing/invalid: {filename}: {error}")
    for relative in V2_TEMPLATES:
        path = Path(root) / "kits/dev/templates" / relative
        if not path.is_file() or _is_reparse(path):
            errors.append(f"V2 template/boundary missing or unsafe: {relative}")
    for relative in V1_ARTIFACTS:
        path = Path(root) / "kits/dev" / relative
        if not path.is_file() or _is_reparse(path):
            errors.append(f"V1 LEGACY_COMPAT artifact missing or unsafe: {relative}")
    for name in ("start-request", "impact-manifest", "dev-handoff"):
        try:
            schema = _read_json(Path(root) / f"kits/dev/schemas/{name}.schema.json")
            template = _read_json(Path(root) / f"kits/dev/templates/{name}.template.json")
            if schema.get("properties", {}).get("schema_version", {}).get("const") != 1:
                errors.append(f"V1 {name} schema no longer exposes schema_version 1 LEGACY_COMPAT")
            if template.get("schema_version") != 1:
                errors.append(f"V1 {name} template no longer remains schema_version 1")
        except (OSError, ValueError, AttributeError):
            errors.append(f"V1 LEGACY_COMPAT {name} schema/template cannot be inspected")
    legacy_note = Path(root) / "kits/dev/LEGACY_COMPAT.md"
    try:
        note = legacy_note.read_text(encoding="utf-8")
        if "LEGACY_COMPAT" not in note or "never supply VNext authority" not in note:
            errors.append("V1 package surfaces lack their explicit LEGACY_COMPAT boundary")
    except OSError:
        errors.append("V1 LEGACY_COMPAT note is missing")
    boundary = Path(root) / "kits/dev/templates/technical-approval-v2.boundary.md"
    try:
        text = boundary.read_text(encoding="utf-8")
        if '"decision": "APPROVE"' in text or '"actor_id":' in text:
            errors.append("technical approval boundary contains a fabricated usable receipt")
        if "host" not in text.lower() or "does not approve" not in text.lower():
            errors.append("technical approval boundary does not state host-authentication limits")
    except OSError:
        pass
    return errors


def _skill_errors(root, kit):
    root = Path(root)
    errors = []
    groups = kit.get("plugin_skills", {}) if isinstance(kit, dict) else {}
    if not isinstance(groups, dict):
        errors.append("kit.yaml plugin_skills must be an object")
        groups = {}
    plugin = root / "kits/dev/plugin"
    try:
        plugin_meta = _read_json(plugin / "plugin.json")
    except (OSError, ValueError):
        plugin_meta = {}
        errors.append("Dev plugin metadata is missing or invalid")
    if not isinstance(plugin_meta, dict):
        plugin_meta = {}
        errors.append("Dev plugin metadata must be an object")
    if plugin_meta.get("version") != kit.get("version"):
        errors.append("plugin and kit prerelease versions differ")
    core = groups.get("core", [])
    conditional = groups.get("conditional", [])
    if not isinstance(core, list) or not isinstance(conditional, list):
        errors.append("plugin core and conditional skills must be lists")
        core = core if isinstance(core, list) else []
        conditional = conditional if isinstance(conditional, list) else []
    for skill in core + conditional:
        if not isinstance(skill, str):
            errors.append("plugin skill identity must be text")
            continue
        skill_path = plugin / "skills" / skill / "SKILL.md"
        if not skill_path.is_file() or _is_reparse(skill_path):
            errors.append(f"Dev plugin skill is missing or unsafe: {skill}")
    shared = kit.get("shared_skills", {}) if isinstance(kit, dict) else {}
    if not isinstance(shared, dict):
        errors.append("kit.yaml shared_skills must be an object")
        shared = {}
    required = shared.get("required", [])
    if not isinstance(required, list):
        errors.append("kit.yaml required shared skills must be a list")
        required = []
    for skill in required:
        if not isinstance(skill, str):
            errors.append("shared skill identity must be text")
            continue
        if not (root / skill / "SKILL.md").is_file():
            errors.append(f"required shared skill is missing: {skill}")
    return errors


def doctor(root=ROOT, spec_kit_cli=None):
    root = Path(root).resolve()
    errors = []
    checks = []
    try:
        kit = _read_json(root / "kits/dev/kit.yaml")
        if not isinstance(kit, dict):
            raise ValueError("kit.yaml must be a JSON object")
    except (OSError, ValueError) as error:
        kit = {}
        errors.append(f"kit metadata is missing or invalid: {error}")
    layout_ok = root.name == "v2" and root.parent.name == "runtime"
    checks.append({"name": "installed runtime/v2 layout", "status": "PASS" if layout_ok else "FAIL"})
    if not layout_ok:
        errors.append("Dev VNext Doctor requires the installed runtime/v2 root")

    manifest_errors = _manifest_errors(root, kit)
    checks.append({"name": "install manifest, hashes, Python isolation and launcher", "status": "PASS" if not manifest_errors else "FAIL", "details": manifest_errors})
    errors.extend(manifest_errors)

    module_paths, module_errors = _module_paths(root)
    checks.append({"name": "VNext, BA, Shared SDLC and Foundation import closure", "status": "PASS" if not module_errors else "FAIL", "modules": module_paths, "details": module_errors})
    errors.extend(module_errors)

    contract_errors = _contract_errors(root)
    checks.append({"name": "V2 schemas/templates and V1 LEGACY_COMPAT artifacts", "status": "PASS" if not contract_errors else "FAIL", "details": contract_errors})
    errors.extend(contract_errors)

    try:
        from tooling.lib import dev_kit

        provenance_errors = dev_kit.validate_provenance(root)
        workflow_errors = dev_kit.validate_workflow_package(root)
    except (ImportError, OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        provenance_errors = [f"provenance tools unavailable: {error}"]
        workflow_errors = []
    if not (root / "LICENSE").is_file() or not (root / "THIRD_PARTY_NOTICES.md").is_file():
        provenance_errors.append("root license or third-party notices are missing")
    if not (root / "kits/dev/plugin/THIRD_PARTY_NOTICES.md").is_file():
        provenance_errors.append("plugin third-party notices are missing")
    checks.append({"name": "provenance, licenses, notices and package hashes", "status": "PASS" if not provenance_errors else "FAIL", "details": provenance_errors})
    errors.extend(provenance_errors)
    checks.append({"name": "Spec Kit forbidden commands and workflow pin", "status": "PASS" if not workflow_errors else "FAIL", "details": workflow_errors})
    errors.extend(workflow_errors)

    skill_errors = _skill_errors(root, kit)
    checks.append({"name": "plugin core, conditional and shared skill closure", "status": "PASS" if not skill_errors else "FAIL", "details": skill_errors})
    errors.extend(skill_errors)

    spec = str(spec_kit_cli) if spec_kit_cli else shutil.which("specify")
    try:
        command = [spec, "--version"] if spec else None
        if spec and os.name == "nt" and Path(spec).suffix.lower() in (".cmd", ".bat"):
            command = ["cmd", "/c", spec, "--version"]
        elif spec and os.name == "nt" and Path(spec).suffix.lower() == ".ps1":
            command = ["powershell", "-NoProfile", "-File", spec, "--version"]
        process = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False) if command else None
        actual_version = _version((process.stdout + " " + process.stderr) if process else "")
    except (OSError, subprocess.TimeoutExpired):
        actual_version = None
    pinned = kit.get("runtime_dependencies", {}).get("spec_kit", {}).get("version")
    spec_ok = pinned == "v1.0.11" and actual_version == SPEC_KIT_VERSION
    details = {"pinned": pinned, "installed": ".".join(map(str, actual_version)) if actual_version else "unavailable"}
    checks.append({"name": "Spec Kit 1.0.11 runtime pin", "status": "PASS" if spec_ok else "FAIL", "details": details})
    if not spec_ok:
        errors.append("Spec Kit CLI is missing or differs from the required 1.0.11 pin")

    return {
        "status": "FAIL" if errors else "READY",
        "readiness_scope": "PACKAGE/CAPABILITY READY",
        "checks": checks,
        "errors": errors,
        "module_paths": module_paths,
    }


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Dev Kit VNext package/capability Doctor")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--spec-kit-cli", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = doctor(args.root, args.spec_kit_cli)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("Dev Kit VNext Doctor — PACKAGE/CAPABILITY READY check")
        for check in report["checks"]:
            print(f"[{check['status']}] {check['name']}")
            for detail in check.get("details", []):
                print(f"  - {detail}")
        print("STATUS: " + report["status"])
        print("READINESS SCOPE: " + report["readiness_scope"])
    return 1 if report["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
