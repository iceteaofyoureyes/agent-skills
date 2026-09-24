# BA Kit Usage Guide by Scenario

Use BA Kit through **natural intent**; you do not need to remember individual skill names. The workflow routes work based on operation, project mode, artifact, and Human Gate.

## Operation rules

~~~text
CREATE   create a new artifact
EDIT     update an artifact
REVIEW   read-only; do not mutate
CONTINUE resume workflow; never approve
~~~

The Human remains business authority in every mode.

## Scenario 1 — Review an incoming requirement

~~~text
Review this requirement.
Find ambiguity, missing rules, edge cases, and questions I need to take back to stakeholders.
Do not write the SRS yet.
~~~

Expected: gap list, evidence classification, blocking/non-blocking questions, no artifact mutation.

## Scenario 2 — Brownfield review against the current project

~~~text
Review CR-123 against the current codebase.
Discover current behavior first.
Separate CURRENT_SYSTEM, INFERRED, and UNKNOWN.
Then ask me for the missing decisions.
~~~

Current behavior does not become a target requirement automatically.

## Scenario 3 — Review a CRUD/list screen

~~~text
Review this correspondence-list feature.
Check missing:
- search/filter;
- default sort;
- pagination/page size;
- displayed fields;
- row actions;
- states;
- permissions;
- empty/loading/error;
- validation and destructive actions.
Only ask about points without evidence.
~~~

## Scenario 4 — Screenshot/Figma/PDF/HTML input

If direct Figma access is unavailable, export the visual to a readable local artifact.

~~~text
Review this screenshot together with CR-208.
List observed UI elements, compare with the requirement, and ask about gaps.
Do not infer permissions/validation/business rules from pixels.
~~~

After Human clarification:

~~~text
Update the canonical SRS UI Behavior section from the confirmed decisions.
~~~

## Scenario 5 — Answer clarification and build Business Rules

~~~text
Default sort is createdAt descending.
Default page size is 20; allowed values are 20/50/100.
Only Supervisor has Cancel.
~~~

Then:

~~~text
Build the CONFIRMED Business Rules.
Keep unanswered items UNKNOWN.
Report which rules remain blocking.
~~~

**ANSWER is not APPROVE.**

## Scenario 6 — Create canonical SRS

~~~text
Create the canonical functional SRS from confirmed decisions and Business Rules.
Preserve traceability.
Do not choose API/DB/architecture.
Keep UNKNOWN explicit.
~~~

## Scenario 7 — Update existing SRS

~~~text
Update SRS CR-123 using the new decisions in decisions.md.
Only change sort/pagination.
Preserve other approved rules.
Report the semantic diff afterward.
~~~

## Scenario 8 — Export SRS DOCX using a company template

~~~text
Create a DOCX from docs/srs/CR-123.md.
Use docs/templates/COMPANY_SRS_TEMPLATE.docx.
Preserve template layout/styles.
If a section lacks confirmed data, keep UNKNOWN or report it; do not invent it.
~~~

BA Kit RC1 **does not bundle a default SRS Word template**.

## Scenario 9 — Review/edit an existing DOCX

~~~text
Review Existing-SRS.docx against the current requirement and Business Rules.
Only report mismatches, missing sections, and format issues.
Do not edit the file yet.
~~~

When canonical Markdown exists, update semantic meaning there first, then synchronize DOCX.

## Scenario 10 — Create Draw.io flowchart/state/swimlane

~~~text
Create an editable .drawio business flow from the approved Business Rules.
Also export a PNG preview.
Reference BR IDs where useful.
Do not add unconfirmed transitions/rules.
~~~

## Scenario 11 — Review/update existing Draw.io

~~~text
Review process.drawio against the canonical SRS.
Report mismatches only; do not edit it.
~~~

After approval:

~~~text
Update process.drawio for newly approved BR-022 only.
Preserve unrelated layout/style.
~~~

## Scenario 12 — UI prototype — optional

~~~text
Create a local prototype from the confirmed SRS and screenshot reference.
Cover desktop/mobile and confirmed states.
This is a visual proposal; do not change Business Rules.
~~~

## Scenario 13 — Review without changing workflow

~~~text
Review the current SRS for completeness and consistency.
REVIEW only. Do not edit files or advance workflow.
~~~

## Scenario 14 — Request changes

~~~text
Request changes for SRS revision SRS-42:
- FR-12 lacks empty-state behavior;
- BR-08 trace is wrong;
- page size is unresolved.
Do not approve.
~~~

## Scenario 15 — Approve BA baseline

~~~text
I approve Business Rules revision BR-42
and SRS revision SRS-42
as the BA baseline for Engineering.
~~~

Approval must be explicit. **Continue is not approval.**

## Scenario 16 — Create Engineering Handoff

~~~text
Create the Engineering Handoff from the approved baseline.
~~~

Expected: immutable revision, source path + SHA-256, open items, downstream policy, next stage; no technical ownership/design.

## Scenario 17 — Continue

~~~text
Continue.
~~~

The workflow reads **workflow-state.json** and performs the next valid action. It does not answer questions for the Human, approve artifacts, or bypass blocking gates.

## Full working flow

~~~text
BA input
→ REVIEW
→ brownfield/visual discovery when needed
→ gaps/questions
→ Human ANSWER
→ Business Rules
→ canonical SRS
→ Draw.io / prototype draft when needed
→ DOCX delivery when needed
→ Human REQUEST_CHANGES / APPROVE
→ Engineering Handoff
~~~

Derived artifacts should be regenerated/updated from canonical sources after semantic changes.

## See also

- [BA Kit capabilities](BA_KIT_CAPABILITIES.md)
- [Workflow and Human Gates](BA_KIT_WORKFLOW.md)
- [SRS and DOCX](SRS_DOCX_GUIDE.md)
- [Draw.io, visual input, and prototypes](DIAGRAMS_PROTOTYPES.md)
- [CR-001 example](../../kits/ba/examples/CR-001/README.md)

---

Tiếng Việt: [Hướng dẫn sử dụng](../vi/BA_KIT_USAGE_GUIDE.md)
