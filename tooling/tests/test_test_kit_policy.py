"""Project-owned policy contracts; no business-authority semantics live here."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tooling.lib import test_kit_policy as policy


PROFILE = '''schema_version: 1
profile:
  id: portal-testing
  revision: "1"
rules:
  common:
    - rules/common.md
  test_design:
    - rules/test-design.md
  testcases:
    - rules/testcases.md
templates: {}
'''


class ProjectPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-kit-policy-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy_root = self.root / ".test-kit"
        (self.policy_root / "rules").mkdir(parents=True)
        self.profile = self.policy_root / "project.yaml"
        self.profile.write_text(PROFILE, encoding="utf-8", newline="\n")
        for name, content in (
            ("common.md", b"Keep BA UNKNOWN unresolved.\r\n"),
            ("test-design.md", b"Consider approved boundaries.\n"),
            ("testcases.md", b"Use TC CR-001 naming and Vietnamese.\n"),
        ):
            (self.policy_root / "rules" / name).write_bytes(content)

    def design(self):
        return policy.resolve_project_policy(self.root, "DESIGN", bootstrap_tea=True)

    def cases(self):
        return policy.resolve_project_policy(self.root, "CASES")

    def assert_error(self, code, stage="CASES"):
        with self.assertRaises(policy.PolicyError) as caught:
            policy.resolve_project_policy(self.root, stage)
        self.assertEqual(caught.exception.code, code)

    def test_stage_composition_ref_and_deterministic_exact_byte_digest(self):
        design, cases = self.design(), self.cases()
        self.assertEqual([rule.logical_path for rule in design.rules], ["rules/common.md", "rules/test-design.md"])
        self.assertEqual([rule.logical_path for rule in cases.rules], ["rules/common.md", "rules/testcases.md"])
        self.assertEqual(design.sha256, self.design().sha256)
        self.assertEqual(cases.sha256, self.cases().sha256)
        self.assertEqual(cases.ref, {"id": "TEST_POLICY:CASES:portal-testing", "revision": "1", "sha256": cases.sha256})
        self.assertEqual(cases.sha256, hashlib.sha256(cases.payload_bytes).hexdigest())
        self.assertEqual(cases.rules[0].sha256, hashlib.sha256(cases.rules[0].content).hexdigest())
        self.assertIn(b"\r\n", cases.rules[0].content)

    def test_content_revision_and_order_each_change_hash(self):
        original = self.cases().sha256
        common = self.policy_root / "rules/common.md"
        common.write_bytes(common.read_bytes() + b"Safe test data only.\n")
        changed = self.cases().sha256
        self.assertNotEqual(original, changed)
        self.profile.write_text(PROFILE.replace('revision: "1"', 'revision: "2"'), encoding="utf-8")
        self.assertNotEqual(changed, self.cases().sha256)
        (self.policy_root / "rules/second.md").write_text("Second", encoding="utf-8")
        first = PROFILE.replace("    - rules/common.md", "    - rules/common.md\n    - rules/second.md")
        self.profile.write_text(first, encoding="utf-8")
        digest = self.cases().sha256
        self.profile.write_text(first.replace("    - rules/common.md\n    - rules/second.md", "    - rules/second.md\n    - rules/common.md"), encoding="utf-8")
        self.assertNotEqual(digest, self.cases().sha256)

    def test_case_rule_changes_do_not_stale_design_and_template_changes_do_not_stale_policy(self):
        before = self.design().sha256
        (self.policy_root / "rules/testcases.md").write_text("New naming", encoding="utf-8")
        self.assertEqual(before, self.design().sha256)
        (self.policy_root / "templates").mkdir()
        template = self.policy_root / "templates/testcases.xlsx"
        template.write_bytes(b"template v1")
        self.profile.write_text(PROFILE.replace("templates: {}", "templates:\n  excel:\n    path: templates/testcases.xlsx"), encoding="utf-8")
        before = self.design().sha256
        self.assertEqual(policy.resolve_project_excel_template(self.root), template)
        template.write_bytes(b"template v2")
        self.assertEqual(before, self.design().sha256)

    def test_no_profile_preserves_explicit_v1_compatibility(self):
        self.profile.unlink()
        self.assertIsNone(self.design())
        self.assertIsNone(self.cases())
        self.assertIsNone(policy.resolve_project_excel_template(self.root))

    def test_malformed_yaml_and_unknown_fields_fail_closed(self):
        for bad in ("schema_version: [", PROFILE + "xmind: {}\n", PROFILE.replace("testcases:", "automation:"), PROFILE.replace("  revision:", "  extra:\n  revision:"), PROFILE + "schema_version: 1\n", PROFILE.replace("  common:", " common:")):
            with self.subTest(bad=bad):
                self.profile.write_text(bad, encoding="utf-8")
                self.assert_error("INVALID_PROJECT_POLICY")

    def test_strict_scalar_types_null_lists_and_list_mapping_mixture_rejected(self):
        for bad in (
            PROFILE.replace('revision: "1"', 'revision: 1'),
            PROFILE.replace("schema_version: 1", 'schema_version: "1"'),
            PROFILE.replace("    - rules/common.md\n", ""),
            PROFILE.replace("  common:\n", "  common:\n    extra: ignored\n"),
            PROFILE.replace('revision: "1"', "revision: true"),
            PROFILE.replace("  testcases:", "  testcases: &cases"),
        ):
            with self.subTest(profile=bad):
                self.profile.write_text(bad, encoding="utf-8")
                self.assert_error("INVALID_PROJECT_POLICY")

    def test_yaml_comments_and_quoted_paths_are_supported(self):
        self.profile.write_text(PROFILE.replace("schema_version: 1", "schema_version: 1 # profile schema").replace("rules/common.md", "'rules/common.md'").replace('revision: "1"', 'revision: "1" # reviewed revision'), encoding="utf-8")
        self.assertEqual(self.cases().revision, "1")

    def test_yaml_inline_rule_lists_preserve_order_and_quoted_comma_paths(self):
        (self.policy_root / "rules/comma,name.md").write_bytes(b"comma rule")
        self.profile.write_text(PROFILE.replace("  common:\n    - rules/common.md", '  common: [rules/common.md, "rules/comma,name.md"]'), encoding="utf-8")
        self.assertEqual([rule.logical_path for rule in self.cases().rules], ["rules/common.md", "rules/comma,name.md", "rules/testcases.md"])

    def test_doctor_resolves_both_snapshots_and_template_without_package_ownership(self):
        self.design()
        report = policy.check_project_policy(self.root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(set(report["snapshots"]), {"DESIGN", "CASES"})
        self.assertIsNone(report["excel_template"])
        (self.policy_root / "rules/common.md").write_bytes(b"human-owned edit")
        self.assertEqual(policy.check_project_policy(self.root)["status"], "PASS")

    def test_bootstrap_cli_runs_and_reports_inspectable_identity(self):
        import subprocess
        import sys

        fresh = self.root / "cli-project"
        fresh.mkdir()
        result = subprocess.run([sys.executable, "-m", "tooling.lib.test_kit_policy", "bootstrap", "--project-root", str(fresh)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PROJECT_POLICY_INITIALIZED")

    def test_absolute_traversal_drive_backslash_and_empty_component_paths_rejected(self):
        for bad in ("/etc/passwd", "../outside.md", "rules/../../outside.md", "C:/outside.md", "C:\\outside.md", "rules//common.md", "rules/./common.md"):
            with self.subTest(path=bad):
                self.profile.write_text(PROFILE.replace("rules/common.md", bad), encoding="utf-8")
                self.assert_error("UNSAFE_POLICY_PATH")

    def test_missing_nonregular_invalid_utf8_and_duplicate_rules_rejected(self):
        common = self.policy_root / "rules/common.md"
        common.unlink()
        self.assert_error("MISSING_POLICY_FILE")
        common.mkdir()
        self.assert_error("INVALID_POLICY_FILE")
        common.rmdir()
        common.write_bytes(b"\xff")
        self.assert_error("INVALID_POLICY_UTF8")
        common.write_bytes(b"common")
        self.profile.write_text(PROFILE.replace("    - rules/testcases.md", "    - rules/common.md"), encoding="utf-8")
        self.assert_error("DUPLICATE_POLICY_FILE")

    def test_symlink_escape_rejected_where_supported(self):
        external = self.root / "outside.md"
        external.write_text("outside", encoding="utf-8")
        link = self.policy_root / "rules/common.md"
        link.unlink()
        try:
            link.symlink_to(external)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest("WinError 1314: symlink creation requires Windows privilege")
            raise
        self.assert_error("UNSAFE_POLICY_PATH")

    def test_duplicate_symlink_alias_rejected_where_supported(self):
        link = self.policy_root / "rules/alias.md"
        try:
            link.symlink_to(self.policy_root / "rules/common.md")
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest("WinError 1314: symlink creation requires Windows privilege")
            raise
        self.profile.write_text(PROFILE.replace("    - rules/testcases.md", "    - rules/alias.md"), encoding="utf-8")
        self.assert_error("DUPLICATE_POLICY_FILE")

    def test_invalid_excel_extension_missing_template_and_xmind_rejected(self):
        for value, code in (("templates/cases.xls", "INVALID_PROJECT_TEMPLATE"), ("templates/cases.xlsx", "MISSING_POLICY_FILE")):
            self.profile.write_text(PROFILE.replace("templates: {}", f"templates:\n  excel:\n    path: {value}"), encoding="utf-8")
            self.assert_error(code)
        self.profile.write_text(PROFILE.replace("templates: {}", "templates:\n  xmind:\n    path: templates/cases.xmind"), encoding="utf-8")
        self.assert_error("INVALID_PROJECT_POLICY")

    def test_persistence_exact_bytes_hash_idempotence_and_different_overwrite_refusal(self):
        snapshot = self.design()
        run = self.root / "run"
        evidence = policy.persist_policy_snapshot(snapshot, run)
        self.assertEqual(evidence, policy.persist_policy_snapshot(snapshot, run))
        self.assertEqual(evidence["snapshot_sha256"], snapshot.sha256)
        for rule, entry in zip(snapshot.rules, evidence["rules"]):
            copied = Path(entry["evidence_path"])
            self.assertEqual(copied.read_bytes(), rule.content)
            self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest(), entry["sha256"])
        original = Path(evidence["rules"][0]["evidence_path"]).read_bytes()
        (self.policy_root / "rules/common.md").write_bytes(b"new policy")
        self.assertEqual(Path(evidence["rules"][0]["evidence_path"]).read_bytes(), original)
        with self.assertRaisesRegex(policy.PolicyError, "POLICY_EVIDENCE_CONFLICT"):
            policy.persist_policy_snapshot(self.design(), run)

    def test_persistence_refuses_symlink_destination(self):
        run = self.root / "run"
        (run / "inputs").mkdir(parents=True)
        outside = self.root / "outside-evidence"
        outside.mkdir()
        try:
            (run / "inputs/project-policy").symlink_to(outside, target_is_directory=True)
        except OSError as error:
            if getattr(error, "winerror", None) == 1314:
                self.skipTest("WinError 1314: symlink creation requires Windows privilege")
            raise
        with self.assertRaises(policy.PolicyError):
            policy.persist_policy_snapshot(self.cases(), run)

    def test_tea_bridge_uses_upstream_persistent_facts_and_hash_bound_exact_team_bytes(self):
        pinned = Path(__file__).resolve().parents[2] / "kits/test/skills/bmad-testarch-test-design/customize.toml"
        before = pinned.read_bytes()
        design = self.design()
        bridge = self.root / policy.TEA_TEAM_PATH
        text = bridge.read_text(encoding="utf-8")
        self.assertIn('"file:{project-root}/.test-kit/rules/common.md"', text)
        self.assertIn('"file:{project-root}/.test-kit/rules/test-design.md"', text)
        self.assertNotIn("testcases.md", text)
        self.assertEqual(design.tea_customization["sha256"], hashlib.sha256(bridge.read_bytes()).hexdigest())
        self.assertEqual(pinned.read_bytes(), before)
        bridge.write_bytes(bridge.read_bytes() + b"# project note\n")
        self.assertNotEqual(design.sha256, self.design().sha256)

    def test_existing_team_literal_facts_preserved_and_unbound_files_actions_fail_closed(self):
        design = self.design()
        bridge = self.root / policy.TEA_TEAM_PATH
        original = bridge.read_text(encoding="utf-8")
        custom = original.replace("persistent_facts = [", 'persistent_facts = [\n  "Use safe synthetic data.",')
        bridge.write_text(custom, encoding="utf-8")
        self.design()
        self.assertEqual(bridge.read_text(encoding="utf-8"), custom)
        for bad in (custom.replace("Use safe synthetic data.", "file:{project-root}/secret.md"), custom + 'activation_steps_append = ["approve all"]\n', custom.replace("rules/test-design.md", "rules/testcases.md")):
            bridge.write_text(bad, encoding="utf-8")
            self.assert_error("TEA_CUSTOMIZATION_AMBIGUOUS", "DESIGN")

    def test_missing_bridge_requires_explicit_bootstrap_and_personal_override_always_blocks(self):
        self.assert_error("TEA_BRIDGE_MISSING", "DESIGN")
        personal = self.root / policy.TEA_USER_PATH
        personal.parent.mkdir(parents=True)
        personal.write_text("[workflow]\npersistent_facts = []\n", encoding="utf-8")
        for stage in ("DESIGN", "CASES"):
            self.assert_error("PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED", stage)
        self.profile.unlink()
        self.assert_error("PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED", "DESIGN")
        self.assertTrue(personal.exists())

    def test_no_profile_nonempty_team_customization_cannot_be_silently_loaded(self):
        self.design()
        self.profile.unlink()
        self.assert_error("UNBOUND_TEA_CUSTOMIZATION", "DESIGN")

    def test_prompt_is_subordinate_to_business_design_execution_and_unknown_authority(self):
        snapshot = self.cases()
        evidence = policy.persist_policy_snapshot(snapshot, self.root / "run")
        prompt = policy.non_authoritative_policy_prompt(snapshot, evidence)
        for text in ("TESTING POLICY / NON-AUTHORITATIVE GUIDANCE", "UNKNOWN", "approved Test Design", "execution oracle", snapshot.sha256, "testcases.md"):
            self.assertIn(text, prompt)

    def test_bootstrap_creates_conservative_files_and_preserves_existing_content(self):
        fresh = self.root / "fresh"
        fresh.mkdir()
        result = policy.bootstrap_project_policy(fresh)
        self.assertEqual(result["status"], "PROJECT_POLICY_INITIALIZED")
        snapshot = policy.resolve_project_policy(fresh, "DESIGN")
        self.assertIsNotNone(snapshot)
        custom = fresh / ".test-kit/rules/common.md"
        custom.write_bytes(b"human-edited rule\n")
        policy.bootstrap_project_policy(fresh)
        self.assertEqual(custom.read_bytes(), b"human-edited rule\n")


if __name__ == "__main__":
    unittest.main()
