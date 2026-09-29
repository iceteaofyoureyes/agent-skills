# Findings

## Findings requiring an upstream change

None.

## Oracle results

Each check links the approved source and rule to the exact candidate output location.

| ID | BA source → requirement/rule | Candidate output | Finding |
|---|---|---|---|
| O-001 | 03-approved-business-rules.md BR-005 and 04-srs-excerpt.md FR-001/open item → maximum Appointment duration is UNKNOWN | raw-output/test-design/test-design-epic-1.md, TD-003, NFR Planning, Assumptions item 4 | PASS — the plan tests only positive/non-positive duration and asserts no maximum. |
| O-002 | 04-srs-excerpt.md FR-006 and 03-approved-business-rules.md BR-014 → list filters are UNKNOWN | raw-output/test-design/test-design-epic-1.md, TD-014, Assumptions item 5 | PASS — no filter behavior is asserted. |
| O-003 | 04-srs-excerpt.md FR-006 and 03-approved-business-rules.md BR-014 → default sorting is UNKNOWN | raw-output/test-design/test-design-epic-1.md, TD-014, Assumptions item 5 | PASS — no default order is asserted. |
| O-004 | 04-srs-excerpt.md FR-006 and 03-approved-business-rules.md BR-014 → pagination/page size is UNKNOWN | raw-output/test-design/test-design-epic-1.md, TD-014, Assumptions item 5 | PASS — no page behavior or size is asserted. |

## Advisory

| ID | BA source → requirement/rule | Candidate output | Finding |
|---|---|---|---|
| A-001 | 03-approved-business-rules.md BR-001–BR-014 and 04-srs-excerpt.md FR-001–FR-006 define functional behavior; none defines test coverage percentages | raw-output/test-design/test-design-epic-1.md, Quality Gate Criteria | TEA's template contributes generic 80%/70%/50% coverage targets. The output labels them as generic and requiring project-owner agreement. They are not BA requirements and must remain advisory unless approved separately. This did not change Appointment behavior or trigger a release gate. |

## Patch candidates

None. A-001 is an explicitly qualified template default, not a failure that requires modifying TEA. No patch was applied or proposed.
