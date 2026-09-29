# Coverage note

**Coverage techniques from the pinned skill**

- Use-case testing: create and view a valid Appointment.
- Boundary-value analysis: start at T0−1 minute, exactly T0, and T0+1 minute; both touching directions for [start, end).
- Equivalence partitions: positive, zero, and negative duration; Scheduled versus Cancelled/Completed state.
- Decision rules: same Veterinarian overlap, different Veterinarian, cancellation release, Completed status, and simultaneous conflicting submissions.
- State-transition coverage: Scheduled → Cancelled/Completed and each edit/reschedule/cancel/complete action against both terminal states.

**Selected cases:** 27 manual cases, all P1 after combining the overlapping create/view end-to-end path from TD-001 and TD-014 into TC-001. The merged case keeps P1, the higher priority of the create path; the view-only P2 intent is covered in that same end-to-end case. This avoids a duplicate view assertion. There is no P0 case.

**Deferred / not covered:**

- Appointment maximum duration, because BA keeps it UNKNOWN.
- List filters, default sorting, pagination, and page size, because BA keeps them UNKNOWN.
- Exact UI labels/routes, the editable field set, and the duration-to-interval-end input mapping, because those interface details are not supplied.
- Authorization rules, response codes/messages, and Visit field mapping, because they are not in the approved behavior.

**Reason:** preserve the BA and Test Design oracle; do not fill unknown decisions with assumed behavior. This note describes case coverage only. It does not import, automate, or execute cases.
