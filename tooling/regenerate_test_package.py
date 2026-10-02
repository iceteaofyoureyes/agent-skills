"""Regenerate Test package authority and manifest pins from the canonical allowlist."""
import hashlib
import json
from pathlib import Path

from tooling.lib.package import build_package_authority, package_authority_bytes


def regenerate(root):
    root = Path(root)
    path = root / "kits/test/kit.yaml"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    authority = build_package_authority(root, manifest)
    content = package_authority_bytes(authority)
    (root / "kits/test/package-authority.json").write_bytes(content)
    manifest["integrity"]["authority"]["sha256"] = hashlib.sha256(content).hexdigest()
    manifest["integrity"]["payload"]["sha256"] = authority["payload_tree_sha256"]
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return authority


if __name__ == "__main__":
    print(regenerate(Path(__file__).resolve().parents[1])["payload_tree_sha256"])
