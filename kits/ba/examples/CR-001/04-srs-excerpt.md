# SRS Excerpt — Illustrative Example

This excerpt illustrates traceability from requirements to Business Rules. The IDs and wording are examples, not mandatory runtime output.

| Example requirement ID | Requirement | Trace |
|---|---|---|
| FR-001 | Clinic Staff can create an Appointment with Pet, Veterinarian, start datetime, duration, and reason/description. A valid creation starts in Scheduled status. Start must be later than current time in Asia/Ho_Chi_Minh; duration must be greater than zero. | BR-001, BR-003, BR-004, BR-005, BR-008 |
| FR-002 | A Scheduled Appointment must not overlap another Scheduled Appointment for the same Veterinarian. Treat intervals as [start, end); touching appointments are allowed. | BR-006 |
| FR-003 | Clinic Staff can edit or reschedule an Appointment only while it is Scheduled. Conflict validation excludes the Appointment being rescheduled. | BR-007, BR-008 |
| FR-004 | Clinic Staff can cancel an Appointment only while it is Scheduled. Cancellation releases its time slot; the Appointment is not hard-deleted. | BR-008, BR-009, BR-011 |
| FR-005 | Clinic Staff can complete an Appointment only while it is Scheduled. Completion creates exactly one new Visit and moves the Appointment to Completed. | BR-002, BR-008, BR-010 |
| FR-006 | Clinic Staff can view Appointments. Filter, sort, and pagination behavior remain UNKNOWN pending a BA decision. | BR-001, BR-014 |

## Out of BA Technical Scope

This SRS does not choose repositories or modules, API or event schemas, database design, service boundaries, locking, transaction strategy, or the implementation mechanism for concurrent booking. Engineering Impact and downstream engineering work make those decisions while preserving the approved business outcome.

Maximum Appointment duration is UNKNOWN. Do not invent a limit or treat this excerpt as resolving that question.
