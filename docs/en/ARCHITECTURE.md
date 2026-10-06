# Current architecture and lifecycle

This is the canonical explanation of the integrated lifecycle. Role guides link here rather than defining competing flows. Executable contracts remain authoritative: [suite manifest](../../tooling/sdlc-suite.json), [acceptance contract](../../tooling/sdlc-suite-acceptance.yaml).

## Authority and ownership

Authority precedence is: (1) Human-approved decisions, (2) Shared SDLC invariants, (3) project policy/instructions, (4) Kit or atomic-skill mechanics, (5) runtime defaults.

| Role | Owns |
|---|---|
| BA | WHAT: approved business behavior |
| Engineering / Dev | WHERE, WHO OWNS, HOW: repository scope, impact, technical decisions, implementation |
| Test | Evidence that approved behavior was tested |
| Human | Final semantic authority and approval of exact snapshots |

Artifacts are classified as CANONICAL, DERIVED, RUNTIME, EVIDENCE, or HANDOFF_MANIFEST. A derived output, runtime state, evidence item, or handoff does not become authority by being generated.

## Project Foundation

Project Foundation is a shared SDLC workflow, not a fourth role Kit. Modes are GREENFIELD_BOOTSTRAP, BROWNFIELD_RECOVERY, and FOUNDATION_REFRESH; profiles are MINIMAL, STANDARD, and EXTENDED. Its architecture basis uses arc42 Standard, ISO 42010 concepts, C4, and ADRs.

Brownfield evidence distinguishes CURRENT_SYSTEM, CONFIRMED, INFERRED, and UNKNOWN. Greenfield evidence distinguishes APPROVED_TARGET, PROPOSED, DEFERRED, and UNKNOWN. PROJECT_FOUNDATION_READY proves Foundation readiness only. It does not approve business behavior, prove feature readiness or implementation correctness, establish Tester verification, or authorize release. See the [Foundation operator guide](PROJECT_FOUNDATION.md) and [technical reference](../project-foundation.md).

## Canonical lifecycle

~~~
Project Foundation
→ BA
→ UX / Interaction Contract when required
→ Engineering Handoff
→ Engineering / Dev → READY_FOR_TEST
→ Test Design → Human approval → APPROVED_DESIGN
→ Testcases → Human approval → APPROVED_TESTWARE
→ Automation Plan → implementation/review → automation verification → EXECUTION_READY
→ Execution → Observation → Finding classification
→ Dev Fix when applicable → READY_FOR_RETEST
→ Tester retest → VERIFIED / REOPENED
→ separate Human merge / release decision
~~~

The Tester classifies a Finding as DEFECT, SPEC_GAP, BUSINESS_DECISION_REQUIRED, TEST_ISSUE, or ENVIRONMENT_ISSUE. Only a DEFECT uses the defect handoff to Dev. A command failure alone is not a DEFECT. Dev fixes through FEATURE_DELIVERY, returns READY_FOR_RETEST, and the Tester retests.

## Human gates and boundaries

CONTINUE != APPROVE; ANSWER != APPROVE; validator PASS != APPROVE; generated != APPROVED; Derived != Authority; Runtime != Authority; CURRENT_SYSTEM != confirmed target.

READY_FOR_TEST is a Dev handoff, not VERIFIED. A Dev fix does not create Tester verification. APPROVED_TESTWARE is not EXECUTION_READY; EXECUTION_READY is not PASS. The current lifecycle ends at VERIFIED; a separate Human decision governs merge/release. READY_TO_MERGE is not a lifecycle state.

## Gate owners

| Gate / output | Owner | What it proves |
|---|---|---|
| APPROVED_BASELINE | BA + Human through trusted host | Exact approved WHAT baseline and sources |
| Engineering Handoff | BA workflow validates approved proof | Business input for Engineering |
| Technical approval when required | Human / Tech Lead | Exact technical snapshot under risk policy |
| READY_FOR_TEST | Dev | Engineering work, checks, and handoff are complete |
| APPROVED_DESIGN, APPROVED_TESTWARE | Human for each Test snapshot | Design coverage / testware is approved |
| EXECUTION_READY | Automation workflow after review | Automation and execution authority are bound |
| Finding classification / VERIFIED | Authenticated Tester | Observations and retest against the approved oracle |
| Merge / release | Human outside this lifecycle | Separate integration or release decision |

See [BA workflow](BA_KIT_WORKFLOW.md), [Dev operator guide](DEV_KIT_GUIDE.md), [Manual Test](TEST_KIT_MANUAL.md), [Automation](TEST_AUTOMATION_V1.md), and [Execution / Retest](TEST_EXECUTION_VNEXT.md). State ownership and next transitions are in [Readiness states](READINESS_STATES.md); recovery is in [Troubleshooting](TROUBLESHOOTING.md).

---

Tiếng Việt: [Kiến trúc và lifecycle](../vi/ARCHITECTURE.md)
