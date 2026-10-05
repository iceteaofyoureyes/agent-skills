"""Synthetic multi-repository acceptance for Test Automation V1."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tooling.lib import test_automation_v1 as automation
from tooling.lib import test_kit_policy
from tooling.lib import test_kit_v1 as test_v1
from tooling.lib import test_kit_v1_cases as test_cases
from tooling.lib import test_kit_vnext as test_vnext
from tooling.tests import test_ba_vnext as ba_tests
from tooling.tests import test_dev_vnext as dev_tests


ROOT = Path(__file__).resolve().parents[2]
REVIEW_CHECKS = {
    "trace", "repository_ownership", "oracle_duplication", "fixtures", "secrets",
    "setup_cleanup", "flakiness", "selectors_interfaces", "dependencies",
    "project_conventions", "write_scope",
}


class TestAutomationV1Acceptance(unittest.TestCase):
    def setUp(self):
        self.ba = ba_tests.BAVNextTests("test_greenfield_exact_baseline_and_handoff")
        self.ba.setUp()
        self.addCleanup(self.ba.doCleanups)
        self.root = self.ba.root
        self.ba_state, self.ba_auth = self.ba.approved()
        self.ba_module = ba_tests.ba
        self.handoff = self.ba_module.make_handoff(
            self.ba_state, self.root, human_actor_authenticator=self.ba_auth,
        )
        self.handoff_path = self.root / "engineering-handoff-vnext.json"
        self._write_json(self.handoff_path, self.handoff)
        self._project_contracts()
        self.app_root = self.root / "app"
        self.automation_root = self.root / "automation"
        self.app_base = self._init_repository(self.app_root, "example/app", "application")
        self.automation_base = self._init_repository(self.automation_root, "example/qa", "automation")
        self._write_app_revision()
        self.human_gate_receipts = []
        self.human_test_auth = lambda actor, receipt: (
            test_v1.AuthenticatedHumanActorContext(actor)
            if actor == "synthetic-human" and receipt in self.human_gate_receipts else None
        )
        self.test_run_dir = self._approved_testware()
        self.dev_handoff_path = self._ready_for_test_handoff()

    @staticmethod
    def _write_json(path, value):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _run_git(root, *args):
        process = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace", shell=False,
        )
        if process.returncode:
            raise AssertionError(process.stderr)
        return process.stdout.strip()

    def _project_contracts(self):
        policy = {
            "schema_version": 1,
            "project": {"language": "en"},
            "foundation": {"profile": "arc42-standard-v1"},
            "authority": {
                "product": "docs/product.md", "domain": "docs/domain.md",
                "architecture": "docs/architecture.md", "testing": "docs/testing.md",
                "features": "docs/features.md",
            },
            "workflow": {"feature_root": "docs/features", "branch_convention": "feature/{feature_id}"},
            "testing": {"automation_repository_role": "project_test_automation"},
            "artifacts": {"optional": []},
        }
        topology = {
            "schema_version": 1,
            "project": {"id": "synthetic-project"},
            "repositories": [
                {"id": "core", "path": "app", "repository": "example/app", "role": "application"},
                {"id": "quality", "path": "automation", "repository": "example/qa", "role": "project_test_automation"},
            ],
        }
        self._write_json(self.root / ".sdlc/project-policy.yml", policy)
        self._write_json(self.root / ".sdlc/project-topology.yml", topology)

    def _init_repository(self, root, name, kind):
        root.mkdir(parents=True)
        self._run_git(root, "init", "-q")
        self._run_git(root, "config", "user.name", "Acceptance Fixture")
        self._run_git(root, "config", "user.email", "acceptance@example.invalid")
        (root / "README.md").write_text(f"Synthetic {kind} repository.\n", encoding="utf-8")
        self._run_git(root, "add", "README.md")
        self._run_git(root, "commit", "-q", "-m", "fixture base")
        self._run_git(root, "remote", "add", "origin", f"https://github.com/{name}.git")
        return self._run_git(root, "rev-parse", "HEAD")

    def _commit(self, root, message):
        self._run_git(root, "add", "-A")
        self._run_git(root, "commit", "-q", "-m", message)
        return self._run_git(root, "rev-parse", "HEAD")

    def _write_app_revision(self):
        (self.app_root / "src").mkdir()
        (self.app_root / "tests").mkdir()
        (self.app_root / "src/request.py").write_text("def submit(payload):\n    return payload\n", encoding="utf-8")
        (self.app_root / "tests/test_request.py").write_text("def test_source_local_evidence():\n    assert True\n", encoding="utf-8")
        self.app_revision = self._commit(self.app_root, "synthetic app revision")

    def _approved_testware(self):
        test_kit_policy.bootstrap_project_policy(self.root)
        design_skill = self.root / ".agents/skills/bmad-testarch-test-design"
        case_skill = self.root / ".agents/skills/create-test-cases"
        design_skill.parent.mkdir(parents=True, exist_ok=True)
        if not design_skill.exists():
            shutil.copytree(ROOT / "kits/test/skills/bmad-testarch-test-design", design_skill)
        if not case_skill.exists():
            shutil.copytree(ROOT / "kits/test/skills/create-test-cases", case_skill)
        config = self.root / "_bmad/tea/config.yaml"
        config.parent.mkdir(parents=True, exist_ok=True)
        if not config.exists():
            config.write_text(
                "user_name: Synthetic Tester\n"
                "communication_language: English\n"
                "document_output_language: English\n"
                "output_folder: .test-kit/runtime\n"
                "test_artifacts: .test-kit/runtime\n"
                "test_stack_type: Python unittest\n",
                encoding="utf-8",
            )
        design_run = self.root / ".test-kit/runs/FEATURE-1/automation-acceptance-design"
        prepared = test_vnext.prepare_vnext_design(
            self.handoff_path, design_run, project_root=self.root,
            skill_dir=design_skill, human_actor_authenticator=self.ba_auth,
        )
        design_rows = []
        for index, title in enumerate(("Submit an API request", "Run a system flow", "Verify a source-local component", "Review a manual scenario"), 1):
            design_rows.append(
                f"| TD-{index:03d} | {title} | API | - | BR-001; FR-001 | An eligible member receives the business outcome. |"
            )
        raw_design = Path(prepared["raw_output_path"])
        raw_design.write_text("\n".join((
            "# Test Design: Synthetic request flow", "## Test Coverage Plan",
            "### P0 - Critical", "None.", "### P1 - High",
            "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |",
            "|---|---|---|---|---|---|", *design_rows,
            "### P2 - Medium", "None.", "### P3 - Low", "None.",
        )) + "\n", encoding="utf-8")
        finalized = test_vnext.finalize_vnext_design(
            self.handoff_path, design_run, human_actor_authenticator=self.ba_auth,
        )
        self.assertEqual(finalized["status"], "DESIGN_REVIEW")
        design_snapshot = test_v1.load_persisted_design_snapshot(design_run, require_state="DESIGN_REVIEW")
        authority = test_vnext.revalidate_vnext_authority(design_run, human_actor_authenticator=self.ba_auth)
        design_receipt = {
            "gate": "DESIGN_REVIEW", "decision": "APPROVE",
            "artifact_id": design_snapshot.artifact_id, "artifact_revision": design_snapshot.revision,
            "artifact_sha256": design_snapshot.sha256,
            "input_refs": test_vnext.design_gate_input_refs(design_run, authority.baseline),
            "actor_id": "synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-05T10:00:00Z", "feedback": "",
        }
        self.human_gate_receipts.append(design_receipt)
        design_auth = lambda actor, actual: test_v1.AuthenticatedHumanActorContext(actor) if actor == "synthetic-human" and actual == design_receipt else None
        design_decision = test_vnext.apply_vnext_design_decision(
            design_run, design_receipt,
            human_actor_authenticator=design_auth,
            ba_human_actor_authenticator=self.ba_auth,
        )
        self.assertTrue(design_decision.accepted)
        approved_design = test_v1.load_persisted_design_snapshot(design_run, require_state="APPROVED_DESIGN")

        case_run = self.root / ".test-kit/runs/FEATURE-1/automation-acceptance-cases"
        prepared_cases = test_vnext.prepare_vnext_cases(
            self.handoff_path, design_run, case_run,
            project_root=self.root, skill_dir=case_skill,
            ba_human_actor_authenticator=self.ba_auth,
        )
        case_rows = []
        for index, title in enumerate(("Submit an API request", "Run a system flow", "Verify a source-local component", "Review a manual scenario"), 1):
            case_rows.extend((
                f"## TC-{index:03d} {title}",
                "- Mô tả: Verify the approved request behavior.",
                "- Tiền điều kiện: An eligible member exists.",
                "- Bước và kết quả mong đợi:",
                "  1. Submit a request. → The member receives the business outcome.",
                "- Test Data: Synthetic member",
                "- Priority: P1.",
                f"- Trace: BR-001; FR-001; TD-{index:03d}",
                "",
            ))
        Path(prepared_cases["raw_output_path"]).write_text("\n".join(("# Manual Test Cases", "", *case_rows)), encoding="utf-8")
        finalized_cases = test_vnext.finalize_vnext_cases(
            self.handoff_path, case_run, ba_human_actor_authenticator=self.ba_auth,
        )
        self.assertEqual(finalized_cases.status, "CASE_REVIEW")
        snapshot, case_state = test_cases.load_case_review_snapshot(
            case_run / "canonical/canonical-testcases.json",
            case_run / "workflow-state.json",
            case_run / "canonical/semantic-payload.json",
        )
        authority = test_vnext.revalidate_vnext_authority(case_run, human_actor_authenticator=self.ba_auth)
        case_refs = test_cases.case_gate_input_refs(
            authority.baseline, approved_design, run_dir=case_run,
            execution_contract_refs=case_state.execution_oracle_refs,
            case_snapshot=snapshot, vnext_authority=True,
        )
        case_receipt = {
            "gate": "CASE_REVIEW", "decision": "APPROVE",
            "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": case_refs,
            "actor_id": "synthetic-human", "actor_role": "HUMAN",
            "decided_at": "2026-10-05T10:05:00Z", "feedback": "",
        }
        self.human_gate_receipts.append(case_receipt)
        approved = test_vnext.apply_vnext_case_decision(
            case_run, case_receipt,
            human_actor_authenticator=self.human_test_auth,
            ba_human_actor_authenticator=self.ba_auth,
        )
        self.assertEqual(approved.status, "APPROVED_TESTWARE", (approved.finding, approved.findings))
        manifest = json.loads((case_run / "approved-testware-vnext.json").read_text(encoding="utf-8"))
        self.assertNotIn("fixture_type", manifest)
        self.assertIsNot(manifest.get("not_for_production"), True)
        return case_run

    def _ready_for_test_handoff(self):
        evidence_dir = self.root / "app"
        coverage = [
            {
                "id": identity, "status": "COVERED",
                "code_refs": [self.ba.ref("app/src/request.py")],
                "test_refs": [self.ba.ref("app/tests/test_request.py")],
            }
            for identity in ("BR-001", "FR-001")
        ]
        dev = dev_tests.DevVNextTests("test_normal_contract_acceptance_keeps_ba_bytes_immutable")
        dev.ba = self.ba
        dev.root = self.root
        dev.handoff = self.handoff
        dev.upstream = self.ba.ref("engineering-handoff-vnext.json")
        dev.repos = [{
            "id": "core", "role": "IMPLEMENTATION", "base_revision": self.app_base,
            "allowed_write_paths": ["src", "tests"], "read_only_evidence_paths": ["docs"],
        }]
        dev.checks = [{"name": "unit", "repository_id": "core", "category": "UNIT", "command": ["python", "-m", "unittest"]}]
        dev.context = {"ba_authenticator": self.ba_auth}
        dev.produced = {"core": self.app_revision}
        dev.ba.put("code.json", {"source": "exact app revision"})
        dev.ba.put("test.json", {"source": "exact app test evidence"})
        dev.ba.put("review.json", {"source": "exact consolidated Dev review"})
        dev.coverage = lambda: coverage
        handoff = dev.finish()
        path = self.root / "dev-handoff-vnext.json"
        self._write_json(path, handoff)
        return path

    def _runtime(self, name="FEATURE-1", repository_roots=None):
        return automation.AutomationRuntime(
            self.root, self.root / f".test-kit/automation/runs/{name}",
            human_actor_authenticator=self.human_test_auth,
            ba_human_actor_authenticator=self.ba_auth,
            repository_roots=repository_roots if repository_roots is not None else {
                "core": self.app_root, "quality": self.automation_root,
            },
        )

    def _directory_reparse_point(self, link, target):
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            environment = os.environ.copy()
            environment["TEST_AUTOMATION_LINK_PATH"] = str(link)
            environment["TEST_AUTOMATION_TARGET_PATH"] = str(target)
            result = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-Command",
                    "New-Item -ItemType Junction -Path $env:TEST_AUTOMATION_LINK_PATH -Target $env:TEST_AUTOMATION_TARGET_PATH | Out-Null",
                ],
                capture_output=True, text=True, env=environment, shell=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def _assert_repository_routing_boundaries(self):
        topology_path = self.root / ".sdlc/project-topology.yml"
        original = json.loads(topology_path.read_text(encoding="utf-8"))
        try:
            wrong_role = json.loads(json.dumps(original))
            wrong_role["repositories"][1]["role"] = "application"
            self._write_json(topology_path, wrong_role)
            with self.assertRaisesRegex(automation.AutomationV1Error, "AUTOMATION_REPOSITORY_AMBIGUOUS"):
                self._runtime("WRONG-ROLE").start(self.test_run_dir)

            ambiguous = json.loads(json.dumps(original))
            ambiguous["repositories"].append({
                "id": "second-quality", "path": "second-automation",
                "repository": "example/second-qa", "role": "project_test_automation",
            })
            self._write_json(topology_path, ambiguous)
            with self.assertRaisesRegex(automation.AutomationV1Error, "AUTOMATION_REPOSITORY_AMBIGUOUS"):
                self._runtime("AMBIGUOUS-ROLE").start(self.test_run_dir)

            self._write_json(topology_path, original)
            with self.assertRaisesRegex(automation.AutomationV1Error, "REPOSITORY_IDENTITY_INVALID"):
                self._runtime("WRONG-REPOSITORY", {
                    "core": self.app_root, "quality": self.app_root,
                }).start(self.test_run_dir)

            same_repository = json.loads(json.dumps(original))
            same_repository["repositories"][1]["repository"] = "Example/App"
            self._write_json(topology_path, same_repository)
            with self.assertRaisesRegex(ValueError, "duplicate repository"):
                self._runtime("SHARED-REPOSITORY", {
                    "core": self.app_root, "quality": self.app_root,
                }).start(self.test_run_dir)
            self._write_json(topology_path, original)

            alias = self.root / "automation-alias"
            self._directory_reparse_point(alias, self.automation_root)
            try:
                with self.assertRaisesRegex(automation.AutomationV1Error, "REPOSITORY_IDENTITY_INVALID"):
                    self._runtime("SYMLINKED-REPOSITORY", {
                        "core": self.app_root, "quality": alias,
                    }).start(self.test_run_dir)
            finally:
                if alias.is_symlink():
                    alias.unlink()
                elif alias.exists():
                    alias.rmdir()

            route_runtime = self._runtime("TOPOLOGY-DRIFT")
            route_runtime.start(self.test_run_dir)
            drifted = json.loads(json.dumps(original))
            drifted["repositories"][1]["path"] = "automation-replaced"
            self._write_json(topology_path, drifted)
            with self.assertRaisesRegex(automation.AutomationV1Error, "NEEDS_REPLAN"):
                route_runtime.status()

            missing = json.loads(json.dumps(original))
            missing["repositories"][1]["path"] = "not-yet-created/automation"
            self._write_json(topology_path, missing)
            runtime = self._runtime("MISSING-REPOSITORY", {"core": self.app_root})
            state = runtime.start(self.test_run_dir)
            state = runtime.analyze_suitability(self._assessments())
            state = runtime.plan(self._plan_specs())
            self.assertIsNone(runtime._read_artifact_ref(state["plan_ref"])["base_revision"])
            blocked = runtime.begin_implementation()
            self.assertEqual(blocked["lifecycle"], "BLOCKED")
            self.assertEqual(blocked["blocked_reason"]["code"], "AUTOMATION_REPOSITORY_MISSING")
            with self.assertRaisesRegex(automation.AutomationV1Error, "INVALID_TRANSITION"):
                runtime.finalize(self.dev_handoff_path)
        finally:
            self._write_json(topology_path, original)

    @staticmethod
    def _assessments(blocked=False, add_open_dependency=False, manual_only=False, blocked_required=True):
        nonblocked = "MANUAL_ONLY" if blocked or manual_only else None
        rows = [
            {"testcase_id": "TC-001", "classification": "BLOCKED" if blocked else (nonblocked or "API"), "required": blocked_required if blocked else True, "rationale": "Use the approved interface."},
            {"testcase_id": "TC-002", "classification": "MANUAL_ONLY", "required": True, "rationale": "Keep the approved case as a manual protocol."},
            {"testcase_id": "TC-003", "classification": nonblocked or "UNIT", "required": True, "rationale": "Reference exact Dev-local coverage."},
            {"testcase_id": "TC-004", "classification": nonblocked or "E2E", "required": True, "rationale": "Use the project-owned end-to-end runner."},
        ]
        if add_open_dependency:
            rows[1]["dependency_refs"] = [{
                "kind": "ENVIRONMENT_ACCESS", "status": "OPEN", "required": True, "resolution_ref": None,
            }]
        return rows

    @staticmethod
    def _plan_specs(include_api=True, include_e2e=True):
        verification = [{"category": "STATIC", "argv": ["git", "diff", "--cached", "--check"]}]
        specs = {}
        if include_api:
            specs["TC-001"] = {
                "suite": "api", "planned_paths": ["tests/api/test_request.py"],
                "runner": "project-native", "execution_command": ["python", "-m", "pytest", "tests/api/test_request.py"],
                "verification_commands": verification,
            }
        if include_e2e:
            specs["TC-004"] = {
                "suite": "end-to-end", "planned_paths": ["tests/e2e/test_request_flow.py"],
                "runner": "project-native", "execution_command": ["python", "-m", "pytest", "tests/e2e/test_request_flow.py"],
                "verification_commands": verification,
            }
        return specs

    def _review(self):
        return {"reviewer": "synthetic-review", "checks": {key: True for key in REVIEW_CHECKS}, "findings": []}

    def _implement(self, runtime, state):
        plan = runtime._read_artifact_ref(state["plan_ref"])
        base = state["implementation_base_revision"]
        sources = {
            "AUT-0001": f"# plan revision {plan['revision']}\ndef test_api_harness_shape():\n    assert True\n",
            "AUT-0002": f"# plan revision {plan['revision']}\ndef test_e2e_harness_shape():\n    assert True\n",
        }
        for item in plan["items"]:
            for path in item["planned_paths"]:
                self.assertIn(item["aut_id"], sources)
                runtime.write_source(item["aut_id"], "quality", path, sources[item["aut_id"]], base_revision=base)
        self._run_git(self.automation_root, "add", "tests/api/test_request.py", "tests/e2e/test_request_flow.py")
        self._run_git(self.automation_root, "commit", "-q", "-m", "Implement planned automation")
        return runtime.record_implementation()

    def _new_automation_implementation(self, name):
        repository = self.root / f"automation-{name}"
        self._init_repository(repository, "example/qa", "automation")
        runtime = self._runtime(name, {"core": self.app_root, "quality": repository})
        state = runtime.start(self.test_run_dir)
        runtime.analyze_suitability(self._assessments())
        state = runtime.plan(self._plan_specs())
        state = runtime.begin_implementation()
        plan = runtime._read_artifact_ref(state["plan_ref"])
        for item in plan["items"]:
            path = item["planned_paths"][0]
            source = f"# {item['aut_id']}\ndef test_harness_shape():\n    assert True\n"
            runtime.write_source(
                item["aut_id"], "quality", path, source,
                base_revision=state["implementation_base_revision"],
            )
        return runtime, state, repository

    def test_uncommitted_automation_states_are_rejected_before_implementation_evidence(self):
        for name, mode in (("STAGED", "staged"), ("UNSTAGED", "unstaged"), ("UNTRACKED", "untracked")):
            with self.subTest(mode=mode):
                runtime, state, repository = self._new_automation_implementation(name)
                if mode == "staged":
                    self._run_git(repository, "add", "tests/api/test_request.py", "tests/e2e/test_request_flow.py")
                elif mode == "untracked":
                    (repository / "unplanned.py").write_text("# untracked\n", encoding="utf-8")
                with self.assertRaises(automation.AutomationV1Error) as caught:
                    runtime.record_implementation()
                self.assertEqual(caught.exception.code, "AUTOMATION_COMMIT_REQUIRED")

    def test_committed_automation_diff_must_match_all_planned_paths(self):
        runtime, state, repository = self._new_automation_implementation("OUT-OF-PLAN")
        (repository / "unplanned.py").write_text("# outside the Plan\n", encoding="utf-8")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Commit planned and unplanned files")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            runtime.record_implementation()
        self.assertEqual(caught.exception.code, "WRITE_SCOPE_VIOLATION")

        runtime, state, repository = self._new_automation_implementation("MISSING-PLANNED")
        (repository / "tests/e2e/test_request_flow.py").unlink()
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Commit only one planned file")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            runtime.record_implementation()
        self.assertEqual(caught.exception.code, "IMPLEMENTATION_INCOMPLETE")

    def test_dirty_or_new_automation_revision_invalidates_review_and_verification(self):
        runtime, state, repository = self._new_automation_implementation("DIRTY-AFTER-COMMIT")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Commit automation")
        runtime.record_implementation()
        source = repository / "tests/api/test_request.py"
        source.write_text(source.read_text(encoding="utf-8") + "# local edit\n", encoding="utf-8")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            runtime.record_review(self._review())
        self.assertEqual(caught.exception.code, "AUTOMATION_COMMIT_REQUIRED")

        runtime, state, repository = self._new_automation_implementation("NEW-COMMIT-AFTER-REVIEW")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Commit automation")
        runtime.record_implementation()
        runtime.record_review(self._review())
        source = repository / "tests/api/test_request.py"
        source.write_text(source.read_text(encoding="utf-8") + "# later commit\n", encoding="utf-8")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Change after review")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            runtime.verify()
        self.assertEqual(caught.exception.code, "NEEDS_REPLAN")

        runtime, state, repository = self._new_automation_implementation("VERIFY-MUTATES-SOURCE")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Commit automation")
        runtime.record_implementation()
        runtime.record_review(self._review())
        real_run = automation.subprocess.run

        def mutate_after_verification(args, *positional, **options):
            result = real_run(args, *positional, **options)
            if list(args) == ["git", "diff", "--cached", "--check"]:
                source = repository / "tests/api/test_request.py"
                source.write_text(source.read_text(encoding="utf-8") + "# verification edit\n", encoding="utf-8")
            return result

        with mock.patch.object(automation.subprocess, "run", side_effect=mutate_after_verification):
            with self.assertRaises(automation.AutomationV1Error) as caught:
                runtime.verify()
        self.assertEqual(caught.exception.code, "AUTOMATION_VERIFICATION_MUTATED_SOURCE")

    def test_new_automation_commit_after_review_and_verification_requires_replan(self):
        runtime, state, repository = self._new_automation_implementation("NEW-COMMIT-AFTER-VERIFY")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Commit automation")
        runtime.record_implementation()
        runtime.record_review(self._review())
        runtime.verify()
        source = repository / "tests/api/test_request.py"
        source.write_text(source.read_text(encoding="utf-8") + "# later commit\n", encoding="utf-8")
        self._run_git(repository, "add", "-A")
        self._run_git(repository, "commit", "-q", "-m", "Change after verification")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            runtime.finalize(self.dev_handoff_path)
        self.assertEqual(caught.exception.code, "NEEDS_REPLAN")

    def _finish_automation(self, runtime):
        state = runtime.begin_implementation()
        self.assertEqual(state["lifecycle"], "AUTOMATION_IMPLEMENTING")
        self._implement(runtime, state)
        state = runtime.record_review(self._review())
        self.assertEqual(state["lifecycle"], "AUTOMATION_VERIFYING")
        state = runtime.verify()
        self.assertEqual(state["lifecycle"], "AUTOMATION_VERIFYING")
        self.assertEqual(runtime._read_artifact_ref(state["verification_ref"])["status"], "PASS")
        return state

    def test_api_e2e_shift_left_dev_local_manual_review_verify_and_fresh_resume(self):
        self._assert_repository_routing_boundaries()
        manifest_path = self.test_run_dir / "approved-testware-vnext.json"
        approved_manifest = manifest_path.read_bytes()
        legacy_manifest = json.loads(approved_manifest)
        legacy_manifest["state"] = "LEGACY_COMPAT"
        legacy_manifest["vnext_authority"] = False
        self._write_json(manifest_path, legacy_manifest)
        try:
            with self.assertRaisesRegex(automation.AutomationV1Error, "APPROVED_TESTWARE_REQUIRED"):
                self._runtime("LEGACY-REJECT").start(self.test_run_dir)
        finally:
            manifest_path.write_bytes(approved_manifest)

        runtime = self._runtime()
        state = runtime.start(self.test_run_dir)
        self.assertEqual(state["lifecycle"], "AUTOMATION_INTAKE")
        state = runtime.analyze_suitability(self._assessments())
        suitability = runtime._read_artifact_ref(state["suitability_ref"])
        self.assertEqual(len(suitability["rows"]), 4)
        self.assertEqual(suitability["rows"][1]["owner"], "MANUAL")
        self.assertEqual(suitability["rows"][2]["owner"], "DEV_LOCAL_REFERENCE")

        state = runtime.plan(self._plan_specs())
        plan = runtime._read_artifact_ref(state["plan_ref"])
        self.assertEqual([row["aut_id"] for row in plan["items"]], ["AUT-0001", "AUT-0002"])
        self.assertEqual(plan["items"][1]["runner"], "project-native")
        self.assertNotIn("approval", json.dumps(plan).lower())

        state = runtime.begin_implementation()
        app_file = self.app_root / "tests/test_request.py"
        app_before = hashlib.sha256(app_file.read_bytes()).hexdigest()
        outside = self.root / "outside-automation-path"
        outside.mkdir()
        link = self.automation_root / "tests/api"
        link.parent.mkdir()
        self._directory_reparse_point(link, outside)
        try:
            with self.assertRaisesRegex(automation.AutomationV1Error, "UNSAFE_PATH"):
                runtime.write_source(
                    "AUT-0001", "quality", "tests/api/test_request.py", "# escaped\n",
                    base_revision=state["implementation_base_revision"],
                )
        finally:
            if link.is_symlink():
                link.unlink()
            elif os.name == "nt" and link.exists():
                link.rmdir()
            outside.rmdir()
        out_of_scope = self.automation_root / "unplanned-automation-source.py"
        out_of_scope.write_text("# arbitrary editor write\n", encoding="utf-8")
        try:
            with self.assertRaisesRegex(automation.AutomationV1Error, "AUTOMATION_COMMIT_REQUIRED"):
                runtime.record_implementation()
        finally:
            out_of_scope.unlink()
        with self.assertRaisesRegex(automation.AutomationV1Error, "APP_REPOSITORY_WRITE_FORBIDDEN"):
            runtime.write_source("AUT-0001", "core", "tests/test_request.py", "# forbidden\n", base_revision=state["implementation_base_revision"])
        with self.assertRaisesRegex(automation.AutomationV1Error, "WRITE_SCOPE_VIOLATION"):
            runtime.write_source("AUT-0001", "quality", "tests/not-planned.py", "# forbidden\n", base_revision=state["implementation_base_revision"])
        self.assertEqual(hashlib.sha256(app_file.read_bytes()).hexdigest(), app_before)

        self._implement(runtime, state)
        state = runtime.record_review(self._review())
        self.assertEqual(state["lifecycle"], "AUTOMATION_VERIFYING")
        missing_dev = self.root / "missing-dev-handoff.json"
        with self.assertRaises(automation.AutomationV1Error):
            runtime.finalize(missing_dev)
        self.assertIsNone(runtime.status()["handoff_ref"])

        executed = []
        real_run = automation.subprocess.run

        def observe_command(args, *call_args, **call_kwargs):
            executed.append(list(args))
            return real_run(args, *call_args, **call_kwargs)

        with mock.patch.object(automation.subprocess, "run", side_effect=observe_command):
            state = runtime.verify()
        self.assertFalse(any("pytest" in part for command in executed for part in command))
        self.assertEqual(runtime._read_artifact_ref(state["verification_ref"])["product_execution"], "NOT_RUN")
        old_plan = runtime._read_artifact_ref(state["plan_ref"])
        state = runtime.request_replan("Execution command changed after implementation started")
        self.assertEqual(state["lifecycle"], "NEEDS_REPLAN")
        self.assertIsNone(state["implementation"])
        self.assertIsNone(state["review_ref"])
        self.assertIsNone(state["verification_ref"])
        revised_specs = self._plan_specs()
        revised_specs["TC-001"]["execution_command"] = ["python", "-m", "pytest", "tests/api/test_request.py", "-q"]
        state = runtime.replan(self._assessments(), revised_specs)
        new_plan = runtime._read_artifact_ref(state["plan_ref"])
        self.assertEqual(new_plan["revision"], "2")
        self.assertEqual([item["aut_id"] for item in new_plan["items"]], [item["aut_id"] for item in old_plan["items"]])
        self.assertNotEqual(new_plan["items"][0]["execution_command"], old_plan["items"][0]["execution_command"])
        state = runtime.begin_implementation()
        self._implement(runtime, state)
        state = runtime.record_review(self._review())
        state = runtime.verify()
        (self.app_root / "src/request.py").write_text("def submit(payload):\n    return {\"saved\": payload}\n", encoding="utf-8")
        self.app_revision = self._commit(self.app_root, "Dev updates the current application revision")
        stale_dev = runtime.finalize(self.dev_handoff_path)
        self.assertEqual(stale_dev["lifecycle"], "BLOCKED")
        self.assertIn(stale_dev["blocked_reason"]["code"], {"DEV_HANDOFF_INVALID", "DEV_REVISION_STALE"})
        self.dev_handoff_path = self._ready_for_test_handoff()
        ready = runtime.finalize(self.dev_handoff_path)
        self.assertEqual(ready["lifecycle"], "EXECUTION_READY")
        handoff = runtime.revalidate_handoff()
        self.assertEqual(handoff["state"], "EXECUTION_READY")
        self.assertEqual(len(handoff["automation_items"]), 2)
        self.assertEqual(len(handoff["manual_testcases"]), 1)
        self.assertEqual(len(handoff["dev_local_references"]), 1)
        self.assertEqual(handoff["application_revisions"]["core"], self.app_revision)
        self.assertEqual(handoff["automation_revision"], self._run_git(self.automation_root, "rev-parse", "HEAD"))
        self.assertEqual(
            {item["revision"] for item in handoff["automation_items"]},
            {handoff["automation_revision"]},
        )
        self.assertNotIn("expected_result", json.dumps(handoff).lower())
        self.assertNotIn("verified", json.dumps(handoff).lower())

        clone = self.root / "automation-fresh-clone"
        cloned = subprocess.run(
            ["git", "clone", "--quiet", "--no-local", str(self.automation_root), str(clone)],
            capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False,
        )
        self.assertEqual(cloned.returncode, 0, cloned.stdout + cloned.stderr)
        self._run_git(clone, "checkout", "--quiet", "--detach", handoff["automation_revision"])
        self.assertEqual(self._run_git(clone, "rev-parse", "HEAD"), handoff["automation_revision"])
        implementation = runtime.status()["implementation"]
        committed_hashes = {row["path"]: row["sha256"] for row in implementation["files"]}
        self.assertEqual(implementation["base_revision"], new_plan["base_revision"])
        self.assertEqual(implementation["repository_revision"], handoff["automation_revision"])
        self.assertEqual(implementation["changed_paths"], sorted(committed_hashes))
        self.assertEqual(
            implementation["aut_paths"],
            {item["aut_id"]: item["planned_paths"] for item in new_plan["items"]},
        )
        for item in handoff["automation_items"]:
            for path in item["paths"]:
                reconstructed = clone / Path(path)
                self.assertTrue(reconstructed.is_file(), path)
                committed = subprocess.run(
                    ["git", "-C", str(clone), "cat-file", "blob", f"{handoff['automation_revision']}:{path}"],
                    capture_output=True, check=True, shell=False,
                ).stdout
                self.assertEqual(hashlib.sha256(committed).hexdigest(), committed_hashes[path])

        resumed = self._runtime().status()
        self.assertEqual(resumed["lifecycle"], "EXECUTION_READY")
        self.assertEqual(self._runtime().revalidate_handoff(), handoff)

        source = self.automation_root / handoff["automation_items"][0]["paths"][0]
        source.write_bytes(source.read_bytes() + b"# local drift\n")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            self._runtime().revalidate_handoff()
        self.assertEqual(caught.exception.code, "AUTOMATION_COMMIT_REQUIRED")
        relative_source = handoff["automation_items"][0]["paths"][0]
        self._run_git(self.automation_root, "checkout", "--quiet", "--", relative_source)
        source.write_bytes(source.read_bytes() + b"# committed drift\n")
        self._run_git(self.automation_root, "add", "--", relative_source)
        self._run_git(self.automation_root, "commit", "-q", "-m", "Automation changes after readiness")
        with self.assertRaises(automation.AutomationV1Error) as caught:
            self._runtime().revalidate_handoff()
        self.assertEqual(caught.exception.code, "NEEDS_REPLAN")

    def test_required_blocked_and_open_dependencies_stop_until_replan_and_manual_only_can_finish(self):
        runtime = self._runtime("BLOCKED-1")
        state = runtime.start(self.test_run_dir)
        state = runtime.analyze_suitability(self._assessments(blocked=True))
        state = runtime.plan({})
        state = runtime.begin_implementation()
        self.assertEqual(state["lifecycle"], "AUTOMATION_IMPLEMENTING")
        state = runtime.record_implementation()
        state = runtime.record_review(self._review())
        state = runtime.verify()
        blocked = runtime.finalize(self.dev_handoff_path)
        self.assertEqual(blocked["lifecycle"], "BLOCKED")
        self.assertEqual(blocked["blocked_reason"]["code"], "REQUIRED_BLOCKED_TESTCASE")
        self.assertIsNone(blocked["handoff_ref"])

        state = runtime.replan(self._assessments(add_open_dependency=True, manual_only=True), {})
        self.assertEqual(state["lifecycle"], "AUTOMATION_PLANNED")
        self.assertIsNone(state["implementation"])
        state = runtime.begin_implementation()
        state = runtime.record_implementation()
        state = runtime.record_review(self._review())
        state = runtime.verify()
        open_blocked = runtime.finalize(self.dev_handoff_path)
        self.assertEqual(open_blocked["lifecycle"], "BLOCKED")
        self.assertEqual(open_blocked["blocked_reason"]["code"], "REQUIRED_DEPENDENCY_OPEN")

        state = runtime.replan(self._assessments(manual_only=True), {})
        state = runtime.begin_implementation()
        state = runtime.record_implementation()
        state = runtime.record_review(self._review())
        state = runtime.verify()
        ready = runtime.finalize(self.dev_handoff_path)
        self.assertEqual(ready["lifecycle"], "EXECUTION_READY")
        self.assertEqual(runtime.revalidate_handoff()["manual_testcases"].__len__(), 4)

        optional_block = self._runtime("OPTIONAL-BLOCKED")
        optional_block.start(self.test_run_dir)
        optional_block.analyze_suitability(self._assessments(blocked=True, blocked_required=False))
        optional_block.plan({})
        optional_block.begin_implementation()
        optional_block.record_implementation()
        optional_block.record_review(self._review())
        optional_block.verify()
        ready = optional_block.finalize(self.dev_handoff_path)
        self.assertEqual(ready["lifecycle"], "EXECUTION_READY")
        handoff = optional_block.revalidate_handoff()
        self.assertEqual([row["testcase_id"] for row in handoff["blocked_testcases"]], ["TC-001"])
        self.assertNotIn("expected_result", json.dumps(handoff).lower())


if __name__ == "__main__":
    unittest.main()
