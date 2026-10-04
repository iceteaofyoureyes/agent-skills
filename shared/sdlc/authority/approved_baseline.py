"""Approved BA authority reader shared by downstream lanes. BAREF is a locator, never a business ID."""
from shared.sdlc.compatibility import retain_legacy_identity as _retain_legacy_identity
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from shared.sdlc.authority.contracts import _yaml_fields, validate_handoff_file

_retain_legacy_identity(__name__, 'approved_baseline')

CONTRACT_VERSION = 1
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")
SOURCE_HEADING = re.compile(
    r"^(?P<marks>#{2,6})\s+(?P<id>`?(?:FR|BR)-(?:[A-Za-z0-9]+-)*\d+`?)\s*(?:[—–-]\s*)?(?P<title>.*?)\s*$",
    re.IGNORECASE,
)
MARKDOWN_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
TABLE_SEPARATOR = re.compile(r"^\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?$")


class BaselineError(ValueError):
    def __init__(self, message: str, *, code: str = "INVALID_BA_BASELINE"):
        super().__init__(message)
        self.code = code


def _field(fields, path):
    return fields.get(tuple(path.split('.')))

def _source_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

@dataclass(frozen=True)
class BaselineRow:
    id: str
    text: str
    path: str
    line: int
    source_role: str = ""
    source_sha256: str = ""
    ordinal: int = 0
    locator_sha256: str = ""


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
    def identity(self):
        return {"feature_id": self.feature_id, "revision": self.revision,
                "handoff_sha256": self.handoff_sha256, "source_hashes": self.source_hashes}

    def snapshot(self):
        return {"path": str(self.handoff_path), "revision": self.revision,
                "sha256": self.handoff_sha256, "identity": self.identity,
                "sources": [{"path": str(path), "sha256": self.source_hashes[role]}
                            for role, path in self.source_paths.items()]}

    @property
    def requirement_ids(self) -> set[str]:
        return {row.id for row in self.requirements}

    @property
    def business_rule_ids(self) -> set[str]:
        return {row.id for row in self.business_rules}

    @property
    def authority_ref_ids(self) -> set[str]:
        """All source references, including structural BAREF locators."""
        return self.requirement_ids | self.business_rule_ids

    @property
    def coverage_ids(self) -> set[str]:
        """Only canonical FR/BR IDs impose mandatory business coverage."""
        return {identifier for identifier in self.authority_ref_ids
                if _source_id_matches(identifier, "FR") or _source_id_matches(identifier, "BR")}

    @property
    def ba_ids(self) -> set[str]:
        """Compatibility alias for authority refs, never mandatory coverage."""
        return self.authority_ref_ids


def _markdown_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _normalize_source_id(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and not value.startswith("``") and not value.endswith("``"):
        return value[1:-1].strip()
    return value


def _source_id_matches(value: str, id_prefix: str) -> bool:
    return bool(re.fullmatch(rf"{id_prefix}-(?:[A-Za-z0-9]+-)*\d+", _normalize_source_id(value), re.IGNORECASE))


def _parse_source_rows(path: Path, id_prefix: str, wanted_columns: int, *, source_path=None) -> tuple[BaselineRow, ...]:
    """Accept legacy source tables and current BA Kit heading-based artifacts."""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[BaselineRow] = []

    for number, raw in enumerate(lines, 1):
        if not raw.lstrip().startswith("|") or TABLE_SEPARATOR.fullmatch(raw.strip()):
            continue
        cells = _markdown_cells(raw)
        if not cells:
            continue
        source_id = _normalize_source_id(cells[0])
        if not _source_id_matches(source_id, id_prefix):
            continue
        if len(cells) < 2:
            raise BaselineError(f"{path}:{number}: source ID requires source text")
        if not cells[1]:
            raise BaselineError(f"{path}:{number}: {source_id} has no source text")
        rows.append(BaselineRow(source_id, cells[1], str(path), number))

    for index, raw in enumerate(lines):
        match = SOURCE_HEADING.match(raw)
        if not match:
            continue
        source_id = _normalize_source_id(match.group("id"))
        if not _source_id_matches(source_id, id_prefix):
            continue
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

    for number, raw in enumerate(lines, 1):
        match = re.match(rf"^\s*(?:[-*+]\s+|\d+[.)]\s+)?(?P<id>`?{id_prefix}-(?:[A-Za-z0-9]+-)*\d+`?)\s*[:—–-]\s*(?P<text>.+)$", raw)
        if match:
            source_id = _normalize_source_id(match.group("id"))
            if _source_id_matches(source_id, id_prefix):
                rows.append(BaselineRow(source_id, match.group("text"), str(path), number))

    if not rows:
        # Structural sections preserve authority text without asserting new business IDs.
        starts = [i for i, line in enumerate(lines) if MARKDOWN_HEADING.match(line)]
        starts = sorted(set([0, *starts, len(lines)]))
        for start, end in zip(starts, starts[1:]):
            text = "\n".join(lines[start:end]).strip()
            if text:
                rows.append(BaselineRow(f"BAREF:{'SRS' if id_prefix == 'FR' else 'BR'}:{len(rows)+1:03d}", text, str(path), start+1))
        if not rows:
            raise BaselineError(f"{path}: empty authority source")
    folded = [row.id.casefold() for row in rows]
    if len(folded) != len(set(folded)):
        raise BaselineError(f"{path}: duplicate {id_prefix} source IDs")
    role = "srs" if id_prefix == "FR" else "business_rules"
    digest = _source_hash(path)
    bound = []
    for ordinal, row in enumerate(rows, 1):
        binding = json.dumps([role, source_path or path.name, digest, row.line, ordinal, row.text], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        bound.append(BaselineRow(row.id, row.text, row.path, row.line, role, digest, ordinal, hashlib.sha256(binding).hexdigest()))
    return tuple(bound)

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


def read_approved_baseline(handoff_path: str | Path) -> ApprovedBaseline:
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

    requirements = _parse_source_rows(source_paths["srs"], "FR", 3, source_path=_field(fields, "authoritative_sources.srs.path"))
    business_rules = _parse_source_rows(source_paths["business_rules"], "BR", 3, source_path=_field(fields, "authoritative_sources.business_rules.path"))
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


def verify_baseline_snapshot(snapshot):
    errors = []
    if not isinstance(snapshot, dict):
        return ["baseline snapshot is missing"]
    for item in [{"path": snapshot.get("path"), "sha256": snapshot.get("sha256")}, *snapshot.get("sources", [])]:
        if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
            errors.append("baseline snapshot entry is invalid")
            continue
        try:
            actual = hashlib.sha256(Path(item["path"]).read_bytes()).hexdigest()
        except OSError as error:
            errors.append(f"cannot read baseline source {item['path']}: {error}")
            continue
        if actual != item["sha256"]:
            errors.append(f"SHA-256 changed: {item['path']}")
    return errors
