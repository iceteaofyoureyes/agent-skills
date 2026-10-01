import json
import hashlib
import re
import tempfile
import unittest
from pathlib import Path

from tooling.lib import dev_kit


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tooling/tests/fixtures/dev"


class DevKitTests(unittest.TestCase):
    def test_dev_struct_01_normal_uses_lean_path(self):
        route = dev_kit.route_change("feature", "Add a local search filter")
        self.assertEqual(route["risk_level"], "NORMAL")
        self.assertEqual(route["status"], "READY_FOR_PLANNING")
        self.assertEqual(route["stages"].count("ONE_CONSOLIDATED_REVIEW"), 1)
        self.assertNotIn("codebase-memory-mcp", route["capabilities"])
        self.assertNotIn("security-and-hardening", route["capabilities"])

    def test_dev_struct_02_trivial_skips_planning_and_review(self):
        route = dev_kit.route_change("docs", "Fix a README typo")
        self.assertEqual(route["risk_level"], "TRIVIAL")
        self.assertEqual(route["stages"], ["UNDERSTAND", "EDIT", "DETERMINISTIC_CHECK", "COMPLETE"])
        self.assertFalse(route["formal_plan"])
        self.assertFalse(route["full_review"])
        self.assertEqual(dev_kit.route_change("config", "Change the active timeout", behavior_change=True)["risk_level"], "NORMAL")

    def test_dev_struct_03_auth_security_routes_high_risk(self):
        route = dev_kit.route_change("feature", "Protect the auth endpoint", ["auth"])
        self.assertEqual(route["risk_level"], "HIGH_RISK")
        self.assertIn("security-and-hardening", route["capabilities"])
        self.assertTrue(route["human_gate_required"])

    def test_dev_struct_04_business_ambiguity_blocks_planning(self):
        route = dev_kit.route_change("feature", "Add a cancellation flow", business_ambiguities=["refund timing is undecided"])
        self.assertEqual(route["status"], "NEEDS_BA_CLARIFICATION")
        self.assertFalse(route["planning_allowed"])

    def test_dev_struct_05_review_budget_is_capped_at_one(self):
        budget = {"full_reviews": 0, "blocking_fix_waves": 0, "scoped_rereviews": 0}
        for action in ("full_reviews", "blocking_fix_waves", "scoped_rereviews"):
            budget = dev_kit.claim_review_action(budget, action)
            with self.assertRaises(ValueError):
                dev_kit.claim_review_action(budget, action)

    def test_dev_struct_06_failed_verification_cannot_be_ready(self):
        handoff = json.loads((FIXTURES / "dev-handoff.valid.json").read_text(encoding="utf-8"))
        handoff["verification"]["tests"][0]["exit_code"] = 1
        self.assertTrue(any("verification" in error.lower() for error in dev_kit.validate_dev_handoff(handoff)))
        self.assertEqual(dev_kit._derive_handoff_state(handoff), "NEEDS_REPLAN")
        handoff["verification"]["tests"] = []
        self.assertEqual(dev_kit._derive_handoff_state(handoff), "NEEDS_REPLAN")

    def test_dev_struct_07_artifacts_cannot_overwrite_baseline(self):
        with tempfile.TemporaryDirectory() as temp:
            baseline = Path(temp) / "approved-ba-baseline.md"
            baseline.write_text("approved", encoding="utf-8")
            snapshot = dev_kit.hash_baseline(baseline)
            with self.assertRaises(ValueError):
                dev_kit.write_artifact(baseline, {"mutated": True}, [snapshot])
            self.assertEqual(baseline.read_text(encoding="utf-8"), "approved")

    def test_dev_struct_08_relevant_global_methodology_fails_benchmark(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            home = Path(temp) / "home"
            skill = home / ".agents/skills/test-driven-development"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: test-driven-development\ndescription: TDD\n---\n", encoding="utf-8")
            report = dev_kit.inspect_context_purity(project, home, mode="benchmark")
            self.assertEqual(report["context_purity"], "DEGRADED")
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(any(item["relevant"] for item in report["contamination"]))

    def test_daily_doctor_degrades_for_unrelated_context_contamination(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            home = Path(temp) / "home"
            plugin = project / ".codex/plugins/formatter"
            plugin.mkdir(parents=True)
            (plugin / "plugin.json").write_text('{"name":"formatter"}', encoding="utf-8")
            report = dev_kit.inspect_context_purity(project, home, mode="daily")
            self.assertEqual(report["context_purity"], "DEGRADED")
            self.assertEqual(report["status"], "DEGRADED")

    def test_doctor_pins_the_frozen_core_and_conditional_skill_split(self):
        core = ["planning-and-task-breakdown", "incremental-implementation", "test-driven-development", "code-review-and-quality"]
        conditional = ["debugging-and-error-recovery", "security-and-hardening", "api-and-interface-design", "source-driven-development", "performance-optimization", "observability-and-instrumentation"]
        self.assertTrue(dev_kit._composition_matches(core, conditional))
        self.assertFalse(dev_kit._composition_matches(core + [conditional[1]], [skill for skill in conditional if skill != conditional[1]]))
        self.assertFalse(dev_kit._composition_matches("planning-and-task-breakdown", conditional))

    def test_benchmark_mode_warns_for_unrelated_but_only_fails_relevant_contamination(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            home = Path(temp) / "home"
            plugin = project / ".codex/plugins/formatter"
            plugin.mkdir(parents=True)
            (plugin / "plugin.json").write_text('{"name":"formatter"}', encoding="utf-8")
            report = dev_kit.inspect_context_purity(project, home, mode="benchmark")
            self.assertEqual(report["context_purity"], "DEGRADED")
            self.assertEqual(report["status"], "DEGRADED")

    def test_start_and_preflight_keep_approved_baseline_immutable_and_resume_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            sources = {
                "rules.md": "approved rules",
                "srs.md": "approved SRS",
                "decisions.md": "approved decisions",
            }
            for name, content in sources.items():
                (project / name).write_text(content, encoding="utf-8")
            digest = lambda name: hashlib.sha256(sources[name].encode()).hexdigest()
            baseline = project / "engineering-handoff.yml"
            baseline.write_text(
                "schema_version: 1\n"
                "feature:\n  id: CR-001\n  title: Example\n"
                "ba_baseline:\n  status: APPROVED_FOR_ENGINEERING\n  revision: ba-rev-7\n"
                "authoritative_sources:\n"
                f"  business_rules:\n    path: rules.md\n    sha256: {digest('rules.md')}\n"
                f"  srs:\n    path: srs.md\n    sha256: {digest('srs.md')}\n"
                f"  decisions:\n    path: decisions.md\n    sha256: {digest('decisions.md')}\n"
                "open_items:\n  blocking: []\n  non_blocking: []\n"
                "policy:\n  downstream_may_change_business_semantics: false\n"
                "  downstream_may_make_technical_design_decisions: true\n"
                "next_stage:\n  capability: engineering-impact-analysis\n",
                encoding="utf-8",
            )
            before = baseline.read_bytes()
            checks = [
                {"name": "build", "category": "build", "argv": ["python", "-c", "pass"]},
                {"name": "unit", "category": "tests", "argv": ["python", "-c", "pass"]},
            ]
            started = dev_kit.start_run(project, "CHANGE-001", "feature", "Add appointment search", baseline=baseline, checks=checks)
            run_dir = Path(started["run_dir"])
            self.assertEqual(dev_kit.assert_workflow(project, "normal")["risk_level"], "NORMAL")
            with self.assertRaises(ValueError):
                dev_kit.assert_workflow(project, "trivial")
            dev_kit.write_artifact(run_dir / "spec-readiness.json", {"status": "READY_FOR_PLANNING", "business_ambiguities": []})
            self.assertEqual(dev_kit.preflight(project)["status"], "READY_FOR_PLANNING")
            self.assertEqual(baseline.read_bytes(), before)
            with self.assertRaises(ValueError):
                dev_kit.write_artifact(baseline, {"status": "unapproved"}, [dev_kit.hash_baseline(baseline)])
            self.assertEqual(baseline.read_bytes(), before)
            impact_path = run_dir / "impact-manifest.json"
            impact = json.loads(impact_path.read_text(encoding="utf-8"))
            impact["unknowns"] = [{"id": "BUS-001", "kind": "BUSINESS", "description": "Cancellation penalty is unknown", "blocking": True}]
            dev_kit.write_artifact(impact_path, impact)
            self.assertEqual(dev_kit.preflight(project)["status"], "NEEDS_BA_CLARIFICATION")

    def test_workflows_use_bounded_spec_kit_primitives_without_spec_commands(self):
        workflow_root = ROOT / "kits/dev/plugin/workflows"
        self.assertFalse((workflow_root / "dev-trivial.workflow.yml").exists())
        trivial = dev_kit.route_change("docs", "Fix a typo")
        self.assertEqual(trivial["stages"], ["UNDERSTAND", "EDIT", "DETERMINISTIC_CHECK", "COMPLETE"])
        for filename in ("dev-normal.workflow.yml", "dev-high-risk.workflow.yml"):
            workflow = (workflow_root / filename).read_text(encoding="utf-8")
            self.assertIn('speckit_version: "==1.0.11"', workflow)
            for forbidden in ("speckit.specify", "speckit.plan", "speckit.tasks", "speckit.analyze", "speckit.converge"):
                self.assertNotIn(forbidden, workflow)
            self.assertEqual(workflow.count("id: consolidated-review"), 1)
            self.assertEqual(workflow.count("id: one-blocking-fix-wave"), 1)
            self.assertEqual(workflow.count("id: optional-scoped-rereview"), 1)
        normal = (workflow_root / "dev-normal.workflow.yml").read_text(encoding="utf-8")
        high = (workflow_root / "dev-high-risk.workflow.yml").read_text(encoding="utf-8")
        self.assertNotIn("type: gate", normal)
        self.assertEqual(high.count("type: gate"), 1)

    def test_installed_dev_plugin_does_not_contaminate_its_own_context(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project"
            home = Path(temp) / "home"
            plugin = project / ".codex/plugins/agent-skills-dev-kit"
            skill = plugin / "skills/test-driven-development"
            skill.mkdir(parents=True)
            (plugin / "plugin.json").write_text('{"name":"agent-skills-dev-kit"}', encoding="utf-8")
            (skill / "SKILL.md").write_text("---\nname: test-driven-development\ndescription: TDD\n---\n", encoding="utf-8")
            report = dev_kit.inspect_context_purity(project, home)
            self.assertEqual(report["context_purity"], "CLEAN")
            self.assertEqual(report["contamination"], [])

    def test_dev_document_internal_links_resolve(self):
        docs = list((ROOT / "docs/vi").glob("DEV_KIT_*.md")) + [
            ROOT / "kits/dev/README.md", ROOT / "docs/vi/ARCHITECTURE.md",
            ROOT / "docs/vi/KIT_CONTRACT.md", ROOT / "docs/vi/RELEASE.md",
            ROOT / "docs/vi/PROVENANCE.md", ROOT / "docs/vi/README.md",
        ]
        for document in docs:
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", document.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                path = target.split("#", 1)[0]
                if path:
                    self.assertTrue((document.parent / path).resolve().exists(), f"{document}: {target}")

    def test_impact_manifest_fixtures(self):
        valid = json.loads((FIXTURES / "impact-manifest.valid.json").read_text(encoding="utf-8"))
        invalid = json.loads((FIXTURES / "impact-manifest.invalid.json").read_text(encoding="utf-8"))
        self.assertEqual(dev_kit.validate_impact_manifest(valid), [])
        self.assertTrue(dev_kit.validate_impact_manifest(invalid))

    def test_handoff_fixtures_and_budget_guard(self):
        valid = json.loads((FIXTURES / "dev-handoff.valid.json").read_text(encoding="utf-8"))
        invalid = json.loads((FIXTURES / "dev-handoff.invalid.json").read_text(encoding="utf-8"))
        self.assertEqual(dev_kit.validate_dev_handoff(valid), [])
        self.assertTrue(dev_kit.validate_dev_handoff(invalid))
        valid["review"]["full_reviews"] = 2
        self.assertTrue(any("budget" in error.lower() for error in dev_kit.validate_dev_handoff(valid)))
        valid["review"]["full_reviews"] = 1
        valid["requirements_coverage"] = []
        self.assertTrue(any("coverage" in error.lower() for error in dev_kit.validate_dev_handoff(valid)))

    def test_json_schemas_match_fixture_contract_keys(self):
        impact_schema = json.loads((ROOT / "kits/dev/schemas/impact-manifest.schema.json").read_text(encoding="utf-8"))
        handoff_schema = json.loads((ROOT / "kits/dev/schemas/dev-handoff.schema.json").read_text(encoding="utf-8"))
        impact = json.loads((FIXTURES / "impact-manifest.valid.json").read_text(encoding="utf-8"))
        handoff = json.loads((FIXTURES / "dev-handoff.valid.json").read_text(encoding="utf-8"))
        self.assertEqual(set(impact_schema["required"]), set(impact))
        self.assertEqual(set(handoff_schema["required"]), set(handoff))
        ready = handoff_schema["allOf"][0]["then"]["properties"]
        self.assertFalse(handoff_schema["$defs"]["check"]["additionalProperties"])
        self.assertEqual(ready["implementation"]["properties"]["changed_components"]["minItems"], 1)
        self.assertEqual(ready["requirements_coverage"]["items"]["properties"]["evidence"]["minItems"], 1)

    def test_provenance_matches_frozen_component_hashes(self):
        errors = dev_kit.validate_provenance(ROOT)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
