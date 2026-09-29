# Normalized testcase traceability

**Total:** 27 manual cases; 27 P1, 0 P0, 0 P2. No test was executed.

The case set expands the approved Stage 1–2 scenario IDs without changing their business meaning. TC-001 combines the compatible create-and-view intent from TD-001 and TD-014 to avoid a duplicate visibility-only assertion.

## Testcase → approved design and requirement

| Case | Validation intent | FR refs | BR refs | Test Design refs |
|---|---|---|---|---|
| TC-001 | Valid create and view end-to-end | FR-001, FR-006 | BR-001, BR-003, BR-008, BR-014 | TD-001, TD-014 |
| TC-002 | Start just after T0 is accepted | FR-001 | BR-004 | TD-002 |
| TC-003 | Start equal to T0 is rejected | FR-001 | BR-004 | TD-002 |
| TC-004 | Past start is rejected | FR-001 | BR-004 | TD-002 |
| TC-005 | Positive duration is accepted | FR-001 | BR-005 | TD-003 |
| TC-006 | Zero duration is rejected | FR-001 | BR-005 | TD-003 |
| TC-007 | Negative duration is rejected | FR-001 | BR-005 | TD-003 |
| TC-008 | Same-Veterinarian Scheduled overlap is rejected | FR-002 | BR-006 | TD-004 |
| TC-009 | New start equals existing end; allowed | FR-002 | BR-006 | TD-004 |
| TC-010 | New end equals existing start; allowed | FR-002 | BR-006 | TD-004 |
| TC-011 | Same Pet overlap with a different Veterinarian is allowed | FR-002 | BR-006, BR-012 | TD-005 |
| TC-012 | Scheduled Appointment edit is accepted | FR-003 | BR-008 | TD-006 |
| TC-013 | Reschedule excludes its own old interval | FR-003 | BR-006, BR-007, BR-008 | TD-006 |
| TC-014 | Conflict with another Scheduled Appointment blocks reschedule | FR-002, FR-003 | BR-006, BR-007 | TD-007 |
| TC-015 | Cancelled Appointment cannot be edited | FR-003 | BR-008 | TD-008 |
| TC-016 | Cancelled Appointment cannot be rescheduled | FR-003 | BR-008 | TD-008 |
| TC-017 | Cancelled Appointment cannot be cancelled again | FR-004 | BR-008 | TD-008 |
| TC-018 | Cancelled Appointment cannot be completed | FR-005 | BR-008 | TD-008 |
| TC-019 | Completed Appointment cannot be edited | FR-003 | BR-008 | TD-008 |
| TC-020 | Completed Appointment cannot be rescheduled | FR-003 | BR-008 | TD-008 |
| TC-021 | Completed Appointment cannot be cancelled | FR-004 | BR-008 | TD-008 |
| TC-022 | Completed Appointment cannot be completed again | FR-005 | BR-008, BR-010 | TD-008, TD-011 |
| TC-023 | Cancel changes state and retains the record | FR-004 | BR-008, BR-009, BR-011 | TD-009 |
| TC-024 | Cancelled interval can be booked again | FR-002, FR-004 | BR-006, BR-009 | TD-010 |
| TC-025 | Completion changes state and creates exactly one Visit | FR-005 | BR-002, BR-008, BR-010 | TD-011 |
| TC-026 | Completed Appointment does not block a new booking | FR-002 | BR-006, BR-008 | TD-012 |
| TC-027 | Concurrent conflicting creates persist only one conflicting Appointment | FR-002 | BR-006, BR-013 | TD-013 |

## FR coverage

| Requirement | Case coverage |
|---|---|
| FR-001 | TC-001 through TC-007 |
| FR-002 | TC-008 through TC-011, TC-014, TC-024, TC-026, TC-027 |
| FR-003 | TC-012 through TC-016, TC-019, TC-020 |
| FR-004 | TC-017, TC-021, TC-023, TC-024 |
| FR-005 | TC-018, TC-022, TC-025 |
| FR-006 | TC-001 |

## BR coverage

| Rule | Case coverage |
|---|---|
| BR-001 | TC-001 |
| BR-002 | TC-025 |
| BR-003 | TC-001 |
| BR-004 | TC-002 through TC-004 |
| BR-005 | TC-001, TC-005 through TC-007; maximum duration remains UNKNOWN |
| BR-006 | TC-008 through TC-011, TC-013, TC-014, TC-024, TC-026, TC-027 |
| BR-007 | TC-013, TC-014, TC-016, TC-020 |
| BR-008 | TC-001, TC-012 through TC-026 |
| BR-009 | TC-023, TC-024 |
| BR-010 | TC-022, TC-025 |
| BR-011 | TC-023 |
| BR-012 | TC-011 |
| BR-013 | TC-027 |
| BR-014 | TC-001; list policy remains UNKNOWN |

## UNKNOWN preservation

| Unknown | Case treatment |
|---|---|
| Maximum Appointment duration | No upper-limit value or expected result is tested. TC-005 covers only one positive input; TC-006/TC-007 cover zero/negative. |
| List filters | TC-001 checks the created record is viewable without asserting filters. |
| Default sorting | No case asserts order. |
| Pagination/page size | No case asserts page count, boundary, or size. |

## Execution dependencies, not new requirements

- TC-012 requires the approved UI/API contract to name an editable field and its value. The BA/Test Design does not identify one.
- Interval cases use the [start, end) values of a test fixture. The cases do not define how duration produces an end value.
- UI labels/routes and error strings are not specified; steps use business actions and do not assert literal UI text.
- The Appointment feature does not exist in the supplied current source, so these are future-feature manual cases, not currently executable PetClinic tests.
