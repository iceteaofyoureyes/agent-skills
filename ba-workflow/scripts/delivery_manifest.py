"""Project delivery authority. JSON or the documented mapping/list YAML subset."""
import ast
import hashlib
import json
import re
from pathlib import Path

from approved_baseline import read_approved_baseline

CONTRACT_VERSION = 1


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
    if revision and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", ref.get("revision", "")):
        raise ValueError("immutable artifact revision required")
    return path


def load_delivery_manifest(path):
    path = Path(path).resolve()
    data = read_mapping(path)
    if set(data) != {"schema_version", "feature", "delivery_revision", "ba", "ux", "targets", "open_items"}:
        raise ValueError("unsupported or missing delivery fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Delivery Manifest schema_version must be 1")
    feature = data["feature"].get("id", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", feature):
        raise ValueError("invalid feature ID")
    if not data["delivery_revision"].startswith(feature + "-DELIVERY-"):
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
        contract = _reference(path.parent, ux.get("contract"), revision=True)
        text = contract.read_text(encoding="utf-8")
        if not re.search(r"(?m)^revision:\s*" + re.escape(ux["contract"]["revision"]) + r"\s*$", text):
            raise ValueError("UX revision mismatch")
        if not re.search(r"(?m)^status:\s*APPROVED\s*$", text):
            raise ValueError("UX contract must declare its approved snapshot status")
    if "prototype" in ux:
        _reference(path.parent, ux["prototype"])
        if ux["prototype"].get("authority") != "REVIEW_EVIDENCE":
            raise ValueError("prototype promotion requires a separate approved contract")
    targets = data["targets"]
    if not isinstance(targets, list) or not targets:
        raise ValueError("at least one delivery target required")
    for target in targets:
        if set(target) != {"repository", "module", "base_revision"}:
            raise ValueError("unsupported target fields; credentials are forbidden")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", target["repository"]):
            raise ValueError("invalid target repository")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", target["module"]) or ".." in target["module"].split("/"):
            raise ValueError("invalid target module")
        if not re.fullmatch(r"[0-9a-f]{40}", target["base_revision"]):
            raise ValueError("target base_revision must be exact Git SHA")
    return {"data": data, "baseline": baseline, "path": path,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
