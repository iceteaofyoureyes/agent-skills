"""Project-owned customization diagnostics stay outside package integrity."""

import io
import builtins
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from tooling.lib import ba_kit
from tooling.lib import test_kit_policy as policy


class ProjectPolicyDoctorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-kit-policy-doctor-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        self.project = self.root / "project"
        self.target = self.project / ".agents/skills"
        source_skill = self.source / "kits/test/skills/test-kit"
        source_skill.mkdir(parents=True)
        (source_skill / "SKILL.md").write_bytes(b"---\nname: test-kit\ndescription: Doctor fixture\n---\n")
        manifest = {
            "schema_version": 1, "id": "test", "name": "Test Kit", "version": "1.1.0",
            "workflow": {"skill": "test-kit"}, "core": [],
            "skills": {"required": [], "optional": []},
            "skill_sources": {"test-kit": "kits/test/skills/test-kit"},
        }
        (self.source / "kits/test/kit.yaml").write_bytes(json.dumps(manifest).encode())
        ba_kit.install(self.source, self.target, "test")

    def _bootstrap(self):
        policy.bootstrap_project_policy(self.project)

    def _report(self):
        return ba_kit.doctor(self.source, self.target, "test", project_root=self.project)

    def _assert_policy_failure(self, report):
        self.assertEqual(report["status"], "FAIL", report)
        self.assertEqual(report["project_policy"]["status"], "FAIL")
        self.assertTrue(any(not ok and kind == "project_policy" for _, ok, kind, _ in report["checks"]))
        self.assertFalse(any(name in {"MODIFIED_MANAGED_FILE", "MISSING_MANAGED_FILE"} for name, _, _, _ in report["checks"]))

    def test_no_profile_keeps_v1_compatibility(self):
        report = self._report()
        self.assertEqual(report["status"], "READY", report)
        self.assertEqual(report["project_policy"]["status"], "NO_PROJECT_POLICY")
        self.assertIn(("NO_PROJECT_POLICY", True, "project_policy", ""), report["checks"])
        self.assertEqual(report["readiness"]["automation_v1"], "PACKAGE_CAPABILITY_ONLY")
        self.assertEqual(report["readiness"]["execution_ready"], "NOT_EVALUATED")

    def test_valid_policy_passes_and_conventional_target_infers_project(self):
        self._bootstrap()
        report = ba_kit.doctor(self.source, self.target, "test")
        self.assertEqual(report["status"], "READY", report)
        self.assertEqual(report["project_policy"]["status"], "PASS")
        self.assertEqual(set(report["project_policy"]["snapshots"]), {"DESIGN", "CASES"})

    def test_malformed_profile_is_reported_separately(self):
        self._bootstrap()
        (self.project / ".test-kit/project.yaml").write_bytes(b"schema_version: [unterminated\n")
        self._assert_policy_failure(self._report())

    def test_missing_rule_is_reported_separately(self):
        self._bootstrap()
        (self.project / ".test-kit/rules/common.md").unlink()
        self._assert_policy_failure(self._report())

    def test_invalid_utf8_is_reported(self):
        self._bootstrap()
        (self.project / ".test-kit/rules/common.md").write_bytes(b"\xff\xfe")
        self._assert_policy_failure(self._report())

    def test_traversal_is_reported(self):
        self._bootstrap()
        profile = self.project / ".test-kit/project.yaml"
        profile.write_bytes(profile.read_bytes().replace(b"rules/common.md", b"../outside.md"))
        self._assert_policy_failure(self._report())

    def test_duplicate_rule_is_reported(self):
        self._bootstrap()
        profile = self.project / ".test-kit/project.yaml"
        profile.write_bytes(profile.read_bytes().replace(b"- rules/common.md", b"- rules/common.md\n    - rules/common.md"))
        self._assert_policy_failure(self._report())

    def test_template_path_and_type_are_checked_without_excel_dependencies(self):
        self._bootstrap()
        template = self.project / ".test-kit/templates/testcases.xlsx"
        template.parent.mkdir()
        template.write_bytes(b"presentation-only workbook is inspected at projection time")
        profile = self.project / ".test-kit/project.yaml"
        original = profile.read_bytes()
        profile.write_bytes(original.replace(b"templates: {}", b"templates:\n  excel:\n    path: templates/testcases.xlsx"))
        self.assertIn(b"path: templates/testcases.xlsx", profile.read_bytes())
        import_module = builtins.__import__

        def core_only_import(name, *args, **kwargs):
            if "openpyxl" in name or "test_kit_v1_excel" in name:
                raise ModuleNotFoundError("optional Excel dependencies intentionally unavailable")
            return import_module(name, *args, **kwargs)

        with mock.patch.object(builtins, "__import__", side_effect=core_only_import):
            report = self._report()
        self.assertEqual(report["status"], "READY", report)
        self.assertEqual(Path(report["project_policy"]["excel_template"]), template.resolve())
        profile.write_bytes(profile.read_bytes().replace(b"testcases.xlsx", b"testcases.xls"))
        self._assert_policy_failure(self._report())

    def test_personal_override_blocks_even_without_profile_and_is_preserved(self):
        personal = self.project / "_bmad/custom/bmad-testarch-test-design.user.toml"
        personal.parent.mkdir(parents=True)
        content = b'[workflow]\npersistent_facts = ["private convention"]\n'
        personal.write_bytes(content)
        report = self._report()
        self._assert_policy_failure(report)
        self.assertIn("PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED", {f["code"] for f in report["project_policy"]["findings"]})
        self.assertEqual(personal.read_bytes(), content)

    def test_missing_tea_bridge_is_reported_without_creating_it(self):
        self._bootstrap()
        bridge = self.project / "_bmad/custom/bmad-testarch-test-design.toml"
        bridge.unlink()
        report = self._report()
        self._assert_policy_failure(report)
        self.assertIn("TEA_BRIDGE_MISSING", {f["code"] for f in report["project_policy"]["findings"]})
        self.assertFalse(bridge.exists())

    def test_user_rule_edit_changes_snapshot_without_package_drift(self):
        self._bootstrap()
        before = self._report()
        rule = self.project / ".test-kit/rules/common.md"
        rule.write_bytes(rule.read_bytes() + b"\nUse project-approved data fixtures.\n")
        after = self._report()
        self.assertEqual(after["status"], "READY", after)
        self.assertNotEqual(before["project_policy"]["snapshots"], after["project_policy"]["snapshots"])
        self.assertFalse(any(name == "MODIFIED_MANAGED_FILE" for name, _, _, _ in after["checks"]))
        record = json.loads((self.target / ".test-kit-install.json").read_text(encoding="utf-8"))
        self.assertFalse(any("rules/" in name or name.endswith("project.yaml") for name in record["managed_files"]))

    def test_doctor_cli_checks_explicit_project_and_prints_separate_group(self):
        self._bootstrap()
        output = io.StringIO()
        with mock.patch.object(ba_kit, "ROOT", self.source), redirect_stdout(output):
            code = ba_kit.main(["doctor", "test", "--target", str(self.target), "--project-root", str(self.project)])
        self.assertEqual(code, 0, output.getvalue())
        self.assertIn("Project policy", output.getvalue())
        self.assertIn("PROJECT_POLICY_VALID", output.getvalue())

    def test_doctor_cli_defaults_policy_root_to_working_directory(self):
        self._bootstrap()
        (self.project / ".test-kit/rules/common.md").unlink()
        output = io.StringIO()
        with mock.patch.object(ba_kit, "ROOT", self.source), mock.patch.object(Path, "cwd", return_value=self.project), redirect_stdout(output):
            code = ba_kit.main(["doctor", "test", "--target", str(self.target)])
        self.assertEqual(code, 1, output.getvalue())
        self.assertIn("Project policy", output.getvalue())

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper is Windows-specific")
    def test_powershell_doctor_forwards_explicit_project_root(self):
        self._bootstrap()
        canonical = self.target / ".test-kit/kit.yaml"
        canonical.parent.mkdir()
        canonical.write_bytes((self.source / "kits/test/kit.yaml").read_bytes())
        script = Path(__file__).resolve().parents[1] / "doctor.ps1"
        result = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(script), "test", "--target", str(self.target), "--project-root", str(self.project)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PROJECT_POLICY_VALID", result.stdout)


if __name__ == "__main__":
    unittest.main()
