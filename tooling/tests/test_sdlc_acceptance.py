"""Fresh synthetic end-to-end fixtures. Never uses the Digital Wedding CR."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.lib import ba_kit, dev_kit as dev, dev_router, test_kit_v1 as design, test_kit_v1_cases as cases
from tooling.lib import execution_contract as execution, testware_promotion as promotion
from tooling.tests.test_sdlc_contracts import delivery_fixture, generalized_delivery_fixture
from tooling.tests.test_dev_kit import _planning_text, _advance_high_risk_to_plan_gate
from tooling import install_dev_kit, prepare_agent_profile
from tooling.sdlc_suite import check_runtime_ignores
from delivery_manifest import load_delivery_manifest

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return ref(path)


def ref(path):
    return {"path": str(path), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def git(project, *args):
    return subprocess.check_output(["git", "-C", str(project), *args], text=True, stderr=subprocess.DEVNULL).strip()


def init(project, lane):
    project.mkdir(parents=True, exist_ok=True)
    git(project, "init", "-b", "synthetic-readiness")
    git(project, "config", "user.name", "Synthetic Acceptance")
    git(project, "config", "user.email", "synthetic@example.invalid")
    ignores = ".test-kit/runs/\n.test-kit/runtime/\ntest-runs/\n.agents/skills/\n" if lane == "docs" else ".devkit/\n.specify/workflows/runs/\n__pycache__/\n"
    (project / ".gitignore").write_text(ignores, encoding="utf-8")
    (project / "AGENTS.md").write_text("# Synthetic fixture\nDev implements approved scope. Reviewer is read-only. Tester owns VERIFIED. Human gates are never inferred.\n", encoding="utf-8")


def receipt(snapshot, refs, gate):
    return {"gate": gate, "decision": "APPROVE", "artifact_id": snapshot.artifact_id,
            "artifact_revision": snapshot.revision, "artifact_sha256": snapshot.sha256,
            "input_refs": refs, "actor_id": "human:synthetic-fixture", "actor_role": "HUMAN",
            "decided_at": "2026-10-02T00:00:00Z", "feedback": "Synthetic contract fixture only"}


def fixture_actor(actor_id, _receipt):
    return design.AuthenticatedHumanActorContext(actor_id)


class FreshSyntheticAcceptance(unittest.TestCase):
    def test_dev_readiness_uses_external_approval_precedence_for_historical_lifecycle_text(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-approval-precedence-") as temp:
            root = Path(temp)
            docs = root / "docs"
            feature = docs / "features/CR-001"
            feature.mkdir(parents=True)
            manifest, data = generalized_delivery_fixture(feature)
            handoff = feature / "engineering-handoff.yml"
            rules = feature / "rules.md"
            srs = feature / "srs.md"
            rules.write_text(
                "# Business Rules\n\nTrạng thái lịch sử: DRAFT_FOR_HUMAN_BASELINE_REVIEW.\n\n"
                "| ID | Rule | Note |\n|---|---|---|\n"
                "| `BR-001` | Search and status are combined with AND. | Confirmed |\n",
                encoding="utf-8",
            )
            srs.write_text(
                "# SRS\n\nTrạng thái lịch sử: DRAFT_FOR_HUMAN_BASELINE_REVIEW.\n\n"
                "| ID | Requirement | Note |\n|---|---|---|\n"
                "| `FR-001` | Filter the approved list. | Confirmed |\n",
                encoding="utf-8",
            )
            handoff_text = handoff.read_text(encoding="utf-8")
            fields, _, _, _ = dev._yaml_fields(handoff_text)
            for role, source in (("business_rules", rules), ("srs", srs)):
                old = fields[("authoritative_sources", role, "sha256")]
                handoff_text = handoff_text.replace(old, ref(source)["sha256"])
            handoff_text = handoff_text.replace(
                "  non_blocking: []",
                "  non_blocking:\n    - UX Contract and prototype are pending the G2 Human UX Gate; do not create the Delivery Manifest or implement.",
            )
            handoff.write_text(handoff_text, encoding="utf-8")
            data["ba"]["handoff"]["sha256"] = ref(handoff)["sha256"]

            contract = feature / data["ux"]["contract"]["path"]
            contract.write_text(
                contract.read_text(encoding="utf-8") + "\nHistorical status: DRAFT_FOR_HUMAN_UX_REVIEW / PENDING_HUMAN_REVIEW.\n",
                encoding="utf-8",
            )
            receipt_path = feature / data["ux"]["approval_receipt"]["path"]
            receipt_data = json.loads(receipt_path.read_text(encoding="utf-8"))
            contract_ref = data["ux"]["contract"]["path"]
            receipt_data["sources"][contract_ref] = ref(contract)["sha256"]
            receipt_data["semantic_snapshot_sha256"] = hashlib.sha256(
                json.dumps(receipt_data["sources"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            receipt_path.write_text(json.dumps(receipt_data), encoding="utf-8")
            data["ux"]["contract"]["sha256"] = ref(contract)["sha256"]
            data["ux"]["approval_receipt"]["sha256"] = ref(receipt_path)["sha256"]

            app = root / "app"
            init(app, "app")
            (app / "package.json").write_text(
                json.dumps({"scripts": {"build": "node -e \"\"", "qa:gate": "node -e \"\""}}),
                encoding="utf-8",
            )
            git(app, "add", ".")
            git(app, "commit", "-m", "Synthetic authority precedence fixture")
            git(app, "remote", "add", "origin", "https://github.com/fixture/app.git")
            data["targets"][0]["base_revision"] = git(app, "rev-parse", "HEAD")
            write_json(manifest, data)

            delivery = load_delivery_manifest(manifest)
            self.assertEqual(delivery["sha256"], ref(manifest)["sha256"])
            source_bytes = {path: path.read_bytes() for path in (handoff, rules, srs, contract, receipt_path)}
            started = dev_router._legacy_start_from_delivery(app, manifest, "Implement approved fixture behavior")
            self.assertEqual(started["route"]["risk_level"], "NORMAL")
            run = Path(started["run_dir"])
            inputs = dev._read_json(run / "input.json")
            authority = inputs["authority_precedence"]
            self.assertEqual(authority["ba"]["status"], "APPROVED_FOR_ENGINEERING")
            self.assertEqual(authority["ba"]["source_hashes"], delivery["baseline"].source_hashes)
            self.assertEqual(authority["ux"]["status"], "APPROVED_EXACT_SNAPSHOT")
            self.assertEqual(authority["ux"]["approval_receipt_sha256"], data["ux"]["approval_receipt"]["sha256"])

            dev.write_artifact(run / "spec-readiness.json", {"status": "READY_FOR_PLANNING", "business_ambiguities": []})
            self.assertEqual(dev.preflight(app)["status"], "READY_FOR_PLANNING")
            for path, original in source_bytes.items():
                self.assertEqual(path.read_bytes(), original)

            dev.write_artifact(run / "spec-readiness.json", {
                "status": "NEEDS_BA_CLARIFICATION",
                "business_ambiguities": ["Approved semantic rules disagree about the combined filter behavior."],
            })
            self.assertEqual(dev.preflight(app)["status"], "NEEDS_BA_CLARIFICATION")
            inputs["authority_precedence"]["ux"]["status"] = "PENDING_HUMAN_REVIEW"
            dev._write_run_json(run, "input.json", inputs, inputs["baseline_snapshot"])
            with self.assertRaisesRegex(ValueError, "validated delivery approval context changed"):
                dev.preflight(app)

    def check_preparation_patches_preserve_authority_and_ignore_runtime(self):
        workspace = ROOT.parent / "digital-wedding-workspace"
        patches = workspace / "audits/golden-run-readiness-2026-10-02/preparation"
        if not patches.is_dir():
            raise AssertionError("readiness preparation patches must be supplied with suite acceptance")
        with tempfile.TemporaryDirectory(prefix="sdlc-preparation-") as temp:
            root = Path(temp)
            app = root / "app"
            init(app, "app")
            original = workspace / "digital-wedding-card-app"
            for name in ("AGENTS.md", ".gitignore"):
                (app / name).write_bytes((original / name).read_bytes())
            git(app, "apply", str(patches / "application-preparation.patch"))
            text = (app / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Dev Agent (Feature Builder)", text)
            self.assertIn("Tester", text)
            self.assertNotIn("Gemini (Feature Builder)", text)
            for rule in ("npm run qa:gate", "No Direct Merging", "No Silent Business Decisions", "Supabase", "Human"):
                self.assertIn(rule, text)
            self.assertEqual(check_runtime_ignores(app, "app"), "PASS")
            docs = root / "docs"
            init(docs, "docs")
            (docs / ".gitignore").unlink()
            git(docs, "apply", str(patches / "docs-runtime-preparation.patch"))
            self.assertEqual(check_runtime_ignores(docs, "docs"), "PASS")

    def test_canonical_srs_without_ids_and_ba_gate_fixture(self):
        from contracts import validate_handoff_file, validate_state_data
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-ba-") as temp:
            root = Path(temp)
            manifest, data = delivery_fixture(root, False)
            srs = root / "srs.md"
            srs.write_text("# 1 Cộng hai số nguyên — SYNTHETIC ONLY\n\n"
                "## 1.1 Thông tin chung về chức năng\n| Nội dung | Mô tả |\n|---|---|\n"
                "| Mô tả | Chức năng cho phép người dùng cộng hai số nguyên. |\n| Tác nhân | Người dùng fixture. |\n"
                "| Trigger | Gửi hai số nguyên. |\n| Điều kiện trước | Hai giá trị là số nguyên. |\n"
                "| Điều kiện sau | Trả tổng của hai số. |\n| Luồng ngoại lệ | Không áp dụng trong fixture này. |\n"
                "| Luồng thay thế | Không áp dụng. |\n\n## 1.2 Luồng nghiệp vụ\n"
                "### Biểu đồ luồng nghiệp vụ\nNgười dùng gửi hai số → hệ thống trả tổng.\n"
                "### Mô tả chi tiết nghiệp vụ\n| STT | Business Rule | Mô tả chi tiết |\n|---|---|---|\n"
                "| 1 | Quy tắc cộng | Kết quả bằng tổng hai số nguyên được gửi. |\n\n"
                "## 1.3 Thiết kế giao diện (nếu có)\nN/A: fixture không có UX lane.\n"
                "### Mô tả chi tiết thành phần theo giao diện\nN/A.\n", encoding="utf-8")
            rules = root / "rules.md"
            rules.write_text("# Quy tắc fixture\nKết quả bằng tổng hai số nguyên được gửi.\n", encoding="utf-8")
            handoff = root / "engineering-handoff.yml"
            text = handoff.read_text(encoding="utf-8")
            fields, _, _, _ = dev._yaml_fields(text)
            for role, path in (("srs", srs), ("business_rules", rules)):
                text = text.replace(fields[("authoritative_sources", role, "sha256")], ref(path)["sha256"])
            handoff.write_text(text, encoding="utf-8")
            data["ba"]["handoff"]["sha256"] = ref(handoff)["sha256"]
            write_json(manifest, data)
            self.assertEqual(validate_handoff_file(handoff), [])
            baseline = design.load_approved_baseline(handoff)
            self.assertTrue(all(unit.id.startswith("BAREF:") for unit in (*baseline.requirements, *baseline.business_rules)))
            state = {"schema_version": 1, "feature": {"id": "CR-001"}, "operation": "synthetic_acceptance", "stage": "HANDOFF",
                     "artifacts": {"srs": ref(srs)}, "gates": {"ba": {"fixture": "SYNTHETIC_ONLY", "decision": "APPROVE", "sha256": ref(srs)["sha256"]}},
                     "pending": [], "source_of_truth": {"handoff": ref(handoff)}, "history": []}
            self.assertEqual(validate_state_data(state), [])

    def test_same_session_design_traces_cr_dwc_inline_business_rule_ids(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-inline-id-design-") as temp:
            docs = Path(temp) / "docs"
            init(docs, "docs")
            feature = docs / "features/CR-001"
            feature.mkdir(parents=True)
            manifest, data = generalized_delivery_fixture(feature)
            handoff = feature / "engineering-handoff.yml"
            rules = feature / "rules.md"
            srs = feature / "srs.md"
            rules.write_bytes((Path(__file__).parent / "fixtures/approved-baseline-inline-ids/business-rules.md").read_bytes())
            srs.write_text(
                "# SRS fixture\n\n| ID | Requirement | Notes |\n|---|---|---|\n"
                "| `FR-001` | The approved rule set can be traced. | Confirmed |\n",
                encoding="utf-8",
            )
            handoff_text = handoff.read_text(encoding="utf-8")
            fields, _, _, _ = dev._yaml_fields(handoff_text)
            for role, source in (("business_rules", rules), ("srs", srs)):
                old = fields[("authoritative_sources", role, "sha256")]
                handoff_text = handoff_text.replace(old, ref(source)["sha256"])
            handoff.write_text(handoff_text, encoding="utf-8")
            data["ba"]["handoff"]["sha256"] = ref(handoff)["sha256"]
            write_json(manifest, data)

            skills = docs / ".agents/skills"
            ba_kit.install(ROOT, skills, "test", project_root=docs)
            doctor = ba_kit.doctor(ROOT, skills, "test", project_root=docs)
            self.assertIn(doctor["status"], {"READY", "DEGRADED"}, doctor)
            self.assertEqual(doctor["readiness"]["scope"], "PACKAGE_CAPABILITY_ONLY")
            self.assertTrue(next(row for row in doctor["checks"] if row[0] == "Test VNext installed capability")[1])
            run = docs / ".test-kit/runs/CR-001/design-inline-ids"
            prepared = design.prepare_same_session_design(
                handoff, run, project_root=docs, skill_dir=skills / "bmad-testarch-test-design",
                delivery_path=manifest,
            )
            self.assertEqual(prepared["status"], "PREPARED")
            baseline = design.load_approved_baseline(handoff)
            expected = {f"BR-DASH-{number:03d}" for number in range(1, 7)}
            self.assertEqual(baseline.business_rule_ids, expected)
            self.assertFalse(any(identifier.startswith("BAREF:BR:") for identifier in baseline.ba_ids))
            adapter = (run / "inputs/adapter/business-rules.md").read_text(encoding="utf-8")
            for identifier in expected:
                self.assertIn(identifier, adapter)

            raw = Path(prepared["raw_output_path"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            trace = "; ".join(["FR-001", *sorted(expected)])
            raw.write_text(
                "# Test Design: Epic 1 — CR-001\n\n## Test Coverage Plan\n\n### P0\nNone\n\n### P1\n\n"
                "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |\n"
                "|---|---|---|---|---|---|\n"
                f"| 1.0-UNIT-001 | Trace approved search rules | UNIT | None | {trace} | Approved search result is observable. |\n\n"
                "### P2\nNone\n\n### P3\nNone\n",
                encoding="utf-8",
            )
            self.assertEqual(design.finalize_same_session_design(handoff, run)["status"], "DESIGN_REVIEW")

    def test_same_session_no_ids_gates_promotion_and_clean_docs(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-test-") as temp:
            docs = Path(temp) / "docs"
            init(docs, "docs")
            feature = docs / "features/CR-001"
            feature.mkdir(parents=True)
            manifest, _ = delivery_fixture(feature)
            handoff = feature / "engineering-handoff.yml"
            skills = docs / ".agents/skills"
            for kit in ("ba", "test"):
                ba_kit.install(ROOT, skills, kit, project_root=docs)
                doctor = ba_kit.doctor(ROOT, skills, kit, project_root=docs)
                if kit == "test":
                    self.assertIn(doctor["status"], {"READY", "DEGRADED"}, doctor)
                    self.assertEqual(doctor["readiness"]["scope"], "PACKAGE_CAPABILITY_ONLY")
                    self.assertTrue(next(row for row in doctor["checks"] if row[0] == "Test VNext installed capability")[1])
                else:
                    self.assertEqual(doctor["status"], "READY", doctor)
            git(docs, "add", ".")
            git(docs, "commit", "-m", "Synthetic inputs and stable team configuration")
            config = ref(docs / "_bmad/tea/config.yaml")
            run = docs / ".test-kit/runs/CR-001/design-synthetic"
            prepared = design.prepare_same_session_design(handoff, run, project_root=docs,
                       skill_dir=skills / "bmad-testarch-test-design", delivery_path=manifest)
            # This current session supplies deterministic native-profile fixture output.
            raw = Path(prepared["raw_output_path"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("# Test Design: Epic 1 — CR-001\n\n## Test Coverage Plan\n\n### P0\nNone\n\n### P1\n\n"
                           "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |\n"
                           "|---|---|---|---|---|---|\n"
                           "| 1.0-UNIT-001 | Synthetic authority | UNIT | None | BAREF:SRS:001; BAREF:BR:001 | Approved synthetic result is observable. |\n\n### P2\nNone\n\n### P3\nNone\n", encoding="utf-8")
            self.assertEqual(design.finalize_same_session_design(handoff, run)["status"], "DESIGN_REVIEW")
            baseline = design.load_approved_baseline(handoff)
            snapshot = design.load_persisted_design_snapshot(run)
            gate = receipt(snapshot, design.design_gate_input_refs(baseline, run), "DESIGN_REVIEW")
            decision = design.apply_design_decision(run, snapshot, baseline, gate, human_actor_authenticator=fixture_actor)
            self.assertTrue(decision.accepted, decision.finding)
            promoted = promotion.promote(run, feature, baseline, stage="design", human_actor_authenticator=fixture_actor)
            self.assertEqual(promoted["semantic_sha256"], snapshot.sha256)
            case_run = docs / ".test-kit/runs/CR-001/cases-synthetic"
            prepared = cases.prepare_same_session_cases(handoff, run, case_run, project_root=docs,
                       skill_dir=skills / "create-test-cases", delivery_path=manifest)
            raw = Path(prepared["raw_output_path"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_text("## TC-001 Synthetic authority\n- Mô tả: Observe approved synthetic result\n"
                           "- Tiền điều kiện: OPEN execution dependencies: [ENVIRONMENT_ACCESS] synthetic staging address.\n"
                           "- Bước và kết quả mong đợi:\n  1. Perform approved synthetic operation. → Approved synthetic result is observable.\n"
                           "- Test Data: None\n- Priority: P1\n- Trace: BAREF:SRS:001, BAREF:BR:001; 1.0-UNIT-001\n", encoding="utf-8")
            finalized = cases.finalize_same_session_cases(handoff, case_run)
            self.assertEqual(finalized.status, "CASE_REVIEW")
            case_snapshot, state = cases.load_case_review_snapshot(case_run / "canonical/canonical-testcases.json", case_run / "workflow-state.json", case_run / "canonical/semantic-payload.json")
            design_snapshot, _, _ = cases._load_persisted_design_authorization(run, baseline)
            gate = receipt(case_snapshot, cases.case_gate_input_refs(baseline, design_snapshot, run_dir=case_run), "CASE_REVIEW")
            result = cases.apply_case_gate_decision(gate, case_snapshot, design_snapshot, baseline, state,
                       workflow_dir=case_run, human_actor_authenticator=fixture_actor)
            self.assertEqual(result.status, "STOP_V1", result.finding)
            promoted = promotion.promote(case_run, feature, baseline, stage="cases", human_actor_authenticator=fixture_actor)
            self.assertEqual(promoted["semantic_sha256"], case_snapshot.sha256)
            self.assertEqual((feature / "test/cases/testcases.json").read_bytes(), case_snapshot.payload_bytes)
            self.assertEqual(config, ref(docs / "_bmad/tea/config.yaml"))
            self.assertEqual(check_runtime_ignores(docs, "docs"), "PASS")
            git(docs, "add", "features/CR-001/test")
            git(docs, "commit", "-m", "Synthetic approved testware promotion")
            self.assertEqual(git(docs, "status", "--short"), "")
            # Exact old receipts and approved bytes cannot make drift healthy.
            (feature / "ux/ux-contract.md").write_text("Changed UX", encoding="utf-8")
            with self.assertRaises(ValueError):
                design.current_delivery_refs(run)

    def test_natural_dev_router_normal_and_high_risk_boundary(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-dev-") as temp:
            root = Path(temp)
            app = root / "app"
            init(app, "app")
            git(app, "remote", "add", "origin", "https://github.com/fixture/app.git")
            (app / "selfcheck.py").write_text("assert sum([1, 2, 3]) == 6\n", encoding="utf-8")
            write_json(app / "quality-gate.json", {"checks": [
                {"name": "build", "category": "build", "argv": [sys.executable, "-m", "py_compile", "selfcheck.py"]},
                {"name": "tests", "category": "tests", "argv": [sys.executable, "selfcheck.py"]}]})
            git(app, "add", "."); git(app, "commit", "-m", "Synthetic application quality gate")
            docs = root / "feature"
            docs.mkdir()
            manifest, data = delivery_fixture(docs, False)
            data["targets"][0]["base_revision"] = git(app, "rev-parse", "HEAD")
            write_json(manifest, data)
            started = dev_router._legacy_start_from_delivery(app, manifest, "Implement synthetic local summary")
            self.assertEqual(started["route"]["risk_level"], "NORMAL")
            self.assertEqual(dev_router._legacy_start_from_delivery(app, manifest, "Resume synthetic") ["status"], "RESUMED")
            run = Path(started["run_dir"])
            inputs = dev._read_json(run / "input.json")
            dev.write_artifact(run / "spec-readiness.json", {"status": "READY_FOR_PLANNING", "business_ambiguities": []})
            dev.preflight(app)
            for filename in ("dev-plan.md", "dev-tasks.md"):
                (run / filename).write_text(_planning_text(inputs), encoding="utf-8")
            dev.validate_planning_artifacts(app)
            dev.assert_implementation_allowed(app, "normal")
            (app / "selfcheck.py").write_text("def summarize(values):\n    return sum(values)\nassert summarize([1, 2, 3]) == 6\n", encoding="utf-8")
            git(app, "add", "selfcheck.py"); git(app, "commit", "-m", "Implement synthetic local summary")
            self.assertEqual(dev.run_checks(app, "focused")["status"], "PASS")
            dev.claim_action(app, "full_reviews")
            dev.write_artifact(run / "review.json", {"change_id": inputs["change_id"], "baseline_ref": inputs["baseline_ref"],
                "full_review_performed": True, "blocking_findings": [], "followups": [], "fixture": "SYNTHETIC_REVIEW_CONTRACT_ONLY"})
            dev.record_review(app)
            with self.assertRaises(ValueError): dev.claim_action(app, "full_reviews")
            self.assertEqual(dev.run_checks(app, "fresh")["status"], "PASS")
            handoff_record = dev.prepare_handoff(app)
            handoff_record["implementation"] = {"commits": [git(app, "rev-parse", "HEAD")], "changed_components": ["selfcheck.py"]}
            handoff_record["requirements_coverage"] = [{"requirement_id": key, "status": "COVERED", "evidence": ["selfcheck.py"]}
                for key in design.load_approved_baseline(docs / "engineering-handoff.yml").ba_ids]
            dev.write_artifact(run / "dev-handoff.json", handoff_record)
            self.assertEqual(dev.finalize_handoff(app)["state"], "READY_FOR_TEST")
            self.assertEqual(check_runtime_ignores(app, "app"), "PASS")
            self.assertEqual(git(app, "status", "--short"), "")
            data["delivery_revision"] = "CR-001-DELIVERY-002"
            write_json(manifest, data)
            with self.assertRaises(ValueError): dev._load_run(app)
            # Separate throwaway target for HIGH_RISK; no Human gate is approved.
            high = root / "high"
            init(high, "app")
            handoff = docs / "engineering-handoff.yml"
            checks = inputs["checks"]
            started = dev.start_run(high, "SYNTHETIC-HIGH", "feature", "Change synthetic authorization", baseline=handoff, checks=checks)
            self.assertTrue(started["route"]["human_gate_required"])
            paused = _advance_high_risk_to_plan_gate(high, Path(started["run_dir"]))
            self.assertNotEqual(paused.returncode, 0)
            self.assertFalse(dev._read_json(Path(started["run_dir"]) / "lifecycle.json")["human_gate"]["resolved"])

    def test_execution_classification_fix_retest_and_lane_guards(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-execution-") as temp:
            root = Path(temp)
            manifest, _ = delivery_fixture(root, False)
            testcase = write_json(root / "test/cases/testcases.json", [{"test_case_id": "TC-SYNTHETIC", "steps": [{"expected_result": "3"}]}])
            receipt_ref = write_json(root / "test/approvals/receipt.json", {"fixture": "SYNTHETIC_ONLY", "decision": "APPROVE", "artifact_sha256": testcase["sha256"]})
            approved = write_json(root / "test/approvals/promotion.json", {"stage": "cases", "approval_mode": "HUMAN_AUTHENTICATED",
                                  "semantic_sha256": testcase["sha256"], "approval_receipt_sha256": receipt_ref["sha256"],
                                  "semantic_path": "../cases/testcases.json", "approval_path": "receipt.json"})
            handoff = write_json(root / "handoff.json", {"state": "READY_FOR_TEST", "implementation": {"commits": ["a" * 40]}})
            for kind in execution.DEPENDENCY_TYPES:
                state = execution.begin(approved, handoff, ref(manifest), [{"kind": kind, "status": "OPEN", "required": True}])
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    execution.transition(state, "READY", actor_role="TESTER")
            state = execution.begin(approved, handoff, ref(manifest), [])
            state = execution.transition(state, "READY", actor_role="TESTER")
            state = execution.transition(state, "EXECUTE", actor_role="TESTER")
            broken_add = lambda a, b: a - b
            observation = write_json(root / "observed.json", {"actual": str(broken_add(1, 2)), "expected": "3"})
            failed = write_json(root / "failed.json", {"status": "FAIL", "implementation_commit": "a" * 40, "testcase_id": "TC-SYNTHETIC",
                                "expected": "3", "actual": str(broken_add(1, 2)), "oracle_ref": testcase, "observation_ref": observation})
            state = execution.transition(state, "FAIL", actor_role="TESTER", evidence=failed)
            classify = write_json(root / "classification.json", {"implementation_commit": "a" * 40,
                                   "approved_expected": True, "reproducible": True, "test_environment_excluded": True})
            for classification, expected in execution.CLASSIFICATIONS.items():
                classified = execution.transition(state, "CLASSIFY", actor_role="TESTER", evidence=classify, classification=classification)
                self.assertEqual(execution.transition(classified, "ROUTE", actor_role="TESTER")["state"], expected)
            state = execution.transition(state, "CLASSIFY", actor_role="TESTER", evidence=classify, classification="DEFECT")
            state = execution.transition(state, "ROUTE", actor_role="TESTER")
            self.assertEqual(execution.validate_defect_handoff(state["defect_handoff"], state), [])
            defect_ref = write_json(root / "defect-handoff.yml", state["defect_handoff"])
            fixed_add = lambda a, b: a + b
            self.assertEqual(fixed_add(1, 2), 3)
            verified = write_json(root / "fresh-verification.json", {"actual": fixed_add(1, 2), "status": "PASS", "implementation_commit": "b" * 40})
            fix = write_json(root / "fix.json", {"implementation_commit": "b" * 40, "verification": "PASS", "verification_ref": verified, "defect_handoff_ref": defect_ref})
            state = execution.transition(state, "FIX", actor_role="DEV", evidence=fix)
            ready = write_json(root / "retest-handoff.json", {"implementation_commit": "b" * 40, "state": "READY_FOR_RETEST"})
            state = execution.transition(state, "HANDOFF", actor_role="DEV", evidence=ready)
            state = execution.transition(state, "RETEST", actor_role="TESTER")
            observation = write_json(root / "reobserved.json", {"actual": str(fixed_add(1, 2)), "expected": "3"})
            passed = write_json(root / "passed.json", {"status": "PASS", "implementation_commit": "b" * 40, "testcase_id": "TC-SYNTHETIC",
                                "expected": "3", "actual": str(fixed_add(1, 2)), "oracle_ref": testcase, "observation_ref": observation})
            with self.assertRaises(ValueError): execution.transition(state, "PASS", actor_role="DEV", evidence=passed)
            self.assertEqual(execution.transition(state, "PASS", actor_role="TESTER", evidence=passed)["state"], "VERIFIED")
            with self.assertRaises(ValueError): execution.transition(state, "FAIL", actor_role="TESTER", evidence=failed)
            repeated = json.loads(Path(failed["path"]).read_text(encoding="utf-8"))
            repeated["implementation_commit"] = "b" * 40
            reopened = write_json(root / "reopened.json", repeated)
            self.assertEqual(execution.transition(state, "FAIL", actor_role="TESTER", evidence=reopened)["state"], "REOPENED")

    def test_profile_and_installed_dev_doctor(self):
        with tempfile.TemporaryDirectory(prefix="sdlc-synthetic-profile-") as temp:
            root = Path(temp)
            profile = root / "codex-home"
            prepare_agent_profile.prepare(ROOT, profile)
            prepare_agent_profile.register(profile)
            app = root / "app"
            init(app, "app")
            purity = dev.inspect_context_purity(app, root, "benchmark", codex_home=profile)
            self.assertEqual(purity["context_purity"], "CLEAN", purity)
            installed = install_dev_kit.install(ROOT, root / "runtime-home")
            self.assertTrue((Path(installed["runtime_root"]) / "dev-kit/SKILL.md").is_file())
            # Hook contamination in the dedicated profile cannot be hidden by the global-home override.
            (profile / "config.toml").write_text('hooks = "unrelated methodology"\n', encoding="utf-8")
            purity = dev.inspect_context_purity(app, root, "benchmark", codex_home=profile)
            self.assertNotEqual(purity["context_purity"], "CLEAN")
