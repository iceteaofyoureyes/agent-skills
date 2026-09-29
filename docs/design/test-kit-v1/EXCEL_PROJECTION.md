# Test Kit V1 Excel Projection

Excel is a human-facing derived view of persisted canonical Testcases. It has no reverse import, gate transition, execution, or automation behavior. Production export accepts only a persisted `STOP_V1` `APPROVED_TESTWARE` snapshot whose Case Gate receipt, current BA and Design refs, execution evidence, and Human actor pass the existing Test Kit validators. TEST_ONLY fixtures remain under `benchmark/`; generated output uses an OS temporary directory or `.work/benchmark-runs/` and remains non-production evidence.

## Default profile

`DEFAULT_TESTCASE_EXCEL_V1` version `1.0.0` is pinned in `tooling/pins/testcase-excel-default-v1.json`. It uses one testcase per worksheet row and ordered multiline `Step`, `Test Data`, and `Expected Result` cells. Its exact headers are pinned in that file. Unsupported reference-workbook fields stay blank; canonical testcase IDs and machine trace stay in `<workbook>.projection.json`.

`Folder` reuses the approved XMind functional grouping pin against current BA text. A unique functional group produces `<feature title>/<approved group label>`. Ambiguous or unmapped references leave the presentation-only field blank under the pinned profile policy.

## Template precedence and mapping

Selection order is human-supplied approved workbook, project workbook, then the pinned default. The custom workbook is inspected for a unique testcase sheet/header row, exact recognized semantic headers, start row, row model, and its presentation structures. Ambiguous or unsupported mappings fail with `CANNOT_PROJECT_TEMPLATE`; they never fall back to the default. `ONE_STEP_PER_ROW` can be selected explicitly in the mapping contract when that row pattern is intentional.

The custom-template preservation boundary is limited to workbook structures covered by the committed fixture: sheets, cell styles, fonts/fills/borders, dimensions, merges, formulas, validations, hidden regions, panes, protection, and a repeatable styled row. Rich text anywhere in the workbook (including hidden sheets), external workbook links, charts/images, and pivot tables are rejected with `CANNOT_PROJECT_TEMPLATE`; macro-enabled files are rejected by the `.xlsx` requirement. Other untested Excel extension parts are outside the V1 preservation guarantee and are rejected when the inspector can identify them. A custom template must provide blank testcase cells. Its original SHA-256 and inspected mapping contract are pinned into the external manifest.

## Validation and evidence

Validation reopens the serialized workbook and compares every mapped cell and row binding against the canonical snapshot and manifest, normalizing newline encodings only. It checks the workbook hash, template hash, semantic projection hash, case identities, ordered steps, scoped test data, expected results, priorities, and all canonical trace fields. Failures return `EXCEL_SEMANTIC_DIFF: FAIL` or `CANNOT_PROJECT_TEMPLATE`; the adapter does not repair the workbook.

Published workbooks and manifests are sealed immutable evidence snapshots. A projection artifact is not an editable working copy; Humans who want to edit the workbook should copy it to another file. Manual edits to the generated artifact invalidate its manifest binding. This filesystem seal rejects ordinary writes; it is not protection against a privileged user deliberately changing permissions.

Failed-export rollback on Windows opens each published file with `DELETE`, `FILE_READ_ATTRIBUTES`, and `FILE_WRITE_ATTRIBUTES`, using share mode `0`. It verifies the volume serial and file ID from that handle, then clears read-only state and sets delete disposition through the same still-open handle. POSIX rollback compares `st_dev`/`st_ino` and preserves detected identity conflicts, but its final deletion is path-based; portable Python does not provide the same race-free unlink-by-handle guarantee, and V1 does not claim that Windows guarantee on POSIX.

The spreadsheet runtime is pinned in `tooling/requirements-excel.lock`. Focused coverage lives in `tooling/tests/test_test_kit_v1_excel.py`; it generates TEST_ONLY output in temporary directories from the stable fixtures under `benchmark/test-kit/petclinic/fixtures/`.
