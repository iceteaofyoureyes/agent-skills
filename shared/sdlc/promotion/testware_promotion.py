"""Promote authenticated approved testware into durable feature documentation."""
from shared.sdlc.compatibility import retain_legacy_identity as _retain_legacy_identity
_retain_legacy_identity(__name__, 'tooling.lib.testware_promotion')

import hashlib
import json
from pathlib import Path

from tooling.lib import test_kit_v1 as design, test_kit_v1_cases as cases
from shared.sdlc.approvals.gate_persistence import write_if_same_or_absent
from shared.sdlc.provenance.runtime_paths import preflight_paths, revision_component


def render_testware(rows, stage):
    lines = ["# Test Design" if stage == "design" else "# Testcases", ""]
    for row in rows:
        key = "design_id" if stage == "design" else "test_case_id"
        lines += ["## " + row[key], "", json.dumps(row, ensure_ascii=False, indent=2), ""]
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _copy_exact(path, content):
    write_if_same_or_absent(path, content)


def promote(run_dir, feature_root, baseline, *, stage, human_actor_authenticator):
    run_dir, feature_root = Path(run_dir).resolve(), Path(feature_root).resolve()
    if stage not in {"design", "cases"} or feature_root.name != baseline.feature_id:
        raise ValueError("promotion stage/feature routing mismatch")
    workflow = json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))
    expected_state = "APPROVED_DESIGN" if stage == "design" else "STOP_V1"
    if workflow.get("state") != expected_state or workflow.get("review_status") != "APPROVED":
        raise ValueError("valid approved gate required before promotion")
    if stage == "design":
        snapshot = design.load_persisted_design_snapshot(run_dir, require_state=expected_state)
        receipt_path = run_dir / "design-gate/revisions" / snapshot.revision / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        checked = cases.validate_design_gate_receipt(receipt, snapshot, baseline, design_workflow_dir=run_dir,
                                                   human_actor_authenticator=human_actor_authenticator)
        if checked.status != "PASS":
            raise ValueError(f"promotion Design receipt rejected: {checked.finding}")
    else:
        receipt_path = run_dir / "case-gate/receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if workflow.get("case_gate_receipt_mode") != "HUMAN_AUTHENTICATED":
            raise ValueError("synthetic/legacy receipts cannot promote production testware")
        ref = workflow.get("case_gate_receipt_evidence", {})
        if ref.get("sha256") != hashlib.sha256(receipt_path.read_bytes()).hexdigest():
            raise ValueError("Case approval receipt drift")
        actor = human_actor_authenticator(receipt.get("actor_id"), receipt) if callable(human_actor_authenticator) else None
        if type(actor) is not design.AuthenticatedHumanActorContext or actor.actor_id != receipt.get("actor_id") or actor.actor_role != "HUMAN":
            raise ValueError("host-authenticated Human approval required")
        if receipt.get("decision") != "APPROVE" or receipt.get("artifact_sha256") != workflow.get("artifact_sha256"):
            raise ValueError("Case approval snapshot mismatch")
        if receipt.get("artifact_revision") != workflow.get("artifact_revision") or receipt.get("artifact_id") != workflow.get("artifact_id"):
            raise ValueError("Case approval identity mismatch")
        if cases._receipt_refs(receipt) != tuple((ref["id"], ref["revision"], ref["sha256"]) for ref in workflow.get("input_refs", [])):
            raise ValueError("Case approval input refs mismatch")
        design.current_delivery_refs(run_dir)
        current = design.load_approved_baseline(baseline.handoff_path)
        if current.identity != baseline.identity:
            raise ValueError("BA baseline drift before promotion")
    semantic = (run_dir / "canonical/semantic-payload.json").read_bytes()
    digest = hashlib.sha256(semantic).hexdigest()
    if digest != workflow["artifact_sha256"] or digest != receipt["artifact_sha256"]:
        raise ValueError("approved semantic payload drift")
    rows = json.loads(semantic)
    name = "test-design" if stage == "design" else "testcases"
    markdown = render_testware(rows, stage)
    target = feature_root / "test" / stage
    for directory in (feature_root, feature_root / "test", target, feature_root / "test/approvals"):
        if directory.is_symlink():
            raise ValueError("unsafe promotion directory")
    receipt_bytes = receipt_path.read_bytes()
    revision_component(workflow['artifact_revision'])
    receipt_name = f"{stage}-{workflow['artifact_revision']}-receipt.json"
    record = {"schema_version": 1, "source_run_id": run_dir.name, "stage": stage,
              "artifact_id": workflow["artifact_id"], "revision": workflow["artifact_revision"],
              "semantic_sha256": digest, "markdown_sha256": hashlib.sha256(markdown).hexdigest(),
              "approval_receipt": receipt_name, "approval_receipt_sha256": hashlib.sha256(receipt_bytes).hexdigest(),
              "approval_mode": "HUMAN_AUTHENTICATED"}
    # Portable durable refs; execution resolves them from the promotion record directory.
    record["semantic_path"] = f"../{stage}/{name}.json"
    record["approval_path"] = receipt_name
    writes = [(target / (name + '.json'), semantic), (target / (name + '.md'), markdown),
              (feature_root / 'test/approvals' / receipt_name, receipt_bytes),
              (feature_root / 'test/approvals' / (stage + '-promotion.json'),
               (json.dumps(record, indent=2) + '\n').encode())]
    preflight_paths([path for path, _ in writes], stage='TESTWARE_PROMOTION', transition=stage)
    for path, content in writes:
        if path.exists() and path.read_bytes() != content:
            raise ValueError('promotion cannot overwrite a different approved snapshot')
    for path, content in writes:
        _copy_exact(path, content)
    return record
