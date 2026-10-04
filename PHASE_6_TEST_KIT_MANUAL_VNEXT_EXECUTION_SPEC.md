# PHASE 6 — TEST KIT MANUAL VNEXT EXECUTION SPEC

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills
Authoritative base: main @ ec9955f7c26cd69e2a83d56dfbfba02fb55abc44
Implementation branch for Wave 1: feat/test-kit-manual-vnext-wave1
Recommended model: gpt-6-luna, Extra High if available; otherwise High/Medium with the same stop conditions.

> Phase 6 standardizes the manual Test Design + Testcase lane only.
> Automation planning, automation implementation, execution, defect/retest and final VERIFIED are deliberately out of scope.

---

## 1. Objective

Migrate the mature Test Kit V1/V1.1 manual lane into Test Kit Manual VNext without rewriting working canonical testware mechanics.

The production path after this phase is:

```text
Engineering Handoff VNext
        │
        ├── optional Approved UX Context
        ├── optional Dev/execution context
        └── optional Project Test Policy
        │
        ▼
DRAFT_DESIGN
        ▼
DESIGN_REVIEW
        ▼
Human Design Gate
        ▼
APPROVED_DESIGN
        ▼
DRAFT_CASES
        ▼
CASE_REVIEW
        ▼
Human Case Gate
        ▼
APPROVED_TESTWARE
```

There is no STOP_VNEXT state.

APPROVED_TESTWARE is the Phase 6 terminal state and the durable handoff to Phase 7 Automation Planning.

---

## 2. Frozen architecture principles

Use:

```text
STRICT AT AUTHORITY BOUNDARIES
LEAN IN ORCHESTRATION
```

Do not create a new abstraction if the existing Test V1 mechanism already satisfies the VNext invariant.

Frozen authority order remains:

1. Human-approved decisions
2. Shared SDLC invariants
3. Project policy/instructions
4. Kit/atomic-skill mechanics
5. Runtime defaults

Frozen invariants:

- CONTINUE != APPROVE
- ANSWER != APPROVE
- REVIEW != APPROVE
- PASS != APPROVE
- validator PASS != APPROVE
- generated != APPROVED
- Derived != Authority
- CURRENT_SYSTEM != confirmed target
- Human Gate binds exact artifact revision/hash
- BA owns WHAT
- UX owns approved interaction/presentation semantics
- Engineering owns HOW
- Test proves approved behavior
- Dev implementation cannot become the business oracle
- Tester does not invent missing business semantics
- APPROVED_TESTWARE != EXECUTION_READY
- APPROVED_TESTWARE != VERIFIED
- BAREF is provenance/locator only, never canonical coverage

---

## 3. Existing Test Kit behavior to preserve

The current Test Kit is already mature in the manual lane. Preserve the following unless an objective VNext requirement proves a change is necessary.

### 3.1 Canonical Test Design

Semantic shape:

```text
design_id
hierarchy_path
scenario_title
expected_behavior
requirement_refs
open_questions
```

review_status remains a projection and is not part of immutable semantic bytes.

### 3.2 Immutable Test Design snapshot

Preserve:

```text
artifact_id
revision
semantic payload bytes
SHA-256
raw evidence
field sources
```

### 3.3 Human Design Gate

Preserve the exact-snapshot model:

```text
DRAFT_DESIGN
→ validator PASS
→ DESIGN_REVIEW
→ exact authenticated Human receipt
→ APPROVED_DESIGN
```

REQUEST_CHANGES must create a new immutable revision.

### 3.4 Canonical Testcases

Preserve semantic shape:

```text
test_case_id
name
objective
preconditions
test_data
steps:
  action
  test_data
  expected_result
priority
requirement_refs
test_design_refs
execution_dependencies
```

### 3.5 Human Case Gate

Preserve the existing exact-snapshot behavior:

- exact CASE_REVIEW state;
- exact artifact ID/revision/hash;
- exact current input refs;
- host-authenticated Human;
- exact approved Design + Design Gate proof;
- exact execution-oracle refs when consumed;
- fail closed on unresolved required semantic oracle;
- REQUEST_CHANGES creates a new immutable revision.

### 3.6 Generator boundaries

Keep:

```text
BMAD TEA
  = analysis/advisory/raw generator
  != canonical authority

Katalon create-test-cases
  = raw testcase generator
  != canonical authority
```

### 3.7 Derived projections

Keep one-way only:

```text
APPROVED_DESIGN
→ XMind DERIVED projection

APPROVED_TESTWARE
→ Excel DERIVED projection
```

No reverse import.

### 3.8 Project Test Policy

Project Test Policy remains testing/generation guidance only.

It may affect decomposition, naming, safe test data, coverage emphasis and presentation.

It may not supply:

- business WHAT;
- expected business result;
- execution oracle;
- Human approval.

### 3.9 TEST_ONLY fixtures

Synthetic receipts/testware remain explicitly TEST_ONLY and not_for_production.

They may prove the framework path but cannot establish production authority.

---

## 4. Current gaps to fix

### P6-01 — Legacy BA authority plumbing

Current Test V1 relies on legacy ApprovedBaseline / engineering-handoff.yml / APPROVED_FOR_ENGINEERING style semantics.

VNext must consume the canonical BA Engineering Handoff VNext reader and exact BA approval proof.

Do not duplicate BA validator semantics.

### P6-02 — BAREF is accepted in canonical trace

VNext canonical business trace must contain only:

```text
BR-*
FR-*
```

BAREF:* may remain in provenance/evidence locators only.

Any BAREF in canonical Test Design/Testcase requirement_refs must fail.

### P6-03 — STOP_V1 terminal

For new VNext runs, replace:

```text
CASE_REVIEW
→ APPROVED_TESTWARE
→ STOP_V1
```

with:

```text
CASE_REVIEW
→ APPROVED_TESTWARE
```

Do not invent STOP_VNEXT.

### P6-04 — Delivery Manifest currently mixes BA/UX context

Delivery Manifest remains:

```text
DEFERRED_NON_AUTHORITATIVE
```

Phase 6 must not redesign Delivery Manifest or make it required.

Use direct BA VNext authority plus a narrow optional UX-context adapter.

### P6-05 — UX context needs a direct safe adapter

Reuse the repository's existing UX approval receipt contract.

Do not invent UX V3.

The Test-owned UX adapter must validate exact contract bytes, exact receipt bytes, feature/revision binding, snapshot hash and trusted Human authentication.

Prototype remains REVIEW_EVIDENCE, not semantic authority.

### P6-06 — Dev technical context must not become WHAT

Dev Handoff V2 is optional in Phase 6.

Manual Test Design must be possible before implementation is complete.

Dev/execution context may help with:

- setup;
- interface location;
- fixture contract;
- observation mechanism;
- implementation revision evidence.

It may not change FR/BR or approved UX expected behavior.

If implementation contradicts approved BA/UX semantics, stop and raise the upstream gap. Do not change the expected result to match code.

### P6-07 — Operator/package surfaces are V1-oriented

Operational surfaces still teach V1 wording, CR-001 and STOP_V1.

Wave 2 will convert default operational guidance to VNext while preserving V1 compatibility.

---

## 5. Test Authority Bundle

Do not create a new Shared Core global artifact merely for naming.

Conceptually, the Test authority context is:

```text
Test Authority Bundle
├── REQUIRED: Engineering Handoff VNext
├── OPTIONAL: Approved UX Context
├── OPTIONAL: Dev / execution context
└── OPTIONAL: Project Test Policy snapshot
```

Role separation:

```text
BA Handoff
  = business WHAT authority

Approved UX Context
  = approved interaction/presentation semantics

Dev / execution context
  = technical setup/action/observation evidence only

Project Test Policy
  = testing/generation guidance only
```

The Human Design/Case receipts bind the exact refs actually consumed.

No new authority rank is introduced.

---

## 6. Required BA VNext authority

Production Test Design requires Engineering Handoff VNext.

Revalidate using the canonical BA VNext implementation.

The Test reader must prove at least:

- exact BA baseline candidate;
- exact Human BA approval receipt;
- trusted Human authentication;
- exact Decisions / Business Rules / SRS bytes;
- exact BR/FR inventory;
- no blocking open items;
- Project Foundation durable proof when present;
- no stale upstream bytes after callback.

Do not implement a second BA approval engine inside Test Kit.

Legacy V1 BA inputs may remain inspectable only through explicit compatibility paths and cannot grant VNext authority.

---

## 7. Optional Approved UX Context

UX is required only when:

- project/feature metadata explicitly requires it; or
- the Test Design/Testcase asserts approved interaction/presentation behavior not fully represented by BA authority.

Do not require UX for every feature.

Reuse the existing UX approval receipt schema version 1 or 2.

The Test UX adapter must:

1. resolve an exact UX semantic contract ref;
2. resolve an exact UX approval receipt ref;
3. validate matching feature and revision;
4. validate exact source bytes/hashes;
5. validate canonical snapshot hash;
6. validate decision APPROVE and explicit Human approval shape;
7. call a trusted host authenticator for production authority;
8. recheck exact bytes after the callback;
9. return normalized immutable refs for gate binding.

Prototype remains REVIEW_EVIDENCE.

Forbidden:

- modifying Delivery Manifest V2;
- creating Delivery Manifest V3;
- creating UX receipt V3;
- treating prototype HTML/image/screenshot as semantic authority;
- allowing UX to override BA WHAT.

A BA/UX semantic contradiction is a blocking upstream gap.

---

## 8. Optional Dev / execution context

Dev Handoff V2 is optional.

Test Design must be able to complete without Dev Handoff.

Testcase execution dependencies may consume exact technical/execution contracts when required to define setup/action/observation.

Example valid technical context:

- approved endpoint/interface;
- observable response field;
- DB setup contract;
- fixture creation boundary;
- repository/revision evidence;
- module-local technical behavior that does not redefine business WHAT.

Any such ref must be exact and immutable at the Case Gate.

Implementation behavior is never allowed to override approved BA/UX semantics.

---

## 9. Canonical trace

Business trace for VNext:

```text
Human BA Decision
→ BR-* / FR-*
→ TD-*
→ TC-*
```

Canonical requirement_refs may contain BR-* and FR-* only.

Reject:

- BAREF:*;
- unknown IDs;
- malformed IDs;
- duplicate trace rows;
- range expansion containing IDs absent from the approved BA inventory.

Optional context may be recorded separately:

```text
Approved UX source
→ TD / TC interaction evidence

Dev/execution contract
→ TC execution dependency resolution
```

Do not create AUT-* in Phase 6.

---

## 10. Test Design VNext

Preserve the current canonical Test Design semantic shape.

Raw TEA output stays EVIDENCE.

Canonical Test Design stays CANONICAL.

review_status remains a non-semantic projection.

Validator must prove:

- exact BA authority is current;
- optional UX authority is current when consumed;
- each requirement_ref is canonical FR/BR;
- expected behavior is supported by approved authority;
- UNKNOWN remains UNKNOWN;
- no invented threshold/filter/sort/pagination/business result;
- project policy did not supply business semantics;
- raw TEA evidence is preserved but non-authoritative.

Lifecycle:

```text
DRAFT_DESIGN
→ DESIGN_REVIEW
→ APPROVED_DESIGN
```

Request changes:

```text
DESIGN_REVIEW
→ CHANGES_REQUESTED
→ new DRAFT_DESIGN revision
```

Do not add VALIDATED_DESIGN as a lifecycle state.

Validator PASS is an entry condition to DESIGN_REVIEW, not approval.

---

## 11. Human Design Gate

Production receipt continues to bind:

```text
gate = DESIGN_REVIEW
decision = APPROVE | REQUEST_CHANGES
artifact_id
artifact_revision
artifact_sha256
exact input_refs
actor_id
actor_role = HUMAN
decided_at
feedback
```

Rules:

- trusted host authenticates the Human;
- validator PASS cannot approve;
- TEA completion cannot approve;
- REVIEW cannot approve;
- CONTINUE cannot approve;
- PASS cannot approve;
- ANSWER cannot approve;
- workflow-state prose cannot approve;
- exact input drift invalidates stale approval;
- receipt replay fails;
- REQUEST_CHANGES creates a new revision.

---

## 12. Canonical Testcases VNext

Preserve the current semantic shape.

Raw Katalon output stays EVIDENCE.

Canonical Testcases stay CANONICAL.

Production testcase generation requires exact APPROVED_DESIGN + exact Design Gate receipt.

Do not bypass Design approval and generate production testcases directly from BA authority.

Testcase validator must:

- bind exact approved Design;
- trace to canonical BR/FR;
- reject BAREF;
- preserve ordered actions and expected results;
- preserve explicit test data scope;
- keep execution dependencies explicit;
- fail closed when raw generator output cannot be mapped without invention.

---

## 13. Execution dependencies

Preserve the existing execution_dependencies concept.

Keep explicit fields equivalent to:

```text
need
kind
required/material semantics
status
resolution_ref
```

Do not require Dev Handoff merely because an execution dependency exists.

If a dependency is unresolved but not required for semantic correctness, keep it explicit.

If unresolved dependency prevents a testcase from asserting an observable pass/fail condition, Case approval must fail.

Do not invent an execution oracle.

---

## 14. Human Case Gate

Lifecycle:

```text
DRAFT_CASES
→ CASE_REVIEW
→ APPROVED_TESTWARE
```

Request changes:

```text
CASE_REVIEW
→ CHANGES_REQUESTED
→ new DRAFT_CASES revision
```

Approval requires:

- exact CASE_REVIEW snapshot;
- exact approved Design;
- exact Design Gate receipt;
- exact BA authority refs;
- exact approved UX refs when consumed;
- exact project policy ref when consumed;
- exact execution oracle refs when consumed;
- current validator PASS;
- no unresolved required semantic oracle;
- trusted Human authentication.

Receipt replay or input drift fails closed.

For VNext, APPROVED_TESTWARE is terminal. Do not write STOP_V1 or STOP_VNEXT as the production VNext terminal.

---

## 15. Approved Testware VNext

Create/version a VNext Approved Testware manifest.

Artifact class:

```text
HANDOFF_MANIFEST
```

Minimum binding:

```text
schema_version
feature_id
testcase_collection
approved_design
design_gate_receipt
case_gate_receipt
ba_engineering_handoff
ba_baseline exact identity
ux_context optional
dev_context optional
execution_oracle_refs
project_policy_context optional
trace_summary
state = APPROVED_TESTWARE
```

Do not copy BR/FR prose into the handoff manifest.

Bind exact refs only.

This manifest is the durable Phase 6 output consumed by Phase 7.

APPROVED_TESTWARE does not mean:

- EXECUTION_READY;
- execution PASS;
- VERIFIED;
- READY_TO_MERGE.

---

## 16. Findings and upstream gaps

Use Shared finding vocabulary.

Business/UX ambiguity:

```text
SPEC_GAP
BUSINESS_DECISION_REQUIRED
```

Test-generation/tooling issue:

```text
TEST_ISSUE
```

Environment/dependency issue:

```text
ENVIRONMENT_ISSUE
```

Do not implement Phase 8 defect/retest state machine here.

If Test analysis finds a contradiction in approved WHAT:

```text
stop affected testware
→ preserve evidence
→ route upstream
→ receive revised approved authority
→ create/review a new testware revision
```

Do not patch test expected results to match implementation.

---

## 17. Project Test Policy

Preserve existing project policy snapshots and drift checks.

Policy is non-authoritative guidance.

Human gate input_refs continue to bind the exact policy snapshot consumed.

Do not redesign Test project policy in Phase 6.

---

## 18. XMind and Excel

Preserve current architecture.

XMind:

```text
APPROVED_DESIGN
→ XMind DERIVED projection
```

No reverse import.

Do not add Human-supplied XMind-template support in Phase 6 unless existing code already supports it without semantic change.

Excel:

```text
APPROVED_TESTWARE
→ Excel DERIVED projection
```

Existing template precedence may remain:

```text
HUMAN_SUPPLIED_APPROVED_TEMPLATE
→ PROJECT_TEMPLATE
→ DEFAULT_TEMPLATE
```

Templates must not alter canonical semantics.

No automation result state belongs in these manual-test projections.

---

## 19. V1 compatibility

Current V1 artifacts remain readable.

Use explicit compatibility results equivalent to:

```text
LEGACY_COMPAT
vnext_authority = false
```

A V1 Design/Case/Testware artifact cannot silently become VNext authority.

No migration utility may fabricate:

- BA VNext authority;
- UX Human approval;
- Design approval;
- Case approval;
- execution oracle approval.

Optional draft-only migration is acceptable if it remains unapproved.

Do not weaken existing V1 tests.

---

## 20. Runtime persistence

Reuse current Test run-directory and gate persistence architecture where practical.

Requirements:

- immutable reviewed snapshots;
- atomic Human gate writes;
- receipt replay protection;
- fresh-process resume;
- exact gate input refs;
- project policy drift detection;
- raw evidence integrity;
- VNext state independent of conversational/session memory.

Do not rewrite persistence just for naming consistency.

---

## 21. Public genericity

VNext default operational examples must be neutral synthetic examples.

Do not use as default operational guidance:

- Digital Wedding;
- CR-DWC-*;
- PetClinic;
- Appointment;
- user/company-specific paths.

Historical PetClinic benchmark evidence may remain clearly isolated under benchmark/test-kit/.

Do not rewrite benchmark history only to make names generic.

---

## 22. Phase 6 non-goals

Do NOT implement:

- Automation Suitability;
- Automation Plan;
- AUT-* artifacts;
- Playwright/API automation generation;
- automation repository orchestration;
- test execution;
- execution manifest;
- PASS/FAIL execution results;
- defect creation;
- Dev fix/retest;
- VERIFIED;
- Delivery Manifest redesign;
- Dev Kit semantic changes;
- BA Kit semantic changes;
- Project Foundation semantic changes;
- Shared Core redesign;
- Digital Wedding migration.

These belong to later phases.

---

# WAVE 1 — LARGE IMPLEMENTATION WAVE

## 23. Wave 1 objective

Wave 1 intentionally combines semantic migration and runtime/operator integration to reduce manual review rounds.

Implement all of the following in one branch:

```text
feat/test-kit-manual-vnext-wave1
```

### 23.1 Semantic authority migration

Implement:

- BA Engineering Handoff VNext reader for Test;
- exact BA Human proof revalidation;
- normalized Test authority context;
- canonical BR/FR-only trace;
- BAREF rejection from canonical coverage;
- optional approved UX adapter;
- optional Dev/execution context adapter;
- exact Design Gate VNext input refs;
- exact Case Gate VNext input refs;
- terminal APPROVED_TESTWARE;
- VNext Approved Testware handoff manifest;
- explicit V1 LEGACY_COMPAT readers.

### 23.2 Runtime/operator integration

In the same Wave 1, integrate:

- default new-run VNext routing;
- persisted VNext authority refs;
- trusted host callbacks for BA/UX/Human gate authentication;
- TEA native invocation through current production operator path;
- Katalon native invocation through current production operator path;
- Design review/request-changes/resume;
- Case review/request-changes/resume;
- project Test Policy snapshots and stale detection;
- optional approved UX refs in Design/Case gates;
- optional Dev/execution-oracle refs in Case gate;
- XMind production projection from exact APPROVED_DESIGN;
- Excel production projection from exact APPROVED_TESTWARE;
- fresh-process resume for current persisted run architecture;
- neutral synthetic full manual-flow acceptance.

### 23.3 Do not do in Wave 1

Do not:

- change package version solely for the semantic implementation;
- rewrite installer/package authority unless runtime integration absolutely requires a compatibility hook;
- rewrite all docs;
- build fresh-install acceptance;
- redesign TEA/Katalon pins;
- add automation planning/execution;
- change Delivery Manifest V2;
- change Shared Core/BA/Dev semantics.

If an existing package test needs a minimal mechanical compatibility update because a file moved or a default router now points to VNext, that is allowed. Full packaging remains Wave 2.

---

## 24. Wave 1 baseline

Base:

```text
ec9955f7c26cd69e2a83d56dfbfba02fb55abc44
```

Before changes, record baseline results for at least:

```text
tooling.tests.test_test_kit_v1
tooling.tests.test_test_kit_v1_case_gate
tooling.tests.test_test_kit_v1_cases
tooling.tests.test_test_kit_policy
tooling.tests.test_test_kit_policy_review
tooling.tests.test_test_kit_customization
tooling.tests.test_kit_packaging
tooling.tests.test_ba_vnext
tooling.tests.test_dev_vnext
tooling.tests.test_sdlc_contracts
full tooling unittest discovery
```

Do not weaken failing assertions to make VNext pass.

If a baseline failure already exists, record it exactly before modification and prove the final result does not introduce a regression.

---

## 25. Wave 1 mandatory acceptance

### A. Normal manual feature

Prove:

```text
Engineering Handoff VNext
→ Test Design candidate
→ validator PASS
→ DESIGN_REVIEW
→ authenticated Human APPROVE
→ APPROVED_DESIGN
→ Testcases candidate
→ validator PASS
→ CASE_REVIEW
→ authenticated Human APPROVE
→ APPROVED_TESTWARE
```

Assert exact FR/BR trace.

### B. No self approval

Prove none of these can approve Design or Case Gate:

```text
validator PASS
TEA complete
Katalon complete
CONTINUE
REVIEW
PASS
ANSWER
workflow/status prose
```

### C. BAREF exclusion

Any canonical Design or Case requirement_refs containing BAREF:* must fail.

### D. BA UNKNOWN

An unresolved BA outcome:

- remains an open question;
- may yield deferred Design expected behavior;
- cannot become a concrete Case expected result without revised approved authority.

### E. UX-required feature

When UX is explicitly required:

- missing approved UX proof blocks relevant UX assertions;
- exact approved UX context passes;
- prototype alone fails;
- changed UX bytes invalidate current gate proof;
- stale receipt fails;
- unauthenticated Human fails;
- BA/UX contradiction blocks.

### F. No-UX feature

A feature that does not require UX can complete the full manual flow without a UX artifact.

### G. Optional Dev context

Test Design completes without Dev Handoff.

Case may consume exact Dev/execution contract to resolve technical setup/observation.

Implementation cannot override BA/UX expected result.

### H. Human request changes

For both Design and Case:

```text
REQUEST_CHANGES
→ reviewed snapshot remains immutable
→ new revision starts DRAFT
→ old receipt cannot approve new revision
```

### I. Runtime resume

Persist an in-progress run, create a fresh runtime/process, reload and continue without relying on session memory.

At minimum cover one Design-stage resume and one Case-stage resume if current persistence architecture supports both.

### J. Projection compatibility

Prove:

```text
APPROVED_DESIGN → XMind
APPROVED_TESTWARE → Excel
```

while projections remain DERIVED and one-way.

### K. V1 compatibility

V1 Design/Case/Testware stays inspectable but cannot authorize VNext production flow.

---

## 26. Wave 1 architecture drift guards

Add direct regressions proving:

```text
BA WHAT immutable
UX prototype != authority
Dev implementation != business oracle
TEA != authority
Katalon != authority
Project Test Policy != authority
validator PASS != Human approval
CONTINUE/PASS/REVIEW/ANSWER != approval
BAREF != canonical trace
APPROVED_TESTWARE != EXECUTION_READY
APPROVED_TESTWARE != VERIFIED
V1 != VNext authority
Delivery Manifest != required VNext authority
```

---

## 27. Wave 1 STOP conditions

Stop and report:

```text
ARCHITECTURE_DECISION_REQUIRED
```

instead of silently changing architecture if implementation would require:

- changing BA VNext approval semantics;
- changing Dev VNext authority semantics;
- changing Shared Core authority precedence;
- modifying Delivery Manifest V2 semantics;
- creating UX schema V3;
- making prototype authority;
- requiring Dev Handoff for all Test Design;
- making Test Design depend on implementation completion;
- adding automation planning/execution;
- making APPROVED_TESTWARE mean VERIFIED;
- redesigning the entire Test package/install system;
- materially modifying pinned upstream TEA/Katalon semantics;
- introducing a new fourth/fifth kit;
- adding a new global Shared authority artifact not required by the frozen design.

---

## 28. Wave 1 file/scope guidance

Prefer extending existing Test modules rather than rewriting them.

Expected likely areas include:

```text
tooling/lib/test_kit_v1.py
tooling/lib/test_kit_v1_cases.py
tooling/lib/test_kit_policy.py
tooling/lib/*new narrow VNext adapters if justified*
tooling/tests/test_test_kit_*
kits/test/skills/test-kit/SKILL.md only if needed for runtime routing
```

A dedicated VNext module is allowed if it reduces compatibility risk, but do not duplicate the full V1 codebase.

Preserve current XMind/Excel implementations unless the new terminal state requires a minimal compatibility adapter.

Do not rewrite historical benchmark fixtures unless required for a compatibility regression.

---

## 29. Wave 1 final tests

Run focused tests plus full discovery.

Minimum:

```text
python -m unittest tooling.tests.test_test_kit_v1
python -m unittest tooling.tests.test_test_kit_v1_case_gate
python -m unittest tooling.tests.test_test_kit_v1_cases
python -m unittest tooling.tests.test_test_kit_policy
python -m unittest tooling.tests.test_test_kit_policy_review
python -m unittest tooling.tests.test_test_kit_customization
python -m unittest tooling.tests.test_test_kit_v1_xmind
python -m unittest tooling.tests.test_test_kit_v1_excel
python -m unittest tooling.tests.test_ba_vnext
python -m unittest tooling.tests.test_dev_vnext
python -m unittest tooling.tests.test_sdlc_contracts
python -m unittest discover -s tooling/tests -p "test_*.py"
git diff --check
```

Run any newly added VNext Test modules explicitly as well.

Zero new failures/errors are allowed.

---

## 30. Wave 1 branch hygiene

Source bootstrap branch:

```text
phase6/test-kit-manual-vnext-bootstrap
```

Implementation branch:

```text
feat/test-kit-manual-vnext-wave1
```

Requirements:

1. fetch origin;
2. start from the exact bootstrap commit containing this spec;
3. keep semantic base identity recorded as ec9955f7c26cd69e2a83d56dfbfba02fb55abc44;
4. implement Wave 1 only;
5. delete this temporary spec before final implementation commit;
6. final tree must not contain this temporary spec;
7. push branch;
8. do not merge;
9. worktree must be clean;
10. report exact final HEAD.

---

## 31. Wave 1 required report

```text
PHASE_6_WAVE_1_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/test-kit-manual-vnext-wave1

BASE:
ec9955f7c26cd69e2a83d56dfbfba02fb55abc44

HEAD:
<exact SHA>

UPSTREAM_AUTHORITY:
<BA Engineering Handoff VNext exact proof>

UX_CONTEXT:
<optional approved-context implementation>

DEV_CONTEXT:
<optional technical/execution implementation>

DESIGN_CONTRACT:
<preserved canonical semantics>

DESIGN_GATE:
<exact Human binding>

TRACEABILITY:
<FR/BR only; BAREF excluded>

CASE_CONTRACT:
<preserved canonical semantics>

EXECUTION_DEPENDENCIES:
<fail-closed resolution>

CASE_GATE:
<exact Human binding>

APPROVED_TESTWARE:
<VNext handoff manifest + terminal semantics>

RUNTIME_ROUTING:
<default VNext operator flow>

PERSISTENCE_RESUME:
<fresh-process results>

TEA_BOUNDARY:
<advisory/evidence only>

KATALON_BOUNDARY:
<generator/evidence only>

PROJECT_POLICY:
<non-authoritative>

XMIND:
<APPROVED_DESIGN derived projection>

EXCEL:
<APPROVED_TESTWARE derived projection>

LEGACY_COMPAT:
<V1 read compatibility>

SYNTHETIC_ACCEPTANCE:
<full manual E2E results>

TESTS:
<commands + pass/fail/skip>

SEMANTIC_DRIFT:
NONE
or exact list

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
feat/test-kit-manual-vnext-wave1

RECOMMENDED_WAVE_2:
READY | NOT_READY
```

---

# WAVE 2 — PACKAGING / FRESH INSTALL / COMPLETION

## 32. Wave 2 objective

Wave 2 is a larger mechanical completion wave after independent Wave 1 review.

Scope:

- Test Kit manifest/version;
- package-authority regeneration;
- package payload/provenance regeneration;
- default VNext router/skill docs;
- VNext schemas/templates where useful;
- explicit V1 LEGACY_COMPAT docs/surfaces;
- installer and uninstall behavior;
- Doctor;
- neutral public example;
- EN/VI operational docs;
- acceptance tiers;
- fresh installed-runtime acceptance;
- installed isolation;
- XMind/Excel optional dependency packaging;
- genericity scan;
- full package tests;
- final Phase 6 completion review.

Wave 2 must not redesign Wave 1 semantics.

If semantic change is required, stop ARCHITECTURE_DECISION_REQUIRED.

---

## 33. Wave 2 package semantics

Test Kit remains one product/orchestrator.

Do not create:

```text
test-manual-kit
test-vnext-kit
automation-test-kit inside Phase 6
```

The installed default new-run behavior is VNext.

V1 is explicit compatibility/inspection only.

Doctor READY means package/capability readiness only.

Doctor must not claim:

- Human approval;
- APPROVED_TESTWARE;
- EXECUTION_READY;
- VERIFIED.

---

## 34. Wave 2 fresh-install acceptance

Mandatory:

1. install into a clean temporary target;
2. prevent accidental imports from source checkout;
3. run Doctor;
4. create a neutral synthetic BA VNext approved authority fixture through the trusted test host path;
5. run full manual VNext flow:
   - Design candidate;
   - Design review;
   - negative self-approval;
   - synthetic authenticated Human Design approval;
   - Cases candidate;
   - Case review;
   - negative self-approval;
   - synthetic authenticated Human Case approval;
   - APPROVED_TESTWARE;
6. re-read and revalidate installed artifacts;
7. prove V1 remains LEGACY_COMPAT;
8. run Doctor again;
9. assert installed modules load only from installed Test Kit package/runtime;
10. verify XMind/Excel optional-capability behavior without making them required for core Test Kit readiness.

---

## 35. Wave 2 public example

Replace default/public CR-001 guidance with a neutral synthetic example.

No Digital Wedding, PetClinic, Appointment or user/company-specific semantics in default operational examples.

Historical benchmarks can remain in benchmark/ paths.

---

## 36. Wave 2 completion guard

Phase 6 completes only when all of the following are true:

```text
BA VNext authority consumed exactly
FR/BR-only canonical trace
Human Design Gate exact
Human Case Gate exact
APPROVED_TESTWARE terminal
V1 LEGACY_COMPAT
TEA/Katalon non-authoritative
Project Test Policy non-authoritative
XMind/Excel derived only
fresh install PASS
installed isolation PASS
Doctor package/capability semantics PASS
neutral public example PASS
full tooling tests PASS
temporary specs absent
```

---

## 37. Phase 6 final terminal

After Wave 2 independent review:

```text
PHASE 6 — TEST KIT MANUAL VNEXT
STATUS: VERIFIED COMPLETE
```

Next phase:

```text
PHASE 7 — AUTOMATION V1
Automation Suitability
→ Automation Plan
→ AUT-* identity
→ automation repository implementation
→ EXECUTION_READY
```

Do not implement Phase 7 inside Phase 6.
