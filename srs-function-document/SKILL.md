---
name: srs-function-document
description: Create or update a traceable functional SRS from confirmed BA semantics while preserving unknowns, source authority, and Human approval gates.
---

# Functional SRS

Turn the authorized BA semantic baseline into a canonical functional Software Requirements Specification. The SRS describes observable business behavior. It does not make new business decisions or choose technical design.

## Read the authoritative inputs

Before writing, identify:

- Confirmed BA Decisions and their evidence.
- Approved Business Rules and their identifiers.
- The current canonical SRS and its revision when updating.
- Relevant requirements, source evidence, and workflow state.

Treat workflow state as evidence of artifact identity, revision, and approval status. Do not use it to invent semantics. The business meaning comes from Confirmed BA Decisions and Approved Business Rules. Preserve confirmed, unaffected content from the current canonical SRS when updating. If sources conflict or an approval is unclear, record the conflict and ask for clarification instead of choosing a side.

## Preserve evidence meaning

Keep these labels distinct:

- CONFIRMED: an authorized BA decision or approved rule that defines target behavior.
- CURRENT_SYSTEM: observed existing behavior. Describe it as as-is evidence only. Do not turn CURRENT_SYSTEM evidence into a target requirement.
- INFERRED: a deduction that has not been confirmed. Keep it separate from target requirements.
- PROPOSED: a suggested behavior awaiting a decision. Do not present it as approved.
- UNKNOWN: unresolved. Keep UNKNOWN values explicitly unresolved; do not fill them with defaults or plausible values.

Never promote INFERRED or PROPOSED content to CONFIRMED. Do not silently resolve ambiguity, add rules, or treat a missing value as permission to choose one.

## Write functional, traceable requirements

Include only sections needed for the feature. They may cover the feature and scope, actors, preconditions, functional requirements, approved business rules, validation, states and lifecycle, error and edge behavior, list/filter/sort/pagination behavior, open items, and traceability.

Describe user-visible outcomes and conditions clearly enough to review and verify. Where the source provides identifiers, maintain the chain:

Business Rule → Functional Requirement → acceptance criteria or behavior

Use existing identifiers. Do not manufacture IDs for cosmetic completeness. Keep source references and evidence labels with the requirements they support.

## Keep technical choices downstream

Do not decide repository or module ownership, frontend/backend ownership, API shape, database schema, event architecture, locking, transaction implementation, a new microservice, or deployment architecture. When a technical choice is raised, record it as an Engineering decision and leave the implementation to the downstream owner.

## Update an existing SRS safely

Compare the authorized changes with the current canonical SRS before editing it.

- Preserve every confirmed, unaffected requirement and its identifiers.
- Change only semantics supported by new Confirmed decisions or Approved Business Rules.
- Keep unapproved proposals, current-system observations, and unknowns out of target requirements.
- Surface conflicts with existing confirmed content. Do not silently overwrite, remove, or weaken a Human-approved requirement.
- Keep a change trace so reviewers can see what changed and which authority supports it.

## Output and Human Gate

Produce or update the canonical functional SRS and list unresolved items and conflicts. SRS generation is preparation for Human review.

Do not set or imply APPROVED_FOR_ENGINEERING. Do not record Human approval, advance workflow gates, or create an Engineering Handoff. The BA workflow owns those actions and requires an explicit Human decision for the named artifact revision.
