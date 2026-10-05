"""Isolated synthetic Automation V1 flow using only installed Test Kit modules."""
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


runtime_root = Path(sys.argv[1]).resolve()
project = Path(sys.argv[2]).resolve()
test_run = Path(sys.argv[3]).resolve()
dev_handoff = Path(sys.argv[4]).resolve()
host = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))
sys.path[:0] = [str(runtime_root), str(runtime_root / "ba-workflow" / "scripts")]

module_names = (
    "tooling.lib.test_automation_v1",
    "tooling.lib.test_kit_vnext",
    "tooling.lib.test_kit_v1",
    "tooling.lib.dev_vnext",
    "shared.sdlc.policy.contract",
    "shared.sdlc.topology.contract",
)
modules = {name: importlib.import_module(name) for name in module_names}
installed_only = all(Path(module.__file__).resolve().is_relative_to(runtime_root) for module in modules.values())
assert installed_only, {name: module.__file__ for name, module in modules.items()}

automation = modules["tooling.lib.test_automation_v1"]
test_v1 = modules["tooling.lib.test_kit_v1"]
ba_receipt = json.loads((project / "receipt.json").read_text(encoding="utf-8"))
test_receipts = host["test_receipts"]


def ba_auth(actor, receipt):
    if actor == "synthetic-human" and receipt == ba_receipt:
        return True
    return None


def test_auth(actor, receipt):
    if actor == "synthetic-human" and any(receipt == expected for expected in test_receipts):
        return test_v1.AuthenticatedHumanActorContext(actor)
    return None


app_root = project / "app"
automation_root = project / "automation"
runtime = automation.AutomationRuntime(
    project,
    project / ".test-kit/automation/runs/FEATURE-1",
    human_actor_authenticator=test_auth,
    ba_human_actor_authenticator=ba_auth,
    repository_roots={"core": app_root, "quality": automation_root},
)
state = runtime.start(test_run)
assessments = [
    {"testcase_id": "TC-001", "classification": "API", "required": True, "rationale": "Use the approved API boundary."},
    {"testcase_id": "TC-002", "classification": "MANUAL_ONLY", "required": True, "rationale": "Keep its approved steps as the manual protocol."},
    {"testcase_id": "TC-003", "classification": "UNIT", "required": True, "rationale": "Reference exact Dev-local evidence."},
    {"testcase_id": "TC-004", "classification": "E2E", "required": True, "rationale": "Use the project-owned end-to-end runner."},
]
state = runtime.analyze_suitability(assessments)
suitability = runtime._read_artifact_ref(state["suitability_ref"])
assert [(row["testcase_id"], row["owner"]) for row in suitability["rows"]] == [
    ("TC-001", "TEST_AUTOMATION"),
    ("TC-002", "MANUAL"),
    ("TC-003", "DEV_LOCAL_REFERENCE"),
    ("TC-004", "TEST_AUTOMATION"),
]

verification = [{"category": "STATIC", "argv": ["git", "diff", "--cached", "--check"]}]
specs = {
    "TC-001": {
        "suite": "api", "planned_paths": ["tests/api/test_request.py"],
        "runner": "project-native",
        "execution_command": ["python", "-m", "pytest", "tests/api/test_request.py"],
        "verification_commands": verification,
    },
    "TC-004": {
        "suite": "end-to-end", "planned_paths": ["tests/e2e/test_request_flow.py"],
        "runner": "project-native",
        "execution_command": ["python", "-m", "pytest", "tests/e2e/test_request_flow.py"],
        "verification_commands": verification,
    },
}
state = runtime.plan(specs)
plan = runtime._read_artifact_ref(state["plan_ref"])
assert [item["aut_id"] for item in plan["items"]] == ["AUT-0001", "AUT-0002"]
assert plan["items"][1]["runner"] == "project-native"

state = runtime.begin_implementation()
app_evidence = app_root / "tests/test_request.py"
app_before = hashlib.sha256(app_evidence.read_bytes()).hexdigest()
app_write_rejected = False
try:
    runtime.write_source(
        "AUT-0001", "core", "tests/test_request.py", "# forbidden\n",
        base_revision=state["implementation_base_revision"],
    )
except automation.AutomationV1Error as error:
    app_write_rejected = error.code == "APP_REPOSITORY_WRITE_FORBIDDEN"
assert app_write_rejected
assert hashlib.sha256(app_evidence.read_bytes()).hexdigest() == app_before
try:
    runtime.write_source(
        "AUT-0001", "quality", "tests/not-planned.py", "# forbidden\n",
        base_revision=state["implementation_base_revision"],
    )
except automation.AutomationV1Error as error:
    assert error.code == "WRITE_SCOPE_VIOLATION"
else:
    raise AssertionError("unplanned automation path was accepted")

source = {
    "AUT-0001": "def test_api_harness_shape():\n    assert True\n",
    "AUT-0002": "def test_e2e_harness_shape():\n    assert True\n",
}
for item in plan["items"]:
    runtime.write_source(
        item["aut_id"], "quality", item["planned_paths"][0], source[item["aut_id"]],
        base_revision=state["implementation_base_revision"],
    )
subprocess.run(
    ["git", "add", "tests/api/test_request.py", "tests/e2e/test_request_flow.py"],
    cwd=automation_root, check=True, shell=False,
)
subprocess.run(
    ["git", "commit", "-q", "-m", "Implement planned automation"],
    cwd=automation_root, check=True, shell=False,
)
state = runtime.record_implementation()
review_checks = {
    "trace", "repository_ownership", "oracle_duplication", "fixtures", "secrets",
    "setup_cleanup", "flakiness", "selectors_interfaces", "dependencies",
    "project_conventions", "write_scope",
}
state = runtime.record_review({
    "reviewer": "synthetic-review",
    "checks": {key: True for key in review_checks},
    "findings": [],
})

executed = []
run = automation.subprocess.run


def observe(args, *positional, **options):
    executed.append(list(args))
    return run(args, *positional, **options)


automation.subprocess.run = observe
try:
    state = runtime.verify()
finally:
    automation.subprocess.run = run
verification_report = runtime._read_artifact_ref(state["verification_ref"])
product_command_executed = any("pytest" in str(part).casefold() for command in executed for part in command)
assert verification_report["status"] == "PASS"
assert verification_report["product_execution"] == "NOT_RUN"
assert verification_report["claims"] == []
assert not product_command_executed

state = runtime.finalize(dev_handoff)
assert state["lifecycle"] == "EXECUTION_READY", state
handoff = runtime.revalidate_handoff()
automation_revision = subprocess.run(
    ["git", "-C", str(automation_root), "rev-parse", "HEAD"],
    capture_output=True, check=True, text=True, encoding="utf-8", shell=False,
).stdout.strip()
assert handoff["automation_revision"] == automation_revision
implementation = runtime.status()["implementation"]
committed_hashes = {row["path"]: row["sha256"] for row in implementation["files"]}
with tempfile.TemporaryDirectory(prefix="automation-fresh-clone-") as temporary:
    clone = Path(temporary) / "checkout"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-local", str(automation_root), str(clone)],
        check=True, capture_output=True, shell=False,
    )
    subprocess.run(
        ["git", "-C", str(clone), "checkout", "--quiet", "--detach", automation_revision],
        check=True, capture_output=True, shell=False,
    )
    clone_head = subprocess.run(
        ["git", "-C", str(clone), "rev-parse", "HEAD"],
        capture_output=True, check=True, text=True, encoding="utf-8", shell=False,
    ).stdout.strip()
    assert clone_head == automation_revision
    for item in handoff["automation_items"]:
        for path in item["paths"]:
            assert (clone / Path(path)).is_file(), path
            committed = subprocess.run(
                ["git", "-C", str(clone), "cat-file", "blob", f"{automation_revision}:{path}"],
                capture_output=True, check=True, shell=False,
            ).stdout
            assert hashlib.sha256(committed).hexdigest() == committed_hashes[path], path
resumed = automation.AutomationRuntime(
    project,
    project / ".test-kit/automation/runs/FEATURE-1",
    human_actor_authenticator=test_auth,
    ba_human_actor_authenticator=ba_auth,
    repository_roots={"core": app_root, "quality": automation_root},
)
assert resumed.status()["lifecycle"] == "EXECUTION_READY"
assert resumed.revalidate_handoff() == handoff
assert not any(key in json.dumps(handoff).casefold() for key in ("expected_result", "execution_outcome", "verified"))

print(json.dumps({
    "state": state["lifecycle"],
    "aut_ids": [item["aut_id"] for item in plan["items"]],
    "manual_testcases": [row["testcase_id"] for row in handoff["manual_testcases"]],
    "dev_local_testcases": [row["testcase_id"] for row in handoff["dev_local_references"]],
    "app_write_rejected": app_write_rejected,
    "installed_only_imports": installed_only,
    "module_paths": {name: module.__file__ for name, module in modules.items()},
    "product_execution": verification_report["product_execution"],
    "product_command_executed": product_command_executed,
    "automation_revision": automation_revision,
    "fresh_clone_revision": clone_head,
    "fresh_clone_paths_reconstructed": True,
}, sort_keys=True))
