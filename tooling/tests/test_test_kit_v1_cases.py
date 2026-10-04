import json
import hashlib
import io
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tooling.lib import test_kit_v1 as foundation
from tooling.lib import test_kit_v1_cases as cases
from tooling.tests.codex_stub import fake_codex_on_path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "tooling/tests/fixtures/ba-v1-legacy-compat/05-engineering-handoff.yml"
DESIGN_DIR = ROOT / "benchmark/test-kit/petclinic/foundation-v1-native-profiled/canonical"
DESIGN = cases.load_design_snapshot(
    DESIGN_DIR / "canonical-test-design.json",
    ROOT / "benchmark/test-kit/petclinic/foundation-v1-native-profiled/workflow-state.json",
    DESIGN_DIR / "semantic-payload.json",
)
BENCHMARK_RAW = ROOT / "benchmark/test-kit/petclinic/katalon-create-test-cases/raw-output/test-cases.md"
PINNED_SKILL_FILES = (
    "SKILL.md",
    "references/capability-boundaries.md",
    "references/istqb-coverage.md",
    "references/manual-test-case-format.md",
    "references/requirement-analysis.md",
)


class TestKitV1CaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = foundation.load_approved_baseline(HANDOFF)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="test-kit-cases-")
        self.addCleanup(self.temp.cleanup)
        self.test_root = Path(self.temp.name)
        self.design = foundation.DesignSnapshot.create(
            DESIGN.records, artifact_id=DESIGN.artifact_id, revision=DESIGN.revision,
        )
        self.design_root, self.design_receipt = self._persist_approved_design(
            self.test_root / "production-design", self.design,
        )
        self.test_only_design_root, self.test_only_design_fixture = self._persist_test_only_design(
            self.test_root / "test-only-design", self.design,
        )

    def _persist_approved_design(self, run_dir, design):
        run_dir = Path(run_dir)
        validation = foundation.validate_design(design, self.baseline)
        state = foundation.submit_design_for_review(
            foundation.start_design_workflow(design), design, validation,
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        raw = run_dir / "raw-output/test-design.md"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("# persisted test design fixture\n", encoding="utf-8")
        foundation.persist_design_review(
            run_dir, foundation.adapt_ba_to_tea(HANDOFF), raw, design, validation, state,
        )
        receipt = self._design_receipt(snapshot=design)
        decision = foundation.apply_design_decision(
            run_dir, design, self.baseline, receipt,
            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
            validation=validation,
        )
        if not decision.accepted:
            raise AssertionError(decision.finding)
        return run_dir, receipt

    def _persist_test_only_design(self, run_dir, design):
        run_dir = Path(run_dir)
        validation = foundation.validate_design(design, self.baseline)
        state = foundation.submit_design_for_review(
            foundation.start_design_workflow(design), design, validation,
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        raw = run_dir / "raw-output/test-design.md"
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_text("# TEST_ONLY persisted test design fixture\n", encoding="utf-8")
        foundation.persist_design_review(
            run_dir, foundation.adapt_ba_to_tea(HANDOFF), raw, design, validation, state,
        )
        fixture = self.test_root / "test-only-design-receipt.json"
        fixture.write_text(json.dumps(self._test_only_fixture(design)), encoding="utf-8")
        result = foundation.apply_test_only_design_decision(
            run_dir, design, self.baseline, fixture, validation=validation,
        )
        if not result.accepted:
            raise AssertionError(result.finding)
        return run_dir, fixture

    def test_missing_design_gate_receipt_is_rejected(self):
        result = cases.validate_design_gate_receipt(
            None, self.design, self.baseline, design_workflow_dir=self.design_root,
            human_actor_authenticator=lambda *_: True,
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "MISSING_DESIGN_GATE_RECEIPT")

    def test_stale_design_hash_is_rejected(self):
        receipt = self._design_receipt(snapshot=self.design)
        receipt["artifact_sha256"] = "0" * 64
        result = cases.validate_design_gate_receipt(
            receipt, self.design, self.baseline, design_workflow_dir=self.design_root,
            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "DESIGN_RECEIPT_BINDING_MISMATCH")

    def test_stale_ba_source_hash_is_rejected(self):
        receipt = self._design_receipt(snapshot=self.design)
        receipt["input_refs"][0]["sha256"] = "0" * 64
        result = cases.validate_design_gate_receipt(
            receipt, self.design, self.baseline, design_workflow_dir=self.design_root,
            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "DESIGN_RECEIPT_BINDING_MISMATCH")

    def test_agent_authored_fake_human_receipt_is_rejected(self):
        receipt = self._design_receipt(actor_id="agent-claims-human", snapshot=self.design)
        result = cases.validate_design_gate_receipt(
            receipt, self.design, self.baseline, design_workflow_dir=self.design_root,
            human_actor_authenticator=lambda actor_id, _receipt: actor_id.startswith("human:"),
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "HUMAN_ACTOR_NOT_AUTHENTICATED")

    def test_test_only_receipt_is_accepted_only_by_test_harness(self):
        fixture = json.loads(self.test_only_design_fixture.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="test-kit-cases-") as temp:
            fixture_path = Path(temp) / "test-only-receipt.json"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            result = cases.validate_test_only_design_fixture(
                self.test_only_design_fixture, self.design, self.baseline,
                design_workflow_dir=self.test_only_design_root,
            )

        self.assertEqual(result.status, "PASS")
        self.assertTrue(result.authorization.test_only)
        production = cases.validate_design_gate_receipt(
            fixture["receipt"], self.design, self.baseline,
            design_workflow_dir=self.design_root,
            human_actor_authenticator=lambda *_: True,
        )
        self.assertEqual(production.status, "FAIL")
        self.assertEqual(production.finding.code, "TEST_ONLY_RECEIPT_NOT_PRODUCTION")

    def test_production_katalon_requires_authoritative_approved_design_state(self):
        pending_root = self.test_root / "pending-design"
        validation = foundation.validate_design(self.design, self.baseline)
        review = foundation.submit_design_for_review(
            foundation.start_design_workflow(self.design), self.design, validation,
        )
        raw = pending_root / "raw-output/test-design.md"
        raw.parent.mkdir(parents=True)
        raw.write_text("# Test Design fixture\n", encoding="utf-8")
        foundation.persist_design_review(
            pending_root, foundation.adapt_ba_to_tea(HANDOFF), raw,
            self.design, validation, review,
        )
        receipt_path = pending_root / "design-gate/revisions" / self.design.revision / "receipt.json"
        receipt_path.parent.mkdir(parents=True)
        approved_receipt_path = self.design_root / "design-gate/revisions" / self.design.revision / "receipt.json"
        receipt_path.write_bytes(approved_receipt_path.read_bytes())
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

        result = cases.validate_design_gate_receipt(
            receipt, self.design, self.baseline, design_workflow_dir=pending_root,
            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "DESIGN_APPROVAL_NOT_PERSISTED")

    def test_local_skill_pin_verifier_accepts_exact_manifest_bytes(self):
        contents = {name: f"pinned {name}\n".encode() for name in PINNED_SKILL_FILES}
        manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp) / "create-test-cases"
            self._write_skill(skill_dir, contents)
            with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                inventory = cases._verify_pinned_skill(skill_dir)

        self.assertEqual({item["path"] for item in inventory}, set(PINNED_SKILL_FILES))

    def test_local_skill_pin_verifier_rejects_crlf_transformation(self):
        content = b"line one\nline two\n"
        manifest = {name: hashlib.sha256(b"pinned\n").hexdigest() for name in PINNED_SKILL_FILES}
        manifest["SKILL.md"] = hashlib.sha256(content).hexdigest()
        contents = {name: b"pinned\n" for name in PINNED_SKILL_FILES}
        contents["SKILL.md"] = content.replace(b"\n", b"\r\n")
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp) / "create-test-cases"
            self._write_skill(skill_dir, contents)
            with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE.*SKILL.md") as error:
                    cases._verify_pinned_skill(skill_dir)

        self.assertIn(manifest["SKILL.md"], str(error.exception))
        self.assertIn(hashlib.sha256(contents["SKILL.md"]).hexdigest(), str(error.exception))
        self.assertIn(cases.KATALON_COMMIT, str(error.exception))

    def test_local_skill_pin_verifier_rejects_changed_reference_file(self):
        contents = {name: f"pinned {name}\n".encode() for name in PINNED_SKILL_FILES}
        manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
        relative = "references/istqb-coverage.md"
        contents[relative] += b"changed\n"
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp) / "create-test-cases"
            self._write_skill(skill_dir, contents)
            with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE.*istqb-coverage.md"):
                    cases._verify_pinned_skill(skill_dir)

    def test_local_skill_pin_verifier_rejects_missing_file(self):
        contents = {name: f"pinned {name}\n".encode() for name in PINNED_SKILL_FILES[:-1]}
        manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp) / "create-test-cases"
            self._write_skill(skill_dir, contents)
            with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE.*requirement-analysis.md"):
                    cases._verify_pinned_skill(skill_dir)

    def test_local_skill_pin_verifier_rejects_missing_expected_manifest_entry(self):
        contents = {name: f"pinned {name}\n".encode() for name in PINNED_SKILL_FILES}
        manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
        relative = "references/requirement-analysis.md"
        manifest.pop(relative)
        with tempfile.TemporaryDirectory() as temp:
            skill_dir = Path(temp) / "create-test-cases"
            self._write_skill(skill_dir, contents)
            with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE.*requirement-analysis.md") as error:
                    cases._verify_pinned_skill(skill_dir)

        self.assertIn(hashlib.sha256(contents[relative]).hexdigest(), str(error.exception))

    def test_production_invocation_uses_project_skill_and_never_temporary_install(self):
        contents = {name: f"pinned {name}\n".encode() for name in PINNED_SKILL_FILES}
        manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}

        class FakeProcess:
            def __init__(self):
                self.stdin = io.BytesIO()

            @staticmethod
            def poll():
                return 0

            @staticmethod
            def wait():
                return 0

        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            project_root = temp / "project"
            self._write_skill(project_root / ".agents/skills/create-test-cases", contents)
            run_dir = temp / "run"

            def start(argv, **kwargs):
                raw = run_dir / "raw-output/test-cases.md"
                raw.parent.mkdir(parents=True, exist_ok=True)
                raw.write_text("# Raw Katalon cases\n", encoding="utf-8")
                return FakeProcess()

            with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                with mock.patch.object(cases, "resolve_codex_command", return_value=cases.CodexCommand(("codex-stub",), "codex-stub", "test")):
                    with mock.patch.object(cases.subprocess, "Popen", side_effect=start) as popen:
                        with mock.patch.object(cases, "_install_pinned_skill") as temporary_install:
                            result = cases.invoke_native_katalon(
                                self.design, self.design_receipt, self.baseline, run_dir,
                                design_workflow_dir=self.design_root,
                                human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
                                project_root=project_root,
                            )

        self.assertEqual(result["status"], "ARTIFACT_COMPLETE")
        self.assertEqual(result["invocation_mode"], "PROJECT_LOCAL")
        self.assertEqual(result["installed_skill_path"], str(project_root.resolve() / ".agents/skills/create-test-cases"))
        self.assertEqual(Path(popen.call_args.kwargs["cwd"]), project_root.resolve())
        self.assertIn(str(project_root.resolve()), popen.call_args.args[0])
        temporary_install.assert_not_called()

    def test_production_pin_failure_aborts_before_invocation_or_temporary_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            with mock.patch.object(cases.subprocess, "Popen") as popen:
                with mock.patch.object(cases, "_install_pinned_skill") as temporary_install:
                    with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE"):
                        cases.invoke_native_katalon(
                            self.design, self.design_receipt, self.baseline, temp / "run",
                            design_workflow_dir=self.design_root,
                            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
                            project_root=temp / "empty-project",
                        )

        popen.assert_not_called()
        temporary_install.assert_not_called()
        self.assertFalse((temp / "run/evidence/invocation-manifest.json").exists())

    def test_test_only_runner_keeps_isolated_verified_copy(self):
        contents = {name: f"pinned {name}\n".encode() for name in PINNED_SKILL_FILES}
        manifest = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}

        def install(workspace):
            skill_dir = workspace / ".agents/skills/create-test-cases"
            self._write_skill(skill_dir, contents)
            return skill_dir, cases._verify_pinned_skill(skill_dir)

        with tempfile.TemporaryDirectory(prefix="test-kit-cases with spaces-") as temp:
            run_dir = Path(temp) / "run"
            self._prepare_native_run(run_dir)
            with fake_codex_on_path() as (fake_codex, capture_path):
                with mock.patch.dict(cases.KATALON_SKILL_FILES, manifest, clear=True):
                    with mock.patch.object(cases, "_install_pinned_skill", side_effect=install) as temporary_install:
                        result = cases._run_pinned_native_skill(
                            run_dir, run_dir / "inputs/approved-test-design.md", "gpt-6-luna",
                            self._invocation_manifest_input("TEST_ONLY"),
                            run_dir / "raw-output/test-cases.md",
                            run_dir / "evidence/invocation-manifest.json",
                            project_root=None, test_only=True,
                        )
                        resolved = cases.resolve_codex_command()
                        captured = json.loads(capture_path.read_text(encoding="utf-8"))
                        self.assertEqual(result["invocation_command"], resolved.argv(captured))
                        self.assertEqual(
                            Path(resolved.target),
                            (fake_codex.parent / "node_modules/@openai/codex/bin/codex.js").resolve(),
                        )
                        self.assertNotIn("nvm4w", " ".join(resolved.argv_prefix).casefold())
                        self.assertEqual(captured[captured.index("--model") + 1], "gpt-6-luna")

        self.assertEqual(result["invocation_mode"], "TEST_ONLY_TEMPORARY")
        self.assertEqual(result["status"], "ARTIFACT_COMPLETE")
        temporary_install.assert_called_once()

    @staticmethod
    def _write_skill(skill_dir, contents):
        for relative, content in contents.items():
            path = skill_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    @staticmethod
    def _invocation_manifest_input(receipt_mode):
        return {
            "design": {"artifact_id": "CR-001-test-design", "revision": "1", "sha256": DESIGN.sha256},
            "ba_input_refs": [],
            "execution_contract_refs": [],
            "receipt_mode": receipt_mode,
            "design_gate_receipt_evidence": None,
        }

    @staticmethod
    def _prepare_native_run(run_dir):
        (run_dir / "inputs/baseline").mkdir(parents=True)
        (run_dir / "evidence").mkdir()
        (run_dir / "inputs/approved-test-design.md").write_text("Approved design fixture", encoding="utf-8")
        (run_dir / "inputs/baseline/03-approved-business-rules.md").write_text("BR source", encoding="utf-8")
        (run_dir / "inputs/baseline/04-srs-excerpt.md").write_text("FR source", encoding="utf-8")

    def test_approved_design_adapter_preserves_ids_wording_and_oracle_scopes(self):
        auth = cases.validate_design_gate_receipt(
            self.design_receipt, self.design, self.baseline,
            design_workflow_dir=self.design_root,
            human_actor_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
        ).authorization
        adapted = cases.adapt_approved_design_to_katalon(self.design, auth, self.baseline)

        self.assertIn(self.design.records[0].design_id, adapted.markdown)
        self.assertIn(self.design.records[0].scenario_title, adapted.markdown)
        self.assertIn(self.design.records[0].expected_behavior, adapted.markdown)
        self.assertIn("BUSINESS ORACLE", adapted.markdown)
        self.assertIn("EXECUTION ORACLE", adapted.markdown)
        self.assertIn("OPEN execution dependencies: [TYPE] <detail>", adapted.markdown)
        self.assertEqual(adapted.design_sha256, self.design.sha256)
        self.assertIn("FR-001", adapted.markdown)
        self.assertIn("BR-014", adapted.markdown)

    def test_native_prompt_requires_nonnull_td_coverage_and_exact_utf8_file_write(self):
        prompt = cases._invocation_prompt(
            Path("input.md"), Path("output.md"), "gpt-6-luna",
            skill_dir=Path("skill"), baseline_dir=Path("baseline"), project_root=Path("project"),
        )

        self.assertIn("Every Test Design row with non-null expected behavior needs testcase coverage", prompt)
        self.assertIn("Do not prefix design IDs with TD", prompt)
        self.assertIn("OPEN execution dependencies: [TYPE] <detail>", prompt)
        self.assertIn("Write the completed output with Python 3 pathlib", prompt)

    def test_null_outcome_design_row_is_deferred_and_cannot_be_asserted(self):
        unknown = foundation.CanonicalTestDesign(
            "TD-999",
            ("Test Design", "P1"),
            "Unresolved duration upper bound",
            None,
            ("BR-005",),
            (foundation.OpenQuestion("BR-005", self.baseline.unknown_clauses["BR-005"]),),
        )
        design = foundation.DesignSnapshot.create((*DESIGN.records, unknown), artifact_id="CR-001-test", revision="1")
        auth = self._test_authorization(design)
        adapted = cases.adapt_approved_design_to_katalon(design, auth, self.baseline)
        raw = self._native_case(
            requirement_refs="BR-005", design_refs="TD-999",
            expected="Maximum duration is 30 minutes.",
        )
        normalized = cases.normalize_katalon_markdown(raw, design, self.baseline)
        validation = cases.validate_testcases(normalized.snapshot, design, self.baseline)

        self.assertIn("DEFERRED / UNKNOWN", adapted.markdown)
        self.assertNotIn("## TD-999", adapted.markdown)
        self.assertIn("DEFERRED_TD_ASSERTION", {finding.code for finding in validation.findings})
        self.assertIn("UNKNOWN_ASSERTION_LEAK", {finding.code for finding in validation.findings})

    def test_backed_execution_oracle_cannot_resolve_deferred_ba_business_rule(self):
        unknown = foundation.CanonicalTestDesign(
            "TD-MAX", ("Test Design", "P1"), "Maximum duration awaiting BA decision", None,
            ("BR-005",), (foundation.OpenQuestion("BR-005", self.baseline.unknown_clauses["BR-005"]),),
        )
        design = foundation.DesignSnapshot.create((*DESIGN.records, unknown), artifact_id="CR-001-test", revision="1")
        adapted = cases.adapt_approved_design_to_katalon(design, self._test_authorization(design), self.baseline)
        self.assertIn("DEFERRED / UNKNOWN", adapted.markdown)
        self.assertIn("TD-MAX", adapted.markdown)
        self.assertNotIn("## TD-MAX", adapted.markdown)
        execution_ref = self._execution_ref()
        dependency = cases.ExecutionDependency("Maximum-duration execution fixture", "SEMANTIC_ORACLE", "RESOLVED", execution_ref["id"])
        case = cases.CanonicalTestcase(
            "TC-999", "Check maximum duration", "Assert the maximum duration", "A maximum-duration oracle is available.", None,
            (cases.CaseStep("Create an appointment at the maximum", None, "Maximum duration is 60 minutes."),), "P1",
            ("BR-005",), ("TD-MAX",), (dependency,),
        )
        snapshot = cases.CaseSnapshot.create((case,), artifact_id="CR-001-cases", revision="1")

        validation = cases.validate_testcases(
            snapshot, design, self.baseline,
            execution_contract_refs=(execution_ref,),
            execution_oracle_authenticator=lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id),
        )

        codes = {finding.code for finding in validation.findings}
        self.assertEqual(validation.status, "FAIL")
        self.assertIn("DEFERRED_TD_ASSERTION", codes)
        self.assertIn("UNKNOWN_ASSERTION_LEAK", codes)

    def test_benchmark_katalon_profile_is_accepted(self):
        normalized = cases.normalize_katalon_markdown(
            BENCHMARK_RAW.read_text(encoding="utf-8"), DESIGN, self.baseline, source_path=str(BENCHMARK_RAW)
        )

        self.assertEqual(normalized.status, "NORMALIZED")
        self.assertEqual(normalized.profile, "benchmark-v1")
        self.assertEqual(len(normalized.snapshot.records), 27)
        self.assertEqual(normalized.snapshot.records[0].test_case_id, "TC-001")

    def test_normalization_maps_each_field_to_raw_line_evidence(self):
        normalized = cases.normalize_katalon_markdown(self._native_case(), DESIGN, self.baseline, source_path="native.md")
        sources = normalized.snapshot.field_sources["TC-001"]

        self.assertEqual(set(sources), set(cases.CASE_SEMANTIC_FIELDS))
        self.assertTrue(all(source.line is not None and source.line > 0 for source in sources.values()))

    def test_trace_parser_accepts_domain_scoped_ba_ids(self):
        refs = cases._parse_explicit_refs(
            "FR-001; BR-WED-011; BR-AUTH-004",
            case_id="TC-001",
            field="Trace",
        )
        self.assertEqual(refs, ["FR-001", "BR-WED-011", "BR-AUTH-004"])

    def test_native_katalon_profile_is_accepted(self):
        normalized = cases.normalize_katalon_markdown(
            self._native_case(), DESIGN, self.baseline, source_path="native.md"
        )

        self.assertEqual(normalized.status, "NORMALIZED")
        self.assertEqual(normalized.profile, "native-v1")
        self.assertEqual(normalized.snapshot.records[0].steps[0].action, "Open appointment capability.")

    def test_native_trace_preserves_single_level_tea_id(self):
        normalized = cases.normalize_katalon_markdown(
            self._native_case(design_refs="1-INT-001"), DESIGN, self.baseline, source_path="single-level-id.md",
        )

        self.assertEqual(normalized.status, "NORMALIZED")
        self.assertEqual(normalized.snapshot.records[0].test_design_refs, ("1-INT-001",))

    def test_unknown_raw_profile_returns_cannot_normalize_without_cases(self):
        raw = self._benchmark_case().replace("Objective:", "Intent:")
        normalized = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline, source_path="changed.md")

        self.assertEqual(normalized.status, "CANNOT_NORMALIZE")
        self.assertIsNone(normalized.snapshot)
        self.assertEqual(normalized.evidence[0].sha256, cases.sha256_text(raw))

    def test_unknown_tc_block_is_not_silently_dropped_but_trailing_prose_is_allowed(self):
        raw = self._native_case()
        unknown = cases.normalize_katalon_markdown(
            raw + "\n## TC-999 Unrecognized extra case\n\nThis case must not disappear.\n",
            DESIGN, self.baseline, source_path="extra-case.md",
        )
        prose = cases.normalize_katalon_markdown(
            raw + "\nGeneration completed; no further testcase rows follow.\n",
            DESIGN, self.baseline, source_path="trailing-prose.md",
        )

        self.assertEqual(unknown.status, "CANNOT_NORMALIZE")
        self.assertIsNone(unknown.snapshot)
        self.assertEqual(unknown.findings[0].line, 14)
        self.assertEqual(prose.status, "NORMALIZED")

    def test_exact_tc_design_refs_and_deferred_metadata_do_not_look_like_extra_cases(self):
        active = self._design("TC-001", "Appointment is created in Scheduled.", ("FR-001",))
        deferred = foundation.CanonicalTestDesign(
            "TC-002", ("Test Design", "P2"), "Deferred maximum duration", None,
            ("BR-005",), (foundation.OpenQuestion("BR-005", self.baseline.unknown_clauses["BR-005"]),),
        )
        design = foundation.DesignSnapshot.create(
            (*active.records, deferred), artifact_id="CR-001-collision-design", revision="1",
        )
        raw = self._native_case(requirement_refs="FR-001", design_refs="TC-001") + (
            "\n## Deferred / UNKNOWN\n\n"
            "- TC-002: Maximum duration remains deferred; no expected behavior is approved.\n"
        )

        normalized = cases.normalize_katalon_markdown(raw, design, self.baseline)
        unknown = cases.normalize_katalon_markdown(
            raw.replace("TC-002: Maximum duration", "TC-999: Maximum duration"), design, self.baseline,
        )

        self.assertEqual(normalized.status, "NORMALIZED", normalized.findings)
        self.assertEqual(normalized.snapshot.records[0].test_design_refs, ("TC-001",))
        self.assertEqual(unknown.status, "CANNOT_NORMALIZE")
        self.assertIn("TC-999", unknown.findings[0].message)

    def test_unheaded_tc_shaped_block_is_not_silently_dropped(self):
        raw = self._native_case() + "\n## Test Case TC-999 Unrecognized extra case\n\n- Mô tả: assert an unapproved outcome.\n"
        result = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline, source_path="unheaded-case.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertEqual(result.findings[0].path, "unheaded-case.md")
        self.assertEqual(result.findings[0].line, 14)

    def test_katalon_manifest_hash_is_checked_before_normalization(self):
        run_dir = self.test_root / "raw-integrity"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_path.write_text(self._native_case(), encoding="utf-8")
        actual = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": "0" * 64}

        mismatch = cases._finish_case_integration(
            manifest, self.design, self.baseline, run_dir,
            execution_contract_refs=(), artifact_id="TC-SET", revision="1",
        )

        self.assertEqual(mismatch.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        manifest["raw_output_sha256"] = actual
        matched = cases._finish_case_integration(
            manifest, self.design, self.baseline, run_dir / "matching",
            execution_contract_refs=(), artifact_id="TC-SET", revision="1",
        )
        self.assertNotEqual(matched.status, "RAW_OUTPUT_INTEGRITY_FAILURE")

    def test_katalon_raw_mutation_after_verification_cannot_change_parsed_or_persisted_bytes(self):
        run_dir = self.test_root / "raw-toctou"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment")
        raw_path.write_text(raw, encoding="utf-8")
        raw_bytes = raw_path.read_bytes()
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()
        manifest = {
            "raw_output_path": str(raw_path),
            "raw_output_sha256": raw_sha,
        }
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004"))
        read_verified = cases._read_verified_katalon_raw
        read_count = 0
        changed = raw.replace("## TC-001 Create appointment", "## TC-001 Changed after verification")

        def mutate_after_verified_read(current_manifest):
            nonlocal read_count
            verified = read_verified(current_manifest)
            read_count += 1
            if read_count == 1:
                raw_path.write_text(changed, encoding="utf-8")
            return verified

        with mock.patch.object(cases, "_read_verified_katalon_raw", side_effect=mutate_after_verified_read):
            result = cases._finish_case_integration(
                manifest, design, self.baseline, run_dir,
                execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(result.status, "CASE_REVIEW")
        self.assertEqual(read_count, 1)
        self.assertEqual(result.normalization.snapshot.records[0].name, "Create appointment")
        verified_copy = run_dir / "evidence/verified-katalon-output.md"
        self.assertEqual(verified_copy.read_bytes(), raw_bytes)
        self.assertEqual(result.normalization.snapshot.evidence[0].path, str(verified_copy.resolve()))
        self.assertEqual(result.normalization.snapshot.evidence[0].sha256, raw_sha)
        self.assertEqual(result.normalization.snapshot.evidence[0].sha256, manifest["raw_output_sha256"])
        self.assertEqual(
            (
                hashlib.sha256(raw_bytes).hexdigest(), raw_sha, manifest["raw_output_sha256"],
                result.normalization.snapshot.evidence[0].sha256,
                hashlib.sha256(verified_copy.read_bytes()).hexdigest(),
            ),
            (raw_sha,) * 5,
        )
        self.assertEqual(json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))["state"], "CASE_REVIEW")
        self.assertNotEqual(raw_path.read_bytes(), verified_copy.read_bytes())

    def test_katalon_mutated_evidence_copy_is_rematerialized_from_captured_bytes(self):
        run_dir = self.test_root / "verified-copy-toctou"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        raw_sha = hashlib.sha256(raw_bytes).hexdigest()
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": raw_sha}
        verified_copy = run_dir / "evidence/verified-katalon-output.md"
        normalize = cases.normalize_katalon_output_bytes
        parsed_bytes = []
        parsed_names = []

        def mutate_copy_then_parse(raw_source, design, baseline, **kwargs):
            parsed_bytes.append(raw_source)
            verified_copy.parent.mkdir(parents=True, exist_ok=True)
            verified_copy.write_bytes(raw_bytes.replace(
                b"## TC-001 Create appointment", b"## TC-001 Mutated after verification",
            ))
            normalized = normalize(raw_source, design, baseline, **kwargs)
            parsed_names.extend(case.name for case in normalized.snapshot.records)
            return normalized

        with mock.patch.object(cases, "normalize_katalon_output_bytes", side_effect=mutate_copy_then_parse):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")), self.baseline, run_dir,
                execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(parsed_bytes, [raw_bytes])
        self.assertEqual(parsed_names, ["Create appointment"])
        self.assertEqual(result.status, "CASE_REVIEW")
        self.assertEqual(verified_copy.read_bytes(), raw_bytes)
        self.assertEqual(result.normalization.snapshot.evidence[0].sha256, raw_sha)
        self.assertEqual(hashlib.sha256(verified_copy.read_bytes()).hexdigest(), manifest["raw_output_sha256"])
        self.assertEqual(json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))["state"], "CASE_REVIEW")

    def _prepare_raw_case_review(self, run_dir, raw_bytes):
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004"))
        normalization = cases.normalize_katalon_output_bytes(
            raw_bytes, design, self.baseline,
            source_path=run_dir / "evidence/verified-katalon-output.md",
            artifact_id="TC-SET", revision="1",
        )
        self.assertEqual(normalization.status, "NORMALIZED", normalization.findings)
        validation = cases.validate_testcases(normalization.snapshot, design, self.baseline)
        self.assertEqual(validation.status, "PASS", validation.findings)
        workflow = cases.submit_cases_for_review(
            cases.start_case_workflow(normalization.snapshot), normalization.snapshot, validation,
        )
        return normalization, validation, workflow

    def test_persist_case_review_replaces_mutated_evidence_with_captured_bytes(self):
        run_dir = self.test_root / "persist-rematerializes-evidence"
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        normalization, validation, workflow = self._prepare_raw_case_review(run_dir, raw_bytes)
        evidence_path = Path(normalization.snapshot.evidence[0].path)
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_bytes(raw_bytes.replace(
            b"## TC-001 Create appointment", b"## TC-001 Mutated before persistence",
        ))

        cases.persist_case_review(
            run_dir, normalization, validation, workflow,
            raw_evidence_bytes=raw_bytes, expected_raw_output_sha256=raw_hash,
        )

        self.assertEqual(evidence_path.read_bytes(), raw_bytes)
        self.assertEqual(hashlib.sha256(evidence_path.read_bytes()).hexdigest(), raw_hash)
        self.assertEqual(normalization.snapshot.evidence[0].sha256, raw_hash)
        self.assertEqual(json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))["state"], "CASE_REVIEW")

    def test_mutation_at_old_final_check_boundary_is_overwritten_inside_persistence(self):
        run_dir = self.test_root / "persist-boundary-race"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": raw_hash}
        verified_path = run_dir / "evidence/verified-katalon-output.md"
        submit = cases.submit_cases_for_review

        def mutate_after_validation(*args, **kwargs):
            verified_path.parent.mkdir(parents=True, exist_ok=True)
            verified_path.write_bytes(raw_bytes.replace(
                b"## TC-001 Create appointment", b"## TC-001 Mutated at persistence boundary",
            ))
            return submit(*args, **kwargs)

        with mock.patch.object(cases, "submit_cases_for_review", side_effect=mutate_after_validation):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, run_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(result.status, "CASE_REVIEW")
        self.assertEqual(verified_path.read_bytes(), raw_bytes)
        self.assertEqual(result.normalization.snapshot.evidence[0].sha256, raw_hash)
        self.assertEqual(hashlib.sha256(verified_path.read_bytes()).hexdigest(), manifest["raw_output_sha256"])
        self.assertEqual(json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))["state"], "CASE_REVIEW")

    def test_evidence_mutation_after_persistence_verification_blocks_commit(self):
        run_dir = self.test_root / "persist-after-verification-race"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": raw_hash}
        write_authoritative = cases._write_authoritative_raw_evidence

        def mutate_after_persisted_hash(path, captured, expected_hash):
            write_authoritative(path, captured, expected_hash)
            path.write_bytes(captured.replace(
                b"## TC-001 Create appointment", b"## TC-001 Changed after persistence verification",
            ))

        with mock.patch.object(cases, "_write_authoritative_raw_evidence", side_effect=mutate_after_persisted_hash):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, run_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        self.assertFalse((run_dir / "canonical/canonical-testcases.json").exists())
        self.assertFalse((run_dir / "workflow-state.json").exists())

    def test_probe_a_mutation_after_evidence_write_is_checked_after_workflow_write_and_rolled_back(self):
        run_dir = self.test_root / "postcommit-probe-a"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": hashlib.sha256(raw_bytes).hexdigest()}
        write_evidence = cases._write_authoritative_raw_evidence
        original_write = cases._write_if_same_or_absent
        workflow_writes = []

        def mutate_after_initial_evidence_check(path, captured, expected_hash):
            write_evidence(path, captured, expected_hash)
            path.write_bytes(captured.replace(
                b"## TC-001 Create appointment", b"## TC-001 Mutated after initial check",
            ))

        def record_workflow_write(path, content):
            original_write(path, content)
            if path == run_dir / "workflow-state.json":
                workflow_writes.append(path.is_file())

        with mock.patch.object(cases, "_write_authoritative_raw_evidence", side_effect=mutate_after_initial_evidence_check), \
             mock.patch.object(cases, "_write_if_same_or_absent", side_effect=record_workflow_write):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, run_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(workflow_writes, [True])
        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        self.assertFalse((run_dir / "canonical/canonical-testcases.json").exists())
        self.assertFalse((run_dir / "workflow-state.json").exists())
        self.assertFalse((run_dir / "case-gate/receipt.json").exists())
        self.assertFalse((run_dir / "evidence/verified-katalon-output.md").exists())

    def test_probe_c_mutation_after_canonical_write_is_detected_after_workflow_and_rolled_back(self):
        run_dir = self.test_root / "postcommit-probe-c"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": hashlib.sha256(raw_bytes).hexdigest()}
        original_write = cases._write_if_same_or_absent
        workflow_writes = []

        def mutate_after_canonical_write(path, content):
            original_write(path, content)
            if path.name == "canonical-testcases.json":
                verified_path = run_dir / "evidence/verified-katalon-output.md"
                verified_path.write_bytes(raw_bytes.replace(
                    b"## TC-001 Create appointment", b"## TC-001 Mutated after canonical write",
                ))
            if path == run_dir / "workflow-state.json":
                workflow_writes.append(path.is_file())

        with mock.patch.object(cases, "_write_if_same_or_absent", side_effect=mutate_after_canonical_write):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, run_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(workflow_writes, [True])
        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        self.assertFalse((run_dir / "canonical/canonical-testcases.json").exists())
        self.assertFalse((run_dir / "workflow-state.json").exists())
        self.assertFalse((run_dir / "evidence/verified-katalon-output.md").exists())

    def test_probe_d_mutation_after_workflow_write_is_detected_and_rolled_back(self):
        run_dir = self.test_root / "postcommit-probe-d"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": hashlib.sha256(raw_bytes).hexdigest()}
        original_write = cases._write_if_same_or_absent
        workflow_writes = []

        def mutate_after_workflow_write(path, content):
            original_write(path, content)
            if path == run_dir / "workflow-state.json":
                workflow_writes.append(path.is_file())
                verified_path = run_dir / "evidence/verified-katalon-output.md"
                verified_path.write_bytes(raw_bytes.replace(
                    b"## TC-001 Create appointment", b"## TC-001 Mutated after workflow write",
                ))

        with mock.patch.object(cases, "_write_if_same_or_absent", side_effect=mutate_after_workflow_write):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, run_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(workflow_writes, [True])
        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        self.assertFalse((run_dir / "canonical/canonical-testcases.json").exists())
        self.assertFalse((run_dir / "workflow-state.json").exists())

    def test_rollback_preserves_preexisting_older_review_revision(self):
        root = self.test_root / "rollback-preserves-old"
        old_dir = root / "revisions/1"
        new_dir = root / "revisions/2"
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_hash = hashlib.sha256(raw_bytes).hexdigest()
        old_normalization, old_validation, old_state = self._prepare_raw_case_review(old_dir, raw_bytes)
        old_manifest = {"raw_output_path": "source.md", "raw_output_sha256": raw_hash}
        (old_dir / "evidence").mkdir(parents=True, exist_ok=True)
        (old_dir / "evidence/invocation-manifest.json").write_text(json.dumps(old_manifest), encoding="utf-8")
        cases.persist_case_review(
            old_dir, old_normalization, old_validation, old_state,
            raw_evidence_bytes=raw_bytes, expected_raw_output_sha256=raw_hash,
        )
        old_paths = (
            old_dir / "canonical/canonical-testcases.json",
            old_dir / "canonical/semantic-payload.json",
            old_dir / "workflow-state.json",
            old_dir / "evidence/verified-katalon-output.md",
        )
        old_contents = tuple(path.read_bytes() for path in old_paths)
        old_load_args = (old_paths[0], old_paths[2], old_paths[1])
        old_snapshot_before, old_state_before = cases.load_case_review_snapshot(*old_load_args)
        raw_path = root / "source/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_path.write_bytes(raw_bytes)
        new_manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": raw_hash}
        original_write = cases._write_if_same_or_absent

        def fail_new_revision_after_workflow(path, content):
            original_write(path, content)
            if path == new_dir / "workflow-state.json":
                (new_dir / "evidence/verified-katalon-output.md").write_bytes(
                    raw_bytes.replace(b"## TC-001 Create appointment", b"## TC-001 Mutated revision 2"),
                )

        with mock.patch.object(cases, "_write_if_same_or_absent", side_effect=fail_new_revision_after_workflow):
            result = cases._finish_case_integration(
                new_manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, new_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="2",
            )

        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertEqual(tuple(path.read_bytes() for path in old_paths), old_contents)
        self.assertEqual(json.loads((old_dir / "workflow-state.json").read_text(encoding="utf-8"))["state"], "CASE_REVIEW")
        old_snapshot_after, old_state_after = cases.load_case_review_snapshot(*old_load_args)
        self.assertEqual(old_snapshot_after.sha256, old_snapshot_before.sha256)
        self.assertEqual(old_state_after.state, old_state_before.state)
        self.assertFalse((new_dir / "canonical/canonical-testcases.json").exists())
        self.assertFalse((new_dir / "workflow-state.json").exists())

    def test_case_review_loader_rejects_postcommit_katalon_evidence_tampering(self):
        run_dir = self.test_root / "postcommit-tamper-loader"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        manifest = {"raw_output_path": str(raw_path), "raw_output_sha256": hashlib.sha256(raw_bytes).hexdigest()}
        (run_dir / "evidence").mkdir(parents=True)
        (run_dir / "evidence/invocation-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = cases._finish_case_integration(
            manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
            self.baseline, run_dir, execution_contract_refs=(), artifact_id="TC-SET", revision="1",
        )
        self.assertEqual(result.status, "CASE_REVIEW")
        load_args = (
            run_dir / "canonical/canonical-testcases.json",
            run_dir / "workflow-state.json",
            run_dir / "canonical/semantic-payload.json",
        )
        cases.load_case_review_snapshot(*load_args)

        evidence_path = run_dir / "evidence/verified-katalon-output.md"
        evidence_path.write_bytes(raw_bytes.replace(
            b"## TC-001 Create appointment", b"## TC-001 Tampered after commit",
        ))
        with self.assertRaisesRegex(cases.RawOutputIntegrityError, "authoritative Katalon evidence"):
            cases.load_case_review_snapshot(*load_args)
        gate = cases.apply_case_gate_decision(
            {}, result.normalization.snapshot.project("IN_REVIEW"),
            self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
            self.baseline, result.workflow, workflow_dir=run_dir,
            human_actor_authenticator=lambda *_: foundation.AuthenticatedHumanActorContext("human:test"),
            validation=result.validation, execution_contract_refs=(),
        )
        self.assertEqual(gate.status, "REJECTED")
        self.assertEqual(gate.finding.code, "RAW_OUTPUT_INTEGRITY_FAILURE")

    def test_authoritative_evidence_persistence_failure_leaves_no_snapshot_or_workflow(self):
        run_dir = self.test_root / "persist-evidence-failure"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw_bytes = self._native_case(
            requirement_refs="FR-001; BR-004", design_refs="TD-001",
            expected="Appointment is created in Scheduled.",
            preconditions="A valid Pet exists. OPEN: interface action and saved-state observation are not supplied.",
        ).replace("Open appointment capability", "Choose an appointment").encode("utf-8")
        raw_path.write_bytes(raw_bytes)
        manifest = {
            "raw_output_path": str(raw_path),
            "raw_output_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        }

        with mock.patch.object(cases, "_write_authoritative_raw_evidence", side_effect=OSError("injected evidence failure")):
            result = cases._finish_case_integration(
                manifest, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001", "BR-004")),
                self.baseline, run_dir,
                execution_contract_refs=(), artifact_id="TC-SET", revision="1",
            )

        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        self.assertFalse((run_dir / "canonical/canonical-testcases.json").exists())
        self.assertFalse((run_dir / "workflow-state.json").exists())

    def test_katalon_bytes_changed_before_initial_verification_fail_without_transition(self):
        run_dir = self.test_root / "raw-before-verification"
        raw_path = run_dir / "raw-output/test-cases.md"
        raw_path.parent.mkdir(parents=True)
        raw = self._native_case()
        raw_path.write_text(raw, encoding="utf-8")
        expected_hash = hashlib.sha256(raw_path.read_bytes()).hexdigest()
        raw_path.write_text(raw.replace("Create appointment", "Changed before verification"), encoding="utf-8")
        result = cases._finish_case_integration(
            {"raw_output_path": str(raw_path), "raw_output_sha256": expected_hash},
            self.design, self.baseline, run_dir,
            execution_contract_refs=(), artifact_id="TC-SET", revision="1",
        )

        self.assertEqual(result.status, "RAW_OUTPUT_INTEGRITY_FAILURE")
        self.assertIsNone(result.normalization.snapshot)
        self.assertFalse((run_dir / "canonical/semantic-payload.json").exists())
        self.assertFalse((run_dir / "workflow-state.json").exists())

    def test_case_level_test_data_is_never_guessed_into_steps(self):
        normalized = cases.normalize_katalon_markdown(self._benchmark_case(), DESIGN, self.baseline)
        record = normalized.snapshot.records[0]

        self.assertEqual(record.test_data, "Pet A; Veterinarian B")
        self.assertIsNone(record.steps[0].test_data)
        self.assertIsNone(record.steps[1].test_data)

    def test_invalid_td_and_ba_refs_fail_validation(self):
        raw = self._native_case(requirement_refs="FR-999", design_refs="TD-999")
        normalized = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline)
        result = cases.validate_testcases(normalized.snapshot, DESIGN, self.baseline)
        codes = {finding.code for finding in result.findings}

        self.assertEqual(result.status, "FAIL")
        self.assertIn("ORPHAN_BA_REF", codes)
        self.assertIn("ORPHAN_TD_REF", codes)

    def test_case_validator_binds_records_to_immutable_semantic_bytes(self):
        raw = cases.normalize_katalon_markdown(self._native_case(), DESIGN, self.baseline)
        changed = replace(raw.snapshot.records[0], objective="silently changed objective")
        forged = replace(raw.snapshot, records=(changed,))

        validation = cases.validate_testcases(forged, DESIGN, self.baseline)

        self.assertEqual(validation.status, "FAIL")
        self.assertIn("SNAPSHOT_RECORD_MISMATCH", {finding.code for finding in validation.findings})

    def test_case_result_conflicting_with_ba_and_design_is_blocked(self):
        design = self._design("TD-VISIT", "Exactly one Visit is created after completion.", ("BR-010",))
        case = cases.CanonicalTestcase(
            "TC-001", "Complete appointment", "Check completion", "A Scheduled appointment exists.",
            "A", (cases.CaseStep("Complete appointment", None, "Two Visits are created."),), "P1",
            ("BR-010",), ("TD-VISIT",), (),
        )
        result = cases.validate_testcases(cases.CaseSnapshot.create((case,), artifact_id="CR-001", revision="1"), design, self.baseline)

        self.assertEqual(result.status, "FAIL")
        self.assertIn("EXPECTED_RESULT_AUTHORITY_CONFLICT", {finding.code for finding in result.findings})

    def test_explicit_material_execution_dependency_is_retained(self):
        raw = self._native_case(
            preconditions="The editable field must be selected by the approved interface contract."
        )
        normalized = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline)
        record = normalized.snapshot.records[0]

        self.assertTrue(record.execution_dependencies)
        self.assertEqual(record.execution_dependencies[0].kind, "IMPLEMENTATION_LOCATOR")
        self.assertEqual(record.execution_dependencies[0].status, "OPEN")
        self.assertIn("editable field", record.execution_dependencies[0].need)

    def test_open_marker_in_preconditions_becomes_material_execution_dependency(self):
        raw = self._native_case(
            preconditions="Clinic Staff actor. OPEN: route and persisted-state observation are not specified."
        )
        normalized = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline)

        self.assertEqual(normalized.status, "NORMALIZED")
        dependency = normalized.snapshot.records[0].execution_dependencies[0]
        self.assertEqual(dependency.need, "route and persisted-state observation are not specified.")
        self.assertEqual(dependency.kind, "OBSERVABILITY")
        self.assertEqual(dependency.status, "OPEN")

    def test_open_execution_dependencies_marker_in_preconditions_is_parsed(self):
        raw = self._native_case(
            preconditions="Clinic Staff actor. OPEN execution dependencies: fixture and observation mapping."
        )
        normalized = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline)

        self.assertEqual(normalized.status, "NORMALIZED")
        self.assertEqual(
            normalized.snapshot.records[0].execution_dependencies[0].need,
            "fixture and observation mapping.",
        )
    def test_open_execution_dependency_label_is_retained(self):
        raw = self._native_case(preconditions="OPEN execution dependencies: UI action and observation mapping remain unresolved.")
        normalized = cases.normalize_katalon_markdown(raw, DESIGN, self.baseline)

        self.assertTrue(normalized.snapshot.records[0].execution_dependencies)
        self.assertIn("UI action and observation mapping", normalized.snapshot.records[0].execution_dependencies[0].need)

    def test_material_open_dependency_blocks_case_gate_approval(self):
        design = self.design
        active_design = tuple(row.design_id for row in design.records if row.expected_behavior is not None)
        ba_refs = tuple(sorted({ref for row in design.records if row.expected_behavior is not None for ref in row.requirement_refs}))
        dependency = cases.ExecutionDependency("Approved interface action mapping is required", "SEMANTIC_ORACLE", "OPEN", None)
        case = cases.CanonicalTestcase(
            "TC-001", "Create appointment", "Check creation", "A valid Pet exists.", "Pet A",
            (cases.CaseStep("Create an appointment", None, "Appointment is Scheduled."),), "P1",
            ba_refs, active_design, (dependency,),
        )
        snapshot = cases.CaseSnapshot.create((case,), artifact_id="CR-001-cases", revision="1")
        validation = cases.validate_testcases(snapshot, design, self.baseline)
        workflow = cases.submit_cases_for_review(
            cases.start_case_workflow(snapshot), snapshot, validation,
            design_gate_receipt_mode="HUMAN_AUTHENTICATED",
            design_gate_receipt_evidence=self._design_evidence(test_only=False),
            input_refs=cases.case_gate_input_refs(self.baseline, design),
        )
        snapshot = snapshot.project("IN_REVIEW")
        receipt = self._case_receipt(snapshot, design, decision="APPROVE")
        result = cases.validate_case_gate_receipt(
            receipt, snapshot, design, self.baseline, workflow,
            human_actor_authenticator=lambda actor_id, _receipt: cases.AuthenticatedHumanActorContext(actor_id), validation=validation,
        )

        self.assertEqual(validation.status, "PASS")
        self.assertEqual(workflow.state, "CASE_REVIEW")
        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "OPEN_SEMANTIC_ORACLE")
        self.assertNotEqual(workflow.review_status, "APPROVED")

    def test_validator_pass_submits_only_to_case_review(self):
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",))
        case = cases.CanonicalTestcase(
            "TC-001", "Create appointment", "Check creation", "A valid Pet exists.", None,
            (cases.CaseStep("Create an appointment", None, "Appointment is Scheduled."),), "P1",
            ("FR-001",), ("TD-001",), (),
        )
        snapshot = cases.CaseSnapshot.create((case,), artifact_id="CR-001-cases", revision="1")
        validation = cases.validate_testcases(snapshot, design, self.baseline)
        workflow = cases.submit_cases_for_review(
            cases.start_case_workflow(snapshot), snapshot, validation,
            design_gate_receipt_mode="HUMAN_AUTHENTICATED",
            input_refs=cases.case_gate_input_refs(self.baseline, design),
        )

        self.assertEqual(validation.status, "PASS")
        self.assertEqual(workflow.state, "CASE_REVIEW")
        self.assertEqual(workflow.review_status, "IN_REVIEW")
        self.assertEqual(snapshot.records[0].review_status, "DRAFT")
        self.assertNotIn("APPROVED_TESTWARE", {workflow.state, snapshot.records[0].review_status})

    def test_duplicate_case_ids_and_resolution_refs_are_blocking(self):
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",))
        dependency = cases.ExecutionDependency("Approved execution mapping", "SEMANTIC_ORACLE", "RESOLVED", "EXEC-1")
        record = cases.CanonicalTestcase(
            "TC-001", "Create", "Check", "No setup required.", None,
            (cases.CaseStep("Create", None, "Appointment is Scheduled."),), "P1",
            ("FR-001",), ("TD-001",), (dependency,),
        )
        snapshot = cases.CaseSnapshot.create((record, record), artifact_id="CR-001-cases", revision="1")
        result = cases.validate_testcases(snapshot, design, self.baseline, execution_contract_refs=())
        codes = {finding.code for finding in result.findings}

        self.assertIn("DUPLICATE_TC_ID", codes)
        self.assertIn("INVALID_EXECUTION_RESOLUTION_REF", codes)

    def test_execution_oracle_requires_current_backed_human_approval(self):
        ref = self._execution_ref()
        snapshot = self._resolved_snapshot(ref)
        auth = lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id)
        valid = cases.validate_testcases(
            snapshot, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",)),
            self.baseline, execution_contract_refs=(ref,), execution_oracle_authenticator=auth,
        )
        self.assertEqual(valid.status, "PASS", [finding.message for finding in valid.findings])

        for changed in (
            {key: value for key, value in ref.items() if key != "approval_evidence"},
            {**ref, "approved": False},
            {"id": "EXEC:synthetic", "revision": "1", "sha256": "a" * 64, "approved": True},
        ):
            result = cases.validate_testcases(
                snapshot, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",)),
                self.baseline, execution_contract_refs=(changed,), execution_oracle_authenticator=auth,
            )
            self.assertIn("EXECUTION_ORACLE_PROVENANCE_INVALID", {item.code for item in result.findings})

        evidence_path = Path(ref["approval_evidence"]["path"])
        approval = json.loads(evidence_path.read_text(encoding="utf-8"))
        approval["source_revision"] = "0"
        stale_bytes = (json.dumps(approval, indent=2) + "\n").encode("utf-8")
        evidence_path.write_bytes(stale_bytes)
        stale_ref = {
            **ref,
            "approval_evidence": {"path": str(evidence_path), "sha256": hashlib.sha256(stale_bytes).hexdigest()},
        }
        stale = cases.validate_testcases(
            snapshot, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",)),
            self.baseline, execution_contract_refs=(stale_ref,), execution_oracle_authenticator=auth,
        )
        self.assertIn("EXECUTION_ORACLE_PROVENANCE_INVALID", {item.code for item in stale.findings})

        ref = self._execution_ref()
        Path(ref["path"]).write_text("changed source", encoding="utf-8")
        changed_source = cases.validate_testcases(
            snapshot, self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",)),
            self.baseline, execution_contract_refs=(ref,), execution_oracle_authenticator=auth,
        )
        self.assertIn("PROVENANCE_HASH_MISMATCH", {item.code for item in changed_source.findings})

    def test_execution_oracle_cannot_answer_ba_unknowns(self):
        auth = lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id)
        cases_to_reject = (
            ("BR-005 maximum duration is 30 minutes", "BR-005"),
            ("Default sorting is newest first", None),
            ("Page size is 20", None),
            ("Filter appointments by status", None),
        )
        for source_text, expected_ref in cases_to_reject:
            with self.subTest(source_text=source_text):
                ref = self._execution_ref(source_text=source_text)
                snapshot = self._resolved_snapshot(ref)
                validation = cases.validate_testcases(
                    snapshot, DESIGN, self.baseline,
                    execution_contract_refs=(ref,), execution_oracle_authenticator=auth,
                )

                scope = [item for item in validation.findings if item.code == "AUTHORITY_SCOPE_VIOLATION"]
                self.assertEqual(validation.status, "FAIL")
                self.assertTrue(scope)
                self.assertIn(ref["id"], scope[0].message)
                self.assertIn(source_text, scope[0].message)
                if expected_ref:
                    self.assertIn(expected_ref, scope[0].message)
                self.assertEqual(scope[0].path, str(Path(ref["path"]).resolve()))
                self.assertIsNotNone(scope[0].line)

    def test_execution_oracle_accepts_execution_only_details(self):
        auth = lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id)
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",))
        for source_text in (
            "UI field selector: input[name='startTime']",
            "API request field: appointment.durationMinutes",
            "Fixture setup mapping: seed appointment fixture A",
            "Observation path: GET /appointments/{id}, inspect the saved status field",
        ):
            with self.subTest(source_text=source_text):
                ref = self._execution_ref(source_text=source_text)
                validation = cases.validate_testcases(
                    self._resolved_snapshot(ref), design, self.baseline,
                    execution_contract_refs=(ref,), execution_oracle_authenticator=auth,
                )
                self.assertEqual(validation.status, "PASS", [item.message for item in validation.findings])

    def test_execution_dependency_cannot_link_its_resolution_to_a_ba_unknown(self):
        ref = self._execution_ref(source_text="Approved interface field selector: input[name='duration']")
        snapshot = self._resolved_snapshot(ref, dependency_need="BR-005 maximum duration is 30 minutes")
        auth = lambda actor_id, _receipt: foundation.AuthenticatedHumanActorContext(actor_id)

        validation = cases.validate_testcases(
            snapshot, DESIGN, self.baseline,
            execution_contract_refs=(ref,), execution_oracle_authenticator=auth,
        )

        scope = [item for item in validation.findings if item.code == "AUTHORITY_SCOPE_VIOLATION"]
        self.assertEqual(validation.status, "FAIL")
        self.assertTrue(scope)
        self.assertIn("BR-005", scope[0].message)
        self.assertIn(ref["id"], scope[0].message)

    def test_case_review_rejects_stale_validation_and_wrong_transition(self):
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",))
        case = cases.CanonicalTestcase(
            "TC-001", "Create", "Check", "No setup required.", None,
            (cases.CaseStep("Create", None, "Appointment is Scheduled."),), "P1",
            ("FR-001",), ("TD-001",), (),
        )
        snapshot = cases.CaseSnapshot.create((case,), artifact_id="CR-001-cases", revision="1")
        validation = cases.validate_testcases(snapshot, design, self.baseline)
        self.assertEqual(validation.status, "PASS", [finding.__dict__ for finding in validation.findings])
        state = cases.start_case_workflow(snapshot)
        changed = cases.CaseSnapshot.create((case,), artifact_id="CR-001-cases", revision="2")

        with self.assertRaisesRegex(ValueError, "not bound"):
            cases.submit_cases_for_review(state, changed, validation)
        submitted = cases.submit_cases_for_review(state, snapshot, validation)
        with self.assertRaisesRegex(ValueError, "only DRAFT_CASES"):
            cases.submit_cases_for_review(submitted, snapshot, validation)

    def test_agent_case_gate_receipt_cannot_approve(self):
        design = self._design("TD-001", "Appointment is created in Scheduled.", ("FR-001",))
        case = cases.CanonicalTestcase(
            "TC-001", "Create", "Check", "No setup required.", None,
            (cases.CaseStep("Create appointment", None, "Appointment is Scheduled."),), "P1",
            ("FR-001",), ("TD-001",), (),
        )
        snapshot = cases.CaseSnapshot.create((case,), artifact_id="CR-001-cases", revision="1")
        validation = cases.validate_testcases(snapshot, design, self.baseline)
        workflow = cases.submit_cases_for_review(
            cases.start_case_workflow(snapshot), snapshot, validation,
            design_gate_receipt_mode="HUMAN_AUTHENTICATED",
            input_refs=cases.case_gate_input_refs(self.baseline, design),
        )
        snapshot = snapshot.project("IN_REVIEW")
        receipt = self._case_receipt(snapshot, design, decision="APPROVE")
        receipt["actor_id"] = "agent:fake-human"
        receipt["actor_role"] = "AGENT"
        result = cases.validate_case_gate_receipt(
            receipt, snapshot, design, self.baseline, workflow,
            human_actor_authenticator=lambda actor_id, _receipt: cases.AuthenticatedHumanActorContext(actor_id), validation=validation,
        )

        self.assertEqual(result.status, "FAIL")
        self.assertEqual(result.finding.code, "HUMAN_ACTOR_REQUIRED")

    def _design_receipt(self, actor_id="human:test-actor", snapshot=DESIGN, input_refs=None):
        return {
            "gate": "DESIGN_REVIEW",
            "decision": "APPROVE",
            "artifact_id": snapshot.artifact_id,
            "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": input_refs if input_refs is not None else cases.baseline_receipt_refs(self.baseline),
            "actor_id": actor_id,
            "actor_role": "HUMAN",
            "decided_at": "2026-09-25T12:00:00Z",
            "feedback": "",
        }

    def _case_receipt(self, snapshot, design, decision="APPROVE"):
        return {
            "gate": "CASE_REVIEW",
            "decision": decision,
            "artifact_id": snapshot.artifact_id,
            "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "input_refs": cases.baseline_receipt_refs(self.baseline) + [
                {"id": design.artifact_id, "revision": design.revision, "sha256": design.sha256}
            ],
            "actor_id": "human:test-actor",
            "actor_role": "HUMAN",
            "decided_at": "2026-09-25T12:00:00Z",
            "feedback": "",
        }

    def _design_evidence(self, test_only=False):
        run_dir = self.test_only_design_root if test_only else self.design_root
        receipt_path = run_dir / "design-gate/revisions" / self.design.revision / "receipt.json"
        evidence = {
            "path": str(receipt_path),
            "sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            "mode": "TEST_ONLY" if test_only else "HUMAN_AUTHENTICATED",
        }
        if test_only:
            evidence["fixture"] = {
                "path": str(self.test_only_design_fixture),
                "sha256": hashlib.sha256(self.test_only_design_fixture.read_bytes()).hexdigest(),
            }
        return evidence

    def _test_only_fixture(self, snapshot=DESIGN):
        return {
            "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT",
            "not_for_production": True,
            "receipt": self._design_receipt(actor_id="TEST_ONLY:simulated-human", snapshot=snapshot),
        }

    def _test_authorization(self, snapshot):
        if snapshot.sha256 == self.design.sha256:
            design_root, fixture = self.test_only_design_root, self.test_only_design_fixture
        else:
            design_root, fixture = self._persist_test_only_design(
                self.test_root / f"test-only-design-{len(snapshot.records)}-{snapshot.sha256[:8]}", snapshot,
            )
        return cases.validate_test_only_design_fixture(
            fixture, snapshot, self.baseline, design_workflow_dir=design_root,
        ).authorization

    def _design(self, design_id, expected, refs):
        record = foundation.CanonicalTestDesign(
            design_id, ("Test Design", "P1"), design_id, expected, refs, ()
        )
        return foundation.DesignSnapshot.create((record,), artifact_id="CR-001-test-design", revision="1")

    def _execution_ref(self, *, source_text="Approved execution-oracle source fixture."):
        source_path = self.test_root / "execution-oracle.json"
        source_bytes = (json.dumps({"source": source_text, "revision": "1"}, indent=2) + "\n").encode("utf-8")
        source_path.write_bytes(source_bytes)
        source_hash = hashlib.sha256(source_bytes).hexdigest()
        approval_path = self.test_root / "execution-oracle-approval.json"
        approval_bytes = (json.dumps({
            "decision": "APPROVE", "actor_role": "HUMAN", "actor_id": "human:oracle-owner",
            "source_id": "EXEC:interface-v1", "source_revision": "1", "source_sha256": source_hash,
        }, indent=2) + "\n").encode("utf-8")
        approval_path.write_bytes(approval_bytes)
        return {
            "id": "EXEC:interface-v1", "revision": "1", "sha256": source_hash,
            "approved": True, "path": str(source_path),
            "approval_evidence": {
                "path": str(approval_path), "sha256": hashlib.sha256(approval_bytes).hexdigest(),
            },
        }

    def _resolved_snapshot(self, ref, *, dependency_need="Approved interface action mapping"):
        dependency = cases.ExecutionDependency(dependency_need, "OBSERVABILITY", "RESOLVED", ref["id"])
        record = cases.CanonicalTestcase(
            "TC-001", "Create appointment", "Check creation", "A valid Pet exists.", "Pet A",
            (cases.CaseStep("Create appointment", None, "Appointment is saved as Scheduled."),), "P1",
            ("FR-001",), ("TD-001",), (dependency,),
        )
        return cases.CaseSnapshot.create((record,), artifact_id="CR-001-case-set", revision="1")

    @staticmethod
    def _benchmark_case():
        return """# Manual cases

## TC-001 Create appointment

**Objective:** Check a valid appointment can be created.
**Preconditions:** A valid Pet and Veterinarian exist.
**Test Data:** Pet A; Veterinarian B
**Priority:** P1
**Requirement refs:** FR-001, BR-004
**Test Design refs:** 1.0-UNIT-001

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Open appointment capability | Appointment entry is available. |
| 2 | Submit valid appointment data | Appointment is created in Scheduled. |

**Expected Result:** Appointment is created in Scheduled.
"""

    @staticmethod
    def _native_case(
        requirement_refs="FR-001; BR-004", design_refs="1.0-UNIT-001",
        expected="Appointment is created in Scheduled.",
        preconditions="A valid Pet and Veterinarian exist.",
    ):
        return f"""# Manual Test Cases

## TC-001 Create appointment

- Mô tả: Check a valid appointment can be created.
- Tiền điều kiện: {preconditions}
- Bước và kết quả mong đợi:
  1. Open appointment capability. → Appointment entry is available.
  2. Submit valid appointment data. → {expected}
- Test Data: Pet A; Veterinarian B
- Priority: P1.
- Trace: {requirement_refs}; {design_refs}
"""


if __name__ == "__main__":
    unittest.main()
