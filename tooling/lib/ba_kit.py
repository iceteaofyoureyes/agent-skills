"""Standard-library installer and contract checks for Agent Skills Kits."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ba-workflow/scripts"))
from contracts import validate_handoff_file, validate_handoff_text, validate_state_data  # noqa: E402


INSTALL_RECORD = ".ba-kit-install.json"
SKILL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _install_record_path(target_dir, kit_id):
    if not isinstance(kit_id, str) or not SKILL_ID.fullmatch(kit_id):
        raise ValueError(f"invalid kit id: {kit_id}")
    return Path(target_dir) / (INSTALL_RECORD if kit_id == "ba" else f".{kit_id}-kit-install.json")


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_json_object)


def _safe_relative_path(value, label):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError(f"manifest {label} must be a relative POSIX path")
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"manifest {label} must stay inside its package root: {value}")
    return path


def _resolve_under(root, relative, label):
    root = Path(root).resolve()
    path = root.joinpath(*_safe_relative_path(relative, label).parts)
    if path.is_symlink():
        raise ValueError(f"manifest {label} cannot be a symlink: {path}")
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"manifest {label} escapes its root: {path}") from error
    return path


def _validate_install_record(record, path, kit_id="ba"):
    if (
        not isinstance(record, dict)
        or type(record.get("schema_version")) is not int
        or record["schema_version"] != 1
        or record.get("kit") != kit_id
        or not isinstance(record.get("kit"), str)
        or not SKILL_ID.fullmatch(record["kit"])
        or not isinstance(record.get("skills"), dict)
        or not isinstance(record.get("files", {}), dict)
        or not isinstance(record.get("managed_files", {}), dict)
    ):
        raise ValueError(f"refusing to use unrelated or invalid install record {path}")
    has_managed_files = "managed_files" in record
    has_managed_count = "managed_file_count" in record
    if has_managed_files != has_managed_count or (
        has_managed_count
        and (type(record["managed_file_count"]) is not int or record["managed_file_count"] < 0 or record["managed_file_count"] != len(record["managed_files"]))
    ):
        raise ValueError(f"invalid managed file inventory in install record {path}")
    for name, details in record["skills"].items():
        digest = details.get("sha256") if isinstance(details, dict) else None
        if not isinstance(name, str) or not SKILL_ID.fullmatch(name) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError(f"invalid managed skill entry in install record {path}")
    for name, details in record.get("files", {}).items():
        digest = details.get("sha256") if isinstance(details, dict) else None
        classification = details.get("classification") if isinstance(details, dict) else None
        try:
            _safe_relative_path(name, "install record file")
        except ValueError as error:
            raise ValueError(f"invalid managed file entry in install record {path}: {error}") from error
        if not isinstance(digest, str) or not SHA256.fullmatch(digest) or not isinstance(classification, str) or not classification:
            raise ValueError(f"invalid managed file entry in install record {path}")
    file_names = set(record.get("files", {}))
    for name, details in record.get("managed_files", {}).items():
        digest = details.get("sha256") if isinstance(details, dict) else None
        classification = details.get("classification") if isinstance(details, dict) else None
        try:
            safe_name = _safe_relative_path(name, "managed file").as_posix()
        except ValueError as error:
            raise ValueError(f"invalid managed file entry in install record {path}: {error}") from error
        if (
            safe_name not in file_names
            and PurePosixPath(safe_name).parts[0] not in record["skills"]
        ) or not isinstance(digest, str) or not SHA256.fullmatch(digest) or not isinstance(classification, str) or not classification:
            raise ValueError(f"invalid managed file entry in install record {path}")
    has_algorithm = "package_digest_algorithm" in record
    has_digest = "package_tree_sha256" in record
    if has_algorithm != has_digest or (has_digest and (not isinstance(record["package_digest_algorithm"], str) or not record["package_digest_algorithm"] or not isinstance(record["package_tree_sha256"], str) or not SHA256.fullmatch(record["package_tree_sha256"]))):
        raise ValueError(f"invalid package digest metadata in install record {path}")
    has_payload_algorithm = "payload_digest_algorithm" in record
    has_payload_digest = "payload_tree_sha256" in record
    if has_payload_algorithm != has_payload_digest or (
        has_payload_digest
        and (
            not isinstance(record["payload_digest_algorithm"], str)
            or not record["payload_digest_algorithm"]
            or not isinstance(record["payload_tree_sha256"], str)
            or not SHA256.fullmatch(record["payload_tree_sha256"])
        )
    ):
        raise ValueError(f"invalid payload digest metadata in install record {path}")


def load_manifest(root, kit_id="ba"):
    if not isinstance(kit_id, str) or not SKILL_ID.fullmatch(kit_id):
        raise ValueError(f"invalid kit id: {kit_id}")
    path = Path(root) / "kits" / kit_id / "kit.yaml"
    try:
        manifest = _read_json(path)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {kit_id} Kit manifest {path}: {error}") from error
    return validate_manifest_data(manifest, kit_id, path)


def validate_manifest_data(manifest, kit_id, path="package definition"):
    if not isinstance(manifest, dict) or type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1 or manifest.get("id") != kit_id:
        raise ValueError(f"unsupported or invalid {kit_id} Kit manifest: {path}")
    if not isinstance(manifest.get("name"), str) or not manifest["name"] or not isinstance(manifest.get("version"), str) or not manifest["version"]:
        raise ValueError("manifest requires kit name and version")
    workflow = manifest.get("workflow")
    skills = manifest.get("skills")
    if not isinstance(workflow, dict) or not isinstance(skills, dict):
        raise ValueError("manifest requires workflow and skills objects")
    groups = [manifest.get("core"), skills.get("required"), skills.get("optional")]
    if not isinstance(workflow.get("skill"), str) or any(not isinstance(group, list) for group in groups):
        raise ValueError("manifest requires workflow.skill and core/required/optional lists")
    names = [workflow["skill"]]
    for group in groups:
        names.extend(group)
    if any(not isinstance(name, str) or not SKILL_ID.fullmatch(name) for name in names):
        raise ValueError("manifest contains an invalid skill id")
    if len(names) != len(set(names)):
        raise ValueError("manifest defines a skill more than once")
    skill_sources = manifest.get("skill_sources", {})
    if not isinstance(skill_sources, dict) or set(skill_sources) - set(names):
        raise ValueError("manifest skill_sources must map declared skill ids to source directories")
    for skill, source in skill_sources.items():
        _safe_relative_path(source, f"skill_sources.{skill}")
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise ValueError("manifest files must be a list")
    sources, destinations = set(), set()
    for index, item in enumerate(files):
        if not isinstance(item, dict) or not all(isinstance(item.get(key), str) and item[key] for key in ("source", "destination", "classification")):
            raise ValueError(f"manifest files[{index}] requires source, destination, and classification")
        source = _safe_relative_path(item["source"], f"files[{index}].source").as_posix()
        destination = _safe_relative_path(item["destination"], f"files[{index}].destination").as_posix()
        if source in sources or destination in destinations:
            raise ValueError(f"manifest has duplicate file source or destination: {source} -> {destination}")
        if PurePosixPath(destination).parts[0] in names or destination == f".{kit_id}-kit-install.json":
            raise ValueError(f"manifest file destination collides with a skill or install record: {destination}")
        sources.add(source)
        destinations.add(destination)
    integrity = manifest.get("integrity")
    if integrity is not None:
        if not isinstance(integrity, dict) or set(integrity) != {"authority", "payload"}:
            raise ValueError("manifest integrity must contain authority and payload objects")
        authority = integrity["authority"]
        payload = integrity["payload"]
        if (
            not isinstance(authority, dict)
            or set(authority) != {"path", "sha256"}
            or not isinstance(authority.get("path"), str)
            or not isinstance(authority.get("sha256"), str)
            or not SHA256.fullmatch(authority["sha256"])
            or not isinstance(payload, dict)
            or set(payload) != {"algorithm", "sha256"}
            or not isinstance(payload.get("algorithm"), str)
            or not isinstance(payload.get("sha256"), str)
            or not SHA256.fullmatch(payload["sha256"])
        ):
            raise ValueError("manifest integrity authority/payload pins are invalid")
        authority_path = _safe_relative_path(authority["path"], "integrity.authority.path").as_posix()
        definition_path = f".{kit_id}-kit/kit.yaml"
        definition_items = [item for item in files if item["destination"] == definition_path]
        authority_items = [item for item in files if item["destination"] == authority_path]
        if (
            payload["algorithm"] != "TEST_KIT_PACKAGE_PAYLOAD_V1"
            or authority_path == definition_path
            or len(definition_items) != 1
            or definition_items[0]["source"] != f"kits/{kit_id}/kit.yaml"
            or len(authority_items) != 1
            or PurePosixPath(authority_path).parts[0] in names
        ):
            raise ValueError("manifest integrity paths or digest algorithm are unsupported")
    for field in ("dependencies",):
        if field in manifest and not isinstance(manifest[field], list):
            raise ValueError(f"manifest {field} must be a list")
    for dependency in manifest.get("dependencies", []):
        if not isinstance(dependency, dict) or not isinstance(dependency.get("id"), str) or not isinstance(dependency.get("version"), str):
            raise ValueError("manifest dependencies require id and version strings")
    if "capabilities" in manifest and not isinstance(manifest["capabilities"], dict):
        raise ValueError("manifest capabilities must be an object")
    if "install_metadata" in manifest and not isinstance(manifest["install_metadata"], dict):
        raise ValueError("manifest install_metadata must be an object")
    if "agents" in manifest:
        agents = manifest["agents"]
        if (
            not isinstance(agents, list)
            or not agents
            or any(not isinstance(agent, str) or agent not in ("codex", "claude-code") for agent in agents)
            or len(set(agents)) != len(agents)
        ):
            raise ValueError("manifest agents must be a unique list of supported native agents")
    if "scopes" in manifest:
        scopes = manifest["scopes"]
        if not isinstance(scopes, list) or not scopes or any(scope not in ("user", "project") for scope in scopes) or len(set(scopes)) != len(scopes):
            raise ValueError("manifest scopes must be a unique list of user/project scopes")
    if "prerequisites" in manifest:
        prerequisites = manifest["prerequisites"]
        python = prerequisites.get("python") if isinstance(prerequisites, dict) else None
        if not isinstance(python, list) or len(python) != 2 or any(type(part) is not int or part < 0 for part in python):
            raise ValueError("manifest prerequisites.python must be a [major, minor] version")
    metadata = manifest.get("install_metadata", {})
    if "source_repository" in metadata and not isinstance(metadata["source_repository"], str):
        raise ValueError("manifest install_metadata.source_repository must be a string")
    return manifest


def skill_composition(manifest):
    return [manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"], *manifest["skills"]["optional"]]


def _valid_skill(directory, skill):
    try:
        content = (Path(directory) / "SKILL.md").read_text(encoding="utf-8").lstrip("\ufeff")
    except OSError:
        return False
    parts = content.split("---", 2)
    if len(parts) != 3 or parts[0].strip():
        return False
    header = parts[1]
    name = re.search(r"(?m)^name:\s*(.*?)\s*$", header)
    description = re.search(r"(?m)^description:\s*(.*?)\s*$", header)
    if not name or not description or name.group(1).strip("\"'") != skill:
        return False
    value = description.group(1).strip().strip("\"'")
    if value and value not in (">", "|-", "|", ">-"):
        return True
    lines = header.splitlines()
    line_number = header[:description.start()].count("\n")
    for line in lines[line_number + 1:]:
        if line.strip() and (len(line) - len(line.lstrip())) > 0:
            return True
        if line.strip() and (len(line) - len(line.lstrip())) == 0:
            break
    return False


def tree_hash(directory):
    directory = Path(directory)
    digest = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"refusing to hash symlink: {path}")
        if path.is_file():
            digest.update(path.relative_to(directory).as_posix().encode("utf-8"))
            digest.update(b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
    return digest.hexdigest()


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".ba-kit-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _content_hash(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"managed file is missing, not regular, or a symlink: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _managed_skill_files(source, skill, classification):
    result = {}
    source = Path(source)
    for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix().encode("utf-8")):
        if path.is_symlink():
            raise ValueError(f"refusing to record symlink: {path}")
        if path.is_file():
            relative = path.relative_to(source).as_posix()
            result[f"{skill}/{relative}"] = {"sha256": _content_hash(path), "classification": classification}
    return result


def _recorded_skill_files(record, skill):
    prefix = f"{skill}/"
    return {
        path: details
        for path, details in record.get("managed_files", {}).items()
        if path.startswith(prefix)
    }


def _target_path(target_dir, relative):
    target_dir = Path(target_dir).resolve()
    parts = _safe_relative_path(relative, "destination").parts
    path = target_dir.joinpath(*parts)
    current = target_dir
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"managed destination passes through a symlink: {current}")
    try:
        path.parent.resolve().relative_to(target_dir)
    except ValueError as error:
        raise ValueError(f"managed destination escapes target: {path}") from error
    return path


def _source_metadata(source_root, manifest, authority=None):
    config = manifest.get("install_metadata")
    if not config and authority is None:
        return {}
    metadata = {}
    if config:
        metadata = {
            "manifest_schema_version": manifest["schema_version"],
            "source_repository": config.get("source_repository"),
            "source_revision": config.get("source_revision"),
            "source_dirty": None,
            "pinned_dependencies": manifest.get("dependencies", []),
            "capabilities": manifest.get("capabilities", {}),
        }
    if authority is not None:
        metadata["payload_digest_algorithm"] = authority["payload_digest_algorithm"]
        metadata["payload_tree_sha256"] = authority["payload_tree_sha256"]
    git = shutil.which("git") if config else None
    if git:
        revision = subprocess.run(
            [git, "-C", str(source_root), "rev-parse", "--verify", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        if revision.returncode == 0:
            metadata["source_revision"] = revision.stdout.strip()
            status = subprocess.run(
                [git, "-C", str(source_root), "status", "--porcelain", "--untracked-files=no"],
                capture_output=True, text=True, check=False,
            )
            if status.returncode == 0:
                metadata["source_dirty"] = bool(status.stdout.strip())
    return metadata


def _validate_package_authority(authority, manifest):
    from tooling.lib.package import PAYLOAD_DIGEST_ALGORITHM, payload_tree_sha256_from_inventory

    if (
        not isinstance(authority, dict)
        or set(authority) != {
            "schema_version", "kit_id", "kit_version", "manifest_schema_version",
            "managed_files", "managed_file_count", "payload_digest_algorithm", "payload_tree_sha256",
        }
        or type(authority.get("schema_version")) is not int
        or authority["schema_version"] != 1
        or not isinstance(authority.get("kit_id"), str)
        or authority.get("kit_id") != manifest["id"]
        or not isinstance(authority.get("kit_version"), str)
        or authority.get("kit_version") != manifest["version"]
        or type(authority.get("manifest_schema_version")) is not int
        or authority.get("manifest_schema_version") != manifest["schema_version"]
        or not isinstance(authority.get("payload_digest_algorithm"), str)
        or authority.get("payload_digest_algorithm") != PAYLOAD_DIGEST_ALGORITHM
        or type(authority.get("managed_file_count")) is not int
        or not isinstance(authority.get("managed_files"), list)
        or not isinstance(authority.get("payload_tree_sha256"), str)
        or not SHA256.fullmatch(authority["payload_tree_sha256"])
    ):
        raise ValueError("invalid package authority schema or identity")

    authority_path = manifest["integrity"]["authority"]["path"]
    classes = {
        skill: "REQUIRED_SKILL" if skill in {
            manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"]
        } else "OPTIONAL_SKILL"
        for skill in skill_composition(manifest)
    }
    definition_path = f".{manifest['id']}-kit/kit.yaml"
    exact_classes = {
        item["destination"]: item["classification"]
        for item in manifest.get("files", [])
        if item["destination"] not in (authority_path, definition_path)
    }
    entries, normalized_names = {}, set()
    for item in authority["managed_files"]:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "classification"}:
            raise ValueError("invalid package authority file entry")
        relative = item["path"]
        try:
            safe = _safe_relative_path(relative, "package authority path").as_posix()
        except ValueError as error:
            raise ValueError(f"invalid package authority path: {relative}") from error
        folded = safe.casefold()
        classification = exact_classes.get(safe)
        first = PurePosixPath(safe).parts[0]
        if classification is None and first in classes and safe.startswith(f"{first}/"):
            classification = classes[first]
        if (
            safe != relative
            or unicodedata.normalize("NFC", safe) != safe
            or safe == authority_path
            or folded in normalized_names
            or classification is None
            or item["classification"] != classification
            or not isinstance(item["sha256"], str)
            or not SHA256.fullmatch(item["sha256"])
        ):
            raise ValueError(f"invalid or duplicate package authority entry: {relative}")
        normalized_names.add(folded)
        entries[safe] = {"sha256": item["sha256"], "classification": classification}
    if authority["managed_file_count"] != len(entries):
        raise ValueError("package authority managed_file_count differs from its inventory")
    digest_entries = [{"path": path, **details} for path, details in entries.items()]
    if payload_tree_sha256_from_inventory(digest_entries) != authority["payload_tree_sha256"]:
        raise ValueError("package authority digest does not match its inventory")
    payload_pin = manifest["integrity"]["payload"]
    if authority["payload_digest_algorithm"] != payload_pin["algorithm"] or authority["payload_tree_sha256"] != payload_pin["sha256"]:
        raise ValueError("package authority payload identity differs from the manifest pin")
    return entries


def _another_kit_owns(target_dir, collection, key, own_record):
    for path in Path(target_dir).glob(".*-kit-install.json"):
        if path == own_record:
            continue
        try:
            record = _read_json(path)
            _validate_install_record(record, path, record.get("kit"))
            ownership = record.get(collection)
            if isinstance(ownership, dict) and key in ownership:
                return True
            if collection == "files" and key in record.get("managed_files", {}):
                return True
        except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
            return True
    return False


def _hash_managed(path, kind):
    return tree_hash(path) if kind == "skill" else _content_hash(path)


def _apply_plan(target_dir, plan, record_path, record):
    if not plan and not record.get("skills") and not record.get("files") and not record.get("managed_files"):
        return
    staging = Path(tempfile.mkdtemp(prefix=f".{record['kit']}-kit-stage-", dir=str(target_dir)))
    backups = staging / "backups"
    staged = staging / "new"
    applied = []
    rollback_failed = False
    try:
        for index, item in enumerate(plan):
            if item["action"] != "write":
                continue
            stage_path = staged / str(index)
            stage_path.parent.mkdir(parents=True, exist_ok=True)
            if item["kind"] == "skill":
                shutil.copytree(item["source"], stage_path)
                actual = tree_hash(stage_path)
            else:
                shutil.copyfile(item["source"], stage_path)
                actual = _content_hash(stage_path)
            if actual != item["new_hash"]:
                raise ValueError(f"source changed while preparing install: {item['source']}")
            item["stage_path"] = stage_path

        # ponytail: no cross-process install lock; per-target locking can be added if concurrent installs matter.
        for index, item in enumerate(plan):
            destination = item["destination"]
            old_hash = item.get("old_hash")
            if destination.exists() or destination.is_symlink():
                if destination.is_symlink() or _hash_managed(destination, item["kind"]) != old_hash:
                    raise ValueError(f"managed destination changed during install; preserved: {destination}")
                backup = backups / str(index)
                backup.parent.mkdir(parents=True, exist_ok=True)
                os.replace(destination, backup)
            else:
                backup = None
                if old_hash is not None:
                    raise ValueError(f"managed destination disappeared during install: {destination}")
            applied.append((item, backup))
            if item["action"] == "write":
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(item["stage_path"], destination)
        _write_json(record_path, record)
    except BaseException as error:
        for item, backup in reversed(applied):
            destination = item["destination"]
            if destination.exists() and not destination.is_symlink():
                try:
                    if _hash_managed(destination, item["kind"]) == item.get("new_hash"):
                        shutil.rmtree(destination) if destination.is_dir() else destination.unlink()
                except (OSError, ValueError):
                    pass
            if backup is not None and backup.exists():
                if destination.exists():
                    rollback_failed = True
                else:
                    try:
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(backup, destination)
                    except OSError:
                        rollback_failed = True
        if rollback_failed:
            raise RuntimeError(f"install rollback incomplete; preserved recovery files at {staging}") from error
        raise
    finally:
        if not rollback_failed:
            shutil.rmtree(staging, ignore_errors=True)


def install(source_root, target_dir, kit_id="ba", *, project_root=None):
    source_root = Path(source_root).resolve()
    target_dir = Path(target_dir).expanduser().resolve()
    manifest = load_manifest(source_root, kit_id)
    integrity = manifest.get("integrity")
    authority = None
    if integrity:
        from tooling.lib.package import validate_source_package_integrity

        authority, _, _ = validate_source_package_integrity(source_root, manifest)
    required = {manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"]}
    target_dir.mkdir(parents=True, exist_ok=True)
    record_path = _install_record_path(target_dir, kit_id)
    record = {"schema_version": 1, "kit": kit_id, "version": manifest["version"], "skills": {}, "managed_files": {}, "managed_file_count": 0}
    if record_path.exists():
        try:
            record = _read_json(record_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid install record {record_path}: {error}") from error
        _validate_install_record(record, record_path, kit_id)

    authority_managed = {
        item["path"]: {"sha256": item["sha256"], "classification": item["classification"]}
        for item in (authority or {}).get("managed_files", [])
    }
    if integrity:
        record.pop("package_digest_algorithm", None)
        record.pop("package_tree_sha256", None)
    record.update({"version": manifest["version"], **_source_metadata(source_root, manifest, authority)})

    installed, preserved, skipped, conflicts, plan = [], [], [], [], []
    composition = skill_composition(manifest)
    required_skills = {manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"]}
    next_skills = {}
    next_managed_files = {}

    def retain_skill_files(skill):
        prefix = f"{skill}/"
        package_files = {path: details for path, details in authority_managed.items() if path.startswith(prefix)}
        next_managed_files.update(package_files or _recorded_skill_files(record, skill))

    for skill in composition:
        source_rel = manifest.get("skill_sources", {}).get(skill, skill)
        source = _resolve_under(source_root, source_rel, f"skill source {skill}")
        destination = _target_path(target_dir, skill)
        if not _valid_skill(source, skill):
            if skill in required:
                raise ValueError(f"required skill is missing or has invalid Agent Skills frontmatter: {source / 'SKILL.md'}")
            skipped.append(skill)
            if skill in record["skills"]:
                next_skills[skill] = record["skills"][skill]
                retain_skill_files(skill)
            continue
        source_hash = tree_hash(source)
        old = record["skills"].get(skill)
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_dir() or not (destination / "SKILL.md").is_file():
                if skill in required:
                    raise ValueError(f"skill destination exists but is not a valid skill; preserved: {destination}")
                preserved.append(skill)
                if old:
                    next_skills[skill] = old
                    retain_skill_files(skill)
                    conflicts.append(skill)
                continue
            current_hash = tree_hash(destination)
            if old and old.get("sha256") == current_hash:
                next_skills[skill] = {"sha256": source_hash}
                classification = "REQUIRED_SKILL" if skill in required_skills else "OPTIONAL_SKILL"
                next_managed_files.update(_managed_skill_files(source, skill, classification))
                if current_hash != source_hash:
                    plan.append({"kind": "skill", "key": skill, "action": "write", "source": source, "destination": destination, "old_hash": current_hash, "new_hash": source_hash})
                else:
                    installed.append(skill)
                if current_hash != source_hash:
                    installed.append(skill)
            else:
                preserved.append(skill)
                if old:
                    next_skills[skill] = old
                    retain_skill_files(skill)
                    conflicts.append(skill)
            continue
        plan.append({"kind": "skill", "key": skill, "action": "write", "source": source, "destination": destination, "old_hash": None, "new_hash": source_hash})
        next_skills[skill] = {"sha256": source_hash}
        classification = "REQUIRED_SKILL" if skill in required_skills else "OPTIONAL_SKILL"
        next_managed_files.update(_managed_skill_files(source, skill, classification))
        installed.append(skill)

    declared_files = {item["destination"]: item for item in manifest.get("files", [])}
    authority_path = integrity["authority"]["path"] if integrity else None
    definition_path = f".{kit_id}-kit/kit.yaml" if integrity else None
    metadata_paths = {path for path in (authority_path, definition_path) if path}
    next_files = {}
    for relative, item in declared_files.items():
        source = _resolve_under(source_root, item["source"], f"file source {item['source']}")
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"required manifest file is missing or not regular: {source}")
        source_hash = _content_hash(source)
        destination = _target_path(target_dir, relative)
        old = record.get("files", {}).get(relative)
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or not destination.is_file():
                raise ValueError(f"managed file destination exists but is not a regular file; preserved: {destination}")
            current_hash = _content_hash(destination)
            if old and old.get("sha256") == current_hash:
                details = {"sha256": source_hash, "classification": item["classification"]}
                next_files[relative] = details
                if relative not in metadata_paths:
                    next_managed_files[relative] = details
                if current_hash != source_hash:
                    plan.append({"kind": "file", "key": relative, "action": "write", "source": source, "destination": destination, "old_hash": current_hash, "new_hash": source_hash})
                    installed.append(relative)
                else:
                    installed.append(relative)
            else:
                preserved.append(relative)
                if old:
                    expected = {"sha256": source_hash, "classification": item["classification"]} if integrity else old
                    next_files[relative] = expected
                    if relative not in metadata_paths:
                        next_managed_files[relative] = authority_managed.get(relative, record.get("managed_files", {}).get(relative, expected))
                    conflicts.append(relative)
        else:
            plan.append({"kind": "file", "key": relative, "action": "write", "source": source, "destination": destination, "old_hash": None, "new_hash": source_hash})
            details = {"sha256": source_hash, "classification": item["classification"]}
            next_files[relative] = details
            if relative not in metadata_paths:
                next_managed_files[relative] = details
            installed.append(relative)

    for skill, details in record["skills"].items():
        if skill in composition:
            continue
        destination = _target_path(target_dir, skill)
        if not destination.exists():
            continue
        if destination.is_symlink() or not destination.is_dir():
            preserved.append(skill)
            next_skills[skill] = details
            retain_skill_files(skill)
        elif _another_kit_owns(target_dir, "skills", skill, record_path):
            preserved.append(skill)
            next_skills[skill] = details
            retain_skill_files(skill)
        elif tree_hash(destination) != details["sha256"]:
            preserved.append(skill)
            next_skills[skill] = details
            retain_skill_files(skill)
            conflicts.append(skill)
        else:
            plan.append({"kind": "skill", "key": skill, "action": "remove", "destination": destination, "old_hash": details["sha256"], "new_hash": None})

    for relative, details in record.get("files", {}).items():
        if relative in declared_files:
            continue
        destination = _target_path(target_dir, relative)
        if not destination.exists():
            continue
        if destination.is_symlink() or not destination.is_file():
            preserved.append(relative)
            next_files[relative] = details
            next_managed_files[relative] = record.get("managed_files", {}).get(relative, details)
        elif _another_kit_owns(target_dir, "files", relative, record_path):
            preserved.append(relative)
            next_files[relative] = details
            next_managed_files[relative] = record.get("managed_files", {}).get(relative, details)
        elif _content_hash(destination) != details["sha256"]:
            preserved.append(relative)
            next_files[relative] = details
            next_managed_files[relative] = record.get("managed_files", {}).get(relative, details)
            conflicts.append(relative)
        else:
            plan.append({"kind": "file", "key": relative, "action": "remove", "destination": destination, "old_hash": details["sha256"], "new_hash": None})

    record["skills"] = next_skills
    if declared_files or "files" in record:
        record["files"] = next_files
    else:
        record.pop("files", None)
    record["managed_files"] = dict(sorted(next_managed_files.items(), key=lambda item: item[0].encode("utf-8")))
    record["managed_file_count"] = len(record["managed_files"])
    _apply_plan(target_dir, plan, record_path, record)
    tea_project_config = None
    if kit_id == "test":
        resolved_project_root = Path(project_root).resolve() if project_root is not None else _infer_project_root_from_target(target_dir)
        if resolved_project_root is not None:
            tea_project_config = _ensure_test_tea_project_config(resolved_project_root)
    return {
        "installed": installed,
        "preserved": preserved,
        "conflicts": sorted(set(conflicts)),
        "skipped": skipped,
        "tea_project_config": tea_project_config,
    }


def _prune_empty_parents(path, stop):
    path, stop = Path(path), Path(stop)
    while path != stop:
        try:
            path.rmdir()
        except OSError:
            break
        path = path.parent


def uninstall(target_dir, kit_id="ba"):
    target_dir = Path(target_dir).expanduser().resolve()
    record_path = _install_record_path(target_dir, kit_id)
    if not record_path.is_file():
        return {"removed": [], "preserved": []}
    try:
        record = _read_json(record_path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid install record {record_path}: {error}") from error
    _validate_install_record(record, record_path, kit_id)
    had_file_records = "files" in record
    removed, preserved, remaining_skills, remaining_files, remaining_managed_files = [], [], {}, {}, {}
    for skill, details in record["skills"].items():
        path = _target_path(target_dir, skill)
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_dir():
            preserved.append(skill)
            remaining_skills[skill] = details
            remaining_managed_files.update(_recorded_skill_files(record, skill))
            continue
        try:
            unchanged = tree_hash(path) == details["sha256"]
        except (OSError, ValueError):
            unchanged = False
        if _another_kit_owns(target_dir, "skills", skill, record_path) or not unchanged:
            preserved.append(skill)
            remaining_skills[skill] = details
            remaining_managed_files.update(_recorded_skill_files(record, skill))
            continue
        shutil.rmtree(path)
        removed.append(skill)
    for relative, details in record.get("files", {}).items():
        path = _target_path(target_dir, relative)
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_file():
            preserved.append(relative)
            remaining_files[relative] = details
            remaining_managed_files[relative] = record.get("managed_files", {}).get(relative, details)
            continue
        try:
            unchanged = _content_hash(path) == details["sha256"]
        except (OSError, ValueError):
            unchanged = False
        if _another_kit_owns(target_dir, "files", relative, record_path) or not unchanged:
            preserved.append(relative)
            remaining_files[relative] = details
            remaining_managed_files[relative] = record.get("managed_files", {}).get(relative, details)
            continue
        path.unlink()
        removed.append(relative)
        _prune_empty_parents(path.parent, target_dir)
    if remaining_skills or remaining_files:
        record["skills"] = remaining_skills
        record["managed_files"] = dict(sorted(remaining_managed_files.items(), key=lambda item: item[0].encode("utf-8")))
        record["managed_file_count"] = len(record["managed_files"])
        if had_file_records or remaining_files:
            record["files"] = remaining_files
        _write_json(record_path, record)
    else:
        record_path.unlink()
    return {"removed": removed, "preserved": preserved}


def _skill_names(manifest):
    workflow = manifest["workflow"]["skill"]
    required = [workflow, *manifest["core"], *manifest["skills"]["required"]]
    return required, manifest["skills"]["optional"]


TEST_TEA_CONFIG_RELATIVE = Path("_bmad/tea/config.yaml")
TEST_TEA_REQUIRED_CONFIG_FIELDS = (
    "user_name",
    "communication_language",
    "document_output_language",
    "output_folder",
    "test_artifacts",
    "test_stack_type",
)


def _infer_project_root_from_target(target_dir):
    target = Path(target_dir).expanduser().resolve()
    if target.name == "skills" and target.parent.name in {".agents", ".claude"}:
        return target.parent.parent
    return None


def _tea_project_config_text(project_root):
    # Keep starter paths portable so this project-owned config can be committed
    # and shared by every tester regardless of checkout location.
    Path(project_root).resolve()
    test_artifacts = "test-runs"
    return (
        "user_name: Tester\n"
        "communication_language: Vietnamese\n"
        "document_output_language: Vietnamese\n"
        f"output_folder: {test_artifacts}\n"
        f"test_artifacts: {test_artifacts}\n"
        "test_stack_type: fullstack\n"
        "tea_use_playwright_utils: false\n"
        "tea_use_pactjs_utils: false\n"
        "tea_pact_mcp: none\n"
        "tea_browser_automation: none\n"
        "tea_execution_mode: sequential\n"
        "tea_capability_probe: false\n"
    )


def _ensure_test_tea_project_config(project_root):
    project_root = Path(project_root).expanduser().resolve()
    path = project_root / TEST_TEA_CONFIG_RELATIVE
    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"TEA project config exists but is not a regular file: {path}")
        return {"status": "PRESERVED", "path": str(path)}

    for directory in (project_root / "_bmad", project_root / "_bmad/tea"):
        if directory.exists() or directory.is_symlink():
            if directory.is_symlink() or not directory.is_dir():
                raise ValueError(f"refusing to write TEA project config through unsafe path: {directory}")
        else:
            directory.mkdir()

    test_runs = project_root / "test-runs"
    if test_runs.exists() or test_runs.is_symlink():
        if test_runs.is_symlink() or not test_runs.is_dir():
            raise ValueError(f"Test Kit output path exists but is not a directory: {test_runs}")
    else:
        test_runs.mkdir()

    path.write_text(_tea_project_config_text(project_root), encoding="utf-8", newline="\n")
    return {"status": "CREATED", "path": str(path)}


def _flat_yaml_mapping(path):
    fields = {}
    for number, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw[:1].isspace() or ":" not in raw:
            raise ValueError(f"line {number}: expected a flat key: value entry")
        key, value = raw.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key or key in fields:
            raise ValueError(f"line {number}: invalid or duplicate key")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        fields[key] = value
    return fields


def _check_test_tea_project_config(project_root):
    project_root = Path(project_root).expanduser().resolve()
    path = project_root / TEST_TEA_CONFIG_RELATIVE
    if path.is_symlink() or not path.is_file():
        return False, f"TEA_PROJECT_CONFIG_MISSING: {path}"
    try:
        fields = _flat_yaml_mapping(path)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        return False, f"TEA_PROJECT_CONFIG_INVALID: {error}"
    missing = [key for key in TEST_TEA_REQUIRED_CONFIG_FIELDS if not fields.get(key)]
    if missing:
        return False, "TEA_PROJECT_CONFIG_INVALID: missing/non-empty fields: " + ", ".join(missing)
    return True, str(path)


def _dependency_checks(manifest, target_dir):
    import importlib.util

    checks = []
    for dependency in manifest.get("dependencies", []):
        if dependency.get("source") == "bundled pinned skill":
            continue
        dependency_id = dependency["id"]
        found = True
        detail = dependency_id
        if dependency_id == "python":
            minimum = tuple(int(part) for part in dependency["version"].removeprefix(">=").split("."))
            found = tuple(sys.version_info[:2]) >= minimum
        elif dependency_id == "codex-cli":
            try:
                from tooling.lib.codex_cli import resolve_codex_command

                resolve_codex_command()
            except (ImportError, RuntimeError) as error:
                found = False
                detail = str(error)
        elif dependency_id in ("node", "npm"):
            commands = ("node.exe", "node") if dependency_id == "node" else ("npm.cmd", "npm")
            found = any(shutil.which(command) for command in commands)
        elif dependency_id in ("openpyxl", "et-xmlfile"):
            module_name = "et_xmlfile" if dependency_id == "et-xmlfile" else dependency_id
            found = importlib.util.find_spec(module_name) is not None
        elif dependency_id == "xmind":
            found = (Path(target_dir) / ".test-kit/tooling/xmind/node_modules/xmind/package.json").is_file()
        else:
            continue
        if not found:
            kind = "contract" if dependency.get("required") else "dependency"
            checks.append(("DEPENDENCY_MISSING", False, kind, detail))
    return checks


def _doctor_file_hash(target_dir, relative):
    try:
        path = _target_path(target_dir, relative)
        return _content_hash(path) if path.is_file() and not path.is_symlink() else None
    except (OSError, ValueError):
        return None


def _doctor_manifest(source_root, target_dir, kit_id):
    canonical = Path(target_dir) / f".{kit_id}-kit" / "kit.yaml"
    if canonical.exists() or canonical.is_symlink() or canonical.parent.is_symlink():
        if canonical.is_symlink() or canonical.parent.is_symlink() or not canonical.is_file():
            raise ValueError(f"canonical installed package definition is missing, not regular, or a symlink: {canonical}")
        return validate_manifest_data(_read_json(canonical), kit_id, canonical), canonical

    source_manifest = load_manifest(source_root, kit_id)
    if source_manifest.get("integrity"):
        raise ValueError(f"canonical installed package definition is missing: {canonical}")
    return source_manifest, None


def _with_project_policy(report, target_dir, kit_id, project_root):
    """Diagnose project inputs independently of installed-package ownership."""
    if kit_id != "test":
        return report
    target = Path(target_dir).resolve()
    if project_root is None:
        if target.name == "skills" and target.parent.name in {".agents", ".claude"}:
            project_root = target.parent.parent
        else:
            # Generic package inspection has no unambiguous project context.
            return report
    from tooling.lib.test_kit_policy import check_project_policy

    project_report = check_project_policy(Path(project_root).resolve())
    report["project_policy"] = project_report
    if project_report["status"] == "FAIL":
        report["checks"].extend(
            (finding["code"], False, "project_policy", finding["message"])
            for finding in project_report["findings"]
        )
        report["status"] = "FAIL"
    else:
        name = "NO_PROJECT_POLICY" if project_report["status"] == "NO_PROJECT_POLICY" else "PROJECT_POLICY_VALID"
        report["checks"].append((name, True, "project_policy", ""))
    return report


def doctor(source_root, target_dir, kit_id="ba", *, project_root=None):
    source_root = Path(source_root).resolve()
    target_dir = Path(target_dir).expanduser().resolve()
    try:
        manifest, definition_file = _doctor_manifest(source_root, target_dir, kit_id)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return _with_project_policy(
            {"status": "FAIL", "kit": kit_id, "checks": [("PACKAGE_DEFINITION_INVALID", False, "contract", str(error))]},
            target_dir, kit_id, project_root,
        )
    checks = []
    integrity = manifest.get("integrity")
    authority_spec = integrity.get("authority") if integrity else None
    authority_entries, authority_error, authority_sha256 = {}, None, None
    if authority_spec:
        try:
            authority_path = _target_path(target_dir, authority_spec["path"])
            if authority_path.is_symlink() or not authority_path.is_file():
                raise ValueError("package authority is missing or not a regular file")
            authority_bytes = authority_path.read_bytes()
            authority_sha256 = hashlib.sha256(authority_bytes).hexdigest()
            if authority_sha256 != authority_spec["sha256"]:
                raise ValueError("package authority SHA-256 differs from the installed manifest pin")
            authority = _read_json(authority_path)
            authority_entries = _validate_package_authority(authority, manifest)
            from tooling.lib.package import package_authority_bytes

            if authority_bytes != package_authority_bytes(authority):
                raise ValueError("package authority serialization is not canonical")
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            authority_error = str(error)
        checks.append(("PACKAGE_AUTHORITY_INVALID", authority_error is None, "contract", authority_error or ""))

    required, optional = _skill_names(manifest)
    for skill in required:
        ok = _valid_skill(target_dir / skill, skill)
        detail = "" if ok else f"missing or invalid: {target_dir / skill / 'SKILL.md'}"
        checks.append((skill, ok, "required", detail))
    for skill in optional:
        ok = _valid_skill(target_dir / skill, skill)
        detail = "" if ok else f"unavailable: {target_dir / skill / 'SKILL.md'}"
        checks.append((skill, ok, "optional", detail))

    record_path = _install_record_path(target_dir, kit_id)
    record_required = bool(manifest.get("files") or manifest.get("install_metadata") or integrity)
    if record_required or record_path.exists():
        try:
            record = _read_json(record_path)
            _validate_install_record(record, record_path, kit_id)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            record = {}
            checks.append(("installed provenance", False, "contract", str(error)))
            if manifest.get("install_metadata") or integrity:
                checks.append(("PACKAGE_METADATA_INVALID", False, "contract", str(error)))
        else:
            version_ok = record.get("version") == manifest["version"]
            checks.append(("installed provenance", version_ok, "contract", "" if version_ok else "install record version differs from the manifest"))

            if manifest.get("install_metadata") or integrity:
                metadata_errors = []
                if manifest.get("install_metadata"):
                    if record.get("manifest_schema_version") != manifest["schema_version"]:
                        metadata_errors.append("manifest schema version differs")
                    if record.get("source_repository") != manifest["install_metadata"].get("source_repository"):
                        metadata_errors.append("source repository differs")
                    if record.get("pinned_dependencies") != manifest.get("dependencies", []):
                        metadata_errors.append("pinned dependency metadata differs")
                    if record.get("capabilities") != manifest.get("capabilities", {}):
                        metadata_errors.append("capability metadata differs")
                if integrity:
                    if "managed_files" not in record or "managed_file_count" not in record:
                        metadata_errors.append("managed-file inventory is missing")
                    payload_pin = integrity["payload"]
                    if record.get("payload_digest_algorithm") != payload_pin["algorithm"]:
                        metadata_errors.append("install record payload digest algorithm differs from the manifest")
                    if record.get("payload_tree_sha256") != payload_pin["sha256"]:
                        metadata_errors.append("install record payload digest differs from the manifest")
                    if authority_error:
                        metadata_errors.append(f"invalid package authority: {authority_error}")
                    else:
                        if record.get("payload_digest_algorithm") != authority["payload_digest_algorithm"]:
                            metadata_errors.append("install record payload digest algorithm differs from package authority")
                        if record.get("payload_tree_sha256") != authority["payload_tree_sha256"]:
                            metadata_errors.append("install record payload digest differs from package authority")
                        record_inventory = record.get("managed_files", {})
                        if set(record_inventory) != set(authority_entries):
                            metadata_errors.append("install record managed-file set differs from package authority")
                        else:
                            for relative, expected in authority_entries.items():
                                if record_inventory[relative] != expected:
                                    metadata_errors.append(f"install record managed-file identity differs for {relative}")
                        if record.get("managed_file_count") != len(authority_entries):
                            metadata_errors.append("install record managed_file_count differs from package authority")
                        authority_record = record.get("files", {}).get(authority_spec["path"])
                        if (
                            authority_record != {"sha256": authority_sha256, "classification": next(item["classification"] for item in manifest["files"] if item["destination"] == authority_spec["path"])}
                        ):
                            metadata_errors.append("package authority file ownership/hash differs from installed authority")
                        definition_path = f".{kit_id}-kit/kit.yaml"
                        for item in manifest.get("files", []):
                            relative = item["destination"]
                            if relative in (authority_spec["path"], definition_path):
                                continue
                            if record.get("files", {}).get(relative) != authority_entries.get(relative):
                                metadata_errors.append(f"install record file identity differs from package authority for {relative}")

                checks.append(("PACKAGE_METADATA_INVALID", not metadata_errors, "contract", "; ".join(metadata_errors)))

            recorded_files = record.get("files", {})
            if integrity:
                definition_path = f".{kit_id}-kit/kit.yaml"
                definition_hash = _content_hash(definition_file)
                if recorded_files.get(definition_path) != {
                    "sha256": definition_hash,
                    "classification": next(item["classification"] for item in manifest["files"] if item["destination"] == definition_path),
                }:
                    checks.append(("PACKAGE_DEFINITION_INVALID", False, "contract", "installed root package definition differs from its recorded file identity"))
                authority_record = recorded_files.get(authority_spec["path"])
                if authority_record is None:
                    checks.append(("PACKAGE_METADATA_INVALID", False, "contract", "package authority ownership is missing from install record"))
                elif _doctor_file_hash(target_dir, authority_spec["path"]) != authority_record["sha256"]:
                    checks.append(("PACKAGE_AUTHORITY_INVALID", False, "contract", "installed package authority differs from install record file identity"))
            else:
                for relative, details in recorded_files.items():
                    actual = _doctor_file_hash(target_dir, relative)
                    if actual is None:
                        checks.append(("MISSING_MANAGED_FILE", False, "contract", relative))
                    elif actual != details["sha256"]:
                        checks.append(("MODIFIED_MANAGED_FILE", False, "contract", f"{relative}: expected {details['sha256']}, actual {actual}"))

            manifest_file_paths = {item["destination"] for item in manifest.get("files", [])}
            managed_files = authority_entries if integrity and not authority_error else record.get("managed_files", {})
            observed_skill_failures = set()
            for relative, details in managed_files.items():
                if integrity:
                    actual = _doctor_file_hash(target_dir, relative)
                    if actual is None:
                        checks.append(("MISSING_MANAGED_FILE", False, "contract", relative))
                        observed_skill_failures.add(PurePosixPath(relative).parts[0])
                    elif actual != details["sha256"]:
                        checks.append(("MODIFIED_MANAGED_FILE", False, "contract", f"{relative}: expected {details['sha256']}, actual {actual}"))
                        observed_skill_failures.add(PurePosixPath(relative).parts[0])
                else:
                    if relative in manifest_file_paths:
                        continue
                    actual = _doctor_file_hash(target_dir, relative)
                    if actual is None:
                        checks.append(("MISSING_MANAGED_FILE", False, "contract", relative))
                        observed_skill_failures.add(PurePosixPath(relative).parts[0])
                    elif actual != details["sha256"]:
                        checks.append(("MODIFIED_MANAGED_FILE", False, "contract", f"{relative}: expected {details['sha256']}, actual {actual}"))
                        observed_skill_failures.add(PurePosixPath(relative).parts[0])

            for skill, details in record.get("skills", {}).items():
                try:
                    skill_path = _target_path(target_dir, skill)
                except (OSError, ValueError):
                    checks.append(("MODIFIED_MANAGED_FILE", False, "contract", f"{skill}/<unsafe skill tree>"))
                    continue
                if not skill_path.is_dir() or skill_path.is_symlink():
                    if skill not in observed_skill_failures:
                        checks.append(("MISSING_MANAGED_FILE", False, "contract", f"{skill}/<skill tree>"))
                    continue
                try:
                    actual_tree = tree_hash(skill_path)
                except (OSError, ValueError):
                    actual_tree = None
                if actual_tree != details["sha256"] and skill not in observed_skill_failures:
                    checks.append(("MODIFIED_MANAGED_FILE", False, "contract", f"{skill}/<skill tree>: expected {details['sha256']}, actual {actual_tree}"))

            if not managed_files and not integrity:
                for relative, details in recorded_files.items():
                    if relative in manifest_file_paths:
                        continue
                    actual = _doctor_file_hash(target_dir, relative)
                    if actual is None:
                        checks.append(("MISSING_MANAGED_FILE", False, "contract", relative))
                    elif actual != details["sha256"]:
                        checks.append(("MODIFIED_MANAGED_FILE", False, "contract", f"{relative}: expected {details['sha256']}, actual {actual}"))

    if kit_id == "test":
        resolved_project_root = Path(project_root).resolve() if project_root is not None else _infer_project_root_from_target(target_dir)
        if resolved_project_root is not None:
            tea_ok, tea_detail = _check_test_tea_project_config(resolved_project_root)
            checks.append(("TEA_PROJECT_CONFIG", tea_ok, "contract", tea_detail))

    checks.extend(_dependency_checks(manifest, target_dir))

    if kit_id == "ba":
        state_path = source_root / "ba-workflow/templates/workflow-state.json"
        try:
            state_errors = validate_state_data(json.loads(state_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as error:
            state_errors = [str(error)]
        checks.append(("workflow-state contract", not state_errors, "contract", "; ".join(state_errors)))

        authority = source_root / "ba-workflow/references/source-authority.md"
        try:
            authority_text = authority.read_text(encoding="utf-8")
            labels = ("CONFIRMED", "CURRENT_SYSTEM", "INFERRED", "PROPOSED", "UNKNOWN")
            missing = [label for label in labels if label not in authority_text and label not in (source_root / "ba-workflow/references/evidence-model.md").read_text(encoding="utf-8")]
        except OSError as error:
            missing = [str(error)]
        checks.append(("source-authority contract", not missing, "contract", "missing: " + ", ".join(missing) if missing else ""))

        srs_contract_path = target_dir / "srs-function-document" / "SKILL.md"
        srs_contract_markers = (
            "## 5. Format đầu ra bắt buộc",
            "| Nội dung | Mô tả |",
            "| STT | Business Rule | Mô tả chi tiết |",
            "| STT | Tên | Kiểu dữ liệu<br>[Độ dài dữ liệu] | Bắt buộc<br>(Y/N) | Input/Output | Giá trị khởi tạo | Mô tả (Mapping với CSDL nếu có) |",
            "## `<SỐ_MỤC>.1` Thông tin chung về chức năng",
            "## `<SỐ_MỤC>.2` Luồng nghiệp vụ",
            "## `<SỐ_MỤC>.3` Thiết kế giao diện (nếu có)",
            "### Nội dung cần xác nhận",
            "# 3.2.1.4 Chức năng xóa rule 4G",
        )
        try:
            srs_contract_text = srs_contract_path.read_text(encoding="utf-8")
            missing_srs_contract = [marker for marker in srs_contract_markers if marker not in srs_contract_text]
            generic_replacement = "Include only sections needed for the feature" in srs_contract_text
        except OSError as error:
            missing_srs_contract = [str(error)]
            generic_replacement = False
        srs_contract_ok = not missing_srs_contract and not generic_replacement
        srs_contract_detail = ""
        if missing_srs_contract:
            srs_contract_detail = "missing canonical SRS markers: " + "; ".join(missing_srs_contract)
        elif generic_replacement:
            srs_contract_detail = "generic SRS structure replaced the canonical internal template"
        checks.append(("srs-function-document format contract", srs_contract_ok, "contract", srs_contract_detail))

        handoff_path = source_root / "ba-workflow/templates/engineering-handoff.yml"
        try:
            handoff_errors = validate_handoff_text(handoff_path.read_text(encoding="utf-8"), allow_placeholders=True)
        except OSError as error:
            handoff_errors = [str(error)]
        checks.append(("engineering-handoff contract", not handoff_errors, "contract", "; ".join(handoff_errors)))

    required_failed = any(not ok and kind == "required" for _, ok, kind, _ in checks)
    contract_failed = any(not ok and kind == "contract" for _, ok, kind, _ in checks)
    optional_missing = any(not ok and kind == "optional" for _, ok, kind, _ in checks)
    status = "FAIL" if required_failed or contract_failed else "DEGRADED" if optional_missing else "READY"
    return _with_project_policy(
        {"status": status, "kit": manifest["name"], "checks": checks},
        target_dir, kit_id, project_root,
    )


def resolve_target(agent, scope, explicit=None, project_dir=None):
    if explicit:
        return Path(explicit).expanduser().resolve()
    if agent == "generic":
        raise ValueError("generic agent requires --target <skills-directory>")
    if scope not in ("user", "project"):
        raise ValueError("--scope must be user or project")
    if scope == "project":
        base = Path(project_dir or Path.cwd())
        return (base / (".agents/skills" if agent == "codex" else ".claude/skills")).resolve()
    if agent == "codex":
        return (Path.home() / ".agents/skills").resolve()
    return (Path.home() / ".claude/skills").resolve()


def _print_doctor(report):
    print(f"{report.get('kit', 'Kit')} Doctor")
    package_checks = [check for check in report["checks"] if check[2] != "project_policy"]
    project_checks = [check for check in report["checks"] if check[2] == "project_policy"]
    for name, ok, kind, detail in package_checks:
        label = "PASS" if ok else "MISSING" if kind == "dependency" else "DEGRADED" if kind == "optional" else "FAIL"
        suffix = f" - {kind}" if kind == "optional" and not ok else ""
        if kind == "required":
            suffix = " - required"
        if detail:
            suffix += f": {detail}"
        print(f"[{label}] {name}{suffix}")
    if project_checks:
        print("Project policy (project-owned inputs)")
        for name, ok, _kind, detail in project_checks:
            suffix = f": {detail}" if detail else ""
            print(f"[{'PASS' if ok else 'FAIL'}] {name}{suffix}")
    print(f"STATUS: {report['status']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install, inspect, and remove Agent Skills Kits")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "doctor", "uninstall"):
        sub = commands.add_parser(command)
        sub.add_argument("kit", help="kit id from kits/<id>/kit.yaml")
        sub.add_argument("--agent", choices=("codex", "claude-code", "generic"), default="codex")
        sub.add_argument("--scope", choices=("user", "project"), default="project")
        sub.add_argument("--target", type=Path)
        if command == "doctor":
            sub.add_argument("--project-root", type=Path, help="project customization root (default: current directory)")
    state_parser = commands.add_parser("validate-state")
    state_parser.add_argument("path", type=Path)
    handoff_parser = commands.add_parser("validate-handoff")
    handoff_parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-state":
            data = json.loads(args.path.read_text(encoding="utf-8"))
            errors = validate_state_data(data)
            for error in errors:
                print(f"INVALID: {error}", file=sys.stderr)
            if errors:
                return 1
            print("VALID: workflow state")
            return 0
        if args.command == "validate-handoff":
            errors = validate_handoff_file(args.path)
            for error in errors:
                print(f"INVALID: {error}", file=sys.stderr)
            if errors:
                return 1
            print("VALID: engineering handoff and source hashes")
            return 0
        if args.command != "uninstall":
            manifest = load_manifest(ROOT, args.kit)
            minimum = tuple(manifest.get("prerequisites", {}).get("python", (3, 8)))
            if sys.version_info[:2] < minimum:
                required = ".".join(map(str, minimum))
                print(f"ERROR: Python {required}+ is required for {manifest['name']} runtime.", file=sys.stderr)
                return 2
            supported_agents = manifest.get("agents", ("codex", "claude-code", "generic"))
            if args.agent not in supported_agents and not (args.agent == "generic" and args.target):
                print(f"ERROR: {manifest['name']} supports these agents: {', '.join(supported_agents)}.", file=sys.stderr)
                return 2
            supported_scopes = manifest.get("scopes", ("user", "project"))
            if args.agent != "generic" and args.scope not in supported_scopes:
                print(f"ERROR: {manifest['name']} supports these scopes: {', '.join(supported_scopes)}.", file=sys.stderr)
                return 2
        target = resolve_target(args.agent, args.scope, args.target)
        if args.command == "install":
            project_root = Path.cwd() if args.scope == "project" and args.agent != "generic" else None
            result = install(ROOT, target, args.kit, project_root=project_root)
            if args.kit == "ba":
                print(f"Installed or verified {len(result['installed'])} BA skills at {target}")
            else:
                print(f"Installed or verified {len(result['installed'])} {manifest['name']} assets at {target}")
            if result["conflicts"]:
                print("Managed-file conflicts preserved; doctor will report drift: " + ", ".join(result["conflicts"]))
            if result["preserved"]:
                print("Preserved existing skills: " + ", ".join(result["preserved"]))
            if result["skipped"]:
                print("Optional skills unavailable: " + ", ".join(result["skipped"]))
            if args.kit == "test" and result.get("tea_project_config"):
                tea_config = result["tea_project_config"]
                action = "Created" if tea_config["status"] == "CREATED" else "Preserved existing"
                print(f"{action} TEA project config: {tea_config['path']}")
            return 0
        if args.command == "uninstall":
            result = uninstall(target, args.kit)
            label = "BA skills" if args.kit == "ba" else f"{args.kit} Kit assets"
            print(f"Removed {label}: " + (", ".join(result["removed"]) or "none"))
            if result["preserved"]:
                print("Preserved modified or shared skills: " + ", ".join(result["preserved"]))
            return 0
        doctor_project_root = args.project_root
        if doctor_project_root is None and args.agent != "generic" and args.scope == "project":
            doctor_project_root = Path.cwd()
        report = doctor(ROOT, target, args.kit, project_root=doctor_project_root)
        _print_doctor(report)
        return 1 if report["status"] == "FAIL" else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
