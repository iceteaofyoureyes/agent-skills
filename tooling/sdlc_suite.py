"""VNext suite manifest, compatibility, lock, and Doctor.

Component package implementations own their contracts. This module records the
suite's required public boundaries and reads their versions from kit manifests,
executable schemas, and public JSON schemas.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = Path("tooling/sdlc-suite.json")
COMPONENTS = ("ba", "dev", "test")
CONTRACT_SOURCES = {
    "project_foundation": ("shared/sdlc/schema.py", "VERSION"),
    "ba_engineering_handoff": ("ba-workflow/scripts/ba_vnext.py", "V2"),
    "dev_handoff": "kits/dev/schemas/dev-handoff-v2.schema.json",
    "approved_testware": "kits/test/schemas/approved-testware-vnext-handoff-manifest.schema.json",
    "execution_ready": "kits/test/schemas/execution-ready-v1-handoff.schema.json",
    "finding_classification": "kits/test/schemas/finding-classification-v1.schema.json",
    "defect_handoff": "kits/test/schemas/defect-handoff-v1.schema.json",
    "ready_for_retest": "kits/test/schemas/ready-for-retest-v1.schema.json",
    "verified_handoff": "kits/test/schemas/verified-handoff-v1.schema.json",
}
PUBLIC_SKILLS = (
    "project-foundation/SKILL.md",
    "ba-workflow/SKILL.md",
    "dev-kit/SKILL.md",
    "kits/test/skills/test-kit/SKILL.md",
    "kits/test/skills/test-automation-v1/SKILL.md",
    "kits/test/skills/test-execution-vnext/SKILL.md",
)
OPTIONAL_TEST_PROJECTIONS = {"openpyxl", "et-xmlfile", "node", "npm", "xmind"}


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_value(root: str | Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def source_is_clean(root: str | Path = ROOT) -> bool:
    return not git_value(root, "status", "--porcelain=v1")


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(root: str | Path = ROOT) -> dict:
    root = Path(root)
    data = _json(root / MANIFEST_PATH)
    if data.get("schema_version") != 1:
        raise ValueError("unsupported suite manifest schema")
    if (data.get("suite_id"), data.get("suite_version"), data.get("release_status")) != (
        "agent-assisted-sdlc-vnext", "1.0.0-rc.1", "INTERNAL_RC_CANDIDATE",
    ):
        raise ValueError("suite candidate identity is invalid")
    if set(data.get("components", {})) != set(COMPONENTS):
        raise ValueError("suite manifest component set is invalid")
    if set(data.get("contracts", {})) != set(CONTRACT_SOURCES):
        raise ValueError("suite manifest public contract set is invalid")
    if data.get("delivery_manifest", {}).get("status") != "DEFERRED_NON_AUTHORITATIVE":
        raise ValueError("Delivery Manifest must remain DEFERRED_NON_AUTHORITATIVE")
    if "delivery_manifest" in data["contracts"] or "delivery_manifest" in data.get("required_capabilities", []):
        raise ValueError("Delivery Manifest cannot be VNext suite authority")
    return data


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return ast.literal_eval(node.value)
    raise ValueError(f"executable contract constant is missing: {path}:{name}")


def _python_schema_version(root: Path, relative: str, symbol: str) -> int:
    path = root / relative
    value = _literal_assignment(path, symbol)
    if isinstance(value, dict):
        versions = value.get("enum")
    else:
        versions = None
    if not isinstance(versions, (tuple, list)) or len(versions) != 1 or type(versions[0]) is not int:
        raise ValueError(f"cannot derive one integer contract version from {relative}:{symbol}")
    return versions[0]


def _json_schema_version(path: Path) -> int:
    schema = _json(path)
    value = schema.get("properties", {}).get("schema_version", {})
    versions = [value["const"]] if type(value.get("const")) is int else value.get("enum")
    if not isinstance(versions, list) or len(versions) != 1 or type(versions[0]) is not int:
        raise ValueError(f"cannot derive one integer contract version from {path}")
    return versions[0]


def current_contract_versions(root: str | Path = ROOT) -> dict:
    root = Path(root)
    versions = {}
    for name, source in CONTRACT_SOURCES.items():
        if isinstance(source, tuple):
            relative, symbol = source
            versions[name] = _python_schema_version(root, relative, symbol)
        else:
            versions[name] = _json_schema_version(root / source)
    # These version constants must describe the named public objects, not an
    # unrelated shared schema reused by accident.
    foundation = (root / "shared/sdlc/foundation/contract.py").read_text(encoding="utf-8")
    ba = (root / "ba-workflow/scripts/ba_vnext.py").read_text(encoding="utf-8")
    if "FOUNDATION_MANIFEST_V1" not in foundation or "APPROVAL_RECEIPT_V1" not in foundation:
        raise ValueError("Project Foundation V1 executable contracts are missing")
    if "HANDOFF_V2" not in ba:
        raise ValueError("BA Engineering Handoff V2 executable contract is missing")
    return versions


def current_component_versions(root: str | Path = ROOT) -> dict:
    root = Path(root)
    versions = {name: _json(root / f"kits/{name}/kit.yaml")["version"] for name in COMPONENTS}
    authority = _json(root / "kits/test/package-authority.json")
    if authority.get("version") not in (None, versions["test"]):
        raise ValueError("Test package authority version differs from kit manifest")
    return versions


def compatibility(root: str | Path = ROOT, *, manifest: dict | None = None) -> dict:
    root = Path(root)
    manifest = load_manifest(root) if manifest is None else manifest
    actual_components = current_component_versions(root)
    for name, actual in actual_components.items():
        expected = manifest["components"][name].get("version")
        if expected != actual:
            raise ValueError(f"component version mismatch: {name} expected {expected}, found {actual}")
    actual_contracts = current_contract_versions(root)
    for name, actual in actual_contracts.items():
        expected = manifest["contracts"][name].get("version")
        if expected != actual:
            raise ValueError(f"contract version mismatch: {name} expected {expected}, found {actual}")
        expected_source = manifest["contracts"][name].get("source")
        declared_source = CONTRACT_SOURCES[name][0] if isinstance(CONTRACT_SOURCES[name], tuple) else CONTRACT_SOURCES[name]
        if expected_source != declared_source:
            raise ValueError(f"contract source mismatch: {name}")
    return {"status": "PASS", "component_versions": actual_components,
            "contract_versions": actual_contracts, "delivery_manifest": "DEFERRED_NON_AUTHORITATIVE"}


def lock_data(root: str | Path = ROOT) -> dict:
    root = Path(root)
    manifest = load_manifest(root)
    compatible = compatibility(root, manifest=manifest)
    return {
        "schema_version": 1,
        "suite_id": manifest["suite_id"],
        "suite_version": manifest["suite_version"],
        "framework_sha": git_value(root, "rev-parse", "HEAD"),
        "framework_tree": git_value(root, "rev-parse", "HEAD^{tree}"),
        "suite_manifest_sha256": sha256(root / MANIFEST_PATH),
        "component_versions": compatible["component_versions"],
        "contract_versions": compatible["contract_versions"],
    }


def generate_lock(root: str | Path = ROOT, output_path: str | Path | None = None) -> dict:
    root = Path(root).resolve()
    if not source_is_clean(root):
        raise ValueError("suite lock requires a clean committed source tree")
    if output_path is None:
        raise ValueError("suite lock output path must be provided outside source tree")
    output_path = Path(output_path).resolve()
    if output_path.is_relative_to(root):
        raise ValueError("suite lock output must be outside the framework source tree")
    data = lock_data(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def verify_lock(root: str | Path, lock: dict) -> dict:
    root = Path(root).resolve()
    if not source_is_clean(root) or lock != lock_data(root):
        raise ValueError("suite lock is stale; rerun full public conformance")
    return {"current": True, "framework_sha": lock["framework_sha"], "framework_tree": lock["framework_tree"]}


def check_runtime_ignores(project: str | Path, lane: str) -> str:
    project = Path(project)
    paths = {
        "docs": [".test-kit/runs/CONFORMANCE/runtime.json", ".sdlc/runs/foundation/CONFORMANCE/state.json"],
        "app": [".devkit/runs/CONFORMANCE/input.json"],
        "automation": [".test-kit/automation/runs/CONFORMANCE/runtime.json"],
    }
    if lane not in paths:
        raise ValueError(f"unknown project lane: {lane}")
    for relative in paths[lane]:
        result = subprocess.run(["git", "-C", str(project), "check-ignore", "--quiet", relative], capture_output=True)
        if result.returncode != 0:
            raise ValueError(f"runtime path is not ignored: {relative}")
    if lane == "app" and subprocess.run(["git", "-C", str(project), "check-ignore", "--quiet", ".specify/project-config.yml"], capture_output=True).returncode == 0:
        raise ValueError("versioned Spec Kit config must remain visible")
    return "PASS"


def test_core_readiness(report: dict) -> str:
    status = report.get("status")
    if status == "READY":
        return "CORE_READY"
    if status != "DEGRADED":
        raise ValueError(f"Test Doctor is not ready: {status}")
    failures = []
    for row in report.get("checks", []):
        if isinstance(row, dict):
            if row.get("status") == "FAIL":
                failures.append((row.get("name"), "contract", str(row.get("details", row))))
        elif isinstance(row, (tuple, list)) and len(row) >= 4 and not row[1]:
            failures.append((row[0], row[2], str(row[3])))
    allowed = bool(failures)
    for name, kind, detail in failures:
        missing_optional = any(dependency in detail.lower() for dependency in OPTIONAL_TEST_PROJECTIONS)
        if name != "DEPENDENCY_MISSING" or kind != "dependency" or not missing_optional:
            allowed = False
    if not allowed:
        raise ValueError("Test Doctor DEGRADED includes a required capability or integrity failure")
    return "CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE"


def _check(name, action, checks):
    try:
        detail = action()
        checks.append({"name": name, "status": "PASS", "detail": detail})
        return detail
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, zipfile.BadZipFile) as error:
        checks.append({"name": name, "status": "FAIL", "detail": str(error)})
        return None


def doctor_summary(reports: dict) -> dict:
    return {key: value.get("status", value) if isinstance(value, dict) else value
            for key, value in reports.items()}


def _foundation_closure(root: Path) -> str:
    required = {
        "shared/sdlc/foundation/contract.py", "shared/sdlc/foundation/workflow.py",
        "shared/sdlc/foundation/cli.py", "shared/sdlc/schema.py",
    }
    archive = root / "ba-workflow/scripts/shared-sdlc-core.zip"
    with zipfile.ZipFile(archive) as payload:
        names = set(payload.namelist())
        missing = required - names
        if missing:
            raise ValueError("Foundation runtime closure missing: " + ", ".join(sorted(missing)))
        for relative in required:
            if payload.read(relative) != (root / relative).read_bytes():
                raise ValueError(f"Foundation runtime package drift: {relative}")
    return "PASS"


def _dev_doctor_command(runtime_root: str | Path, spec_kit_cli: str | Path | None = None) -> list[str]:
    runtime_root = Path(runtime_root).resolve()
    bootstrap = (
        "import pathlib,sys; root=pathlib.Path(sys.argv[1]); arguments=sys.argv[2:]; "
        "sys.path.insert(0,str(root)); from tooling.lib.dev_vnext_doctor import main; "
        "sys.argv=[str(root/'tooling/lib/dev_vnext_doctor.py'),*arguments]; raise SystemExit(main())"
    )
    command = [
        sys.executable, "-I", "-B", "-c", bootstrap, str(runtime_root),
        "--root", str(runtime_root), "--json",
    ]
    if spec_kit_cli:
        command.extend(["--spec-kit-cli", str(spec_kit_cli)])
    return command


def doctor(root: str | Path = ROOT, *, spec_kit_cli: str | Path | None = None,
           docs_project: str | Path | None = None, app_project: str | Path | None = None,
           automation_project: str | Path | None = None) -> dict:
    root = Path(root).resolve()
    checks: list[dict] = []
    reports = {}
    _check("suite manifest and current public contract compatibility", lambda: compatibility(root), checks)
    _check("Project Foundation runtime closure", lambda: _foundation_closure(root), checks)
    _check("required public routers and skills", lambda: _required_files(root, PUBLIC_SKILLS), checks)
    _check("Delivery Manifest non-authority", lambda: _delivery_non_authority(root), checks)
    _check("Test package authority", lambda: _test_package_authority(root), checks)
    _check("runtime-ignore contract", lambda: _runtime_ignore_contract(root), checks)
    if docs_project:
        _check("docs runtime ignore contract", lambda: check_runtime_ignores(docs_project, "docs"), checks)
    if app_project:
        _check("app runtime ignore contract", lambda: check_runtime_ignores(app_project, "app"), checks)
    if automation_project:
        _check("automation runtime ignore contract", lambda: check_runtime_ignores(automation_project, "automation"), checks)

    try:
        from tooling.lib import ba_kit
        from tooling.install_dev_kit import install as install_dev
        with tempfile.TemporaryDirectory(prefix="sdlc-suite-doctor-") as temp:
            temp = Path(temp)
            skills = temp / "project/.agents/skills"
            project = temp / "project"
            project.mkdir(parents=True)
            for kit in ("ba", "test"):
                installed = ba_kit.install(root, skills, kit, project_root=project)
                if installed.get("conflicts"):
                    raise ValueError(f"{kit} package install conflict: {installed['conflicts']}")
                report = ba_kit.doctor(root, skills, kit, project_root=project)
                reports[kit] = report
                if kit == "ba" and report.get("status") != "READY":
                    raise ValueError("BA Doctor must be READY: " + json.dumps(report, ensure_ascii=False))
                if kit == "test":
                    reports["test_core_readiness"] = test_core_readiness(report)
            installed_dev = install_dev(root, temp / "dev-home")
            runtime_root = Path(installed_dev["runtime_root"])
            spec_cli = str(spec_kit_cli) if spec_kit_cli else shutil.which("specify")
            env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "CODEX_HOME"}}
            with tempfile.TemporaryDirectory(prefix="sdlc-dev-doctor-cwd-") as external:
                env["HOME"] = external
                env["USERPROFILE"] = external
                command = _dev_doctor_command(runtime_root, spec_cli)
                result = subprocess.run(command, cwd=external, env=env, capture_output=True, text=True, timeout=120)
                try:
                    reports["dev"] = json.loads(result.stdout)
                except json.JSONDecodeError:
                    reports["dev"] = {"status": "FAIL", "error": result.stderr or result.stdout}
                if result.returncode and reports["dev"].get("status") != "FAIL":
                    reports["dev"]["status"] = "FAIL"
            if reports["dev"].get("status") != "READY":
                raise ValueError("Dev VNext Doctor must be READY: " + json.dumps(reports["dev"], ensure_ascii=False))
        checks.append({"name": "BA, Dev, and Test Doctors", "status": "PASS",
                       "detail": doctor_summary(reports)})
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        checks.append({"name": "BA, Dev, and Test Doctors", "status": "FAIL", "detail": str(error)})

    try:
        env = {key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "CODEX_HOME"}}
        with tempfile.TemporaryDirectory(prefix="foundation-suite-doctor-") as external:
            env["HOME"] = external
            env["USERPROFILE"] = external
            command = [sys.executable, "-I", str(root / "project-foundation/scripts/project_foundation.py"), "--help"]
            result = subprocess.run(command, cwd=external, env=env, capture_output=True, text=True, timeout=30)
            if result.returncode:
                raise ValueError(result.stderr or result.stdout)
        checks.append({"name": "Project Foundation public entrypoint", "status": "PASS", "detail": "isolated --help"})
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        checks.append({"name": "Project Foundation public entrypoint", "status": "FAIL", "detail": str(error)})
    failures = [row for row in checks if row["status"] != "PASS"]
    return {"status": "FAIL" if failures else "READY", "checks": checks,
            "per_kit": {key: value for key, value in reports.items() if key in COMPONENTS}}


def _required_files(root: Path, paths: tuple[str, ...]) -> str:
    missing = [path for path in paths if not (root / path).is_file()]
    if missing:
        raise ValueError("missing public router/skill: " + ", ".join(missing))
    return "PASS"


def _delivery_non_authority(root: Path) -> str:
    manifest = load_manifest(root)
    if "delivery_manifest" in manifest["contracts"] or manifest["delivery_manifest"]["status"] != "DEFERRED_NON_AUTHORITATIVE":
        raise ValueError("Delivery Manifest is required by the suite")
    return "DEFERRED_NON_AUTHORITATIVE"


def _test_package_authority(root: Path) -> str:
    from tooling.lib import ba_kit
    from tooling.lib.package import validate_source_package_integrity
    manifest = ba_kit.load_manifest(root, "test")
    validate_source_package_integrity(root, manifest)
    return "PASS"


def _runtime_ignore_contract(root: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="sdlc-runtime-ignore-") as temp:
        for lane in ("docs", "app", "automation"):
            project = Path(temp) / lane
            project.mkdir()
            subprocess.run(["git", "-C", str(project), "init", "-q"], check=True)
            template = root / "tooling/fixtures/readiness" / ("app.gitignore" if lane == "app" else "docs.gitignore")
            shutil.copyfile(template, project / ".gitignore")
            check_runtime_ignores(project, lane)
    return "PASS"


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Agent-assisted SDLC VNext suite metadata and Doctor")
    commands = parser.add_subparsers(dest="command", required=True)
    lock_parser = commands.add_parser("lock", help="write an external candidate suite lock")
    lock_parser.add_argument("--root", type=Path, default=ROOT)
    lock_parser.add_argument("--output", type=Path, required=True)
    doctor_parser = commands.add_parser("doctor", help="check VNext suite compatibility and installed package Doctors")
    doctor_parser.add_argument("--root", type=Path, default=ROOT)
    doctor_parser.add_argument("--spec-kit-cli", type=Path)
    doctor_parser.add_argument("--docs-project", type=Path)
    doctor_parser.add_argument("--app-project", type=Path)
    doctor_parser.add_argument("--automation-project", type=Path)
    verify_parser = commands.add_parser("verify-lock", help="reject stale candidate suite locks")
    verify_parser.add_argument("--root", type=Path, default=ROOT)
    verify_parser.add_argument("--lock", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "lock":
            report = generate_lock(args.root, args.output)
        elif args.command == "verify-lock":
            report = verify_lock(args.root, _json(args.lock))
        else:
            report = doctor(args.root, spec_kit_cli=args.spec_kit_cli,
                            docs_project=args.docs_project, app_project=args.app_project,
                            automation_project=args.automation_project)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report.get("status") == "FAIL" else 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
