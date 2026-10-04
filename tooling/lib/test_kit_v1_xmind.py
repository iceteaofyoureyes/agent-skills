"""Optional, one-way XMind projection of an approved Test Kit V1 design."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tooling.lib import test_kit_v1 as core
from tooling.lib import test_kit_v1_cases as cases


ROOT = Path(__file__).resolve().parents[2]
PIN_PATH = ROOT / "tooling/pins/xmind-sdk-v1.json"
PROFILE_PATH = ROOT / "tooling/pins/xmind-human-facing-profile-v1.json"
EXPORTER_VERSION = "1.2.0"
SEMANTIC_MODEL_VERSION = "4"
ROOT_STRUCTURE_CLASS = "org.xmind.ui.logic.right"
XMIND_LAYOUT = "LOGIC_CHART_RIGHT"
UNKNOWN_LABEL = "UNKNOWN"
PROJECTION_METADATA_PREFIX = "TEST_KIT_V1_PROJECTION_METADATA:"
MM_PREFIX = "MM: "
BA_WARNING_PREFIX = "⚠ Chờ BA: "
SHEET_TITLE = "Test Design"
REQUIRED_XMIND_MEMBERS = {"content.json", "content.xml", "manifest.json", "metadata.json"}
FORBIDDEN_VISIBLE_TITLES = {
    "Canonical Test Design", "Test Coverage Plan", "P0", "P1", "P2", "P3",
    "Expected Behavior", "Requirement Refs", "Open Questions / UNKNOWN",
}


class XMindProjectionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class SemanticDiffResult:
    status: str
    canonical_row_count: int
    scenario_count: int
    deferred_count: int
    findings: tuple[str, ...] = ()
    resolved_count: int = 0
    group_names: tuple[str, ...] = ()
    visible_mm_count: int = 0
    visible_ba_warning_count: int = 0
    forbidden_technical_node_count: int = 0
    root_structure_class: str | None = None
    xmind_layout: str | None = None
    content_json_notes_key_count: int = 0
    machine_readable_note_count: int = 0
    machine_label_count: int = 0
    visible_requirement_ref_count: int = 0
    visible_deferred_marker_count: int = 0


@dataclass(frozen=True)
class XMindExportResult:
    xmind_path: Path
    manifest_path: Path
    tree_preview_path: Path
    semantic_diff: SemanticDiffResult


@dataclass(frozen=True)
class HumanFacingProjection:
    model: dict
    group_by_design_id: dict[str, str]
    group_labels: dict[str, str]
    scenario_titles: dict[str, str]
    question_presentations: dict[str, str]
    topic_ids: dict[str, str]
    profile_name: str
    profile_version: str
    profile_sha256: str
    root_title: str


def _read_pin() -> dict:
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    required = {"package", "version", "repository", "revision", "license", "integrity"}
    if not isinstance(pin, dict) or set(pin) != required:
        raise XMindProjectionError("XMIND_PIN_INVALID", "XMind SDK pin manifest has an unsupported shape")
    if pin["package"] != "xmind" or pin["version"] != "2.2.33":
        raise XMindProjectionError("XMIND_PIN_INVALID", "XMind SDK package/version does not match the reviewed pin")
    try:
        lock = json.loads((ROOT / "tooling/xmind/package-lock.json").read_text(encoding="utf-8"))
        locked = lock["packages"]["node_modules/xmind"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise XMindProjectionError("XMIND_PIN_INVALID", f"XMind SDK lockfile is unavailable: {error}") from error
    if locked.get("version") != pin["version"] or locked.get("integrity") != pin["integrity"]:
        raise XMindProjectionError("XMIND_PIN_INVALID", "XMind SDK lockfile does not match the reviewed package pin")
    return pin


def _load_design(run_dir: Path) -> tuple[dict, core.DesignSnapshot]:
    try:
        workflow = json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))
        design = cases.load_design_snapshot(
            run_dir / "canonical/canonical-test-design.json",
            run_dir / "workflow-state.json",
            run_dir / "canonical/semantic-payload.json",
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise XMindProjectionError("CANONICAL_DESIGN_INVALID", f"Canonical Test Design is unavailable or stale: {error}") from error
    return workflow, design


def _load_baseline(path: str | Path) -> core.ApprovedBaseline:
    try:
        return core.load_approved_baseline(path)
    except (OSError, ValueError) as error:
        raise XMindProjectionError("BA_BASELINE_STALE", str(error)) from error


def export_approved_design_xmind(
    design_workflow_dir: str | Path,
    baseline_handoff_path: str | Path,
    output_dir: str | Path,
    *,
    human_actor_authenticator,
    baseline_override: core.ApprovedBaseline | None = None,
    generic_vnext: bool = False,
) -> XMindExportResult:
    """Export only a persisted, current APPROVED_DESIGN with host-authenticated Human receipt."""
    run_dir = Path(design_workflow_dir).resolve()
    workflow, design = _load_design(run_dir)
    if workflow.get("state") != "APPROVED_DESIGN" or workflow.get("review_status") != "APPROVED":
        raise XMindProjectionError("DESIGN_NOT_APPROVED", "XMind export requires persisted APPROVED_DESIGN")
    if workflow.get("design_gate_receipt_mode") == "TEST_ONLY":
        raise XMindProjectionError("TEST_ONLY_RECEIPT_NOT_PRODUCTION", "TEST_ONLY Design Gate receipts cannot authorize production XMind export")
    if workflow.get("design_gate_receipt_mode") != "HUMAN_AUTHENTICATED":
        raise XMindProjectionError("MISSING_HUMAN_DESIGN_RECEIPT", "XMind export requires a persisted Human Design Gate receipt")
    baseline = baseline_override or _load_baseline(baseline_handoff_path)
    receipt_path = run_dir / "design-gate/revisions" / design.revision / "receipt.json"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise XMindProjectionError("MISSING_HUMAN_DESIGN_RECEIPT", str(error)) from error
    checked = cases.validate_design_gate_receipt(
        receipt,
        design,
        baseline,
        design_workflow_dir=run_dir,
        human_actor_authenticator=human_actor_authenticator,
    )
    if checked.status != "PASS" or checked.authorization is None:
        finding = checked.finding
        raise XMindProjectionError(
            finding.code if finding else "DESIGN_GATE_VALIDATION_FAILED",
            finding.message if finding else "Human Design Gate authorization did not validate",
        )
    return _export_validated(
        design, baseline, checked.authorization, "HUMAN_AUTHENTICATED", output_dir,
        generic_vnext=generic_vnext,
    )


def export_test_only_design_xmind(
    design_workflow_dir: str | Path,
    baseline_handoff_path: str | Path,
    output_dir: str | Path,
    *,
    test_only_receipt_fixture_path: str | Path,
    baseline_override: core.ApprovedBaseline | None = None,
    generic_vnext: bool = False,
) -> XMindExportResult:
    """Acceptance-only path for isolated TEST_ONLY fixtures; outputs stay temporary."""
    run_dir = Path(design_workflow_dir).resolve()
    workflow, design = _load_design(run_dir)
    if workflow.get("state") != "APPROVED_DESIGN" or workflow.get("review_status") != "APPROVED":
        raise XMindProjectionError("DESIGN_NOT_APPROVED", "XMind export requires persisted APPROVED_DESIGN")
    baseline = baseline_override or _load_baseline(baseline_handoff_path)
    checked = cases.validate_test_only_design_fixture(
        test_only_receipt_fixture_path,
        design,
        baseline,
        design_workflow_dir=run_dir,
    )
    if checked.status != "PASS" or checked.authorization is None:
        finding = checked.finding
        raise XMindProjectionError(
            finding.code if finding else "TEST_ONLY_DESIGN_GATE_VALIDATION_FAILED",
            finding.message if finding else "TEST_ONLY Design Gate fixture did not validate",
        )
    return _export_validated(
        design, baseline, checked.authorization, "TEST_ONLY", output_dir,
        benchmark_only=True, generic_vnext=generic_vnext,
    )


def _node(
    title: str,
    *,
    children: list[dict] | None = None,
    component_id: str | None = None,
    custom_id: str | None = None,
) -> dict:
    if not isinstance(title, str):
        raise XMindProjectionError("CANONICAL_DESIGN_INVALID", "Canonical XMind topic titles must be strings")
    result = {"title": title, "children": children or []}
    if component_id is not None:
        result["component_id"] = component_id
    if custom_id is not None:
        result["custom_id"] = custom_id
    return result


def _scenario_topic_id(collection_id: str, design_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"test-kit-v1:{collection_id}:{design_id}"))


def _scenario_display_title(scenario_title: str) -> str:
    if scenario_title.casefold().startswith("kiểm tra "):
        return scenario_title
    if not scenario_title:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Canonical scenario title is empty")
    return "Kiểm tra " + scenario_title[0].lower() + scenario_title[1:]


def _question_display_groups(row, presentations: dict[str, str]) -> dict[str, list]:
    groups: dict[str, list] = {}
    for question in row.open_questions:
        groups.setdefault(presentations.get(question.text, question.text), []).append(question)
    return groups


def _resolve_human_facing_projection(
    design: core.DesignSnapshot,
    baseline: core.ApprovedBaseline,
    *,
    generic_vnext: bool = False,
) -> HumanFacingProjection:
    if generic_vnext:
        group_label = "Manual test scenarios"
        root_title = f"{baseline.feature_id} — {baseline.feature_title}"
        group_node = _node(group_label)
        group_by_design_id = {}
        scenario_titles = {}
        topic_ids = {}
        for row in design.records:
            if not row.design_id or row.design_id in group_by_design_id:
                raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Canonical Test Design contains an empty or duplicate design_id")
            if row.expected_behavior is None and not row.open_questions:
                raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Deferred row has no approved unresolved topic: {row.design_id}")
            group_by_design_id[row.design_id] = group_label
            title = _scenario_display_title(row.scenario_title)
            scenario_titles[row.design_id] = title
            topic_ids[row.design_id] = _scenario_topic_id(design.artifact_id, row.design_id)
            children = (
                [_node(f"{MM_PREFIX}{row.expected_behavior}")]
                if row.expected_behavior is not None
                else [_node(f"{BA_WARNING_PREFIX}{question.text}") for question in row.open_questions]
            )
            group_node["children"].append(_node(title, children=children, component_id=topic_ids[row.design_id], custom_id=row.design_id))
        config = b"TEST_KIT_VNEXT_GENERIC_XMIND_PROFILE_V1"
        return HumanFacingProjection(
            model={"sheet_title": SHEET_TITLE, "root_title": root_title, "children": [group_node]},
            group_by_design_id=group_by_design_id,
            group_labels={group_label: group_label},
            scenario_titles=scenario_titles,
            question_presentations={},
            topic_ids=topic_ids,
            profile_name="TEST_KIT_VNEXT_GENERIC_XMIND_PROFILE",
            profile_version="1",
            profile_sha256=hashlib.sha256(config).hexdigest(),
            root_title=root_title,
        )
    try:
        config_bytes = PROFILE_PATH.read_bytes()
        config = json.loads(config_bytes.decode("utf-8"))
    except (OSError, ValueError) as error:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Human-facing XMind profile is unavailable: {error}") from error

    required_config = {
        "profile", "version", "functional_groups", "business_rule_group_refs", "scenario_overrides",
        "scenario_presentations", "open_question_presentations",
        "layout", "machine_notes_allowed", "machine_labels_allowed", "machine_visible_metadata_allowed",
        "traceability_location",
    }
    if (
        not isinstance(config, dict)
        or set(config) != required_config
        or config.get("profile") != "HUMAN_FACING_XMIND_PROFILE"
        or config.get("layout") != XMIND_LAYOUT
        or config.get("machine_notes_allowed") is not False
        or config.get("machine_labels_allowed") is not False
        or config.get("machine_visible_metadata_allowed") is not False
        or config.get("traceability_location") != "EXTERNAL_PROJECTION_MANIFEST"
        or not isinstance(config.get("version"), str)
        or not isinstance(config.get("functional_groups"), list)
        or not isinstance(config.get("business_rule_group_refs"), list)
        or not isinstance(config.get("scenario_overrides"), dict)
        or not isinstance(config.get("scenario_presentations"), dict)
        or not isinstance(config.get("open_question_presentations"), list)
    ):
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Human-facing XMind profile has an unsupported shape")
    try:
        core.baseline_receipt_refs(baseline)
    except (OSError, ValueError) as error:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Approved BA inputs are stale: {error}") from error

    labels: dict[str, str] = {}
    requirements = {row.id: row for row in baseline.requirements}
    business_rules = {row.id: row for row in baseline.business_rules}
    for group in config["functional_groups"]:
        if not isinstance(group, dict) or set(group) != {"functional_ref", "label", "source_phrase"}:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Functional group mapping is malformed")
        functional_ref, label, phrase = group["functional_ref"], group["label"], group["source_phrase"]
        source = requirements.get(functional_ref)
        if (
            source is None
            or not isinstance(label, str)
            or not isinstance(phrase, str)
            or not label.strip()
            or re.search(r"\b(?:FR|BR)-\d+\b", label, re.IGNORECASE)
            or phrase.casefold() not in source.text.casefold()
            or functional_ref in labels
        ):
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Functional group is not anchored to approved BA text: {functional_ref}")
        labels[functional_ref] = label
    if len(set(labels.values())) != len(labels):
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Functional group labels must be unique")

    business_rule_groups: dict[str, str] = {}
    for mapping in config["business_rule_group_refs"]:
        if not isinstance(mapping, dict) or set(mapping) != {"business_rule_ref", "functional_ref", "source_phrase"}:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Business-rule group mapping is malformed")
        rule_ref, functional_ref, phrase = mapping["business_rule_ref"], mapping["functional_ref"], mapping["source_phrase"]
        source = business_rules.get(rule_ref)
        if (
            source is None
            or functional_ref not in labels
            or not isinstance(phrase, str)
            or phrase.casefold() not in source.text.casefold()
            or rule_ref in business_rule_groups
        ):
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Business-rule group is not anchored to approved BA text: {rule_ref}")
        business_rule_groups[rule_ref] = functional_ref

    raw_overrides = config["scenario_overrides"].get(design.artifact_id, {})
    if not isinstance(raw_overrides, dict):
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Scenario group overrides are malformed")
    raw_scenario_presentations = config["scenario_presentations"].get(design.artifact_id, {})
    if not isinstance(raw_scenario_presentations, dict):
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Scenario presentation mappings are malformed")

    question_presentations: dict[str, str] = {}
    for mapping in config["open_question_presentations"]:
        if not isinstance(mapping, dict) or set(mapping) != {"canonical_text", "visible_text"}:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Open-question presentation mapping is malformed")
        canonical_text, visible_text = mapping["canonical_text"], mapping["visible_text"]
        if (
            not isinstance(canonical_text, str)
            or not canonical_text
            or not isinstance(visible_text, str)
            or not visible_text
            or canonical_text in question_presentations
            or re.search(r"\b(?:FR|BR)-\d+\b", visible_text, re.IGNORECASE)
            or "deferred theo" in visible_text.casefold()
        ):
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Open-question presentation mapping is invalid")
        question_presentations[canonical_text] = visible_text

    group_by_design_id: dict[str, str] = {}
    scenario_titles: dict[str, str] = {}
    topic_ids: dict[str, str] = {}
    seen_ids: set[str] = set()
    for row in design.records:
        if not isinstance(row.design_id, str) or not row.design_id or row.design_id in seen_ids:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Canonical Test Design contains an empty or duplicate design_id")
        seen_ids.add(row.design_id)
        candidates = {ref for ref in row.requirement_refs if ref in labels}
        candidates.update(business_rule_groups[ref] for ref in row.requirement_refs if ref in business_rule_groups)
        override = raw_overrides.get(row.design_id)
        if override is not None:
            if (
                not isinstance(override, dict)
                or set(override) != {"functional_ref", "source_phrase"}
                or not isinstance(override["source_phrase"], str)
                or override["source_phrase"].casefold() not in row.scenario_title.casefold()
                or override["functional_ref"] not in candidates
            ):
                raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Explicit group mapping is not supported by {row.design_id} BA refs")
            selected = override["functional_ref"]
        elif len(candidates) == 1:
            selected = next(iter(candidates))
        else:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"No unambiguous BA functional group for {row.design_id}")
        group_by_design_id[row.design_id] = selected

        title_override = raw_scenario_presentations.get(row.design_id)
        if title_override is None:
            visible_title = _scenario_display_title(row.scenario_title)
        else:
            if (
                not isinstance(title_override, dict)
                or set(title_override) != {"visible_title", "source_phrase"}
                or not isinstance(title_override["visible_title"], str)
                or not isinstance(title_override["source_phrase"], str)
                or title_override["source_phrase"].casefold() not in row.scenario_title.casefold()
            ):
                raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Scenario presentation mapping is not anchored to {row.design_id}")
            visible_title = title_override["visible_title"]
        if (
            not visible_title.startswith("Kiểm tra ")
            or re.search(r"\b(?:FR|BR)-\d+\b", visible_title, re.IGNORECASE)
            or "deferred theo" in visible_title.casefold()
        ):
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Scenario title is not human-facing: {row.design_id}")
        scenario_titles[row.design_id] = visible_title
        topic_ids[row.design_id] = _scenario_topic_id(design.artifact_id, row.design_id)

        if row.expected_behavior is None and not row.open_questions:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Deferred row has no approved unresolved topic: {row.design_id}")
        if row.expected_behavior is not None and row.open_questions:
            raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Resolved row also has open questions: {row.design_id}")
        for question in row.open_questions:
            if question.status != UNKNOWN_LABEL:
                raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Open question is not marked UNKNOWN: {row.design_id}")

    if set(raw_overrides) - seen_ids:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Human-facing profile contains a stale scenario override")
    if set(raw_scenario_presentations) - seen_ids:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Human-facing profile contains a stale scenario presentation")
    known_questions = {question.text for row in design.records for question in row.open_questions}
    if set(question_presentations) - known_questions:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Human-facing profile contains a stale open-question presentation")
    if not isinstance(baseline.feature_id, str) or not baseline.feature_id or not isinstance(baseline.feature_title, str) or not baseline.feature_title:
        raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", "Approved BA feature identity is incomplete")

    root_title = f"{baseline.feature_id} — {baseline.feature_title}"
    root = _node(root_title)
    used_refs = set(group_by_design_id.values())
    group_nodes = {
        functional_ref: _node(labels[functional_ref])
        for functional_ref in labels if functional_ref in used_refs
    }
    root["children"].extend(group_nodes[functional_ref] for functional_ref in labels if functional_ref in used_refs)
    for row in design.records:
        functional_ref = group_by_design_id[row.design_id]
        if row.expected_behavior is None:
            warning_groups = _question_display_groups(row, question_presentations)
            visible_children = [
                _node(f"{BA_WARNING_PREFIX}{visible_text}")
                for visible_text, questions in warning_groups.items()
            ]
        else:
            if not isinstance(row.expected_behavior, str):
                raise XMindProjectionError("CANNOT_PROJECT_HUMAN_PROFILE", f"Expected behavior is not text: {row.design_id}")
            visible_children = [_node(f"{MM_PREFIX}{row.expected_behavior}")]
        group_nodes[functional_ref]["children"].append(
            _node(
                scenario_titles[row.design_id],
                children=visible_children,
                component_id=topic_ids[row.design_id],
                custom_id=row.design_id,
            )
        )

    return HumanFacingProjection(
        model={"sheet_title": SHEET_TITLE, "root_title": root_title, "children": root["children"]},
        group_by_design_id=group_by_design_id,
        group_labels=labels,
        scenario_titles=scenario_titles,
        question_presentations=question_presentations,
        topic_ids=topic_ids,
        profile_name=config["profile"],
        profile_version=config["version"],
        profile_sha256=hashlib.sha256(config_bytes).hexdigest(),
        root_title=root_title,
    )


def build_semantic_projection_model(design: core.DesignSnapshot, baseline: core.ApprovedBaseline) -> dict:
    return _resolve_human_facing_projection(design, baseline).model


def _safe_filename(collection_id: str) -> str:
    if not isinstance(collection_id, str):
        raise XMindProjectionError("INVALID_COLLECTION_ID", "Collection ID must be text")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", collection_id).strip("._-")[:64] or "test-design"
    suffix = hashlib.sha256(collection_id.encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{suffix}.xmind"


def _serialize_xmind(model: dict, output_dir: Path, filename: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", filename):
        raise XMindProjectionError("INVALID_OUTPUT_FILENAME", "XMind SDK filename must be a safe basename")
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir.resolve() / f"{filename}.xmind"
    adapter = ROOT / "tooling/xmind/serialize.js"
    try:
        completed = subprocess.run(
            ["node", str(adapter), str(target.parent), filename],
            input=json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            text=True,
            encoding="utf-8",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=60,
            cwd=adapter.parent,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise XMindProjectionError("XMIND_SDK_UNAVAILABLE", f"Could not run the pinned XMind SDK: {error}") from error
    if completed.returncode != 0 or not target.is_file():
        message = completed.stderr.strip() or "XMind SDK did not create an artifact"
        raise XMindProjectionError("XMIND_SERIALIZATION_FAILED", message[-2000:])
    return target


def _children(topic: dict) -> list[dict]:
    children = topic.get("children", {})
    if not isinstance(children, dict):
        raise ValueError("XMind topic children are malformed")
    attached = children.get("attached", [])
    if not isinstance(attached, list) or any(not isinstance(child, dict) for child in attached):
        raise ValueError("XMind attached topics are malformed")
    return attached


def _contains_machine_note(value) -> bool:
    if isinstance(value, str):
        if PROJECTION_METADATA_PREFIX in value:
            return True
        try:
            parsed = json.loads(value)
        except ValueError:
            return False
        return isinstance(parsed, dict) and bool(
            {"design_id", "requirement_refs", "open_questions", "record_type"} & set(parsed)
        )
    if isinstance(value, dict):
        return any(_contains_machine_note(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_machine_note(item) for item in value)
    return False


def _expected_scenario_trace(row, projection: HumanFacingProjection) -> dict:
    return {
        "design_id": row.design_id,
        "xmind_topic_id": projection.topic_ids[row.design_id],
        "scenario_title": row.scenario_title,
        "visible_scenario_title": projection.scenario_titles[row.design_id],
        "hierarchy_path": list(row.hierarchy_path),
        "functional_group_ref": projection.group_by_design_id[row.design_id],
        "expected_behavior": row.expected_behavior,
        "requirement_refs": list(row.requirement_refs),
        "outcome_state": "DEFERRED" if row.expected_behavior is None else "RESOLVED",
        "open_questions": [question.to_dict() for question in row.open_questions],
        "visible_open_question_warnings": [
            f"{BA_WARNING_PREFIX}{visible_text}"
            for visible_text in _question_display_groups(row, projection.question_presentations)
        ],
    }


def _read_projection_manifest(manifest: dict | str | Path | None) -> dict:
    if isinstance(manifest, dict):
        return manifest
    if isinstance(manifest, (str, Path)):
        value = json.loads(Path(manifest).read_text(encoding="utf-8"))
        if isinstance(value, dict):
            return value
    raise ValueError("External XMind projection manifest is required")

def _read_xmind_document(xmind_path: str | Path) -> list[dict]:
    with zipfile.ZipFile(xmind_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or set(names) != REQUIRED_XMIND_MEMBERS:
            raise ValueError("XMind package members do not match the pinned SDK structure")
        if archive.testzip() is not None:
            raise ValueError("XMind ZIP integrity check failed")
        document = json.loads(archive.read("content.json"))
        json.loads(archive.read("manifest.json"))
        json.loads(archive.read("metadata.json"))
        ET.fromstring(archive.read("content.xml"))
    if not isinstance(document, list) or len(document) != 1 or not isinstance(document[0], dict):
        raise ValueError("XMind must contain exactly one sheet")
    return document


def _walk(topic: dict):
    yield topic
    for child in _children(topic):
        yield from _walk(child)


def validate_xmind_projection(
    design: core.DesignSnapshot,
    xmind_path: str | Path,
    baseline: core.ApprovedBaseline,
    *,
    projection_manifest: dict | str | Path | None = None,
    projection: HumanFacingProjection | None = None,
) -> SemanticDiffResult:
    rows = {row.design_id: row for row in design.records}
    deferred_count = sum(row.expected_behavior is None for row in design.records)
    resolved_count = len(design.records) - deferred_count
    findings: list[str] = []
    try:
        projection = projection or _resolve_human_facing_projection(design, baseline)
        manifest = _read_projection_manifest(projection_manifest)
        artifact_sha256 = hashlib.sha256(Path(xmind_path).read_bytes()).hexdigest()
        document = _read_xmind_document(xmind_path)
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, ET.ParseError, XMindProjectionError) as error:
        return SemanticDiffResult(
            "FAIL", len(rows), 0, deferred_count, (str(error),), resolved_count=resolved_count,
        )

    expected_trace = [_expected_scenario_trace(row, projection) for row in design.records]
    if manifest.get("projection_type") != "XMIND":
        findings.append("Projection manifest type is not XMIND")
    if (
        manifest.get("presentation_profile") != projection.profile_name
        or manifest.get("presentation_profile_version") != projection.profile_version
        or manifest.get("presentation_config_sha256") != projection.profile_sha256
    ):
        findings.append("Projection manifest presentation profile binding changed")
    if (
        manifest.get("canonical_collection_id") != design.artifact_id
        or manifest.get("canonical_revision") != design.revision
        or manifest.get("canonical_semantic_sha256") != design.sha256
    ):
        findings.append("Projection manifest is not bound to the current canonical design")
    model_bytes = json.dumps(projection.model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if manifest.get("semantic_projection_sha256") != hashlib.sha256(model_bytes).hexdigest():
        findings.append("Projection manifest semantic model hash changed")
    if manifest.get("projection_status") != "PASS" or manifest.get("semantic_diff") != "PASS":
        findings.append("Projection manifest does not record a passing projection")
    if manifest.get("authority") != "DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH":
        findings.append("Projection manifest authority classification changed")
    if (
        manifest.get("layout") != XMIND_LAYOUT
        or manifest.get("root_structure_class") != ROOT_STRUCTURE_CLASS
        or manifest.get("machine_notes_allowed") is not False
        or manifest.get("machine_labels_allowed") is not False
        or manifest.get("machine_visible_metadata_allowed") is not False
        or manifest.get("traceability_location") != "EXTERNAL_PROJECTION_MANIFEST"
    ):
        findings.append("Projection manifest human-facing profile contract changed")
    expected_group_refs = list(dict.fromkeys(projection.group_by_design_id.values()))
    expected_group_names = [projection.group_labels[ref] for ref in projection.group_labels if ref in expected_group_refs]
    expected_group_trace = [
        {"functional_group_ref": ref, "visible_label": projection.group_labels[ref]}
        for ref in expected_group_refs
    ]
    if manifest.get("business_group_names") != expected_group_names or manifest.get("business_group_trace") != expected_group_trace:
        findings.append("Projection manifest functional group trace changed")
    if manifest.get("scenario_trace") != expected_trace:
        findings.append("Projection manifest scenario trace differs from Canonical Test Design")
    if manifest.get("scenario_topic_count") != len(rows):
        findings.append("Projection manifest scenario count changed")
    if manifest.get("resolved_scenario_count") != resolved_count or manifest.get("deferred_topic_count") != deferred_count:
        findings.append("Projection manifest resolved/deferred counts changed")
    if manifest.get("canonical_open_question_record_count") != sum(len(row.open_questions) for row in design.records):
        findings.append("Projection manifest open-question record count changed")
    if manifest.get("generated_xmind_sha256") != artifact_sha256:
        findings.append("Projection manifest XMind SHA-256 does not match the serialized artifact")

    sheet = document[0]
    root = sheet.get("rootTopic")
    if sheet.get("title") != SHEET_TITLE or not isinstance(root, dict):
        return SemanticDiffResult("FAIL", len(rows), 0, deferred_count, ("XMind sheet or root topic changed",), resolved_count=resolved_count)
    if root.get("title") != projection.root_title:
        findings.append("Feature root does not match the approved BA feature title")

    try:
        visible_topics = list(_walk(root))
        group_topics = _children(root)
    except (TypeError, ValueError) as error:
        return SemanticDiffResult("FAIL", len(rows), 0, deferred_count, (f"Malformed visible XMind tree: {error}",), resolved_count=resolved_count)

    expected_group_refs = list(dict.fromkeys(projection.group_by_design_id.values()))
    expected_group_names = [projection.group_labels[ref] for ref in projection.group_labels if ref in expected_group_refs]
    actual_group_names = [group.get("title") if isinstance(group.get("title"), str) else None for group in group_topics]
    if actual_group_names != expected_group_names:
        findings.append("Visible business grouping does not match the approved BA functional mapping")

    visible_titles = [topic.get("title") for topic in visible_topics]
    visible_titles = [title for title in visible_titles if isinstance(title, str)]
    forbidden_count = sum(title in FORBIDDEN_VISIBLE_TITLES for title in visible_titles)
    if forbidden_count:
        findings.append("Forbidden technical presentation nodes are visible")
    visible_requirement_ref_count = sum(len(re.findall(r"\b(?:FR|BR)-\d+\b", title, re.IGNORECASE)) for title in visible_titles)
    if visible_requirement_ref_count:
        findings.append("Requirement IDs are visible on the human-facing canvas")
    visible_deferred_marker_count = sum(title.casefold().count("deferred theo") for title in visible_titles)
    if visible_deferred_marker_count:
        findings.append("Technical deferred refs are visible on the human-facing canvas")
    visible_mm_count = sum(title.startswith(MM_PREFIX) for title in visible_titles)
    visible_warning_count = sum(title.startswith(BA_WARNING_PREFIX) for title in visible_titles)
    root_structure_class = root.get("structureClass") if isinstance(root.get("structureClass"), str) else None
    xmind_layout = XMIND_LAYOUT if root_structure_class == ROOT_STRUCTURE_CLASS else None
    if root_structure_class != ROOT_STRUCTURE_CLASS:
        findings.append("XMind content.json root does not use Logic Chart Right structure")

    content_json_notes_key_count = sum("notes" in topic for topic in visible_topics)
    machine_readable_note_count = sum(
        _contains_machine_note(topic.get("notes")) for topic in visible_topics if "notes" in topic
    )
    machine_label_count = 0
    machine_labels_present = False
    forbidden_surface_keys = {"notes", "labels", "hyperlink", "href", "comments", "comment", "callout", "callouts", "summary", "summaries", "markers", "marker"}
    for topic in visible_topics:
        machine_labels_present = machine_labels_present or "labels" in topic
        labels = topic.get("labels")
        if isinstance(labels, list):
            machine_label_count += len(labels)
        elif labels:
            machine_label_count += 1
        if set(topic) & forbidden_surface_keys:
            findings.append("Machine material is present in an XMind Human UX surface")
        if set(topic) - {"id", "customId", "title", "style", "children", "structureClass"}:
            findings.append("Unexpected technical topic metadata is present in content.json")
    content_json_text = json.dumps(document, ensure_ascii=False, sort_keys=True)
    if PROJECTION_METADATA_PREFIX in content_json_text:
        findings.append("Machine projection metadata is embedded in content.json")
    if content_json_notes_key_count:
        findings.append("content.json topics contain Notes; the Human-facing profile prohibits Notes")
    if machine_labels_present or machine_label_count:
        findings.append("content.json topics contain labels; the Human-facing profile prohibits labels")

    if manifest.get("content_json_notes_key_count") != content_json_notes_key_count:
        findings.append("Projection manifest Notes count does not match content.json")
    if manifest.get("machine_readable_note_count") != machine_readable_note_count:
        findings.append("Projection manifest machine Notes count does not match content.json")
    if manifest.get("machine_label_count") != machine_label_count:
        findings.append("Projection manifest machine label count does not match content.json")
    if manifest.get("visible_requirement_ref_count") != visible_requirement_ref_count:
        findings.append("Projection manifest visible requirement-ref count does not match content.json")
    if manifest.get("visible_deferred_marker_count") != visible_deferred_marker_count:
        findings.append("Projection manifest visible deferred-marker count does not match content.json")
    if manifest.get("visible_mm_count") != visible_mm_count or manifest.get("visible_ba_warning_count") != visible_warning_count:
        findings.append("Projection manifest visible outcome counts do not match content.json")

    group_ref_by_title = {projection.group_labels[ref]: ref for ref in expected_group_refs}
    scenario_entries: list[tuple[dict, str | None]] = []
    for group in group_topics:
        group_title = group.get("title")
        actual_group_ref = group_ref_by_title.get(group_title) if isinstance(group_title, str) else None
        for scenario in _children(group):
            scenario_entries.append((scenario, actual_group_ref))

    if len(scenario_entries) != len(rows):
        findings.append(f"Canonical row count {len(rows)} does not match visible scenario count {len(scenario_entries)}")

    trace = manifest.get("scenario_trace")
    trace_by_topic_id = {}
    if isinstance(trace, list):
        for trace_row in trace:
            if (
                isinstance(trace_row, dict)
                and isinstance(trace_row.get("xmind_topic_id"), str)
                and isinstance(trace_row.get("design_id"), str)
                and trace_row["design_id"] in rows
            ):
                trace_by_topic_id[trace_row["xmind_topic_id"]] = trace_row
    found: dict[str, list[tuple[dict, str | None, dict]]] = {}
    for scenario, actual_group_ref in scenario_entries:
        component_id = scenario.get("id")
        scenario_trace = trace_by_topic_id.get(component_id)
        if scenario_trace is None:
            findings.append(f"Scenario component ID is absent from the projection manifest: {component_id}")
            continue
        design_id = scenario_trace["design_id"]
        found.setdefault(design_id, []).append((scenario, actual_group_ref, scenario_trace))

    for design_id, row in rows.items():
        entries = found.get(design_id, [])
        if not entries:
            findings.append(f"Missing scenario topic for {design_id}")
            continue
        if len(entries) > 1:
            findings.append(f"Duplicate scenario topic for {design_id}")
        scenario, actual_group_ref, trace_row = entries[0]
        expected_group_ref = projection.group_by_design_id[design_id]
        if scenario.get("id") != projection.topic_ids[design_id]:
            findings.append(f"XMind component ID does not identify {design_id}")
        if scenario.get("customId") != design_id:
            findings.append(f"XMind SDK custom component ID does not identify {design_id}")
        if scenario.get("title") != trace_row.get("visible_scenario_title"):
            findings.append(f"Visible scenario title changed for {design_id}")
        if actual_group_ref != expected_group_ref or trace_row.get("functional_group_ref") != expected_group_ref:
            findings.append(f"Functional grouping is not traceable for {design_id}")
        if trace_row.get("hierarchy_path") != list(row.hierarchy_path):
            findings.append(f"Canonical hierarchy metadata changed for {design_id}")
        if trace_row.get("requirement_refs") != list(row.requirement_refs):
            findings.append(f"Requirement refs changed for {design_id}")
        expected_state = "DEFERRED" if row.expected_behavior is None else "RESOLVED"
        if trace_row.get("outcome_state") != expected_state or trace_row.get("expected_behavior") != row.expected_behavior:
            findings.append(f"Resolved/deferred state or expected behavior changed for {design_id}")
        if trace_row.get("scenario_title") != row.scenario_title:
            findings.append(f"Canonical scenario title changed in projection manifest for {design_id}")
        if trace_row.get("open_questions") != [question.to_dict() for question in row.open_questions]:
            findings.append(f"Canonical open questions changed in projection manifest for {design_id}")

        children = _children(scenario)
        if row.expected_behavior is not None:
            if row.open_questions or len(children) != 1 or children[0].get("title") != f"{MM_PREFIX}{row.expected_behavior}":
                findings.append(f"Visible MM behavior changed for {design_id}")
            elif _children(children[0]):
                findings.append(f"MM behavior has unexpected nested content for {design_id}")
        else:
            expected_warnings = trace_row.get("visible_open_question_warnings")
            if not row.open_questions or not isinstance(expected_warnings, list):
                findings.append(f"Deferred manifest warning trace is missing for {design_id}")
                expected_warnings = []
            if len(children) != len(expected_warnings) or [child.get("title") for child in children] != expected_warnings:
                findings.append(f"Visible Chờ BA warnings changed for {design_id}")
            if any(_children(child) for child in children):
                findings.append(f"Visible Chờ BA warning has unexpected nested content for {design_id}")

    for design_id in found:
        if design_id not in rows:
            findings.append(f"Invented scenario topic: {design_id}")
    return SemanticDiffResult(
        "PASS" if not findings else "FAIL",
        len(rows),
        len(scenario_entries),
        deferred_count,
        tuple(dict.fromkeys(findings)),
        resolved_count=resolved_count,
        group_names=tuple(actual_group_names),
        visible_mm_count=visible_mm_count,
        visible_ba_warning_count=visible_warning_count,
        forbidden_technical_node_count=forbidden_count,
        root_structure_class=root_structure_class,
        xmind_layout=xmind_layout,
        content_json_notes_key_count=content_json_notes_key_count,
        machine_readable_note_count=machine_readable_note_count,
        machine_label_count=machine_label_count,
        visible_requirement_ref_count=visible_requirement_ref_count,
        visible_deferred_marker_count=visible_deferred_marker_count,
    )

def _render_tree_preview(xmind_path: str | Path) -> str:
    root = _read_xmind_document(xmind_path)[0]["rootTopic"]
    lines = [root["title"]]

    def append_children(parent: dict, prefix: str) -> None:
        children = _children(parent)
        for index, child in enumerate(children):
            is_last = index == len(children) - 1
            lines.append(prefix + ("└── " if is_last else "├── ") + child["title"])
            append_children(child, prefix + ("    " if is_last else "│   "))

    append_children(root, "")
    return "\n".join(lines) + "\n"


def _export_validated(
    design: core.DesignSnapshot,
    baseline: core.ApprovedBaseline,
    authorization: cases.DesignGateAuthorization,
    receipt_mode: str,
    output_dir: str | Path,
    *,
    benchmark_only: bool = False,
    generic_vnext: bool = False,
) -> XMindExportResult:
    pin = _read_pin()
    projection = _resolve_human_facing_projection(design, baseline, generic_vnext=generic_vnext)
    model = projection.model
    model_bytes = json.dumps(model, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    model_sha256 = hashlib.sha256(model_bytes).hexdigest()
    output = Path(output_dir).resolve()
    if benchmark_only and not core.is_test_only_workspace_path(output):
        raise XMindProjectionError("TEST_ONLY_OUTPUT_OUTSIDE_EVIDENCE", "TEST_ONLY XMind output must use a temporary directory or .work/benchmark-runs")
    filename = _safe_filename(design.artifact_id)
    xmind_path = output / filename
    manifest_path = output / f"{filename}.projection.json"
    tree_preview_path = output / f"{filename}.tree.txt"
    if any(path.exists() for path in (xmind_path, manifest_path, tree_preview_path)):
        raise XMindProjectionError("PROJECTION_OUTPUT_EXISTS", "XMind projection output already exists")
    output.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=".xmind-projection-", dir=output) as temporary:
        sdk_name = Path(filename).stem
        candidate = _serialize_xmind(model, Path(temporary), sdk_name)
        generated_sha256 = hashlib.sha256(candidate.read_bytes()).hexdigest()
        preview_bytes = _render_tree_preview(candidate).encode("utf-8")
        receipt_ref = {
            "path": f"design-gate/revisions/{design.revision}/receipt.json",
            "sha256": authorization.receipt_sha256,
        }
        scenario_trace = [_expected_scenario_trace(row, projection) for row in design.records]
        group_refs = list(dict.fromkeys(projection.group_by_design_id.values()))
        group_names = [projection.group_labels[ref] for ref in projection.group_labels if ref in group_refs]
        resolved_count = sum(row.expected_behavior is not None for row in design.records)
        deferred_count = len(design.records) - resolved_count
        visible_mm_count = resolved_count
        visible_ba_warning_count = sum(
            len(_question_display_groups(row, projection.question_presentations))
            for row in design.records if row.expected_behavior is None
        )
        manifest = {
            "projection_type": "XMIND",
            "presentation_profile": projection.profile_name,
            "presentation_profile_version": projection.profile_version,
            "presentation_config_sha256": projection.profile_sha256,
            "layout": XMIND_LAYOUT,
            "root_structure_class": ROOT_STRUCTURE_CLASS,
            "machine_notes_allowed": False,
            "machine_labels_allowed": False,
            "machine_visible_metadata_allowed": False,
            "traceability_location": "EXTERNAL_PROJECTION_MANIFEST",
            "exporter_version": EXPORTER_VERSION,
            "semantic_model_version": SEMANTIC_MODEL_VERSION,
            "canonical_collection_id": design.artifact_id,
            "canonical_revision": design.revision,
            "canonical_semantic_sha256": design.sha256,
            "design_gate_receipt_ref": receipt_ref,
            "design_gate_receipt_mode": receipt_mode,
            "current_input_refs": [
                {"id": ref_id, "revision": revision, "sha256": digest}
                for ref_id, revision, digest in authorization.input_refs
            ],
            "generated_xmind_sha256": generated_sha256,
            "semantic_projection_sha256": model_sha256,
            "upstream_xmind_sdk": {
                "package": pin["package"],
                "version": pin["version"],
                "repository": pin["repository"],
                "revision": pin["revision"],
                "license": pin["license"],
                "integrity": pin["integrity"],
            },
            "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "projection_status": "PASS",
            "scenario_topic_count": len(design.records),
            "resolved_scenario_count": resolved_count,
            "deferred_topic_count": deferred_count,
            "business_group_count": len(group_names),
            "business_group_names": group_names,
            "business_group_trace": [
                {"functional_group_ref": ref, "visible_label": projection.group_labels[ref]}
                for ref in group_refs
            ],
            "canonical_open_question_record_count": sum(len(row.open_questions) for row in design.records),
            "content_json_notes_key_count": 0,
            "machine_readable_note_count": 0,
            "machine_label_count": 0,
            "visible_requirement_ref_count": 0,
            "visible_deferred_marker_count": 0,
            "visible_mm_count": visible_mm_count,
            "visible_ba_warning_count": visible_ba_warning_count,
            "forbidden_technical_visible_node_count": 0,
            "scenario_trace": scenario_trace,
            "tree_preview": {
                "path": tree_preview_path.name,
                "sha256": hashlib.sha256(preview_bytes).hexdigest(),
            },
            "semantic_diff": "PASS",
            "authority": "DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH",
        }
        diff = validate_xmind_projection(
            design,
            candidate,
            baseline,
            projection_manifest=manifest,
            projection=projection,
        )
        if diff.status != "PASS":
            raise XMindProjectionError("XMIND_SEMANTIC_DIFF_FAIL", "; ".join(diff.findings))
        temporary_manifest = Path(temporary) / f"{filename}.projection.json"
        temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary_preview = Path(temporary) / f"{filename}.tree.txt"
        temporary_preview.write_bytes(preview_bytes)
        created: list[Path] = []
        try:
            for target, source in (
                (xmind_path, candidate),
                (manifest_path, temporary_manifest),
                (tree_preview_path, temporary_preview),
            ):
                with target.open("xb") as output_file:
                    created.append(target)
                    output_file.write(source.read_bytes())
        except OSError:
            for target in created:
                target.unlink(missing_ok=True)
            raise
    return XMindExportResult(xmind_path, manifest_path, tree_preview_path, diff)
