# Test Kit V1.1 — Implementation Plan

## Phase A — Foundation / resolver

Add a small project-policy module rather than modifying canonical artifact classes first.

Deliverables:

- project profile loader;
- strict schema validation;
- safe path resolver;
- deterministic Design/Case policy snapshots;
- policy SHA tests;
- production check for personal TEA override;
- TEST_ONLY escape hatch with explicit evidence.

No gates or invocation behavior change until this layer is independently tested.

## Phase B — Design/TEA integration

- validate/reuse upstream TEA project customization;
- ensure common + test-design rules are loaded through upstream `persistent_facts`;
- copy resolved policy inputs into run evidence;
- record policy snapshot in TEA invocation/input manifests;
- bind Design Gate receipt refs to Design Policy snapshot;
- reject stale Design Policy at approval.

Regression requirement: existing V1 run with no policy either uses an explicit default-empty policy snapshot or preserves a clearly documented compatibility behavior; no implicit machine-local rules.

## Phase C — Testcase integration

- copy common + testcase rule files into case run evidence;
- add non-authoritative testing-policy section to native Katalon invocation;
- record Case Policy snapshot in input/invocation manifests;
- bind Case Review/Gate to Case Policy ref;
- reject stale Case Policy at approval;
- retain all existing BA/Design/execution-oracle validators.

## Phase D — Excel project template

- resolve `templates.excel.path` from project profile;
- feed it into existing `PROJECT_TEMPLATE` path;
- preserve Human template precedence;
- add missing/ambiguous/project-template tests;
- no XMind changes.

## Phase E — Doctor + operator UX

- Doctor diagnostics for project customization;
- bootstrap/example profile and rule files;
- Vietnamese Quick Start/Usage Guide customization sections;
- CR-001 customization fixture demonstrating:
  - valid testing convention;
  - BA UNKNOWN conflict remains unresolved;
  - policy change invalidates relevant gate;
  - personal override production block;
  - Excel project template selection.

## Phase F — Regression and Human Gate

Required evidence before V1.1 acceptance:

- new policy unit/integration tests PASS;
- Test Kit packaging PASS;
- full existing tooling regression PASS;
- source/package integrity PASS;
- TEST_ONLY fixtures remain non-production;
- docs review PASS;
- Human explicitly APPROVE V1.1.

Then merge V1.1 and return to `STOP_V1_1`. Automation Test V2 remains a separate future lane.
