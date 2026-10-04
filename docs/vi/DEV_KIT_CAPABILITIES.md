# Dev Kit VNext — Capability Routing

Capabilities are selected from evidence and the current engineering task. They
do not create authority, lifecycle state or approval.

| Capability | Role | When used | Boundary |
|---|---|---|---|
| `requirements-gap-auditor` | Clarify upstream gaps | Verify exact Engineering Handoff VNext and report WHAT uncertainty | Cannot edit approved WHAT or approve a baseline |
| `verification-before-completion` | Evidence discipline | Before claiming checks or handoff complete | Evidence must come from fresh repository-scoped checks |
| `planning-and-task-breakdown` | Technical plan/tasks | FEATURE_DELIVERY after Engineering Impact | Technical HOW only; snapshot binds repositories, bases, scope and risk |
| `incremental-implementation` | Scoped code slices | IMPLEMENTING | Runtime authorization applies to every write |
| `test-driven-development` | Test behavior changes | Relevant implementation slices | Does not alter approved requirements |
| `code-review-and-quality` | Consolidated engineering review | One full review, bounded fix and optional scoped rereview | Review cannot rewrite BA authority |
| `debugging-and-error-recovery` | Diagnose failures | Regression or runtime failure | Findings and recovery must preserve exact snapshot evidence |
| `security-and-hardening` | Security analysis | Security-sensitive scope or findings | HIGH_RISK requires exact technical gate |
| `api-and-interface-design` | Public contract design | Interface/public API changes | Record decisions as ED-*; gate when required |
| `source-driven-development` | Source-backed decisions | Existing behavior or compatibility is uncertain | Confirm against target repository evidence |
| `performance-optimization` | Performance work | Measured or explicit performance requirements | Risk and check scope remain repository-bound |
| `observability-and-instrumentation` | Diagnostics design | Production behavior needs evidence | Instrumentation is still within approved change scope |

## Runtime dependencies

GitHub Spec Kit `1.0.11` transports workflow state, pause/resume and bundles.
Its feature-spec commands remain excluded. The plugin owns core and conditional
engineering skills; `requirements-gap-auditor` and
`verification-before-completion` stay shared repository skills.

## Capability boundaries

Only two authority modes route work: `FEATURE_DELIVERY` with exact Engineering
Handoff VNext, and evidence-bound nonbehavioral `TECHNICAL_MAINTENANCE`. Neither
skill selection nor a model/tool name changes those contracts. The terminal Dev
state is `READY_FOR_TEST`.

V1 schemas/readers remain `LEGACY_COMPAT`, with no VNext authority. Delivery
Manifest stays `DEFERRED_NON_AUTHORITATIVE`.
