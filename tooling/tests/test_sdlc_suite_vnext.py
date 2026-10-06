"""Suite-level VNext compatibility and candidate-lock contracts."""
import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tooling import sdlc_suite
from tooling.install_dev_kit import install as install_dev

ROOT = Path(__file__).resolve().parents[2]


class SuiteManifestTests(unittest.TestCase):
    def test_manifest_binds_current_component_and_public_contract_versions(self):
        manifest = sdlc_suite.load_manifest(ROOT)
        compatibility = sdlc_suite.compatibility(ROOT, manifest=manifest)

        self.assertEqual(manifest["suite_id"], "agent-assisted-sdlc-vnext")
        self.assertEqual(manifest["suite_version"], "1.0.0-rc.2")
        self.assertEqual(manifest["release_status"], "INTERNAL_RC_CANDIDATE")
        self.assertEqual(compatibility["status"], "PASS", compatibility)
        self.assertEqual(compatibility["component_versions"], {
            "ba": "2.0.0-rc.4", "dev": "0.4.0-rc.3", "test": "2.0.0-rc.12",
        })
        self.assertEqual(compatibility["contract_versions"], {
            "project_foundation": 1,
            "ba_engineering_handoff": 2,
            "dev_handoff": 2,
            "approved_testware": 1,
            "execution_ready": 1,
            "finding_classification": 1,
            "defect_handoff": 1,
            "ready_for_retest": 1,
            "verified_handoff": 1,
        })
        self.assertEqual(manifest["delivery_manifest"]["status"], "DEFERRED_NON_AUTHORITATIVE")
        self.assertNotIn("delivery_manifest", manifest["contracts"])

    def test_component_and_contract_mismatches_fail_compatibility(self):
        manifest = sdlc_suite.load_manifest(ROOT)

        component_mismatch = copy.deepcopy(manifest)
        component_mismatch["components"]["ba"]["version"] = "1.0.0"
        with self.assertRaisesRegex(ValueError, "component version mismatch"):
            sdlc_suite.compatibility(ROOT, manifest=component_mismatch)

        contract_mismatch = copy.deepcopy(manifest)
        contract_mismatch["contracts"]["execution_ready"]["version"] = 2
        with self.assertRaisesRegex(ValueError, "contract version mismatch"):
            sdlc_suite.compatibility(ROOT, manifest=contract_mismatch)

    def test_delivery_manifest_absence_does_not_block_vnext_compatibility(self):
        manifest = sdlc_suite.load_manifest(ROOT)
        manifest["delivery_manifest"]["present"] = False
        self.assertEqual(sdlc_suite.compatibility(ROOT, manifest=manifest)["status"], "PASS")


class SuiteLockTests(unittest.TestCase):
    def test_lock_binds_exact_candidate_and_is_written_outside_source(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "suite-lock.json"
            with patch.object(sdlc_suite, "source_is_clean", return_value=True):
                lock = sdlc_suite.generate_lock(ROOT, output)
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(lock, persisted)
            self.assertEqual(lock["framework_sha"], sdlc_suite.git_value(ROOT, "rev-parse", "HEAD"))
            self.assertEqual(lock["framework_tree"], sdlc_suite.git_value(ROOT, "rev-parse", "HEAD^{tree}"))
            self.assertEqual(lock["suite_manifest_sha256"], sdlc_suite.sha256(ROOT / "tooling/sdlc-suite.json"))
            with patch.object(sdlc_suite, "source_is_clean", return_value=True):
                self.assertTrue(sdlc_suite.verify_lock(ROOT, lock)["current"])

    def test_dirty_candidate_or_stale_lock_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sdlc_suite, "source_is_clean", return_value=True):
                lock = sdlc_suite.generate_lock(ROOT, Path(directory) / "suite-lock.json")
            stale = copy.deepcopy(lock)
            stale["framework_sha"] = "0" * 40
            with patch.object(sdlc_suite, "source_is_clean", return_value=True):
                with self.assertRaisesRegex(ValueError, "suite lock is stale"):
                    sdlc_suite.verify_lock(ROOT, stale)

    def test_dirty_source_cannot_be_locked(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(sdlc_suite, "source_is_clean", return_value=False):
                with self.assertRaisesRegex(ValueError, "clean committed source tree"):
                    sdlc_suite.generate_lock(ROOT, Path(directory) / "suite-lock.json")


class OptionalProjectionPolicyTests(unittest.TestCase):
    def test_test_doctor_degraded_only_for_optional_xmind_excel_is_core_ready(self):
        report = {"status": "DEGRADED", "checks": [
            ("DEPENDENCY_MISSING", False, "dependency", "XMind projection dependency unavailable"),
            ("DEPENDENCY_MISSING", False, "dependency", "Excel projection dependency openpyxl unavailable"),
        ]}
        self.assertEqual(sdlc_suite.test_core_readiness(report), "CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE")

    def test_test_doctor_does_not_blanket_accept_degraded(self):
        reports = (
            {"status": "FAIL", "checks": []},
            {"status": "DEGRADED", "checks": [("PACKAGE_AUTHORITY_INVALID", False, "contract", "drift")]},
            {"status": "DEGRADED", "checks": [("python", False, "dependency", "missing")]},
            {"status": "DEGRADED", "checks": [("xmind", False, "optional", "skill missing")]},
        )
        for report in reports:
            with self.subTest(report=report), self.assertRaises(ValueError):
                sdlc_suite.test_core_readiness(report)

    def test_doctor_summary_accepts_component_status_strings(self):
        self.assertEqual(sdlc_suite.doctor_summary({
            "ba": {"status": "READY"}, "test_core_readiness": "CORE_READY",
        }), {"ba": "READY", "test_core_readiness": "CORE_READY"})


class InstalledDevDoctorIsolationTests(unittest.TestCase):
    def test_dev_doctor_loads_contracts_from_isolated_installed_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            runtime_root = Path(install_dev(ROOT, temp / "dev-home")["runtime_root"])
            env = {key: value for key, value in os.environ.items()
                   if key not in {"PYTHONPATH", "PYTHONHOME", "CODEX_HOME", "HOME", "USERPROFILE"}}
            env.update({"HOME": str(temp), "USERPROFILE": str(temp),
                        "CODEX_HOME": str(temp / "codex-home"), "PYTHONDONTWRITEBYTECODE": "1"})
            command = sdlc_suite._dev_doctor_command(runtime_root)
            result = subprocess.run(
                command, cwd=temp, env=env, capture_output=True, text=True, timeout=120,
            )

            self.assertNotIn("No module named 'tooling'", result.stderr + result.stdout)
            report = json.loads(result.stdout)
            checks = {row["name"]: row["status"] for row in report["checks"]}
            self.assertEqual(checks["VNext, BA, Shared SDLC and Foundation import closure"], "PASS")
            self.assertEqual(checks["V2 schemas/templates and V1 LEGACY_COMPAT artifacts"], "PASS")
            self.assertEqual(checks["provenance, licenses, notices and package hashes"], "PASS", report)
            self.assertTrue(all(Path(path).is_relative_to(runtime_root)
                                for path in report["module_paths"].values()))


if __name__ == "__main__":
    unittest.main()
