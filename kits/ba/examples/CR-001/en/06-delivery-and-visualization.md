# CR-001 — Draw.io, DOCX, and Visual Delivery Examples

This file adds no business rules. It demonstrates how to use delivery/visual capabilities **after approved semantics exist**.

## 1. Draw.io lifecycle

Semantic sources:

- BR-008: Scheduled, Cancelled, Completed; create → Scheduled; actions only from Scheduled;
- BR-009: Cancel releases the slot;
- BR-010: Complete creates exactly one Visit;
- BR-011: no hard delete.

Example prompt:

~~~text
From BR-008..BR-011 in 03-approved-business-rules.md,
create docs/diagrams/CR-001-appointment-lifecycle.drawio.

Requirements:
- editable .drawio;
- PNG preview;
- relevant BR labels;
- no unconfirmed statuses/transitions.
~~~

Expected semantic shape:

~~~text
Create
  ↓
Scheduled
  ├── Cancel ───→ Cancelled
  │               releases slot
  └── Complete ─→ Completed
                  creates exactly one Visit
~~~

The diagram is derived. Change BR/SRS first when lifecycle semantics change.

## 2. Draw.io booking flow

Semantic sources: BR-003..BR-007 and BR-013.

~~~text
Create a business flowchart for create/reschedule Appointment.
Show business decisions only:
- required data;
- future start;
- duration > 0;
- same-Veterinarian Scheduled conflict;
- [start,end), touching allowed;
- reschedule excludes itself;
- only a non-conflicting appointment is saved.

Do not describe API, transaction, DB constraint, or locking.
~~~

The save outcome is business meaning; atomicity mechanism belongs to Engineering.

## 3. SRS DOCX using a template

The example repository **does not contain a company SRS template**.

Assume a real project provides:

~~~text
docs/templates/COMPANY_SRS_TEMPLATE.docx
~~~

and canonical SRS:

~~~text
docs/srs/CR-001.md
~~~

Prompt:

~~~text
Create docs/output/CR-001-SRS.docx from docs/srs/CR-001.md.
Use docs/templates/COMPANY_SRS_TEMPLATE.docx.
Preserve layout/styles.
Maximum duration remains UNKNOWN.
Do not invent unresolved filter/sort/pagination details.
~~~

If a template section lacks authoritative content, report it or keep UNKNOWN.

## 4. Without a template

~~~text
Export the canonical SRS to a generic DOCX for internal review.
Use clear headings/tables.
Do not describe it as a company-template SRS.
~~~

## 5. Visual/Figma lane

The CR-001 fixture contains no screenshot/Figma source, so it does **not fabricate UI**.

If a real project supplies an Appointment screenshot:

~~~text
Review the screenshot against the canonical SRS.
Separate:
- observed fields/actions;
- SRS mismatch;
- missing decisions;
- visual proposal.

Do not update SRS until the Human answers.
~~~

If the image shows Delete while BR-011 says no hard delete, that is a mismatch for Human review, not permission to rewrite BR-011.

## 6. Prototype lane — optional

~~~text
Using confirmed SRS and visual references, create a local prototype.
Render confirmed normal/empty/error states.
This is a visual proposal; do not change Business Rules.
~~~

Prototype output requires a separate Human visual gate.

## 7. Authority direction

~~~text
Human decisions / BR / canonical SRS
        ↓
Draw.io / DOCX / prototype
~~~

Never:

~~~text
DOCX/diagram/prototype
        ✗
silently creates a new business rule
~~~

See:

- [SRS and DOCX](../../../../../docs/en/SRS_DOCX_GUIDE.md)
- [Draw.io, visual input, and prototypes](../../../../../docs/en/DIAGRAMS_PROTOTYPES.md)
