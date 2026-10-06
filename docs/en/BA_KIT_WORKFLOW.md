# BA Kit Workflow and Human Gates

BA Kit is not a rigid pipeline that forces every request through every stage. It starts at the **earliest safe checkpoint** for the work:

- **brownfield** — requirement/change against an existing system;
- **greenfield** — no current system is relevant;
- **document-only** — review/edit an existing SRS/DOCX/diagram;
- **visual-assisted** — screenshot/Figma/PDF/prototype is visual evidence.

## Core semantic flow

New BA writes use the normative lifecycle:

```text
DRAFT → VALIDATED → HUMAN_REVIEW → APPROVED_BASELINE
```

Validation PASS is evidence only. HUMAN_REVIEW freezes the exact manifest,
revision and input hashes; APPROVED_BASELINE requires an external receipt bound
to that identity/revision/semantic SHA-256 and authenticated by the trusted Human
host. ANSWER, CONTINUE, generation, Foundation READY and UX approval never grant
BA approval. Changed candidate bytes require a new revision and new approval.

Workflow state schema 2 is RUNTIME. Business Rules/SRS stages below are activity
metadata. New handoff schema 2 binds exact candidate + receipt + Decisions/BR/SRS,
Shared Foundation Knowledge Impact and optional exact Foundation context, and
revalidates proof on consumption. V1 state/handoff remain LEGACY_COMPAT with
insufficient evidence for new approval. Historical Shared Core imports, Delivery
Manifest V2, UX receipt V2 and atomic skills retain their contracts.

BR-* = Business Rule; FR-* = Functional Requirement. Preserve stable IDs and
retain retired identities; BAREF:* is a structural locator only, never mandatory
coverage. Confirmed Human decisions must bind updated BR/SRS before readiness.
BA owns WHAT; technical owners, API/event/DB design, service boundaries,
locking/transactions and architecture decisions belong downstream.

Consume Foundation inventory/context where available. CURRENT_SYSTEM and
INFERRED never establish target requirements automatically; material differences
become gaps until Human clarification. Greenfield begins with Human intent and
explicit questions/decisions. A full Foundation is optional for bounded feature
analysis. Knowledge Impact binds product/domain/architecture/testing affected
flags and targets to baseline/handoff, routing technical assessment downstream.

Trusted hosts use [the executable VNext contracts](../../ba-workflow/references/baseline-vnext.md).
Read-only validator CLIs cannot authenticate Human approval and fail closed for
VNext approved state/handoff without that trusted host. Derived artifact refs
require refresh after candidate changes; approved snapshot bytes remain immutable.

~~~mermaid
flowchart TD
    A[BA Input / Requirement / CR] --> B{Current system matters?}
    B -- Yes --> C[Current-System Discovery]
    B -- No --> D[Requirement Review / Gap Analysis]
    C --> D
    D --> E[Human Clarification]
    E --> F[Business Rules]
    F --> G[Canonical SRS]
    G --> H[Human BA Baseline Gate]
    H --> I[Engineering Handoff]
    I --> J[Engineering Impact]
    J --> K[Dev Kit VNext]
    K --> L[READY_FOR_TEST]
    L --> M[Test Manual / Automation / Execution]
    M --> N[Tester VERIFIED / REOPENED]
~~~

This core flow manages **business semantics**. Draw.io, prototypes, and DOCX are derived/visual/delivery lanes and do not replace semantic authority.

## Derived artifact lanes

~~~mermaid
flowchart LR
    A[Confirmed Decisions + Approved BR + Canonical SRS]
    A --> B[Draw.io Business Diagrams]
    A --> C[DOCX Delivery]
    A --> D[Optional UX / Prototype]
    V[Approved visual source] --> D
    T[Selected Word template] --> C
    B --> E[Human visual/document review]
    C --> E
    D --> E
~~~

When the semantic baseline changes, affected derived artifacts must be reviewed/updated.

## Project modes

| Mode | Use | Discovery |
|---|---|---|
| Brownfield | Feature/CR on an existing system | Inspect source/current behavior before concluding target behavior |
| Greenfield | No relevant current system | Start from requirement/gap clarification |
| Document-only | Review/edit existing artifact | Code discovery is optional unless current behavior matters |
| Visual-assisted | Image/Figma/PDF/HTML/prototype exists | Visuals are evidence; hidden behavior still requires Human confirmation |

## Operation modes

| Operation | Rule |
|---|---|
| REVIEW | Read-only; do not mutate artifact or advance stage |
| CREATE | Create requested artifact when authority is sufficient |
| EDIT | Change only selected scope; preserve unaffected approved semantics |
| CONTINUE | Read workflow state and perform next valid action; never approval |

## Stages and outputs

| Stage | Agent | Human | Typical output |
|---|---|---|---|
| Input | Resolve feature/artifact/mode | Provide requirement/source | Input refs |
| Current-System Discovery | Inspect relevant current behavior | Clarify discovery scope if needed | CURRENT_SYSTEM findings |
| Gap Analysis | Find missing/ambiguous/contradictory cases | Review questions | Gap list |
| Clarification | Record answers/evidence | Make business decisions | Confirmed decisions |
| Business Rules | Structure traceable rules | Review/request changes | Business Rules |
| SRS | Create/update functional SRS | Review/request changes | Canonical SRS |
| Draw.io/DOCX/Prototype | Create derived artifacts | Visual/document review | .drawio, DOCX, prototype |
| Approval | Never self-approve | APPROVE/REJECT/REQUEST_CHANGES | Gate decision |
| Handoff | Revalidate exact baseline/receipt/sources | Authenticate exact baseline decision | engineering-handoff.json (VNext) |

## Gap areas BA Kit should consider

Not every feature needs every item, but CRUD/list/workflow work commonly requires checks around:

- actors/roles/permissions;
- fields and required/optional status;
- validation/boundaries;
- state/lifecycle;
- search/filter;
- sort/default sort;
- pagination/page size;
- list columns;
- row/bulk actions;
- empty/loading/error;
- destructive actions/confirmation;
- concurrency business outcomes;
- timezone/date semantics;
- audit/history when required;
- integration outcomes at business level.

Ask only where authority is missing.

## Evidence labels

| Label | Meaning |
|---|---|
| CONFIRMED | Authorized Human decision defining target behavior |
| CURRENT_SYSTEM | Verified existing behavior |
| INFERRED | Evidence-based deduction not yet confirmed |
| PROPOSED | Suggested behavior awaiting a decision |
| UNKNOWN | Missing/conflicting evidence |

Screenshots, current code, prototypes, and template text do not become CONFIRMED automatically.

## Human Gates

Gate types:

- **ANSWER** — resolve the named question;
- **CONTINUE** — proceed to the next valid action;
- **APPROVE** — approve the named artifact/revision;
- **REQUEST_CHANGES** — request changes to a named artifact/gate;
- **REJECT** — reject a named artifact/gate.

Invariant:

~~~text
CONTINUE != APPROVE
ANSWER != APPROVE
validation PASS != APPROVE
artifact generated != APPROVE
~~~

## Relationship between SRS, diagram, prototype, and DOCX

~~~text
Confirmed Decisions
+ Approved Business Rules
+ Canonical SRS
        │
        ├──> Draw.io business diagrams
        ├──> DOCX delivery using selected template
        └──> Optional prototype / visual contract
~~~

If a diagram/prototype reveals a new business question:

~~~text
visual finding
→ PROPOSED / UNKNOWN
→ Human clarification
→ update BR/SRS
→ regenerate/update derived artifact
~~~

Do not change a derived artifact alone and treat it as a new business rule.

## Visual Gate

Prototype/Figma-derived outputs may need a separate Human visual review.

Visual approval confirms the stated presentation/interaction scope. BA baseline approval requires its separate exact trusted-host authenticated receipt.

## Engineering Handoff Gate

Create the handoff only when:

- the exact candidate is APPROVED_BASELINE with a trusted-host authenticated receipt;
- no blocking item remains;
- source paths/hashes are valid;
- no technical ownership/design fields are present.

The next stage is **Engineering Impact**, which resolves WHERE/WHO OWNS. Dev then owns HOW through READY_FOR_TEST; Test owns approvals, execution evidence, Finding classification, and retest. See the [canonical integrated lifecycle](ARCHITECTURE.md). BA does not own downstream implementation or verification.

## See also

- [BA Kit capabilities](BA_KIT_CAPABILITIES.md)
- [Usage guide](BA_KIT_USAGE_GUIDE.md)
- [SRS and DOCX](SRS_DOCX_GUIDE.md)
- [Draw.io, visual input, and prototypes](DIAGRAMS_PROTOTYPES.md)
- [Kit contract](KIT_CONTRACT.md)

---

Tiếng Việt: [Quy trình và Human Gate](../vi/BA_KIT_WORKFLOW.md)
