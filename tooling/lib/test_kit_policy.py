"""Project-owned, non-authoritative Test Kit guidance and immutable evidence.

The supported YAML/TOML subset is intentionally small and dependency-free on
Python 3.10. Unsupported syntax fails closed; upstream skills remain untouched.
"""

from __future__ import annotations

import ast
import argparse
import hashlib
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ba-workflow/scripts"))
from contracts import _yaml_fields  # noqa: E402


TEA_TEAM_PATH = "_bmad/custom/bmad-testarch-test-design.toml"
TEA_USER_PATH = "_bmad/custom/bmad-testarch-test-design.user.toml"
POLICY_ALGORITHM = "TEST_KIT_PROJECT_POLICY_V1"


class PolicyError(ValueError):
    def __init__(self, code: str, message: str, path: str | Path | None = None):
        super().__init__(f"{code}: {message}")
        self.code, self.path = code, str(path) if path is not None else None


@dataclass(frozen=True)
class PolicyRule:
    logical_path: str
    sha256: str
    content: bytes


@dataclass(frozen=True)
class PolicySnapshot:
    project_root: Path
    stage: str
    profile_id: str
    revision: str
    rules: tuple[PolicyRule, ...]
    payload_bytes: bytes
    sha256: str
    tea_customization: dict | None = None
    tea_content: bytes | None = None

    @property
    def ref(self) -> dict:
        return {"id": f"TEST_POLICY:{self.stage}:{self.profile_id}", "revision": self.revision, "sha256": self.sha256}


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json_bytes(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _exists(path: Path) -> bool:
    return os.path.lexists(path)


def _reparse(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _project_root(project_root: str | Path) -> Path:
    project = Path(project_root).resolve()
    if not project.is_dir():
        raise PolicyError("INVALID_PROJECT_POLICY", "project root is not a directory", project)
    return project


def _policy_root(project_root: Path) -> Path:
    root = project_root / ".test-kit"
    if _exists(root) and (_reparse(root) or not root.is_dir()):
        raise PolicyError("UNSAFE_POLICY_PATH", ".test-kit must be a real project-owned directory", root)
    return root


def _safe_path(root: Path, logical: str) -> Path:
    if (
        not isinstance(logical, str) or not logical or "\\" in logical or ":" in logical
        or PurePosixPath(logical).is_absolute() or PureWindowsPath(logical).is_absolute()
        or any(part in ("", ".", "..") for part in logical.split("/"))
    ):
        raise PolicyError("UNSAFE_POLICY_PATH", "use a relative path without traversal", str(logical))
    path = root.joinpath(*logical.split("/"))
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as error:
        raise PolicyError("UNSAFE_POLICY_PATH", str(error), path) from error
    if not resolved.is_relative_to(root):
        raise PolicyError("UNSAFE_POLICY_PATH", "resolved file escapes .test-kit", path)
    if not resolved.exists():
        raise PolicyError("MISSING_POLICY_FILE", "referenced file does not exist", path)
    if not resolved.is_file():
        raise PolicyError("INVALID_POLICY_FILE", "referenced path must be a regular file", path)
    return resolved


def _read_utf8(path: Path) -> bytes:
    try:
        content = path.read_bytes()
        content.decode("utf-8")
    except UnicodeError as error:
        raise PolicyError("INVALID_POLICY_UTF8", "file must contain UTF-8 text", path) from error
    except OSError as error:
        raise PolicyError("INVALID_POLICY_FILE", str(error), path) from error
    return content


def _without_comment(line: str) -> str:
    quote, escaped = None, False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
        elif quote == '"' and char == "\\":
            escaped = True
        elif char == quote:
            quote = None
        elif quote is None and char in "\"'":
            quote = char
        elif quote is None and char == "#":
            return line[:index].rstrip()
    if quote is not None:
        raise PolicyError("INVALID_PROJECT_POLICY", "unterminated quoted value")
    return line.rstrip()


def _scalar(value: str) -> str:
    if value.startswith('"'):
        try:
            decoded = json.loads(value)
        except ValueError as error:
            raise PolicyError("INVALID_PROJECT_POLICY", "invalid double-quoted string") from error
        if not isinstance(decoded, str):
            raise PolicyError("INVALID_PROJECT_POLICY", "expected a string")
        return decoded
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'") or "'" in value[1:-1].replace("''", ""):
            raise PolicyError("INVALID_PROJECT_POLICY", "invalid single-quoted string")
        return value[1:-1].replace("''", "'")
    if (
        not value or any(char in value for char in "[]{}&*!|>\"'")
        or value.lower() in ("null", "true", "false", "~", ".nan", ".inf", "-.inf", "+.inf")
        or re.fullmatch(r"[-+]?(?:\d[\d_]*(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", value)
    ):
        raise PolicyError("INVALID_PROJECT_POLICY", "unsupported YAML scalar")
    return value


def _inline_list(value: str) -> list[str]:
    if not value.endswith("]"):
        raise PolicyError("INVALID_PROJECT_POLICY", "unterminated inline rule list")
    body, items, start, quote, escaped = value[1:-1], [], 0, None, False
    for index, char in enumerate(body):
        if escaped:
            escaped = False
        elif quote == '"' and char == "\\":
            escaped = True
        elif char == quote:
            quote = None
        elif quote is None and char in "\"'":
            quote = char
        elif quote is None and char == ",":
            items.append(_scalar(body[start:index].strip()))
            start = index + 1
    if quote:
        raise PolicyError("INVALID_PROJECT_POLICY", "unterminated inline list string")
    if body[start:].strip():
        items.append(_scalar(body[start:].strip()))
    return items


def _parse_profile(text: str) -> dict:
    # Reuse the existing package's YAML mapping parser after checking indentation
    # and scalar syntax; its permissive handoff parser alone is insufficient here.
    clean, stack, raw_values, raw_lists, inline_lists = [], [], {}, {}, set()
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[:len(raw) - len(raw.lstrip())]:
            raise PolicyError("INVALID_PROJECT_POLICY", f"line {number}: tabs are not supported")
        line = _without_comment(raw)
        indent = len(line) - len(line.lstrip(" "))
        value = line[indent:]
        if value.startswith("- "):
            if not stack or indent != stack[-1][0] + 2:
                raise PolicyError("INVALID_PROJECT_POLICY", f"line {number}: invalid list indentation")
            raw_lists.setdefault(tuple(key for _, key in stack), []).append(_scalar(value[2:].strip()))
            clean.append(line)
            continue
        match = re.fullmatch(r"([A-Za-z0-9_-]+):(?: *(.*))?", value)
        if not match:
            raise PolicyError("INVALID_PROJECT_POLICY", f"line {number}: unsupported YAML mapping")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if indent != (stack[-1][0] + 2 if stack else 0):
            raise PolicyError("INVALID_PROJECT_POLICY", f"line {number}: invalid mapping indentation")
        key, raw_value = match.groups()
        key_path = tuple(key for _, key in stack) + (key,)
        if raw_value:
            raw_value = raw_value.strip()
            if len(key_path) == 2 and key_path[0] == "rules" and raw_value.startswith("["):
                raw_lists[key_path] = _inline_list(raw_value)
                inline_lists.add(key_path)
                raw_values[key_path] = "[]"
            else:
                raw_values[key_path] = raw_value if raw_value in ("[]", "{}") or key_path == ("schema_version",) and raw_value == "1" else _scalar(raw_value)
        else:
            stack.append((indent, key))
        clean.append(line)
    fields, keys, _, errors = _yaml_fields("\n".join(clean))
    if errors:
        raise PolicyError("INVALID_PROJECT_POLICY", "; ".join(errors))
    allowed = {("schema_version",), ("profile",), ("profile", "id"), ("profile", "revision"), ("rules",), ("templates",), ("templates", "excel"), ("templates", "excel", "path")}
    allowed.update(("rules", name) for name in ("common", "test_design", "testcases"))
    unknown = keys - allowed
    if unknown:
        raise PolicyError("INVALID_PROJECT_POLICY", "unknown field: " + ".".join(sorted(unknown)[0]))
    if raw_values.get(("schema_version",)) != "1" or not any(line == "schema_version: 1" for line in clean):
        raise PolicyError("INVALID_PROJECT_POLICY", "schema_version must be integer 1")
    for key in ("profile", "rules"):
        if (key,) not in keys or fields[(key,)] not in (None, "{}"):
            raise PolicyError("INVALID_PROJECT_POLICY", f"{key} must be a mapping")
    profile = {key: raw_values.get(("profile", key)) for key in ("id", "revision")}
    if any(not isinstance(value, str) or not value.strip() or value in ("[]", "{}") for value in profile.values()):
        raise PolicyError("INVALID_PROJECT_POLICY", "profile id and revision must be non-empty strings")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", profile["id"]):
        raise PolicyError("INVALID_PROJECT_POLICY", "profile id must be a stable identifier")
    rules = {}
    for category in ("common", "test_design", "testcases"):
        path = ("rules", category)
        scalar = fields.get(path)
        if path not in inline_lists and (scalar not in (None, "[]") or (scalar == "[]" and path in raw_lists)):
            raise PolicyError("INVALID_PROJECT_POLICY", f"rules.{category} must be a string list")
        if path in keys and scalar is None and path not in raw_lists:
            raise PolicyError("INVALID_PROJECT_POLICY", f"rules.{category} must be a list; use [] for an empty category")
        if any(key[:2] == path and len(key) > 2 for key in keys):
            raise PolicyError("INVALID_PROJECT_POLICY", f"rules.{category} must be a string list")
        rules[category] = raw_lists.get(path, [])
    if set(raw_lists) - {("rules", category) for category in rules}:
        raise PolicyError("INVALID_PROJECT_POLICY", "lists are supported only under rules categories")
    for key in (("templates",), ("templates", "excel")):
        if key in keys and fields[key] not in (None, "{}"):
            raise PolicyError("INVALID_PROJECT_POLICY", f"{'.'.join(key)} must be a mapping")
    template = raw_values.get(("templates", "excel", "path"))
    if ("templates", "excel") in keys and not template:
        raise PolicyError("INVALID_PROJECT_POLICY", "templates.excel requires path")
    return {"profile": profile, "rules": rules, "excel_path": template}


def _load_profile(project: Path) -> tuple[Path, dict | None]:
    root = _policy_root(project)
    profile = root / "project.yaml"
    if not _exists(profile):
        return root, None
    profile = _safe_path(root, "project.yaml")
    return root, _parse_profile(_read_utf8(profile).decode("utf-8"))


def resolve_project_excel_template(project_root: str | Path) -> Path | None:
    """Select only the declared presentation template; no TEA/rule side effects."""
    root, profile = _load_profile(_project_root(project_root))
    logical = profile["excel_path"] if profile else None
    if logical is None:
        return None
    if not isinstance(logical, str) or PurePosixPath(logical).suffix.lower() != ".xlsx":
        raise PolicyError("INVALID_PROJECT_TEMPLATE", "Excel project template must use .xlsx", str(logical))
    return _safe_path(root, logical)


def _team_path(project: Path) -> Path:
    path = project / TEA_TEAM_PATH
    current = project
    for component in PurePosixPath(TEA_TEAM_PATH).parts:
        current /= component
        if _exists(current) and _reparse(current):
            raise PolicyError("UNSAFE_POLICY_PATH", "TEA customization cannot use symlinks/reparse points", current)
    return path


def _check_personal(project: Path) -> None:
    path = project / TEA_USER_PATH
    if _exists(path):
        raise PolicyError("PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED", "personal TEA override is blocked; preserve the file and use reviewed project policy", path)


def _parse_tea(content: bytes) -> dict:
    """Portable TOML subset: workflow string arrays and on_complete only."""
    try:
        text = content.decode("utf-8")
        workflow, section, pending = {}, None, ""
        for raw in text.splitlines():
            line = _without_comment(raw).strip()
            if not line:
                continue
            if pending:
                line = pending + " " + line
            if line == "[workflow]":
                if section is not None:
                    raise ValueError("duplicate workflow table")
                section = "workflow"
                continue
            if section != "workflow" or line.startswith("["):
                raise ValueError("only the upstream workflow customization table is supported")
            key, separator, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if not separator or key not in {"persistent_facts", "activation_steps_prepend", "activation_steps_append", "on_complete"}:
                raise ValueError("unsupported workflow customization key")
            if value.startswith("[") and not value.endswith("]"):
                pending = line
                continue
            pending = ""
            if key in workflow:
                raise ValueError("duplicate workflow customization key")
            parsed = ast.literal_eval(value)
            if key == "on_complete":
                if not isinstance(parsed, str) or parsed:
                    raise ValueError("on_complete actions cannot be bound as testing guidance")
            elif not isinstance(parsed, list) or not all(isinstance(entry, str) for entry in parsed):
                raise ValueError("workflow arrays must contain strings")
            elif key.startswith("activation_steps") and parsed:
                raise ValueError("activation actions cannot be bound as testing guidance")
            workflow[key] = parsed
        if pending or section is None:
            raise ValueError("incomplete workflow TOML")
        return workflow
    except (UnicodeError, ValueError, SyntaxError, PolicyError) as error:
        raise PolicyError("TEA_CUSTOMIZATION_AMBIGUOUS", str(error)) from error


def _tea_bridge(project: Path, rules: tuple[PolicyRule, ...], *, create: bool) -> tuple[dict, bytes]:
    _check_personal(project)
    path = _team_path(project)
    expected = [f"file:{{project-root}}/.test-kit/{rule.logical_path}" for rule in rules]
    if not _exists(path):
        if not create:
            raise PolicyError("TEA_BRIDGE_MISSING", "bootstrap or author the project-owned TEA persistent_facts bridge", path)
        content = ("# Project-owned Test Kit bridge; testing guidance only.\n[workflow]\npersistent_facts = [\n" + "".join(f"  {json.dumps(fact, ensure_ascii=False)},\n" for fact in expected) + "]\n").encode("utf-8")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(content)
    if not path.is_file():
        raise PolicyError("TEA_CUSTOMIZATION_AMBIGUOUS", "team customization must be a regular file", path)
    content = path.read_bytes()
    workflow = _parse_tea(content)
    actual = workflow.get("persistent_facts", [])
    actual_files = [fact for fact in actual if fact.startswith("file:")]
    if actual_files != expected:
        raise PolicyError("TEA_CUSTOMIZATION_AMBIGUOUS", "persistent_facts must load exactly common then Design rules in declared order; external/glob facts are not bound", path)
    return {"logical_path": TEA_TEAM_PATH, "sha256": _sha(content)}, content


def prepare_tea_bridge(project_root: str | Path, snapshot: PolicySnapshot | None, *, create: bool = False) -> dict | None:
    project = _project_root(project_root)
    _check_personal(project)
    if snapshot is None:
        path = _team_path(project)
        if _exists(path):
            workflow = _parse_tea(path.read_bytes())
            if any(workflow.values()):
                raise PolicyError("UNBOUND_TEA_CUSTOMIZATION", "team customization requires a project policy snapshot", path)
        return None
    if snapshot.stage != "DESIGN" or snapshot.project_root != project:
        raise PolicyError("INVALID_PROJECT_POLICY", "TEA bridge requires this project's DESIGN snapshot")
    identity, _ = _tea_bridge(project, snapshot.rules, create=create)
    return identity


def resolve_project_policy(project_root: str | Path, stage: str, *, bootstrap_tea: bool = False) -> PolicySnapshot | None:
    if stage not in ("DESIGN", "CASES"):
        raise PolicyError("INVALID_POLICY_STAGE", "supported stages are DESIGN and CASES")
    project = _project_root(project_root)
    _check_personal(project)
    root, profile = _load_profile(project)
    if profile is None:
        if stage == "DESIGN":
            prepare_tea_bridge(project, None)
        return None
    # Validate the entire profile, even unused stages, before trusting guidance.
    resolved, categories = set(), {}
    for category, logical_paths in profile["rules"].items():
        entries = []
        for logical in logical_paths:
            path = _safe_path(root, logical)
            if path in resolved:
                raise PolicyError("DUPLICATE_POLICY_FILE", "rule is declared more than once after path resolution", logical)
            resolved.add(path)
            content = _read_utf8(path)
            entries.append(PolicyRule(logical, _sha(content), content))
        categories[category] = entries
    resolve_project_excel_template(project)
    rules = tuple(categories["common"] + categories["test_design" if stage == "DESIGN" else "testcases"])
    tea, tea_content = _tea_bridge(project, rules, create=bootstrap_tea) if stage == "DESIGN" else (None, None)
    payload = {
        "algorithm": POLICY_ALGORITHM,
        "schema_version": 1,
        "stage": stage,
        "profile": profile["profile"],
        "rules": [{"logical_path": rule.logical_path, "sha256": rule.sha256} for rule in rules],
    }
    if tea is not None:
        payload["tea_customization"] = tea
    content = _json_bytes(payload)
    return PolicySnapshot(project, stage, profile["profile"]["id"], profile["profile"]["revision"], rules, content, _sha(content), tea, tea_content)


def _safe_evidence_path(run_root: Path, relative: str) -> Path:
    target = run_root / relative
    current = run_root
    for component in PurePosixPath(relative).parts:
        current /= component
        if _exists(current) and _reparse(current):
            raise PolicyError("UNSAFE_POLICY_EVIDENCE_PATH", "evidence cannot use symlinks/reparse points", current)
    if not target.resolve().is_relative_to(run_root):
        raise PolicyError("UNSAFE_POLICY_EVIDENCE_PATH", "evidence escapes run root", target)
    return target


def _immutable_write(path: Path, content: bytes) -> None:
    if _exists(path):
        if not path.is_file() or path.read_bytes() != content:
            raise PolicyError("POLICY_EVIDENCE_CONFLICT", "refuse overwriting different evidence bytes", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        if path.read_bytes() != content:
            raise PolicyError("POLICY_EVIDENCE_CONFLICT", "concurrent evidence differs", path)


def persist_policy_snapshot(snapshot: PolicySnapshot, run_dir: str | Path) -> dict:
    run = Path(run_dir).resolve()
    if _sha(snapshot.payload_bytes) != snapshot.sha256:
        raise PolicyError("INVALID_PROJECT_POLICY", "snapshot digest does not match exact semantic bytes")
    rules = []
    writes = []
    for rule in snapshot.rules:
        if _sha(rule.content) != rule.sha256:
            raise PolicyError("INVALID_PROJECT_POLICY", "rule digest does not match exact bytes", rule.logical_path)
        relative = f"inputs/project-policy/rules/{rule.logical_path}"
        path = _safe_evidence_path(run, relative)
        rules.append({"logical_path": rule.logical_path, "evidence_path": str(path), "sha256": rule.sha256})
        writes.append((path, rule.content))
    manifest = {
        "status": "PROJECT_POLICY_RESOLVED",
        "stage": snapshot.stage,
        "profile": {"id": snapshot.profile_id, "revision": snapshot.revision},
        "policy_ref": snapshot.ref,
        "snapshot_sha256": snapshot.sha256,
        "snapshot_path": str(_safe_evidence_path(run, "inputs/project-policy/policy-snapshot.json")),
        "rules": rules,
        "tea_customization": None,
        "authority": "TESTING_POLICY / NON-AUTHORITATIVE GUIDANCE",
    }
    if snapshot.tea_customization is not None:
        if snapshot.tea_content is None or _sha(snapshot.tea_content) != snapshot.tea_customization["sha256"]:
            raise PolicyError("INVALID_PROJECT_POLICY", "team customization bytes differ from snapshot")
        path = _safe_evidence_path(run, "inputs/project-policy/tea-team-customization.toml")
        manifest["tea_customization"] = {**snapshot.tea_customization, "evidence_path": str(path)}
        writes.append((path, snapshot.tea_content))
    record = {"semantic_payload": json.loads(snapshot.payload_bytes), "semantic_payload_sha256": snapshot.sha256, "evidence": manifest}
    writes.append((Path(manifest["snapshot_path"]), _json_bytes(record)))
    # Check the whole immutable write set before creating any evidence file.
    for path, content in writes:
        if _exists(path) and (not path.is_file() or path.read_bytes() != content):
            raise PolicyError("POLICY_EVIDENCE_CONFLICT", "existing evidence differs; choose a new run", path)
    for path, content in writes:
        _immutable_write(path, content)
    return manifest


def non_authoritative_policy_prompt(snapshot: PolicySnapshot | None, evidence: dict | None = None) -> str:
    if snapshot is None:
        return "NO_PROJECT_POLICY: no project testing conventions supplied.\n"
    lines = [
        "## TESTING POLICY / NON-AUTHORITATIVE GUIDANCE",
        f"Stage {snapshot.stage}; profile {snapshot.profile_id} revision {snapshot.revision}; snapshot SHA-256 {snapshot.sha256}.",
        "Approved BA is business authority; approved Test Design is coverage authority; approved execution oracle is execution authority.",
        "Policy cannot answer BA UNKNOWN, override FR/BR, invent behavior/expected results, expand approved Test Design coverage, replace an execution oracle, bypass validation, or grant Human approval.",
        "Authoritative sources win any conflict: retain UNKNOWN/deferred semantics or report the conflict and fail closed.",
        "Read the following exact run-evidence rule files in declared order:",
    ]
    entries = evidence["rules"] if evidence else [{"logical_path": rule.logical_path, "evidence_path": str(snapshot.project_root / ".test-kit" / rule.logical_path), "sha256": rule.sha256} for rule in snapshot.rules]
    lines.extend(f"- {entry['logical_path']}: {entry['evidence_path']} (SHA-256 {entry['sha256']})" for entry in entries)
    return "\n".join(lines) + "\n"


def bootstrap_project_policy(project_root: str | Path) -> dict:
    project = _project_root(project_root)
    _check_personal(project)
    root = _policy_root(project)
    starter = {
        "project.yaml": 'schema_version: 1\nprofile:\n  id: project-testing\n  revision: "1"\nrules:\n  common:\n    - rules/common.md\n  test_design:\n    - rules/test-design.md\n  testcases:\n    - rules/testcases.md\ntemplates: {}\n',
        "rules/common.md": "# Editable project testing guidance\n\nKeep BA FR/BR and UNKNOWN authoritative. Use safe synthetic test data.\nPolicy never supplies business behavior, expected results, execution oracles or approval.\n",
        "rules/test-design.md": "# Editable Test Design guidance\n\nConsider boundary and negative analysis only for approved BA behavior.\nRetain unresolved BA decisions as UNKNOWN; do not invent a numeric limit.\n",
        "rules/testcases.md": "# Editable manual testcase guidance\n\nUse clear names and one validation condition per self-contained case.\nKeep decomposition within approved Design coverage and approved execution oracles.\n",
    }
    created, preserved = [], []
    for relative, text in starter.items():
        path = _safe_evidence_path(project, f".test-kit/{relative}")
        if _exists(path):
            preserved.append(relative)
            continue
        _immutable_write(path, text.encode("utf-8"))
        created.append(relative)
    snapshot = resolve_project_policy(project, "DESIGN", bootstrap_tea=True)
    return {"status": "PROJECT_POLICY_INITIALIZED", "created": created, "preserved": preserved, "design_policy_ref": snapshot.ref if snapshot else None}


def check_project_policy(project_root: str | Path) -> dict:
    """Read-only Doctor diagnostics independent of installed package integrity."""
    try:
        design = resolve_project_policy(project_root, "DESIGN")
        cases = resolve_project_policy(project_root, "CASES")
        template = resolve_project_excel_template(project_root)
        return {"status": "PASS" if design else "NO_PROJECT_POLICY", "findings": [], "snapshots": {"DESIGN": design.ref if design else None, "CASES": cases.ref if cases else None}, "excel_template": str(template) if template else None}
    except (PolicyError, OSError) as error:
        return {"status": "FAIL", "findings": [{"code": error.code if isinstance(error, PolicyError) else "INVALID_PROJECT_POLICY", "message": str(error), "path": error.path if isinstance(error, PolicyError) else str(project_root)}], "snapshots": {}}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap or inspect project-owned Test Kit testing guidance")
    parser.add_argument("command", choices=("bootstrap", "doctor"))
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        report = bootstrap_project_policy(args.project_root) if args.command == "bootstrap" else check_project_policy(args.project_root)
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 1 if report["status"] == "FAIL" else 0
    except (PolicyError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
