import hashlib
import json
import re
import shutil
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tooling.lib import test_kit_v1 as test_kit
from tooling.tests.codex_stub import fake_codex_on_path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "kits/ba/examples/CR-001/vi/05-engineering-handoff.yml"
BENCHMARK = ROOT / "benchmark/test-kit/petclinic/tea-test-design/raw-output/test-design/test-design-epic-1.md"
NATIVE = ROOT / "benchmark/test-kit/petclinic/fixtures/test-only-native-tea-output-v1/test-design-epic-1.md"
PINNED_TEA_FIXTURE = ROOT / "kits/test/skills/bmad-testarch-test-design"


def _machine_specific_paths(text):
    patterns = (
        re.compile(r"(?i)(?<![A-Z0-9])[A-Z]:[\\/][^\s<>|]+"),
        re.compile(r"(?<![\w])\\\\[^\\/\s]+\\[^\\/\s]+(?:\\[^\s]*)?"),
        re.compile(r"(?<![\w])/home/[^/\s]+(?:/[^\s]*)?"),
    )
    return [match.group(0) for pattern in patterns for match in pattern.finditer(text)]


class TestKitV1Tests(unittest.TestCase):
    def setUp(self):
        self.baseline = test_kit.load_approved_baseline(HANDOFF)

    def test_source_parser_accepts_current_ba_heading_format_and_domain_br_ids(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            srs = root / "srs.md"
            rules = root / "rules.md"
            srs.write_text(
                "# SRS\n\n### FR-001 — Search title\n\nSearch theo title.\n\n"
                "### FR-002 — Status\n\nStatus single-select.\n",
                encoding="utf-8",
            )
            rules.write_text(
                "# Rules\n\n### BR-WED-011 — Search scope\n\nKhông search slug.\n\n"
                "### BR-AUTH-004 — Access\n\nChỉ dữ liệu actor được phép xem.\n",
                encoding="utf-8",
            )

            fr = test_kit._parse_source_rows(srs, "FR", 3)
            br = test_kit._parse_source_rows(rules, "BR", 3)

            self.assertEqual([row.id for row in fr], ["FR-001", "FR-002"])
            self.assertEqual([row.id for row in br], ["BR-WED-011", "BR-AUTH-004"])
            self.assertIn("Search theo title.", fr[0].text)
            self.assertIn("Không search slug.", br[0].text)

    def test_trace_parser_accepts_domain_scoped_ba_ids(self):
        refs = test_kit._parse_ref_cell(
            "FR-001; BR-WED-011; BR-AUTH-004",
            {"FR-001", "BR-WED-011", "BR-AUTH-004"},
            path="tea.md",
            line=10,
            field="Truy vết",
        )
        self.assertEqual(refs, ["FR-001", "BR-WED-011", "BR-AUTH-004"])

    def test_ba_adapter_copies_fr_and_br_separately_and_keeps_supplemental_separate(self):
        supplemental = "Visit has date, description, and Pet; this is supplemental only."
        bundle = test_kit.adapt_ba_to_tea(HANDOFF, supplemental=supplemental)

        self.assertEqual([row.id for row in bundle.requirements], [f"FR-{n:03}" for n in range(1, 7)])
        self.assertEqual([row.id for row in bundle.business_rules], [f"BR-{n:03}" for n in range(1, 15)])
        self.assertIn(bundle.requirements[0].text, bundle.epic_markdown)
        self.assertNotIn("BR-001", bundle.epic_markdown)
        self.assertIn("BR-001", bundle.business_rules_markdown)
        self.assertNotIn(supplemental, bundle.epic_markdown)
        self.assertEqual(bundle.supplemental_text, supplemental)

    def test_ba_adapter_preserves_all_source_unknown_text(self):
        bundle = test_kit.adapt_ba_to_tea(HANDOFF)

        self.assertEqual(len(bundle.open_items), 2)
        self.assertTrue(any(("maximum" in text.lower() or "tối đa" in text.lower()) and "unknown" in text.lower() for text in bundle.unknown_texts))
        self.assertTrue(any("lọc" in text.lower() and "phân trang" in text.lower() for text in bundle.unknown_texts))
        self.assertIn("UNKNOWN", bundle.open_decisions_markdown)

    def test_vietnamese_upper_bound_unknown_is_linked_to_its_explicit_ba_ref(self):
        questions = test_kit._unknown_for_row(
            ["BR-005"],
            "Kiểm tra thời lượng dương và không dương",
            "Không kiểm tra cận trên vì UNKNOWN.",
            self.baseline,
            path="tea.md",
            line=12,
        )

        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0].source_ref, "BR-005")
        self.assertIn("UNKNOWN", questions[0].text)

    def test_missing_ba_approval_fails_before_adapter_output(self):
        with tempfile.TemporaryDirectory() as temp:
            handoff = self._copy_fixture(temp)
            handoff.write_text(handoff.read_text(encoding="utf-8").replace("APPROVED_FOR_ENGINEERING", "DRAFT"), encoding="utf-8")

            with self.assertRaises(test_kit.BaselineError):
                test_kit.adapt_ba_to_tea(handoff)

    def test_missing_authoritative_hash_fails_before_adapter_output(self):
        with tempfile.TemporaryDirectory() as temp:
            handoff = self._copy_fixture(temp)
            text = handoff.read_text(encoding="utf-8")
            text = text.replace("sha256: f8a3aa2ed7d8c2aae57f49b919afcf40c26c905493628429da94b9440d33fc32", "sha256: ")
            handoff.write_text(text, encoding="utf-8")

            with self.assertRaises(test_kit.BaselineError):
                test_kit.adapt_ba_to_tea(handoff)

    def test_accepts_frozen_benchmark_raw_profile(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)

        self.assertEqual(result.status, "NORMALIZED")
        self.assertIsNotNone(result.snapshot)
        self.assertEqual(len(result.snapshot.records), 14)
        self.assertEqual(result.snapshot.records[0].design_id, "TD-001")

    def test_accepts_frozen_native_runtime_raw_profile_and_preserves_unknowns(self):
        result = test_kit.normalize_tea_output(NATIVE, self.baseline)

        self.assertEqual(result.status, "NORMALIZED")
        self.assertEqual(len(result.snapshot.records), 35)
        self.assertEqual(result.snapshot.records[-1].design_id, "TD-35")
        self.assertIsNone(result.snapshot.records[-1].expected_behavior)
        self.assertTrue(result.snapshot.records[-1].open_questions)
        first_row = next(row for row in result.snapshot.records if row.design_id == "TD-01")
        self.assertTrue({"BR-001", "BR-002", "BR-003"}.issubset(first_row.requirement_refs))
        self.assertEqual(test_kit.validate_design(result.snapshot, self.baseline).status, "PASS")
        refs = {question.source_ref for row in result.snapshot.records for question in row.open_questions}
        self.assertTrue({"BR-005", "FR-006", "BR-014"}.issubset(refs))

    def test_native_test_id_is_preserved_without_td_prefix_or_renumbering(self):
        raw = NATIVE.read_text(encoding="utf-8").replace("TD-28", "TC-E1-01")
        result = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="native-id.md")

        self.assertEqual(result.status, "NORMALIZED", result.findings)
        self.assertEqual(result.snapshot.records[0].design_id, "TC-E1-01")

    def test_native_deferred_scenario_with_placeholder_id_is_cannot_normalize(self):
        raw = NATIVE.read_text(encoding="utf-8").replace("| TD-35 |", "| — |", 1)
        result = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="missing-native-id.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertEqual(result.findings[0].field, "Test ID")

    def test_same_session_prepare_and_finalize_reach_design_review_without_nested_codex(self):
        manifest = json.loads(test_kit.TEA_PIN_MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="same-session-test-kit-") as temp:
            project = Path(temp) / "project"
            project.mkdir()
            handoff = self._copy_fixture(project)
            skill = project / ".agents/skills" / test_kit.TEA_CAPABILITY
            for relative in manifest["files"]:
                target = skill / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((PINNED_TEA_FIXTURE / relative).read_bytes())
            config = project / "_bmad/tea/config.yaml"
            config.parent.mkdir(parents=True)
            config.write_text(
                "user_name: Tester\n"
                "communication_language: Vietnamese\n"
                "document_output_language: Vietnamese\n"
                "output_folder: test-runs\n"
                "test_artifacts: test-runs\n"
                "test_stack_type: fullstack\n",
                encoding="utf-8",
            )
            run_dir = project / "test-runs/CR-001/design-001"

            original_config = config.read_bytes()
            with mock.patch.object(test_kit, "resolve_codex_command") as resolver:
                prepared = test_kit.prepare_same_session_design(
                    handoff, run_dir, project_root=project, skill_dir=skill,
                )
                resolver.assert_not_called()
                self.assertEqual(config.read_bytes(), original_config)
                runtime_config = Path(prepared["runtime_config"]["path"])
                self.assertTrue(runtime_config.is_file())
                runtime_text = runtime_config.read_text(encoding="utf-8")
                self.assertIn((run_dir / "raw-output").resolve().as_posix(), runtime_text)
                self.assertNotEqual(runtime_config.resolve(), config.resolve())

                raw = Path(prepared["raw_output_path"])
                raw.parent.mkdir(parents=True, exist_ok=True)
                raw.write_bytes(BENCHMARK.read_bytes())

                result = test_kit.finalize_same_session_design(handoff, run_dir)
                resolver.assert_not_called()
                self.assertEqual(config.read_bytes(), original_config)

            self.assertEqual(result["status"], "DESIGN_REVIEW")
            self.assertEqual(result["review_status"], "IN_REVIEW")
            self.assertEqual(result["validation_status"], "PASS")
            self.assertTrue((run_dir / "canonical/canonical-test-design.json").is_file())
            self.assertTrue((run_dir / "workflow-state.json").is_file())
            self.assertTrue((run_dir / "evidence/same-session-prepare.json").is_file())
            self.assertTrue((run_dir / "evidence/same-session-finalize.json").is_file())

    def test_same_session_finalize_rejects_project_config_drift(self):
        manifest = json.loads(test_kit.TEA_PIN_MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="same-session-config-drift-") as temp:
            project = Path(temp) / "project"
            project.mkdir()
            handoff = self._copy_fixture(project)
            skill = project / ".agents/skills" / test_kit.TEA_CAPABILITY
            for relative in manifest["files"]:
                target = skill / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((PINNED_TEA_FIXTURE / relative).read_bytes())
            config = project / "_bmad/tea/config.yaml"
            config.parent.mkdir(parents=True)
            config.write_text(
                "user_name: Tester\n"
                "communication_language: Vietnamese\n"
                "document_output_language: Vietnamese\n"
                "output_folder: .test-kit/runtime\n"
                "test_artifacts: .test-kit/runtime\n"
                "test_stack_type: fullstack\n",
                encoding="utf-8",
            )
            run_dir = project / ".test-kit/runs/CR-001/design-001"
            prepared = test_kit.prepare_same_session_design(
                handoff, run_dir, project_root=project, skill_dir=skill,
            )
            raw = Path(prepared["raw_output_path"])
            raw.parent.mkdir(parents=True, exist_ok=True)
            raw.write_bytes(BENCHMARK.read_bytes())
            config.write_text(config.read_text(encoding="utf-8") + "tea_execution_mode: sequential\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "PROJECT_TEA_CONFIG_DRIFT"):
                test_kit.finalize_same_session_design(handoff, run_dir)

    def test_same_session_prepare_fails_closed_on_unpinned_skill(self):
        with tempfile.TemporaryDirectory(prefix="same-session-pin-") as temp:
            project = Path(temp) / "project"
            project.mkdir()
            handoff = self._copy_fixture(project)
            skill = project / ".agents/skills" / test_kit.TEA_CAPABILITY
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("wrong bytes", encoding="utf-8")
            config = project / "_bmad/tea/config.yaml"
            config.parent.mkdir(parents=True)
            config.write_text("user_name: Tester\n", encoding="utf-8")

            with mock.patch.object(test_kit, "resolve_codex_command") as resolver:
                with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE"):
                    test_kit.prepare_same_session_design(
                        handoff, project / "test-runs/run-1",
                        project_root=project, skill_dir=skill,
                    )
                resolver.assert_not_called()

    def test_native_invocation_requests_only_the_frozen_raw_profile(self):
        prompt = test_kit._invocation_prompt(Path("epic.md"), Path("rules.md"), Path("unknowns.md"), Path("output.md"), None)

        self.assertIn("Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được", prompt)
        self.assertIn("do not rename or renumber IDs", prompt)
        self.assertIn("no result can be asserted while the BA decision awaits clarification", prompt)
        self.assertIn("Every scenario row, including deferred/UNKNOWN rows, needs a unique non-empty Test ID", prompt)
        self.assertIn("Use the native coverage heading exactly as `## Test Coverage Plan`", prompt)
        self.assertIn("The Trace cell must contain only exact FR/BR IDs separated by semicolons", prompt)

    def test_completed_artifact_can_be_preserved_before_closeout_overwrites_target(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "test-design.md"
            snapshot = Path(temp) / "completed-artifact.md"
            completed = b"---\nworkflowStatus: completed\n---\n# Raw test design\n"
            output.write_bytes(completed)

            artifact = test_kit._completed_artifact_bytes(output)
            test_kit._write_exclusive(snapshot, artifact)
            output.write_text("Completed. The design file contains the result.", encoding="utf-8")

            self.assertEqual(snapshot.read_bytes(), completed)
            self.assertIsNone(test_kit._completed_artifact_bytes(output))

    def test_native_profile_is_complete_only_after_tea_step_five_checkpoint(self):
        native_header = "| " + " | ".join(test_kit.NATIVE_HEADERS) + " |"
        body = "\n".join((
            "# Test Design: Epic 1",
            "## Test Coverage Plan",
            "### P0", native_header,
            "| TD-01 | Scenario | Unit | - | FR-001 | Outcome |",
            "### P1", "### P2", "### P3",
        ))
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "test-design.md"
            checkpoint = Path(temp) / "progress.md"
            output.write_text(body, encoding="utf-8")
            checkpoint.write_text("workflowStatus: in-progress\nstepsCompleted: []\n", encoding="utf-8")
            self.assertIsNone(test_kit._completed_artifact_bytes(output, checkpoint))

            checkpoint.write_text(
                "workflowStatus: completed\nstepsCompleted: ['step-05-generate-output']\n", encoding="utf-8"
            )
            self.assertEqual(test_kit._completed_artifact_bytes(output, checkpoint), output.read_bytes())
    def test_unknown_tea_shape_is_cannot_normalize(self):
        result = test_kit.normalize_tea_markdown("""# Test Design: Epic 1
## Test Coverage Plan
### P1 — High
| Scenario | Requirement | New Column |
|---|---|---|
| TD-001 — A | FR-001 | value |
""", self.baseline, source_path="unknown.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertIn("header", result.findings[0].field)
        self.assertEqual(result.findings[0].path, "unknown.md")

    def test_malformed_or_ambiguous_trace_is_cannot_normalize(self):
        raw = self._minimal_native("TD-01", "FR-001, FR-O01", "Outcome is observable.")
        result = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="ambiguous.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertEqual(result.findings[0].field, "Truy vết")

    def test_missing_observable_without_explicit_unknown_is_cannot_normalize(self):
        raw = self._minimal_native("TD-01", "FR-001; BR-001", "")
        result = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="missing-result.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertEqual(result.findings[0].field, "Kết quả quan sát được")

    def test_unknown_tea_scenario_shape_is_not_silently_dropped(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        marker = "## Execution Strategy"
        self.assertIn(marker, raw)
        altered = raw.replace(marker, "TD-999 | FR-001 | unsupported extra scenario\n\n" + marker, 1)
        result = test_kit.normalize_tea_markdown(altered, self.baseline, source_path="tea-extra.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertEqual(result.findings[0].line, altered[:altered.index("TD-999")].count("\n") + 1)

    def test_td_scenario_after_the_known_coverage_section_is_rejected(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        for token in ("TD-999", "1.1-UNIT-999", "1-INT-999"):
            with self.subTest(token=token):
                altered = raw + f"\n## Additional scenario\n\n{token} — Unsupported extra scenario.\n"
                result = test_kit.normalize_tea_markdown(altered, self.baseline, source_path="outside-plan.md")

                self.assertEqual(result.status, "CANNOT_NORMALIZE")
                self.assertIsNone(result.snapshot)
                self.assertEqual(result.findings[0].path, "outside-plan.md")
                self.assertEqual(result.findings[0].line, altered[:altered.index(token)].count("\n") + 1)

    def test_unconsumed_td_scenario_inside_assumptions_section_is_rejected(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        marker = "### Assumptions and open decisions"
        self.assertIn(marker, raw)
        extra = "1. TD-999 — Maximum-duration scenario with an unsupported outcome."
        altered = raw.replace(marker, marker + "\n\n" + extra, 1)
        result = test_kit.normalize_tea_markdown(altered, self.baseline, source_path="assumption-td.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertIsNone(result.snapshot)
        self.assertEqual(result.findings[0].path, "assumption-td.md")
        self.assertEqual(result.findings[0].line, altered[:altered.index("TD-999")].count("\n") + 1)
        self.assertIn("Assumptions and open decisions", result.findings[0].message)
        self.assertIn("TD-999", result.findings[0].message)

    def test_numbered_known_td_item_inside_assumptions_is_not_metadata_exempt(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        marker = "### Assumptions and open decisions"
        extra = "1. TD-001 scenario-shaped item with an unsupported outcome."
        altered = raw.replace(marker, marker + "\n\n" + extra, 1)
        result = test_kit.normalize_tea_markdown(altered, self.baseline, source_path="known-td-assumption.md")

        self.assertEqual(result.status, "CANNOT_NORMALIZE")
        self.assertEqual(result.findings[0].path, "known-td-assumption.md")
        self.assertEqual(result.findings[0].line, altered[:altered.index("TD-001 scenario")].count("\n") + 1)
        self.assertIn("TD-001", result.findings[0].message)

    def test_ordinary_assumption_and_unknown_decision_bullets_remain_allowed(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        marker = "### Assumptions and open decisions"
        ordinary = (
            "1. Appointment duration must remain positive for the approved scenario.\n"
            "2. The maximum duration remains UNKNOWN pending a BA decision.\n"
            "3. List filters, default sorting, and page size remain unresolved."
        )
        altered = raw.replace(marker, marker + "\n\n" + ordinary, 1)
        result = test_kit.normalize_tea_markdown(altered, self.baseline, source_path="assumption-prose.md")

        self.assertEqual(result.status, "NORMALIZED", result.findings)

    def test_known_td_references_in_ba_decision_prose_are_metadata_but_unknown_ids_are_not(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        section = "## Quyết định BA còn mở\nCác hàng TD-001 giữ điều kiện ở trạng thái deferred.\n\n"
        valid = test_kit.normalize_tea_markdown(
            raw.replace("## Test Coverage Plan", section + "## Test Coverage Plan", 1),
            self.baseline,
            source_path="known-deferred-metadata.md",
        )
        contaminated = test_kit.normalize_tea_markdown(
            raw.replace("## Test Coverage Plan", section.replace("TD-001", "TD-999") + "## Test Coverage Plan", 1),
            self.baseline,
            source_path="unknown-deferred-metadata.md",
        )

        self.assertEqual(valid.status, "NORMALIZED", valid.findings)
        self.assertEqual(contaminated.status, "CANNOT_NORMALIZE")
        self.assertIn("Quyết định BA còn mở", contaminated.findings[0].message)
        self.assertIn("TD-999", contaminated.findings[0].message)

    def test_known_tea_coverage_summary_id_is_metadata_but_unknown_id_is_not(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        summary = "**Kế hoạch bao phủ:** Example Test ID theo profile epic-level; ví dụ `1-INT-001`."
        self.assertIn("## Test Coverage Plan", raw)
        raw = raw.replace("## Test Coverage Plan", summary + "\n\n## Test Coverage Plan", 1)
        valid = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="summary-metadata.md")
        contaminated = test_kit.normalize_tea_markdown(
            raw.replace("ví dụ `1-INT-001`", "ví dụ `1-INT-001`, TD-999", 1),
            self.baseline,
            source_path="contaminated-summary.md",
        )

        self.assertEqual(valid.status, "NORMALIZED")
        self.assertEqual(contaminated.status, "CANNOT_NORMALIZE")
        self.assertEqual(contaminated.findings[0].path, "contaminated-summary.md")

    def test_frozen_deferred_metadata_can_reference_known_rows_only(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        metadata = (
            "## Ngoài phạm vi của bản Test Design này\n\n"
            "| Hạng mục | Xử lý |\n| --- | --- |\n"
            "| Deferred row | UNKNOWN; `TD-001` remains deferred. |\n\n"
            "## Truy vết FR/BR tới scenario\n\n"
            "| Requirement | Test ID |\n| --- | --- |\n| FR-001 | TD-001 |\n\n"
            "## Entry / Exit Criteria\n\n### Entry Criteria\n\n- Defer `TD-001` until BA approval.\n\n"
            "## Assumptions and Dependencies\n\n- This assumption affects `TD-001`.\n\n"
        )
        self.assertIn("TD-001", raw)
        raw = raw.replace("## Test Coverage Plan", metadata + "## Test Coverage Plan", 1)
        valid = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="deferred-metadata.md")
        contaminated = test_kit.normalize_tea_markdown(
            raw.replace("| FR-001 | TD-001 |", "| FR-001 | TD-001; TD-999 |", 1),
            self.baseline,
            source_path="unmapped-metadata.md",
        )

        self.assertEqual(valid.status, "NORMALIZED")
        self.assertEqual(contaminated.status, "CANNOT_NORMALIZE")

    def test_awaiting_ba_maximum_duration_row_stays_null_and_linked_unknown(self):
        raw = BENCHMARK.read_text(encoding="utf-8")
        raw = raw.replace("TD-003 — Positive duration", "TD-999 — Maximum duration — awaiting BA decision", 1)
        raw = raw.replace(
            "A positive duration is accepted; zero and negative duration are rejected. No upper-bound value or result is asserted.",
            "No result can be asserted while maximum duration awaits BA decision; no threshold is approved.",
            1,
        )
        normalized = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="deferred-max.md")

        self.assertEqual(normalized.status, "NORMALIZED")
        deferred = next(row for row in normalized.snapshot.records if row.design_id == "TD-999")
        self.assertIsNone(deferred.expected_behavior)
        self.assertEqual(
            [(question.source_ref, question.text, question.status) for question in deferred.open_questions],
            [("BR-005", self.baseline.unknown_clauses["BR-005"], "UNKNOWN")],
        )
        self.assertEqual(test_kit.validate_design(normalized.snapshot, self.baseline).status, "PASS")

    def test_ba_id_range_requires_exact_case_and_spelling(self):
        self.assertEqual(
            test_kit._parse_ref_cell("FR-001 to FR-003", self.baseline.ba_ids, path="trace.md", line=1, field="Requirement"),
            ["FR-001", "FR-002", "FR-003"],
        )
        with self.assertRaises(test_kit._NormalizationError):
            test_kit._parse_ref_cell("fr-001 to fr-003", self.baseline.ba_ids, path="trace.md", line=1, field="Requirement")
        for invalid in (
            "FR-1 to FR-003", "fr-001 to FR-003", "FR-001 to FR-099", "FR001 to FR-003",
        ):
            with self.subTest(invalid=invalid), self.assertRaises(test_kit._NormalizationError):
                test_kit._parse_ref_cell(invalid, self.baseline.ba_ids, path="trace.md", line=7, field="Requirement")

    def test_tea_runtime_pin_checks_exact_tree_and_rejects_mutations(self):
        manifest = json.loads(test_kit.TEA_PIN_MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp) / "skill"
            for relative in manifest["files"]:
                target = skill / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((PINNED_TEA_FIXTURE / relative).read_bytes())
            self.assertEqual(len(test_kit.verify_pinned_tea_skill(skill)), len(manifest["files"]))
            changed = skill / next(path for path in manifest["files"] if path != "SKILL.md")
            changed.write_bytes(changed.read_bytes() + b"mutation")
            with self.assertRaisesRegex(RuntimeError, "PIN_INTEGRITY_FAILURE"):
                test_kit.verify_pinned_tea_skill(skill)
            changed.unlink()
            with self.assertRaisesRegex(RuntimeError, "runtime tree mismatch"):
                test_kit.verify_pinned_tea_skill(skill)

    def test_test_kit_runtime_has_no_machine_paths_and_guard_detects_codex_path(self):
        relocation_pin = ROOT / "tooling/pins/test-only-provenance-relocations-v1.json"
        python_runtime = sorted((ROOT / "tooling/lib").glob("test_kit_v1*.py")) + [ROOT / "tooling/lib/codex_cli.py"]
        xmind_runtime = [
            path for path in (ROOT / "tooling/xmind").rglob("*")
            if path.is_file() and "node_modules" not in path.parts and path.suffix.casefold() in {".js", ".mjs", ".json"}
        ]
        pinned_config = [path for path in sorted((ROOT / "tooling/pins").glob("*.json")) if path != relocation_pin]
        files = (*python_runtime, *xmind_runtime, *pinned_config)
        findings = [
            f"{path.relative_to(ROOT)}:{line_number}:{match}"
            for path in files
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            for match in _machine_specific_paths(line)
        ]
        self.assertEqual(findings, [])
        mutations = (
            "C:" + "/" + "nvm4w/nodejs/node_modules/@openai/codex/bin/codex.js",
            "D:" + "\\" + "AI" + "\\agent-skills\\tooling",
            "\\" * 2 + "server" + "\\share\\tools",
            "/" + "home/" + "specific-user/" + "codex",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertEqual(_machine_specific_paths(mutation), [mutation])

    def test_tea_pin_failure_aborts_before_native_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / ".agents/skills" / test_kit.TEA_CAPABILITY
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("wrong bytes", encoding="utf-8")
            (root / "_bmad/tea").mkdir(parents=True)
            (root / "_bmad/tea/config.yaml").write_text("project config", encoding="utf-8")
            run_dir = root / "run"
            with mock.patch.object(test_kit.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(RuntimeError, "runtime tree mismatch"):
                    test_kit.invoke_native_tea(
                        test_kit.adapt_ba_to_tea(HANDOFF), run_dir,
                        petclinic_root=root, skill_dir=skill,
                    )
            popen.assert_not_called()

    def test_native_tea_resolves_temporary_codex_command_from_path(self):
        manifest = json.loads(test_kit.TEA_PIN_MANIFEST.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix="Native TEA workspace with spaces ") as temp:
            root = Path(temp) / "PetClinic project"
            skill = root / ".agents/skills" / test_kit.TEA_CAPABILITY
            for relative in manifest["files"]:
                target = skill / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((PINNED_TEA_FIXTURE / relative).read_bytes())
            config = root / "_bmad/tea/config.yaml"
            config.parent.mkdir(parents=True)
            config.write_text("project config\n", encoding="utf-8")
            run_dir = Path(temp) / "native run with spaces"
            with fake_codex_on_path() as (fake_codex, capture_path):
                resolved = test_kit.resolve_codex_command()
                result = test_kit.invoke_native_tea(
                    test_kit.adapt_ba_to_tea(HANDOFF), run_dir,
                    petclinic_root=root, skill_dir=skill, model="model name with spaces",
                )
                captured = json.loads(capture_path.read_text(encoding="utf-8"))
                command = result["invocation_command"]
                self.assertEqual(result["status"], "ARTIFACT_COMPLETE")
                self.assertEqual(resolved.resolution, "PATH")
                self.assertEqual(
                    Path(resolved.target),
                    (fake_codex.parent / "node_modules/@openai/codex/bin/codex.js").resolve(),
                )
                self.assertNotIn("nvm4w", " ".join(resolved.argv_prefix).casefold())
                self.assertEqual(command, resolved.argv(captured))
                self.assertNotIn("--no-daemon", captured)
                self.assertNotIn("--approve-for-me", captured)
                self.assertIn("--ask-for-approval", captured)
                self.assertEqual(captured[captured.index("--ask-for-approval") + 1], "never")
                self.assertLess(captured.index("--ask-for-approval"), captured.index("exec"))
                self.assertEqual(captured[captured.index("--model") + 1], "model name with spaces")
                self.assertEqual(captured[captured.index("-C") + 1], str(root.resolve()))
                self.assertEqual(captured[captured.index("--add-dir") + 1], str(run_dir.resolve()))
    def test_advisory_priority_and_other_tea_metadata_do_not_enter_semantic_schema(self):
        result = test_kit.normalize_tea_output(NATIVE, self.baseline)
        semantic = result.snapshot.records[0].semantic_dict()

        self.assertEqual(set(semantic), set(test_kit.SEMANTIC_FIELDS))
        self.assertNotIn("priority", semantic)
        self.assertNotIn("risk", semantic)
        self.assertNotIn("level", semantic)

    def test_duplicate_and_orphan_refs_are_blocking_validator_findings(self):
        raw = self._replace_benchmark_cell("TD-001", 1, "FR-001, FR-001, BR-999")
        result = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="refs.md")
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        codes = {finding.code for finding in validation.findings}

        self.assertIn("DUPLICATE_REQUIREMENT_REF", codes)
        self.assertIn("ORPHAN_REQUIREMENT_REF", codes)
        self.assertEqual(validation.status, "FAIL")

    def test_explicit_authority_conflict_blocks_review_submission(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        conflict = test_kit.Finding("AUTHORITY_CONFLICT", "scenario outcome conflicts with the approved BA oracle", field="expected_behavior")
        validation = test_kit.validate_design(result.snapshot, self.baseline, explicit_authority_conflicts=[conflict])

        self.assertEqual(validation.status, "FAIL")
        self.assertIn(conflict, validation.findings)

    def test_unknown_answer_leak_is_a_blocking_validator_finding(self):
        raw = self._replace_benchmark_cell("TD-003", 6, "The maximum duration is 30 minutes.")
        result = test_kit.normalize_tea_markdown(raw, self.baseline, source_path="leak.md")
        validation = test_kit.validate_design(result.snapshot, self.baseline)

        self.assertIn("UNKNOWN_ASSERTION_LEAK", {finding.code for finding in validation.findings})

    def test_validator_pass_and_design_review_submission_never_approve(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        self.assertEqual(validation.status, "PASS", [f.message for f in validation.findings])

        state = test_kit.start_design_workflow(result.snapshot)
        self.assertEqual(state.state, "DRAFT_DESIGN")
        submitted = test_kit.submit_design_for_review(state, result.snapshot, validation)
        self.assertEqual(submitted.state, "DESIGN_REVIEW")
        self.assertEqual(submitted.review_status, "IN_REVIEW")
        self.assertNotEqual(submitted.review_status, "APPROVED")
        self.assertEqual(submitted.artifact_sha256, result.snapshot.sha256)

    def test_review_transition_rejects_wrong_state_and_snapshot(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        state = test_kit.start_design_workflow(result.snapshot)
        changed = test_kit.DesignSnapshot.create(
            result.snapshot.records,
            artifact_id=result.snapshot.artifact_id,
            revision="2",
            evidence=result.snapshot.evidence,
            field_sources=result.snapshot.field_sources,
        )

        with self.assertRaisesRegex(ValueError, "validation result is not bound"):
            test_kit.submit_design_for_review(state, changed, validation)
        submitted = test_kit.submit_design_for_review(state, result.snapshot, validation)
        with self.assertRaisesRegex(ValueError, "only DRAFT_DESIGN"):
            test_kit.submit_design_for_review(submitted, result.snapshot, validation)

    def test_agent_or_upstream_approval_is_rejected_without_state_change(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        state = test_kit.submit_design_for_review(
            test_kit.start_design_workflow(result.snapshot), result.snapshot, validation
        )

        with tempfile.TemporaryDirectory() as temp:
            test_kit.persist_design_review(
                temp, test_kit.adapt_ba_to_tea(HANDOFF), BENCHMARK,
                result.snapshot, validation, state,
            )
            receipt = self._design_receipt(result.snapshot, self.baseline, actor_id="agent:fake-human")
            attempted = test_kit.apply_design_decision(
                temp, result.snapshot, self.baseline, receipt,
                human_actor_authenticator=lambda *_: None,
            )

        self.assertFalse(attempted.accepted)
        self.assertEqual(attempted.finding.code, "HUMAN_ACTOR_REQUIRED")

    def test_design_gate_approve_persists_receipt_and_approved_projection_without_hash_change(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        state = test_kit.submit_design_for_review(
            test_kit.start_design_workflow(result.snapshot), result.snapshot, validation
        )
        receipt = self._design_receipt(result.snapshot, self.baseline)

        with tempfile.TemporaryDirectory() as temp:
            test_kit.persist_design_review(
                temp, test_kit.adapt_ba_to_tea(HANDOFF), BENCHMARK,
                result.snapshot, validation, state,
            )
            decision = test_kit.apply_design_decision(
                temp, result.snapshot, self.baseline, receipt,
                human_actor_authenticator=lambda actor_id, _receipt: test_kit.AuthenticatedHumanActorContext(actor_id),
                validation=validation,
            )
            root = Path(temp)
            workflow = json.loads((root / "workflow-state.json").read_text(encoding="utf-8"))
            projection = json.loads((root / "canonical/canonical-test-design-approved-projection.json").read_text(encoding="utf-8"))

            self.assertTrue(decision.accepted)
            self.assertEqual(decision.state.state, "APPROVED_DESIGN")
            self.assertEqual(workflow["state"], "APPROVED_DESIGN")
            self.assertTrue((root / "design-gate/revisions/1/receipt.json").is_file())
            self.assertTrue(all(row["review_status"] == "APPROVED" for row in projection))
            self.assertEqual((root / "canonical/semantic-payload.json").read_bytes(), result.snapshot.payload_bytes)
            self.assertEqual(decision.state.artifact_sha256, result.snapshot.sha256)

    def test_design_gate_request_changes_preserves_receipt_and_starts_new_revision(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        state = test_kit.submit_design_for_review(
            test_kit.start_design_workflow(result.snapshot), result.snapshot, validation
        )
        receipt = self._design_receipt(
            result.snapshot, self.baseline, decision="REQUEST_CHANGES", feedback="Clarify the mapped outcomes."
        )

        with tempfile.TemporaryDirectory() as temp:
            test_kit.persist_design_review(
                temp, test_kit.adapt_ba_to_tea(HANDOFF), BENCHMARK,
                result.snapshot, validation, state,
            )
            decision = test_kit.apply_design_decision(
                temp, result.snapshot, self.baseline, receipt,
                human_actor_authenticator=lambda actor_id, _receipt: test_kit.AuthenticatedHumanActorContext(actor_id),
                validation=validation, next_revision="2",
            )
            root = Path(temp)
            workflow = json.loads((root / "workflow-state.json").read_text(encoding="utf-8"))

            self.assertTrue(decision.accepted)
            self.assertEqual(workflow["state"], "DRAFT_DESIGN")
            self.assertEqual(workflow["artifact_revision"], "2")
            self.assertEqual(decision.reviewed_snapshot.records[0].review_status, "CHANGES_REQUESTED")
            self.assertEqual(decision.next_snapshot.records[0].review_status, "DRAFT")
            self.assertEqual(decision.next_snapshot.sha256, result.snapshot.sha256)
            self.assertTrue((root / "design-gate/revisions/1/receipt.json").is_file())
            self.assertTrue((root / "revisions/2/canonical/semantic-payload.json").is_file())

    def test_design_gate_replay_is_rejected_after_approval(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        state = test_kit.submit_design_for_review(
            test_kit.start_design_workflow(result.snapshot), result.snapshot, validation
        )
        receipt = self._design_receipt(result.snapshot, self.baseline)
        with tempfile.TemporaryDirectory() as temp:
            test_kit.persist_design_review(
                temp, test_kit.adapt_ba_to_tea(HANDOFF), BENCHMARK,
                result.snapshot, validation, state,
            )
            first = test_kit.apply_design_decision(
                temp, result.snapshot, self.baseline, receipt,
                human_actor_authenticator=lambda actor_id, _receipt: test_kit.AuthenticatedHumanActorContext(actor_id),
                validation=validation,
            )
            replay = test_kit.apply_design_decision(
                temp, result.snapshot, self.baseline, receipt,
                human_actor_authenticator=lambda actor_id, _receipt: test_kit.AuthenticatedHumanActorContext(actor_id),
                validation=validation,
            )

        self.assertTrue(first.accepted)
        self.assertFalse(replay.accepted)
        self.assertEqual(replay.finding.code, "INVALID_REVIEW_TRANSITION")

    def test_design_gate_rechecks_source_bytes_after_baseline_load(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture_root = Path(temp)
            self._copy_fixture(fixture_root)
            handoff = fixture_root / "vi/05-engineering-handoff.yml"
            baseline = test_kit.load_approved_baseline(handoff)
            result = test_kit.normalize_tea_output(BENCHMARK, baseline)
            validation = test_kit.validate_design(result.snapshot, baseline)
            state = test_kit.submit_design_for_review(
                test_kit.start_design_workflow(result.snapshot), result.snapshot, validation
            )
            run_dir = fixture_root / "run"
            raw = run_dir / "raw-output/test-design.md"
            raw.parent.mkdir(parents=True)
            raw.write_bytes(BENCHMARK.read_bytes())
            test_kit.persist_design_review(
                run_dir, test_kit.adapt_ba_to_tea(handoff), raw,
                result.snapshot, validation, state,
            )
            baseline.source_paths["srs"].write_text(
                baseline.source_paths["srs"].read_text(encoding="utf-8") + "\nchanged\n",
                encoding="utf-8",
            )
            receipt = self._design_receipt(result.snapshot, baseline)
            decision = test_kit.apply_design_decision(
                run_dir, result.snapshot, baseline, receipt,
                human_actor_authenticator=lambda actor_id, _receipt: test_kit.AuthenticatedHumanActorContext(actor_id),
                validation=validation,
            )

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.finding.code, "BA_BASELINE_STALE")

    @staticmethod
    def _design_receipt(snapshot, baseline, *, actor_id="human:design-gate", decision="APPROVE", feedback=""):
        refs = [
            {"id": f"BA:{name}", "revision": baseline.revision, "sha256": baseline.source_hashes[name]}
            for name in ("business_rules", "srs", "decisions")
        ]
        refs.append({
            "id": "BA:handoff", "revision": baseline.revision,
            "sha256": test_kit._source_hash(baseline.handoff_path),
        })
        return {
            "gate": "DESIGN_REVIEW", "decision": decision,
            "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256, "input_refs": refs,
            "actor_id": actor_id, "actor_role": "HUMAN",
            "decided_at": "2026-09-25T13:00:00Z", "feedback": feedback,
        }

    def test_snapshot_bytes_are_immutable_and_hash_excludes_projected_review_status(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        snapshot = result.snapshot
        self.assertEqual(hashlib.sha256(snapshot.payload_bytes).hexdigest(), snapshot.sha256)
        self.assertNotIn(b"review_status", snapshot.payload_bytes)
        self.assertEqual(snapshot.records[0].review_status, "DRAFT")

    def test_design_validator_binds_records_to_immutable_semantic_bytes(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        changed = replace(result.snapshot.records[0], scenario_title="silently changed")
        forged = replace(result.snapshot, records=(changed, *result.snapshot.records[1:]))

        validation = test_kit.validate_design(forged, self.baseline)

        self.assertEqual(validation.status, "FAIL")
        self.assertIn("SNAPSHOT_RECORD_MISMATCH", {finding.code for finding in validation.findings})

    def test_design_review_persistence_keeps_exact_schema_and_hash_binding(self):
        result = test_kit.normalize_tea_output(BENCHMARK, self.baseline)
        validation = test_kit.validate_design(result.snapshot, self.baseline)
        state = test_kit.submit_design_for_review(
            test_kit.start_design_workflow(result.snapshot), result.snapshot, validation
        )
        bundle = test_kit.adapt_ba_to_tea(HANDOFF)

        with tempfile.TemporaryDirectory() as temp:
            test_kit.persist_design_review(temp, bundle, BENCHMARK, result.snapshot, validation, state)
            root = Path(temp)
            semantic_payload = (root / "canonical/semantic-payload.json").read_bytes()
            records = json.loads((root / "canonical/canonical-test-design.json").read_text(encoding="utf-8"))
            workflow = json.loads((root / "workflow-state.json").read_text(encoding="utf-8"))

            self.assertEqual(semantic_payload, result.snapshot.payload_bytes)
            self.assertEqual(hashlib.sha256(semantic_payload).hexdigest(), state.artifact_sha256)
            self.assertTrue(all(set(row) == set(test_kit.RECORD_FIELDS) for row in records))
            self.assertTrue(all(row["review_status"] == "IN_REVIEW" for row in records))
            self.assertEqual(workflow["state"], "DESIGN_REVIEW")

    @staticmethod
    def _copy_fixture(temp):
        source_dir = HANDOFF.parent
        target_dir = Path(temp) / "vi"
        target_dir.mkdir()
        for name in ("03-approved-business-rules.md", "04-srs-excerpt.md", "02-gap-review.md", "05-engineering-handoff.yml"):
            shutil.copyfile(source_dir / name, target_dir / name)
        return target_dir / "05-engineering-handoff.yml"

    @staticmethod
    def _minimal_native(design_id, trace, expected):
        return f"""# Test Design: Epic 1 — CR-001 Appointment Scheduling
## Test Coverage Plan
### P0 — Critical
None.
### P1 — High
| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|
| {design_id} | Scenario title | API | — | {trace} | {expected} |
### P2 — Medium
None.
### P3 — Low
None.
"""

    @staticmethod
    def _replace_benchmark_cell(design_id, cell_index, replacement):
        lines = BENCHMARK.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if design_id not in line or not line.startswith("|"):
                continue
            cells = line.strip().strip("|").split("|")
            cells[cell_index] = replacement
            lines[index] = "| " + " | ".join(cell.strip() for cell in cells) + " |"
            return "\n".join(lines) + "\n"
        raise AssertionError(f"benchmark row not found: {design_id}")


if __name__ == "__main__":
    unittest.main()
