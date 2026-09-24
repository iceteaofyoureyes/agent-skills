# Gap Review and Illustrative Human Decisions

This file demonstrates the distinction between gaps found in an incomplete input and answers later supplied by a Human. The answers below are separate example material; they are not present in [the initial requirement](01-input-requirement.md).

## Gaps before clarification

These questions are **UNKNOWN** from the initial requirement alone.

| Area | Questions to clarify |
|---|---|
| Actor and access | Which Clinic Staff roles may create, view, edit, reschedule, cancel, or complete? Are there record-visibility limits? |
| Appointment and Visit | Is Appointment a separate concept from Visit? What should completion create or update? |
| Required fields | Which Pet, Veterinarian, date/time, duration, and reason/details are required? |
| Start datetime | Must an appointment be in the future? Which timezone governs the comparison? |
| Duration | What values are valid? Is there a maximum? |
| Conflict scope | Which appointment statuses count? Is the conflict per Pet, Veterinarian, or both? |
| Interval semantics | Are adjacent appointments allowed when one ends exactly as the next starts? |
| Rescheduling | Which statuses can be rescheduled? Does the appointment conflict with itself during validation? |
| Lifecycle | Which statuses exist, and which transitions are allowed? |
| Cancellation | Which statuses can be cancelled? Does cancellation release the time slot? |
| Completion | Does completion create a Visit? Can it create more than one? Which data carries over? |
| Deletion | Is hard deletion allowed, or must the record remain? |
| Appointment list | Which filters, sort order, and pagination are required? |
| Concurrent booking outcome | If two requests conflict, what business outcome is allowed? |

No current PetClinic behavior is asserted by this documentation-only example. A real brownfield review must discover and label existing behavior as **CURRENT_SYSTEM** evidence.

## Later illustrative Human decisions

The following answers show the supplied Appointment Scheduling semantic baseline. They are example decisions, not conclusions an agent may infer from the initial input.

| Area | Illustrative Human answer |
|---|---|
| Actor | Clinic Staff. |
| Appointment and Visit | Appointment is a separate concept from Visit. |
| Required fields | Pet, Veterinarian, start datetime, duration, and reason/description. |
| Start datetime | Must be later than the current time; use timezone Asia/Ho_Chi_Minh. |
| Duration | Must be greater than zero. Maximum duration remains **UNKNOWN**. |
| Conflict scope | Only Scheduled Appointments for the same Veterinarian conflict. |
| Interval semantics | Use half-open interval **[start, end)**; appointments that touch are allowed. |
| Rescheduling | Only Scheduled Appointments may be rescheduled; exclude the appointment itself from conflict checks. |
| Lifecycle | Scheduled, Cancelled, Completed. Creation starts as Scheduled. |
| Edit, cancel, complete | Only Scheduled Appointments may be edited, rescheduled, cancelled, or completed. |
| Cancellation | Cancelling releases the time slot. |
| Completion | Completing creates exactly one new Visit. |
| Deletion | No hard delete. |
| Pet overlap | The approved baseline imposes no prohibition on overlapping appointments for a Pet. |
| Concurrent booking outcome | Only a non-conflicting appointment is saved. Atomicity and locking remain technical design decisions. |
| Appointment list | Viewing is required. Filters, sorting, and pagination remain **UNKNOWN**. |

For a real feature, record who supplied each answer and its source. If any unknown is material to the next stage, keep it blocking and do not produce an Engineering Handoff.

## Illustrative open-item classification

For the contract-valid handoff fixture only, the example BA classifies the unresolved maximum-duration and appointment-list details as non-blocking for handing off the approved rules above. Both remain **UNKNOWN**; this classification does not approve a maximum or any list behavior. In real work, the BA must decide whether an unknown blocks the next stage.
