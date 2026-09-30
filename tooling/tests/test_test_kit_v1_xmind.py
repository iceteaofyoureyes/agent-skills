import hashlib
import json
import re
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest import mock

from tooling.lib import test_kit_v1 as core
from tooling.lib import test_kit_v1_cases as cases
from tooling.lib import test_kit_v1_xmind as xmind


ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "kits/ba/examples/CR-001/vi/05-engineering-handoff.yml"
FIXTURE = ROOT / "benchmark/test-kit/petclinic/fixtures/test-design-v1"
NON_APPROVED_FIXTURE = ROOT / "benchmark/test-kit/petclinic/foundation-v1-native-profiled"


class TestKitV1XMindTests(unittest.TestCase):
    def test_test_only_output_is_limited_to_temporary_workspace(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-output-location-") as temp:
            self.assertTrue(core.is_test_only_workspace_path(temp))
        self.assertTrue(core.is_test_only_workspace_path(ROOT / ".work/benchmark-runs/example"))
        self.assertFalse(core.is_test_only_workspace_path(ROOT / "benchmark/test-kit/petclinic"))

    def test_repository_assets_are_not_scratch_when_checkout_is_under_system_temp(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-temp-checkout-") as temp:
            checkout = Path(temp) / "repo"
            checkout.mkdir()
            with (
                mock.patch.object(core, "ROOT", checkout),
                mock.patch.object(core, "TEST_ONLY_OUTPUT_ROOT", checkout / ".work/benchmark-runs"),
            ):
                self.assertFalse(core.is_test_only_workspace_path(checkout / "benchmark"))
                self.assertTrue(core.is_test_only_workspace_path(checkout / ".work/benchmark-runs/example"))
                self.assertTrue(core.is_test_only_workspace_path(temp))

    def _copy_fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix="test-kit-xmind-")
        design_dir = Path(temporary.name) / "tea"
        shutil.copytree(FIXTURE, design_dir)
        return temporary, design_dir

    def _export_test_only(self, design_dir, output_dir):
        return xmind.export_test_only_design_xmind(
            design_dir,
            BASELINE,
            output_dir,
            test_only_receipt_fixture_path=design_dir / "design-test-only-receipt.json",
        )

    def _mutated_package(self, source, mutate):
        destination = source.with_name(f"mutated-{source.name}")
        with zipfile.ZipFile(source) as original, zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as changed:
            for info in original.infolist():
                content = original.read(info.filename)
                if info.filename == "content.json":
                    document = json.loads(content)
                    mutate(document)
                    content = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
                changed.writestr(info, content)
        return destination

    @staticmethod
    def _topics(topic):
        yield topic
        for child in topic.get("children", {}).get("attached", []):
            yield from TestKitV1XMindTests._topics(child)

    @staticmethod
    def _manifest(result):
        return json.loads(result.manifest_path.read_text(encoding="utf-8"))

    def _scenarios(self, document, manifest):
        component_ids = {trace["xmind_topic_id"] for trace in manifest["scenario_trace"]}
        return [
            topic for topic in self._topics(document[0]["rootTopic"])
            if topic.get("id") in component_ids
        ]

    @staticmethod
    def _trace(topic, manifest):
        return next(row for row in manifest["scenario_trace"] if row["xmind_topic_id"] == topic.get("id"))

    def _manifest_for_artifact(self, result, xmind_path):
        manifest = self._manifest(result)
        manifest["generated_xmind_sha256"] = hashlib.sha256(xmind_path.read_bytes()).hexdigest()
        return manifest

    def _validate_artifact(self, design, xmind_path, baseline, result):
        return xmind.validate_xmind_projection(
            design,
            xmind_path,
            baseline,
            projection_manifest=self._manifest_for_artifact(result, xmind_path),
        )

    def test_serialized_xmind_has_clean_logic_chart_content_json(self):
        temporary, design_dir = self._copy_fixture()
        try:
            result = self._export_test_only(design_dir, Path(temporary.name) / "projection")
            with zipfile.ZipFile(result.xmind_path) as archive:
                content_bytes = archive.read("content.json")
                document = json.loads(content_bytes)
                self.assertIn("manifest.json", archive.namelist())
                self.assertIn("metadata.json", archive.namelist())
                for member in ("manifest.json", "metadata.json"):
                    packaged_metadata = archive.read(member).decode("utf-8")
                    self.assertNotIn(xmind.PROJECTION_METADATA_PREFIX, packaged_metadata)
                    self.assertNotIn('"scenario_trace"', packaged_metadata)

            root = document[0]["rootTopic"]
            self.assertEqual(root.get("structureClass"), "org.xmind.ui.logic.right")
            topics = list(self._topics(root))
            self.assertEqual(sum("notes" in topic for topic in topics), 0)
            self.assertNotIn(xmind.PROJECTION_METADATA_PREFIX, content_bytes.decode("utf-8"))
            self.assertEqual(sum("labels" in topic for topic in topics), 0)
            self.assertTrue(all(not (set(topic) & {"notes", "labels", "hyperlink", "href", "comments", "callout", "summaries"}) for topic in topics))
            manifest = self._manifest(result)
            self.assertEqual(manifest["generated_xmind_sha256"], hashlib.sha256(result.xmind_path.read_bytes()).hexdigest())
            self.assertEqual(result.semantic_diff.root_structure_class, "org.xmind.ui.logic.right")
            self.assertEqual(result.semantic_diff.xmind_layout, "LOGIC_CHART_RIGHT")
            self.assertEqual(result.semantic_diff.content_json_notes_key_count, 0)
            self.assertEqual(result.semantic_diff.machine_readable_note_count, 0)
            self.assertEqual(result.semantic_diff.machine_label_count, 0)
            self.assertEqual(manifest["machine_notes_allowed"], False)
            self.assertEqual(manifest["machine_labels_allowed"], False)
            self.assertEqual(manifest["traceability_location"], "EXTERNAL_PROJECTION_MANIFEST")
        finally:
            temporary.cleanup()

    def test_human_facing_profile_puts_function_and_outcomes_on_canvas(self):
        temporary, design_dir = self._copy_fixture()
        try:
            result = self._export_test_only(design_dir, Path(temporary.name) / "projection")
            manifest = self._manifest(result)
            design = cases.load_design_snapshot(
                design_dir / "canonical/canonical-test-design.json",
                design_dir / "workflow-state.json",
                design_dir / "canonical/semantic-payload.json",
            )
            baseline = core.load_approved_baseline(BASELINE)
            with zipfile.ZipFile(result.xmind_path) as archive:
                document = json.loads(archive.read("content.json"))
            self.assertEqual(len(document), 1)
            root = document[0]["rootTopic"]
            self.assertEqual(root["title"], "CR-001 — Appointment Scheduling")

            groups = root["children"]["attached"]
            self.assertEqual(
                [group["title"] for group in groups],
                [
                    "Tạo lịch hẹn",
                    "Kiểm tra xung đột lịch",
                    "Chỉnh sửa / Đổi lịch",
                    "Hủy lịch hẹn",
                    "Hoàn tất lịch hẹn",
                    "Xem lịch hẹn",
                ],
            )
            visible = list(self._topics(root))
            titles = [topic["title"] for topic in visible]
            forbidden = {
                "Canonical Test Design", "Test Coverage Plan", "P0", "P1", "P2", "P3",
                "Expected Behavior", "Requirement Refs", "Open Questions / UNKNOWN",
            }
            self.assertEqual(sum(title in forbidden for title in titles), 0)

            scenarios = self._scenarios(document, manifest)
            self.assertEqual(len(scenarios), len(design.records))
            self.assertTrue(all(topic["title"].startswith("Kiểm tra") for topic in scenarios))
            scenario_metadata = {self._trace(topic, manifest)["design_id"]: self._trace(topic, manifest) for topic in scenarios}
            self.assertEqual(
                {metadata["scenario_title"] for metadata in scenario_metadata.values()},
                {row.scenario_title for row in design.records},
            )
            self.assertEqual(scenario_metadata["TC-017"]["scenario_title"], next(row.scenario_title for row in design.records if row.design_id == "TC-017"))
            self.assertEqual(scenario_metadata["TC-018"]["scenario_title"], next(row.scenario_title for row in design.records if row.design_id == "TC-018"))
            self.assertEqual(
                next(topic["title"] for topic in scenarios if self._trace(topic, manifest)["design_id"] == "TC-017"),
                "Kiểm tra giới hạn thời lượng tối đa của Appointment",
            )
            self.assertEqual(
                next(topic["title"] for topic in scenarios if self._trace(topic, manifest)["design_id"] == "TC-018"),
                "Kiểm tra bộ lọc, sắp xếp và phân trang Appointment",
            )
            self.assertEqual(sum(bool(re.search(r"\b(?:FR|BR)-\d+\b", title)) for title in titles), 0)
            self.assertEqual(sum("deferred theo" in title.casefold() for title in titles), 0)
            self.assertEqual(sum(topic["title"].startswith("MM: ") for topic in visible), 16)
            warnings = [topic for topic in visible if topic["title"].startswith("⚠ Chờ BA: ")]
            self.assertEqual(len(warnings), 2)
            self.assertEqual(
                [topic["title"] for topic in warnings],
                [
                    "⚠ Chờ BA: Thời lượng tối đa chưa được xác định.",
                    "⚠ Chờ BA: Bộ lọc, sắp xếp và phân trang chưa được xác định.",
                ],
            )
            tc018 = next(topic for topic in scenarios if self._trace(topic, manifest)["design_id"] == "TC-018")
            self.assertEqual(len(tc018["children"]["attached"]), 1)
            self.assertEqual(
                scenario_metadata["TC-018"]["open_questions"],
                [question.to_dict() for question in next(row for row in design.records if row.design_id == "TC-018").open_questions],
            )
            self.assertEqual(result.semantic_diff.status, "PASS")
            self.assertEqual(result.semantic_diff.resolved_count, 16)
            self.assertEqual(result.semantic_diff.visible_mm_count, 16)
            self.assertEqual(result.semantic_diff.visible_ba_warning_count, 2)
            self.assertEqual(result.semantic_diff.group_names, tuple(group["title"] for group in groups))
            self.assertEqual(result.semantic_diff.forbidden_technical_node_count, 0)
            self.assertFalse(any(title in {ref for row in design.records for ref in row.requirement_refs} for title in titles))
            preview = result.tree_preview_path.read_text(encoding="utf-8")
            self.assertEqual(preview.splitlines()[0], root["title"])
            for topic in visible:
                self.assertIn(topic["title"], preview)
            self.assertEqual(len(baseline.requirements), 6)
        finally:
            temporary.cleanup()

    def test_test_only_approved_design_exports_and_round_trips_all_semantics(self):
        temporary, design_dir = self._copy_fixture()
        try:
            source_files = (
                design_dir / "canonical/canonical-test-design.json",
                design_dir / "canonical/semantic-payload.json",
                design_dir / "workflow-state.json",
            )
            before = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files}
            output_dir = Path(temporary.name) / "projection"
            result = self._export_test_only(design_dir, output_dir)
            manifest = self._manifest(result)
            design = cases.load_design_snapshot(
                design_dir / "canonical/canonical-test-design.json",
                design_dir / "workflow-state.json",
                design_dir / "canonical/semantic-payload.json",
            )
            baseline = core.load_approved_baseline(BASELINE)

            self.assertTrue(result.xmind_path.is_file())
            self.assertTrue(result.manifest_path.is_file())
            self.assertTrue(result.tree_preview_path.is_file())
            self.assertEqual(result.semantic_diff.status, "PASS")
            self.assertEqual(result.semantic_diff.scenario_count, len(design.records))
            self.assertEqual(result.semantic_diff.deferred_count, sum(row.expected_behavior is None for row in design.records))
            self.assertEqual(
                xmind.build_semantic_projection_model(design, baseline),
                xmind.build_semantic_projection_model(design, baseline),
            )
            self.assertEqual(
                xmind.validate_xmind_projection(
                    design, result.xmind_path, baseline, projection_manifest=result.manifest_path
                ).status,
                "PASS",
            )

            with zipfile.ZipFile(result.xmind_path) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual(set(archive.namelist()), {"content.json", "content.xml", "manifest.json", "metadata.json"})
                ET.fromstring(archive.read("content.xml"))
                content = json.loads(archive.read("content.json"))
                package_manifest = json.loads(archive.read("manifest.json"))
                package_metadata = json.loads(archive.read("metadata.json"))
                self.assertNotIn("scenario_trace", json.dumps(package_manifest))
                self.assertNotIn("TC-001", json.dumps(package_metadata))
                self.assertNotIn(xmind.PROJECTION_METADATA_PREFIX, b"".join(archive.read(name) for name in archive.namelist()).decode("utf-8", errors="ignore"))
            self.assertEqual(len(content), 1)
            scenarios = self._scenarios(content, manifest)
            self.assertEqual(len(scenarios), len(design.records))
            rows = {row.design_id: row for row in design.records}
            trace = {row["design_id"]: row for row in manifest["scenario_trace"]}
            for scenario in scenarios:
                row_trace = self._trace(scenario, manifest)
                row = rows[row_trace["design_id"]]
                self.assertTrue(scenario["title"].startswith("Kiểm tra"))
                self.assertEqual(scenario["id"], row_trace["xmind_topic_id"])
                self.assertEqual(scenario["customId"], row.design_id)
                self.assertEqual(row_trace["scenario_title"], row.scenario_title)
                self.assertEqual(row_trace["hierarchy_path"], list(row.hierarchy_path))
                self.assertEqual(row_trace["functional_group_ref"], trace[row.design_id]["functional_group_ref"])
                self.assertEqual(row_trace["requirement_refs"], list(row.requirement_refs))
                self.assertEqual(row_trace["expected_behavior"], row.expected_behavior)
                self.assertEqual(row_trace["open_questions"], [q.to_dict() for q in row.open_questions])
                if row.expected_behavior is not None:
                    self.assertEqual([child["title"] for child in scenario["children"]["attached"]], [f"MM: {row.expected_behavior}"])
                else:
                    self.assertEqual(
                        [child["title"] for child in scenario["children"]["attached"]],
                        row_trace["visible_open_question_warnings"],
                    )
            topics = list(self._topics(content[0]["rootTopic"]))
            self.assertEqual(sum("notes" in topic for topic in topics), 0)
            self.assertEqual(sum("labels" in topic for topic in topics), 0)
            self.assertEqual(content[0]["rootTopic"]["structureClass"], xmind.ROOT_STRUCTURE_CLASS)
            self.assertEqual(manifest["layout"], "LOGIC_CHART_RIGHT")

            self.assertEqual(manifest["projection_type"], "XMIND")
            self.assertEqual(manifest["presentation_profile"], "HUMAN_FACING_XMIND_PROFILE")
            self.assertEqual(manifest["presentation_profile_version"], "1.3.0")
            self.assertEqual(manifest["projection_status"], "PASS")
            self.assertEqual(manifest["canonical_collection_id"], design.artifact_id)
            self.assertEqual(manifest["canonical_revision"], design.revision)
            self.assertEqual(manifest["canonical_semantic_sha256"], design.sha256)
            self.assertEqual(manifest["design_gate_receipt_mode"], "TEST_ONLY")
            self.assertEqual(manifest["authority"], "DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH")
            self.assertEqual(manifest["generated_xmind_sha256"], hashlib.sha256(result.xmind_path.read_bytes()).hexdigest())
            self.assertEqual(manifest["semantic_diff"], "PASS")
            self.assertEqual(manifest["content_json_notes_key_count"], 0)
            self.assertEqual(manifest["machine_readable_note_count"], 0)
            self.assertEqual(manifest["machine_label_count"], 0)
            self.assertEqual(manifest["visible_requirement_ref_count"], 0)
            self.assertEqual(manifest["visible_deferred_marker_count"], 0)
            self.assertEqual(len(manifest["scenario_trace"]), len(design.records))
            self.assertEqual(
                manifest["canonical_open_question_record_count"],
                sum(len(row.open_questions) for row in design.records),
            )
            self.assertEqual(manifest["business_group_names"], list(result.semantic_diff.group_names))
            for row in design.records:
                self.assertEqual(trace[row.design_id]["scenario_title"], row.scenario_title)
                self.assertTrue(trace[row.design_id]["visible_scenario_title"].startswith("Kiểm tra"))
                self.assertEqual(trace[row.design_id]["expected_behavior"], row.expected_behavior)
                self.assertEqual(trace[row.design_id]["hierarchy_path"], list(row.hierarchy_path))
                self.assertEqual(trace[row.design_id]["requirement_refs"], list(row.requirement_refs))
                self.assertEqual(trace[row.design_id]["open_questions"], [question.to_dict() for question in row.open_questions])
                self.assertEqual(trace[row.design_id]["xmind_topic_id"], xmind._scenario_topic_id(design.artifact_id, row.design_id))
            self.assertEqual(manifest["tree_preview"]["sha256"], hashlib.sha256(result.tree_preview_path.read_bytes()).hexdigest())
            self.assertNotIn(str(ROOT), json.dumps(manifest))
            self.assertEqual(before, {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source_files})
        finally:
            temporary.cleanup()

    def test_deferred_expected_behavior_cannot_become_an_assertion(self):
        temporary, design_dir = self._copy_fixture()
        try:
            result = self._export_test_only(design_dir, Path(temporary.name) / "projection")
            manifest = self._manifest(result)
            design = cases.load_design_snapshot(
                design_dir / "canonical/canonical-test-design.json",
                design_dir / "workflow-state.json",
                design_dir / "canonical/semantic-payload.json",
            )
            baseline = core.load_approved_baseline(BASELINE)
            deferred_id = next(row.design_id for row in design.records if row.expected_behavior is None)

            def add_assertion(document):
                scenario = next(
                    topic for topic in self._scenarios(document, manifest)
                    if self._trace(topic, manifest)["design_id"] == deferred_id
                )
                scenario["children"]["attached"] = [{"title": "MM: Assert maximum duration is within a fixed limit"}]

            changed = self._mutated_package(result.xmind_path, add_assertion)
            diff = self._validate_artifact(design, changed, baseline, result)
            self.assertEqual(diff.status, "FAIL")
            self.assertTrue(any("deferred" in finding.casefold() or "chờ ba" in finding.casefold() for finding in diff.findings))
        finally:
            temporary.cleanup()

    def test_production_export_rejects_test_only_receipt(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-xmind-") as temp:
            with self.assertRaises(xmind.XMindProjectionError) as error:
                xmind.export_approved_design_xmind(
                    FIXTURE,
                    BASELINE,
                    Path(temp) / "output",
                    human_actor_authenticator=lambda actor_id, receipt: cases.AuthenticatedHumanActorContext(actor_id),
                )
        self.assertEqual(error.exception.code, "TEST_ONLY_RECEIPT_NOT_PRODUCTION")

    def test_design_review_is_rejected_by_production_export(self):
        with tempfile.TemporaryDirectory(prefix="test-kit-xmind-") as temp:
            with self.assertRaises(xmind.XMindProjectionError) as error:
                xmind.export_approved_design_xmind(
                    NON_APPROVED_FIXTURE,
                    BASELINE,
                    Path(temp) / "output",
                    human_actor_authenticator=lambda actor_id, receipt: cases.AuthenticatedHumanActorContext(actor_id),
                )
        self.assertEqual(error.exception.code, "DESIGN_NOT_APPROVED")

    def test_stale_revision_and_hash_in_test_only_receipt_fail_closed(self):
        for field, value in (("artifact_revision", "stale-revision"), ("artifact_sha256", "0" * 64)):
            with self.subTest(field=field):
                temporary, design_dir = self._copy_fixture()
                try:
                    receipt_path = design_dir / "design-test-only-receipt.json"
                    fixture = json.loads(receipt_path.read_text(encoding="utf-8"))
                    fixture["receipt"][field] = value
                    receipt_path.write_text(json.dumps(fixture), encoding="utf-8")
                    with self.assertRaises(xmind.XMindProjectionError) as error:
                        self._export_test_only(design_dir, Path(temporary.name) / "projection")
                    self.assertEqual(error.exception.code, "DESIGN_RECEIPT_BINDING_MISMATCH")
                finally:
                    temporary.cleanup()

    def test_missing_duplicate_and_semantically_changed_scenarios_fail_round_trip(self):
        temporary, design_dir = self._copy_fixture()
        try:
            result = self._export_test_only(design_dir, Path(temporary.name) / "projection")
            manifest = self._manifest(result)
            design = cases.load_design_snapshot(
                design_dir / "canonical/canonical-test-design.json",
                design_dir / "workflow-state.json",
                design_dir / "canonical/semantic-payload.json",
            )
            baseline = core.load_approved_baseline(BASELINE)

            def changed_package(mutate):
                changed = self._mutated_package(result.xmind_path, mutate)
                return changed, self._validate_artifact(design, changed, baseline, result)

            def remove_scenario(document):
                target = self._scenarios(document, manifest)[0]
                parent = next(
                    topic for topic in self._topics(document[0]["rootTopic"])
                    if target in topic.get("children", {}).get("attached", [])
                )
                parent["children"]["attached"].remove(target)

            missing, missing_diff = changed_package(remove_scenario)
            self.assertEqual(missing_diff.status, "FAIL")

            def duplicate(document):
                source = self._scenarios(document, manifest)[0]
                parent = next(topic for topic in self._topics(document[0]["rootTopic"]) if source in topic.get("children", {}).get("attached", []))
                parent["children"]["attached"].append(json.loads(json.dumps(source)))

            duplicated, duplicate_diff = changed_package(duplicate)
            self.assertEqual(duplicate_diff.status, "FAIL")

            def change_visible_title(document):
                self._scenarios(document, manifest)[0]["title"] += " changed"

            changed_title, title_diff = changed_package(change_visible_title)
            self.assertEqual(title_diff.status, "FAIL")

            def change_component_id(document):
                self._scenarios(document, manifest)[0]["id"] = "changed-component-id"

            changed_id, id_diff = changed_package(change_component_id)
            self.assertEqual(id_diff.status, "FAIL")

            def change_custom_id(document):
                self._scenarios(document, manifest)[0]["customId"] = "TC-999"

            changed_custom_id, custom_id_diff = changed_package(change_custom_id)
            self.assertEqual(custom_id_diff.status, "FAIL")

            def change_mm(document):
                scenario = next(
                    topic for topic in self._scenarios(document, manifest)
                    if self._trace(topic, manifest)["outcome_state"] == "RESOLVED"
                )
                scenario["children"]["attached"][0]["title"] += " changed"

            changed_mm, mm_diff = changed_package(change_mm)
            self.assertEqual(mm_diff.status, "FAIL")

            def remove_ba_warning(document):
                scenario = next(
                    topic for topic in self._scenarios(document, manifest)
                    if self._trace(topic, manifest)["design_id"] == "TC-018"
                )
                scenario["children"]["attached"].clear()

            no_warning, warning_diff = changed_package(remove_ba_warning)
            self.assertEqual(warning_diff.status, "FAIL")

            manifest_refs = self._manifest(result)
            manifest_refs["scenario_trace"][0]["requirement_refs"][0] = "FR-999"
            self.assertEqual(
                xmind.validate_xmind_projection(design, result.xmind_path, baseline, projection_manifest=manifest_refs).status,
                "FAIL",
            )

            manifest_questions = self._manifest(result)
            manifest_questions["scenario_trace"][-1]["open_questions"].pop()
            self.assertEqual(
                xmind.validate_xmind_projection(design, result.xmind_path, baseline, projection_manifest=manifest_questions).status,
                "FAIL",
            )

            manifest_state = self._manifest(result)
            manifest_state["scenario_trace"][-1]["outcome_state"] = "RESOLVED"
            self.assertEqual(
                xmind.validate_xmind_projection(design, result.xmind_path, baseline, projection_manifest=manifest_state).status,
                "FAIL",
            )

            mismatched_hash = self._mutated_package(result.xmind_path, lambda document: None)
            changed_manifest = self._manifest(result)
            self.assertNotEqual(hashlib.sha256(mismatched_hash.read_bytes()).hexdigest(), changed_manifest["generated_xmind_sha256"])
            self.assertEqual(
                xmind.validate_xmind_projection(design, mismatched_hash, baseline, projection_manifest=changed_manifest).status,
                "FAIL",
            )
        finally:
            temporary.cleanup()

    def test_sdk_serializes_untrusted_titles_as_data_without_notes(self):
        with tempfile.TemporaryDirectory() as temp:
            model = {
                "sheet_title": "Test Design",
                "root_title": "Canonical Test Design",
                "children": [{
                    "title": "<script>alert(1)</script> &",
                    "component_id": xmind._scenario_topic_id("CR-001", "TC-001"),
                    "custom_id": "TC-001",
                    "children": [],
                }],
            }
            path = xmind._serialize_xmind(model, Path(temp), "safe-name")
            with zipfile.ZipFile(path) as archive:
                content = json.loads(archive.read("content.json"))
                ET.fromstring(archive.read("content.xml"))
            scenario = content[0]["rootTopic"]["children"]["attached"][0]
            self.assertEqual(scenario["title"], model["children"][0]["title"])
            self.assertEqual(scenario["id"], model["children"][0]["component_id"])
            self.assertEqual(scenario["customId"], model["children"][0]["custom_id"])
            self.assertNotIn("notes", scenario)
            self.assertEqual(content[0]["rootTopic"]["structureClass"], xmind.ROOT_STRUCTURE_CLASS)
            self.assertEqual(set(archive.namelist()), {"content.json", "content.xml", "manifest.json", "metadata.json"})

    def test_output_filename_is_safe_and_deterministic(self):
        first = xmind._safe_filename("../../CR-001: Test Design")
        self.assertEqual(first, xmind._safe_filename("../../CR-001: Test Design"))
        self.assertNotIn("/", first)
        self.assertNotIn("\\", first)
        self.assertTrue(first.endswith(".xmind"))

    def test_ambiguous_or_stale_function_group_mapping_fails_closed(self):
        design = cases.load_design_snapshot(
            FIXTURE / "canonical/canonical-test-design.json",
            FIXTURE / "workflow-state.json",
            FIXTURE / "canonical/semantic-payload.json",
        )
        baseline = core.load_approved_baseline(BASELINE)
        rows = list(design.records)
        index = next(i for i, row in enumerate(rows) if row.design_id == "TC-001")
        rows[index] = replace(rows[index], requirement_refs=(*rows[index].requirement_refs, "FR-003"))
        ambiguous = replace(design, records=tuple(rows))
        with self.assertRaises(xmind.XMindProjectionError) as error:
            xmind.build_semantic_projection_model(ambiguous, baseline)
        self.assertEqual(error.exception.code, "CANNOT_PROJECT_HUMAN_PROFILE")

        rows = list(design.records)
        index = next(i for i, row in enumerate(rows) if row.design_id == "TC-011")
        rows[index] = replace(rows[index], scenario_title="Concurrent appointment conflict")
        stale_override = replace(design, records=tuple(rows))
        with self.assertRaises(xmind.XMindProjectionError) as error:
            xmind.build_semantic_projection_model(stale_override, baseline)
        self.assertEqual(error.exception.code, "CANNOT_PROJECT_HUMAN_PROFILE")


if __name__ == "__main__":
    unittest.main()
