"""Fresh isolated Test Kit install acceptance for Phase 8 execution runtime."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tooling.lib import ba_kit
from tooling.tests import test_test_automation_v1_acceptance as phase7


ROOT = Path(__file__).resolve().parents[2]
DRIVER = ROOT / "tooling/tests/fixtures/installed_execution_vnext_acceptance.py"


class TestExecutionVNextInstalledAcceptance(unittest.TestCase):
    def test_installed_execution_defect_fix_reopen_retest_and_straight_pass(self):
        with tempfile.TemporaryDirectory(prefix="execution-vnext-installed-") as temporary:
            temporary = Path(temporary)
            outside = Path(tempfile.gettempdir()).resolve()
            self.assertFalse(outside.is_relative_to(ROOT.resolve()), outside)
            fixture = phase7.TestAutomationV1Acceptance("test_api_e2e_shift_left_dev_local_manual_review_verify_and_fresh_resume")
            prepare_testware = fixture._approved_testware

            def install_before_test_authority():
                installed = ba_kit.install(
                    ROOT, fixture.root / ".agents/skills", "test", project_root=fixture.root,
                )
                if installed["conflicts"]:
                    raise AssertionError(installed["conflicts"])
                return prepare_testware()

            fixture._approved_testware = install_before_test_authority
            fixture.setUp()
            self.addCleanup(fixture.doCleanups)
            from tooling.tests.test_test_execution_vnext_acceptance import TestExecutionVNextAcceptance
            flow = TestExecutionVNextAcceptance("test_both_paths_real_dev_fix_reopen_and_nondefect_routes")
            flow.fixture = fixture
            flow.root = fixture.root
            flow._install_ignores_before_phase8()
            target = fixture.root / ".agents/skills"
            installed = target / ".test-kit"
            self.assertTrue((installed / "tooling/lib/test_execution_vnext.py").is_file())
            before = ba_kit.doctor(ROOT, target, "test", project_root=fixture.root)
            self.assertIn(before["status"], {"READY", "DEGRADED"}, before)
            self.assertTrue(next(row for row in before["checks"] if row[0] == "Test Execution VNext installed capability")[1], before)

            fixture.dev_handoff_path = fixture._ready_for_test_handoff(fixture.root / "initial-installed-dev-handoff.json")
            phase7_runtime, _ = flow._automation_ready("INSTALLED-DEFECT")
            host = fixture.root / "installed-host-receipts.json"
            host.write_text(json.dumps({
                "actor_id": "synthetic-human",
                "ba_receipt": fixture.ba.load("receipt.json"),
                "test_receipts": fixture.human_gate_receipts,
            }, ensure_ascii=False), encoding="utf-8")
            driver = temporary / "installed-execution-vnext.py"
            shutil.copy2(DRIVER, driver)
            self.assertFalse(driver.resolve().is_relative_to(ROOT.resolve()))
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)

            def run_installed(run_id, execution_id, action, *extra):
                result = subprocess.run(
                    [sys.executable, "-I", str(driver), str(installed), str(fixture.root), run_id, execution_id, str(host), action, *map(str, extra)],
                    cwd=outside, env=environment, capture_output=True, text=True, timeout=180,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                payload = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertTrue(payload["installed_only_imports"])
                return payload

            first = run_installed("INSTALLED-DEFECT", "INSTALLED-EXEC-DEFECT", "defect-start")
            self.assertEqual(first["state"], "DEFECT_READY_FOR_DEV")
            defect_id = first["defect_id"]
            dev_fix_1 = flow._dev_fix(
                defect_id, "INSTALLED-DEVFIX-1", 'def submit(payload):\n    return {"saved": payload}\n',
            )
            reopened = run_installed("INSTALLED-DEFECT", "INSTALLED-EXEC-DEFECT", "fix-retest", dev_fix_1, defect_id)
            self.assertEqual(reopened["state"], "REOPENED")
            self.assertEqual(reopened["ready_for_retest"], "READY_FOR_RETEST")
            next_cycle = run_installed("INSTALLED-DEFECT", "INSTALLED-EXEC-DEFECT", "prepare-reopened", defect_id)
            self.assertEqual(next_cycle["defect_id"], defect_id)
            dev_fix_2 = flow._dev_fix(
                defect_id, "INSTALLED-DEVFIX-2", 'def submit(payload):\n    return {"saved": payload, "accepted": True}\n',
            )
            closed = run_installed("INSTALLED-DEFECT", "INSTALLED-EXEC-DEFECT", "fix-retest", dev_fix_2, defect_id)
            self.assertEqual(closed["state"], "VERIFIED")

            fixture.app_revision = fixture._run_git(fixture.app_root, "rev-parse", "HEAD")
            fixture.dev_handoff_path = fixture._ready_for_test_handoff(fixture.root / "post-fix-installed-dev-handoff.json")
            flow._automation_ready("INSTALLED-STRAIGHT")
            straight = run_installed("INSTALLED-STRAIGHT", "INSTALLED-EXEC-STRAIGHT", "straight-pass")
            self.assertEqual(straight["state"], "VERIFIED")
            app_source = fixture.app_root / "src/request.py"
            app_bytes = app_source.read_bytes()
            app_source.write_bytes(app_bytes + b"\n# installed post-verification drift\n")
            drift = run_installed("INSTALLED-STRAIGHT", "INSTALLED-EXEC-STRAIGHT", "revalidate")
            self.assertEqual(drift["state"], "REJECTED")
            self.assertEqual(drift["code"], "EXECUTION_STALE")
            app_source.write_bytes(app_bytes)

            after = ba_kit.doctor(ROOT, target, "test", project_root=fixture.root)
            self.assertIn(after["status"], {"READY", "DEGRADED"}, after)
            self.assertTrue(next(row for row in after["checks"] if row[0] == "Test Execution VNext installed capability")[1], after)


if __name__ == "__main__":
    unittest.main()
