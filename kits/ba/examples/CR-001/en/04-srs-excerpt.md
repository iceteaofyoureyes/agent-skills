# SRS Excerpt — Illustrative Example

This excerpt illustrates traceability from requirements to Business Rules. The IDs and wording are examples, not mandatory runtime output.

| Stable FR-* ID (illustrative values) | Requirement | Trace |
|---|---|---|
| FR-001 | Service Staff can create a Resource Request with Resource, Coordinator, start datetime, duration, and reason/description. A valid creation starts in Scheduled status. Start must be later than current time in Asia/Ho_Chi_Minh; duration must be greater than zero. | BR-001, BR-003, BR-004, BR-005, BR-008 |
| FR-002 | A Scheduled Resource Request must not overlap another Scheduled Resource Request for the same Coordinator. Treat intervals as [start, end); touching requests are allowed. | BR-006 |
| FR-003 | Service Staff can edit or reschedule a Resource Request only while it is Scheduled. Conflict validation excludes the Resource Request being rescheduled. | BR-007, BR-008 |
| FR-004 | Service Staff can cancel a Resource Request only while it is Scheduled. Cancellation releases its time slot; the Resource Request is not hard-deleted. | BR-008, BR-009, BR-011 |
| FR-005 | Service Staff can complete a Resource Request only while it is Scheduled. Completion creates exactly one new Fulfillment Record and moves the Resource Request to Completed. | BR-002, BR-008, BR-010 |
| FR-006 | Service Staff can view Resource Requests. Filter, sort, and pagination behavior remain UNKNOWN pending a BA decision. | BR-001, BR-014 |

## Out of BA Technical Scope

This SRS does not choose repositories or modules, API or event schemas, database design, service boundaries, locking, transaction strategy, or the implementation mechanism for concurrent booking. Engineering Impact and downstream engineering work make those decisions while preserving the approved business outcome.

Maximum Resource Request duration is UNKNOWN. Do not invent a limit or treat this excerpt as resolving that question.
