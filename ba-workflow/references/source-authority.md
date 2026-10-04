# Source authority

Business meaning is governed jointly by:

1. confirmed BA decisions;
2. approved Business Rules;
3. the canonical SRS.

These sources must agree. A newer confirmed decision is evidence for updating derived artifacts; it does not make an old Business Rules register or SRS silently current.

## VNext authority and business identity

The immutable candidate binds Decisions, BR and canonical functional SRS Markdown by exact path/revision/SHA. It includes optional required glossary/domain refs, open items, evidence, Foundation context and Shared Foundation Knowledge Impact in its semantic identity. DOCX, Draw.io and prototypes are derived outputs. See [VNext contracts](baseline-vnext.md).

BR-* identifies a Business Rule; FR-* a Functional Requirement. Preserve IDs for continuing semantic items, give new meaning a new ID and retain retired IDs in the identity ledger. Duplicates fail closed. Markdown normalization preserves meaning. BAREF:* is a provenance/structural locator only; coverage_ids contains canonical FR/BR only.

BA owns WHAT. Technical owners, API/event/DB design, service boundaries, locking/transactions and architecture decisions belong downstream. Candidate validators reject explicit technical fields in authority text; Human review also assesses narrative meaning. Do not place HOW decisions in BA decisions or handoff.

## Current system

Use `CURRENT_SYSTEM` for verified behavior in the existing code, data, API or UI. Do not promote it to target behavior without BA confirmation. Report material differences between the request and current system as gaps or questions.

Consume Foundation inventory/context where available; READY is context, never BA target approval. A BA Foundation binding must include exact durable manifest, promotion provenance, and authenticated Foundation approval refs; structural readiness alone is insufficient. Architecture remains Engineering-owned. Foundation target approval and BA approval are independent. Full Foundation is optional: bounded feature evidence may suffice. When consuming READY, reuse its existing readiness/reference checks without weakening blockers. Material current/target contradictions remain gaps until Human clarification. Implementation inference stays INFERRED.

## Visual and delivery artifacts

- A Draw.io diagram represents approved semantics. Layout-only edits preserve meaning and stable element IDs. A semantic change waits for the semantic sources to be approved.
- A prototype or screenshot is a proposal until its visual gate is explicitly approved. It never replaces semantic authority.
- When canonical SRS Markdown exists, edit and validate that source before regenerating DOCX. A standalone Word file is editable only when it is the selected source and no canonical semantic source exists.
- Review-only requests do not write artifacts or advance gates.
