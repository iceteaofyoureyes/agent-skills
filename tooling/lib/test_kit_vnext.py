"""Narrow VNext authority adapter over the preserved Test Kit V1 lane."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import re

from . import test_kit_v1 as design
from . import test_kit_v1_cases as cases
from . import dev_vnext
from shared.sdlc.authority.approved_baseline import (
    ApprovedBaseline,
    _parse_source_rows,
    _unknown_sentences,
)
from shared.sdlc.schema import validate_reference

import ba_vnext
import delivery_manifest


class TestAuthorityError(ValueError):
    pass


def _ref_signature(refs):
    return tuple(sorted((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in refs))


@dataclass(frozen=True)
class TestAuthorityContext:
    mode: str
    vnext_authority: bool
    baseline: ApprovedBaseline
    handoff_ref: dict
    candidate_ref: dict
    approval_ref: dict
    refs: tuple[dict, ...]
    project_root: Path | None = None
    baseline_identity: dict | None = None
    ux_context: dict | None = None
    ux_required: bool = False
    dev_context: dict | None = None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _outer_ref(path: Path, root: Path, revision: str) -> dict:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise TestAuthorityError("BA VNext handoff must be inside the declared project root") from error
    return {"path": relative, "revision": revision, "sha256": _sha(path)}


def _authority_refs(handoff: dict, candidate: dict, approval_receipt: dict, root: Path) -> tuple[dict, ...]:
    refs = []
    sources = handoff["authoritative_sources"]
    for role in ("business_rules", "srs", "decisions"):
        source = sources[role]
        source_path = validate_reference(source, root, revision=True)
        refs.append({"id": f"BA:{role}", "revision": source["revision"], "sha256": source["sha256"], "path": str(source_path)})
    manifest = handoff["ba_baseline"]["manifest"]
    approval = handoff["approval_receipt"]
    receipt_path = validate_reference(approval, root, revision=True)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    manifest_path = validate_reference(manifest, root, revision=True)
    refs.extend((
        {"id": "BA:BASELINE_CANDIDATE", "revision": manifest["revision"], "sha256": manifest["sha256"], "path": str(manifest_path)},
        {"id": "BA:APPROVAL_RECEIPT", "revision": approval["revision"], "sha256": approval["sha256"], "path": str(receipt_path)},
    ))
    decision_ref = receipt["decision_ref"]
    decision_path = validate_reference(decision_ref, root, revision=True)
    refs.append({"id": "BA:DECISION", "revision": decision_ref["revision"], "sha256": decision_ref["sha256"], "path": str(decision_path)})
    foundation = candidate.get("project_foundation")
    if foundation:
        for key in ("manifest", "provenance", "approval"):
            ref = foundation[key]
            ref_path = validate_reference(ref, root, revision=True)
            refs.append({"id": f"BA:FOUNDATION:{key.upper()}", "revision": ref["revision"], "sha256": ref["sha256"], "path": str(ref_path)})
        if "previous" in foundation:
            ref = foundation["previous"]
            ref_path = validate_reference(ref, root, revision=True)
            refs.append({"id": "BA:FOUNDATION:PREVIOUS", "revision": ref["revision"], "sha256": ref["sha256"], "path": str(ref_path)})
    return tuple(refs)


def _baseline_from_candidate(candidate: dict, handoff_path: Path, handoff_ref: dict, root: Path) -> ApprovedBaseline:
    source_paths = {}
    source_hashes = {}
    for role, ref in candidate["sources"].items():
        source_paths[role] = validate_reference(ref, root, revision=True)
        source_hashes[role] = ref["sha256"]
    requirements = _parse_source_rows(source_paths["srs"], "FR", 3, source_path=candidate["sources"]["srs"]["path"])
    business_rules = _parse_source_rows(source_paths["business_rules"], "BR", 3, source_path=candidate["sources"]["business_rules"]["path"])
    unknowns = _unknown_sentences((*requirements, *business_rules))
    return ApprovedBaseline(
        candidate["feature"]["id"],
        candidate["feature"]["title"],
        candidate["revision"],
        handoff_path,
        handoff_ref["sha256"],
        source_paths,
        source_hashes,
        requirements,
        business_rules,
        tuple(candidate["blocking"] + candidate["non_blocking"]),
        unknowns,
    )


def load_vnext_authority(
    handoff_path: str | Path,
    *,
    project_root: str | Path,
    human_actor_authenticator,
    foundation_authenticator=None,
) -> TestAuthorityContext:
    """Revalidate the canonical BA Handoff VNext reader and its exact Human proof."""
    root = Path(project_root).resolve()
    path = Path(handoff_path).resolve()
    try:
        raw = path.read_bytes()
        handoff = json.loads(raw.decode("utf-8"))
        ref = _outer_ref(path, root, handoff["ba_baseline"]["revision"])
        result = ba_vnext.validate_handoff(
            handoff,
            root,
            human_actor_authenticator=human_actor_authenticator,
            foundation_authenticator=foundation_authenticator,
        )
        if path.read_bytes() != raw or _sha(path) != ref["sha256"]:
            raise ValueError("Engineering Handoff bytes changed during trusted Human authentication")
        if result.get("status") != "APPROVED_BASELINE" or result.get("human_approval") is not True:
            raise ValueError("BA VNext authority is not Human approved")
        candidate = result["baseline"]
        refs = _authority_refs(handoff, candidate, handoff["approval_receipt"], root)
        baseline = _baseline_from_candidate(candidate, path, ref, root)
        return TestAuthorityContext(
            "VNEXT", True, baseline,
            {"id": f"{baseline.feature_id}:BA_HANDOFF", "revision": ref["revision"], "sha256": ref["sha256"], "path": str(path)},
            dict(handoff["ba_baseline"]["manifest"]),
            dict(handoff["approval_receipt"]),
            tuple((*refs, {"id": "BA:handoff", "revision": ref["revision"], "sha256": ref["sha256"], "path": str(path)})),
            root,
            {"id": candidate["id"], "revision": candidate["revision"], "semantic_sha256": candidate["semantic_sha256"]},
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        if isinstance(error, TestAuthorityError):
            raise
        raise TestAuthorityError(str(error)) from error


def load_approved_ux_context(
    request: dict,
    *,
    feature_id: str,
    human_actor_authenticator,
) -> dict:
    """Test-owned reader for the existing UX approval receipt V1/V2 contract."""
    try:
        if not isinstance(request, dict) or set(request) - {"root", "contract", "approval_receipt", "prototype"}:
            raise ValueError("UX context request has an unsupported shape")
        root = Path(request["root"]).resolve()

        def source_path(relative: str) -> Path:
            path = (root / relative).resolve()
            if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
                raise ValueError(f"UX source is unavailable or outside its root: {relative}")
            return path

        contract_ref = request["contract"]
        if not isinstance(contract_ref, dict) or set(contract_ref) != {"path", "revision", "sha256"}:
            raise ValueError("approved UX semantic contract ref is required")
        contract_path = source_path(contract_ref["path"])
        contract_bytes = contract_path.read_bytes()
        if hashlib.sha256(contract_bytes).hexdigest() != contract_ref["sha256"]:
            raise ValueError("approved UX semantic contract hash mismatch")
        receipt_ref = request["approval_receipt"]
        if not isinstance(receipt_ref, dict) or set(receipt_ref) != {"path", "sha256"}:
            raise ValueError("approved UX receipt ref is required")
        receipt_path = source_path(receipt_ref["path"])
        receipt_bytes = receipt_path.read_bytes()
        if hashlib.sha256(receipt_bytes).hexdigest() != receipt_ref["sha256"] or receipt_path == contract_path:
            raise ValueError("UX approval receipt bytes are stale or overlap the semantic contract")
        receipt = delivery_manifest.read_mapping(receipt_path)
        required = {
            "schema_version", "feature_id", "decision", "decision_type", "approved_by",
            "recorded_at_utc", "revision", "immutable", "semantic_snapshot_sha256",
            "semantic_snapshot_sha256_method", "sources", "source_commit", "source_branch",
            "reapproval_required_if_source_bytes_change",
        }
        optional = {"prototype_authority", "formal_browser_AT_WCAG_testing", "conformance_PASS_claimed"}
        if not isinstance(receipt, dict) or not required.issubset(receipt) or set(receipt) - required - optional:
            raise ValueError("UX approval receipt does not match the existing V1/V2 contract")
        version = receipt["schema_version"]
        if type(version) is not int or version not in (1, 2):
            raise ValueError("UX approval receipt schema version must be 1 or 2")
        if not isinstance(contract_ref["revision"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", contract_ref["revision"]):
            raise ValueError("UX semantic contract revision is invalid")
        if version == 1 and "prototype_authority" not in receipt:
            raise ValueError("UX V1 receipt requires prototype_authority REVIEW_EVIDENCE")
        if (receipt["feature_id"] != feature_id or receipt["revision"] != contract_ref["revision"]
                or receipt["decision"] != "APPROVE" or receipt["approved_by"] != "Human"
                or receipt["decision_type"] != "HUMAN_EXPLICIT_EXACT_SNAPSHOT_APPROVAL"
                or receipt["immutable"] is not True
                or receipt["reapproval_required_if_source_bytes_change"] is not True):
            raise ValueError("UX approval receipt feature, revision or explicit Human approval does not match")
        recorded = receipt["recorded_at_utc"]
        if not isinstance(recorded, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", recorded):
            raise ValueError("UX approval receipt timestamp must be UTC")
        if (not isinstance(receipt["source_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", receipt["source_commit"])
                or not isinstance(receipt["source_branch"], str) or not receipt["source_branch"].strip()):
            raise ValueError("UX approval receipt source provenance is required")
        sources = receipt["sources"]
        if not isinstance(sources, dict) or not sources or (version == 1 and len(sources) != 2):
            raise ValueError("UX approval receipt sources do not match V1/V2 requirements")
        if sources.get(contract_ref["path"]) != contract_ref["sha256"]:
            raise ValueError("UX receipt does not bind the exact semantic contract")
        if len(sources) > 1 and receipt.get("prototype_authority") != "REVIEW_EVIDENCE":
            raise ValueError("UX prototype and supporting sources remain REVIEW_EVIDENCE")
        if "prototype_authority" in receipt and receipt["prototype_authority"] != "REVIEW_EVIDENCE":
            raise ValueError("UX prototype authority must be REVIEW_EVIDENCE")
        if ("formal_browser_AT_WCAG_testing" in receipt and not isinstance(receipt["formal_browser_AT_WCAG_testing"], str)
                or "conformance_PASS_claimed" in receipt and type(receipt["conformance_PASS_claimed"]) is not bool):
            raise ValueError("UX testing provenance has invalid field types")
        method = delivery_manifest.UX_SNAPSHOT_METHOD if version == 1 else delivery_manifest.UX_SNAPSHOT_METHOD_V2
        if receipt["semantic_snapshot_sha256_method"] != method:
            raise ValueError("UX snapshot method is unsupported")
        snapshot_hash = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
        if receipt["semantic_snapshot_sha256"] != snapshot_hash:
            raise ValueError("UX semantic snapshot hash mismatch")

        byte_refs = []
        refs = []
        for relative, digest in sources.items():
            if not isinstance(relative, str) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError("UX receipt source refs must bind exact SHA-256 values")
            path = source_path(relative)
            if path == receipt_path or _sha(path) != digest:
                raise ValueError(f"UX source bytes changed: {relative}")
            byte_refs.append({"id": f"{feature_id}:UX_SOURCE:{relative}", "revision": contract_ref["revision"], "sha256": digest, "path": str(path)})
            if relative != contract_ref["path"]:
                refs.append({"id": f"{feature_id}:UX_SOURCE:{relative}", "revision": contract_ref["revision"], "sha256": digest, "path": str(path)})
        contract_binding = {"id": f"{feature_id}:UX", "revision": contract_ref["revision"], "sha256": contract_ref["sha256"], "path": str(contract_path)}
        receipt_binding = {"id": f"{feature_id}:UX_RECEIPT", "revision": contract_ref["revision"], "sha256": receipt_ref["sha256"], "path": str(receipt_path)}
        refs = [contract_binding, receipt_binding, *refs]
        if request.get("prototype") is not None:
            prototype = request["prototype"]
            if not isinstance(prototype, dict) or set(prototype) != {"path", "sha256", "authority"} or prototype["authority"] != "REVIEW_EVIDENCE":
                raise ValueError("UX prototype can only be recorded as REVIEW_EVIDENCE")
            prototype_path = source_path(prototype["path"])
            if _sha(prototype_path) != prototype["sha256"] or sources.get(prototype["path"]) != prototype["sha256"]:
                raise ValueError("UX prototype is not bound by the approved receipt")

        if not callable(human_actor_authenticator) or human_actor_authenticator("Human", receipt) is not True:
            raise ValueError("UX approval requires trusted Human authentication")
        if contract_path.read_bytes() != contract_bytes or receipt_path.read_bytes() != receipt_bytes:
            raise ValueError("UX contract or receipt changed during trusted Human authentication")
        for ref in byte_refs:
            if _sha(Path(ref["path"])) != ref["sha256"]:
                raise ValueError("UX source bytes changed during trusted Human authentication")
        return {
            "root": str(root), "contract_path": str(contract_path),
            "contract_ref": contract_binding, "approval_receipt_ref": receipt_binding,
            "source_refs": byte_refs, "refs": refs, "receipt": receipt,
            "receipt_sha256": receipt_ref["sha256"], "snapshot_sha256": snapshot_hash,
            "prototype_authority": receipt.get("prototype_authority", "REVIEW_EVIDENCE"),
            "request": request,
        }
    except (OSError, ValueError, KeyError, TypeError) as error:
        if isinstance(error, TestAuthorityError):
            raise
        raise TestAuthorityError(str(error)) from error


def load_dev_vnext_context(
    request: dict,
    authority: TestAuthorityContext,
    *,
    ba_human_actor_authenticator,
    technical_authenticator=None,
    foundation_authenticator=None,
) -> dict:
    """Validate optional Dev V2 context as exact technical evidence only."""
    try:
        root = Path(request["project_root"]).resolve()
        handoff_path = Path(request["handoff_path"]).resolve()
        raw = handoff_path.read_bytes()
        data = json.loads(raw.decode("utf-8"))
        if data.get("authority_mode") != "FEATURE_DELIVERY":
            raise ValueError("Dev technical context must be a feature-delivery VNext handoff")
        upstream = data.get("upstream_engineering_handoff")
        upstream_path = validate_reference(upstream, root, revision=True) if isinstance(upstream, dict) else None
        if not isinstance(upstream, dict) or (str(upstream_path), upstream.get("revision"), upstream.get("sha256")) != (
            authority.handoff_ref["path"], authority.handoff_ref["revision"], authority.handoff_ref["sha256"],
        ):
            raise ValueError("Dev context must bind the exact current BA Engineering Handoff VNext")
        snapshot_ref = data["technical_snapshot"]
        snapshot_path = validate_reference(snapshot_ref, root, revision=True)
        result = dev_vnext.read_artifact(
            data, "handoff", root,
            ba_authenticator=ba_human_actor_authenticator,
            technical_authenticator=technical_authenticator,
            foundation_authenticator=foundation_authenticator,
        )
        if result.get("mode") != "VNEXT" or result.get("vnext_authority") is not True:
            raise ValueError("Dev legacy handoff cannot provide VNext technical context")
        if handoff_path.read_bytes() != raw or _sha(handoff_path) != hashlib.sha256(raw).hexdigest():
            raise ValueError("Dev Handoff bytes changed during trusted authentication")
        refs = [
            {"id": "DEV:HANDOFF", "revision": snapshot_ref["revision"], "sha256": hashlib.sha256(raw).hexdigest(), "path": str(handoff_path)},
            {"id": "DEV:TECHNICAL_SNAPSHOT", "revision": snapshot_ref["revision"], "sha256": snapshot_ref["sha256"], "path": str(snapshot_path)},
        ]
        for index, ref in enumerate(data.get("engineering_decisions", []), 1):
            path = validate_reference(ref, root, revision=True)
            refs.append({"id": f"DEV:ENGINEERING_DECISION:{index}", "revision": ref["revision"], "sha256": ref["sha256"], "path": str(path)})
        return {
            "mode": "VNEXT", "authority_mode": "TECHNICAL_CONTEXT_ONLY",
            "handoff_ref": refs[0], "technical_snapshot_ref": refs[1],
            "refs": refs, "request": request,
        }
    except (OSError, ValueError, KeyError, TypeError) as error:
        if isinstance(error, TestAuthorityError):
            raise
        raise TestAuthorityError(str(error)) from error


AUTHORITY_CONTEXT_PATH = "evidence/test-authority-context.json"


def write_vnext_authority_context(
    run_dir: str | Path,
    authority: TestAuthorityContext,
    *,
    ux_context: dict | None = None,
    dev_context: dict | None = None,
    ux_required: bool = False,
) -> dict:
    run_dir = Path(run_dir).resolve()
    refs = list(authority.refs)
    for context in (ux_context, dev_context):
        if context:
            refs.extend(context.get("refs", []))
    input_refs = [{key: ref[key] for key in ("id", "revision", "sha256")} for ref in refs]
    identities = [(ref["id"], ref["revision"], ref["sha256"].lower()) for ref in input_refs]
    if len(identities) != len(set(identities)):
        raise TestAuthorityError("VNext authority context contains duplicate refs")
    record = {
        "schema_version": 1,
        "artifact_class": "RUNTIME",
        "mode": "VNEXT",
        "project_root": str(authority.project_root or authority.baseline.handoff_path.parent),
        "feature_id": authority.baseline.feature_id,
        "ba": {
            "handoff": authority.handoff_ref,
            "baseline": authority.candidate_ref,
            "approval_receipt": authority.approval_ref,
            "baseline_identity": authority.baseline_identity,
        },
        "refs": input_refs,
        "byte_refs": refs,
        "ux_refs": [ref for ref in input_refs if ":UX" in ref["id"]] or None,
        "dev_refs": [ref for ref in input_refs if ref["id"].startswith("DEV:")] or None,
        "project_policy_ref": next((ref for ref in input_refs if "POLICY" in ref["id"].upper()), None),
        "ux_required": bool(ux_required),
        "ux_context": ux_context,
        "dev_context": dev_context,
    }
    design._write_exclusive(
        run_dir / AUTHORITY_CONTEXT_PATH,
        (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return record


def _read_authority_context(run_dir: str | Path) -> dict | None:
    path = Path(run_dir).resolve() / AUTHORITY_CONTEXT_PATH
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("schema_version") != 1 or record.get("artifact_class") != "RUNTIME" or record.get("mode") != "VNEXT":
            raise ValueError("unsupported Test Authority context")
        if not isinstance(record.get("refs"), list) or not isinstance(record.get("byte_refs"), list):
            raise ValueError("Test Authority context refs are missing")
        if _ref_signature(record["refs"]) != _ref_signature(record["byte_refs"]):
            raise ValueError("persisted VNext authority refs differ from exact byte refs")
        for ref in record["byte_refs"]:
            source = Path(ref["path"])
            if not source.is_file() or _sha(source) != ref["sha256"]:
                raise ValueError(f"VNext authority bytes changed: {ref.get('id', 'unknown ref')}")
        return record
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise TestAuthorityError(str(error)) from error


def current_vnext_input_refs(run_dir: str | Path) -> list[dict]:
    record = _read_authority_context(run_dir)
    return list(record["refs"]) if record else []


def read_vnext_authority_context(run_dir: str | Path) -> dict:
    record = _read_authority_context(run_dir)
    if record is None:
        raise TestAuthorityError("persisted VNext Test Authority context is missing")
    return record


def copy_vnext_authority_context(
    source_run_dir: str | Path,
    target_run_dir: str | Path,
    *,
    dev_context: dict | None = None,
) -> dict:
    source = Path(source_run_dir).resolve() / AUTHORITY_CONTEXT_PATH
    record = dict(read_vnext_authority_context(source_run_dir))
    if dev_context:
        refs = [*record["refs"], *[{key: ref[key] for key in ("id", "revision", "sha256")} for ref in dev_context["refs"]]]
        ids = [ref["id"] for ref in refs]
        if len(ids) != len(set(ids)):
            raise TestAuthorityError("Dev context duplicates an existing Test Authority ref")
        record["refs"] = refs
        record["byte_refs"] = [*record["byte_refs"], *dev_context["refs"]]
        record["dev_context"] = dev_context
        record["dev_refs"] = [{key: ref[key] for key in ("id", "revision", "sha256")} for ref in dev_context["refs"]]
    data = (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    target = Path(target_run_dir).resolve() / AUTHORITY_CONTEXT_PATH
    design._write_exclusive(target, data)
    return record


def revalidate_vnext_authority(
    run_dir: str | Path,
    *,
    human_actor_authenticator,
    foundation_authenticator=None,
    ux_human_actor_authenticator=None,
    technical_authenticator=None,
) -> TestAuthorityContext:
    record = _read_authority_context(run_dir)
    if record is None:
        raise TestAuthorityError("persisted VNext Test Authority context is missing")
    authority = load_vnext_authority(
        record["ba"]["handoff"]["path"],
        project_root=record["project_root"],
        human_actor_authenticator=human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
    )
    saved = [(r["id"], r["revision"], r["sha256"].lower(), r.get("path")) for r in record["byte_refs"] if r["id"].startswith("BA:")]
    current = [(r["id"], r["revision"], r["sha256"].lower(), r.get("path")) for r in authority.refs]
    if sorted(saved) != sorted(current):
        raise TestAuthorityError("BA VNext authority refs changed since the Test run started")
    ux_context = record.get("ux_context")
    if record.get("ux_required") and not ux_context:
        raise TestAuthorityError("approved UX context is required for this feature")
    if ux_context:
        ux_auth = ux_human_actor_authenticator or human_actor_authenticator
        current_ux = load_approved_ux_context(
            ux_context["request"], feature_id=authority.baseline.feature_id,
            human_actor_authenticator=ux_auth,
        )
        saved_ux = [(ref["id"], ref["revision"], ref["sha256"].lower(), ref.get("path")) for ref in ux_context["refs"]]
        actual_ux = [(ref["id"], ref["revision"], ref["sha256"].lower(), ref.get("path")) for ref in current_ux["refs"]]
        if sorted(saved_ux) != sorted(actual_ux):
            raise TestAuthorityError("approved UX context refs changed since the Test run started")
        authority = replace(authority, ux_context=current_ux, ux_required=record["ux_required"])
    else:
        authority = replace(authority, ux_required=record.get("ux_required", False))
    dev_context = record.get("dev_context")
    if dev_context:
        current_dev = load_dev_vnext_context(
            dev_context["request"], authority,
            ba_human_actor_authenticator=human_actor_authenticator,
            technical_authenticator=technical_authenticator,
            foundation_authenticator=foundation_authenticator,
        )
        saved_dev = [(ref["id"], ref["revision"], ref["sha256"].lower(), ref.get("path")) for ref in dev_context["refs"]]
        actual_dev = [(ref["id"], ref["revision"], ref["sha256"].lower(), ref.get("path")) for ref in current_dev["refs"]]
        if sorted(saved_dev) != sorted(actual_dev):
            raise TestAuthorityError("Dev technical context refs changed since the Test run started")
        authority = replace(authority, dev_context=current_dev)
    expected_refs = list(authority.refs)
    if authority.ux_context:
        expected_refs.extend(authority.ux_context["refs"])
    if authority.dev_context:
        expected_refs.extend(authority.dev_context["refs"])
    if _ref_signature(expected_refs) != _ref_signature(record["refs"]):
        raise TestAuthorityError("persisted VNext authority refs differ from revalidated BA/UX/Dev authority")
    return authority


def design_gate_input_refs(run_dir: str | Path, baseline: ApprovedBaseline | None = None) -> list[dict]:
    run_dir = Path(run_dir).resolve()
    context = _read_authority_context(run_dir)
    if context is None:
        raise TestAuthorityError("VNext Test Authority context is missing")
    if baseline is None:
        raise TestAuthorityError("an already revalidated VNext baseline is required; legacy BA fallback is disabled")
    return design.design_gate_input_refs(baseline, run_dir)


def prepare_vnext_design(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    project_root: str | Path,
    skill_dir: str | Path,
    human_actor_authenticator,
    foundation_authenticator=None,
    ux_context: dict | None = None,
    ux_required: bool = False,
    ux_human_actor_authenticator=None,
) -> dict:
    authority = load_vnext_authority(
        handoff_path, project_root=project_root,
        human_actor_authenticator=human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
    )
    if ux_required and ux_context is None:
        raise TestAuthorityError("approved UX context is required for this feature")
    if ux_context is not None:
        ux_context = load_approved_ux_context(
            ux_context, feature_id=authority.baseline.feature_id,
            human_actor_authenticator=ux_human_actor_authenticator or human_actor_authenticator,
        )
        authority = replace(authority, ux_context=ux_context, ux_required=ux_required)
    saved = write_vnext_authority_context(run_dir, authority, ux_context=ux_context, ux_required=ux_required)
    bundle = design.adapt_ba_to_tea(handoff_path, baseline=authority.baseline)
    bundle = design.replace(bundle, authority_refs=tuple(saved["byte_refs"]))
    prepared = design.prepare_same_session_design(
        handoff_path, run_dir, project_root=project_root, skill_dir=skill_dir,
        adapter_bundle=bundle,
    )
    return {**prepared, "authority_mode": "VNEXT", "authority_refs": saved["refs"]}


def finalize_vnext_design(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    human_actor_authenticator,
    foundation_authenticator=None,
    raw_design: str | Path | None = None,
    ux_human_actor_authenticator=None,
) -> dict:
    authority = revalidate_vnext_authority(
        run_dir, human_actor_authenticator=human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
    )
    saved = _read_authority_context(run_dir)
    if saved["ux_required"] and not saved.get("ux_context"):
        raise TestAuthorityError("approved UX context is required for this feature")
    bundle = design.adapt_ba_to_tea(handoff_path, baseline=authority.baseline)
    bundle = design.replace(bundle, authority_refs=tuple(saved["byte_refs"]))
    return design.finalize_same_session_design(
        handoff_path, run_dir, raw_design=raw_design,
        adapter_bundle=bundle, vnext_authority=True,
        authority_context=authority,
    )


def apply_vnext_design_decision(
    run_dir: str | Path,
    receipt: dict,
    *,
    human_actor_authenticator=None,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    next_revision: str | None = None,
    ux_human_actor_authenticator=None,
    test_only_fixture_path: str | Path | None = None,
):
    run_dir = Path(run_dir).resolve()
    authority = revalidate_vnext_authority(
        run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
    )
    snapshot = design.load_persisted_design_snapshot(run_dir, require_state="DESIGN_REVIEW")
    validation = validate_vnext_design(snapshot, authority)

    if test_only_fixture_path is not None:
        if human_actor_authenticator is not None:
            raise TestAuthorityError("TEST_ONLY receipts cannot use the production Human authenticator")
        return design.apply_test_only_design_decision(
            run_dir, snapshot, authority.baseline, test_only_fixture_path,
            validation=validation, next_revision=next_revision,
        )

    def authenticated_host(actor_id, exact_receipt):
        actor = human_actor_authenticator(actor_id, exact_receipt) if callable(human_actor_authenticator) else None
        if actor is None:
            return None
        revalidate_vnext_authority(
            run_dir, human_actor_authenticator=ba_human_actor_authenticator,
            foundation_authenticator=foundation_authenticator,
            ux_human_actor_authenticator=ux_human_actor_authenticator,
        )
        try:
            current_refs = design.design_gate_input_refs(authority.baseline, run_dir)
            receipt_refs = design._design_receipt_refs(exact_receipt)
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if receipt_refs != tuple((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in current_refs):
            return None
        return actor

    return design.apply_design_decision(
        run_dir, snapshot, authority.baseline, receipt,
        human_actor_authenticator=authenticated_host,
        validation=validation,
        next_revision=next_revision,
    )


def resume_vnext_design(
    run_dir: str | Path,
    *,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    ux_human_actor_authenticator=None,
) -> tuple[dict, design.DesignSnapshot]:
    authority = revalidate_vnext_authority(
        run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
    )
    workflow = json.loads((Path(run_dir).resolve() / "workflow-state.json").read_text(encoding="utf-8"))
    snapshot = design.load_persisted_design_snapshot(run_dir)
    return workflow, snapshot


def prepare_vnext_cases(
    handoff_path: str | Path,
    design_run_dir: str | Path,
    run_dir: str | Path,
    *,
    project_root: str | Path,
    skill_dir: str | Path,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    execution_oracle_refs=(),
    ux_human_actor_authenticator=None,
    dev_context: dict | None = None,
    technical_authenticator=None,
) -> dict:
    authority = revalidate_vnext_authority(
        design_run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
    )
    validated_dev = load_dev_vnext_context(
        dev_context, authority,
        ba_human_actor_authenticator=ba_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
        foundation_authenticator=foundation_authenticator,
    ) if dev_context else None
    copy_vnext_authority_context(design_run_dir, run_dir, dev_context=validated_dev)
    return cases.prepare_same_session_cases(
        handoff_path, design_run_dir, run_dir,
        project_root=project_root, skill_dir=skill_dir,
        execution_oracle_refs=execution_oracle_refs,
        baseline_override=authority.baseline,
        terminal_state="APPROVED_TESTWARE",
    )


def prepare_test_only_vnext_cases(
    handoff_path: str | Path,
    design_run_dir: str | Path,
    run_dir: str | Path,
    *,
    test_only_design_fixture_path: str | Path,
    project_root: str | Path,
    skill_dir: str | Path,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    execution_oracle_refs=(),
    ux_human_actor_authenticator=None,
    dev_context: dict | None = None,
    technical_authenticator=None,
) -> dict:
    """Acceptance-only Case preparation that requires a persisted TEST_ONLY Design receipt."""
    authority = revalidate_vnext_authority(
        design_run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
    )
    validated_dev = load_dev_vnext_context(
        dev_context, authority,
        ba_human_actor_authenticator=ba_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
        foundation_authenticator=foundation_authenticator,
    ) if dev_context else None
    copy_vnext_authority_context(design_run_dir, run_dir, dev_context=validated_dev)
    return cases.prepare_same_session_cases(
        handoff_path, design_run_dir, run_dir,
        project_root=project_root, skill_dir=skill_dir,
        execution_oracle_refs=execution_oracle_refs,
        baseline_override=authority.baseline,
        terminal_state="APPROVED_TESTWARE",
        test_only_design_fixture_path=test_only_design_fixture_path,
    )


def finalize_vnext_cases(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    raw_cases: str | Path | None = None,
    artifact_id: str | None = None,
    revision: str = "1",
    ux_human_actor_authenticator=None,
    technical_authenticator=None,
):
    authority = revalidate_vnext_authority(
        run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
    )
    return cases.finalize_same_session_cases(
        handoff_path, run_dir, raw_cases=raw_cases,
        artifact_id=artifact_id, revision=revision,
        baseline_override=authority.baseline,
        vnext_authority=True,
    )


def finalize_test_only_vnext_cases(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    test_only_design_fixture_path: str | Path,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    raw_cases: str | Path | None = None,
    artifact_id: str | None = None,
    revision: str = "1",
    ux_human_actor_authenticator=None,
    technical_authenticator=None,
):
    """Acceptance-only Case finalization that preserves TEST_ONLY receipt isolation."""
    authority = revalidate_vnext_authority(
        run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
    )
    return cases.finalize_same_session_cases(
        handoff_path, run_dir, raw_cases=raw_cases,
        artifact_id=artifact_id, revision=revision,
        baseline_override=authority.baseline,
        vnext_authority=True,
        test_only_design_fixture_path=test_only_design_fixture_path,
    )


def resume_vnext_cases(
    run_dir: str | Path,
    *,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    ux_human_actor_authenticator=None,
    technical_authenticator=None,
) -> tuple[dict, cases.CaseSnapshot, cases.CaseWorkflowState]:
    run_dir = Path(run_dir).resolve()
    revalidate_vnext_authority(
        run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
    )
    snapshot, state = cases.load_case_review_snapshot(
        run_dir / "canonical/canonical-testcases.json",
        run_dir / "workflow-state.json",
        run_dir / "canonical/semantic-payload.json",
    )
    workflow = json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))
    return workflow, snapshot, state


def apply_vnext_case_decision(
    run_dir: str | Path,
    receipt: dict,
    *,
    human_actor_authenticator=None,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    next_revision: str | None = None,
    ux_human_actor_authenticator=None,
    technical_authenticator=None,
    test_only_fixture_path: str | Path | None = None,
):
    run_dir = Path(run_dir).resolve()
    authority = revalidate_vnext_authority(
        run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
    )
    case_workflow = json.loads((run_dir / "workflow-state.json").read_text(encoding="utf-8"))
    design_evidence = case_workflow.get("design_gate_receipt_evidence")
    if not isinstance(design_evidence, dict) or not isinstance(design_evidence.get("path"), str):
        raise TestAuthorityError("persisted Case Review does not bind its Design Gate receipt")
    design_receipt_path = Path(design_evidence["path"]).resolve()
    design_run = design_receipt_path.parents[3]
    approved_design = cases.load_design_snapshot(
        design_run / "canonical/canonical-test-design.json",
        design_run / "workflow-state.json",
        design_run / "canonical/semantic-payload.json",
    )
    snapshot, state = cases.load_case_review_snapshot(
        run_dir / "canonical/canonical-testcases.json",
        run_dir / "workflow-state.json",
        run_dir / "canonical/semantic-payload.json",
    )
    validation = validate_vnext_cases(
        snapshot, approved_design, authority,
        execution_contract_refs=state.execution_oracle_refs,
        execution_oracle_authenticator=human_actor_authenticator,
    )

    if test_only_fixture_path is not None:
        if human_actor_authenticator is not None:
            raise TestAuthorityError("TEST_ONLY receipts cannot use the production Human authenticator")
        return cases.apply_test_only_case_gate_decision(
            test_only_fixture_path, snapshot, approved_design, authority.baseline, state,
            workflow_dir=run_dir, validation=validation,
            execution_contract_refs=state.execution_oracle_refs,
            technical_context_refs=authority.dev_context["refs"] if authority.dev_context else (),
            next_revision=next_revision,
            require_resolved_required_dependencies=True,
        )

    def post_authentication_check():
        design_evidence = state.design_gate_receipt_evidence or {}
        design_receipt_path = Path(design_evidence.get("path", "")).resolve()
        try:
            if not design_receipt_path.is_file() or _sha(design_receipt_path) != design_evidence.get("sha256"):
                return False
            current_case_refs = cases.case_gate_input_refs(
                authority.baseline, approved_design, run_dir=run_dir,
                execution_contract_refs=state.execution_oracle_refs,
                case_snapshot=snapshot,
                vnext_authority=True,
            )
            if _ref_signature(current_case_refs) != tuple(sorted(state.input_refs)):
                return False
            if _ref_signature(receipt.get("input_refs", [])) != _ref_signature(current_case_refs):
                return False
            design_run = design_receipt_path.parents[3]
            persisted_design_receipt = json.loads(design_receipt_path.read_text(encoding="utf-8"))
            current_design_refs = design.design_gate_input_refs(authority.baseline, design_run)
            if design._design_receipt_refs(persisted_design_receipt) != tuple(
                (ref["id"], ref["revision"], ref["sha256"].lower()) for ref in current_design_refs
            ):
                return False
            revalidate_vnext_authority(
                run_dir, human_actor_authenticator=ba_human_actor_authenticator,
                foundation_authenticator=foundation_authenticator,
                ux_human_actor_authenticator=ux_human_actor_authenticator,
                technical_authenticator=technical_authenticator,
            )
            return True
        except (OSError, ValueError, KeyError, TypeError):
            return False

    return cases.apply_case_gate_decision(
        receipt, snapshot, approved_design, authority.baseline, state,
        workflow_dir=run_dir,
        human_actor_authenticator=human_actor_authenticator,
        validation=validation,
        execution_contract_refs=state.execution_oracle_refs,
        technical_context_refs=authority.dev_context["refs"] if authority.dev_context else (),
        post_authentication_validator=post_authentication_check,
        next_revision=next_revision,
        require_resolved_required_dependencies=True,
    )


def export_vnext_approved_design_xmind(
    design_run_dir: str | Path,
    output_dir: str | Path,
    *,
    human_actor_authenticator,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    ux_human_actor_authenticator=None,
    test_only_receipt_fixture_path: str | Path | None = None,
):
    from . import test_kit_v1_xmind as xmind

    authority = revalidate_vnext_authority(
        design_run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
    )

    if test_only_receipt_fixture_path is not None:
        return xmind.export_test_only_design_xmind(
            design_run_dir, authority.baseline.handoff_path, output_dir,
            test_only_receipt_fixture_path=test_only_receipt_fixture_path,
            baseline_override=authority.baseline,
            generic_vnext=True,
        )

    def authenticated_host(actor_id, receipt):
        actor = human_actor_authenticator(actor_id, receipt) if callable(human_actor_authenticator) else None
        if actor is not None:
            revalidate_vnext_authority(
                design_run_dir, human_actor_authenticator=ba_human_actor_authenticator,
                foundation_authenticator=foundation_authenticator,
                ux_human_actor_authenticator=ux_human_actor_authenticator,
            )
            try:
                current = design.design_gate_input_refs(authority.baseline, design_run_dir)
                if design._design_receipt_refs(receipt) != tuple((ref["id"], ref["revision"], ref["sha256"].lower()) for ref in current):
                    return None
            except (OSError, ValueError, KeyError, TypeError):
                return None
        return actor

    return xmind.export_approved_design_xmind(
        design_run_dir, authority.baseline.handoff_path, output_dir,
        human_actor_authenticator=authenticated_host,
        baseline_override=authority.baseline,
        generic_vnext=True,
    )


def export_vnext_approved_testware_excel(
    case_run_dir: str | Path,
    design_run_dir: str | Path,
    output_dir: str | Path,
    *,
    human_actor_authenticator,
    ba_human_actor_authenticator,
    foundation_authenticator=None,
    template_path: str | Path | None = None,
    project_template_path: str | Path | None = None,
    row_model: str | None = None,
    project_root: str | Path | None = None,
    ux_human_actor_authenticator=None,
    technical_authenticator=None,
    test_only_receipt_fixture_path: str | Path | None = None,
):
    from . import test_kit_v1_excel as excel

    authority = revalidate_vnext_authority(
        case_run_dir, human_actor_authenticator=ba_human_actor_authenticator,
        foundation_authenticator=foundation_authenticator,
        ux_human_actor_authenticator=ux_human_actor_authenticator,
        technical_authenticator=technical_authenticator,
    )

    if test_only_receipt_fixture_path is not None:
        manifest = json.loads((Path(case_run_dir).resolve() / "approved-testware-vnext.json").read_text(encoding="utf-8"))
        approved = manifest.get("approved_testware") if manifest.get("fixture_type") == "TEST_ONLY_APPROVED_TESTWARE_EVIDENCE" and manifest.get("not_for_production") is True else None
        if not isinstance(approved, dict):
            raise TestAuthorityError("VNext Test Only projection requires explicitly not_for_production handoff evidence")
        fixture_path = Path(test_only_receipt_fixture_path).resolve()
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        receipt_path = Path(case_run_dir).resolve() / "case-gate/receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if (
            not cases.foundation.is_test_only_workspace_path(fixture_path)
            or set(fixture) != {"fixture_type", "not_for_production", "receipt"}
            or fixture.get("fixture_type") != "TEST_ONLY_SIMULATED_HUMAN_CASE_GATE_RECEIPT"
            or fixture.get("not_for_production") is not True
            or fixture.get("receipt") != receipt
        ):
            raise TestAuthorityError("TEST_ONLY Case Gate fixture does not bind the exact persisted receipt")
        approved_design = cases.load_design_snapshot(
            Path(design_run_dir).resolve() / "canonical/canonical-test-design.json",
            Path(design_run_dir).resolve() / "workflow-state.json",
            Path(design_run_dir).resolve() / "canonical/semantic-payload.json",
        )
        current = cases.case_gate_input_refs(
            authority.baseline, approved_design, run_dir=case_run_dir,
            execution_contract_refs=approved.get("execution_oracle_refs", []),
            vnext_authority=True,
        )
        if (_ref_signature(approved.get("input_refs", [])) != _ref_signature(current)
                or not receipt_path.is_file()
                or _sha(receipt_path) != approved.get("case_gate_receipt", {}).get("sha256")):
            raise TestAuthorityError("TEST_ONLY Approved Testware exact gate refs are stale")
        return excel.export_test_only_approved_testware_excel(
            case_run_dir, design_run_dir, authority.baseline.handoff_path, output_dir,
            template_path=template_path, project_template_path=project_template_path,
            row_model=row_model, project_root=project_root,
            baseline_override=authority.baseline,
        )

    def authenticated_host(actor_id, receipt):
        actor = human_actor_authenticator(actor_id, receipt) if callable(human_actor_authenticator) else None
        if actor is not None:
            revalidate_vnext_authority(
                case_run_dir, human_actor_authenticator=ba_human_actor_authenticator,
                foundation_authenticator=foundation_authenticator,
                ux_human_actor_authenticator=ux_human_actor_authenticator,
                technical_authenticator=technical_authenticator,
            )
            try:
                manifest = json.loads((Path(case_run_dir).resolve() / "approved-testware-vnext.json").read_text(encoding="utf-8"))
                approved_design = cases.load_design_snapshot(
                    Path(design_run_dir).resolve() / "canonical/canonical-test-design.json",
                    Path(design_run_dir).resolve() / "workflow-state.json",
                    Path(design_run_dir).resolve() / "canonical/semantic-payload.json",
                )
                current = cases.case_gate_input_refs(
                    authority.baseline, approved_design, run_dir=case_run_dir,
                    execution_contract_refs=manifest.get("execution_oracle_refs", []),
                    vnext_authority=True,
                )
                receipt_path = Path(case_run_dir).resolve() / "case-gate/receipt.json"
                if (_ref_signature(manifest.get("input_refs", [])) != _ref_signature(current)
                        or not receipt_path.is_file()
                        or _sha(receipt_path) != manifest.get("case_gate_receipt", {}).get("sha256")):
                    return None
            except (OSError, ValueError, KeyError, TypeError):
                return None
        return actor

    return excel.export_approved_testware_excel(
        case_run_dir, design_run_dir, authority.baseline.handoff_path, output_dir,
        human_actor_authenticator=authenticated_host,
        template_path=template_path, project_template_path=project_template_path,
        row_model=row_model, project_root=project_root,
        baseline_override=authority.baseline,
    )


def read_legacy_compat(handoff_path: str | Path | None = None, *, run_dir: str | Path | None = None) -> dict:
    """Permit V1 inspection while making its lack of VNext authority explicit."""
    if run_dir is not None:
        root = Path(run_dir).resolve()
        workflow_path = root / "workflow-state.json"
        if not workflow_path.is_file() and (root / "case-gate/workflow-state.json").is_file():
            workflow_path = root / "case-gate/workflow-state.json"
        try:
            workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
            artifacts = {}
            for relative in (
                "canonical/semantic-payload.json", "canonical/canonical-test-design.json",
                "canonical/canonical-testcases.json", "approved-testware.json",
                "approved-testware-vnext.json", "case-gate/receipt.json",
            ):
                path = root / relative
                if path.is_file():
                    data = path.read_bytes()
                    artifacts[relative] = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": data}
            if not isinstance(workflow, dict):
                raise ValueError("legacy workflow state must be a JSON object")
            return {
                "mode": "LEGACY_COMPAT", "vnext_authority": False,
                "state": workflow.get("state", "UNKNOWN"),
                "workflow": workflow, "artifacts": artifacts,
            }
        except (OSError, ValueError, TypeError) as error:
            raise TestAuthorityError(str(error)) from error
    if handoff_path is None:
        raise TestAuthorityError("legacy inspection requires a handoff or Test run directory")
    try:
        baseline = design.load_approved_baseline(handoff_path)
    except (OSError, ValueError) as error:
        raise TestAuthorityError(str(error)) from error
    return {
        "mode": "LEGACY_COMPAT", "vnext_authority": False,
        "feature_id": baseline.feature_id, "revision": baseline.revision,
        "baseline": baseline,
    }


def validate_vnext_design(snapshot: design.DesignSnapshot, authority: TestAuthorityContext):
    findings = [
        design.Finding(
            "BAREF_CANONICAL_TRACE_FORBIDDEN",
            f"{record.design_id} contains a locator in canonical requirement_refs",
            field="requirement_refs",
        )
        for record in snapshot.records
        if any(ref.upper().startswith("BAREF:") for ref in record.requirement_refs)
    ]
    ux = authority.ux_context
    if authority.ux_required and not ux:
        findings.append(design.Finding("UX_APPROVAL_REQUIRED", "feature requires exact approved UX context"))
    if ux:
        try:
            contract_path = Path(ux["contract_path"])
            if _sha(contract_path) != ux["contract_ref"]["sha256"]:
                raise ValueError("approved UX contract bytes changed")
        except (OSError, ValueError, KeyError, TypeError) as error:
            findings.append(design.Finding("UX_CONTEXT_STALE", str(error)))
    return design.validate_design(snapshot, authority.baseline, explicit_authority_conflicts=findings)


def validate_vnext_cases(
    snapshot: cases.CaseSnapshot,
    approved_design: design.DesignSnapshot,
    authority: TestAuthorityContext,
    *,
    execution_contract_refs=(),
    execution_oracle_authenticator=None,
):
    findings = [
        cases.foundation.Finding(
            "BAREF_CANONICAL_TRACE_FORBIDDEN",
            f"{record.test_case_id} contains a locator in canonical requirement_refs",
            field="requirement_refs",
        )
        for record in snapshot.records
        if any(ref.upper().startswith("BAREF:") for ref in record.requirement_refs)
    ]
    ux = authority.ux_context
    if authority.ux_required and not ux:
        findings.append(cases.foundation.Finding("UX_APPROVAL_REQUIRED", "feature requires exact approved UX context"))
    if ux:
        try:
            contract_path = Path(ux["contract_path"])
            if _sha(contract_path) != ux["contract_ref"]["sha256"]:
                raise ValueError("approved UX contract bytes changed")
        except (OSError, ValueError, KeyError, TypeError) as error:
            findings.append(cases.foundation.Finding("UX_CONTEXT_STALE", str(error)))
    base = cases.validate_testcases(
        snapshot, approved_design, authority.baseline,
        execution_contract_refs=execution_contract_refs,
        execution_oracle_authenticator=execution_oracle_authenticator,
        technical_context_refs=authority.dev_context["refs"] if authority.dev_context else (),
        require_resolved_required_dependencies=True,
    )
    if not findings:
        return base
    return cases.CaseValidatorResult(
        "FAIL", tuple((*base.findings, *findings)), base.artifact_id, base.artifact_revision, base.artifact_sha256,
    )
