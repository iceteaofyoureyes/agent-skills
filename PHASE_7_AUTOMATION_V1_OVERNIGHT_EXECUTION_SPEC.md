# PHASE 7 — TEST AUTOMATION V1 — OVERNIGHT EXECUTION SPEC

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills
Authoritative base: main @ 44617175f1c441811f7bf4f64672964d7446ac39
Phase 6 dependency: Test Kit Manual VNext 2.0.0-rc.6 VERIFIED COMPLETE + merged
Target branch: feat/test-automation-v1-phase7
Recommended model: GPT-6 Luna Extra High

This is a single large overnight completion attempt.

The agent MUST try to complete all Phase 7 work in one branch/session.
Do not voluntarily stop after semantics/runtime because the scope is large.

Early stop is allowed only for:
- ARCHITECTURE_DECISION_REQUIRED; or
- an unrecoverable environment/tooling blocker that cannot be solved without violating this spec.

Normal implementation defects, test failures, package drift, hash drift, documentation drift and mechanical regressions are part of the task and must be fixed in the same branch.

Do not merge to main.

---

## 1. Target lifecycle

Extend the existing Test Kit. Do NOT create a separate Automation Kit.

Target:

APPROVED_TESTWARE
→ Automation Suitability
→ Automation Plan
→ Automation Implementation
→ Automation Review
→ Automation Verification
→ EXECUTION_READY

Shift-left is allowed:

Dev implementation / verification and Test automation planning may proceed in parallel.

But EXECUTION_READY requires an exact current Dev Handoff V2 with state READY_FOR_TEST.

Phase 8 starts after EXECUTION_READY.

Phase 7 MUST NOT implement:
- real product/API/E2E execution;
- PASS/FINDING runtime;
- execution observations;
- defect classification;
- DEFECT handoff;
- Dev fix/retest;
- READY_FOR_RETEST;
- VERIFIED/REOPENED;
- READY_TO_MERGE.

---

## 2. Human-approved frozen architecture decisions

These are already approved and MUST NOT be reopened during implementation:

1. No third Human Gate for Automation Plan.
   Automation Plan is technical/test HOW, not new business authority.

2. Test Automation never writes application repositories.
   UNIT/COMPONENT are Dev-local references.

3. Test-owned automation writes only to the repository resolved from:
   .sdlc/project-policy.yml -> testing.automation_repository_role
   plus .sdlc/project-topology.yml.

4. Final EXECUTION_READY requires exact Dev Handoff V2 READY_FOR_TEST.
   Planning/implementation may begin earlier.

5. Delivery Manifest remains DEFERRED_NON_AUTHORITATIVE for Phase 7.

6. Playwright or any concrete automation framework remains project-owned.
   Core Automation V1 is tool agnostic.

7. Phase 7 ends at EXECUTION_READY.
   No real SUT acceptance execution occurs in Phase 7.

8. Complete Phase 7 as one large overnight branch/session where possible.

Changing any item above requires:

ARCHITECTURE_DECISION_REQUIRED

---

## 3. Guiding principle

STRICT AT AUTHORITY BOUNDARIES.
LEAN IN ORCHESTRATION.

Do not invent new approvals or duplicate existing semantic authority.

The approved Testcase remains the expected-behavior oracle.

Executable automation is never business authority.

---

## 4. Existing contracts to reuse

Reuse canonical existing implementation instead of near-duplicates:

- Test Kit Manual VNext APPROVED_TESTWARE HANDOFF_MANIFEST;
- canonical Design/Testcase artifacts;
- Design Gate and Case Gate exact Human receipts;
- BA VNext exact authority validation;
- optional approved UX context;
- Dev Handoff V2 validator;
- Project Topology V1;
- Project Policy V1;
- Shared readiness vocabulary;
- Shared finding taxonomy;
- typed execution dependency vocabulary;
- existing Test package/install/Doctor architecture.

Do not use the existing legacy shared/sdlc/findings/execution_contract.py as the Phase 7 authority path.
It is Delivery-Manifest/Test-V1 coupled and remains legacy until Phase 8 migration.

Do not modify Delivery Manifest semantics.

---

## 5. Required Test authority

Automation V1 production path requires exact APPROVED_TESTWARE VNext.

Revalidate at least:

- testcase collection;
- approved Design;
- Design Gate receipt;
- Case Gate receipt;
- BA Engineering Handoff VNext;
- BA baseline identity;
- exact optional UX context consumed;
- exact optional Dev context consumed;
- exact project-policy context consumed;
- execution oracle refs;
- canonical BR/FR trace;
- state == APPROVED_TESTWARE.

Only VNext approved testware can authorize Automation V1.

V1/legacy Test artifacts stay inspection-only and cannot authorize this lane.

Synthetic TEST_ONLY fixtures are acceptance fixtures only and never production approval.

---

## 6. Automation classes

Support exactly:

UNIT
COMPONENT
CONTRACT
DB_RUNTIME
API
INTEGRATION
E2E
ACCESSIBILITY
SYSTEM
MANUAL_ONLY
BLOCKED

Ownership defaults:

UNIT / COMPONENT
→ DEV_LOCAL_REFERENCE

CONTRACT / DB_RUNTIME / API / INTEGRATION / E2E / ACCESSIBILITY / SYSTEM
→ TEST_AUTOMATION

MANUAL_ONLY
→ MANUAL

BLOCKED
→ BLOCKED

Do not add a score/confidence threshold.

---

## 7. Application repository boundary

Application/source repositories are read-only to Phase 7 Test Automation.

Phase 7 may inspect:
- Dev Handoff;
- source-local test evidence;
- implementation revisions;
- interfaces/config needed for automation planning.

Phase 7 must not mutate app repositories.

If a UNIT/COMPONENT testcase lacks exact Dev-local evidence:
- do not write the missing test;
- mark/block the coverage disposition;
- route the issue to Dev;
- require revised exact Dev evidence before EXECUTION_READY.

Add direct negative tests proving app-repo mutation is rejected.

---

## 8. Repository routing

Test-owned automation repository must be resolved from declared project data.

Read:
- .sdlc/project-policy.yml
- .sdlc/project-topology.yml

Resolve:
policy.testing.automation_repository_role
→ exactly one topology repository whose role matches.

Do not guess from folder names.

Canonical artifacts must persist repository ID/role and relative paths, not machine-specific absolute paths.

Runtime may receive repository_id -> local root mappings.

If automation repository is absent:
- suitability/planning may continue;
- implementation is blocked;
- EXECUTION_READY is forbidden.

Ambiguous role resolution fails closed.

---

## 9. Automation Suitability canonical artifact

Add a canonical Automation Suitability artifact.

Minimum shape:

schema_version
artifact_class = CANONICAL
feature_id
revision
approved_testware_ref
rows

Every approved Testcase appears exactly once.

Each row:

testcase_id
classification
owner
required
rationale
dependency_refs

Rules:
- no duplicate testcase IDs;
- no orphan testcase IDs;
- exact approved Testcase inventory equality;
- do not copy expected-result prose as a new oracle;
- no BAREF as canonical business trace;
- project policy may guide HOW but cannot redefine WHAT.

MANUAL_ONLY is valid and does not automatically block readiness.

Required BLOCKED rows block readiness.

---

## 10. Automation Plan canonical artifact

Create canonical Automation Plan derived from current exact Suitability.

The plan is technical/test HOW.

No Human semantic approval receipt is added.

Once implementation begins, material plan fields become immutable by revision.

Material fields include:
- suitability classification;
- owner;
- AUT ID;
- testcase refs;
- automation class;
- repository ID;
- suite;
- planned paths;
- runner;
- execution command;
- verification commands;
- dependencies.

Material change after implementation begins:
→ NEEDS_REPLAN
→ new plan revision
→ stale implementation/review/verification evidence cleared.

Never mutate a started plan in place.

---

## 11. AUT identity and trace

Automated plan items use stable AUT-* IDs.

AUT identity:
- unique per feature;
- stable within a plan lineage;
- deterministic enough to preserve trace across resume/replan;
- no AUT ID for MANUAL_ONLY;
- BLOCKED has no executable implementation.

A testcase may map to multiple AUT items only with explicit technical rationale.

Trace must bind IDs/refs only:

BR/FR
→ TD
→ TC
→ AUT
→ repository/path
→ automation revision

Do not copy semantic prose into AUT artifacts.

---

## 12. AUT plan item contract

Minimum executable AUT item:

aut_id
testcase_refs
automation_class
owner
repository_id
suite
planned_paths
runner
execution_command
verification_commands
dependencies
trace

Commands MUST be argv arrays.

Good:
["python", "-m", "pytest", "tests/api/test_resource.py", "--collect-only"]

Bad:
"python -m pytest tests/api/test_resource.py"

No shell=true execution.

---

## 13. Phase 7 lifecycle

Use a small lifecycle:

AUTOMATION_INTAKE
→ SUITABILITY_ANALYZED
→ AUTOMATION_PLANNED
→ AUTOMATION_IMPLEMENTING
→ AUTOMATION_REVIEW
→ AUTOMATION_VERIFYING
→ EXECUTION_READY

Exception states:

BLOCKED
NEEDS_REPLAN

No Human approval lifecycle state is added.

Persistence must be atomic and resume-safe.

Fresh-process resume must revalidate exact authority/revisions and reject drift.

---

## 14. Source mutation guard

Before Test-owned automation source mutation verify:

- lifecycle == AUTOMATION_IMPLEMENTING;
- exact current Automation Plan;
- exact automation repository identity;
- exact base revision;
- path is within plan write scope;
- target repository is the declared automation repository;
- target is not an application repository;
- no symlink/reparse escape.

After implementation:
- inspect changed paths;
- reject any out-of-plan path;
- bind exact automation repository revision.

Do not pretend the framework can intercept every arbitrary editor write.
Use pre-write authorization plus post-diff verification.

---

## 15. Implementation rule

Automation source implements approved Testcase behavior.

It does not become the oracle.

If implementation requires missing WHAT or expected behavior:
→ SPEC_GAP or BUSINESS_DECISION_REQUIRED
→ block/replan
→ do not invent.

If test harness/tooling itself is broken:
→ TEST_ISSUE.

If environment/access/data fixture is unavailable:
→ ENVIRONMENT_ISSUE.

Do not weaken Testcases to make automation easier.

---

## 16. Typed dependencies

Reuse these concepts:

SEMANTIC_ORACLE
ENVIRONMENT_ACCESS
TEST_DATA_FIXTURE
IMPLEMENTATION_LOCATOR
TOOLING
OBSERVABILITY

Statuses:

OPEN
RESOLVED
NOT_REQUIRED

Rules:
- required OPEN dependency blocks EXECUTION_READY;
- RESOLVED requires exact resolution ref;
- semantic oracle gaps route upstream;
- do not relabel a semantic gap as tooling/environment to bypass authority.

---

## 17. Review budget

One consolidated review is enough.

Budget:

full_reviews <= 1
blocking_fix_waves <= 1
scoped_rereviews <= 1

Review:
- trace correctness;
- repo ownership;
- no business-oracle duplication;
- deterministic setup/cleanup;
- secrets;
- fixture safety;
- flaky timing hazards;
- selector/API stability;
- dependency handling;
- project conventions;
- out-of-scope writes.

A review finding requiring new WHAT routes upstream.
Do not rewrite expected behavior.

---

## 18. Automation verification vs product execution

Phase 7 verifies automation implementation only.

Allowed verification categories:

SYNTAX
STATIC
LINT
TYPECHECK
TEST_DISCOVERY
TEST_LIST
CONFIG_VALIDATE
HARNESS_SELF_TEST
FIXTURE_VALIDATE

Allowed harness self-tests must not assert the real target application's approved business outcome.

Forbidden Phase 7 claims:

API PASS
E2E PASS
SYSTEM PASS
feature PASS
WCAG conformance
VERIFIED

Do not execute a real SUT to earn EXECUTION_READY.

---

## 19. Dev shift-left and final binding

Automation planning/implementation may begin before Dev completion.

Before final EXECUTION_READY:

- require exact Dev Handoff V2;
- state == READY_FOR_TEST;
- canonical Dev VNext validation passes;
- exact application repository revisions captured;
- all DEV_LOCAL_REFERENCE items resolve to exact evidence from the current Dev handoff;
- automation assumptions remain compatible with current implementation context.

If current Dev handoff invalidates a material automation assumption:
→ NEEDS_REPLAN.

Do not silently retain stale automation.

---

## 20. EXECUTION_READY handoff

Create a durable HANDOFF_MANIFEST.

State exactly:

EXECUTION_READY

Minimum contents:

schema_version
artifact_class = HANDOFF_MANIFEST
feature_id
approved_testware
automation_suitability
automation_plan
dev_handoff
application_revisions
automation_repository
automation_revision
automation_items
manual_testcases
resolved_dependencies
review
automation_verification
state = EXECUTION_READY

Each automated row binds:

aut_id
testcase_refs
automation_class
owner
repository_id
paths
revision
verification_evidence_refs

Do not copy Testcase expected-result prose.

The exact Testcase remains the Phase 8 oracle.

---

## 21. EXECUTION_READY completion rules

Require all:

- exact current APPROVED_TESTWARE;
- all approved Testcases accounted for;
- no required BLOCKED row;
- every TEST_AUTOMATION AUT item implemented at exact automation revision;
- every DEV_LOCAL_REFERENCE bound to exact current Dev evidence;
- every MANUAL_ONLY testcase references exact approved Testcase;
- exact current Dev Handoff READY_FOR_TEST;
- exact application revisions;
- exact automation repo revision;
- all required dependencies resolved;
- review complete;
- automation verification PASS;
- no out-of-scope writes;
- no product execution claim.

EXECUTION_READY means only:
all authoritative inputs, implementation artifacts and execution prerequisites are ready for Phase 8.

It does NOT mean tests passed.

---

## 22. Tool agnosticism

Do not make Playwright a required package/runtime dependency.

Playwright, Web Accessibility and project-native frameworks are optional implementation aids.

Framework must work for:
- backend/API projects;
- DB-focused projects;
- non-browser projects;
- browser projects;
- JVM/Python/JS stacks.

Do not add a third-party dependency unless core runtime truly needs it.

---

## 23. Fresh synthetic acceptance

Acceptance must not require:
- internet;
- real browser;
- external database;
- real API/SUT;
- Digital Wedding.

Use a neutral synthetic project with:
- project topology;
- project policy;
- app repository;
- automation repository;
- exact Approved Testware VNext fixture;
- exact Dev READY_FOR_TEST fixture;
- deterministic automation files/commands.

Prove:

A. API TEST_AUTOMATION:
APPROVED_TESTWARE
→ API suitability
→ AUT
→ automation repo
→ implementation
→ discovery/static verification
→ EXECUTION_READY.

B. E2E planning:
E2E can be planned without mandatory Playwright package identity.

C. UNIT/COMPONENT:
exact Dev evidence only; app repo remains unchanged.

D. MANUAL_ONLY:
no AUT source required; testcase remains execution protocol.

E. BLOCKED:
required BLOCKED prevents readiness.
Resolution + valid replan can proceed.

F. Repository routing:
wrong repo/role/path rejected.

G. Shift-left:
plan can exist before READY_FOR_TEST.
Final readiness cannot.

H. Drift:
plan/repo/upstream drift invalidates stale evidence.

I. No semantic drift:
missing WHAT routes upstream.

J. No execution claim:
verification PASS != product/test PASS.

---

## 24. Package completion in the same overnight task

After semantics/runtime are green, continue packaging in the SAME branch/session.

Do not stop just because Block A is finished.

Advance Test Kit prerelease from:
2.0.0-rc.6

Expected:
2.0.0-rc.7

unless repository-owned release policy requires a later prerelease.

Do not release stable 2.0.0.

Complete:

- kit.yaml VNext automation capability metadata;
- package authority;
- VNext schemas;
- lean operator templates;
- Doctor;
- acceptance.yaml extension;
- Test Kit README;
- Vietnamese operational docs;
- English overview/release status where maintained;
- neutral public Automation V1 example;
- installer/uninstall closure;
- fresh installed-runtime acceptance;
- installed isolation;
- genericity scan;
- package integrity regeneration;
- full regression.

Do not create fake Human receipts as reusable production templates.

---

## 25. Doctor semantics

Doctor remains package/capability readiness only.

READY:
required Test Manual + Automation V1 package closure is valid.

DEGRADED:
optional tool/projection capability missing.

FAIL:
required package/integrity/runtime capability broken.

Doctor READY must not imply:
APPROVED_TESTWARE
READY_FOR_TEST
EXECUTION_READY
PASS
VERIFIED
READY_TO_MERGE.

Add direct regression if needed.

---

## 26. Acceptance contract

Extend kits/test/acceptance.yaml.

Phase 7 completion requires a fresh installed Automation V1 Tier.

Fresh installed flow must prove at minimum:

clean project
→ install Test Kit
→ Doctor
→ isolated installed runtime
→ exact synthetic Approved Testware VNext
→ suitability
→ plan
→ synthetic automation implementation
→ review
→ automation verification
→ exact Dev READY_FOR_TEST
→ EXECUTION_READY handoff validation
→ Doctor again

Use:
- python -I where practical;
- no PYTHONPATH;
- external working directory;
- imports must resolve from installed package.

Core acceptance must not depend on optional Playwright/openpyxl/XMind availability.

---

## 27. Genericity

Production/default package/docs/examples must not hard-code:

Digital Wedding
CR-DWC-*
PetClinic
Appointment
local usernames
absolute machine paths
feature branch URLs

Historical benchmark fixtures may retain historical names under clearly historical paths.

Do not broaden cleanup to unrelated historical evidence.

---

## 28. Legacy compatibility

V1 artifacts remain:

LEGACY_COMPAT
vnext_authority = false

Legacy execution contract remains legacy.

Do not fabricate Automation V1 authority from legacy artifacts.

---

## 29. Forbidden work

Do NOT implement:

- real product/API/E2E execution;
- execution PASS/FINDING state machine;
- execution observations;
- finding classification workflow;
- DEFECT creation/handoff;
- Dev fix;
- READY_FOR_RETEST;
- retest;
- VERIFIED/REOPENED;
- READY_TO_MERGE;
- Digital Wedding migration;
- Delivery Manifest redesign;
- stable public release;
- separate Automation Kit;
- third Human semantic gate.

---

## 30. Architecture STOP conditions

STOP with:

ARCHITECTURE_DECISION_REQUIRED

only if implementation truly requires:

- changing BA/UX/Testcase authority semantics;
- changing Dev READY_FOR_TEST semantics;
- adding a Human Automation Plan Gate;
- making Delivery Manifest required;
- using legacy execution_contract as new authority;
- writing application repos;
- forcing one automation framework globally;
- running real SUT acceptance in Phase 7;
- adding Phase 8 defect/retest/VERIFIED semantics;
- creating a separate Automation Kit.

Do not use this stop condition for ordinary implementation difficulty.

---

## 31. Overnight execution order

1. fetch origin;
2. verify bootstrap ancestry;
3. create target branch feat/test-automation-v1-phase7;
4. record behavioral base 44617175f1c441811f7bf4f64672964d7446ac39;
5. inspect current Test VNext/Dev VNext/topology/policy/package contracts;
6. record focused baseline;
7. implement semantic/runtime contracts;
8. add focused tests;
9. complete synthetic Phase 7 E2E;
10. self-review architecture;
11. fix all review findings in same branch;
12. continue packaging/docs/Doctor/fresh-install;
13. regenerate package authority/hashes with repository-owned algorithms;
14. run installed isolation;
15. run focused BA/Dev/Test/Foundation/Shared regression;
16. run full tooling unittest discovery;
17. run git diff --check;
18. scan genericity and branch-specific links;
19. delete this temporary spec;
20. commit final state;
21. push target branch;
22. do not merge;
23. worktree clean.

No sub-feature branches.

---

## 32. Mandatory self-review before PASS

Before final PASS explicitly audit:

- new authority sources;
- new Human Gates;
- Delivery Manifest coupling;
- app repo writes;
- project/domain hard-coding;
- mandatory Playwright/tool coupling;
- real-SUT execution;
- Phase 8 states/claims;
- stale refs;
- plan/revision drift;
- shell-string commands;
- absolute paths in canonical artifacts;
- feature-branch URLs in docs;
- package hash drift after docs edits.

Fix issues before PASS.

---

## 33. Full regression

At minimum run:

- current Test VNext suites;
- new Automation V1 semantic/runtime suites;
- new Automation V1 schema tests;
- new fresh-installed Automation V1 acceptance;
- Test package/Doctor/policy suites;
- BA VNext suites;
- Dev VNext suites;
- BA installed acceptance;
- Dev installed acceptance where shared/package changes can affect them;
- Project Foundation tests;
- Shared SDLC contract/acceptance tests;
- full tooling unittest discovery;
- git diff --check.

No assertion weakening.
No skip added just to get green.

---

## 34. Temp spec cleanup

Before final commit remove:

PHASE_7_AUTOMATION_V1_OVERNIGHT_EXECUTION_SPEC.md

Do not copy or rename it elsewhere.

Final implementation tree must not contain:
- temporary Phase 7 bootstrap spec;
- scratch reports;
- node_modules;
- caches;
- machine-local generated state.

---

## 35. Required final report

Return exactly:

PHASE_7_OVERNIGHT_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/test-automation-v1-phase7

BASE:
44617175f1c441811f7bf4f64672964d7446ac39

HEAD:
<exact SHA>

APPROVED_TESTWARE_AUTHORITY:
<status>

AUTOMATION_SUITABILITY:
<status>

AUTOMATION_PLAN:
<status>

AUT_IDENTITY_TRACE:
<status>

REPOSITORY_ROUTING:
<status>

APP_REPO_READ_ONLY_BOUNDARY:
<status>

DEV_LOCAL_REFERENCE:
<status>

TEST_AUTOMATION_IMPLEMENTATION:
<status>

MANUAL_ONLY:
<status>

BLOCKED_BEHAVIOR:
<status>

PLAN_IMMUTABILITY_REPLAN:
<status>

SOURCE_MUTATION_GUARD:
<status>

AUTOMATION_REVIEW:
<status>

AUTOMATION_VERIFICATION:
<status>

DEV_READY_FOR_TEST_BINDING:
<status>

EXECUTION_READY_HANDOFF:
<status>

NO_EXECUTION_CLAIMS:
<status>

NO_THIRD_HUMAN_GATE:
<status>

DELIVERY_MANIFEST:
DEFERRED_NON_AUTHORITATIVE

TOOL_AGNOSTIC:
<status>

KIT_VERSION:
<version>

PACKAGE_AUTHORITY:
<status and hashes>

INSTALLER_UNINSTALL:
<status>

DOCTOR:
<status>

SCHEMAS_TEMPLATES:
<status>

DOCS:
<status>

PUBLIC_EXAMPLE:
<status>

FRESH_INSTALL_ACCEPTANCE:
<status>

INSTALLED_ISOLATION:
<status>

GENERICITY:
<status>

LEGACY_COMPAT:
<status>

TESTS:
<summary>

SELF_REVIEW:
<status + important findings fixed>

SEMANTIC_DRIFT:
NONE
or exact list

BLOCKERS:
NONE
or exact list

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
feat/test-automation-v1-phase7

WORKTREE:
CLEAN

RECOMMENDED_PHASE_7_STATUS:
VERIFIED_COMPLETE_CANDIDATE | NOT_READY

PASS is not permission to merge.
Final merge requires independent remote review.
