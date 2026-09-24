# SRS and DOCX in BA Kit

This page separates two concepts that are easy to confuse:

1. **Canonical SRS** — the BA semantic requirements artifact.
2. **DOCX delivery** — the Word document used for review, customer/internal delivery, or an organization template.

They are not the same layer.

## 1. Which SRS template does BA Kit use?

BA Kit RC1 currently uses a **functional SRS contract**, not one rigid Markdown template for every feature.

The **srs-function-document** skill builds the SRS from:

~~~text
Confirmed BA Decisions
+
Approved Business Rules
+
current canonical SRS (when updating)
+
source evidence / workflow state
~~~

Sections are included when relevant, for example:

~~~text
Feature / Scope
Actors
Preconditions
Functional Requirements
Business Rules
Validation
States / Lifecycle
Error & Edge Behavior
List / Filter / Sort / Pagination
UI Behavior
Open Items / UNKNOWN
Traceability
~~~

Not every feature needs every section. The agent must not fill unused template sections with invented content.

## 2. Does the repository include SRS_TEMPLATE.docx?

**No.**

The BA Kit RC1 production repository currently **does not bundle a default SRS_TEMPLATE.docx**.

That means:

- BA Kit can create canonical SRS Markdown;
- BA Kit can create/edit DOCX and work from Word templates;
- but the organization's official Word template must be **provided or selected by a Human**.

If a default template is later bundled, it must have its own version/provenance/license and this documentation must be updated.

## 3. When the company has a Word template

Prefer a Human-owned **.docx** template.

Example project layout:

~~~text
docs/
├── srs/
│   └── CR-123.md
└── templates/
    └── COMPANY_SRS_TEMPLATE.docx
~~~

Prompt:

~~~text
Create the SRS DOCX for CR-123 from docs/srs/CR-123.md.
Use templates/COMPANY_SRS_TEMPLATE.docx as the delivery template.
Do not change business semantics; if a section lacks confirmed data, keep it UNKNOWN or report it.
~~~

### Lane A — placeholder template

If the Word file is prepared for **docxtpl**, it may contain Jinja placeholders such as:

~~~text
{{ feature_name }}
{{ scope }}
{{ actor }}
{% for requirement in requirements %}
...
{% endfor %}
~~~

document-docx can render structured context into the template while preserving Word-owned styles/layout.

### Lane B — Word template without placeholders

If the template is a regular DOCX with headings/tables/styles but no Jinja tags:

- inspect its structure and styles;
- map canonical SRS content into matching sections/tables;
- use structural editing;
- preserve formatting where practical;
- report unmapped sections instead of inventing content.

This lane needs stronger rendering review because Word structures can be complex.

## 4. When no template is available

BA Kit may create a DOCX from the canonical SRS using a reasonable document structure.

That output is a **generic delivery DOCX**, not an “official company template” document.

~~~text
Export the current canonical SRS to DOCX for internal review.
There is no company template; use standard Word headings and a traceability table.
~~~

## 5. When the only existing SRS is DOCX

The routing contract allows a document-only workflow.

If no canonical Markdown exists and the Human selects the existing DOCX as the standalone Word source:

~~~text
Review Existing-SRS.docx.
Report gaps/inconsistencies first; do not modify the file yet.
~~~

Once canonical Markdown exists, a business-semantic change must flow:

~~~text
Confirmed decision / BR
        ↓
Canonical SRS Markdown
        ↓
Regenerate / update DOCX
~~~

Do not change business meaning only in Word.

## 6. A template is not semantic authority

Suppose the template contains:

~~~text
Maximum duration: 60 minutes
~~~

but the BA baseline never confirmed a maximum.

The agent may not copy 60 minutes into the requirement just because it appears in the template.

Treat it as:

~~~text
UNKNOWN / template content requiring BA confirmation
~~~

A template must not invent:

- permissions;
- state transitions;
- validation;
- default sorting;
- page size;
- API/DB behavior.

## 7. Updating an SRS

When updating:

- preserve unrelated confirmed content;
- change only semantics supported by new authority;
- preserve UNKNOWN;
- surface conflicts;
- keep traceability;
- never set APPROVED_FOR_ENGINEERING by generation alone.

~~~text
Update SRS CR-123 using the new decisions in decisions.md.
Only change pagination.
Preserve all other approved Business Rules.
Report the semantic diff afterward.
~~~

## 8. DOCX quality gate

document-docx provides workflows/scripts for checking:

- unresolved template tags;
- parseability;
- comments/revisions/OOXML;
- structure;
- cross-viewer rendering;
- accessibility hygiene.

For externally delivered documents:

1. validate the document;
2. render/open in Microsoft Word when available;
3. check at least one secondary viewer when portability matters;
4. require Human content review before release.

## 9. Typical canonical-SRS-to-Word mapping

| Canonical BA content | Common Word section |
|---|---|
| Feature identity / scope | Introduction / Scope |
| Actors | Actors / User roles |
| Functional requirements | Functional Requirements |
| Business Rules | Business Rules |
| Validation | Validation / Constraints |
| State/lifecycle | State / Workflow |
| UI behavior | Screen / UI Specification |
| Draw.io diagram | Business Flow / Process Diagram |
| UNKNOWN/open items | Open Questions / TBD |
| Traceability | Traceability Matrix |

The actual section names come from the selected template; this is only a mapping example.

## 10. Prompt examples

### Create SRS Markdown

~~~text
Create the canonical functional SRS from confirmed Business Rules.
Keep UNKNOWN explicit, add traceability, and do not choose technical design.
~~~

### Create DOCX from a template

~~~text
Create docs/output/CR-123-SRS.docx from docs/srs/CR-123.md.
Template: docs/templates/COMPANY_SRS_TEMPLATE.docx.
Preserve template layout/styles.
If a section has no confirmed data, report it or keep UNKNOWN; do not invent it.
~~~

### Review DOCX

~~~text
Review SRS.docx against the current canonical SRS.
Only report semantic mismatches, missing sections, and formatting issues.
Do not edit the file yet.
~~~

---

Tiếng Việt: [SRS và DOCX](../vi/SRS_DOCX_GUIDE.md)
