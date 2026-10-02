"""Test Kit V1 Canonical Testcase flow, pinned Katalon adapter, and Case Review gate."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
from contextlib import nullcontext
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

from . import test_kit_v1 as foundation
from .codex_cli import CodexCommand, resolve_codex_command


ROOT = Path(__file__).resolve().parents[2]
TEST_ONLY_PROVENANCE_PIN = ROOT / "tooling/pins/test-only-provenance-relocations-v1.json"
KATALON_PIN_PATH = ROOT / "tooling/pins/katalon-create-test-cases-v1.json"
KATALON_PIN = json.loads(KATALON_PIN_PATH.read_text(encoding="utf-8"))
KATALON_REPOSITORY = KATALON_PIN["repository"]
KATALON_COMMIT = KATALON_PIN["commit"]
KATALON_CAPABILITY = KATALON_PIN["capability"]
KATALON_SKILL_FILES = KATALON_PIN["files"]
KATALON_REQUIRED_SKILL_FILES = tuple(KATALON_SKILL_FILES)
CASE_SEMANTIC_FIELDS = (
    "test_case_id",
    "name",
    "objective",
    "preconditions",
    "test_data",
    "steps",
    "priority",
    "requirement_refs",
    "test_design_refs",
    "execution_dependencies",
)
CASE_RECORD_FIELDS = (*CASE_SEMANTIC_FIELDS, "review_status")
RECEIPT_FIELDS = {
    "gate", "decision", "artifact_id", "artifact_revision", "artifact_sha256",
    "input_refs", "actor_id", "actor_role", "decided_at", "feedback",
}
BENCHMARK_LABELS = (
    "Objective", "Preconditions", "Test Data", "Priority", "Requirement refs", "Test Design refs",
)
NATIVE_LABELS = (
    "Mô tả", "Tiền điều kiện", "Bước và kết quả mong đợi", "Test Data", "Priority", "Trace",
)
CASE_HEADING = re.compile(r"(?m)^##\s+(TC-[A-Za-z0-9][A-Za-z0-9._-]*)(?:\s+(.+?))?\s*$")
CASE_SHAPED_HEADING = re.compile(r"(?mi)^#{1,6}\s+TC(?:-[^\s]*)?(?:\s|$).*$")
CASE_ID_TOKEN = re.compile(r"(?<![\w.-])TC-[A-Za-z0-9][A-Za-z0-9._-]*(?![\w.-])", re.IGNORECASE)
ANY_HEADING = re.compile(r"(?m)^#{1,6}\s+.+$\n?")
REF_TOKEN = re.compile(r"(?<![\w.-])(?:FR|BR|TD)-[A-Za-z0-9_-]+|(?<![\w.-])\d+(?:\.\d+)?-(?:UNIT|INT|E2E|EXP)-\d+(?![\w-])")
INVALID_REF = re.compile(r"(?<![\w.-])(?:FR|BR|TD)-[A-Za-z0-9_-]*[A-Za-z_][A-Za-z0-9_-]*")
STEP_ARROW = re.compile(r"^\s*(\d+)\.\s+(.+?)\s+→\s+(.+?)\s*$")


@dataclass(frozen=True)
class CaseStep:
    action: str
    test_data: str | None
    expected_result: str

    def to_dict(self) -> dict:
        return {"action": self.action, "test_data": self.test_data, "expected_result": self.expected_result}


@dataclass(frozen=True)
class ExecutionDependency:
    need: str
    material: bool
    status: str
    resolution_ref: str | None

    def to_dict(self) -> dict:
        return {
            "need": self.need,
            "material": self.material,
            "status": self.status,
            "resolution_ref": self.resolution_ref,
        }


@dataclass(frozen=True)
class CanonicalTestcase:
    test_case_id: str
    name: str
    objective: str
    preconditions: str
    test_data: str | None
    steps: tuple[CaseStep, ...]
    priority: str
    requirement_refs: tuple[str, ...]
    test_design_refs: tuple[str, ...]
    execution_dependencies: tuple[ExecutionDependency, ...]
    review_status: str = "DRAFT"

    def semantic_dict(self) -> dict:
        return {
            "test_case_id": self.test_case_id,
            "name": self.name,
            "objective": self.objective,
            "preconditions": self.preconditions,
            "test_data": self.test_data,
            "steps": [step.to_dict() for step in self.steps],
            "priority": self.priority,
            "requirement_refs": list(self.requirement_refs),
            "test_design_refs": list(self.test_design_refs),
            "execution_dependencies": [dependency.to_dict() for dependency in self.execution_dependencies],
        }

    def to_dict(self) -> dict:
        return {**self.semantic_dict(), "review_status": self.review_status}


@dataclass(frozen=True)
class CaseSnapshot:
    artifact_id: str
    revision: str
    records: tuple[CanonicalTestcase, ...]
    payload_bytes: bytes
    sha256: str
    evidence: tuple[foundation.RawEvidenceRef, ...] = ()
    field_sources: dict[str, dict[str, foundation.RawEvidenceRef]] | None = None

    @classmethod
    def create(
        cls,
        records: Iterable[CanonicalTestcase],
        *,
        artifact_id: str,
        revision: str,
        evidence: Iterable[foundation.RawEvidenceRef] = (),
        field_sources: dict[str, dict[str, foundation.RawEvidenceRef]] | None = None,
    ) -> "CaseSnapshot":
        records = tuple(records)
        payload = json.dumps(
            [record.semantic_dict() for record in records], ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
        return cls(
            artifact_id, revision, records, payload, hashlib.sha256(payload).hexdigest(),
            tuple(evidence), field_sources or {},
        )

    def project(self, status: str) -> "CaseSnapshot":
        if status not in {"DRAFT", "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED"}:
            raise ValueError("unsupported testcase review projection")
        return replace(self, records=tuple(replace(row, review_status=status) for row in self.records))


@dataclass(frozen=True)
class CaseNormalizationResult:
    status: str
    profile: str | None
    snapshot: CaseSnapshot | None
    findings: tuple[foundation.Finding, ...]
    evidence: tuple[foundation.RawEvidenceRef, ...]


@dataclass(frozen=True)
class CaseValidatorResult:
    status: str
    findings: tuple[foundation.Finding, ...]
    artifact_id: str
    artifact_revision: str
    artifact_sha256: str


@dataclass(frozen=True)
class DesignGateAuthorization:
    artifact_id: str
    artifact_revision: str
    artifact_sha256: str
    input_refs: tuple[tuple[str, str, str], ...]
    test_only: bool = False
    receipt_path: str = ""
    receipt_sha256: str = ""


AuthenticatedHumanActorContext = foundation.AuthenticatedHumanActorContext


@dataclass(frozen=True)
class TestOnlyHumanActorContext:
    actor_id: str
    actor_role: str = "HUMAN"


@dataclass(frozen=True)
class GateReceiptResult:
    status: str
    finding: foundation.Finding | None
    authorization: DesignGateAuthorization | None = None
    human_actor: AuthenticatedHumanActorContext | TestOnlyHumanActorContext | None = None
    findings: tuple[foundation.Finding, ...] = ()


@dataclass(frozen=True)
class KatalonInput:
    markdown: str
    design_sha256: str
    ba_refs: tuple[dict, ...]
    execution_refs: tuple[dict, ...]


@dataclass(frozen=True)
class CaseWorkflowState:
    state: str
    artifact_id: str
    artifact_revision: str
    artifact_sha256: str
    review_status: str
    validation_status: str
    execution_contract_refs: tuple[str, ...] = ()
    design_gate_receipt_mode: str | None = None
    design_gate_receipt_evidence: dict | None = None
    input_refs: tuple[tuple[str, str, str], ...] = ()
    execution_oracle_refs: tuple[dict, ...] = ()
    project_policy_context: dict | None = None


@dataclass(frozen=True)
class ApprovedTestware:
    payload_bytes: bytes
    sha256: str

    def to_dict(self) -> dict:
        return json.loads(self.payload_bytes)


@dataclass(frozen=True)
class CaseGateDecisionResult:
    status: str
    finding: foundation.Finding | None
    findings: tuple[foundation.Finding, ...]
    workflow: CaseWorkflowState
    reviewed_snapshot: CaseSnapshot
    next_snapshot: CaseSnapshot | None = None
    receipt_bytes: bytes | None = None
    receipt_sha256: str | None = None
    approved_testware: ApprovedTestware | None = None
    state_history: tuple[str, ...] = ()
    test_only: bool = False


@dataclass(frozen=True)
class CaseIntegrationResult:
    status: str
    invocation_manifest: dict
    normalization: CaseNormalizationResult
    validation: CaseValidatorResult | None
    workflow: CaseWorkflowState | None


def _hash_path(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ProvenanceResolutionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _resolve_provenance_reference(
    reference: str,
    expected_sha256: str,
    *,
    allow_test_only: bool,
    test_only: bool,
    relocations: dict | None = None,
) -> Path:
    if not isinstance(reference, str) or not reference:
        raise ProvenanceResolutionError("PROVENANCE_REFERENCE_MISSING", "provenance path is missing")
    if not isinstance(expected_sha256, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("provenance SHA-256 is invalid")

    original = Path(reference).resolve()
    if original.exists():
        if not original.is_file():
            raise ProvenanceResolutionError("PROVENANCE_REFERENCE_INVALID", f"provenance reference is not a file: {reference}")
        if _hash_path(original) != expected_sha256.lower():
            raise ProvenanceResolutionError("PROVENANCE_HASH_MISMATCH", f"original provenance bytes do not match SHA-256: {reference}")
        return original

    if not (allow_test_only and test_only):
        raise ProvenanceResolutionError("PROVENANCE_REFERENCE_MISSING", f"original provenance reference is missing: {reference}")
    if relocations is None:
        try:
            pin = json.loads(TEST_ONLY_PROVENANCE_PIN.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise ProvenanceResolutionError("PROVENANCE_RELOCATION_INVALID", f"TEST_ONLY provenance mapping is unavailable: {error}") from error
        if not isinstance(pin, dict) or pin.get("scope") != "TEST_ONLY_EXPLICIT_MAPPING" or not isinstance(pin.get("references"), dict):
            raise ProvenanceResolutionError("PROVENANCE_RELOCATION_INVALID", "TEST_ONLY provenance mapping has an invalid scope or shape")
        relocations = pin["references"]

    entry = relocations.get(reference)
    if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "scope"}:
        raise ProvenanceResolutionError("PROVENANCE_REFERENCE_MISSING", f"no exact TEST_ONLY relocation is pinned for: {reference}")
    if entry.get("scope") != "TEST_ONLY_FIXTURE":
        raise ProvenanceResolutionError("PROVENANCE_RELOCATION_INVALID", f"relocation is outside TEST_ONLY fixture scope: {reference}")
    if not isinstance(entry.get("path"), str) or not entry["path"]:
        raise ProvenanceResolutionError("PROVENANCE_RELOCATION_INVALID", f"relocation target path is invalid: {reference}")
    if str(entry.get("sha256", "")).lower() != expected_sha256.lower():
        raise ProvenanceResolutionError("PROVENANCE_HASH_MISMATCH", f"pinned relocation hash disagrees with provenance reference: {reference}")
    relative = Path(entry.get("path", ""))
    fixture_root = (ROOT / "benchmark/test-kit/petclinic/fixtures").resolve()
    relocated = (ROOT / relative).resolve()
    if relative.is_absolute() or ".." in relative.parts or not relocated.is_relative_to(fixture_root):
        raise ProvenanceResolutionError("PROVENANCE_RELOCATION_INVALID", f"relocation target is not a repository fixture: {reference}")
    if not relocated.is_file():
        raise ProvenanceResolutionError("PROVENANCE_REFERENCE_MISSING", f"pinned TEST_ONLY fixture is missing: {entry['path']}")
    if _hash_path(relocated) != expected_sha256.lower():
        raise ProvenanceResolutionError("PROVENANCE_HASH_MISMATCH", f"pinned TEST_ONLY fixture bytes do not match SHA-256: {entry['path']}")
    return relocated


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def baseline_receipt_refs(baseline: foundation.ApprovedBaseline) -> list[dict]:
    return foundation.baseline_receipt_refs(baseline)


def case_gate_input_refs(
    baseline: foundation.ApprovedBaseline, design: foundation.DesignSnapshot,
    *, run_dir: str | Path | None = None,
) -> list[dict]:
    refs = baseline_receipt_refs(baseline) + [
        {"id": design.artifact_id, "revision": design.revision, "sha256": design.sha256}
    ]
    policy_ref = foundation.current_project_policy_ref(run_dir, "CASES") if run_dir is not None else None
    return refs + ([policy_ref] if policy_ref else [])


def load_design_snapshot(
    canonical_path: str | Path,
    workflow_path: str | Path,
    semantic_payload_path: str | Path,
) -> foundation.DesignSnapshot:
    canonical_path, workflow_path, semantic_payload_path = map(
        lambda path: Path(path).resolve(), (canonical_path, workflow_path, semantic_payload_path)
    )
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    raw_records = json.loads(canonical_path.read_text(encoding="utf-8"))
    if not isinstance(raw_records, list) or any(not isinstance(row, dict) or set(row) != set(foundation.RECORD_FIELDS) for row in raw_records):
        raise ValueError("canonical Test Design records do not match the frozen schema")
    records = tuple(
        foundation.CanonicalTestDesign(
            row["design_id"], tuple(row["hierarchy_path"]), row["scenario_title"],
            row["expected_behavior"], tuple(row["requirement_refs"]),
            tuple(foundation.OpenQuestion(**question) for question in row["open_questions"]),
            row["review_status"],
        )
        for row in raw_records
    )
    snapshot = foundation.DesignSnapshot.create(
        records,
        artifact_id=workflow["artifact_id"],
        revision=workflow["artifact_revision"],
        evidence=(
            foundation.RawEvidenceRef(str(canonical_path), _hash_path(canonical_path), field="canonical_test_design"),
            foundation.RawEvidenceRef(str(semantic_payload_path), _hash_path(semantic_payload_path), field="semantic_payload"),
        ),
    )
    exact_payload = semantic_payload_path.read_bytes()
    if snapshot.payload_bytes != exact_payload or snapshot.sha256 != workflow["artifact_sha256"]:
        raise ValueError("canonical Test Design does not match its immutable semantic payload and workflow hash")
    if workflow.get("state") not in {"DESIGN_REVIEW", "APPROVED_DESIGN"}:
        raise ValueError("Test Design is not at the Design Gate boundary")
    return snapshot


def load_case_review_snapshot(
    canonical_path: str | Path,
    workflow_path: str | Path,
    semantic_payload_path: str | Path,
    *,
    input_manifest_path: str | Path | None = None,
) -> tuple[CaseSnapshot, CaseWorkflowState]:
    canonical_path, workflow_path, semantic_payload_path = map(
        lambda path: Path(path).resolve(), (canonical_path, workflow_path, semantic_payload_path)
    )
    workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    raw_records = json.loads(canonical_path.read_text(encoding="utf-8"))
    if not isinstance(raw_records, list) or any(not isinstance(row, dict) or set(row) != set(CASE_RECORD_FIELDS) for row in raw_records):
        raise ValueError("canonical Testcases do not match the frozen schema")
    records = tuple(
        CanonicalTestcase(
            row["test_case_id"], row["name"], row["objective"], row["preconditions"], row["test_data"],
            tuple(CaseStep(**step) for step in row["steps"]), row["priority"],
            tuple(row["requirement_refs"]), tuple(row["test_design_refs"]),
            tuple(ExecutionDependency(**dependency) for dependency in row["execution_dependencies"]),
            row["review_status"],
        )
        for row in raw_records
    )
    snapshot = CaseSnapshot.create(
        records,
        artifact_id=workflow["artifact_id"],
        revision=workflow["artifact_revision"],
        evidence=(
            foundation.RawEvidenceRef(str(canonical_path), _hash_path(canonical_path), field="canonical_testcases"),
            foundation.RawEvidenceRef(str(semantic_payload_path), _hash_path(semantic_payload_path), field="semantic_payload"),
        ),
    )
    if (
        snapshot.payload_bytes != semantic_payload_path.read_bytes()
        or snapshot.sha256 != workflow["artifact_sha256"]
        or workflow.get("state") != "CASE_REVIEW"
        or workflow.get("review_status") != "IN_REVIEW"
        or workflow.get("validation_status") != "PASS"
        or any(record.review_status != "IN_REVIEW" for record in snapshot.records)
    ):
        raise ValueError("Case Review evidence does not match its immutable testcase snapshot and state")
    _verify_loaded_case_review_raw_evidence(workflow_path.parent)

    execution_refs = workflow.get("execution_contract_refs", [])
    execution_oracle_refs = workflow.get("execution_oracle_refs", [])
    design_receipt_mode = workflow.get("design_gate_receipt_mode")
    design_receipt_evidence = workflow.get("design_gate_receipt_evidence")
    input_refs = workflow.get("input_refs", [])
    if input_manifest_path is not None:
        input_manifest = json.loads(Path(input_manifest_path).resolve().read_text(encoding="utf-8"))
        if not execution_refs:
            execution_refs = input_manifest.get("execution_contract_refs", [])
        if not execution_oracle_refs:
            execution_oracle_refs = input_manifest.get("execution_contract_refs", [])
        design_receipt_mode = design_receipt_mode or input_manifest.get("receipt_mode")
        design_receipt_evidence = design_receipt_evidence or input_manifest.get("design_gate_receipt_evidence")
        if not input_refs:
            input_refs = list(input_manifest.get("ba_input_refs", [])) + [
                {
                    "id": input_manifest["design"]["artifact_id"],
                    "revision": input_manifest["design"]["revision"],
                    "sha256": input_manifest["design"]["sha256"],
                }
            ]
    signature = _execution_contract_signature(execution_oracle_refs)
    input_signature = _input_ref_signature(input_refs)
    return snapshot, CaseWorkflowState(
        workflow["state"], snapshot.artifact_id, snapshot.revision, snapshot.sha256,
        workflow["review_status"], workflow["validation_status"], signature,
        design_receipt_mode, design_receipt_evidence, input_signature,
        tuple(dict(ref) for ref in execution_oracle_refs),
        workflow.get("project_policy_context"),
    )


def _receipt_refs(receipt: dict) -> tuple[tuple[str, str, str], ...] | None:
    values = receipt.get("input_refs")
    if not isinstance(values, list):
        return None
    refs = []
    for value in values:
        if not isinstance(value, dict) or set(value) != {"id", "revision", "sha256"}:
            return None
        if not all(isinstance(value[key], str) and value[key].strip() for key in value):
            return None
        refs.append((value["id"], value["revision"], value["sha256"].lower()))
    if len(refs) != len(set(refs)):
        return None
    return tuple(refs)


def _receipt_shape_finding(receipt: object, gate: str) -> foundation.Finding | None:
    if not isinstance(receipt, dict):
        return foundation.Finding("MISSING_DESIGN_GATE_RECEIPT" if gate == "DESIGN_REVIEW" else "MISSING_CASE_GATE_RECEIPT", f"{gate} requires an immutable Human receipt")
    if set(receipt) != RECEIPT_FIELDS:
        return foundation.Finding("INVALID_GATE_RECEIPT_SCHEMA", "gate receipt fields do not match the frozen receipt contract")
    if receipt.get("gate") != gate or receipt.get("decision") not in {"APPROVE", "REQUEST_CHANGES"}:
        return foundation.Finding("INVALID_GATE_RECEIPT", f"receipt must target {gate} with APPROVE or REQUEST_CHANGES")
    if receipt.get("actor_role") != "HUMAN" or not isinstance(receipt.get("actor_id"), str) or not receipt["actor_id"].strip():
        return foundation.Finding("HUMAN_ACTOR_REQUIRED", "only an authenticated Human actor may issue a gate receipt")
    if not isinstance(receipt.get("artifact_id"), str) or not receipt["artifact_id"].strip():
        return foundation.Finding("INVALID_GATE_RECEIPT", "receipt artifact_id must be nonempty")
    if not isinstance(receipt.get("artifact_revision"), str) or not receipt["artifact_revision"].strip():
        return foundation.Finding("INVALID_GATE_RECEIPT", "receipt artifact_revision must be nonempty")
    digest = receipt.get("artifact_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
        return foundation.Finding("INVALID_GATE_RECEIPT", "receipt artifact_sha256 must be a SHA-256 digest")
    if _receipt_refs(receipt) is None:
        return foundation.Finding("INVALID_GATE_RECEIPT", "receipt input_refs must contain unique {id, revision, sha256} records")
    try:
        decided_at = datetime.fromisoformat(receipt["decided_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return foundation.Finding("INVALID_GATE_RECEIPT", "receipt decided_at must be an ISO-8601 timestamp")
    if decided_at.tzinfo is None:
        return foundation.Finding("INVALID_GATE_RECEIPT", "receipt decided_at must include a timezone")
    feedback = receipt.get("feedback")
    if not isinstance(feedback, str) or (receipt["decision"] == "REQUEST_CHANGES" and not feedback.strip()):
        return foundation.Finding("INVALID_GATE_RECEIPT", "REQUEST_CHANGES requires nonempty Human feedback")
    return None


def _call_human_authenticator(authenticator: Callable | None, receipt: dict) -> bool:
    if not callable(authenticator):
        return False
    try:
        return authenticator(receipt["actor_id"], receipt) is True
    except Exception:
        return False


def validate_design_gate_receipt(
    receipt: dict | None,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    design_workflow_dir: str | Path,
    human_actor_authenticator: Callable | None,
) -> GateReceiptResult:
    finding = _receipt_shape_finding(receipt, "DESIGN_REVIEW")
    if finding:
        return GateReceiptResult("FAIL", finding)
    if receipt["decision"] != "APPROVE":
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_NOT_APPROVED", "Katalon requires a Design Gate APPROVE receipt"))
    if receipt["actor_id"].startswith("TEST_ONLY:"):
        return GateReceiptResult("FAIL", foundation.Finding("TEST_ONLY_RECEIPT_NOT_PRODUCTION", "TEST_ONLY simulated receipts are never valid for production Human-auth verification"))
    try:
        expected_refs = tuple((ref["id"], ref["revision"], ref["sha256"]) for ref in foundation.design_gate_input_refs(baseline, design_workflow_dir))
    except foundation.ProjectPolicyBindingError as error:
        return GateReceiptResult("FAIL", foundation.Finding(error.code, str(error)))
    except (OSError, ValueError) as error:
        return GateReceiptResult("FAIL", foundation.Finding("BA_BASELINE_STALE", str(error)))
    actual_refs = _receipt_refs(receipt)
    if (
        receipt["artifact_id"] != design.artifact_id
        or receipt["artifact_revision"] != design.revision
        or receipt["artifact_sha256"].lower() != design.sha256
        or actual_refs != expected_refs
    ):
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_RECEIPT_BINDING_MISMATCH", "Design receipt is stale or does not bind the exact design snapshot and current BA inputs"))
    try:
        actor = human_actor_authenticator(receipt["actor_id"], receipt) if callable(human_actor_authenticator) else None
    except Exception:
        actor = None
    if (
        type(actor) is not foundation.AuthenticatedHumanActorContext
        or actor.actor_role != "HUMAN"
        or actor.actor_id != receipt["actor_id"]
    ):
        return GateReceiptResult("FAIL", foundation.Finding("HUMAN_ACTOR_NOT_AUTHENTICATED", "Human actor identity was not authenticated by the host"))
    design_workflow_dir = Path(design_workflow_dir).resolve()
    workflow_path = design_workflow_dir / "workflow-state.json"
    receipt_path = design_workflow_dir / "design-gate/revisions" / design.revision / "receipt.json"
    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        persisted_receipt = receipt_path.read_bytes()
        semantic_bytes = (design_workflow_dir / "canonical/semantic-payload.json").read_bytes()
    except (OSError, ValueError) as error:
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_APPROVAL_NOT_PERSISTED", str(error)))
    receipt_bytes = json.dumps(receipt, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if (
        workflow.get("state") != "APPROVED_DESIGN"
        or workflow.get("review_status") != "APPROVED"
        or workflow.get("artifact_id") != design.artifact_id
        or workflow.get("artifact_revision") != design.revision
        or workflow.get("artifact_sha256") != design.sha256
        or semantic_bytes != design.payload_bytes
        or hashlib.sha256(semantic_bytes).hexdigest() != design.sha256
        or workflow.get("design_gate_receipt_mode") != "HUMAN_AUTHENTICATED"
        or persisted_receipt != receipt_bytes
        or workflow.get("design_gate_receipt_evidence") != {
            "path": str(receipt_path), "sha256": hashlib.sha256(persisted_receipt).hexdigest(),
        }
    ):
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_APPROVAL_NOT_PERSISTED", "authoritative persisted APPROVED_DESIGN or receipt does not match"))
    validation = foundation.validate_design(design, baseline)
    if validation.status != "PASS":
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_VALIDATION_FAILED", "approved-design input does not pass the frozen Test Design validators"))
    return GateReceiptResult(
        "PASS", None,
        DesignGateAuthorization(
            design.artifact_id, design.revision, design.sha256, actual_refs, False,
            str(receipt_path), hashlib.sha256(persisted_receipt).hexdigest(),
        ),
    )


def validate_test_only_design_fixture(
    fixture_path: str | Path,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    design_workflow_dir: str | Path,
) -> GateReceiptResult:
    fixture_path = Path(fixture_path).resolve()
    benchmark_root = (ROOT / "benchmark").resolve()
    if not fixture_path.is_relative_to(benchmark_root) and not foundation.is_test_only_workspace_path(fixture_path):
        return GateReceiptResult("FAIL", foundation.Finding("TEST_ONLY_FIXTURE_OUTSIDE_EVIDENCE", "TEST_ONLY receipt fixtures must live under benchmark evidence or a temporary workspace"))
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return GateReceiptResult("FAIL", foundation.Finding("INVALID_TEST_ONLY_FIXTURE", str(error)))
    if (
        not isinstance(fixture, dict)
        or set(fixture) != {"fixture_type", "not_for_production", "receipt"}
        or fixture.get("fixture_type") != "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT"
        or fixture.get("not_for_production") is not True
        or not isinstance(fixture.get("receipt"), dict)
    ):
        return GateReceiptResult("FAIL", foundation.Finding("INVALID_TEST_ONLY_FIXTURE", "fixture must be explicitly marked TEST_ONLY and not_for_production"))
    receipt = fixture["receipt"]
    finding = _receipt_shape_finding(receipt, "DESIGN_REVIEW")
    if finding:
        return GateReceiptResult("FAIL", finding)
    try:
        expected = tuple((ref["id"], ref["revision"], ref["sha256"]) for ref in foundation.design_gate_input_refs(baseline, design_workflow_dir))
    except foundation.ProjectPolicyBindingError as error:
        return GateReceiptResult("FAIL", foundation.Finding(error.code, str(error)))
    except (OSError, ValueError) as error:
        return GateReceiptResult("FAIL", foundation.Finding("BA_BASELINE_STALE", str(error)))
    actual = _receipt_refs(receipt)
    if (
        receipt["decision"] != "APPROVE"
        or not receipt["actor_id"].startswith("TEST_ONLY:")
        or receipt["artifact_id"] != design.artifact_id
        or receipt["artifact_revision"] != design.revision
        or receipt["artifact_sha256"].lower() != design.sha256
        or actual != expected
    ):
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_RECEIPT_BINDING_MISMATCH", "TEST_ONLY receipt does not bind the exact design and current BA inputs"))
    design_workflow_dir = Path(design_workflow_dir).resolve()
    workflow_path = design_workflow_dir / "workflow-state.json"
    persisted_receipt_path = design_workflow_dir / "design-gate/revisions" / design.revision / "receipt.json"
    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        persisted_receipt = persisted_receipt_path.read_bytes()
        semantic_bytes = (design_workflow_dir / "canonical/semantic-payload.json").read_bytes()
    except (OSError, ValueError) as error:
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_APPROVAL_NOT_PERSISTED", str(error)))
    expected_receipt = json.dumps(receipt, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if (
        workflow.get("state") != "APPROVED_DESIGN"
        or workflow.get("review_status") != "APPROVED"
        or workflow.get("design_gate_receipt_mode") != "TEST_ONLY"
        or workflow.get("artifact_id") != design.artifact_id
        or workflow.get("artifact_revision") != design.revision
        or workflow.get("artifact_sha256") != design.sha256
        or semantic_bytes != design.payload_bytes
        or persisted_receipt != expected_receipt
    ):
        return GateReceiptResult("FAIL", foundation.Finding("TEST_ONLY_DESIGN_NOT_PERSISTED", "TEST_ONLY APPROVED_DESIGN state and receipt do not match"))
    validation = foundation.validate_design(design, baseline)
    if validation.status != "PASS":
        return GateReceiptResult("FAIL", foundation.Finding("DESIGN_VALIDATION_FAILED", "design fixture does not pass the frozen validators"))
    return GateReceiptResult(
        "PASS", None,
        DesignGateAuthorization(
            design.artifact_id, design.revision, design.sha256, actual, True,
            str(persisted_receipt_path), hashlib.sha256(persisted_receipt).hexdigest(),
        ),
    )


def adapt_approved_design_to_katalon(
    design: foundation.DesignSnapshot,
    authorization: DesignGateAuthorization,
    baseline: foundation.ApprovedBaseline,
    *,
    execution_oracle_refs: Iterable[dict] = (),
    execution_oracle_authenticator: Callable | None = None,
    allow_test_only_execution_oracles: bool = False,
) -> KatalonInput:
    execution_refs = tuple(execution_oracle_refs)
    _, provenance_findings = _verify_execution_oracles(
        execution_refs,
        authenticator=execution_oracle_authenticator,
        allow_test_only=allow_test_only_execution_oracles,
        baseline=baseline,
    )
    if provenance_findings:
        raise ValueError(provenance_findings[0].message)
    try:
        design_run_dir = Path(authorization.receipt_path).resolve().parents[3]
        current_refs = tuple((ref["id"], ref["revision"], ref["sha256"]) for ref in foundation.design_gate_input_refs(baseline, design_run_dir))
    except (OSError, ValueError) as error:
        raise ValueError(f"BA_BASELINE_STALE: {error}") from error
    if (
        authorization.artifact_id != design.artifact_id
        or authorization.artifact_revision != design.revision
        or authorization.artifact_sha256 != design.sha256
        or authorization.input_refs != current_refs
        or not authorization.receipt_path
        or not re.fullmatch(r"[0-9a-f]{64}", authorization.receipt_sha256)
    ):
        raise ValueError("Design Gate authorization is not bound to the current design and BA snapshots")
    validation = foundation.validate_design(design, baseline)
    if validation.status != "PASS":
        raise ValueError("Test Design validation must PASS before Katalon input adaptation")

    lines = [
        "# Approved Canonical Test Design input",
        "",
        f"Collection: {design.artifact_id}; revision: {design.revision}; SHA-256: {design.sha256}",
        "Design Gate: Human APPROVE receipt validated for this exact snapshot.",
        "",
        "## Coverage Oracle: approved scenario rows",
        "",
        "Preserve IDs, hierarchy, wording, expected behavior, and explicit FR/BR refs. Do not add, remove, merge, or reinterpret coverage.",
        "Rows with a null expected behavior are deferred and must not create a testcase or pass/fail assertion.",
        "",
    ]
    deferred = []
    for record in design.records:
        if record.expected_behavior is None:
            deferred.append(record)
            continue
        lines.extend((
            f"### {record.design_id}",
            f"Hierarchy: {' / '.join(record.hierarchy_path)}",
            f"Scenario title: {record.scenario_title}",
            f"Expected behavior: {record.expected_behavior}",
            f"Requirement refs: {', '.join(record.requirement_refs)}",
        ))
        if record.open_questions:
            lines.append("Open questions (do not answer or assert):")
            lines.extend(f"- {question.source_ref} [UNKNOWN]: {question.text}" for question in record.open_questions)
        lines.append("")
    lines.extend(("## BUSINESS ORACLE", ""))
    lines.extend(f"### {row.id}\n{row.text}\n" for row in (*baseline.requirements, *baseline.business_rules))
    lines.extend((
        "## EXECUTION ORACLE",
        "",
        "No approved execution contract was supplied." if not execution_refs else "Approved execution contract sources follow.",
        "Execution details may only come from the approved sources listed below; otherwise preserve material OPEN dependencies.",
        "",
    ))
    for ref in execution_refs:
        path = Path(ref["path"]).resolve()
        if not path.is_file() or _hash_path(path) != ref.get("sha256") or ref.get("approved") is not True:
            raise ValueError(f"execution oracle must be an approved, current source: {ref.get('id')}")
        lines.extend((f"### {ref['id']} ({ref['revision']}; SHA-256 {ref['sha256']})", path.read_text(encoding="utf-8"), ""))
    lines.extend(("## DEFERRED / UNKNOWN", ""))
    for record in deferred:
        lines.append(f"- {record.design_id}: {record.scenario_title}; no expected behavior is approved.")
        for question in record.open_questions:
            lines.append(f"  - {question.source_ref} [UNKNOWN]: {question.text}")
    if not deferred:
        lines.append("No scenario row has a null expected behavior.")
    lines.extend((
        "",
        "## Invocation constraints",
        "",
        "Use the installed pinned create-test-cases skill and output local manual-case semantics only.",
        "Do not look up or access Katalon projects, requirements, existing cases, TestOps, suites, links, runs, or execution.",
        "Do not use current Petclinic code to supply business or interface behavior.",
        "Every case must cite explicit source requirement and design IDs. Keep case-level Test Data separate from steps.",
        "Write each missing setup, action, interval mapping, or observation detail as a material execution dependency in preconditions, using this exact marker: OPEN execution dependencies: <execution-only detail>.",
        "Where used, preserve the OPEN dependency for interval/start-duration-end setup and observation mapping, and for TC-012 editable-field selection.",
        "",
    ))
    markdown = "\n".join(lines)
    return KatalonInput(markdown, design.sha256, tuple(baseline_receipt_refs(baseline)), execution_refs)


def normalize_katalon_output(
    raw_path: str | Path,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    artifact_id: str = "KATALON-CASESET",
    revision: str = "1",
    raw_bytes: bytes | None = None,
) -> CaseNormalizationResult:
    path = Path(raw_path)
    raw_bytes = path.read_bytes() if raw_bytes is None else raw_bytes
    return normalize_katalon_output_bytes(
        raw_bytes, design, baseline, source_path=path,
        artifact_id=artifact_id, revision=revision,
    )


def normalize_katalon_output_bytes(
    raw_bytes: bytes,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    source_path: str | Path,
    artifact_id: str = "KATALON-CASESET",
    revision: str = "1",
) -> CaseNormalizationResult:
    path = Path(source_path)
    evidence = foundation.RawEvidenceRef(str(path.resolve()), hashlib.sha256(raw_bytes).hexdigest(), field="katalon_raw_output")
    try:
        raw = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        finding = foundation.Finding("CANNOT_NORMALIZE", f"raw output is not valid UTF-8: {error}", str(path), field="encoding")
        return CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (finding,), (evidence,))
    normalized = normalize_katalon_markdown(
        raw, design, baseline, source_path=str(path.resolve()), artifact_id=artifact_id, revision=revision
    )
    if normalized.snapshot is not None and (
        not normalized.snapshot.evidence
        or normalized.snapshot.evidence[0].sha256 != evidence.sha256
    ):
        finding = foundation.Finding(
            "RAW_OUTPUT_INTEGRITY_FAILURE", "normalized testcase evidence hash differs from captured Katalon bytes",
            str(path), field="sha256",
        )
        return CaseNormalizationResult("CANNOT_NORMALIZE", normalized.profile, None, (finding,), (evidence,))
    return normalized


def _clean(value: str) -> str:
    return value.strip()


def _is_none(value: str) -> bool:
    return _clean(value).casefold().rstrip(".") in {"none", "n/a", "no preconditions", "không có", "không áp dụng"}


def _parse_explicit_refs(
    value: str,
    *,
    case_id: str,
    field: str,
    allowed_design_ids: Iterable[str] = (),
) -> list[str]:
    matches = {(match.start(), match.end()): match.group(0) for match in REF_TOKEN.finditer(value)}
    for design_id in set(allowed_design_ids):
        if isinstance(design_id, str) and design_id:
            pattern = re.compile(rf"(?<![\w.-]){re.escape(design_id)}(?![\w-])")
            matches.update({(match.start(), match.end()): design_id for match in pattern.finditer(value)})
    ordered = sorted((start, end, ref) for (start, end), ref in matches.items())
    if any(current[0] < previous[1] for previous, current in zip(ordered, ordered[1:])):
        raise ValueError(f"{case_id}: overlapping reference tokens in {field}: {value}")
    residual_chars = list(value)
    for start, end, _ in ordered:
        residual_chars[start:end] = " " * (end - start)
    refs = [ref for _, _, ref in ordered]
    residual = "".join(residual_chars)
    if re.sub(r"[\s,;|()/.:]+", "", residual):
        raise ValueError(f"{case_id}: ambiguous reference text in {field}: {value}")
    return refs


def _split_cells(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    return [_clean(cell) for cell in body.split("|")]


def _dependency_note(line: str) -> bool:
    normalized = _fold(line)
    return "open execution dependenc" in normalized or (
        "contract" in normalized
        and any(word in normalized for word in ("not defined", "not specified", "not supplied", "required before", "must define", "chua duoc", "can contract", "do contract xac dinh"))
    )


def _fold(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in value if not unicodedata.combining(char)).replace("đ", "d")


def _dependencies_for_case(block: str, preamble_dependencies: tuple[str, ...]) -> tuple[ExecutionDependency, ...]:
    notes = list(preamble_dependencies)
    for raw_line in block.splitlines():
        line = _clean(raw_line.lstrip("- "))
        open_marker = re.search(r"\bOPEN(?:\s+execution\s+dependencies)?\s*:\s*(.+)$", line, re.IGNORECASE)
        if open_marker:
            notes.append(_clean(open_marker.group(1)))
        elif _dependency_note(line):
            notes.append(line)
        elif "contract" in _fold(line) and any(token in _fold(line) for token in ("editable", "field", "interval", "duration", "mapping", "observation", "action")):
            notes.append(line)
    return tuple(
        ExecutionDependency(need, True, "OPEN", None)
        for need in dict.fromkeys(note for note in notes if note)
    )


def _parse_case_fields(
    block: str,
    profile: str,
    case_id: str,
    title: str,
    path: str,
    *,
    design_ids: Iterable[str] = (),
) -> tuple[CanonicalTestcase, str | None, dict[str, int]]:
    if profile == "benchmark-v1":
        labels = (*BENCHMARK_LABELS, "Expected Result")
        field_re = re.compile(r"(?m)^\*\*(Objective|Preconditions|Test Data|Priority|Requirement refs|Test Design refs|Expected Result):\*\*[ \t]*(.*?)\s*$")
        table_header = ("Step", "Test Step", "Expected Result")
    else:
        labels = NATIVE_LABELS
        field_re = re.compile(r"(?m)^-[ \t]+(Mô tả|Tiền điều kiện|Bước và kết quả mong đợi|Test Data|Priority|Trace):[ \t]*(.*?)\s*$")
        table_header = ()
    matches = list(field_re.finditer(block))
    occurrences: dict[str, list[re.Match]] = {}
    for match in matches:
        occurrences.setdefault(match.group(1), []).append(match)
    required_labels = labels if profile == "native-v1" else BENCHMARK_LABELS
    missing = [label for label in required_labels if len(occurrences.get(label, ())) != 1]
    if missing:
        raise ValueError(f"{case_id}: missing or duplicate required labels: {', '.join(missing)}")
    allowed = set(labels)
    for line in block.splitlines():
        if line.lstrip().startswith("- "):
            label_match = re.match(r"^-\s+([^:]+):", line.strip())
            if label_match and label_match.group(1) not in allowed:
                raise ValueError(f"{case_id}: unknown native field label {label_match.group(1)!r}")
        if profile == "benchmark-v1":
            label_match = re.match(r"^\*\*([^:*]+):\*\*", line.strip())
            if label_match and label_match.group(1) not in allowed:
                raise ValueError(f"{case_id}: unknown benchmark field label {label_match.group(1)!r}")

    def value(label: str) -> str:
        return _clean(occurrences[label][0].group(2))

    summary = value("Expected Result") if profile == "benchmark-v1" and occurrences.get("Expected Result") else None
    objective = value("Objective") if profile == "benchmark-v1" else value("Mô tả")
    preconditions_raw = value("Preconditions") if profile == "benchmark-v1" else value("Tiền điều kiện")
    preconditions = "" if _is_none(preconditions_raw) else preconditions_raw
    if not title or not objective or not preconditions_raw:
        raise ValueError(f"{case_id}: objective and preconditions must be explicit")
    data = value("Test Data")
    if not data:
        raise ValueError(f"{case_id}: Test Data must be explicit, or say None")
    test_data = None if _is_none(data) else data
    priority_raw = value("Priority").rstrip(".")
    if priority_raw not in {"P0", "P1", "P2", "P3"}:
        raise ValueError(f"{case_id}: Priority must be an explicit P0-P3 label")

    if profile == "benchmark-v1":
        reqs = _parse_explicit_refs(value("Requirement refs"), case_id=case_id, field="Requirement refs")
        tds = _parse_explicit_refs(
            value("Test Design refs"), case_id=case_id, field="Test Design refs", allowed_design_ids=design_ids,
        )
        steps = _parse_table_steps(block, table_header, case_id)
    else:
        trace = value("Trace")
        refs = _parse_explicit_refs(trace, case_id=case_id, field="Trace", allowed_design_ids=design_ids)
        design_id_set = set(design_ids)
        tds = [
            ref for ref in refs
            if ref in design_id_set or ref.startswith("TD-")
            or re.match(r"\d+(?:\.\d+)?-(?:UNIT|INT|E2E|EXP)-", ref)
        ]
        reqs = [ref for ref in refs if ref.startswith(("FR-", "BR-"))]
        if len(reqs) + len(tds) != len(refs):
            raise ValueError(f"{case_id}: Trace contains an unclassified reference")
        steps_match = occurrences["Bước và kết quả mong đợi"][0]
        next_field = next((match.start() for match in matches if match.start() > steps_match.start()), len(block))
        steps = _parse_arrow_steps(block[steps_match.end():next_field], case_id)
    if not reqs or not tds:
        raise ValueError(f"{case_id}: explicit Requirement and Test Design refs are required")
    if profile == "benchmark-v1":
        source_labels = {
            "objective": "Objective", "preconditions": "Preconditions", "test_data": "Test Data",
            "priority": "Priority", "requirement_refs": "Requirement refs", "test_design_refs": "Test Design refs",
        }
        source_lines = {field: _line_offset(block, occurrences[label][0].start()) for field, label in source_labels.items()}
        table_header_index = next((i for i, line in enumerate(block.splitlines()) if _split_cells(line) == list(table_header)), 0)
        source_lines["steps"] = table_header_index + 3
    else:
        source_labels = {
            "objective": "Mô tả", "preconditions": "Tiền điều kiện", "test_data": "Test Data", "priority": "Priority",
        }
        source_lines = {field: _line_offset(block, occurrences[label][0].start()) for field, label in source_labels.items()}
        trace_line = _line_offset(block, occurrences["Trace"][0].start())
        source_lines["requirement_refs"] = trace_line
        source_lines["test_design_refs"] = trace_line
        steps_match = occurrences["Bước và kết quả mong đợi"][0]
        step_match = re.search(r"(?m)^[ \t]*\d+\.\s+", block[steps_match.end():])
        source_lines["steps"] = _line_offset(block, steps_match.end() + (step_match.start() if step_match else 0))
    return CanonicalTestcase(
        case_id, title, objective, preconditions, test_data, tuple(steps), priority_raw,
        tuple(reqs), tuple(tds), _dependencies_for_case(block, ()),
    ), summary, source_lines


def _line_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _parse_table_steps(block: str, expected_header: tuple[str, ...], case_id: str) -> list[CaseStep]:
    lines = block.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip().startswith("|")), None)
    if header_index is None or _split_cells(lines[header_index]) != list(expected_header):
        raise ValueError(f"{case_id}: step table header does not match benchmark-v1")
    if header_index + 1 >= len(lines) or not foundation.TABLE_SEPARATOR.match(lines[header_index + 1].strip()):
        raise ValueError(f"{case_id}: malformed step table separator")
    steps = []
    for line in lines[header_index + 2:]:
        if not line.strip().startswith("|"):
            if steps:
                break
            continue
        cells = _split_cells(line)
        if len(cells) != 3 or cells[0] != str(len(steps) + 1) or not cells[1] or not cells[2]:
            raise ValueError(f"{case_id}: malformed or out-of-order benchmark step row")
        steps.append(CaseStep(cells[1], None, cells[2]))
    if not steps:
        raise ValueError(f"{case_id}: no benchmark step rows")
    return steps


def _parse_arrow_steps(section: str, case_id: str) -> list[CaseStep]:
    steps = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = STEP_ARROW.fullmatch(line)
        if not match or int(match.group(1)) != len(steps) + 1:
            raise ValueError(f"{case_id}: malformed, ambiguous, or out-of-order native action/result line")
        steps.append(CaseStep(_clean(match.group(2)), None, _clean(match.group(3))))
    if not steps:
        raise ValueError(f"{case_id}: no native action/result lines")
    return steps


def _summary_conflict(summary: str | None, steps: tuple[CaseStep, ...]) -> bool:
    if not summary:
        return False
    for term, source_count in _count_signals(" ".join(step.expected_result for step in steps)):
        summary_counts = dict(_count_signals(summary))
        if term in summary_counts and summary_counts[term] != source_count:
            return True
    return False


def _count_signals(text: str) -> list[tuple[str, int]]:
    folded = _fold(text)
    result = []
    for term in ("visit", "appointment"):
        if not re.search(rf"\b{term}s?\b", folded):
            continue
        if re.search(rf"\b(?:two|2|multiple|several)\b.{{0,24}}\b{term}s?\b", folded):
            result.append((term, 2))
        elif re.search(rf"\b(?:exactly one|one|single|1)\b.{{0,24}}\b{term}s?\b", folded):
            result.append((term, 1))
    return result


def _preamble_dependencies(preamble: str) -> tuple[str, ...]:
    dependencies = []
    for line in preamble.splitlines():
        note = _clean(line.lstrip("- *"))
        if _dependency_note(note):
            dependencies.append(note)
    return tuple(dict.fromkeys(dependencies))


def _known_design_reference_spans(markdown: str, design: foundation.DesignSnapshot) -> set[tuple[int, int]]:
    design_ids = {row.design_id for row in design.records}
    deferred_ids = {row.design_id for row in design.records if row.expected_behavior is None}
    consumed = set()
    section = None
    offset = 0
    for raw_line in markdown.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line)
        if heading:
            section = heading.group(1).strip().casefold()
        trace_line = bool(re.match(
            r"^\s*(?:-\s*Trace\s*:|\*\*Test Design refs\s*:\*\*)",
            line,
            re.IGNORECASE,
        ))
        for match in CASE_ID_TOKEN.finditer(line):
            token = match.group(0)
            design_id = token[:-1] if token.endswith(".") else token
            if design_id not in design_ids:
                continue
            prefix, suffix = line[:match.start()], line[match.end():]
            deferred_note = (
                section == "deferred / unknown"
                and design_id in deferred_ids
                and re.fullmatch(r"\s*[-*]\s*", prefix)
                and re.match(r"^\s*:", suffix)
                and re.search(r"\b(?:deferred|unknown)\b", suffix, re.IGNORECASE)
            )
            if trace_line or deferred_note:
                consumed.add((offset + match.start(), offset + match.end()))
        offset += len(raw_line)
    return consumed


def normalize_katalon_markdown(
    markdown: str,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    source_path: str = "<memory>",
    artifact_id: str = "KATALON-CASESET",
    revision: str = "1",
) -> CaseNormalizationResult:
    evidence = (foundation.RawEvidenceRef(source_path, sha256_text(markdown), field="katalon_raw_output"),)
    headings = list(CASE_HEADING.finditer(markdown))
    case_shaped_headings = list(CASE_SHAPED_HEADING.finditer(markdown))
    recognized_starts = {match.start() for match in headings}
    consumed_case_ids = {(match.start(1), match.end(1)) for match in headings}
    consumed_case_ids.update(_known_design_reference_spans(markdown, design))
    unconsumed_case_id = next(
        (match for match in CASE_ID_TOKEN.finditer(markdown) if (match.start(), match.end()) not in consumed_case_ids),
        None,
    )
    if unconsumed_case_id:
        line = _line_offset(markdown, unconsumed_case_id.start())
        source_line = markdown.splitlines()[line - 1].strip()
        finding = foundation.Finding(
            "CANNOT_NORMALIZE",
            f"unconsumed TC-shaped semantic content {unconsumed_case_id.group(0)}: {source_line[:180]}",
            source_path,
            line,
            "testcase block",
        )
        return CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (finding,), evidence)
    unconsumed_heading = next((match for match in case_shaped_headings if match.start() not in recognized_starts), None)
    if unconsumed_heading:
        line = _line_offset(markdown, unconsumed_heading.start())
        finding = foundation.Finding("CANNOT_NORMALIZE", "unrecognized or malformed TC-shaped heading", source_path, line, "testcase heading")
        return CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (finding,), evidence)
    if len(case_shaped_headings) != len(headings):
        finding = foundation.Finding("CANNOT_NORMALIZE", "not every TC-shaped block maps to one known testcase", source_path, field="testcase heading")
        return CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (finding,), evidence)
    if not headings:
        return CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (foundation.Finding("CANNOT_NORMALIZE", "no known TC heading profile found", source_path),), evidence)
    all_headings = list(ANY_HEADING.finditer(markdown))
    blocks = []
    for match in headings:
        end = next((heading.start() for heading in all_headings if heading.start() > match.start()), len(markdown))
        blocks.append((match.group(1), _clean(match.group(2) or ""), markdown[match.end():end], match.start()))
    first = blocks[0][2]
    benchmark = any(re.search(rf"(?m)^\*\*{re.escape(label)}:\*\*", first) for label in BENCHMARK_LABELS)
    native = any(re.search(rf"(?m)^-\s+{re.escape(label)}:", first) for label in NATIVE_LABELS)
    if benchmark == native:
        finding = foundation.Finding("CANNOT_NORMALIZE", "raw case fields do not identify exactly one frozen Katalon profile", source_path, field="profile")
        return CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (finding,), evidence)
    profile = "benchmark-v1" if benchmark else "native-v1"
    preamble = markdown[:headings[0].start()]
    global_dependencies = _preamble_dependencies(preamble)
    records = []
    findings = []
    field_sources = {}
    raw_sha256 = evidence[0].sha256
    for case_id, title, block, offset in blocks:
        try:
            record, summary, source_lines = _parse_case_fields(
                block, profile, case_id, title, source_path,
                design_ids={row.design_id for row in design.records},
            )
            record = replace(record, execution_dependencies=_dependencies_for_case(block, global_dependencies))
            if _summary_conflict(summary, record.steps) or _expected_result_conflicts(summary or "", " ".join(step.expected_result for step in record.steps)):
                raise ValueError(f"{case_id}: case-level Expected Result conflicts with its step results")
            records.append(record)
            start_line = _line_offset(markdown, offset)
            field_sources[case_id] = {
                "test_case_id": replace(evidence[0], line=start_line, field="test_case_id"),
                "name": replace(evidence[0], line=start_line, field="name"),
                **{
                    field: replace(evidence[0], line=start_line + line - 1, field=field)
                    for field, line in source_lines.items()
                },
                "execution_dependencies": replace(
                    evidence[0],
                    line=next((i for i, line in enumerate(markdown.splitlines(), 1) if record.execution_dependencies and record.execution_dependencies[0].need in line), start_line),
                    field="execution_dependencies",
                ),
            }
        except ValueError as error:
            start_line = _line_offset(markdown, offset)
            findings.append(foundation.Finding("CANNOT_NORMALIZE", str(error), source_path, start_line, "testcase"))
    if findings:
        return CaseNormalizationResult("CANNOT_NORMALIZE", profile, None, tuple(findings), evidence)
    snapshot = CaseSnapshot.create(
        records, artifact_id=artifact_id, revision=revision, evidence=evidence, field_sources=field_sources
    )
    return CaseNormalizationResult("NORMALIZED", profile, snapshot, (), evidence)


def _unknown_topics(question: foundation.OpenQuestion, baseline: foundation.ApprovedBaseline) -> set[str]:
    text = _fold(question.text + " " + baseline.unknown_clauses.get(question.source_ref, ""))
    topics = set()
    if any(word in text for word in ("maximum", "max duration", "upper bound", "toi da", "can tren")):
        topics.add("maximum-duration")
    if any(word in text for word in ("filter", "bo loc")):
        topics.add("filter")
    if any(word in text for word in ("sort", "sap xep", "ordering", "thu tu")):
        topics.add("default-sort")
    if any(word in text for word in ("pagination", "page size", "phan trang", "kich thuoc trang")):
        topics.add("pagination")
    return topics


def _is_unknown_assertion(text: str, questions: Iterable[foundation.OpenQuestion], baseline: foundation.ApprovedBaseline) -> bool:
    folded = _fold(text)
    disclaimer = bool(re.search(r"\b(?:do not|not|no|unknown|exclude)\b.{0,50}\b(?:assert|test|check|evaluate|verify|assume)\b", folded))
    disclaimer = disclaimer or bool(re.search(r"khong.{0,60}(?:kiem tra|kh[aẳ]ng dinh|danh gia|gia dinh|assert)", folded))
    if disclaimer:
        return False
    for question in questions:
        for topic in _unknown_topics(question, baseline):
            if topic == "maximum-duration" and re.search(r"(?:maximum|max|upper bound|toi da|can tren).{0,60}(?:\d|minute|hour|day|threshold|limit|phut|gio)", folded):
                return True
            if topic == "filter" and re.search(r"(?:filter|bo loc).{0,80}(?:by|uses|apply|must|will|default|only|filters|loc theo|se loc)", folded):
                return True
            if topic == "default-sort" and re.search(r"(?:sort|sorting|sap xep|ordering).{0,80}(?:ascending|descending|newest|oldest|default|by|tang dan|giam dan|mac dinh)", folded):
                return True
            if topic == "pagination" and re.search(r"(?:page size|pagination|phan trang|kich thuoc trang).{0,80}(?:\d|first|next|previous|10|20|mac dinh)", folded):
                return True
    return False


def _unresolved_ba_answer(text: str, baseline: foundation.ApprovedBaseline):
    questions = tuple(
        foundation.OpenQuestion(source_ref, clause)
        for source_ref, clause in baseline.unknown_clauses.items()
    )
    for line_number, line in enumerate(text.splitlines() or (text,), 1):
        for question in questions:
            if re.search(rf"(?<![\w-]){re.escape(question.source_ref)}(?![\w-])", line, re.IGNORECASE):
                return question, line_number, line.strip()
            if _is_unknown_assertion(line, (question,), baseline):
                return question, line_number, line.strip()
    return None


def _execution_scope_finding(source_id: str, text: str, baseline: foundation.ApprovedBaseline, *, path: str | None = None, field: str = "execution_oracle"):
    conflict = _unresolved_ba_answer(text, baseline)
    if conflict is None:
        return None
    question, line, excerpt = conflict
    return foundation.Finding(
        "AUTHORITY_SCOPE_VIOLATION",
        f"execution source {source_id} attempts to answer BA UNKNOWN {question.source_ref}: {excerpt[:180]}",
        path,
        line if path else None,
        field,
    )


def _expected_result_conflicts(assertion: str, source: str) -> bool:
    assertion_counts = dict(_count_signals(assertion))
    source_counts = dict(_count_signals(source))
    if any(term in source_counts and source_counts[term] != count for term, count in assertion_counts.items()):
        return True
    a, s = _fold(assertion), _fold(source)
    for action in ("edit", "reschedule", "cancel", "complete", "create"):
        if action not in a or action not in s:
            continue
        if any(status in a and status in s for status in ("scheduled", "cancelled", "completed")):
            negative = r"(?:not accepted|rejected|not allowed|khong duoc chap nhan|bi tu choi|khong duoc phep)"
            positive = r"(?:accepted|allowed|duoc chap nhan|duoc phep)"
            if re.search(negative, a) and re.search(positive, s) or re.search(positive, a) and re.search(negative, s):
                return True
    return False


def _requires_execution_dependency(case: CanonicalTestcase) -> bool:
    text = _fold(" ".join((case.preconditions, case.test_data or "", *(step.action + " " + step.expected_result for step in case.steps))))
    return bool(re.search(r"\b(?:ui|screen|form|button|route|page|open|click|display|persistence|database|fixture|pet-[a-z]|vet-[a-z]|p[12]|v[12])\b", text))


def validate_testcases(
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    execution_contract_refs: Iterable[dict] = (),
    execution_oracle_authenticator: Callable | None = None,
    allow_test_only_execution_oracles: bool = False,
    explicit_authority_conflicts: Iterable[foundation.Finding] = (),
) -> CaseValidatorResult:
    findings: list[foundation.Finding] = []
    try:
        baseline_receipt_refs(baseline)
    except (OSError, ValueError) as error:
        findings.append(foundation.Finding("BA_BASELINE_STALE", str(error)))
    if not snapshot.records:
        findings.append(foundation.Finding("EMPTY_CASE_COLLECTION", "canonical testcase collection is empty"))
    if hashlib.sha256(snapshot.payload_bytes).hexdigest() != snapshot.sha256:
        findings.append(foundation.Finding("SNAPSHOT_HASH_MISMATCH", "testcase semantic payload hash does not match its bytes"))
    expected_payload = json.dumps(
        [record.semantic_dict() for record in snapshot.records],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if expected_payload != snapshot.payload_bytes:
        findings.append(foundation.Finding("SNAPSHOT_RECORD_MISMATCH", "canonical testcase records do not match the immutable semantic bytes"))
    design_by_id = {row.design_id: row for row in design.records}
    seen_cases: set[str] = set()
    covered_designs: set[str] = set()
    all_unknowns = tuple(dict.fromkeys(question for row in design.records for question in row.open_questions))
    execution_refs = tuple(execution_contract_refs)
    execution_ids, provenance_findings = _verify_execution_oracles(
        execution_refs,
        authenticator=execution_oracle_authenticator,
        allow_test_only=allow_test_only_execution_oracles,
        baseline=baseline,
    )
    findings.extend(provenance_findings)
    for case in snapshot.records:
        if set(case.to_dict()) != set(CASE_RECORD_FIELDS):
            findings.append(foundation.Finding("CANONICAL_SCHEMA_MISMATCH", f"{case.test_case_id} does not match the frozen testcase field set"))
        if not case.test_case_id.strip():
            findings.append(foundation.Finding("INVALID_TC_ID", "test_case_id must be nonempty"))
        if case.test_case_id in seen_cases:
            findings.append(foundation.Finding("DUPLICATE_TC_ID", f"duplicate testcase ID: {case.test_case_id}"))
        seen_cases.add(case.test_case_id)
        if case.review_status not in {"DRAFT", "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED"}:
            findings.append(foundation.Finding("INVALID_REVIEW_STATUS", f"{case.test_case_id} has an unsupported review status"))
        if not case.name.strip() or not case.objective.strip():
            findings.append(foundation.Finding("INVALID_CASE_TEXT", f"{case.test_case_id} requires a name and objective"))
        if not isinstance(case.preconditions, str):
            findings.append(foundation.Finding("INVALID_PRECONDITIONS", f"{case.test_case_id} preconditions must be text"))
        if case.test_data is not None and not isinstance(case.test_data, str):
            findings.append(foundation.Finding("INVALID_TEST_DATA", f"{case.test_case_id} test_data must be text or null"))
        if case.priority not in {"P0", "P1", "P2", "P3"}:
            findings.append(foundation.Finding("INVALID_PRIORITY", f"{case.test_case_id} priority must be P0-P3"))
        if not case.steps:
            findings.append(foundation.Finding("MISSING_STEPS", f"{case.test_case_id} requires at least one step"))
        for step in case.steps:
            if not isinstance(step.action, str) or not step.action.strip() or not isinstance(step.expected_result, str) or not step.expected_result.strip():
                findings.append(foundation.Finding("INVALID_STEP", f"{case.test_case_id} step action/result must be nonempty"))
        if not case.requirement_refs or not case.test_design_refs:
            findings.append(foundation.Finding("MISSING_TRACE_REFS", f"{case.test_case_id} requires BA and Test Design refs"))
        if len(case.requirement_refs) != len(set(case.requirement_refs)):
            findings.append(foundation.Finding("DUPLICATE_BA_REF", f"{case.test_case_id} repeats a BA reference"))
        if len(case.test_design_refs) != len(set(case.test_design_refs)):
            findings.append(foundation.Finding("DUPLICATE_TD_REF", f"{case.test_case_id} repeats a Test Design reference"))
        for ref in case.requirement_refs:
            if not isinstance(ref, str) or not ref.strip():
                findings.append(foundation.Finding("INVALID_BA_REF", f"{case.test_case_id} has an empty or non-string BA ref"))
                continue
            if ref not in baseline.ba_ids:
                findings.append(foundation.Finding("ORPHAN_BA_REF", f"{case.test_case_id} references unknown BA ID {ref}"))
        linked = []
        for ref in case.test_design_refs:
            if not isinstance(ref, str) or not ref.strip():
                findings.append(foundation.Finding("INVALID_TD_REF", f"{case.test_case_id} has an empty or non-string Test Design ref"))
                continue
            design_row = design_by_id.get(ref)
            if design_row is None:
                findings.append(foundation.Finding("ORPHAN_TD_REF", f"{case.test_case_id} references unknown Test Design ID {ref}"))
                continue
            linked.append(design_row)
            covered_designs.add(ref)
            if design_row.expected_behavior is None:
                findings.append(foundation.Finding("DEFERRED_TD_ASSERTION", f"{case.test_case_id} asserts against deferred Test Design row {ref}"))
        supported_ba = {ref for row in linked for ref in row.requirement_refs}
        for ref in case.requirement_refs:
            if ref in baseline.ba_ids and ref not in supported_ba:
                findings.append(foundation.Finding("UNSUPPORTED_BA_REF", f"{case.test_case_id} BA ref {ref} is not supported through its referenced Test Design rows"))
        source_text = " ".join(
            [row.expected_behavior or "" for row in linked]
            + [next((ba.text for ba in (*baseline.requirements, *baseline.business_rules) if ba.id == ref), "") for ref in case.requirement_refs]
        )
        for step in case.steps:
            if _is_unknown_assertion(step.expected_result, all_unknowns, baseline):
                findings.append(foundation.Finding("UNKNOWN_ASSERTION_LEAK", f"{case.test_case_id} expected result answers an unresolved BA UNKNOWN"))
            if _expected_result_conflicts(step.expected_result, source_text):
                findings.append(foundation.Finding("EXPECTED_RESULT_AUTHORITY_CONFLICT", f"{case.test_case_id} expected result contradicts its BA/Test Design chain"))
        if not case.execution_dependencies and _requires_execution_dependency(case):
            findings.append(foundation.Finding("MISSING_EXECUTION_DEPENDENCY", f"{case.test_case_id} needs an explicit execution setup/action/observation dependency"))
        dependency_keys = set()
        for dependency in case.execution_dependencies:
            if not isinstance(dependency.need, str) or not dependency.need.strip() or not isinstance(dependency.material, bool) or dependency.status not in {"OPEN", "RESOLVED"}:
                findings.append(foundation.Finding("INVALID_EXECUTION_DEPENDENCY", f"{case.test_case_id} has an invalid execution dependency"))
                continue
            key = (dependency.need, dependency.material, dependency.status, dependency.resolution_ref)
            if key in dependency_keys:
                findings.append(foundation.Finding("DUPLICATE_EXECUTION_DEPENDENCY", f"{case.test_case_id} repeats an execution dependency"))
            dependency_keys.add(key)
            if dependency.status == "OPEN" and dependency.resolution_ref is not None:
                findings.append(foundation.Finding("INVALID_EXECUTION_RESOLUTION_REF", f"{case.test_case_id} OPEN dependency cannot have a resolution ref"))
            if dependency.status == "RESOLVED" and (
                dependency.resolution_ref is None
                or sum(ref[0] == dependency.resolution_ref for ref in execution_ids) != 1
            ):
                findings.append(foundation.Finding("INVALID_EXECUTION_RESOLUTION_REF", f"{case.test_case_id} resolution ref is not an approved execution source"))
            if dependency.status == "RESOLVED":
                conflict = _unresolved_ba_answer(dependency.need, baseline)
                if conflict:
                    question, _, excerpt = conflict
                    findings.append(foundation.Finding(
                        "AUTHORITY_SCOPE_VIOLATION",
                        f"{dependency.resolution_ref or '<unknown>'} resolves BA UNKNOWN {question.source_ref} through {case.test_case_id} dependency: {excerpt[:180]}",
                        field="execution_dependencies",
                    ))
            if dependency.status == "OPEN" and dependency.material:
                findings.append(foundation.Finding("MATERIAL_OPEN_EXECUTION_DEPENDENCY", f"{case.test_case_id}: {dependency.need}"))
    for row in design.records:
        if row.expected_behavior is not None and row.design_id not in covered_designs:
            findings.append(foundation.Finding("UNCOVERED_TD", f"approved Test Design row has no testcase: {row.design_id}"))
    findings.extend(explicit_authority_conflicts)
    return CaseValidatorResult(
        "PASS" if not any(f.code not in {"MATERIAL_OPEN_EXECUTION_DEPENDENCY"} for f in findings) else "FAIL",
        tuple(findings), snapshot.artifact_id, snapshot.revision, snapshot.sha256,
    )


def has_material_open_dependencies(snapshot: CaseSnapshot) -> bool:
    return any(dep.material and dep.status == "OPEN" for case in snapshot.records for dep in case.execution_dependencies)


def _execution_contract_signature(refs: Iterable[dict]) -> tuple[str, ...]:
    keys = ("id", "revision", "sha256", "approved", "path", "approval_evidence", "test_only")
    return tuple(sorted(
        json.dumps({key: ref.get(key) for key in keys}, sort_keys=True, separators=(",", ":"))
        for ref in refs
    ))


def _verify_execution_oracles(
    refs: Iterable[dict],
    *,
    authenticator: Callable | None,
    allow_test_only: bool,
    baseline: foundation.ApprovedBaseline,
) -> tuple[set[tuple[str, str, str]], list[foundation.Finding]]:
    valid = set()
    findings = []
    for ref in refs:
        source_id = ref.get("id") if isinstance(ref, dict) else None
        try:
            if not isinstance(ref, dict):
                raise ValueError("oracle reference must be an object")
            expected_hash = ref["sha256"]
            if (
                not isinstance(ref.get("id"), str) or not ref["id"].strip()
                or not isinstance(ref.get("revision"), str) or not ref["revision"].strip()
                or not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash)
                or ref.get("approved") is not True
            ):
                raise ValueError("missing identity, approved status, revision, or SHA-256")
            is_test_only = ref.get("test_only") is True
            source_path = _resolve_provenance_reference(
                ref["path"], expected_hash, allow_test_only=allow_test_only, test_only=is_test_only,
            )
            source_bytes = source_path.read_bytes()
            approval = ref.get("approval_evidence")
            if not isinstance(approval, dict) or set(approval) != {"path", "sha256"}:
                raise ValueError("approval_evidence must identify the approved evidence file and SHA-256")
            approval_path = _resolve_provenance_reference(
                approval["path"], approval["sha256"], allow_test_only=allow_test_only, test_only=is_test_only,
            )
            evidence = json.loads(approval_path.read_text(encoding="utf-8"))
            if (
                not isinstance(evidence, dict)
                or evidence.get("decision") != "APPROVE"
                or evidence.get("actor_role") != "HUMAN"
                or evidence.get("source_id") != ref["id"]
                or evidence.get("source_revision") != ref["revision"]
                or str(evidence.get("source_sha256", "")).lower() != expected_hash.lower()
                or not isinstance(evidence.get("actor_id"), str)
                or not evidence["actor_id"].strip()
            ):
                raise ValueError("approval evidence does not approve this exact source revision and hash")
            if is_test_only:
                source_document = json.loads(source_bytes.decode("utf-8"))
                if (
                    not allow_test_only
                    or not str(ref["id"]).startswith("TEST_ONLY:")
                    or evidence.get("fixture_type") != "TEST_ONLY_EXECUTION_ORACLE_APPROVAL"
                    or evidence.get("not_for_production") is not True
                    or not isinstance(source_document, dict)
                    or source_document.get("not_for_production") is not True
                ):
                    raise ValueError("TEST_ONLY execution-oracle evidence is not permitted on this path")
            else:
                try:
                    actor = authenticator(evidence["actor_id"], evidence) if callable(authenticator) else None
                except Exception:
                    actor = None
                if (
                    type(actor) is not foundation.AuthenticatedHumanActorContext
                    or actor.actor_role != "HUMAN"
                    or actor.actor_id != evidence["actor_id"]
                ):
                    raise ValueError("host did not authenticate the execution-oracle approval actor")
            try:
                source_text = source_bytes.decode("utf-8")
            except UnicodeDecodeError:
                findings.append(foundation.Finding(
                    "DESIGN_ESCALATION_REQUIRED",
                    f"{source_id}: execution-oracle source is not inspectable as UTF-8 for authority-scope validation",
                    str(source_path),
                    field="execution_oracle",
                ))
                continue
            scope_finding = _execution_scope_finding(str(source_id), source_text, baseline, path=str(source_path))
            if scope_finding:
                findings.append(scope_finding)
                continue
            valid.add((ref["id"], ref["revision"], expected_hash.lower()))
        except ProvenanceResolutionError as error:
            findings.append(foundation.Finding(error.code, f"{source_id or '<unknown>'}: {error}"))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            findings.append(foundation.Finding(
                "EXECUTION_ORACLE_PROVENANCE_INVALID",
                f"{source_id or '<unknown>'}: {error}",
            ))
    return valid, findings


def _input_ref_signature(refs: Iterable[dict]) -> tuple[tuple[str, str, str], ...]:
    return tuple((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in refs)


def start_case_workflow(snapshot: CaseSnapshot) -> CaseWorkflowState:
    return CaseWorkflowState("DRAFT_CASES", snapshot.artifact_id, snapshot.revision, snapshot.sha256, "DRAFT", "NOT_RUN")


def submit_cases_for_review(
    state: CaseWorkflowState,
    snapshot: CaseSnapshot,
    validation: CaseValidatorResult,
    *,
    execution_contract_refs: Iterable[dict] = (),
    design_gate_receipt_mode: str | None = None,
    design_gate_receipt_evidence: dict | None = None,
    input_refs: Iterable[dict] = (),
    project_policy_context: dict | None = None,
) -> CaseWorkflowState:
    execution_refs = tuple(execution_contract_refs)
    if state.state != "DRAFT_CASES":
        raise ValueError("only DRAFT_CASES can transition to CASE_REVIEW")
    if any(record.review_status != "DRAFT" for record in snapshot.records):
        raise ValueError("only DRAFT testcase projections can transition to CASE_REVIEW")
    if (
        state.artifact_id != snapshot.artifact_id
        or state.artifact_revision != snapshot.revision
        or state.artifact_sha256 != snapshot.sha256
        or validation.status != "PASS"
        or validation.artifact_id != snapshot.artifact_id
        or validation.artifact_revision != snapshot.revision
        or validation.artifact_sha256 != snapshot.sha256
    ):
        raise ValueError("validation result is not bound to the exact testcase snapshot")
    return CaseWorkflowState(
        "CASE_REVIEW", snapshot.artifact_id, snapshot.revision, snapshot.sha256, "IN_REVIEW", "PASS",
        _execution_contract_signature(execution_refs), design_gate_receipt_mode,
        dict(design_gate_receipt_evidence) if design_gate_receipt_evidence else None,
        _input_ref_signature(input_refs),
        tuple(dict(ref) for ref in execution_refs),
        project_policy_context,
    )


def validate_case_gate_receipt(
    receipt: dict | None,
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    state: CaseWorkflowState,
    *,
    human_actor_authenticator: Callable | None,
    validation: CaseValidatorResult | None = None,
    execution_contract_refs: Iterable[dict] = (),
) -> GateReceiptResult:
    return _validate_case_gate_receipt(
        receipt, snapshot, design, baseline, state,
        human_actor_authenticator=human_actor_authenticator,
        validation=validation,
        execution_contract_refs=execution_contract_refs,
    )


def _validate_case_gate_receipt(
    receipt: dict | None,
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    state: CaseWorkflowState,
    *,
    human_actor_authenticator: Callable | None = None,
    test_only_actor: TestOnlyHumanActorContext | None = None,
    validation: CaseValidatorResult | None = None,
    execution_contract_refs: Iterable[dict] = (),
) -> GateReceiptResult:
    finding = _receipt_shape_finding(receipt, "CASE_REVIEW")
    if finding:
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    if state.state != "CASE_REVIEW":
        finding = foundation.Finding("INVALID_CASE_GATE_TRANSITION", "Human Case Gate decisions are accepted only from CASE_REVIEW; STOP_V1 is terminal")
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    if (
        state.review_status != "IN_REVIEW"
        or state.validation_status != "PASS"
        or any(record.review_status != "IN_REVIEW" for record in snapshot.records)
        or (state.artifact_id, state.artifact_revision, state.artifact_sha256)
        != (snapshot.artifact_id, snapshot.revision, snapshot.sha256)
    ):
        finding = foundation.Finding("CASE_RECEIPT_BINDING_MISMATCH", "Case Gate receipt requires the current CASE_REVIEW snapshot")
        return GateReceiptResult("FAIL", finding, findings=(finding,))

    refs = tuple(execution_contract_refs)
    if _execution_contract_signature(refs) != state.execution_contract_refs:
        finding = foundation.Finding("EXECUTION_ORACLE_REFS_STALE", "execution-oracle refs changed after CASE_REVIEW; submit a new review path")
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    if test_only_actor is None and state.design_gate_receipt_mode == "TEST_ONLY":
        finding = foundation.Finding("TEST_ONLY_RECEIPT_NOT_PRODUCTION", "TEST_ONLY Design Gate evidence cannot enter production Case Gate")
        return GateReceiptResult("FAIL", finding, findings=(finding,))

    current_validation = validate_testcases(
        snapshot, design, baseline, execution_contract_refs=refs,
        execution_oracle_authenticator=human_actor_authenticator,
        allow_test_only_execution_oracles=test_only_actor is not None,
    )
    if (
        current_validation.status != "PASS"
        or (current_validation.artifact_id, current_validation.artifact_revision, current_validation.artifact_sha256)
        != (snapshot.artifact_id, snapshot.revision, snapshot.sha256)
        or validation is not None and (
            validation.status != "PASS"
            or (validation.artifact_id, validation.artifact_revision, validation.artifact_sha256)
            != (snapshot.artifact_id, snapshot.revision, snapshot.sha256)
        )
    ):
        finding = foundation.Finding("CASE_VALIDATION_NOT_CURRENT", "Case Gate requires validators to PASS on the exact current snapshot")
        return GateReceiptResult("FAIL", finding, findings=(finding, *current_validation.findings))

    try:
        context = state.project_policy_context
        policy_run = Path(context["context_path"]).parents[1] if context else None
        expected = tuple((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in case_gate_input_refs(baseline, design, run_dir=policy_run))
        if context and json.loads(Path(context["context_path"]).read_text(encoding="utf-8")) != context:
            raise foundation.ProjectPolicyBindingError("Case Review policy context changed")
    except foundation.ProjectPolicyBindingError as error:
        finding = foundation.Finding(error.code, str(error))
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    except (OSError, ValueError) as error:
        finding = foundation.Finding("BA_BASELINE_STALE", str(error))
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    if state.input_refs != expected:
        finding = foundation.Finding("CASE_REVIEW_INPUTS_STALE", "BA or approved Design refs changed after CASE_REVIEW; submit a new review path")
        return GateReceiptResult("FAIL", finding, findings=(finding,))

    design_auth_finding = _validate_design_gate_evidence(
        state, design, baseline,
        human_actor_authenticator=human_actor_authenticator,
        test_only=test_only_actor is not None,
    )
    if design_auth_finding:
        return GateReceiptResult("FAIL", design_auth_finding, findings=(design_auth_finding,))

    actual = _receipt_refs(receipt)
    if (
        receipt["artifact_id"] != snapshot.artifact_id
        or receipt["artifact_revision"] != snapshot.revision
        or receipt["artifact_sha256"].lower() != snapshot.sha256
        or actual != expected
    ):
        finding = foundation.Finding("CASE_RECEIPT_BINDING_MISMATCH", "Case Gate receipt does not bind the exact testcase, Design, and current BA snapshots")
        return GateReceiptResult("FAIL", finding, findings=(finding,))

    if test_only_actor is not None:
        if (
            type(test_only_actor) is not TestOnlyHumanActorContext
            or state.design_gate_receipt_mode != "TEST_ONLY"
            or not receipt["actor_id"].startswith("TEST_ONLY:")
            or test_only_actor.actor_id != receipt["actor_id"]
            or test_only_actor.actor_role != "HUMAN"
        ):
            finding = foundation.Finding("INVALID_TEST_ONLY_HUMAN_CONTEXT", "TEST_ONLY fixture must bind its simulated Human actor and TEST_ONLY Design receipt")
            return GateReceiptResult("FAIL", finding, findings=(finding,))
        actor_context: AuthenticatedHumanActorContext | TestOnlyHumanActorContext = test_only_actor
    else:
        if receipt["actor_id"].startswith("TEST_ONLY:") or state.design_gate_receipt_mode == "TEST_ONLY":
            finding = foundation.Finding("TEST_ONLY_RECEIPT_NOT_PRODUCTION", "TEST_ONLY Design or Case receipts cannot be used by the production Human-auth path")
            return GateReceiptResult("FAIL", finding, findings=(finding,))
        if state.design_gate_receipt_mode != "HUMAN_AUTHENTICATED":
            finding = foundation.Finding("DESIGN_GATE_APPROVAL_REQUIRED", "production Case Gate requires CASE_REVIEW derived from a Human-authenticated approved Design")
            return GateReceiptResult("FAIL", finding, findings=(finding,))
        try:
            actor_context = human_actor_authenticator(receipt["actor_id"], receipt) if callable(human_actor_authenticator) else None
        except Exception:
            actor_context = None
        if (
            type(actor_context) is not AuthenticatedHumanActorContext
            or actor_context.actor_role != "HUMAN"
            or actor_context.actor_id != receipt["actor_id"]
        ):
            finding = foundation.Finding("HUMAN_ACTOR_NOT_AUTHENTICATED", "host must supply a verified Human actor context bound to the receipt")
            return GateReceiptResult("FAIL", finding, findings=(finding,))

    if receipt["decision"] == "APPROVE" and has_material_open_dependencies(snapshot):
        findings = tuple(f for f in current_validation.findings if f.code == "MATERIAL_OPEN_EXECUTION_DEPENDENCY")
        finding = foundation.Finding(
            "MATERIAL_OPEN_EXECUTION_DEPENDENCY",
            "material OPEN execution dependencies prevent APPROVED_TESTWARE",
        )
        return GateReceiptResult("FAIL", finding, human_actor=actor_context, findings=(finding, *findings))
    return GateReceiptResult("PASS", None, human_actor=actor_context)


def _validate_design_gate_evidence(
    state: CaseWorkflowState,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    *,
    human_actor_authenticator: Callable | None,
    test_only: bool,
) -> foundation.Finding | None:
    evidence = state.design_gate_receipt_evidence
    expected_mode = "TEST_ONLY" if test_only else "HUMAN_AUTHENTICATED"
    if (
        not isinstance(evidence, dict)
        or evidence.get("mode") != expected_mode
        or not isinstance(evidence.get("path"), str)
        or not isinstance(evidence.get("sha256"), str)
    ):
        return foundation.Finding("DESIGN_GATE_APPROVAL_REQUIRED", "Case Review must bind the persisted approved Design Gate receipt")
    receipt_path = Path(evidence["path"]).resolve()
    try:
        receipt_bytes = receipt_path.read_bytes()
        if hashlib.sha256(receipt_bytes).hexdigest() != evidence["sha256"].lower():
            raise ValueError("persisted Design Gate receipt bytes changed")
        receipt = json.loads(receipt_bytes.decode("utf-8"))
        design_run_dir = receipt_path.parents[3]
        workflow_path = design_run_dir / "workflow-state.json"
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        semantic_bytes = (design_run_dir / "canonical/semantic-payload.json").read_bytes()
    except (OSError, ValueError, IndexError) as error:
        return foundation.Finding("DESIGN_GATE_APPROVAL_REQUIRED", str(error))
    if semantic_bytes != design.payload_bytes or hashlib.sha256(semantic_bytes).hexdigest() != design.sha256:
        return foundation.Finding("DESIGN_SEMANTIC_SNAPSHOT_STALE", "persisted approved Design semantic bytes changed after Case Review")
    finding = _receipt_shape_finding(receipt, "DESIGN_REVIEW")
    if finding:
        return finding
    try:
        expected_refs = tuple((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in foundation.design_gate_input_refs(baseline, design_run_dir))
    except foundation.ProjectPolicyBindingError as error:
        return foundation.Finding(error.code, str(error))
    except (OSError, ValueError) as error:
        return foundation.Finding("BA_BASELINE_STALE", str(error))
    if (
        receipt["decision"] != "APPROVE"
        or receipt["artifact_id"] != design.artifact_id
        or receipt["artifact_revision"] != design.revision
        or receipt["artifact_sha256"].lower() != design.sha256
        or _receipt_refs(receipt) != expected_refs
        or workflow.get("state") != "APPROVED_DESIGN"
        or workflow.get("review_status") != "APPROVED"
        or workflow.get("artifact_id") != design.artifact_id
        or workflow.get("artifact_revision") != design.revision
        or workflow.get("artifact_sha256") != design.sha256
        or workflow.get("design_gate_receipt_mode") != expected_mode
    ):
        return foundation.Finding("DESIGN_GATE_APPROVAL_REQUIRED", "persisted Design Gate state or receipt does not bind the approved design and current BA baseline")
    if test_only:
        fixture_ref = evidence.get("fixture")
        if not isinstance(fixture_ref, dict) or not isinstance(fixture_ref.get("path"), str):
            return foundation.Finding("INVALID_TEST_ONLY_DESIGN_EVIDENCE", "TEST_ONLY Design Gate fixture reference is missing")
        fixture_path = Path(fixture_ref["path"]).resolve()
        try:
            if (
                (not fixture_path.is_relative_to((ROOT / "benchmark").resolve()) and not foundation.is_test_only_workspace_path(fixture_path))
                or _hash_path(fixture_path) != fixture_ref.get("sha256")
            ):
                raise ValueError("TEST_ONLY Design Gate fixture path or hash is invalid")
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            return foundation.Finding("INVALID_TEST_ONLY_DESIGN_EVIDENCE", str(error))
        if (
            not isinstance(fixture, dict)
            or fixture.get("not_for_production") is not True
            or fixture.get("fixture_type") != "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT"
            or fixture.get("receipt") != receipt
        ):
            return foundation.Finding("INVALID_TEST_ONLY_DESIGN_EVIDENCE", "TEST_ONLY fixture does not contain the persisted Design Gate receipt")
        return None
    if receipt["actor_id"].startswith("TEST_ONLY:"):
        return foundation.Finding("TEST_ONLY_RECEIPT_NOT_PRODUCTION", "TEST_ONLY Design Gate evidence cannot enter production Case Gate")
    try:
        actor = human_actor_authenticator(receipt["actor_id"], receipt) if callable(human_actor_authenticator) else None
    except Exception:
        actor = None
    if (
        type(actor) is not foundation.AuthenticatedHumanActorContext
        or actor.actor_id != receipt["actor_id"]
        or actor.actor_role != "HUMAN"
    ):
        return foundation.Finding("HUMAN_ACTOR_NOT_AUTHENTICATED", "host did not authenticate the Human Design Gate actor")
    return None


def validate_test_only_case_gate_fixture(
    fixture_path: str | Path,
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    state: CaseWorkflowState,
    *,
    workflow_dir: str | Path,
    validation: CaseValidatorResult | None = None,
    execution_contract_refs: Iterable[dict] = (),
) -> GateReceiptResult:
    fixture_path = Path(fixture_path).resolve()
    if not foundation.is_test_only_workspace_path(fixture_path) and not fixture_path.is_relative_to((ROOT / "benchmark").resolve()):
        finding = foundation.Finding("TEST_ONLY_FIXTURE_OUTSIDE_EVIDENCE", "TEST_ONLY Case Gate fixtures must live under benchmark evidence or a temporary workspace")
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        finding = foundation.Finding("INVALID_TEST_ONLY_FIXTURE", str(error))
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    if (
        not isinstance(fixture, dict)
        or set(fixture) != {"fixture_type", "not_for_production", "receipt"}
        or fixture.get("fixture_type") != "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT"
        or fixture.get("not_for_production") is not True
        or not isinstance(fixture.get("receipt"), dict)
    ):
        finding = foundation.Finding("INVALID_TEST_ONLY_FIXTURE", "fixture must be TEST_ONLY and explicitly not_for_production")
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    receipt = fixture["receipt"]
    if not isinstance(receipt.get("actor_id"), str) or not receipt["actor_id"].startswith("TEST_ONLY:"):
        finding = foundation.Finding("INVALID_TEST_ONLY_FIXTURE", "simulated Human actor ID must use the TEST_ONLY namespace")
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    refs = tuple(execution_contract_refs)
    if any(not str(ref.get("id", "")).startswith("TEST_ONLY:") for ref in refs):
        finding = foundation.Finding("INVALID_TEST_ONLY_FIXTURE", "TEST_ONLY resolved execution refs must be explicitly TEST_ONLY")
        return GateReceiptResult("FAIL", finding, findings=(finding,))
    actor = TestOnlyHumanActorContext(receipt["actor_id"])
    return _validate_case_gate_receipt(
        receipt, snapshot, design, baseline, state,
        test_only_actor=actor,
        validation=validation,
        execution_contract_refs=refs,
    )


def _case_gate_receipt_bytes(receipt: dict, actor: AuthenticatedHumanActorContext | TestOnlyHumanActorContext) -> bytes:
    stored = dict(receipt)
    stored["actor_id"] = actor.actor_id
    return json.dumps(stored, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _approved_testware(
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    receipt_sha256: str,
    execution_contract_refs: Iterable[dict],
    project_policy_context: dict | None = None,
) -> ApprovedTestware:
    used_resolution_refs = {
        dependency.resolution_ref
        for record in snapshot.records
        for dependency in record.execution_dependencies
        if dependency.status == "RESOLVED" and dependency.resolution_ref is not None
    }
    execution_refs = tuple(
        dict(ref) for ref in execution_contract_refs if ref.get("id") in used_resolution_refs
    )
    evidence = [
        {"path": str(path), "sha256": baseline.source_hashes[name], "field": f"BA:{name}"}
        for name, path in baseline.source_paths.items()
    ]
    evidence.append({"path": str(baseline.handoff_path), "sha256": _hash_path(baseline.handoff_path), "field": "BA:handoff"})
    evidence.extend(
        {"path": ref.path, "sha256": ref.sha256, "field": ref.field}
        for ref in (*snapshot.evidence, *design.evidence)
    )
    payload = {
        "testcase_collection": {"artifact_id": snapshot.artifact_id, "revision": snapshot.revision, "sha256": snapshot.sha256},
        "approved_design": {"artifact_id": design.artifact_id, "revision": design.revision, "sha256": design.sha256},
        "ba_input_refs": baseline_receipt_refs(baseline),
        "case_gate_receipt": {"path": "case-gate/receipt.json", "sha256": receipt_sha256},
        "execution_oracle_refs": list(execution_refs),
        "evidence_locations": list(evidence),
        "project_policy_context": project_policy_context,
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return ApprovedTestware(payload_bytes, hashlib.sha256(payload_bytes).hexdigest())


def _case_gate_transition(
    receipt: dict,
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    state: CaseWorkflowState,
    validation_result: GateReceiptResult,
    *,
    execution_contract_refs: Iterable[dict],
    next_revision: str | None,
    test_only: bool,
) -> CaseGateDecisionResult:
    if validation_result.status != "PASS" or validation_result.human_actor is None:
        findings = validation_result.findings or ((validation_result.finding,) if validation_result.finding else ())
        return CaseGateDecisionResult(
            "REJECTED", validation_result.finding, tuple(findings), state, snapshot,
            state_history=(state.state, "APPROVAL_REJECTED", state.state), test_only=test_only,
        )
    if receipt["decision"] == "REQUEST_CHANGES" and (
        not isinstance(next_revision, str) or not next_revision.strip() or next_revision == snapshot.revision
    ):
        finding = foundation.Finding("INVALID_NEXT_REVISION", "REQUEST_CHANGES requires a distinct new testcase revision")
        return CaseGateDecisionResult(
            "REJECTED", finding, (finding,), state, snapshot,
            state_history=(state.state, "APPROVAL_REJECTED", state.state), test_only=test_only,
        )

    receipt_bytes = _case_gate_receipt_bytes(receipt, validation_result.human_actor)
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    if receipt["decision"] == "APPROVE":
        approved_snapshot = snapshot.project("APPROVED")
        testware = _approved_testware(
            snapshot, design, baseline, receipt_sha256, execution_contract_refs, state.project_policy_context,
        )
        workflow = CaseWorkflowState(
            "STOP_V1", snapshot.artifact_id, snapshot.revision, snapshot.sha256,
            "APPROVED", "PASS", state.execution_contract_refs,
            state.design_gate_receipt_mode, state.design_gate_receipt_evidence, state.input_refs,
            state.execution_oracle_refs,
            state.project_policy_context,
        )
        return CaseGateDecisionResult(
            "STOP_V1", None, (), workflow, approved_snapshot, receipt_bytes=receipt_bytes,
            receipt_sha256=receipt_sha256, approved_testware=testware,
            state_history=("CASE_REVIEW", "APPROVED_TESTWARE", "STOP_V1"), test_only=test_only,
        )

    changed_snapshot = snapshot.project("CHANGES_REQUESTED")
    next_snapshot = CaseSnapshot.create(
        snapshot.records,
        artifact_id=snapshot.artifact_id,
        revision=next_revision,
        evidence=snapshot.evidence,
        field_sources=snapshot.field_sources,
    ).project("DRAFT")
    workflow = CaseWorkflowState(
        "DRAFT_CASES", next_snapshot.artifact_id, next_snapshot.revision, next_snapshot.sha256,
        "DRAFT", "NOT_RUN", state.execution_contract_refs,
        state.design_gate_receipt_mode, state.design_gate_receipt_evidence, state.input_refs,
        state.execution_oracle_refs,
        state.project_policy_context,
    )
    return CaseGateDecisionResult(
        "DRAFT_CASES", None, (), workflow, changed_snapshot, next_snapshot=next_snapshot,
        receipt_bytes=receipt_bytes, receipt_sha256=receipt_sha256,
        state_history=("CASE_REVIEW", "CHANGES_REQUESTED", "DRAFT_CASES"), test_only=test_only,
    )


def apply_case_gate_decision(
    receipt: dict,
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    state: CaseWorkflowState,
    *,
    workflow_dir: str | Path,
    human_actor_authenticator: Callable | None,
    validation: CaseValidatorResult | None = None,
    execution_contract_refs: Iterable[dict] = (),
    next_revision: str | None = None,
) -> CaseGateDecisionResult:
    workflow_dir = Path(workflow_dir).resolve()
    try:
        persisted_workflow = json.loads((workflow_dir / "workflow-state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        finding = foundation.Finding("CASE_WORKFLOW_UNAVAILABLE", str(error))
        return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot)
    if persisted_workflow.get("state") != "CASE_REVIEW":
        code = "RECEIPT_REPLAY" if (workflow_dir / "case-gate/receipt.json").is_file() else "INVALID_CASE_GATE_TRANSITION"
        finding = foundation.Finding(code, "authoritative persisted state is not CASE_REVIEW")
        return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot)
    try:
        persisted_snapshot, persisted_state = load_case_review_snapshot(
            workflow_dir / "canonical/canonical-testcases.json",
            workflow_dir / "workflow-state.json",
            workflow_dir / "canonical/semantic-payload.json",
        )
    except (OSError, ValueError, KeyError, TypeError, RawOutputIntegrityError) as error:
        code = "RAW_OUTPUT_INTEGRITY_FAILURE" if isinstance(error, RawOutputIntegrityError) else "CASE_WORKFLOW_UNAVAILABLE"
        finding = foundation.Finding(code, str(error))
        return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot)
    if persisted_state.state != "CASE_REVIEW":
        code = "RECEIPT_REPLAY" if (workflow_dir / "case-gate/receipt.json").is_file() or persisted_state.state == "STOP_V1" else "INVALID_CASE_GATE_TRANSITION"
        finding = foundation.Finding(code, "authoritative persisted state is not an unconsumed CASE_REVIEW")
        return CaseGateDecisionResult("REJECTED", finding, (finding,), persisted_state, persisted_snapshot)
    if (
        persisted_snapshot.payload_bytes != snapshot.payload_bytes
        or (persisted_state.artifact_id, persisted_state.artifact_revision, persisted_state.artifact_sha256)
        != (snapshot.artifact_id, snapshot.revision, snapshot.sha256)
    ):
        finding = foundation.Finding("CASE_RECEIPT_BINDING_MISMATCH", "caller snapshot is not the authoritative persisted CASE_REVIEW artifact")
        return CaseGateDecisionResult("REJECTED", finding, (finding,), persisted_state, persisted_snapshot)
    if (workflow_dir / "case-gate/receipt.json").exists():
        finding = foundation.Finding("RECEIPT_REPLAY", "a Case Gate receipt was already consumed for this review")
        return CaseGateDecisionResult("REJECTED", finding, (finding,), persisted_state, persisted_snapshot)
    state = persisted_state
    snapshot = persisted_snapshot
    execution_refs = tuple(execution_contract_refs)
    checked = validate_case_gate_receipt(
        receipt, snapshot, design, baseline, state,
        human_actor_authenticator=human_actor_authenticator,
        validation=validation,
        execution_contract_refs=execution_refs,
    )
    decision_result = _case_gate_transition(
        receipt, snapshot, design, baseline, state, checked,
        execution_contract_refs=execution_refs, next_revision=next_revision, test_only=False,
    )
    if decision_result.status != "REJECTED":
        try:
            persist_case_gate_decision(workflow_dir, decision_result)
        except FileExistsError:
            finding = foundation.Finding("RECEIPT_REPLAY", "another decision already consumed a Case Gate receipt")
            return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot)
    return decision_result


def apply_test_only_case_gate_decision(
    fixture_path: str | Path,
    snapshot: CaseSnapshot,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    state: CaseWorkflowState,
    *,
    workflow_dir: str | Path,
    validation: CaseValidatorResult | None = None,
    execution_contract_refs: Iterable[dict] = (),
    next_revision: str | None = None,
) -> CaseGateDecisionResult:
    workflow_dir = Path(workflow_dir).resolve()
    try:
        persisted_workflow = json.loads((workflow_dir / "workflow-state.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        finding = foundation.Finding("CASE_WORKFLOW_UNAVAILABLE", str(error))
        return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot, test_only=True)
    if persisted_workflow.get("state") != "CASE_REVIEW":
        code = "RECEIPT_REPLAY" if (workflow_dir / "case-gate/receipt.json").is_file() else "INVALID_CASE_GATE_TRANSITION"
        finding = foundation.Finding(code, "authoritative persisted state is not CASE_REVIEW")
        return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot, test_only=True)
    execution_refs = tuple(execution_contract_refs)
    checked = validate_test_only_case_gate_fixture(
        fixture_path, snapshot, design, baseline, state, workflow_dir=workflow_dir,
        validation=validation, execution_contract_refs=execution_refs,
    )
    try:
        fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        receipt = fixture["receipt"]
    except (OSError, ValueError, KeyError, TypeError):
        receipt = {}
    try:
        persisted_snapshot, persisted_state = load_case_review_snapshot(
            workflow_dir / "canonical/canonical-testcases.json",
            workflow_dir / "workflow-state.json",
            workflow_dir / "canonical/semantic-payload.json",
        )
    except (OSError, ValueError, KeyError, TypeError, RawOutputIntegrityError) as error:
        code = "RAW_OUTPUT_INTEGRITY_FAILURE" if isinstance(error, RawOutputIntegrityError) else "CASE_WORKFLOW_UNAVAILABLE"
        finding = foundation.Finding(code, str(error))
        return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot, test_only=True)
    if persisted_state.state != "CASE_REVIEW" or persisted_snapshot.payload_bytes != snapshot.payload_bytes:
        code = "RECEIPT_REPLAY" if (workflow_dir / "case-gate/receipt.json").is_file() else "INVALID_CASE_GATE_TRANSITION"
        finding = foundation.Finding(code, "authoritative persisted state is not the unconsumed TEST_ONLY CASE_REVIEW")
        return CaseGateDecisionResult("REJECTED", finding, (finding,), persisted_state, persisted_snapshot, test_only=True)
    state, snapshot = persisted_state, persisted_snapshot
    decision_result = _case_gate_transition(
        receipt, snapshot, design, baseline, state, checked,
        execution_contract_refs=execution_refs, next_revision=next_revision, test_only=True,
    )
    if decision_result.status != "REJECTED":
        try:
            persist_case_gate_decision(workflow_dir, decision_result)
        except FileExistsError:
            finding = foundation.Finding("RECEIPT_REPLAY", "another decision already consumed a TEST_ONLY Case Gate receipt")
            return CaseGateDecisionResult("REJECTED", finding, (finding,), state, snapshot, test_only=True)
    return decision_result


def persist_case_gate_decision(evidence_dir: str | Path, decision: CaseGateDecisionResult) -> None:
    if decision.status == "REJECTED" or decision.receipt_bytes is None:
        raise ValueError("rejected Case Gate decisions cannot persist a receipt")
    if decision.status == "STOP_V1" and decision.approved_testware is None:
        raise ValueError("STOP_V1 requires an Approved Testware reference artifact")
    if decision.status == "DRAFT_CASES" and decision.next_snapshot is None:
        raise ValueError("REQUEST_CHANGES requires a new DRAFT_CASES revision")
    if decision.status not in {"STOP_V1", "DRAFT_CASES"}:
        raise ValueError(f"unsupported Case Gate result state: {decision.status}")
    evidence_dir = Path(evidence_dir).resolve()
    root_workflow_path = evidence_dir / "workflow-state.json"
    try:
        root_workflow = json.loads(root_workflow_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"authoritative Case Review workflow is unavailable: {error}") from error
    if root_workflow.get("state") != "CASE_REVIEW" or root_workflow.get("artifact_sha256") != decision.reviewed_snapshot.sha256:
        raise ValueError("authoritative Case Review state changed before receipt persistence")
    if decision.test_only and not foundation.is_test_only_workspace_path(evidence_dir):
        raise ValueError("TEST_ONLY Case Gate evidence must use a temporary directory or .work/benchmark-runs")
    _write_exclusive(evidence_dir / "case-gate/receipt.json", decision.receipt_bytes)
    if decision.status == "STOP_V1":
        approved_record = decision.approved_testware.to_dict()
        if decision.test_only:
            approved_record = {
                "fixture_type": "TEST_ONLY_APPROVED_TESTWARE_EVIDENCE",
                "not_for_production": True,
                "approved_testware": approved_record,
            }
        _write_exclusive(
            evidence_dir / "approved-testware.json",
            (json.dumps(approved_record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        projection = [record.to_dict() for record in decision.reviewed_snapshot.records]
        _write_exclusive(
            evidence_dir / "canonical-testcases-approved-projection.json",
            (json.dumps(projection, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
    else:
        old_projection = [record.to_dict() for record in decision.reviewed_snapshot.records]
        _write_exclusive(
            evidence_dir / "case-gate/old-snapshot-projection.json",
            (json.dumps(old_projection, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        revision_dir = evidence_dir / "revisions" / decision.next_snapshot.revision
        draft = decision.next_snapshot.project("DRAFT")
        _write_exclusive(
            revision_dir / "canonical/canonical-testcases.json",
            (json.dumps([record.to_dict() for record in draft.records], ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        _write_exclusive(revision_dir / "canonical/semantic-payload.json", draft.payload_bytes)
        _write_exclusive(
            revision_dir / "workflow-state.json",
            (json.dumps({
                "state": "DRAFT_CASES",
                "artifact_id": draft.artifact_id,
                "artifact_revision": draft.revision,
                "artifact_sha256": draft.sha256,
                "review_status": "DRAFT",
                "validation_status": "NOT_RUN",
                "derived_from": {"artifact_id": decision.reviewed_snapshot.artifact_id, "revision": decision.reviewed_snapshot.revision, "sha256": decision.reviewed_snapshot.sha256},
            }, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
    _write_exclusive(
        evidence_dir / "case-gate/workflow-state.json",
        (json.dumps({
            "state": decision.workflow.state,
            "artifact_id": decision.workflow.artifact_id,
            "artifact_revision": decision.workflow.artifact_revision,
            "artifact_sha256": decision.workflow.artifact_sha256,
            "review_status": decision.workflow.review_status,
            "validation_status": decision.workflow.validation_status,
            "execution_contract_refs": [
                {"id": ref.get("id"), "revision": ref.get("revision"), "sha256": ref.get("sha256"), "approved": ref.get("approved")}
                for ref in decision.workflow.execution_oracle_refs
            ],
            "execution_oracle_refs": list(decision.workflow.execution_oracle_refs),
            "design_gate_receipt_mode": decision.workflow.design_gate_receipt_mode,
            "design_gate_receipt_evidence": decision.workflow.design_gate_receipt_evidence,
            "input_refs": [
                {"id": ref[0], "revision": ref[1], "sha256": ref[2]}
                for ref in decision.workflow.input_refs
            ],
            "history": list(decision.state_history),
            "test_only": decision.test_only,
            "project_policy_context": decision.workflow.project_policy_context,
        }, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    root_workflow.update({
        "state": decision.workflow.state,
        "artifact_id": decision.workflow.artifact_id,
        "artifact_revision": decision.workflow.artifact_revision,
        "artifact_sha256": decision.workflow.artifact_sha256,
        "review_status": decision.workflow.review_status,
        "validation_status": decision.workflow.validation_status,
        "history": list(decision.state_history),
        "test_only": decision.test_only,
    })
    foundation._write_workflow_state_atomic(root_workflow_path, root_workflow, list(decision.state_history))


def _write_exclusive(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as file:
        file.write(content)


def _write_if_same_or_absent(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError(f"refusing to overwrite different evidence: {path}")
    else:
        _write_exclusive(path, content)


class RawOutputIntegrityError(RuntimeError):
    pass


def _verify_authoritative_raw_evidence(path: Path, expected_hash: str) -> None:
    try:
        persisted_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise RawOutputIntegrityError(f"cannot verify authoritative Katalon evidence: {error}") from error
    if persisted_hash != expected_hash.lower():
        raise RawOutputIntegrityError("authoritative Katalon evidence changed before CASE_REVIEW commit")


def _write_authoritative_raw_evidence(path: Path, raw_bytes: bytes, expected_hash: str) -> None:
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash) or actual_hash != expected_hash.lower():
        raise RawOutputIntegrityError("captured Katalon bytes do not match the expected raw-output SHA-256")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".katalon-evidence-", delete=False) as stream:
            temporary_path = Path(stream.name)
            stream.write(raw_bytes)
            stream.flush()
        temporary_path.replace(path)
    except OSError as error:
        raise RawOutputIntegrityError(f"cannot persist or verify authoritative Katalon evidence: {error}") from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    _verify_authoritative_raw_evidence(path, expected_hash)


def _verify_case_review_raw_metadata(
    run_dir: Path,
    evidence_ref: foundation.RawEvidenceRef,
    expected_hash: str,
) -> None:
    _verify_authoritative_raw_evidence(Path(evidence_ref.path), expected_hash)
    for filename, field_name in (
        ("normalization-map.json", "raw_evidence"),
        ("normalization-results.json", "evidence"),
    ):
        try:
            payload = json.loads((run_dir / "evidence" / filename).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise RawOutputIntegrityError(f"CASE_REVIEW raw evidence metadata is unavailable: {filename}: {error}") from error
        values = payload.get(field_name) if isinstance(payload, dict) else None
        refs = [ref for ref in values if isinstance(ref, dict) and ref.get("field") == "katalon_raw_output"] if isinstance(values, list) else []
        if (
            len(refs) != 1
            or not isinstance(refs[0].get("path"), str)
            or Path(refs[0]["path"]).resolve() != Path(evidence_ref.path).resolve()
            or refs[0].get("sha256") != expected_hash
        ):
            raise RawOutputIntegrityError(f"CASE_REVIEW raw evidence metadata does not bind {filename} to the manifest hash")


def _verify_loaded_case_review_raw_evidence(run_dir: Path) -> None:
    evidence_dir = run_dir / "evidence"
    manifest_path = evidence_dir / "invocation-manifest.json"
    map_path = evidence_dir / "normalization-map.json"
    if not manifest_path.exists() and not map_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        normalization_map = json.loads(map_path.read_text(encoding="utf-8")) if map_path.exists() else None
    except (OSError, ValueError) as error:
        raise RawOutputIntegrityError(f"CASE_REVIEW authoritative Katalon evidence metadata is unavailable: {error}") from error
    if manifest is not None and not isinstance(manifest, dict):
        raise RawOutputIntegrityError("CASE_REVIEW invocation manifest has an invalid shape")
    if normalization_map is not None and not isinstance(normalization_map, dict):
        raise RawOutputIntegrityError("CASE_REVIEW normalization map has an invalid shape")
    expected_hash = manifest.get("raw_output_sha256") if manifest is not None else None
    raw_values = (normalization_map or {}).get("raw_evidence", [])
    if not isinstance(raw_values, list):
        raise RawOutputIntegrityError("CASE_REVIEW normalization map has an invalid raw-evidence list")
    raw_refs = [
        ref for ref in raw_values
        if isinstance(ref, dict) and ref.get("field") == "katalon_raw_output"
    ]
    if not raw_refs and expected_hash is None:
        return
    if (
        not isinstance(expected_hash, str)
        or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash)
        or len(raw_refs) != 1
        or raw_refs[0].get("sha256") != expected_hash.lower()
    ):
        raise RawOutputIntegrityError("CASE_REVIEW authoritative Katalon evidence does not match its invocation manifest")
    if not isinstance(raw_refs[0].get("path"), str):
        raise RawOutputIntegrityError("CASE_REVIEW authoritative Katalon evidence path is invalid")
    evidence_path = Path(raw_refs[0]["path"])
    try:
        actual_hash = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    except OSError as error:
        raise RawOutputIntegrityError(f"CASE_REVIEW authoritative Katalon evidence is unavailable: {error}") from error
    if actual_hash != expected_hash.lower():
        raise RawOutputIntegrityError("CASE_REVIEW authoritative Katalon evidence SHA-256 mismatch")


def persist_case_review(
    run_dir: str | Path,
    normalization: CaseNormalizationResult,
    validation: CaseValidatorResult,
    state: CaseWorkflowState,
    *,
    raw_evidence_bytes: bytes | None = None,
    expected_raw_output_sha256: str | None = None,
) -> None:
    if normalization.status != "NORMALIZED" or normalization.snapshot is None:
        raise ValueError("CASE_REVIEW persistence requires successful normalization")
    snapshot = normalization.snapshot
    if validation.status != "PASS" or (validation.artifact_id, validation.artifact_revision, validation.artifact_sha256) != (snapshot.artifact_id, snapshot.revision, snapshot.sha256):
        raise ValueError("CASE_REVIEW persistence requires validators bound to the exact testcase snapshot")
    if state.state != "CASE_REVIEW" or (state.artifact_id, state.artifact_revision, state.artifact_sha256) != (snapshot.artifact_id, snapshot.revision, snapshot.sha256):
        raise ValueError("CASE_REVIEW state is not bound to the exact testcase snapshot")
    run_dir = Path(run_dir)
    created_paths: list[Path] = []
    authoritative_raw_evidence: tuple[Path, str] | None = None
    raw_evidence_refs = [ref for ref in snapshot.evidence if ref.field == "katalon_raw_output"]
    if raw_evidence_refs:
        normalization_raw_refs = [ref for ref in normalization.evidence if ref.field == "katalon_raw_output"]
        if (
            len(raw_evidence_refs) != 1
            or len(normalization_raw_refs) != 1
            or raw_evidence_bytes is None
            or not isinstance(expected_raw_output_sha256, str)
            or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_raw_output_sha256)
            or raw_evidence_refs[0] != normalization_raw_refs[0]
            or raw_evidence_refs[0].sha256 != expected_raw_output_sha256.lower()
        ):
            raise RawOutputIntegrityError("CASE_REVIEW persistence lacks matching captured Katalon evidence and manifest hash")
        authoritative_path = Path(raw_evidence_refs[0].path)
        evidence_preexisting = authoritative_path.exists()
        try:
            authoritative_hash = expected_raw_output_sha256.lower()
            _write_authoritative_raw_evidence(authoritative_path, raw_evidence_bytes, authoritative_hash)
        except RawOutputIntegrityError:
            if not evidence_preexisting:
                authoritative_path.unlink(missing_ok=True)
            raise
        except OSError as error:
            if not evidence_preexisting:
                authoritative_path.unlink(missing_ok=True)
            raise RawOutputIntegrityError(f"cannot persist authoritative Katalon evidence: {error}") from error
        if not evidence_preexisting:
            created_paths.append(authoritative_path)
        authoritative_raw_evidence = (authoritative_path, authoritative_hash)

    def persist_file(path: Path, content: bytes) -> None:
        preexisting = path.exists()
        _write_if_same_or_absent(path, content)
        if not preexisting:
            created_paths.append(path)

    canonical = run_dir / "canonical"
    projected = snapshot.project(state.review_status)
    semantic_payload_path = canonical / "semantic-payload.json"
    persist_file(semantic_payload_path, snapshot.payload_bytes)
    records = [record.to_dict() for record in projected.records]
    canonical_testcases_path = canonical / "canonical-testcases.json"
    persist_file(canonical_testcases_path, (json.dumps(records, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    state_json = {
        "state": state.state,
        "artifact_id": state.artifact_id,
        "artifact_revision": state.artifact_revision,
        "artifact_sha256": state.artifact_sha256,
        "review_status": state.review_status,
        "validation_status": state.validation_status,
        "execution_contract_refs": [
            {"id": ref.get("id"), "revision": ref.get("revision"), "sha256": ref.get("sha256"), "approved": ref.get("approved")}
            for ref in state.execution_oracle_refs
        ],
        "execution_oracle_refs": list(state.execution_oracle_refs),
        "design_gate_receipt_mode": state.design_gate_receipt_mode,
        "design_gate_receipt_evidence": state.design_gate_receipt_evidence,
        "input_refs": [
            {"id": ref[0], "revision": ref[1], "sha256": ref[2]}
            for ref in state.input_refs
        ],
        "project_policy_context": state.project_policy_context,
        "history": [
            {"state": "DRAFT_CASES", "review_status": "DRAFT"},
            {"event": "SUBMIT_FOR_CASE_REVIEW", "state": "CASE_REVIEW", "review_status": "IN_REVIEW", "artifact_sha256": snapshot.sha256},
        ],
    }
    result = {
        "status": validation.status,
        "artifact_id": validation.artifact_id,
        "artifact_revision": validation.artifact_revision,
        "artifact_sha256": validation.artifact_sha256,
        "findings": [finding.__dict__ for finding in validation.findings],
    }
    persist_file(run_dir / "evidence/validator-results.json", (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    source_map = {
        "profile": normalization.profile,
        "raw_evidence": [ref.__dict__ for ref in normalization.evidence],
        "fields": {
            case_id: {field: ref.__dict__ for field, ref in fields.items()}
            for case_id, fields in (snapshot.field_sources or {}).items()
        },
    }
    persist_file(run_dir / "evidence/normalization-map.json", (json.dumps(source_map, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    normalization_result = {
        "status": normalization.status,
        "profile": normalization.profile,
        "findings": [finding.__dict__ for finding in normalization.findings],
        "evidence": [ref.__dict__ for ref in normalization.evidence],
    }
    normalization_results_path = run_dir / "evidence/normalization-results.json"
    persist_file(normalization_results_path, (json.dumps(normalization_result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    workflow_path = run_dir / "workflow-state.json"
    persist_file(workflow_path, (json.dumps(state_json, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if authoritative_raw_evidence is not None:
        try:
            _verify_case_review_raw_metadata(run_dir, raw_evidence_refs[0], authoritative_raw_evidence[1])
        except RawOutputIntegrityError as error:
            rollback_errors = []
            for path in reversed(created_paths):
                try:
                    path.unlink(missing_ok=True)
                except OSError as rollback_error:
                    rollback_errors.append(f"{path}: {rollback_error}")
            if rollback_errors:
                raise RawOutputIntegrityError(f"{error}; CASE_REVIEW rollback incomplete: {'; '.join(rollback_errors)}") from error
            raise


def _skill_inventory(skill_dir: Path) -> list[dict]:
    return [
        {"path": path.relative_to(skill_dir).as_posix(), "sha256": _hash_path(path)}
        for path in sorted(skill_dir.rglob("*")) if path.is_file()
    ]


def _pin_integrity_failure(relative: str, expected: str, actual: str | None, reason: str) -> RuntimeError:
    actual_hash = actual if actual is not None else "<missing>"
    return RuntimeError(
        f"PIN_INTEGRITY_FAILURE: relative_file={relative}; expected_sha256={expected}; "
        f"actual_sha256={actual_hash}; pinned_commit={KATALON_COMMIT}; reason={reason}"
    )


def _validate_pinned_manifest(skill_dir: Path | None = None) -> None:
    if not isinstance(KATALON_COMMIT, str) or not re.fullmatch(r"[0-9a-f]{40}", KATALON_COMMIT):
        commit = KATALON_COMMIT if isinstance(KATALON_COMMIT, str) else None
        raise _pin_integrity_failure("<pin-manifest>", "40-character pinned commit", commit, "pinned commit unavailable")
    manifest_files = set(KATALON_SKILL_FILES)
    required_files = set(KATALON_REQUIRED_SKILL_FILES)
    unresolved = sorted(required_files - manifest_files)
    unexpected = sorted(manifest_files - required_files)
    relative = (unresolved or unexpected or [None])[0]
    if relative is not None:
        expected = KATALON_SKILL_FILES.get(relative, "<missing manifest entry>")
        path = skill_dir / relative if skill_dir is not None else None
        actual = _hash_path(path) if path is not None and path.is_file() else None
        raise _pin_integrity_failure(relative, expected, actual, "pinned manifest entries do not match the required skill files")
    for relative in KATALON_REQUIRED_SKILL_FILES:
        expected = KATALON_SKILL_FILES[relative]
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise _pin_integrity_failure(relative, expected if isinstance(expected, str) and expected else "<unavailable>", None, "expected pin unavailable")


def _verify_pinned_skill(skill_dir: str | Path) -> list[dict]:
    skill_dir = Path(skill_dir).resolve()
    _validate_pinned_manifest(skill_dir)
    for relative in KATALON_REQUIRED_SKILL_FILES:
        path = skill_dir / relative
        actual = _hash_path(path) if path.is_file() else None
        expected = KATALON_SKILL_FILES[relative]
        if actual != expected:
            raise _pin_integrity_failure(relative, expected, actual, "installed skill file does not match the pinned bytes")
    extra_files = sorted(
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file() and path.relative_to(skill_dir).as_posix() not in KATALON_REQUIRED_SKILL_FILES
    )
    if extra_files:
        relative = extra_files[0]
        raise _pin_integrity_failure(relative, "<not present in pinned manifest>", _hash_path(skill_dir / relative), "unexpected installed skill file")
    return _skill_inventory(skill_dir)


def _install_pinned_skill(native_workspace: Path) -> tuple[Path, list[dict]]:
    _validate_pinned_manifest()
    skill_dir = native_workspace / ".agents/skills" / KATALON_CAPABILITY
    source = ROOT / "kits/test/skills" / KATALON_CAPABILITY
    if not source.is_dir():
        raise _pin_integrity_failure("<source>", "bundled skill", None, "test-only bundled skill source is unavailable")
    shutil.copytree(source, skill_dir)
    return skill_dir, _verify_pinned_skill(skill_dir)


def _invocation_prompt(
    input_path: Path,
    raw_output: Path,
    model: str,
    *,
    skill_dir: Path,
    baseline_dir: Path,
    project_root: Path,
) -> str:
    return f"""$create-test-cases

Use the installed project-local native Katalon create-test-cases skill from upstream commit {KATALON_COMMIT}. Follow its manual testcase design method. Do not read the Petclinic implementation source.
The pinned skill is installed at {skill_dir / 'SKILL.md'}. The project root is {project_root}. Read and invoke it natively; if it is not discoverable, stop without generating cases and report PINNED_SKILL_UNAVAILABLE. Do not imitate its methods from this prompt.

Input: {input_path}
Output: {raw_output}
Model: {model}

Use only the approved canonical Test Design as the coverage oracle. Use `{baseline_dir / '04-srs-excerpt.md'}` and `{baseline_dir / '03-approved-business-rules.md'}` as the separate business oracle; do not use decision-history files. The input file has the exact collection ID/revision/hash, all source refs, and the unresolved BA UNKNOWN topics. Preserve all IDs and wording. Do not add behavior, answer UNKNOWN, infer a field mapping, or use current code as a behavior source.

Every Test Design row with non-null expected behavior needs testcase coverage through its exact TD reference. When such a row also has open questions, cover only its approved expected behavior and do not assert the unresolved topic. Only null-outcome rows are deferred without cases.

Generate local manual testcase semantics only. Do not look up or access Katalon projects, repositories, requirements, existing cases, TestOps, suites, requirement links, runs, or execution. Do not write to any external Katalon service. Do not create a suite, automation, execution, XMind, or Excel output.
Do not spawn or delegate to agents. Read only the pinned skill/reference files and approved inputs listed here; do not inspect other project files.

Rows with null expected behavior must appear only in a clearly deferred/UNKNOWN note and must not become a testcase or pass/fail assertion. Every testcase must cite explicit BA refs and exact canonical design IDs. Keep case-level Test Data at case level; include step Test Data only if the source step explicitly has it. Keep priorities P0-P3 as advisory metadata.

Use this exact known native raw profile for every case and add no fields or alternate sections inside a case:
## TC-001 Case title
- Mô tả: objective
- Tiền điều kiện: preconditions
- Bước và kết quả mong đợi:
  1. action. → expected result.
- Test Data: case-level data or None
- Priority: P1.
- Trace: FR/BR IDs; exact canonical design IDs (for example: FR-001, BR-004; 1.1-UNIT-001). Do not prefix design IDs with TD or add other text.

Make each missing setup, action, interval mapping, or observation detail explicit in the relevant preconditions using this exact marker: OPEN execution dependencies: <execution-only detail>. Do not use free-form OPEN prose as a dependency or turn a BA UNKNOWN into an execution dependency. TC-012 editable-field selection remains OPEN when applicable. No approved execution oracle is included unless its refs appear in the input.

Write only the completed raw testcase Markdown to {raw_output}. The caller retains raw output, invocation JSONL, stderr, and status; do not create sidecar evidence files.
Write the completed output with Python 3 pathlib so its UTF-8 bytes are preserved exactly.
"""



def _load_persisted_design_authorization(
    design_run_dir: str | Path,
    baseline: foundation.ApprovedBaseline,
) -> tuple[foundation.DesignSnapshot, DesignGateAuthorization, dict]:
    """Trust only a previously persisted HUMAN_AUTHENTICATED Design approval."""
    design_run = Path(design_run_dir).resolve()
    design = foundation.load_persisted_design_snapshot(
        design_run, require_state="APPROVED_DESIGN"
    )
    workflow_path = design_run / "workflow-state.json"
    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"approved Design workflow is unavailable: {error}") from error
    if workflow.get("design_gate_receipt_mode") != "HUMAN_AUTHENTICATED":
        raise ValueError("production testcase generation requires a persisted Human-authenticated Design approval")

    receipt_path = design_run / "design-gate/revisions" / design.revision / "receipt.json"
    try:
        receipt_bytes = receipt_path.read_bytes()
        receipt = json.loads(receipt_bytes.decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as error:
        raise ValueError(f"persisted Design Gate receipt is unavailable: {error}") from error
    finding = _receipt_shape_finding(receipt, "DESIGN_REVIEW")
    if finding or receipt.get("decision") != "APPROVE":
        raise ValueError(finding.message if finding else "persisted Design Gate receipt is not APPROVE")
    if str(receipt.get("actor_id", "")).startswith("TEST_ONLY:"):
        raise ValueError("TEST_ONLY Design approval is not valid for production testcase generation")

    expected_refs = tuple(
        (ref["id"], ref["revision"], ref["sha256"])
        for ref in foundation.design_gate_input_refs(baseline, design_run)
    )
    actual_refs = _receipt_refs(receipt)
    receipt_ref = {
        "path": str(receipt_path),
        "sha256": hashlib.sha256(receipt_bytes).hexdigest(),
    }
    if (
        receipt.get("artifact_id") != design.artifact_id
        or receipt.get("artifact_revision") != design.revision
        or str(receipt.get("artifact_sha256", "")).lower() != design.sha256
        or actual_refs != expected_refs
        or workflow.get("design_gate_receipt_evidence") != receipt_ref
    ):
        raise ValueError("persisted Design Gate approval is stale or not bound to the current Design/BA inputs")
    validation = foundation.validate_design(design, baseline)
    if validation.status != "PASS":
        raise ValueError("persisted approved Design no longer passes the frozen validator")
    authorization = DesignGateAuthorization(
        design.artifact_id,
        design.revision,
        design.sha256,
        actual_refs,
        False,
        str(receipt_path),
        receipt_ref["sha256"],
    )
    return design, authorization, receipt_ref


def prepare_same_session_cases(
    handoff_path: str | Path,
    design_run_dir: str | Path,
    run_dir: str | Path,
    *,
    project_root: str | Path,
    skill_dir: str | Path,
    execution_oracle_refs: Iterable[dict] = (),
) -> dict:
    """Prepare approved Design inputs for same-session create-test-cases execution."""
    run_dir = Path(run_dir).resolve()
    project_root = Path(project_root).resolve()
    skill_dir = Path(skill_dir).resolve()
    expected_skill = (project_root / ".agents/skills" / KATALON_CAPABILITY).resolve()
    if not expected_skill.is_dir() or not skill_dir.is_dir() or not expected_skill.samefile(skill_dir):
        raise RuntimeError("same-session testcase generation must use the project-local pinned create-test-cases skill")
    skill_files = _verify_pinned_skill(skill_dir)

    baseline = foundation.load_approved_baseline(handoff_path)
    design, authorization, receipt_ref = _load_persisted_design_authorization(
        design_run_dir, baseline
    )
    execution_refs = tuple(execution_oracle_refs)
    katalon_input = adapt_approved_design_to_katalon(
        design,
        authorization,
        baseline,
        execution_oracle_refs=execution_refs,
    )
    policy_context = foundation.persist_project_policy_context(
        run_dir, project_root, "CASES"
    )
    if policy_context and policy_context["policy"]:
        from .test_kit_policy import non_authoritative_policy_prompt, resolve_project_policy
        katalon_input = replace(
            katalon_input,
            markdown=katalon_input.markdown + "\n" + non_authoritative_policy_prompt(
                resolve_project_policy(project_root, "CASES"), policy_context["policy"]
            ),
        )

    input_path = run_dir / "inputs/approved-test-design.md"
    _write_if_same_or_absent(input_path, katalon_input.markdown.encode("utf-8"))
    for source in (*baseline.source_paths.values(), baseline.handoff_path):
        _write_if_same_or_absent(
            run_dir / "inputs/baseline" / source.name, source.read_bytes()
        )

    raw_output = run_dir / "raw-output/test-cases.md"
    instructions = run_dir / "raw-output/same-session-instructions.md"
    prompt = f"""$create-test-cases

Execute the installed project-local create-test-cases capability in this current agent session.
Do not start codex, codexapi, another agent process, or a nested model invocation.
Pinned skill: {skill_dir / 'SKILL.md'}
Approved input: {input_path}
Raw output: {raw_output}

Use the approved canonical Test Design as the coverage oracle and the embedded BUSINESS ORACLE as business authority.
Do not add, remove, merge, or reinterpret approved coverage. Preserve UNKNOWN/deferred semantics.
Generate local manual testcase semantics only. Do not access external Katalon/TestOps services.
Do not inspect application source to invent expected behavior.

Use the pinned skill's manual testcase method and write only its completed raw testcase Markdown to the prepared raw output path.
If the capability cannot complete from these prepared inputs, stop and report the blocker.
"""
    _write_if_same_or_absent(instructions, prompt.encode("utf-8"))

    input_manifest = {
        "design": {
            "artifact_id": design.artifact_id,
            "revision": design.revision,
            "sha256": design.sha256,
        },
        "ba_input_refs": list(katalon_input.ba_refs),
        "execution_contract_refs": list(katalon_input.execution_refs),
        "receipt_mode": "HUMAN_AUTHENTICATED",
        "design_gate_receipt_evidence": receipt_ref,
        "project_policy_context": policy_context,
    }
    _write_if_same_or_absent(
        run_dir / "inputs/input-manifest.json",
        (json.dumps(input_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    manifest = {
        "schema_version": 1,
        "mode": "SAME_SESSION",
        "stage": "CASES",
        "status": "PREPARED",
        "feature_id": baseline.feature_id,
        "ba_revision": baseline.revision,
        "handoff_path": str(baseline.handoff_path),
        "handoff_sha256": baseline.handoff_sha256,
        "design_run_dir": str(Path(design_run_dir).resolve()),
        "design": input_manifest["design"],
        "project_root": str(project_root),
        "skill": {
            "capability": KATALON_CAPABILITY,
            "path": str(skill_dir),
            "commit": KATALON_COMMIT,
            "files": skill_files,
        },
        "project_policy_context": policy_context,
        "receipt_mode": "HUMAN_AUTHENTICATED",
        "design_gate_receipt_evidence": receipt_ref,
        "execution_contract_refs": list(execution_refs),
        "input_path": str(input_path),
        "instructions_path": str(instructions),
        "raw_output_path": str(raw_output),
    }
    manifest_path = run_dir / "evidence/same-session-prepare.json"
    _write_exclusive(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return {**manifest, "manifest_path": str(manifest_path)}


def finalize_same_session_cases(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    raw_cases: str | Path | None = None,
    artifact_id: str | None = None,
    revision: str = "1",
) -> CaseIntegrationResult:
    """Normalize, validate and submit same-session testcase output to CASE_REVIEW."""
    run_dir = Path(run_dir).resolve()
    prepare_path = run_dir / "evidence/same-session-prepare.json"
    if not prepare_path.is_file():
        raise RuntimeError("same-session testcase preparation evidence is missing")
    prepared = json.loads(prepare_path.read_text(encoding="utf-8"))
    if prepared.get("mode") != "SAME_SESSION" or prepared.get("stage") != "CASES" or prepared.get("status") != "PREPARED":
        raise RuntimeError("same-session testcase preparation evidence is invalid")

    baseline = foundation.load_approved_baseline(handoff_path)
    design, _, receipt_ref = _load_persisted_design_authorization(
        prepared["design_run_dir"], baseline
    )
    if (
        prepared.get("feature_id") != baseline.feature_id
        or prepared.get("ba_revision") != baseline.revision
        or prepared.get("handoff_sha256") != baseline.handoff_sha256
        or prepared.get("design") != {
            "artifact_id": design.artifact_id,
            "revision": design.revision,
            "sha256": design.sha256,
        }
        or prepared.get("design_gate_receipt_evidence") != receipt_ref
    ):
        raise RuntimeError("BA baseline or approved Design changed after testcase preparation")

    raw_path = Path(raw_cases).resolve() if raw_cases else Path(prepared["raw_output_path"]).resolve()
    expected_raw = Path(prepared["raw_output_path"]).resolve()
    if raw_path != expected_raw or not raw_path.is_file():
        raise RuntimeError(f"same-session testcase output is missing or not at the prepared path: {expected_raw}")
    raw_hash = _hash_path(raw_path)
    manifest = {
        "mode": "SAME_SESSION",
        "status": "ARTIFACT_COMPLETE",
        "raw_output_path": str(raw_path),
        "raw_output_sha256": raw_hash,
        "receipt_mode": "HUMAN_AUTHENTICATED",
        "design_gate_receipt_evidence": receipt_ref,
        "project_policy_context": prepared.get("project_policy_context"),
    }
    result = _finish_case_integration(
        manifest,
        design,
        baseline,
        run_dir,
        execution_contract_refs=tuple(prepared.get("execution_contract_refs", [])),
        artifact_id=artifact_id or f"{baseline.feature_id}-testcases",
        revision=revision,
    )
    if result.status != "CASE_REVIEW":
        raise RuntimeError(f"testcase finalize failed: {result.status}")
    summary = {
        "schema_version": 1,
        "mode": "SAME_SESSION",
        "stage": "CASES",
        "status": result.status,
        "feature_id": baseline.feature_id,
        "artifact_id": result.workflow.artifact_id,
        "artifact_revision": result.workflow.artifact_revision,
        "artifact_sha256": result.workflow.artifact_sha256,
        "review_status": result.workflow.review_status,
        "validation_status": result.workflow.validation_status,
        "raw_output_path": str(raw_path),
    }
    _write_exclusive(
        run_dir / "evidence/same-session-finalize.json",
        (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return result


def invoke_native_katalon(
    design: foundation.DesignSnapshot,
    receipt: dict,
    baseline: foundation.ApprovedBaseline,
    run_dir: str | Path,
    *,
    design_workflow_dir: str | Path,
    human_actor_authenticator: Callable,
    project_root: str | Path,
    execution_oracle_refs: Iterable[dict] = (),
    model: str = "gpt-6-luna",
) -> dict:
    checked = validate_design_gate_receipt(
        receipt, design, baseline, design_workflow_dir=design_workflow_dir,
        human_actor_authenticator=human_actor_authenticator,
    )
    if checked.status != "PASS":
        raise ValueError(checked.finding.message)
    return _invoke_native_katalon(
        design, checked.authorization, baseline, run_dir,
        execution_oracle_refs=execution_oracle_refs, project_root=project_root, model=model,
        execution_oracle_authenticator=human_actor_authenticator,
    )


def invoke_native_katalon_test_only(
    design: foundation.DesignSnapshot,
    receipt_fixture_path: str | Path,
    baseline: foundation.ApprovedBaseline,
    run_dir: str | Path,
    *,
    design_workflow_dir: str | Path,
    project_root: str | Path | None = None,
    execution_oracle_refs: Iterable[dict] = (),
    model: str = "gpt-6-luna",
) -> dict:
    receipt_fixture_path = Path(receipt_fixture_path).resolve()
    checked = validate_test_only_design_fixture(
        receipt_fixture_path, design, baseline, design_workflow_dir=design_workflow_dir,
    )
    if checked.status != "PASS":
        raise ValueError(checked.finding.message)
    run_dir = Path(run_dir).resolve()
    if not foundation.is_test_only_workspace_path(run_dir):
        raise ValueError("TEST_ONLY native invocation output must use a temporary directory or .work/benchmark-runs")
    return _invoke_native_katalon(
        design, checked.authorization, baseline, run_dir,
        execution_oracle_refs=execution_oracle_refs,
        project_root=project_root,
        receipt_evidence=foundation.RawEvidenceRef(str(receipt_fixture_path), _hash_path(receipt_fixture_path), field="TEST_ONLY_design_gate_receipt_fixture"),
        model=model,
        allow_test_only_execution_oracles=True,
    )


def _invoke_native_katalon(
    design: foundation.DesignSnapshot,
    authorization: DesignGateAuthorization,
    baseline: foundation.ApprovedBaseline,
    run_dir: Path,
    *,
    execution_oracle_refs: Iterable[dict],
    project_root: str | Path | None,
    receipt_evidence: foundation.RawEvidenceRef | None = None,
    model: str,
    execution_oracle_authenticator: Callable | None = None,
    allow_test_only_execution_oracles: bool = False,
) -> dict:
    run_dir = run_dir.resolve()
    if project_root is None and not authorization.test_only:
        raise _pin_integrity_failure(
            f".agents/skills/{KATALON_CAPABILITY}", "project-local pinned skill", None,
            "production invocation requires a project root; temporary fallback is TEST_ONLY only",
        )
    project_root = Path(project_root).resolve() if project_root is not None else None
    design_run = Path(authorization.receipt_path).resolve().parents[3]
    design_context_path = design_run / "inputs/project-policy-context.json"
    if design_context_path.is_file():
        design_context = json.loads(design_context_path.read_text(encoding="utf-8"))
        bound_root = Path(design_context["project_root"]).resolve()
        if project_root is not None and project_root != bound_root:
            raise foundation.ProjectPolicyBindingError("case project root differs from the approved Design run")
        project_root = bound_root
    if project_root is not None:
        _verify_pinned_skill(project_root / ".agents/skills" / KATALON_CAPABILITY)
    codex_command = resolve_codex_command()
    katalon_input = adapt_approved_design_to_katalon(
        design, authorization, baseline, execution_oracle_refs=execution_oracle_refs,
        execution_oracle_authenticator=execution_oracle_authenticator,
        allow_test_only_execution_oracles=allow_test_only_execution_oracles,
    )
    if authorization.test_only and not foundation.is_test_only_workspace_path(run_dir):
        raise RuntimeError("TEST_ONLY invocation must use a temporary directory or .work/benchmark-runs")
    if (run_dir / "evidence/invocation-manifest.json").exists():
        raise RuntimeError("invocation evidence already exists; choose a new run directory")
    policy_context = foundation.persist_project_policy_context(run_dir, project_root, "CASES") if project_root else None
    if policy_context and policy_context["policy"]:
        from .test_kit_policy import non_authoritative_policy_prompt, resolve_project_policy
        guidance = non_authoritative_policy_prompt(resolve_project_policy(project_root, "CASES"), policy_context["policy"])
        katalon_input = replace(katalon_input, markdown=katalon_input.markdown + "\n" + guidance)
    _write_if_same_or_absent(run_dir / "inputs/approved-test-design.md", katalon_input.markdown.encode("utf-8"))
    for source in (*baseline.source_paths.values(), baseline.handoff_path):
        _write_if_same_or_absent(run_dir / "inputs/baseline" / source.name, source.read_bytes())
    input_manifest = {
        "design": {"artifact_id": design.artifact_id, "revision": design.revision, "sha256": design.sha256},
        "design_evidence": [ref.__dict__ for ref in design.evidence],
        "ba_input_refs": list(katalon_input.ba_refs),
        "execution_contract_refs": list(katalon_input.execution_refs),
        "receipt_mode": "TEST_ONLY" if authorization.test_only else "HUMAN_AUTHENTICATED",
        "design_gate_receipt_evidence": {
            "path": authorization.receipt_path,
            "sha256": authorization.receipt_sha256,
            "mode": "TEST_ONLY" if authorization.test_only else "HUMAN_AUTHENTICATED",
            "fixture": receipt_evidence.__dict__ if receipt_evidence else None,
        },
        "model": model,
        "project_policy_context": policy_context,
    }
    _write_if_same_or_absent(run_dir / "inputs/input-manifest.json", (json.dumps(input_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    raw_dir = run_dir / "raw-output"
    raw_output = raw_dir / "test-cases.md"
    manifest_path = run_dir / "evidence/invocation-manifest.json"
    return _run_pinned_native_skill(
        run_dir, run_dir / "inputs/approved-test-design.md", model, input_manifest,
        raw_output, manifest_path, project_root=project_root, test_only=authorization.test_only,
        codex_command=codex_command,
    )


def _run_pinned_native_skill(
    run_dir: Path,
    input_path: Path,
    model: str,
    input_manifest: dict,
    raw_output: Path,
    manifest_path: Path,
    *,
    project_root: Path | None,
    test_only: bool,
    codex_command: CodexCommand | None = None,
) -> dict:
    if project_root is None and not test_only:
        raise _pin_integrity_failure(
            f".agents/skills/{KATALON_CAPABILITY}", "project-local pinned skill", None,
            "temporary skill installation is TEST_ONLY only",
        )
    codex_command = codex_command or resolve_codex_command()
    project_root = Path(project_root).resolve() if project_root is not None else None
    run_dir, input_path, raw_output, manifest_path = map(
        lambda path: Path(path).resolve(), (run_dir, input_path, raw_output, manifest_path)
    )
    stdout_path, stderr_path = raw_output.parent / "invocation.jsonl", raw_output.parent / "stderr.txt"
    raw_output.parent.mkdir(parents=True, exist_ok=True)
    temporary_context = (
        tempfile.TemporaryDirectory(prefix="test-kit-katalon-")
        if project_root is None else nullcontext(None)
    )
    with temporary_context as temporary:
        if project_root is None:
            native_workspace = Path(temporary)
            skill_dir, skill_files = _install_pinned_skill(native_workspace)
            native_input = native_workspace / "inputs/approved-test-design.md"
            native_raw_output = native_workspace / "output/test-cases.md"
            native_agent_final = native_workspace / "output/agent-final.md"
            native_input.parent.mkdir(parents=True, exist_ok=True)
            native_raw_output.parent.mkdir(parents=True, exist_ok=True)
            native_input.write_bytes(input_path.read_bytes())
            native_baseline = native_workspace / "inputs/baseline"
            native_baseline.mkdir(parents=True, exist_ok=True)
            for name in ("03-approved-business-rules.md", "04-srs-excerpt.md"):
                source = run_dir / "inputs/baseline" / name
                if not source.is_file():
                    raise RuntimeError(f"native Katalon invocation is missing approved BA input: {name}")
                (native_baseline / name).write_bytes(source.read_bytes())
            invocation_mode = "TEST_ONLY_TEMPORARY"
            skill_installation = "TEST_ONLY isolated temporary copy; every file SHA-256 matched the pinned upstream commit"
            add_dir = native_workspace
        else:
            native_workspace = project_root
            skill_dir = project_root / ".agents/skills" / KATALON_CAPABILITY
            skill_files = _verify_pinned_skill(skill_dir)
            native_input = input_path
            native_raw_output = raw_output
            native_agent_final = run_dir / "evidence/native-agent-final.md"
            native_agent_final.parent.mkdir(parents=True, exist_ok=True)
            native_baseline = run_dir / "inputs/baseline"
            for name in ("03-approved-business-rules.md", "04-srs-excerpt.md"):
                if not (native_baseline / name).is_file():
                    raise RuntimeError(f"native Katalon invocation is missing approved BA input: {name}")
            invocation_mode = "PROJECT_LOCAL"
            skill_installation = "project-local installed skill; every file SHA-256 matched the pinned upstream commit"
            add_dir = run_dir
        prompt = _invocation_prompt(
            native_input, native_raw_output, model,
            skill_dir=skill_dir, baseline_dir=native_baseline, project_root=native_workspace,
        )
        _write_if_same_or_absent(raw_output.parent / "invocation-prompt.md", prompt.encode("utf-8"))
        argv = codex_command.argv([
            "--no-daemon", "--approve-for-me", "exec", "--json", "--ephemeral",
            "--skip-git-repo-check", "--sandbox", "danger-full-access", "--model", model,
            "-C", str(native_workspace), "--add-dir", str(add_dir), "-o", str(native_agent_final), "-",
        ])
        manifest = {
            "repository": KATALON_REPOSITORY,
            "commit": KATALON_COMMIT,
            "capability": KATALON_CAPABILITY,
            "invocation_mode": invocation_mode,
            "installed_skill_path": str(skill_dir),
            "installed_skill_files": skill_files,
            "skill_installation": skill_installation,
            "native_workspace_path": str(native_workspace),
            "native_raw_output_path": str(native_raw_output),
            "native_agent_final_path": str(native_agent_final),
            "filesystem_sandbox": "danger-full-access",
            "petclinic_source_supplied_as_input": False,
            "model": model,
            "normalizer_profile": "katalon-native-v1",
            "design": input_manifest["design"],
            "ba_input_refs": input_manifest["ba_input_refs"],
            "execution_contract_refs": input_manifest["execution_contract_refs"],
            "receipt_mode": input_manifest["receipt_mode"],
            "design_gate_receipt_evidence": input_manifest["design_gate_receipt_evidence"],
            "project_policy_context": input_manifest.get("project_policy_context"),
            "invocation_command": argv,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "status": "RUNNING",
            "raw_output_path": str(raw_output),
            "raw_output_sha256": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "exit_code": None,
        }
        _write_exclusive(manifest_path, (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        with stdout_path.open("xb") as stdout_file, stderr_path.open("xb") as stderr_file:
            process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file, cwd=native_workspace)
            try:
                process.stdin.write(prompt.encode("utf-8"))
                process.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            while process.poll() is None:
                time.sleep(0.2)
            exit_code = process.wait()
        if project_root is None and native_raw_output.is_file():
            _write_exclusive(raw_output, native_raw_output.read_bytes())
        if project_root is None and native_agent_final.is_file():
            _write_exclusive(run_dir / "evidence/native-agent-final.md", native_agent_final.read_bytes())
        if raw_output.is_file():
            manifest["raw_output_sha256"] = _hash_path(raw_output)
            if "PINNED_SKILL_UNAVAILABLE" in raw_output.read_text(encoding="utf-8", errors="replace"):
                manifest["failure"] = "native Codex runtime could not load the pinned project-local skill"
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        manifest["exit_code"] = exit_code
        manifest["status"] = "SKILL_UNAVAILABLE" if manifest.get("failure") else "ARTIFACT_COMPLETE" if manifest["raw_output_sha256"] else "FAILED"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if manifest["status"] == "SKILL_UNAVAILABLE":
        raise RuntimeError(f"pinned native Katalon skill was not loaded; see {manifest_path}")
    if not manifest["raw_output_sha256"]:
        raise RuntimeError(f"native Katalon skill did not produce raw testcase output; see {manifest_path}")
    return manifest


def _persist_case_failure(
    run_dir: str | Path,
    normalization: CaseNormalizationResult,
    validation: CaseValidatorResult | None,
) -> None:
    run_dir = Path(run_dir)
    _write_if_same_or_absent(
        run_dir / "evidence/normalization-results.json",
        (json.dumps({
            "status": normalization.status,
            "profile": normalization.profile,
            "findings": [finding.__dict__ for finding in normalization.findings],
            "evidence": [ref.__dict__ for ref in normalization.evidence],
        }, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    if normalization.snapshot is not None:
        snapshot = normalization.snapshot
        records = [record.to_dict() for record in snapshot.records]
        _write_if_same_or_absent(run_dir / "canonical/draft-testcases.json", (json.dumps(records, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        _write_if_same_or_absent(run_dir / "canonical/semantic-payload.json", snapshot.payload_bytes)
        _write_if_same_or_absent(run_dir / "workflow-state.json", (json.dumps({
            "state": "DRAFT_CASES",
            "artifact_id": snapshot.artifact_id,
            "artifact_revision": snapshot.revision,
            "artifact_sha256": snapshot.sha256,
            "review_status": "DRAFT",
            "validation_status": validation.status if validation else "NOT_RUN",
        }, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if validation is not None:
        _write_if_same_or_absent(run_dir / "evidence/validator-results.json", (json.dumps({
            "status": validation.status,
            "artifact_id": validation.artifact_id,
            "artifact_revision": validation.artifact_revision,
            "artifact_sha256": validation.artifact_sha256,
            "findings": [finding.__dict__ for finding in validation.findings],
    }, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def _case_raw_integrity_failure(
    run_dir: str | Path,
    manifest: dict,
    raw_path: Path,
    raw_hash: str,
    message: str,
    *,
    evidence_path: Path | None = None,
) -> CaseIntegrationResult:
    evidence = (foundation.RawEvidenceRef(
        str((evidence_path or raw_path).resolve()), raw_hash, field="katalon_raw_output",
    ),)
    finding = foundation.Finding("RAW_OUTPUT_INTEGRITY_FAILURE", message, str(raw_path), field="sha256")
    normalization = CaseNormalizationResult("CANNOT_NORMALIZE", None, None, (finding,), evidence)
    _persist_case_failure(run_dir, normalization, None)
    return CaseIntegrationResult("RAW_OUTPUT_INTEGRITY_FAILURE", manifest, normalization, None, None)


def _finish_case_integration(
    manifest: dict,
    design: foundation.DesignSnapshot,
    baseline: foundation.ApprovedBaseline,
    run_dir: str | Path,
    *,
    execution_contract_refs: Iterable[dict],
    artifact_id: str,
    revision: str,
    execution_oracle_authenticator: Callable | None = None,
    allow_test_only_execution_oracles: bool = False,
) -> CaseIntegrationResult:
    raw_path, raw_bytes, actual_raw_hash, integrity_message = _read_verified_katalon_raw(manifest)
    if integrity_message:
        return _case_raw_integrity_failure(
            run_dir, manifest, raw_path, actual_raw_hash or hashlib.sha256(raw_bytes).hexdigest(), integrity_message,
        )

    verified_path = Path(run_dir) / "evidence/verified-katalon-output.md"
    normalization = normalize_katalon_output_bytes(
        raw_bytes, design, baseline, source_path=verified_path,
        artifact_id=artifact_id, revision=revision,
    )
    if normalization.status != "NORMALIZED" or normalization.snapshot is None:
        _persist_case_failure(run_dir, normalization, None)
        return CaseIntegrationResult("CANNOT_NORMALIZE", manifest, normalization, None, None)
    validation = validate_testcases(
        normalization.snapshot, design, baseline, execution_contract_refs=execution_contract_refs,
        execution_oracle_authenticator=execution_oracle_authenticator,
        allow_test_only_execution_oracles=allow_test_only_execution_oracles,
    )
    if validation.status != "PASS":
        _persist_case_failure(run_dir, normalization, validation)
        return CaseIntegrationResult("VALIDATION_FAILED", manifest, normalization, validation, None)
    workflow = submit_cases_for_review(
        start_case_workflow(normalization.snapshot), normalization.snapshot, validation,
        execution_contract_refs=execution_contract_refs,
        design_gate_receipt_mode=manifest.get("receipt_mode"),
        design_gate_receipt_evidence=manifest.get("design_gate_receipt_evidence"),
        input_refs=case_gate_input_refs(baseline, design, run_dir=run_dir),
        project_policy_context=manifest.get("project_policy_context"),
    )
    try:
        persist_case_review(
            run_dir, normalization, validation, workflow,
            raw_evidence_bytes=raw_bytes,
            expected_raw_output_sha256=manifest.get("raw_output_sha256"),
        )
    except RawOutputIntegrityError as error:
        return _case_raw_integrity_failure(
            run_dir, manifest, raw_path, actual_raw_hash, str(error), evidence_path=verified_path,
        )
    return CaseIntegrationResult("CASE_REVIEW", manifest, normalization, validation, workflow)


def _read_verified_katalon_raw(manifest: dict) -> tuple[Path, bytes, str | None, str | None]:
    raw_path = Path(manifest.get("raw_output_path", ""))
    try:
        raw_bytes = raw_path.read_bytes()
    except OSError as error:
        return raw_path, b"", None, f"raw Katalon output is unavailable: {error}"
    actual_hash = hashlib.sha256(raw_bytes).hexdigest()
    expected_hash = manifest.get("raw_output_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash) or actual_hash != expected_hash.lower():
        return raw_path, raw_bytes, actual_hash, "raw Katalon output SHA-256 does not match invocation evidence"
    return raw_path, raw_bytes, actual_hash, None


def run_katalon_case_integration(
    design: foundation.DesignSnapshot,
    receipt: dict,
    baseline: foundation.ApprovedBaseline,
    run_dir: str | Path,
    *,
    design_workflow_dir: str | Path,
    human_actor_authenticator: Callable,
    project_root: str | Path,
    execution_oracle_refs: Iterable[dict] = (),
    model: str = "gpt-6-luna",
    artifact_id: str = "CR-001-testcases",
    revision: str = "1",
) -> CaseIntegrationResult:
    run_dir = Path(run_dir).resolve()
    execution_refs = tuple(execution_oracle_refs)
    manifest = invoke_native_katalon(
        design, receipt, baseline, run_dir,
        design_workflow_dir=design_workflow_dir,
        human_actor_authenticator=human_actor_authenticator,
        project_root=project_root,
        execution_oracle_refs=execution_refs, model=model,
    )
    return _finish_case_integration(
        manifest, design, baseline, run_dir,
        execution_contract_refs=execution_refs, artifact_id=artifact_id, revision=revision,
        execution_oracle_authenticator=human_actor_authenticator,
    )


def run_katalon_case_integration_test_only(
    design: foundation.DesignSnapshot,
    receipt_fixture_path: str | Path,
    baseline: foundation.ApprovedBaseline,
    run_dir: str | Path,
    *,
    design_workflow_dir: str | Path,
    project_root: str | Path | None = None,
    execution_oracle_refs: Iterable[dict] = (),
    model: str = "gpt-6-luna",
    artifact_id: str = "CR-001-testcases",
    revision: str = "1",
) -> CaseIntegrationResult:
    run_dir = Path(run_dir).resolve()
    execution_refs = tuple(execution_oracle_refs)
    manifest = invoke_native_katalon_test_only(
        design, receipt_fixture_path, baseline, run_dir,
        design_workflow_dir=design_workflow_dir,
        project_root=project_root,
        execution_oracle_refs=execution_refs, model=model,
    )
    return _finish_case_integration(
        manifest, design, baseline, run_dir,
        execution_contract_refs=execution_refs, artifact_id=artifact_id, revision=revision,
        allow_test_only_execution_oracles=True,
    )


def main(argv=None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Test Kit same-session testcase workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-cases")
    prepare.add_argument("--handoff", type=Path, required=True)
    prepare.add_argument("--design-run-dir", type=Path, required=True)
    prepare.add_argument("--run-dir", type=Path, required=True)
    prepare.add_argument("--project-root", type=Path, required=True)
    prepare.add_argument("--skill-dir", type=Path, required=True)

    finalize = subparsers.add_parser("finalize-cases")
    finalize.add_argument("--handoff", type=Path, required=True)
    finalize.add_argument("--run-dir", type=Path, required=True)
    finalize.add_argument("--raw-cases", type=Path)
    finalize.add_argument("--artifact-id")
    finalize.add_argument("--revision", default="1")

    args = parser.parse_args(argv)
    try:
        if args.command == "prepare-cases":
            result = prepare_same_session_cases(
                args.handoff,
                args.design_run_dir,
                args.run_dir,
                project_root=args.project_root,
                skill_dir=args.skill_dir,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            result = finalize_same_session_cases(
                args.handoff,
                args.run_dir,
                raw_cases=args.raw_cases,
                artifact_id=args.artifact_id,
                revision=args.revision,
            )
            print(json.dumps({
                "status": result.status,
                "artifact_id": result.workflow.artifact_id if result.workflow else None,
                "artifact_revision": result.workflow.artifact_revision if result.workflow else None,
                "artifact_sha256": result.workflow.artifact_sha256 if result.workflow else None,
            }, ensure_ascii=False, indent=2))
        return 0
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
