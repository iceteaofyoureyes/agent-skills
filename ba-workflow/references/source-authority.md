# Source authority

Business meaning is governed jointly by:

1. confirmed BA decisions;
2. approved Business Rules;
3. the canonical SRS.

These sources must agree. A newer confirmed decision is evidence for updating derived artifacts; it does not make an old Business Rules register or SRS silently current.

## Current system

Use `CURRENT_SYSTEM` for verified behavior in the existing code, data, API or UI. Do not promote it to target behavior without BA confirmation. Report material differences between the request and current system as gaps or questions.

## Visual and delivery artifacts

- A Draw.io diagram represents approved semantics. Layout-only edits preserve meaning and stable element IDs. A semantic change waits for the semantic sources to be approved.
- A prototype or screenshot is a proposal until its visual gate is explicitly approved. It never replaces semantic authority.
- When canonical SRS Markdown exists, edit and validate that source before regenerating DOCX. A standalone Word file is editable only when it is the selected source and no canonical semantic source exists.
- Review-only requests do not write artifacts or advance gates.
