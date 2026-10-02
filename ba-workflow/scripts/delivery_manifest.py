"""Project delivery authority. JSON or the documented mapping/list YAML subset."""
import ast
import hashlib
import json
import re
from pathlib import Path

from approved_baseline import read_approved_baseline

CONTRACT_VERSION = 2


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


def _reference(root, ref, *, revision=False):
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
        raise ValueError("artifact reference requires path")
    relative = ref["path"]
    if "\\" in relative or ":" in relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("artifact path must be portable and feature-relative")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink() or not path.is_file():
        raise ValueError(f"artifact missing or unsafe: {relative}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if ref.get("sha256") != digest:
        raise ValueError(f"SHA-256 mismatch: {relative}")
    if revision and (not isinstance(ref.get("revision"), str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", ref["revision"])):
        raise ValueError("immutable artifact revision required")
    return path


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
        keys(receipt, ("schema_version", "feature_id", "source", "approver", "decision"))
        if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1:
            raise ValueError("UX approval receipt schema_version must be 1")
        keys(receipt["source"], ("path", "revision", "sha256"))
        if receipt["feature_id"] != feature:
            raise ValueError("UX approval receipt feature mismatch")
        if receipt["source"] != ux["contract"]:
            raise ValueError("UX approval receipt source path/revision/SHA-256 mismatch")
        keys(receipt["approver"], ("role", "identity"))
        if (receipt["approver"]["role"] != "HUMAN"
                or not isinstance(receipt["approver"]["identity"], str)
                or not receipt["approver"]["identity"].strip()):
            raise ValueError("UX approval receipt requires an explicit Human approver")
        if receipt["decision"] != "APPROVE":
            raise ValueError("UX approval receipt decision must be APPROVE")
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
