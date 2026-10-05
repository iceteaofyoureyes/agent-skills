"""Test Kit Phase 8 execution, Finding, Defect and retest orchestration.

This module consumes the canonical Test Automation V1 EXECUTION_READY path.
It does not grant authority to runtime state, observed application behavior or
Delivery Manifest. Approved Testcase bytes remain the sole behavior oracle.

Host adapters construct ExecutionRuntime with the exact Phase 7 run directory
and trusted BA/Test/Tester authenticators. A Tester callback receives
``(actor_id, request)`` where request contains role, action and artifact hash;
it must return an authenticated actor_id/role mapping. Public operations are
start, execute_automated, execution_manifest, read_artifact,
record_observation, classify_finding, accept_dev_fix, execute_retest,
record_retest_observation, finalize_verified, and revalidate_verified.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import threading

from shared.sdlc.schema import identifier, portable_path, reject_secrets, safe_file, validate_reference
from . import test_automation_v1 as automation


CLASSIFICATIONS = (
    "DEFECT", "SPEC_GAP", "BUSINESS_DECISION_REQUIRED", "TEST_ISSUE", "ENVIRONMENT_ISSUE",
)
ROUTES = {
    "DEFECT": "DEV",
    "SPEC_GAP": "UPSTREAM",
    "BUSINESS_DECISION_REQUIRED": "UPSTREAM",
    "TEST_ISSUE": "TEST",
    "ENVIRONMENT_ISSUE": "ENVIRONMENT",
}
_SHA256 = re.compile(r"[a-f0-9]{64}")
_GIT_SHA = re.compile(r"(?:[a-f0-9]{40}|[a-f0-9]{64})")
_EXECUTION_ROOT = PurePosixPath(".test-kit/execution/runs")


class ExecutionVNextError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _portable_relative(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a portable relative path")
    portable_path(value)
    path = PurePosixPath(value)
    if path.is_absolute() or PureWindowsPath(value).is_absolute() or ":" in value or "\\" in value:
        raise ValueError(f"{label} cannot contain an absolute or machine-specific path")
    return value


def _exact_ref(ref: dict, root: Path, *, label="artifact reference") -> dict:
    if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"}:
        raise ValueError(f"{label} requires id, revision, sha256 and path")
    if not isinstance(ref["id"], str) or not ref["id"].strip() or not isinstance(ref["revision"], str) or not ref["revision"]:
        raise ValueError(f"{label} identity is invalid")
    if not isinstance(ref["sha256"], str) or not _SHA256.fullmatch(ref["sha256"]):
        raise ValueError(f"{label} SHA-256 is invalid")
    relative = _portable_relative(ref["path"], label)
    try:
        path = safe_file(root, relative)
    except (OSError, ValueError) as error:
        raise ValueError(f"{label} is missing or unsafe") from error
    if not path.is_file():
        raise ValueError(f"{label} is missing or unsafe")
    if _sha(path.read_bytes()) != ref["sha256"]:
        raise ValueError(f"{label} bytes are stale")
    return copy.deepcopy(ref)


def _read_exact(ref: dict, root: Path, *, label="artifact reference") -> dict:
    exact = _exact_ref(ref, root, label=label)
    try:
        value = json.loads((root / PurePosixPath(exact["path"])).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as error:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} must resolve to an object")
    return value


def _validate_ref_list(refs, root: Path, label: str, *, required=False) -> list[dict]:
    if not isinstance(refs, list) or (required and not refs):
        raise ValueError(f"{label} must be an array" + (" with at least one ref" if required else ""))
    result = [_exact_ref(row, root, label=label) for row in refs]
    identities = [(row["id"], row["revision"], row["sha256"]) for row in result]
    if len(identities) != len(set(identities)):
        raise ValueError(f"{label} contains duplicate refs")
    return result


def validate_environment_descriptor(value: dict, root: str | Path | None = None) -> dict:
    required = {"schema_version", "artifact_class", "environment_id", "profile", "configuration_refs", "evidence_refs"}
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("Environment Descriptor V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "CANONICAL":
        raise ValueError("Environment Descriptor must be canonical V1")
    identifier(value["environment_id"])
    identifier(value["profile"])
    for key in ("configuration_refs", "evidence_refs"):
        if not isinstance(value[key], list):
            raise ValueError(f"Environment Descriptor {key} must be an array")
        for ref in value[key]:
            if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"}:
                raise ValueError(f"Environment Descriptor {key} contains an invalid exact ref")
            if not isinstance(ref["id"], str) or not ref["id"].strip():
                raise ValueError(f"Environment Descriptor {key} artifact identity is invalid")
            if not isinstance(ref["revision"], str) or not ref["revision"] or not _SHA256.fullmatch(str(ref["sha256"])):
                raise ValueError(f"Environment Descriptor {key} contains an invalid revision or hash")
            _portable_relative(ref["path"], "environment reference")
    reject_secrets(value)
    if root is not None:
        for key in ("configuration_refs", "evidence_refs"):
            refs = _validate_ref_list(value[key], Path(root), f"environment {key}")
            for ref in refs:
                content = (Path(root) / PurePosixPath(ref["path"])).read_bytes()
                try:
                    decoded = content.decode("utf-8")
                except UnicodeDecodeError:
                    if key == "configuration_refs":
                        raise ValueError("environment configuration refs must be sanitized UTF-8 text")
                    continue
                try:
                    parsed = json.loads(decoded)
                except json.JSONDecodeError:
                    parsed = decoded
                reject_secrets(parsed)
    return copy.deepcopy(value)


def validate_execution_manifest(value: dict) -> dict:
    required = {
        "schema_version", "artifact_class", "execution_id", "feature_id", "execution_ready_ref",
        "environment_ref", "approved_testware_ref", "automation_plan_ref", "application_revisions",
        "automation_repository", "automation_revision", "automated_items", "manual_testcases",
        "dev_local_references", "optional_blocked_testcases", "created_at",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("Execution Manifest V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "CANONICAL":
        raise ValueError("Execution Manifest must be canonical V1")
    for key in ("execution_id", "feature_id"):
        identifier(value[key])
    for key in ("execution_ready_ref", "environment_ref", "approved_testware_ref", "automation_plan_ref"):
        ref = value[key]
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"}:
            raise ValueError(f"Execution Manifest {key} must bind an exact artifact ref")
        if not isinstance(ref["id"], str) or not ref["id"].strip():
            raise ValueError(f"Execution Manifest {key} artifact identity is invalid")
        if not isinstance(ref["revision"], str) or not _SHA256.fullmatch(str(ref["sha256"])):
            raise ValueError(f"Execution Manifest {key} identity is invalid")
        _portable_relative(ref["path"], "execution manifest ref")
    if not isinstance(value["application_revisions"], dict) or not value["application_revisions"]:
        raise ValueError("Execution Manifest must bind application repository revisions")
    for repository_id, revision in value["application_revisions"].items():
        identifier(repository_id)
        if not isinstance(revision, str) or not _GIT_SHA.fullmatch(revision):
            raise ValueError("Execution Manifest application revision is invalid")
    repo = value["automation_repository"]
    if not isinstance(repo, dict) or set(repo) != {"id", "role", "repository", "path"}:
        raise ValueError("Execution Manifest automation repository identity is invalid")
    identifier(repo["id"])
    if not all(isinstance(repo[key], str) and repo[key] for key in ("role", "repository")):
        raise ValueError("Execution Manifest automation repository identity is incomplete")
    _portable_relative(repo["path"], "automation repository path")
    if not isinstance(value["automation_revision"], str) or not _GIT_SHA.fullmatch(value["automation_revision"]):
        raise ValueError("Execution Manifest automation revision is invalid")
    for key in ("automated_items", "manual_testcases", "dev_local_references", "optional_blocked_testcases"):
        if not isinstance(value[key], list):
            raise ValueError(f"Execution Manifest {key} must be an array")
    aut_ids, test_ids = [], []
    for row in value["automated_items"]:
        if not isinstance(row, dict) or set(row) != {"aut_id", "testcase_refs"} or not row["testcase_refs"]:
            raise ValueError("Execution Manifest automated item shape is invalid")
        identifier(row["aut_id"])
        if any(not isinstance(case_id, str) or not case_id for case_id in row["testcase_refs"]):
            raise ValueError("Execution Manifest automated testcase refs are invalid")
        aut_ids.append(row["aut_id"])
        test_ids.extend(row["testcase_refs"])
    if len(aut_ids) != len(set(aut_ids)) or len(test_ids) != len(set(test_ids)):
        raise ValueError("Execution Manifest contains duplicate automation or testcase rows")
    for key in ("manual_testcases", "optional_blocked_testcases"):
        ids = []
        for row in value[key]:
            if not isinstance(row, dict) or set(row) != {"testcase_id", "testcase_collection_ref"}:
                raise ValueError(f"Execution Manifest {key} row is invalid")
            ids.append(row["testcase_id"])
            ref = row["testcase_collection_ref"]
            if not isinstance(ref, dict) or set(ref) != {"artifact_id", "revision", "sha256", "path"}:
                raise ValueError(f"Execution Manifest {key} testcase oracle ref is invalid")
            _portable_relative(ref["path"], "testcase collection ref")
            if not _SHA256.fullmatch(str(ref["sha256"])):
                raise ValueError("Execution Manifest testcase collection SHA-256 is invalid")
        if len(ids) != len(set(ids)):
            raise ValueError(f"Execution Manifest {key} contains duplicates")
    if not isinstance(value["dev_local_references"], list):
        raise ValueError("Execution Manifest Dev-local references must be an array")
    for row in value["dev_local_references"]:
        if not isinstance(row, dict) or set(row) != {"testcase_id", "evidence_refs"} or not row["evidence_refs"]:
            raise ValueError("Execution Manifest Dev-local evidence row is invalid")
    if not isinstance(value["created_at"], str) or not value["created_at"].endswith("Z"):
        raise ValueError("Execution Manifest creation timestamp is invalid")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_observation(value: dict) -> dict:
    required = {"observation_id", "execution_id", "testcase_id", "oracle_ref", "oracle_locator", "actual_summary", "evidence_refs", "actor", "outcome", "recorded_at"}
    optional = {"aut_id"}
    if not isinstance(value, dict) or required - set(value) or set(value) - required - optional:
        raise ValueError("Observation V1 shape is invalid")
    for key in ("observation_id", "execution_id", "testcase_id"):
        identifier(value[key])
    if "aut_id" in value:
        identifier(value["aut_id"])
    ref = value["oracle_ref"]
    if not isinstance(ref, dict) or set(ref) != {"artifact_id", "revision", "sha256", "path"} or not _SHA256.fullmatch(str(ref.get("sha256", ""))):
        raise ValueError("Observation exact approved oracle ref is invalid")
    _portable_relative(ref["path"], "Observation oracle ref")
    if value["oracle_locator"] != value["testcase_id"]:
        raise ValueError("Observation oracle_locator must identify its exact approved Testcase")
    if not isinstance(value["actual_summary"], str) or not value["actual_summary"].strip():
        raise ValueError("Observation actual_summary is required")
    if not isinstance(value["evidence_refs"], list) or not value["evidence_refs"]:
        raise ValueError("Observation evidence refs are required")
    actor = value["actor"]
    if not isinstance(actor, dict) or set(actor) != {"actor_id", "role"} or actor["role"] != "TESTER":
        raise ValueError("Observation actor must be an authenticated TESTER")
    if value["outcome"] not in {"PASS", "FINDING"}:
        raise ValueError("Observation outcome is invalid")
    if not isinstance(value["recorded_at"], str) or not value["recorded_at"].endswith("Z"):
        raise ValueError("Observation timestamp is invalid")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_finding(value: dict) -> dict:
    required = {"schema_version", "artifact_class", "finding_id", "feature_id", "execution_id", "testcase_id", "observation_ref", "oracle_ref", "execution_manifest_ref", "execution_ready_ref", "application_revisions", "automation_revision", "environment_ref", "status"}
    optional = {"aut_id"}
    if not isinstance(value, dict) or required - set(value) or set(value) - required - optional:
        raise ValueError("Finding V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "CANONICAL" or value["status"] != "OPEN":
        raise ValueError("Finding identity/status is invalid")
    for key in ("finding_id", "feature_id", "execution_id", "testcase_id"):
        identifier(value[key])
    if "aut_id" in value:
        identifier(value["aut_id"])
    if not isinstance(value["application_revisions"], dict) or value["status"] != "OPEN":
        raise ValueError("Finding repository binding is invalid")
    if not _GIT_SHA.fullmatch(str(value["automation_revision"])):
        raise ValueError("Finding automation revision is invalid")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_classification(value: dict) -> dict:
    required = {"schema_version", "artifact_class", "finding_ref", "classification", "actor", "rationale", "evidence_refs", "route", "target_repository_ids", "classified_at"}
    optional = {"defect_proof"}
    if not isinstance(value, dict) or required - set(value) or set(value) - required - optional:
        raise ValueError("Finding Classification V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "CANONICAL":
        raise ValueError("Finding Classification identity is invalid")
    if value["classification"] not in CLASSIFICATIONS or value["route"] != ROUTES[value["classification"]]:
        raise ValueError("Finding Classification vocabulary or route is invalid")
    actor = value["actor"]
    if not isinstance(actor, dict) or set(actor) != {"actor_id", "role"} or actor["role"] != "TESTER":
        raise ValueError("Finding Classification actor must be an authenticated TESTER")
    if not isinstance(value["rationale"], str) or not value["rationale"].strip():
        raise ValueError("Finding Classification rationale is required")
    if not isinstance(value["evidence_refs"], list):
        raise ValueError("Finding Classification evidence_refs must be an array")
    if not isinstance(value["target_repository_ids"], list) or len(value["target_repository_ids"]) != len(set(value["target_repository_ids"])):
        raise ValueError("Finding Classification target repositories are invalid")
    for repository_id in value["target_repository_ids"]:
        identifier(repository_id)
    if value["classification"] == "DEFECT":
        proof = value.get("defect_proof")
        expected = {"reproducible", "deterministic", "environment_root_cause_excluded", "test_issue_excluded", "mismatch_evidence_refs"}
        if (not isinstance(proof, dict) or set(proof) != expected or proof["reproducible"] is not True
                or proof["deterministic"] is not True
                or proof["environment_root_cause_excluded"] is not True or proof["test_issue_excluded"] is not True
                or not isinstance(proof["mismatch_evidence_refs"], list) or not proof["mismatch_evidence_refs"]
                or not value["target_repository_ids"]):
            raise ValueError("DEFECT requires reproducibility, mismatch, environment and test-issue evidence")
    elif value["target_repository_ids"] or "defect_proof" in value:
        raise ValueError("non-DEFECT classification cannot target application repositories or carry defect proof")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_defect_handoff(value: dict) -> dict:
    required = {
        "schema_version", "artifact_class", "defect_id", "feature_id", "finding_ref", "classification_ref",
        "execution_manifest_ref", "execution_ready_ref", "approved_testware_ref", "testcase_ref", "oracle_ref",
        "observation_ref", "environment_ref", "original_dev_handoff_ref", "original_application_revisions",
        "automation_revision", "target_repository_ids", "verification_owner", "state",
    }
    optional = {"fix_base_application_revisions", "prior_reopened_ref", "reopen_observation_ref"}
    if not isinstance(value, dict) or required - set(value) or set(value) - required - optional:
        raise ValueError("Defect Handoff V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "HANDOFF_MANIFEST" or value["state"] != "DEFECT_READY_FOR_DEV":
        raise ValueError("Defect Handoff identity/state is invalid")
    for key in ("defect_id", "feature_id"):
        identifier(value[key])
    for key in ("finding_ref", "classification_ref", "execution_manifest_ref", "execution_ready_ref", "approved_testware_ref", "observation_ref", "environment_ref", "original_dev_handoff_ref"):
        ref = value[key]
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"} or not _SHA256.fullmatch(str(ref.get("sha256", ""))):
            raise ValueError(f"Defect Handoff {key} is invalid")
        _portable_relative(ref["path"], "Defect Handoff ref")
    for key in ("testcase_ref", "oracle_ref"):
        ref = value[key]
        if not isinstance(ref, dict) or set(ref) != {"artifact_id", "revision", "sha256", "path"} or not _SHA256.fullmatch(str(ref.get("sha256", ""))):
            raise ValueError(f"Defect Handoff {key} is invalid")
        _portable_relative(ref["path"], "Defect Handoff testcase ref")
    if value["testcase_ref"] != value["oracle_ref"]:
        raise ValueError("Defect Handoff must bind one exact approved testcase oracle")
    if value["verification_owner"] != "TESTER" or not isinstance(value["target_repository_ids"], list) or not value["target_repository_ids"]:
        raise ValueError("Defect Handoff requires explicit application targets and TESTER ownership")
    if not isinstance(value["original_application_revisions"], dict) or not value["original_application_revisions"]:
        raise ValueError("Defect Handoff application revision map is required")
    for revision in value["original_application_revisions"].values():
        if not _GIT_SHA.fullmatch(str(revision)):
            raise ValueError("Defect Handoff application revision is invalid")
    if not _GIT_SHA.fullmatch(str(value["automation_revision"])):
        raise ValueError("Defect Handoff automation revision is invalid")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_ready_for_retest(value: dict) -> dict:
    required = {
        "schema_version", "artifact_class", "defect_id", "feature_id", "defect_handoff_ref", "finding_ref",
        "original_execution_manifest_ref", "approved_testware_ref", "testcase_ref", "automation_revision",
        "previous_application_revisions", "fixed_application_revisions", "dev_fix_handoff_ref",
        "dev_fix_verification_ref", "environment_ref", "dev_local_references", "verification_owner", "state",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("READY_FOR_RETEST V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "HANDOFF_MANIFEST" or value["state"] != "READY_FOR_RETEST":
        raise ValueError("READY_FOR_RETEST identity/state is invalid")
    for key in ("defect_id", "feature_id"):
        identifier(value[key])
    for key in ("defect_handoff_ref", "finding_ref", "original_execution_manifest_ref", "approved_testware_ref", "dev_fix_handoff_ref", "dev_fix_verification_ref", "environment_ref"):
        ref = value[key]
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"} or not _SHA256.fullmatch(str(ref.get("sha256", ""))):
            raise ValueError(f"READY_FOR_RETEST {key} is invalid")
        _portable_relative(ref["path"], "READY_FOR_RETEST ref")
    ref = value["testcase_ref"]
    if not isinstance(ref, dict) or set(ref) != {"artifact_id", "revision", "sha256", "path"}:
        raise ValueError("READY_FOR_RETEST exact testcase oracle is invalid")
    _portable_relative(ref["path"], "READY_FOR_RETEST testcase ref")
    for key in ("previous_application_revisions", "fixed_application_revisions"):
        revisions = value[key]
        if not isinstance(revisions, dict) or not revisions:
            raise ValueError(f"READY_FOR_RETEST {key} must be a revision map")
        if any(not _GIT_SHA.fullmatch(str(revision)) for revision in revisions.values()):
            raise ValueError(f"READY_FOR_RETEST {key} contains an invalid revision")
    if set(value["previous_application_revisions"]) != set(value["fixed_application_revisions"]):
        raise ValueError("READY_FOR_RETEST application repository sets differ")
    if not isinstance(value["dev_local_references"], list):
        raise ValueError("READY_FOR_RETEST Dev-local evidence must be an array")
    if not _GIT_SHA.fullmatch(str(value["automation_revision"])) or value["verification_owner"] != "TESTER":
        raise ValueError("READY_FOR_RETEST automation revision or owner is invalid")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_verified_handoff(value: dict) -> dict:
    required = {
        "schema_version", "artifact_class", "feature_id", "execution_manifest_ref", "execution_ready_ref",
        "approved_testware_ref", "application_revisions", "automation_revision", "environment_ref", "observations",
        "dev_local_references", "optional_blocked_testcases", "defect_history", "verification_actor", "verified_at", "state",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("VERIFIED Handoff V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "HANDOFF_MANIFEST" or value["state"] != "VERIFIED":
        raise ValueError("VERIFIED Handoff identity/state is invalid")
    identifier(value["feature_id"])
    for key in ("execution_manifest_ref", "execution_ready_ref", "approved_testware_ref", "environment_ref"):
        ref = value[key]
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"} or not _SHA256.fullmatch(str(ref.get("sha256", ""))):
            raise ValueError(f"VERIFIED Handoff {key} is invalid")
        _portable_relative(ref["path"], "VERIFIED Handoff ref")
    if not isinstance(value["application_revisions"], dict) or not value["application_revisions"]:
        raise ValueError("VERIFIED Handoff application revision map is required")
    if any(not _GIT_SHA.fullmatch(str(revision)) for revision in value["application_revisions"].values()):
        raise ValueError("VERIFIED Handoff application revision is invalid")
    if not _GIT_SHA.fullmatch(str(value["automation_revision"])):
        raise ValueError("VERIFIED Handoff automation revision is invalid")
    if not isinstance(value["observations"], list):
        raise ValueError("VERIFIED Handoff observations must be an array")
    for ref in value["observations"]:
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"}:
            raise ValueError("VERIFIED Handoff Observation ref is invalid")
        _portable_relative(ref["path"], "VERIFIED Observation ref")
    if not isinstance(value["dev_local_references"], list):
        raise ValueError("VERIFIED Handoff Dev-local evidence must be an array")
    for row in value["dev_local_references"]:
        if not isinstance(row, dict) or set(row) != {"testcase_id", "evidence_refs"} or not row["evidence_refs"]:
            raise ValueError("VERIFIED Handoff Dev-local evidence row is invalid")
        identifier(row["testcase_id"])
    actor = value["verification_actor"]
    if not isinstance(actor, dict) or set(actor) != {"actor_id", "role"} or actor["role"] != "TESTER":
        raise ValueError("VERIFIED Handoff must be authenticated as TESTER")
    reject_secrets(value)
    return copy.deepcopy(value)


def validate_reopened(value: dict) -> dict:
    required = {
        "schema_version", "artifact_class", "defect_id", "prior_defect_handoff_ref", "ready_for_retest_ref",
        "new_finding_ref", "new_observation_ref", "fixed_application_revisions", "automation_revision",
        "environment_ref", "reopen_count", "prior_reopen_ref", "state",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise ValueError("REOPENED V1 shape is invalid")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["artifact_class"] != "CANONICAL" or value["state"] != "REOPENED":
        raise ValueError("REOPENED identity/state is invalid")
    identifier(value["defect_id"])
    if type(value["reopen_count"]) is not int or value["reopen_count"] < 1:
        raise ValueError("REOPENED lineage count is invalid")
    for key in ("prior_defect_handoff_ref", "ready_for_retest_ref", "new_finding_ref", "new_observation_ref", "environment_ref"):
        ref = value[key]
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"} or not _SHA256.fullmatch(str(ref.get("sha256", ""))):
            raise ValueError(f"REOPENED {key} is invalid")
        _portable_relative(ref["path"], "REOPENED ref")
    if value["prior_reopen_ref"] is not None:
        ref = value["prior_reopen_ref"]
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256", "path"}:
            raise ValueError("REOPENED previous lineage ref is invalid")
        _portable_relative(ref["path"], "REOPENED prior ref")
    if not isinstance(value["fixed_application_revisions"], dict) or not value["fixed_application_revisions"]:
        raise ValueError("REOPENED fixed application revision map is required")
    if any(not _GIT_SHA.fullmatch(str(revision)) for revision in value["fixed_application_revisions"].values()) or not _GIT_SHA.fullmatch(str(value["automation_revision"])):
        raise ValueError("REOPENED revision binding is invalid")
    reject_secrets(value)
    return copy.deepcopy(value)


def _git(root: Path, *args) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", shell=False)
    if result.returncode:
        raise ExecutionVNextError("EXECUTION_STALE", "exact repository identity could not be revalidated")
    return result.stdout.strip()


class ExecutionRuntime:
    """Durable Phase 8 API over a canonical Phase 7 Automation V1 run.

    Runtime journal state is transport only. Every state-changing operation
    revalidates the exact authority and repository evidence it consumes.
    """

    def __init__(
        self,
        project_root: str | Path,
        automation_run_dir: str | Path,
        execution_id: str,
        *,
        tester_authenticator,
        human_actor_authenticator,
        ba_human_actor_authenticator,
        repository_roots: dict | None = None,
        foundation_authenticator=None,
        ux_human_actor_authenticator=None,
        technical_authenticator=None,
        command_timeout_seconds: int = 900,
    ):
        self.project_root = Path(project_root).resolve()
        identifier(execution_id)
        self.execution_id = execution_id
        self.run_dir = self.project_root / Path(*_EXECUTION_ROOT.parts[1:]) / execution_id
        self.automation_run_dir = Path(automation_run_dir).resolve()
        self.tester_authenticator = tester_authenticator
        self.auth = dict(
            human_actor_authenticator=human_actor_authenticator,
            ba_human_actor_authenticator=ba_human_actor_authenticator,
            foundation_authenticator=foundation_authenticator,
            ux_human_actor_authenticator=ux_human_actor_authenticator,
            technical_authenticator=technical_authenticator,
        )
        self.command_timeout_seconds = command_timeout_seconds
        if not self.project_root.is_dir() or not callable(tester_authenticator) or not callable(human_actor_authenticator) or not callable(ba_human_actor_authenticator):
            raise ExecutionVNextError("AUTHENTICATOR_REQUIRED", "project root and trusted Test/BA/Tester host authenticators are required")
        try:
            relative = self.automation_run_dir.relative_to(self.project_root)
        except ValueError as error:
            raise ExecutionVNextError("EXECUTION_READY_REQUIRED", "Automation V1 run must be under the project root") from error
        if len(relative.parts) != 4 or relative.parts[:3] != (".test-kit", "automation", "runs"):
            raise ExecutionVNextError("EXECUTION_READY_REQUIRED", "exact Phase 7 Automation V1 run directory is required")
        self.automation = automation.AutomationRuntime(
            self.project_root, self.automation_run_dir,
            human_actor_authenticator=human_actor_authenticator,
            ba_human_actor_authenticator=ba_human_actor_authenticator,
            repository_roots=repository_roots,
            foundation_authenticator=foundation_authenticator,
            ux_human_actor_authenticator=ux_human_actor_authenticator,
            technical_authenticator=technical_authenticator,
        )
        self._mutex = threading.RLock()
        self.state = None
        self._load_state_if_present()

    @contextmanager
    def _lock(self):
        with self._mutex:
            self._check_safe(self.run_dir)
            self.run_dir.mkdir(parents=True, exist_ok=True)
            lock = self.run_dir / ".runtime.lock"
            if lock.is_symlink():
                raise ExecutionVNextError("UNSAFE_PATH", "runtime lock cannot be a symlink")
            with lock.open("a+b") as stream:
                if os.name == "nt":
                    import msvcrt
                    stream.seek(0)
                    if not stream.read(1):
                        stream.write(b"0")
                        stream.flush()
                    stream.seek(0)
                    msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(stream, fcntl.LOCK_EX)
                try:
                    self._load_state_if_present()
                    yield
                finally:
                    if os.name == "nt":
                        stream.seek(0)
                        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(stream, fcntl.LOCK_UN)

    @staticmethod
    def _check_safe(path: Path):
        for part in (path, *path.parents):
            if (part.exists() or part.is_symlink()) and automation._reparse(part):
                raise ExecutionVNextError("UNSAFE_PATH", "runtime path cannot cross a symlink")

    def _frames(self):
        journal = self.run_dir / "journal"
        if journal.is_symlink():
            raise ExecutionVNextError("RUNTIME_JOURNAL_INVALID", "journal cannot be a symlink")
        frames = sorted(journal.glob("*.json")) if journal.is_dir() else []
        previous = "0" * 64
        latest = None
        for index, path in enumerate(frames):
            if path.is_symlink() or path.name != f"{index:08d}.json":
                raise ExecutionVNextError("RUNTIME_JOURNAL_INVALID", "journal sequence/path is invalid")
            try:
                frame = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError, UnicodeError) as error:
                raise ExecutionVNextError("RUNTIME_JOURNAL_INVALID", "journal frame cannot be read") from error
            body = {key: value for key, value in frame.items() if key != "sha256"}
            if body.get("sequence") != index or body.get("previous_sha256") != previous or frame.get("sha256") != _sha(_json_bytes(body)):
                raise ExecutionVNextError("RUNTIME_JOURNAL_INVALID", "journal hash chain is invalid")
            previous = frame["sha256"]
            latest = frame
        return frames, latest, previous

    def _save_state(self, state: dict):
        frames, _, previous = self._frames()
        sequence = len(frames)
        body = {"schema_version": 1, "sequence": sequence, "previous_sha256": previous, "state": copy.deepcopy(state)}
        frame = {**body, "sha256": _sha(_json_bytes(body))}
        journal = self.run_dir / "journal"
        journal.mkdir(parents=True, exist_ok=True)
        path = journal / f"{sequence:08d}.json"
        try:
            with path.open("xb") as stream:
                stream.write(_json_bytes(frame))
        except FileExistsError as error:
            raise ExecutionVNextError("RUNTIME_JOURNAL_INVALID", "immutable journal frame already exists") from error
        self.state = copy.deepcopy(state)
        return copy.deepcopy(state)

    def _load_state_if_present(self):
        _, latest, _ = self._frames()
        if latest is None:
            self.state = None
            return None
        state = latest.get("state")
        if not isinstance(state, dict) or state.get("execution_id") != self.execution_id:
            raise ExecutionVNextError("RUNTIME_STATE_INVALID", "runtime state identity is invalid")
        self.state = copy.deepcopy(state)
        return copy.deepcopy(state)

    def _transition(self, state: dict, status: str, action: str):
        updated = copy.deepcopy(state)
        updated["status"] = status
        updated["revision"] = int(updated.get("revision", -1)) + 1
        updated.setdefault("history", []).append({"sequence": updated["revision"], "action": action, "status": status, "recorded_at": _stamp()})
        return self._save_state(updated)

    def _mark_execution_stale(self):
        if self.state and self.state.get("status") not in {"VERIFIED", "REOPENED", "ROUTED", "EXECUTION_STALE"}:
            self._transition(self.state, "EXECUTION_STALE", "EXACT_INPUT_OR_REPOSITORY_DRIFT")

    def _save_artifact(self, relative: str, value: dict, artifact_id: str, revision: str = "1") -> dict:
        _portable_relative(relative, "artifact path")
        path = (self.run_dir / PurePosixPath(relative)).resolve()
        if not path.is_relative_to(self.run_dir.resolve()):
            raise ExecutionVNextError("UNSAFE_PATH", "canonical artifact escaped Phase 8 run")
        self._check_safe(path)
        content = _json_bytes(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as stream:
                stream.write(content)
        except FileExistsError:
            if path.read_bytes() != content:
                raise ExecutionVNextError("ARTIFACT_IMMUTABLE", f"canonical artifact already exists: {relative}")
        return {"id": artifact_id, "revision": revision, "sha256": _sha(content), "path": path.relative_to(self.project_root).as_posix()}

    def _read_artifact(self, ref: dict) -> dict:
        try:
            return _read_exact(ref, self.project_root)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ExecutionVNextError("ARTIFACT_STALE", str(error)) from error

    def _actor(self, actor_id: str, action: str, artifact_sha256: str) -> dict:
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ExecutionVNextError("AUTHENTICATION_FAILED", "trusted Tester actor identity is required")
        request = {"role": "TESTER", "action": action, "artifact_sha256": artifact_sha256}
        try:
            result = self.tester_authenticator(actor_id, request)
        except Exception as error:
            raise ExecutionVNextError("AUTHENTICATION_FAILED", "trusted host rejected Tester identity") from error
        if (not isinstance(result, dict) or result.get("authenticated") is not True
                or result.get("actor_id") != actor_id or result.get("role") != "TESTER"):
            raise ExecutionVNextError("AUTHENTICATION_FAILED", "trusted host did not authenticate this actor as TESTER")
        return {"actor_id": actor_id, "role": "TESTER"}

    def _authority(self, *, initial=False) -> tuple[dict, dict, dict, dict, dict, dict]:
        """Revalidate through Phase 7; after a fix preserve exact input bytes while checking the new app revisions separately."""
        try:
            state = self.automation._load_state()
            if state.get("lifecycle") != "EXECUTION_READY" or not state.get("handoff_ref"):
                raise ValueError("Phase 7 runtime is not EXECUTION_READY")
            ready = self.automation._read_artifact_ref(state["handoff_ref"])
            evidence = self.automation._load_testware(self.project_root / state["testware_run_path"])
            automation.validate_execution_ready_handoff(ready, evidence["testcase_ids"])
            if evidence["manifest_ref"] != state["approved_testware"] or ready["approved_testware"] != evidence["manifest_ref"]:
                raise ValueError("exact Approved Testware ref changed")
            suitability = self.automation._read_artifact_ref(state["suitability_ref"])
            plan = self.automation._read_artifact_ref(state["plan_ref"])
            automation.validate_suitability(suitability, evidence["testcase_ids"])
            automation.validate_plan(plan, suitability, evidence["snapshot"].records)
            if (ready["automation_suitability"] != state["suitability_ref"]
                    or ready["automation_plan"] != state["plan_ref"]
                    or ready["automation_revision"] != state["implementation"]["revision"]):
                raise ValueError("EXECUTION_READY exact plan or automation revision changed")
            route, roots, policy, topology = self.automation._policy_routing()
            if route != state["repository_routing"] or route["automation_repository"] != ready["automation_repository"]:
                raise ValueError("project policy or repository topology differs from exact EXECUTION_READY")
            if (ready["review"] != state["review_ref"] or ready["automation_verification"] != state["verification_ref"]
                    or ready["dev_handoff"] != state["dev_handoff_ref"]):
                raise ValueError("EXECUTION_READY review, verification or Dev handoff binding changed")
            review = self.automation._read_artifact_ref(state["review_ref"])
            verification = self.automation._read_artifact_ref(state["verification_ref"])
            if (review.get("status") != "PASS" or verification.get("status") != "PASS"
                    or review.get("automation_revision") != ready["automation_revision"]
                    or verification.get("automation_revision") != ready["automation_revision"]):
                raise ValueError("exact Automation Review or Verification evidence no longer passes")
            expected_items = [{
                "aut_id": item["aut_id"], "testcase_refs": item["testcase_refs"],
                "automation_class": item["automation_class"], "owner": item["owner"],
                "repository_id": item["repository_id"], "paths": state["implementation"]["aut_paths"][item["aut_id"]],
                "revision": state["implementation"]["revision"],
                "verification_evidence_refs": [state["verification_ref"]],
            } for item in plan["items"]]
            if ready["automation_items"] != expected_items:
                raise ValueError("EXECUTION_READY automated items differ from the exact Automation Plan")
            collection_ref = automation._testcase_collection_ref(self.project_root, evidence)
            if ready["manual_testcases"] != [
                {"testcase_id": case_id, "testcase_collection_ref": collection_ref} for case_id in plan["manual_testcases"]
            ]:
                raise ValueError("EXECUTION_READY manual cases differ from exact Approved Testware")
            if initial:
                checked = self.automation.revalidate_handoff()
                if checked != ready:
                    raise ValueError("canonical Phase 7 revalidation returned a different handoff")
            else:
                _exact_ref(ready["dev_handoff"], self.project_root, label="original Dev Handoff")
            return state, ready, evidence, suitability, plan, (route, roots, policy, topology)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self._mark_execution_stale()
            if isinstance(error, ExecutionVNextError):
                raise
            raise ExecutionVNextError("EXECUTION_STALE", "exact Phase 7 EXECUTION_READY authority failed canonical revalidation") from error

    def _repository_roots(self, routing):
        _, roots, _, topology = routing
        return roots, topology

    def _current_dev_local_references(self, prior_refs: list[dict], evidence: dict, dev_handoff: dict, routing) -> list[dict]:
        coverage = {row["id"]: row for row in dev_handoff.get("requirements_coverage", [])}
        cases = {row.test_case_id: row for row in evidence["snapshot"].records}
        route, _, _, topology = routing
        application_rows = [row for row in topology["repositories"] if row["id"] != route["automation_repository"]["id"]]
        result = []
        for prior in prior_refs:
            testcase = cases.get(prior["testcase_id"])
            if testcase is None:
                raise ExecutionVNextError("DEV_LOCAL_REFERENCE_STALE", "Dev-local Testcase disappeared from exact Approved Testware")
            exact_refs = []
            for requirement_id in testcase.requirement_refs:
                requirement = coverage.get(requirement_id)
                if not requirement or not requirement.get("test_refs"):
                    raise ExecutionVNextError("DEV_LOCAL_REFERENCE_STALE", "fresh Dev fix Handoff lacks testcase requirement verification evidence")
                for ref in requirement["test_refs"]:
                    path = validate_reference(ref, self.project_root, revision=True)
                    relative = PurePosixPath(ref["path"])
                    owner = [row for row in application_rows if relative.is_relative_to(PurePosixPath(row["path"]))]
                    if len(owner) != 1:
                        raise ExecutionVNextError("DEV_LOCAL_REFERENCE_STALE", "Dev-local evidence must stay inside an exact application repository")
                    exact_refs.append({"id": ref["path"], "revision": ref["revision"], "sha256": ref["sha256"], "path": ref["path"]})
            unique_refs = {(ref["id"], ref["revision"], ref["sha256"]): ref for ref in exact_refs}
            if not unique_refs:
                raise ExecutionVNextError("DEV_LOCAL_REFERENCE_STALE", "fresh Dev-local evidence is required")
            result.append({"testcase_id": prior["testcase_id"], "evidence_refs": list(unique_refs.values())})
        return result

    def _check_environment(self, descriptor_ref: dict):
        try:
            descriptor = self._read_artifact(descriptor_ref)
            validate_environment_descriptor(descriptor, self.project_root)
            return descriptor
        except (OSError, ValueError, KeyError, TypeError) as error:
            self._mark_execution_stale()
            if isinstance(error, ExecutionVNextError):
                raise
            raise ExecutionVNextError("EXECUTION_STALE", "exact environment binding is stale") from error

    def _assert_revisions(self, manifest_or_ready: dict, routing, *, expected_revisions=None):
        roots, topology = self._repository_roots(routing)
        automation_repo = manifest_or_ready["automation_repository"]
        automation_id = automation_repo["id"]
        automation_revision = manifest_or_ready["automation_revision"]
        app_revisions = expected_revisions or manifest_or_ready["application_revisions"]
        app_ids = {row["id"] for row in topology["repositories"] if row["id"] != automation_id}
        if set(app_revisions) != app_ids:
            raise ExecutionVNextError("EXECUTION_STALE", "EXECUTION_READY must bind one exact revision for every application repository")
        for repository_id, revision in app_revisions.items():
            root = roots[repository_id]
            if _git(root, "rev-parse", "HEAD") != revision or _git(root, "status", "--porcelain", "--untracked-files=all"):
                self._mark_execution_stale()
                raise ExecutionVNextError("EXECUTION_STALE", f"application repository {repository_id} revision or clean state drifted")
        auto_root = roots[automation_id]
        if _git(auto_root, "rev-parse", "HEAD") != automation_revision or _git(auto_root, "status", "--porcelain", "--untracked-files=all"):
            self._mark_execution_stale()
            raise ExecutionVNextError("EXECUTION_STALE", "automation repository revision or clean state drifted")
        return roots

    def _current_manifest(self):
        if not self.state or not self.state.get("execution_manifest_ref"):
            raise ExecutionVNextError("EXECUTION_MANIFEST_REQUIRED", "no immutable Execution Manifest exists")
        manifest = self._read_artifact(self.state["execution_manifest_ref"])
        validate_execution_manifest(manifest)
        if manifest["execution_id"] != self.execution_id:
            raise ExecutionVNextError("EXECUTION_STALE", "Execution Manifest identity changed")
        self._check_environment(manifest["environment_ref"])
        return manifest

    def _assert_observation_binding(self, ref: dict, manifest: dict, evidence: dict, *, testcase_id: str | None = None) -> dict:
        observation = validate_observation(self._read_artifact(ref))
        collection = automation._testcase_collection_ref(self.project_root, evidence)
        if (observation["execution_id"] != self.execution_id
                or observation["oracle_ref"] != collection
                or observation["testcase_id"] not in set(evidence["testcase_ids"])
                or (testcase_id is not None and observation["testcase_id"] != testcase_id)):
            raise ExecutionVNextError("OBSERVATION_STALE", "Observation is not bound to this execution and exact approved Testcase")
        refs = _validate_ref_list(observation["evidence_refs"], self.project_root, "Observation evidence", required=True)
        if observation.get("aut_id"):
            automated = {row["aut_id"]: row for row in manifest["automated_items"]}
            item = automated.get(observation["aut_id"])
            if not item or observation["testcase_id"] not in item["testcase_refs"]:
                raise ExecutionVNextError("OBSERVATION_STALE", "automated Observation AUT mapping is stale")
            commands = []
            for evidence_ref in refs:
                try:
                    candidate = _read_exact(evidence_ref, self.project_root)
                except (OSError, ValueError, KeyError, TypeError):
                    continue
                if (candidate.get("artifact_class") == "EVIDENCE" and candidate.get("execution_id") == self.execution_id
                        and candidate.get("aut_id") == observation["aut_id"]):
                    commands.append(candidate)
            if not commands:
                raise ExecutionVNextError("COMMAND_EVIDENCE_REQUIRED", "automated Observation lost its exact command evidence")
            accepted_app_revisions = [manifest["application_revisions"]]
            for ready_ref in self.state.get("ready_for_retest_refs", {}).values():
                ready_for_retest = self._read_artifact(ready_ref)
                accepted_app_revisions.append(ready_for_retest["fixed_application_revisions"])
            if not any(
                command["testcase_refs"] == item["testcase_refs"]
                and command["automation_revision"] == manifest["automation_revision"]
                and command["environment_ref"] == manifest["environment_ref"]
                and command["application_revisions"] in accepted_app_revisions
                and (observation["outcome"] != "PASS" or command["status"] == "COMMAND_PASS")
                for command in commands
            ):
                raise ExecutionVNextError("OBSERVATION_STALE", "command evidence revision or outcome does not match Observation")
        else:
            manual_ids = {row["testcase_id"] for row in manifest["manual_testcases"]}
            if observation["testcase_id"] not in manual_ids:
                raise ExecutionVNextError("OBSERVATION_STALE", "manual Observation does not bind a MANUAL_ONLY testcase")
        return observation

    def start(self, environment_descriptor: dict) -> dict:
        with self._lock():
            if self.state:
                raise ExecutionVNextError("RUN_IDENTITY_CONFLICT", "Execution run already exists and its manifest is immutable")
            _, ready, evidence, _, _, routing = self._authority(initial=True)
            env = validate_environment_descriptor(environment_descriptor, self.project_root)
            roots = self._assert_revisions(ready, routing)
            environment_ref = self._save_artifact("canonical/environment-v1.json", env, f"{env['environment_id']}:ENVIRONMENT", "1")
            handoff_ref = self.automation.state["handoff_ref"]
            plan_ref = ready["automation_plan"]
            automation_repo = ready["automation_repository"]
            collection = automation._testcase_collection_ref(self.project_root, evidence)
            plan = self.automation._read_artifact_ref(plan_ref)
            suitability = self.automation._read_artifact_ref(ready["automation_suitability"])
            required = {row["testcase_id"] for row in suitability["rows"] if row["required"] and row["owner"] in {"TEST_AUTOMATION", "MANUAL"}}
            optional_blocked = {row["testcase_id"] for row in suitability["rows"] if row["owner"] == "BLOCKED" and not row["required"]}
            if {case_id for item in plan["items"] for case_id in item["testcase_refs"]} | set(plan["manual_testcases"]) | optional_blocked | set(plan["dev_local_testcases"]) != set(evidence["testcase_ids"]):
                raise ExecutionVNextError("EXECUTION_STALE", "Phase 7 testcase accounting is incomplete")
            manifest = {
                "schema_version": 1,
                "artifact_class": "CANONICAL",
                "execution_id": self.execution_id,
                "feature_id": ready["feature_id"],
                "execution_ready_ref": copy.deepcopy(handoff_ref),
                "environment_ref": environment_ref,
                "approved_testware_ref": copy.deepcopy(ready["approved_testware"]),
                "automation_plan_ref": copy.deepcopy(plan_ref),
                "application_revisions": copy.deepcopy(ready["application_revisions"]),
                "automation_repository": copy.deepcopy(automation_repo),
                "automation_revision": ready["automation_revision"],
                "automated_items": [{"aut_id": item["aut_id"], "testcase_refs": copy.deepcopy(item["testcase_refs"])} for item in plan["items"]],
                "manual_testcases": [
                    {"testcase_id": case_id, "testcase_collection_ref": collection} for case_id in plan["manual_testcases"]
                ],
                "dev_local_references": copy.deepcopy(ready["dev_local_references"]),
                "optional_blocked_testcases": [
                    {"testcase_id": row["testcase_id"], "testcase_collection_ref": collection}
                    for row in ready["blocked_testcases"]
                ],
                "created_at": _stamp(),
            }
            validate_execution_manifest(manifest)
            ref = self._save_artifact("canonical/execution-manifest-v1.json", manifest, f"{self.execution_id}:EXECUTION_MANIFEST", "1")
            self._assert_revisions(manifest, routing)
            state = {
                "schema_version": 1, "execution_id": self.execution_id, "revision": -1,
                "status": "EXECUTION_MANIFEST_READY", "execution_manifest_ref": ref,
                "command_evidence_refs": {}, "command_evidence_count": 0, "observation_refs": {}, "finding_refs": {},
                "classification_refs": {}, "defect_handoffs": {}, "ready_for_retest_refs": {},
                "reopened_refs": {}, "verified_ref": None, "history": [],
            }
            return self._transition(state, "EXECUTION_MANIFEST_READY", "EXECUTION_MANIFEST_CREATED")

    def status(self) -> dict:
        with self._lock():
            if not self.state:
                raise ExecutionVNextError("RUNTIME_STATE_MISSING", "Phase 8 execution has not started")
            return copy.deepcopy(self.state)

    def execution_manifest(self) -> dict:
        """Read and revalidate this run's exact immutable Execution Manifest."""
        with self._lock():
            return copy.deepcopy(self._current_manifest())

    def read_artifact(self, ref: dict) -> dict:
        """Read an exact artifact produced within this Phase 8 run."""
        with self._lock():
            exact = _exact_ref(ref, self.project_root)
            path = (self.project_root / PurePosixPath(exact["path"])).resolve()
            if not path.is_relative_to(self.run_dir.resolve()):
                raise ExecutionVNextError("ARTIFACT_OUT_OF_SCOPE", "Phase 8 runtime reads only its exact run artifacts")
            return copy.deepcopy(self._read_artifact(exact))

    @staticmethod
    def _drain_hash(stream, result: dict, key: str):
        digest = hashlib.sha256()
        while True:
            chunk = stream.read(65536)
            if not chunk:
                break
            digest.update(chunk)
        result[key] = digest.hexdigest()

    def _run_plan_item(self, manifest: dict, plan_item: dict, testcase_refs: list[str], *, expected_app_revisions=None, initial=True):
        state, ready, _, _, plan, routing = self._authority(initial=initial)
        if ready["automation_revision"] != manifest["automation_revision"] or ready["automation_plan"] != manifest["automation_plan_ref"]:
            raise ExecutionVNextError("EXECUTION_STALE", "automation plan or revision changed")
        expected_apps = expected_app_revisions or manifest["application_revisions"]
        roots = self._assert_revisions(manifest, routing, expected_revisions=expected_apps)
        env_ref = manifest["environment_ref"]
        self._check_environment(env_ref)
        if plan_item not in plan["items"] or plan_item["testcase_refs"] != testcase_refs:
            raise ExecutionVNextError("EXECUTION_STALE", "execution command is not from the exact bound Automation Plan")
        argv = plan_item["execution_command"]
        if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
            raise ExecutionVNextError("INVALID_EXECUTION_COMMAND", "Automation Plan execution_command must be an argv array")
        automation_root = roots[manifest["automation_repository"]["id"]]
        started = _stamp()
        exit_code = -1
        try:
            process = subprocess.Popen(
                argv, cwd=automation_root, shell=False,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            hashes = {}
            stdout_thread = threading.Thread(target=self._drain_hash, args=(process.stdout, hashes, "stdout"), daemon=False)
            stderr_thread = threading.Thread(target=self._drain_hash, args=(process.stderr, hashes, "stderr"), daemon=False)
            stdout_thread.start()
            stderr_thread.start()
            try:
                exit_code = process.wait(timeout=self.command_timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                exit_code = 124
            stdout_thread.join()
            stderr_thread.join()
            stdout_sha256, stderr_sha256 = hashes["stdout"], hashes["stderr"]
            process.stdout.close()
            process.stderr.close()
        except OSError as error:
            exit_code = 127
            stdout_sha256 = _sha(b"")
            stderr_sha256 = _sha(str(error).encode("utf-8", errors="replace"))
        completed = _stamp()
        evidence = {
            "schema_version": 1, "artifact_class": "EVIDENCE", "execution_id": self.execution_id,
            "aut_id": plan_item["aut_id"], "testcase_refs": copy.deepcopy(testcase_refs),
            "application_revisions": copy.deepcopy(expected_apps), "automation_revision": manifest["automation_revision"],
            "environment_ref": copy.deepcopy(env_ref), "argv": copy.deepcopy(argv),
            "started_at": started, "completed_at": completed, "exit_code": exit_code,
            "stdout_sha256": stdout_sha256, "stderr_sha256": stderr_sha256,
            "status": "COMMAND_PASS" if exit_code == 0 else "COMMAND_FAIL",
        }
        reject_secrets(evidence)
        command_sequence = int(self.state["command_evidence_count"]) + 1
        ref = self._save_artifact(
            f"evidence/commands/{plan_item['aut_id']}-{command_sequence:04d}.json",
            evidence, f"{self.execution_id}:{plan_item['aut_id']}:COMMAND", str(command_sequence),
        )
        # Store hashes only. Command streams stay in temporary evidence spools and are deleted.
        self.state["command_evidence_refs"][plan_item["aut_id"]] = ref
        self.state["command_evidence_count"] = command_sequence
        self._transition(self.state, "EXECUTING" if initial else "RETESTING", "AUTOMATION_COMMAND_RECORDED")
        self._check_environment(env_ref)
        self._assert_revisions(manifest, routing, expected_revisions=expected_apps)
        _, current_ready, _, _, _, _ = self._authority(initial=initial)
        if current_ready != ready:
            raise ExecutionVNextError("EXECUTION_STALE", "EXECUTION_READY changed while an automation command ran")
        return ref, evidence

    def execute_automated(self) -> dict:
        with self._lock():
            manifest = self._current_manifest()
            if self.state["status"] not in {"EXECUTION_MANIFEST_READY", "EXECUTING"}:
                raise ExecutionVNextError("INVALID_TRANSITION", "automated execution requires a ready manifest")
            _, _, _, _, plan, routing = self._authority(initial=True)
            self._assert_revisions(manifest, routing)
            self._transition(self.state, "EXECUTING", "EXECUTION_STARTED")
            for item in plan["items"]:
                if item["aut_id"] in self.state["command_evidence_refs"]:
                    continue
                self._run_plan_item(manifest, item, item["testcase_refs"], initial=True)
            self._transition(self.state, "EXECUTION_COMPLETE", "AUTOMATED_ITEMS_EXECUTED")
            return copy.deepcopy(self.state)

    def record_observation(
        self, *, testcase_id: str, actual_summary: str, evidence_refs: list[dict],
        outcome: str, actor_id: str, aut_id: str | None = None,
    ) -> dict:
        with self._lock():
            manifest = self._current_manifest()
            if self.state["status"] not in {"EXECUTION_MANIFEST_READY", "EXECUTING", "EXECUTION_COMPLETE", "FINDING", "FINDING_CLASSIFIED", "ROUTED"}:
                raise ExecutionVNextError("INVALID_TRANSITION", "initial Observation is not allowed in this state")
            state, ready, evidence, _, _, routing = self._authority(initial=True)
            self._assert_revisions(manifest, routing)
            case_ids = set(evidence["testcase_ids"])
            if testcase_id not in case_ids:
                raise ExecutionVNextError("ORACLE_NOT_FOUND", "Observation must bind an exact approved Testcase")
            if testcase_id in self.state["observation_refs"]:
                raise ExecutionVNextError("DUPLICATE_TESTCASE_DISPOSITION", "one initial Observation is allowed per testcase")
            aut_rows = {item["aut_id"]: item for item in ready["automation_items"]}
            manual_ids = {row["testcase_id"] for row in manifest["manual_testcases"]}
            if aut_id:
                item = aut_rows.get(aut_id)
                if not item or testcase_id not in item["testcase_refs"]:
                    raise ExecutionVNextError("ORACLE_NOT_FOUND", "AUT does not bind this approved Testcase")
                command_ref = self.state["command_evidence_refs"].get(aut_id)
                if not command_ref:
                    raise ExecutionVNextError("COMMAND_EVIDENCE_REQUIRED", "automated testcase requires exact command evidence")
                command = self._read_artifact(command_ref)
                if outcome == "PASS" and command["status"] != "COMMAND_PASS":
                    raise ExecutionVNextError("PASS_REQUIRES_COMMAND_PASS", "automated PASS requires COMMAND_PASS")
                if outcome == "FINDING" and not evidence_refs:
                    raise ExecutionVNextError("FINDING_EVIDENCE_REQUIRED", "automated Finding requires evidence")
                if not any(ref == command_ref for ref in evidence_refs):
                    evidence_refs = [*evidence_refs, command_ref]
            else:
                if testcase_id not in manual_ids:
                    raise ExecutionVNextError("OBSERVATION_OWNER_MISMATCH", "manual Observation requires a MANUAL_ONLY testcase")
                if not evidence_refs:
                    raise ExecutionVNextError("OBSERVATION_EVIDENCE_REQUIRED", "manual Observation requires exact evidence refs")
            checked_refs = _validate_ref_list(evidence_refs, self.project_root, "Observation evidence", required=True)
            actor = self._actor(actor_id, "OBSERVE", _sha(_json_bytes({"testcase_id": testcase_id, "outcome": outcome, "actual_summary": actual_summary})))
            obs_id = "OBS-" + hashlib.sha256(f"{self.execution_id}:{testcase_id}:{len(self.state['observation_refs'])}".encode()).hexdigest()[:12]
            collection = automation._testcase_collection_ref(self.project_root, evidence)
            observation = {
                "observation_id": obs_id, "execution_id": self.execution_id, "testcase_id": testcase_id,
                **({"aut_id": aut_id} if aut_id else {}), "oracle_ref": collection,
                "oracle_locator": testcase_id, "actual_summary": actual_summary.strip(),
                "evidence_refs": checked_refs, "actor": actor, "outcome": outcome, "recorded_at": _stamp(),
            }
            validate_observation(observation)
            observation_ref = self._save_artifact(f"evidence/observations/{obs_id}.json", observation, obs_id)
            self.state["observation_refs"][testcase_id] = observation_ref
            if outcome == "FINDING":
                finding_id = "FND-" + hashlib.sha256(_json_bytes(observation)).hexdigest()[:12]
                finding = {
                    "schema_version": 1, "artifact_class": "CANONICAL", "finding_id": finding_id,
                    "feature_id": manifest["feature_id"], "execution_id": self.execution_id,
                    "testcase_id": testcase_id, **({"aut_id": aut_id} if aut_id else {}),
                    "observation_ref": observation_ref, "oracle_ref": copy.deepcopy(collection),
                    "execution_manifest_ref": copy.deepcopy(self.state["execution_manifest_ref"]),
                    "execution_ready_ref": copy.deepcopy(manifest["execution_ready_ref"]),
                    "application_revisions": copy.deepcopy(manifest["application_revisions"]),
                    "automation_revision": manifest["automation_revision"],
                    "environment_ref": copy.deepcopy(manifest["environment_ref"]), "status": "OPEN",
                }
                validate_finding(finding)
                finding_ref = self._save_artifact(f"canonical/findings/{finding_id}.json", finding, finding_id)
                self.state["finding_refs"][finding_id] = finding_ref
            status = "FINDING" if outcome == "FINDING" else self.state["status"]
            self._transition(self.state, status, "OBSERVATION_RECORDED")
            return {"observation_ref": observation_ref, "finding_ref": self.state["finding_refs"].get(finding_id) if outcome == "FINDING" else None}

    def classify_finding(
        self, finding_id: str, classification: str, *, actor_id: str, rationale: str,
        evidence_refs: list[dict], target_repository_ids: list[str] | None = None,
        defect_proof: dict | None = None,
    ) -> dict:
        with self._lock():
            if classification not in CLASSIFICATIONS:
                raise ExecutionVNextError("INVALID_CLASSIFICATION", "classification vocabulary is frozen")
            finding_ref = self.state["finding_refs"].get(finding_id) if self.state else None
            if not finding_ref:
                raise ExecutionVNextError("FINDING_NOT_FOUND", "durable Finding is required")
            if finding_id in self.state["classification_refs"]:
                raise ExecutionVNextError("FINDING_ALREADY_CLASSIFIED", "Finding classification is immutable")
            finding = validate_finding(self._read_artifact(finding_ref))
            manifest = self._current_manifest()
            _, ready, evidence, _, _, routing = self._authority(initial=True)
            observation = self._assert_observation_binding(
                finding["observation_ref"], manifest, evidence, testcase_id=finding["testcase_id"],
            )
            collection = automation._testcase_collection_ref(self.project_root, evidence)
            if (observation["outcome"] != "FINDING" or finding["oracle_ref"] != collection
                    or finding["execution_manifest_ref"] != self.state["execution_manifest_ref"]
                    or finding["execution_ready_ref"] != manifest["execution_ready_ref"]
                    or finding["application_revisions"] != manifest["application_revisions"]
                    or finding["automation_revision"] != manifest["automation_revision"]
                    or finding["environment_ref"] != manifest["environment_ref"]):
                raise ExecutionVNextError("FINDING_STALE", "Finding is not bound to this exact execution and approved Observation")
            actor = self._actor(actor_id, "CLASSIFY_FINDING", finding_ref["sha256"])
            refs = _validate_ref_list(evidence_refs, self.project_root, "classification evidence")
            targets = list(target_repository_ids or [])
            route, _, _, topology = routing
            app_ids = {row["id"] for row in topology["repositories"] if row["id"] != ready["automation_repository"]["id"]}
            if classification == "DEFECT":
                proof = copy.deepcopy(defect_proof)
                if not proof or proof.get("mismatch_evidence_refs") is None:
                    raise ExecutionVNextError("DEFECT_PROOF_REQUIRED", "reproducibility and root-cause evidence is required")
                proof["mismatch_evidence_refs"] = _validate_ref_list(proof["mismatch_evidence_refs"], self.project_root, "DEFECT mismatch evidence", required=True)
                refs = list({(ref["id"], ref["revision"], ref["sha256"]): ref for ref in [*refs, *proof["mismatch_evidence_refs"]]}.values())
                if not targets or set(targets) - app_ids:
                    raise ExecutionVNextError("DEFECT_PROOF_REQUIRED", "DEFECT must prove approved oracle, mismatch and in-topology application targets")
            else:
                proof = None
                if targets:
                    raise ExecutionVNextError("INVALID_TARGET_REPOSITORY", "non-DEFECT route cannot target an application repository")
            classification_artifact = {
                "schema_version": 1, "artifact_class": "CANONICAL", "finding_ref": finding_ref,
                "classification": classification, "actor": actor, "rationale": rationale.strip() if isinstance(rationale, str) else rationale,
                "evidence_refs": refs, "route": ROUTES[classification], "target_repository_ids": targets,
                "classified_at": _stamp(), **({"defect_proof": proof} if proof is not None else {}),
            }
            validate_classification(classification_artifact)
            ref = self._save_artifact(f"canonical/classifications/{finding_id}.json", classification_artifact, f"{finding_id}:CLASSIFICATION")
            self.state["classification_refs"][finding_id] = ref
            if classification == "DEFECT":
                defect_id = "DEF-" + hashlib.sha256(f"{self.execution_id}:{finding_id}".encode()).hexdigest()[:12]
                defect = {
                    "schema_version": 1, "artifact_class": "HANDOFF_MANIFEST", "defect_id": defect_id,
                    "feature_id": finding["feature_id"], "finding_ref": finding_ref, "classification_ref": ref,
                    "execution_manifest_ref": copy.deepcopy(finding["execution_manifest_ref"]),
                    "execution_ready_ref": copy.deepcopy(finding["execution_ready_ref"]),
                    "approved_testware_ref": copy.deepcopy(manifest["approved_testware_ref"]),
                    "testcase_ref": copy.deepcopy(finding["oracle_ref"]), "oracle_ref": copy.deepcopy(finding["oracle_ref"]),
                    "observation_ref": copy.deepcopy(finding["observation_ref"]), "environment_ref": copy.deepcopy(manifest["environment_ref"]),
                    "original_dev_handoff_ref": copy.deepcopy(ready["dev_handoff"]),
                    "original_application_revisions": copy.deepcopy(manifest["application_revisions"]),
                    "automation_revision": manifest["automation_revision"], "target_repository_ids": targets,
                    "verification_owner": "TESTER", "state": "DEFECT_READY_FOR_DEV",
                }
                validate_defect_handoff(defect)
                reject_secrets(defect)
                defect_ref = self._save_artifact(f"canonical/defects/{defect_id}/defect-handoff-v1.json", defect, f"{defect_id}:DEFECT_HANDOFF")
                self.state["defect_handoffs"][defect_id] = defect_ref
                self._transition(self.state, "DEFECT_READY_FOR_DEV", "DEFECT_CLASSIFIED")
                return {"classification_ref": ref, "defect_handoff_ref": defect_ref}
            self._transition(self.state, "ROUTED", f"FINDING_ROUTED_{ROUTES[classification]}")
            return {"classification_ref": ref, "route": ROUTES[classification], "verified": False}

    def _dev_context(self, handoff_path: Path, ready: dict, evidence: dict):
        try:
            from tooling.lib import dev_vnext, test_kit_vnext
            raw = handoff_path.read_bytes()
            data = json.loads(raw.decode("utf-8"))
            if data.get("schema_version") != 2 or data.get("artifact_class") != "HANDOFF_MANIFEST" or data.get("state") != "READY_FOR_TEST":
                raise ValueError("exact Dev V2 READY_FOR_TEST Handoff is required")
            test_kit_vnext.load_dev_vnext_context(
                {"project_root": str(self.project_root), "handoff_path": str(handoff_path)}, evidence["authority"],
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
            if handoff_path.read_bytes() != raw:
                raise ValueError("Dev handoff changed during validation")
            return data, raw
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise ExecutionVNextError("DEV_FIX_HANDOFF_INVALID", "canonical Dev VNext rejected the fix handoff") from error

    def accept_dev_fix(self, defect_id: str, dev_handoff_path: str | Path) -> dict:
        with self._lock():
            defect_ref = self._latest_defect_handoff(defect_id)
            if not defect_ref:
                raise ExecutionVNextError("DEFECT_HANDOFF_REQUIRED", "exact current Defect Handoff is required")
            defect = self._read_artifact(defect_ref)
            if defect.get("defect_id") != defect_id or defect.get("state") != "DEFECT_READY_FOR_DEV":
                raise ExecutionVNextError("DEFECT_HANDOFF_STALE", "Defect Handoff identity or state is invalid")
            validate_defect_handoff(defect)
            cycle = len([key for key in self.state["ready_for_retest_refs"] if key == defect_id or key.startswith(defect_id + ":")]) + 1
            manifest = self._current_manifest()
            _, ready, evidence, _, _, routing = self._authority(initial=False)
            classification = validate_classification(self._read_artifact(defect["classification_ref"]))
            finding = validate_finding(self._read_artifact(defect["finding_ref"]))
            observation = self._assert_observation_binding(
                defect["observation_ref"], manifest, evidence, testcase_id=finding["testcase_id"],
            )
            if (classification["classification"] != "DEFECT" or classification["route"] != "DEV"
                    or classification["finding_ref"] != defect["finding_ref"] or finding["observation_ref"] != defect["observation_ref"]
                    or observation["outcome"] != "FINDING"
                    or defect["execution_manifest_ref"] != self.state["execution_manifest_ref"]
                    or defect["execution_ready_ref"] != manifest["execution_ready_ref"]
                    or defect["approved_testware_ref"] != manifest["approved_testware_ref"]
                    or defect["environment_ref"] != manifest["environment_ref"]
                    or defect["original_application_revisions"] != manifest["application_revisions"]
                    or defect["automation_revision"] != manifest["automation_revision"]
                    or defect["original_dev_handoff_ref"] != ready["dev_handoff"]):
                raise ExecutionVNextError("DEFECT_HANDOFF_STALE", "Defect Handoff chain differs from exact Finding and EXECUTION_READY")
            handoff_path = Path(dev_handoff_path).resolve()
            if not handoff_path.is_relative_to(self.project_root) or not handoff_path.is_file():
                raise ExecutionVNextError("DEV_FIX_HANDOFF_INVALID", "Dev fix Handoff must be an exact project artifact")
            data, raw = self._dev_context(handoff_path, ready, evidence)
            run_state = data["run_state"]
            if data["change_id"] != defect_id or run_state["change_id"] != defect_id:
                raise ExecutionVNextError("DEV_FIX_CHANGE_ID_MISMATCH", "Dev FEATURE_DELIVERY change_id must equal stable defect_id")
            if data["authority_mode"] != "FEATURE_DELIVERY":
                raise ExecutionVNextError("DEV_FIX_AUTHORITY_INVALID", "Dev fix must use normal FEATURE_DELIVERY")
            try:
                original_dev = _read_exact(ready["dev_handoff"], self.project_root, label="original Dev Handoff")
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise ExecutionVNextError("DEV_FIX_AUTHORITY_INVALID", "original Dev Handoff bytes are stale") from error
            if data["upstream_engineering_handoff"] != original_dev.get("upstream_engineering_handoff"):
                raise ExecutionVNextError("DEV_FIX_AUTHORITY_INVALID", "Dev fix must use the original BA Engineering Handoff")
            # The canonical Dev VNext adapter already verifies the original exact BA authority.
            # Here we enforce each selected repository's base and every application's final revision.
            route, roots, _, topology = routing
            app_ids = {row["id"] for row in topology["repositories"] if row["id"] != ready["automation_repository"]["id"]}
            targets = set(defect["target_repository_ids"])
            failed_revisions = defect.get("fix_base_application_revisions", defect["original_application_revisions"])
            repos = {row["id"]: row for row in run_state["repositories"]}
            if not targets.issubset(repos):
                raise ExecutionVNextError("DEV_FIX_TARGET_MISMATCH", "Dev fix run does not include all explicitly targeted repositories")
            for repository_id in targets:
                if repos[repository_id]["base_revision"] != failed_revisions[repository_id]:
                    raise ExecutionVNextError("DEV_FIX_BASE_MISMATCH", "Dev fix repository base must equal the failed application revision")
            revisions = data["repository_revisions"]
            if set(revisions) != app_ids:
                raise ExecutionVNextError("DEV_FIX_REPOSITORY_SET_MISMATCH", "Dev fix Handoff must bind every application repository")
            changed_targets = set()
            for repository_id in app_ids:
                root = roots[repository_id]
                current_head = _git(root, "rev-parse", "HEAD")
                if current_head != revisions[repository_id] or _git(root, "status", "--porcelain", "--untracked-files=all"):
                    raise ExecutionVNextError("DEV_FIX_STALE", f"application repository {repository_id} differs from clean Dev fix revision")
                previous = failed_revisions.get(repository_id)
                if previous is None:
                    raise ExecutionVNextError("DEV_FIX_REPOSITORY_SET_MISMATCH", "original Phase 7 authority omitted an application repository")
                if repository_id in targets and revisions[repository_id] != previous:
                    changed_targets.add(repository_id)
                if repository_id not in targets and revisions[repository_id] != previous:
                    raise ExecutionVNextError("DEV_FIX_NON_TARGET_DRIFT", "non-target application repository drifted")
            if not changed_targets:
                raise ExecutionVNextError("DEV_FIX_NO_TARGET_REVISION_CHANGE", "at least one targeted application revision must change")
            automation_root = roots[ready["automation_repository"]["id"]]
            if _git(automation_root, "rev-parse", "HEAD") != manifest["automation_revision"] or _git(automation_root, "status", "--porcelain", "--untracked-files=all"):
                raise ExecutionVNextError("EXECUTION_STALE", "automation revision changed during Dev fix")
            relative = handoff_path.relative_to(self.project_root).as_posix()
            fix_ref = {"id": f"{defect_id}:DEV_FIX_HANDOFF", "revision": data["technical_snapshot"]["revision"], "sha256": _sha(raw), "path": relative}
            verification_artifact = {
                "schema_version": 1, "artifact_class": "EVIDENCE", "defect_id": defect_id,
                "dev_fix_handoff_ref": fix_ref,
                "engineering_verification": copy.deepcopy(data["engineering_verification"]),
                "review": copy.deepcopy(data["review"]),
                "application_revisions": copy.deepcopy(revisions),
            }
            reject_secrets(verification_artifact)
            verify_ref = self._save_artifact(f"evidence/defects/{defect_id}/dev-fix-verification-{cycle:04d}.json", verification_artifact, f"{defect_id}:DEV_FIX_VERIFICATION:{cycle}")
            previous = failed_revisions
            current_dev_local_references = self._current_dev_local_references(
                manifest["dev_local_references"], evidence, data, routing,
            )
            ready_for_retest = {
                "schema_version": 1, "artifact_class": "HANDOFF_MANIFEST", "defect_id": defect_id,
                "feature_id": defect["feature_id"], "defect_handoff_ref": defect_ref,
                "finding_ref": defect["finding_ref"], "original_execution_manifest_ref": defect["execution_manifest_ref"],
                "approved_testware_ref": defect["approved_testware_ref"], "testcase_ref": defect["testcase_ref"],
                "automation_revision": manifest["automation_revision"],
                "previous_application_revisions": copy.deepcopy(previous),
                "fixed_application_revisions": copy.deepcopy(revisions),
                "dev_fix_handoff_ref": fix_ref, "dev_fix_verification_ref": verify_ref,
                "environment_ref": copy.deepcopy(manifest["environment_ref"]),
                "dev_local_references": current_dev_local_references,
                "verification_owner": "TESTER", "state": "READY_FOR_RETEST",
            }
            validate_ready_for_retest(ready_for_retest)
            reject_secrets(ready_for_retest)
            ready_ref = self._save_artifact(f"canonical/defects/{defect_id}/ready-for-retest-{cycle:04d}.json", ready_for_retest, f"{defect_id}:READY_FOR_RETEST:{cycle}")
            self.state["ready_for_retest_refs"][f"{defect_id}:{cycle}"] = ready_ref
            self._transition(self.state, "READY_FOR_RETEST", "DEV_FIX_ACCEPTED")
            return {"ready_for_retest_ref": ready_ref, "dev_fix_handoff_ref": fix_ref, "dev_fix_verification_ref": verify_ref}

    def _latest_defect_handoff(self, defect_id: str):
        if not self.state:
            return None
        matching = [ref for key, ref in self.state["defect_handoffs"].items() if key == defect_id or key.startswith(defect_id + ":")]
        return matching[-1] if matching else None

    def _latest_ready_for_retest(self, defect_id: str):
        if not self.state:
            return None
        matching = [ref for key, ref in self.state["ready_for_retest_refs"].items() if key == defect_id or key.startswith(defect_id + ":")]
        return matching[-1] if matching else None

    def prepare_reopened_defect_handoff(self, defect_id: str) -> dict:
        """Continue a same-ID Dev VNext cycle after Tester records REOPENED."""
        with self._lock():
            if not self.state or self.state["status"] != "REOPENED":
                raise ExecutionVNextError("REOPENED_REQUIRED", "a Tester-owned REOPENED artifact is required")
            matching = [
                (key, ref) for key, ref in self.state["reopened_refs"].items()
                if key.startswith(defect_id + ":") and self._read_artifact(ref).get("defect_id") == defect_id
            ]
            if not matching:
                raise ExecutionVNextError("REOPENED_REQUIRED", "no exact reopen lineage exists for this defect")
            reopened_ref = matching[-1][1]
            reopened = self._read_artifact(reopened_ref)
            prior_ref = self._latest_defect_handoff(defect_id)
            if not prior_ref:
                raise ExecutionVNextError("DEFECT_HANDOFF_REQUIRED", "stable Defect Handoff lineage is missing")
            previous = self._read_artifact(prior_ref)
            new_finding_ref = reopened["new_finding_ref"]
            defect = copy.deepcopy(previous)
            defect.update({
                "fix_base_application_revisions": copy.deepcopy(reopened["fixed_application_revisions"]),
                "prior_reopened_ref": reopened_ref,
                "reopen_observation_ref": reopened["new_observation_ref"],
                "state": "DEFECT_READY_FOR_DEV",
            })
            cycle = len([key for key in self.state["defect_handoffs"] if key == defect_id or key.startswith(defect_id + ":")]) + 1
            validate_defect_handoff(defect)
            ref = self._save_artifact(
                f"canonical/defects/{defect_id}/defect-handoff-cycle-{cycle:04d}.json",
                defect, f"{defect_id}:DEFECT_HANDOFF:{cycle}",
            )
            self.state["defect_handoffs"][f"{defect_id}:{cycle}"] = ref
            self._transition(self.state, "DEFECT_READY_FOR_DEV", "REOPENED_DEFECT_RETURNED_TO_DEV")
            return {"defect_handoff_ref": ref, "defect_id": defect_id, "cycle": cycle}

    def _retest_guard(self, defect_id: str, ready_ref: dict):
        if not self.state or self.state["status"] not in {"READY_FOR_RETEST", "RETESTING"}:
            raise ExecutionVNextError("READY_FOR_RETEST_REQUIRED", "a fresh accepted Dev fix is required for this retest")
        ready_for_retest = self._read_artifact(ready_ref)
        manifest = self._current_manifest()
        state, ready, evidence, _, plan, routing = self._authority(initial=False)
        self._check_environment(ready_for_retest["environment_ref"])
        if (ready_for_retest.get("state") != "READY_FOR_RETEST" or ready_for_retest.get("verification_owner") != "TESTER"
                or ready_for_retest.get("defect_id") != defect_id
                or ready_for_retest["original_execution_manifest_ref"] != self.state["execution_manifest_ref"]
                or ready_for_retest["automation_revision"] != manifest["automation_revision"]
                or ready_for_retest["environment_ref"] != manifest["environment_ref"]
                or ready_for_retest["approved_testware_ref"] != manifest["approved_testware_ref"]):
            raise ExecutionVNextError("READY_FOR_RETEST_STALE", "READY_FOR_RETEST is not bound to this exact execution attempt")
        validate_ready_for_retest(ready_for_retest)
        roots = self._assert_revisions(manifest, routing, expected_revisions=ready_for_retest["fixed_application_revisions"])
        if ready["automation_revision"] != manifest["automation_revision"]:
            raise ExecutionVNextError("EXECUTION_STALE", "automation revision changed before retest")
        defect = validate_defect_handoff(self._read_artifact(ready_for_retest["defect_handoff_ref"]))
        finding = validate_finding(self._read_artifact(ready_for_retest["finding_ref"]))
        classification = validate_classification(self._read_artifact(defect["classification_ref"]))
        testcase_id = finding["testcase_id"]
        if (ready_for_retest["finding_ref"] != defect["finding_ref"]
                or classification["classification"] != "DEFECT" or classification["route"] != "DEV"
                or classification["finding_ref"] != defect["finding_ref"]
                or finding["observation_ref"] != defect["observation_ref"]
                or ready_for_retest["testcase_ref"] != defect["testcase_ref"]
                or ready_for_retest["previous_application_revisions"] != defect.get("fix_base_application_revisions", defect["original_application_revisions"])):
            raise ExecutionVNextError("READY_FOR_RETEST_STALE", "retest oracle differs from original approved Testcase")
        observation = self._assert_observation_binding(defect["observation_ref"], manifest, evidence, testcase_id=testcase_id)
        if observation["outcome"] != "FINDING":
            raise ExecutionVNextError("FINDING_STALE", "original Defect Observation no longer records FINDING")
        fix_path = self.project_root / PurePosixPath(ready_for_retest["dev_fix_handoff_ref"]["path"])
        fix_data, fix_bytes = self._dev_context(fix_path, ready, evidence)
        if (_sha(fix_bytes) != ready_for_retest["dev_fix_handoff_ref"]["sha256"]
                or fix_data["change_id"] != defect_id or fix_data["authority_mode"] != "FEATURE_DELIVERY"
                or fix_data["repository_revisions"] != ready_for_retest["fixed_application_revisions"]
                or ready_for_retest["dev_fix_handoff_ref"]["revision"] != fix_data["technical_snapshot"]["revision"]):
            raise ExecutionVNextError("DEV_FIX_STALE", "READY_FOR_RETEST Dev fix handoff changed or drifted")
        verification = self._read_artifact(ready_for_retest["dev_fix_verification_ref"])
        if (verification.get("defect_id") != defect_id
                or verification.get("dev_fix_handoff_ref") != ready_for_retest["dev_fix_handoff_ref"]
                or verification.get("engineering_verification") != fix_data["engineering_verification"]
                or verification.get("review") != fix_data["review"]
                or verification.get("application_revisions") != ready_for_retest["fixed_application_revisions"]
                or not fix_data["engineering_verification"]["checks"]
                or any(row["status"] != "PASS" for row in fix_data["engineering_verification"]["checks"])
                or fix_data["review"]["blocking_findings"]):
            raise ExecutionVNextError("DEV_FIX_VERIFICATION_STALE", "fresh Dev review or verification evidence no longer passes")
        for row in ready_for_retest["dev_local_references"]:
            _validate_ref_list(row["evidence_refs"], self.project_root, "READY_FOR_RETEST Dev-local evidence", required=True)
        plan_item = next((item for item in plan["items"] if testcase_id in item["testcase_refs"]), None)
        return ready_for_retest, manifest, state, ready, evidence, routing, roots, testcase_id, plan_item

    def execute_retest(self, defect_id: str) -> dict:
        with self._lock():
            ready_ref = self._latest_ready_for_retest(defect_id)
            if not ready_ref:
                raise ExecutionVNextError("READY_FOR_RETEST_REQUIRED", "exact READY_FOR_RETEST handoff is required")
            ready_for_retest, manifest, _, _, _, routing, roots, testcase_id, plan_item = self._retest_guard(defect_id, ready_ref)
            if not plan_item:
                return {"status": "MANUAL_ONLY", "testcase_id": testcase_id}
            self._transition(self.state, "RETESTING", "TESTER_RETEST_STARTED")
            ref, evidence = self._run_plan_item(
                manifest, plan_item, [testcase_id], expected_app_revisions=ready_for_retest["fixed_application_revisions"], initial=False,
            )
            # The Phase 7 authority remains byte-exact; after a Dev fix only its original app-revision check is intentionally superseded.
            self._retest_guard(defect_id, ready_ref)
            return {"command_evidence_ref": ref, "command_status": evidence["status"], "testcase_id": testcase_id}

    def record_retest_observation(
        self, defect_id: str, *, actual_summary: str, evidence_refs: list[dict], outcome: str, actor_id: str,
    ) -> dict:
        with self._lock():
            ready_ref = self._latest_ready_for_retest(defect_id)
            if not ready_ref:
                raise ExecutionVNextError("READY_FOR_RETEST_REQUIRED", "exact READY_FOR_RETEST handoff is required")
            retest, manifest, _, _, evidence, routing, _, testcase_id, plan_item = self._retest_guard(defect_id, ready_ref)
            checked_refs = _validate_ref_list(evidence_refs, self.project_root, "retest evidence", required=True)
            if plan_item:
                command_ref = self.state["command_evidence_refs"].get(plan_item["aut_id"])
                if not command_ref:
                    raise ExecutionVNextError("COMMAND_EVIDENCE_REQUIRED", "original automated testcase must be executed for retest")
                command = self._read_artifact(command_ref)
                if outcome == "PASS" and command["status"] != "COMMAND_PASS":
                    raise ExecutionVNextError("PASS_REQUIRES_COMMAND_PASS", "retest PASS requires COMMAND_PASS")
                if command_ref not in checked_refs:
                    checked_refs.append(command_ref)
            else:
                manual_ids = {row["testcase_id"] for row in manifest["manual_testcases"]}
                if testcase_id not in manual_ids:
                    raise ExecutionVNextError("OBSERVATION_OWNER_MISMATCH", "original testcase is neither automated nor manual")
            actor = self._actor(actor_id, "RETEST", ready_ref["sha256"])
            collection = automation._testcase_collection_ref(self.project_root, evidence)
            observation_id = "OBS-" + hashlib.sha256(f"{defect_id}:{ready_ref['sha256']}:{outcome}".encode()).hexdigest()[:12]
            observation = {
                "observation_id": observation_id, "execution_id": self.execution_id, "testcase_id": testcase_id,
                **({"aut_id": plan_item["aut_id"]} if plan_item else {}), "oracle_ref": collection,
                "oracle_locator": testcase_id, "actual_summary": actual_summary.strip(),
                "evidence_refs": checked_refs, "actor": actor, "outcome": outcome, "recorded_at": _stamp(),
            }
            validate_observation(observation)
            observation_ref = self._save_artifact(f"evidence/retests/{defect_id}-{observation_id}.json", observation, observation_id)
            self._retest_guard(defect_id, ready_ref)
            if outcome == "PASS":
                verified = {
                    "schema_version": 1, "artifact_class": "HANDOFF_MANIFEST", "feature_id": manifest["feature_id"],
                    "execution_manifest_ref": self.state["execution_manifest_ref"], "execution_ready_ref": manifest["execution_ready_ref"],
                    "approved_testware_ref": manifest["approved_testware_ref"],
                    "application_revisions": copy.deepcopy(retest["fixed_application_revisions"]),
                    "automation_revision": manifest["automation_revision"], "environment_ref": manifest["environment_ref"],
                    "observations": [*self.state["observation_refs"].values(), observation_ref],
                    "dev_local_references": copy.deepcopy(retest["dev_local_references"]),
                    "optional_blocked_testcases": copy.deepcopy(manifest["optional_blocked_testcases"]),
                    "defect_history": [self.state["finding_refs"], self.state["classification_refs"], self.state["defect_handoffs"], self.state["ready_for_retest_refs"], self.state["reopened_refs"]],
                    "verification_actor": actor, "verified_at": _stamp(), "state": "VERIFIED",
                }
                validate_verified_handoff(verified)
                reject_secrets(verified)
                verified_ref = self._save_artifact("handoffs/verified-after-retest-v1.json", verified, f"{self.execution_id}:VERIFIED")
                self.state["verified_ref"] = verified_ref
                self.state["retest_observation_ref"] = observation_ref
                self._transition(self.state, "VERIFIED", "TESTER_RETEST_PASSED")
                return {"verified_ref": verified_ref, "observation_ref": observation_ref, "state": "VERIFIED"}
            prior_refs = [
                ref for ref in self.state["reopened_refs"].values()
                if self._read_artifact(ref).get("defect_id") == defect_id
            ]
            reopen_count = len(prior_refs) + 1
            previous = prior_refs[-1] if prior_refs else None
            finding_id = "FND-" + hashlib.sha256(_json_bytes(observation)).hexdigest()[:12]
            finding = {
                "schema_version": 1, "artifact_class": "CANONICAL", "finding_id": finding_id,
                "feature_id": manifest["feature_id"], "execution_id": self.execution_id,
                "testcase_id": testcase_id, **({"aut_id": plan_item["aut_id"]} if plan_item else {}),
                "observation_ref": observation_ref, "oracle_ref": copy.deepcopy(collection),
                "execution_manifest_ref": copy.deepcopy(self.state["execution_manifest_ref"]),
                "execution_ready_ref": copy.deepcopy(manifest["execution_ready_ref"]),
                "application_revisions": copy.deepcopy(retest["fixed_application_revisions"]),
                "automation_revision": manifest["automation_revision"],
                "environment_ref": copy.deepcopy(manifest["environment_ref"]), "status": "OPEN",
            }
            validate_finding(finding)
            new_finding_ref = self._save_artifact(f"canonical/findings/{finding_id}.json", finding, finding_id)
            self.state["finding_refs"][finding_id] = new_finding_ref
            reopened = {
                "schema_version": 1, "artifact_class": "CANONICAL", "defect_id": defect_id,
                "prior_defect_handoff_ref": retest["defect_handoff_ref"], "ready_for_retest_ref": ready_ref,
                "new_finding_ref": new_finding_ref, "new_observation_ref": observation_ref,
                "fixed_application_revisions": copy.deepcopy(retest["fixed_application_revisions"]),
                "automation_revision": manifest["automation_revision"], "environment_ref": manifest["environment_ref"],
                "reopen_count": reopen_count, "prior_reopen_ref": previous, "state": "REOPENED",
            }
            validate_reopened(reopened)
            reject_secrets(reopened)
            reopened_ref = self._save_artifact(f"canonical/defects/{defect_id}/reopened-{reopen_count:04d}.json", reopened, f"{defect_id}:REOPENED:{reopen_count}")
            self.state["reopened_refs"][f"{defect_id}:{reopen_count}"] = reopened_ref
            self._transition(self.state, "REOPENED", "TESTER_RETEST_FAILED")
            return {"reopened_ref": reopened_ref, "observation_ref": observation_ref, "state": "REOPENED"}

    def finalize_verified(self, *, actor_id: str) -> dict:
        """Tester-only straight-pass closure. Defect attempts close only via retest."""
        with self._lock():
            manifest = self._current_manifest()
            if self.state["status"] not in {"EXECUTION_COMPLETE", "FINDING"}:
                raise ExecutionVNextError("INVALID_TRANSITION", "initial final verification requires completed execution")
            if self.state["finding_refs"]:
                raise ExecutionVNextError("OPEN_FINDING", "a Finding must be classified and routed before final verification")
            _, ready, evidence, suitability, _, routing = self._authority(initial=True)
            self._assert_revisions(manifest, routing)
            required = {row["testcase_id"] for row in suitability["rows"] if row["required"] and row["owner"] in {"TEST_AUTOMATION", "MANUAL"}}
            expected_observations = {case_id for case_id in evidence["testcase_ids"] if case_id in required}
            if set(self.state["observation_refs"]) != expected_observations:
                raise ExecutionVNextError(
                    "TESTCASE_ACCOUNTING_INCOMPLETE",
                    f"all required automated/manual Testcases need one Observation; expected={sorted(expected_observations)} actual={sorted(self.state['observation_refs'])}",
                )
            for testcase_id, ref in self.state["observation_refs"].items():
                observation = self._assert_observation_binding(ref, manifest, evidence, testcase_id=testcase_id)
                if observation["outcome"] != "PASS":
                    raise ExecutionVNextError("OPEN_FINDING", "all required Observations must PASS")
            actor = self._actor(actor_id, "FINAL_VERIFICATION", self.state["execution_manifest_ref"]["sha256"])
            verified = {
                "schema_version": 1, "artifact_class": "HANDOFF_MANIFEST", "feature_id": manifest["feature_id"],
                "execution_manifest_ref": self.state["execution_manifest_ref"], "execution_ready_ref": manifest["execution_ready_ref"],
                "approved_testware_ref": manifest["approved_testware_ref"],
                "application_revisions": copy.deepcopy(manifest["application_revisions"]),
                "automation_revision": manifest["automation_revision"], "environment_ref": manifest["environment_ref"],
                "observations": list(self.state["observation_refs"].values()),
                "dev_local_references": copy.deepcopy(manifest["dev_local_references"]),
                "optional_blocked_testcases": copy.deepcopy(manifest["optional_blocked_testcases"]),
                "defect_history": [], "verification_actor": actor,
                "verified_at": _stamp(), "state": "VERIFIED",
            }
            validate_verified_handoff(verified)
            reject_secrets(verified)
            verified_ref = self._save_artifact("handoffs/verified-v1.json", verified, f"{self.execution_id}:VERIFIED")
            self.state["verified_ref"] = verified_ref
            self._transition(self.state, "VERIFIED", "TESTER_FINAL_VERIFICATION")
            return {"verified_ref": verified_ref, "state": "VERIFIED"}

    def revalidate_verified(self) -> dict:
        """Reject local, authority, environment or repository drift after verification."""
        with self._lock():
            if not self.state or self.state.get("status") != "VERIFIED" or not self.state.get("verified_ref"):
                raise ExecutionVNextError("VERIFIED_REQUIRED", "no durable VERIFIED handoff exists")
            verified = validate_verified_handoff(self._read_artifact(self.state["verified_ref"]))
            manifest = self._current_manifest()
            has_defect_cycle = bool(self.state["defect_handoffs"])
            _, ready, evidence, _, _, routing = self._authority(initial=not has_defect_cycle)
            if (verified["execution_manifest_ref"] != self.state["execution_manifest_ref"]
                    or verified["execution_ready_ref"] != manifest["execution_ready_ref"]
                    or verified["approved_testware_ref"] != manifest["approved_testware_ref"]
                    or verified["automation_revision"] != manifest["automation_revision"]
                    or ready["automation_revision"] != verified["automation_revision"]):
                raise ExecutionVNextError("EXECUTION_STALE", "VERIFIED authority references drifted")
            self._check_environment(verified["environment_ref"])
            self._assert_revisions(manifest, routing, expected_revisions=verified["application_revisions"])
            observations = [self._assert_observation_binding(ref, manifest, evidence) for ref in verified["observations"]]
            for row in verified["dev_local_references"]:
                _validate_ref_list(row["evidence_refs"], self.project_root, "VERIFIED Dev-local evidence", required=True)
            if has_defect_cycle:
                if not observations or observations[-1]["outcome"] != "PASS":
                    raise ExecutionVNextError("VERIFIED_STALE", "defect closure must retain a passing Tester retest Observation")
            elif any(row["outcome"] != "PASS" for row in observations):
                raise ExecutionVNextError("VERIFIED_STALE", "straight-pass VERIFIED contains a non-PASS Observation")
            reopened_findings = set()
            for ref in self.state["reopened_refs"].values():
                reopened_findings.add(self._read_artifact(ref)["new_finding_ref"]["id"])
            for finding_id in self.state["finding_refs"]:
                if finding_id not in self.state["classification_refs"] and finding_id not in reopened_findings:
                    raise ExecutionVNextError("OPEN_FINDING", "VERIFIED attempt contains an unclassified Finding")
            return verified


__all__ = [
    "CLASSIFICATIONS", "ROUTES", "ExecutionRuntime", "ExecutionVNextError",
    "validate_classification", "validate_environment_descriptor", "validate_execution_manifest",
    "validate_defect_handoff", "validate_finding", "validate_observation", "validate_ready_for_retest",
    "validate_reopened", "validate_verified_handoff",
]
