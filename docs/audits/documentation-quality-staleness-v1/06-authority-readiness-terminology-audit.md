# Authority and readiness terminology audit

## Authority model

| Boundary | Current source-defined meaning | Documentation assessment |
|---|---|---|
| BA | WHAT: Human-approved business decisions, BR/FR and exact BA baseline | Current BA guides are strong; stale architecture summaries still call downstream Dev/Test planned. |
| Engineering | WHERE / WHO OWNS / HOW: topology, repository owners, technical impact/decisions and implementation | Current Dev VNext guides state these roles clearly but are not indexed and have no English counterpart. |
| Test | Proves approved behavior through Design, Testcases, automation and execution evidence | Current Test VNext guides distinguish the manual, automation and execution lanes clearly. |
| Human | Final semantic authority and authenticated approval at named gates | Current BA/Test/Dev guides require exact host-authenticated receipts and preserve role separation. |

The executable precedence is Human-approved decisions > Shared SDLC invariants > Project Policy > Kit / skill instructions > Runtime defaults. Source: shared/sdlc/approvals/invariants.py. The five current artifact classes are CANONICAL, DERIVED, RUNTIME, EVIDENCE and HANDOFF_MANIFEST. Source: shared/sdlc/artifacts/classes.py.

| Artifact class | Authority interpretation |
|---|---|
| CANONICAL | Governing semantic or approved artifact in its declared domain; authority remains bounded by its contract. |
| DERIVED | Projection from canonical sources; no reverse authority. |
| RUNTIME | Execution/workflow state and temporary candidates; does not become semantic approval. |
| EVIDENCE | Observation or proof input; evidence alone does not grant approval. |
| HANDOFF_MANIFEST | Immutable binding of upstream artifacts/revisions and a readiness boundary; not itself a product result. |

Current operator guidance repeatedly and correctly states CONTINUE != APPROVE, ANSWER != APPROVE, validator PASS != APPROVE, generated != APPROVED, derived != authority, runtime != authority, CURRENT_SYSTEM != target requirement, Dev READY_FOR_TEST != Tester VERIFIED, automation PASS != product PASS, APPROVED_TESTWARE != EXECUTION_READY, and EXECUTION_READY != PASS. Test Execution states that a Dev fix cannot close a defect and only a trusted Tester can create VERIFIED. Conformance receipts are labelled TEST_ONLY and not_for_production.

## Readiness/state terminology

| Term | Owner | What it proves | What it does not prove | Allowed next transition | Documentation assessment |
|---|---|---|---|---|---|
| READY (BA Doctor) | BA package Doctor | Required BA package/capability closure | Human approval, approved baseline, feature readiness | Start BA workflow | Defined in Installation and BA guides |
| READY (Dev Doctor) | Dev package Doctor | Dev PACKAGE/CAPABILITY READY, including required Spec Kit pin | Feature readiness or Tester acceptance | Start/continue Dev lifecycle | Defined in Dev guide |
| READY (Test Doctor) | Test package Doctor | Package/core capability and integrity checks pass | BA/Design/Case approval, execution or product PASS | Start/continue Test workflow | Defined in Test guides |
| DEGRADED | BA/Test Doctor | Required core remains usable while an optional capability is unavailable | Full optional capability closure | Use core or restore optional dependency | Defined; exact Test projection report status is not |
| OPTIONAL_DEGRADED | Public conformance projection setup | Optional XMind projection did not become available | Suite failure or lack of core readiness by itself | Continue if optional projection is not required; rerun after repair if needed | Missing from operator docs; DOC-P3-001 |
| CORE_READY | Suite Test readiness adapter | Test Doctor returned READY | Feature/test approval | Continue Suite Doctor/conformance | Internal code term, no operator glossary |
| CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE | Suite Test readiness adapter | Only optional projection checks failed | Required integrity failure or product result | Continue suite flow under optional policy | Internal code term, no operator glossary |
| PROJECT_FOUNDATION_READY | Foundation workflow/Doctor | Foundation profile/manifest and authenticated promotion/readiness checks | Feature or business approval | Provide exact Foundation context to BA/Engineering/Test | Well bounded in Foundation docs |
| APPROVED_BASELINE | BA Human Gate through trusted host | Exact candidate, revision, sources and authenticated Human receipt | Engineering approval, implementation, release | Create/revalidate Engineering Handoff VNext | Well documented |
| READY_FOR_TEST | Dev lifecycle | Dev Handoff V2 and required engineering evidence are valid | Tester PASS, VERIFIED, merge approval | Test intake | Well documented |
| APPROVED_TESTWARE | Test Human Case Gate | Exact Testcases and upstream refs were approved | EXECUTION_READY, execution, PASS or VERIFIED | Automation planning or manual-lane stop | Well documented |
| EXECUTION_READY | Automation V1 | Exact approved testware, revisions, dependencies, review and automation verification are bound | Product test execution or PASS | Test Execution intake | Well documented |
| READY_FOR_RETEST | Dev fix handoff | Required fix/review/fresh checks are ready for the specified retest | Retest success or defect closure | Tester retest | Well documented |
| VERIFIED | Trusted Tester | Required execution/retest observations satisfy exact approved scope | Merge/release authorization | Separate Human merge/release decision | Well documented |
| REOPENED | Trusted Tester retest route | A retest found the same defect lineage remains open | Defect resolution | Return to Dev fix route | Well documented in execution guide |
| INTERNAL_RC_CANDIDATE | Suite release metadata | Internal candidate identity and compatibility target | Stable release, tag, publication or merge approval | Human release/merge decision after required evidence | Machine truth is clear; no suite release page in primary navigation |
| READY_TO_MERGE | No runtime owner or emitter found | No current executable proof | No framework-authorized merge state | Not a current framework transition | docs/en/SHARED_SDLC_CONTRACTS_V1.md lists a conceptual readiness row, then says it adds no lifecycle/Gate and no state grants approval; clarify or remove the row. DOC-P2-004 |

No current documentation finding supports a P0 classification. The READY_TO_MERGE row is a bounded terminology conflict because its surrounding caveat explicitly denies a lifecycle or Human Gate.

## Authority misunderstandings checked

| Potential misunderstanding | Finding in current operator guidance |
|---|---|
| validator PASS = approval | Rejected explicitly in BA, Test and Foundation guides. |
| generated file = approved | Rejected explicitly; exact Human receipt and trusted host are required. |
| Doctor READY = product verified | Rejected in BA, Dev, Test and release guidance. |
| READY_FOR_TEST = feature verified | Rejected in Dev README/workflow and Test automation docs. |
| APPROVED_TESTWARE = execution ready | Rejected in root/Test README, quickstart and workflow. |
| EXECUTION_READY = product PASS | Rejected in Automation and Execution docs and schema description. |
| command failure = DEFECT | Rejected in Test Execution VNext; Tester classification and evidence are required. |
| Dev fix = final verification | Rejected; Dev produces READY_FOR_TEST/READY_FOR_RETEST, Tester owns VERIFIED. |
| synthetic TEST_ONLY approval = production Human approval | Safeguarded in schemas/runtime; public conformance and operator docs mark fixtures TEST_ONLY/not_for_production. |
| VERIFIED = READY_TO_MERGE | Test Execution separates VERIFIED from merge and release; only the shared readiness table creates a conflicting conceptual label. |

## Human Gate semantics

BA, Foundation, Test Design and Test Case documentation all stop at exact Human review boundaries. The Human identity and authorization remain with trusted host callbacks. Dev technical approval is conditional on HIGH_RISK or active material ED and binds the exact technical snapshot. No docs repair or semantic change was performed during this audit.
