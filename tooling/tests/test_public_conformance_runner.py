"""Public Phase 9 runner report and genericity contracts."""
import os
import json
import shutil
import tempfile
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tooling import public_conformance, readiness_acceptance
from tooling.tests.fixtures import public_cross_kit_conformance

ROOT = Path(__file__).resolve().parents[2]


class PublicConformanceContractTests(unittest.TestCase):
    def test_readiness_compatibility_entrypoint_delegates_to_public_runner(self):
        with patch.object(public_conformance, "main", return_value=0) as runner:
            self.assertEqual(readiness_acceptance.main(["--output", "external-report.json"]), 0)
        runner.assert_called_once_with(["--output", "external-report.json"])

    def test_candidate_runner_requires_explicit_spec_kit_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "explicit Spec Kit 1.0.11"):
                public_conformance.run_candidate(ROOT, Path(directory) / "report.json")

    def _git_candidate(self, parent, *, branch="feature/candidate", detached=False):
        repo = Path(parent) / "candidate"
        repo.mkdir()
        compatibility_sources = (
            "tooling/sdlc-suite.json",
            "kits/ba/kit.yaml", "kits/dev/kit.yaml", "kits/test/kit.yaml",
            "kits/test/package-authority.json",
            "shared/sdlc/schema.py", "shared/sdlc/foundation/contract.py",
            "ba-workflow/scripts/ba_vnext.py",
            "kits/dev/schemas/dev-handoff-v2.schema.json",
            "kits/test/schemas/approved-testware-vnext-handoff-manifest.schema.json",
            "kits/test/schemas/execution-ready-v1-handoff.schema.json",
            "kits/test/schemas/finding-classification-v1.schema.json",
            "kits/test/schemas/defect-handoff-v1.schema.json",
            "kits/test/schemas/ready-for-retest-v1.schema.json",
            "kits/test/schemas/verified-handoff-v1.schema.json",
        )
        for relative in compatibility_sources:
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        subprocess.run(["git", "-C", str(repo), "init", "--quiet", "--initial-branch=main"], check=True)
        for key, value in (("user.name", "Conformance Fixture"),
                           ("user.email", "conformance@example.invalid"),
                           ("core.autocrlf", "false")):
            subprocess.run(["git", "-C", str(repo), "config", key, value], check=True)
        (repo / "source.txt").write_text("committed candidate\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "--quiet", "-m", "Candidate"], check=True)
        if branch != "main":
            subprocess.run(["git", "-C", str(repo), "checkout", "--quiet", "-b", branch], check=True)
        if detached:
            subprocess.run(["git", "-C", str(repo), "checkout", "--quiet", "--detach", "HEAD"], check=True)
        return repo

    def _run_candidate_with_mocked_child(self, repo, external, *, change_source_during_run=False,
                                         commit_source_during_run=False):
        external = Path(external)
        cli = external / "specify"
        cli.write_text("fixture executable", encoding="utf-8")
        dependency_site = external / "pytest-site"
        (dependency_site / "pytest").mkdir(parents=True)
        (dependency_site / "pytest/__init__.py").write_text("", encoding="utf-8")
        output = external / "public-report.json"
        actual_run = public_conformance._run

        def run(command, *, cwd, env, timeout=1800):
            if "--clone-child" not in command:
                return actual_run(command, cwd=cwd, env=env, timeout=timeout)
            child_output = Path(command[command.index("--output") + 1])
            lock = json.loads(Path(command[command.index("--lock") + 1]).read_text(encoding="utf-8"))
            child_output.write_text(json.dumps({
                "status": "PASS",
                "fresh_clone": {"status": "PASS", "clean": True},
                "framework_sha": lock["framework_sha"],
                "framework_tree": lock["framework_tree"],
            }), encoding="utf-8")
            if change_source_during_run:
                (Path(repo) / "source.txt").write_text("changed after candidate start\n", encoding="utf-8")
            if commit_source_during_run:
                (Path(repo) / "source.txt").write_text("new committed source\n", encoding="utf-8")
                subprocess.run(["git", "-C", str(repo), "add", "source.txt"], check=True)
                subprocess.run(["git", "-C", str(repo), "commit", "--quiet", "-m", "New source revision"], check=True)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch.object(public_conformance, "test_dependency_runtime", return_value=(dependency_site, "fixture")), \
                patch.object(public_conformance, "_run", side_effect=run):
            return public_conformance.run_candidate(repo, output, spec_kit_cli=cli)

    def test_clean_arbitrary_candidate_branch_is_accepted_and_clone_identity_is_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._git_candidate(directory, branch="feature/portable-candidate")
            expected_sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            expected_tree = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"], text=True).strip()

            report = self._run_candidate_with_mocked_child(repo, directory)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["fresh_clone"]["framework_sha"], expected_sha)
            self.assertEqual(report["fresh_clone"]["framework_tree"], expected_tree)
            self.assertTrue(report["fresh_clone"]["clean"])

    def test_clean_main_candidate_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._git_candidate(directory, branch="main")

            report = self._run_candidate_with_mocked_child(repo, directory)

            self.assertEqual(report["status"], "PASS")

    def test_clean_detached_head_candidate_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._git_candidate(directory, branch="main", detached=True)

            report = self._run_candidate_with_mocked_child(repo, directory)

            self.assertEqual(report["status"], "PASS")

    def test_dirty_candidate_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._git_candidate(directory)
            (repo / "source.txt").write_text("uncommitted source\n", encoding="utf-8")
            cli = Path(directory) / "specify"
            cli.write_text("fixture executable", encoding="utf-8")
            dependency_site = Path(directory) / "pytest-site"
            (dependency_site / "pytest").mkdir(parents=True)
            (dependency_site / "pytest/__init__.py").write_text("", encoding="utf-8")

            with patch.object(public_conformance, "test_dependency_runtime", return_value=(dependency_site, "fixture")):
                with self.assertRaisesRegex(ValueError, "source must be clean"):
                    public_conformance.run_candidate(repo, Path(directory) / "report.json", spec_kit_cli=cli)

    def test_source_change_after_candidate_start_invalidates_run(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._git_candidate(directory)

            report = self._run_candidate_with_mocked_child(repo, directory, change_source_during_run=True)

            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["fresh_clone"]["status"], "FAIL")

    def test_clean_new_source_commit_after_candidate_start_invalidates_run(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._git_candidate(directory)

            report = self._run_candidate_with_mocked_child(repo, directory, commit_source_during_run=True)

            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(public_conformance.sdlc_suite.source_is_clean(repo))

    def test_fresh_clone_checkout_preserves_exact_git_blob_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory)
            source = external / "source"
            source.mkdir()
            subprocess.run(["git", "-C", str(source), "init", "--quiet"], check=True)
            for key, value in (("user.name", "Conformance Fixture"),
                               ("user.email", "conformance@example.invalid"),
                               ("core.autocrlf", "false")):
                subprocess.run(["git", "-C", str(source), "config", key, value], check=True)
            expected = b"first line\nsecond line\n"
            (source / "sample.txt").write_bytes(expected)
            subprocess.run(["git", "-C", str(source), "add", "sample.txt"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "--quiet", "-m", "Fixture"], check=True)
            candidate = subprocess.check_output(
                ["git", "-C", str(source), "rev-parse", "HEAD"], text=True,
            ).strip()
            clone = external / "clone"
            subprocess.run(
                ["git", "clone", "--local", "--no-hardlinks", "--no-checkout", str(source), str(clone)],
                check=True, capture_output=True, text=True,
            )

            public_conformance.checkout_exact_clone(
                clone, candidate, cwd=external,
                env=public_conformance._isolated_env(external / "temporary-home"),
            )

            self.assertEqual((clone / "sample.txt").read_bytes(), expected)

    def test_optional_projection_runtime_uses_external_locked_offline_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            external = Path(directory) / "external"
            package = root / "tooling/xmind"
            package.mkdir(parents=True)
            external.mkdir()
            for name in ("package.json", "package-lock.json"):
                (package / name).write_text(name, encoding="utf-8")
            environment = {}
            with patch.object(public_conformance.shutil, "which", side_effect=lambda name: "npm" if "npm" in name else "node"), \
                    patch.object(public_conformance, "_run", return_value=SimpleNamespace(
                        returncode=0, stdout="", stderr="")) as run:
                report = public_conformance.prepare_optional_projection_test_runtime(root, external, environment)

            self.assertEqual(report["status"], "OPTIONAL_AVAILABLE")
            self.assertEqual(environment["NODE_PATH"], str(external / "optional-test-projections/node_modules"))
            self.assertEqual(run.call_args.args[0][1], "ci")
            self.assertIn("--offline", run.call_args.args[0])
            self.assertEqual(
                (external / "optional-test-projections/package-lock.json").read_text(encoding="utf-8"),
                "package-lock.json",
            )

    def _run_clone_candidate(self, external, *, npm_available=False, node_available=False,
                              install_returncode=0, doctor_status="READY", test_doctor_status="READY"):
        external = Path(external)
        root = external / "fresh-clone"
        tooling = root / "tooling"
        tooling.mkdir(parents=True)
        (root / "docs/vi").mkdir(parents=True)
        for relative in (
            "sdlc-suite.json", "sdlc-suite-acceptance.yaml", "sdlc_suite.py",
            "public_conformance.py", "tests/fixtures/public_cross_kit_conformance.py",
        ):
            path = tooling / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("neutral public fixture\n", encoding="utf-8")
        (root / "docs/vi/SDLC_SUITE_CONTRACT.md").write_text("neutral public contract\n", encoding="utf-8")
        optional_package = tooling / "xmind"
        optional_package.mkdir()
        (optional_package / "package.json").write_text("{}", encoding="utf-8")
        (optional_package / "package-lock.json").write_text("{}", encoding="utf-8")
        lock_path = external / "suite-lock.json"
        lock_path.write_text(json.dumps({
            "framework_sha": "a" * 40,
            "framework_tree": "b" * 40,
            "suite_manifest_sha256": "c" * 64,
        }), encoding="utf-8")
        output = external / "public-report.json"
        cli = external / "specify"
        cli.write_text("fixture executable", encoding="utf-8")
        dependency_site = external / "pytest-site"
        (dependency_site / "pytest").mkdir(parents=True)
        (dependency_site / "pytest/__init__.py").write_text("", encoding="utf-8")
        flow = {
            "status": "PASS",
            "negative_probes": {name: True for name in public_conformance.REQUIRED_NEGATIVE_PROBES},
            "scenario_results": {}, "trace_checks": {}, "revision_checks": {},
        }
        if test_doctor_status == "DEGRADED":
            test_doctor = {"status": "DEGRADED", "checks": [
                ("DEPENDENCY_MISSING", False, "dependency", "Excel projection dependency openpyxl unavailable"),
            ]}
        elif doctor_status == "FAIL":
            test_doctor = {"status": "FAIL", "checks": [
                ("PACKAGE_AUTHORITY_INVALID", False, "contract", "Test package integrity mismatch"),
            ]}
        else:
            test_doctor = {"status": "READY", "checks": []}
        doctor = {
            "status": doctor_status,
            "checks": [{"name": "Test Doctor optional projections", "status": "PASS"}],
            "per_kit": {"test": test_doctor},
        }

        def locate(command, name):
            return command[command.index(name) + 1]

        def run(command, *, cwd, env, timeout=1800):
            if len(command) > 1 and command[1] == "ci":
                return SimpleNamespace(returncode=install_returncode, stdout="", stderr="offline cache unavailable")
            if any("public_cross_kit_conformance.py" in part for part in command):
                Path(locate(command, "--output")).write_text(json.dumps(flow), encoding="utf-8")
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            if "diff" in command:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stdout=json.dumps(doctor), stderr="")

        def test_command(*args, **kwargs):
            return SimpleNamespace(
                returncode=0,
                stdout="PUBLIC_TEST_SUMMARY={\"total\":1,\"failures\":0,\"errors\":0,\"skipped\":0,\"pytest_version\":\"fixture\"}",
                stderr="",
            )

        def which(name):
            if name in {"npm.cmd", "npm"} and npm_available:
                return "npm.cmd"
            if name in {"node.exe", "node"} and node_available:
                return "node.exe"
            return None

        compatibility = {
            "component_versions": {"ba": "2.0.0-rc.4", "dev": "0.4.0-rc.3", "test": "2.0.0-rc.12"},
            "contract_versions": {"project_foundation": 1},
        }
        with patch.object(public_conformance.shutil, "which", side_effect=which), \
                patch.object(public_conformance, "_run", side_effect=run), \
                patch.object(public_conformance, "_test_command", side_effect=test_command), \
                patch.object(public_conformance.sdlc_suite, "verify_lock"), \
                patch.object(public_conformance.sdlc_suite, "load_manifest", return_value={}), \
                patch.object(public_conformance.sdlc_suite, "compatibility", return_value=compatibility), \
                patch.object(public_conformance.sdlc_suite, "git_value", return_value=""):
            return_code = public_conformance._run_in_clone(root, output, lock_path, cli, dependency_site)
        return return_code, json.loads(output.read_text(encoding="utf-8"))

    def test_public_runner_passes_when_node_and_npm_are_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            return_code, report = self._run_clone_candidate(directory)

            self.assertEqual(return_code, 0)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["test_summary"]["optional_projection_runtime"]["status"], "OPTIONAL_DEGRADED")
            self.assertTrue(report["test_summary"]["optional_projection_runtime"]["reason"])

    def test_public_runner_degrades_when_node_is_absent_even_if_npm_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            return_code, report = self._run_clone_candidate(directory, npm_available=True)

            self.assertEqual(return_code, 0)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["test_summary"]["optional_projection_runtime"]["status"], "OPTIONAL_DEGRADED")
            self.assertIn("Node.js is unavailable", report["test_summary"]["optional_projection_runtime"]["reason"])

    def test_public_runner_passes_when_offline_optional_install_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            return_code, report = self._run_clone_candidate(
                directory, npm_available=True, node_available=True, install_returncode=1,
            )

            self.assertEqual(return_code, 0)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["test_summary"]["optional_projection_runtime"]["status"], "OPTIONAL_DEGRADED")
            self.assertIn("offline cache unavailable", report["test_summary"]["optional_projection_runtime"]["reason"])

    def test_public_runner_reports_available_optional_projection_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            return_code, report = self._run_clone_candidate(
                directory, npm_available=True, node_available=True,
            )

            self.assertEqual(return_code, 0)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["test_summary"]["optional_projection_runtime"]["status"], "OPTIONAL_AVAILABLE")
            self.assertTrue(report["test_summary"]["optional_projection_runtime"]["reason"])

    def test_optional_test_doctor_degradation_keeps_public_core_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            return_code, report = self._run_clone_candidate(
                directory, npm_available=True, node_available=True, test_doctor_status="DEGRADED",
            )

            self.assertEqual(return_code, 0)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["doctor_results"]["test_core_readiness"], "CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE")
            self.assertEqual(report["test_summary"]["optional_projection_runtime"]["status"], "OPTIONAL_DEGRADED")

    def test_public_runner_still_fails_required_test_doctor_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            return_code, report = self._run_clone_candidate(directory, doctor_status="FAIL")

            self.assertEqual(return_code, 1)
            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["doctor_results"]["suite_doctor"], "FAIL")
            self.assertIn("Test package integrity mismatch", str(report["doctor_results"]["test_doctor"]["checks"]))

    def test_isolated_test_environment_drops_global_node_module_paths(self):
        with patch.dict("os.environ", {"NODE_PATH": "user-global-modules"}):
            environment = public_conformance._isolated_env(Path("external-test-home"))
        self.assertNotIn("NODE_PATH", environment)

    def test_legacy_readiness_module_is_not_suite_tier_a_authority(self):
        modules = {module for group in public_conformance.TIER_A.values() for module in group}
        self.assertNotIn("tooling.tests.test_sdlc_acceptance", modules)

    def test_full_discovery_uses_the_tests_directory_as_unittest_top_level(self):
        test_dependency_site = Path("external-test-dependencies")
        code = public_conformance._unittest_code(
            ROOT, discover=True, test_dependency_site=test_dependency_site,
        )
        self.assertIn("loader.discover(str(root / 'tooling/tests'), pattern='test_*.py')", code)
        self.assertNotIn("top_level_dir=str(root)", code)
        dependency_path = repr(str(test_dependency_site.resolve()))
        self.assertIn(dependency_path, code)
        self.assertLess(code.index("sys.path.insert(0, str(root))"), code.index(dependency_path))
        self.assertNotIn("site.getusersitepackages()", code)
        compile(code, "public-full-discovery-runner", "exec")

    def test_full_discovery_runs_from_the_candidate_clone(self):
        with patch.object(public_conformance, "_run", return_value=SimpleNamespace(returncode=0)) as run:
            public_conformance._test_command(
                ROOT, (), cwd=Path("external"), env={}, discover=True,
                test_dependency_site=Path("external-test-dependencies"),
            )
        self.assertEqual(run.call_args.kwargs["cwd"], ROOT)

    def test_runner_resolves_pytest_from_the_operator_test_site(self):
        explicit_site = os.environ.get("PUBLIC_CONFORMANCE_TEST_DEPENDENCY_SITE")
        test_site, version = public_conformance.test_dependency_runtime(explicit_site)
        with tempfile.TemporaryDirectory() as directory:
            environment = public_conformance._isolated_env(Path(directory))
            environment["PUBLIC_CONFORMANCE_TEST_DEPENDENCY_SITE"] = str(test_site)
            code = (
                f"import sys; sys.path.insert(0, {str(ROOT)!r}); "
                "from tooling.public_conformance import test_dependency_runtime; "
                "site, version = test_dependency_runtime(); print(site); print(version)"
            )
            result = subprocess.run(
                [public_conformance.sys.executable, "-I", "-c", code],
                cwd=directory, env=environment, capture_output=True, text=True,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [str(test_site), version])

    def test_manual_stage_requires_negative_probe_evidence_from_prior_stage(self):
        passed = {"negative_probes": {"validator_not_approval": True}}
        self.assertTrue(public_cross_kit_conformance.require_stage_probe(passed, "validator_not_approval"))
        for evidence in ({}, {"negative_probes": {}},
                         {"negative_probes": {"validator_not_approval": False}}):
            with self.subTest(evidence=evidence), self.assertRaisesRegex(AssertionError, "validator_not_approval"):
                public_cross_kit_conformance.require_stage_probe(evidence, "validator_not_approval")

    def test_retest_trace_uses_validated_ready_for_retest_artifact(self):
        source = Path(public_cross_kit_conformance.__file__).read_text(encoding="utf-8")
        self.assertIn('"ready_for_retest": ready_for_retest_artifact["state"]', source)
        self.assertNotIn('"ready_for_retest": ready_for_retest["state"]', source)

    def test_public_long_running_stages_have_explicit_timeout_budgets(self):
        self.assertEqual(public_cross_kit_conformance.stage_timeout_seconds("manual-execution"), 1800)
        self.assertEqual(public_conformance.PUBLIC_FLOW_TIMEOUT_SECONDS, 3600)
        self.assertEqual(public_conformance.FULL_DISCOVERY_TIMEOUT_SECONDS, 5400)
        self.assertEqual(public_conformance.PUBLIC_RUN_TIMEOUT_SECONDS, 10800)

    def test_test_command_applies_its_explicit_timeout(self):
        with patch.object(public_conformance, "_run", return_value=SimpleNamespace(returncode=0)) as run:
            public_conformance._test_command(
                ROOT, (), cwd=ROOT, env={}, discover=True,
                timeout=public_conformance.FULL_DISCOVERY_TIMEOUT_SECONDS,
                test_dependency_site=Path("external-test-dependencies"),
            )
        self.assertEqual(run.call_args.kwargs["timeout"], public_conformance.FULL_DISCOVERY_TIMEOUT_SECONDS)

    def test_negative_probe_contract_requires_every_probe_to_pass(self):
        passed = {name: True for name in public_conformance.REQUIRED_NEGATIVE_PROBES}
        self.assertEqual(public_conformance.negative_probe_issues(passed), [])
        passed.pop("stale_ba_receipt_rejected")
        passed["legacy_ba_v1_rejected"] = False
        self.assertEqual(set(public_conformance.negative_probe_issues(passed)), {
            "stale_ba_receipt_rejected", "legacy_ba_v1_rejected",
        })

    def test_report_test_total_uses_full_discovery_once(self):
        summary = public_conformance.summarize_test_results(
            {"component": {"status": "PASS", "total": 10},
             "full_tooling_unittest_discovery": {"status": "PASS", "total": 20}},
            {"total": 20, "failures": 0, "errors": 0, "skipped": 0},
            diff_check_passed=True,
        )
        self.assertEqual(summary["total"], 20)
        self.assertEqual(summary["tiers"]["component"]["total"], 10)

    def test_unittest_failure_summary_keeps_case_names_without_traceback_paths(self):
        output = (
            "ERROR: test_repo_binding (tooling.tests.test_execution_vnext_acceptance.ExecutionTests)\n"
            "Traceback (most recent call last):\n"
            "  File: C:\\workspace\\test.py\n"
            "FAIL: test_other_contract (tooling.tests.test_execution_vnext.ExecutionTests)\n"
        )
        self.assertEqual(public_conformance.unittest_failure_names(output), [
            "ERROR: test_repo_binding (tooling.tests.test_execution_vnext_acceptance.ExecutionTests)",
            "FAIL: test_other_contract (tooling.tests.test_execution_vnext.ExecutionTests)",
        ])

    def test_unittest_failure_details_extracts_terminal_error_messages(self):
        output = (
            "Traceback (most recent call last):\n"
            "  File: C:\\workspace\\test.py\n"
            "tooling.lib.test_execution_vnext.ExecutionVNextError: application revision mismatch\n"
            "AssertionError: expected VERIFIED\n"
        )
        self.assertEqual(public_conformance.unittest_failure_details(output), [
            "tooling.lib.test_execution_vnext.ExecutionVNextError: application revision mismatch",
            "AssertionError: expected VERIFIED",
        ])

    def test_report_has_required_evidence_only_fields_and_closed_status(self):
        report = public_conformance.make_report(
            framework_sha="a" * 40,
            framework_tree="b" * 40,
            suite_manifest_sha256="c" * 64,
            suite_lock_sha256="d" * 64,
            component_versions={"ba": "2.0.0-rc.4", "dev": "0.4.0-rc.3", "test": "2.0.0-rc.12"},
            contract_versions={"project_foundation": 1},
            doctor_results={"suite": "READY"},
            scenario_results={"straight_pass": {"status": "PASS"}},
            trace_checks={"continuous": True},
            revision_checks={"reproduced": True},
            fresh_clone={"status": "PASS", "clean": True},
            genericity={"status": "PASS", "issues": []},
            test_summary={"status": "PASS", "total": 1, "failures": 0, "errors": 0},
            status="PASS",
        )
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["evidence_class"], "PUBLIC_CROSS_KIT_CONFORMANCE")
        self.assertNotIn("READY_TO_MERGE", str(report))
        with self.assertRaises(ValueError):
            public_conformance.make_report(
                framework_sha="a" * 40,
                framework_tree="b" * 40,
                suite_manifest_sha256="c" * 64,
                suite_lock_sha256="d" * 64,
                component_versions={}, contract_versions={}, doctor_results={},
                scenario_results={}, trace_checks={}, revision_checks={},
                fresh_clone={}, genericity={}, test_summary={}, status="READY_TO_MERGE",
            )

    def test_genericity_scan_rejects_private_semantics_and_branch_urls(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "public-fixture.md"
            source.write_text(
                "An Appoint" + "ment sample.\n" +
                "C:" + "\\Users\\" + "someone\\work\\repo\n" +
                "https://github.com/team/project/tree/feature/private-run\n",
                encoding="utf-8",
            )
            issues = public_conformance.scan_genericity([source])
            self.assertEqual({row["rule"] for row in issues}, {
                "private_domain_term", "local_user_path", "feature_branch_url",
            })

    def test_genericity_scan_accepts_neutral_multirepo_example(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "public-fixture.md"
            source.write_text("resource reservation workspace; project-docs, service-app, test-automation\n", encoding="utf-8")
            self.assertEqual(public_conformance.scan_genericity([source]), [])

    def test_genericity_scanner_does_not_match_its_own_rule_literals(self):
        self.assertEqual(public_conformance.scan_genericity([Path(public_conformance.__file__)]), [])


if __name__ == "__main__":
    unittest.main()
