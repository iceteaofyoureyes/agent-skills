# Test Kit V1

Test Kit V1 turns an approved BA handoff into a reviewed Test Design and reviewed manual testcases. Human decisions remain the gates between the artifacts.

## Prerequisites

- Python 3.10 or newer.
- The packaged V1 workflow targets Codex projects (`.agents/skills`).
- Codex CLI for native TEA and Katalon generation. The shared resolver uses `TEST_KIT_CODEX_COMMAND`, then `PATH`, then fails closed. A `.js` override also needs Node on `PATH`.
- A project `_bmad/tea/config.yaml` compatible with the pinned TEA skill.
- The pinned TEA and Katalon skills are included in the install. Installation makes no network requests.

Node/npm and Python projection packages are needed only when you explicitly request XMind or Excel output.

## Install and verify

From the Agent Skills repository, install into the current Codex project. V1 uses project scope because native TEA and Katalon invocations require project-local pinned skills:

```powershell
.\tooling\install.ps1 -Kit test --agent codex --scope project
.\tooling\doctor.ps1 -Kit test --agent codex --scope project
```

The skills install under `.agents/skills/`. Test Kit runtime, pins, dependency locks, notices, and this guide install under `.agents/skills/.test-kit/`.

To verify the installed runtime without loading repository modules:

```powershell
$env:PYTHONPATH = (Resolve-Path .agents/skills/.test-kit).Path
python -m tooling.lib.test_kit_v1 --help
```

The `test-kit` skill provides the workflow instructions. The upstream TEA skill is `bmad-testarch-test-design`; the Katalon skill is `create-test-cases`.

## Core workflow and Human Gates

Use a project-owned run directory for each feature. The Test Kit writes raw invocation evidence, canonical snapshots, receipts, validation results, and workflow state only under that run directory.

1. Supply an approved BA handoff and its source files.
2. Test Kit adapts the approved BA baseline and invokes pinned TEA.
3. The adapter normalizes and validates the raw Test Design, then stops at `DESIGN_REVIEW`.
4. A Human reviews the exact canonical snapshot and records `APPROVE` or `REQUEST_CHANGES`.
5. After approval, Test Kit invokes the pinned Katalon skill and normalizes its manual testcase output.
6. Test Kit stops at `CASE_REVIEW`. A Human reviews the exact canonical cases. Approval produces `APPROVED_TESTWARE`; material unresolved execution dependencies keep the gate blocked.

The BA baseline owns business behavior. Approved Test Design owns coverage. An approved interface or execution contract owns execution details. Test Kit does not infer missing Human decisions.

## Optional XMind projection

XMind is an on-demand projection after the relevant Human decision. It does not change canonical artifacts or gate state. Install Node.js 18+ and npm 9+, then explicitly bootstrap the pinned SDK from the installed lockfile:

```powershell
Push-Location .agents/skills/.test-kit/tooling/xmind
npm ci
Pop-Location
```

The exporter uses the installed SDK and writes projection output beside the selected run artifact.

## Optional Excel projection

Excel is an on-demand projection of approved testcases. It does not change canonical artifacts or gate state. With the Python environment used by the projection, explicitly install the hash-pinned requirements:

```powershell
python -m pip install --require-hashes -r .agents/skills/.test-kit/tooling/requirements-excel.lock
```

Generated workbooks are written beside the selected run artifact. The projection code does not require an external workbook template.

## Reinstall, upgrade, and removal

Run the same install command to reinstall. Reinstall is idempotent. A newer manifest updates unchanged managed assets; locally edited managed assets and unrelated project files are preserved and reported.

Remove an install with:

```powershell
.\tooling\uninstall.ps1 -Kit test --agent codex --scope project
```

Only unchanged files owned by Test Kit are removed. Edited or shared assets stay in place.

Doctor reads `.test-kit/kit.yaml` as the installed package definition, verifies the pinned authority and payload, then reports local drift or corrupt metadata.

## Troubleshooting

- `Python 3.10+ is required`: use a supported Python interpreter and rerun install/doctor.
- Codex resolution failed: set `TEST_KIT_CODEX_COMMAND` to the Codex executable/launcher, or make `codex` available on `PATH`. An invalid explicit override fails closed.
- `XMIND_SDK_UNAVAILABLE`: install Node/npm and run the explicit `npm ci` bootstrap above.
- Excel reports missing `openpyxl`: run the explicit `pip install --require-hashes` command above in the Python environment used for the projection.
- `PIN_INTEGRITY_FAILURE`: reinstall Test Kit from the same pinned package source; do not edit upstream skill files.
- `MODIFIED_MANAGED_FILE`: doctor found local edits. Reinstall preserves them and keeps the package's expected hash, so doctor remains not ready until you restore the expected file or resolve the edit and restore the pinned bytes.
- `MISSING_MANAGED_FILE`: restore the missing file from the same pinned package and run doctor again.
- `DEPENDENCY_MISSING`: Codex CLI is required for native generation. Optional XMind or Excel dependencies only affect their projection capabilities.
- A preserved file was locally edited or is shared with another kit. Review it before manually removing it.

## V1 boundary

V1 covers Test Design, Human Design Review, manual testcase generation, Human Case Review, and optional XMind/Excel projections.

**Automation execution, triage, and evidence automation are V2 and are not included in V1.**
