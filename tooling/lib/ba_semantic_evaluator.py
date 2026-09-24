"""Evaluate generated BA artifacts against acceptance-only semantic fixtures."""

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = ROOT / "ba-workflow/evals/cr001-semantic-contract.json"
PASS_STATUSES = {"MATCH", "UNKNOWN_PRESERVED"}


def load_fixture(path=DEFAULT_FIXTURE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _matches(pattern, text):
    return re.search(pattern, text, re.IGNORECASE | re.DOTALL) is not None


def _check_status(check, text):
    kind = check["kind"]
    if kind == "forbidden":
        return "UNSUPPORTED_INVENTION" if any(_matches(p, text) for p in check["patterns"]) else "MATCH"
    if kind == "exact_ids":
        actual = re.findall(check["pattern"], text, re.IGNORECASE)
        expected = check["expected"]
        if len(actual) != len(set(actual)):
            return "CONTRADICTION"
        if set(actual) - set(expected):
            return "UNSUPPORTED_INVENTION"
        if actual != expected:
            return "MISSING_REQUIRED_BEHAVIOR"
        return "MATCH"
    if kind != "required":
        raise ValueError(f"unsupported evaluator check kind: {kind}")

    if any(_matches(pattern, text) for pattern in check.get("contradiction_any", [])):
        return "CONTRADICTION"
    if all(any(_matches(pattern, text) for pattern in alternatives) for alternatives in check["groups"]):
        return check.get("status_on_match", "MATCH")
    return "MISSING_REQUIRED_BEHAVIOR"


def evaluate_artifacts(business_rules, srs, case_id, gap_review=None, fixture=None):
    fixture = load_fixture(fixture or DEFAULT_FIXTURE)
    case = fixture["cases"].get(case_id)
    if case is None:
        raise ValueError(f"unknown semantic evaluation case: {case_id}")
    documents = {"business_rules": business_rules, "srs": srs}
    if gap_review is not None:
        documents["gap_review"] = gap_review
    results = []
    artifact_overrides = case.get("artifact_overrides", {})
    default_artifacts = case.get("default_artifacts")
    for check_id in case.get("check_ids", []):
        check = fixture["checks"][check_id]
        for artifact in artifact_overrides.get(check_id, default_artifacts or check["artifacts"]):
            if artifact not in documents:
                raise ValueError(f"case {case_id} requires --{artifact.replace('_', '-')} input")
            results.append({
                "semantic_id": check_id,
                "artifact": artifact,
                "status": _check_status(check, documents[artifact]),
            })
    for check_id in case.get("forbidden_ids", []):
        check = fixture["checks"][check_id]
        for artifact in artifact_overrides.get(check_id, default_artifacts or check["artifacts"]):
            if artifact not in documents:
                raise ValueError(f"case {case_id} requires --{artifact.replace('_', '-')} input")
            results.append({
                "semantic_id": check_id,
                "artifact": artifact,
                "status": _check_status(check, documents[artifact]),
            })
    return {
        "case_id": case_id,
        "passed": all(result["status"] in PASS_STATUSES for result in results),
        "results": results,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Evaluate generated BA artifacts against semantic acceptance fixtures")
    parser.add_argument("--case", required=True)
    parser.add_argument("--business-rules", type=Path, required=True)
    parser.add_argument("--srs", type=Path, required=True)
    parser.add_argument("--gap-review", type=Path)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args(argv)
    try:
        result = evaluate_artifacts(
            args.business_rules.read_text(encoding="utf-8"),
            args.srs.read_text(encoding="utf-8"),
            args.case,
            args.gap_review.read_text(encoding="utf-8") if args.gap_review else None,
            args.fixture,
        )
    except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
