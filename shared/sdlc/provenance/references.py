"""Exact reference profiles; portable delivery and execution syntax stay distinct."""
import hashlib
from pathlib import Path
import re


def delivery_reference(root, ref, *, revision=False):
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str):
        raise ValueError("artifact reference requires path")
    relative = ref["path"]
    if "\\" in relative or ":" in relative or Path(relative).is_absolute() or any(part in ("", ".", "..") for part in relative.split("/")):
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


def checked_ref(ref):
    if not isinstance(ref, dict) or not isinstance(ref.get("path"), str) or not re.fullmatch(r"[0-9a-f]{64}", ref.get("sha256", "")):
        raise ValueError("exact artifact path/SHA reference required")
    path = Path(ref["path"])
    if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != ref["sha256"]:
        raise ValueError("artifact missing or hash drift")
    return path


