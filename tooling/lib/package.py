"""Deterministic inventory and digest for explicitly installed kit trees."""

import hashlib
import argparse
import json
import re
import unicodedata
from pathlib import Path, PurePosixPath


PAYLOAD_DIGEST_ALGORITHM = "TEST_KIT_PACKAGE_PAYLOAD_V1"
INSTALLED_TREE_ALGORITHM = "INSTALLED_TREE_SHA256_V1"


def _package_files(directory: str | Path) -> list[tuple[str, Path]]:
    root = Path(directory).resolve()
    if not root.is_dir():
        raise ValueError(f"package tree is not a directory: {root}")
    files = []
    names = set()
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"package tree contains symlink: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError(f"package tree contains a non-regular file: {path}")
        relative = unicodedata.normalize("NFC", path.relative_to(root).as_posix())
        folded = relative.casefold()
        if relative.startswith("/") or ".." in relative.split("/") or folded in names:
            raise ValueError(f"package tree has an invalid or duplicate normalized path: {relative}")
        names.add(folded)
        files.append((relative, path))
    return sorted(files, key=lambda item: item[0].encode("utf-8"))


def installed_tree_sha256(directory: str | Path) -> str:
    """Hash every regular file in an installed tree, including generated metadata."""
    digest = hashlib.sha256()
    for relative, path in _package_files(directory):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def payload_tree_sha256_from_inventory(inventory: list[dict]) -> str:
    """Hash normalized payload paths and file hashes using PAYLOAD_DIGEST_ALGORITHM."""
    digest = hashlib.sha256()
    names = set()
    if any(not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"] for item in inventory):
        raise ValueError("invalid package inventory path")
    for item in sorted(inventory, key=lambda entry: unicodedata.normalize("NFC", entry["path"]).encode("utf-8")):
        relative = unicodedata.normalize("NFC", item["path"])
        path = PurePosixPath(relative)
        if path.is_absolute() or path.as_posix() != relative or "\\" in relative or any(part in ("", ".", "..") for part in relative.split("/")):
            raise ValueError(f"invalid package inventory path: {relative}")
        folded = relative.casefold()
        file_hash = item.get("sha256")
        if folded in names or not isinstance(file_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", file_hash):
            raise ValueError(f"invalid or duplicate package inventory entry: {relative}")
        names.add(folded)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def package_source_inventory(source_root: str | Path, manifest: dict) -> list[dict]:
    """Resolve runtime files, excluding the root definition and authority metadata."""
    from .ba_kit import _content_hash, _resolve_under, _valid_skill, skill_composition

    source_root = Path(source_root).resolve()
    required = {manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"]}
    inventory = []
    for skill in skill_composition(manifest):
        source_rel = manifest.get("skill_sources", {}).get(skill, skill)
        source = _resolve_under(source_root, source_rel, f"skill source {skill}")
        if not _valid_skill(source, skill):
            if skill in required:
                raise ValueError(f"required skill is missing or invalid: {source}")
            continue
        for path in source.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"package source contains symlink: {path}")
            if not path.is_dir() and not path.is_file():
                raise ValueError(f"package source contains a non-regular file: {path}")
            if path.is_file():
                inventory.append({
                    "path": f"{skill}/{path.relative_to(source).as_posix()}",
                    "sha256": _content_hash(path),
                    "classification": "REQUIRED_SKILL" if skill in required else "OPTIONAL_SKILL",
                })

    integrity = manifest.get("integrity") or {}
    authority_path = integrity.get("authority", {}).get("path")
    definition_path = f".{manifest['id']}-kit/kit.yaml"
    for item in manifest.get("files", []):
        if item["destination"] in (definition_path, authority_path):
            continue
        source = _resolve_under(source_root, item["source"], f"file source {item['source']}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"package source is missing or not regular: {source}")
        inventory.append({
            "path": item["destination"],
            "sha256": _content_hash(source),
            "classification": item["classification"],
        })
    # The manifest, authority, and generated install record are separate digest domains.
    payload_tree_sha256_from_inventory(inventory)
    return sorted(inventory, key=lambda item: unicodedata.normalize("NFC", item["path"]).encode("utf-8"))


def payload_tree_sha256(source_root: str | Path, manifest: dict) -> str:
    """Hash manifest-selected runtime files, excluding definition and authority metadata."""
    return payload_tree_sha256_from_inventory(package_source_inventory(source_root, manifest))


def build_package_authority(source_root: str | Path, manifest: dict) -> dict:
    inventory = package_source_inventory(source_root, manifest)
    return {
        "schema_version": 1,
        "kit_id": manifest["id"],
        "kit_version": manifest["version"],
        "manifest_schema_version": manifest["schema_version"],
        "managed_files": inventory,
        "managed_file_count": len(inventory),
        "payload_digest_algorithm": PAYLOAD_DIGEST_ALGORITHM,
        "payload_tree_sha256": payload_tree_sha256_from_inventory(inventory),
    }


def package_authority_bytes(authority: dict) -> bytes:
    return (json.dumps(authority, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def validate_source_package_integrity(source_root: str | Path, manifest: dict) -> tuple[dict, bytes, str]:
    """Check the durable authority artifact and both manifest-pinned identities."""
    from .ba_kit import _content_hash, _resolve_under

    integrity = manifest["integrity"]
    authority_entry = next(item for item in manifest["files"] if item["destination"] == integrity["authority"]["path"])
    authority = build_package_authority(source_root, manifest)
    expected_bytes = package_authority_bytes(authority)
    authority_source = _resolve_under(source_root, authority_entry["source"], "package authority source")
    actual_bytes = authority_source.read_bytes()
    actual_sha256 = _content_hash(authority_source)
    if actual_bytes != expected_bytes:
        raise ValueError("source package-authority.json differs from the resolved package definition")
    if actual_sha256 != integrity["authority"]["sha256"]:
        raise ValueError("source package-authority.json SHA-256 differs from the manifest pin")
    if authority["payload_digest_algorithm"] != integrity["payload"]["algorithm"]:
        raise ValueError("source payload digest algorithm differs from the manifest")
    if authority["payload_tree_sha256"] != integrity["payload"]["sha256"]:
        raise ValueError("source payload digest differs from the manifest pin")
    return authority, actual_bytes, actual_sha256


def package_inventory(package_root: str | Path, *, source_root: str | Path, manifest: dict) -> list[dict]:
    """Inventory every package file and mark files outside the manifest."""
    from .ba_kit import skill_composition

    package_root = Path(package_root).resolve()
    source_root = Path(source_root).resolve()
    kit_id = manifest["id"]
    sources = {}
    required = {manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"]}
    for skill in skill_composition(manifest):
        source = source_root / manifest.get("skill_sources", {}).get(skill, skill)
        classification = "REQUIRED_SKILL" if skill in required else "OPTIONAL_SKILL"
        for path in source.rglob("*"):
            if path.is_file():
                relative = path.relative_to(source).as_posix()
                sources[f"{skill}/{relative}"] = (classification, path.relative_to(source_root).as_posix())
    for item in manifest.get("files", []):
        sources[item["destination"]] = (item["classification"], item["source"])
    sources[f".{kit_id}-kit-install.json"] = ("INSTALLED_PROVENANCE", "generated by tooling/lib/ba_kit.py")
    inventory = []
    for relative, path in _package_files(package_root):
        classification, source = sources.get(relative, ("UNDECLARED_FILE", ""))
        content = path.read_bytes()
        inventory.append({
            "path": relative,
            "size": len(content),
            "sha256": hashlib.sha256(content).hexdigest(),
            "classification": classification,
            "source": source,
        })
    return inventory


def write_package_inventory(path: str | Path, inventory: list[dict]) -> None:
    import csv

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("path", "size", "sha256", "classification", "source"))
        writer.writeheader()
        writer.writerows(inventory)


def main(argv=None) -> int:
    from .ba_kit import ROOT, load_manifest

    parser = argparse.ArgumentParser(description="Inventory and digest an installed kit tree")
    parser.add_argument("--kit", required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = load_manifest(args.source_root, args.kit)
    if manifest.get("integrity"):
        authority, _, authority_sha = validate_source_package_integrity(args.source_root, manifest)
    else:
        authority, authority_sha = None, None
    inventory = package_inventory(args.target, source_root=args.source_root, manifest=manifest)
    write_package_inventory(args.output, inventory)
    print(f"FILES: {len(inventory)}")
    print(f"BYTES: {sum(item['size'] for item in inventory)}")
    if authority:
        print(f"AUTHORITY_FILE_SHA256: {authority_sha}")
        print(f"PAYLOAD_DIGEST_ALGORITHM: {authority['payload_digest_algorithm']}")
        print(f"PAYLOAD_TREE_SHA256: {authority['payload_tree_sha256']}")
    print(f"INSTALLED_TREE_ALGORITHM: {INSTALLED_TREE_ALGORITHM}")
    print(f"INSTALLED_TREE_SHA256: {installed_tree_sha256(args.target)}")
    undeclared = [item["path"] for item in inventory if item["classification"] == "UNDECLARED_FILE"]
    if undeclared:
        print("UNDECLARED: " + ", ".join(undeclared))
        return 1
    print(f"INVENTORY: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
