"""Adversarial review of persisted bindings, independent of generation tests."""

import json

import pytest

from tooling.lib import test_kit_policy as policy
from tooling.lib import test_kit_v1 as core
from tooling.tests.test_test_kit_customization import auth, design_review, project, receipt


@pytest.mark.parametrize("target", ["context", "snapshot", "rule", "team"])
def test_missing_or_mutated_policy_evidence_never_approves(tmp_path, target):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    decision = receipt(design, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    context = json.loads((run / "inputs/project-policy-context.json").read_text(encoding="utf-8"))
    evidence = context["policy"]
    from pathlib import Path

    targets = {
        "context": run / "inputs/project-policy-context.json",
        "snapshot": Path(evidence["snapshot_path"]),
        "rule": Path(evidence["rules"][0]["evidence_path"]),
        "team": Path(evidence["tea_customization"]["evidence_path"]),
    }
    if target == "context":
        targets[target].unlink()
    else:
        targets[target].write_bytes(b"tampered evidence")
    result = core.apply_design_decision(run, design, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code == "PROJECT_POLICY_STALE"
    assert not (run / "design-gate/revisions/1/receipt.json").exists()


def test_profile_appearing_after_no_policy_review_requires_new_run(tmp_path):
    pr = tmp_path / "project"
    pr.mkdir()
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    decision = receipt(design, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    policy.bootstrap_project_policy(pr)
    result = core.apply_design_decision(run, design, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code == "PROJECT_POLICY_STALE"


def test_updating_context_alone_cannot_rebind_old_canonical_design(tmp_path):
    pr = project(tmp_path / "project")
    run = tmp_path / "design"
    baseline, design = design_review(run, pr)
    decision = receipt(design, "DESIGN_REVIEW", core.design_gate_input_refs(baseline, run))
    path = run / "inputs/project-policy-context.json"
    context = json.loads(path.read_text(encoding="utf-8"))
    context["status"] = "NO_PROJECT_POLICY"
    context["policy"] = None
    path.write_text(json.dumps(context), encoding="utf-8")
    result = core.apply_design_decision(run, design, baseline, decision, human_actor_authenticator=auth)
    assert not result.accepted
    assert result.finding.code == "PROJECT_POLICY_STALE"
