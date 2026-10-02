"""Build current typed testware for projection tests; archived v1 evidence stays immutable."""
import hashlib
import json
import shutil
from pathlib import Path

from tooling.lib import test_kit_v1 as core, test_kit_v1_cases as cases, test_kit_v1_excel as excel


def build(root, archive, design_dir, baseline_path):
    root, archive, design_dir = Path(root), Path(archive), Path(design_dir)
    root.mkdir(parents=True, exist_ok=True)
    for name in ("execution-oracles", "execution-oracle-approvals"):
        shutil.copytree(archive / name, root / name)
    baseline = core.load_approved_baseline(baseline_path)
    design = excel._load_design(design_dir)
    old = json.loads((archive / "approved-testware.json").read_text(encoding="utf-8"))["approved_testware"]
    refs = old["execution_oracle_refs"]
    for item in refs:
        filename = item["id"].removeprefix("TEST_ONLY:EXECUTION:").replace(":", "-") + ".json"
        item["path"] = str(root / "execution-oracles" / filename)
        item["approval_evidence"]["path"] = str(root / "execution-oracle-approvals" / filename)
    authored = json.loads((archive / "canonical-testcases-approved-projection.json").read_text(encoding="utf-8"))
    rows = []
    for row in authored:
        # This is fixture authoring for a new contract, not a production compatibility parser.
        dependencies = tuple(cases.ExecutionDependency(dep["need"], cases.dependency_kind(dep["need"])[0], dep["status"], dep["resolution_ref"])
                             for dep in row["execution_dependencies"])
        rows.append(cases.CanonicalTestcase(row["test_case_id"], row["name"], row["objective"], row["preconditions"], row["test_data"],
                     tuple(cases.CaseStep(**step) for step in row["steps"]), row["priority"], tuple(row["requirement_refs"]), tuple(row["test_design_refs"]), dependencies))
    snapshot = cases.CaseSnapshot.create(rows, artifact_id="TEST_ONLY:CR-001-testcases-resolved", revision="2")
    checked = cases.validate_testcases(snapshot, design, baseline, execution_contract_refs=refs, allow_test_only_execution_oracles=True)
    if checked.status != "PASS":
        raise ValueError(checked.findings)
    receipt_path = design_dir / "design-gate/revisions/1/receipt.json"
    fixture_path = design_dir / "design-test-only-receipt.json"
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    evidence = {"mode": "TEST_ONLY", "path": str(receipt_path), "sha256": digest(receipt_path),
                "fixture": {"path": str(fixture_path), "sha256": digest(fixture_path)}}
    state = cases.submit_cases_for_review(cases.start_case_workflow(snapshot), snapshot, checked, execution_contract_refs=refs,
             design_gate_receipt_mode="TEST_ONLY", design_gate_receipt_evidence=evidence,
             input_refs=cases.case_gate_input_refs(baseline, design))
    normalized = cases.CaseNormalizationResult("NORMALIZED", "synthetic-current-contract", snapshot, (), ())
    cases.persist_case_review(root, normalized, checked, state)
    snapshot = snapshot.project("IN_REVIEW")
    receipt = {"gate": "CASE_REVIEW", "decision": "APPROVE", "artifact_id": snapshot.artifact_id, "artifact_revision": snapshot.revision,
               "artifact_sha256": snapshot.sha256, "input_refs": cases.case_gate_input_refs(baseline, design),
               "actor_id": "TEST_ONLY:synthetic-current", "actor_role": "HUMAN", "decided_at": "2026-10-02T00:00:00Z", "feedback": "Current contract projection fixture"}
    fixture = root / "case-gate-fixture.json"
    fixture.write_text(json.dumps({"fixture_type": "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT", "not_for_production": True, "receipt": receipt}), encoding="utf-8")
    decision = cases.apply_test_only_case_gate_decision(fixture, snapshot, design, baseline, state, workflow_dir=root,
               validation=checked, execution_contract_refs=refs)
    if decision.status != "STOP_V1":
        raise ValueError(decision.finding)
    return root
