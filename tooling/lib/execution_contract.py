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
    promotion = json.loads(checked_ref(testware_ref).read_text(encoding="utf-8"))
    handoff = json.loads(checked_ref(dev_handoff_ref).read_text(encoding="utf-8"))
    from delivery_manifest import load_delivery_manifest
    delivery = load_delivery_manifest(checked_ref(delivery_ref))
    if promotion.get("approval_mode") != "HUMAN_AUTHENTICATED" or promotion.get("stage") != "cases":
        raise ValueError("APPROVED_TESTWARE promotion required")
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


def transition(state, event, *, actor_role, evidence=None, classification=None):
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
    if execution_blockers(state["dependencies"]):
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
            checked_ref(record["oracle_ref"]); checked_ref(record["observation_ref"])
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
            commit = record.get("implementation_commit")
            if not re.fullmatch(r"[0-9a-f]{40}", commit or "") or commit == state["implementation_commit"]:
                raise ValueError("fix requires a new exact implementation commit")
            if record.get("verification") != "PASS":
                raise ValueError("fresh fix verification required")
            checked_ref(record.get("verification_ref"))
            result["implementation_commit"] = commit
        if event == "HANDOFF" and record.get("state") != "READY_FOR_RETEST":
            raise ValueError("READY_FOR_RETEST evidence required")
    if event == "ROUTE":
        target = CLASSIFICATIONS[result["classification"]]
    result["state"] = target
    result["history"].append({"from": current, "event": event, "to": target, "actor_role": actor_role,
                              "evidence": evidence, "classification": classification})
    return result
