# Normalized traceability and oracle matrix

Candidate source: raw-output/test-design/test-design-epic-1.md. Scenario IDs and requirement IDs are retained. “Covered” means the plan names at least one observable scenario; it does not mean a test was generated or executed.

## FR coverage

| BA source | Requirement | Candidate scenarios | Coverage | Main / alternate / negative |
|---|---|---|---|---|
| kits/ba/examples/CR-001/vi/04-srs-excerpt.md | FR-001 — Create Appointment with Pet, Veterinarian, start, duration, reason/description; valid creation is Scheduled; start is future in Asia/Ho_Chi_Minh; duration > 0 | TD-001, TD-002, TD-003 | Covered | Main create; negative now/past start and non-positive duration |
| kits/ba/examples/CR-001/vi/04-srs-excerpt.md | FR-002 — Scheduled appointments of the same Veterinarian must not overlap; touching endpoints are allowed | TD-004, TD-005, TD-010, TD-012, TD-013 | Covered | Negative same-vet overlap; alternate touching, other-vet, canceled/completed, and concurrent outcomes |
| kits/ba/examples/CR-001/vi/04-srs-excerpt.md | FR-003 — Edit/reschedule only while Scheduled; exclude the appointment being rescheduled from conflict checks | TD-006, TD-007, TD-008 | Covered | Main Scheduled edit/reschedule; negative conflicting target and terminal-state actions |
| kits/ba/examples/CR-001/vi/04-srs-excerpt.md | FR-004 — Cancel only while Scheduled; cancellation frees time and does not hard-delete | TD-008, TD-009, TD-010 | Covered | Main cancel; negative terminal-state action; alternate reuse of released interval |
| kits/ba/examples/CR-001/vi/04-srs-excerpt.md | FR-005 — Complete only while Scheduled; completion changes state to Completed and creates exactly one Visit | TD-008, TD-011 | Covered | Main completion; negative terminal-state action |
| kits/ba/examples/CR-001/vi/04-srs-excerpt.md | FR-006 — Clinic Staff can view Appointment; filters, sorting, pagination are UNKNOWN | TD-014 | Covered with explicit limits | Main visibility only; no list-policy outcome asserted |

## BR coverage

| BA source | Rule | Candidate scenarios | Coverage | Review note |
|---|---|---|---|---|
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-001 — Clinic Staff manages Appointment | TD-001, TD-014 | Covered | Actor/use is retained; no authorization behavior invented |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-002 — Appointment is separate from Visit | TD-011 | Covered | Distinct records are asserted; Visit field mapping is not |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-003 — Appointment carries Pet, Veterinarian, start, duration, reason/description | TD-001 | Covered | Submitted fields are preserved; requiredness/defaults are not inferred |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-004 — Start must be after current time in Asia/Ho_Chi_Minh | TD-002 | Covered | Strict boundary represented |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-005 — Duration > 0; maximum is UNKNOWN | TD-003 | Covered with UNKNOWN preserved | No upper-bound value or outcome asserted |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-006 — Only Scheduled appointments for same Veterinarian conflict; interval is [start, end) | TD-004, TD-005, TD-010, TD-012, TD-013 | Covered | Both touching directions and status/same-vet boundaries are represented |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-007 — Reschedule only Scheduled and exclude the primary Appointment from comparison | TD-006, TD-007 | Covered | Self-overlap case specifically checks exclusion |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-008 — Lifecycle Scheduled, Cancelled, Completed; only Scheduled can change | TD-001, TD-006, TD-008, TD-009, TD-011, TD-012 | Covered | Both allowed terminal transitions and 8 terminal-state/action combinations |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-009 — Cancellation releases time | TD-009, TD-010 | Covered | Follow-up booking checks observable release |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-010 — Completion creates exactly one Visit | TD-011 | Covered | Count of newly created Visit records |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-011 — No hard delete | TD-009 | Covered | Same Appointment record remains after cancellation |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-012 — No prohibition on same-Pet overlap | TD-005 | Covered | Same Pet and different Veterinarian overlap |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-013 — Simultaneous booking stores only a non-conflicting Appointment | TD-013 | Covered | Persisted state is the oracle; response contract stays unspecified |
| kits/ba/examples/CR-001/vi/03-approved-business-rules.md | BR-014 — Appointment can be viewed; filters/sort/pagination UNKNOWN | TD-014 | Covered with UNKNOWN preserved | Visibility only |

## Critical UNKNOWN oracle

| UNKNOWN | BA source → requirement/rule | Candidate output | Result |
|---|---|---|---|
| Appointment maximum duration | 03-approved-business-rules.md BR-005; 04-srs-excerpt.md FR-001/open item | TD-003; NFR Planning; Assumptions item 4 | Preserved. No limit or pass/fail behavior invented. |
| List filters | 04-srs-excerpt.md FR-006; 03-approved-business-rules.md BR-014 | TD-014; NFR Planning; Assumptions item 5 | Preserved. No filter scenarios or default filter assumed. |
| Default sorting | 04-srs-excerpt.md FR-006; 03-approved-business-rules.md BR-014 | TD-014; NFR Planning; Assumptions item 5 | Preserved. No order asserted. |
| Pagination/page size | 04-srs-excerpt.md FR-006; 03-approved-business-rules.md BR-014 | TD-014; NFR Planning; Assumptions item 5 | Preserved. No page behavior or size asserted. |

## Expected-outcome guard

Candidate outcomes stay within the approved baseline for future-time validation, positive duration, same-Veterinarian overlap, half-open boundaries, state restrictions, cancellation, completion, Visit count, and viewing. The plan does not assign an HTTP status/message, authorization mapping, default duration, reason requiredness, or Appointment-to-Visit field mapping.

Test levels are planning recommendations only. The current fullstack source is supplemental and does not establish an Appointment API or UI contract.
