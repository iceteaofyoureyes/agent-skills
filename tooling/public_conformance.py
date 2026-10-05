"""Reproduce Phase 9 from a committed candidate in a fresh local clone."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from importlib import metadata
from pathlib import Path
import re
import shutil
import site
import subprocess
import sys
import tempfile

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tooling import sdlc_suite

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "feat/public-cross-kit-conformance-phase9"
TIER_A = {
    "project_foundation": ("tooling.tests.test_project_foundation", "tooling.tests.test_foundation_producers"),
    "ba_vnext": ("tooling.tests.test_ba_vnext", "tooling.tests.test_ba_vnext_installed_acceptance", "tooling.tests.test_baref_coverage"),
    "dev_vnext": (
        "tooling.tests.test_dev_vnext", "tooling.tests.test_dev_vnext_runtime",
        "tooling.tests.test_dev_vnext_runtime_acceptance", "tooling.tests.test_dev_vnext_cli",
        "tooling.tests.test_dev_vnext_spec_kit", "tooling.tests.test_dev_vnext_installed_acceptance",
    ),
    "test_manual_vnext": (
        "tooling.tests.test_test_kit_vnext", "tooling.tests.test_test_kit_vnext_schemas",
        "tooling.tests.test_test_kit_vnext_installed_acceptance",
    ),
    "automation_v1": (
        "tooling.tests.test_test_automation_v1", "tooling.tests.test_test_automation_v1_schemas",
        "tooling.tests.test_test_automation_v1_acceptance", "tooling.tests.test_test_automation_v1_installed_acceptance",
    ),
    "execution_vnext": (
        "tooling.tests.test_test_execution_vnext", "tooling.tests.test_test_execution_vnext_schemas",
        "tooling.tests.test_test_execution_vnext_acceptance", "tooling.tests.test_test_execution_vnext_installed_acceptance",
    ),
    "shared_sdlc": (
        "tooling.tests.test_sdlc_contracts", "tooling.tests.test_shared_sdlc_core",
        "tooling.tests.test_shared_sdlc_wave2",
    ),
    "suite_doctor": ("tooling.tests.test_sdlc_suite_vnext", "tooling.tests.test_public_conformance_runner"),
}
REQUIRED_NEGATIVE_PROBES = (
    "legacy_ba_v1_rejected", "validator_not_approval", "stale_ba_receipt_rejected",
    "stale_test_gate_receipt_rejected", "delivery_manifest_missing_valid",
    "ambiguous_automation_repository_rejected", "wrong_app_revision_rejected",
    "wrong_automation_revision_rejected", "test_only_without_host_rejected",
    "test_automation_app_write_rejected", "dev_verified_rejected", "command_fail_not_defect",
)
REPORT_KEYS = {
    "schema_version", "evidence_class", "framework_sha", "framework_tree",
    "suite_manifest_sha256", "suite_lock_sha256", "component_versions",
    "contract_versions", "doctor_results", "scenario_results", "trace_checks",
    "revision_checks", "fresh_clone", "genericity", "test_summary", "status",
}
PUBLIC_FLOW_TIMEOUT_SECONDS = 3600
FULL_DISCOVERY_TIMEOUT_SECONDS = 5400
PUBLIC_RUN_TIMEOUT_SECONDS = 10800


def test_dependency_runtime():
    dependency_site = Path(site.getusersitepackages()).resolve()
    if not (dependency_site / "pytest/__init__.py").is_file():
        raise ValueError("full tooling unittest discovery requires pytest in the invoking Python user site")
    original_path = sys.path[:]
    sys.path.insert(0, str(dependency_site))
    try:
        distribution = metadata.distribution("pytest")
    except metadata.PackageNotFoundError as error:
        raise ValueError("full tooling unittest discovery requires pytest metadata in the invoking Python user site") from error
    finally:
        sys.path[:] = original_path
    package_path = Path(distribution.locate_file("pytest/__init__.py")).resolve()
    if not package_path.is_relative_to(dependency_site):
        raise ValueError("pytest metadata did not resolve inside the explicit Python user site")
    return dependency_site, distribution.version


def make_report(*, framework_sha, framework_tree, suite_manifest_sha256,
                suite_lock_sha256, component_versions, contract_versions,
                doctor_results, scenario_results, trace_checks, revision_checks,
                fresh_clone, genericity, test_summary, status):
    if status not in {"PASS", "FAIL"}:
        raise ValueError("public conformance report status must be PASS or FAIL")
    report = {
        "schema_version": 1,
        "evidence_class": "PUBLIC_CROSS_KIT_CONFORMANCE",
        "framework_sha": framework_sha,
        "framework_tree": framework_tree,
        "suite_manifest_sha256": suite_manifest_sha256,
        "suite_lock_sha256": suite_lock_sha256,
        "component_versions": component_versions,
        "contract_versions": contract_versions,
        "doctor_results": doctor_results,
        "scenario_results": scenario_results,
        "trace_checks": trace_checks,
        "revision_checks": revision_checks,
        "fresh_clone": fresh_clone,
        "genericity": genericity,
        "test_summary": test_summary,
        "status": status,
    }
    if set(report) != REPORT_KEYS or "READY_TO_MERGE" in json.dumps(report):
        raise ValueError("invalid public conformance evidence shape")
    return report


def scan_genericity(paths):
    private_terms = (
        "Digital" + " " + "Wedding",
        "CR" + "-DWC-",
        "Pet" + "Clinic",
        "Appoint" + "ment",
    )
    windows_user_path = r"[A-Z]:" + re.escape("\\") + "Users" + re.escape("\\") + r"[^\\\s]+"
    home_user_path = re.escape("/" + "home" + "/") + r"[^/\s]+/[^\s]+"
    patterns = (
        ("private_domain_term", re.compile("|".join(re.escape(term) for term in private_terms), re.IGNORECASE)),
        ("local_user_path", re.compile("(?i)(?:" + windows_user_path + "|" + home_user_path + ")")),
        ("private_hostname", re.compile(r"(?i)\b[a-z0-9-]+\.(?:corp|internal)\b")),
        ("feature_branch_url", re.compile(r"(?i)https?://github\.com/[^/\s]+/[^/\s]+/(?:tree|blob)/[^\s]*feature[^\s]*")),
    )
    issues = []
    for candidate in paths:
        path = Path(candidate)
        if not path.is_file():
            issues.append({"path": path.name, "rule": "missing_public_surface"})
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        for rule, pattern in patterns:
            if pattern.search(content):
                issues.append({"path": path.name, "rule": rule})
    return issues


def negative_probe_issues(probes):
    if not isinstance(probes, dict):
        return list(REQUIRED_NEGATIVE_PROBES)
    return sorted(name for name in REQUIRED_NEGATIVE_PROBES if probes.get(name) is not True)


def _run(command, *, cwd, env, timeout=1800):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    return result


def checkout_exact_clone(clone: Path, candidate_sha: str, *, cwd: Path, env: dict) -> None:
    configured = _run(
        ["git", "-C", str(clone), "config", "core.autocrlf", "false"],
        cwd=cwd, env=env, timeout=120,
    )
    if configured.returncode:
        raise ValueError(configured.stderr or "could not pin fresh clone checkout bytes")
    checked_out = _run(
        ["git", "-C", str(clone), "checkout", "--detach", candidate_sha],
        cwd=cwd, env=env, timeout=120,
    )
    if checked_out.returncode:
        raise ValueError(checked_out.stderr or "could not check out exact candidate SHA")


def _unittest_code(root: Path, modules=(), *, discover=False, test_dependency_site=None):
    module_names = repr(tuple(modules))
    if discover and test_dependency_site is None:
        raise ValueError("full unittest discovery requires an explicit pytest test dependency site")
    test_dependencies = (
        f"sys.path.append({str(Path(test_dependency_site).resolve())!r})\n"
        if test_dependency_site is not None else ""
    )
    pytest_summary = (
        "summary['pytest_version'] = __import__('importlib.metadata', fromlist=['version']).version('pytest')\n"
        if discover else ""
    )
    discovery = "suite = loader.discover(str(root / 'tooling/tests'), pattern='test_*.py')" if discover else (
        "suite = unittest.TestSuite()\nfor name in modules:\n    suite.addTests(loader.loadTestsFromName(name))"
    )
    return (
        "import json, pathlib, sys, unittest\n"
        f"root = pathlib.Path({str(root)!r})\n"
        "sys.path.insert(0, str(root))\n"
        f"{test_dependencies}"
        f"modules = {module_names}\n"
        "loader = unittest.defaultTestLoader\n"
        f"{discovery}\n"
        "result = unittest.TextTestRunner(verbosity=1).run(suite)\n"
        "summary = {'total': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'skipped': len(result.skipped)}\n"
        f"{pytest_summary}"
        "print('PUBLIC_TEST_SUMMARY=' + json.dumps(summary))\n"
        "sys.exit(0 if result.wasSuccessful() else 1)\n"
    )


def _isolated_env(home: Path):
    allowed = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "LOCALAPPDATA"}
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env.update({"HOME": str(home), "USERPROFILE": str(home), "CODEX_HOME": str(home / "codex-home"), "PYTHONDONTWRITEBYTECODE": "1"})
    return env


def prepare_optional_projection_test_runtime(root: Path, external: Path, env: dict) -> dict:
    package_root = Path(root) / "tooling/xmind"
    npm = shutil.which("npm.cmd") or shutil.which("npm")
    if npm is None or not all((package_root / name).is_file() for name in ("package.json", "package-lock.json")):
        return {"status": "FAIL"}
    install_root = Path(external) / "optional-test-projections"
    install_root.mkdir(parents=True, exist_ok=True)
    for name in ("package.json", "package-lock.json"):
        shutil.copyfile(package_root / name, install_root / name)
    result = _run([npm, "ci", "--offline", "--prefix", str(install_root)],
                  cwd=external, env=env, timeout=600)
    if result.returncode:
        return {"status": "FAIL"}
    env["NODE_PATH"] = str(install_root / "node_modules")
    return {"status": "PASS", "package": "tooling/xmind/package-lock.json"}


def _test_command(root: Path, modules, *, cwd: Path, env, discover=False, timeout=1800,
                  test_dependency_site=None):
    test_cwd = root if discover else cwd
    code = _unittest_code(root, modules, discover=discover, test_dependency_site=test_dependency_site)
    return _run([sys.executable, "-I", "-B", "-c", code],
                cwd=test_cwd, env=env, timeout=timeout)


def _parse_test_summary(output):
    for line in reversed(output.splitlines()):
        if line.startswith("PUBLIC_TEST_SUMMARY="):
            summary = json.loads(line.split("=", 1)[1])
            summary["summary_marker"] = True
            return summary
    return {"total": 0, "failures": 0, "errors": 1, "skipped": 0, "summary_marker": False}


def unittest_failure_names(output):
    return [line.strip() for line in output.splitlines()
            if line.startswith(("FAIL: ", "ERROR: "))]


def unittest_failure_details(output):
    host_roots = [str(Path.home())]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        try:
            host_roots.append(str(Path(local_app_data).resolve().parents[1]))
        except IndexError:
            pass
    details = []
    for line in output.splitlines():
        detail = line.strip()
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception): .+", detail):
            continue
        for root in host_roots:
            detail = detail.replace(root, "<local>").replace(root.replace("\\", "/"), "<local>")
        details.append(detail)
    return details[-8:]


def summarize_test_results(tiers, full_summary, *, diff_check_passed):
    return {
        "status": "PASS" if all(row.get("status") == "PASS" for row in tiers.values()) else "FAIL",
        "total": full_summary.get("total", 0),
        "failures": full_summary.get("failures", 0),
        "errors": full_summary.get("errors", 0),
        "skipped": full_summary.get("skipped", 0),
        "diff_check": "PASS" if diff_check_passed else "FAIL",
        "tiers": tiers,
    }


def _run_in_clone(root: Path, output: Path, lock_path: Path, spec_kit_cli: Path | None,
                  test_dependency_site: Path | None) -> int:
    root, output, lock_path = root.resolve(), output.resolve(), lock_path.resolve()
    if output.is_relative_to(root) or lock_path.is_relative_to(root):
        raise ValueError("conformance report and run lock must stay outside source tree")
    if spec_kit_cli is None or not Path(spec_kit_cli).is_file():
        raise ValueError("public conformance requires an explicit Spec Kit 1.0.11 executable")
    spec_kit_cli = Path(spec_kit_cli).resolve()
    if test_dependency_site is None:
        raise ValueError("public conformance requires the explicit pytest test dependency site")
    test_dependency_site = Path(test_dependency_site).resolve()
    if test_dependency_site.is_relative_to(root) or not (test_dependency_site / "pytest/__init__.py").is_file():
        raise ValueError("pytest test dependency site must exist outside the fresh framework clone")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    sdlc_suite.verify_lock(root, lock)
    suite_manifest = sdlc_suite.load_manifest(root)
    env = _isolated_env(output.parent / "runtime-home")
    env["PATH"] = str(Path(spec_kit_cli).parent) + os.pathsep + env.get("PATH", "")
    output.parent.mkdir(parents=True, exist_ok=True)
    projection_runtime = prepare_optional_projection_test_runtime(root, output.parent, env)
    doctor_code = (
        "import pathlib,sys; root=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(root)); "
        "from tooling.sdlc_suite import main; sys.exit(main(['doctor','--root',str(root),*sys.argv[2:]]))"
    )
    doctor_args = ["--spec-kit-cli", str(spec_kit_cli)] if spec_kit_cli else []
    doctor_result = _run([sys.executable, "-I", "-B", "-c", doctor_code, str(root), *doctor_args],
                          cwd=output.parent, env=env, timeout=600)
    try:
        doctor = json.loads(doctor_result.stdout)
    except json.JSONDecodeError:
        doctor = {"status": "FAIL", "error": doctor_result.stderr or doctor_result.stdout}

    tiers = {}
    for tier, modules in TIER_A.items():
        result = _test_command(root, modules, cwd=output.parent, env=env)
        summary = _parse_test_summary(result.stderr + "\n" + result.stdout)
        tiers[tier] = {"status": "PASS" if result.returncode == 0 else "FAIL",
                       **summary, "process_returncode": result.returncode}
        failed_tests = unittest_failure_names(result.stderr + "\n" + result.stdout)
        if failed_tests:
            tiers[tier]["failed_tests"] = failed_tests
        failure_details = unittest_failure_details(result.stderr + "\n" + result.stdout)
        if failure_details:
            tiers[tier]["failure_details"] = failure_details

    flow_path = root / "tooling/tests/fixtures/public_cross_kit_conformance.py"
    flow_output = output.parent / "public-flow.json"
    flow_command = [sys.executable, "-I", "-B", str(flow_path), "--framework-root", str(root),
                    "--spec-kit-cli", str(spec_kit_cli), "--output", str(flow_output)]
    flow_result = _run(flow_command, cwd=output.parent, env=env, timeout=PUBLIC_FLOW_TIMEOUT_SECONDS)
    try:
        flow = json.loads(flow_output.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        flow = {"status": "FAIL", "error": flow_result.stderr or flow_result.stdout}
    tiers["installed_public_cross_kit_flow"] = {"status": flow.get("status", "FAIL"), **flow}

    full = _test_command(root, (), cwd=output.parent, env=env, discover=True,
                         timeout=FULL_DISCOVERY_TIMEOUT_SECONDS,
                         test_dependency_site=test_dependency_site)
    full_summary = _parse_test_summary(full.stderr + "\n" + full.stdout)
    tiers["full_tooling_unittest_discovery"] = {
        "status": "PASS" if full.returncode == 0 else "FAIL",
        **full_summary, "process_returncode": full.returncode,
    }
    failed_tests = unittest_failure_names(full.stderr + "\n" + full.stdout)
    if failed_tests:
        tiers["full_tooling_unittest_discovery"]["failed_tests"] = failed_tests
    failure_details = unittest_failure_details(full.stderr + "\n" + full.stdout)
    if failure_details:
        tiers["full_tooling_unittest_discovery"]["failure_details"] = failure_details
    diff_check = _run(["git", "-C", str(root), "diff", "--check"], cwd=output.parent, env=env)
    clean = not sdlc_suite.git_value(root, "status", "--porcelain=v1")

    surfaces = [
        root / "tooling/sdlc-suite.json",
        root / "tooling/sdlc-suite-acceptance.yaml",
        root / "tooling/sdlc_suite.py",
        root / "tooling/public_conformance.py",
        flow_path,
        root / "docs/vi/SDLC_SUITE_CONTRACT.md",
    ]
    genericity_issues = scan_genericity(surfaces)
    genericity = {"status": "FAIL" if genericity_issues else "PASS", "issues": genericity_issues}
    negative_probes = flow.get("negative_probes", {})
    negative_issues = negative_probe_issues(negative_probes)
    if negative_issues:
        flow["status"] = "FAIL"
    scenario_results = dict(flow.get("scenario_results", {}))
    scenario_results["negative_probes"] = negative_probes
    if negative_issues:
        scenario_results["negative_probe_issues"] = negative_issues
    trace_checks = flow.get("trace_checks", {})
    revision_checks = flow.get("revision_checks", {})
    fresh_clone = {"status": "PASS", "clean": clean, "framework_sha": lock["framework_sha"],
                   "framework_tree": lock["framework_tree"], "installed_isolation": flow.get("installed_isolation", {})}
    if not clean:
        fresh_clone["status"] = "FAIL"
    test_summary = summarize_test_results(tiers, full_summary, diff_check_passed=diff_check.returncode == 0)
    test_summary["test_dependency_versions"] = {"pytest": full_summary.get("pytest_version")}
    test_summary["optional_projection_runtime"] = projection_runtime["status"]
    if projection_runtime["status"] != "PASS":
        test_summary["status"] = "FAIL"
    doctor_results = {"suite_doctor": doctor.get("status", "FAIL"), "checks": doctor.get("checks", [])}
    doctor_ready = doctor_results["suite_doctor"] == "READY"
    status = "PASS" if (doctor_ready and test_summary["status"] == "PASS" and
                         genericity["status"] == "PASS" and fresh_clone["status"] == "PASS" and
                         flow.get("status") == "PASS" and diff_check.returncode == 0) else "FAIL"
    compatibility = sdlc_suite.compatibility(root, manifest=suite_manifest)
    report = make_report(
        framework_sha=lock["framework_sha"], framework_tree=lock["framework_tree"],
        suite_manifest_sha256=lock["suite_manifest_sha256"],
        suite_lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
        component_versions=compatibility["component_versions"],
        contract_versions=compatibility["contract_versions"], doctor_results=doctor_results,
        scenario_results=scenario_results, trace_checks=trace_checks,
        revision_checks=revision_checks, fresh_clone=fresh_clone,
        genericity=genericity, test_summary=test_summary, status=status,
    )
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if status == "PASS" else 1


def run_candidate(root: str | Path, output: str | Path, *, spec_kit_cli: str | Path | None = None) -> dict:
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("conformance report must be outside source tree")
    if spec_kit_cli is None or not Path(spec_kit_cli).is_file():
        raise ValueError("public conformance requires an explicit Spec Kit 1.0.11 executable")
    test_dependency_site, _ = test_dependency_runtime()
    branch = sdlc_suite.git_value(root, "branch", "--show-current")
    if branch != BRANCH:
        raise ValueError(f"expected candidate branch {BRANCH}; found {branch}")
    if not sdlc_suite.source_is_clean(root):
        raise ValueError("candidate source must be clean and committed before public conformance")
    candidate_sha = sdlc_suite.git_value(root, "rev-parse", "HEAD")
    candidate_tree = sdlc_suite.git_value(root, "rev-parse", "HEAD^{tree}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="public-cross-kit-conformance-") as temporary:
        external = Path(temporary)
        clone = external / "fresh-framework-clone"
        lock_path = external / "suite-lock.json"
        child_report = external / "clone-report.json"
        clone_result = _run(["git", "clone", "--local", "--no-hardlinks", "--no-checkout", str(root), str(clone)],
                            cwd=external, env=_isolated_env(external / "home"))
        if clone_result.returncode:
            raise ValueError(clone_result.stderr)
        checkout_exact_clone(clone, candidate_sha, cwd=external, env=_isolated_env(external / "home"))
        if sdlc_suite.git_value(clone, "rev-parse", "HEAD") != candidate_sha or not sdlc_suite.source_is_clean(clone):
            raise ValueError("fresh local clone does not match the exact clean candidate")
        sdlc_suite.generate_lock(clone, lock_path)
        script = clone / "tooling/public_conformance.py"
        command = [sys.executable, "-I", "-B", str(script), "--clone-child", "--root", str(clone),
                   "--output", str(child_report), "--lock", str(lock_path)]
        if spec_kit_cli:
            command.extend(["--spec-kit-cli", str(Path(spec_kit_cli).resolve())])
        command.extend(["--test-dependency-site", str(test_dependency_site)])
        result = _run(command, cwd=external, env=_isolated_env(external / "child-home"),
                      timeout=PUBLIC_RUN_TIMEOUT_SECONDS)
        if child_report.is_file():
            report = json.loads(child_report.read_text(encoding="utf-8"))
        else:
            compatibility = sdlc_suite.compatibility(clone)
            report = make_report(
                framework_sha=candidate_sha, framework_tree=candidate_tree,
                suite_manifest_sha256=sdlc_suite.sha256(clone / sdlc_suite.MANIFEST_PATH),
                suite_lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest(),
                component_versions=compatibility["component_versions"], contract_versions=compatibility["contract_versions"],
                doctor_results={"suite_doctor": "NOT_RUN", "error": result.stderr or result.stdout},
                scenario_results={}, trace_checks={}, revision_checks={},
                fresh_clone={"status": "PASS", "clean": sdlc_suite.source_is_clean(clone)},
                genericity={"status": "NOT_RUN", "issues": []},
                test_summary={"status": "FAIL", "total": 0, "failures": 0, "errors": 1, "skipped": 0}, status="FAIL",
            )
        if sdlc_suite.git_value(root, "rev-parse", "HEAD") != candidate_sha or not sdlc_suite.source_is_clean(root):
            report["fresh_clone"]["status"] = "FAIL"
            report["status"] = "FAIL"
        report["fresh_clone"].update({"status": report["fresh_clone"].get("status", "PASS"),
                                      "clean": sdlc_suite.source_is_clean(clone),
                                      "framework_sha": candidate_sha, "framework_tree": candidate_tree})
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run public cross-kit conformance from an exact clean candidate clone")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--spec-kit-cli", type=Path, required=True)
    parser.add_argument("--clone-child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--test-dependency-site", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.clone_child:
            if args.root is None or args.lock is None or args.test_dependency_site is None:
                parser.error("clone child requires --root, --lock, and --test-dependency-site")
            child_root = args.root.resolve()
            sys.path.insert(0, str(child_root))
            if Path(__file__).resolve().parents[1] != child_root:
                raise ValueError("public conformance runner did not execute from the exact fresh clone")
            code = _run_in_clone(child_root, args.output, args.lock, args.spec_kit_cli,
                                 args.test_dependency_site)
            return code
        report = run_candidate(args.repo, args.output, spec_kit_cli=args.spec_kit_cli)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "PASS" else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
