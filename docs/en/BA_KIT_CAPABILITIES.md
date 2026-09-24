# BA Kit Capabilities

BA Kit is a set of capabilities that helps a **Business Analyst work with requirements and BA artifacts**. It is not an autonomous replacement for the BA. The Human BA still owns stakeholder/customer communication, business decisions, Business Rule confirmation, and baseline approval.

BA Kit owns **WHAT — what the system must do**. Technical ownership and implementation belong downstream.

## What inputs can BA Kit work with?

| Input | What BA Kit uses it for | Important boundary |
|---|---|---|
| Requirement, CR, user notes, meeting notes | Gap, ambiguity, edge-case, and missing-rule review | Ambiguous wording never becomes a decision automatically |
| Current source/project | Brownfield discovery and CURRENT_SYSTEM evidence | Current behavior is evidence, not automatically target behavior |
| Existing SRS/BR/Markdown | Review or controlled update | Preserve unaffected approved semantics |
| Existing DOCX | Document-only review/edit or delivery | If canonical Markdown exists, do not change business meaning only in DOCX |
| Word .docx template | Produce SRS/DOCX in an organization layout | RC1 does **not bundle a default SRS_TEMPLATE.docx** |
| Screenshot/image/PDF export | Visual evidence, UI description, gap finding, diagram reconstruction | Only claim what is observable; hidden rules still need Human confirmation |
| Figma | Visual source when the runtime has access/integration | Otherwise export screenshot/PDF/local artifacts |
| Existing HTML prototype/UI | Interaction/state review and SRS UI description | A prototype is not business authority |
| Existing .drawio | Review, edit, sync, restyle | Semantic changes must return to BR/SRS first |
| Approved Business Rules/SRS | Produce Draw.io, DOCX, and Engineering Handoff | Derived artifacts may not change source semantics |

## Core capabilities

### 1. Requirement review and gap finding

BA Kit can:

- inspect the BA's incoming brief;
- find ambiguity, contradictions, and missing cases;
- ask about frequently omitted areas such as actors/permissions, required fields, validation, state/lifecycle, search/filter, sorting, pagination/page size, row actions, error/edge cases, and destructive behavior;
- classify blocking vs non-blocking gaps;
- preserve **UNKNOWN** rather than choosing a plausible value.

Example:

~~~text
Review this requirement.
Find missing/unclear cases.
Do not write the SRS until I answer the blocking questions.
~~~

### 2. Brownfield/current-system discovery

For an existing project, BA Kit can use **codebase-discovery** to inspect relevant current behavior and record it as **CURRENT_SYSTEM** evidence.

~~~text
Review this CR against the current project.
Discover related screens/APIs/models first and separate:
- CURRENT_SYSTEM
- UNKNOWN
- questions that need BA confirmation.
~~~

Discovery does not replace BA decisions about target behavior.

### 3. Business Rules

From confirmed Human answers, BA Kit can produce traceable Business Rules while keeping these evidence classes distinct:

- CONFIRMED;
- CURRENT_SYSTEM;
- INFERRED;
- PROPOSED;
- UNKNOWN.

### 4. Create or update SRS

BA Kit can create/update a **canonical functional SRS in Markdown** from Confirmed BA Decisions and Approved Business Rules.

Useful sections may include:

- scope/actors;
- preconditions;
- functional requirements;
- Business Rules;
- validation;
- state/lifecycle;
- error/edge behavior;
- list/filter/sort/pagination;
- confirmed UI behavior;
- open items/UNKNOWN;
- traceability.

The SRS must not choose APIs, DB schemas, event schemas, locking, transaction strategy, or service architecture.

See [SRS and DOCX](SRS_DOCX_GUIDE.md).

### 5. Produce SRS/DOCX using a template

**document-docx** supports:

- new DOCX creation;
- editing an existing DOCX;
- Word-authored templates;
- docxtpl rendering for placeholder templates;
- structural editing with python-docx;
- comments/review workflows;
- quality gates and OOXML inspection.

BA Kit RC1 **does not include a built-in company SRS Word template**. If the organization has one, provide the .docx and select it as the delivery template.

The semantic source remains the canonical BA baseline; the Word template controls document structure/presentation only.

### 6. Create and edit Draw.io

**drawio-skill** produces editable **.drawio** artifacts, not only flattened images. In BA scope, prefer:

- business process flowcharts;
- actor/role swimlanes;
- user/task flows;
- state/lifecycle diagrams;
- decision trees;
- business-level context/interaction maps;
- screenshot/whiteboard reconstruction;
- review/edit of an existing .drawio.

PNG/SVG/PDF exports are available when the environment has the required draw.io tooling.

BA Kit must not use this capability to invent target technical architecture, ERDs, or service boundaries.

See [Draw.io, visual input, and prototypes](DIAGRAMS_PROTOTYPES.md).

### 7. Review Figma/image/UI and describe UI in the SRS

When a visual source is accessible, BA Kit can:

- identify visible screens/sections;
- list visible fields, labels, and controls;
- identify visible actions/states;
- compare the visual with the requirement;
- find gaps between visual evidence and business semantics;
- write confirmed UI behavior into the SRS.

Permissions, validation, backend rules, and hidden navigation may not be inferred from pixels alone.

### 8. Prototype/UI support — optional

With optional skills installed, BA Kit can use:

- **product-design-and-ux** for task/state/recovery/interface contracts;
- **frontend-design** for a local visual prototype;
- **playwright** for rendering/browser checks;
- **impeccable** for critique/polish;
- **web-accessibility** for accessibility review.

A prototype is a **visual proposal** that needs Human visual review. It does not become a business requirement or production implementation automatically.

### 9. Review/edit existing artifacts

Operations are distinct:

| Operation | Meaning |
|---|---|
| REVIEW | Read-only review; do not mutate artifacts or advance workflow |
| CREATE | Create a new artifact from sufficient authority |
| EDIT | Update the selected artifact while preserving unrelated approved semantics |
| CONTINUE | Resume from saved state; **never approval** |

### 10. Engineering Handoff

After explicit Human approval of the BA baseline and resolution of all blocking items, BA Kit creates **engineering-handoff.yml** containing:

- feature identity;
- approved immutable revision;
- Business Rules/SRS/decision source paths + SHA-256;
- open items;
- downstream policy;
- next stage = engineering-impact-analysis.

It does not contain repo/module owners, FE/BE owners, API/DB/event design, locking, or transaction strategy.

## Source of truth by artifact type

~~~text
Business semantics:
Confirmed BA Decisions
+ Approved Business Rules
+ Canonical SRS

Visual evidence:
Approved Figma / screenshot / prototype / diagram
(only confirmed visual/interaction meaning)

Delivery formatting:
Selected Word template

Current implementation:
CURRENT_SYSTEM evidence
~~~

Derived artifacts such as DOCX, Draw.io, or prototypes **may not silently change business semantics**.

## Required and optional capabilities

Required in BA Kit RC1:

- verification-before-completion
- codebase-discovery
- requirements-gap-auditor
- requirements-interrogator
- requirements-quality-check
- business-rule-extractor
- srs-function-document
- document-docx
- drawio-skill

Optional:

- product-design-and-ux
- frontend-design
- impeccable
- playwright
- web-accessibility

Doctor may report **DEGRADED** when optional capabilities are missing; required capabilities/contracts must still be present for READY.

## Outside BA Kit scope

BA Kit does not:

- communicate with customers instead of the BA;
- approve requirements/SRS automatically;
- choose architecture;
- assign repo/module/service ownership;
- design APIs/DB/events;
- choose locking/transaction strategy;
- implement production code.

Those responsibilities remain with Humans and downstream Engineering Impact/Dev/Test phases.

---

Tiếng Việt: [Khả năng BA Kit](../vi/BA_KIT_CAPABILITIES.md)
