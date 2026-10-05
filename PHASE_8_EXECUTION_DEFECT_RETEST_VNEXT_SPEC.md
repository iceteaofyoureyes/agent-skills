# PHASE 8 — EXECUTION / FINDING / DEFECT / RETEST VNEXT

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills
Authoritative base: main @ 3075b6c51ef7a3ee58e9b11eedf57bb7ba7a8645
Phase 7 dependency: Test Automation V1 2.0.0-rc.7 VERIFIED COMPLETE + merged
Recommended model: GPT-6 Luna Extra High when available.

Phase 8 begins from exact EXECUTION_READY.

It owns:
- product execution evidence;
- Finding classification;
- Defect Handoff;
- Dev-fix acceptance;
- READY_FOR_RETEST;
- Tester retest;
- final VERIFIED / REOPENED.

Phase 8 does not create READY_TO_MERGE and does not merge product code.

---

# 1. Target lifecycle

```text
EXECUTION_READY
      ↓
Execution Manifest
      ↓
EXECUTING
      ↓
┌──────────── PASS ────────────┐
│                              │
│                              ▼
│                    Tester Final Verification
│                              ↓
│                          VERIFIED
│
└────────── FINDING
             ↓
     Finding Classification
             ↓
   ┌─────────┼───────────────┬──────────────────────┐
   │         │               │                      │
 DEFECT   SPEC_GAP /      TEST_ISSUE          ENVIRONMENT_ISSUE
   │      BUSINESS...         │                      │
   │         │               │                      │
   │     ROUTE_UPSTREAM   ROUTE_TEST           ROUTE_ENVIRONMENT
   │
   ↓
DEFECT_READY_FOR_DEV
   ↓
Dev VNext FEATURE_DELIVERY fix
   ↓
Fresh Dev Verify / READY_FOR_TEST
   ↓
Phase 8 validates exact fix
   ↓
READY_FOR_RETEST
   ↓
Tester Retest
   ↓
PASS → VERIFIED
FAIL → REOPENED
```

A reopened defect may be fixed again through another exact Dev VNext fix run.

---

# 2. Reference-plan alignment

Phase 8 implements:

```text
execution manifest
environment/revision binding
evidence
findings
defect handoff
fix
retest
VERIFIED / REOPENED
```

Finding taxonomy remains exactly:

```text
DEFECT
SPEC_GAP
BUSINESS_DECISION_REQUIRED
TEST_ISSUE
ENVIRONMENT_ISSUE
```

Defect lifecycle remains:

```text
DEFECT
→ DEFECT_READY_FOR_DEV
→ Dev Reproduce / Fix
→ Fresh Dev Verify
→ READY_FOR_RETEST
→ Tester Retest
→ VERIFIED | REOPENED
```

Dev may not self-VERIFY final closure.

---

# 3. Guiding principles

```text
STRICT AT AUTHORITY BOUNDARIES
LEAN IN ORCHESTRATION
```

Do not create a fourth kit.

Test Kit remains responsible for execution, findings and retest orchestration.

Dev Kit remains responsible for Dev source mutation, engineering review and fresh Dev verification.

Do not duplicate Dev source mutation/review/verification logic in Phase 8.

Do not make runtime evidence canonical business authority.

---

# 4. Frozen authority boundaries

Preserve:

- BA approved WHAT remains authoritative.
- Approved UX remains authoritative when applicable.
- Approved Testcases remain the expected-behavior oracle.
- EXECUTION_READY binds exact app + automation revisions.
- Dev implementation cannot redefine expected behavior.
- automation code cannot redefine expected behavior.
- observed current-system behavior is evidence only.
- Test execution failure does not automatically mean DEFECT.
- Dev fix PASS does not mean final defect VERIFIED.
- final VERIFIED is Tester-owned.
- Delivery Manifest remains DEFERRED_NON_AUTHORITATIVE.

No new Human semantic approval gate is added in Phase 8.

---

# 5. Legacy execution layer

Current:

```text
shared/sdlc/findings/execution_contract.py
tooling/lib/execution_contract.py
tooling/schemas/execution-state.schema.json
tooling/schemas/defect-handoff.schema.json
```

is legacy/project-layer behavior.

It depends on:
- old Test promotion;
- Delivery Manifest;
- one implementation commit;
- legacy execution authority semantics.

Do not use it as the VNext production path.

Preserve it only as LEGACY_COMPAT where compatibility requires it.

Phase 8 creates a new VNext execution path.

---

# 6. Phase 8 input authority

Required production input:

```text
EXECUTION_READY HANDOFF_MANIFEST
```

from Test Automation V1.

Revalidate using the canonical Phase 7 implementation.

The execution runtime must prove:

- exact Approved Testware;
- exact Automation Suitability;
- exact Automation Plan;
- exact Dev Handoff V2 READY_FOR_TEST;
- exact application repository revisions;
- exact automation repository identity;
- exact committed automation Git SHA;
- exact AUT paths;
- exact review evidence;
- exact automation verification evidence;
- all required dependencies resolved;
- no stale repository state;
- no stale upstream authority.

Do not reconstruct this authority manually.

Do not accept EXECUTION_READY by state text alone.

---

# 7. Execution Environment Binding

Create a small V1 environment descriptor.

Artifact class:

```text
CANONICAL
```

Minimum shape:

```text
schema_version
artifact_class = CANONICAL
environment_id
profile
configuration_refs[]
evidence_refs[]
```

Rules:

- environment_id and profile are project-owned identifiers;
- configuration_refs are exact refs to sanitized project/runtime configuration;
- evidence_refs may identify environment provisioning/health evidence;
- no credentials, tokens, passwords, private keys or secret values;
- no machine-specific absolute paths in canonical artifact;
- environment descriptor does not define business expected behavior.

The environment descriptor is bound into the Execution Manifest.

No fixed environment names such as dev/stage/prod are required by the framework.

---

# 8. Execution Manifest V1

Create a canonical Execution Manifest before product execution.

Artifact class:

```text
CANONICAL
```

Minimum shape:

```text
schema_version
artifact_class
execution_id
feature_id
execution_ready_ref
environment_ref
approved_testware_ref
automation_plan_ref
application_revisions
automation_repository
automation_revision
automated_items
manual_testcases
dev_local_references
optional_blocked_testcases
created_at
```

Rules:

- bind exact current EXECUTION_READY;
- application revisions exactly equal Phase 7 handoff;
- automation revision exactly equals Phase 7 committed Git SHA;
- no testcase expected-result prose is copied;
- exact Approved Testcase remains oracle;
- changing environment or any repository revision creates a new execution attempt;
- execution manifest is immutable after execution starts.

---

# 9. Execution ownership

## TEST_AUTOMATION

Execute the exact execution_command from the current Automation Plan.

Rules:

- argv array only;
- shell=False;
- cwd = exact automation repository;
- automation HEAD == exact handoff SHA;
- automation repo clean;
- every app repo HEAD == exact application revision;
- app repos clean;
- no command mutation of framework authority artifacts;
- raw stdout/stderr retained only as EVIDENCE;
- store SHA-256 and bounded/raw evidence files, not business authority.

Product execution is explicitly allowed in Phase 8.

## MANUAL_ONLY

No AUT command.

A Tester records an Observation against the exact approved Testcase.

## DEV_LOCAL_REFERENCE

Do not rerun source-local Dev checks automatically.

They are already exact Dev verification evidence bound by EXECUTION_READY.

They remain part of total testcase accounting.

## Optional BLOCKED

Optional blocked testcases remain visible in the Execution Manifest.

They are not treated as PASS.

They do not block final verification only when the current Approved Testware/Suitability marks them non-required.

Required BLOCKED must have been rejected before EXECUTION_READY.

---

# 10. Execution Command Evidence

Each automated command invocation creates immutable EVIDENCE.

Minimum:

```text
execution_id
aut_id
testcase_refs
automation_revision
application_revisions
environment_ref
argv
started_at
completed_at
exit_code
stdout_sha256
stderr_sha256
status = COMMAND_PASS | COMMAND_FAIL
```

Raw stdout/stderr may be stored as separate evidence files.

Do not infer DEFECT from nonzero exit code.

A nonzero exit requires a Finding observation.

A zero exit may still produce a Finding if observation evidence shows behavior violates the approved Testcase.

---

# 11. Unified Observation V1

Automated and manual execution use the same observation contract.

Artifact class:

```text
EVIDENCE
```

Minimum:

```text
observation_id
execution_id
testcase_id
aut_id optional
oracle_ref
oracle_locator
actual_summary
evidence_refs[]
actor
outcome = PASS | FINDING
recorded_at
```

oracle_ref binds the exact approved testcase collection.

oracle_locator identifies the exact testcase / step(s) being asserted.

Do not duplicate expected-result prose into Observation.

actual_summary is observed evidence, not authority.

For automated AUT:
- PASS requires its command evidence to be COMMAND_PASS;
- FINDING may follow COMMAND_PASS or COMMAND_FAIL if evidence supports it.

For MANUAL_ONLY:
- trusted Tester records the observation directly.

Observation actor must be authenticated by a host callback.

Allowed role:

```text
TESTER
```

Automation may collect raw evidence, but final PASS/FINDING observation is Tester-owned or trusted Tester-service-owned according to host policy.

---

# 12. Execution attempt state

Use a small runtime lifecycle:

```text
EXECUTION_INTAKE
→ EXECUTION_MANIFEST_READY
→ EXECUTING
→ EXECUTION_COMPLETE
→ VERIFIED
```

Finding path:

```text
EXECUTING
→ FINDING
→ FINDING_CLASSIFIED
→ ROUTED
```

Defect path extends:

```text
FINDING_CLASSIFIED
→ DEFECT_READY_FOR_DEV
→ READY_FOR_RETEST
→ RETESTING
→ VERIFIED | REOPENED
```

Do not create READY_TO_MERGE in Phase 8.

Runtime state is RUNTIME, not canonical authority.

---

# 13. Complete execution rules

Every required Phase 7 disposition must be accounted for:

- TEST_AUTOMATION → exact Observation;
- MANUAL_ONLY → exact Tester Observation;
- DEV_LOCAL_REFERENCE → exact Dev evidence binding;
- optional BLOCKED → explicitly carried as non-required;
- no duplicate testcase disposition.

If all required executed/manual observations are PASS and no open Finding exists:

```text
Tester Final Verification
→ VERIFIED
```

No retest is required when the initial full execution passes.

Final verification must bind the exact execution attempt and exact revisions.

---

# 14. VERIFIED V1 handoff

Create a durable Phase 8 final handoff.

Artifact class:

```text
HANDOFF_MANIFEST
```

State:

```text
VERIFIED
```

Minimum:

```text
schema_version
artifact_class
feature_id
execution_manifest
execution_ready
approved_testware
application_revisions
automation_revision
environment_ref
observations[]
dev_local_references
optional_blocked_testcases
defect_history[]
verification_actor
verified_at
state = VERIFIED
```

Rules:

- actor role must authenticate as TESTER;
- all required testcase dispositions accounted;
- all required observations PASS;
- no open Finding;
- if defect history exists, final verified revisions come from READY_FOR_RETEST/retest;
- no runtime-only path is authority;
- Dev actor cannot produce this handoff.

VERIFIED does not mean READY_TO_MERGE.

---

# 15. Finding V1

Any FINDING Observation creates an immutable Finding artifact.

Artifact class:

```text
CANONICAL
```

Minimum:

```text
finding_id
feature_id
execution_id
testcase_id
aut_id optional
observation_ref
oracle_ref
execution_manifest_ref
execution_ready_ref
application_revisions
automation_revision
environment_ref
status = OPEN
```

Do not classify automatically from exit code.

Finding is a durable fact that an approved expectation and observed evidence need disposition.

---

# 16. Finding Classification V1

Classification must use exactly:

```text
DEFECT
SPEC_GAP
BUSINESS_DECISION_REQUIRED
TEST_ISSUE
ENVIRONMENT_ISSUE
```

Classification artifact is CANONICAL technical/test disposition.

Minimum:

```text
finding_ref
classification
actor
rationale
evidence_refs[]
route
target_repository_ids[]
classified_at
```

Actor must authenticate as TESTER.

Routes:

```text
DEFECT → DEV
SPEC_GAP → UPSTREAM
BUSINESS_DECISION_REQUIRED → UPSTREAM
TEST_ISSUE → TEST
ENVIRONMENT_ISSUE → ENVIRONMENT
```

Do not create DEFECT automatically.

---

# 17. DEFECT proof requirements

Classification as DEFECT requires all:

- exact approved oracle exists;
- Finding Observation exists;
- behavior is reproducible or exact deterministic evidence proves the mismatch;
- current execution environment has been assessed and not identified as the root cause;
- test/automation issue has been excluded to the extent required by available evidence;
- at least one application repository target is named;
- all target repositories belong to the exact Phase 7 application repository set;
- Tester actor authenticates the classification.

Use compact fields/evidence, not a new Human semantic gate.

If evidence instead shows missing/ambiguous WHAT:

```text
SPEC_GAP
or
BUSINESS_DECISION_REQUIRED
```

not DEFECT.

---

# 18. Non-defect routes

## SPEC_GAP / BUSINESS_DECISION_REQUIRED

Current execution attempt cannot become VERIFIED.

Route upstream.

A revised approved BA/UX/Testware chain creates a new downstream flow.

Do not patch expected results in Phase 8.

## TEST_ISSUE

Current execution attempt cannot become VERIFIED.

Route back to Test Automation/Test Kit.

A corrected Test/Automation artifact must create a new exact EXECUTION_READY before another execution attempt.

## ENVIRONMENT_ISSUE

Current execution attempt cannot become VERIFIED.

Correct environment/evidence and start a new execution attempt with a new exact environment binding.

Do not call environment failures product defects.

---

# 19. Defect Handoff V1

For DEFECT, create:

```text
HANDOFF_MANIFEST
state = DEFECT_READY_FOR_DEV
```

Minimum:

```text
schema_version
artifact_class
defect_id
feature_id
finding_ref
classification_ref
execution_manifest_ref
execution_ready_ref
approved_testware_ref
testcase_ref
oracle_ref
observation_ref
environment_ref
original_dev_handoff_ref
original_application_revisions
automation_revision
target_repository_ids
verification_owner = TESTER
state = DEFECT_READY_FOR_DEV
```

Do not include Delivery Manifest.

Do not copy business expected-result prose.

defect_id remains stable across reopen/fix cycles.

---

# 20. Dev fix integration — no new Dev authority mode

Do NOT add DEFECT_REPAIR to core Dev authority modes unless implementation proves impossible without it.

Preferred integration:

1. Defect Handoff identifies exact defect evidence and target repositories.
2. Dev starts a normal Dev VNext FEATURE_DELIVERY run.
3. Upstream remains original exact Engineering Handoff VNext / BA WHAT authority.
4. Use:
   ```text
   change_id = defect_id
   ```
5. Repository base revisions start from exact failed application revisions.
6. Defect Handoff is bound as read-only workflow/evidence context, not replacement business authority.
7. Dev performs Impact/Plan/Implementation/Review/Fresh Verification normally.
8. Dev produces normal V2 READY_FOR_TEST handoff.
9. Phase 8 validates this Dev fix handoff and creates READY_FOR_RETEST.

Reuse Dev Kit instead of duplicating its engine.

---

# 21. Defect fix acceptance contract

Accept Dev fix only if:

- exact original Defect Handoff still current;
- new Dev Handoff V2 validates canonically;
- state = READY_FOR_TEST;
- change_id == defect_id;
- same original BA Engineering Handoff authority;
- Dev run repository bases match exact failed application revisions for targeted implementation repos;
- target repo changes are within Dev-authorized scope;
- at least one targeted application revision changes;
- non-target app repos cannot silently drift;
- requirements coverage remains valid;
- fresh engineering review and verification PASS through Dev VNext validation;
- automation revision remains exact execution automation SHA;
- no Testcase expected-result change is inferred from the fix.

If Dev discovers WHAT is wrong, route upstream.

---

# 22. READY_FOR_RETEST V1

After valid Dev fix, create:

```text
HANDOFF_MANIFEST
state = READY_FOR_RETEST
```

Minimum:

```text
schema_version
artifact_class
defect_id
feature_id
defect_handoff_ref
finding_ref
original_execution_manifest_ref
approved_testware_ref
testcase_ref
automation_revision
previous_application_revisions
fixed_application_revisions
dev_fix_handoff_ref
dev_fix_verification_ref
environment_ref
verification_owner = TESTER
state = READY_FOR_RETEST
```

This is readiness, not final verification.

Dev cannot set VERIFIED.

---

# 23. Retest

Tester retest uses exact READY_FOR_RETEST.

Rules:

- app repos at exact fixed revisions;
- automation repo remains exact recorded automation revision;
- environment binding current;
- original failed Testcase must be executed/observed;
- optional regression selection may run additionally;
- original approved Testcase oracle remains authoritative;
- retest Observation uses same Observation V1 contract;
- actor authenticates as TESTER.

Outcome:

```text
PASS → VERIFIED
FINDING → REOPENED
```

---

# 24. REOPENED

A failed retest creates durable state REOPENED.

Bind:

- same stable defect ID;
- prior Defect Handoff;
- READY_FOR_RETEST;
- new retest observation;
- fixed application revisions;
- automation revision;
- environment;
- reopen count / lineage.

The same defect may return to Dev for another fix cycle.

Do not silently create a brand-new unrelated defect ID for the same failed retest.

A clearly different failure may create a separate Finding after Tester classification.

---

# 25. Role separation

Enforce:

```text
TESTER
→ observations
→ finding classification
→ final VERIFIED
→ retest VERIFIED/REOPENED

DEV
→ source fix
→ engineering review/verification
→ READY_FOR_TEST
```

Dev cannot authenticate final Test VERIFIED.

Automation agent may execute commands and collect raw evidence but cannot self-classify a failure as DEFECT without Tester classification authority.

---

# 26. Execution drift guards

Before and after each execution command/retest:

- app repository HEADs equal expected application revisions;
- app working trees clean;
- automation HEAD equals exact automation revision;
- automation working tree clean;
- environment binding refs unchanged;
- Approved Testware and Execution Ready still exact;
- no authority artifact bytes changed.

If drift occurs:

```text
EXECUTION_STALE
```

and stop.

Do not continue with mixed revisions.

---

# 27. Command/result safety

Execution command comes only from exact Automation Plan.

Use:

```text
subprocess.run(argv, shell=False)
```

Do not accept arbitrary new command strings during execution.

Do not persist secrets from stdout/stderr.

Use existing secret rejection/redaction conventions where practical.

Bound raw evidence size or write raw output to evidence files rather than embedding unbounded logs in canonical artifacts.

---

# 28. Multi-repository exact identity

Execution evidence must capture:

```text
all application repository SHAs
automation repository SHA
```

Do not collapse multi-repo state into one commit.

Defect Handoff and VERIFIED handoff retain the exact revision map.

Fresh clone reproduction must be possible from Git revisions without local working-tree state.

---

# 29. Package architecture

Phase 8 extends Test Kit.

Do not create a separate Execution Kit.

Suggested new skill:

```text
test-execution-vnext
```

or repository-consistent equivalent.

Test Kit default docs should show:

```text
Manual VNext
→ Automation V1
→ Execution / Finding / Defect / Retest VNext
```

Legacy execution contract must be clearly labeled compatibility/history.

---

# 30. Package version

Current Test Kit:

```text
2.0.0-rc.7
```

Phase 8 should advance on same prerelease line.

Expected:

```text
2.0.0-rc.8
```

unless repository-owned version policy requires another RC.

Do not publish stable 2.0.0.

---

# 31. Doctor

Doctor remains package/capability diagnostics.

Add Phase 8 runtime/schema/package checks.

Doctor READY must not imply:

- EXECUTION_READY;
- execution PASS;
- no Findings;
- READY_FOR_RETEST;
- VERIFIED;
- READY_TO_MERGE.

Optional execution tooling may be DEGRADED only if not required by installed project configuration.

Core package/integrity failures remain FAIL.

---

# 32. Acceptance contract

Extend kits/test/acceptance.yaml.

Phase 8 completion requires fresh installed execution acceptance.

Suggested:

```text
Tier 5 — Execution / Defect / Retest installed acceptance
```

It is mandatory for Phase 8 completion.

---

# 33. Synthetic full Phase 8 acceptance

Use a neutral local synthetic multi-repo project.

No external network.

Repositories:

```text
project
├── app
└── automation
```

Use actual local Git commits.

Acceptance demonstrates both paths.

## A. Straight PASS path

```text
EXECUTION_READY
→ Execution Manifest
→ automated/manual observations PASS
→ Tester final verification
→ VERIFIED
```

Assert:
- exact app SHA;
- exact automation SHA;
- exact environment ref;
- Dev-local evidence accounted;
- no Defect;
- Dev cannot self-VERIFY.

## B. Defect / fix / retest path

1. exact EXECUTION_READY;
2. execute synthetic test against deliberately failing local app behavior;
3. Finding;
4. Tester classifies DEFECT;
5. exact Defect Handoff;
6. run a real Dev VNext FEATURE_DELIVERY fix flow or closest installed production Dev runtime path;
7. commit app fix;
8. Dev review + fresh verification;
9. produce Dev V2 READY_FOR_TEST;
10. Phase 8 accepts fix;
11. create READY_FOR_RETEST;
12. Tester retest original testcase;
13. PASS;
14. final VERIFIED.

No framework hot patch.

---

# 34. Required negative acceptance

Cover:

## Authority
- state text only cannot authorize execution;
- stale EXECUTION_READY rejected;
- legacy execution input cannot authorize VNext.

## Revision drift
- app commit changes before execution → reject;
- automation commit changes before execution → reject;
- dirty app repo → reject;
- dirty automation repo → reject.

## Finding classification
- command FAIL does not auto-create DEFECT;
- SPEC_GAP does not create Defect Handoff;
- BUSINESS_DECISION_REQUIRED does not create Defect Handoff;
- TEST_ISSUE does not create Defect Handoff;
- ENVIRONMENT_ISSUE does not create Defect Handoff.

## Defect
- unauthenticated/non-Tester classification rejected;
- defect target outside app topology rejected;
- missing oracle/observation rejected.

## Dev fix
- old Dev handoff rejected;
- change_id != defect_id rejected;
- no targeted repo revision change rejected;
- stale/failing Dev verification rejected;
- fix against wrong BA authority rejected.

## Retest
- Dev actor cannot VERIFIED;
- wrong testcase retest cannot close defect;
- wrong app revision rejected;
- wrong automation revision rejected;
- failed retest → REOPENED;
- later local drift invalidates VERIFIED revalidation.

---

# 35. Non-defect route acceptance

At least one direct acceptance each:

```text
SPEC_GAP
BUSINESS_DECISION_REQUIRED
TEST_ISSUE
ENVIRONMENT_ISSUE
```

Assert correct route and current execution attempt cannot become VERIFIED.

Do not require full BA/Test/environment correction loop inside Phase 8 acceptance.

Those corrections create new upstream/downstream artifacts and a new execution attempt.

---

# 36. Fresh installed acceptance

Install Test Kit into a clean temporary project.

Use installed package only.

Prefer:

```text
python -I
PYTHONPATH absent
external cwd
```

Assert execution modules load from installed .test-kit.

Run at minimum:

- straight PASS → VERIFIED;
- one DEFECT → Dev fix → READY_FOR_RETEST → retest PASS → VERIFIED;
- one failed retest → REOPENED negative or focused installed subcase;
- role-separation negative;
- revision-drift negative.

No network dependency.

---

# 37. Public example

Use a neutral synthetic domain, e.g. Resource Reservation.

Show:

```text
EXECUTION_READY
→ Execution Manifest
→ PASS
→ VERIFIED
```

and compact defect example:

```text
FINDING
→ DEFECT
→ Dev fix
→ READY_FOR_RETEST
→ VERIFIED
```

Do not use default examples from:
- Digital Wedding;
- CR-DWC-*;
- PetClinic;
- Appointment;
- machine-specific paths.

Historical benchmark material may remain clearly historical.

---

# 38. Documentation

Update relevant:

```text
kits/test/README.md
kits/test/skills/*
docs/vi/TEST_AUTOMATION_V1.md
docs/vi/TEST_EXECUTION_VNEXT.md
docs/en/TEST_AUTOMATION_V1.md
docs/en/TEST_EXECUTION_VNEXT.md
docs/vi/RELEASE.md
docs/en/RELEASE.md
installation/provenance docs when needed
```

Document explicitly:

- Execution Ready input;
- environment/revision binding;
- PASS vs Finding;
- Finding taxonomy;
- Defect classification is not automatic;
- Dev fix via normal Dev VNext FEATURE_DELIVERY;
- READY_FOR_RETEST;
- Tester-owned VERIFIED;
- REOPENED;
- Delivery Manifest deferred;
- legacy execution compatibility.

No feature-branch links.

---

# 39. Implementation strategy — one large completion attempt

To minimize manual rounds, implement Phase 8 as one large branch/session.

Target:

```text
feat/execution-defect-retest-vnext-phase8
```

Block A:

```text
VNext execution contracts
environment binding
execution manifest
runner/evidence
Observation
Finding
classification/routes
VERIFIED straight-pass
```

Block B:

```text
Defect Handoff
Dev-fix acceptance adapter
READY_FOR_RETEST
Retest
REOPENED
final VERIFIED
```

Block C:

```text
schemas/templates
skill/docs
package rc.8
Doctor
acceptance tiers
fresh installed acceptance
installed isolation
genericity
full regression
```

Do not voluntarily stop after Block A/B because task is large.

Stop early only for ARCHITECTURE_DECISION_REQUIRED or unrecoverable environment blocker.

Normal implementation/test/package failures must be fixed in same branch.

---

# 40. Architecture STOP conditions

Stop if implementation requires:

- making Delivery Manifest VNext authority;
- changing BA/UX/Testcase semantic authority;
- making current app behavior the expected oracle;
- auto-classifying every test failure as DEFECT;
- allowing Dev to final-VERIFY;
- adding a new Human semantic approval gate;
- duplicating Dev source mutation/review/verification engine;
- adding DEFECT_REPAIR authority mode to Dev without proving normal FEATURE_DELIVERY adapter impossible;
- making one Git SHA represent all multi-repo revisions;
- creating READY_TO_MERGE behavior;
- merging product branches automatically;
- hard-coding Playwright or one automation framework;
- hard-coding Digital Wedding semantics.

---

# 41. Package/provenance integrity

All managed package changes require canonical regeneration:

- package authority;
- payload tree digest;
- kit manifest integrity pins;
- provenance/notices/licenses when required.

Do not hand-edit hashes as shortcut.

After final docs changes, rerun/regenerate integrity again.

---

# 42. Regression requirements

Run focused Phase 8 suites plus all important existing suites.

At minimum:

```text
new Test Execution VNext unit tests
new full execution acceptance
new defect/retest acceptance
new installed Phase 8 acceptance
Test Automation V1 suites
Test Manual VNext suites
Test package/Doctor suites
Dev VNext contract/runtime/acceptance suites
BA VNext authority tests
Foundation tests
Shared SDLC tests
full tooling unittest discovery
git diff --check
```

No new skip added merely to bypass failures.

---

# 43. Temporary spec hygiene

Temporary bootstrap spec must be removed from final implementation tree.

Do not copy it elsewhere.

No scratch repos, caches, runtime evidence or local test outputs in final Git tree.

---

# 44. Final report

```text
PHASE_8_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/execution-defect-retest-vnext-phase8

BASE:
3075b6c51ef7a3ee58e9b11eedf57bb7ba7a8645

HEAD:
<exact SHA>

EXECUTION_READY_AUTHORITY:
<status>

ENVIRONMENT_BINDING:
<status>

EXECUTION_MANIFEST:
<status>

AUTOMATED_EXECUTION:
<status>

MANUAL_EXECUTION:
<status>

DEV_LOCAL_ACCOUNTING:
<status>

OBSERVATION_CONTRACT:
<status>

STRAIGHT_PASS_VERIFIED:
<status>

FINDING:
<status>

FINDING_CLASSIFICATION:
<status>

NON_DEFECT_ROUTES:
<status>

DEFECT_HANDOFF:
<status>

DEV_FIX_INTEGRATION:
<status>

READY_FOR_RETEST:
<status>

RETEST:
<status>

REOPENED:
<status>

TESTER_VERIFICATION_OWNERSHIP:
<status>

REVISION_DRIFT_GUARDS:
<status>

MULTI_REPO_BINDING:
<status>

NO_DELIVERY_MANIFEST_AUTHORITY:
<status>

LEGACY_COMPAT:
<status>

KIT_VERSION:
<version>

PACKAGE_AUTHORITY:
<status + hashes>

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

TESTS:
<summary>

SELF_REVIEW:
<status>

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
feat/execution-defect-retest-vnext-phase8

WORKTREE:
CLEAN

RECOMMENDED_PHASE_8_STATUS:
VERIFIED_COMPLETE_CANDIDATE | NOT_READY
```

A PASS report is not permission to merge. Final merge requires independent remote review.
