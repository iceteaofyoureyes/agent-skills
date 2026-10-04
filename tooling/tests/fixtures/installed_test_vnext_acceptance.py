"""Isolated installed-runtime acceptance driver. Human receipts are TEST_ONLY fixtures."""
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys


runtime = Path(sys.argv[1]).resolve()
project = Path(sys.argv[2]).resolve()
handoff_path = Path(sys.argv[3]).resolve()
host_dir = Path(sys.argv[4]).resolve()
ba_host_path = Path(sys.argv[5]).resolve()
ux_request_path = Path(sys.argv[6]).resolve()
ux_host_path = Path(sys.argv[7]).resolve()
scripts = runtime / "ba-workflow" / "scripts"

assert "PYTHONPATH" not in __import__("os").environ
sys.path[:0] = [str(runtime), str(scripts)]
import ba_vnext
from tooling.lib import test_kit_v1 as v1
from tooling.lib import test_kit_v1_cases as cases
from tooling.lib import test_kit_vnext as vnext
from tooling.lib import dev_vnext
from shared.sdlc import schema as shared_schema
from shared.sdlc.authority import approved_baseline as shared_baseline

modules = {
    "ba_vnext": ba_vnext,
    "test_kit_vnext": vnext,
    "test_kit_v1": v1,
    "test_kit_v1_cases": cases,
    "dev_vnext": dev_vnext,
    "shared_schema": shared_schema,
    "shared_baseline": shared_baseline,
}
for name, module in modules.items():
    assert Path(module.__file__).resolve().is_relative_to(runtime), (name, module.__file__)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


ba_fixture = read_json(ba_host_path)
assert ba_fixture["not_for_production"] is True
ba_receipt = ba_fixture["receipt"]


def ba_human(actor, exact_receipt):
    return actor == ba_receipt["actor_id"] and exact_receipt == ba_receipt


authority = vnext.load_vnext_authority(
    handoff_path, project_root=project, human_actor_authenticator=ba_human,
)
assert authority.vnext_authority is True
assert authority.baseline.coverage_ids == {"BR-001", "FR-001"}
assert authority.baseline.requirement_ids == {"FR-001"}
assert all(item.startswith(("BR-", "FR-")) for item in authority.baseline.coverage_ids)

# UX lexical regressions run against the installed runtime with explicit false authority.
for title, expected in (
    ("API response field is mapped", "API response field is returned"),
    ("Input payload is retained", "The input payload is returned"),
    ("Page number remains stable", "The requested page number is returned"),
):
    snapshot = v1.DesignSnapshot.create((
        v1.CanonicalTestDesign("TD-UX-FALSE", ("P1",), title, expected, ("BR-001", "FR-001"), ()),
    ), artifact_id="FEATURE-1-ux-false", revision="1")
    result = vnext.validate_vnext_design(snapshot, authority)
    assert result.status == "PASS", result.findings

plain_design = v1.DesignSnapshot.create((
    v1.CanonicalTestDesign("TD-UX-FALSE", ("P1",), "Submit reservation", "An eligible member receives the business outcome.", ("BR-001", "FR-001"), ()),
), artifact_id="FEATURE-1-ux-false-cases", revision="1")
for phrase in ("API response field", "input payload", "page number"):
    case = cases.CanonicalTestcase(
        "TC-UX-FALSE", f"Check {phrase}", f"Verify {phrase} handling",
        "An eligible member exists.", None,
        (cases.CaseStep("Submit a request.", None, "The member receives the business outcome."),),
        "P1", ("BR-001", "FR-001"), ("TD-UX-FALSE",), (),
    )
    case_result = vnext.validate_vnext_cases(
        cases.CaseSnapshot.create((case,), artifact_id="FEATURE-1-ux-false-cases", revision="1"),
        plain_design, authority,
    )
    assert case_result.status == "PASS", (phrase, case_result.findings)

required_design = v1.DesignSnapshot.create((
    v1.CanonicalTestDesign("TD-UX-REQUIRED", ("P1",), "Submit a reservation", "The member receives the business outcome.", ("BR-001", "FR-001"), ()),
), artifact_id="FEATURE-1-ux-required", revision="1")
required_without_ux = vnext.validate_vnext_design(
    required_design,
    vnext.replace(authority, ux_required=True),
)
assert required_without_ux.status == "FAIL"
assert "UX_APPROVAL_REQUIRED" in {finding.code for finding in required_without_ux.findings}
required_case = cases.CanonicalTestcase(
    "TC-UX-REQUIRED", "Submit a reservation", "Verify the reservation outcome",
    "An eligible member exists.", None,
    (cases.CaseStep("Submit request", None, "The member receives the business outcome."),),
    "P1", ("BR-001", "FR-001"), ("TD-UX-REQUIRED",), (),
)
required_case_result = vnext.validate_vnext_cases(
    cases.CaseSnapshot.create((required_case,), artifact_id="FEATURE-1-ux-required-cases", revision="1"),
    required_design,
    vnext.replace(authority, ux_required=True),
)
assert "UX_APPROVAL_REQUIRED" in {finding.code for finding in required_case_result.findings}

ux_request = read_json(ux_request_path)
ux_fixture = read_json(ux_host_path)
assert ux_fixture["not_for_production"] is True
ux_receipt = ux_fixture["receipt"]


def ux_human(actor, receipt):
    return actor == "Human" and receipt == ux_receipt


approved_ux = vnext.load_approved_ux_context(
    ux_request, feature_id="FEATURE-1", human_actor_authenticator=ux_human,
)
ux_authority = vnext.replace(authority, ux_context=approved_ux, ux_required=True)
ux_design = v1.DesignSnapshot.create((
    v1.CanonicalTestDesign("TD-UX-TRUE", ("P1",), "API response field is returned", "The input payload includes page number 2.", ("BR-001", "FR-001"), ()),
), artifact_id="FEATURE-1-ux-true", revision="1")
ux_result = vnext.validate_vnext_design(
    ux_design,
    ux_authority,
)
assert ux_result.status == "PASS", ux_result.findings
assert approved_ux["prototype_authority"] == "REVIEW_EVIDENCE"
ux_case = cases.CanonicalTestcase(
    "TC-UX-TRUE", "Verify input payload page number", "Check the API response field",
    "An eligible member exists.", None,
    (cases.CaseStep("Submit request", None, "The member receives the business outcome."),),
    "P1", ("BR-001", "FR-001"), ("TD-UX-TRUE",), (),
)
ux_case_result = vnext.validate_vnext_cases(
    cases.CaseSnapshot.create((ux_case,), artifact_id="FEATURE-1-ux-true-cases", revision="1"),
    ux_design,
    ux_authority,
)
assert ux_case_result.status == "PASS", ux_case_result.findings

prototype_only = {"root": ux_request["root"], "prototype": ux_request.get("prototype")}
try:
    vnext.load_approved_ux_context(prototype_only, feature_id="FEATURE-1", human_actor_authenticator=ux_human)
except vnext.TestAuthorityError:
    pass
else:
    raise AssertionError("prototype-only UX context was accepted")
try:
    vnext.load_approved_ux_context(ux_request, feature_id="FEATURE-1", human_actor_authenticator=lambda *_: False)
except vnext.TestAuthorityError:
    pass
else:
    raise AssertionError("unauthenticated UX approval was accepted")

ux_run = project / ".test-kit/runs/FEATURE-1/ux-revalidation"
vnext.prepare_vnext_design(
    handoff_path, ux_run, project_root=project,
    skill_dir=runtime.parent / "bmad-testarch-test-design",
    human_actor_authenticator=ba_human, ux_context=ux_request, ux_required=True,
    ux_human_actor_authenticator=ux_human,
)
vnext.revalidate_vnext_authority(
    ux_run, human_actor_authenticator=ba_human, ux_human_actor_authenticator=ux_human,
)
ux_contract = Path(ux_request["root"]) / ux_request["contract"]["path"]
ux_contract.write_bytes(ux_contract.read_bytes() + b"\nstale installed UX bytes\n")
try:
    vnext.revalidate_vnext_authority(
        ux_run, human_actor_authenticator=ba_human, ux_human_actor_authenticator=ux_human,
    )
except vnext.TestAuthorityError:
    pass
else:
    raise AssertionError("stale UX proof was accepted")


design_run = project / ".test-kit/runs/FEATURE-1/installed-design"
design_prepared = vnext.prepare_vnext_design(
    handoff_path, design_run, project_root=project,
    skill_dir=runtime.parent / "bmad-testarch-test-design",
    human_actor_authenticator=ba_human,
)
raw_design = Path(design_prepared["raw_output_path"])
raw_design.write_text("\n".join((
    "# Test Design: Collection requests",
    "## Test Coverage Plan",
    "### P0 - Critical", "None.", "### P1 - High",
    "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |",
    "|---|---|---|---|---|---|",
    "| TD-001 | Submit an eligible reservation request | API | - | BR-001; FR-001 | An eligible member receives the business outcome. |",
    "### P2 - Medium", "None.", "### P3 - Low", "None.",
)), encoding="utf-8")
design_finalized = vnext.finalize_vnext_design(
    handoff_path, design_run, human_actor_authenticator=ba_human,
)
assert design_finalized["status"] == "DESIGN_REVIEW", design_finalized
design_workflow = read_json(design_run / "workflow-state.json")
assert design_workflow["state"] == "DESIGN_REVIEW"
assert design_workflow.get("validation_status") == "PASS", design_workflow
design_snapshot = v1.load_persisted_design_snapshot(design_run, require_state="DESIGN_REVIEW")
design_receipt = {
    "gate": "DESIGN_REVIEW", "decision": "APPROVE",
    "artifact_id": design_snapshot.artifact_id, "artifact_revision": design_snapshot.revision,
    "artifact_sha256": design_snapshot.sha256,
    "input_refs": vnext.design_gate_input_refs(design_run, authority.baseline),
    "actor_id": "TEST_ONLY:installed-acceptance", "actor_role": "HUMAN",
    "decided_at": "2026-10-04T10:10:00Z", "feedback": "",
}
design_host_path = host_dir / "design-human.json"
write_json(design_host_path, {
    "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT",
    "not_for_production": True, "receipt": design_receipt,
})
design_rejected = vnext.apply_vnext_design_decision(
    design_run, design_receipt, human_actor_authenticator=None,
    ba_human_actor_authenticator=ba_human,
)
assert not design_rejected.accepted, design_rejected
design_approved = vnext.apply_vnext_design_decision(
    design_run, design_receipt, human_actor_authenticator=None,
    ba_human_actor_authenticator=ba_human, test_only_fixture_path=design_host_path,
)
assert design_approved.accepted and design_approved.state.state == "APPROVED_DESIGN", design_approved
assert read_json(design_run / "workflow-state.json")["design_gate_receipt_mode"] == "TEST_ONLY"

case_run = project / ".test-kit/runs/FEATURE-1/installed-cases"
case_prepared = vnext.prepare_test_only_vnext_cases(
    handoff_path, design_run, case_run, project_root=project,
    skill_dir=runtime.parent / "create-test-cases",
    ba_human_actor_authenticator=ba_human,
    test_only_design_fixture_path=design_host_path,
)
raw_cases = Path(case_prepared["raw_output_path"])
raw_cases.write_text("\n".join((
    "# Manual Test Cases", "", "## TC-001 Submit an eligible reservation request", "",
    "- Mô tả: Verify an eligible member can submit a reservation request.",
    "- Tiền điều kiện: An eligible member exists.",
    "- Bước và kết quả mong đợi:",
    "  1. Submit a reservation request. → The member receives the business outcome.",
    "- Test Data: Eligible member", "- Priority: P1.", "- Trace: BR-001; FR-001; TD-001", "",
)), encoding="utf-8")
case_finalized = vnext.finalize_test_only_vnext_cases(
    handoff_path, case_run, test_only_design_fixture_path=design_host_path,
    ba_human_actor_authenticator=ba_human,
)
assert case_finalized.status == "CASE_REVIEW", case_finalized
case_workflow = read_json(case_run / "workflow-state.json")
assert case_workflow["state"] == "CASE_REVIEW"
assert case_workflow.get("validation_status") == "PASS", case_workflow
case_snapshot, case_state = cases.load_case_review_snapshot(
    case_run / "canonical/canonical-testcases.json",
    case_run / "workflow-state.json",
    case_run / "canonical/semantic-payload.json",
)
resumed_workflow, resumed_snapshot, resumed_state = vnext.resume_vnext_cases(
    case_run, ba_human_actor_authenticator=ba_human,
)
assert resumed_workflow["state"] == "CASE_REVIEW"
assert resumed_snapshot.sha256 == case_snapshot.sha256
assert resumed_state.input_refs == case_state.input_refs
approved_design = v1.load_persisted_design_snapshot(design_run, require_state="APPROVED_DESIGN")
case_receipt = {
    "gate": "CASE_REVIEW", "decision": "APPROVE",
    "artifact_id": case_snapshot.artifact_id, "artifact_revision": case_snapshot.revision,
    "artifact_sha256": case_snapshot.sha256,
    "input_refs": cases.case_gate_input_refs(authority.baseline, approved_design, run_dir=case_run),
    "actor_id": "TEST_ONLY:installed-acceptance", "actor_role": "HUMAN",
    "decided_at": "2026-10-04T10:15:00Z", "feedback": "",
}
case_host_path = host_dir / "case-human.json"
write_json(case_host_path, {
    "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT",
    "not_for_production": True, "receipt": case_receipt,
})
case_rejected = vnext.apply_vnext_case_decision(
    case_run, case_receipt, human_actor_authenticator=None,
    ba_human_actor_authenticator=ba_human,
)
assert case_rejected.status == "REJECTED", case_rejected
case_approved = vnext.apply_vnext_case_decision(
    case_run, case_receipt, human_actor_authenticator=None,
    ba_human_actor_authenticator=ba_human, test_only_fixture_path=case_host_path,
)
assert case_approved.status == "APPROVED_TESTWARE", case_approved

manifest_path = case_run / "approved-testware-vnext.json"
manifest_envelope = read_json(manifest_path)
assert manifest_envelope["not_for_production"] is True
manifest = manifest_envelope["approved_testware"]
assert manifest["artifact_class"] == "HANDOFF_MANIFEST"
assert manifest["state"] == "APPROVED_TESTWARE"
assert manifest["state"] not in {"EXECUTION_READY", "VERIFIED"}
assert "delivery_manifest" not in manifest
assert set(manifest["trace_summary"]["requirement_ids"]) == {"BR-001", "FR-001"}
assert all(ref.startswith(("BR-", "FR-")) for ref in manifest["trace_summary"]["requirement_ids"])
assert all(ref.startswith(("BR-", "FR-")) for row in case_snapshot.records for ref in row.requirement_refs)
assert all(ref.startswith(("BR-", "FR-")) for row in approved_design.records for ref in row.requirement_refs)
assert not any(ref.startswith("BAREF:") for row in case_snapshot.records for ref in row.requirement_refs)
assert not any(ref.startswith("BAREF:") for row in approved_design.records for ref in row.requirement_refs)
expected_refs = {(ref_id, revision, sha256.lower()) for ref_id, revision, sha256 in case_state.input_refs}
actual_refs = {(ref["id"], ref["revision"], ref["sha256"].lower()) for ref in manifest["input_refs"]}
assert actual_refs == expected_refs
for name in ("testcase_collection", "approved_design", "design_gate_receipt", "case_gate_receipt", "ba_engineering_handoff"):
    ref = manifest[name]
    path = Path(ref["path"])
    if not path.is_absolute():
        path = case_run / path
    assert path.is_file() and digest(path) == ref["sha256"], (name, ref)

# Re-read the artifact and revalidate the exact BA, UX/Dev, gate, and byte refs.
authority_after = vnext.revalidate_vnext_authority(case_run, human_actor_authenticator=ba_human)
assert authority_after.vnext_authority is True
assert read_json(manifest_path)["approved_testware"]["state"] == "APPROVED_TESTWARE"
legacy = vnext.read_legacy_compat(run_dir=runtime / "examples/legacy-v1")
assert legacy["mode"] == "LEGACY_COMPAT" and legacy["vnext_authority"] is False

optional_smokes = {}
if importlib.util.find_spec("openpyxl") is not None:
    excel = vnext.export_vnext_approved_testware_excel(
        case_run, design_run, case_run / "derived/excel",
        human_actor_authenticator=None, test_only_receipt_fixture_path=case_host_path,
        ba_human_actor_authenticator=ba_human, project_root=project,
    )
    assert excel.semantic_diff.status == "PASS"
    optional_smokes["excel"] = "PASS"
else:
    optional_smokes["excel"] = "UNAVAILABLE"
if shutil.which("node") and (runtime / "tooling/xmind/node_modules/xmind/package.json").is_file():
    xmind = vnext.export_vnext_approved_design_xmind(
        design_run, design_run / "derived/xmind",
        human_actor_authenticator=None, test_only_receipt_fixture_path=design_host_path,
        ba_human_actor_authenticator=ba_human,
    )
    assert xmind.semantic_diff.status == "PASS"
    optional_smokes["xmind"] = "PASS"
else:
    optional_smokes["xmind"] = "UNAVAILABLE"

print(json.dumps({
    "state": "APPROVED_TESTWARE",
    "design": "APPROVED_DESIGN",
    "design_validation": design_workflow["validation_status"],
    "case_validation": case_workflow["validation_status"],
    "trace_ids": manifest["trace_summary"]["requirement_ids"],
    "legacy": legacy["mode"],
    "vnext_authority": legacy["vnext_authority"],
    "optional_smokes": optional_smokes,
    "module_paths": {name: str(Path(module.__file__).resolve()) for name, module in modules.items()},
}, sort_keys=True))
