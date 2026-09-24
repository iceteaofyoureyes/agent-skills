# BA Kit Workflow and Human Gates

The workflow below is a typical brownfield path. Greenfield and document-only requests start at the earliest relevant stage.

~~~mermaid
flowchart TD
    A[Requirement] --> B[Current-System Discovery]
    B --> C[Requirement Gap Review]
    C --> D[Human Clarification]
    D --> E[Business Rules]
    E --> F[SRS]
    F --> G[Human Approval]
    G --> H[Engineering Handoff]
    H -. Planned .-> I[Engineering Impact]
    I -. Planned .-> J[Dev Kit + Spec Kit]
    J -. Planned .-> K[Test Kit + TEA]
~~~

## Stages

| Stage | What happens |
|---|---|
| Requirement | Identify the feature, requested outcome, and available source material. |
| Current-System Discovery | For brownfield work, inspect relevant code, behavior, data, APIs, or UI. Record findings as **CURRENT_SYSTEM**; current behavior is evidence, not a new requirement. |
| Requirement Gap Review | Identify ambiguity, omissions, conflicts, and material questions. Keep unknowns open. |
| Human Clarification | The authorized BA/stakeholder answers named questions. Record the source of each answer. |
| Business Rules | Derive traceable rules from confirmed answers while preserving **UNKNOWN**, **INFERRED**, and **PROPOSED** items. |
| SRS | Prepare the canonical requirement specification from the confirmed decisions and approved Business Rules. Keep unresolved items visible. |
| Human Approval | The Human approves, rejects, or requests changes to a named artifact or gate. Validation is evidence, not approval. |
| Engineering Handoff | After explicit approval and with no blocking open items, package the approved baseline, source paths and hashes, remaining open items, downstream policy, and next stage. |

## Evidence labels

| Label | Meaning |
|---|---|
| **CONFIRMED** | Directly stated or decided by the authorized Human. |
| **CURRENT_SYSTEM** | Verified behavior of the existing system. |
| **INFERRED** | A conclusion drawn from evidence but not directly confirmed. |
| **PROPOSED** | A suggested behavior awaiting confirmation. |
| **UNKNOWN** | Missing, conflicting, or unchecked evidence. |

Do not turn current behavior, a screenshot, a prototype, or an inference into a requirement without BA confirmation.

## Human Gates

Ask the Human when missing information could change a business rule, actor or permission, required data, validation, lifecycle, conflict outcome, destructive behavior, semantic source, or target artifact.

- **Continue** resumes from recorded workflow state. **Tiếp tục** is not approval.
- **Answer** resolves only the named question. Answers do not approve an SRS or other artifact.
- **Approve**, **Reject**, and **Request Changes** apply to the named artifact or gate.
- Clearing blocking questions can satisfy the question-resolution gate. Approval of an artifact still requires explicit approval of that artifact.
- Create Engineering Handoff only after explicit BA approval and when no blocking items remain.

## Source authority

Business meaning is governed jointly by:

1. confirmed BA decisions;
2. approved Business Rules;
3. the canonical SRS.

These sources must agree. A newer decision does not silently update older derived artifacts. Verified current-system behavior is recorded separately and does not override approved business semantics. Visual or delivery artifacts, including screenshots, prototypes, diagrams, and generated DOCX files, do not silently change those semantics.

## Boundary after BA

| Work | Responsibility | Status |
|---|---|---|
| BA Kit | **WHAT** the system needs to do | RC1 candidate |
| Engineering Impact | **WHERE** the work belongs and **WHO** owns it | Planned; not implemented |
| Dev Kit + Spec Kit | **HOW** to design and build it | Planned; not implemented |
| Test Kit + TEA | **HOW DO WE PROVE IT** works | Planned; not implemented |

BA Kit does not assign repositories or modules, API design, database or event schemas, locking, transaction strategy, service boundaries, or implementation owners. Those decisions belong downstream. See [Architecture](ARCHITECTURE.md), [Usage Guide](BA_KIT_USAGE_GUIDE.md), and the [CR-001 example](../kits/ba/examples/CR-001/README.md).
