# Draw.io, Visual Input, and Prototypes

BA Kit includes required **drawio-skill** capability and optional UX/UI capabilities. This page describes how to use them within BA boundaries.

## 1. What is Draw.io for in BA Kit?

drawio-skill is broad, but in the BA phase it should primarily represent **business behavior with established authority**.

Appropriate BA diagrams include:

| Type | Use |
|---|---|
| Business process flowchart | Business steps and decisions |
| Swimlane | Which actor/role performs each step |
| User/task flow | Functional user paths |
| State/lifecycle | Confirmed states and transitions |
| Decision tree | Rules and decision branches |
| Context/interaction map | Business-level interactions, not target architecture |
| Existing diagram review | Review/edit/sync an existing .drawio |
| Image/whiteboard → editable | Reconstruct a screenshot/photo into editable .drawio for review |

## 2. Example lifecycle from Business Rules

Given confirmed semantics:

~~~text
- Create Appointment → Scheduled
- Only Scheduled can be cancelled/completed
- Cancel → Cancelled and releases slot
- Complete → Completed and creates exactly one Visit
~~~

Prompt:

~~~text
Create an editable Draw.io Appointment lifecycle from the approved Business Rules.
Output docs/diagrams/appointment-lifecycle.drawio plus a PNG preview.
Do not add transitions that are not confirmed.
~~~

Expected semantic shape:

~~~text
          ┌───────────┐
Create ──▶│ Scheduled │
          └─────┬─────┘
                │
        ┌───────┴────────┐
        │                │
      Cancel          Complete
        │                │
        ▼                ▼
  ┌───────────┐     ┌───────────┐
  │ Cancelled │     │ Completed │
  └───────────┘     └───────────┘
      releases          creates
        slot          exactly 1 Visit
~~~

The diagram may not silently add Rescheduled/No-show/Pending states.

## 3. drawio-skill outputs

Primary source:

~~~text
diagram.drawio
~~~

Optional exports when tooling is available:

~~~text
diagram.png
diagram.svg
diagram.pdf
~~~

The skill provides structural validation and visual-review workflows. The .drawio remains the editable source; PNG/PDF are derivative delivery artifacts.

## 4. Review and update an existing diagram

Review-only:

~~~text
Review appointment-flow.drawio against the current Business Rules.
Report mismatches and ambiguous edges only; do not edit the file.
~~~

Update:

~~~text
BR-012 is now Human-approved.
Update only the BR-012-related part of appointment-flow.drawio.
Preserve unrelated layout/style.
~~~

If a diagram change introduces new business meaning, classify it as PROPOSED/UNKNOWN and return to Human confirmation instead of silently changing semantics.

## 5. Technical diagrams and BA boundaries

drawio-skill itself can produce architecture, ERD, C4, network, and API diagrams.

BA Kit must not use that power to choose target:

- service boundaries;
- API shapes;
- DB schemas;
- event architecture;
- deployment;
- locking/transactions.

An **as-is CURRENT_SYSTEM** technical diagram may be documented when backed by evidence, but target technical design belongs to Engineering Impact/Dev.

## 6. Visual inputs: Figma, screenshot, image, PDF, HTML

A visual source may be used to:

- identify visible screens/sections;
- list visible fields/labels/controls;
- identify visible actions and states;
- compare visuals with requirements;
- find missing decisions;
- write confirmed UI behavior into the SRS;
- derive a visual/prototype.

### Figma

BA Kit does not bundle a Figma connector.

If the runtime has a Figma integration and the Human grants access, use it.

Otherwise:

~~~text
Figma
→ export screenshot / image / PDF / HTML reference
→ provide a local artifact the agent can read
~~~

An inaccessible Figma link is not permission to guess.

## 7. Visual evidence is not business authority

If a screenshot shows a **Delete** button, the agent may record:

~~~text
OBSERVED VISUAL:
A Delete action is visible.
~~~

It may not conclude:

~~~text
CONFIRMED:
The user may hard-delete the record.
~~~

The BA must still confirm permission, soft/hard deletion, confirmation rules, and applicable states.

The same applies to required fields, validation, roles, default sort, page size, and backend side effects.

## 8. From visual source to SRS

~~~text
Here is the correspondence-list screenshot and CR-208.

1. List visible UI elements.
2. Compare them with the requirement.
3. Ask about missing search/filter, sort, pagination/page size, row actions, permissions, empty/error/loading states.
4. Only after I answer, update the UI Behavior section of the canonical SRS.
~~~

This reflects the original BA Kit goal: the agent helps the BA discover missing cases without replacing BA decisions.

## 9. Prototype — optional capability

When optional skills are installed:

~~~text
Approved BA semantics
        ↓
product-design-and-ux
        ↓
interaction/task/state contract
        ↓
frontend-design
        ↓
local prototype
        ↓
Playwright / visual review
        ↓
Human visual gate
~~~

A prototype may be local HTML/React or another project-appropriate form, but it remains a **prototype**, not production implementation.

When visual direction is not confirmed, the output is **PROPOSED**.

## 10. Prototype states

When relevant, review more than a happy path:

- normal/data;
- empty;
- loading;
- validation errors;
- permission/disabled;
- destructive confirmation;
- success/error feedback;
- desktop/mobile/reflow when in scope.

Do not invent business states without evidence; unresolved UI behavior should be a question/proposal.

## 11. Prompt examples

### Draw.io flowchart

~~~text
Create an editable Draw.io business flow from BR-001..BR-008.
Also export a PNG preview.
Reference BRs on nodes/edges where useful.
Do not add new business rules.
~~~

### Swimlane

~~~text
Create a swimlane for the confirmed correspondence approval process.
If ownership of a step is unknown, keep it UNKNOWN and report it instead of assigning an actor.
~~~

### Visual review

~~~text
Review this screenshot/Figma export against the current SRS.
Separate observed visual, mismatch, missing decision, and proposal.
Do not edit the SRS yet.
~~~

### Prototype

~~~text
Using the confirmed SRS and visual reference, create a local desktop/mobile prototype.
This is a visual proposal; do not change Business Rules.
Render the main states for Human review.
~~~

---

Tiếng Việt: [Draw.io, visual input và prototype](../vi/DIAGRAMS_PROTOTYPES.md)
