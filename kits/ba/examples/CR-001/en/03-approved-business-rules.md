# Approved Business Rules — Illustrative Example

This is an illustrative output based on the separate Human answers in [02-gap-review.md](02-gap-review.md). These rules are not present in the initial requirement and are not runtime-generated golden text. Example IDs are not mandatory.

| Stable BR-* ID (illustrative values) | Rule | Evidence |
|---|---|---|
| BR-001 | Service Staff may manage requests. | CONFIRMED in the example decision record. |
| BR-002 | A Resource Request is a separate concept from a Fulfillment Record. | CONFIRMED in the example decision record. |
| BR-003 | Resource Request data includes Resource, Coordinator, start datetime, duration, and reason/description. | CONFIRMED in the example decision record. |
| BR-004 | Start datetime must be later than current time, evaluated in Asia/Ho_Chi_Minh. | CONFIRMED in the example decision record. |
| BR-005 | Duration must be greater than zero. Maximum duration is UNKNOWN. | CONFIRMED minimum; maximum remains UNKNOWN. |
| BR-006 | Conflict checks apply only to Scheduled Resource Requests for the same Coordinator. Use half-open interval [start, end), so touching requests are allowed. | CONFIRMED in the example decision record. |
| BR-007 | A reschedule is allowed only while Scheduled and excludes the request itself from conflict checks. | CONFIRMED in the example decision record. |
| BR-008 | The lifecycle is Scheduled, Cancelled, Completed. Creation produces Scheduled; only Scheduled may be edited, rescheduled, cancelled, or completed. | CONFIRMED in the example decision record. |
| BR-009 | Cancellation releases the time slot. | CONFIRMED in the example decision record. |
| BR-010 | Completion creates exactly one new Fulfillment Record. | CONFIRMED in the example decision record. |
| BR-011 | Resource Request records are not hard-deleted. | CONFIRMED in the example decision record. |
| BR-012 | The approved baseline contains no Resource-overlap prohibition. | CONFIRMED in the example decision record. |
| BR-013 | The business outcome for concurrent booking is that only a non-conflicting request is saved. | CONFIRMED in the example decision record; technical atomicity/locking is out of BA scope. |
| BR-014 | Resource Request viewing is required. Filter, sort, and pagination behavior remain UNKNOWN. | CONFIRMED for viewing; remaining list behavior is UNKNOWN. |

The rule IDs, ordering, and wording are illustrative. Preserve the actual source references and evidence labels in a real BA baseline.
