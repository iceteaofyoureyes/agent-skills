"""Test Automation V1: exact Test VNext intake and bounded readiness handoff."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import subprocess
import tempfile
import threading
from datetime import datetime, timezone

from shared.sdlc.schema import (
    identifier,
    portable_path,
    read_document,
    reject_secrets,
    safe_file,
    validate_reference,
)
from shared.sdlc.policy.contract import read_policy
from shared.sdlc.topology.contract import read_topology


AUTOMATION_CLASSES = (
    "UNIT", "COMPONENT", "CONTRACT", "DB_RUNTIME", "API", "INTEGRATION",
    "E2E", "ACCESSIBILITY", "SYSTEM", "MANUAL_ONLY", "BLOCKED",
)
OWNERS = {
    "UNIT": "DEV_LOCAL_REFERENCE", "COMPONENT": "DEV_LOCAL_REFERENCE",
    "CONTRACT": "TEST_AUTOMATION", "DB_RUNTIME": "TEST_AUTOMATION",
    "API": "TEST_AUTOMATION", "INTEGRATION": "TEST_AUTOMATION",
    "E2E": "TEST_AUTOMATION", "ACCESSIBILITY": "TEST_AUTOMATION",
    "SYSTEM": "TEST_AUTOMATION", "MANUAL_ONLY": "MANUAL", "BLOCKED": "BLOCKED",
}
DEPENDENCY_KINDS = (
    "SEMANTIC_ORACLE", "ENVIRONMENT_ACCESS", "TEST_DATA_FIXTURE",
    "IMPLEMENTATION_LOCATOR", "TOOLING", "OBSERVABILITY",
)
DEPENDENCY_STATUSES = ("OPEN", "RESOLVED", "NOT_REQUIRED")
VERIFICATION_CATEGORIES = (
    "SYNTAX", "STATIC", "LINT", "TYPECHECK", "TEST_DISCOVERY", "TEST_LIST",
    "CONFIG_VALIDATE", "HARNESS_SELF_TEST", "FIXTURE_VALIDATE",
)
REVIEW_CHECKS = (
    "trace", "repository_ownership", "oracle_duplication", "fixtures", "secrets",
    "setup_cleanup", "flakiness", "selectors_interfaces", "dependencies",
    "project_conventions", "write_scope",
)
LIFECYCLES = (
    "AUTOMATION_INTAKE", "SUITABILITY_ANALYZED", "AUTOMATION_PLANNED",
    "AUTOMATION_IMPLEMENTING", "AUTOMATION_REVIEW", "AUTOMATION_VERIFYING",
    "EXECUTION_READY", "BLOCKED", "NEEDS_REPLAN",
)
_SHA256 = re.compile(r"[a-f0-9]{64}")
_BR_FR = re.compile(r"(?:BR|FR)-[A-Za-z0-9][A-Za-z0-9._-]*")
_TD_ID = re.compile(r"TD-[A-Za-z0-9][A-Za-z0-9._-]*")
_AUT_ID = re.compile(r"AUT-[A-Za-z0-9][A-Za-z0-9._-]*")
_CODE_STRING_SWITCHES = {"-c", "/c", "/k", "-command", "--command", "-enc", "-ec", "-encodedcommand", "-e", "--eval"}


class AutomationV1Error(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def owner_for(classification: str) -> str:
    try:
        return OWNERS[classification]
    except (KeyError, TypeError) as error:
        raise ValueError(f"unsupported automation class: {classification}") from error


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _sha_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _portable_ref(ref: dict, *, artifact=False) -> dict:
    if not isinstance(ref, dict):
        raise ValueError("exact artifact reference required")
    keys = {"id", "revision", "sha256", "path"}
    if set(ref) != keys:
        raise ValueError("artifact reference requires id, revision, sha256 and relative path")
    if not isinstance(ref["id"], str) or not ref["id"].strip():
        raise ValueError("artifact reference id is required")
    identifier(ref["revision"])
    if not isinstance(ref["sha256"], str) or not _SHA256.fullmatch(ref["sha256"]):
        raise ValueError("exact SHA-256 required")
    portable_path(ref["path"])
    if PureWindowsPath(ref["path"]).is_absolute() or ":" in ref["path"]:
        raise ValueError("canonical references cannot contain machine-specific paths")
    return dict(ref)


def _check_trace(testcase) -> tuple[list[str], list[str]]:
    requirement_refs = list(testcase.requirement_refs)
    test_design_refs = list(testcase.test_design_refs)
    if not requirement_refs or any(not isinstance(ref, str) or not _BR_FR.fullmatch(ref) for ref in requirement_refs):
        raise ValueError(f"{testcase.test_case_id}: canonical BR/FR trace required; BAREF is not authority")
    if len(requirement_refs) != len(set(requirement_refs)):
        raise ValueError(f"{testcase.test_case_id}: duplicate canonical trace")
    if not test_design_refs or any(not isinstance(ref, str) or not _TD_ID.fullmatch(ref) for ref in test_design_refs):
        raise ValueError(f"{testcase.test_case_id}: exact Test Design refs required")
    if len(test_design_refs) != len(set(test_design_refs)):
        raise ValueError(f"{testcase.test_case_id}: duplicate Test Design trace")
    return requirement_refs, test_design_refs


def _dependency_refs(testcase, oracle_refs: set[str]) -> list[dict]:
    result = []
    for index, dependency in enumerate(testcase.execution_dependencies, 1):
        kind = dependency.kind
        status = dependency.status
        required = dependency.required
        resolution_ref = dependency.resolution_ref
        if kind not in DEPENDENCY_KINDS or status not in DEPENDENCY_STATUSES or type(required) is not bool:
            raise ValueError(f"{testcase.test_case_id}: invalid typed execution dependency")
        if status == "RESOLVED" and (not isinstance(resolution_ref, str) or not resolution_ref.strip()):
            raise ValueError(f"{testcase.test_case_id}: RESOLVED dependency requires exact resolution ref")
        if status == "RESOLVED" and oracle_refs and resolution_ref not in oracle_refs:
            raise ValueError(f"{testcase.test_case_id}: resolution ref is not in exact Approved Testware oracle refs")
        if status != "RESOLVED" and resolution_ref is not None:
            raise ValueError(f"{testcase.test_case_id}: unresolved dependency cannot carry a resolution ref")
        result.append({
            "id": f"{testcase.test_case_id}:DEPENDENCY:{index:03d}",
            "kind": kind,
            "status": status,
            "required": required,
            "resolution_ref": resolution_ref,
        })
    return result


def _additional_dependency_refs(testcase_id: str, dependencies, oracle_refs: set[str], *, offset: int) -> list[dict]:
    result = []
    for index, dependency in enumerate(dependencies, offset + 1):
        if not isinstance(dependency, dict) or set(dependency) != {"kind", "status", "required", "resolution_ref"}:
            raise ValueError(f"{testcase_id}: automation dependency shape is invalid")
        kind, status = dependency["kind"], dependency["status"]
        required, resolution_ref = dependency["required"], dependency["resolution_ref"]
        if kind not in DEPENDENCY_KINDS or status not in DEPENDENCY_STATUSES or type(required) is not bool:
            raise ValueError(f"{testcase_id}: invalid typed automation dependency")
        if status == "RESOLVED" and (not isinstance(resolution_ref, str) or not resolution_ref.strip()):
            raise ValueError(f"{testcase_id}: RESOLVED dependency requires exact resolution ref")
        if status == "RESOLVED" and oracle_refs and resolution_ref not in oracle_refs:
            raise ValueError(f"{testcase_id}: resolution ref is not in exact Approved Testware oracle refs")
        if status != "RESOLVED" and resolution_ref is not None:
            raise ValueError(f"{testcase_id}: unresolved dependency cannot carry a resolution ref")
        result.append({
            "id": f"{testcase_id}:DEPENDENCY:{index:03d}", "kind": kind, "status": status,
            "required": required, "resolution_ref": resolution_ref,
        })
    return result


def validate_suitability(artifact: dict, approved_testcase_ids) -> dict:
    expected = list(approved_testcase_ids)
    if len(expected) != len(set(expected)):
        raise ValueError("approved testcase inventory contains duplicate IDs")
    if not isinstance(artifact, dict) or set(artifact) != {
        "schema_version", "artifact_class", "feature_id", "revision", "approved_testware_ref", "rows",
    }:
        raise ValueError("Automation Suitability shape is invalid")
    if type(artifact["schema_version"]) is not int or artifact["schema_version"] != 1 or artifact["artifact_class"] != "CANONICAL":
        raise ValueError("Automation Suitability must be canonical V1")
    identifier(artifact["feature_id"])
    identifier(artifact["revision"])
    _portable_ref(artifact["approved_testware_ref"])
    rows = artifact["rows"]
    if not isinstance(rows, list):
        raise ValueError("Automation Suitability rows are required")
    seen = []
    row_keys = {"testcase_id", "classification", "owner", "required", "rationale", "dependency_refs"}
    for row in rows:
        if not isinstance(row, dict) or set(row) != row_keys:
            raise ValueError("Automation Suitability row shape is invalid")
        testcase_id = identifier(row["testcase_id"])
        seen.append(testcase_id)
        owner = owner_for(row["classification"])
        if row["owner"] != owner:
            raise ValueError("Automation Suitability owner/class mismatch")
        if type(row["required"]) is not bool or not isinstance(row["rationale"], str) or not row["rationale"].strip():
            raise ValueError("Automation Suitability required flag and rationale are required")
        if not isinstance(row["dependency_refs"], list):
            raise ValueError("typed dependency refs are required")
        dep_ids = []
        for dep in row["dependency_refs"]:
            if not isinstance(dep, dict) or set(dep) != {"id", "kind", "status", "required", "resolution_ref"}:
                raise ValueError("typed dependency reference shape is invalid")
            if not isinstance(dep["id"], str) or not dep["id"].strip():
                raise ValueError("typed dependency identity is required")
            dep_ids.append(dep["id"])
            if dep["kind"] not in DEPENDENCY_KINDS or dep["status"] not in DEPENDENCY_STATUSES or type(dep["required"]) is not bool:
                raise ValueError("typed dependency kind/status is invalid")
            if dep["status"] == "RESOLVED" and (not isinstance(dep["resolution_ref"], str) or not dep["resolution_ref"].strip()):
                raise ValueError("RESOLVED dependency requires exact resolution ref")
            if dep["status"] != "RESOLVED" and dep["resolution_ref"] is not None:
                raise ValueError("unresolved dependency cannot carry a resolution ref")
        if len(dep_ids) != len(set(dep_ids)):
            raise ValueError("duplicate dependency ref")
    if len(seen) != len(set(seen)):
        raise ValueError("duplicate testcase in Automation Suitability")
    if set(seen) != set(expected):
        raise ValueError("Automation Suitability testcase inventory does not exactly match Approved Testware")
    reject_secrets(artifact)
    return artifact


def make_suitability(
    feature_id: str,
    approved_testware_ref: dict,
    testcases,
    assessments,
    *,
    revision: str = "1",
    execution_oracle_refs=(),
) -> dict:
    testcase_ids = [row.test_case_id for row in testcases]
    if len(testcase_ids) != len(set(testcase_ids)):
        raise ValueError("approved testcase inventory contains duplicate IDs")
    by_id = {}
    for assessment in assessments:
        testcase_id = assessment.get("testcase_id") if isinstance(assessment, dict) else None
        if testcase_id in by_id:
            raise ValueError("duplicate testcase assessment")
        by_id[testcase_id] = assessment
    if set(by_id) != set(testcase_ids):
        raise ValueError("assessment testcase inventory must exactly match Approved Testware")
    oracle_ids = {ref.get("id") for ref in execution_oracle_refs if isinstance(ref, dict)}
    rows = []
    for testcase in testcases:
        _check_trace(testcase)
        assessment = by_id[testcase.test_case_id]
        if set(assessment) - {"testcase_id", "classification", "owner", "required", "rationale", "dependency_refs"}:
            raise ValueError("unsupported Automation Suitability assessment field")
        classification = assessment.get("classification")
        owner = owner_for(classification)
        if "owner" in assessment and assessment["owner"] != owner:
            raise ValueError("Automation Suitability owner/class mismatch")
        dependency_refs = _dependency_refs(testcase, oracle_ids)
        additional = assessment.get("dependency_refs", [])
        if not isinstance(additional, list):
            raise ValueError("automation dependency_refs must be an array")
        dependency_refs.extend(_additional_dependency_refs(
            testcase.test_case_id, additional, oracle_ids, offset=len(dependency_refs),
        ))
        rows.append({
            "testcase_id": testcase.test_case_id,
            "classification": classification,
            "owner": owner,
            "required": assessment.get("required"),
            "rationale": assessment.get("rationale"),
            "dependency_refs": dependency_refs,
        })
    artifact = {
        "schema_version": 1,
        "artifact_class": "CANONICAL",
        "feature_id": feature_id,
        "revision": revision,
        "approved_testware_ref": _portable_ref(approved_testware_ref),
        "rows": rows,
    }
    return validate_suitability(artifact, testcase_ids)


def _argv(value, label):
    if not isinstance(value, list) or not value or any(not isinstance(part, str) or not part or "\x00" in part for part in value):
        raise ValueError(f"{label} must be a nonempty argv array")
    if any(part.casefold().partition("=")[0] in _CODE_STRING_SWITCHES for part in value):
        raise ValueError(f"{label} cannot invoke a shell/code-string mode")
    for part in value:
        path_token = part.partition("=")[2] if part.startswith("-") and "=" in part else part
        if PureWindowsPath(path_token).is_absolute() or PurePosixPath(path_token).is_absolute():
            raise ValueError(f"{label} cannot contain machine-specific absolute paths")
    return list(value)


def _planned_path(value):
    portable_path(value)
    if PureWindowsPath(value).is_absolute() or ":" in value or "\\" in value:
        raise ValueError("planned paths must be portable repository-relative paths")
    return value


def _verification_commands(value):
    if not isinstance(value, list) or not value:
        raise ValueError("at least one automation verification command is required")
    result = []
    for command in value:
        if not isinstance(command, dict) or set(command) != {"category", "argv"} or command["category"] not in VERIFICATION_CATEGORIES:
            raise ValueError("verification command category/shape is invalid")
        result.append({"category": command["category"], "argv": _argv(command["argv"], "verification command")})
    return result


def make_plan(
    suitability: dict,
    testcases,
    repository_id: str,
    item_specs: dict,
    *,
    revision: str = "1",
    previous_plan: dict | None = None,
    repository_role: str = "",
    repository_path: str = "",
    repository_name: str = "",
    base_revision: str | None = None,
) -> dict:
    identifier(repository_id)
    identifier(revision)
    testcase_map = {row.test_case_id: row for row in testcases}
    validate_suitability(suitability, list(testcase_map))
    suitability_rows = {row["testcase_id"]: row for row in suitability["rows"]}
    automated_ids = [key for key, row in suitability_rows.items() if row["owner"] == "TEST_AUTOMATION"]
    if not isinstance(item_specs, dict) or set(item_specs) != set(automated_ids):
        raise ValueError("Automation Plan item coverage must exactly match TEST_AUTOMATION suitability rows")
    if previous_plan and previous_plan.get("feature_id") != suitability["feature_id"]:
        raise ValueError("AUT identity lineage cannot cross features")
    prior_ids = {}
    if previous_plan:
        for item in previous_plan.get("items", []):
            refs = item.get("testcase_refs", [])
            if len(refs) == 1:
                prior_ids.setdefault(refs[0], []).append(item["aut_id"])
    next_number = 1
    if previous_plan:
        for item in previous_plan.get("items", []):
            match = re.fullmatch(r"AUT-(\d+)", item.get("aut_id", ""))
            if match:
                next_number = max(next_number, int(match.group(1)) + 1)
    items = []
    for testcase_id in automated_ids:
        testcase = testcase_map[testcase_id]
        requirement_refs, design_refs = _check_trace(testcase)
        spec = item_specs[testcase_id]
        if not isinstance(spec, dict) or set(spec) - {
            "suite", "planned_paths", "runner", "execution_command", "verification_commands",
            "technical_rationale",
        }:
            raise ValueError("Automation Plan item specification has unsupported fields")
        suite = spec.get("suite")
        runner = spec.get("runner")
        paths = spec.get("planned_paths")
        if not isinstance(suite, str) or not suite.strip() or not isinstance(runner, str) or not runner.strip():
            raise ValueError("suite and project-owned runner are required")
        if not isinstance(paths, list) or not paths:
            raise ValueError("planned write paths are required for TEST_AUTOMATION")
        paths = [_planned_path(path) for path in paths]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate planned path")
        old_ids = prior_ids.get(testcase_id, [])
        aut_id = old_ids.pop(0) if old_ids else f"AUT-{next_number:04d}"
        if not old_ids:
            next_number += 1
        item = {
            "aut_id": aut_id,
            "testcase_refs": [testcase_id],
            "automation_class": suitability_rows[testcase_id]["classification"],
            "owner": "TEST_AUTOMATION",
            "repository_id": repository_id,
            "suite": suite.strip(),
            "planned_paths": paths,
            "runner": runner.strip(),
            "execution_command": _argv(spec.get("execution_command"), "execution command"),
            "verification_commands": _verification_commands(spec.get("verification_commands")),
            "dependencies": copy.deepcopy(suitability_rows[testcase_id]["dependency_refs"]),
            "trace": {
                "requirement_refs": requirement_refs,
                "test_design_refs": design_refs,
                "testcase_refs": [testcase_id],
                "aut_id": aut_id,
            },
        }
        if spec.get("technical_rationale") is not None:
            if not isinstance(spec["technical_rationale"], str) or not spec["technical_rationale"].strip():
                raise ValueError("technical rationale must be nonempty")
            item["technical_rationale"] = spec["technical_rationale"].strip()
        items.append(item)
    if previous_plan:
        old_counts = {}
        new_counts = {}
        for item in previous_plan.get("items", []):
            for ref in item.get("testcase_refs", []):
                old_counts[ref] = old_counts.get(ref, 0) + 1
        for item in items:
            for ref in item["testcase_refs"]:
                new_counts[ref] = new_counts.get(ref, 0) + 1
        if any(count > 1 and count > old_counts.get(ref, 0) and not all(i.get("technical_rationale") for i in items if ref in i["testcase_refs"])
               for ref, count in new_counts.items()):
            raise ValueError("multiple AUT items for one testcase require explicit technical rationale")
    rows = suitability_rows
    plan = {
        "schema_version": 1,
        "artifact_class": "CANONICAL",
        "feature_id": suitability["feature_id"],
        "revision": revision,
        "suitability_ref": {
            "id": f"{suitability['feature_id']}:AUTOMATION_SUITABILITY",
            "revision": suitability["revision"],
            "sha256": _sha_bytes(_json_bytes(suitability)),
        },
        "repository_id": repository_id,
        "repository_role": repository_role,
        "repository_path": _planned_path(repository_path) if repository_path else "",
        "repository_name": repository_name,
        "base_revision": base_revision,
        "items": items,
        "dev_local_testcases": [key for key, row in rows.items() if row["owner"] == "DEV_LOCAL_REFERENCE"],
        "manual_testcases": [key for key, row in rows.items() if row["owner"] == "MANUAL"],
        "blocked_testcases": [key for key, row in rows.items() if row["owner"] == "BLOCKED"],
    }
    validate_plan(plan, suitability, testcases)
    return plan


def validate_plan(plan: dict, suitability: dict, testcases) -> dict:
    testcase_map = {row.test_case_id: row for row in testcases}
    validate_suitability(suitability, list(testcase_map))
    expected_keys = {
        "schema_version", "artifact_class", "feature_id", "revision", "suitability_ref",
        "repository_id", "repository_role", "repository_path", "repository_name", "base_revision",
        "items", "dev_local_testcases", "manual_testcases", "blocked_testcases",
    }
    if not isinstance(plan, dict) or set(plan) != expected_keys:
        raise ValueError("Automation Plan shape is invalid")
    if type(plan["schema_version"]) is not int or plan["schema_version"] != 1 or plan["artifact_class"] != "CANONICAL":
        raise ValueError("Automation Plan must be canonical V1")
    identifier(plan["feature_id"]); identifier(plan["revision"]); identifier(plan["repository_id"])
    if plan["feature_id"] != suitability["feature_id"]:
        raise ValueError("Automation Plan feature binding mismatch")
    if plan["repository_role"] and not isinstance(plan["repository_role"], str):
        raise ValueError("Automation repository role is invalid")
    if plan["repository_path"]:
        _planned_path(plan["repository_path"])
    if plan["repository_name"] and not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", plan["repository_name"]):
        raise ValueError("Automation repository identity is invalid")
    if plan["base_revision"] is not None and not isinstance(plan["base_revision"], str):
        raise ValueError("automation base revision is invalid")
    expected_suitability_ref = {
        "id": f"{suitability['feature_id']}:AUTOMATION_SUITABILITY",
        "revision": suitability["revision"],
        "sha256": _sha_bytes(_json_bytes(suitability)),
    }
    if plan["suitability_ref"] != expected_suitability_ref:
        raise ValueError("Automation Plan is stale against current Suitability")
    suit_rows = {row["testcase_id"]: row for row in suitability["rows"]}
    automated = {key for key, row in suit_rows.items() if row["owner"] == "TEST_AUTOMATION"}
    if not isinstance(plan["items"], list):
        raise ValueError("Automation Plan items are required")
    aut_ids, mapped = [], []
    item_keys = {
        "aut_id", "testcase_refs", "automation_class", "owner", "repository_id", "suite",
        "planned_paths", "runner", "execution_command", "verification_commands", "dependencies", "trace",
    }
    for item in plan["items"]:
        if not isinstance(item, dict) or not item_keys.issubset(item) or set(item) - item_keys - {"technical_rationale"}:
            raise ValueError("Automation Plan item shape is invalid")
        if not _AUT_ID.fullmatch(item["aut_id"]):
            raise ValueError("AUT identity is invalid")
        aut_ids.append(item["aut_id"])
        if item["owner"] != "TEST_AUTOMATION" or item["repository_id"] != plan["repository_id"]:
            raise ValueError("AUT owner/repository binding mismatch")
        refs = item["testcase_refs"]
        if not isinstance(refs, list) or len(refs) != 1 or refs[0] not in automated:
            raise ValueError("AUT testcase mapping must bind exact automated Testcases")
        testcase_id = refs[0]
        mapped.extend(refs)
        source = testcase_map[testcase_id]
        reqs, designs = _check_trace(source)
        if (item["automation_class"] != suit_rows[testcase_id]["classification"]
                or item["trace"] != {"requirement_refs": reqs, "test_design_refs": designs,
                                     "testcase_refs": [testcase_id], "aut_id": item["aut_id"]}):
            raise ValueError("AUT trace/classification drift")
        if not isinstance(item["suite"], str) or not item["suite"].strip() or not isinstance(item["runner"], str) or not item["runner"].strip():
            raise ValueError("AUT suite and runner are required")
        paths = item["planned_paths"]
        if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
            raise ValueError("AUT planned paths are invalid")
        for path in paths:
            _planned_path(path)
        _argv(item["execution_command"], "execution command")
        _verification_commands(item["verification_commands"])
        if item["dependencies"] != suit_rows[testcase_id]["dependency_refs"]:
            raise ValueError("AUT dependency refs differ from Suitability")
    if len(aut_ids) != len(set(aut_ids)) or set(mapped) != automated or len(mapped) != len(automated):
        raise ValueError("Automation Plan AUT coverage must exactly account for automated Testcases")
    for key, owner in (("dev_local_testcases", "DEV_LOCAL_REFERENCE"), ("manual_testcases", "MANUAL"), ("blocked_testcases", "BLOCKED")):
        expected = [identity for identity, row in suit_rows.items() if row["owner"] == owner]
        if plan[key] != expected:
            raise ValueError(f"Automation Plan {key} do not exactly match Suitability")
    reject_secrets(plan)
    return plan


MATERIAL_PLAN_FIELDS = (
    "suitability_ref", "repository_id", "repository_role", "repository_path", "repository_name",
    "base_revision", "items", "dev_local_testcases", "manual_testcases", "blocked_testcases",
)


def material_plan_projection(plan: dict) -> dict:
    return {key: copy.deepcopy(plan[key]) for key in MATERIAL_PLAN_FIELDS}


def assert_material_plan_unchanged(current: dict, candidate: dict) -> None:
    if material_plan_projection(current) != material_plan_projection(candidate):
        raise AutomationV1Error("NEEDS_REPLAN", "material Automation Plan fields changed after implementation began")


def reject_execution_claims(value) -> None:
    forbidden = re.compile(r"\b(?:API PASS|E2E PASS|SYSTEM PASS|FEATURE PASS|WCAG CONFORMANCE|VERIFIED)\b", re.IGNORECASE)
    if isinstance(value, dict):
        for nested in value.values():
            reject_execution_claims(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            reject_execution_claims(nested)
    elif isinstance(value, str) and forbidden.search(value):
        raise ValueError("Phase 7 cannot persist product execution/conformance claims")


def _reparse(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _safe_components(root: Path, relative: str) -> Path:
    _planned_path(relative)
    root = root.resolve()
    current = root
    for component in PurePosixPath(relative).parts:
        current = current / component
        if current.exists() or current.is_symlink():
            if _reparse(current):
                raise AutomationV1Error("UNSAFE_PATH", "symlink/reparse point in repository write path")
    target = (root / PurePosixPath(relative)).resolve(strict=False)
    if not target.is_relative_to(root):
        raise AutomationV1Error("UNSAFE_PATH", "repository path escapes its declared root")
    return target


def _git(root: Path, *args) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", shell=False,
    )
    if result.returncode:
        raise AutomationV1Error("REPOSITORY_IDENTITY_INVALID", result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def _remote_name(remote: str) -> str:
    remote = remote.strip().replace("\\", "/")
    if remote.startswith("git@") and ":" in remote:
        remote = remote.split(":", 1)[1]
    elif "://" in remote:
        from urllib.parse import urlparse
        remote = urlparse(remote).path.lstrip("/")
    remote = remote.removesuffix(".git").strip("/")
    return remote.casefold()


def _repo_snapshot(root: Path, *, clean_base: str | None = None) -> tuple[str, list[str], list[dict]]:
    head = _git(root, "rev-parse", "HEAD")
    changed = set(filter(None, _git(root, "diff", "--name-only", "HEAD", "--").splitlines()))
    changed.update(filter(None, _git(root, "ls-files", "--others", "--exclude-standard").splitlines()))
    if clean_base is not None:
        if _git(root, "merge-base", clean_base, head) != clean_base:
            raise AutomationV1Error("BASE_REVISION_DRIFT", "automation repository no longer descends from its exact planned base")
        changed.update(filter(None, _git(root, "diff", "--name-only", clean_base, head, "--").splitlines()))
    files = []
    for relative in sorted(changed):
        path = _safe_components(root, relative)
        if not path.is_file():
            raise AutomationV1Error("UNSAFE_PATH", "changed automation path is not a regular file")
        files.append({"path": relative, "sha256": _sha_bytes(path.read_bytes())})
    return head, sorted(changed), files


def _repository_rows(project_root: Path, local_roots: dict | None = None):
    project = project_root.resolve()
    policy_path = safe_file(project, ".sdlc/project-policy.yml")
    topology_path = safe_file(project, ".sdlc/project-topology.yml")
    policy_data = read_policy(project)
    topology_data = read_topology(topology_path.read_text(encoding="utf-8"))
    rows = topology_data["repositories"]
    role = policy_data["testing"]["automation_repository_role"]
    matches = [row for row in rows if row["role"] == role]
    if len(matches) != 1:
        raise AutomationV1Error("AUTOMATION_REPOSITORY_AMBIGUOUS", "policy role must resolve to exactly one topology repository")
    by_id = {row["id"]: row for row in rows}
    local_roots = dict(local_roots or {})
    if set(local_roots) - set(by_id):
        raise AutomationV1Error("REPOSITORY_IDENTITY_INVALID", "runtime root mapping contains an undeclared repository id")
    roots = {}
    for repo_id, row in by_id.items():
        candidate = Path(local_roots.get(repo_id, project / row["path"])).expanduser().absolute()
        if any(
            (path.exists() or path.is_symlink()) and _reparse(path)
            for path in (candidate, *candidate.parents)
        ):
            raise AutomationV1Error("REPOSITORY_IDENTITY_INVALID", "declared repository root crosses a symlink/reparse point")
        roots[repo_id] = candidate.resolve()
    for repo_id, root in roots.items():
        if root.exists():
            if not root.is_dir() or root.is_symlink():
                raise AutomationV1Error("REPOSITORY_IDENTITY_INVALID", "declared repository root is not a real directory")
            top = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
            remote = _remote_name(_git(root, "remote", "get-url", "origin"))
            if top != root or remote != by_id[repo_id]["repository"].casefold():
                raise AutomationV1Error("REPOSITORY_IDENTITY_INVALID", f"local root does not match declared repository {repo_id}")
    automation_row = matches[0]
    binding = {
        "policy_ref": {"id": "PROJECT_POLICY", "revision": _sha_bytes(policy_path.read_bytes()), "sha256": _sha_bytes(policy_path.read_bytes()), "path": ".sdlc/project-policy.yml"},
        "topology_ref": {"id": "PROJECT_TOPOLOGY", "revision": _sha_bytes(topology_path.read_bytes()), "sha256": _sha_bytes(topology_path.read_bytes()), "path": ".sdlc/project-topology.yml"},
        "automation_repository": {key: automation_row[key] for key in ("id", "role", "repository", "path")},
        "application_repositories": [
            {key: row[key] for key in ("id", "role", "repository", "path")}
            for row in rows if row["id"] != automation_row["id"]
        ],
    }
    return binding, roots, policy_data, topology_data


def _relative_to(root: Path, path: Path) -> str:
    try:
        value = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise AutomationV1Error("UNSAFE_PATH", "canonical artifact is outside the project root") from error
    portable_path(value)
    return value


def _testcase_collection_ref(project_root: Path, evidence: dict) -> dict:
    collection = evidence["manifest"]["testcase_collection"]
    path = Path(collection["path"])
    if not path.is_absolute():
        candidates = (evidence["manifest_path"].parent / path, project_root / path)
        path = next((candidate for candidate in candidates if candidate.is_file()), candidates[0])
    return {
        "artifact_id": collection["artifact_id"], "revision": collection["revision"],
        "sha256": collection["sha256"], "path": _relative_to(project_root, path),
    }


def _read_json(path: Path) -> tuple[dict, bytes]:
    try:
        content = path.read_bytes()
        value = json.loads(content.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("JSON object required")
        return value, content
    except (OSError, UnicodeError, ValueError) as error:
        raise AutomationV1Error("INVALID_EVIDENCE", f"cannot read exact JSON evidence: {path.name}") from error


def _atomic_write(path: Path, content: bytes) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            if _reparse(ancestor):
                raise AutomationV1Error("UNSAFE_PATH", "symlink/reparse point in runtime path")
    path.parent.mkdir(parents=True, exist_ok=True)
    for ancestor in (path, *path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            if _reparse(ancestor):
                raise AutomationV1Error("UNSAFE_PATH", "symlink/reparse point appeared in runtime path")
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _write_immutable(path: Path, content: bytes) -> None:
    for ancestor in (path, *path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            if _reparse(ancestor):
                raise AutomationV1Error("UNSAFE_PATH", "symlink/reparse point in canonical artifact path")
    path.parent.mkdir(parents=True, exist_ok=True)
    for ancestor in (path, *path.parents):
        if ancestor.exists() or ancestor.is_symlink():
            if _reparse(ancestor):
                raise AutomationV1Error("UNSAFE_PATH", "symlink/reparse point appeared in canonical artifact path")
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if not path.is_file() or path.read_bytes() != content:
                raise AutomationV1Error("IMMUTABLE_ARTIFACT_CONFLICT", "canonical revision already contains different bytes")
    except FileExistsError:
        if not path.is_file() or path.read_bytes() != content:
            raise AutomationV1Error("IMMUTABLE_ARTIFACT_CONFLICT", "canonical revision already contains different bytes")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class AutomationRuntime:
    """Resume-safe Automation V1 runtime; every operation revalidates its authority inputs."""

    def __init__(
        self,
        project_root: str | Path,
        run_dir: str | Path,
        *,
        human_actor_authenticator,
        ba_human_actor_authenticator,
        repository_roots: dict | None = None,
        foundation_authenticator=None,
        ux_human_actor_authenticator=None,
        technical_authenticator=None,
    ):
        self.project_root = Path(project_root).resolve()
        self.run_dir = Path(os.path.abspath(run_dir))
        self.repository_roots = dict(repository_roots or {})
        self.auth = {
            "human_actor_authenticator": human_actor_authenticator,
            "ba_human_actor_authenticator": ba_human_actor_authenticator,
            "foundation_authenticator": foundation_authenticator,
            "ux_human_actor_authenticator": ux_human_actor_authenticator,
            "technical_authenticator": technical_authenticator,
        }
        self._mutex = threading.RLock()
        if not self.project_root.is_dir():
            raise AutomationV1Error("INVALID_PROJECT", "project root must be an existing directory")
        if not callable(human_actor_authenticator) or not callable(ba_human_actor_authenticator):
            raise AutomationV1Error("AUTHENTICATOR_REQUIRED", "exact Test and BA Human authenticators are required")
        try:
            relative = self.run_dir.relative_to(self.project_root)
        except ValueError as error:
            raise AutomationV1Error("UNSAFE_PATH", "Automation runtime must be inside the project root") from error
        if len(relative.parts) < 4 or relative.parts[:3] != (".test-kit", "automation", "runs"):
            raise AutomationV1Error("UNSAFE_PATH", "Automation runtime must live under .test-kit/automation/runs")
        identifier(relative.parts[3])
        self._run_relative = relative.as_posix()
        self.state = None
        self.frame_hash = None
        self.sequence = 0

    @contextmanager
    def _lock(self):
        with self._mutex:
            current = self.project_root
            for component in Path(self._run_relative).parts:
                current = current / component
                if current.exists() or current.is_symlink():
                    if _reparse(current):
                        raise AutomationV1Error("UNSAFE_PATH", "runtime directory cannot cross a symlink/reparse point")
            self.run_dir.mkdir(parents=True, exist_ok=True)
            lock_path = self.run_dir / ".runtime.lock"
            if lock_path.exists() and _reparse(lock_path):
                raise AutomationV1Error("UNSAFE_PATH", "runtime lock cannot be a symlink/reparse point")
            with lock_path.open("a+b") as stream:
                if lock_path.stat().st_size == 0:
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    if os.name == "nt":
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def _frames(self):
        journal = self.run_dir / "journal"
        if journal.exists() and _reparse(journal):
            raise AutomationV1Error("UNSAFE_PATH", "runtime journal cannot be a symlink/reparse point")
        frames = sorted(journal.glob("*.json")) if journal.is_dir() else []
        previous = "0" * 64
        latest = None
        for sequence, path in enumerate(frames):
            if path.name != f"{sequence:08d}.json" or _reparse(path):
                raise AutomationV1Error("RUNTIME_JOURNAL_INVALID", "journal sequence/path is invalid")
            frame, _ = _read_json(path)
            body = {key: value for key, value in frame.items() if key != "sha256"}
            if (set(body) != {"schema_version", "sequence", "previous_sha256", "state"}
                    or body["schema_version"] != 1 or body["sequence"] != sequence
                    or body["previous_sha256"] != previous or frame.get("sha256") != _sha_bytes(_json_bytes(body))):
                raise AutomationV1Error("RUNTIME_JOURNAL_INVALID", "journal hash chain is invalid")
            previous = frame["sha256"]
            latest = frame
        return frames, latest, previous

    def _save(self, state: dict):
        frames, _, previous = self._frames()
        sequence = len(frames)
        body = {"schema_version": 1, "sequence": sequence, "previous_sha256": previous, "state": copy.deepcopy(state)}
        frame = {**body, "sha256": _sha_bytes(_json_bytes(body))}
        path = self.run_dir / "journal" / f"{sequence:08d}.json"
        _write_immutable(path, _json_bytes(frame))
        _atomic_write(self.run_dir / "workflow-state.json", _json_bytes(state))
        self.state = copy.deepcopy(state)
        self.sequence = sequence + 1
        self.frame_hash = frame["sha256"]
        return copy.deepcopy(state)

    def _load_state(self) -> dict:
        frames, latest, previous = self._frames()
        if latest is None:
            raise AutomationV1Error("RUNTIME_STATE_MISSING", "Automation V1 run has not started")
        state = latest["state"]
        if not isinstance(state, dict) or state.get("lifecycle") not in LIFECYCLES:
            raise AutomationV1Error("RUNTIME_STATE_INVALID", "persisted Automation V1 state is invalid")
        projection = self.run_dir / "workflow-state.json"
        try:
            projected, _ = _read_json(projection)
        except AutomationV1Error:
            projected = None
        if projected != state:
            _atomic_write(projection, _json_bytes(state))
        self.state = copy.deepcopy(state)
        self.sequence = len(frames)
        self.frame_hash = previous
        return copy.deepcopy(state)

    def _transition(self, state: dict, action: str, lifecycle: str | None = None) -> dict:
        before = self.state or {}
        result = copy.deepcopy(state)
        if lifecycle:
            result["lifecycle"] = lifecycle
        result["revision"] = before.get("revision", -1) + 1
        result.setdefault("history", []).append({
            "sequence": result["revision"],
            "from": before.get("lifecycle"),
            "to": result["lifecycle"],
            "action": action,
        })
        return self._save(result)

    def _policy_routing(self):
        return _repository_rows(self.project_root, self.repository_roots)

    def _load_testware(self, test_run_dir: Path):
        from tooling.lib import gate_persistence
        from tooling.lib import test_kit_v1_cases as cases
        from tooling.lib import test_kit_vnext as vnext

        test_run_dir = Path(os.path.abspath(test_run_dir))
        current = self.project_root
        try:
            test_relative = test_run_dir.relative_to(self.project_root)
        except ValueError as error:
            raise AutomationV1Error("UNSAFE_PATH", "Approved Testware run must be inside the Test project root") from error
        for component in test_relative.parts:
            current = current / component
            if current.exists() and _reparse(current):
                raise AutomationV1Error("UNSAFE_PATH", "Approved Testware path crosses a symlink/reparse point")
        test_run_dir = test_run_dir.resolve()
        test_run_relative = _relative_to(self.project_root, test_run_dir)
        manifest_path = test_run_dir / "approved-testware-vnext.json"
        manifest, manifest_bytes = _read_json(manifest_path)
        if "fixture_type" in manifest or manifest.get("not_for_production") is True:
            raise AutomationV1Error("TEST_ONLY_AUTHORITY_FORBIDDEN", "TEST_ONLY Approved Testware cannot authorize production Automation V1")
        if (manifest.get("schema_version") != 1 or manifest.get("artifact_class") != "HANDOFF_MANIFEST"
                or manifest.get("state") != "APPROVED_TESTWARE" or not isinstance(manifest.get("feature_id"), str)):
            raise AutomationV1Error("APPROVED_TESTWARE_REQUIRED", "exact Approved Testware VNext HANDOFF_MANIFEST is required")
        receipt_path = test_run_dir / "case-gate/receipt.json"
        receipt, _ = _read_json(receipt_path)
        try:
            authority = vnext.revalidate_vnext_authority(
                test_run_dir,
                human_actor_authenticator=self.auth["ba_human_actor_authenticator"],
                foundation_authenticator=self.auth["foundation_authenticator"],
                ux_human_actor_authenticator=self.auth["ux_human_actor_authenticator"],
                technical_authenticator=self.auth["technical_authenticator"],
            )
            receipt_bytes = json.dumps(receipt, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            review_workflow = gate_persistence.review_state(test_run_dir, receipt_path, receipt_bytes)
            if review_workflow.get("state") != "CASE_REVIEW" or review_workflow.get("test_only") is True:
                raise ValueError("exact production Case Review transaction is required")
            if review_workflow.get("design_gate_receipt_mode") == "TEST_ONLY":
                raise ValueError("TEST_ONLY Design Gate cannot authorize Automation V1")
            snapshot, case_state = cases.load_case_review_snapshot(
                test_run_dir / "canonical/canonical-testcases.json",
                test_run_dir / "workflow-state.json",
                test_run_dir / "canonical/semantic-payload.json",
                _review_workflow=review_workflow,
            )
            design_evidence = review_workflow.get("design_gate_receipt_evidence")
            if not isinstance(design_evidence, dict) or not isinstance(design_evidence.get("path"), str):
                raise ValueError("exact Design Gate receipt evidence is required")
            design_receipt_path = Path(design_evidence["path"]).resolve()
            if not design_receipt_path.is_file() or _sha_bytes(design_receipt_path.read_bytes()) != design_evidence.get("sha256"):
                raise ValueError("Design Gate receipt bytes are stale")
            design_run = design_receipt_path.parents[3]
            approved_design = cases.load_design_snapshot(
                design_run / "canonical/canonical-test-design.json",
                design_run / "workflow-state.json",
                design_run / "canonical/semantic-payload.json",
            )
            validation = vnext.validate_vnext_cases(
                snapshot, approved_design, authority,
                execution_contract_refs=case_state.execution_oracle_refs,
                execution_oracle_authenticator=self.auth["human_actor_authenticator"],
            )

            def post_authentication_check():
                try:
                    current_authority = vnext.revalidate_vnext_authority(
                        test_run_dir,
                        human_actor_authenticator=self.auth["ba_human_actor_authenticator"],
                        foundation_authenticator=self.auth["foundation_authenticator"],
                        ux_human_actor_authenticator=self.auth["ux_human_actor_authenticator"],
                        technical_authenticator=self.auth["technical_authenticator"],
                    )
                    if current_authority.handoff_ref != authority.handoff_ref:
                        return False
                    current_refs = cases.case_gate_input_refs(
                        current_authority.baseline, approved_design, run_dir=test_run_dir,
                        execution_contract_refs=case_state.execution_oracle_refs,
                        case_snapshot=snapshot, vnext_authority=True,
                    )
                    if vnext._ref_signature(current_refs) != tuple(sorted(case_state.input_refs)):
                        return False
                    return _sha_bytes(design_receipt_path.read_bytes()) == design_evidence["sha256"]
                except (OSError, ValueError, KeyError, TypeError):
                    return False

            decision = cases.apply_case_gate_decision(
                receipt, snapshot, approved_design, authority.baseline, case_state,
                workflow_dir=test_run_dir,
                human_actor_authenticator=self.auth["human_actor_authenticator"],
                validation=validation,
                execution_contract_refs=case_state.execution_oracle_refs,
                technical_context_refs=authority.dev_context["refs"] if authority.dev_context else (),
                post_authentication_validator=post_authentication_check,
                require_resolved_required_dependencies=True,
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise AutomationV1Error("APPROVED_TESTWARE_INVALID", "Test VNext authority or exact Case Gate receipt failed revalidation") from error
        if decision.status != "APPROVED_TESTWARE" or not authority.vnext_authority:
            raise AutomationV1Error("APPROVED_TESTWARE_INVALID", "Test VNext revalidation did not return exact APPROVED_TESTWARE")
        if decision.approved_testware is None or decision.approved_testware.to_dict() != manifest:
            raise AutomationV1Error("APPROVED_TESTWARE_STALE", "Approved Testware manifest differs from the canonical Case Gate output")
        if manifest_path.read_bytes() != manifest_bytes:
            raise AutomationV1Error("APPROVED_TESTWARE_STALE", "Approved Testware changed during trusted Human revalidation")
        snapshot = decision.reviewed_snapshot
        approved_ref = {
            "id": f"{manifest['feature_id']}:APPROVED_TESTWARE",
            "revision": manifest["testcase_collection"]["revision"],
            "sha256": _sha_bytes(manifest_bytes),
            "path": _relative_to(self.project_root, manifest_path),
        }
        collection = manifest["testcase_collection"]
        if (collection.get("artifact_id"), collection.get("revision"), collection.get("sha256")) != (
            snapshot.artifact_id, snapshot.revision, snapshot.sha256,
        ):
            raise AutomationV1Error("APPROVED_TESTWARE_STALE", "Testcase collection differs from the exact approved Case Gate snapshot")
        design_ref = manifest["approved_design"]
        if not design_ref.get("artifact_id") or not design_ref.get("revision") or not _SHA256.fullmatch(design_ref.get("sha256", "")):
            raise AutomationV1Error("APPROVED_TESTWARE_INVALID", "exact approved Design reference is missing")
        ids = [row.test_case_id for row in snapshot.records]
        if len(ids) != len(set(ids)) or any(row.review_status != "APPROVED" for row in snapshot.records):
            states = [(row.test_case_id, row.review_status) for row in snapshot.records]
            raise AutomationV1Error("APPROVED_TESTWARE_INVALID", f"Approved Testcase inventory is malformed: {states}")
        return {
            "feature_id": manifest["feature_id"],
            "manifest": manifest,
            "manifest_bytes": manifest_bytes,
            "manifest_path": manifest_path,
            "manifest_ref": approved_ref,
            "test_run_path": test_run_relative,
            "authority": authority,
            "snapshot": snapshot,
            "testcase_ids": ids,
        }

    def _artifact_path(self, relative: str) -> Path:
        return _safe_components(self.run_dir, relative)

    def _save_artifact(self, relative: str, value: dict, artifact_id: str, revision: str) -> dict:
        content = _json_bytes(value)
        path = self._artifact_path(relative)
        _write_immutable(path, content)
        return {
            "id": artifact_id,
            "revision": revision,
            "sha256": _sha_bytes(content),
            "path": _relative_to(self.project_root, path),
        }

    def _read_artifact_ref(self, ref: dict) -> dict:
        path = self.project_root / ref["path"]
        path = path.resolve()
        if not path.is_relative_to(self.project_root) or not path.is_file() or _reparse(path):
            raise AutomationV1Error("CANONICAL_ARTIFACT_STALE", "canonical artifact path is missing or unsafe")
        data, content = _read_json(path)
        if _sha_bytes(content) != ref["sha256"]:
            raise AutomationV1Error("CANONICAL_ARTIFACT_STALE", "canonical artifact hash changed")
        return data

    def _load(self, *, validate_inputs=True):
        state = self._load_state()
        if validate_inputs:
            route, _, _, _ = self._policy_routing()
            if route != state["repository_routing"]:
                raise AutomationV1Error("NEEDS_REPLAN", "project policy/topology or repository routing changed")
            test_run = self.project_root / state["testware_run_path"]
            evidence = self._load_testware(test_run)
            if evidence["manifest_ref"] != state["approved_testware"]:
                raise AutomationV1Error("NEEDS_REPLAN", "exact Approved Testware identity changed")
            testcase_ids = evidence["testcase_ids"]
            if state.get("suitability_ref"):
                suitability = self._read_artifact_ref(state["suitability_ref"])
                validate_suitability(suitability, testcase_ids)
            if state.get("plan_ref"):
                plan = self._read_artifact_ref(state["plan_ref"])
                validate_plan(plan, suitability, evidence["snapshot"].records)
            if state.get("implementation"):
                self._assert_implementation_current(state, plan)
            if state.get("dev_handoff_ref"):
                self._validate_dev_handoff(self.project_root / state["dev_handoff_ref"]["path"], evidence, route)
        return state

    def start(self, approved_testware_run_dir: str | Path) -> dict:
        with self._lock():
            route, _, _, _ = self._policy_routing()
            evidence = self._load_testware(Path(approved_testware_run_dir))
            if self._frames()[1] is not None:
                state = self._load()
                if state["approved_testware"] != evidence["manifest_ref"]:
                    raise AutomationV1Error("RUN_IDENTITY_CONFLICT", "Automation run is already bound to different Approved Testware")
                return state
            run_id = "AUT-" + hashlib.sha256((evidence["feature_id"] + evidence["manifest_ref"]["sha256"]).encode()).hexdigest()[:12]
            state = {
                "schema_version": 1,
                "artifact_class": "RUNTIME",
                "run_id": run_id,
                "feature_id": evidence["feature_id"],
                "revision": -1,
                "lifecycle": "AUTOMATION_INTAKE",
                "testware_run_path": evidence["test_run_path"],
                "approved_testware": evidence["manifest_ref"],
                "repository_routing": route,
                "suitability_ref": None,
                "plan_ref": None,
                "implementation": None,
                "review_ref": None,
                "verification_ref": None,
                "dev_handoff_ref": None,
                "handoff_ref": None,
                "review_budget": {"full_reviews": 0, "blocking_fix_waves": 0, "scoped_rereviews": 0},
                "blocked_reason": None,
                "history": [],
            }
            self.state = state
            return self._transition(state, "AUTOMATION_INTAKE")

    def status(self) -> dict:
        with self._lock():
            return self._load()

    def analyze_suitability(self, assessments) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "AUTOMATION_INTAKE":
                raise AutomationV1Error("INVALID_TRANSITION", "Suitability requires AUTOMATION_INTAKE")
            evidence = self._load_testware(self.project_root / state["testware_run_path"])
            manifest = evidence["manifest"]
            oracles = manifest.get("execution_oracle_refs", [])
            suitability = make_suitability(
                state["feature_id"], state["approved_testware"], evidence["snapshot"].records,
                assessments, execution_oracle_refs=oracles,
            )
            ref = self._save_artifact(
                f"canonical/automation-suitability-v1-r{suitability['revision']}.json",
                suitability, f"{state['feature_id']}:AUTOMATION_SUITABILITY", suitability["revision"],
            )
            state["suitability_ref"] = ref
            return self._transition(state, "SUITABILITY_ANALYZED", "SUITABILITY_ANALYZED")

    def _base_revision(self, route, roots) -> str | None:
        repo_id = route["automation_repository"]["id"]
        root = roots[repo_id]
        if not root.is_dir():
            return None
        status = _git(root, "status", "--porcelain", "--untracked-files=all")
        if status:
            return None
        return _git(root, "rev-parse", "HEAD")

    def plan(self, item_specs: dict) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "SUITABILITY_ANALYZED":
                raise AutomationV1Error("INVALID_TRANSITION", "Automation Plan requires SUITABILITY_ANALYZED")
            evidence = self._load_testware(self.project_root / state["testware_run_path"])
            suitability = self._read_artifact_ref(state["suitability_ref"])
            route, roots, _, _ = self._policy_routing()
            repository = route["automation_repository"]
            plan = make_plan(
                suitability, evidence["snapshot"].records, repository["id"], item_specs,
                repository_role=repository["role"], repository_path=repository["path"],
                repository_name=repository["repository"],
                base_revision=self._base_revision(route, roots),
            )
            ref = self._save_artifact(
                f"canonical/automation-plan-v1-r{plan['revision']}.json", plan,
                f"{state['feature_id']}:AUTOMATION_PLAN", plan["revision"],
            )
            state["plan_ref"] = ref
            state["review_budget"] = {"full_reviews": 0, "blocking_fix_waves": 0, "scoped_rereviews": 0}
            return self._transition(state, "AUTOMATION_PLANNED", "AUTOMATION_PLANNED")

    def _clear_stale_evidence(self, state: dict) -> None:
        state["implementation"] = None
        state["implementation_started"] = False
        state["implementation_base_revision"] = None
        state["review_ref"] = None
        state["verification_ref"] = None
        state["dev_handoff_ref"] = None
        state["handoff_ref"] = None
        state["blocked_reason"] = None

    def request_replan(self, reason: str) -> dict:
        with self._lock():
            state = self._load(validate_inputs=False)
            if state["lifecycle"] == "EXECUTION_READY":
                raise AutomationV1Error("TERMINAL_STATE", "EXECUTION_READY is terminal for Phase 7")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("material replan reason is required")
            prior = state.get("implementation")
            if prior is None and state.get("implementation_started") and state.get("implementation_base_revision"):
                try:
                    route, roots, _, _ = self._policy_routing()
                    root = roots[route["automation_repository"]["id"]]
                    head, changed, files = _repo_snapshot(root, clean_base=state["implementation_base_revision"])
                    prior = {
                        "base_revision": state["implementation_base_revision"],
                        "head_revision": head,
                        "changed_paths": changed,
                        "files": files,
                    }
                except (AutomationV1Error, KeyError, TypeError):
                    prior = None
            if prior:
                state["replan_base"] = {key: copy.deepcopy(prior[key]) for key in (
                    "base_revision", "head_revision", "changed_paths", "files",
                )}
            self._clear_stale_evidence(state)
            state["blocked_reason"] = {"code": "MATERIAL_CHANGE", "route": "REPLAN", "detail": reason.strip()}
            return self._transition(state, "NEEDS_REPLAN", "NEEDS_REPLAN")

    def replan(self, assessments, item_specs: dict, *, approved_testware_run_dir: str | Path | None = None) -> dict:
        with self._lock():
            state = self._load(validate_inputs=False)
            if state["lifecycle"] not in {"NEEDS_REPLAN", "BLOCKED"}:
                raise AutomationV1Error("INVALID_TRANSITION", "replan requires NEEDS_REPLAN or BLOCKED")
            route, roots, _, _ = self._policy_routing()
            prior_base = state.get("replan_base") or state.get("implementation")
            old_suitability = None
            old_plan = None
            if state.get("suitability_ref"):
                try:
                    old_suitability = self._read_artifact_ref(state["suitability_ref"])
                except AutomationV1Error:
                    pass
            if state.get("plan_ref"):
                try:
                    old_plan = self._read_artifact_ref(state["plan_ref"])
                except AutomationV1Error:
                    pass
            test_run = Path(approved_testware_run_dir) if approved_testware_run_dir else self.project_root / state["testware_run_path"]
            evidence = self._load_testware(test_run)
            if evidence["feature_id"] != state["feature_id"]:
                raise AutomationV1Error("RUN_IDENTITY_CONFLICT", "a new feature requires a new Automation run")
            if approved_testware_run_dir:
                state["testware_run_path"] = evidence["test_run_path"]
                state["approved_testware"] = evidence["manifest_ref"]
            state["repository_routing"] = route
            suit_revision = str(int(old_suitability["revision"]) + 1) if old_suitability else "1"
            suitability = make_suitability(
                state["feature_id"], evidence["manifest_ref"], evidence["snapshot"].records,
                assessments, revision=suit_revision,
                execution_oracle_refs=evidence["manifest"].get("execution_oracle_refs", []),
            )
            suit_ref = self._save_artifact(
                f"canonical/automation-suitability-v1-r{suit_revision}.json", suitability,
                f"{state['feature_id']}:AUTOMATION_SUITABILITY", suit_revision,
            )
            repository = route["automation_repository"]
            plan_revision = str(int(old_plan["revision"]) + 1) if old_plan else "1"
            base_revision = self._base_revision(route, roots)
            if base_revision is None and prior_base:
                base_revision = prior_base.get("base_revision")
                root = roots[repository["id"]]
                head, changed, files = _repo_snapshot(root, clean_base=base_revision)
                if (head != prior_base.get("head_revision") or changed != prior_base.get("changed_paths")
                        or files != prior_base.get("files")):
                    raise AutomationV1Error("NEEDS_REPLAN", "automation worktree changed after replan was requested")
            plan = make_plan(
                suitability, evidence["snapshot"].records, repository["id"], item_specs,
                revision=plan_revision, previous_plan=old_plan,
                repository_role=repository["role"], repository_path=repository["path"],
                repository_name=repository["repository"], base_revision=base_revision,
            )
            if prior_base and plan["base_revision"] == prior_base.get("base_revision"):
                planned_paths = {path for item in plan["items"] for path in item["planned_paths"]}
                if set(prior_base.get("changed_paths", [])) - planned_paths:
                    raise AutomationV1Error("WRITE_SCOPE_VIOLATION", "new Plan must account for retained automation worktree paths")
            plan_ref = self._save_artifact(
                f"canonical/automation-plan-v1-r{plan_revision}.json", plan,
                f"{state['feature_id']}:AUTOMATION_PLAN", plan_revision,
            )
            state["suitability_ref"] = suit_ref
            state["plan_ref"] = plan_ref
            state["replan_base"] = prior_base
            self._clear_stale_evidence(state)
            state["review_budget"] = {"full_reviews": 0, "blocking_fix_waves": 0, "scoped_rereviews": 0}
            state["blocked_reason"] = None
            return self._transition(state, "NEEDS_REPLAN", "AUTOMATION_PLANNED")

    def begin_implementation(self) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "AUTOMATION_PLANNED":
                raise AutomationV1Error("INVALID_TRANSITION", "implementation requires AUTOMATION_PLANNED")
            plan = self._read_artifact_ref(state["plan_ref"])
            route, roots, _, _ = self._policy_routing()
            repository = route["automation_repository"]
            root = roots[repository["id"]]
            if not root.is_dir() or not plan["base_revision"]:
                state["blocked_reason"] = {"code": "AUTOMATION_REPOSITORY_MISSING", "route": "PROJECT_SETUP"}
                return self._transition(state, "AUTOMATION_REPOSITORY_UNAVAILABLE", "BLOCKED")
            head = _git(root, "rev-parse", "HEAD")
            if head != plan["base_revision"]:
                state["blocked_reason"] = {"code": "BASE_REVISION_DRIFT", "route": "REPLAN"}
                return self._transition(state, "AUTOMATION_BASE_DRIFT", "NEEDS_REPLAN")
            if _git(root, "status", "--porcelain", "--untracked-files=all"):
                prior = state.get("replan_base")
                if not prior or prior.get("base_revision") != head:
                    state["blocked_reason"] = {"code": "AUTOMATION_REPOSITORY_DIRTY", "route": "REPLAN"}
                    return self._transition(state, "AUTOMATION_REPOSITORY_DIRTY", "BLOCKED")
                current_head, changed, files = _repo_snapshot(root, clean_base=head)
                planned_paths = {path for item in plan["items"] for path in item["planned_paths"]}
                if (current_head != prior.get("head_revision") or changed != prior.get("changed_paths")
                        or files != prior.get("files") or set(changed) - planned_paths):
                    state["blocked_reason"] = {"code": "AUTOMATION_REPOSITORY_DIRTY", "route": "REPLAN"}
                    return self._transition(state, "AUTOMATION_REPOSITORY_DIRTY", "BLOCKED")
            state["implementation_started"] = True
            state["implementation_base_revision"] = head
            return self._transition(state, "AUTOMATION_IMPLEMENTING", "AUTOMATION_IMPLEMENTING")

    def _plan_item(self, plan: dict, aut_id: str) -> dict:
        items = [item for item in plan["items"] if item["aut_id"] == aut_id]
        if len(items) != 1:
            raise AutomationV1Error("AUT_ID_UNKNOWN", "AUT ID does not identify exactly one plan item")
        return items[0]

    def authorize_source_mutation(self, aut_id: str, repository_id: str, relative_path: str, base_revision: str) -> Path:
        state = self._load()
        if state["lifecycle"] != "AUTOMATION_IMPLEMENTING":
            raise AutomationV1Error("WRITE_NOT_AUTHORIZED", "source writes require AUTOMATION_IMPLEMENTING")
        route, roots, _, _ = self._policy_routing()
        declared = route["automation_repository"]
        if repository_id != declared["id"]:
            app_ids = {row["id"] for row in route["application_repositories"]}
            code = "APP_REPOSITORY_WRITE_FORBIDDEN" if repository_id in app_ids else "WRONG_REPOSITORY"
            raise AutomationV1Error(code, "Test Automation source writes are limited to the declared automation repository")
        plan = self._read_artifact_ref(state["plan_ref"])
        item = self._plan_item(plan, aut_id)
        if item["repository_id"] != repository_id or relative_path not in item["planned_paths"]:
            raise AutomationV1Error("WRITE_SCOPE_VIOLATION", "path is not in this AUT item's exact planned write scope")
        if base_revision != state.get("implementation_base_revision") or base_revision != plan["base_revision"]:
            raise AutomationV1Error("BASE_REVISION_DRIFT", "write is not bound to the exact planned automation base")
        root = roots[repository_id]
        if not root.is_dir() or _git(root, "rev-parse", "HEAD") != base_revision:
            raise AutomationV1Error("BASE_REVISION_DRIFT", "automation repository HEAD changed before write")
        _, changed, _ = _repo_snapshot(root, clean_base=base_revision)
        planned = {path for plan_item in plan["items"] for path in plan_item["planned_paths"]}
        if set(changed) - planned:
            raise AutomationV1Error("WRITE_SCOPE_VIOLATION", "automation repo already contains out-of-plan changes")
        return _safe_components(root, relative_path)

    def write_source(self, aut_id: str, repository_id: str, relative_path: str, content: str | bytes, *, base_revision: str) -> dict:
        with self._lock():
            target = self.authorize_source_mutation(aut_id, repository_id, relative_path, base_revision)
            if not isinstance(content, (str, bytes)):
                raise TypeError("automation source must be UTF-8 text or bytes")
            encoded = content.encode("utf-8") if isinstance(content, str) else content
            target.parent.mkdir(parents=True, exist_ok=True)
            target = self.authorize_source_mutation(aut_id, repository_id, relative_path, base_revision)
            _atomic_write(target, encoded)
            return {"repository_id": repository_id, "path": relative_path, "sha256": _sha_bytes(encoded)}

    def _automation_revision(self, state: dict, plan: dict) -> dict:
        route, roots, _, _ = self._policy_routing()
        repo = route["automation_repository"]
        root = roots[repo["id"]]
        head, changed, files = _repo_snapshot(root, clean_base=state["implementation_base_revision"])
        allowed = {path for item in plan["items"] for path in item["planned_paths"]}
        if set(changed) - allowed:
            raise AutomationV1Error("WRITE_SCOPE_VIOLATION", "post-implementation diff contains out-of-plan paths")
        if (plan["items"] and not changed) or allowed - set(changed):
            raise AutomationV1Error("IMPLEMENTATION_INCOMPLETE", "every planned automation path must have exact changed bytes")
        digest = _sha_bytes(_json_bytes({"base_revision": state["implementation_base_revision"], "head_revision": head, "files": files}))
        return {
            "revision": "AUTOMATION_TREE_SHA256:" + digest,
            "base_revision": state["implementation_base_revision"],
            "head_revision": head,
            "changed_paths": changed,
            "files": files,
            "aut_paths": {item["aut_id"]: [path for path in item["planned_paths"] if path in changed] for item in plan["items"]},
        }

    def _assert_implementation_current(self, state: dict, plan: dict) -> None:
        if state["lifecycle"] not in {"AUTOMATION_REVIEW", "AUTOMATION_VERIFYING", "EXECUTION_READY"}:
            return
        current = self._automation_revision(state, plan)
        if current != state["implementation"]:
            raise AutomationV1Error("NEEDS_REPLAN", "automation source revision changed after implementation was recorded")

    def record_implementation(self) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "AUTOMATION_IMPLEMENTING":
                raise AutomationV1Error("INVALID_TRANSITION", "implementation evidence requires AUTOMATION_IMPLEMENTING")
            plan = self._read_artifact_ref(state["plan_ref"])
            implementation = self._automation_revision(state, plan)
            state["implementation"] = implementation
            state["review_ref"] = None
            state["verification_ref"] = None
            return self._transition(state, "AUTOMATION_IMPLEMENTATION_RECORDED", "AUTOMATION_REVIEW")

    def record_review(self, review: dict, *, scoped: bool = False) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "AUTOMATION_REVIEW":
                raise AutomationV1Error("INVALID_TRANSITION", "Automation Review requires AUTOMATION_REVIEW")
            if not isinstance(review, dict) or set(review) != {"reviewer", "checks", "findings"}:
                raise AutomationV1Error("INVALID_REVIEW", "consolidated review fields are required")
            if not isinstance(review["reviewer"], str) or not review["reviewer"].strip():
                raise AutomationV1Error("INVALID_REVIEW", "reviewer identity is required")
            checks = review["checks"]
            if not isinstance(checks, dict) or set(checks) != set(REVIEW_CHECKS) or any(type(value) is not bool for value in checks.values()):
                raise AutomationV1Error("INVALID_REVIEW", "review must cover every required review dimension")
            findings = review["findings"]
            if not isinstance(findings, list):
                raise AutomationV1Error("INVALID_REVIEW", "review findings must be an array")
            normalized = []
            for finding in findings:
                if not isinstance(finding, dict) or set(finding) != {"code", "blocking", "route"}:
                    raise AutomationV1Error("INVALID_REVIEW", "review finding shape is invalid")
                identifier(finding["code"])
                if type(finding["blocking"]) is not bool or finding["route"] not in {"FIX", "UPSTREAM", "DEV", "NONE"}:
                    raise AutomationV1Error("INVALID_REVIEW", "review finding route/blocking values are invalid")
                if finding["code"] in {"SPEC_GAP", "BUSINESS_DECISION_REQUIRED"} and finding["route"] != "UPSTREAM":
                    raise AutomationV1Error("SEMANTIC_AUTHORITY_VIOLATION", "missing WHAT must route upstream")
                normalized.append(dict(finding))
            budget = state["review_budget"]
            if scoped:
                if budget["full_reviews"] != 1 or budget["blocking_fix_waves"] != 1 or budget["scoped_rereviews"] != 0:
                    raise AutomationV1Error("REVIEW_BUDGET_EXCEEDED", "one full review, one blocking fix wave and one scoped rereview are the limits")
                budget["scoped_rereviews"] = 1
            else:
                if budget["full_reviews"] != 0:
                    raise AutomationV1Error("REVIEW_BUDGET_EXCEEDED", "only one consolidated full review is allowed")
                budget["full_reviews"] = 1
            blocked = any(not value for value in checks.values()) or any(row["blocking"] for row in normalized)
            implementation = state["implementation"]
            record = {
                "schema_version": 1,
                "artifact_class": "EVIDENCE",
                "feature_id": state["feature_id"],
                "plan_revision": self._read_artifact_ref(state["plan_ref"])["revision"],
                "automation_revision": implementation["revision"],
                "review_scope": "SCOPED_REREVIEW" if scoped else "CONSOLIDATED_FULL_REVIEW",
                "reviewer": review["reviewer"].strip(),
                "checks": checks,
                "findings": normalized,
                "budget": copy.deepcopy(budget),
                "status": "BLOCKED" if blocked else "PASS",
                "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            reject_execution_claims(record)
            ref = self._save_artifact(
                f"evidence/automation-review-v1-r{state['revision'] + 1}.json", record,
                f"{state['feature_id']}:AUTOMATION_REVIEW", str(state["revision"] + 1),
            )
            state["review_budget"] = budget
            state["review_ref"] = ref
            state["verification_ref"] = None
            upstream = any(row["route"] == "UPSTREAM" for row in normalized)
            if upstream:
                state["blocked_reason"] = {"code": "SEMANTIC_GAP", "route": "UPSTREAM"}
                return self._transition(state, "REVIEW_ROUTED_UPSTREAM", "BLOCKED")
            if blocked and scoped:
                state["blocked_reason"] = {"code": "REVIEW_STILL_BLOCKING", "route": "REPLAN"}
                return self._transition(state, "SCOPED_REVIEW_BLOCKED", "BLOCKED")
            if blocked:
                return self._transition(state, "AUTOMATION_REVIEW_BLOCKED", "AUTOMATION_REVIEW")
            return self._transition(state, "AUTOMATION_REVIEW_PASSED", "AUTOMATION_VERIFYING")

    def begin_fix_wave(self) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "AUTOMATION_REVIEW" or not state["review_ref"]:
                raise AutomationV1Error("INVALID_TRANSITION", "blocking review evidence is required before a fix wave")
            review = self._read_artifact_ref(state["review_ref"])
            if review["status"] != "BLOCKED" or state["review_budget"]["full_reviews"] != 1 or state["review_budget"]["blocking_fix_waves"] != 0:
                raise AutomationV1Error("REVIEW_BUDGET_EXCEEDED", "only one blocking fix wave is permitted")
            if any(row["route"] in {"UPSTREAM", "DEV"} for row in review["findings"]):
                raise AutomationV1Error("UPSTREAM_ROUTE_REQUIRED", "semantic or Dev findings cannot be repaired by Test Automation")
            state["review_budget"]["blocking_fix_waves"] = 1
            state["review_ref"] = None
            state["verification_ref"] = None
            return self._transition(state, "AUTOMATION_BLOCKING_FIX_WAVE", "AUTOMATION_IMPLEMENTING")

    def _safe_verification_argv(self, category: str, argv: list[str]) -> None:
        tokens = {part.casefold() for part in argv}
        if category == "TEST_DISCOVERY" and not tokens.intersection({"--collect-only", "--list-tests", "--dry-run"}):
            raise AutomationV1Error("UNSAFE_VERIFICATION_COMMAND", "test discovery must use a nonexecuting collect/list/dry-run mode")
        if category == "TEST_LIST" and not tokens.intersection({"--list-tests", "--collect-only", "--list"}):
            raise AutomationV1Error("UNSAFE_VERIFICATION_COMMAND", "test listing must use a nonexecuting list/collect mode")

    def verify(self) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "AUTOMATION_VERIFYING":
                raise AutomationV1Error("INVALID_TRANSITION", "Automation Verification requires AUTOMATION_VERIFYING")
            plan = self._read_artifact_ref(state["plan_ref"])
            before = self._automation_revision(state, plan)
            if before != state["implementation"]:
                raise AutomationV1Error("NEEDS_REPLAN", "automation source changed after review")
            route, roots, _, _ = self._policy_routing()
            automation_root = roots[route["automation_repository"]["id"]]
            results = []
            commands = []
            for item in plan["items"]:
                for command in item["verification_commands"]:
                    key = (command["category"], tuple(command["argv"]))
                    if key not in commands:
                        commands.append(key)
            for category, argv in commands:
                self._safe_verification_argv(category, list(argv))
                try:
                    process = subprocess.run(
                        list(argv), cwd=automation_root, capture_output=True, text=True,
                        encoding="utf-8", errors="replace", shell=False,
                    )
                    code, stdout, stderr = process.returncode, process.stdout, process.stderr
                except OSError as error:
                    code, stdout, stderr = 127, "", str(error)
                reject_execution_claims(stdout)
                reject_execution_claims(stderr)
                results.append({
                    "category": category,
                    "argv": list(argv),
                    "exit_code": code,
                    "status": "PASS" if code == 0 else "FAIL",
                    "stdout_sha256": _sha_bytes(stdout.encode("utf-8")),
                    "stderr_sha256": _sha_bytes(stderr.encode("utf-8")),
                })
            after = self._automation_revision(state, plan)
            if after != before:
                raise AutomationV1Error("AUTOMATION_VERIFICATION_MUTATED_SOURCE", "verification changed automation repository bytes")
            report = {
                "schema_version": 1,
                "artifact_class": "EVIDENCE",
                "feature_id": state["feature_id"],
                "plan_revision": plan["revision"],
                "automation_revision": before["revision"],
                "categories": list(VERIFICATION_CATEGORIES),
                "checks": results,
                "status": "PASS" if all(row["status"] == "PASS" for row in results) else "FAIL",
                "product_execution": "NOT_RUN",
                "claims": [],
                "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            reject_execution_claims(report)
            ref = self._save_artifact(
                f"evidence/automation-verification-v1-r{state['revision'] + 1}.json", report,
                f"{state['feature_id']}:AUTOMATION_VERIFICATION", str(state["revision"] + 1),
            )
            state["verification_ref"] = ref
            if report["status"] != "PASS":
                state["blocked_reason"] = {"code": "AUTOMATION_VERIFICATION_FAILED", "route": "REPLAN"}
                return self._transition(state, "AUTOMATION_VERIFICATION_FAILED", "BLOCKED")
            return self._transition(state, "AUTOMATION_VERIFICATION_PASSED", "AUTOMATION_VERIFYING")

    def _validate_dev_handoff(self, handoff_path: Path, evidence: dict, route: dict) -> dict:
        from tooling.lib import dev_vnext
        from tooling.lib import test_kit_vnext as vnext

        handoff_path = handoff_path.resolve()
        relative = _relative_to(self.project_root, handoff_path)
        data, content = _read_json(handoff_path)
        if data.get("schema_version") != 2 or data.get("artifact_class") != "HANDOFF_MANIFEST" or data.get("state") != "READY_FOR_TEST":
            raise AutomationV1Error("DEV_HANDOFF_NOT_READY", "exact Dev Handoff V2 READY_FOR_TEST is required")
        try:
            vnext.load_dev_vnext_context(
                {"project_root": str(self.project_root), "handoff_path": str(handoff_path)},
                evidence["authority"],
                ba_human_actor_authenticator=self.auth["ba_human_actor_authenticator"],
                technical_authenticator=self.auth["technical_authenticator"],
                foundation_authenticator=self.auth["foundation_authenticator"],
            )
            dev_vnext.validate_handoff(
                data, self.project_root,
                ba_authenticator=self.auth["ba_human_actor_authenticator"],
                technical_authenticator=self.auth["technical_authenticator"],
                foundation_authenticator=self.auth["foundation_authenticator"],
            )
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise AutomationV1Error("DEV_HANDOFF_INVALID", "canonical Dev VNext validator rejected the exact handoff") from error
        if handoff_path.read_bytes() != content:
            raise AutomationV1Error("DEV_HANDOFF_STALE", "Dev Handoff changed during authority revalidation")
        automation_id = route["automation_repository"]["id"]
        application_ids = {row["id"] for row in route["application_repositories"]}
        revisions = data.get("repository_revisions")
        if not isinstance(revisions, dict) or not revisions or set(revisions) - application_ids or automation_id in revisions:
            raise AutomationV1Error("DEV_HANDOFF_INVALID", "Dev implementation revisions must bind declared application repositories")
        _, roots, _, topology = self._policy_routing()
        for repository_id, revision in revisions.items():
            root = roots[repository_id]
            if not root.is_dir() or _git(root, "rev-parse", "HEAD") != revision:
                raise AutomationV1Error("DEV_REVISION_STALE", f"application repository {repository_id} differs from exact Dev READY_FOR_TEST revision")
            if _git(root, "status", "--porcelain", "--untracked-files=all"):
                raise AutomationV1Error("DEV_REVISION_STALE", f"application repository {repository_id} has uncommitted changes")
        app_rows = {row["id"]: row for row in topology["repositories"] if row["id"] in revisions}
        coverage = {row["id"]: row for row in data["requirements_coverage"]}
        suit = self._read_artifact_ref(self.state["suitability_ref"])
        case_by_id = {row.test_case_id: row for row in evidence["snapshot"].records}
        dev_references = []
        for suitability_row in suit["rows"]:
            if suitability_row["owner"] != "DEV_LOCAL_REFERENCE":
                continue
            testcase = case_by_id[suitability_row["testcase_id"]]
            refs = []
            for requirement_id in testcase.requirement_refs:
                covered = coverage.get(requirement_id)
                if not covered or not covered.get("test_refs"):
                    raise AutomationV1Error("DEV_LOCAL_REFERENCE_MISSING", f"Dev must provide exact source-local test evidence for {testcase.test_case_id}")
                for ref in covered["test_refs"]:
                    try:
                        exact_path = validate_reference(ref, self.project_root, revision=True)
                    except (OSError, ValueError, KeyError, TypeError) as error:
                        raise AutomationV1Error("DEV_LOCAL_REFERENCE_MISSING", "Dev-local evidence ref failed exact byte validation") from error
                    path_value = PurePosixPath(ref["path"])
                    owners = [row for row in app_rows.values() if path_value.is_relative_to(PurePosixPath(row["path"]))]
                    if len(owners) != 1 or not exact_path.is_file():
                        raise AutomationV1Error("DEV_LOCAL_REFERENCE_MISSING", "Dev-local test evidence must reside in an exact declared application repository")
                    refs.append({"id": ref["path"], "revision": ref["revision"], "sha256": ref["sha256"], "path": ref["path"]})
            unique_refs = { (ref["id"], ref["revision"], ref["sha256"]): ref for ref in refs }
            dev_references.append({"testcase_id": testcase.test_case_id, "evidence_refs": list(unique_refs.values())})
        current_ids = set()
        def collect(value):
            if isinstance(value, dict):
                if all(isinstance(value.get(key), str) for key in ("id", "revision", "sha256")):
                    current_ids.add(value["id"])
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)
        collect(data)
        for row in suit["rows"]:
            for dep in row["dependency_refs"]:
                if dep["kind"] == "IMPLEMENTATION_LOCATOR" and dep["status"] == "RESOLVED" and dep["resolution_ref"] not in current_ids:
                    raise AutomationV1Error("NEEDS_REPLAN", "current Dev handoff invalidates a consumed implementation locator")
        return {
            "data": data,
            "ref": {"id": f"{data['change_id']}:DEV_HANDOFF", "revision": data["technical_snapshot"]["revision"], "sha256": _sha_bytes(content), "path": relative},
            "application_revisions": revisions,
            "dev_local_references": dev_references,
        }

    def _block_finalization(self, state: dict, code: str, route: str) -> dict:
        state["blocked_reason"] = {"code": code, "route": route}
        return self._transition(state, code, "BLOCKED")

    def finalize(self, dev_handoff_path: str | Path) -> dict:
        with self._lock():
            state = self._load()
            resumable_dev_block = state["lifecycle"] == "BLOCKED" and state.get("blocked_reason", {}).get("code") in {
                "DEV_HANDOFF_NOT_READY", "DEV_HANDOFF_INVALID", "DEV_LOCAL_REFERENCE_MISSING", "DEV_REVISION_STALE",
            }
            if state["lifecycle"] != "AUTOMATION_VERIFYING" and not resumable_dev_block:
                raise AutomationV1Error("INVALID_TRANSITION", "EXECUTION_READY requires automation verification and review")
            if not state.get("verification_ref") or not state.get("review_ref"):
                raise AutomationV1Error("EXECUTION_READY_FORBIDDEN", "review and automation verification evidence are required")
            verification = self._read_artifact_ref(state["verification_ref"])
            review = self._read_artifact_ref(state["review_ref"])
            if verification["status"] != "PASS" or review["status"] != "PASS":
                raise AutomationV1Error("EXECUTION_READY_FORBIDDEN", "review and automation verification must PASS")
            test_evidence = self._load_testware(self.project_root / state["testware_run_path"])
            suitability = self._read_artifact_ref(state["suitability_ref"])
            plan = self._read_artifact_ref(state["plan_ref"])
            validate_suitability(suitability, test_evidence["testcase_ids"])
            validate_plan(plan, suitability, test_evidence["snapshot"].records)
            required_blocked = [row["testcase_id"] for row in suitability["rows"] if row["owner"] == "BLOCKED" and row["required"]]
            if required_blocked:
                return self._block_finalization(state, "REQUIRED_BLOCKED_TESTCASE", "REPLAN")
            open_required = [dep["id"] for row in suitability["rows"] for dep in row["dependency_refs"] if dep["required"] and dep["status"] == "OPEN"]
            if open_required:
                semantic_open = any(
                    dep["kind"] == "SEMANTIC_ORACLE" and dep["status"] == "OPEN" and dep["required"]
                    for row in suitability["rows"] for dep in row["dependency_refs"]
                )
                if semantic_open:
                    return self._block_finalization(state, "SEMANTIC_ORACLE_OPEN", "UPSTREAM")
                return self._block_finalization(state, "REQUIRED_DEPENDENCY_OPEN", "REPLAN")
            if not state.get("implementation") or not state.get("implementation_started"):
                raise AutomationV1Error("EXECUTION_READY_FORBIDDEN", "all TEST_AUTOMATION items require an exact implementation revision")
            try:
                dev = self._validate_dev_handoff(Path(dev_handoff_path), test_evidence, state["repository_routing"])
            except AutomationV1Error as error:
                if error.code in {"DEV_HANDOFF_NOT_READY", "DEV_HANDOFF_INVALID", "DEV_LOCAL_REFERENCE_MISSING", "DEV_REVISION_STALE"}:
                    return self._block_finalization(state, error.code, "DEV")
                if error.code == "NEEDS_REPLAN":
                    return self._transition({**state, "blocked_reason": {"code": error.code, "route": "REPLAN"}}, error.code, "NEEDS_REPLAN")
                raise
            implementation = self._automation_revision(state, plan)
            if implementation != state["implementation"]:
                return self._transition({**state, "blocked_reason": {"code": "AUTOMATION_SOURCE_DRIFT", "route": "REPLAN"}}, "AUTOMATION_SOURCE_DRIFT", "NEEDS_REPLAN")
            testware = test_evidence["manifest"]
            oracle_by_id = {ref["id"]: ref for ref in testware.get("execution_oracle_refs", []) if isinstance(ref, dict)}
            resolved_dependencies = []
            for row in suitability["rows"]:
                for dep in row["dependency_refs"]:
                    if dep["status"] == "RESOLVED":
                        oracle = oracle_by_id.get(dep["resolution_ref"])
                        if not oracle:
                            return self._block_finalization(state, "RESOLVED_DEPENDENCY_REF_MISSING", "REPLAN")
                        resolved_dependencies.append({
                            "testcase_id": row["testcase_id"], "dependency_id": dep["id"],
                            "kind": dep["kind"], "ref": {key: oracle[key] for key in ("id", "revision", "sha256")},
                        })
            testcase_collection = _testcase_collection_ref(self.project_root, test_evidence)
            manual = [
                {"testcase_id": identity, "testcase_collection_ref": testcase_collection}
                for identity in plan["manual_testcases"]
            ]
            blocked = [
                {"testcase_id": identity, "testcase_collection_ref": testcase_collection}
                for identity in plan["blocked_testcases"]
            ]
            automation_rows = []
            for item in plan["items"]:
                automation_rows.append({
                    "aut_id": item["aut_id"],
                    "testcase_refs": list(item["testcase_refs"]),
                    "automation_class": item["automation_class"],
                    "owner": item["owner"],
                    "repository_id": item["repository_id"],
                    "paths": list(implementation["aut_paths"][item["aut_id"]]),
                    "revision": implementation["revision"],
                    "verification_evidence_refs": [state["verification_ref"]],
                })
            handoff = {
                "schema_version": 1,
                "artifact_class": "HANDOFF_MANIFEST",
                "feature_id": state["feature_id"],
                "approved_testware": state["approved_testware"],
                "automation_suitability": state["suitability_ref"],
                "automation_plan": state["plan_ref"],
                "dev_handoff": dev["ref"],
                "application_revisions": dev["application_revisions"],
                "automation_repository": state["repository_routing"]["automation_repository"],
                "automation_revision": implementation["revision"],
                "automation_items": automation_rows,
                "manual_testcases": manual,
                "blocked_testcases": blocked,
                "dev_local_references": dev["dev_local_references"],
                "resolved_dependencies": resolved_dependencies,
                "review": state["review_ref"],
                "automation_verification": state["verification_ref"],
                "state": "EXECUTION_READY",
            }
            validate_execution_ready_handoff(handoff, test_evidence["testcase_ids"])
            reject_execution_claims(handoff)
            ref = self._save_artifact(
                "canonical/execution-ready-handoff-v1.json", handoff,
                f"{state['feature_id']}:EXECUTION_READY", "1",
            )
            state["dev_handoff_ref"] = dev["ref"]
            state["handoff_ref"] = ref
            state["blocked_reason"] = None
            return self._transition(state, "EXECUTION_READY", "EXECUTION_READY")

    def revalidate_handoff(self) -> dict:
        with self._lock():
            state = self._load()
            if state["lifecycle"] != "EXECUTION_READY" or not state.get("handoff_ref"):
                raise AutomationV1Error("EXECUTION_READY_REQUIRED", "no current EXECUTION_READY handoff exists")
            handoff = self._read_artifact_ref(state["handoff_ref"])
            evidence = self._load_testware(self.project_root / state["testware_run_path"])
            validate_execution_ready_handoff(handoff, evidence["testcase_ids"])
            suitability = self._read_artifact_ref(state["suitability_ref"])
            plan = self._read_artifact_ref(state["plan_ref"])
            validate_plan(plan, suitability, evidence["snapshot"].records)
            if (handoff["approved_testware"] != state["approved_testware"]
                    or handoff["automation_suitability"] != state["suitability_ref"]
                    or handoff["automation_plan"] != state["plan_ref"]
                    or handoff["automation_revision"] != state["implementation"]["revision"]
                    or handoff["review"] != state["review_ref"]
                    or handoff["automation_verification"] != state["verification_ref"]
                    or handoff["automation_repository"] != state["repository_routing"]["automation_repository"]):
                raise AutomationV1Error("EXECUTION_READY_STALE", "handoff refs differ from exact current runtime evidence")
            expected_items = [{
                "aut_id": item["aut_id"], "testcase_refs": item["testcase_refs"],
                "automation_class": item["automation_class"], "owner": item["owner"],
                "repository_id": item["repository_id"],
                "paths": state["implementation"]["aut_paths"][item["aut_id"]],
                "revision": state["implementation"]["revision"],
                "verification_evidence_refs": [state["verification_ref"]],
            } for item in plan["items"]]
            if handoff["automation_items"] != expected_items:
                raise AutomationV1Error("EXECUTION_READY_STALE", "handoff automation rows differ from exact current Plan")
            collection_ref = _testcase_collection_ref(self.project_root, evidence)
            expected_manual = [
                {"testcase_id": identity, "testcase_collection_ref": collection_ref}
                for identity in plan["manual_testcases"]
            ]
            expected_blocked = [
                {"testcase_id": identity, "testcase_collection_ref": collection_ref}
                for identity in plan["blocked_testcases"]
            ]
            if handoff["manual_testcases"] != expected_manual:
                raise AutomationV1Error("EXECUTION_READY_STALE", "manual testcase rows differ from exact Approved Testware inventory")
            if handoff["blocked_testcases"] != expected_blocked:
                raise AutomationV1Error("EXECUTION_READY_STALE", "blocked testcase rows differ from exact Approved Testware inventory")
            dev = self._validate_dev_handoff(
                self.project_root / state["dev_handoff_ref"]["path"], evidence, state["repository_routing"],
            )
            if (dev["ref"] != handoff["dev_handoff"]
                    or dev["application_revisions"] != handoff["application_revisions"]
                    or dev["dev_local_references"] != handoff["dev_local_references"]):
                raise AutomationV1Error("DEV_HANDOFF_STALE", "EXECUTION_READY handoff is not bound to current Dev evidence")
            verification = self._read_artifact_ref(state["verification_ref"])
            review = self._read_artifact_ref(state["review_ref"])
            if verification.get("status") != "PASS" or review.get("status") != "PASS":
                raise AutomationV1Error("EXECUTION_READY_STALE", "Automation Review or Verification no longer passes")
            return handoff


def validate_execution_ready_handoff(handoff: dict, approved_testcase_ids) -> dict:
    keys = {
        "schema_version", "artifact_class", "feature_id", "approved_testware", "automation_suitability",
        "automation_plan", "dev_handoff", "application_revisions", "automation_repository",
        "automation_revision", "automation_items", "manual_testcases", "blocked_testcases", "dev_local_references",
        "resolved_dependencies", "review", "automation_verification", "state",
    }
    if not isinstance(handoff, dict) or set(handoff) != keys:
        raise ValueError("EXECUTION_READY HANDOFF_MANIFEST shape is invalid")
    if type(handoff["schema_version"]) is not int or handoff["schema_version"] != 1 or handoff["artifact_class"] != "HANDOFF_MANIFEST" or handoff["state"] != "EXECUTION_READY":
        raise ValueError("EXECUTION_READY manifest identity/state is invalid")
    identifier(handoff["feature_id"])
    for key in ("approved_testware", "automation_suitability", "automation_plan", "dev_handoff", "review", "automation_verification"):
        _portable_ref(handoff[key])
    repo = handoff["automation_repository"]
    if not isinstance(repo, dict) or set(repo) != {"id", "role", "repository", "path"} or repo["role"] == "":
        raise ValueError("exact automation repository ownership is required")
    identifier(repo["id"]); identifier(repo["role"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo["repository"]):
        raise ValueError("automation repository identity is invalid")
    _planned_path(repo["path"])
    automation_revision = handoff["automation_revision"]
    if not isinstance(automation_revision, str) or not re.fullmatch(r"AUTOMATION_TREE_SHA256:[a-f0-9]{64}", automation_revision):
        raise ValueError("exact automation source revision is required")
    revisions = handoff["application_revisions"]
    if not isinstance(revisions, dict) or not revisions:
        raise ValueError("exact application repository revisions are required")
    for repository_id, revision in revisions.items():
        identifier(repository_id)
        if not isinstance(revision, str) or not re.fullmatch(r"[a-f0-9]{40,64}", revision):
            raise ValueError("application repository revision is invalid")
    testcase_ids = list(approved_testcase_ids)
    if len(testcase_ids) != len(set(testcase_ids)):
        raise ValueError("Approved Testware testcase inventory contains duplicates")
    automated, aut_ids = [], []
    for item in handoff["automation_items"]:
        expected = {"aut_id", "testcase_refs", "automation_class", "owner", "repository_id", "paths", "revision", "verification_evidence_refs"}
        if not isinstance(item, dict) or set(item) != expected:
            raise ValueError("EXECUTION_READY automation row shape is invalid")
        if not _AUT_ID.fullmatch(item["aut_id"]) or item["owner"] != "TEST_AUTOMATION" or item["repository_id"] != repo["id"]:
            raise ValueError("EXECUTION_READY AUT identity/ownership mismatch")
        if owner_for(item["automation_class"]) != "TEST_AUTOMATION" or item["revision"] != automation_revision:
            raise ValueError("EXECUTION_READY AUT class/revision mismatch")
        if not isinstance(item["testcase_refs"], list) or not item["testcase_refs"]:
            raise ValueError("EXECUTION_READY AUT testcase refs are required")
        automated.extend(item["testcase_refs"])
        aut_ids.append(item["aut_id"])
        if not item["paths"] or len(item["paths"]) != len(set(item["paths"])):
            raise ValueError("EXECUTION_READY AUT source paths are required")
        for path in item["paths"]:
            _planned_path(path)
        if not item["verification_evidence_refs"]:
            raise ValueError("exact Automation Verification evidence is required per AUT")
        for ref in item["verification_evidence_refs"]:
            _portable_ref(ref)
    if len(aut_ids) != len(set(aut_ids)) or len(automated) != len(set(automated)):
        raise ValueError("EXECUTION_READY AUT/testcase mapping is duplicated")
    manual_ids = []
    for row in handoff["manual_testcases"]:
        if not isinstance(row, dict) or set(row) != {"testcase_id", "testcase_collection_ref"}:
            raise ValueError("manual testcase reference shape is invalid")
        manual_ids.append(row["testcase_id"])
        ref = row["testcase_collection_ref"]
        if not isinstance(ref, dict) or set(ref) != {"artifact_id", "revision", "sha256", "path"}:
            raise ValueError("manual testcase must bind exact approved testcase collection")
        if not _SHA256.fullmatch(ref["sha256"]):
            raise ValueError("manual testcase collection hash is invalid")
        portable_path(ref["path"])
    blocked_ids = []
    for row in handoff["blocked_testcases"]:
        if not isinstance(row, dict) or set(row) != {"testcase_id", "testcase_collection_ref"}:
            raise ValueError("blocked testcase reference shape is invalid")
        blocked_ids.append(row["testcase_id"])
        ref = row["testcase_collection_ref"]
        if not isinstance(ref, dict) or set(ref) != {"artifact_id", "revision", "sha256", "path"}:
            raise ValueError("blocked testcase must bind exact approved testcase collection")
        if not _SHA256.fullmatch(ref["sha256"]):
            raise ValueError("blocked testcase collection hash is invalid")
        portable_path(ref["path"])
    dev_ids = []
    for row in handoff["dev_local_references"]:
        if not isinstance(row, dict) or set(row) != {"testcase_id", "evidence_refs"} or not row["evidence_refs"]:
            raise ValueError("Dev-local reference must bind exact evidence")
        dev_ids.append(row["testcase_id"])
        for ref in row["evidence_refs"]:
            _portable_ref(ref)
    if not isinstance(handoff["resolved_dependencies"], list):
        raise ValueError("resolved dependency refs must be an array")
    for dependency in handoff["resolved_dependencies"]:
        if not isinstance(dependency, dict) or set(dependency) != {"testcase_id", "dependency_id", "kind", "ref"}:
            raise ValueError("resolved dependency binding shape is invalid")
        if dependency["kind"] not in DEPENDENCY_KINDS:
            raise ValueError("resolved dependency kind is invalid")
        if not isinstance(dependency["ref"], dict) or set(dependency["ref"]) != {"id", "revision", "sha256"}:
            raise ValueError("resolved dependency requires exact identity, revision and hash")
        identifier(dependency["ref"]["revision"])
        if not isinstance(dependency["ref"]["id"], str) or not _SHA256.fullmatch(dependency["ref"]["sha256"]):
            raise ValueError("resolved dependency exact reference is invalid")
    if set(automated) | set(manual_ids) | set(blocked_ids) | set(dev_ids) != set(testcase_ids):
        raise ValueError("EXECUTION_READY does not account for every Approved Testcase exactly once")
    if len(automated) + len(manual_ids) + len(blocked_ids) + len(dev_ids) != len(testcase_ids):
        raise ValueError("EXECUTION_READY testcase disposition is duplicated")
    reject_secrets(handoff)
    reject_execution_claims(handoff)
    return handoff
