"""Isolated driver; every Test Kit import must resolve from the installed package."""
import json
import hashlib
import os
from pathlib import Path
import sys


installed = Path(sys.argv[1]).resolve()
project = Path(sys.argv[2]).resolve()
automation_run_id = sys.argv[3]
execution_id = sys.argv[4]
host_path = Path(sys.argv[5]).resolve()
action = sys.argv[6]
sys.path[:0] = [str(installed), str(installed / "ba-workflow" / "scripts")]

from tooling.lib import test_execution_vnext as execution
from tooling.lib import test_automation_v1
from tooling.lib import test_kit_v1
from tooling.lib import test_kit_vnext
from tooling.lib import dev_vnext
from shared.sdlc import schema
import ba_vnext
import ba_contracts

modules = (execution, test_automation_v1, test_kit_v1, test_kit_vnext, dev_vnext, schema, ba_vnext, ba_contracts)
assert all(Path(module.__file__).resolve().is_relative_to(installed) for module in modules), {
    module.__name__: module.__file__ for module in modules
}
host = json.loads(host_path.read_text(encoding="utf-8"))


def ba_auth(actor_id, receipt):
    return actor_id == host["actor_id"] and receipt == host["ba_receipt"]


def test_auth(actor_id, receipt):
    if actor_id == host["actor_id"] and receipt in host["test_receipts"]:
        return test_kit_v1.AuthenticatedHumanActorContext(actor_id)
    return None


def tester_auth(actor_id, request):
    if actor_id == "synthetic-tester" and request.get("role") == "TESTER":
        return {"authenticated": True, "actor_id": actor_id, "role": "TESTER"}
    if actor_id == "synthetic-dev":
        return {"authenticated": True, "actor_id": actor_id, "role": "DEV"}
    return None


runtime = execution.ExecutionRuntime(
    project, project / ".test-kit" / "automation" / "runs" / automation_run_id, execution_id,
    tester_authenticator=tester_auth, human_actor_authenticator=test_auth,
    ba_human_actor_authenticator=ba_auth,
    repository_roots={"core": project / "app", "quality": project / "automation"},
)


def evidence(label):
    path = project / "installed-test-evidence" / f"{label}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"evidence": label}, sort_keys=True) + "\n", encoding="utf-8")
    return {"id": f"EVIDENCE-{label}", "revision": "1", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "path": path.relative_to(project).as_posix()}


def print_result(value):
    print(json.dumps({"action": action, "installed_only_imports": True, **value}, sort_keys=True))


if action == "defect-start":
    runtime.start({
        "schema_version": 1, "artifact_class": "CANONICAL", "environment_id": "ENV-INSTALLED-1",
        "profile": "PROFILE-INSTALLED-1", "configuration_refs": [], "evidence_refs": [],
    })
    runtime.execute_automated()
    manifest = runtime.execution_manifest()
    failed = []
    for item in manifest["automated_items"]:
        command_ref = runtime.state["command_evidence_refs"][item["aut_id"]]
        command = runtime.read_artifact(command_ref)
        case_id = item["testcase_refs"][0]
        outcome = "FINDING" if command["status"] == "COMMAND_FAIL" else "PASS"
        result = runtime.record_observation(
            testcase_id=case_id, aut_id=item["aut_id"], outcome=outcome,
            actual_summary="Observed the exact approved automated testcase outcome.",
            evidence_refs=[command_ref], actor_id="synthetic-tester",
        )
        if outcome == "FINDING":
            failed.append((case_id, item, command_ref, result))
    assert len(failed) == 1, "synthetic defect path must produce exactly one failed approved testcase"
    for row in manifest["manual_testcases"]:
        runtime.record_observation(
            testcase_id=row["testcase_id"], outcome="PASS", actual_summary="Manual approved scenario was observed.",
            evidence_refs=[evidence(f"manual-{execution_id}")], actor_id="synthetic-tester",
        )
    case_id, item, command_ref, finding_result = failed[0]
    finding_id = next(iter(runtime.state["finding_refs"]))
    classified = runtime.classify_finding(
        finding_id, "DEFECT", actor_id="synthetic-tester",
        rationale="The exact approved oracle has a reproducible mismatch; environment and test causes are excluded.",
        evidence_refs=[command_ref], target_repository_ids=[next(iter(manifest["application_revisions"]))],
        defect_proof={
            "reproducible": True, "deterministic": True, "environment_root_cause_excluded": True,
            "test_issue_excluded": True, "mismatch_evidence_refs": [command_ref],
        },
    )
    defect = runtime.read_artifact(classified["defect_handoff_ref"])
    print_result({"state": runtime.state["status"], "defect_id": defect["defect_id"], "failed_testcase": case_id, "finding_id": finding_id})
elif action == "fix-retest":
    dev_handoff_path = Path(sys.argv[7]).resolve()
    defect_id = sys.argv[8]
    accepted = runtime.accept_dev_fix(defect_id, dev_handoff_path)
    ready = runtime.read_artifact(accepted["ready_for_retest_ref"])
    result = runtime.execute_retest(defect_id)
    outcome = "PASS" if result.get("command_status") == "COMMAND_PASS" else "FINDING"
    closed = runtime.record_retest_observation(
        defect_id, outcome=outcome,
        actual_summary="Tester reran the original approved testcase at exact fixed revisions.",
        evidence_refs=([result["command_evidence_ref"]] if result.get("command_evidence_ref") else [evidence(f"manual-retest-{execution_id}")]),
        actor_id="synthetic-tester",
    )
    if outcome == "PASS":
        runtime.revalidate_verified()
    print_result({"state": closed["state"], "defect_id": defect_id, "ready_for_retest": ready["state"], "command_status": result.get("command_status", "MANUAL_ONLY")})
elif action == "prepare-reopened":
    defect_id = sys.argv[7]
    value = runtime.prepare_reopened_defect_handoff(defect_id)
    print_result({"state": runtime.state["status"], "defect_id": value["defect_id"], "cycle": value["cycle"]})
elif action == "straight-pass":
    runtime.start({
        "schema_version": 1, "artifact_class": "CANONICAL", "environment_id": "ENV-INSTALLED-1",
        "profile": "PROFILE-INSTALLED-1", "configuration_refs": [], "evidence_refs": [],
    })
    runtime.execute_automated()
    manifest = runtime.execution_manifest()
    for item in manifest["automated_items"]:
        command_ref = runtime.state["command_evidence_refs"][item["aut_id"]]
        assert runtime.read_artifact(command_ref)["status"] == "COMMAND_PASS"
        runtime.record_observation(
            testcase_id=item["testcase_refs"][0], aut_id=item["aut_id"], outcome="PASS",
            actual_summary="Exact approved automated testcase passed.", evidence_refs=[command_ref], actor_id="synthetic-tester",
        )
    for row in manifest["manual_testcases"]:
        runtime.record_observation(
            testcase_id=row["testcase_id"], outcome="PASS", actual_summary="Exact approved manual testcase passed.",
            evidence_refs=[evidence(f"manual-{execution_id}")], actor_id="synthetic-tester",
        )
    try:
        runtime.finalize_verified(actor_id="synthetic-dev")
    except execution.ExecutionVNextError as error:
        assert error.code == "AUTHENTICATION_FAILED", error
    else:
        raise AssertionError("Dev actor authenticated final VERIFIED")
    verified = runtime.finalize_verified(actor_id="synthetic-tester")
    runtime.revalidate_verified()
    print_result({"state": verified["state"], "verified_ref": verified["verified_ref"]})
elif action == "revalidate":
    try:
        verified = runtime.revalidate_verified()
    except execution.ExecutionVNextError as error:
        print_result({"state": "REJECTED", "code": error.code})
    else:
        print_result({"state": verified["state"]})
else:
    raise ValueError("unsupported installed acceptance action")
