import hashlib
import re
from pathlib import Path


SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")
FORBIDDEN_HANDOFF_KEYS = {
    "frontend_owner", "backend_owner", "service_owner", "module_owner",
    "implementation_owner", "api_owner", "database_design", "db_design",
    "api_design", "event_schema", "locking_strategy", "transaction_strategy",
    "architecture", "architecture_choice", "architecture_decision",
    "service_architecture",
}


def validate_state_data(data):
    errors = []
    required = {
        "schema_version": int,
        "feature": dict,
        "operation": str,
        "stage": str,
        "artifacts": dict,
        "gates": dict,
        "pending": list,
        "source_of_truth": dict,
        "history": list,
    }
    if not isinstance(data, dict):
        return ["state must be a JSON object"]
    for name, expected in required.items():
        if name not in data:
            errors.append(f"missing required field: {name}")
        elif expected is int and type(data[name]) is not int:
            errors.append(f"{name} must be {expected.__name__}")
        elif expected is not int and not isinstance(data[name], expected):
            errors.append(f"{name} must be {expected.__name__}")
    if type(data.get("schema_version")) is int and data["schema_version"] != 1:
        errors.append("schema_version must be 1")
    return errors


def _yaml_fields(text):
    fields = {}
    keys = set()
    sequences = {}
    errors = []
    stack = []
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw[indent:]
        if line.startswith("- "):
            if not stack:
                errors.append(f"line {number}: list item has no parent key")
            else:
                key_path = tuple(key for _, key in stack)
                sequences.setdefault(key_path, []).append(line[2:].strip())
            continue
        match = re.fullmatch(r"([A-Za-z0-9_-]+):(?:[ \t]*(.*))?", line)
        if not match:
            errors.append(f"line {number}: unsupported YAML; expected a mapping or list item")
            continue
        key, value = match.groups()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        key_path = tuple(item[1] for item in stack) + (key,)
        if key_path in fields or key_path in keys:
            errors.append(f"line {number}: duplicate key: {'.'.join(key_path)}")
            continue
        keys.add(key_path)
        if value:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key_path] = value
        else:
            fields[key_path] = None
            stack.append((indent, key))
    return fields, keys, sequences, errors


def validate_handoff_text(text, allow_placeholders=False):
    fields, keys, sequences, errors = _yaml_fields(text)

    def get(path):
        return fields.get(tuple(path.split(".")))

    required = (
        "schema_version", "feature.id", "feature.title", "ba_baseline.status",
        "ba_baseline.revision", "authoritative_sources.business_rules.path",
        "authoritative_sources.business_rules.sha256", "authoritative_sources.srs.path",
        "authoritative_sources.srs.sha256", "authoritative_sources.decisions.path",
        "authoritative_sources.decisions.sha256", "open_items.blocking",
        "open_items.non_blocking", "policy.downstream_may_change_business_semantics",
        "policy.downstream_may_make_technical_design_decisions", "next_stage.capability",
    )
    allowed_keys = set()
    for path in required:
        parts = tuple(path.split("."))
        allowed_keys.update(parts[:index] for index in range(1, len(parts) + 1))
    for path in required:
        if tuple(path.split(".")) not in fields:
            errors.append(f"missing required field: {path}")
    if errors:
        return errors

    for path in (
        "feature.id", "feature.title", "ba_baseline.revision",
        "authoritative_sources.business_rules.path",
        "authoritative_sources.srs.path",
        "authoritative_sources.decisions.path",
    ):
        value = fields.get(tuple(path.split(".")))
        placeholder = allow_placeholders and value and value.startswith("<") and value.endswith(">")
        if not value or (value.startswith("<") and value.endswith(">") and not placeholder):
            errors.append(f"{path} must be filled in before handoff")
    if get("schema_version") != "1":
        errors.append("schema_version must be 1")
    status = get("ba_baseline.status")
    approved = status == "APPROVED_FOR_ENGINEERING"
    template_status = allow_placeholders and status and status.startswith("<APPROVED_FOR_ENGINEERING")
    if not (approved or template_status):
        errors.append("ba_baseline.status must be APPROVED_FOR_ENGINEERING after explicit BA approval")
    if not get("ba_baseline.revision"):
        errors.append("ba_baseline.revision must contain an immutable revision")
    blocking = get("open_items.blocking")
    blocking_items = sequences.get(("open_items", "blocking"), [])
    if not re.fullmatch(r"\[\s*\]", blocking or "") or blocking_items:
        errors.append("open_items.blocking must be empty before engineering handoff")
    non_blocking = get("open_items.non_blocking")
    inline_list = non_blocking is not None and non_blocking.startswith("[") and non_blocking.endswith("]")
    if not inline_list and not sequences.get(("open_items", "non_blocking")):
        errors.append("open_items.non_blocking must be a YAML list")
    for path in (
        "authoritative_sources.business_rules.sha256",
        "authoritative_sources.srs.sha256",
        "authoritative_sources.decisions.sha256",
    ):
        value = get(path)
        if not SHA256.fullmatch(value or "") and not (allow_placeholders and value and value.startswith("<") and value.endswith(">")):
            errors.append(f"{path} must be a 64-character SHA-256")
    if get("policy.downstream_may_change_business_semantics") != "false":
        errors.append("downstream may not change business semantics; set policy.downstream_may_change_business_semantics to false")
    if get("policy.downstream_may_make_technical_design_decisions") != "true":
        errors.append("policy.downstream_may_make_technical_design_decisions must be true")
    if get("next_stage.capability") != "engineering-impact-analysis":
        errors.append("next_stage.capability must be engineering-impact-analysis")
    for path in keys:
        if path[-1].lower() in FORBIDDEN_HANDOFF_KEYS:
            errors.append(f"handoff contains forbidden technical field: {'.'.join(path)}")
        elif path not in allowed_keys:
            errors.append(f"unsupported handoff field: {'.'.join(path)}")
    return errors


def validate_handoff_file(path):
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [f"cannot read handoff {path}: {error}"]
    errors = validate_handoff_text(text)
    if errors:
        return errors
    fields, _, _, _ = _yaml_fields(text)
    for source in ("business_rules", "srs", "decisions"):
        prefix = ("authoritative_sources", source)
        source_path = fields[prefix + ("path",)]
        expected = fields[prefix + ("sha256",)].lower()
        candidate = Path(source_path)
        if not candidate.is_absolute():
            candidate = path.parent / candidate
        if not candidate.is_file():
            errors.append(f"authoritative source does not exist: {candidate}")
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != expected:
            errors.append(f"SHA-256 mismatch for {source}: {candidate}")
    return errors
