"""Thin project orchestration above Test Kit. Trusted host supplies lane identity."""
import copy
import hashlib
import json
import re
from pathlib import Path

DEPENDENCY_TYPES = {"SEMANTIC_ORACLE", "ENVIRONMENT_ACCESS", "TEST_DATA_FIXTURE", "IMPLEMENTATION_LOCATOR", "TOOLING", "OBSERVABILITY"}
CLASSIFICATIONS = {"DEFECT": "DEFECT_READY_FOR_DEV", "SPEC_GAP": "BA_DECISION_REQUIRED",
                   "BUSINESS_DECISION_REQUIRED": "BA_DECISION_REQUIRED", "TEST_ISSUE": "TEST_ISSUE",
                   "ENVIRONMENT_ISSUE": "TEST_ENV_CORRECTION"}
TRANSITIONS = {
    "EXECUTION_READINESS": {"READY": "EXECUTION_READY"},
    "EXECUTION_READY": {"EXECUTE": "EXECUTING"},
    "EXECUTING": {"PASS": "PASS", "FAIL": "FINDING"},
    "FINDING": {"CLASSIFY": "FINDING_CLASSIFIED"},
    "FINDING_CLASSIFIED": {"ROUTE": None},
    "DEFECT_READY_FOR_DEV": {"FIX": "FIX_IMPLEMENTED"},
    "FIX_IMPLEMENTED": {"HANDOFF": "READY_FOR_RETEST"},
    "READY_FOR_RETEST": {"RETEST": "RETESTING"},
    "RETESTING": {"PASS": "VERIFIED", "FAIL": "REOPENED"},
    "REOPENED": {"FIX": "FIX_IMPLEMENTED"},
}


def checked_ref(ref):
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not re.fullmatch(r"[0-9a-f]{64}", ref.get("sha256", "")):
        raise ValueError("exact artifact path/SHA reference required")
    path = Path(ref["path"])
    if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
        raise ValueError("artifact missing or hash drift")
    return path


def execution_blockers(dependencies):
    blockers = []
    for dep in dependencies:
        if dep.get("kind") not in DEPENDENCY_TYPES or dep.get("status") not in {"OPEN", "RESOLVED", "NOT_REQUIRED"} or type(dep.get("required")) is not bool:
            raise ValueError("invalid typed execution dependency")
        if dep["status"] == "RESOLVED":
            checked_ref(dep.get("resolution_ref"))
        if dep["status"] == "OPEN" and dep["required"]:
            blockers.append(dep)
    return blockers


def begin(testware_ref, dev_handoff_ref, delivery_ref, dependencies):
    promotion_path = checked_ref(testware_ref)
    promotion = json.loads(promotion_path.read_text(encoding="utf-8"))
    handoff = json.loads(checked_ref(dev_handoff_ref).read_text(encoding="utf-8"))
    from delivery_manifest import load_delivery_manifest
    delivery = load_delivery_manifest(checked_ref(delivery_ref))
    if promotion.get("approval_mode") != "HUMAN_AUTHENTICATED" or promotion.get("stage") != "cases":
        raise ValueError("APPROVED_TESTWARE promotion required")
    semantic_path = (promotion_path.parent / promotion.get("semantic_path", "")).resolve()
    approval_path = (promotion_path.parent / promotion.get("approval_path", "")).resolve()
    if not semantic_path.is_relative_to(promotion_path.parent.parent) or not approval_path.is_relative_to(promotion_path.parent):
        raise ValueError("promotion references escape durable testware")
    semantic_ref = {"path": str(semantic_path), "sha256": promotion.get("semantic_sha256")}
    semantic = checked_ref(semantic_ref)
    if semantic_ref["sha256"] != promotion.get("semantic_sha256"):
        raise ValueError("approved testcase semantic hash mismatch")
    approval_ref = {"path": str(approval_path), "sha256": promotion.get("approval_receipt_sha256")}
    approval = json.loads(checked_ref(approval_ref).read_text(encoding="utf-8"))
    if approval_ref["sha256"] != promotion.get("approval_receipt_sha256") or approval.get("decision") != "APPROVE" or approval.get("artifact_sha256") != promotion["semantic_sha256"]:
        raise ValueError("approved testcase receipt binding mismatch")
    if handoff.get("state") != "READY_FOR_TEST":
        raise ValueError("READY_FOR_TEST handoff required")
    commits = handoff.get("implementation", {}).get("commits", [])
    commit = commits[-1] if commits else None
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        raise ValueError("exact implementation commit required")
    execution_blockers(dependencies)
    return {"schema_version": 1, "state": "EXECUTION_READINESS", "feature_id": delivery["baseline"].feature_id,
            "testware_ref": testware_ref, "dev_handoff_ref": dev_handoff_ref, "delivery_ref": delivery_ref,
            "implementation_commit": commit, "dependencies": copy.deepcopy(dependencies), "history": []}


def validate_state(state):
    required = {"schema_version", "state", "feature_id", "testware_ref", "dev_handoff_ref", "delivery_ref", "implementation_commit", "dependencies", "history"}
    if not isinstance(state, dict) or not required.issubset(state) or state.get("schema_version") != 1:
        raise ValueError("invalid project execution state schema")
    states = set(TRANSITIONS) | {"PASS", "VERIFIED", "BA_DECISION_REQUIRED", "TEST_ENV_CORRECTION", "TEST_ISSUE"}
    if state["state"] not in states or not re.fullmatch(r"[0-9a-f]{40}", state["implementation_commit"]):
        raise ValueError("invalid state or implementation revision")
    if not isinstance(state["history"], list) or not isinstance(state["dependencies"], list):
        raise ValueError("state history/dependencies must be lists")
    return execution_blockers(state["dependencies"])


def make_defect_handoff(state):
    if state.get("classification") != "DEFECT" or state.get("state") != "DEFECT_READY_FOR_DEV":
        raise ValueError("only a classified implementation defect may be handed to Dev")
    from delivery_manifest import load_delivery_manifest
    delivery = load_delivery_manifest(state["delivery_ref"]["path"])
    finding = state["finding"]
    return {"schema_version": 1, "defect_id": "DEF-" + state["feature_id"] + "-" + finding["testcase_id"],
            "feature_id": state["feature_id"], "classification": "DEFECT", "state": "DEFECT_READY_FOR_DEV",
            "delivery_manifest": {"path": "delivery-manifest.yml", "revision": delivery["data"]["delivery_revision"], "sha256": delivery["sha256"]},
            "targets": delivery["data"]["targets"], "implementation_commit": state["implementation_commit"],
            "testcase": {"id": finding["testcase_id"], "oracle_sha256": finding["oracle_ref"]["sha256"]},
            "expected": finding["expected"], "actual": finding["actual"], "observation_sha256": finding["observation_ref"]["sha256"],
            "verification_owner": "TESTER"}


def validate_defect_handoff(data, state):
    if data != make_defect_handoff(state):
        raise ValueError("defect handoff differs from the classified finding/approved delivery")
    return []


def transition(state, event, *, actor_role, evidence=None, classification=None):
    blockers = validate_state(state)
    current = state.get("state")
    if event not in TRANSITIONS.get(current, {}):
        raise ValueError("invalid execution/defect/retest transition")
    expected_role = "DEV" if event in {"FIX", "HANDOFF"} else "TESTER"
    if actor_role != expected_role:
        raise ValueError(f"{expected_role} owns this transition")
    for name in ("testware_ref", "dev_handoff_ref", "delivery_ref"):
        checked_ref(state[name])
    from delivery_manifest import load_delivery_manifest
    load_delivery_manifest(state["delivery_ref"]["path"])
    if blockers:
        raise ValueError("execution dependencies remain OPEN")
    result = copy.deepcopy(state)
    target = TRANSITIONS[current][event]
    if event in {"PASS", "FAIL", "FIX", "HANDOFF", "CLASSIFY"}:
        record = json.loads(checked_ref(evidence).read_text(encoding="utf-8"))
        if record.get("implementation_commit") != state["implementation_commit"] and event not in {"FIX"}:
            raise ValueError("evidence belongs to a different implementation commit")
        if event in {"PASS", "FAIL"}:
            if not all(record.get(key) for key in ("testcase_id", "expected", "actual", "oracle_ref", "observation_ref")):
                raise ValueError("execution observation and approved oracle required")
            checked_ref(record["oracle_ref"])
            approved = json.loads(checked_ref(state["testware_ref"]).read_text(encoding="utf-8"))
            if record["oracle_ref"]["sha256"] != approved["semantic_sha256"]:
                raise ValueError("execution oracle differs from approved testcase snapshot")
            rows = json.loads(Path(record["oracle_ref"]["path"]).read_text(encoding="utf-8"))
            case = next((row for row in rows if row.get("test_case_id") == record["testcase_id"]), None)
            if case is None or record["expected"] not in [step.get("expected_result") for step in case.get("steps", [])]:
                raise ValueError("expected result is not defined by the approved testcase")
            observation = json.loads(checked_ref(record["observation_ref"]).read_text(encoding="utf-8"))
            if observation.get("actual") != record["actual"] or observation.get("expected") != record["expected"]:
                raise ValueError("execution record does not match observed evidence")
            if current == "RETESTING" and record["testcase_id"] != state["finding"]["testcase_id"]:
                raise ValueError("retest must cover the original failed testcase")
            if record.get("status") != event:
                raise ValueError("observation status mismatch")
            result["finding"] = record if event == "FAIL" else result.get("finding")
        if event == "CLASSIFY":
            if classification not in CLASSIFICATIONS:
                raise ValueError("finding classification required")
            if classification == "DEFECT" and not (record.get("approved_expected") is True and record.get("reproducible") is True and record.get("test_environment_excluded") is True):
                raise ValueError("failure is not proven to be an implementation defect")
            result["classification"] = classification
        if event == "FIX":
            handoff = json.loads(checked_ref(record.get("defect_handoff_ref")).read_text(encoding="utf-8"))
            if handoff != state.get("defect_handoff"):
                raise ValueError("fix is not bound to this exact defect handoff")
            commit = record.get("implementation_commit")
            if not re.fullmatch(r"[0-9a-f]{40}", commit or "") or commit == state["implementation_commit"]:
                raise ValueError("fix requires a new exact implementation commit")
            if record.get("verification") != "PASS":
                raise ValueError("fresh fix verification required")
            verification = json.loads(checked_ref(record.get("verification_ref")).read_text(encoding="utf-8"))
            if verification.get("status") != "PASS" or verification.get("implementation_commit") != commit:
                raise ValueError("fix verification is stale or failing")
            result["implementation_commit"] = commit
        if event == "HANDOFF" and record.get("state") != "READY_FOR_RETEST":
            raise ValueError("READY_FOR_RETEST evidence required")
    if event == "ROUTE":
        target = CLASSIFICATIONS[result["classification"]]
    result["state"] = target
    if target == "DEFECT_READY_FOR_DEV":
        result["defect_handoff"] = make_defect_handoff(result)
    result["history"].append({"from": current, "event": event, "to": target, "actor_role": actor_role,
                              "evidence": evidence, "classification": classification})
    return result
