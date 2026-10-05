"""Fresh isolated install acceptance for Test Automation V1."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tooling.lib import ba_kit
from tooling.tests import test_test_automation_v1_acceptance as source_acceptance


ROOT = Path(__file__).resolve().parents[2]


class TestAutomationV1InstalledAcceptance(unittest.TestCase):
    def test_clean_install_runs_automation_v1_from_installed_package(self):
        with tempfile.TemporaryDirectory(prefix="test-automation-v1-installed-") as temporary:
            temporary = Path(temporary)
            outside = temporary / "external-cwd"
            host_dir = temporary / "test-only-host"
            outside.mkdir()
            host_dir.mkdir()

            fixture = source_acceptance.TestAutomationV1Acceptance(
                "test_api_e2e_shift_left_dev_local_manual_review_verify_and_fresh_resume"
            )
            prepare_testware = fixture._approved_testware

            def install_and_prepare_testware():
                installed = ba_kit.install(
                    ROOT, fixture.root / ".agents/skills", "test", project_root=fixture.root,
                )
                if installed["conflicts"]:
                    raise AssertionError(installed["conflicts"])
                return prepare_testware()

            fixture._approved_testware = install_and_prepare_testware
            fixture.setUp()
            self.addCleanup(fixture.doCleanups)
            project = fixture.root
            unrelated = project / "user-owned.txt"
            unrelated.write_bytes(b"preserve project-owned data\n")

            target = project / ".agents/skills"
            self.assertTrue((target / ".test-kit/package-authority.json").is_file())
            expected_unrelated = unrelated.read_bytes()

            doctor_command = [
                sys.executable, "-I", str(ROOT / "tooling/lib/ba_kit.py"),
                "doctor", "test", "--agent", "generic", "--target", str(target),
                "--project-root", str(project),
            ]
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            before = subprocess.run(
                doctor_command, cwd=outside, env=env, capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
            self.assertIn("SCOPE: PACKAGE/CAPABILITY ONLY", before.stdout)

            host = host_dir / "human-receipts.json"
            host.write_text(json.dumps({"test_receipts": fixture.human_gate_receipts}), encoding="utf-8")
            driver = temporary / "installed-automation-v1.py"
            shutil.copy2(ROOT / "tooling/tests/fixtures/installed_automation_v1_acceptance.py", driver)
            self.assertFalse(driver.resolve().is_relative_to(ROOT.resolve()))
            result = subprocess.run(
                [
                    sys.executable, "-I", str(driver), str(target / ".test-kit"), str(project),
                    str(project / fixture.test_run_dir.relative_to(fixture.root)),
                    str(project / fixture.dev_handoff_path.relative_to(fixture.root)), str(host),
                ],
                cwd=outside, env=env, capture_output=True, text=True, timeout=180,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            acceptance = json.loads(result.stdout.strip().splitlines()[-1])
            self.assertEqual(acceptance["state"], "EXECUTION_READY")
            self.assertEqual(acceptance["aut_ids"], ["AUT-0001", "AUT-0002"])
            self.assertEqual(acceptance["manual_testcases"], ["TC-002"])
            self.assertEqual(acceptance["dev_local_testcases"], ["TC-003"])
            self.assertTrue(acceptance["app_write_rejected"])
            self.assertTrue(acceptance["installed_only_imports"])
            self.assertEqual(acceptance["product_execution"], "NOT_RUN")
            self.assertFalse(acceptance["product_command_executed"])
            self.assertRegex(acceptance["automation_revision"], r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
            self.assertEqual(acceptance["fresh_clone_revision"], acceptance["automation_revision"])
            self.assertTrue(acceptance["fresh_clone_paths_reconstructed"])

            after = subprocess.run(
                doctor_command, cwd=outside, env=env, capture_output=True, text=True, timeout=90,
            )
            self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
            self.assertIn("SCOPE: PACKAGE/CAPABILITY ONLY", after.stdout)
            self.assertEqual(unrelated.read_bytes(), expected_unrelated)


if __name__ == "__main__":
    unittest.main()
