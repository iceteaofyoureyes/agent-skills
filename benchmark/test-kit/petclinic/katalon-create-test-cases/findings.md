# Findings

## Business-semantics hallucinations

None found.

## UNKNOWN oracle

Every row follows the required evidence chain: **BA source → rule/requirement → Stage 1–2 design → generated testcase → result**.

| UNKNOWN | Evidence chain | Result |
|---|---|---|
| Maximum Appointment duration | 03-approved-business-rules.md BR-005 / 04-srs-excerpt.md FR-001 → TD-003 → TC-001 and TC-005 through TC-007 | Preserved. Cases cover one positive datum, zero, and negative; none sets an upper limit or tests an invented maximum. |
| List filters | 04-srs-excerpt.md FR-006 / 03-approved-business-rules.md BR-014 → TD-014 → TC-001 | Preserved. The view step asserts visibility only; no filter is selected or assumed. |
| Default sorting | 04-srs-excerpt.md FR-006 / 03-approved-business-rules.md BR-014 → TD-014 → TC-001 | Preserved. No order is asserted. |
| Pagination/page size | 04-srs-excerpt.md FR-006 / 03-approved-business-rules.md BR-014 → TD-014 → TC-001 | Preserved. No page count, page boundary, or size is asserted. |

## Execution/input findings

| ID | Source/design → testcase | Finding |
|---|---|---|
| I-001 | 04-srs-excerpt.md FR-003 and 03-approved-business-rules.md BR-007/BR-008 → TD-006 says the editable field comes from the future interface contract → TC-012 uses EDIT_FIELD/EDIT_VALUE placeholders | The status rule is covered without guessing a field. TC-012 needs the approved edit contract before it can be run. This is a source/UI dependency, not a semantic hallucination or upstream skill failure. |
| I-002 | 03-approved-business-rules.md BR-003/BR-006 → Stage 1–2 Assumptions item 3 leaves the interval-end mapping unspecified → TC-008 through TC-014 use explicit displayed interval fixtures without deriving end from duration | Half-open boundaries are testable once fixture intervals are available. The testcase set correctly leaves the mapping as an execution dependency rather than inventing a formula. |
| I-003 | Pinned skills/create-test-cases/SKILL.md describes optional Katalon discovery/create/link operations → no Katalon MCP tools or registered skill were available → raw-output/test-cases.md remains local Markdown with source references | Semantic case generation ran from pinned skill text; project discovery, duplicate search, platform writes, and requirement linking were not exercised. This is an integration limitation, not a semantic mismatch. |

## Patch candidates

None. I-001 and I-002 require future interface/test-fixture information. I-003 is outside the requested semantic-only scope. No upstream code or skill was changed.
