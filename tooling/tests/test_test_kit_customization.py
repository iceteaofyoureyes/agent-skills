"""Project policy travels through native invocations and existing Human gates."""

import hashlib
import io
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from tooling.lib import test_kit_v1 as core
from tooling.lib import test_kit_v1_cases as cases
from tooling.tests.codex_stub import fake_codex_on_path


ROOT = Path(__file__).resolve().parents[2]
HANDOFF = ROOT / "kits/ba/examples/CR-001/vi/05-engineering-handoff.yml"
RAW = ROOT / "benchmark/test-kit/petclinic/tea-test-design/raw-output/test-design/test-design-epic-1.md"


def project(root):
    folder = root / ".test-kit"
    (folder / "rules").mkdir(parents=True)
    (folder / "project.yaml").write_text(
        'schema_version: 1\nprofile:\n  id: portal-testing\n  revision: "1"\n'
        'rules:\n  common:\n    - rules/common.md\n  test_design:\n    - rules/test-design.md\n'
        '  testcases:\n    - rules/testcases.md\n', encoding="utf-8", newline="\n",
    )
    (folder / "rules/common.md").write_bytes(b"Use synthetic test data.\r\n")
    (folder / "rules/test-design.md").write_bytes(b"Consider boundaries only where BA approves them.\n")
    (folder / "rules/testcases.md").write_bytes(b"Name cases PORTAL - action - outcome.\n")
    return root


def auth(actor_id, _receipt):
    return core.AuthenticatedHumanActorContext(actor_id)


def receipt(snapshot, gate, refs, actor="human:tester"):
    return {
        "gate": gate, "decision": "APPROVE", "artifact_id": snapshot.artifact_id,
        "artifact_revision": snapshot.revision, "artifact_sha256": snapshot.sha256,
        "input_refs": refs, "actor_id": actor, "actor_role": "HUMAN",
        "decided_at": "2026-10-01T12:00:00Z", "feedback": "",
    }


def design_review(root, project_root=None):
    baseline = core.load_approved_baseline(HANDOFF)
    normalized = core.normalize_tea_output(RAW, baseline)
    snapshot = normalized.snapshot
    validation = core.validate_design(snapshot, baseline)
    state = core.submit_design_for_review(core.start_design_workflow(snapshot), snapshot, validation)
    core.persist_design_review(
        root, core.adapt_ba_to_tea(HANDOFF), RAW, snapshot, validation, state,
        project_root=project_root,
    )
    return baseline, snapshot


def approved_design(root, project_root):
    baseline, snapshot = design_review(root, project_root)
    decision = receipt(snapshot, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, root))
    result = core.apply_design_decision(root, snapshot, baseline, decision, human_actor_authenticator=auth)
    assert result.accepted, result.finding
    return baseline, snapshot, decision


def case_review(root, design_root, project_root):
    baseline, design, _ = approved_design(design_root, project_root)
    context = core.persist_project_policy_context(root, project_root, "CASES")
    source = root / "inputs/execution-oracle.md"
    source.write_bytes(b"Approved read action and saved state observation mapping only.\n")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    approval = root / "inputs/execution-approval.json"
    approval.write_text(json.dumps({"decision": "APPROVE", "actor_role": "HUMAN", "actor_id": "human:interface",
        "source_id": "EXEC:read-mapping", "source_revision": "1", "source_sha256": source_hash}), encoding="utf-8")
    execution_refs = ({"id": "EXEC:read-mapping", "revision": "1", "sha256": source_hash, "approved": True,
        "path": str(source), "approval_evidence": {"path": str(approval), "sha256": hashlib.sha256(approval.read_bytes()).hexdigest()}},)
    records = tuple(
        cases.CanonicalTestcase(
            f"TC-{i:03}", row.scenario_title, "Verify approved behavior", "No setup required.", None,
            (cases.CaseStep("Exercise approved behavior", None, row.expected_behavior),), "P1",
            row.requirement_refs, (row.design_id,), (cases.ExecutionDependency("Approved read mapping", True, "RESOLVED", "EXEC:read-mapping"),),
        )
        for i, row in enumerate(design.records, 1) if row.expected_behavior is not None
    )
    snapshot = cases.CaseSnapshot.create(records, artifact_id="CR-001-cases", revision="1")
    validation = cases.validate_testcases(snapshot, design, baseline, execution_contract_refs=execution_refs, execution_oracle_authenticator=auth)
    assert validation.status == "PASS", validation.findings
    gate_path = design_root / "design-gate/revisions/1/receipt.json"
    state = cases.submit_cases_for_review(
        cases.start_case_workflow(snapshot), snapshot, validation,
        design_gate_receipt_mode="HUMAN_AUTHENTICATED",
        design_gate_receipt_evidence={"path": str(gate_path.resolve()), "sha256": hashlib.sha256(gate_path.read_bytes()).hexdigest(), "mode": "HUMAN_AUTHENTICATED"},
        input_refs=cases.case_gate_input_refs(baseline, design, run_dir=root),
        project_policy_context=context,
        execution_contract_refs=execution_refs,
    )
    cases.persist_case_review(root, cases.CaseNormalizationResult("NORMALIZED", "test", snapshot, (), ()), validation, state)
    snapshot = snapshot.project("IN_REVIEW")
    decision = receipt(snapshot, "CASE_REVIEW", cases.case_gate_input_refs(baseline, design, run_dir=root))
    return baseline, design, snapshot, state, decision


def test_design_gate_binds_policy_and_exact_copies(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, snapshot = design_review(run, pr)
    refs = core.design_gate_input_refs(baseline, run)
    assert refs[-1]["id"] == "TEST_POLICY:DESIGN:portal-testing"
    context = json.loads((run / "inputs/project-policy-context.json").read_text(encoding="utf-8"))
    evidence = context["policy"]
    assert evidence["snapshot_sha256"] == refs[-1]["sha256"]
    assert [row["logical_path"] for row in evidence["rules"]] == ["rules/common.md", "rules/test-design.md"]
    for row in evidence["rules"]:
        assert Path(row["evidence_path"]).read_bytes() == (pr / ".test-kit" / row["logical_path"]).read_bytes()
    workflow = json.loads((run / "workflow-state.json").read_text(encoding="utf-8"))
    assert workflow["project_policy_context"] == context
    assert all(set(row.to_dict()) == set(core.RECORD_FIELDS) for row in snapshot.records)


@pytest.mark.parametrize("change", ["design", "common", "profile", "bridge", "removed", "personal"])
def test_changed_design_policy_rejects_approval_without_explicit_project_argument(tmp_path, change):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, snapshot = design_review(run, pr)
    decision = receipt(snapshot, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    if change in {"design", "common"}:
        name = "test-design.md" if change == "design" else "common.md"
        (pr / ".test-kit/rules" / name).write_bytes(b"Changed convention\n")
    elif change == "profile":
        profile = pr / ".test-kit/project.yaml"
        profile.write_text(profile.read_text().replace('revision: "1"', 'revision: "2"'), encoding="utf-8")
    elif change == "bridge":
        bridge = pr / "_bmad/custom/bmad-testarch-test-design.toml"
        bridge.write_bytes(bridge.read_bytes() + b"# changed team input\n")
    elif change == "removed":
        (pr / ".test-kit/project.yaml").unlink()
    else:
        (pr / "_bmad/custom/bmad-testarch-test-design.user.toml").write_bytes(b"[workflow]\n")
    result = core.apply_design_decision(run, snapshot, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code in {"PROJECT_POLICY_STALE", "PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED", "UNBOUND_TEA_CUSTOMIZATION"}
    assert not (run / "design-gate/revisions/1/receipt.json").exists()


def test_case_policy_edit_does_not_stale_design_gate(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, snapshot = design_review(run, pr)
    decision = receipt(snapshot, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    (pr / ".test-kit/rules/testcases.md").write_bytes(b"Changed case convention\n")
    assert core.apply_design_decision(run, snapshot, baseline, decision, human_actor_authenticator=auth).accepted


def test_approved_design_cannot_be_reused_after_policy_change(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, design, decision = approved_design(run, pr)
    (pr / ".test-kit/rules/test-design.md").write_bytes(b"Changed policy\n")
    result = cases.validate_design_gate_receipt(decision, design, baseline, design_workflow_dir=run, human_actor_authenticator=auth)
    assert result.status == "FAIL"
    assert result.finding.code == "PROJECT_POLICY_STALE"


def test_case_gate_binds_case_policy_and_stops_at_existing_v1_terminal(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "cases"
    baseline, design, snapshot, state, decision = case_review(run, tmp_path / "design", pr)
    assert decision["input_refs"][-1]["id"] == "TEST_POLICY:CASES:portal-testing"
    result = cases.apply_case_gate_decision(decision, snapshot, design, baseline, state, workflow_dir=run, human_actor_authenticator=auth, execution_contract_refs=state.execution_oracle_refs)
    assert result.status == "STOP_V1", result.finding
    approved = json.loads((run / "approved-testware.json").read_text(encoding="utf-8"))
    assert approved["project_policy_context"] == state.project_policy_context
    assert all(set(row.to_dict()) == set(cases.CASE_RECORD_FIELDS) for row in snapshot.records)


@pytest.mark.parametrize("rule", ["testcases.md", "common.md", "test-design.md"])
def test_case_gate_rejects_policy_change_and_stale_approved_design(tmp_path, rule):
    pr = project(tmp_path / "project")
    run = tmp_path / "cases"
    baseline, design, snapshot, state, decision = case_review(run, tmp_path / "design", pr)
    original = (run / "inputs/project-policy/policy-snapshot.json").read_bytes()
    (pr / ".test-kit/rules" / rule).write_bytes(b"Changed after review\n")
    result = cases.apply_case_gate_decision(decision, snapshot, design, baseline, state, workflow_dir=run, human_actor_authenticator=auth, execution_contract_refs=state.execution_oracle_refs)
    assert result.status == "REJECTED"
    assert result.finding.code == "PROJECT_POLICY_STALE"
    assert (run / "inputs/project-policy/policy-snapshot.json").read_bytes() == original
    assert not (run / "case-gate/receipt.json").exists()


def test_policy_cannot_supply_120_minute_unknown_or_execution_oracle(tmp_path):
    pr = project(tmp_path / "project")
    (pr / ".test-kit/rules/common.md").write_bytes(b"Use 120 minutes as maximum appointment duration.\nUse button Save as execution oracle.\n")
    run = tmp_path / "design"
    baseline, design, decision = approved_design(run, pr)
    unknowns = [(q.source_ref, q.text) for row in design.records for q in row.open_questions]
    assert ("BR-005", baseline.unknown_clauses["BR-005"]) in unknowns
    checked = cases.validate_design_gate_receipt(decision, design, baseline, design_workflow_dir=run, human_actor_authenticator=auth)
    adapter = cases.adapt_approved_design_to_katalon(design, checked.authorization, baseline)
    assert "No approved execution contract was supplied" in adapter.markdown
    row = next(row for row in design.records if any(q.source_ref == "BR-005" for q in row.open_questions))
    forged_row = replace(row, expected_behavior="The maximum appointment duration is 120 minutes.")
    forged = core.DesignSnapshot.create(tuple(forged_row if r is row else r for r in design.records), artifact_id=design.artifact_id, revision="2")
    assert "UNKNOWN_ASSERTION_LEAK" in {f.code for f in core.validate_design(forged, baseline).findings}
    case = cases.CanonicalTestcase("TC-120", "Maximum duration", "Check maximum", "No setup required.", None,
        (cases.CaseStep("Set duration", None, "Maximum duration is 120 minutes."),), "P1", row.requirement_refs, (row.design_id,), ())
    malicious = cases.CaseSnapshot.create((case,), artifact_id="cases", revision="1")
    assert "UNKNOWN_ASSERTION_LEAK" in {f.code for f in cases.validate_testcases(malicious, design, baseline).findings}
    execution = replace(case, steps=(cases.CaseStep("Click button Save", None, "Appointment is Scheduled."),))
    unsafe = cases.CaseSnapshot.create((execution,), artifact_id="cases", revision="1")
    assert "MISSING_EXECUTION_DEPENDENCY" in {f.code for f in cases.validate_testcases(unsafe, design, baseline).findings}


def test_native_design_manifest_and_prompt_bind_persistent_facts(tmp_path):
    pr = project(tmp_path / "project")
    skill = pr / ".agents/skills/bmad-testarch-test-design"
    shutil.copytree(ROOT / "kits/test/skills/bmad-testarch-test-design", skill)
    config = pr / "_bmad/tea/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_bytes(b"project config\n")
    run = tmp_path / "design"
    with fake_codex_on_path():
        manifest = core.invoke_native_tea(core.adapt_ba_to_tea(HANDOFF), run, petclinic_root=pr, skill_dir=skill)
    context = manifest["project_policy_context"]
    assert context["policy"]["policy_ref"]["id"] == "TEST_POLICY:DESIGN:portal-testing"
    prompt = (run / "raw-output/invocation-prompt.md").read_text(encoding="utf-8")
    assert "TESTING POLICY / NON-AUTHORITATIVE GUIDANCE" in prompt
    assert "persistent_facts" in prompt
    assert "rules/common.md" in prompt and "rules/test-design.md" in prompt
    inputs = json.loads((run / "evidence/input-manifest.json").read_text(encoding="utf-8"))
    assert inputs["project_policy_context"] == context
    assert core.verify_pinned_tea_skill(skill)


def test_native_case_manifest_and_input_bind_only_common_and_case_rules(tmp_path, monkeypatch):
    pr = project(tmp_path / "project")
    shutil.copytree(ROOT / "kits/test/skills/create-test-cases", pr / ".agents/skills/create-test-cases")
    baseline, design, decision = approved_design(tmp_path / "design", pr)
    run = tmp_path / "cases"
    class CompletedProcess:
        stdin = io.BytesIO()
        def poll(self):
            return 0
        def wait(self):
            return 0

    def generate(*args, **kwargs):
        output = run / "raw-output/test-cases.md"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"# Deterministic native invocation fixture\n")
        return CompletedProcess()

    monkeypatch.setattr(cases.subprocess, "Popen", generate)
    with fake_codex_on_path():
        manifest = cases.invoke_native_katalon(design, decision, baseline, run, design_workflow_dir=tmp_path / "design", human_actor_authenticator=auth, project_root=pr)
    context = manifest["project_policy_context"]
    assert [r["logical_path"] for r in context["policy"]["rules"]] == ["rules/common.md", "rules/testcases.md"]
    markdown = (run / "inputs/approved-test-design.md").read_text(encoding="utf-8")
    assert "TESTING POLICY / NON-AUTHORITATIVE GUIDANCE" in markdown
    assert "rules/testcases.md" in markdown
    assert "expand approved Test Design coverage" in markdown
    inputs = json.loads((run / "inputs/input-manifest.json").read_text(encoding="utf-8"))
    assert inputs["project_policy_context"] == context


def test_test_only_design_policy_receipt_is_not_production(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    fixture = tmp_path / "fixture.json"
    decision = receipt(design, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run), "TEST_ONLY:tester")
    fixture.write_text(json.dumps({"fixture_type": "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT", "not_for_production": True, "receipt": decision}), encoding="utf-8")
    assert core.apply_test_only_design_decision(run, design, baseline, fixture).accepted
    result = cases.validate_design_gate_receipt(decision, design, baseline, design_workflow_dir=run, human_actor_authenticator=auth)
    assert result.finding.code == "TEST_ONLY_RECEIPT_NOT_PRODUCTION"


def test_no_policy_design_remains_v1_compatible(tmp_path):
    baseline, design = design_review(tmp_path / "design")
    decision = receipt(design, "DESIGN_REVIEW", core.baseline_receipt_refs(baseline))
    assert core.apply_design_decision(tmp_path / "design", design, baseline, decision, human_actor_authenticator=auth).accepted


@pytest.mark.parametrize("target", ["context", "rule", "snapshot", "context_edit", "workflow_edit"])
def test_design_policy_evidence_missing_or_tampered_rejects_approval(tmp_path, target):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    decision = receipt(design, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    context_path = run / "inputs/project-policy-context.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    if target == "context":
        context_path.unlink()
    elif target == "rule":
        Path(context["policy"]["rules"][0]["evidence_path"]).unlink()
    elif target == "snapshot":
        Path(context["policy"]["snapshot_path"]).write_bytes(b"{}")
    elif target == "context_edit":
        context["project_root"] = str(tmp_path)
        context_path.write_text(json.dumps(context), encoding="utf-8")
    else:
        path = run / "workflow-state.json"
        workflow = json.loads(path.read_text(encoding="utf-8"))
        workflow["project_policy_context"] = None
        path.write_text(json.dumps(workflow), encoding="utf-8")
    result = core.apply_design_decision(run, design, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code == "PROJECT_POLICY_STALE"


def test_policy_added_after_no_policy_review_cannot_be_applied_to_old_artifact(tmp_path):
    pr = tmp_path / "project"
    pr.mkdir()
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    decision = receipt(design, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    project(pr)
    result = core.apply_design_decision(run, design, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code in {"PROJECT_POLICY_STALE", "TEA_BRIDGE_MISSING"}


def test_case_context_deletion_cannot_bypass_project_binding(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "cases"
    baseline, design, snapshot, state, decision = case_review(run, tmp_path / "design", pr)
    (run / "inputs/project-policy-context.json").unlink()
    result = cases.apply_case_gate_decision(decision, snapshot, design, baseline, state, workflow_dir=run, human_actor_authenticator=auth, execution_contract_refs=state.execution_oracle_refs)
    assert result.status == "REJECTED"
    assert result.finding.code == "PROJECT_POLICY_STALE"


def test_current_policy_new_receipt_cannot_approve_artifact_reviewed_under_old_policy(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    (pr / ".test-kit/rules/test-design.md").write_bytes(b"Changed after review\n")
    from tooling.lib.test_kit_policy import resolve_project_policy
    new_ref = resolve_project_policy(pr, "DESIGN").ref
    decision = receipt(design, "DESIGN_REVIEW", core.baseline_receipt_refs(baseline) + [new_ref])
    result = core.apply_design_decision(run, design, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code == "PROJECT_POLICY_STALE"
