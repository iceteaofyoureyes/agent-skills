"""Project delivery authority. JSON or the documented mapping/list YAML subset."""
from shared.sdlc.compatibility import retain_legacy_identity as _retain_legacy_identity
_retain_legacy_identity(__name__, 'delivery_manifest')

import ast
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from shared.sdlc.authority.approved_baseline import read_approved_baseline

CONTRACT_VERSION = 2
UX_RECEIPT_VERSION = 2
UX_SNAPSHOT_METHOD = "SHA-256 of UTF-8 canonical JSON mapping the two relative UX artifact paths to individual SHA-256 values; keys sorted, compact separators."
UX_SNAPSHOT_METHOD_V2 = "UX_APPROVED_SOURCES_CANONICAL_JSON_SHA256_V2"


def read_mapping(path):
    text = Path(path).read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate key: {key}")
                result[key] = value
            return result
        return json.loads(text, object_pairs_hook=unique)
    rows = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line or re.search(r"(?:^|\s)[&*!]", line):
            raise ValueError("unsupported YAML construct")
        rows.append((len(line) - len(line.lstrip()), line.strip()))

    def scalar(value):
        if value in {"true", "false"}:
            return value == "true"
        if value == "[]":
            return []
        if re.fullmatch(r"\d+", value):
            return int(value)
        if value.startswith(('"', "'")):
            return ast.literal_eval(value)
        return value

    def block(index, indent):
        sequence = rows[index][1].startswith("- ")
        result = [] if sequence else {}
        while index < len(rows) and rows[index][0] == indent:
            value = rows[index][1]
            if sequence:
                if not value.startswith("- "):
                    raise ValueError("mixed YAML sequence/mapping")
                value = value[2:]
                if ": " not in value:
                    result.append(scalar(value)); index += 1; continue
                # List mapping starts at the indentation after '- '.
                rows[index] = (indent + 2, value)
                item, index = block(index, indent + 2)
                result.append(item)
                continue
            key, sep, value = value.partition(":")
            if not sep or not re.fullmatch(r"[A-Za-z0-9_-]+", key) or key in result:
                raise ValueError("invalid or duplicate YAML mapping key")
            index += 1
            if value.strip():
                result[key] = scalar(value.strip())
            elif index < len(rows) and rows[index][0] > indent:
                result[key], index = block(index, rows[index][0])
            else:
                result[key] = None
        return result, index

    if not rows:
        raise ValueError("empty manifest")
    result, consumed = block(0, 0)
    if consumed != len(rows) or not isinstance(result, dict):
        raise ValueError("invalid YAML structure")
    return result


from shared.sdlc.provenance.references import delivery_reference as _reference


def load_delivery_manifest(path):
    path = Path(path).resolve()
    data = read_mapping(path)
    if set(data) != {"schema_version", "feature", "delivery_revision", "ba", "ux", "targets", "open_items"}:
        raise ValueError("unsupported or missing delivery fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != CONTRACT_VERSION:
        raise ValueError("Delivery Manifest schema_version must be 2")
    def keys(value, required, optional=()):
        if not isinstance(value, dict) or not set(required).issubset(value) or set(value) - set(required) - set(optional):
            raise ValueError("unsupported/missing delivery fields; credentials are forbidden")
    keys(data["feature"], ("id",))
    keys(data["ba"], ("handoff",))
    keys(data["ba"]["handoff"], ("path", "revision", "sha256"))
    keys(data["ux"], ("required",), ("contract", "approval_receipt", "prototype"))
    keys(data["open_items"], ("blocking",), ("non_blocking",))
    feature = data["feature"].get("id", "")
    if not isinstance(feature, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", feature):
        raise ValueError("invalid feature ID")
    if not isinstance(data["delivery_revision"], str) or not data["delivery_revision"].startswith(feature + "-DELIVERY-"):
        raise ValueError("delivery revision must bind the feature")
    if data["open_items"].get("blocking") != []:
        raise ValueError("blocking open item prevents delivery readiness")
    ref = data["ba"]["handoff"]
    handoff = _reference(path.parent, ref, revision=True)
    baseline = read_approved_baseline(handoff)
    if baseline.feature_id != feature or baseline.revision != ref["revision"]:
        raise ValueError("BA feature/revision mismatch")
    ux = data["ux"]
    if type(ux.get("required")) is not bool:
        raise ValueError("ux.required must be boolean")
    if ux["required"] or "contract" in ux:
        keys(ux.get("contract"), ("path", "revision", "sha256"))
        contract = _reference(path.parent, ux["contract"], revision=True)
        keys(ux.get("approval_receipt"), ("path", "sha256"))
        receipt_path = _reference(path.parent, ux["approval_receipt"])
        if receipt_path.resolve() == contract.resolve():
            raise ValueError("UX approval receipt must be external to the semantic source")
        receipt = read_mapping(receipt_path)
        keys(receipt, ("schema_version", "feature_id", "decision", "decision_type", "approved_by",
                       "recorded_at_utc", "revision", "immutable", "semantic_snapshot_sha256",
                       "semantic_snapshot_sha256_method", "sources", "source_commit", "source_branch",
                       "reapproval_required_if_source_bytes_change"),
             ("prototype_authority", "formal_browser_AT_WCAG_testing", "conformance_PASS_claimed"))
        version = receipt["schema_version"]
        if type(version) is not int or version not in (1, UX_RECEIPT_VERSION):
            raise ValueError("UX approval receipt schema_version must be 1 or 2")
        if receipt["feature_id"] != feature:
            raise ValueError("UX approval receipt feature mismatch")
        if receipt["revision"] != ux["contract"]["revision"]:
            raise ValueError("UX approval receipt revision mismatch")
        if receipt["approved_by"] != "Human" or receipt["decision_type"] != "HUMAN_EXPLICIT_EXACT_SNAPSHOT_APPROVAL":
            raise ValueError("UX approval receipt requires an explicit Human approver")
        if receipt["decision"] != "APPROVE":
            raise ValueError("UX approval receipt decision must be APPROVE")
        if receipt["immutable"] is not True or receipt["reapproval_required_if_source_bytes_change"] is not True:
            raise ValueError("UX approval receipt must bind an immutable snapshot requiring reapproval")
        if "prototype_authority" in receipt and receipt["prototype_authority"] != "REVIEW_EVIDENCE":
            raise ValueError("UX receipt prototype authority must be REVIEW_EVIDENCE")
        if (not isinstance(receipt["source_commit"], str) or not re.fullmatch(r"[0-9a-f]{40}", receipt["source_commit"])
                or not isinstance(receipt["source_branch"], str) or not receipt["source_branch"].strip()):
            raise ValueError("UX approval receipt requires source provenance")
        recorded = receipt["recorded_at_utc"]
        if not isinstance(recorded, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", recorded):
            raise ValueError("UX approval receipt requires a UTC timestamp")
        datetime.fromisoformat(recorded[:-1] + "+00:00")
        if "formal_browser_AT_WCAG_testing" in receipt and not isinstance(receipt["formal_browser_AT_WCAG_testing"], str):
            raise ValueError("invalid UX testing provenance")
        if "conformance_PASS_claimed" in receipt and type(receipt["conformance_PASS_claimed"]) is not bool:
            raise ValueError("invalid UX conformance provenance")
        sources = receipt["sources"]
        if not isinstance(sources, dict) or not sources or (version == 1 and len(sources) != 2):
            raise ValueError("UX receipt requires approved sources; legacy V1 requires two paths")
        if len(sources) > 1 and receipt.get("prototype_authority") != "REVIEW_EVIDENCE":
            raise ValueError("UX receipt review evidence requires prototype authority REVIEW_EVIDENCE")
        if sources.get(ux["contract"]["path"]) != ux["contract"]["sha256"]:
            raise ValueError("UX contract path/SHA-256 missing or mismatched in receipt sources")
        resolved_sources = set()
        for relative, digest in sources.items():
            source = _reference(path.parent, {"path": relative, "sha256": digest})
            if source.resolve() == receipt_path.resolve():
                raise ValueError("UX receipt cannot be a source")
            resolved_sources.add(source.resolve())
        if len(resolved_sources) != len(sources):
            raise ValueError("UX semantic source and prototype must be distinct")
        if "prototype" in ux:
            keys(ux["prototype"], ("path", "sha256", "authority"))
            if ux["prototype"]["path"] == ux["contract"]["path"]:
                raise ValueError("prototype cannot also be the UX semantic source")
            if sources.get(ux["prototype"]["path"]) != ux["prototype"]["sha256"]:
                raise ValueError("UX prototype path/SHA-256 missing or mismatched in receipt sources")
        method = UX_SNAPSHOT_METHOD if version == 1 else UX_SNAPSHOT_METHOD_V2
        if receipt["semantic_snapshot_sha256_method"] != method:
            raise ValueError("unsupported UX semantic snapshot method")
        snapshot = hashlib.sha256(json.dumps(sources, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()
        if receipt["semantic_snapshot_sha256"] != snapshot:
            raise ValueError("UX semantic snapshot SHA-256 mismatch")
    elif "approval_receipt" in ux:
        raise ValueError("UX approval receipt requires a semantic source contract")
    if "prototype" in ux:
        keys(ux["prototype"], ("path", "sha256", "authority"))
        prototype = _reference(path.parent, ux["prototype"])
        if "contract" in ux and prototype.resolve() == contract.resolve():
            raise ValueError("prototype cannot also be the UX semantic source")
        if ux["prototype"].get("authority") != "REVIEW_EVIDENCE":
            raise ValueError("prototype promotion requires a separate approved contract")
    targets = data["targets"]
    if not isinstance(targets, list) or not targets:
        raise ValueError("at least one delivery target required")
    for target in targets:
        if not isinstance(target, dict) or set(target) != {"repository", "module", "base_revision"} or any(not isinstance(value, str) for value in target.values()):
            raise ValueError("unsupported target fields; credentials are forbidden")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", target["repository"]):
            raise ValueError("invalid target repository")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", target["module"]) or ".." in target["module"].split("/"):
            raise ValueError("invalid target module")
        if not re.fullmatch(r"[0-9a-f]{40}", target["base_revision"]):
            raise ValueError("target base_revision must be exact Git SHA")
    return {"data": data, "baseline": baseline, "path": path,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
