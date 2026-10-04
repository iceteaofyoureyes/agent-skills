"""Export packaged Spec Kit workflow transport from Dev VNext's canonical adapter."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tooling.lib.dev_vnext_spec_kit import workflow_document  # noqa: E402


def regenerate(root=ROOT):
    directory = Path(root) / "kits/dev/plugin/workflows"
    outputs = {}
    for name, high_risk in (("dev-normal.workflow.yml", False), ("dev-high-risk.workflow.yml", True)):
        path = directory / name
        path.write_text(json.dumps(workflow_document(high_risk=high_risk), indent=2) + "\n", encoding="utf-8", newline="\n")
        outputs[name] = path
    return outputs


if __name__ == "__main__":
    for path in regenerate().values():
        print(path.relative_to(ROOT).as_posix())
