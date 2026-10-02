"""First Test Kit V1 slice: approved BA to pinned TEA through Design Review."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .codex_cli import resolve_codex_command


ROOT = Path(__file__).resolve().parents[2]
TEST_ONLY_OUTPUT_ROOT = ROOT / ".work/benchmark-runs"


def is_test_only_workspace_path(path: str | Path) -> bool:
    target = Path(path).resolve()
    if target.is_relative_to(TEST_ONLY_OUTPUT_ROOT.resolve()):
        return True
    if target.is_relative_to(ROOT.resolve()):
        return False
    return target.is_relative_to(Path(tempfile.gettempdir()).resolve())


sys.path.insert(0, str(ROOT / "ba-workflow/scripts"))
from contracts import _yaml_fields, validate_handoff_file  # noqa: E402


TEA_REPOSITORY = "bmad-code-org/bmad-method-test-architecture-enterprise"
TEA_COMMIT = "1f53e9095061ab66f3c35abd9b98baf0f50cf8fe"
TEA_CAPABILITY = "bmad-testarch-test-design"
TEA_SKILL_SHA256 = "ca933c020623c796a95ce9701039c2d5658fc3cc60f7768e2fdf556b1d0d506b"
TEA_PIN_MANIFEST = ROOT / "tooling/pins/tea-test-design-v1.json"
TEA_PIN_MANIFEST_SHA256 = "d29797d379c013964c9755a5fe3e9b485bd4a5f0cf62b5604b41d426c171f337"
SEMANTIC_FIELDS = (
    "design_id",
    "hierarchy_path",
    "scenario_title",
    "expected_behavior",
    "requirement_refs",
    "open_questions",
)
RECORD_FIELDS = (*SEMANTIC_FIELDS, "review_status")
BENCHMARK_HEADERS = (
    "Scenario", "Requirement", "Level", "Risk Link", "Count", "Owner", "Observable expected result",
)
NATIVE_HEADERS = (
    "Test ID", "Kịch bản", "Mức kiểm thử", "Risk Link", "Truy vết", "Kết quả quan sát được",
)
BA_ID_TOKEN = re.compile(r"\b(?P<id>(?:FR|BR)-(?:[A-Za-z0-9]+-)*\d+)\b", re.IGNORECASE)
TEA_SCENARIO_TOKEN = re.compile(
    r"\b(?:TD-[A-Za-z0-9][A-Za-z0-9_-]*|\d+(?:\.\d+)?-(?:UNIT|INT|E2E|EXP)-\d+|TC-E\d+-\d+)\b",
    re.IGNORECASE,
)
RANGE_TOKEN = re.compile(
    r"\b(?P<prefix>FR|BR)-(?P<start>\d+)\s*(?P<separator>–|—|-|\bto\b)\s*"
    r"(?:(?P<end_prefix>FR|BR)-)?(?P<end>\d+)\b",
    re.IGNORECASE,
)
BAD_BA_ID_TOKEN = re.compile(r"\b(?:FR|BR)-[A-Za-z0-9_-]+", re.IGNORECASE)
SOURCE_HEADING = re.compile(
    r"^(?P<marks>#{2,6})\s+(?P<id>(?:FR|BR)-(?:[A-Za-z0-9]+-)*\d+)\s*(?:[—–-]\s*)?(?P<title>.*?)\s*$",
    re.IGNORECASE,
)
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")


class BaselineError(ValueError):
    def __init__(self, message: str, *, code: str = "INVALID_BA_BASELINE"):
        super().__init__(message)
        self.code = code


class _NormalizationError(ValueError):
    def __init__(self, finding: "Finding"):
        super().__init__(finding.message)
        self.finding = finding


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    path: str | None = None
    line: int | None = None
    field: str | None = None


@dataclass(frozen=True)
class RawEvidenceRef:
    path: str
    sha256: str
    line: int | None = None
    field: str | None = None


@dataclass(frozen=True)
class BaselineRow:
    id: str
    text: str
    path: str
    line: int


@dataclass(frozen=True)
class ApprovedBaseline:
    feature_id: str
    feature_title: str
    revision: str
    handoff_path: Path
    handoff_sha256: str
    source_paths: dict[str, Path]
    source_hashes: dict[str, str]
    requirements: tuple[BaselineRow, ...]
    business_rules: tuple[BaselineRow, ...]
    open_items: tuple[str, ...]
    unknown_clauses: dict[str, str]

    @property
    def requirement_ids(self) -> set[str]:
        return {row.id for row in self.requirements}

    @property
    def business_rule_ids(self) -> set[str]:
        return {row.id for row in self.business_rules}

    @property
    def ba_ids(self) -> set[str]:
        return self.requirement_ids | self.business_rule_ids


@dataclass(frozen=True)
class AdapterBundle:
    baseline: ApprovedBaseline
    requirements: tuple[BaselineRow, ...]
    business_rules: tuple[BaselineRow, ...]
    open_items: tuple[str, ...]
    unknown_texts: tuple[str, ...]
    epic_markdown: str
    business_rules_markdown: str
    open_decisions_markdown: str
    supplemental_text: str | None = None
    supplemental_source: RawEvidenceRef | None = None


@dataclass(frozen=True)
class OpenQuestion:
    source_ref: str
    text: str
    status: str = "UNKNOWN"

    def to_dict(self) -> dict[str, str]:
        return {"source_ref": self.source_ref, "text": self.text, "status": self.status}


@dataclass(frozen=True)
class CanonicalTestDesign:
    design_id: str
    hierarchy_path: tuple[str, ...]
    scenario_title: str
    expected_behavior: str | None
    requirement_refs: tuple[str, ...]
    open_questions: tuple[OpenQuestion, ...]
    review_status: str = "DRAFT"

    def semantic_dict(self) -> dict:
        return {
            "design_id": self.design_id,
            "hierarchy_path": list(self.hierarchy_path),
            "scenario_title": self.scenario_title,
            "expected_behavior": self.expected_behavior,
            "requirement_refs": list(self.requirement_refs),
            "open_questions": [question.to_dict() for question in self.open_questions],
        }

    def to_dict(self) -> dict:
        return {**self.semantic_dict(), "review_status": self.review_status}


@dataclass(frozen=True)
class DesignSnapshot:
    artifact_id: str
    revision: str
    records: tuple[CanonicalTestDesign, ...]
    payload_bytes: bytes
    sha256: str
    evidence: tuple[RawEvidenceRef, ...]
    field_sources: dict[str, dict[str, RawEvidenceRef]]

    @classmethod
    def create(
        cls,
        records: Iterable[CanonicalTestDesign],
        *,
        artifact_id: str,
        revision: str,
        evidence: Iterable[RawEvidenceRef] = (),
        field_sources: dict[str, dict[str, RawEvidenceRef]] | None = None,
    ) -> "DesignSnapshot":
        records = tuple(records)
        payload = json.dumps(
            [record.semantic_dict() for record in records],
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return cls(
            artifact_id=artifact_id,
            revision=revision,
            records=records,
            payload_bytes=payload,
            sha256=hashlib.sha256(payload).hexdigest(),
            evidence=tuple(evidence),
            field_sources=field_sources or {},
        )

    def project(self, status: str) -> "DesignSnapshot":
        if status not in {"DRAFT", "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED"}:
            raise ValueError("unsupported Test Design review projection")
        return replace(self, records=tuple(replace(row, review_status=status) for row in self.records))


@dataclass(frozen=True)
class NormalizationResult:
    status: str
    snapshot: DesignSnapshot | None
    findings: tuple[Finding, ...]


@dataclass(frozen=True)
class ValidatorResult:
    status: str
    findings: tuple[Finding, ...]
    artifact_id: str
    artifact_revision: str
    artifact_sha256: str


@dataclass(frozen=True)
class DesignWorkflowState:
    state: str
    artifact_id: str
    artifact_revision: str
    artifact_sha256: str
    review_status: str
    validation_status: str


@dataclass(frozen=True)
class AuthenticatedHumanActorContext:
    actor_id: str
    actor_role: str = "HUMAN"


@dataclass(frozen=True)
class DecisionAttempt:
    accepted: bool
    state: DesignWorkflowState
    finding: Finding | None = None
    reviewed_snapshot: DesignSnapshot | None = None
    next_snapshot: DesignSnapshot | None = None
    receipt_bytes: bytes | None = None
    receipt_sha256: str | None = None


def _field(fields: dict, path: str) -> str | None:
    return fields.get(tuple(path.split(".")))


def _source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pinned_tea_skill(skill_dir: str | Path) -> list[dict]:
    skill_dir = Path(skill_dir).resolve()
    manifest_bytes = TEA_PIN_MANIFEST.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != TEA_PIN_MANIFEST_SHA256:
        raise RuntimeError("TEA pin manifest bytes do not match the reviewed V1 manifest")
    manifest = json.loads(manifest_bytes.decode("utf-8"))
    if (
        manifest.get("repository") != TEA_REPOSITORY
        or manifest.get("commit") != TEA_COMMIT
        or manifest.get("capability") != TEA_CAPABILITY
        or not isinstance(manifest.get("files"), dict)
        or not manifest["files"]
    ):
        raise RuntimeError("TEA pin manifest does not identify the approved capability revision")
    expected = manifest["files"]
    if any(not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts for path in expected):
        raise RuntimeError("TEA pin manifest contains an invalid runtime path")
    actual_paths = {
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*") if path.is_file()
    }
    if actual_paths != set(expected):
        missing = sorted(set(expected) - actual_paths)
        extra = sorted(actual_paths - set(expected))
        raise RuntimeError(f"PIN_INTEGRITY_FAILURE: TEA runtime tree mismatch; missing={missing}; extra={extra}")
    inventory = []
    for relative, digest in expected.items():
        path = skill_dir / relative
        actual = _source_hash(path)
        if actual != digest:
            raise RuntimeError(
                f"PIN_INTEGRITY_FAILURE: TEA file={relative}; expected_sha256={digest}; "
                f"actual_sha256={actual}; pinned_commit={TEA_COMMIT}"
            )
        inventory.append({"path": relative, "sha256": actual})
    if expected.get("SKILL.md") != TEA_SKILL_SHA256:
        raise RuntimeError("TEA workflow entrypoint hash disagrees with the approved pin")
    return inventory


def _markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _source_id_matches(value: str, id_prefix: str) -> bool:
    return bool(re.fullmatch(rf"{id_prefix}-(?:[A-Za-z0-9]+-)*\d+", value, re.IGNORECASE))


def _parse_source_rows(path: Path, id_prefix: str, wanted_columns: int) -> tuple[BaselineRow, ...]:
    """Accept legacy source tables and current BA Kit heading-based artifacts."""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[BaselineRow] = []

    for number, raw in enumerate(lines, 1):
        if not raw.lstrip().startswith("|") or TABLE_SEPARATOR.fullmatch(raw.strip()):
            continue
        cells = _markdown_cells(raw)
        if not cells or not _source_id_matches(cells[0], id_prefix):
            continue
        if len(cells) != wanted_columns:
            raise BaselineError(f"{path}:{number}: expected {wanted_columns} source columns, found {len(cells)}")
        if not cells[1]:
            raise BaselineError(f"{path}:{number}: {cells[0]} has no source text")
        rows.append(BaselineRow(cells[0], cells[1], str(path), number))

    for index, raw in enumerate(lines):
        match = SOURCE_HEADING.match(raw)
        if not match or not _source_id_matches(match.group("id"), id_prefix):
            continue
        source_id = match.group("id")
        heading_depth = len(match.group("marks"))
        body: list[str] = []
        cursor = index + 1
        while cursor < len(lines):
            next_heading = MARKDOWN_HEADING.match(lines[cursor])
            if next_heading and len(next_heading.group(1)) <= heading_depth:
                break
            body.append(lines[cursor])
            cursor += 1
        title = match.group("title").strip()
        section = "\n".join(body).strip()
        text = "\n\n".join(part for part in (title, section) if part).strip()
        if not text:
            raise BaselineError(f"{path}:{index + 1}: {source_id} has no source text")
        rows.append(BaselineRow(source_id, text, str(path), index + 1))

    if not rows:
        raise BaselineError(f"{path}: no {id_prefix}-* source rows found")
    folded = [row.id.casefold() for row in rows]
    if len(folded) != len(set(folded)):
        raise BaselineError(f"{path}: duplicate {id_prefix} source IDs")
    return tuple(rows)

def _parse_open_items(fields: dict, sequences: dict) -> tuple[str, ...]:
    raw = _field(fields, "open_items.non_blocking")
    if raw and raw.startswith("["):
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as error:
            raise BaselineError(f"unsupported open_items.non_blocking list: {error}") from error
        if not isinstance(items, list) or not all(isinstance(item, str) for item in items):
            raise BaselineError("open_items.non_blocking must be a string list")
        return tuple(items)
    items = sequences.get(("open_items", "non_blocking"), [])
    if not all(isinstance(item, str) for item in items):
        raise BaselineError("open_items.non_blocking must be a string list")
    return tuple(items)


def _unknown_sentences(rows: Iterable[BaselineRow]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        for sentence in re.split(r"(?<=[.!?])\s+", row.text):
            sentence = sentence.strip()
            if re.search(r"\bUNKNOWN\b", sentence, re.IGNORECASE):
                result[row.id] = sentence
    return result


def load_approved_baseline(handoff_path: str | Path) -> ApprovedBaseline:
    handoff_path = Path(handoff_path).resolve()
    errors = validate_handoff_file(handoff_path)
    if errors:
        raise BaselineError("; ".join(errors))
    fields, _, sequences, parse_errors = _yaml_fields(handoff_path.read_text(encoding="utf-8"))
    if parse_errors:
        raise BaselineError("; ".join(parse_errors))
    if _field(fields, "ba_baseline.status") != "APPROVED_FOR_ENGINEERING":
        raise BaselineError("ba_baseline.status must be APPROVED_FOR_ENGINEERING")

    source_paths: dict[str, Path] = {}
    source_hashes: dict[str, str] = {}
    for source in ("business_rules", "srs", "decisions"):
        relative = _field(fields, f"authoritative_sources.{source}.path")
        expected = (_field(fields, f"authoritative_sources.{source}.sha256") or "").lower()
        path = Path(relative)
        if not path.is_absolute():
            path = handoff_path.parent / path
        path = path.resolve()
        if not path.is_file() or _source_hash(path) != expected:
            raise BaselineError(f"authoritative source missing or SHA-256 mismatch: {source}: {path}")
        source_paths[source] = path
        source_hashes[source] = expected

    requirements = _parse_source_rows(source_paths["srs"], "FR", 3)
    business_rules = _parse_source_rows(source_paths["business_rules"], "BR", 3)
    rows = (*requirements, *business_rules)
    return ApprovedBaseline(
        feature_id=_field(fields, "feature.id") or "",
        feature_title=_field(fields, "feature.title") or "",
        revision=_field(fields, "ba_baseline.revision") or "",
        handoff_path=handoff_path,
        handoff_sha256=_source_hash(handoff_path),
        source_paths=source_paths,
        source_hashes=source_hashes,
        requirements=requirements,
        business_rules=business_rules,
        open_items=_parse_open_items(fields, sequences),
        unknown_clauses=_unknown_sentences(rows),
    )


def _heading_markdown(title: str, rows: Iterable[BaselineRow]) -> str:
    lines = [title, ""]
    for row in rows:
        lines.extend((f"### {row.id}", "", row.text, ""))
    return "\n".join(lines).rstrip() + "\n"


def adapt_ba_to_tea(
    handoff_path: str | Path,
    *,
    supplemental: str | None = None,
    supplemental_source: RawEvidenceRef | None = None,
) -> AdapterBundle:
    baseline = load_approved_baseline(handoff_path)
    epic = _heading_markdown(f"# Epic 1 — {baseline.feature_id} {baseline.feature_title}", baseline.requirements)
    epic = epic.replace("\n### FR-", "\n## Acceptance criteria\n\n### FR-", 1)
    business = _heading_markdown("# Separate approved business-rule context", baseline.business_rules)
    unknown_texts = tuple(baseline.unknown_clauses.values())
    open_lines = ["# BA open decisions — UNKNOWN", ""]
    for item in baseline.open_items:
        open_lines.extend((f"- {item}",))
    open_lines.extend(("", "## Source clauses", ""))
    for source_id, clause in baseline.unknown_clauses.items():
        open_lines.extend((f"- {source_id}: {clause}",))
    return AdapterBundle(
        baseline=baseline,
        requirements=baseline.requirements,
        business_rules=baseline.business_rules,
        open_items=baseline.open_items,
        unknown_texts=unknown_texts,
        epic_markdown=epic,
        business_rules_markdown=business,
        open_decisions_markdown="\n".join(open_lines).rstrip() + "\n",
        supplemental_text=supplemental,
        supplemental_source=supplemental_source,
    )


def _parse_ref_cell(value: str, inventory: set[str], *, path: str, line: int, field: str) -> list[str]:
    tokens: list[tuple[int, int, list[str]]] = []
    covered: list[tuple[int, int]] = []
    for match in RANGE_TOKEN.finditer(value):
        prefix = match.group("prefix")
        if prefix not in {"FR", "BR"}:
            raise _normalize_error(path, line, field, "range prefix spelling must match canonical BA IDs")
        end_prefix = match.group("end_prefix")
        if end_prefix and end_prefix != prefix:
            raise _normalize_error(path, line, field, "range endpoints use different ID types")
        start_token = f"{prefix}-{match.group('start')}"
        end_token = f"{prefix}-{match.group('end')}"
        if start_token not in inventory:
            raise _normalize_error(path, line, field, f"range start is absent from the approved BA inventory: {start_token}")
        if end_token not in inventory:
            raise _normalize_error(path, line, field, f"range end is absent from the approved BA inventory: {end_token}")
        start, end = int(match.group("start")), int(match.group("end"))
        if start > end:
            raise _normalize_error(path, line, field, "range is reversed")
        width = max(len(match.group("start")), len(match.group("end")))
        expanded = [f"{prefix}-{number:0{width}d}" for number in range(start, end + 1)]
        if any(item not in inventory for item in expanded):
            missing = next(item for item in expanded if item not in inventory)
            raise _normalize_error(path, line, field, f"range member is absent from the approved BA inventory: {missing}")
        tokens.append((match.start(), match.end(), expanded))
        covered.append(match.span())
    inventory_by_fold = {item.casefold(): item for item in inventory}
    for match in BA_ID_TOKEN.finditer(value):
        if any(start <= match.start() and match.end() <= end for start, end in covered):
            continue
        raw_id = match.group("id")
        canonical_id = inventory_by_fold.get(raw_id.casefold())
        if canonical_id is None:
            raise _normalize_error(path, line, field, f"BA ID is absent from the approved inventory: {raw_id}")
        tokens.append((match.start(), match.end(), [canonical_id]))
        covered.append(match.span())
    tokens.sort(key=lambda item: item[0])
    if not tokens:
        raise _normalize_error(path, line, field, "no explicit FR/BR IDs found")
    remainder = list(value)
    for start, end in covered:
        remainder[start:end] = " " * (end - start)
    leftovers = "".join(remainder)
    if BAD_BA_ID_TOKEN.search(leftovers):
        bad = BAD_BA_ID_TOKEN.search(leftovers).group(0)
        raise _normalize_error(path, line, field, f"ambiguous or malformed ID token: {bad}")
    if re.sub(r"\b(?:and|or|và|hoặc)\b", "", leftovers, flags=re.IGNORECASE).strip(" \t,;:/|&()[]·—–-"):
        raise _normalize_error(path, line, field, "unparsed text makes the trace ambiguous")
    return [token for _, _, expanded in tokens for token in expanded]


def _normalize_error(path: str, line: int, field: str, message: str) -> Finding:
    return _NormalizationError(Finding("CANNOT_NORMALIZE", message, path, line, field))


def _unknown_for_row(
    refs: list[str], title: str, expected: str, baseline: ApprovedBaseline, *, path: str, line: int
) -> tuple[OpenQuestion, ...]:
    text = f"{title} {expected}".casefold()
    open_questions: list[OpenQuestion] = []
    for ref in refs:
        clause = baseline.unknown_clauses.get(ref)
        if not clause:
            continue
        clause_lower = clause.casefold()
        max_question = "maximum" in clause_lower or "tối đa" in clause_lower
        list_question = any(word in clause_lower for word in ("filter", "sort", "pagination", "lọc", "sắp xếp", "phân trang"))
        if max_question:
            mentioned = "upper-bound" in text or "upper bound" in text or "cận trên" in text or bool(re.search(
                r"(?:maximum|max|tối đa).{0,50}(?:duration|thời lượng)|(?:duration|thời lượng).{0,50}(?:maximum|max|tối đa)", text
            ))
        elif list_question:
            mentioned = any(word in text for word in ("filter", "sort", "order", "pagination", "page size", "lọc", "sắp xếp", "phân trang"))
        else:
            mentioned = False
        if mentioned:
            question = OpenQuestion(ref, clause)
            if question not in open_questions:
                open_questions.append(question)
    explicit_unknown = expected.strip().casefold() == "unknown"
    explicit_deferred = _scenario_outcome_is_deferred(title, expected) or explicit_unknown or any(
        marker in expected.casefold()
        for marker in ("blocked", "deferred", "chưa chọn", "chưa xác định", "chờ ba", "ba quyết định")
    )
    if explicit_deferred and not open_questions:
        candidates = [baseline.unknown_clauses[ref] for ref in refs if ref in baseline.unknown_clauses]
        unique = list(dict.fromkeys(candidates))
        if len(unique) == 1:
            ref = next(ref for ref in refs if ref in baseline.unknown_clauses)
            open_questions.append(OpenQuestion(ref, unique[0]))
        elif not unique:
            raise _normalize_error(path, line, "Kết quả quan sát được", "deferred outcome has no matching BA UNKNOWN")
        else:
            raise _normalize_error(path, line, "Kết quả quan sát được", "deferred outcome matches multiple BA UNKNOWN clauses")
    return tuple(open_questions)


def _leaks_unknown_answer(record: CanonicalTestDesign, baseline: ApprovedBaseline) -> bool:
    outcome = record.expected_behavior or ""
    lowered = outcome.casefold()
    for question in record.open_questions:
        source = baseline.unknown_clauses.get(question.source_ref, "").casefold()
        if ("maximum" in source or "tối đa" in source) and re.search(
            r"(?:maximum|max|tối đa).{0,40}(?:duration|thời lượng).{0,24}\d+|\d+.{0,24}(?:minute|hour|day|phút|giờ|ngày).{0,40}(?:maximum|max|tối đa)",
            lowered,
        ):
            return True
        if any(word in source for word in ("filter", "sort", "pagination")):
            policies = (
                r"filter(?:ed)?\s+by\s+\w+", r"sort(?:ed)?\s+by\s+\w+", r"order(?:ed)?\s+by\s+\w+",
                r"default sorting.{0,24}(?:asc|desc|by)", r"page size\s*(?:is|=|:)?\s*\d+",
                r"lọc theo\s+\w+", r"sắp xếp theo\s+\w+", r"page size\s*\d+",
            )
            if any(re.search(policy, lowered) for policy in policies):
                return True
    return False


def _expected_is_deferred(value: str) -> bool:
    lowered = value.casefold()
    return value.strip().casefold() == "unknown" or any(
        marker in lowered for marker in ("blocked", "deferred", "chưa chọn", "chưa xác định", "chờ ba", "ba quyết định")
    )


def _scenario_outcome_is_deferred(title: str, expected: str) -> bool:
    if _expected_is_deferred(expected):
        return True
    text = f"{title} {expected}".casefold()
    return bool(
        re.search(r"\b(?:awaiting|awaits|pending|waiting)\b.{0,80}\b(?:ba|clarification|decision|business rule)\b", text)
        or re.search(r"\bchờ\b.{0,80}\b(?:ba|quyết định|làm rõ)\b", text)
        or re.search(r"\b(?:conditional(?:ly)? on|subject to|depends solely on)\b.{0,80}\b(?:unresolved|unknown|pending|awaiting|ba|business rule|clarification|decision)\b", text)
        or re.search(r"\bno\b.{0,40}\b(?:result|outcome|threshold)\b.{0,80}\b(?:unresolved|unknown|awaiting|pending|ba|clarification|decision)\b", text)
    )


def _tea_noncanonical_metadata_line(line: str, section: str | None, known_scenario_ids: set[str]) -> bool:
    ids = [match.group(0) for match in TEA_SCENARIO_TOKEN.finditer(line)]
    known_refs_only = all(token in known_scenario_ids for token in ids)
    if _tea_scenario_shaped_structure(line):
        return False
    if re.match(r"^\s*\*\*Verification:\*\*", line):
        return known_refs_only
    if re.match(r"^\s*\*\*Kế hoạch bao phủ:\*\*", line):
        return ids == ["1-INT-001"] and "Test ID theo profile epic-level" in line
    if section is not None and section.casefold() in {"nfr planning", "traceability matrix"} and line.lstrip().startswith("|"):
        return known_refs_only
    if (
        section in {
            "Ngoài phạm vi", "Ngoài phạm vi của bản Test Design này", "Truy vết FR/BR tới scenario",
        }
        and line.lstrip().startswith("|")
    ):
        return known_refs_only
    if section is not None and (
        section.casefold() in {
            "entry / exit criteria", "entry criteria", "assumptions and dependencies", "risk to the plan",
        }
        or section.casefold().startswith("exit criteria")
    ):
        return known_refs_only
    if (
        section is not None
        and section.casefold() == "quyết định ba còn mở"
        and re.match(r"^\s*Các hàng\b", line, re.IGNORECASE)
    ):
        return bool(ids) and known_refs_only and bool(re.search(r"\b(?:deferred|UNKNOWN)\b", line, re.IGNORECASE))
    if section is not None and section.casefold() == "assumptions and open decisions" and re.match(r"^\s*\d+\.\s+", line):
        return known_refs_only
    return section == "Dependencies" and known_refs_only and bool(
        re.match(r"^\s*\d+\.\s+", line) and re.search(r"required before executing", line, re.IGNORECASE)
    )


def _tea_scenario_shaped_structure(line: str) -> bool:
    candidate = line.strip()
    heading = MARKDOWN_HEADING.match(candidate)
    if heading:
        candidate = heading.group(2).strip()
    if candidate.startswith("|"):
        cells = _markdown_cells(candidate)
        return len(cells) > 1 and bool(TEA_SCENARIO_TOKEN.fullmatch(cells[0])) and bool(cells[1])
    list_item = bool(re.match(r"^(?:[-*]\s+|\d+[.)]\s+)", candidate))
    candidate = re.sub(r"^(?:[-*]\s+|\d+[.)]\s+)", "", candidate)
    scenario = TEA_SCENARIO_TOKEN.match(candidate)
    if scenario and list_item:
        return True
    return bool(scenario and re.match(r"\s*(?:[—–:-]|\|)\s*\S", candidate[scenario.end():]))


def _validate_tea_scenario_consumption(
    markdown: str,
    header: tuple[str, ...],
    rows: list[tuple[list[str], tuple[str, ...], int]],
    source_path: str,
) -> None:
    consumed: dict[int, list[str]] = {}
    for cells, _hierarchy, line in rows:
        design_id = _scenario_values(header, cells, source_path, line)[0]
        consumed.setdefault(line, []).extend(match.group(0) for match in TEA_SCENARIO_TOKEN.finditer(design_id))
    known_scenario_ids = {token for tokens in consumed.values() for token in tokens}

    section = None
    for number, raw in enumerate(markdown.splitlines(), 1):
        heading = MARKDOWN_HEADING.match(raw)
        if heading:
            section = heading.group(2).strip()
        actual = [match.group(0) for match in TEA_SCENARIO_TOKEN.finditer(raw)]
        if not actual or _tea_noncanonical_metadata_line(raw, section, known_scenario_ids):
            continue
        if actual != consumed.get(number, []):
            raise _normalize_error(
                source_path, number, "scenario",
                f"unconsumed scenario-shaped content in section {section or '<document>'}: {raw.strip()[:180]}",
            )


def _profile_rows(markdown: str, source_path: str) -> tuple[tuple[str, ...], list[tuple[list[str], tuple[str, ...], int]]]:
    lines = markdown.splitlines()
    title_match = next((MARKDOWN_HEADING.match(line) for line in lines if MARKDOWN_HEADING.match(line) and len(MARKDOWN_HEADING.match(line).group(1)) == 1), None)
    if not title_match:
        raise _normalize_error(source_path, 1, "hierarchy_path", "missing document title heading")
    headings: list[tuple[int, str]] = []
    in_plan = False
    seen_plan = 0
    current_header: tuple[str, ...] | None = None
    expected_columns: tuple[str, ...] | None = None
    rows: list[tuple[list[str], tuple[str, ...], int]] = []
    table_open = False
    priorities: set[str] = set()

    for number, raw in enumerate(lines, 1):
        heading = MARKDOWN_HEADING.match(raw)
        if heading:
            depth, text = len(heading.group(1)), heading.group(2).strip()
            if depth == 2 and text == "Test Coverage Plan":
                seen_plan += 1
                in_plan = True
                headings = [(1, title_match.group(2).strip()), (2, text)]
                table_open = False
                continue
            if in_plan and depth <= 2:
                in_plan = False
                table_open = False
            elif in_plan:
                while headings and headings[-1][0] >= depth:
                    headings.pop()
                headings.append((depth, text))
                priority = re.search(r"\bP([0-3])\b", text)
                if priority:
                    priorities.add("P" + priority.group(1))
                table_open = False
            continue
        if not in_plan:
            continue
        if not raw.strip().startswith("|"):
            if re.match(r"^TD-[A-Za-z0-9_-]+\b", raw.strip()):
                raise _normalize_error(source_path, number, "scenario", "unconsumed TD-shaped content inside Test Coverage Plan")
            continue
        if TABLE_SEPARATOR.fullmatch(raw.strip()):
            continue
        cells = _markdown_cells(raw)
        if not table_open:
            header = tuple(cells)
            if header not in (BENCHMARK_HEADERS, NATIVE_HEADERS):
                raise _normalize_error(source_path, number, "header", f"unknown Test Coverage Plan table header ({len(header)} columns)")
            if expected_columns is not None and expected_columns != header:
                raise _normalize_error(source_path, number, "header", "multiple raw profiles in one document")
            expected_columns = header
            current_header = header
            table_open = True
            continue
        if current_header is None or expected_columns is None:
            continue
        if len(cells) != len(current_header):
            raise _normalize_error(source_path, number, "row", f"expected {len(current_header)} cells, found {len(cells)}")
        # A row that starts a nested table without a heading is an unknown raw shape.
        if tuple(cells) in (BENCHMARK_HEADERS, NATIVE_HEADERS):
            raise _normalize_error(source_path, number, "header", "unexpected repeated table header")
        priority_heading = next((text for depth, text in reversed(headings) if re.search(r"\bP[0-3]\b", text)), None)
        if priority_heading is None:
            raise _normalize_error(source_path, number, "hierarchy_path", "scenario is not under a P0-P3 heading")
        path = tuple(text for _, text in headings)
        rows.append((cells, path, number))
    if seen_plan != 1:
        raise _normalize_error(source_path, 1, "Test Coverage Plan", "expected exactly one Test Coverage Plan heading")
    if expected_columns is None or not rows:
        raise _normalize_error(source_path, 1, "Test Coverage Plan", "no recognized scenario table found")
    if priorities != {"P0", "P1", "P2", "P3"}:
        raise _normalize_error(source_path, 1, "priority headings", "expected P0, P1, P2, and P3 headings")
    return expected_columns, rows


def _scenario_values(header: tuple[str, ...], cells: list[str], path: str, line: int):
    values = dict(zip(header, cells))
    if header == BENCHMARK_HEADERS:
        match = re.fullmatch(r"(TD-\d+)\s*(?:—|–|-)\s*(.+)", values["Scenario"])
        if not match:
            raise _normalize_error(path, line, "Scenario", "expected explicit TD ID followed by a title")
        design_id, title = match.group(1), match.group(2).strip()
        trace_field, observable_field = "Requirement", "Observable expected result"
    else:
        design_id = values["Test ID"]
        title = values["Kịch bản"]
        if not design_id or design_id.strip().casefold() in {"—", "–", "-", "none", "n/a", "unknown"}:
            raise _normalize_error(path, line, "Test ID", "scenario ID is empty or a placeholder")
        trace_field, observable_field = "Truy vết", "Kết quả quan sát được"
    if not title:
        raise _normalize_error(path, line, "scenario_title", "scenario title is empty")
    if not values[trace_field]:
        raise _normalize_error(path, line, trace_field, "required trace field is empty")
    if not values[observable_field]:
        raise _normalize_error(path, line, observable_field, "observable result is missing without an explicit UNKNOWN")
    return design_id, title, values[trace_field], values[observable_field], trace_field, observable_field


def normalize_tea_markdown(
    markdown: str,
    baseline: ApprovedBaseline,
    *,
    source_path: str = "<memory>",
    artifact_id: str | None = None,
    revision: str = "1",
) -> NormalizationResult:
    try:
        header, rows = _profile_rows(markdown, source_path)
        _validate_tea_scenario_consumption(markdown, header, rows, source_path)
        records: list[CanonicalTestDesign] = []
        field_sources: dict[str, dict[str, RawEvidenceRef]] = {}
        file_digest = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
        evidence = (RawEvidenceRef(source_path, file_digest),)
        for cells, hierarchy, line in rows:
            design_id, title, trace, expected, trace_field, observable_field = _scenario_values(header, cells, source_path, line)
            refs = _parse_ref_cell(trace, baseline.ba_ids, path=source_path, line=line, field=trace_field)
            questions = _unknown_for_row(refs, title, expected, baseline, path=source_path, line=line)
            is_null = _scenario_outcome_is_deferred(title, expected)
            behavior = None if is_null else expected
            if behavior is None and not questions:
                raise _normalize_error(source_path, line, observable_field, "deferred outcome has no explicit linked UNKNOWN")
            record = CanonicalTestDesign(
                design_id=design_id,
                hierarchy_path=hierarchy,
                scenario_title=title,
                expected_behavior=behavior,
                requirement_refs=tuple(refs),
                open_questions=questions,
            )
            records.append(record)
            row_ref = RawEvidenceRef(source_path, file_digest, line, "scenario row")
            field_sources[design_id] = {field: row_ref for field in RECORD_FIELDS}
            field_sources[design_id]["requirement_refs"] = RawEvidenceRef(source_path, file_digest, line, trace_field)
            field_sources[design_id]["expected_behavior"] = RawEvidenceRef(source_path, file_digest, line, observable_field)
        found_unknown_ids = {question.source_ref for row in records for question in row.open_questions}
        needed_unknown_ids = set(baseline.unknown_clauses)
        if not needed_unknown_ids.issubset(found_unknown_ids):
            missing = sorted(needed_unknown_ids - found_unknown_ids)
            # Duplicate FR/BR statements may describe the same UNKNOWN; require one exact source-linked record.
            for source_id in missing:
                clause = baseline.unknown_clauses[source_id].casefold()
                equivalent = next((qid for qid in found_unknown_ids if baseline.unknown_clauses.get(qid, "").casefold() == clause), None)
                if equivalent is None:
                    raise _normalize_error(source_path, 1, "open_questions", f"BA UNKNOWN clause was not located in a scenario: {source_id}")
        snapshot = DesignSnapshot.create(
            records,
            artifact_id=artifact_id or f"{baseline.feature_id}-test-design",
            revision=revision,
            evidence=evidence,
            field_sources=field_sources,
        )
        return NormalizationResult("NORMALIZED", snapshot, ())
    except _NormalizationError as error:
        return NormalizationResult("CANNOT_NORMALIZE", None, (error.finding,))


def normalize_tea_output(
    path: str | Path,
    baseline: ApprovedBaseline,
    *,
    artifact_id: str | None = None,
    revision: str = "1",
) -> NormalizationResult:
    path = Path(path)
    raw = path.read_bytes()
    try:
        markdown = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        finding = Finding("CANNOT_NORMALIZE", f"raw output is not valid UTF-8: {error}", str(path), None, "encoding")
        return NormalizationResult("CANNOT_NORMALIZE", None, (finding,))
    return normalize_tea_markdown(
        markdown, baseline, source_path=str(path), artifact_id=artifact_id, revision=revision
    )


def _record_findings(snapshot: DesignSnapshot, baseline: ApprovedBaseline) -> list[Finding]:
    findings: list[Finding] = []
    if not snapshot.records:
        findings.append(Finding("EMPTY_DESIGN", "canonical Test Design collection is empty"))
    ids: set[str] = set()
    covered: set[str] = set()
    preserved_unknowns: set[tuple[str, str]] = set()
    for record in snapshot.records:
        source = snapshot.field_sources.get(record.design_id, {}).get("design_id")
        if not isinstance(record.design_id, str) or not record.design_id.strip():
            findings.append(Finding("INVALID_DESIGN_ID", "design ID must be a nonempty upstream scenario ID", source.path if source else None, source.line if source else None, "design_id"))
        if record.design_id in ids:
            findings.append(Finding("DUPLICATE_TD_ID", f"duplicate design ID: {record.design_id}", source.path if source else None, source.line if source else None, "design_id"))
        ids.add(record.design_id)
        if not record.hierarchy_path or any(not item.strip() for item in record.hierarchy_path):
            findings.append(Finding("INVALID_HIERARCHY", f"{record.design_id} has an empty hierarchy path", source.path if source else None, source.line if source else None, "hierarchy_path"))
        if not record.scenario_title.strip():
            findings.append(Finding("INVALID_TITLE", f"{record.design_id} has an empty title", source.path if source else None, source.line if source else None, "scenario_title"))
        if record.expected_behavior is not None and not record.expected_behavior.strip():
            findings.append(Finding("INVALID_EXPECTED_BEHAVIOR", f"{record.design_id} has an empty expected behavior", source.path if source else None, source.line if source else None, "expected_behavior"))
        if record.expected_behavior is not None and _scenario_outcome_is_deferred(record.scenario_title, record.expected_behavior):
            findings.append(Finding("DEFERRED_OUTCOME_NOT_NULL", f"{record.design_id} marks a deferred BA outcome as an active assertion", source.path if source else None, source.line if source else None, "expected_behavior"))
        if record.expected_behavior is None and not record.open_questions:
            findings.append(Finding("UNKNOWN_OUTCOME_UNLINKED", f"{record.design_id} has a null outcome without an UNKNOWN", source.path if source else None, source.line if source else None, "open_questions"))
        if not record.requirement_refs:
            findings.append(Finding("MISSING_REQUIREMENT_REFS", f"{record.design_id} has no BA references", source.path if source else None, source.line if source else None, "requirement_refs"))
        if len(record.requirement_refs) != len(set(record.requirement_refs)):
            findings.append(Finding("DUPLICATE_REQUIREMENT_REF", f"{record.design_id} repeats a BA reference", source.path if source else None, source.line if source else None, "requirement_refs"))
        for ref in record.requirement_refs:
            if ref not in baseline.ba_ids:
                findings.append(Finding("ORPHAN_REQUIREMENT_REF", f"{record.design_id} references unknown BA ID {ref}", source.path if source else None, source.line if source else None, "requirement_refs"))
            else:
                covered.add(ref)
        for question in record.open_questions:
            if question.status != "UNKNOWN" or question.source_ref not in baseline.ba_ids:
                findings.append(Finding("INVALID_OPEN_QUESTION_REF", f"{record.design_id} has an invalid UNKNOWN reference {question.source_ref}", source.path if source else None, source.line if source else None, "open_questions"))
            elif baseline.unknown_clauses.get(question.source_ref) != question.text:
                findings.append(Finding("UNKNOWN_TEXT_DRIFT", f"{record.design_id} changed UNKNOWN text for {question.source_ref}", source.path if source else None, source.line if source else None, "open_questions"))
            else:
                preserved_unknowns.add((question.source_ref, question.text))
                covered.add(question.source_ref)
        if _leaks_unknown_answer(record, baseline):
            findings.append(Finding("UNKNOWN_ASSERTION_LEAK", f"{record.design_id} asserts a value for an unresolved BA question", source.path if source else None, source.line if source else None, "expected_behavior"))

    missing_refs = sorted(baseline.ba_ids - covered)
    for ref in missing_refs:
        findings.append(Finding("UNCOVERED_BA_REQUIREMENT", f"approved BA ID has no Test Design or explicit UNKNOWN: {ref}", field="requirement_refs"))
    for source_id, text in baseline.unknown_clauses.items():
        if source_id in covered and not any(question_text == text for _, question_text in preserved_unknowns):
            findings.append(Finding("UNKNOWN_NOT_PRESERVED", f"BA UNKNOWN was not preserved: {source_id}", field="open_questions"))
    return findings


def validate_design(
    snapshot: DesignSnapshot,
    baseline: ApprovedBaseline,
    *,
    explicit_authority_conflicts: Iterable[Finding] = (),
) -> ValidatorResult:
    findings = _record_findings(snapshot, baseline)
    try:
        baseline_receipt_refs(baseline)
    except (BaselineError, OSError) as error:
        findings.append(Finding("BA_BASELINE_STALE", str(error)))
    for row in snapshot.records:
        if set(row.to_dict()) != set(RECORD_FIELDS):
            findings.append(Finding("CANONICAL_SCHEMA_MISMATCH", f"{row.design_id} does not match the frozen field set"))
        if row.review_status not in {"DRAFT", "IN_REVIEW", "CHANGES_REQUESTED", "APPROVED"}:
            findings.append(Finding("INVALID_REVIEW_STATUS", f"{row.design_id} has an unsupported review status"))
    findings.extend(explicit_authority_conflicts)
    expected_payload = json.dumps(
        [record.semantic_dict() for record in snapshot.records],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if expected_payload != snapshot.payload_bytes:
        findings.append(Finding("SNAPSHOT_RECORD_MISMATCH", "canonical Test Design records do not match the immutable semantic bytes"))
    if hashlib.sha256(snapshot.payload_bytes).hexdigest() != snapshot.sha256:
        findings.append(Finding("SNAPSHOT_HASH_MISMATCH", "canonical snapshot payload hash does not match its bytes"))
    return ValidatorResult(
        "PASS" if not findings else "FAIL",
        tuple(findings),
        snapshot.artifact_id,
        snapshot.revision,
        snapshot.sha256,
    )


def start_design_workflow(snapshot: DesignSnapshot) -> DesignWorkflowState:
    return DesignWorkflowState("DRAFT_DESIGN", snapshot.artifact_id, snapshot.revision, snapshot.sha256, "DRAFT", "NOT_RUN")


def submit_design_for_review(
    state: DesignWorkflowState,
    snapshot: DesignSnapshot,
    validation: ValidatorResult,
) -> DesignWorkflowState:
    if state.state != "DRAFT_DESIGN":
        raise ValueError("only DRAFT_DESIGN can transition to DESIGN_REVIEW")
    if validation.status != "PASS":
        raise ValueError("DESIGN_REVIEW requires validator PASS")
    if (validation.artifact_id, validation.artifact_revision, validation.artifact_sha256) != (
        snapshot.artifact_id, snapshot.revision, snapshot.sha256
    ):
        raise ValueError("validation result is not bound to the exact immutable collection snapshot")
    if (state.artifact_id, state.artifact_revision, state.artifact_sha256) != (
        snapshot.artifact_id, snapshot.revision, snapshot.sha256
    ) or hashlib.sha256(snapshot.payload_bytes).hexdigest() != snapshot.sha256:
        raise ValueError("DESIGN_REVIEW requires the exact immutable collection snapshot")
    return DesignWorkflowState("DESIGN_REVIEW", snapshot.artifact_id, snapshot.revision, snapshot.sha256, "IN_REVIEW", "PASS")


def apply_design_decision(
    run_dir: str | Path,
    snapshot: DesignSnapshot,
    baseline: ApprovedBaseline,
    receipt: dict,
    *,
    human_actor_authenticator,
    validation: ValidatorResult | None = None,
    next_revision: str | None = None,
) -> DecisionAttempt:
    return _apply_design_decision(
        run_dir, snapshot, baseline, receipt,
        human_actor_authenticator=human_actor_authenticator,
        validation=validation, next_revision=next_revision,
    )


def apply_test_only_design_decision(
    run_dir: str | Path,
    snapshot: DesignSnapshot,
    baseline: ApprovedBaseline,
    fixture_path: str | Path,
    *,
    validation: ValidatorResult | None = None,
    next_revision: str | None = None,
) -> DecisionAttempt:
    fixture_path = Path(fixture_path).resolve()
    if not fixture_path.is_relative_to((ROOT / "benchmark").resolve()) and not is_test_only_workspace_path(fixture_path):
        return _design_decision_rejected(snapshot, "TEST_ONLY_FIXTURE_OUTSIDE_EVIDENCE", "TEST_ONLY design receipts must live under benchmark evidence or a temporary workspace")
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return _design_decision_rejected(snapshot, "INVALID_TEST_ONLY_FIXTURE", str(error))
    if (
        not isinstance(fixture, dict)
        or set(fixture) != {"fixture_type", "not_for_production", "receipt"}
        or fixture.get("fixture_type") != "TEST_ONLY_SIMULATED_HUMAN_DESIGN_GATE_RECEIPT"
        or fixture.get("not_for_production") is not True
    ):
        return _design_decision_rejected(snapshot, "INVALID_TEST_ONLY_FIXTURE", "fixture must be TEST_ONLY and not_for_production")
    receipt = fixture.get("receipt")
    if not isinstance(receipt, dict) or not str(receipt.get("actor_id", "")).startswith("TEST_ONLY:"):
        return _design_decision_rejected(snapshot, "INVALID_TEST_ONLY_FIXTURE", "fixture must identify a TEST_ONLY actor")
    return _apply_design_decision(
        run_dir, snapshot, baseline, receipt, human_actor_authenticator=None,
        validation=validation, next_revision=next_revision,
        test_only_fixture_path=fixture_path,
    )


def _apply_design_decision(
    run_dir: str | Path,
    snapshot: DesignSnapshot,
    baseline: ApprovedBaseline,
    receipt: dict,
    *,
    human_actor_authenticator,
    validation: ValidatorResult | None = None,
    next_revision: str | None = None,
    test_only_fixture_path: Path | None = None,
) -> DecisionAttempt:
    run_dir = Path(run_dir).resolve()
    workflow_path = run_dir / "workflow-state.json"
    try:
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return _design_decision_rejected(snapshot, "DESIGN_WORKFLOW_UNAVAILABLE", str(error))
    state = _design_state_from_workflow(workflow)
    if state.state != "DESIGN_REVIEW":
        return DecisionAttempt(False, state, Finding("INVALID_REVIEW_TRANSITION", "authoritative persisted state must be DESIGN_REVIEW"))
    if (state.artifact_id, state.artifact_revision, state.artifact_sha256) != (
        snapshot.artifact_id, snapshot.revision, snapshot.sha256,
    ):
        return DecisionAttempt(False, state, Finding("DESIGN_RECEIPT_BINDING_MISMATCH", "design snapshot is not the current persisted artifact"))
    semantic_path = run_dir / "canonical/semantic-payload.json"
    if not semantic_path.is_file() or semantic_path.read_bytes() != snapshot.payload_bytes:
        return DecisionAttempt(False, state, Finding("DESIGN_RECEIPT_BINDING_MISMATCH", "persisted semantic bytes do not match the reviewed design"))
    actual_hash = hashlib.sha256(snapshot.payload_bytes).hexdigest()
    if actual_hash != snapshot.sha256 or actual_hash != state.artifact_sha256:
        return DecisionAttempt(False, state, Finding("DESIGN_RECEIPT_BINDING_MISMATCH", "design semantic hash does not match persisted state"))

    finding = _design_receipt_shape_finding(receipt)
    if finding:
        return DecisionAttempt(False, state, finding)
    try:
        expected_refs = tuple((row["id"], row["revision"], row["sha256"]) for row in design_gate_input_refs(baseline, run_dir))
    except ProjectPolicyBindingError as error:
        return DecisionAttempt(False, state, Finding(error.code, str(error)))
    except (BaselineError, OSError) as error:
        return DecisionAttempt(False, state, Finding("BA_BASELINE_STALE", str(error)))
    actual_refs = _design_receipt_refs(receipt)
    if (
        receipt["artifact_id"] != snapshot.artifact_id
        or receipt["artifact_revision"] != snapshot.revision
        or receipt["artifact_sha256"].lower() != snapshot.sha256
        or actual_refs != expected_refs
    ):
        return DecisionAttempt(False, state, Finding("DESIGN_RECEIPT_BINDING_MISMATCH", "receipt is stale or does not bind current design and BA sources"))
    test_only = test_only_fixture_path is not None
    if receipt["actor_id"].startswith("TEST_ONLY:") != test_only:
        return DecisionAttempt(False, state, Finding("TEST_ONLY_RECEIPT_NOT_PRODUCTION", "TEST_ONLY decisions require the isolated acceptance path"))
    if test_only:
        if receipt["decision"] != "APPROVE":
            return DecisionAttempt(False, state, Finding("INVALID_TEST_ONLY_DECISION", "TEST_ONLY acceptance fixtures support approval only"))
    else:
        try:
            actor = human_actor_authenticator(receipt["actor_id"], receipt) if callable(human_actor_authenticator) else None
        except Exception:
            actor = None
        if (
            type(actor) is not AuthenticatedHumanActorContext
            or actor.actor_role != "HUMAN"
            or actor.actor_id != receipt["actor_id"]
        ):
            return DecisionAttempt(False, state, Finding("HUMAN_ACTOR_REQUIRED", "host did not authenticate the Human actor for this receipt"))

    current_validation = validate_design(snapshot, baseline)
    if (
        current_validation.status != "PASS"
        or validation is not None and (
            validation.status != "PASS"
            or (validation.artifact_id, validation.artifact_revision, validation.artifact_sha256)
            != (snapshot.artifact_id, snapshot.revision, snapshot.sha256)
        )
    ):
        return DecisionAttempt(False, state, Finding("DESIGN_VALIDATION_NOT_CURRENT", "Design Gate requires validators to PASS on this exact snapshot"))
    if receipt["decision"] == "REQUEST_CHANGES" and (
        not isinstance(next_revision, str) or not next_revision.strip() or next_revision == snapshot.revision
    ):
        return DecisionAttempt(False, state, Finding("INVALID_NEXT_REVISION", "REQUEST_CHANGES requires a distinct new design revision"))

    receipt_bytes = json.dumps(receipt, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    receipt_path = run_dir / "design-gate" / "revisions" / snapshot.revision / "receipt.json"
    if receipt_path.exists():
        return DecisionAttempt(False, state, Finding("RECEIPT_REPLAY", "a receipt was already consumed for this design revision"))
    try:
        _write_exclusive(receipt_path, receipt_bytes)
        receipt_ref = {"path": str(receipt_path), "sha256": receipt_sha256}
        history = list(workflow.get("history", []))
        if receipt["decision"] == "APPROVE":
            approved_projection = snapshot.project("APPROVED")
            projection_path = run_dir / "canonical/canonical-test-design-approved-projection.json"
            _write_exclusive(
                projection_path,
                (json.dumps([row.to_dict() for row in approved_projection.records], ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )
            next_state = DesignWorkflowState(
                "APPROVED_DESIGN", snapshot.artifact_id, snapshot.revision, snapshot.sha256,
                "APPROVED", "PASS",
            )
            history.append({"event": "HUMAN_APPROVE", "state": "APPROVED_DESIGN", "artifact_sha256": snapshot.sha256, "receipt_sha256": receipt_sha256})
            workflow.update({
                "state": next_state.state, "review_status": next_state.review_status,
                "validation_status": next_state.validation_status,
                "design_gate_receipt_mode": "TEST_ONLY" if test_only else "HUMAN_AUTHENTICATED",
                "design_gate_receipt_evidence": receipt_ref,
                "design_gate_test_only_fixture": (
                    {"path": str(test_only_fixture_path), "sha256": _source_hash(test_only_fixture_path)}
                    if test_only_fixture_path else None
                ),
            })
            _write_workflow_state_atomic(workflow_path, workflow, history)
            return DecisionAttempt(True, next_state, reviewed_snapshot=approved_projection, receipt_bytes=receipt_bytes, receipt_sha256=receipt_sha256)

        changed_projection = snapshot.project("CHANGES_REQUESTED")
        _write_exclusive(
            run_dir / "design-gate/revisions" / snapshot.revision / "canonical-test-design-changes-requested.json",
            (json.dumps([row.to_dict() for row in changed_projection.records], ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        next_snapshot = DesignSnapshot.create(
            snapshot.records, artifact_id=snapshot.artifact_id, revision=next_revision,
            evidence=snapshot.evidence, field_sources=snapshot.field_sources,
        )
        next_snapshot = next_snapshot.project("DRAFT")
        next_dir = run_dir / "revisions" / next_revision / "canonical"
        _write_exclusive(next_dir / "semantic-payload.json", next_snapshot.payload_bytes)
        _write_exclusive(
            next_dir / "canonical-test-design.json",
            (json.dumps([row.to_dict() for row in next_snapshot.records], ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        next_state = DesignWorkflowState(
            "DRAFT_DESIGN", next_snapshot.artifact_id, next_snapshot.revision,
            next_snapshot.sha256, "DRAFT", "NOT_RUN",
        )
        history.extend((
            {"event": "HUMAN_REQUEST_CHANGES", "state": "CHANGES_REQUESTED", "artifact_sha256": snapshot.sha256, "receipt_sha256": receipt_sha256},
            {"state": "DRAFT_DESIGN", "artifact_revision": next_revision, "artifact_sha256": next_snapshot.sha256},
        ))
        workflow.update({
            "state": next_state.state, "artifact_revision": next_state.artifact_revision,
            "artifact_sha256": next_state.artifact_sha256, "review_status": next_state.review_status,
            "validation_status": next_state.validation_status,
            "design_gate_receipt_mode": None, "design_gate_receipt_evidence": None,
            "derived_from": {"artifact_id": snapshot.artifact_id, "revision": snapshot.revision, "sha256": snapshot.sha256},
        })
        _write_workflow_state_atomic(workflow_path, workflow, history)
        return DecisionAttempt(
            True, next_state, reviewed_snapshot=changed_projection,
            next_snapshot=next_snapshot, receipt_bytes=receipt_bytes, receipt_sha256=receipt_sha256,
        )
    except OSError as error:
        return DecisionAttempt(False, state, Finding("DESIGN_GATE_PERSISTENCE_FAILED", str(error)))


def baseline_receipt_refs(baseline: ApprovedBaseline) -> list[dict]:
    refs = []
    for name in ("business_rules", "srs", "decisions"):
        actual = _source_hash(baseline.source_paths[name])
        if actual != baseline.source_hashes[name]:
            raise BaselineError(f"approved BA source changed after loading: {name}")
        refs.append({"id": f"BA:{name}", "revision": baseline.revision, "sha256": actual})
    handoff_hash = _source_hash(baseline.handoff_path)
    if handoff_hash != baseline.handoff_sha256:
        raise BaselineError("approved BA handoff changed after loading")
    refs.append({"id": "BA:handoff", "revision": baseline.revision, "sha256": handoff_hash})
    return refs


class ProjectPolicyBindingError(ValueError):
    def __init__(self, message: str, *, code: str = "PROJECT_POLICY_STALE"):
        super().__init__(message)
        self.code = code


def persist_project_policy_context(
    run_dir: str | Path, project_root: str | Path, stage: str, *, bootstrap_tea: bool = False,
) -> dict:
    """Bind a run to its project, including explicit no-policy compatibility."""
    from .test_kit_policy import persist_policy_snapshot, resolve_project_policy

    root = Path(project_root).resolve()
    run_dir = Path(run_dir).resolve()
    snapshot = resolve_project_policy(root, stage, bootstrap_tea=bootstrap_tea)
    context = {
        "project_root": str(root), "stage": stage,
        "status": "PROJECT_POLICY" if snapshot else "NO_PROJECT_POLICY",
        "policy": persist_policy_snapshot(snapshot, run_dir) if snapshot else None,
        "context_path": str(run_dir / "inputs/project-policy-context.json"),
    }
    _write_if_same_or_absent(
        Path(context["context_path"]),
        (json.dumps(context, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return context


def current_project_policy_ref(run_dir: str | Path, stage: str) -> dict | None:
    """Re-resolve policy at each gate; callers cannot omit the recorded project."""
    from .test_kit_policy import resolve_project_policy

    run_dir = Path(run_dir).resolve()
    path = run_dir / "inputs/project-policy-context.json"
    bindings = []
    for relative in ("workflow-state.json", "raw-output/invocation-manifest.json", "evidence/invocation-manifest.json", "evidence/input-manifest.json", "inputs/input-manifest.json"):
        anchor = run_dir / relative
        if anchor.is_file():
            try:
                value = json.loads(anchor.read_text(encoding="utf-8"))
                if "project_policy_context" in value:
                    bindings.append(value["project_policy_context"])
            except (OSError, ValueError, TypeError) as error:
                raise ProjectPolicyBindingError(f"policy binding metadata is unavailable: {relative}: {error}") from error
    if not path.is_file():
        if (run_dir / "inputs/project-policy").exists() or any(binding is not None for binding in bindings):
            raise ProjectPolicyBindingError("policy evidence exists without its run/project binding")
        return None  # V1 runs predate project-policy context.
    try:
        context = json.loads(path.read_text(encoding="utf-8"))
        if any(binding != context for binding in bindings):
            raise ValueError("review/invocation binding differs from the immutable policy run context")
        if (
            not isinstance(context, dict) or context.get("stage") != stage
            or context.get("context_path") != str(path)
            or not isinstance(context.get("project_root"), str)
        ):
            raise ValueError("invalid policy run context")
        snapshot = resolve_project_policy(context["project_root"], stage)
        evidence = context.get("policy")
        if snapshot is None:
            if evidence is not None or context.get("status") != "NO_PROJECT_POLICY":
                raise ValueError("project policy was removed after invocation/review")
            return None
        if not isinstance(evidence, dict) or context.get("status") != "PROJECT_POLICY" or evidence.get("policy_ref") != snapshot.ref:
            raise ValueError("project policy differs from the invocation/review snapshot")
        if [(r["logical_path"], r["sha256"]) for r in evidence["rules"]] != [(r.logical_path, r.sha256) for r in snapshot.rules]:
            raise ValueError("policy rule provenance differs from the ordered snapshot")
        snapshot_path = Path(evidence["snapshot_path"]).resolve()
        record = {"semantic_payload": json.loads(snapshot.payload_bytes), "semantic_payload_sha256": snapshot.sha256, "evidence": evidence}
        expected_bytes = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if not snapshot_path.is_relative_to(run_dir) or snapshot_path.read_bytes() != expected_bytes:
            raise ValueError("immutable policy snapshot evidence changed")
        for rule in evidence["rules"]:
            evidence_path = Path(rule["evidence_path"]).resolve()
            if not evidence_path.is_relative_to(run_dir) or _source_hash(evidence_path) != rule["sha256"]:
                raise ValueError("immutable policy rule evidence changed")
        tea = evidence.get("tea_customization")
        if tea:
            tea_path = Path(tea["evidence_path"]).resolve()
            if not tea_path.is_relative_to(run_dir) or _source_hash(tea_path) != tea["sha256"]:
                raise ValueError("immutable TEA customization evidence changed")
        return snapshot.ref
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ProjectPolicyBindingError(str(error), code=getattr(error, "code", "PROJECT_POLICY_STALE")) from error


def design_gate_input_refs(baseline: ApprovedBaseline, run_dir: str | Path) -> list[dict]:
    refs = baseline_receipt_refs(baseline)
    policy_ref = current_project_policy_ref(run_dir, "DESIGN")
    return refs + ([policy_ref] if policy_ref else [])


def _design_receipt_refs(receipt: dict) -> tuple[tuple[str, str, str], ...] | None:
    refs = receipt.get("input_refs")
    if not isinstance(refs, list):
        return None
    result = []
    for ref in refs:
        if not isinstance(ref, dict) or set(ref) != {"id", "revision", "sha256"}:
            return None
        if not all(isinstance(ref[key], str) and ref[key].strip() for key in ref):
            return None
        result.append((ref["id"], ref["revision"], ref["sha256"].lower()))
    if len(result) != len(set(result)):
        return None
    return tuple(result)


def _design_receipt_shape_finding(receipt: object) -> Finding | None:
    fields = {"gate", "decision", "artifact_id", "artifact_revision", "artifact_sha256", "input_refs", "actor_id", "actor_role", "decided_at", "feedback"}
    if not isinstance(receipt, dict):
        return Finding("INVALID_GATE_RECEIPT", "Design Gate requires a receipt object")
    if set(receipt) != fields:
        return Finding("INVALID_GATE_RECEIPT_SCHEMA", "receipt fields do not match the frozen schema")
    if receipt["gate"] != "DESIGN_REVIEW" or receipt["decision"] not in {"APPROVE", "REQUEST_CHANGES"}:
        return Finding("INVALID_GATE_RECEIPT", "Design Gate accepts only APPROVE or REQUEST_CHANGES")
    if receipt["actor_role"] != "HUMAN" or not isinstance(receipt["actor_id"], str) or not receipt["actor_id"].strip():
        return Finding("HUMAN_ACTOR_REQUIRED", "receipt must identify a Human actor")
    if not all(isinstance(receipt[key], str) and receipt[key].strip() for key in ("artifact_id", "artifact_revision")):
        return Finding("INVALID_GATE_RECEIPT", "artifact ID and revision must be nonempty strings")
    if not isinstance(receipt["artifact_sha256"], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", receipt["artifact_sha256"]):
        return Finding("INVALID_GATE_RECEIPT", "artifact_sha256 must be a SHA-256 digest")
    if _design_receipt_refs(receipt) is None:
        return Finding("INVALID_GATE_RECEIPT", "input_refs must contain unique {id, revision, sha256} records")
    try:
        decided_at = datetime.fromisoformat(receipt["decided_at"].replace("Z", "+00:00"))
    except (TypeError, ValueError, AttributeError):
        return Finding("INVALID_GATE_RECEIPT", "decided_at must be an ISO-8601 timestamp")
    if decided_at.tzinfo is None:
        return Finding("INVALID_GATE_RECEIPT", "decided_at must include a timezone")
    if not isinstance(receipt["feedback"], str) or receipt["decision"] == "REQUEST_CHANGES" and not receipt["feedback"].strip():
        return Finding("INVALID_GATE_RECEIPT", "REQUEST_CHANGES requires nonempty Human feedback")
    return None


def _design_state_from_workflow(workflow: dict) -> DesignWorkflowState:
    return DesignWorkflowState(
        workflow.get("state", "INVALID"), workflow.get("artifact_id", ""),
        workflow.get("artifact_revision", ""), workflow.get("artifact_sha256", ""),
        workflow.get("review_status", ""), workflow.get("validation_status", "NOT_RUN"),
    )


def _design_decision_rejected(snapshot: DesignSnapshot, code: str, message: str) -> DecisionAttempt:
    return DecisionAttempt(False, DesignWorkflowState(
        "INVALID", snapshot.artifact_id, snapshot.revision, snapshot.sha256, "IN_REVIEW", "NOT_RUN",
    ), Finding(code, message))


def _write_workflow_state_atomic(path: Path, workflow: dict, history: list) -> None:
    workflow["history"] = history
    content = (json.dumps(workflow, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix="workflow-state-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _write_exclusive(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(content)


def _completed_artifact_bytes(path: Path, checkpoint_path: Path | None = None) -> bytes | None:
    try:
        content = path.read_bytes()
        text = content.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if re.search(r"(?m)^workflowStatus:\s*['\"]?completed['\"]?\s*$", text):
        return content
    if checkpoint_path is None or not checkpoint_path.is_file():
        return None
    checkpoint = checkpoint_path.read_text(encoding="utf-8")
    complete = (
        re.search(r"(?m)^workflowStatus:\s*['\"]?completed['\"]?\s*$", checkpoint)
        and "step-05-generate-output" in checkpoint
    )
    profile_headers = {
        "| " + " | ".join(BENCHMARK_HEADERS) + " |",
        "| " + " | ".join(NATIVE_HEADERS) + " |",
    }
    headings = {f"### P{priority}" for priority in range(4)}
    if complete and "## Test Coverage Plan" in text and profile_headers.intersection(text.splitlines()):
        if headings.issubset(set(line.strip().split(" —", 1)[0].split(" (", 1)[0] for line in text.splitlines() if line.startswith("### P"))):
            return content
    return None


def persist_design_review(
    run_dir: str | Path,
    bundle: AdapterBundle,
    raw_tea_output: str | Path,
    snapshot: DesignSnapshot,
    validation: ValidatorResult,
    state: DesignWorkflowState,
    *,
    project_root: str | Path | None = None,
) -> None:
    run_dir = Path(run_dir).resolve()
    context_path = run_dir / "inputs/project-policy-context.json"
    if project_root is not None and not context_path.exists():
        persist_project_policy_context(run_dir, project_root, "DESIGN", bootstrap_tea=True)
    policy_ref = current_project_policy_ref(run_dir, "DESIGN")
    policy_context = json.loads(context_path.read_text(encoding="utf-8")) if context_path.is_file() else None
    identity = (snapshot.artifact_id, snapshot.revision, snapshot.sha256)
    if state.state != "DESIGN_REVIEW" or state.review_status != "IN_REVIEW" or validation.status != "PASS":
        raise ValueError("only validated DESIGN_REVIEW artifacts can be persisted")
    if (state.artifact_id, state.artifact_revision, state.artifact_sha256) != identity:
        raise ValueError("workflow state does not identify the canonical snapshot")
    if (validation.artifact_id, validation.artifact_revision, validation.artifact_sha256) != identity:
        raise ValueError("validator result does not identify the canonical snapshot")
    if hashlib.sha256(snapshot.payload_bytes).hexdigest() != snapshot.sha256:
        raise ValueError("canonical snapshot hash does not match its semantic payload")
    raw_path = Path(raw_tea_output)
    raw_bytes = raw_path.read_bytes()
    if snapshot.evidence and hashlib.sha256(raw_bytes).hexdigest() != snapshot.evidence[0].sha256:
        raise ValueError("raw TEA evidence changed after normalization")
    invocation_manifest = run_dir / "raw-output/invocation-manifest.json"
    manifest = None
    if invocation_manifest.is_file():
        manifest = json.loads(invocation_manifest.read_text(encoding="utf-8"))
        if manifest.get("status") != "ARTIFACT_COMPLETE" or manifest.get("artifact_sha256") != hashlib.sha256(raw_bytes).hexdigest():
            raise ValueError("invocation manifest is not bound to the preserved native artifact")
    evidence_dir = run_dir / "evidence"
    canonical_dir = run_dir / "canonical"
    input_refs = []
    for name, source in bundle.baseline.source_paths.items():
        input_refs.append({"name": name, "path": str(source), "revision": bundle.baseline.revision, "sha256": bundle.baseline.source_hashes[name]})
    input_refs.append({"name": "handoff", "path": str(bundle.baseline.handoff_path), "revision": bundle.baseline.revision, "sha256": _source_hash(bundle.baseline.handoff_path)})
    if policy_ref:
        input_refs.append(policy_ref)
    _write_exclusive(evidence_dir / "tea-raw-output.md", raw_bytes)
    _write_exclusive(canonical_dir / "semantic-payload.json", snapshot.payload_bytes)
    projection = snapshot.project("IN_REVIEW")
    _write_exclusive(
        canonical_dir / "canonical-test-design.json",
        (json.dumps([row.to_dict() for row in projection.records], ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    evidence_map = {
        design_id: {
            field: {"path": ref.path, "sha256": ref.sha256, "line": ref.line, "field": ref.field}
            for field, ref in mapping.items()
        }
        for design_id, mapping in snapshot.field_sources.items()
    }
    _write_exclusive(evidence_dir / "normalization-map.json", (json.dumps(evidence_map, ensure_ascii=False, indent=2) + "\n").encode())
    normalization_json = {
        "status": "NORMALIZED",
        "record_count": len(snapshot.records),
        "artifact_id": snapshot.artifact_id,
        "artifact_revision": snapshot.revision,
        "artifact_sha256": snapshot.sha256,
        "raw_evidence_path": str(raw_path),
        "raw_evidence_sha256": _source_hash(raw_path),
    }
    _write_exclusive(evidence_dir / "normalization-results.json", (json.dumps(normalization_json, ensure_ascii=False, indent=2) + "\n").encode())
    validation_json = {"status": validation.status, "findings": [finding.__dict__ for finding in validation.findings]}
    _write_exclusive(evidence_dir / "validator-results.json", (json.dumps(validation_json, ensure_ascii=False, indent=2) + "\n").encode())
    workflow_json = {
        "state": state.state,
        "artifact_id": state.artifact_id,
        "artifact_revision": state.artifact_revision,
        "artifact_sha256": state.artifact_sha256,
        "review_status": state.review_status,
        "validation_status": state.validation_status,
        "semantic_payload_encoding": "UTF-8 compact JSON; frozen field order; review_status excluded",
        "history": [
            {"state": "DRAFT_DESIGN", "review_status": "DRAFT"},
            {"event": "SUBMIT_FOR_DESIGN_REVIEW", "state": "DESIGN_REVIEW", "review_status": "IN_REVIEW", "artifact_sha256": state.artifact_sha256},
        ],
        "inputs": input_refs,
        "project_policy_context": policy_context,
    }
    _write_exclusive(run_dir / "workflow-state.json", (json.dumps(workflow_json, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if manifest is not None:
        manifest.update(
            {
                "completion_basis": manifest.get("completion_basis") or (
                    "upstream-workflowStatus-and-frozen-raw-profile"
                    if manifest.get("workflow_status") == "completed"
                    else "completed-native-artifact-and-frozen-profile"
                ),
                "normalization_status": "NORMALIZED",
                "canonical_artifact_id": snapshot.artifact_id,
                "canonical_artifact_revision": snapshot.revision,
                "canonical_artifact_sha256": snapshot.sha256,
                "validator_status": validation.status,
                "workflow_state": state.state,
                "review_status": state.review_status,
            }
        )
        invocation_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_if_same_or_absent(path: Path, content: bytes) -> None:
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError(f"refusing to overwrite different evidence: {path}")
        return
    _write_exclusive(path, content)


def _write_adapter_inputs(bundle: AdapterBundle, run_dir: Path) -> tuple[Path, Path, Path]:
    input_dir = run_dir / "inputs"
    baseline_dir = input_dir / "baseline"
    adapter_dir = input_dir / "adapter"
    for source in bundle.baseline.source_paths.values():
        name = source.name
        _write_if_same_or_absent(baseline_dir / name, source.read_bytes())
    _write_if_same_or_absent(input_dir / "baseline" / bundle.baseline.handoff_path.name, bundle.baseline.handoff_path.read_bytes())
    epic = adapter_dir / "epic-1.md"
    rules = adapter_dir / "business-rules.md"
    unknowns = adapter_dir / "open-decisions.md"
    _write_if_same_or_absent(epic, bundle.epic_markdown.encode("utf-8"))
    _write_if_same_or_absent(rules, bundle.business_rules_markdown.encode("utf-8"))
    _write_if_same_or_absent(unknowns, bundle.open_decisions_markdown.encode("utf-8"))
    if bundle.supplemental_text is not None:
        supplemental = "# CURRENT_SYSTEM / SUPPLEMENTAL\n\n" + bundle.supplemental_text.strip() + "\n"
        _write_if_same_or_absent(adapter_dir / "current-system-supplemental.md", supplemental.encode("utf-8"))
    return epic, rules, unknowns


def _invocation_prompt(epic: Path, rules: Path, unknowns: Path, raw_output: Path, supplemental: Path | None) -> str:
    supplemental_line = (
        f"- CURRENT_SYSTEM / SUPPLEMENTAL only: {supplemental}\n"
        if supplemental
        else "- No current-system evidence is supplied.\n"
    )
    return f"""$bmad-testarch-test-design

Invoke the installed project-local native skill bmad-testarch-test-design at the pinned upstream revision. Complete an epic-level Test Design for Epic 1. Do not read or copy the skill file to simulate execution.

Business authority and inputs:
- Structural epic wrapper (FR IDs and wording are copied from the approved SRS): {epic}
- Separate approved Business Rules context; do not merge BRs into FR acceptance criteria: {rules}
- BA open decisions and UNKNOWN clauses; preserve them without answering them: {unknowns}
{supplemental_line}- Approved baseline handoff and source files are under {epic.parent.parent / 'baseline'}; use only the SRS and Business Rules as business authority.

Keep the output in Vietnamese. Preserve every FR and BR ID and the source wording. Do not infer UI/API behavior or fill an UNKNOWN. Produce testability/risk analysis and Test Coverage Plan scenarios with explicit traceability and observable outcomes. TEA priorities, risk, level, count, effort, and thresholds are advisory only. Do not generate code/automation, run tests, export XMind/Excel, access TestOps, modify PetClinic source, or give a release verdict.
When an expected outcome is awaiting a BA decision or conditional solely on an unresolved BA business rule, keep it deferred: state explicitly that no result can be asserted while the BA decision awaits clarification. Do not turn that row into an executable pass/fail outcome.
Every scenario row, including deferred/UNKNOWN rows, needs a unique non-empty Test ID. For new rows, use the native profile's existing sequence convention; do not use a placeholder ID.
Use the native coverage heading exactly as `## Test Coverage Plan` and the four priority headings exactly as `### P0`, `### P1`, `### P2`, and `### P3`. Keep other narrative in Vietnamese.

For the Test Coverage Plan, use the already-approved native raw profile exactly: group rows under P0, P1, P2, P3 headings and use this six-column header without additions or renaming: `Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được`. Keep scenario title, explicit FR/BR trace, and observable outcome in their separate columns. Preserve the upstream Test ID spelling exactly; do not rename or renumber IDs.

The Trace cell must contain only exact FR/BR IDs separated by semicolons. Do not add labels, open-decision text, or prose there; preserve unresolved wording in the observable-outcome cell and link it by its exact BA ID.

Write the final Test Design to {raw_output}. Intermediate outputs must remain in that run's raw-output folder.
"""


def invoke_native_tea(
    bundle: AdapterBundle,
    run_dir: str | Path,
    *,
    petclinic_root: str | Path,
    skill_dir: str | Path,
    model: str = "gpt-6-luna",
    timeout_seconds: float = 300.0,
) -> dict:
    run_dir = Path(run_dir).resolve()
    petclinic_root = Path(petclinic_root).resolve()
    skill_dir = Path(skill_dir).resolve()
    skill_file = skill_dir / "SKILL.md"
    pinned_skill_files = verify_pinned_tea_skill(skill_dir)
    if not (petclinic_root / ".agents/skills" / TEA_CAPABILITY).resolve().samefile(skill_dir):
        raise RuntimeError("native TEA invocation must use the project-local pinned skill")
    project_config = petclinic_root / "_bmad/tea/config.yaml"
    if not project_config.is_file():
        raise RuntimeError(f"native TEA invocation requires its project configuration: {project_config}")
    project_config_sha256 = _source_hash(project_config)
    policy_context = persist_project_policy_context(run_dir, petclinic_root, "DESIGN", bootstrap_tea=True)
    codex_command = resolve_codex_command()
    epic, rules, unknowns = persist_adapter_bundle(bundle, run_dir, project_policy_context=policy_context)
    output_dir = run_dir / "raw-output"
    output = output_dir / "test-design-epic-1.md"
    output_dir.mkdir(parents=True, exist_ok=True)
    supplemental_path = run_dir / "inputs/adapter/current-system-supplemental.md"
    prompt = _invocation_prompt(epic, rules, unknowns, output, supplemental_path if supplemental_path.is_file() else None)
    if policy_context["policy"]:
        from .test_kit_policy import non_authoritative_policy_prompt, resolve_project_policy
        prompt += "\n" + non_authoritative_policy_prompt(resolve_project_policy(petclinic_root, "DESIGN"), policy_context["policy"])
        prompt += "\nLoad the project-owned TEA team customization via upstream workflow.persistent_facts in declared order; these facts remain testing guidance only.\n"
    else:
        prompt += """
Test Kit preflight resolved NO_PROJECT_POLICY for this run.
Compatibility rule for upstream activation: if {project-root}/_bmad/scripts/resolve_customization.py is absent, do not retry the missing resolver through uv or shell quoting. Resolve the workflow block directly from the installed skill's customize.toml; no team/user customization is present for this run. Use project-relative paths for skill files on Windows and do not rebuild absolute PowerShell command strings merely to read them. If a prerequisite command fails, apply the documented fallback once and continue; do not retry the same read/probe under alternate quoting.
"""
    prompt_path = output_dir / "invocation-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8", newline="\n")
    stdout_path = output_dir / "invocation.jsonl"
    stderr_path = output_dir / "stderr.txt"
    manifest_path = output_dir / "invocation-manifest.json"
    completed_artifact = run_dir / "evidence/tea-generated-completed.md"
    checkpoint_path = output_dir / "test-design/test-design-progress-epic-1.md"
    if manifest_path.exists():
        raise RuntimeError(f"invocation evidence already exists; choose a new run directory: {manifest_path}")
    input_files = [bundle.baseline.handoff_path, *bundle.baseline.source_paths.values(), epic, rules, unknowns, prompt_path, project_config]
    if bundle.supplemental_source is not None:
        input_files.append(Path(bundle.supplemental_source.path))
    if supplemental_path.is_file():
        input_files.append(supplemental_path)
    argv = codex_command.argv([
        "--ask-for-approval", "never", "exec", "--json", "--ephemeral",
        "--skip-git-repo-check", "--sandbox", "workspace-write", "--model", model,
        "-C", str(petclinic_root), "--add-dir", str(run_dir), "-o", str(output), "-",
    ])
    manifest = {
        "repository": TEA_REPOSITORY,
        "commit": TEA_COMMIT,
        "capability": TEA_CAPABILITY,
        "installed_skill_path": str(skill_dir),
        "installed_skill_sha256": _source_hash(skill_file),
        "installed_skill_files": pinned_skill_files,
        "pin_manifest_sha256": TEA_PIN_MANIFEST_SHA256,
        "project_config": {"path": str(project_config), "sha256": project_config_sha256},
        "project_policy_context": policy_context,
        "model": model,
        "normalizer_profile": "tea-native-runtime-v1",
        "ba_revision": bundle.baseline.revision,
        "invocation_command": argv,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "RUNNING",
        "inputs": [{"path": str(path), "sha256": _source_hash(path)} for path in input_files],
        "raw_output_path": str(output),
        "completed_artifact_path": str(completed_artifact),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    previous_digest = None
    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        process = subprocess.Popen(
            argv, stdin=subprocess.PIPE, stdout=stdout_file, stderr=stderr_file, cwd=petclinic_root
        )
        try:
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
        except BrokenPipeError:
            pass
        deadline = time.monotonic() + timeout_seconds
        timed_out = False
        while process.poll() is None:
            artifact_bytes = _completed_artifact_bytes(output, checkpoint_path)
            if artifact_bytes is not None:
                digest = hashlib.sha256(artifact_bytes).hexdigest()
                if digest == previous_digest and not completed_artifact.exists():
                    _write_exclusive(completed_artifact, artifact_bytes)
                previous_digest = digest
            if time.monotonic() >= deadline:
                timed_out = True
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                break
            time.sleep(0.15)
        exit_code = process.wait()
        if not completed_artifact.exists():
            artifact_bytes = _completed_artifact_bytes(output, checkpoint_path)
            if artifact_bytes is not None:
                _write_exclusive(completed_artifact, artifact_bytes)

    preserved_bytes = completed_artifact.read_bytes() if completed_artifact.is_file() else None
    workflow_complete = preserved_bytes is not None
    preserved_text = preserved_bytes.decode("utf-8", errors="replace") if preserved_bytes else ""
    has_tea_status = bool(re.search(r"(?m)^workflowStatus:\s*['\"]?completed['\"]?\s*$", preserved_text))
    final_output_digest = _source_hash(output) if output.is_file() else None
    stdout_text = stdout_path.read_bytes().decode("utf-8", errors="replace")
    stderr_text = stderr_path.read_bytes().decode("utf-8", errors="replace")
    closeout_text = stdout_text + "\n" + stderr_text
    closeout_failed = bool(re.search(r"(?i)(apply_patch|context[- ]mismatch).{0,120}(failed|could not|not found)|failed to find expected lines", closeout_text))
    preserved_digest = hashlib.sha256(preserved_bytes).hexdigest() if preserved_bytes else None
    manifest.update(
        {
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": exit_code,
            "artifact_sha256": preserved_digest,
            "final_output_sha256": final_output_digest,
            "workflow_status": "completed" if has_tea_status else None,
            "completion_basis": (
                "upstream-workflow-status" if has_tea_status
                else "completed-tea-checkpoint-and-frozen-raw-profile" if workflow_complete
                else None
            ),
            "status": "ARTIFACT_COMPLETE" if workflow_complete else "FAILED",
            "closeout_caveat": (
                "TEA wrote a completed artifact, then replaced the output target during closeout; the immutable completed copy is preserved at completed_artifact_path."
                if workflow_complete and final_output_digest != preserved_digest
                else
                "TEA wrote a completed artifact, then closeout patch/context reconciliation failed; retain logs and use the artifact contract as completion evidence."
                if workflow_complete and closeout_failed
                else "Artifact declares workflowStatus completed, but CLI exited nonzero; retain logs and use artifact state as completion evidence."
                if workflow_complete and exit_code != 0
                else None
            ),
        }
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if timed_out and not workflow_complete:
        manifest["status"] = "TIMEOUT"
        manifest["closeout_caveat"] = f"native TEA exceeded {timeout_seconds:g}s without a completed artifact"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise RuntimeError(f"native TEA timed out after {timeout_seconds:g}s; see {manifest_path}")
    if not workflow_complete:
        raise RuntimeError(f"native TEA did not produce a completed artifact; see {manifest_path}")
    return manifest


def read_supplemental_context(input_manifest_path: str | Path) -> str:
    path = Path(input_manifest_path)
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^## Supplemental CURRENT_SYSTEM evidence\s*\n(.*?)(?=^## |\Z)", text)
    if not match:
        raise ValueError(f"CURRENT_SYSTEM supplemental section not found: {path}")
    return match.group(1).strip()


def persist_adapter_bundle(
    bundle: AdapterBundle, run_dir: str | Path, *, project_policy_context: dict | None = None,
) -> tuple[Path, Path, Path]:
    """Write only fresh evidence paths; existing files are never overwritten."""
    run_dir = Path(run_dir)
    epic, rules, unknowns = _write_adapter_inputs(bundle, run_dir)
    input_dir = run_dir / "inputs"
    adapter_dir = input_dir / "adapter"
    manifest = {
        "feature_id": bundle.baseline.feature_id,
        "project_policy_context": project_policy_context,
        "ba_baseline_revision": bundle.baseline.revision,
        "ba_handoff_sha256": _source_hash(bundle.baseline.handoff_path),
        "sources": [
            {"authority": name, "path": str(path), "sha256": bundle.baseline.source_hashes[name]}
            for name, path in bundle.baseline.source_paths.items()
        ],
        "fr_ids": [row.id for row in bundle.requirements],
        "br_ids": [row.id for row in bundle.business_rules],
        "open_items": list(bundle.open_items),
        "supplemental_ref": (
            {
                "path": str(input_dir / "adapter/current-system-supplemental.md"),
                "sha256": _source_hash(input_dir / "adapter/current-system-supplemental.md"),
                "source_path": bundle.supplemental_source.path if bundle.supplemental_source else None,
                "source_sha256": bundle.supplemental_source.sha256 if bundle.supplemental_source else None,
            }
            if bundle.supplemental_text is not None
            else None
        ),
    }
    _write_exclusive(run_dir / "evidence/input-manifest.json", (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return epic, rules, unknowns



def prepare_same_session_design(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    project_root: str | Path,
    skill_dir: str | Path,
    supplemental_manifest: str | Path | None = None,
) -> dict:
    """Prepare immutable Test Design inputs for execution by the current agent session."""
    run_dir = Path(run_dir).resolve()
    project_root = Path(project_root).resolve()
    skill_dir = Path(skill_dir).resolve()
    expected_skill = (project_root / ".agents/skills" / TEA_CAPABILITY).resolve()
    if not expected_skill.is_dir() or not skill_dir.is_dir() or not expected_skill.samefile(skill_dir):
        raise RuntimeError("same-session TEA must use the project-local pinned skill")
    skill_files = verify_pinned_tea_skill(skill_dir)
    project_config = project_root / "_bmad/tea/config.yaml"
    if not project_config.is_file():
        raise RuntimeError(f"Test Kit project config is missing: {project_config}")

    supplemental = read_supplemental_context(supplemental_manifest) if supplemental_manifest else None
    supplemental_ref = None
    if supplemental_manifest:
        path = Path(supplemental_manifest).resolve()
        line = next(
            (number for number, row in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
             if row == "## Supplemental CURRENT_SYSTEM evidence"),
            None,
        )
        supplemental_ref = RawEvidenceRef(str(path), _source_hash(path), line, "CURRENT_SYSTEM / SUPPLEMENTAL")

    bundle = adapt_ba_to_tea(
        handoff_path, supplemental=supplemental, supplemental_source=supplemental_ref
    )
    policy_context = persist_project_policy_context(
        run_dir, project_root, "DESIGN", bootstrap_tea=True
    )
    epic, rules, unknowns = persist_adapter_bundle(
        bundle, run_dir, project_policy_context=policy_context
    )
    raw_output = run_dir / "raw-output/test-design-epic-1.md"
    instructions = run_dir / "raw-output/same-session-instructions.md"
    supplemental_path = run_dir / "inputs/adapter/current-system-supplemental.md"
    prompt = _invocation_prompt(
        epic, rules, unknowns, raw_output,
        supplemental_path if supplemental_path.is_file() else None,
    )
    prompt += """
SAME_SESSION_EXECUTION:
- Execute the installed bmad-testarch-test-design capability in this current agent session.
- Do not start codex, codexapi, another agent process, or a nested model invocation.
- Test Kit has already verified BA authority, pinned skill integrity, project policy, and adapter inputs.
- Do not create compatibility shims or edit installed Test Kit/TEA runtime.
- If the capability cannot complete from these prepared inputs, stop and report the blocker.
"""
    _write_if_same_or_absent(instructions, prompt.encode("utf-8"))
    manifest = {
        "schema_version": 1,
        "mode": "SAME_SESSION",
        "stage": "DESIGN",
        "status": "PREPARED",
        "feature_id": bundle.baseline.feature_id,
        "ba_revision": bundle.baseline.revision,
        "handoff_path": str(bundle.baseline.handoff_path),
        "handoff_sha256": bundle.baseline.handoff_sha256,
        "project_root": str(project_root),
        "project_config": {"path": str(project_config), "sha256": _source_hash(project_config)},
        "skill": {
            "capability": TEA_CAPABILITY,
            "path": str(skill_dir),
            "commit": TEA_COMMIT,
            "files": skill_files,
        },
        "project_policy_context": policy_context,
        "prepared_inputs": {
            "epic": str(epic),
            "business_rules": str(rules),
            "open_decisions": str(unknowns),
            "instructions": str(instructions),
        },
        "raw_output_path": str(raw_output),
    }
    manifest_path = run_dir / "evidence/same-session-prepare.json"
    _write_exclusive(
        manifest_path,
        (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return {**manifest, "manifest_path": str(manifest_path)}


def finalize_same_session_design(
    handoff_path: str | Path,
    run_dir: str | Path,
    *,
    raw_design: str | Path | None = None,
) -> dict:
    """Normalize, validate and submit same-session TEA output to Human Design Review."""
    run_dir = Path(run_dir).resolve()
    prepare_path = run_dir / "evidence/same-session-prepare.json"
    if not prepare_path.is_file():
        raise RuntimeError("same-session Design preparation evidence is missing")
    prepared = json.loads(prepare_path.read_text(encoding="utf-8"))
    if prepared.get("mode") != "SAME_SESSION" or prepared.get("stage") != "DESIGN" or prepared.get("status") != "PREPARED":
        raise RuntimeError("same-session Design preparation evidence is invalid")

    bundle = adapt_ba_to_tea(handoff_path)
    if (
        prepared.get("feature_id") != bundle.baseline.feature_id
        or prepared.get("ba_revision") != bundle.baseline.revision
        or prepared.get("handoff_sha256") != bundle.baseline.handoff_sha256
    ):
        raise RuntimeError("BA baseline changed after same-session preparation")

    raw_path = Path(raw_design).resolve() if raw_design else Path(prepared["raw_output_path"]).resolve()
    expected_raw = Path(prepared["raw_output_path"]).resolve()
    if raw_path != expected_raw or not raw_path.is_file():
        raise RuntimeError(f"same-session TEA output is missing or not at the prepared path: {expected_raw}")

    normalized = normalize_tea_output(raw_path, bundle.baseline)
    if normalized.status != "NORMALIZED" or normalized.snapshot is None:
        findings_path = run_dir / "evidence/normalization-findings.json"
        _write_exclusive(
            findings_path,
            (json.dumps(
                {"status": normalized.status, "findings": [finding.__dict__ for finding in normalized.findings]},
                ensure_ascii=False, indent=2,
            ) + "\n").encode("utf-8"),
        )
        raise RuntimeError(f"CANNOT_NORMALIZE: {normalized.findings}")

    validation = validate_design(normalized.snapshot, bundle.baseline)
    if validation.status != "PASS":
        findings_path = run_dir / "evidence/validator-results.json"
        _write_exclusive(
            findings_path,
            (json.dumps(
                {"status": validation.status, "findings": [finding.__dict__ for finding in validation.findings]},
                ensure_ascii=False, indent=2,
            ) + "\n").encode("utf-8"),
        )
        raise RuntimeError(f"validator FAIL; no gate transition: {validation.findings}")

    state = submit_design_for_review(
        start_design_workflow(normalized.snapshot), normalized.snapshot, validation
    )
    persist_design_review(
        run_dir, bundle, raw_path, normalized.snapshot, validation, state
    )
    result = {
        "schema_version": 1,
        "mode": "SAME_SESSION",
        "stage": "DESIGN",
        "status": state.state,
        "feature_id": bundle.baseline.feature_id,
        "artifact_id": state.artifact_id,
        "artifact_revision": state.artifact_revision,
        "artifact_sha256": state.artifact_sha256,
        "review_status": state.review_status,
        "validation_status": state.validation_status,
        "record_count": len(normalized.snapshot.records),
        "raw_output_path": str(raw_path),
    }
    _write_exclusive(
        run_dir / "evidence/same-session-finalize.json",
        (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )
    return result


def _same_session_main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Test Kit same-session Design workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare = subparsers.add_parser("prepare-design")
    prepare.add_argument("--handoff", type=Path, required=True)
    prepare.add_argument("--run-dir", type=Path, required=True)
    prepare.add_argument("--project-root", type=Path, required=True)
    prepare.add_argument("--skill-dir", type=Path, required=True)
    prepare.add_argument("--supplemental-manifest", type=Path)

    finalize = subparsers.add_parser("finalize-design")
    finalize.add_argument("--handoff", type=Path, required=True)
    finalize.add_argument("--run-dir", type=Path, required=True)
    finalize.add_argument("--raw-design", type=Path)

    args = parser.parse_args(argv)
    if args.command == "prepare-design":
        result = prepare_same_session_design(
            args.handoff, args.run_dir,
            project_root=args.project_root,
            skill_dir=args.skill_dir,
            supplemental_manifest=args.supplemental_manifest,
        )
    else:
        result = finalize_same_session_design(
            args.handoff, args.run_dir, raw_design=args.raw_design
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {"prepare-design", "finalize-design"}:
        try:
            return _same_session_main(argv)
        except (BaselineError, RuntimeError, ValueError, OSError, json.JSONDecodeError) as error:
            print(f"FAIL: {error}", file=sys.stderr)
            return 1

    parser = argparse.ArgumentParser(description="Legacy nested-agent Test Kit Design runner")
    parser.add_argument("--handoff", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--petclinic-root", type=Path, required=True)
    parser.add_argument("--skill-dir", type=Path, required=True)
    parser.add_argument("--supplemental-manifest", type=Path)
    parser.add_argument("--model", default="gpt-6-luna")
    args = parser.parse_args(argv)
    try:
        supplemental = read_supplemental_context(args.supplemental_manifest) if args.supplemental_manifest else None
        supplemental_ref = None
        if args.supplemental_manifest:
            path = args.supplemental_manifest.resolve()
            line = next((number for number, row in enumerate(path.read_text(encoding="utf-8").splitlines(), 1) if row == "## Supplemental CURRENT_SYSTEM evidence"), None)
            supplemental_ref = RawEvidenceRef(str(path), _source_hash(path), line, "CURRENT_SYSTEM / SUPPLEMENTAL")
        bundle = adapt_ba_to_tea(args.handoff, supplemental=supplemental, supplemental_source=supplemental_ref)
        invocation = invoke_native_tea(bundle, args.run_dir, petclinic_root=args.petclinic_root, skill_dir=args.skill_dir, model=args.model)
        raw_path = Path(invocation["completed_artifact_path"])
        normalized = normalize_tea_output(raw_path, bundle.baseline)
        if normalized.status != "NORMALIZED" or normalized.snapshot is None:
            findings_path = Path(args.run_dir) / "evidence/normalization-findings.json"
            _write_exclusive(
                findings_path,
                (json.dumps({"status": normalized.status, "findings": [finding.__dict__ for finding in normalized.findings]}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )
            raise RuntimeError(f"CANNOT_NORMALIZE: {normalized.findings}")
        validation = validate_design(normalized.snapshot, bundle.baseline)
        if validation.status != "PASS":
            findings_path = Path(args.run_dir) / "evidence/validator-results.json"
            _write_exclusive(
                findings_path,
                (json.dumps({"status": validation.status, "findings": [finding.__dict__ for finding in validation.findings]}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
            )
            raise RuntimeError(f"validator FAIL; no gate transition: {validation.findings}")
        state = submit_design_for_review(start_design_workflow(normalized.snapshot), normalized.snapshot, validation)
        persist_design_review(args.run_dir, bundle, raw_path, normalized.snapshot, validation, state)
        print(f"STATE: {state.state}; SHA256: {state.artifact_sha256}; TD_ROWS: {len(normalized.snapshot.records)}")
        return 0
    except (BaselineError, RuntimeError, ValueError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
