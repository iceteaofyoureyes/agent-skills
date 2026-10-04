# Gap Review and Illustrative Human Decisions

This file demonstrates the distinction between gaps found in an incomplete input and answers later supplied by a Human. The answers below are separate example material; they are not present in [the initial requirement](01-input-requirement.md).

## Gaps before clarification

These questions are **UNKNOWN** from the initial requirement alone.

| Area | Questions to clarify |
|---|---|
| Actor and access | Which Service Staff roles may create, view, edit, reschedule, cancel, or complete? Are there record-visibility limits? |
| Resource Request and Fulfillment Record | Is Resource Request a separate concept from Fulfillment Record? What should completion create or update? |
| Required fields | Which Resource, Coordinator, date/time, duration, and reason/details are required? |
| Start datetime | Must a request be in the future? Which timezone governs the comparison? |
| Duration | What values are valid? Is there a maximum? |
| Conflict scope | Which request statuses count? Is the conflict per Resource, Coordinator, or both? |
| Interval semantics | Are adjacent requests allowed when one ends exactly as the next starts? |
| Rescheduling | Which statuses can be rescheduled? Does the request conflict with itself during validation? |
| Lifecycle | Which statuses exist, and which transitions are allowed? |
| Cancellation | Which statuses can be cancelled? Does cancellation release the time slot? |
| Completion | Does completion create a Fulfillment Record? Can it create more than one? Which data carries over? |
| Deletion | Is hard deletion allowed, or must the record remain? |
| Resource Request list | Which filters, sort order, and pagination are required? |
| Concurrent booking outcome | If two requests conflict, what business outcome is allowed? |

No current SamplePlatform behavior is asserted by this documentation-only example. A real brownfield review must discover and label existing behavior as **CURRENT_SYSTEM** evidence.

## Later illustrative Human decisions

The following answers show the supplied Resource Request Submission semantic baseline. They are example decisions, not conclusions an agent may infer from the initial input.

| Area | Illustrative Human answer |
|---|---|
| Actor | Service Staff. |
| Resource Request and Fulfillment Record | Resource Request is a separate concept from Fulfillment Record. |
| Required fields | Resource, Coordinator, start datetime, duration, and reason/description. |
| Start datetime | Must be later than the current time; use timezone Asia/Ho_Chi_Minh. |
| Duration | Must be greater than zero. Maximum duration remains **UNKNOWN**. |
| Conflict scope | Only Scheduled Resource Requests for the same Coordinator conflict. |
| Interval semantics | Use half-open interval **[start, end)**; requests that touch are allowed. |
| Rescheduling | Only Scheduled Resource Requests may be rescheduled; exclude the request itself from conflict checks. |
| Lifecycle | Scheduled, Cancelled, Completed. Creation starts as Scheduled. |
| Edit, cancel, complete | Only Scheduled Resource Requests may be edited, rescheduled, cancelled, or completed. |
| Cancellation | Cancelling releases the time slot. |
| Completion | Completing creates exactly one new Fulfillment Record. |
| Deletion | No hard delete. |
| Resource overlap | The approved baseline imposes no prohibition on overlapping requests for a Resource. |
| Concurrent booking outcome | Only a non-conflicting request is saved. Atomicity and locking remain technical design decisions. |
| Resource Request list | Viewing is required. Filters, sorting, and pagination remain **UNKNOWN**. |

For a real feature, record who supplied each answer and its source. If any unknown is material to the next stage, keep it blocking and do not produce an Engineering Handoff.

## Illustrative open-item classification

For this documentation fixture only, the example BA classifies the unresolved maximum-duration and request-list details as non-blocking for the illustrative candidate. Both remain **UNKNOWN**; this classification does not approve a maximum or any list behavior. In real work, the BA must decide whether an unknown blocks the next stage.
