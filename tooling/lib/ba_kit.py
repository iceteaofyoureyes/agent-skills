"""Standard-library installer and contract checks for BA Kit."""

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "ba-workflow/scripts"))
from contracts import validate_handoff_file, validate_handoff_text, validate_state_data  # noqa: E402


MANIFEST = Path("kits/ba/kit.yaml")
INSTALL_RECORD = ".ba-kit-install.json"
SKILL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _validate_install_record(record, path):
    if not isinstance(record, dict) or type(record.get("schema_version")) is not int or record["schema_version"] != 1 or record.get("kit") != "ba" or not isinstance(record.get("skills"), dict):
        raise ValueError(f"refusing to use unrelated or invalid install record {path}")
    for name, details in record["skills"].items():
        digest = details.get("sha256") if isinstance(details, dict) else None
        if not isinstance(name, str) or not SKILL_ID.fullmatch(name) or not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise ValueError(f"invalid managed skill entry in install record {path}")


def load_manifest(root):
    path = Path(root) / MANIFEST
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read BA Kit manifest {path}: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("id") != "ba":
        raise ValueError(f"unsupported or invalid BA Kit manifest: {path}")
    if manifest.get("name") != "BA Kit" or not isinstance(manifest.get("version"), str) or not manifest["version"]:
        raise ValueError("manifest requires BA Kit name and version")
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
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(source_root, target_dir):
    source_root = Path(source_root).resolve()
    target_dir = Path(target_dir).expanduser().resolve()
    manifest = load_manifest(source_root)
    required = {manifest["workflow"]["skill"], *manifest["core"], *manifest["skills"]["required"]}
    target_dir.mkdir(parents=True, exist_ok=True)
    record_path = target_dir / INSTALL_RECORD
    record = {"schema_version": 1, "kit": "ba", "version": manifest["version"], "skills": {}}
    if record_path.exists():
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid install record {record_path}: {error}") from error
        _validate_install_record(record, record_path)
        record["version"] = manifest["version"]

    installed, preserved, skipped = [], [], []
    plan = []
    # ponytail: no cross-process lock; installs are idempotent, add a per-target lock if concurrent installs matter.
    for skill in skill_composition(manifest):
        source = source_root / skill
        destination = target_dir / skill
        if not _valid_skill(source, skill):
            if skill in required:
                raise ValueError(f"required skill is missing or has invalid Agent Skills frontmatter: {source / 'SKILL.md'}")
            skipped.append(skill)
            continue
        if destination.exists() or destination.is_symlink():
            if destination.is_dir() and not destination.is_symlink() and (destination / "SKILL.md").is_file():
                old = record["skills"].get(skill, {})
                try:
                    current_hash = tree_hash(destination)
                    source_hash = tree_hash(source)
                except ValueError:
                    if skill in required:
                        raise
                    preserved.append(skill)
                    continue
                if old.get("sha256") == current_hash == source_hash:
                    installed.append(skill)
                else:
                    preserved.append(skill)
                continue
            if skill not in required:
                preserved.append(skill)
                continue
            raise ValueError(f"skill destination exists but is not a valid skill; preserved: {destination}")
        plan.append((skill, source, destination))

    created = []
    try:
        for skill, source, destination in plan:
            stage = Path(tempfile.mkdtemp(prefix=".ba-kit-stage-", dir=str(target_dir)))
            try:
                staged_skill = stage / skill
                shutil.copytree(source, staged_skill)
                digest = tree_hash(staged_skill)
                os.replace(staged_skill, destination)
            finally:
                shutil.rmtree(stage, ignore_errors=True)
            created.append((destination, digest))
            record["skills"][skill] = {"sha256": digest}
            installed.append(skill)
        if record["skills"]:
            _write_json(record_path, record)
    except BaseException:
        for path, digest in reversed(created):
            try:
                if path.is_dir() and not path.is_symlink() and tree_hash(path) == digest:
                    shutil.rmtree(path)
            except (OSError, ValueError):
                pass
        raise
    return {"installed": installed, "preserved": preserved, "skipped": skipped}


def _used_by_another_kit(target_dir, skill, own_record):
    for path in target_dir.glob(".*-kit-install.json"):
        if path == own_record:
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record.get("skills"), dict):
                return True
            if skill in record["skills"]:
                return True
        except (OSError, json.JSONDecodeError, AttributeError):
            return True
    return False


def uninstall(target_dir):
    target_dir = Path(target_dir).expanduser().resolve()
    record_path = target_dir / INSTALL_RECORD
    if not record_path.is_file():
        return {"removed": [], "preserved": []}
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid install record {record_path}: {error}") from error
    _validate_install_record(record, record_path)
    removed, preserved, remaining = [], [], {}
    for skill, details in record["skills"].items():
        path = target_dir / skill
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_dir():
            preserved.append(skill)
            remaining[skill] = details
            continue
        try:
            unchanged = tree_hash(path) == details["sha256"]
        except (OSError, ValueError):
            unchanged = False
        if _used_by_another_kit(target_dir, skill, record_path) or not unchanged:
            preserved.append(skill)
            remaining[skill] = details
            continue
        shutil.rmtree(path)
        removed.append(skill)
    if remaining:
        record["skills"] = remaining
        _write_json(record_path, record)
    else:
        record_path.unlink()
    return {"removed": removed, "preserved": preserved}


def _skill_names(manifest):
    workflow = manifest["workflow"]["skill"]
    required = [workflow, *manifest["core"], *manifest["skills"]["required"]]
    return required, manifest["skills"]["optional"]


def doctor(source_root, target_dir):
    source_root = Path(source_root).resolve()
    target_dir = Path(target_dir).expanduser().resolve()
    try:
        manifest = load_manifest(source_root)
    except ValueError as error:
        return {"status": "FAIL", "checks": [("kit manifest", False, "contract", str(error))]}
    required, optional = _skill_names(manifest)
    checks = []
    for skill in required:
        ok = _valid_skill(target_dir / skill, skill)
        detail = "" if ok else f"missing or invalid: {target_dir / skill / 'SKILL.md'}"
        checks.append((skill, ok, "required", detail))
    for skill in optional:
        ok = _valid_skill(target_dir / skill, skill)
        detail = "" if ok else f"unavailable: {target_dir / skill / 'SKILL.md'}"
        checks.append((skill, ok, "optional", detail))

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
    return {"status": status, "checks": checks}


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
    print("BA Kit Doctor")
    for name, ok, kind, detail in report["checks"]:
        label = "PASS" if ok else "DEGRADED" if kind == "optional" else "FAIL"
        suffix = f" - {kind}" if kind == "optional" and not ok else ""
        if kind == "required":
            suffix = " - required"
        if detail:
            suffix += f": {detail}"
        print(f"[{label}] {name}{suffix}")
    print(f"STATUS: {report['status']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install, inspect, and remove BA Kit")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("install", "doctor", "uninstall"):
        sub = commands.add_parser(command)
        sub.add_argument("kit", choices=("ba",))
        sub.add_argument("--agent", choices=("codex", "claude-code", "generic"), default="codex")
        sub.add_argument("--scope", choices=("user", "project"), default="project")
        sub.add_argument("--target", type=Path)
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
        target = resolve_target(args.agent, args.scope, args.target)
        if args.command == "install":
            result = install(ROOT, target)
            print(f"Installed or verified {len(result['installed'])} BA skills at {target}")
            if result["preserved"]:
                print("Preserved existing skills: " + ", ".join(result["preserved"]))
            if result["skipped"]:
                print("Optional skills unavailable: " + ", ".join(result["skipped"]))
            return 0
        if args.command == "uninstall":
            result = uninstall(target)
            print("Removed BA skills: " + (", ".join(result["removed"]) or "none"))
            if result["preserved"]:
                print("Preserved modified or shared skills: " + ", ".join(result["preserved"]))
            return 0
        report = doctor(ROOT, target)
        _print_doctor(report)
        return 1 if report["status"] == "FAIL" else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
