import hashlib
import base64
import json
import os
import re
import shutil
import sys
from pathlib import Path

runtime = Path(sys.argv[1]).resolve()
source_repo = Path(sys.argv[2]).resolve()
project = Path.cwd().resolve()
sys.path.insert(0, str(runtime))
from tooling.lib import test_kit_v1 as core
from tooling.lib import test_kit_v1_cases as cases
from tooling.lib.codex_cli import resolve_codex_command

assert Path(core.__file__).resolve().is_relative_to(runtime)
assert Path(cases.__file__).resolve().is_relative_to(runtime)
assert not any(Path(entry or project).resolve().is_relative_to(source_repo) for entry in sys.path)

input_dir = project / "smoke-input"
input_dir.mkdir()


def save(name, content):
    path = input_dir / name
    path.write_text(content, encoding="utf-8")
    return path


rules = save(
    "03-approved-business-rules.md",
    "# Rules\n| ID | Rule | Status |\n|---|---|---|\n"
    "| BR-001 | A valid new request starts in Scheduled status. | CONFIRMED |\n"
    "| BR-006 | For overlap checks, đối chiếu xung đột with other Scheduled appointments. | CONFIRMED |\n"
    "| BR-013 | Resolve đặt đồng thời requests for one Veterinarian without overlapping appointments. | CONFIRMED |\n",
)
srs = save(
    "04-srs-excerpt.md",
    "# Requirements\n| ID | Requirement | Status |\n|---|---|---|\n"
    "| FR-001 | Clinic Staff có thể tạo Appointment với dữ liệu hợp lệ. | CONFIRMED |\n"
    "| FR-002 | Appointment không được chồng lấn Appointment Scheduled khác của cùng Veterinarian. | CONFIRMED |\n"
    "| FR-003 | Clinic Staff chỉ được chỉnh sửa hoặc đổi lịch Appointment đang Scheduled. | CONFIRMED |\n"
    "| FR-004 | Clinic Staff chỉ được hủy Appointment đang Scheduled. | CONFIRMED |\n"
    "| FR-005 | Clinic Staff chỉ được hoàn tất Appointment đang Scheduled. | CONFIRMED |\n"
    "| FR-006 | Clinic Staff có thể xem Appointment. | CONFIRMED |\n",
)
decisions = save("05-ba-decisions.md", "Approved smoke fixture; no open decisions.\n")
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
handoff = save(
    "engineering-handoff.yml",
    f"""schema_version: 1
feature:
  id: SMOKE-001
  title: Self-contained packaging smoke
ba_baseline:
  status: APPROVED_FOR_ENGINEERING
  revision: smoke-rev-1
authoritative_sources:
  business_rules:
    path: 03-approved-business-rules.md
    sha256: {digest(rules)}
  srs:
    path: 04-srs-excerpt.md
    sha256: {digest(srs)}
  decisions:
    path: 05-ba-decisions.md
    sha256: {digest(decisions)}
open_items:
  blocking: []
  non_blocking: []
policy:
  downstream_may_change_business_semantics: false
  downstream_may_make_technical_design_decisions: true
next_stage:
  capability: engineering-impact-analysis
""",
)
assert (project / "_bmad/tea/config.yaml").is_file()
tea_config_sha = digest(project / "_bmad/tea/config.yaml")

smoke_scenarios = [
    ("TD-001", "Create appointment", "FR-001; BR-001", "A valid request is stored in Scheduled status."),
    ("TD-002", "Prevent overlap", "FR-002; BR-006; BR-013", "Overlapping Scheduled appointments are prevented."),
    ("TD-003", "Edit appointment", "FR-003", "A Scheduled appointment can be edited or rescheduled."),
    ("TD-004", "Cancel appointment", "FR-004", "A Scheduled appointment can be cancelled."),
    ("TD-005", "Complete appointment", "FR-005", "Completing a Scheduled appointment creates one Visit."),
    ("TD-006", "View appointment", "FR-006", "Clinic Staff can view appointments."),
]
tea_rows = [
    "---",
    "workflowStatus: 'completed'",
    "---",
    "# Test Design: Smoke",
    "## Test Coverage Plan",
    "### P0",
    "### P1",
    "| " + " | ".join(core.BENCHMARK_HEADERS) + " |",
    "|---|---|---|---|---|---|---|",
]
tea_rows.extend(
    f"| {design_id} - {title} | {refs} | Integration | Normal | 1 | QA | {expected} |"
    for design_id, title, refs, expected in smoke_scenarios
)
tea_rows.extend(["### P2", "### P3", ""])
tea_raw = "\n".join(tea_rows)
native_labels = cases.NATIVE_LABELS
case_rows = ["# Manual Test Cases", ""]
for index, (design_id, title, refs, expected) in enumerate(smoke_scenarios, 1):
    case_rows.extend([
        f"## TC-{index:03} {title}",
        "",
        f"- {native_labels[0]}: Check {title.casefold()}.",
        f"- {native_labels[1]}: A valid appointment setup is available.",
        f"- {native_labels[2]}:",
        f"  1. Submit the mapped input. \u2192 {expected}",
        "- Test Data: Approved smoke input",
        "- Priority: P1.",
        f"- {native_labels[5]}: {refs}; {design_id}",
        "",
    ])
case_raw = "\n".join(case_rows)
use_real_codex_stub = os.environ.get("TEST_KIT_USE_REAL_CODEX_STUB") == "1"
if use_real_codex_stub:
    os.environ["TEST_KIT_SMOKE_TEA"] = base64.b64encode(tea_raw.encode("utf-8")).decode("ascii")
    os.environ["TEST_KIT_SMOKE_CASES"] = base64.b64encode(case_raw.encode("utf-8")).decode("ascii")
    Path(os.environ["TEST_KIT_CODEX_COMMAND"]).write_text(
        "const fs=require('fs');let p='';process.stdin.setEncoding('utf8');"
        "process.stdin.on('data',x=>p+=x).on('end',()=>{"
        "const d=(k)=>Buffer.from(process.env[k],'base64');"
        "if(p.includes('project-local native Katalon create-test-cases skill')){"
        "const m=p.match(/^Output: (.+)$/m);if(!m)process.exit(3);"
        "fs.mkdirSync(require('path').dirname(m[1]),{recursive:true});"
        "fs.writeFileSync(m[1],d('TEST_KIT_SMOKE_CASES'));"
        "}else{const i=process.argv.indexOf('-o');if(i<0)process.exit(4);"
        "fs.mkdirSync(require('path').dirname(process.argv[i+1]),{recursive:true});"
        "fs.writeFileSync(process.argv[i+1],d('TEST_KIT_SMOKE_TEA'));}});\n",
        encoding="utf-8",
    )
codex = resolve_codex_command()
assert Path(codex.target).resolve() == Path(os.environ["TEST_KIT_CODEX_COMMAND"]).resolve()


class FakeInput:
    def __init__(self):
        self.data = bytearray()

    def write(self, data):
        self.data.extend(data)

    def close(self):
        pass


class FakeCodexProcess:
    def __init__(self, argv, **kwargs):
        self.argv = list(argv)
        self.stdin = FakeInput()
        self.done = False

    def poll(self):
        if not self.done:
            self.done = True
            prompt = self.stdin.data.decode("utf-8")
            if "project-local native Katalon create-test-cases skill" in prompt:
                match = re.search(r"(?m)^Output: (.+)$", prompt)
                if not match:
                    raise AssertionError("Katalon prompt has no output path")
                output = Path(match.group(1).strip())
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(case_raw, encoding="utf-8")
            else:
                output = Path(self.argv[self.argv.index("-o") + 1])
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(tea_raw, encoding="utf-8")
        return 0

    def wait(self):
        return 0


if not use_real_codex_stub:
    core.subprocess.Popen = FakeCodexProcess
baseline = core.load_approved_baseline(handoff)
bundle = core.adapt_ba_to_tea(handoff)
tea_skill = project / ".agents/skills/bmad-testarch-test-design"
run_dir = project / "test-artifacts/smoke"
tea_invocation = core.invoke_native_tea(
    bundle, run_dir, petclinic_root=project, skill_dir=tea_skill
)
assert tea_invocation["status"] == "ARTIFACT_COMPLETE"
assert Path(tea_invocation["installed_skill_path"]).resolve() == tea_skill.resolve()
normalization = core.normalize_tea_output(
    tea_invocation["completed_artifact_path"], baseline
)
assert normalization.status == "NORMALIZED", normalization.findings
design = normalization.snapshot
validation = core.validate_design(design, baseline)
assert validation.status == "PASS", validation.findings
design_state = core.submit_design_for_review(
    core.start_design_workflow(design), design, validation
)
core.persist_design_review(
    run_dir,
    bundle,
    tea_invocation["completed_artifact_path"],
    design,
    validation,
    design_state,
)
design_receipt = {
    "gate": "DESIGN_REVIEW",
    "decision": "APPROVE",
    "artifact_id": design.artifact_id,
    "artifact_revision": design.revision,
    "artifact_sha256": design.sha256,
    "input_refs": core.baseline_receipt_refs(baseline),
    "actor_id": "human:smoke",
    "actor_role": "HUMAN",
    "decided_at": "2026-09-29T00:00:00Z",
    "feedback": "",
}
human = lambda actor_id, _receipt: core.AuthenticatedHumanActorContext(actor_id)
design_decision = core.apply_design_decision(
    run_dir,
    design,
    baseline,
    design_receipt,
    human_actor_authenticator=human,
    validation=validation,
)
assert design_decision.accepted
assert design_decision.state.state == "APPROVED_DESIGN"

case_run_dir = project / "test-artifacts/smoke-cases"
case_baseline = case_run_dir / "inputs/baseline"
case_baseline.mkdir(parents=True)
for source, name in (
    (baseline.source_paths["business_rules"], "03-approved-business-rules.md"),
    (baseline.source_paths["srs"], "04-srs-excerpt.md"),
):
    shutil.copyfile(source, case_baseline / name)

cases_invocation = cases.invoke_native_katalon(
    design,
    design_receipt,
    baseline,
    case_run_dir,
    design_workflow_dir=run_dir,
    human_actor_authenticator=human,
    project_root=project,
)
assert cases_invocation["status"] == "ARTIFACT_COMPLETE"
assert Path(cases_invocation["installed_skill_path"]).resolve() == (
    project / ".agents/skills/create-test-cases"
).resolve()
case_normalization = cases.normalize_katalon_output(
    cases_invocation["raw_output_path"],
    design,
    baseline,
    artifact_id="SMOKE-CASES",
)
assert case_normalization.status == "NORMALIZED", case_normalization.findings
case_snapshot = case_normalization.snapshot
case_validation = cases.validate_testcases(case_snapshot, design, baseline)
assert case_validation.status == "PASS", case_validation.findings
case_refs = cases.baseline_receipt_refs(baseline) + [
    {"id": design.artifact_id, "revision": design.revision, "sha256": design.sha256}
]
case_state = cases.submit_cases_for_review(
    cases.start_case_workflow(case_snapshot),
    case_snapshot,
    case_validation,
    design_gate_receipt_mode=cases_invocation["receipt_mode"],
    design_gate_receipt_evidence=cases_invocation["design_gate_receipt_evidence"],
    input_refs=case_refs,
)
raw_path = Path(cases_invocation["raw_output_path"])
raw_bytes = raw_path.read_bytes()
cases.persist_case_review(
    case_run_dir,
    case_normalization,
    case_validation,
    case_state,
    raw_evidence_bytes=raw_bytes,
    expected_raw_output_sha256=hashlib.sha256(raw_bytes).hexdigest(),
)
case_receipt = {
    "gate": "CASE_REVIEW",
    "decision": "APPROVE",
    "artifact_id": case_snapshot.artifact_id,
    "artifact_revision": case_snapshot.revision,
    "artifact_sha256": case_snapshot.sha256,
    "input_refs": case_refs,
    "actor_id": "human:smoke",
    "actor_role": "HUMAN",
    "decided_at": "2026-09-29T00:00:00Z",
    "feedback": "",
}
case_decision = cases.apply_case_gate_decision(
    case_receipt,
    case_snapshot,
    design,
    baseline,
    case_state,
    workflow_dir=case_run_dir,
    human_actor_authenticator=human,
    validation=case_validation,
)
assert case_decision.status == "STOP_V1"
assert case_decision.approved_testware is not None
assert json.loads(
    (case_run_dir / "workflow-state.json").read_text(encoding="utf-8")
)["state"] == "STOP_V1"
assert (case_run_dir / "approved-testware.json").is_file()

if os.environ.get("TEST_KIT_RUN_OPTIONAL") == "1":
    from tooling.lib import test_kit_v1_excel as excel
    from tooling.lib import test_kit_v1_xmind as xmind

    xmind_inputs = project / "xmind-inputs"
    xmind_inputs.mkdir()

    def xmind_save(name, content):
        path = xmind_inputs / name
        path.write_text(content, encoding="utf-8")
        return path

    xmind_rules = xmind_save(
        "03-approved-business-rules.md",
        "# Rules\n| ID | Rule | Status |\n|---|---|---|\n"
        "| BR-001 | A valid new request starts in Scheduled status. | CONFIRMED |\n"
        "| BR-005 | Thời lượng tối đa là UNKNOWN. | UNKNOWN |\n"
        "| BR-006 | For overlap checks, đối chiếu xung đột with other Scheduled appointments. | CONFIRMED |\n"
        "| BR-013 | Resolve đặt đồng thời requests for one Veterinarian without overlapping appointments. | CONFIRMED |\n"
        "| BR-014 | Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định. | UNKNOWN |\n"
        "| BR-015 | Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN. | UNKNOWN |\n",
    )
    xmind_srs = xmind_save(
        "04-srs-excerpt.md",
        "# Requirements\n| ID | Requirement | Status |\n|---|---|---|\n"
        "| FR-001 | Clinic Staff có thể tạo Appointment với dữ liệu hợp lệ. | CONFIRMED |\n"
        "| FR-002 | Appointment không được chồng lấn Appointment Scheduled khác của cùng Veterinarian. | CONFIRMED |\n"
        "| FR-003 | Clinic Staff chỉ được chỉnh sửa hoặc đổi lịch Appointment đang Scheduled. | CONFIRMED |\n"
        "| FR-004 | Clinic Staff chỉ được hủy Appointment đang Scheduled. | CONFIRMED |\n"
        "| FR-005 | Clinic Staff chỉ được hoàn tất Appointment đang Scheduled. | CONFIRMED |\n"
        "| FR-006 | Clinic Staff có thể xem Appointment. | CONFIRMED |\n",
    )
    xmind_decisions = xmind_save("05-ba-decisions.md", "Approved XMind smoke fixture.\n")
    xmind_hash = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    xmind_handoff = xmind_save(
        "engineering-handoff.yml",
        f"""schema_version: 1
feature:
  id: XMIND-001
  title: Optional projection smoke
ba_baseline:
  status: APPROVED_FOR_ENGINEERING
  revision: xmind-smoke-1
authoritative_sources:
  business_rules:
    path: 03-approved-business-rules.md
    sha256: {xmind_hash(xmind_rules)}
  srs:
    path: 04-srs-excerpt.md
    sha256: {xmind_hash(xmind_srs)}
  decisions:
    path: 05-ba-decisions.md
    sha256: {xmind_hash(xmind_decisions)}
open_items:
  blocking: []
  non_blocking: []
policy:
  downstream_may_change_business_semantics: false
  downstream_may_make_technical_design_decisions: true
next_stage:
  capability: engineering-impact-analysis
""",
        )
    xmind_baseline = core.load_approved_baseline(xmind_handoff)
    xmind_bundle = core.adapt_ba_to_tea(xmind_handoff)

    xmind_dir = project / "test-artifacts/smoke-xmind"
    xmind_records = [
        core.CanonicalTestDesign("TD-001", ("Test Design", "P1"), "Tạo lịch hẹn", "A valid request is created.", ("FR-001", "BR-001"), ()),
        core.CanonicalTestDesign("TD-002", ("Test Design", "P1"), "Kiểm tra xung đột lịch", "Overlapping Scheduled appointments are prevented.", ("FR-002", "BR-006", "BR-013"), ()),
        core.CanonicalTestDesign("TD-003", ("Test Design", "P1"), "Chỉnh sửa lịch hẹn", "A Scheduled appointment can be edited or rescheduled.", ("FR-003",), ()),
        core.CanonicalTestDesign("TD-004", ("Test Design", "P1"), "Hủy lịch hẹn", "A Scheduled appointment can be cancelled.", ("FR-004",), ()),
        core.CanonicalTestDesign("TD-005", ("Test Design", "P1"), "Hoàn tất lịch hẹn", "Completing a Scheduled appointment creates one Visit.", ("FR-005",), ()),
        core.CanonicalTestDesign("TD-006", ("Test Design", "P1"), "Xem lịch hẹn", "Clinic Staff can view appointments.", ("FR-006",), ()),
        core.CanonicalTestDesign(
            "TD-007", ("Test Design", "P2"), "Maximum duration", None,
            ("FR-005", "BR-005"), (core.OpenQuestion("BR-005", "Thời lượng tối đa là UNKNOWN."),),
        ),
        core.CanonicalTestDesign(
            "TD-008", ("Test Design", "P2"), "List controls", None,
            ("FR-006", "BR-014"), (core.OpenQuestion("BR-014", "Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định."),),
        ),
        core.CanonicalTestDesign(
            "TD-009", ("Test Design", "P2"), "List controls details", None,
            ("FR-006", "BR-015"), (core.OpenQuestion("BR-015", "Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN."),),
        ),
    ]
    xmind_design = core.DesignSnapshot.create(xmind_records, artifact_id="SMOKE-XMIND", revision="1")
    xmind_validation = core.validate_design(xmind_design, xmind_baseline)
    assert xmind_validation.status == "PASS", xmind_validation.findings
    xmind_state = core.submit_design_for_review(
        core.start_design_workflow(xmind_design), xmind_design, xmind_validation
    )
    core.persist_design_review(
        xmind_dir,
        xmind_bundle,
        tea_invocation["completed_artifact_path"],
        xmind_design,
        xmind_validation,
        xmind_state,
    )
    xmind_receipt = {
        "gate": "DESIGN_REVIEW",
        "decision": "APPROVE",
        "artifact_id": xmind_design.artifact_id,
        "artifact_revision": xmind_design.revision,
        "artifact_sha256": xmind_design.sha256,
        "input_refs": core.baseline_receipt_refs(xmind_baseline),
        "actor_id": "human:smoke",
        "actor_role": "HUMAN",
        "decided_at": "2026-09-29T00:00:00Z",
        "feedback": "",
    }
    xmind_decision = core.apply_design_decision(
        xmind_dir,
        xmind_design,
        xmind_baseline,
        xmind_receipt,
        human_actor_authenticator=human,
        validation=xmind_validation,
    )
    assert xmind_decision.accepted
    xmind_result = xmind.export_approved_design_xmind(
        xmind_dir,
        xmind_handoff,
        xmind_dir / "projections/xmind",
        human_actor_authenticator=human,
    )
    excel_result = excel.export_approved_testware_excel(
        case_run_dir,
        run_dir,
        handoff,
        case_run_dir / "projections/excel",
        human_actor_authenticator=human,
    )
    assert xmind_result.xmind_path.is_file()
    assert excel_result.xlsx_path.is_file()
    print("OPTIONAL_PROJECTIONS: PASS")
print("INSTALLED_SMOKE: PASS")

assert digest(project / "_bmad/tea/config.yaml") == tea_config_sha
