# PHASE 5 — DEV KIT VNEXT EXECUTION SPEC

**Status:** HUMAN_APPROVED  
**Repository:** `iceteaofyoureyes/agent-skills`  
**Authoritative base:** `main` @ `84c050865630125751f8bfe1c1ca30c0a0a7b8c7`  
**Phase 4 dependency:** BA Kit VNext merged and frozen  
**Implementation:** NOT STARTED  
**Recommended models:** SOL High for Waves 1–2; LUNA Medium for Wave 3

> Human review completed on 2026-10-04. Phase 5 implementation is authorized under this exact specification.

---

## 1. Objective

Migrate the existing Dev Kit V1 into Dev Kit VNext without discarding capabilities that are already correct.

Dev Kit VNext must:

1. consume exact, revalidated BA Engineering Handoff VNext;
2. preserve approved BA WHAT as immutable upstream authority;
3. own technical WHERE / WHO OWNS / HOW;
4. make Engineering Impact first-class and traceable;
5. make upstream requirement gaps first-class, resumable artifacts;
6. make material technical decisions durable and versioned;
7. require exact Human/Tech Lead approval for material technical decisions;
8. prevent implementation before required technical gates;
9. execute through bounded, risk-based workflows;
10. produce deterministic engineering verification evidence;
11. produce a versioned Dev Handoff ending at READY_FOR_TEST, never VERIFIED;
12. preserve useful V1 routing/review/Spec Kit infrastructure through compatibility;
13. work after clean install without source-checkout imports;
14. remain generic, with no Digital Wedding/PetClinic/Appointment semantics.

Dev Kit VNext must never create a second business-requirements authority.

---

## 2. Frozen upstream contracts

### 2.1 BA authority

Canonical BA authority remains:

- Human BA Decisions;
- Business Rules `BR-*`;
- canonical functional SRS `FR-*`;
- exact BA Baseline Candidate / Manifest;
- exact authenticated BA approval receipt;
- Engineering Handoff VNext.

`BAREF:*` remains structural/provenance locator only.

### 2.2 BA lifecycle

Frozen:

```text
DRAFT
→ VALIDATED
→ HUMAN_REVIEW
→ APPROVED_BASELINE
```

Dev Kit never promotes or edits BA lifecycle.

### 2.3 Ownership

```text
BA          owns WHAT
ENGINEERING owns WHERE / WHO OWNS / HOW
TEST        owns downstream proof / system acceptance
```

Dev Kit MUST NOT:

- rewrite `BR-*`;
- rewrite `FR-*`;
- edit BA Decisions;
- reinterpret UNKNOWN/TBD as known;
- silently weaken business behavior;
- replace BA authority with implementation reality;
- make a technical decision that changes WHAT without upstream re-approval.

### 2.4 Project Foundation

If the Engineering Handoff carries Project Foundation context, Dev must preserve Phase 4 durable proof:

```text
durable Foundation manifest
+ promotion provenance
+ Foundation Human receipt
+ trusted-host authentication
```

`PROJECT_FOUNDATION_READY` is context readiness, not feature approval.

### 2.5 Delivery / UX

Delivery Manifest V2 and UX approval remain frozen contracts.

Engineering Handoff VNext is the authoritative BA WHAT input to Dev.

Delivery Manifest V2 may be consumed as a delivery envelope for approved UX, targets and delivery metadata, but MUST NOT substitute for Engineering Handoff VNext approval proof.

---

## 3. Dev Kit V1 audit

Audit base:

```text
main
84c050865630125751f8bfe1c1ca30c0a0a7b8c7
```

### 3.1 Existing strengths to preserve

1. **Correct WHAT/HOW intent** — current docs already separate BA WHAT from Dev HOW.
2. **Risk-based routing** — TRIVIAL / NORMAL / HIGH_RISK with security, migration, public API, event, cross-repo, concurrency, architecture and deployment signals.
3. **Bounded review** — one full review, one blocking fix wave, at most one scoped rereview.
4. **Fresh deterministic verification** — repository-native checks are rerun before READY_FOR_TEST.
5. **Spec Kit containment** — current Dev Kit excludes `speckit.specify/plan/tasks/analyze/converge`; this correctly prevents a second WHAT representation.
6. **Installer/provenance foundation** — external runtime, provenance lock, plugin composition, schemas/templates, workflows and Doctor already exist.

### 3.2 VNext gaps

#### P5-01 — obsolete upstream proof

Current runtime still uses legacy ApprovedBaseline / V1 Engineering Handoff / `APPROVED_FOR_ENGINEERING` semantics. VNext must consume Engineering Handoff schema V2 and exact authenticated proof.

#### P5-02 — no normative Dev lifecycle contract

Current state mixes `RUNNING`, readiness, risk escalation and terminal handoff states. VNext needs one versioned fail-closed lifecycle.

#### P5-03 — upstream requirement gaps are not first-class

`NEEDS_BA_CLARIFICATION` is mainly state/text. VNext needs an exact Engineering Gap artifact with evidence, affected BR/FR IDs and replacement-handoff binding.

#### P5-04 — material HOW decisions live mainly in plan prose

`dev-plan.md` is useful runtime planning, but material technical decisions need durable/versioned Engineering Decision records.

#### P5-05 — Human technical gate proof is too weak

A Spec Kit gate choice/workflow state is orchestration evidence, not automatically authenticated Human authority. VNext needs exact snapshot binding and trusted Human/Tech Lead authentication.

#### P5-06 — coverage IDs are underconstrained

Current Dev Handoff accepts generic IDs. VNext coverage must be canonical FR/BR only and must match upstream required coverage. BAREF is excluded.

#### P5-07 — engineering verification vs system acceptance needs explicit separation

Dev owns build/static/unit/component/module-local checks. READY_FOR_TEST is not system acceptance, Tester PASS or VERIFIED.

#### P5-08 — cross-repository work needs exact revision/write-scope binding

Impact may list repos today, but VNext needs exact repository identity, base revision, allowed write scope and produced revision per repo.

#### P5-09 — V1 compatibility must not authorize VNext runs

V1 remains readable only as `LEGACY_COMPAT`; it cannot silently become VNext authority.

---

## 4. Dev Kit VNext authority model

### 4.1 Upstream immutable authority

For feature delivery:

```text
Engineering Handoff VNext
├── APPROVED_BASELINE identity
├── exact BA candidate manifest
├── exact BA approval receipt
├── exact Decisions / BR / SRS refs
├── Knowledge Impact
├── Project Foundation proof when present
└── open-items policy
```

Dev must revalidate through the canonical BA VNext reader. Do not implement a near-duplicate BA proof parser.

### 4.2 Delivery envelope

If supplied:

```text
Delivery Manifest V2
├── exact Engineering Handoff binding
├── UX contract / approval where required
├── delivery revision
├── target repository context
└── downstream metadata
```

This is a HANDOFF_MANIFEST, not business authority.

### 4.3 Dev-owned authority

Dev owns:

- Engineering Impact;
- repository/module ownership;
- technical constraints and risk;
- Engineering Decisions;
- implementation plan/tasks;
- source changes and migrations;
- engineering verification evidence;
- Dev Handoff.

---

## 5. Authority modes

### FEATURE_DELIVERY

Required for any feature/business behavior change.

Mandatory upstream authority:

```text
Engineering Handoff VNext
```

Delivery Manifest V2 is additionally required where the project workflow needs UX or delivery-target binding.

### TECHNICAL_MAINTENANCE

May omit BA Handoff only when the change is proven not to change WHAT, such as:

- documentation-only;
- rename-only;
- mechanical refactor;
- non-behavioral tooling/config maintenance.

If analysis discovers business behavior, public contract, data semantics or user-visible outcome change:

```text
TECHNICAL_MAINTENANCE
→ BLOCK
→ require FEATURE_DELIVERY authority
```

Maintenance mode cannot be used as a BA bypass.

---

## 6. Normative Dev lifecycle V2

```text
INTAKE
→ AUTHORITY_VALIDATED
→ IMPACT_ANALYZED
→ TECHNICAL_PLANNED
→ IMPLEMENTATION_READY
→ IMPLEMENTING
→ ENGINEERING_REVIEW
→ VERIFYING
→ READY_FOR_TEST
```

Exception states:

```text
UPSTREAM_GAP
NEEDS_REPLAN
BLOCKED
```

### Transition meanings

- **INTAKE** — run created; no implementation authorized.
- **AUTHORITY_VALIDATED** — exact upstream authority revalidated.
- **IMPACT_ANALYZED** — technical blast radius/risk/write scope known enough to plan.
- **TECHNICAL_PLANNED** — plan/tasks and material Engineering Decisions bind exact upstream/impact.
- **IMPLEMENTATION_READY** — required technical Human gates resolved; source mutation authorized.
- **IMPLEMENTING** — approved technical scope being implemented.
- **ENGINEERING_REVIEW** — candidate enters bounded consolidated review.
- **VERIFYING** — blocking findings resolved per policy and fresh checks running.
- **READY_FOR_TEST** — engineering obligations complete; downstream Test owns final verification.

`READY_FOR_TEST != VERIFIED`.

---

## 7. Lifecycle profiles

### 7.1 TRIVIAL maintenance fast path

TECHNICAL_MAINTENANCE only:

```text
INTAKE
→ AUTHORITY_VALIDATED
→ IMPLEMENTATION_READY
→ IMPLEMENTING
→ VERIFYING
→ READY_FOR_TEST
```

Allowed only when there is no behavior/public-contract/schema/security/cross-repo risk.

### 7.2 NORMAL feature path

Uses the full normative lifecycle. No mandatory Human technical gate for routine reversible local HOW decisions.

### 7.3 HIGH_RISK feature path

Uses the full lifecycle, but:

```text
TECHNICAL_PLANNED
→ IMPLEMENTATION_READY
```

requires exact Human/Tech Lead approval when material decision policy triggers.

---

## 8. Dev run state V2

Create a versioned, fail-closed RUNTIME state with at least:

```text
schema_version
run_id
change_id
authority_mode
feature_id optional for maintenance
lifecycle
risk
upstream
delivery
repositories
artifacts
gates
open_items
engineering_gap
history
review_budget
verification
```

Rules:

- append-only transition history;
- exact refs with revision/hash;
- unsupported versions fail closed;
- unknown fields fail closed unless an explicit extension namespace exists;
- lifecycle cannot jump;
- no source mutation before IMPLEMENTATION_READY;
- booleans/status strings never create Human approval.

V1 state may be readable as `LEGACY_COMPAT`, not promoted to VNext authority.

---

## 9. Input contract

### 9.1 Feature delivery

Required:

- change id;
- summary;
- exact Engineering Handoff VNext ref;
- repository base revisions;
- repository-native engineering checks.

Conditional:

- Delivery Manifest V2 ref;
- Project Topology/Policy refs;
- explicit risk signals;
- requested target scope.

### 9.2 Intake validation

Must revalidate Engineering Handoff VNext through the canonical BA implementation, including:

- baseline manifest identity/revision/semantic hash;
- exact Human BA receipt;
- trusted Human authentication;
- Decisions/BR/SRS bytes;
- Knowledge Impact;
- blocking items = none;
- Foundation durable proof where present.

No copy of BA semantics becomes Dev authority.

### 9.3 Legacy input

V1 Engineering Handoff:

```text
LEGACY_COMPAT
vnext_authority = false
```

It cannot start a VNext FEATURE_DELIVERY implementation run.

---

## 10. Engineering Impact VNext

Create schema V2 (or equivalent versioned contract) containing at least:

```text
change_id
upstream_ref
repository_base_revisions
affected_repositories
affected_components
affected_interfaces
affected_data
dependencies
constraints
risk
technical_unknowns
upstream_gaps
write_scope
knowledge_impact
```

Each repository entry binds:

```text
repository id
role
base revision
allowed write paths
read-only evidence paths if needed
```

Engineering Impact is Dev-owned technical authority for the run after validation. It must not alter WHAT.

---

## 11. First-class Engineering Gap

Reuse Shared finding semantics where possible:

```text
SPEC_GAP
BUSINESS_DECISION_REQUIRED
```

The Dev routing path may be named:

```text
UPSTREAM_REQUIREMENT_GAP
```

without adding a new Shared FindingKind unless necessary.

Gap artifact minimum fields:

```text
gap_id
finding_kind
feature_id
engineering_handoff_ref
affected_business_ids
evidence_refs
question
blocking_scope
discovered_at
status
resolution_ref optional
replacement_handoff_ref optional
```

`affected_business_ids` are `BR-*` / `FR-*`, never BAREF.

Flow:

```text
Dev detects gap
→ freeze affected downstream work
→ publish exact gap evidence/question
→ BA/Human resolution
→ revised BA baseline if needed
→ new Human approval
→ new Engineering Handoff VNext
→ exact replacement binding
→ downstream resume
```

Do not code first and rewrite BA docs afterward.

---

## 12. Engineering Decision contract

Introduce durable material HOW decisions with IDs:

```text
ED-*
```

Minimum fields:

```text
schema_version
id
change_id
topic
category
decision
status
evidence_refs
upstream_refs
affected_repositories/components/interfaces/data
alternatives
consequences
risk
materiality
approval_requirement
approval_ref optional
supersedes
superseded_by
```

Statuses:

```text
PROPOSED
APPROVED
SUPERSEDED
```

Validation PASS cannot turn a proposal into APPROVED.

Routine local choices do not need durable ED records. Material decisions do.

---

## 13. Engineering Decision vs ADR

- Feature-local material implementation choice → Engineering Decision.
- Durable project architecture change → Project Foundation/Engineering ADR update.

Examples that should route to ADR/Foundation impact:

- service boundaries;
- deployment topology;
- platform choice;
- long-lived public integration strategy;
- cross-project architecture.

An Engineering Decision may reference an ADR; it must not duplicate project architecture authority inside `.devkit/`.

---

## 14. Human / Tech Lead gate policy

Mandatory gate categories include at least:

- breaking public API/contract;
- auth/authz/security boundary;
- persistence schema/destructive migration;
- distributed transaction/concurrency semantics;
- destructive data operation;
- deployment topology;
- cross-component/cross-repository architecture;
- major dependency/platform choice;
- material deviation from an already approved technical plan.

Project-local policy may strengthen but not silently weaken these rules.

---

## 15. Exact technical approval binding

Human technical approval binds the exact technical snapshot:

```text
Engineering Impact ref/hash
Engineering Decision set refs/hashes
Dev Plan hash
Dev Tasks hash
repository base revisions
approved write scope
risk classification
```

Receipt includes at least:

```text
decision = APPROVE
actor id
actor role = HUMAN / TECH_LEAD
recorded time
change id
snapshot revision/hash
decision evidence ref
```

Trusted host authenticates actor identity.

Hash proves integrity, not identity.

A Spec Kit gate MAY fulfill this only when its adapter proves authenticated identity + exact snapshot binding + replay-safe evidence. Otherwise it is only pause/resume orchestration.

---

## 16. Planning contract

Keep:

```text
dev-plan.md
dev-tasks.md
```

as RUNTIME planning artifacts.

They bind exact:

- Engineering Handoff;
- Engineering Impact;
- Engineering Decisions;
- repository base revisions;
- risk;
- write scope.

They must not duplicate BR/FR content into a second requirements source.

Material changes to upstream/impact/decisions/write scope invalidate prior technical approval.

---

## 17. Spec Kit boundary

Allowed:

```text
workflow engine
state / pause / resume
bundle orchestration
gate transport when trustworthy
```

Forbidden authority roles:

```text
spec.md business WHAT
alternative requirements source
implicit plan authority
implicit Human approval
```

Continue excluding Spec Kit feature-spec commands unless a future Human architecture decision changes this.

Add regression proving Dev VNext does not create or require `spec.md`.

---

## 18. Implementation authorization

Source mutation is authorized only in:

```text
IMPLEMENTATION_READY
```

Implementation must fail closed after:

- upstream drift;
- approval-receipt drift;
- new Engineering Gap;
- risk escalation requiring a gate;
- repository base revision drift;
- write-scope expansion;
- material Engineering Decision change;
- plan/tasks hash change after approval.

Route to `UPSTREAM_GAP`, `NEEDS_REPLAN` or `BLOCKED` as appropriate.

---

## 19. Implementation discipline

Preserve V1 strengths:

1. smallest complete slices;
2. TDD/regression tests for behavior changes;
3. repository-native focused checks;
4. no unrelated cleanup;
5. no BA-authority mutation;
6. no unapproved write-scope expansion;
7. no independent reviewer after every slice;
8. conditional specialist skills only when evidence/risk triggers them.

---

## 20. Engineering verification ownership
Dev-owned verification classes:

```text
BUILD
STATIC
LINT
TYPECHECK
UNIT
COMPONENT
MODULE_LOCAL_INTEGRATION
```

Project-native equivalents are allowed.

Dev must not claim final acceptance from:

- cross-service system E2E;
- production-like acceptance;
- full DB/RLS system behavior;
- browser Golden Journey;
- Tester verification.

Those remain downstream Test/Automation ownership.

---

## 21. Engineering review

Preserve bounded policy:

```text
1 consolidated full review
→ 1 blocking fix wave
→ 0–1 scoped rereview
```

Review binds exact upstream, impact, decisions, plan/tasks, base/head revisions, write scope and focused verification.

If review finds a WHAT/spec problem, route the first-class upstream gap path rather than patching BA authority.

---

## 22. Requirements coverage

Dev Handoff VNext coverage domain:

```text
BR-*
FR-*
```

Rules:

- BAREF excluded;
- duplicate IDs fail;
- unknown IDs fail;
- required coverage set must equal exact upstream BA coverage set unless a formally approved deferral exists;
- `COVERED` requires code/test evidence refs;
- Dev cannot mark altered business meaning as covered through implementation reinterpretation.

---

## 23. Dev Handoff VNext

Create versioned Dev Handoff VNext as HANDOFF_MANIFEST.

Minimum:

```text
schema_version
change_id
feature
upstream_engineering_handoff
delivery_manifest optional
engineering_impact
engineering_decisions
technical_approval
repository_revisions
implementation
requirements_coverage
engineering_verification
review
known_risks
knowledge_impact
state
```

Terminal success:

```text
READY_FOR_TEST
```

For multi-repo implementation, bind exact implementation revision per repository.

Finalization must revalidate upstream BA proof.

---

## 24. READY_FOR_TEST conditions

Requires:

1. upstream Engineering Handoff still valid;
2. no unresolved upstream gap;
3. repository base/write-scope integrity;
4. required Engineering Decisions resolved;
5. required Human technical gate authenticated;
6. implementation revisions recorded;
7. no blocking engineering review findings;
8. review budget valid;
9. required engineering verification PASS;
10. exact FR/BR coverage complete;
11. no unapproved scope drift.

It does not mean:

```text
VERIFIED
READY_TO_MERGE
business acceptance
Tester PASS
```

---

## 25. Knowledge Impact

Consume upstream BA Knowledge Impact.

Dev may refine technical targets for architecture/testing without rewriting BA-owned product/domain meaning.

At handoff:

- architecture impact can route Project Foundation/ADR maintenance;
- testing impact routes Test Kit;
- changed technical interfaces/data contracts are explicit.

---

## 26. Compatibility

### Read-old

Keep V1 schemas/readers for historical inspection and benchmark/evidence compatibility.

### Write-new

All new Phase 5 feature runs write VNext.

### No fabricated migration

```text
V1 artifact
→ LEGACY_COMPAT
→ vnext_authority = false
```

A migration helper may create DRAFT VNext runtime artifacts from exact evidence, but may never create authenticated upstream authority, approved Engineering Decisions, technical Human approval or READY_FOR_TEST.

---

## 27. Installed runtime

VNext runtime must include:

- canonical BA VNext reader dependencies;
- Shared SDLC dependencies;
- VNext schemas/state/gap/decision/handoff contracts;
- runtime CLI/adapter;
- Spec Kit workflow definitions;
- plugin skills;
- Doctor;
- provenance.

Isolation acceptance must run with source checkout unavailable, using equivalent isolation to:

```text
python -I
PYTHONPATH removed
```

and assert imports resolve from installed runtime.

---

## 28. Doctor semantics

Doctor checks package/capability readiness only:

- VNext upstream reader;
- VNext schemas;
- workflow definitions;
- Spec Kit pin;
- plugin composition;
- provenance;
- installed imports;
- BA/Foundation dependency closure;
- templates;
- forbidden Spec Kit command absence.

Doctor READY does not imply technical approval, READY_FOR_TEST or VERIFIED.

---

## 29. Public synthetic acceptance

### 29.1 NORMAL feature

```text
Engineering Handoff VNext
→ intake
→ authority validation
→ impact
→ normal plan
→ implementation ready
→ synthetic implementation evidence
→ review
→ fresh engineering verification
→ Dev Handoff VNext READY_FOR_TEST
```

Assert BA bytes never change.

### 29.2 HIGH_RISK feature

Use a neutral public API or persistence migration decision.

Assert implementation is blocked before exact Human technical approval; fake gate text fails; exact authenticated approval passes; changed plan/decision hash invalidates approval.

### 29.3 Engineering Gap

Create a WHAT contradiction and require `UPSTREAM_GAP` with exact affected FR/BR and evidence. No implementation may proceed. Resume requires an explicitly bound replacement Engineering Handoff VNext.

### 29.4 Multi-repo

Bind two neutral repos with exact base revisions/write scopes. Cross-repo must be HIGH_RISK and handoff binds exact output revisions.

### 29.5 Maintenance fast path

No BA Handoff. Only non-behavioral change is allowed; discovering behavior/high-risk invalidates the fast path.

---

## 30. Mandatory negative acceptance

1. V1 handoff cannot start VNext feature implementation.
2. `APPROVED_BASELINE` text alone cannot authorize.
3. missing/false BA Human authenticator fails.
4. changed BA candidate/BR/SRS/Decision/receipt fails.
5. changed Foundation proof fails when present.
6. blocking BA open item fails.
7. BAREF creates no coverage obligation.
8. implementation before IMPLEMENTATION_READY fails.
9. technical gate choice string alone cannot approve.
10. changed plan/decision/impact after technical approval invalidates it.
11. upstream gap blocks affected work.
12. Dev cannot edit BA paths.
13. risk cannot downgrade.
14. NORMAL→HIGH_RISK requires reauthorization.
15. repository base revision drift blocks.
16. write-scope expansion blocks.
17. review budget cannot exceed limit.
18. failing fresh verification blocks READY_FOR_TEST.
19. missing FR/BR coverage blocks READY_FOR_TEST.
20. READY_FOR_TEST never maps to VERIFIED.
21. Doctor READY never maps to feature approval.
22. Spec Kit does not create/require competing `spec.md`.

---

## 31. Genericity

Production/public fixtures must not hard-code:

- Digital Wedding;
- PetClinic;
- Appointment;
- `CR-DWC-*`;
- user-specific names/paths.

Historical benchmark evidence may remain only when clearly non-production and not installed as guidance.

---

## 32. Non-goals

Phase 5 does NOT:

- migrate Test Kit;
- implement system automation;
- implement Phase 8 defect/retest lifecycle;
- make Dev final verifier;
- change BA VNext semantics;
- change Project Foundation semantics;
- change Delivery Manifest V2;
- change UX receipt V2;
- redesign Shared Project Policy;
- modify Digital Wedding repos;
- create Digital Wedding automation repo;
- publish stable OSS release.

---

## 33. Implementation waves

### Wave 1 — Semantic contracts

**Model:** SOL High

Implement only:

- Engineering Handoff VNext intake/revalidation;
- authority modes;
- lifecycle/state V2;
- Engineering Impact VNext;
- Engineering Gap contract;
- Engineering Decision contract;
- technical Human Gate contract;
- FR/BR coverage contract;
- Dev Handoff VNext;
- V1 read compatibility;
- direct unit/contract tests.

Do not wire the full Spec Kit workflows yet.

### Wave 2 — Runtime/workflow integration

**Model:** SOL High

Implement:

- router/start integration;
- NORMAL/HIGH_RISK/TRIVIAL VNext transitions;
- Spec Kit workflow adapter;
- technical gate integration;
- write-scope/base-revision guards;
- planning metadata VNext;
- review/fix/rereview integration;
- fresh engineering verification;
- cross-repo support;
- neutral synthetic E2E;
- installed-runtime semantic acceptance.

No semantic redesign. If Wave 1 is insufficient, stop with `ARCHITECTURE_DECISION_REQUIRED`.

### Wave 3 — Packaging/docs/fresh install

**Model:** LUNA Medium

Mechanical only:

- installer allowlists;
- package/provenance regeneration;
- schemas/templates;
- plugin/kit manifests;
- Doctor;
- EN/VI docs;
- public examples;
- acceptance tiers;
- clean install and isolated runtime;
- compatibility cleanup.

No semantic changes.

---

## 34. Baseline testing

Before Wave 1 modifications, capture baseline at:

```text
main
84c050865630125751f8bfe1c1ca30c0a0a7b8c7
```

Run at least:

- `tooling.tests.test_dev_kit`;
- BA VNext tests;
- Shared SDLC contracts/acceptance;
- Project Foundation tests;
- full tooling unittest discovery.

Do not weaken existing assertions.

---

## 35. Architecture drift guards

Add targeted tests proving:

```text
BA WHAT immutable
Engineering HOW only
legacy V1 != VNext authority
Spec Kit != WHAT authority
Engineering Gap != code-first workaround
technical validator PASS != Human gate approval
gate choice string != authenticated approval
READY_FOR_TEST != VERIFIED
BAREF != coverage
CURRENT_SYSTEM != target WHAT
Doctor READY != feature approval
```

---

## 36. Required Wave 1 report

```text
PHASE_5_WAVE_1_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/dev-kit-vnext-wave1

BASE:
84c050865630125751f8bfe1c1ca30c0a0a7b8c7

HEAD:
<exact SHA>

UPSTREAM_AUTHORITY:
<Engineering Handoff VNext proof>

AUTHORITY_MODES:
<feature delivery / technical maintenance>

DEV_LIFECYCLE:
<state contract>

ENGINEERING_IMPACT:
<contract>

ENGINEERING_GAP:
<first-class upstream path>

ENGINEERING_DECISIONS:
<material HOW records>

TECHNICAL_HUMAN_GATE:
<exact authenticated binding>

SPEC_KIT_BOUNDARY:
<proof no second WHAT>

REQUIREMENTS_COVERAGE:
<FR/BR only; BAREF excluded>

DEV_HANDOFF_VNEXT:
<READY_FOR_TEST semantics>

COMPATIBILITY:
<V1 LEGACY_COMPAT>

SYNTHETIC_CONTRACT_TESTS:
<results>

TESTS:
<commands + counts>

SEMANTIC_CHANGES:
<Dev VNext only; no frozen upstream drift>

BLOCKERS:
<list>

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
feat/dev-kit-vnext-wave1
```

---

## 37. Implementation STOP conditions

Agent must stop with:

```text
ARCHITECTURE_DECISION_REQUIRED
```

instead of silently changing contracts if it needs to:

- alter BA VNext approval semantics;
- alter Project Foundation proof;
- alter Delivery Manifest V2;
- alter UX receipt V2;
- add a new Shared FindingKind when existing taxonomy is sufficient;
- create a second WHAT representation;
- treat Spec Kit plan/spec as business authority;
- weaken Human authentication;
- make READY_FOR_TEST mean VERIFIED;
- move final acceptance into Dev Kit.

---

## 38. Human review checklist

Human approval has been recorded for the following Phase 5 decisions:

1. Engineering Handoff VNext is mandatory WHAT authority for feature delivery.
2. Delivery Manifest remains a delivery envelope and never substitutes BA proof.
3. Technical maintenance may bypass BA only when no WHAT changes.
4. Normative Dev lifecycle V2.
5. `UPSTREAM_REQUIREMENT_GAP` routing reuses Shared `SPEC_GAP` / `BUSINESS_DECISION_REQUIRED` semantics.
6. `ED-*` Engineering Decision identity.
7. mandatory material technical gate categories.
8. exact technical Human approval binding.
9. Spec Kit remains workflow/state infrastructure only.
10. Dev verification stops at READY_FOR_TEST.
11. FR/BR-only coverage contract.
12. three-wave implementation plan.

This checklist is approved. Phase 5 Wave 1 implementation may start under this exact specification.

---

## 39. Action after Human approval

1. Commit the approved spec as a temporary bootstrap artifact on a dedicated Phase 5 source branch created from current `main`.
2. Start a fresh SOL High implementation session.
3. Agent fetches remote and reads the exact spec.
4. Agent creates `feat/dev-kit-vnext-wave1`.
5. Agent implements Wave 1 only.
6. Temporary spec is removed from the final implementation tree.
7. Push remote.
8. Independent SOL review before Wave 2.

---

## 40. Temporary bootstrap cleanup

This file is a temporary bootstrap artifact on `phase5/dev-kit-vnext-bootstrap`.

A fresh implementation agent must:

1. fetch and read this entire file before implementation;
2. create `feat/dev-kit-vnext-wave1` from the latest remote bootstrap branch;
3. implement **Wave 1 only**;
4. DELETE `PHASE_5_DEV_KIT_VNEXT_EXECUTION_SPEC.md` from the implementation branch before the final commit/report;
5. not copy, rename, or preserve this temporary spec under docs/evidence/runtime;
6. verify the final Wave 1 tree does not contain this file.

The authoritative behavioral implementation base remains:

```text
84c050865630125751f8bfe1c1ca30c0a0a7b8c7
```

The bootstrap-only commit(s) do not change Phase 4 behavior.
