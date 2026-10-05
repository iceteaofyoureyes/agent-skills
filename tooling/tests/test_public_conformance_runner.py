"""Public Phase 9 runner report and genericity contracts."""
import tempfile
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tooling import public_conformance, readiness_acceptance

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
            with patch.object(public_conformance.shutil, "which", return_value="npm"), \
                    patch.object(public_conformance, "_run", return_value=SimpleNamespace(
                        returncode=0, stdout="", stderr="")) as run:
                report = public_conformance.prepare_optional_projection_test_runtime(root, external, environment)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(environment["NODE_PATH"], str(external / "optional-test-projections/node_modules"))
            self.assertEqual(run.call_args.args[0][1], "ci")
            self.assertIn("--offline", run.call_args.args[0])
            self.assertEqual(
                (external / "optional-test-projections/package-lock.json").read_text(encoding="utf-8"),
                "package-lock.json",
            )

    def test_isolated_test_environment_drops_global_node_module_paths(self):
        with patch.dict("os.environ", {"NODE_PATH": "user-global-modules"}):
            environment = public_conformance._isolated_env(Path("external-test-home"))
        self.assertNotIn("NODE_PATH", environment)

    def test_legacy_readiness_module_is_not_suite_tier_a_authority(self):
        modules = {module for group in public_conformance.TIER_A.values() for module in group}
        self.assertNotIn("tooling.tests.test_sdlc_acceptance", modules)

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

    def test_report_has_required_evidence_only_fields_and_closed_status(self):
        report = public_conformance.make_report(
            framework_sha="a" * 40,
            framework_tree="b" * 40,
            suite_manifest_sha256="c" * 64,
            suite_lock_sha256="d" * 64,
            component_versions={"ba": "2.0.0-rc.3", "dev": "0.4.0-rc.2", "test": "2.0.0-rc.10"},
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
