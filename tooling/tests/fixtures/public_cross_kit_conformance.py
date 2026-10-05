"""Isolated public Phase 9 cross-kit scenario using installed kit runtimes."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


FEATURE_ID = "FEATURE-RSV-001"
BA_IDS = ("BR-RSV-001", "FR-RSV-001")
TEST_ONLY_ACTOR = "TEST_ONLY:synthetic-reviewer"
BA_TEST_ONLY_ACTOR = "TEST_ONLY-synthetic-reviewer"


def repository_for_role(topology: dict, role: str) -> dict:
    matches = [row for row in topology.get("repositories", []) if row.get("role") == role]
    if len(matches) != 1:
        raise ValueError(f"repository role is ambiguous or missing: {role}")
    return matches[0]


def write_json(path: Path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def file_ref(root: Path, relative: str, revision: str = "R1") -> dict:
    path = (Path(root) / relative).resolve()
    if not path.is_file() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError(f"public artifact reference is missing or outside project: {relative}")
    return {"path": relative.replace("\\", "/"), "revision": revision,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def read_ref(root: Path, ref: dict):
    path = (Path(root) / ref["path"]).resolve()
    if not path.is_file() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError("artifact reference is missing or unsafe")
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != ref["sha256"]:
        raise ValueError("artifact reference hash mismatch")
    return json.loads(content.decode("utf-8"))


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}: {result.stderr}")
    return result.stdout.strip()


def commit_repository(root: Path, name: str, repository_id: str) -> str:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "--quiet")
    git(root, "config", "user.name", "Synthetic Conformance Host")
    git(root, "config", "user.email", "conformance@example.invalid")
    git(root, "config", "core.autocrlf", "false")
    (root / "README.md").write_text(f"Neutral synthetic repository: {repository_id}.\n", encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "--quiet", "-m", "Create synthetic repository baseline")
    git(root, "remote", "add", "origin", f"https://github.com/{name}.git")
    return git(root, "rev-parse", "HEAD")


def import_installed_modules(runtime_root: Path, names: tuple[str, ...], extra_paths=()) -> dict:
    runtime_root = Path(runtime_root).resolve()
    runtime_roots = [Path(path).resolve() for path in extra_paths] + [runtime_root]
    sys.path[:0] = [str(path) for path in runtime_roots]
    modules = {name: importlib.import_module(name) for name in names}
    outside = {name: str(Path(module.__file__).resolve()) for name, module in modules.items()
               if not any(Path(module.__file__).resolve().is_relative_to(root) for root in runtime_roots)}
    if outside:
        raise AssertionError(f"runtime modules did not resolve from installed package: {outside}")
    if "PYTHONPATH" in os.environ:
        raise AssertionError("installed acceptance requires PYTHONPATH to be absent")
    return modules


def _host_auth(actor_id: str, expected_receipt: dict, envelope_path: Path, decision_path: Path):
    envelope = read_json(envelope_path)
    if (envelope.get("not_for_production") is True and envelope.get("receipt") == expected_receipt
            and actor_id == expected_receipt.get("actor_id")
            and "TEST_ONLY" in decision_path.read_text(encoding="utf-8")
            and "not_for_production" in decision_path.read_text(encoding="utf-8")):
        return True
    return False


def setup_workspace(root: Path):
    root = Path(root).resolve()
    root.mkdir(parents=True)
    docs = root / "project-docs"
    app = root / "service-app"
    automation = root / "test-automation"
    repos = {
        "project_documentation_authority": {"id": "docs", "path": "project-docs", "repository": "example/resource-reservation-docs", "role": "project_documentation_authority"},
        "application_implementation": {"id": "service-app", "path": "service-app", "repository": "example/resource-reservation-app", "role": "application_implementation"},
        "project_test_automation": {"id": "test-automation", "path": "test-automation", "repository": "example/resource-reservation-automation", "role": "project_test_automation"},
    }
    topology = {"schema_version": 1, "project": {"id": "resource-reservation"}, "repositories": list(repos.values())}
    policy = {
        "schema_version": 1,
        "project": {"language": "en"},
        "foundation": {"profile": "arc42-standard-v1"},
        "authority": {
            "product": "project-docs/product.md", "domain": "project-docs/domain.md",
            "architecture": "project-docs/architecture.md", "testing": "project-docs/testing.md",
            "features": "project-docs/features.md",
        },
        "workflow": {"feature_root": "project-docs/features", "branch_convention": "feature/{feature_id}"},
        "testing": {"automation_repository_role": "project_test_automation"},
        "artifacts": {"optional": [
            "project-docs/foundation/R1.json", "project-docs/foundation/R1.provenance.json",
        ]},
    }
    for relative, content in {
        "product.md": "# Product\nA resource owner can request an available reservation slot.\n",
        "domain.md": "# Domain\nA slot is either available or occupied; a reservation claims one slot.\n",
        "architecture.md": "# Architecture\nThe service is a local Python module with an explicit repository boundary.\n",
        "testing.md": "# Testing\nThe automation repository runs a local Python oracle against the service repository.\n",
        "features.md": "# Feature Context\nReservation availability is covered by BR-RSV-001 and FR-RSV-001.\n",
    }.items():
        target = docs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    (docs / ".gitignore").write_text("features/*/workflow-state-vnext.json\n__pycache__/\n", encoding="utf-8")
    commit_repository(docs, repos["project_documentation_authority"]["repository"], "docs")

    (app / "src").mkdir(parents=True)
    (app / "tests").mkdir()
    (app / ".gitignore").write_text("__pycache__/\n.devkit/\n", encoding="utf-8")
    (app / "src/reservations.py").write_text(
        "def is_available(slot):\n    return True\n", encoding="utf-8",
    )
    (app / "tests/test_contract_shape.py").write_text(
        "from pathlib import Path\nimport sys\nsys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        "from src.reservations import is_available\nassert isinstance(is_available('occupied'), bool)\n",
        encoding="utf-8",
    )
    commit_repository(app, repos["application_implementation"]["repository"], "service-app")

    (automation / "tests").mkdir(parents=True)
    (automation / ".gitignore").write_text("__pycache__/\n.test-kit/\n", encoding="utf-8")
    commit_repository(automation, repos["project_test_automation"]["repository"], "test-automation")

    root_ignore = "\n".join((
        ".sdlc/runs/", ".sdlc/phase9-inputs/", ".sdlc/phase9-evidence/",
        ".test-kit/", ".agents/skills/", ".devkit/", "project-docs/", "service-app/", "test-automation/", "",
    ))
    (root / ".gitignore").write_text(root_ignore, encoding="utf-8")
    write_json(root / ".sdlc/topology.json", topology)
    write_json(root / ".sdlc/project-topology.yml", topology)
    write_json(root / ".sdlc/project-policy.yml", policy)
    git(root, "init", "--quiet")
    git(root, "config", "user.name", "Synthetic Workspace Owner")
    git(root, "config", "user.email", "workspace@example.invalid")
    git(root, "add", ".gitignore", ".sdlc/topology.json", ".sdlc/project-topology.yml", ".sdlc/project-policy.yml")
    git(root, "commit", "--quiet", "-m", "Declare synthetic workspace topology and policy")
    return {"root": root, "docs": docs, "app": app, "automation": automation, "topology": topology, "policy": policy}


def foundation_and_ba_stage(args):
    root = Path(args.workspace).resolve()
    skill_root = Path(args.skills).resolve()
    scripts = skill_root / "ba-workflow/scripts"
    foundation_payload = Path(args.framework_root).resolve() / "project-foundation/scripts/shared-sdlc-core.zip"
    modules = import_installed_modules(skill_root / ".test-kit", (
        "shared.sdlc.foundation.workflow", "shared.sdlc.foundation.impact",
        "ba_vnext", "ba_contracts", "shared.sdlc.schema",
    ), (foundation_payload, scripts))
    foundation = modules["shared.sdlc.foundation.workflow"]
    ba = modules["ba_vnext"]
    public_entry = Path(args.framework_root).resolve() / "project-foundation/scripts/project_foundation.py"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("CODEX_HOME", None)
    run_id = "phase9-foundation"
    command = [sys.executable, "-I", str(public_entry), "start", "--project-root", str(root),
               "--run-id", run_id, "--mode", "GREENFIELD_BOOTSTRAP", "--level", "STANDARD",
               "--topology", ".sdlc/topology.json", "--config-revision", "R1"]
    started = subprocess.run(command, cwd=args.external_cwd, env=env, capture_output=True, text=True, timeout=90)
    if started.returncode:
        raise RuntimeError("Project Foundation public start failed: " + (started.stderr or started.stdout))

    authority_paths = read_json(root / ".sdlc/project-policy.yml")["authority"]
    sections = {}
    for section, domain, owner in (
        ("introduction_goals", "product", "BA"),
        ("constraints", "architecture", "ENGINEERING"),
        ("quality_requirements", "testing", "TEST"),
    ):
        source = authority_paths[domain]
        sections[section] = {
            "status": "PARTIAL", "owner": owner, "evidence": "PROPOSED", "blocking": False,
            "references": [{"path": source, "revision": "R1", "sha256": hashlib.sha256((root / source).read_bytes()).hexdigest()}],
        }
    inputs = root / ".sdlc/phase9-inputs/foundation-sections.json"
    write_json(inputs, {"sections": sections, "blockers": []})
    prepared = subprocess.run(
        [sys.executable, "-I", str(public_entry), "prepare", "--project-root", str(root), "--run-id", run_id,
         "--manifest-id", "foundation-resource-reservation", "--revision", "R1", "--input", ".sdlc/phase9-inputs/foundation-sections.json"],
        cwd=args.external_cwd, env=env, capture_output=True, text=True, timeout=90,
    )
    if prepared.returncode:
        raise RuntimeError("Project Foundation public prepare failed: " + (prepared.stderr or prepared.stdout))
    candidate_path = root / ".sdlc/runs/foundation/phase9-foundation/candidates/R1/manifest.json"
    candidate = read_json(candidate_path)
    before_gate = foundation.doctor(root, run_id)
    if before_gate.get("status") == "PROJECT_FOUNDATION_READY":
        raise AssertionError("Foundation review preparation self-approved")

    foundation_decision = root / ".sdlc/phase9-evidence/foundation-human-decision.txt"
    foundation_decision.parent.mkdir(parents=True, exist_ok=True)
    foundation_decision.write_text(
        "TEST_ONLY; not_for_production\nHuman review of the exact Project Foundation candidate.\n", encoding="utf-8",
    )
    foundation_receipt = {
        "schema_version": 1, "decision": "APPROVE", "actor_id": TEST_ONLY_ACTOR, "actor_role": "HUMAN",
        "artifact_id": candidate["id"], "artifact_revision": candidate["revision"],
        "manifest_sha256": foundation.manifest_sha256(candidate),
        "decision_ref": foundation.exact_ref(root, ".sdlc/phase9-evidence/foundation-human-decision.txt", "R1"),
    }
    receipt_path = root / ".sdlc/phase9-evidence/foundation-receipt.json"
    write_json(receipt_path, foundation_receipt)
    receipt_ref = foundation.exact_ref(root, ".sdlc/phase9-evidence/foundation-receipt.json", "R1")
    host_path = root / ".sdlc/phase9-evidence/foundation-human-host.json"
    write_json(host_path, {"fixture_type": "TEST_ONLY_FOUNDATION_HUMAN_APPROVAL", "not_for_production": True,
                           "receipt": foundation_receipt})
    foundation_auth = lambda actor, actual: _host_auth(actor, foundation_receipt, host_path, foundation_decision) and actual == foundation_receipt
    validator_not_approval = True
    for authenticator in (None, lambda *_: False):
        try:
            foundation.accept(root, run_id, receipt_ref, human_actor_authenticator=authenticator)
        except (ValueError, TypeError):
            pass
        else:
            validator_not_approval = False
            raise AssertionError("Foundation accepted validator/preparation without trusted Human authentication")
    accepted = foundation.accept(root, run_id, receipt_ref, human_actor_authenticator=foundation_auth)
    if accepted.get("state") not in {"ACCEPTED_BASELINE", "APPROVED_BASELINE"}:
        raise AssertionError("exact Foundation receipt did not create accepted baseline")
    foundation.promote(root, run_id, "project-docs/foundation/R1.json", "project-docs/foundation/R1.provenance.json",
                       human_actor_authenticator=foundation_auth)
    foundation_ready = foundation.doctor(root, run_id, human_actor_authenticator=foundation_auth)
    if foundation_ready.get("status") != "PROJECT_FOUNDATION_READY":
        raise AssertionError(f"Foundation promotion did not reach PROJECT_FOUNDATION_READY: {foundation_ready}")
    foundation_refs = {
        "manifest": foundation.exact_ref(root, "project-docs/foundation/R1.json", "R1"),
        "provenance": foundation.exact_ref(root, "project-docs/foundation/R1.provenance.json", "R1"),
        "approval": receipt_ref,
    }
    git(root / "project-docs", "add", "foundation/R1.json", "foundation/R1.provenance.json")
    git(root / "project-docs", "commit", "--quiet", "-m", "Promote approved Project Foundation snapshot")
    ba_binding = {**foundation_refs, "root": "."}

    feature_dir = root / "project-docs/features" / FEATURE_ID
    feature_dir.mkdir(parents=True, exist_ok=True)
    business_rules = feature_dir / "business-rules.md"
    srs = feature_dir / "srs.md"
    decisions_path = feature_dir / "decisions.json"
    human_decision = feature_dir / "human-decision.txt"
    business_rules.write_text(
        "# Business Rules\n\n## BR-RSV-001 Occupied slot\nCONFIRMED: An occupied slot cannot be reserved again.\n",
        encoding="utf-8",
    )
    srs.write_text(
        "# Reservation requirements\n\n## FR-RSV-001 Request an available slot\nCONFIRMED: A request for an occupied slot returns unavailable and does not change the slot state.\n",
        encoding="utf-8",
    )
    human_decision.write_text("TEST_ONLY; not_for_production\nApprove the exact BR/FR baseline for this feature.\n", encoding="utf-8")
    source_refs = {
        "business_rules": file_ref(root, business_rules.relative_to(root).as_posix()),
        "srs": file_ref(root, srs.relative_to(root).as_posix()),
    }
    decisions = {
        "schema_version": 1, "feature_id": FEATURE_ID,
        "decisions": [{
            "id": "DEC-RSV-001", "topic": "occupied-slot behavior",
            "text": "An occupied slot remains unavailable after a rejected request.",
            "actor_id": BA_TEST_ONLY_ACTOR, "actor_role": "HUMAN", "recorded_at": "2026-10-05T00:00:00Z",
            "input_refs": [file_ref(root, human_decision.relative_to(root).as_posix())],
            "affected_ids": list(BA_IDS), "status": "CONFIRMED", "supersedes": [], "superseded_by": [],
            "implemented_sources": copy.deepcopy(source_refs),
        }],
    }
    write_json(decisions_path, decisions)
    sources = {**source_refs, "decisions": file_ref(root, decisions_path.relative_to(root).as_posix())}
    feature = {"id": FEATURE_ID, "title": "Reserve an available resource slot"}
    human_host_path = root / ".sdlc/phase9-evidence/ba-human-host.json"
    baseline_id = "BA-RSV-001"
    candidate = ba.make_candidate(
        root, feature=feature, baseline_id=baseline_id, revision="R1", sources=sources,
        business_identities=[
            {"id": BA_IDS[0], "semantic_key": "occupied-slot-block", "status": "ACTIVE"},
            {"id": BA_IDS[1], "semantic_key": "reserve-available-slot", "status": "ACTIVE"},
        ], knowledge=modules["shared.sdlc.foundation.impact"].knowledge_impact(),
        project_foundation=ba_binding, foundation_authenticator=foundation_auth,
    )
    candidate_ref = ba.publish_candidate(root, f"project-docs/features/{FEATURE_ID}/candidates/R1.json", candidate)
    state = ba.select_candidate(ba.new_state(feature, "GREENFIELD"), candidate_ref, root,
                               foundation_authenticator=foundation_auth)
    state_path = f"project-docs/features/{FEATURE_ID}/workflow-state-vnext.json"
    ba.save_state(root, state_path, ba.new_state(feature, "GREENFIELD"), state,
                  foundation_authenticator=foundation_auth)
    state = ba.advance(state, "VALIDATE", root, foundation_authenticator=foundation_auth)
    before = ba.read_document((root / state_path).read_text(encoding="utf-8"))
    ba.save_state(root, state_path, before, state, foundation_authenticator=foundation_auth)
    before = state
    state = ba.advance(state, "REQUEST_REVIEW", root, foundation_authenticator=foundation_auth)
    ba.save_state(root, state_path, before, state, foundation_authenticator=foundation_auth)
    try:
        ba.advance(state, "APPROVE", root, foundation_authenticator=foundation_auth)
    except ValueError:
        pass
    else:
        raise AssertionError("BA validator/review did not require a separate authenticated Human approval")
    receipt = {
        "schema_version": 1, "artifact_type": "BA_BASELINE", "decision": "APPROVE",
        "actor_id": BA_TEST_ONLY_ACTOR, "actor_role": "HUMAN", "recorded_at": "2026-10-05T00:05:00Z",
        "feature_id": FEATURE_ID, "baseline_id": candidate["id"], "baseline_revision": candidate["revision"],
        "baseline_semantic_sha256": candidate["semantic_sha256"], "baseline_manifest": candidate_ref,
        "decision_ref": file_ref(root, human_decision.relative_to(root).as_posix()),
    }
    receipt_path = feature_dir / "human-approval-receipt.json"
    receipt_path.write_bytes(ba.semantic_bytes(receipt))
    receipt_ref = file_ref(root, receipt_path.relative_to(root).as_posix(), "R1")
    write_json(human_host_path, {"fixture_type": "TEST_ONLY_BA_HUMAN_APPROVAL", "not_for_production": True,
                                 "receipt": receipt})
    ba_auth = lambda actor, actual: _host_auth(actor, receipt, human_host_path, human_decision) and actual == receipt
    before = state
    state = ba.advance(state, "APPROVE", root, approval=receipt_ref,
                       human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth)
    ba.save_state(root, state_path, before, state, human_actor_authenticator=ba_auth,
                  foundation_authenticator=foundation_auth)
    handoff = ba.make_handoff(state, root, human_actor_authenticator=ba_auth,
                              foundation_authenticator=foundation_auth)
    handoff_path = feature_dir / "engineering-handoff-vnext.json"
    handoff_path.write_bytes(ba.semantic_bytes(handoff))
    validated_handoff = ba.validate_handoff(read_json(handoff_path), root,
                                           human_actor_authenticator=ba_auth,
                                           foundation_authenticator=foundation_auth)
    if handoff.get("schema_version") != 2 or validated_handoff.get("human_approval") is not True:
        raise AssertionError("BA did not publish authenticated Engineering Handoff V2")
    if not set(BA_IDS) <= set(candidate["coverage_ids"]) or any(item.startswith("BAREF:") for item in candidate["coverage_ids"]):
        raise AssertionError("BA canonical trace must retain exact BR/FR identities without BAREF")
    stale_handoff = copy.deepcopy(handoff)
    stale_handoff["approval_receipt"] = {**stale_handoff["approval_receipt"], "sha256": "0" * 64}
    try:
        ba.validate_handoff(stale_handoff, root, human_actor_authenticator=ba_auth,
                            foundation_authenticator=foundation_auth)
    except ValueError:
        pass
    else:
        raise AssertionError("stale BA Human receipt was accepted downstream")
    feature_relative = Path("features") / FEATURE_ID
    git(root / "project-docs", "add",
        str(feature_relative / "business-rules.md"), str(feature_relative / "srs.md"),
        str(feature_relative / "decisions.json"), str(feature_relative / "human-decision.txt"),
        str(feature_relative / "human-approval-receipt.json"),
        str(feature_relative / "candidates/R1.json"),
        str(feature_relative / "engineering-handoff-vnext.json"))
    git(root / "project-docs", "commit", "--quiet", "-m", "Approve neutral reservation requirements")
    print(json.dumps({
        "foundation": {"status": foundation_ready["status"], **foundation_refs},
        "ba": {"status": state["lifecycle"], "handoff_path": handoff_path.relative_to(root).as_posix(),
               "handoff_sha256": hashlib.sha256(handoff_path.read_bytes()).hexdigest(),
               "human_receipt": receipt_ref, "requirements": list(BA_IDS)},
        "project_doc_repo": {"id": "docs", "sha": git(root / "project-docs", "rev-parse", "HEAD")},
        "installed_modules": {name: str(Path(module.__file__).resolve()) for name, module in modules.items()},
    }, ensure_ascii=False, sort_keys=True))


def dev_stage(args):
    root = Path(args.workspace).resolve()
    runtime_root = Path(args.dev_runtime).resolve()
    modules = import_installed_modules(runtime_root, ("tooling.lib.dev_vnext_runtime", "tooling.lib.dev_vnext"))
    runtime_module = modules["tooling.lib.dev_vnext_runtime"]
    dev = modules["tooling.lib.dev_vnext"]
    topology = read_json(root / ".sdlc/topology.json")
    app_repo = repository_for_role(topology, "application_implementation")
    app_root = root / app_repo["path"]
    handoff_path = Path(args.ba_handoff).resolve()
    handoff = read_json(handoff_path)
    receipt_ref = handoff["approval_receipt"]
    receipt = read_ref(root, receipt_ref)
    ba_auth = lambda actor, actual: actor == receipt["actor_id"] and actual == receipt
    change_id = args.change_id
    initial = args.kind == "initial"
    source_text = "def is_available(slot):\n    return True\n" if initial else (
        "def is_available(slot):\n    return slot != 'occupied'\n"
    )
    base_revision = git(app_root, "rev-parse", "HEAD")
    check_name = "shape-only" if initial else "fresh-behavior-check"
    checks = [
        {"name": "compile", "repository_id": app_repo["id"], "category": "BUILD",
         "command": ["python", "-I", "-m", "py_compile", "src/reservations.py"]},
        {"name": check_name, "repository_id": app_repo["id"], "category": "UNIT",
         "command": ["python", "-I", "tests/test_contract_shape.py"]},
    ]
    if not initial:
        checks.append({
            "name": "occupied-slot-contract", "repository_id": app_repo["id"], "category": "UNIT",
            "command": ["python", "-I", "-c",
                        "import sys;sys.path.insert(0,'.');from src.reservations import is_available;assert is_available('occupied') is False"],
        })
    upstream = file_ref(root, handoff_path.relative_to(root).as_posix(), "R1")
    request = {
        "run_id": args.run_id, "change_id": change_id,
        "summary": "Implement or repair approved resource reservation behavior",
        "authority_mode": "FEATURE_DELIVERY",
        "repositories": [{"id": app_repo["id"], "role": "IMPLEMENTATION", "base_revision": base_revision,
                           "allowed_write_paths": ["src", "tests"], "read_only_evidence_paths": []}],
        "repository_roots": {app_repo["id"]: str(app_root)}, "checks": checks,
        "upstream": upstream,
    }
    foundation_receipt = read_ref(root, handoff["project_foundation"]["approval"])
    foundation_host_path = root / ".sdlc/phase9-evidence/foundation-human-host.json"
    foundation_decision_path = root / ".sdlc/phase9-evidence/foundation-human-decision.txt"
    foundation_auth = lambda actor, actual: _host_auth(actor, foundation_receipt, foundation_host_path, foundation_decision_path) and actual == foundation_receipt
    runtime = runtime_module.DevRuntime(root, ba_authenticator=ba_auth,
                                        foundation_authenticator=foundation_auth)
    state = runtime.start(request)
    state = runtime.validate_authority()
    if state["authority_mode"] != "FEATURE_DELIVERY":
        raise AssertionError("Dev flow must use normal FEATURE_DELIVERY authority")
    impact = {
        "schema_version": 2, "change_id": state["change_id"], "upstream_ref": state["upstream"],
        "repository_base_revisions": {row["id"]: row["base_revision"] for row in state["repositories"]},
        "affected_repositories": copy.deepcopy(state["repositories"]), "affected_components": ["reservation behavior"],
        "affected_interfaces": ["is_available(slot)"], "affected_data": [], "dependencies": [], "constraints": [],
        "risk": copy.deepcopy(state["risk"]), "technical_unknowns": [], "upstream_gaps": [],
        "write_scope": {row["id"]: row["allowed_write_paths"] for row in state["repositories"]},
        "knowledge_impact": copy.deepcopy(handoff["knowledge_impact"]),
    }
    runtime.impact(impact)
    plan_path = root / ".sdlc/phase9-inputs" / f"{args.run_id}-plan.md"
    tasks_path = root / ".sdlc/phase9-inputs" / f"{args.run_id}-tasks.md"
    plan_path.write_text("Preserve BA WHAT; choose the implementation details for the slot operation.\n", encoding="utf-8")
    tasks_path.write_text("Update the implementation, review the change, then run fresh repository-scoped checks.\n", encoding="utf-8")
    runtime.plan(plan_path, tasks_path, revision=f"PLAN-{args.run_id}")
    if runtime.technical_gate_required():
        raise AssertionError("neutral local behavior change unexpectedly requires a technical approval gate")
    runtime.implementation_ready()
    runtime.begin_implementation()
    runtime.write_source(app_repo["id"], "src/reservations.py", source_text)
    git(app_root, "add", "src/reservations.py")
    git(app_root, "commit", "--quiet", "-m", "Implement approved reservation behavior" if initial else "Fix occupied-slot reservation behavior")
    review_path = root / ".sdlc/phase9-evidence" / f"{args.run_id}-review.json"
    write_json(review_path, {"review": "TEST_ONLY consolidated review", "findings": []})
    runtime.record_review([runtime.reference(review_path.relative_to(root).as_posix())])
    verification = runtime.verify()
    if not verification.get("checks") or any(row.get("status") != "PASS" or row.get("exit_code") != 0 for row in verification["checks"]):
        raise AssertionError(f"Dev fresh repository-scoped verification failed: {verification}")
    code_ref = runtime.reference(f"{app_repo['path']}/src/reservations.py")
    test_ref = runtime.reference(f"{app_repo['path']}/tests/test_contract_shape.py")
    coverage = [{"id": identifier, "status": "COVERED", "code_refs": [code_ref], "test_refs": [test_ref]}
                for identifier in BA_IDS]
    dev_handoff = runtime.finalize(coverage)
    if dev_handoff.get("state") != "READY_FOR_TEST" or dev_handoff.get("verified"):
        raise AssertionError("Dev may publish only READY_FOR_TEST")
    path = Path(runtime.run_directory) / "dev-handoff.json"
    if args.output_handoff:
        target = Path(args.output_handoff)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        path = target
    result = {
        "state": dev_handoff["state"], "change_id": dev_handoff["change_id"],
        "application_repository": app_repo["id"], "application_sha": git(app_root, "rev-parse", "HEAD"),
        "handoff_path": path.relative_to(root).as_posix(), "handoff_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "requirements_coverage": [row["id"] for row in dev_handoff["requirements_coverage"]],
        "verification": "PASS", "authority_mode": dev_handoff["authority_mode"],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def manual_automation_execution_stage(args):
    root = Path(args.workspace).resolve()
    skills = Path(args.skills).resolve()
    runtime_root = skills / ".test-kit"
    scripts = runtime_root / "ba-workflow/scripts"
    foundation_payload = Path(args.framework_root).resolve() / "project-foundation/scripts/shared-sdlc-core.zip"
    modules = import_installed_modules(runtime_root, (
        "tooling.lib.test_kit_vnext", "tooling.lib.test_kit_v1", "tooling.lib.test_kit_v1_cases",
        "tooling.lib.test_automation_v1", "tooling.lib.test_execution_vnext",
        "ba_vnext", "ba_contracts", "shared.sdlc.schema", "shared.sdlc.foundation.workflow",
    ), (foundation_payload, scripts))
    test_vnext = modules["tooling.lib.test_kit_vnext"]
    test_v1 = modules["tooling.lib.test_kit_v1"]
    cases = modules["tooling.lib.test_kit_v1_cases"]
    automation_module = modules["tooling.lib.test_automation_v1"]
    execution_module = modules["tooling.lib.test_execution_vnext"]
    topology = read_json(root / ".sdlc/project-topology.yml")
    policy = read_json(root / ".sdlc/project-policy.yml")
    app_repo = repository_for_role(topology, "application_implementation")
    automation_repo = repository_for_role(topology, policy["testing"]["automation_repository_role"])
    repo_roots = {row["id"]: root / row["path"] for row in topology["repositories"]}
    app_root, automation_root = repo_roots[app_repo["id"]], repo_roots[automation_repo["id"]]
    handoff_path = Path(args.ba_handoff).resolve()
    handoff = read_json(handoff_path)
    ba_receipt = read_ref(root, handoff["approval_receipt"])
    ba_host_path = root / ".sdlc/phase9-evidence/ba-human-host.json"
    ba_decision_path = root / "project-docs/features" / FEATURE_ID / "human-decision.txt"
    ba_auth = lambda actor, actual: _host_auth(actor, ba_receipt, ba_host_path, ba_decision_path) and actual == ba_receipt
    foundation_receipt = read_ref(root, handoff["project_foundation"]["approval"])
    foundation_host_path = root / ".sdlc/phase9-evidence/foundation-human-host.json"
    foundation_decision_path = root / ".sdlc/phase9-evidence/foundation-human-decision.txt"
    foundation_auth = lambda actor, actual: _host_auth(actor, foundation_receipt, foundation_host_path, foundation_decision_path) and actual == foundation_receipt

    authority = test_vnext.load_vnext_authority(
        handoff_path, project_root=root, human_actor_authenticator=ba_auth,
        foundation_authenticator=foundation_auth,
    )
    if authority.vnext_authority is not True or not set(BA_IDS) <= authority.baseline.coverage_ids:
        raise AssertionError("Test VNext did not consume the exact Human-approved BA VNext authority")
    if any(value.startswith("BAREF:") for value in authority.baseline.coverage_ids):
        raise AssertionError("BAREF cannot be a canonical downstream requirement identity")

    # A legacy BA V1 handoff can be inspected for compatibility but has no VNext authority.
    legacy_path = Path(args.framework_root).resolve() / "tooling/tests/fixtures/ba-v1-legacy-compat/05-engineering-handoff.yml"
    legacy = modules["ba_contracts"].read_handoff(legacy_path)
    if legacy.get("mode") != "LEGACY_COMPAT" or legacy.get("vnext_approval") is not False:
        raise AssertionError("legacy BA V1 unexpectedly gained VNext authority")
    try:
        test_vnext.load_vnext_authority(legacy_path, project_root=Path(args.framework_root).resolve())
    except Exception:
        legacy_blocked = True
    else:
        legacy_blocked = False
    if not legacy_blocked:
        raise AssertionError("legacy BA V1 entered the public VNext flow")

    stale_handoff = copy.deepcopy(handoff)
    stale_handoff["approval_receipt"] = {**stale_handoff["approval_receipt"], "sha256": "f" * 64}
    stale_handoff_path = root / "project-docs/features" / FEATURE_ID / "stale-engineering-handoff.json"
    write_json(stale_handoff_path, stale_handoff)
    try:
        test_vnext.load_vnext_authority(stale_handoff_path, project_root=root, human_actor_authenticator=ba_auth)
    except Exception:
        stale_ba_rejected = True
    else:
        stale_ba_rejected = False
    if not stale_ba_rejected:
        raise AssertionError("downstream Test VNext accepted a stale BA Human receipt")
    stale_handoff_path.unlink(missing_ok=True)

    dev_handoff_path = Path(args.dev_handoff).resolve()
    dev_context = {"project_root": str(root), "handoff_path": str(dev_handoff_path)}
    design_run = root / ".test-kit/runs" / FEATURE_ID / "phase9-design"
    design_host_path = root / ".sdlc/phase9-evidence/test-design-host.json"
    prepared_design = test_vnext.prepare_vnext_design(
        handoff_path, design_run, project_root=root,
        skill_dir=skills / "bmad-testarch-test-design",
        human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
    )
    Path(prepared_design["raw_output_path"]).write_text("\n".join((
        "# Test Design: Resource reservation",
        "## Test Coverage Plan", "### P0 - Critical", "None.", "### P1 - High",
        "| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |",
        "|---|---|---|---|---|---|",
        "| TD-001 | Request an occupied slot | API | - | BR-RSV-001; FR-RSV-001 | The request returns unavailable and the slot remains occupied. |",
        "| TD-002 | Check the local availability result type | UNIT | - | FR-RSV-001 | The availability result is a boolean. |",
        "### P2 - Medium", "None.", "### P3 - Low", "None.", "",
    )), encoding="utf-8")
    design_final = test_vnext.finalize_vnext_design(
        handoff_path, design_run, human_actor_authenticator=ba_auth,
        foundation_authenticator=foundation_auth,
    )
    if design_final.get("status") != "DESIGN_REVIEW":
        raise AssertionError(f"Test Design did not stop at DESIGN_REVIEW: {design_final}")
    design_workflow = read_json(design_run / "workflow-state.json")
    if design_workflow.get("validation_status") != "PASS":
        raise AssertionError("Test Design validation did not pass")
    design_snapshot = test_v1.load_persisted_design_snapshot(design_run, require_state="DESIGN_REVIEW")
    design_receipt = {
        "gate": "DESIGN_REVIEW", "decision": "APPROVE", "artifact_id": design_snapshot.artifact_id,
        "artifact_revision": design_snapshot.revision, "artifact_sha256": design_snapshot.sha256,
        "input_refs": test_vnext.design_gate_input_refs(design_run, authority.baseline),
        "actor_id": TEST_ONLY_ACTOR, "actor_role": "HUMAN",
        "decided_at": "2026-10-05T00:10:00Z", "feedback": "",
    }
    write_json(design_host_path, {
        "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT",
        "not_for_production": True, "receipt": design_receipt,
    })
    design_without_human = test_vnext.apply_vnext_design_decision(
        design_run, design_receipt, human_actor_authenticator=None,
        ba_human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
    )
    if design_without_human.accepted:
        raise AssertionError("validator PASS replaced the Test Design Human Gate")
    design_approved = test_vnext.apply_vnext_design_decision(
        design_run, design_receipt, human_actor_authenticator=None,
        ba_human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
        test_only_fixture_path=design_host_path,
    )
    if not design_approved.accepted or design_approved.state.state != "APPROVED_DESIGN":
        raise AssertionError(f"TEST_ONLY Human Design approval failed: {design_approved}")

    case_run = root / ".test-kit/runs" / FEATURE_ID / "phase9-cases"
    case_host_path = root / ".sdlc/phase9-evidence/test-case-host.json"
    prepared_cases = test_vnext.prepare_test_only_vnext_cases(
        handoff_path, design_run, case_run, project_root=root,
        skill_dir=skills / "create-test-cases", ba_human_actor_authenticator=ba_auth,
        foundation_authenticator=foundation_auth,
        test_only_design_fixture_path=design_host_path, dev_context=dev_context,
    )
    Path(prepared_cases["raw_output_path"]).write_text("\n".join((
        "# Manual Test Cases", "",
        "## TC-001 Request an occupied slot", "",
        "- Mô tả: Confirm an occupied resource slot cannot be reserved again.",
        "- Tiền điều kiện: The target slot is occupied.",
        "- Bước và kết quả mong đợi:",
        "  1. Request the occupied slot. → The response is unavailable and the slot remains occupied.",
        "- Test Data: occupied slot", "- Priority: P1.", "- Trace: BR-RSV-001; FR-RSV-001; TD-001", "",
        "## TC-002 Check the local availability result type", "",
        "- Mô tả: Check the local availability result type.",
        "- Tiền điều kiện: A slot identifier is available.",
        "- Bước và kết quả mong đợi:",
        "  1. Read the availability result. → The result is a boolean.",
        "- Test Data: occupied slot", "- Priority: P1.", "- Trace: FR-RSV-001; TD-002", "",
    )), encoding="utf-8")
    cases_final = test_vnext.finalize_test_only_vnext_cases(
        handoff_path, case_run, test_only_design_fixture_path=design_host_path,
        ba_human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
    )
    if cases_final.status != "CASE_REVIEW":
        raise AssertionError(f"Testcases did not stop at CASE_REVIEW: {cases_final}")
    case_workflow = read_json(case_run / "workflow-state.json")
    if case_workflow.get("validation_status") != "PASS":
        raise AssertionError("Testcase validation did not pass")
    case_snapshot, case_state = cases.load_case_review_snapshot(
        case_run / "canonical/canonical-testcases.json", case_run / "workflow-state.json",
        case_run / "canonical/semantic-payload.json",
    )
    approved_design = test_v1.load_persisted_design_snapshot(design_run, require_state="APPROVED_DESIGN")
    gate_refs = cases.case_gate_input_refs(
        authority.baseline, approved_design, run_dir=case_run,
        execution_contract_refs=case_state.execution_oracle_refs,
        case_snapshot=case_snapshot, vnext_authority=True,
    )
    case_receipt = {
        "gate": "CASE_REVIEW", "decision": "APPROVE", "artifact_id": case_snapshot.artifact_id,
        "artifact_revision": case_snapshot.revision, "artifact_sha256": case_snapshot.sha256,
        "input_refs": gate_refs, "actor_id": TEST_ONLY_ACTOR, "actor_role": "HUMAN",
        "decided_at": "2026-10-05T00:15:00Z", "feedback": "",
    }
    write_json(case_host_path, {
        "fixture_type": "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT",
        "not_for_production": True, "receipt": case_receipt,
    })
    rejected_case_gate = test_vnext.apply_vnext_case_decision(
        case_run, case_receipt, human_actor_authenticator=None,
        ba_human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
    )
    if rejected_case_gate.status == "APPROVED_TESTWARE":
        raise AssertionError("Case validator PASS replaced the authenticated Human Gate")
    approved_case_gate = test_vnext.apply_vnext_case_decision(
        case_run, case_receipt, human_actor_authenticator=None,
        ba_human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
        test_only_fixture_path=case_host_path,
    )
    if approved_case_gate.status != "APPROVED_TESTWARE":
        raise AssertionError(f"TEST_ONLY Human Case approval failed: {approved_case_gate}")
    case_workflow = read_json(case_run / "workflow-state.json")
    approved_envelope = read_json(case_run / "approved-testware-vnext.json")
    approved_testware = approved_envelope["approved_testware"]
    if (approved_envelope.get("not_for_production") is not True or approved_testware.get("state") != "APPROVED_TESTWARE"
            or "delivery_manifest" in approved_testware):
        raise AssertionError("Approved Testware authority or TEST_ONLY classification is invalid")
    if set(approved_testware["trace_summary"]["requirement_ids"]) != set(BA_IDS):
        raise AssertionError("Approved Testware lost canonical BA BR/FR trace")
    if len(case_snapshot.records) != 2:
        raise AssertionError("Approved Testware must retain the automated and Dev-local testcase records")
    approved_testware_sha = hashlib.sha256((case_run / "approved-testware-vnext.json").read_bytes()).hexdigest()

    stale_receipt_evidence = case_workflow.get("case_gate_receipt_evidence")
    if not stale_receipt_evidence:
        raise AssertionError("approved Test gate lacks exact receipt evidence")
    stale_receipt_path = Path(stale_receipt_evidence["path"]).resolve()
    stale_bytes = stale_receipt_path.read_bytes()
    stale_receipt_path.write_bytes(stale_bytes + b"\n")

    test_receipts = [design_receipt, case_receipt]
    def test_human(actor, actual):
        if actor == TEST_ONLY_ACTOR and any(actual == row for row in test_receipts):
            return test_v1.AuthenticatedHumanActorContext(actor)
        return None

    def test_only_authority_authenticator(test_run_dir, envelope):
        try:
            test_run_dir = Path(test_run_dir).resolve()
            if (not test_run_dir.is_relative_to(root.resolve())
                    or envelope.get("fixture_type") != "TEST_ONLY_APPROVED_TESTWARE_EVIDENCE"
                    or envelope.get("not_for_production") is not True
                    or read_json(test_run_dir / "approved-testware-vnext.json") != envelope):
                return False
            case_state = read_json(test_run_dir / "workflow-state.json")
            case_evidence = case_state["case_gate_receipt_evidence"]
            design_evidence = case_state["design_gate_receipt_evidence"]
            case_receipt_path = Path(case_evidence["path"]).resolve()
            design_receipt_path = Path(design_evidence["path"]).resolve()
            if (not case_receipt_path.is_relative_to(root.resolve())
                    or not design_receipt_path.is_relative_to(root.resolve())):
                return False
            design_run = design_receipt_path.parents[3]
            design_state = read_json(design_run / "workflow-state.json")
            case_receipt = read_json(case_receipt_path)
            design_receipt = read_json(design_receipt_path)
            case_host_path = root / ".sdlc/phase9-evidence/test-case-host.json"
            design_host_path = root / ".sdlc/phase9-evidence/test-design-host.json"
            case_host = read_json(case_host_path)
            design_host = read_json(design_host_path)
            authenticated = (
                case_state.get("test_only") is True
                and case_state.get("case_gate_receipt_mode") == "TEST_ONLY"
                and case_state.get("design_gate_receipt_mode") == "TEST_ONLY"
                and design_state.get("state") == "APPROVED_DESIGN"
                and hashlib.sha256(case_receipt_path.read_bytes()).hexdigest() == case_evidence["sha256"]
                and hashlib.sha256(design_receipt_path.read_bytes()).hexdigest() == design_evidence["sha256"]
                and design_evidence.get("fixture", {}).get("path") == str(design_host_path.resolve())
                and design_evidence.get("fixture", {}).get("sha256") == hashlib.sha256(design_host_path.read_bytes()).hexdigest()
                and case_host.get("fixture_type") == "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT"
                and case_host.get("not_for_production") is True
                and case_host.get("receipt") == case_receipt
                and design_host.get("fixture_type") == "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT"
                and design_host.get("not_for_production") is True
                and design_host.get("receipt") == design_receipt
                and case_receipt.get("actor_id", "").startswith("TEST_ONLY:")
                and design_receipt.get("actor_id", "").startswith("TEST_ONLY:")
            )
            if not authenticated:
                return False
            return {"authenticated": True, "case_gate_fixture_path": str(case_host_path.resolve())}
        except (OSError, ValueError, KeyError, TypeError):
            return False

    runtime_root = runtime_root.resolve()
    def new_automation(run_id, roots=None):
        return automation_module.AutomationRuntime(
            root, root / ".test-kit/automation/runs" / run_id,
            human_actor_authenticator=test_human,
            ba_human_actor_authenticator=ba_auth,
            foundation_authenticator=foundation_auth,
            test_only_authority_authenticator=test_only_authority_authenticator,
            repository_roots=roots or repo_roots,
        )

    untrusted_test_only = automation_module.AutomationRuntime(
        root, root / ".test-kit/automation/runs/untrusted-test-only",
        human_actor_authenticator=test_human, ba_human_actor_authenticator=ba_auth,
        foundation_authenticator=foundation_auth, repository_roots=repo_roots,
    )
    try:
        untrusted_test_only.start(case_run)
    except automation_module.AutomationV1Error as error:
        test_only_without_host_rejected = error.code == "TEST_ONLY_AUTHORITY_FORBIDDEN"
    else:
        test_only_without_host_rejected = False
    if not test_only_without_host_rejected:
        raise AssertionError("Automation accepted TEST_ONLY Testware without its trusted host authenticator")

    try:
        stale_runtime = new_automation("stale-test-gate")
        stale_runtime.start(case_run)
    except Exception:
        stale_test_receipt_rejected = True
    else:
        stale_test_receipt_rejected = False
    finally:
        stale_receipt_path.write_bytes(stale_bytes)
    if not stale_test_receipt_rejected:
        raise AssertionError("Automation accepted stale Test Gate receipt bytes")

    testware_path = case_run / "approved-testware-vnext.json"
    testware_hash_before = hashlib.sha256(testware_path.read_bytes()).hexdigest()
    before_app_sha = git(app_root, "rev-parse", "HEAD")
    before_automation_sha = git(automation_root, "rev-parse", "HEAD")
    auto_runtime = new_automation("phase9-automation")
    try:
        auto_runtime.start(case_run)
    except automation_module.AutomationV1Error as error:
        raise RuntimeError(f"Automation intake failed: {error.code}; cause={error.__cause__!r}") from error
    assessment_rows = [
        {"testcase_id": "TC-001", "classification": "API", "required": True,
         "rationale": "Run the approved occupied-slot oracle against the application repository."},
        {"testcase_id": "TC-002", "classification": "UNIT", "required": True,
         "rationale": "Retain the exact Dev-local reference from the approved Testcase."},
    ]
    suitability = auto_runtime.analyze_suitability(assessment_rows)

    # Resolve both repository roots from topology and derive the relative read-only app argument.
    relative_app = os.path.relpath(app_root, automation_root).replace("\\", "/")
    automation_source = "\n".join((
        "import pathlib, sys",
        "app_root = pathlib.Path(sys.argv[1]).resolve()",
        "sys.path.insert(0, str(app_root))",
        "from src.reservations import is_available",
        "assert is_available('occupied') is False, 'occupied slot was reported available'",
        "",
    ))
    automation_plan_spec = {
        "TC-001": {
            "suite": "reservation-availability", "planned_paths": ["tests/test_reservation.py"],
            "runner": "project-native",
            "execution_command": ["python", "-I", "tests/test_reservation.py", relative_app],
            "verification_commands": [{"category": "SYNTAX", "argv": [
                "python", "-I", "-m", "py_compile", "tests/test_reservation.py",
            ]}],
        },
    }
    planned_state = auto_runtime.plan(automation_plan_spec)
    plan = read_ref(root, planned_state["plan_ref"])
    aut_item = next(row for row in plan["items"] if "TC-001" in row["testcase_refs"])
    implementation_ready = auto_runtime.begin_implementation()
    automation_base_sha = implementation_ready["implementation_base_revision"]
    try:
        auto_runtime.write_source(aut_item["aut_id"], app_repo["id"], "src/reservations.py",
                                 "unauthorized\n", base_revision=automation_base_sha)
    except automation_module.AutomationV1Error as error:
        initial_auto_refusal = error.code == "APP_REPOSITORY_WRITE_FORBIDDEN"
    else:
        initial_auto_refusal = False
    if not initial_auto_refusal:
        raise AssertionError("Test Automation app write was not rejected by repository ownership")
    if git(app_root, "rev-parse", "HEAD") != before_app_sha:
        raise AssertionError("Test Automation changed the application revision")
    auto_runtime.write_source(aut_item["aut_id"], automation_repo["id"], "tests/test_reservation.py",
                             automation_source, base_revision=automation_base_sha)
    git(automation_root, "add", "tests/test_reservation.py")
    git(automation_root, "commit", "--quiet", "-m", "Implement approved reservation automation")
    implementation = auto_runtime.record_implementation()
    review_checks = {name: True for name in automation_module.REVIEW_CHECKS}
    auto_runtime.record_review({"reviewer": "TEST_ONLY-synthetic-reviewer", "checks": review_checks, "findings": []})
    auto_runtime.verify()
    verification_record = read_ref(root, auto_runtime.status()["verification_ref"])
    if verification_record.get("status") != "PASS":
        raise AssertionError(f"Automation-only verification did not PASS: {verification_record}")
    if verification_record.get("product_execution") != "NOT_RUN":
        raise AssertionError("Automation verification claimed a product execution result")
    execution_ready = auto_runtime.finalize(dev_handoff_path)
    if execution_ready.get("lifecycle") != "EXECUTION_READY" or not execution_ready.get("handoff_ref"):
        raise AssertionError("Automation did not publish EXECUTION_READY")
    if auto_runtime.revalidate_handoff().get("state") != "EXECUTION_READY":
        raise AssertionError("Automation V1 handoff did not revalidate")
    automation_sha = git(automation_root, "rev-parse", "HEAD")
    if auto_runtime.status()["implementation"]["repository_revision"] != automation_sha:
        raise AssertionError("EXECUTION_READY does not bind exact committed automation revision")
    if before_automation_sha == automation_sha:
        raise AssertionError("automation repository did not receive its own committed revision")

    topology_path = root / ".sdlc/project-topology.yml"
    original_topology = topology_path.read_bytes()
    ambiguous = copy.deepcopy(topology)
    ambiguous["repositories"].append({
        "id": "alternate-automation", "path": "alternate-automation",
        "repository": "example/resource-reservation-alternate-automation", "role": "project_test_automation",
    })
    write_json(topology_path, ambiguous)
    try:
        new_automation("ambiguous-automation").start(case_run)
    except Exception as error:
        ambiguous_automation_rejected = "AMBIGUOUS" in str(error).upper()
    else:
        ambiguous_automation_rejected = False
    finally:
        topology_path.write_bytes(original_topology)
    if not ambiguous_automation_rejected:
        raise AssertionError("ambiguous automation repository role was not rejected")

    tester_host_path = root / ".sdlc/phase9-evidence/tester-host.json"
    tester_id = "TEST_ONLY-synthetic-tester"
    write_json(tester_host_path, {
        "fixture_type": "TEST_ONLY_AUTHENTICATED_TESTER", "not_for_production": True,
        "actor_id": tester_id, "role": "TESTER",
    })
    tester_host = read_json(tester_host_path)
    def tester_auth(actor, request):
        if (tester_host.get("not_for_production") is True and actor == tester_host.get("actor_id")
                and request.get("role") == "TESTER" and request.get("action")):
            return {"authenticated": True, "actor_id": actor, "role": "TESTER"}
        return None

    def new_execution(execution_id, automation_run_id="phase9-automation"):
        return execution_module.ExecutionRuntime(
            root, root / ".test-kit/automation/runs" / automation_run_id, execution_id,
            tester_authenticator=tester_auth, human_actor_authenticator=test_human,
            ba_human_actor_authenticator=ba_auth, foundation_authenticator=foundation_auth,
            repository_roots=repo_roots,
            test_only_authority_authenticator=test_only_authority_authenticator,
        )

    def prepare_straight_automation(dev_ready_handoff):
        runtime = new_automation("phase9-straight-automation")
        runtime.start(case_run)
        runtime.analyze_suitability(assessment_rows)
        planned = runtime.plan(automation_plan_spec)
        plan = read_ref(root, planned["plan_ref"])
        item = next(row for row in plan["items"] if "TC-001" in row["testcase_refs"])
        implementation_ready = runtime.begin_implementation()
        runtime.write_source(
            item["aut_id"], automation_repo["id"], "tests/test_reservation.py",
            automation_source + "# Rebound to the exact fixed Dev revision.\n",
            base_revision=implementation_ready["implementation_base_revision"],
        )
        git(automation_root, "add", "tests/test_reservation.py")
        git(automation_root, "commit", "--quiet", "-m", "Rebind automation to fixed application revision")
        runtime.record_implementation()
        runtime.record_review({
            "reviewer": "TEST_ONLY-straight-pass-reviewer",
            "checks": {name: True for name in automation_module.REVIEW_CHECKS}, "findings": [],
        })
        runtime.verify()
        verification = read_ref(root, runtime.status()["verification_ref"])
        if verification.get("status") != "PASS" or verification.get("product_execution") != "NOT_RUN":
            raise AssertionError("straight-pass Automation V1 verification must PASS without a product result")
        ready = runtime.finalize(dev_ready_handoff)
        if ready.get("lifecycle") != "EXECUTION_READY" or not ready.get("handoff_ref"):
            raise AssertionError("straight-pass Automation V1 did not publish EXECUTION_READY")
        handoff = runtime.revalidate_handoff()
        dev_ready = read_json(dev_ready_handoff)
        if handoff.get("application_revisions") != dev_ready.get("repository_revisions"):
            raise AssertionError("straight-pass EXECUTION_READY does not bind the exact fixed Dev revision")
        revision = git(automation_root, "rev-parse", "HEAD")
        if runtime.status()["implementation"]["repository_revision"] != revision:
            raise AssertionError("straight-pass EXECUTION_READY does not bind the exact automation revision")
        return item, revision

    environment = {
        "schema_version": 1, "artifact_class": "CANONICAL", "environment_id": "local-test-only",
        "profile": "synthetic-local", "configuration_refs": [], "evidence_refs": [],
    }
    app_sha = git(app_root, "rev-parse", "HEAD")
    revision_probe_results = {}
    for label, changed_root, app_change in (("wrong-app-revision", app_root, True),
                                            ("wrong-automation-revision", automation_root, False)):
        original_sha = git(changed_root, "rev-parse", "HEAD")
        drift = changed_root / ".conformance-revision-probe"
        drift.write_text("unapproved repository revision\n", encoding="utf-8")
        git(changed_root, "add", ".conformance-revision-probe")
        git(changed_root, "commit", "--quiet", "-m", "Temporary wrong revision negative probe")
        try:
            new_execution(label).start(environment)
        except Exception:
            rejected = True
        else:
            rejected = False
        git(changed_root, "reset", "--hard", original_sha)
        if drift.exists():
            drift.unlink()
        revision_probe_results["wrong_app_revision_rejected" if app_change else "wrong_automation_revision_rejected"] = rejected
        if not rejected:
            raise AssertionError(f"execution accepted wrong {('application' if app_change else 'automation')} revision")
    if git(app_root, "rev-parse", "HEAD") != app_sha:
        raise AssertionError("negative revision probe did not restore the exact Dev revision")

    defect_execution = new_execution("phase9-defect-execution")
    try:
        defect_execution.start(environment)
    except execution_module.ExecutionVNextError as error:
        cause = error.__cause__
        nested = getattr(cause, "__cause__", None)
        raise RuntimeError(f"Execution start failed: {error.code}; cause={cause!r}; nested={nested!r}") from error
    defect_state = defect_execution.execute_automated()
    if defect_state["finding_refs"] or defect_state["defect_handoffs"]:
        raise AssertionError("command failure automatically created a Finding or Defect")
    aut_id = aut_item["aut_id"]
    failed_command_ref = defect_state["command_evidence_refs"][aut_id]
    failed_command = read_ref(root, failed_command_ref)
    if failed_command.get("status") != "COMMAND_FAIL":
        raise AssertionError(f"approved product command did not reproduce the expected mismatch: {failed_command}")
    try:
        defect_execution.finalize_verified(actor_id="TEST_ONLY-developer").get("state")
    except Exception:
        dev_verified_rejected = True
    else:
        dev_verified_rejected = False
    if not dev_verified_rejected:
        raise AssertionError("Dev identity reached Tester VERIFIED")

    finding_result = defect_execution.record_observation(
        testcase_id="TC-001", aut_id=aut_id, outcome="FINDING",
        actual_summary="The occupied slot was reported available by the approved application revision.",
        evidence_refs=[failed_command_ref], actor_id=tester_id,
    )
    finding_id = next(iter(defect_execution.state["finding_refs"]))
    if defect_execution.state["classification_refs"] or defect_execution.state["defect_handoffs"]:
        raise AssertionError("Tester Observation created a Defect without explicit classification")
    proof = {
        "reproducible": True, "deterministic": True, "environment_root_cause_excluded": True,
        "test_issue_excluded": True, "mismatch_evidence_refs": [failed_command_ref],
    }
    classification = defect_execution.classify_finding(
        finding_id, "DEFECT", actor_id=tester_id,
        rationale="The approved oracle and deterministic mismatch are bound to the exact execution.",
        evidence_refs=[failed_command_ref], target_repository_ids=[app_repo["id"]], defect_proof=proof,
    )
    defect_handoff = read_ref(root, classification["defect_handoff_ref"])
    defect_id = defect_handoff["defect_id"]
    initial_dev_handoff_path = dev_handoff_path
    try:
        defect_execution.accept_dev_fix(defect_id, initial_dev_handoff_path)
    except Exception:
        stale_original_dev_rejected = True
    else:
        stale_original_dev_rejected = False
    if not stale_original_dev_rejected:
        raise AssertionError("execution accepted the original pre-defect Dev handoff as a fix")

    fix_handoff_path = root / ".sdlc/phase9-evidence" / "ready-for-retest-dev-handoff.json"
    fix_command = [sys.executable, "-I", str(Path(__file__).resolve()), "--stage", "dev",
                   "--framework-root", str(Path(args.framework_root).resolve()),
                   "--workspace", str(root), "--dev-runtime", args.dev_runtime,
                   "--ba-handoff", str(handoff_path), "--change-id", defect_id,
                   "--run-id", "DEV-" + defect_id, "--kind", "fix", "--output-handoff", str(fix_handoff_path),
                   "--external-cwd", str(Path(args.external_cwd).resolve()),
                   "--output", str(root / ".sdlc/phase9-evidence/dev-fix-stage.json")]
    fixed = subprocess.run(fix_command, cwd=args.external_cwd, env=dict(os.environ), capture_output=True,
                           text=True, timeout=240)
    if fixed.returncode:
        raise RuntimeError("Dev VNext defect fix failed: " + (fixed.stderr or fixed.stdout))
    fix_summary = json.loads(fixed.stdout.strip().splitlines()[-1])
    if fix_summary["change_id"] != defect_id or fix_summary["state"] != "READY_FOR_TEST":
        raise AssertionError("Dev defect fix did not use change_id=defect_id and READY_FOR_TEST")
    ready_for_retest = defect_execution.accept_dev_fix(defect_id, fix_handoff_path)
    ready_for_retest_artifact = read_ref(root, ready_for_retest["ready_for_retest_ref"])
    if ready_for_retest_artifact.get("state") != "READY_FOR_RETEST":
        raise AssertionError("exact Dev VNext fix did not create READY_FOR_RETEST")
    retest_command = defect_execution.execute_retest(defect_id)
    if retest_command.get("command_status") != "COMMAND_PASS":
        raise AssertionError(f"Test retest did not pass on the exact fixed app revision: {retest_command}")
    retest_result = defect_execution.record_retest_observation(
        defect_id, outcome="PASS", actual_summary="The occupied slot now returns unavailable.",
        evidence_refs=[retest_command["command_evidence_ref"]], actor_id=tester_id,
    )
    if retest_result.get("state") != "VERIFIED":
        raise AssertionError("Tester retest did not complete VERIFIED")
    verified_retest = defect_execution.revalidate_verified()
    if verified_retest.get("state") != "VERIFIED":
        raise AssertionError("verified defect cycle did not revalidate")

    straight_item, straight_automation_sha = prepare_straight_automation(fix_handoff_path)
    straight_execution = new_execution(
        "phase9-straight-execution", automation_run_id="phase9-straight-automation",
    )
    straight_execution.start(environment)
    straight_state = straight_execution.execute_automated()
    straight_aut_id = straight_item["aut_id"]
    straight_command_ref = straight_state["command_evidence_refs"][straight_aut_id]
    straight_command = read_ref(root, straight_command_ref)
    if straight_command.get("status") != "COMMAND_PASS":
        raise AssertionError("straight-pass scenario did not execute cleanly")
    straight_execution.record_observation(
        testcase_id="TC-001", aut_id=straight_aut_id, outcome="PASS",
        actual_summary="The approved testcase result was observed on the clean fixed revision.",
        evidence_refs=[straight_command_ref], actor_id=tester_id,
    )
    straight_verified = straight_execution.finalize_verified(actor_id=tester_id)
    if straight_verified.get("state") != "VERIFIED" or straight_execution.revalidate_verified().get("state") != "VERIFIED":
        raise AssertionError("straight clean execution did not reach Tester VERIFIED")

    app_sha_after = git(app_root, "rev-parse", "HEAD")
    if (app_sha_after == app_sha or automation_sha == before_automation_sha
            or straight_automation_sha == automation_sha
            or git(automation_root, "rev-parse", "HEAD") != straight_automation_sha):
        raise AssertionError("defect and straight-pass repository revisions were not preserved separately")
    if hashlib.sha256(testware_path.read_bytes()).hexdigest() != testware_hash_before:
        raise AssertionError("Approved Testware oracle changed during the defect fix")

    revision_reproduction = {}
    for label, repository_id, repo_path, expected_sha in (
        ("docs", "docs", root / "project-docs", git(root / "project-docs", "rev-parse", "HEAD")),
        ("application", app_repo["id"], app_root, app_sha_after),
        ("automation_defect_path", automation_repo["id"], automation_root, automation_sha),
        ("automation_straight_pass", automation_repo["id"], automation_root, straight_automation_sha),
    ):
        clone = Path(args.external_cwd) / "revision-checkouts" / label
        clone.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(["git", "clone", "--local", "--no-hardlinks", "--no-checkout", str(repo_path), str(clone)],
                                cwd=args.external_cwd, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("local revision reproduction clone failed: " + result.stderr)
        git(clone, "checkout", "--detach", expected_sha)
        if git(clone, "rev-parse", "HEAD") != expected_sha or git(clone, "status", "--porcelain"):
            raise AssertionError(f"clean clone could not reproduce exact {repository_id} revision")
        revision_reproduction[label] = {
            "repository_id": repository_id, "sha": expected_sha, "clean_checkout": True,
        }

    foundation_manifest = read_json(root / "project-docs/foundation/R1.json")
    trace = {
        "foundation_manifest_sha256": hashlib.sha256((root / "project-docs/foundation/R1.json").read_bytes()).hexdigest(),
        "foundation_provenance_sha256": hashlib.sha256((root / "project-docs/foundation/R1.provenance.json").read_bytes()).hexdigest(),
        "human_ba_receipt_sha256": hashlib.sha256((root / "project-docs/features" / FEATURE_ID / "human-approval-receipt.json").read_bytes()).hexdigest(),
        "br_ids": [BA_IDS[0]], "fr_ids": [BA_IDS[1]],
        "test_design_ids": [row.design_id for row in design_snapshot.records],
        "testcase_ids": [row.test_case_id for row in case_snapshot.records],
        "aut_ids": [row["aut_id"] for row in plan["items"]],
        "automation_path": (Path(automation_repo["path"]) / "tests/test_reservation.py").as_posix(),
        "automation_repository_id": automation_repo["id"], "automation_sha": automation_sha,
        "straight_pass_automation_sha": straight_automation_sha,
        "straight_pass_aut_ids": [straight_item["aut_id"]],
        "failed_command_evidence": failed_command_ref,
        "finding_id": finding_id, "defect_id": defect_id,
        "dev_fix_sha": app_sha_after, "ready_for_retest": ready_for_retest["state"],
        "retest_command_evidence": retest_command["command_evidence_ref"],
        "retest": "PASS", "verified": retest_result["state"],
        "straight_pass_command_evidence": straight_command_ref,
        "straight_pass": straight_verified["state"],
        "app_repository_id": app_repo["id"], "app_sha": app_sha_after,
        "foundation_repo_id": "docs",
        "ba_what_immutable": True,
    }
    if any(str(value).startswith("BAREF:") for value in trace["br_ids"] + trace["fr_ids"]):
        raise AssertionError("trace canonical requirement identity contains BAREF")
    outputs = {
        "status": "PASS",
        "scenario_results": {
            "project_foundation": "PASS", "ba_vnext": "PASS", "dev_vnext": "PASS",
            "test_manual_vnext": "PASS", "automation_v1": "PASS", "execution_vnext": "PASS",
            "defect_fix_retest": "PASS", "straight_pass": "PASS",
        },
        "trace_checks": {"continuous": True, "trace": trace},
        "revision_checks": {"reproduced": True, "repositories": revision_reproduction},
        "installed_isolation": {"status": "PASS", "python_isolated": sys.flags.isolated == 1,
                                 "pythonpath_absent": "PYTHONPATH" not in os.environ,
                                 "runtime_modules": {name: "ISOLATED_INSTALLED_RUNTIME" for name in modules}},
        "negative_probes": {
            "legacy_ba_v1_rejected": legacy_blocked, "validator_not_approval": validator_not_approval,
            "stale_ba_receipt_rejected": stale_ba_rejected,
            "stale_test_gate_receipt_rejected": stale_test_receipt_rejected,
            "delivery_manifest_missing_valid": "delivery_manifest" not in approved_testware,
            "ambiguous_automation_repository_rejected": ambiguous_automation_rejected,
            **revision_probe_results,
            "test_only_without_host_rejected": test_only_without_host_rejected,
            "test_automation_app_write_rejected": initial_auto_refusal,
            "dev_verified_rejected": dev_verified_rejected,
            "command_fail_not_defect": not bool(defect_state["finding_refs"]) and not bool(defect_state["defect_handoffs"]),
        },
    }
    write_json(Path(args.output), outputs)
    print(json.dumps({"status": "PASS", "scenario_results": outputs["scenario_results"]}, sort_keys=True))


def run_all(args):
    framework_root = Path(args.framework_root).resolve()
    if args.spec_kit_cli is None or not Path(args.spec_kit_cli).is_file():
        raise ValueError("public flow requires the explicitly provisioned Spec Kit executable")
    spec_kit_cli = Path(args.spec_kit_cli).resolve()
    version = subprocess.run([str(spec_kit_cli), "--version"], capture_output=True, text=True, timeout=30)
    if version.returncode or version.stdout.strip() != "specify 1.0.11":
        raise ValueError("public flow requires Spec Kit 1.0.11")
    external = Path(args.external_cwd).resolve()
    external.mkdir(parents=True, exist_ok=True)
    workspace = external / "resource-reservation-workspace"
    setup_workspace(workspace)
    skills = workspace / ".agents/skills"
    installer = framework_root / "tooling/lib/ba_kit.py"
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment.pop("CODEX_HOME", None)
    environment["PATH"] = str(spec_kit_cli.parent) + os.pathsep + environment.get("PATH", "")
    for kit in ("ba", "test"):
        result = subprocess.run(
            [sys.executable, "-I", str(installer), "install", kit, "--agent", "generic", "--target", str(skills)],
            cwd=external, env=environment, capture_output=True, text=True, timeout=240,
        )
        if result.returncode:
            raise RuntimeError(f"fresh installed {kit} package setup failed: {result.stderr or result.stdout}")
    dev_home = external / "isolated-dev-home"
    dev_install = subprocess.run(
        [sys.executable, "-I", str(framework_root / "tooling/install_dev_kit.py"),
         "--source-root", str(framework_root), "--install-home", str(dev_home)],
        cwd=external, env=environment, capture_output=True, text=True, timeout=240,
    )
    if dev_install.returncode:
        raise RuntimeError("fresh installed Dev package setup failed: " + (dev_install.stderr or dev_install.stdout))
    dev_runtime = Path(json.loads(dev_install.stdout)["runtime_root"]).resolve()

    def stage(name, **values):
        values.setdefault("output", external / f"{name}-stage.json")
        command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                   "--stage", name, "--framework-root", str(framework_root),
                   "--workspace", str(workspace), "--external-cwd", str(external)]
        for key, value in values.items():
            command.extend(["--" + key.replace("_", "-"), str(value)])
        result = subprocess.run(command, cwd=external, env=environment, capture_output=True,
                                text=True, timeout=900)
        if result.returncode:
            raise RuntimeError(f"installed {name} cross-kit stage failed: {result.stderr or result.stdout}")
        try:
            return json.loads(result.stdout.strip().splitlines()[-1])
        except (IndexError, json.JSONDecodeError) as error:
            raise RuntimeError(f"installed {name} stage emitted no evidence JSON: {result.stdout}") from error

    foundation_ba = stage("foundation-ba", skills=skills)
    ba_handoff = workspace / foundation_ba["ba"]["handoff_path"]
    initial_handoff = workspace / ".devkit/ready-for-test-initial.json"
    initial_dev = stage(
        "dev", skills=skills, dev_runtime=dev_runtime, spec_kit_cli=spec_kit_cli, ba_handoff=ba_handoff,
        change_id=FEATURE_ID, run_id="DEV-INITIAL", kind="initial", output_handoff=initial_handoff,
    )
    flow_output = external / "public-flow-result.json"
    stage("manual-execution", skills=skills, dev_runtime=dev_runtime, ba_handoff=ba_handoff,
          dev_handoff=initial_handoff, spec_kit_cli=spec_kit_cli, output=flow_output)
    result = read_json(flow_output)
    if result.get("status") != "PASS":
        raise AssertionError(f"installed public flow returned non-PASS evidence: {result}")
    result["installed_isolation"]["dev_runtime_root"] = "ISOLATED_TEMPORARY_RUNTIME"
    result["initial_dev"] = initial_dev
    result["foundation_and_ba"] = foundation_ba
    output = Path(args.output).resolve()
    write_json(output, result)
    print(json.dumps({"status": result["status"], "scenario_results": result["scenario_results"]}, sort_keys=True))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Installed public Project Foundation-to-VERIFIED synthetic acceptance")
    parser.add_argument("--stage", choices=("run", "foundation-ba", "dev", "manual-execution"), default="run")
    parser.add_argument("--framework-root", type=Path, required=True)
    parser.add_argument("--spec-kit-cli", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--skills", type=Path)
    parser.add_argument("--dev-runtime", type=Path)
    parser.add_argument("--ba-handoff", type=Path)
    parser.add_argument("--dev-handoff", type=Path)
    parser.add_argument("--change-id")
    parser.add_argument("--run-id")
    parser.add_argument("--kind", choices=("initial", "fix"))
    parser.add_argument("--output-handoff", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--external-cwd", type=Path)
    args = parser.parse_args(argv)
    if args.external_cwd is None:
        args.external_cwd = Path(args.output).resolve().parent
    try:
        if args.stage == "run":
            run_all(args)
        elif args.stage == "foundation-ba":
            foundation_and_ba_stage(args)
        elif args.stage == "dev":
            dev_stage(args)
        else:
            manual_automation_execution_stage(args)
        return 0
    except Exception as error:
        payload = {"status": "FAIL", "error": f"{type(error).__name__}: {error}"}
        if args.stage in {"run", "manual-execution"} and args.output:
            try:
                write_json(Path(args.output), payload)
            except OSError:
                pass
        print(json.dumps(payload, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
