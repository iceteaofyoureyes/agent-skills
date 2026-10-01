import json
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.lib import dev_kit


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tooling/tests/fixtures/dev"


def _start_normal_run(project, signals=()):
    project = Path(project)
    project.mkdir(parents=True, exist_ok=True)
    sources = {name: f"approved {name}" for name in ("rules.md", "srs.md", "decisions.md")}
    for name, content in sources.items():
        (project / name).write_text(content, encoding="utf-8")
    digest = lambda name: hashlib.sha256(sources[name].encode()).hexdigest()
    baseline = project / "engineering-handoff.yml"
    baseline.write_text(
        "schema_version: 1\nfeature:\n  id: CR-001\n  title: Example\n"
        "ba_baseline:\n  status: APPROVED_FOR_ENGINEERING\n  revision: ba-rev-test\n"
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
    checks = [
        {"name": "build", "category": "build", "argv": [sys.executable, "-c", "pass"]},
        {"name": "tests", "category": "tests", "argv": [sys.executable, "-c", "pass"]},
    ]
    started = dev_kit.start_run(project, "CHANGE-TEST", "feature", "Add an ordinary feature", signals, baseline, checks)
    run_dir = Path(started["run_dir"])
    dev_kit.write_artifact(run_dir / "spec-readiness.json", {"status": "READY_FOR_PLANNING", "business_ambiguities": []})
    dev_kit.preflight(project)
    return project, run_dir, dev_kit._read_json(run_dir / "input.json")


def _planning_text(inputs, variant="valid"):
    metadata = {
        "change_id": inputs["change_id"],
        "baseline_ref": dict(inputs["baseline_ref"]),
        "business_ambiguity": "CLEAR",
    }
    if variant == "wrong_change":
        metadata["change_id"] = "OTHER-CHANGE"
    elif variant == "wrong_baseline":
        metadata["baseline_ref"]["sha256"] = "0" * 64
    return "<!-- devkit-planning-metadata\n" + json.dumps(metadata) + "\n-->\n\n# Plan\n"


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

    def test_sol_02_handoff_retains_all_build_verification_results(self):
        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "project")
            lifecycle = dev_kit._read_json(run_dir / "lifecycle.json")
            lifecycle["readiness"] = "READY_FOR_PLANNING"
            lifecycle["review_budget"]["full_reviews"] = 1
            lifecycle["review"] = {"blocking_findings": [], "followups": []}
            lifecycle["verification"] = [
                {"name": "build-1", "category": "build", "status": "PASS", "command": ["build-1"], "exit_code": 0},
                {"name": "build-2", "category": "build", "status": "FAIL", "command": ["build-2"], "exit_code": 1},
                {"name": "tests", "category": "tests", "status": "PASS", "command": ["tests"], "exit_code": 0},
            ]
            dev_kit._save_lifecycle(project, run_dir, inputs, lifecycle)
            handoff = dev_kit.prepare_handoff(project)
            self.assertEqual([item["name"] for item in handoff["verification"]["build"]], ["build-1", "build-2"])
            self.assertEqual(handoff["verification"]["build"][1]["status"], "FAIL")
            handoff["implementation"]["changed_components"] = ["appointments"]
            handoff["requirements_coverage"] = [{"requirement_id": "FR-001", "status": "COVERED", "evidence": ["tests"]}]
            self.assertNotEqual(dev_kit._derive_handoff_state(handoff), "READY_FOR_TEST")
            handoff["verification"]["build"][1].update(status="PASS", exit_code=0)
            self.assertEqual(dev_kit._derive_handoff_state(handoff), "READY_FOR_TEST")

    def test_invalid_handoff_cannot_persist_a_derived_ready_state(self):
        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "project")
            lifecycle = dev_kit._read_json(run_dir / "lifecycle.json")
            lifecycle["readiness"] = "READY_FOR_PLANNING"
            lifecycle["review_budget"]["full_reviews"] = 1
            lifecycle["review"] = {"blocking_findings": [], "followups": []}
            lifecycle["verification"] = [
                {"name": "build", "category": "build", "status": "PASS", "command": ["build"], "exit_code": 0},
                {"name": "tests", "category": "tests", "status": "PASS", "command": ["tests"], "exit_code": 0},
            ]
            dev_kit._save_lifecycle(project, run_dir, inputs, lifecycle)
            handoff = dev_kit.prepare_handoff(project)
            handoff["requirements_coverage"] = [{"requirement_id": "FR-001", "status": "COVERED", "evidence": ["tests"]}]
            handoff["implementation"]["changed_components"] = []
            self.assertEqual(dev_kit._derive_handoff_state(handoff), "READY_FOR_TEST")
            dev_kit.write_artifact(run_dir / "dev-handoff.json", handoff)
            with self.assertRaisesRegex(ValueError, "changed component ownership"):
                dev_kit.finalize_handoff(project)
            persisted = dev_kit._read_json(run_dir / "dev-handoff.json")
            self.assertNotEqual(persisted["state"], "READY_FOR_TEST")

    def test_sol_03_impact_can_escalate_normal_but_cannot_downgrade_high_risk(self):
        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "normal")
            impact_path = run_dir / "impact-manifest.json"
            impact = dev_kit._read_json(impact_path)
            impact["affected_interfaces"] = ["public appointment API"]
            impact["risk"] = {"level": "HIGH_RISK", "reasons": ["public_api", "database_migration", "cross_repo"]}
            dev_kit.write_artifact(impact_path, impact)
            result = dev_kit.preflight(project)
            self.assertEqual(result["status"], "HIGH_RISK_REENTRY_REQUIRED")
            self.assertFalse(result["planning_allowed"])
            impact["risk"] = {"level": "NORMAL", "reasons": []}
            dev_kit.write_artifact(impact_path, impact)
            self.assertEqual(dev_kit.preflight(project)["status"], "HIGH_RISK_REENTRY_REQUIRED")
            with self.assertRaisesRegex(ValueError, "HIGH_RISK"):
                dev_kit.assert_implementation_allowed(project, "normal")
            lifecycle = dev_kit._read_json(run_dir / "lifecycle.json")
            self.assertEqual(lifecycle["status"], "HIGH_RISK_REENTRY_REQUIRED")
            self.assertFalse(lifecycle["human_gate"]["required"])

        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, _ = _start_normal_run(Path(temp) / "high", signals=("public_api",))
            impact_path = run_dir / "impact-manifest.json"
            impact = dev_kit._read_json(impact_path)
            impact["risk"] = {"level": "NORMAL", "reasons": []}
            dev_kit.write_artifact(impact_path, impact)
            with self.assertRaisesRegex(ValueError, "cannot downgrade"):
                dev_kit.preflight(project)
            lifecycle = dev_kit._read_json(run_dir / "lifecycle.json")
            self.assertTrue(lifecycle["human_gate"]["required"])

    def test_sol_04_planning_artifacts_are_required_and_bound_before_implementation(self):
        cases = (
            ("missing plan", None, "valid"),
            ("missing tasks", "valid", None),
            ("empty plan", "", "valid"),
            ("empty tasks", "valid", "  \n"),
            ("wrong change", "wrong_change", "valid"),
            ("wrong baseline", "wrong_baseline", "valid"),
        )
        for label, plan_case, tasks_case in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                project, run_dir, inputs = _start_normal_run(Path(temp) / "project")
                if plan_case is not None:
                    plan_text = "  \n" if plan_case == "" else _planning_text(inputs, plan_case)
                    (run_dir / "dev-plan.md").write_text(plan_text, encoding="utf-8")
                if tasks_case is not None:
                    tasks_text = "  \n" if tasks_case == "  \n" else _planning_text(inputs, tasks_case)
                    (run_dir / "dev-tasks.md").write_text(tasks_text, encoding="utf-8")
                with self.assertRaises(ValueError):
                    dev_kit.validate_planning_artifacts(project)
                with self.assertRaises(ValueError):
                    dev_kit.assert_implementation_allowed(project, "normal")

        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "project")
            for name in ("dev-plan.md", "dev-tasks.md"):
                (run_dir / name).write_text(_planning_text(inputs, "valid"), encoding="utf-8")
            result = dev_kit.validate_planning_artifacts(project)
            self.assertTrue(result["planning_allowed"])
            self.assertTrue(dev_kit.assert_implementation_allowed(project, "normal")["implementation_allowed"])

        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "project")
            impact = dev_kit._read_json(run_dir / "impact-manifest.json")
            impact["unknowns"] = [{"id": "BUS-1", "kind": "BUSINESS", "description": "Refund policy is undecided", "blocking": True}]
            dev_kit.write_artifact(run_dir / "impact-manifest.json", impact)
            for name in ("dev-plan.md", "dev-tasks.md"):
                (run_dir / name).write_text(_planning_text(inputs), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "business-semantic"):
                dev_kit.validate_planning_artifacts(project)

        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "project")
            for name in ("dev-plan.md", "dev-tasks.md"):
                (run_dir / name).write_text(_planning_text(inputs), encoding="utf-8")
            dev_kit.validate_planning_artifacts(project)
            impact = dev_kit._read_json(run_dir / "impact-manifest.json")
            impact["unknowns"] = [{"id": "BUS-2", "kind": "BUSINESS", "description": "Refund policy is undecided", "blocking": True}]
            dev_kit.write_artifact(run_dir / "impact-manifest.json", impact)
            with self.assertRaisesRegex(ValueError, "business-semantic"):
                dev_kit.assert_implementation_allowed(project, "normal")

    def test_sol_f01_high_risk_implementation_needs_spec_kit_gate_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            project, run_dir, inputs = _start_normal_run(Path(temp) / "project", signals=("public_api",))
            for name in ("dev-plan.md", "dev-tasks.md"):
                (run_dir / name).write_text(_planning_text(inputs), encoding="utf-8")
            dev_kit.validate_planning_artifacts(project)
            with self.assertRaisesRegex(ValueError, "gate"):
                dev_kit.assert_implementation_allowed(project, "high-risk")
            with self.assertRaisesRegex(ValueError, "approve"):
                dev_kit.mark_gate_approved(project, "reject", "RUN-001")
            workflow_run_id = "RUN-001"
            workflow_state_path = project / ".specify/workflows/runs/RUN-001/state.json"
            workflow_state_path.parent.mkdir(parents=True)
            state = {
                "run_id": workflow_run_id,
                "step_results": {"human-tech-lead-plan-gate": {"status": "completed", "output": {"choice": "reject"}}},
            }
            workflow_state_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "persisted gate evidence"):
                dev_kit.mark_gate_approved(project, "approve", workflow_run_id)
            state["step_results"]["human-tech-lead-plan-gate"]["output"]["choice"] = "approve"
            workflow_state_path.write_text(json.dumps(state), encoding="utf-8")
            approval = dev_kit.mark_gate_approved(project, "approve", workflow_run_id)
            self.assertEqual(approval["choice"], "approve")
            self.assertEqual(approval["workflow_run_id"], workflow_run_id)
            self.assertEqual(approval["workflow_state_path"], ".specify/workflows/runs/RUN-001/state.json")
            self.assertTrue(dev_kit.assert_implementation_allowed(project, "high-risk")["implementation_allowed"])
            (run_dir / "dev-plan.md").write_text(_planning_text(inputs) + "Changed after approval.\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "validated artifacts"):
                dev_kit.assert_implementation_allowed(project, "high-risk")

        handoff = json.loads((FIXTURES / "dev-handoff.valid.json").read_text(encoding="utf-8"))
        handoff["human_gate"] = {"required": True, "resolved": True, "choice": "approve"}
        self.assertNotEqual(dev_kit._derive_handoff_state(handoff), "READY_FOR_TEST")

    def test_sol_01_installed_runtime_operates_from_external_project(self):
        from tooling import install_dev_kit

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "external-project"
            install_home = root / "developer-home"
            target.mkdir()
            installed = install_dev_kit.install(ROOT, install_home)
            runtime_root = Path(installed["runtime_root"]).resolve()
            self.assertNotEqual(os.path.commonpath((str(runtime_root), str(target.resolve()))), str(target.resolve()))
            self.assertFalse((target / "tooling/lib/dev_kit.py").exists())
            self.assertFalse((runtime_root / "kits/dev/plugin/skills").exists())
            manifest = json.loads(Path(installed["manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["files"]), installed["file_count"])
            for relative, digest in manifest["files"].items():
                self.assertEqual(hashlib.sha256((runtime_root / relative).read_bytes()).hexdigest(), digest)

            args = [
                "start", "--change-id", "EXT-001", "--kind", "docs", "--summary", "External README edit",
                "--check", json.dumps({"name": "docs", "category": "static_checks", "argv": [sys.executable, "-c", "pass"]}),
            ]
            command = [sys.executable, str(runtime_root / "tooling/lib/dev_kit.py"), *args]
            completed = subprocess.run(command, cwd=target, text=True, capture_output=True, check=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            state = json.loads((target / ".devkit/current.json").read_text(encoding="utf-8"))
            self.assertEqual(state["change_id"], "EXT-001")
            self.assertTrue((target / ".devkit/runs/EXT-001/input.json").is_file())
            self.assertTrue((target / ".devkit/runs/EXT-001/lifecycle.json").is_file())
            runtime = subprocess.run(
                ["powershell", "-NoProfile", "-File", installed["launcher"], "runtime-root"] if os.name == "nt"
                else [installed["launcher"], "runtime-root"],
                cwd=target, text=True, capture_output=True, check=False,
            )
            self.assertEqual(runtime.returncode, 0, runtime.stderr)
            self.assertEqual(Path(runtime.stdout.strip()).resolve(), runtime_root)
            schema = subprocess.run(
                ["powershell", "-NoProfile", "-File", installed["launcher"], "schema", "impact-manifest"] if os.name == "nt"
                else [installed["launcher"], "schema", "impact-manifest"],
                cwd=target, text=True, capture_output=True, check=False,
            )
            self.assertEqual(schema.returncode, 0, schema.stderr)
            self.assertIn("affected_components", json.loads(schema.stdout)["required"])
            workflow = subprocess.run(
                ["powershell", "-NoProfile", "-File", installed["launcher"], "workflow", "normal"] if os.name == "nt"
                else [installed["launcher"], "workflow", "normal"],
                cwd=target, text=True, capture_output=True, check=False,
            )
            self.assertEqual(workflow.returncode, 0, workflow.stderr)
            self.assertTrue(Path(workflow.stdout.strip()).is_file())

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
        for workflow in (normal, high):
            self.assertIn("{{ inputs.devkit_command }}", workflow)
            self.assertNotIn("tooling/lib/dev_kit.py", workflow)
            self.assertIn("id: enforce-planning-artifacts", workflow)
        self.assertLess(normal.index("id: enforce-planning-artifacts"), normal.index("id: implementation"))
        self.assertLess(high.index("id: enforce-planning-artifacts"), high.index("id: human-tech-lead-plan-gate"))
        self.assertLess(high.index("id: authorize-high-risk-implementation"), high.index("id: implementation"))
        self.assertIn("steps.human-tech-lead-plan-gate.output.choice", high)

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
        approved = json.loads(json.dumps(valid))
        approved["human_gate"] = {
            "required": True, "resolved": True, "choice": "approve", "workflow_run_id": "RUN-001",
            "workflow_state_path": ".specify/workflows/runs/RUN-001/state.json",
            "planning_artifacts_sha256": {"dev-plan.md": "a" * 64, "dev-tasks.md": "b" * 64},
        }
        self.assertEqual(dev_kit.validate_dev_handoff(approved), [])
        del approved["human_gate"]["workflow_state_path"]
        self.assertTrue(any("workflow evidence" in error for error in dev_kit.validate_dev_handoff(approved)))
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
        self.assertFalse(handoff_schema["$defs"]["namedCheck"]["additionalProperties"])
        self.assertEqual(handoff_schema["properties"]["verification"]["properties"]["build"]["type"], "array")
        self.assertEqual(ready["implementation"]["properties"]["changed_components"]["minItems"], 1)
        self.assertEqual(ready["requirements_coverage"]["items"]["properties"]["evidence"]["minItems"], 1)

    def test_provenance_matches_frozen_component_hashes(self):
        errors = dev_kit.validate_provenance(ROOT)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
