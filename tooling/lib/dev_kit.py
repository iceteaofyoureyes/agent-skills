"""Standard-library Dev Kit contracts plus read-only V1 LEGACY_COMPAT support."""

from __future__ import annotations

import argparse
import hashlib
import json
import ntpath
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


KIT_ROOT = Path(__file__).resolve().parents[2]
_WINDOWS = os.name == "nt"
RUNS_DIR = Path(".devkit/runs")
CURRENT_RUN = Path(".devkit/current.json")
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
REVIEW_LIMITS = {"full_reviews": 1, "blocking_fix_waves": 1, "scoped_rereviews": 1}
RISK_LEVEL_ORDER = {"TRIVIAL": 0, "NORMAL": 1, "HIGH_RISK": 2}
START_KINDS = {"docs", "rename", "mechanical", "config", "feature", "bug", "behavior"}
CHECK_CATEGORIES = {"build", "tests", "static_checks"}
RISK_SIGNALS = {
    "auth", "security", "sensitive_data", "pii", "database_migration",
    "public_api", "event_contract", "cross_repo", "concurrency",
    "major_architecture", "deployment_topology",
}
SIGNAL_ALIASES = {
    "authz": "auth", "authorization": "auth", "authentication": "auth",
    "security_boundary": "security", "sensitive_data": "sensitive_data",
    "personal_data": "pii", "migration": "database_migration", "schema": "database_migration",
    "api": "public_api", "public-api": "public_api", "events": "event_contract",
    "cross-service": "cross_repo", "cross-repository": "cross_repo",
    "locking": "concurrency", "transaction": "concurrency", "architecture": "major_architecture",
    "deployment": "deployment_topology", "uncertain-blast-radius": "uncertain_blast_radius",
    "performance": "performance", "observability": "observability",
    "external-api-uncertainty": "external_api_uncertainty",
}
SIGNAL_PATTERNS = {
    "auth": r"\b(auth(?:entication|orization)?|login|permission|privilege)\b",
    "security": r"\b(security boundary|security-sensitive|vulnerability|untrusted input)\b",
    "sensitive_data": r"\b(sensitive data|regulated data)\b",
    "pii": r"\b(pii|personal data|personally identifiable)\b",
    "database_migration": r"\b(database migration|db migration|schema migration|schema change)\b",
    "public_api": r"\b(public api|public endpoint|api compatibility|api contract)\b",
    "event_contract": r"\b(event contract|event schema|event compatibility)\b",
    "cross_repo": r"\b(cross[- ]service|cross[- ]repo|multiple repositories)\b",
    "concurrency": r"\b(concurrency|locking|transaction semantics|race condition)\b",
    "major_architecture": r"\b(major architecture|architecture change|system redesign)\b",
    "deployment_topology": r"\b(deployment topology|deployment architecture|cluster topology)\b",
    "performance": r"\b(performance regression|performance requirement|latency target)\b",
    "observability": r"\b(production telemetry|observability|distributed tracing)\b",
    "external_api_uncertainty": r"\b(uncertain external api|unknown framework behavior|external api uncertainty)\b",
    "uncertain_blast_radius": r"\b(uncertain blast radius|unknown callers|unknown dependencies)\b",
}
RELEVANT_CONTEXT = re.compile(
    r"(bmad|gsd|superpowers|ponytail|spec[-_ ]?driven|planning|task[-_ ]?breakdown|"
    r"test[-_ ]?driven|\btdd\b|incremental[-_ ]?implementation|code[-_ ]?review|"
    r"engineering[-_ ]?workflow|software[-_ ]?engineering)", re.IGNORECASE,
)
DEV_SKILLS = {
    "dev-kit",
    "requirements-gap-auditor", "verification-before-completion",
    "planning-and-task-breakdown", "incremental-implementation",
    "test-driven-development", "code-review-and-quality",
}
EXPECTED_CORE_SKILLS = {
    "planning-and-task-breakdown", "incremental-implementation",
    "test-driven-development", "code-review-and-quality",
}
EXPECTED_CONDITIONAL_SKILLS = {
    "debugging-and-error-recovery", "security-and-hardening",
    "api-and-interface-design", "source-driven-development",
    "performance-optimization", "observability-and-instrumentation",
}
EXPECTED_SHARED_SKILLS = {"requirements-gap-auditor", "verification-before-completion"}

sys.dont_write_bytecode = True
sys.path.insert(0, str(KIT_ROOT / "ba-workflow/scripts"))
from contracts import _yaml_fields, validate_handoff_file  # noqa: E402
from approved_baseline import read_approved_baseline, verify_baseline_snapshot
from delivery_manifest import load_delivery_manifest


def _is_string(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value, field, errors):
    if not isinstance(value, list) or any(not _is_string(item) for item in value):
        errors.append(f"{field} must be a list of non-empty strings")


def _only_keys(value, allowed, field, errors):
    if isinstance(value, dict):
        for key in value.keys() - set(allowed):
            errors.append(f"{field} contains unsupported field: {key}")


def _baseline_errors(value, errors):
    if not isinstance(value, dict):
        errors.append("baseline_ref must be an object")
        return
    _only_keys(value, {"path", "revision", "sha256"}, "baseline_ref", errors)
    for name in ("path", "revision"):
        if not _is_string(value.get(name)):
            errors.append(f"baseline_ref.{name} must be a non-empty string")
    if not isinstance(value.get("sha256"), str) or not SHA256_PATTERN.fullmatch(value["sha256"]):
        errors.append("baseline_ref.sha256 must be a lowercase SHA-256")


def validate_impact_manifest(data):
    errors = []
    required = {
        "schema_version", "change_id", "baseline_ref", "affected_repositories",
        "affected_components", "affected_interfaces", "affected_data",
        "dependencies", "constraints", "risk", "unknowns",
    }
    if not isinstance(data, dict):
        return ["impact manifest must be a JSON object"]
    _only_keys(data, required, "impact manifest", errors)
    for field in sorted(required - data.keys()):
        errors.append(f"missing required field: {field}")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("schema_version must be integer 1")
    if not _is_string(data.get("change_id")):
        errors.append("change_id must be a non-empty string")
    _baseline_errors(data.get("baseline_ref"), errors)
    for field in (
        "affected_repositories", "affected_components", "affected_interfaces",
        "affected_data", "dependencies", "constraints",
    ):
        _strings(data.get(field), field, errors)
    risk = data.get("risk")
    if not isinstance(risk, dict):
        errors.append("risk must be an object")
    else:
        _only_keys(risk, {"level", "reasons"}, "risk", errors)
        if risk.get("level") not in ("TRIVIAL", "NORMAL", "HIGH_RISK"):
            errors.append("risk.level must be TRIVIAL, NORMAL, or HIGH_RISK")
        _strings(risk.get("reasons"), "risk.reasons", errors)
    unknowns = data.get("unknowns")
    if not isinstance(unknowns, list):
        errors.append("unknowns must be a list")
    else:
        for index, item in enumerate(unknowns):
            prefix = f"unknowns[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            _only_keys(item, {"id", "kind", "description", "blocking"}, prefix, errors)
            if not _is_string(item.get("id")) or not _is_string(item.get("description")):
                errors.append(f"{prefix} requires non-empty id and description")
            if item.get("kind") not in ("BUSINESS", "TECHNICAL"):
                errors.append(f"{prefix}.kind must be BUSINESS or TECHNICAL")
            if type(item.get("blocking")) is not bool:
                errors.append(f"{prefix}.blocking must be a boolean")
    return errors


def _check_record(value, field, errors, require_pass=False):
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return
    allowed = {"status", "command", "exit_code"} | ({"name"} if field != "verification.build" else set())
    _only_keys(value, allowed, field, errors)
    if value.get("status") not in ("PASS", "FAIL", "NOT_RUN"):
        errors.append(f"{field}.status must be PASS, FAIL, or NOT_RUN")
    if not isinstance(value.get("command"), list) or not value["command"] or any(not _is_string(x) for x in value["command"]):
        errors.append(f"{field}.command must be a non-empty argv list")
    if type(value.get("exit_code")) is not int:
        errors.append(f"{field}.exit_code must be an integer")
    if require_pass and (value.get("status") != "PASS" or value.get("exit_code") != 0):
        errors.append(f"{field} verification must be PASS with exit_code 0")


def validate_dev_handoff(data):
    errors = []
    required = {
        "schema_version", "change_id", "baseline_ref", "implementation",
        "requirements_coverage", "verification", "review", "business_ambiguity",
        "human_gate", "known_risks", "state",
    }
    if not isinstance(data, dict):
        return ["Dev Handoff must be a JSON object"]
    _only_keys(data, required, "Dev Handoff", errors)
    for field in sorted(required - data.keys()):
        errors.append(f"missing required field: {field}")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("schema_version must be integer 1")
    if not _is_string(data.get("change_id")):
        errors.append("change_id must be a non-empty string")
    _baseline_errors(data.get("baseline_ref"), errors)
    implementation = data.get("implementation")
    if not isinstance(implementation, dict):
        errors.append("implementation must be an object")
    else:
        _only_keys(implementation, {"commits", "changed_components"}, "implementation", errors)
        _strings(implementation.get("commits"), "implementation.commits", errors)
        _strings(implementation.get("changed_components"), "implementation.changed_components", errors)
    coverage = data.get("requirements_coverage")
    if not isinstance(coverage, list):
        errors.append("requirements_coverage must be a list")
    else:
        for index, item in enumerate(coverage):
            prefix = f"requirements_coverage[{index}]"
            if not isinstance(item, dict) or not _is_string(item.get("requirement_id")):
                errors.append(f"{prefix} requires requirement_id")
                continue
            _only_keys(item, {"requirement_id", "status", "evidence"}, prefix, errors)
            if item.get("status") not in ("COVERED", "NOT_COVERED", "DEFERRED"):
                errors.append(f"{prefix}.status must be COVERED, NOT_COVERED, or DEFERRED")
            _strings(item.get("evidence"), f"{prefix}.evidence", errors)
            if item.get("status") == "COVERED" and not item.get("evidence"):
                errors.append(f"{prefix}.evidence must be non-empty when status is COVERED")
    verification = data.get("verification")
    if not isinstance(verification, dict):
        errors.append("verification must be an object")
    else:
        _only_keys(verification, {"build", "tests", "static_checks"}, "verification", errors)
        for field in ("build", "tests", "static_checks"):
            checks = verification.get(field)
            if not isinstance(checks, list):
                errors.append(f"verification.{field} must be a list")
                continue
            if data.get("state") == "READY_FOR_TEST" and field in ("build", "tests") and not checks:
                errors.append(f"verification.{field} must not be empty for READY_FOR_TEST")
            for index, check in enumerate(checks):
                prefix = f"verification.{field}[{index}]"
                if not isinstance(check, dict) or not _is_string(check.get("name")):
                    errors.append(f"{prefix} requires a name")
                    continue
                _check_record(check, prefix, errors, data.get("state") == "READY_FOR_TEST")
    review = data.get("review")
    blocking_findings = None
    if not isinstance(review, dict):
        errors.append("review must be an object")
    else:
        _only_keys(review, {*REVIEW_LIMITS, "blocking_findings", "followups"}, "review", errors)
        for key, maximum in REVIEW_LIMITS.items():
            value = review.get(key)
            if type(value) is not int or value < 0 or value > maximum:
                errors.append(f"review.{key} exceeds or violates the review budget (max {maximum})")
        blocking_findings = review.get("blocking_findings")
        if not isinstance(blocking_findings, list):
            errors.append("review.blocking_findings must be a list")
        elif any(not isinstance(item, dict) or item.get("class") != "BLOCKING" or not _is_string(item.get("id")) or not _is_string(item.get("description")) for item in blocking_findings):
            errors.append("review.blocking_findings may contain only BLOCKING findings")
        followups = review.get("followups")
        if not isinstance(followups, list) or any(not isinstance(item, dict) or item.get("class") != "FOLLOW_UP" or not _is_string(item.get("id")) or not _is_string(item.get("description")) for item in followups):
            errors.append("review.followups may contain only FOLLOW_UP findings")
    ambiguity = data.get("business_ambiguity")
    if not isinstance(ambiguity, dict) or ambiguity.get("status") not in ("CLEAR", "NEEDS_BA_CLARIFICATION") or not isinstance(ambiguity.get("items"), list):
        errors.append("business_ambiguity requires CLEAR/NEEDS_BA_CLARIFICATION status and an items list")
    else:
        _only_keys(ambiguity, {"status", "items"}, "business_ambiguity", errors)
        if ambiguity["status"] == "CLEAR" and ambiguity["items"]:
            errors.append("business_ambiguity.items must be empty when status is CLEAR")
        elif any(not _is_string(item) for item in ambiguity["items"]):
            errors.append("business_ambiguity.items must contain non-empty strings")
    gate = data.get("human_gate")
    if not isinstance(gate, dict) or type(gate.get("required")) is not bool or type(gate.get("resolved")) is not bool:
        errors.append("human_gate requires boolean required and resolved fields")
    else:
        _only_keys(gate, {"required", "resolved", "choice", "workflow_run_id", "workflow_state_path", "planning_artifacts_sha256"}, "human_gate", errors)
        if "choice" in gate and gate["choice"] not in (None, "approve", "reject"):
            errors.append("human_gate.choice must be approve, reject, or null")
        if "workflow_run_id" in gate and gate["workflow_run_id"] is not None and not _is_string(gate["workflow_run_id"]):
            errors.append("human_gate.workflow_run_id must be a non-empty string or null")
        if "workflow_state_path" in gate and gate["workflow_state_path"] is not None and not _is_string(gate["workflow_state_path"]):
            errors.append("human_gate.workflow_state_path must be a non-empty string or null")
        hashes = gate.get("planning_artifacts_sha256")
        if hashes is not None and (not isinstance(hashes, dict) or set(hashes) != {"dev-plan.md", "dev-tasks.md"} or any(not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value) for value in hashes.values())):
            errors.append("human_gate.planning_artifacts_sha256 must contain SHA-256 values for dev-plan.md and dev-tasks.md")
        if gate.get("required") and gate.get("resolved") and (
            gate.get("choice") != "approve" or not _is_string(gate.get("workflow_run_id"))
            or not _is_string(gate.get("workflow_state_path")) or not isinstance(hashes, dict)
        ):
            errors.append("resolved Human/Tech Lead gate requires the Spec Kit approve choice and workflow evidence")
    _strings(data.get("known_risks"), "known_risks", errors)
    allowed_states = {"IN_PROGRESS", "NEEDS_BA_CLARIFICATION", "NEEDS_REPLAN", "HUMAN_TECH_LEAD_REVIEW", "READY_FOR_TEST"}
    if data.get("state") not in allowed_states:
        errors.append("state is not a supported Dev Kit handoff state")
    if data.get("state") == "READY_FOR_TEST":
        if isinstance(review, dict) and review.get("full_reviews") != 1:
            errors.append("READY_FOR_TEST requires exactly one consolidated full review")
        if isinstance(ambiguity, dict) and (ambiguity.get("status") != "CLEAR" or ambiguity.get("items")):
            errors.append("READY_FOR_TEST is blocked by unresolved business ambiguity")
        if isinstance(gate, dict) and gate.get("required") and not gate.get("resolved"):
            errors.append("READY_FOR_TEST is blocked by unresolved Human/Tech Lead gate")
        if isinstance(gate, dict) and gate.get("required") and gate.get("choice") != "approve":
            errors.append("READY_FOR_TEST requires an approved Spec Kit Human/Tech Lead gate choice")
        if isinstance(blocking_findings, list) and blocking_findings:
            errors.append("READY_FOR_TEST is blocked by a blocking review finding")
        if isinstance(coverage, list) and any(item.get("status") != "COVERED" for item in coverage if isinstance(item, dict)):
            errors.append("READY_FOR_TEST is blocked by incomplete requirements coverage")
        if isinstance(coverage, list) and not coverage:
            errors.append("READY_FOR_TEST requires requirements coverage evidence")
        if isinstance(implementation, dict) and not implementation.get("changed_components"):
            errors.append("READY_FOR_TEST requires changed component ownership evidence")
    return errors


def route_change(kind, summary, signals=(), business_ambiguities=(), behavior_change=None):
    if kind not in START_KINDS:
        raise ValueError("kind must be docs, rename, mechanical, config, feature, bug, or behavior")
    text = f"{summary} {' '.join(signals)}".lower()
    found = set()
    for signal in signals:
        normalized = SIGNAL_ALIASES.get(str(signal).lower(), str(signal).lower().replace("-", "_"))
        if normalized in SIGNAL_PATTERNS:
            found.add(normalized)
        elif normalized not in RISK_SIGNALS and normalized != "uncertain_blast_radius":
            raise ValueError(f"unknown risk signal: {signal}")
    for signal, pattern in SIGNAL_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found.add(signal)
    high_signals = found & RISK_SIGNALS
    trivial_kind = kind in {"docs", "rename", "mechanical", "config"} and behavior_change is not True and not high_signals
    if business_ambiguities:
        risk = "HIGH_RISK" if high_signals else ("TRIVIAL" if trivial_kind else "NORMAL")
        return {
            "status": "NEEDS_BA_CLARIFICATION", "risk_level": risk,
            "reasons": sorted(high_signals), "business_ambiguities": list(business_ambiguities),
            "planning_allowed": False, "formal_plan": False, "full_review": False,
            "human_gate_required": False, "capabilities": ["requirements-gap-auditor"],
            "stages": ["SPEC_READINESS", "RETURN_TO_BA"], "workflow": None,
        }
    if trivial_kind:
        return {
            "status": "READY_FOR_EXECUTION", "risk_level": "TRIVIAL", "reasons": [],
            "business_ambiguities": [], "planning_allowed": False, "formal_plan": False,
            "full_review": False, "human_gate_required": False, "capabilities": [],
            "stages": ["UNDERSTAND", "EDIT", "DETERMINISTIC_CHECK", "COMPLETE"],
            "workflow": "trivial",
        }
    risk = "HIGH_RISK" if high_signals else "NORMAL"
    capabilities = [
        "requirements-gap-auditor", "planning-and-task-breakdown",
        "incremental-implementation", "code-review-and-quality",
        "verification-before-completion",
    ]
    if kind in {"feature", "bug", "behavior"} or behavior_change:
        capabilities.append("test-driven-development")
    if found & {"auth", "security", "sensitive_data", "pii"}:
        capabilities.append("security-and-hardening")
    if found & {"public_api", "event_contract"}:
        capabilities.append("api-and-interface-design")
    if "external_api_uncertainty" in found:
        capabilities.append("source-driven-development")
    if "performance" in found:
        capabilities.append("performance-optimization")
    if "observability" in found:
        capabilities.append("observability-and-instrumentation")
    if "uncertain_blast_radius" in found:
        capabilities.append("codebase-memory-mcp")
    return {
        "status": "READY_FOR_PLANNING", "risk_level": risk,
        "reasons": sorted(high_signals), "business_ambiguities": [],
        "planning_allowed": True, "formal_plan": True, "full_review": True,
        "human_gate_required": risk == "HIGH_RISK", "capabilities": capabilities,
        "stages": ["SPEC_READINESS", "PLANNING_PREFLIGHT", "TECHNICAL_PLAN", "IMPLEMENTATION", "FOCUSED_CHECKS", "ONE_CONSOLIDATED_REVIEW", "ONE_BLOCKING_FIX_WAVE", "OPTIONAL_ONE_SCOPED_REREVIEW", "FRESH_VERIFICATION", "DEV_HANDOFF"],
        "workflow": "high-risk" if risk == "HIGH_RISK" else "normal",
    }


def claim_review_action(budget, action, needed=True):
    if action not in REVIEW_LIMITS:
        raise ValueError(f"unknown review action: {action}")
    result = {key: budget.get(key, 0) for key in REVIEW_LIMITS}
    for key, maximum in REVIEW_LIMITS.items():
        if type(result[key]) is not int or result[key] < 0 or result[key] > maximum:
            raise ValueError(f"invalid review budget value for {key}")
    if not needed:
        return result
    if result[action] >= REVIEW_LIMITS[action]:
        raise ValueError(f"review budget exhausted: {action} max is {REVIEW_LIMITS[action]}")
    result[action] += 1
    return result


def hash_baseline(path):
    path = Path(path).expanduser().resolve(strict=True)
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write_artifact(path, value, protected_baselines=()):
    path = Path(path).resolve()
    protected = {Path(item["path"]).resolve() for item in protected_baselines}
    if path in protected:
        raise ValueError(f"Dev Kit artifact cannot overwrite Approved BA Baseline: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".dev-kit-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def inspect_context_purity(project_root, user_home, mode="daily", codex_home=None):
    if mode not in ("daily", "benchmark"):
        raise ValueError("mode must be daily or benchmark")
    project_root, user_home = Path(project_root), Path(user_home)
    skill_roots = [
        project_root / ".agents/skills", project_root / ".codex/skills",
        user_home / ".agents/skills", user_home / ".codex/skills",
    ]
    plugin_roots = [
        project_root / ".codex/plugins", user_home / ".codex/plugins",
    ]
    if codex_home is not None:
        codex_home = Path(codex_home).resolve()
        skill_roots = [project_root / ".agents/skills", project_root / ".codex/skills", codex_home / "skills"]
        plugin_roots = [project_root / ".codex/plugins", codex_home / "plugins"]
    records, contamination, seen = [], [], {}
    for root in skill_roots:
        if not root.is_dir():
            continue
        for skill in root.iterdir():
            path = skill / "SKILL.md"
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            match = re.search(r"(?m)^name:\s*['\"]?([^'\"\r\n]+)", content)
            name = match.group(1).strip() if match else skill.name
            relevant = bool(RELEVANT_CONTEXT.search(name)) or name in DEV_SKILLS
            record = {"kind": "skill", "name": name, "path": str(path), "relevant": relevant}
            records.append(record)
            if name in seen:
                contamination.append({**record, "reason": f"duplicate skill name also found at {seen[name]}"})
            elif relevant and name not in {"requirements-gap-auditor", "verification-before-completion", "dev-kit"}:
                contamination.append({**record, "reason": "global/project methodology overlaps Dev Kit"})
            elif not relevant:
                contamination.append({**record, "reason": "unrelated skill is present in project/user context"})
            seen[name] = str(path)
    for root in plugin_roots:
        if not root.is_dir():
            continue
        for manifest in root.rglob("plugin.json"):
            plugin = manifest.parent
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            name = str(data.get("name", plugin.name))
            dev_plugin = name == "agent-skills-dev-kit"
            relevant = bool(RELEVANT_CONTEXT.search(name))
            record = {"kind": "plugin", "name": name, "path": str(manifest), "relevant": relevant}
            records.append(record)
            if data.get("hooks") or data.get("extensions", {}).get("com.openai", {}).get("hooks"):
                contamination.append({**record, "relevant": True, "reason": "plugin hooks affect agent context"})
            if not dev_plugin:
                contamination.append({**record, "reason": "methodology plugin overlaps Dev Kit" if relevant else "unrelated plugin is present in project/user context"})
            plugin_skills = plugin / "skills"
            if plugin_skills.is_dir():
                for skill_dir in plugin_skills.iterdir():
                    skill_file = skill_dir / "SKILL.md"
                    if not skill_file.is_file():
                        continue
                    try:
                        skill_text = skill_file.read_text(encoding="utf-8")
                    except OSError:
                        continue
                    match = re.search(r"(?m)^name:\s*['\"]?([^'\"\r\n]+)", skill_text)
                    skill_name = match.group(1).strip() if match else skill_dir.name
                    skill_relevant = bool(RELEVANT_CONTEXT.search(skill_name)) or skill_name in DEV_SKILLS
                    skill_record = {"kind": "plugin_skill", "name": skill_name, "path": str(skill_file), "relevant": skill_relevant}
                    records.append(skill_record)
                    if skill_name in seen:
                        contamination.append({**skill_record, "reason": f"duplicate skill name also found at {seen[skill_name]}"})
                    elif not dev_plugin and skill_relevant and skill_name not in {"requirements-gap-auditor", "verification-before-completion"}:
                        contamination.append({**skill_record, "reason": "plugin methodology overlaps Dev Kit"})
                    elif not dev_plugin and not skill_relevant:
                        contamination.append({**skill_record, "reason": "unrelated plugin skill is present in project/user context"})
                    seen[skill_name] = str(skill_file)
    config_paths = [
        project_root / ".codex/config.toml", user_home / ".codex/config.toml",
    ]
    if codex_home is not None:
        config_paths = [project_root / ".codex/config.toml", codex_home / "config.toml"]
    mcp_names = []
    for config in config_paths:
        if not config.is_file():
            continue
        try:
            text = config.read_text(encoding="utf-8")
        except OSError:
            continue
        if re.search(r"\[mcp_servers\.|\"mcpServers\"\s*:", text):
            names = re.findall(r"(?im)^\s*\[mcp_servers\.([^\]]+)\]|\"([^\"]+)\"\s*:\s*\{", text)
            seen_in_config = set()
            for pair in names:
                name = (pair[0] or pair[1]).split(".")[0].strip("\"'")
                if name in seen_in_config:
                    continue
                seen_in_config.add(name)
                if name and ("mcp" not in name.lower() or name.lower() != "mcpservers"):
                    mcp_names.append((name, config))
        if re.search(r"(?im)^\s*hooks\s*=|\"hooks\"\s*:", text):
            relevant = bool(RELEVANT_CONTEXT.search(text))
            records.append({"kind": "hooks", "name": "configured hooks", "path": str(config), "relevant": relevant})
            contamination.append({"kind": "hooks", "name": "configured hooks", "path": str(config), "relevant": relevant, "reason": "always-on hooks affect agent context"})
    code_intelligence = [name for name, _ in mcp_names if re.search(r"(codebase|memory|graph|code.?intel)", name, re.IGNORECASE)]
    for name, config in mcp_names:
        relevant = bool(re.search(r"(codebase|memory|graph|code.?intel)", name, re.IGNORECASE))
        records.append({"kind": "mcp", "name": name, "path": str(config), "relevant": relevant})
        if relevant:
            if len(code_intelligence) > 1:
                contamination.append({"kind": "mcp", "name": name, "path": str(config), "relevant": True, "reason": "duplicate code-intelligence MCP"})
        else:
            contamination.append({"kind": "mcp", "name": name, "path": str(config), "relevant": False, "reason": "unrelated MCP server is present in project/user context"})
    relevant_items = [item for item in contamination if item["relevant"]]
    purity = "DEGRADED" if contamination else "CLEAN"
    status = "FAIL" if mode == "benchmark" and relevant_items else "DEGRADED" if contamination else "PASS"
    return {"status": status, "context_purity": purity, "mode": mode, "inventory": records, "contamination": contamination, "warnings": [item["reason"] for item in contamination]}


def _git_blob_sha1(path, root):
    path = Path(path).resolve()
    relative = path.relative_to(Path(root).resolve()).as_posix()
    result = subprocess.run(
        ["git", "-C", str(root), "hash-object", f"--path={relative}", relative],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise OSError(result.stderr.strip() or "git hash-object failed")
    return result.stdout.strip()


def validate_provenance(root):
    root = Path(root)
    errors = []
    try:
        kit = json.loads((root / "kits/dev/kit.yaml").read_text(encoding="utf-8"))
        lock = json.loads((root / "kits/dev/provenance.lock.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot load Dev Kit provenance inputs: {error}"]
    components = lock.get("components", {})
    payload = lock.get('runtime_payload')
    if payload is not None:
        try:
            files = payload['files']
            actual = {}
            for relative in files:
                candidate = root / relative
                path = candidate.resolve()
                info = candidate.lstat()
                if (Path(relative).is_absolute() or '..' in Path(relative).parts
                    or not path.is_relative_to(root.resolve()) or candidate.is_symlink()
                    or bool(getattr(info, 'st_file_attributes', 0) & 0x400)):
                    raise ValueError('unsafe runtime provenance path')
                actual[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
            digest = hashlib.sha256(json.dumps(actual, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            if (payload.get('algorithm') != 'DEV_RUNTIME_PACKAGE_SHA256_V2'
                or payload.get('runtime') != 'dev-kit-v2'
                or payload.get('self_excluded') != 'kits/dev/provenance.lock.json'
                or actual != files or digest != payload['sha256']):
                raise ValueError('Dev installed payload digest mismatch')
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f'Dev runtime payload provenance invalid: {error}')
    if lock.get("schema_version") != 1 or lock.get("status") != "ASSEMBLED_WITH_ONE_MINIMAL_UPSTREAM_ADAPTATION":
        errors.append("provenance lock schema/status differs from the frozen assembly")
    packaging = lock.get('packaging', {})
    if (packaging.get('version') != kit.get('version') or packaging.get('runtime') != 'dev-kit-v2'
        or packaging.get('runtime_root') != '~/.devkit/runtime/v2'
        or packaging.get('business_what_authority') != kit.get('authority', {}).get('business_what')
        or packaging.get('terminal_dev_readiness') != 'READY_FOR_TEST'
        or packaging.get('v1_compatibility') != 'LEGACY_COMPAT'
        or packaging.get('delivery_manifest') != 'DEFERRED_NON_AUTHORITATIVE'):
        errors.append('provenance package metadata differs from the VNext kit manifest')
    if set(kit.get("runtime_dependencies", {})) != {"spec_kit", "codebase_memory_mcp"}:
        errors.append("kit.yaml declares an unexpected runtime dependency")
    if (kit.get('name') != 'Dev Kit VNext'
        or not isinstance(kit.get('version'),str)
        or re.fullmatch(r'\d+\.\d+\.\d+-rc\.\d+',kit['version']) is None
        or kit.get('runtime', {}).get('external_project_runtime_root') != '~/.devkit/runtime/v2'
        or kit.get('authority', {}).get('business_what') != 'Engineering Handoff VNext backed by exact APPROVED_BASELINE proof'
        or kit.get('compatibility', {}).get('v1') != 'LEGACY_COMPAT; read-only inspection and no VNext authority'
        or kit.get('compatibility', {}).get('delivery_manifest') != 'DEFERRED_NON_AUTHORITATIVE'):
        errors.append('kit.yaml does not describe the frozen Dev VNext package boundary')
    try:
        plugin = json.loads((root / 'kits/dev/plugin/plugin.json').read_text(encoding='utf-8'))
        if plugin.get('version') != kit.get('version'):
            errors.append('plugin and kit versions differ')
    except (OSError, json.JSONDecodeError):
        errors.append('cannot read Dev plugin package metadata')
    spec = components.get("github-spec-kit", {})
    kit_spec = kit.get("runtime_dependencies", {}).get("spec_kit", {})
    if (spec.get("release"), spec.get("commit"), spec.get("license"), spec.get("classification"), spec.get("distributed_by_dev_kit")) != (
        "v1.0.11", "8147943512404afb9d99c6252cb9bf84369fd0b0", "MIT", "RUNTIME_DEPENDENCY", False,
    ):
        errors.append("Spec Kit provenance differs from the pinned non-distributed runtime")
    if kit_spec.get("version") != spec.get("release") or kit_spec.get("required_for") != ["normal", "high-risk"]:
        errors.append("kit.yaml Spec Kit version/required paths differ from frozen policy")
    cbm = components.get("codebase-memory-mcp", {})
    kit_cbm = kit.get("runtime_dependencies", {}).get("codebase_memory_mcp", {})
    if (cbm.get("release"), cbm.get("commit"), cbm.get("classification"), cbm.get("distributed_by_dev_kit")) != (
        "v0.11.0", "8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798", "RUNTIME_DEPENDENCY", False,
    ) or kit_cbm.get("required") is not False:
        errors.append("optional CBM provenance differs from the pinned non-distributed runtime")
    verification = components.get("superpowers-verification", {})
    if verification.get("current_local_provenance_commit") != "3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b":
        errors.append("canonical verification-before-completion provenance changed")
    gap_auditor = components.get("requirements-gap-auditor", {})
    if gap_auditor.get("commit") != "1fe1950bc4759e732b036c562b0cff99675e1695":
        errors.append("canonical requirements-gap-auditor provenance changed")
    addy = components.get("addy-agent-skills", {})
    expected_upstream = "c004a74784a08295d52749b04cda634125b9a581"
    if addy.get("commit") != expected_upstream or addy.get("release") != "0.6.10":
        errors.append("Addy planner upstream revision/release differs from frozen provenance")
    expected_skills = addy.get("selected_skills", {})
    for name, expected in expected_skills.items():
        if name == "planning-and-task-breakdown":
            continue
        path = root / "kits/dev/plugin/skills" / name / "SKILL.md"
        try:
            actual = _git_blob_sha1(path, root)
        except OSError as error:
            errors.append(f"missing vendored skill {name}: {error}")
            continue
        if name == "planning-and-task-breakdown":
            approved = expected == "670508158bb832d58266deebc833ea9859e2bc2d"
        else:
            approved = expected == actual
        if not approved:
            errors.append(f"unexpected Addy skill blob: {name} expected={expected} actual={actual}")
    planner = components.get("addy-planning-and-task-breakdown", {})
    planner_path = root / "kits/dev/plugin/skills/planning-and-task-breakdown/SKILL.md"
    try:
        planner_hash = _git_blob_sha1(planner_path, root)
        if (
            planner.get("classification") != "MODIFIED_UPSTREAM"
            or planner.get("source_blob") != "296249b64334bcfd1aeaefd27b9e3e5494e38ec0"
            or planner.get("local_blob") != planner_hash
            or planner_hash != "670508158bb832d58266deebc833ea9859e2bc2d"
            or len(planner.get("local_changes", [])) != 2
        ):
            errors.append("planner differs from the exact approved two-line local patch")
    except OSError as error:
        errors.append(f"missing planner: {error}")
    for reference, expected in addy.get("shared_references", {}).items():
        path = root / "kits/dev/plugin" / reference
        try:
            actual = _git_blob_sha1(path, root)
        except OSError as error:
            errors.append(f"missing shared Addy reference {reference}: {error}")
            continue
        if actual != expected:
            errors.append(f"unexpected Addy reference blob: {reference} expected={expected} actual={actual}")
    review = components.get("superpowers-review-package", {})
    review_path = root / "kits/dev/plugin/scripts/review-package"
    try:
        if _git_blob_sha1(review_path, root) != review.get("source_blob"):
            errors.append("Superpowers review-package blob differs from pinned upstream")
    except OSError as error:
        errors.append(f"missing Superpowers review-package: {error}")
    for component, filename, key in (
        (addy, "kits/dev/plugin/licenses/ADDY_AGENT_SKILLS_LICENSE.txt", "license_blob"),
        (review, "kits/dev/plugin/licenses/SUPERPOWERS_LICENSE.txt", "license_blob"),
    ):
        try:
            if _git_blob_sha1(root / filename, root) != component.get(key):
                errors.append(f"license blob mismatch: {filename}")
        except OSError as error:
            errors.append(f"missing license {filename}: {error}")
    notice = root / "kits/dev/plugin/THIRD_PARTY_NOTICES.md"
    try:
        notice_text = notice.read_text(encoding="utf-8")
        if (
            "addyosmani/agent-skills" not in notice_text
            or "obra/superpowers" not in notice_text
            or "MIT" not in notice_text
            or "GitHub Spec Kit" not in notice_text
            or "not redistributed" not in notice_text
        ):
            errors.append("plugin THIRD_PARTY_NOTICES.md is missing selected component attribution")
    except OSError as error:
        errors.append(f"missing plugin third-party notice: {error}")
    repository_notice = root / "THIRD_PARTY_NOTICES.md"
    try:
        notice_text = repository_notice.read_text(encoding="utf-8")
        if "Dev Kit VNext plugin payload" not in notice_text or "addyosmani/agent-skills" not in notice_text or "obra/superpowers" not in notice_text:
            errors.append("repository THIRD_PARTY_NOTICES.md is missing Dev Kit payload attribution")
    except OSError as error:
        errors.append(f"cannot read repository third-party notice: {error}")
    for required in kit.get("shared_skills", {}).get("required", []):
        if not (root / required / "SKILL.md").is_file():
            errors.append(f"required canonical shared skill is missing: {required}")
    review_budget = kit.get("execution", {}).get("review_budget", {})
    budget_contract = {
        "full_reviews": review_budget.get("max_full_reviews"),
        "blocking_fix_waves": review_budget.get("max_blocking_fix_waves"),
        "scoped_rereviews": review_budget.get("max_scoped_rereviews"),
    }
    if budget_contract != REVIEW_LIMITS:
        errors.append("kit.yaml review budget differs from the enforced 1/1/1 limit")
    return errors


def validate_workflow_package(root):
    root = Path(root)
    errors = []
    from tooling.lib.dev_vnext_spec_kit import FORBIDDEN_COMMANDS, workflow_document

    paths = {
        "normal": root / "kits/dev/plugin/workflows/dev-normal.workflow.yml",
        "high-risk": root / "kits/dev/plugin/workflows/dev-high-risk.workflow.yml",
    }
    for depth, path in paths.items():
        try:
            content = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append(f"missing workflow definition: {path}")
            continue
        serialized = json.dumps(content, sort_keys=True)
        for forbidden in FORBIDDEN_COMMANDS:
            if forbidden in serialized:
                errors.append(f"forbidden Spec Kit feature command {forbidden} in {path.name}")
        if "spec.md" in serialized or content != workflow_document(high_risk=depth == "high-risk"):
            errors.append(f"{depth} workflow differs from the canonical Dev VNext transport")
        if content.get("requires", {}).get("speckit_version") != "==1.0.11":
            errors.append(f"{depth} workflow does not pin Spec Kit v1.0.11")
    return errors


def validate_artifact_package(root):
    root = Path(root)
    errors = []
    base = root / "kits/dev"
    try:
        impact_schema = _read_json(base / "schemas/impact-manifest.schema.json")
        handoff_schema = _read_json(base / "schemas/dev-handoff.schema.json")
        impact_template = _read_json(base / "templates/impact-manifest.template.json")
        handoff_template = _read_json(base / "templates/dev-handoff.template.json")
        impact_valid = _read_json(root / "tooling/tests/fixtures/dev/impact-manifest.valid.json")
        impact_invalid = _read_json(root / "tooling/tests/fixtures/dev/impact-manifest.invalid.json")
        handoff_valid = _read_json(root / "tooling/tests/fixtures/dev/dev-handoff.valid.json")
        handoff_invalid = _read_json(root / "tooling/tests/fixtures/dev/dev-handoff.invalid.json")
    except ValueError as error:
        return [str(error)]
    for schema, fixture, label in (
        (impact_schema, impact_template, "Impact Manifest"),
        (handoff_schema, handoff_template, "Dev Handoff"),
    ):
        if not isinstance(schema.get("required"), list) or set(schema["required"]) != set(fixture):
            errors.append(f"{label} schema does not match its template")
    for data, label in ((impact_template, "Impact Manifest template"), (impact_valid, "valid Impact Manifest fixture")):
        if validate_impact_manifest(data):
            errors.append(f"{label} fails its validator")
    for data, label in ((impact_invalid, "invalid Impact Manifest fixture"),):
        if not validate_impact_manifest(data):
            errors.append(f"{label} unexpectedly passes")
    for data, label in ((handoff_template, "Dev Handoff template"), (handoff_valid, "valid Dev Handoff fixture")):
        if validate_dev_handoff(data):
            errors.append(f"{label} fails its validator")
    if not validate_dev_handoff(handoff_invalid):
        errors.append("invalid Dev Handoff fixture unexpectedly passes")
    return errors


def _read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read JSON {path}: {error}") from error


def _run_dir(project_root, change_id=None):
    if change_id is None:
        current = _read_json(Path(project_root) / CURRENT_RUN)
        change_id = current.get("change_id") if isinstance(current, dict) else None
    if not isinstance(change_id, str) or not ID_PATTERN.fullmatch(change_id):
        raise ValueError("no valid active Dev Kit run; run the start command first")
    return Path(project_root) / RUNS_DIR / change_id


def _load_run(project_root, change_id=None, check_baseline=True):
    project_root = Path(project_root).resolve()
    run_dir = _run_dir(project_root, change_id)
    inputs = _read_json(run_dir / "input.json")
    if Path(inputs.get("project_root", "")).resolve() != project_root:
        raise ValueError("active Dev Kit run belongs to a different project root")
    if check_baseline and inputs.get("baseline_snapshot"):
        errors = verify_baseline(inputs["baseline_snapshot"])
        if errors:
            raise ValueError("Approved BA Baseline changed: " + "; ".join(errors))
    if check_baseline and inputs.get("delivery_snapshot"):
        ref = inputs["delivery_snapshot"]
        delivery = load_delivery_manifest(ref["path"])
        if delivery["sha256"] != ref["sha256"]:
            raise ValueError("Delivery Manifest changed after run start")
        expected_authority = delivery_approval_context(delivery)
        if inputs.get("authority_precedence") is not None and inputs["authority_precedence"] != expected_authority:
            raise ValueError("validated delivery approval context changed after run start")
    return run_dir, inputs


def snapshot_approved_baseline(path):
    return read_approved_baseline(path).snapshot()


def verify_baseline(snapshot):
    return verify_baseline_snapshot(snapshot)


def delivery_approval_context(delivery):
    """Describe approval only from the validated handoff, source hashes, and Delivery Manifest V2."""
    data = delivery["data"]
    baseline = delivery["baseline"]
    handoff = data["ba"]["handoff"]
    ux = data["ux"]
    contract = ux.get("contract", {})
    receipt = ux.get("approval_receipt", {})
    return {
        "basis": "VALIDATED_DELIVERY_MANIFEST_V2",
        "delivery_revision": data["delivery_revision"],
        "delivery_manifest_sha256": delivery["sha256"],
        "ba": {
            "status": "APPROVED_FOR_ENGINEERING",
            "revision": baseline.revision,
            "handoff_sha256": handoff["sha256"],
            "source_hashes": dict(baseline.source_hashes),
            "non_blocking_items": list(baseline.open_items),
        },
        "ux": {
            "status": "APPROVED_EXACT_SNAPSHOT" if ux["required"] else "NOT_REQUIRED",
            "revision": contract.get("revision"),
            "contract_sha256": contract.get("sha256"),
            "approval_receipt_sha256": receipt.get("sha256"),
        },
        "delivery_blocking_items": list(data["open_items"]["blocking"]),
        "delivery_non_blocking_items": list(data["open_items"].get("non_blocking", [])),
    }


def _write_run_json(run_dir, name, value, baseline_snapshot):
    protected = []
    if baseline_snapshot:
        protected.append({"path": baseline_snapshot["path"]})
        protected.extend(baseline_snapshot.get("sources", []))
    write_artifact(Path(run_dir) / name, value, protected)


def start_run(project_root, change_id, kind, summary, signals=(), baseline=None, checks=(), business_ambiguities=(), behavior_change=False):
    project_root = Path(project_root).resolve()
    if not ID_PATTERN.fullmatch(change_id):
        raise ValueError("change_id must use letters, numbers, '_' or '-' and be at most 80 characters")
    if not _is_string(summary):
        raise ValueError("summary must be a non-empty string")
    if not isinstance(checks, (list, tuple)):
        raise ValueError("checks must be a list of JSON check objects")
    route = route_change(kind, summary, signals, business_ambiguities, behavior_change)
    if route["risk_level"] != "TRIVIAL" and not baseline and route["status"] != "NEEDS_BA_CLARIFICATION":
        raise ValueError("NORMAL and HIGH_RISK work requires an Approved BA Baseline path")
    if checks and any(not isinstance(item, dict) or item.get("category") not in ("build", "tests", "static_checks") or not _is_string(item.get("name")) or not isinstance(item.get("argv"), list) or not item["argv"] or any(not _is_string(arg) for arg in item["argv"]) for item in checks):
        raise ValueError("checks must be objects with name, category, and a non-empty argv list")
    categories = {item["category"] for item in checks}
    if route["workflow"] == "trivial" and not checks:
        raise ValueError("TRIVIAL work requires at least one deterministic --check")
    if route["workflow"] in ("normal", "high-risk") and not {"build", "tests"}.issubset(categories):
        raise ValueError("NORMAL and HIGH_RISK work requires at least one build and one tests --check")
    snapshot = snapshot_approved_baseline(baseline) if baseline else None
    current_path = project_root / CURRENT_RUN
    if current_path.is_file():
        current = _read_json(current_path)
        old_id = current.get("change_id") if isinstance(current, dict) else None
        if old_id:
            old_state_path = project_root / RUNS_DIR / old_id / "lifecycle.json"
            old_state = _read_json(old_state_path) if old_state_path.is_file() else {}
            if old_state.get("status") in ("RUNNING", "PAUSED"):
                raise ValueError(f"Dev Kit run {old_id} is still active")
    run_dir = project_root / RUNS_DIR / change_id
    if run_dir.exists():
        raise ValueError(f"Dev Kit run already exists: {run_dir}; choose a new change_id")
    run_dir.mkdir(parents=True)
    inputs = {
        "schema_version": 1, "change_id": change_id, "kind": kind, "summary": summary,
        "signals": list(signals), "checks": list(checks), "project_root": str(project_root),
        "baseline_snapshot": snapshot, "baseline_ref": ({"path": snapshot["path"], "revision": snapshot["revision"], "sha256": snapshot["sha256"]} if snapshot else None),
        "route": route,
    }
    lifecycle = {
        "schema_version": 1, "change_id": change_id,
        "status": route["status"] if route["status"] == "NEEDS_BA_CLARIFICATION" else "RUNNING",
        "review_budget": {key: 0 for key in REVIEW_LIMITS},
        "human_gate": {
            "required": route["human_gate_required"], "resolved": not route["human_gate_required"],
            "choice": None, "workflow_run_id": None, "workflow_state_path": None,
            "planning_artifacts_sha256": None,
        },
        "readiness": "UNKNOWN", "created_artifacts": [],
    }
    _write_run_json(run_dir, "input.json", inputs, snapshot)
    _write_run_json(run_dir, "lifecycle.json", lifecycle, snapshot)
    impact = {
        "schema_version": 1, "change_id": change_id, "baseline_ref": inputs["baseline_ref"],
        "affected_repositories": [], "affected_components": [], "affected_interfaces": [],
        "affected_data": [], "dependencies": [], "constraints": [],
        "risk": {"level": route["risk_level"], "reasons": route["reasons"]}, "unknowns": [],
    }
    if snapshot:
        _write_run_json(run_dir, "impact-manifest.json", impact, snapshot)
    _write_run_json(project_root, str(CURRENT_RUN), {"change_id": change_id}, snapshot)
    next_step = {
        "NEEDS_BA_CLARIFICATION": "Stop for BA clarification; do not plan or implement.",
        "TRIVIAL": "Edit only after this start; run finish-trivial and wait for a terminal result before reporting.",
        "NORMAL": "Continue the NORMAL workflow now; complete readiness, preflight/impact, plan-check, and implementation-ready before editing.",
        "HIGH_RISK": "Continue the HIGH_RISK workflow now; stop at the Human/Tech Lead gate before implementation.",
    }[route["risk_level"] if route["status"] != "NEEDS_BA_CLARIFICATION" else route["status"]]
    return {"run_dir": str(run_dir), "route": route, "baseline_ref": inputs["baseline_ref"], "next_step": next_step}


def load_start_request(path):
    try:
        request = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read start request {path}: {error}") from error
    if not isinstance(request, dict):
        raise ValueError("start request must be a JSON object")
    required = {"schema_version", "change_id", "kind", "summary", "signals", "baseline", "checks"}
    optional = {"business_ambiguities", "behavior_change"}
    missing = sorted(required - set(request))
    unexpected = sorted(set(request) - required - optional)
    if missing:
        raise ValueError("start request is missing required fields: " + ", ".join(missing))
    if unexpected:
        raise ValueError("start request has unexpected fields: " + ", ".join(unexpected))
    if type(request["schema_version"]) is not int or request["schema_version"] != 1:
        raise ValueError("start request schema_version must be 1")
    if not _is_string(request["change_id"]) or not ID_PATTERN.fullmatch(request["change_id"]):
        raise ValueError("start request change_id must use letters, numbers, '_' or '-' and be at most 80 characters")
    if not _is_string(request["kind"]) or request["kind"] not in START_KINDS:
        raise ValueError("start request kind must be one of: " + ", ".join(sorted(START_KINDS)))
    if not _is_string(request["summary"]):
        raise ValueError("start request summary must be a non-empty string")
    for field in ("signals", "business_ambiguities"):
        value = request.get(field, [])
        if not isinstance(value, list) or any(not _is_string(item) for item in value):
            raise ValueError(f"start request {field} must be a list of non-empty strings")
    if type(request.get("behavior_change", False)) is not bool:
        raise ValueError("start request behavior_change must be a boolean")
    baseline = request["baseline"]
    if baseline is not None and not _is_string(baseline):
        raise ValueError("start request baseline must be a non-empty path string or null")
    checks = request["checks"]
    if not isinstance(checks, list):
        raise ValueError("start request checks must be a list")
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ValueError(f"start request checks[{index}] must be an object")
        if set(check) != {"name", "category", "argv"}:
            raise ValueError(f"start request checks[{index}] must contain exactly name, category, and argv")
        if not _is_string(check["name"]):
            raise ValueError(f"start request checks[{index}].name must be a non-empty string")
        if not _is_string(check["category"]) or check["category"] not in CHECK_CATEGORIES:
            raise ValueError(f"start request checks[{index}].category must be build, tests, or static_checks")
        if not isinstance(check["argv"], list) or not check["argv"] or any(not _is_string(arg) for arg in check["argv"]):
            raise ValueError(f"start request checks[{index}].argv must be a non-empty list of non-empty strings")
    return {
        "change_id": request["change_id"],
        "kind": request["kind"],
        "summary": request["summary"],
        "signals": request["signals"],
        "baseline": baseline,
        "checks": checks,
        "business_ambiguities": request.get("business_ambiguities", []),
        "behavior_change": request.get("behavior_change", False),
    }


def _save_lifecycle(project_root, run_dir, inputs, state):
    _write_run_json(run_dir, "lifecycle.json", state, inputs.get("baseline_snapshot"))


def preflight(project_root):
    run_dir, inputs = _load_run(project_root)
    readiness = _read_json(run_dir / "spec-readiness.json")
    lifecycle = _read_json(run_dir / "lifecycle.json")
    if lifecycle.get("status") == "HIGH_RISK_REENTRY_REQUIRED":
        escalation = lifecycle.get("risk_escalation", {})
        return {
            "status": "HIGH_RISK_REENTRY_REQUIRED", "planning_allowed": False,
            "reasons": escalation.get("reasons", []),
        }
    status = readiness.get("status") if isinstance(readiness, dict) else None
    if status != "READY_FOR_PLANNING":
        lifecycle["status"] = "NEEDS_BA_CLARIFICATION"
        lifecycle["readiness"] = "NEEDS_BA_CLARIFICATION"
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
        return {"status": "NEEDS_BA_CLARIFICATION", "planning_allowed": False}
    ambiguities = readiness.get("business_ambiguities", [])
    if not isinstance(ambiguities, list) or ambiguities:
        lifecycle["status"] = "NEEDS_BA_CLARIFICATION"
        lifecycle["readiness"] = "NEEDS_BA_CLARIFICATION"
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
        return {"status": "NEEDS_BA_CLARIFICATION", "planning_allowed": False}
    impact = _read_json(run_dir / "impact-manifest.json")
    errors = validate_impact_manifest(impact)
    if errors:
        raise ValueError("invalid Impact Manifest: " + "; ".join(errors))
    if impact.get("change_id") != inputs["change_id"] or impact.get("baseline_ref") != inputs.get("baseline_ref"):
        raise ValueError("Impact Manifest does not reference the active change and Approved BA Baseline")
    business_blockers = [item for item in impact["unknowns"] if item["kind"] == "BUSINESS" and item["blocking"]]
    if business_blockers:
        lifecycle["status"] = "NEEDS_BA_CLARIFICATION"
        lifecycle["readiness"] = "NEEDS_BA_CLARIFICATION"
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
        return {"status": "NEEDS_BA_CLARIFICATION", "planning_allowed": False, "business_ambiguities": [item["description"] for item in business_blockers]}
    routed_risk = inputs["route"]["risk_level"]
    impact_risk = impact["risk"]["level"]
    if RISK_LEVEL_ORDER[impact_risk] < RISK_LEVEL_ORDER[routed_risk]:
        lifecycle["status"] = "RISK_DOWNGRADE_BLOCKED"
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
        raise ValueError(f"Impact Manifest cannot downgrade the initial {routed_risk} route to {impact_risk}")
    if impact_risk == "HIGH_RISK" and routed_risk == "NORMAL":
        lifecycle["status"] = "HIGH_RISK_REENTRY_REQUIRED"
        lifecycle["risk_escalation"] = {"from": "NORMAL", "to": "HIGH_RISK", "reasons": impact["risk"]["reasons"]}
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
        return {"status": "HIGH_RISK_REENTRY_REQUIRED", "planning_allowed": False, "reasons": impact["risk"]["reasons"]}
    if impact_risk != routed_risk:
        raise ValueError("Impact Manifest risk is incompatible with the deterministic route")
    lifecycle["readiness"] = "READY_FOR_PLANNING"
    lifecycle["status"] = "RUNNING"
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"status": "READY_FOR_PLANNING", "planning_allowed": True, "risk_level": impact["risk"]["level"]}


def assert_workflow(project_root, expected):
    _, inputs = _load_run(project_root)
    actual = inputs["route"].get("workflow")
    if actual != expected:
        raise ValueError(f"active change routes to {actual!r}, not {expected!r}")
    return {"workflow": expected, "risk_level": inputs["route"]["risk_level"]}


def _planning_artifact(run_dir, inputs, filename):
    path = run_dir / filename
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"required planning artifact is missing: {filename}") from error
    if not text.strip():
        raise ValueError(f"planning artifact is empty: {filename}")
    match = re.match(r"\A<!-- devkit-planning-metadata\r?\n([^\r\n]+)\r?\n-->\s*", text)
    if not match or not text[match.end():].strip():
        raise ValueError(f"{filename} requires metadata and non-empty planning content")
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError as error:
        raise ValueError(f"{filename} has invalid Dev Kit planning metadata: {error}") from error
    if not isinstance(metadata, dict) or metadata.get("change_id") != inputs["change_id"]:
        raise ValueError(f"{filename} does not belong to the active change")
    if metadata.get("baseline_ref") != inputs.get("baseline_ref"):
        raise ValueError(f"{filename} does not reference the active Approved BA Baseline")
    if metadata.get("business_ambiguity") != "CLEAR":
        raise ValueError(f"{filename} does not declare business ambiguity clear")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_planning_artifacts(project_root):
    run_dir, inputs = _load_run(project_root)
    lifecycle = _read_json(run_dir / "lifecycle.json")
    readiness = _read_json(run_dir / "spec-readiness.json")
    impact = _read_json(run_dir / "impact-manifest.json")
    if lifecycle.get("status") == "HIGH_RISK_REENTRY_REQUIRED":
        raise ValueError("NORMAL implementation is blocked; start a new HIGH_RISK run with the Impact risk signals")
    if (
        not isinstance(readiness, dict) or readiness.get("status") != "READY_FOR_PLANNING"
        or not isinstance(readiness.get("business_ambiguities"), list) or readiness["business_ambiguities"]
    ):
        raise ValueError("planning artifacts cannot pass with unresolved business ambiguity")
    impact_errors = validate_impact_manifest(impact)
    if impact_errors or impact.get("change_id") != inputs["change_id"] or impact.get("baseline_ref") != inputs.get("baseline_ref"):
        raise ValueError("planning artifacts require a valid Impact Manifest for the active change and baseline")
    if any(item["kind"] == "BUSINESS" and item["blocking"] for item in impact["unknowns"]):
        raise ValueError("planning artifacts cannot pass with a blocking business-semantic unknown")
    routed_risk = inputs["route"]["risk_level"]
    impact_risk = impact["risk"]["level"]
    if impact_risk != routed_risk:
        if routed_risk == "NORMAL" and impact_risk == "HIGH_RISK":
            raise ValueError("HIGH_RISK Impact escalation requires a new HIGH_RISK run before implementation")
        raise ValueError(f"Impact risk cannot change from the initial {routed_risk} route to {impact_risk}")
    hashes = {filename: _planning_artifact(run_dir, inputs, filename) for filename in ("dev-plan.md", "dev-tasks.md")}
    lifecycle["planning_artifacts"] = {
        "change_id": inputs["change_id"], "baseline_ref": inputs["baseline_ref"], "sha256": hashes,
    }
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"planning_allowed": True, "artifacts": hashes}


def assert_implementation_allowed(project_root, expected):
    run_dir, inputs = _load_run(project_root)
    lifecycle = _read_json(run_dir / "lifecycle.json")
    if lifecycle.get("status") == "HIGH_RISK_REENTRY_REQUIRED":
        raise ValueError("HIGH_RISK impact escalation blocks implementation; create a new HIGH_RISK run")
    if inputs["route"].get("workflow") != expected:
        raise ValueError(f"active route is {inputs['route'].get('workflow')!r}, not {expected!r}")
    planning = lifecycle.get("planning_artifacts", {})
    if not isinstance(planning, dict):
        raise ValueError("planning artifacts have not passed the deterministic planning gate")
    expected_hashes = planning.get("sha256", {})
    actual_hashes = {filename: _planning_artifact(run_dir, inputs, filename) for filename in ("dev-plan.md", "dev-tasks.md")}
    if (
        planning.get("change_id") != inputs["change_id"]
        or planning.get("baseline_ref") != inputs.get("baseline_ref")
        or expected_hashes != actual_hashes
    ):
        raise ValueError("planning artifacts are not the validated artifacts for the active change and baseline")
    current = validate_planning_artifacts(project_root)
    if current["artifacts"] != expected_hashes:
        raise ValueError("planning artifacts or readiness changed before implementation")
    lifecycle = _read_json(run_dir / "lifecycle.json")
    impact = _read_json(run_dir / "impact-manifest.json")
    if impact["risk"]["level"] != inputs["route"]["risk_level"]:
        raise ValueError("implementation cannot proceed with an unhandled Impact risk escalation")
    if expected == "high-risk":
        gate = lifecycle.get("human_gate", {})
        if not gate.get("required") or not gate.get("resolved") or gate.get("choice") != "approve":
            raise ValueError("HIGH_RISK implementation requires the approved Human/Tech Lead gate")
        if gate.get("planning_artifacts_sha256") != actual_hashes:
            raise ValueError("HIGH_RISK plan changed after the Human/Tech Lead gate")
    return {"implementation_allowed": True, "artifacts": actual_hashes}


def _check_artifact(project_root, filename):
    run_dir, inputs = _load_run(project_root)
    return run_dir, inputs, _read_json(run_dir / filename)


def claim_action(project_root, action):
    run_dir, inputs = _load_run(project_root)
    lifecycle = _read_json(run_dir / "lifecycle.json")
    needed = True
    if action == "blocking_fix_waves":
        review = _read_json(run_dir / "review.json")
        needed = bool(review.get("blocking_findings"))
    elif action == "scoped_rereviews":
        fix = _read_json(run_dir / "fix-result.json")
        needed = bool(fix.get("materially_changed"))
    budget = claim_review_action(lifecycle["review_budget"], action, needed)
    lifecycle["review_budget"] = budget
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"claimed": needed, "review_budget": budget}


def record_review(project_root):
    run_dir, inputs, review = _check_artifact(project_root, "review.json")
    if review.get("full_review_performed") is not True:
        raise ValueError("review.json must confirm exactly one full consolidated review")
    findings = review.get("blocking_findings")
    followups = review.get("followups")
    if not isinstance(findings, list) or any(not isinstance(item, dict) or item.get("class") != "BLOCKING" or not _is_string(item.get("id")) or not _is_string(item.get("description")) for item in findings):
        raise ValueError("review.json blocking_findings must contain only BLOCKING findings")
    if not isinstance(followups, list) or any(not isinstance(item, dict) or item.get("class") != "FOLLOW_UP" or not _is_string(item.get("id")) or not _is_string(item.get("description")) for item in followups):
        raise ValueError("review.json followups must contain only FOLLOW_UP findings")
    lifecycle = _read_json(run_dir / "lifecycle.json")
    if lifecycle["review_budget"]["full_reviews"] != 1:
        raise ValueError("full review was not claimed exactly once")
    lifecycle["review"] = {"initial_blocking_findings": findings, "blocking_findings": findings, "followups": followups}
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"blocking_findings": len(findings), "followups": len(followups)}


def record_fix(project_root):
    run_dir, inputs = _load_run(project_root)
    review = _read_json(run_dir / "review.json")
    fix = _read_json(run_dir / "fix-result.json")
    if type(fix.get("performed")) is not bool or type(fix.get("materially_changed")) is not bool:
        raise ValueError("fix-result.json performed and materially_changed must be booleans")
    original = review.get("blocking_findings", [])
    remaining = fix.get("remaining_blocking_findings", [])
    if not isinstance(remaining, list) or any(not isinstance(item, dict) or item.get("class") != "BLOCKING" for item in remaining):
        raise ValueError("fix-result.json remaining_blocking_findings must contain only BLOCKING findings")
    lifecycle = _read_json(run_dir / "lifecycle.json")
    if original and (fix.get("performed") is not True or lifecycle["review_budget"]["blocking_fix_waves"] != 1):
        raise ValueError("blocking findings require exactly one blocking fix wave")
    if not original and fix.get("performed") is not False:
        raise ValueError("a fix wave must be skipped when the consolidated review found no blockers")
    if remaining:
        lifecycle["status"] = "HUMAN_TECH_LEAD_REVIEW" if inputs["route"]["risk_level"] == "HIGH_RISK" else "NEEDS_REPLAN"
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
        return {"status": lifecycle["status"], "remaining_blockers": len(remaining)}
    lifecycle["review"]["blocking_findings"] = []
    lifecycle["fix_result"] = {"materially_changed": bool(fix.get("materially_changed")), "remaining_blocking_findings": []}
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"status": "READY_FOR_VERIFICATION", "materially_changed": bool(fix.get("materially_changed"))}


def record_scoped_rereview(project_root):
    run_dir, inputs = _load_run(project_root)
    lifecycle = _read_json(run_dir / "lifecycle.json")
    fix = _read_json(run_dir / "fix-result.json")
    rereview_path = run_dir / "scoped-rereview.json"
    if fix.get("materially_changed"):
        rereview = _read_json(rereview_path)
        if rereview.get("performed") is not True or lifecycle["review_budget"]["scoped_rereviews"] != 1:
            raise ValueError("material fix changes require exactly one scoped re-review")
        if rereview.get("full_feature_review") is not False:
            raise ValueError("scoped re-review must not perform a second full feature review")
        original_ids = {item.get("id") for item in lifecycle["review"].get("initial_blocking_findings", []) if item.get("id")}
        reviewed_ids = set(rereview.get("reviewed_finding_ids", []))
        if not original_ids.issubset(reviewed_ids):
            raise ValueError("scoped re-review must cover each prior blocking finding")
        new_blockers = rereview.get("blocking_findings", [])
        if not isinstance(new_blockers, list):
            raise ValueError("scoped-rereview.json blocking_findings must be a list")
        if new_blockers:
            lifecycle["review"]["blocking_findings"] = new_blockers
            lifecycle["status"] = "HUMAN_TECH_LEAD_REVIEW" if inputs["route"]["risk_level"] == "HIGH_RISK" else "NEEDS_REPLAN"
            _save_lifecycle(project_root, run_dir, inputs, lifecycle)
            return {"status": lifecycle["status"], "blocking_findings": len(new_blockers)}
    else:
        lifecycle["review_budget"]["scoped_rereviews"] = 0
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"scoped_rereviews": lifecycle["review_budget"]["scoped_rereviews"]}


def mark_gate_approved(project_root, choice, workflow_run_id):
    run_dir, inputs = _load_run(project_root)
    if not inputs["route"]["human_gate_required"]:
        raise ValueError("the active route does not require a Human/Tech Lead gate")
    if choice != "approve":
        raise ValueError("the Spec Kit Human/Tech Lead gate did not return approve")
    if not isinstance(workflow_run_id, str) or not ID_PATTERN.fullmatch(workflow_run_id):
        raise ValueError("gate approval requires a valid Spec Kit workflow run ID")
    state_path = Path(project_root).resolve() / ".specify/workflows/runs" / workflow_run_id / "state.json"
    workflow_state = _read_json(state_path)
    if not isinstance(workflow_state, dict):
        raise ValueError("Spec Kit workflow state must be a JSON object")
    step_results = workflow_state.get("step_results", {})
    if not isinstance(step_results, dict):
        raise ValueError("Spec Kit workflow state has invalid step results")
    gate_step = step_results.get("human-tech-lead-plan-gate", {})
    gate_output = gate_step.get("output") if isinstance(gate_step, dict) else None
    if (
        workflow_state.get("run_id") != workflow_run_id or not isinstance(gate_step, dict)
        or gate_step.get("status") != "completed" or not isinstance(gate_output, dict) or gate_output.get("choice") != choice
    ):
        raise ValueError("Spec Kit persisted gate evidence does not match an approved gate choice")
    planning = validate_planning_artifacts(project_root)
    lifecycle = _read_json(run_dir / "lifecycle.json")
    lifecycle["human_gate"]["resolved"] = True
    lifecycle["human_gate"]["choice"] = choice
    lifecycle["human_gate"]["workflow_run_id"] = workflow_run_id
    lifecycle["human_gate"]["workflow_state_path"] = state_path.relative_to(Path(project_root).resolve()).as_posix()
    lifecycle["human_gate"]["planning_artifacts_sha256"] = planning["artifacts"]
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return lifecycle["human_gate"]


def resolve_executable_argv(argv):
    """Resolve Windows bare names without shell parsing or changing arguments.

    CreateProcess does not apply PATHEXT like shutil.which does. Preserve
    explicit caller paths, including drive-relative paths, and POSIX behavior.
    The returned copy is execution-only; evidence retains declared argv.
    """
    executable = argv[0]
    resolved = list(argv)
    if _WINDOWS and not ntpath.dirname(executable) and not ntpath.splitdrive(executable)[0]:
        found = shutil.which(executable)
        if found is None:
            raise FileNotFoundError(f"EXECUTABLE_NOT_FOUND: {executable}")
        resolved[0] = found
    return resolved


def run_checks(project_root, phase):
    if phase not in ("focused", "fresh"):
        raise ValueError("phase must be focused or fresh")
    run_dir, inputs = _load_run(project_root)
    checks = inputs.get("checks", [])
    if not checks:
        raise ValueError("no deterministic checks configured; restart with at least one --check JSON object")
    results = []
    failed = False
    for check in checks:
        try:
            proc = subprocess.run(resolve_executable_argv(check["argv"]), cwd=project_root, capture_output=True, text=True, timeout=1800, shell=False)
            exit_code = proc.returncode
            stdout, stderr = proc.stdout[-4000:], proc.stderr[-4000:]
        except FileNotFoundError as error:
            exit_code, stdout, stderr = -1, "", f"EXECUTABLE_NOT_FOUND: {check['argv'][0]} ({error})"
        except (OSError, subprocess.TimeoutExpired) as error:
            exit_code, stdout, stderr = -1, "", str(error)
        result = {"name": check["name"], "status": "PASS" if exit_code == 0 else "FAIL", "command": check["argv"], "exit_code": exit_code, "stdout": stdout, "stderr": stderr}
        results.append({**result, "category": check["category"]})
        failed |= exit_code != 0
    snapshot = inputs.get("baseline_snapshot")
    protected = [{"path": snapshot["path"]}, *snapshot.get("sources", [])] if snapshot else ()
    write_artifact(run_dir / f"verification-{phase}.json", {"phase": phase, "checks": results}, protected)
    if phase == "fresh":
        lifecycle = _read_json(run_dir / "lifecycle.json")
        lifecycle["verification"] = results
        if failed:
            lifecycle["status"] = "NEEDS_REPLAN"
        _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"phase": phase, "checks": results, "status": "FAIL" if failed else "PASS"}


def prepare_handoff(project_root):
    run_dir, inputs = _load_run(project_root)
    lifecycle = _read_json(run_dir / "lifecycle.json")
    impact = _read_json(run_dir / "impact-manifest.json")
    review = lifecycle.get("review", {"blocking_findings": [], "followups": []})
    verification = lifecycle.get("verification", [])
    checks = {"build": [], "tests": [], "static_checks": []}
    for item in verification:
        checks[item["category"]].append({key: item[key] for key in ("name", "status", "command", "exit_code")})
    handoff = {
        "schema_version": 1, "change_id": inputs["change_id"], "baseline_ref": inputs["baseline_ref"],
        "implementation": {"commits": [], "changed_components": impact["affected_components"]},
        "requirements_coverage": [],
        "verification": {"build": checks["build"], "tests": checks["tests"], "static_checks": checks["static_checks"]},
        "review": {
            **lifecycle["review_budget"], "blocking_findings": review["blocking_findings"],
            "followups": review["followups"],
        },
        "business_ambiguity": {"status": lifecycle.get("readiness", "UNKNOWN"), "items": []},
        "human_gate": lifecycle["human_gate"],
        "known_risks": [*impact["risk"]["reasons"], *(item.get("description", item.get("id", "unknown")) for item in impact["unknowns"])],
        "state": "IN_PROGRESS",
    }
    if handoff["business_ambiguity"]["status"] != "READY_FOR_PLANNING":
        handoff["business_ambiguity"] = {"status": "NEEDS_BA_CLARIFICATION", "items": ["Spec readiness has not passed"]}
    else:
        handoff["business_ambiguity"] = {"status": "CLEAR", "items": []}
    write_artifact(run_dir / "dev-handoff.json", handoff, [{"path": inputs["baseline_snapshot"]["path"]}, *inputs["baseline_snapshot"]["sources"]])
    return handoff


def finalize_handoff(project_root):
    run_dir, inputs = _load_run(project_root)
    handoff = _read_json(run_dir / "dev-handoff.json")
    handoff["state"] = _derive_handoff_state(handoff)
    errors = validate_dev_handoff(handoff)
    if errors:
        raise ValueError("invalid Dev Handoff: " + "; ".join(errors))
    write_artifact(run_dir / "dev-handoff.json", handoff, [{"path": inputs["baseline_snapshot"]["path"]}, *inputs["baseline_snapshot"]["sources"]])
    lifecycle = _read_json(run_dir / "lifecycle.json")
    lifecycle["status"] = handoff["state"]
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return {"state": handoff["state"], "path": str(run_dir / "dev-handoff.json")}


def _derive_handoff_state(handoff):
    ambiguity = handoff.get("business_ambiguity", {})
    if ambiguity.get("status") != "CLEAR" or ambiguity.get("items"):
        return "NEEDS_BA_CLARIFICATION"
    gate = handoff.get("human_gate", {})
    review = handoff.get("review", {})
    if not gate.get("resolved"):
        return "HUMAN_TECH_LEAD_REVIEW" if gate.get("required") else "IN_PROGRESS"
    if gate.get("required") and (
        gate.get("choice") != "approve" or not _is_string(gate.get("workflow_run_id"))
        or not _is_string(gate.get("workflow_state_path")) or not isinstance(gate.get("planning_artifacts_sha256"), dict)
    ):
        return "HUMAN_TECH_LEAD_REVIEW"
    if review.get("blocking_findings"):
        return "HUMAN_TECH_LEAD_REVIEW" if gate.get("required") else "NEEDS_REPLAN"
    verification = handoff.get("verification", {})
    build = verification.get("build", [])
    if not isinstance(build, list):
        return "NEEDS_REPLAN"
    checks = [*build, *verification.get("tests", []), *verification.get("static_checks", [])]
    if not checks or any(not isinstance(item, dict) or item.get("status") != "PASS" or item.get("exit_code") != 0 for item in checks):
        return "NEEDS_REPLAN"
    coverage = handoff.get("requirements_coverage", [])
    if not coverage or any(not isinstance(item, dict) or item.get("status") != "COVERED" for item in coverage):
        return "NEEDS_REPLAN"
    if not verification.get("tests"):
        return "NEEDS_REPLAN"
    if review.get("full_reviews") != 1:
        return "IN_PROGRESS"
    return "READY_FOR_TEST"


def finish_trivial(project_root):
    run_dir, inputs = _load_run(project_root)
    if inputs["route"]["risk_level"] != "TRIVIAL":
        raise ValueError("trivial completion only accepts a TRIVIAL route")
    result = run_checks(project_root, "fresh")
    lifecycle = _read_json(run_dir / "lifecycle.json")
    lifecycle["status"] = "COMPLETED" if result["status"] == "PASS" else "NEEDS_REPLAN"
    _save_lifecycle(project_root, run_dir, inputs, lifecycle)
    return lifecycle["status"]


def _version_tuple(text):
    match = re.search(r"\b(\d+)\.(\d+)\.(\d+)\b", text)
    return tuple(map(int, match.groups())) if match else None


def _valid_skill(path, expected_name):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return False
    match = re.search(r"(?m)^name:\s*['\"]?([^'\"\r\n]+)", text)
    return bool(match and match.group(1).strip() == expected_name and text.startswith("---"))


def _composition_matches(core, conditional):
    return (
        isinstance(core, list)
        and isinstance(conditional, list)
        and all(isinstance(item, str) for item in core + conditional)
        and len(core + conditional) == len(set(core + conditional))
        and set(core) == EXPECTED_CORE_SKILLS
        and set(conditional) == EXPECTED_CONDITIONAL_SKILLS
    )


def doctor(root=KIT_ROOT, project_root=None, user_home=None, mode="daily", spec_kit_cli=None, codex_home=None):
    root = Path(root).resolve()
    project_root = Path(project_root or root).resolve()
    user_home = Path(user_home or Path.home()).resolve()
    checks = []
    errors = []
    warnings = []
    try:
        kit = _read_json(root / "kits/dev/kit.yaml")
        plugin = _read_json(root / "kits/dev/plugin/plugin.json")
    except ValueError as error:
        kit, plugin = {}, {}
        errors.append(str(error))
    groups = kit.get("plugin_skills") if isinstance(kit, dict) else None
    core = groups.get("core") if isinstance(groups, dict) else None
    conditional = groups.get("conditional") if isinstance(groups, dict) else None
    shared = kit.get("shared_skills") if isinstance(kit, dict) else None
    shared_required = shared.get("required") if isinstance(shared, dict) else None
    composition_ok = (
        _composition_matches(core, conditional)
        and isinstance(shared_required, list)
        and all(isinstance(item, str) for item in shared_required)
        and set(shared_required) == EXPECTED_SHARED_SKILLS
        and isinstance(plugin, dict)
        and plugin.get("name") == "agent-skills-dev-kit"
        and plugin.get("version") == kit.get("version")
    )
    for skill in (core if isinstance(core, list) else []) + (conditional if isinstance(conditional, list) else []):
        if isinstance(skill, str):
            composition_ok &= _valid_skill(root / "kits/dev/plugin/skills" / skill / "SKILL.md", skill)
    checks.append({"name": "composition (kit.yaml/plugin/core/conditional/shared skills)", "status": "PASS" if composition_ok else "FAIL"})
    if not composition_ok:
        errors.append("Dev Kit composition is inconsistent or missing a selected skill")
    provenance_errors = validate_provenance(root)
    checks.append({"name": "provenance blobs/licenses/notices/planner patch", "status": "PASS" if not provenance_errors else "FAIL", "details": provenance_errors})
    errors.extend(provenance_errors)
    workflow_errors = validate_workflow_package(root)
    checks.append({"name": "workflow definitions and bounded routing", "status": "PASS" if not workflow_errors else "FAIL", "details": workflow_errors})
    errors.extend(workflow_errors)
    artifact_errors = validate_artifact_package(root)
    checks.append({"name": "schemas/validators/fixtures/templates", "status": "PASS" if not artifact_errors else "FAIL", "details": artifact_errors})
    errors.extend(artifact_errors)
    try:
        marketplace = _read_json(root / ".agents/plugins/marketplace.json")
        entry = next(item for item in marketplace.get("plugins", []) if item.get("name") == plugin.get("name"))
        marketplace_ok = (
            marketplace.get("name") == "agent-skills-dev-kit"
            and entry.get("source", {}).get("source") == "local"
            and entry.get("source", {}).get("path") == "./kits/dev/plugin"
            and entry.get("policy", {}).get("installation") == "AVAILABLE"
            and isinstance(entry.get("policy", {}).get("authentication"), str)
            and isinstance(entry.get("category"), str)
        )
    except (ValueError, StopIteration, AttributeError, TypeError):
        marketplace_ok = False
    checks.append({"name": "repo-local Codex plugin marketplace entry", "status": "PASS" if marketplace_ok else "FAIL"})
    if not marketplace_ok:
        errors.append("local plugin marketplace entry does not point at the frozen Dev Kit plugin payload")
    spec = str(spec_kit_cli) if spec_kit_cli else shutil.which("specify")
    spec_version = None
    if spec:
        try:
            result = subprocess.run([spec, "--version"], capture_output=True, text=True, timeout=10, check=False)
            spec_version = _version_tuple(result.stdout + " " + result.stderr)
        except (OSError, subprocess.TimeoutExpired):
            spec_version = None
    spec_ok = spec_version == (1, 0, 11)
    checks.append({"name": "pinned Spec Kit workflow runtime 1.0.11", "status": "PASS" if spec_ok else "FAIL", "version": ".".join(map(str, spec_version)) if spec_version else "unavailable"})
    if not spec_ok:
        errors.append("pinned Spec Kit CLI v1.0.11 is missing or the installed version differs")
    purity = inspect_context_purity(project_root, user_home, mode, codex_home=codex_home)
    cbm_available = any(
        item["kind"] == "mcp" and re.search(r"codebase.?memory", item["name"], re.IGNORECASE)
        for item in purity["inventory"]
    )
    checks.append({"name": "conditional codebase-memory-mcp", "status": "INFO", "details": "available" if cbm_available else "not configured; native source reading remains available"})
    checks.append({"name": "context purity", "status": purity["status"], "context_purity": purity["context_purity"], "contamination": purity["contamination"]})
    warnings.extend(purity["warnings"])
    if purity["status"] == "FAIL":
        errors.extend(item["reason"] for item in purity["contamination"] if item["relevant"])
    status = "FAIL" if errors else "DEGRADED" if warnings else "READY"
    return {"status": status, "context_purity": purity["context_purity"], "mode": mode, "checks": checks, "warnings": warnings, "errors": errors}


def _print_doctor(report, as_json=False):
    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    print("Dev Kit Doctor")
    for check in report["checks"]:
        status = check["status"]
        print(f"[{status}] {check['name']}")
        if check["name"] == "context purity":
            items = check.get("contamination", [])
            relevant = sum(bool(item.get("relevant")) for item in items)
            print(f"  {len(items)} context findings; {relevant} relevant to Dev Kit")
            groups = {}
            for item in items:
                key = item["reason"]
                groups.setdefault(key, []).append(item["name"])
            for reason, names in sorted(groups.items()):
                examples = ", ".join(names[:3])
                suffix = f" (examples: {examples})" if examples else ""
                print(f"  WARN: {reason} x{len(names)}{suffix}")
            continue
        for detail in check.get("details", []) if isinstance(check.get("details"), list) else [check.get("details", "")]:
            if detail:
                print(f"  {detail}")
    print(f"CONTEXT_PURITY = {report['context_purity']}")
    print(f"STATUS: {report['status']}")
    error_counts = {}
    for error in report["errors"]:
        error_counts[error] = error_counts.get(error, 0) + 1
    for error, count in error_counts.items():
        suffix = f" x{count}" if count > 1 else ""
        print(f"ERROR: {error}{suffix}")


def _legacy_main(argv=None):
    """Historical regression entrypoint; public VNext CLI never dispatches mutations here."""
    parser = argparse.ArgumentParser(description="Dev Kit V1 compatibility runtime and contract checks")
    commands = parser.add_subparsers(dest="command", required=True)
    router = commands.add_parser("route", help="Internal natural-intent delivery router")
    router.add_argument("--delivery", type=Path, required=True)
    router.add_argument("--summary", required=True)
    start = commands.add_parser("start")
    start.add_argument("--request", type=Path, help="Read and validate a structured start request JSON file")
    start.add_argument("--change-id")
    start.add_argument("--kind", choices=tuple(sorted(START_KINDS)))
    start.add_argument("--summary")
    start.add_argument("--signal", action="append", default=[])
    start.add_argument("--business-ambiguity", action="append", default=[])
    start.add_argument("--behavior-change", action="store_true")
    start.add_argument("--baseline", type=Path)
    start.add_argument("--check", action="append", default=[], help="JSON object: {name,category,argv}")
    request_validator = commands.add_parser("validate-start-request")
    request_validator.add_argument("path", type=Path)
    for name in ("validate-impact", "validate-handoff"):
        sub = commands.add_parser(name)
        sub.add_argument("path", type=Path, nargs="?")
    for name in ("preflight", "plan-check", "prepare-handoff", "review-check", "fix-check", "rereview-check", "handoff", "finish-trivial"):
        commands.add_parser(name)
    claim = commands.add_parser("claim")
    claim.add_argument("stage", choices=tuple(REVIEW_LIMITS))
    verify = commands.add_parser("verify")
    verify.add_argument("phase", choices=("focused", "fresh"))
    workflow_parser = commands.add_parser("assert-workflow")
    workflow_parser.add_argument("depth", choices=("normal", "high-risk"))
    implementation_parser = commands.add_parser("implementation-ready")
    implementation_parser.add_argument("depth", choices=("normal", "high-risk"))
    gate_parser = commands.add_parser("gate-approved")
    gate_parser.add_argument("--choice", required=True)
    gate_parser.add_argument("--workflow-run-id", required=True)
    schema_parser = commands.add_parser("schema")
    schema_parser.add_argument("name", choices=(
        "start-request", "engineering-impact", "engineering-gap", "engineering-decision",
        "dev-state", "technical-approval", "dev-handoff",
        "legacy/start-request", "legacy/impact-manifest", "legacy/dev-handoff",
    ))
    template_parser = commands.add_parser("template")
    template_parser.add_argument("name", choices=(
        "start-request", "engineering-impact", "engineering-gap", "engineering-decision",
        "technical-approval", "dev-handoff", "legacy/start-request",
        "legacy/impact-manifest", "legacy/dev-handoff",
    ))
    commands.add_parser("runtime-root")
    workflow_path_parser = commands.add_parser("workflow")
    workflow_path_parser.add_argument("depth", choices=("normal", "high-risk"))
    doctor_parser = commands.add_parser("doctor")
    doctor_parser.add_argument("--mode", choices=("daily", "benchmark"), default="daily")
    doctor_parser.add_argument("--root", type=Path, default=KIT_ROOT)
    doctor_parser.add_argument("--project-root", type=Path, default=Path.cwd())
    doctor_parser.add_argument("--home", type=Path, default=Path.home())
    doctor_parser.add_argument("--codex-home", type=Path, help="Dedicated profile root; excludes global user methodology")
    doctor_parser.add_argument("--spec-kit-cli", type=Path, help="Use this compatible specify executable instead of PATH lookup")
    doctor_parser.add_argument("--json", action="store_true")
    commands.add_parser("provenance")
    args = parser.parse_args(argv)
    try:
        if args.command == "route":
            sys.path.insert(0, str(KIT_ROOT))
            from tooling.lib.dev_router import _legacy_start_from_delivery
            print(json.dumps(_legacy_start_from_delivery(Path.cwd(), args.delivery, args.summary), indent=2, ensure_ascii=False))
            return 0
        if args.command == "start":
            if args.request:
                legacy_values = (args.change_id, args.kind, args.summary, args.signal, args.business_ambiguity, args.baseline, args.check, args.behavior_change)
                if any(legacy_values):
                    raise ValueError("--request cannot be combined with legacy start options")
                request = load_start_request(args.request)
            else:
                missing = [name for name, value in (("--change-id", args.change_id), ("--kind", args.kind), ("--summary", args.summary)) if value is None]
                if missing:
                    raise ValueError("start requires --request or all of: " + ", ".join(missing))
                request = {
                    "change_id": args.change_id, "kind": args.kind, "summary": args.summary,
                    "signals": args.signal, "baseline": args.baseline, "checks": [json.loads(item) for item in args.check],
                    "business_ambiguities": args.business_ambiguity, "behavior_change": args.behavior_change,
                }
            result = start_run(
                Path.cwd(), request["change_id"], request["kind"], request["summary"],
                request["signals"], request["baseline"], request["checks"],
                request["business_ambiguities"], request["behavior_change"],
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0 if result["route"]["status"] != "NEEDS_BA_CLARIFICATION" else 12
        if args.command == "validate-start-request":
            request = load_start_request(args.path)
            print(json.dumps({"status": "VALID", "change_id": request["change_id"], "check_count": len(request["checks"])}, indent=2))
            return 0
        if args.command in ("validate-impact", "validate-handoff"):
            if args.path:
                data = _read_json(args.path)
            else:
                run_dir, _ = _load_run(Path.cwd())
                data = _read_json(run_dir / ("impact-manifest.json" if args.command == "validate-impact" else "dev-handoff.json"))
            errors = validate_impact_manifest(data) if args.command == "validate-impact" else validate_dev_handoff(data)
            if errors:
                for error in errors:
                    print(f"INVALID: {error}", file=sys.stderr)
                return 1
            print(f"VALID: {args.command[len('validate-'):]}")
            return 0
        if args.command == "doctor":
            report = doctor(args.root, args.project_root, args.home, args.mode, args.spec_kit_cli, codex_home=args.codex_home)
            _print_doctor(report, args.json)
            return 1 if report["status"] == "FAIL" else 0
        if args.command == "provenance":
            errors = validate_provenance(KIT_ROOT)
            for error in errors:
                print(f"FAIL: {error}", file=sys.stderr)
            if errors:
                return 1
            print("PASS: 9 exact Addy skill blobs, 5 shared references, the approved planner patch, review-package, 2 license blobs, and notices")
            return 0
        if args.command == "preflight":
            result = preflight(Path.cwd())
            print(json.dumps(result, indent=2))
            return 0 if result["planning_allowed"] else 12
        if args.command in ("plan-check", "implementation-ready"):
            result = (
                validate_planning_artifacts(Path.cwd())
                if args.command == "plan-check"
                else assert_implementation_allowed(Path.cwd(), "high-risk" if args.depth == "high-risk" else "normal")
            )
            print(json.dumps(result, indent=2))
            return 0
        if args.command == "schema":
            legacy = args.name.startswith("legacy/")
            name = args.name.removeprefix("legacy/")
            filename = {
                "start-request": "start-request.schema.json" if legacy else "start-request-v2.schema.json",
                "impact-manifest": "impact-manifest.schema.json",
                "engineering-impact": "engineering-impact-v2.schema.json",
                "engineering-gap": "engineering-gap-v2.schema.json",
                "engineering-decision": "engineering-decision-v2.schema.json",
                "dev-state": "dev-state-v2.schema.json",
                "technical-approval": "technical-approval-v2.schema.json",
                "dev-handoff": "dev-handoff.schema.json" if legacy else "dev-handoff-v2.schema.json",
            }[name]
            path = KIT_ROOT / "kits/dev/schemas" / filename
            print(path.read_text(encoding="utf-8"), end="")
            return 0
        if args.command == "template":
            legacy = args.name.startswith("legacy/")
            name = args.name.removeprefix("legacy/")
            filename = {
                "start-request": "start-request.template.json" if legacy else "start-request-v2.template.json",
                "impact-manifest": "impact-manifest.template.json",
                "engineering-impact": "engineering-impact-v2.template.json",
                "engineering-gap": "engineering-gap-v2.template.json",
                "engineering-decision": "engineering-decision-v2.template.json",
                "technical-approval": "technical-approval-v2.boundary.md",
                "dev-handoff": "dev-handoff.template.json" if legacy else "dev-handoff-v2.shape.md",
            }[name]
            path = KIT_ROOT / "kits/dev/templates" / filename
            print(path.read_text(encoding="utf-8"), end="")
            return 0
        if args.command == "runtime-root":
            print(KIT_ROOT.resolve())
            return 0
        if args.command == "workflow":
            suffix = "high-risk" if args.depth == "high-risk" else "normal"
            path = KIT_ROOT / "kits/dev/plugin/workflows" / f"dev-{suffix}.workflow.yml"
            print(path.resolve())
            return 0
        if args.command == "claim":
            result = claim_action(Path.cwd(), args.stage)
        elif args.command == "assert-workflow":
            result = assert_workflow(Path.cwd(), args.depth)
        elif args.command == "review-check":
            result = record_review(Path.cwd())
        elif args.command == "fix-check":
            result = record_fix(Path.cwd())
        elif args.command == "rereview-check":
            result = record_scoped_rereview(Path.cwd())
        elif args.command == "gate-approved":
            result = mark_gate_approved(Path.cwd(), args.choice, args.workflow_run_id)
        elif args.command == "verify":
            result = run_checks(Path.cwd(), args.phase)
        elif args.command == "handoff":
            result = finalize_handoff(Path.cwd())
        elif args.command == "prepare-handoff":
            result = prepare_handoff(Path.cwd())
        elif args.command == "finish-trivial":
            result = {"status": finish_trivial(Path.cwd())}
        else:
            raise ValueError(f"unsupported command: {args.command}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if args.command == "handoff" and result.get("state") != "READY_FOR_TEST":
            return 1
        outcome = result.get("status", result.get("state"))
        return 1 if outcome in ("FAIL", "NEEDS_BA_CLARIFICATION", "NEEDS_REPLAN", "HUMAN_TECH_LEAD_REVIEW") else 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


def main(argv=None):
    """New runs use VNext; V1 artifacts are available for explicit inspection."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "doctor":
        sys.path.insert(0, str(KIT_ROOT))
        from tooling.lib.dev_vnext_doctor import main as doctor_main
        return doctor_main(argv[1:])
    # Schema/template inspection is package discovery; V1 stays explicit LEGACY_COMPAT.
    if argv and argv[0] in {"provenance", "runtime-root", "schema", "template"}:
        return _legacy_main(argv)
    sys.path.insert(0, str(KIT_ROOT))
    from tooling.lib.dev_vnext_cli import main as vnext_main
    return vnext_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
