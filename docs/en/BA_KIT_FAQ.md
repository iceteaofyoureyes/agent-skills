# BA Kit FAQ

### What can BA Kit actually do?

BA Kit reviews requirements, discovers current-system behavior when needed, finds gaps, supports clarification, builds Business Rules, creates/updates SRS, creates/edits DOCX, creates/edits Draw.io business diagrams, supports visual inputs and optional prototypes, then produces an Engineering Handoff after Human approval.

See [BA Kit capabilities](BA_KIT_CAPABILITIES.md).

### Do I need Skills Manager?

No. Repository installer/Doctor workflows are independent. Skills Manager is optional.

### Do I need to know individual skill names?

No. Ask for the outcome; ba-workflow routes the required capability.

### Does BA Kit replace BA customer communication?

No. The BA owns elicitation, business decisions, customer/stakeholder communication, and approval.

### Does BA Kit write production code?

No. Optional prototyping may create local UI code for review, but that is a prototype/visual proposal, not production implementation.

### Can BA Kit inspect the current project?

Yes. Brownfield mode uses codebase-discovery when current behavior matters. Findings are CURRENT_SYSTEM evidence and do not automatically become target requirements.

### Can BA Kit read Figma?

BA Kit does not bundle a Figma connector. If the runtime has a Figma integration and the Human grants access, it can be used. Otherwise export screenshot/image/PDF/HTML/local artifacts.

### Can a screenshot automatically create SRS rules?

No. The agent may record observable UI, find mismatches/gaps, and ask the BA. Permissions, validation, hidden flows, and business side effects need Human confirmation.

### Which SRS template does BA Kit use?

The canonical SRS follows a functional SRS contract and is managed in Markdown; there is not one rigid Markdown form for every feature.

The RC1 production repository **does not bundle a default SRS_TEMPLATE.docx**.

### Can it create SRS using our company Word template?

Yes. Provide the .docx and identify it as the delivery template. document-docx supports template rendering and structural editing.

The template controls layout/sections; it may not override confirmed semantics.

See [SRS and DOCX](SRS_DOCX_GUIDE.md).

### What if no Word template exists?

BA Kit can generate a generic DOCX from the canonical SRS for review, but it should not be described as an official company-template document.

### What if the project only has an old SRS.docx?

Use document-only mode to review/edit it. Once canonical Markdown exists, semantic changes must update the canonical source before synchronizing DOCX.

### What Draw.io diagrams can BA Kit create?

Within BA scope: process flowcharts, swimlanes, user/task flows, state/lifecycle diagrams, decision trees, business context/interaction maps, review/edit of existing .drawio, and image/whiteboard reconstruction.

drawio-skill supports broader technical diagrams, but BA Kit must not use it to invent target architecture/API/DB design.

### Can Draw.io export PNG/PDF?

Yes when the environment has draw.io CLI tooling. Editable .drawio is the source; PNG/SVG/PDF are derivative outputs.

### Can a diagram become the business source of truth?

No. Diagrams reflect approved BR/SRS. A newly discovered rule goes back to PROPOSED/UNKNOWN and Human clarification.

### Can BA Kit create a prototype?

Yes as an optional capability when UX/UI skills are installed. A prototype is a visual proposal requiring Human visual review and does not silently change Business Rules.

### Are the examples mandatory templates?

No. CR-001 illustrates artifact flow and Human Gates. Wording/IDs are not golden output.

### Does Continue mean approval?

No.

~~~text
CONTINUE != APPROVE
ANSWER != APPROVE
~~~

### Can BA Kit approve requirements/SRS automatically?

No. Agent validation is evidence only. Approval must be an explicit Human decision for a named artifact/revision.

### What if current code conflicts with the SRS?

Record the discrepancy. CURRENT_SYSTEM is as-is evidence; Confirmed Decisions + Approved BR + Canonical SRS govern target business meaning. Do not silently change either side to hide the conflict.

### What follows Engineering Handoff?

Engineering Impact resolves WHERE / WHO OWNS. Dev Kit + repo-local Spec Kit then handles HOW.

### Has RC1 passed runtime acceptance?

No. BA Kit 1.0.0-rc.1 is a Public Preview and is not fully accepted. Manual checks for Requirement, Business Rules, SRS, and Draw.io have been exercised; final manual DOCX validation and final approval/handoff validation remain pending. The first full CR-001 acceptance run returned **BA_KIT_RC1_CHANGES_REQUIRED** as historical defect-finding evidence, not final acceptance.

### Is BA Kit licensing ready?

The BA Kit payload is **BA_KIT_LICENSE_READY** for this curated Public Preview distribution.

---

Tiếng Việt: [Câu hỏi thường gặp](../vi/BA_KIT_FAQ.md)
