"""Export the installed JSON Schemas from Dev VNext's executable contracts."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tooling.lib import dev_vnext as contracts  # noqa: E402


SCHEMAS = {
    "start-request-v2.schema.json": contracts.START_REQUEST_V2,
    "engineering-impact-v2.schema.json": contracts.IMPACT_V2,
    "engineering-gap-v2.schema.json": contracts.GAP_V2,
    "engineering-decision-v2.schema.json": contracts.DECISION_V2,
    "dev-state-v2.schema.json": contracts.STATE_V2,
    "technical-approval-v2.schema.json": contracts.TECHNICAL_RECEIPT_V2,
    "dev-handoff-v2.schema.json": contracts.HANDOFF_V2,
}


def regenerate(root=ROOT):
    directory = Path(root) / "kits/dev/schemas"
    for name, schema in SCHEMAS.items():
        (directory / name).write_text(
            json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return tuple(directory / name for name in SCHEMAS)


if __name__ == "__main__":
    for path in regenerate():
        print(path.relative_to(ROOT).as_posix())
