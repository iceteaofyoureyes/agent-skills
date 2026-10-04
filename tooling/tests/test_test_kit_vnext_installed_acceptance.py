"""Fresh installed Test VNext acceptance; synthetic Human receipts are not production approvals."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tooling.lib import ba_kit
from tooling.tests import test_ba_vnext as ba_tests


ROOT = Path(__file__).resolve().parents[2]


class InstalledTestVNextAcceptance(unittest.TestCase):
    def _ux_fixture(self, project, suffix):
        root = project / f"approved-ux-{suffix}"
        shutil.copytree(ROOT / "tooling/tests/fixtures/delivery-ux-canonical", root)
        contract = root / "ux/ux-contract.md"
        receipt_path = root / "ux/approval-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["feature_id"] = "FEATURE-1"
        receipt["sources"]["ux/ux-contract.md"] = hashlib.sha256(contract.read_bytes()).hexdigest()
        receipt["semantic_snapshot_sha256"] = hashlib.sha256(
            json.dumps(receipt["sources"], sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        request = {
            "root": str(root),
            "contract": {"path": "ux/ux-contract.md", "revision": receipt["revision"], "sha256": hashlib.sha256(contract.read_bytes()).hexdigest()},
            "approval_receipt": {"path": "ux/approval-receipt.json", "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest()},
            "prototype": {"path": "ux/prototype.html", "sha256": hashlib.sha256((root / "ux/prototype.html").read_bytes()).hexdigest(), "authority": "REVIEW_EVIDENCE"},
        }
        request_path = project / f"ux-request-{suffix}.json"
        request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        host_path = project / f"ux-human-{suffix}.json"
        host_path.write_text(json.dumps({
            "fixture_type": "TEST_ONLY_SYNTHETIC_UX_HUMAN_APPROVAL",
            "not_for_production": True,
            "receipt": receipt,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return request_path, host_path

    def test_clean_installed_runtime_completes_manual_vnext_and_ux_acceptance(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-vnext-installed-") as temporary:
            temporary = Path(temporary)
            project = temporary / "project"
            target = project / ".agents/skills"
            host_dir = temporary / "test-only-human-host"
            outside = temporary / "external-cwd"
            project.mkdir()
            host_dir.mkdir()
            outside.mkdir()
            unrelated = project / "user-owned.txt"
            unrelated.write_bytes(b"preserve project-owned data\n")

            ba_fixture = ba_tests.BAVNextTests("test_greenfield_exact_baseline_and_handoff")
            ba_fixture.setUp()
            self.addCleanup(ba_fixture.doCleanups)
            _state, ba_auth = ba_fixture.approved()
            handoff = ba_tests.ba.make_handoff(
                _state, ba_fixture.root, human_actor_authenticator=ba_auth,
            )
            shutil.copytree(ba_fixture.root, project, dirs_exist_ok=True)
            handoff_path = project / "engineering-handoff-vnext.json"
            handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            ba_host_path = host_dir / "ba-human.json"
            ba_host_path.write_text(json.dumps({
                "fixture_type": "TEST_ONLY_SYNTHETIC_BA_HUMAN_APPROVAL",
                "not_for_production": True,
                "receipt": json.loads((project / "receipt.json").read_text(encoding="utf-8")),
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            ux_request_path, ux_host_path = self._ux_fixture(project, "installed")

            install = ba_kit.install(ROOT, target, "test", project_root=project)
            self.assertFalse(install["conflicts"])
            expected_unrelated = unrelated.read_bytes()
            installed_tree = ba_kit.tree_hash(target)
            second_install = ba_kit.install(ROOT, target, "test", project_root=project)
            self.assertFalse(second_install["conflicts"])
            self.assertEqual(installed_tree, ba_kit.tree_hash(target))
            self.assertEqual(unrelated.read_bytes(), expected_unrelated)

            doctor_command = [
                sys.executable, "-I", str(ROOT / "tooling/lib/ba_kit.py"),
                "doctor", "test", "--agent", "generic", "--target", str(target),
                "--project-root", str(project),
            ]
            doctor = subprocess.run(doctor_command, cwd=outside, capture_output=True, text=True, timeout=90)
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            self.assertIn("SCOPE: PACKAGE/CAPABILITY ONLY", doctor.stdout)
            self.assertIn("STATUS: ", doctor.stdout)
            initial_report = ba_kit.doctor(ROOT, target, "test", project_root=project)
            self.assertIn(initial_report["status"], {"READY", "DEGRADED"}, initial_report)
            self.assertEqual(initial_report["readiness"]["scope"], "PACKAGE_CAPABILITY_ONLY")
            self.assertEqual(initial_report["readiness"]["project_approval"], "NOT_EVALUATED")
            self.assertEqual(initial_report["readiness"]["approved_design"], "NOT_EVALUATED")
            self.assertEqual(initial_report["readiness"]["approved_testware"], "NOT_EVALUATED")
            self.assertEqual(initial_report["readiness"]["execution"], "NOT_EVALUATED")
            installed_check = next(row for row in initial_report["checks"] if row[0] == "Test VNext installed capability")
            self.assertTrue(installed_check[1], installed_check)

            # Simulate absent optional projection dependencies. Core Test VNext must remain ready.
            with (
                mock.patch.dict(os.environ, {"PATH": "", "PYTHONPATH": ""}),
                mock.patch.object(ba_kit.shutil, "which", return_value=None),
                mock.patch("importlib.util.find_spec", return_value=None),
            ):
                optional_report = ba_kit.doctor(ROOT, target, "test", project_root=project)
            self.assertEqual(optional_report["status"], "DEGRADED", optional_report)
            self.assertTrue(next(row for row in optional_report["checks"] if row[0] == "Test VNext installed capability")[1])
            self.assertTrue(any(name == "DEPENDENCY_MISSING" and kind == "dependency" for name, _, kind, _ in optional_report["checks"]))

            driver = temporary / "isolated-installed-test-vnext.py"
            driver.write_bytes((ROOT / "tooling/tests/fixtures/installed_test_vnext_acceptance.py").read_bytes())
            self.assertFalse(driver.resolve().is_relative_to(ROOT.resolve()))
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            result = subprocess.run(
                [sys.executable, "-I", str(driver), str(target / ".test-kit"), str(project),
                 str(handoff_path), str(host_dir), str(ba_host_path), str(ux_request_path), str(ux_host_path)],
                cwd=outside, env=env, capture_output=True, text=True, timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            acceptance = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(acceptance["state"], "APPROVED_TESTWARE")
            self.assertEqual(acceptance["design"], "APPROVED_DESIGN")
            self.assertEqual(acceptance["design_validation"], "PASS")
            self.assertEqual(acceptance["case_validation"], "PASS")
            self.assertEqual(acceptance["trace_ids"], ["BR-001", "FR-001"])
            self.assertEqual(acceptance["legacy"], "LEGACY_COMPAT")
            self.assertIs(acceptance["vnext_authority"], False)
            self.assertEqual(set(acceptance["optional_smokes"]), {"excel", "xmind"})
            self.assertTrue(all(value in {"PASS", "UNAVAILABLE"} for value in acceptance["optional_smokes"].values()))
            self.assertTrue(all(Path(path).resolve().is_relative_to((target / ".test-kit").resolve()) for path in acceptance["module_paths"].values()))

            final_doctor = subprocess.run(doctor_command, cwd=outside, capture_output=True, text=True, timeout=90)
            self.assertEqual(final_doctor.returncode, 0, final_doctor.stdout + final_doctor.stderr)
            final_report = ba_kit.doctor(ROOT, target, "test", project_root=project)
            self.assertIn(final_report["status"], {"READY", "DEGRADED"}, final_report)
            self.assertEqual(final_report["readiness"]["approved_testware"], "NOT_EVALUATED")
            self.assertEqual(unrelated.read_bytes(), expected_unrelated)


if __name__ == "__main__":
    unittest.main()
