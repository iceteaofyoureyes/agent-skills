# PHASE 9 — PUBLIC CROSS-KIT CONFORMANCE / INTERNAL RC CANDIDATE

**Status:** HUMAN APPROVED FOR IMPLEMENTATION  
**Repository:** `iceteaofyoureyes/agent-skills`  
**Authoritative base:** `main` @ `ddee1d2c213587f1f46486ee7ecf1723db8c524a`  
**Phase 8 dependency:** Test Execution VNext `2.0.0-rc.8` VERIFIED COMPLETE + merged  
**Recommended model:** GPT-6 Luna Extra High when available.

> Phase 9 proves that Project Foundation + BA + Dev + Test Manual + Automation + Execution/Defect/Retest operate as one public framework through supported/public boundaries.
>
> Phase 9 is a conformance/release-candidate gate, not a new product-feature phase.

# 1. Target outcome

A neutral fresh-clone synthetic multi-repository project must complete:

```text
Project Foundation
→ BA VNext
→ Dev VNext
→ Test Design
→ Human Design Gate
→ Testcases
→ Human Case Gate
→ APPROVED_TESTWARE
→ Automation Suitability
→ Automation Plan
→ Automation Implementation
→ EXECUTION_READY
→ Execution
→ Finding
→ DEFECT
→ Dev VNext Fix
→ READY_FOR_RETEST
→ Tester Retest
→ VERIFIED
```

The same suite must also prove the no-defect route can reach `VERIFIED`.

Final Phase 9 result:

```text
PUBLIC_CROSS_KIT_CONFORMANCE = PASS
FRAMEWORK_INTERNAL_RC_CANDIDATE = READY
```

Do **not** publish/tag the internal RC in Phase 9.

A separate documentation quality/staleness audit follows Phase 9 before the first internal/pilot RC tag is created.

# 2. Frozen framework invariants

Do not redesign Phases 0–8.

Preserve:

```text
CONTINUE != APPROVE
ANSWER != APPROVE
validator PASS != APPROVE
generated != APPROVED
Derived != Authority
CURRENT_SYSTEM != confirmed target
Dev READY_FOR_TEST != Tester VERIFIED
Dev fix PASS != Tester VERIFIED
Human Gate = exact artifact revision/hash
BA = WHAT
Engineering = WHERE / WHO OWNS / HOW
Test = proves approved behavior
Delivery Manifest = DEFERRED_NON_AUTHORITATIVE
BAREF = locator/provenance only
APPROVED_TESTWARE != EXECUTION_READY
EXECUTION_READY != PASS
VERIFIED != READY_TO_MERGE
```

Do not add a new Human semantic gate.

Do not add a fourth kit.

# 3. Phase 9 is not a new feature phase

Allowed production changes:

- suite-level compatibility/orchestration;
- suite manifest/lock;
- public conformance runner;
- neutral synthetic conformance fixture;
- suite Doctor corrections;
- acceptance contract;
- release-candidate identity;
- minimal Phase-9-specific docs needed to run the conformance suite.

Not allowed:

- redesign BA/Dev/Test workflows;
- new artifact authority classes;
- Delivery Manifest redesign;
- Digital Wedding semantics;
- real project migration;
- stable release;
- large documentation rewrite.

The broad documentation audit happens immediately after Phase 9.

# 4. Existing suite layer is stale and must be corrected

Current `tooling/sdlc_suite.py` still contains legacy integration assumptions such as:

```text
ba_handoff = 1
delivery_manifest = 2
ux_approval_receipt = 2
testware_gate = 2
golden_provenance = 1
```

and legacy shared-contract checks.

This no longer represents the actual VNext suite.

Phase 9 must update suite-level compatibility so it verifies current public contracts instead of using legacy Delivery Manifest as a compatibility anchor.

Delivery Manifest may remain visible as compatibility/runtime packaging, but:

```text
Delivery Manifest MUST NOT be required for VNext suite conformance.
```

# 5. Framework Suite Manifest

Create one durable suite manifest, suggested path:

```text
tooling/sdlc-suite.json
```

This is release/package metadata, not business authority.

Minimum:

```text
schema_version
suite_id
suite_version
release_status
components
contracts
required_capabilities
compatibility
```

Expected identity:

```text
suite_id = agent-assisted-sdlc-vnext
suite_version = 1.0.0-rc.1
release_status = INTERNAL_RC_CANDIDATE
```

Component versions must be read/validated against the actual kit manifests:

```text
BA   = 2.0.0-rc.3
Dev  = 0.4.0-rc.1
Test = 2.0.0-rc.8
```

Do not duplicate component implementation semantics.

# 6. Current VNext suite contracts

Suite compatibility must bind current public boundary versions.

At minimum:

```text
Project Foundation Manifest / promotion = V1
BA Engineering Handoff VNext = V2
Dev Handoff = V2
Approved Testware Handoff = V1
Execution Ready Handoff = V1
Verified Handoff = V1
Finding Classification = V1
Defect Handoff = V1
Ready For Retest = V1
```

If an exact executable/schema version can be read from source, derive/check it there rather than maintaining an unrelated magic number.

Delivery Manifest:

```text
status = DEFERRED_NON_AUTHORITATIVE
```

Do not list it as required suite authority.

# 7. Suite lock

Keep the existing principle:

```text
suite lock binds exact framework Git commit + source tree + component versions + contract versions
```

Avoid circular self-hash.

The generated run-specific lock does not need to be committed if its own commit identity would create a cycle.

Phase 9 public acceptance evidence must record:

```text
framework commit SHA
framework tree SHA
suite manifest SHA-256
suite lock SHA-256
component versions
contract versions
```

Any source modification after candidate locking invalidates the conformance result and requires rerun.

# 8. Suite Doctor

Modernize suite Doctor to current VNext.

It must check at least:

```text
suite manifest
component version agreement
current VNext contract compatibility
Project Foundation runtime closure
BA package/Doctor
Dev package/Doctor
Test package/Doctor
Test package authority
required public skills/routers
runtime-ignore rules
no Delivery Manifest authority dependency
```

Current Test Kit correctly allows `READY` or `DEGRADED` when only optional capabilities such as XMind/Excel are absent.

Suite Doctor must distinguish core readiness from optional degradation. A Test Doctor `DEGRADED` caused exclusively by documented optional projection dependencies must not fail public core conformance. A required capability/integrity failure must fail suite Doctor.

# 9. Public-boundary rule

System conformance MUST run through supported/public boundaries.

It MUST NOT prove the framework by importing arbitrary source-private internals from the developer checkout.

Allowed examples:

- installed package/runtime public APIs;
- installed CLI/skill entrypoints;
- Project Foundation public script;
- host adapter APIs explicitly documented as runtime boundaries.

Not acceptable:

```text
sys.path += original developer checkout
import a private helper only because the public interface is inconvenient
```

A test helper may orchestrate public APIs, but must not bypass their authority validation.

# 10. Fresh framework clone

Phase 9 requires a fresh local clone of the exact Phase 9 candidate commit.

Acceptance must:

1. commit the Phase 9 candidate;
2. create a second clean local clone from that repository;
3. checkout the exact candidate SHA;
4. prove clean working tree;
5. run public conformance from the clone;
6. never import runtime code from the original working checkout.

No network is required. Use local Git clone. Do not use uncommitted source files.

# 11. Isolated runtime

Public conformance should use:

```text
external working directory
PYTHONPATH absent
python -I where supported
temporary HOME / CODEX_HOME where needed
```

No hidden user-global skills/configuration may be required for the deterministic conformance lane.

If Dev installation needs a dedicated profile/runtime, create it inside the synthetic acceptance environment.

Do not copy user auth, global hooks or private config into acceptance.

# 12. Synthetic multi-repo project

Create a neutral project such as:

```text
resource-reservation-workspace/
├── project-docs/
├── service-app/
└── test-automation/
```

Each implementation/automation repository is a real local Git repository with committed revisions.

Use neutral domain terms only.

Do not use:

```text
Digital Wedding
CR-DWC-*
PetClinic
Appointment
user-specific paths
company-specific semantics
```

The workspace must declare Project Topology and Project Policy.

Roles must allow the framework to resolve documentation/product authority, application implementation and automation repository without guessing directory names.

# 13. Project Foundation conformance

Phase 9 begins with real Project Foundation VNext behavior through public Foundation entrypoints.

Demonstrate a neutral Foundation flow using `GREENFIELD_BOOTSTRAP` or a clearly justified synthetic mode.

It must produce/revalidate product/domain context, architecture/runtime context, testing/automation context, topology/policy, Foundation review candidate, exact Human approval, promoted Foundation manifest/provenance, and `PROJECT_FOUNDATION_READY`.

Use deterministic synthetic owner inputs.

Human approval is `TEST_ONLY` / `not_for_production`, but must go through the same trusted-host approval boundary.

Validator/prepare/CONTINUE must not self-approve.

# 14. BA cross-kit conformance

From the approved Foundation context, execute BA VNext through public/installed boundaries.

Produce a neutral feature with at least one `BR-*` and one `FR-*`, no BAREF in canonical business trace, and no blocking UNKNOWN at approval.

Required lifecycle:

```text
DRAFT
→ VALIDATED
→ HUMAN_REVIEW
→ authenticated Human APPROVE
→ APPROVED_BASELINE
→ Engineering Handoff VNext
```

Prove exact Foundation refs are consumed when declared, no self approval, handoff is V2, exact Human receipt revalidates, and downstream may not change WHAT.

# 15. Dev cross-kit conformance

Install/run Dev VNext through supported runtime with:

```text
authority_mode = FEATURE_DELIVERY
```

Bind exact BA Engineering Handoff VNext.

Demonstrate:

```text
Authority validated
→ Impact
→ Plan
→ tasks
→ implementation
→ consolidated review
→ fresh repository-scoped verification
→ BR/FR coverage
→ READY_FOR_TEST
```

Application source changes must be committed.

Dev Handoff V2 must bind exact app Git SHA.

No VERIFIED claim.

# 16. Test Manual cross-kit conformance

Consume exact BA authority and current Dev context through Test VNext.

Demonstrate:

```text
Test Design
→ DESIGN_REVIEW
→ authenticated Human Design approval
→ APPROVED_DESIGN
→ Testcases
→ CASE_REVIEW
→ authenticated Human Case approval
→ APPROVED_TESTWARE
```

At least one TEST_AUTOMATION testcase is required. A DEV_LOCAL_REFERENCE testcase should also be present when supported by the approved design.

No fabricated Human receipt. Synthetic Human callbacks must be explicit TEST_ONLY/not_for_production.

# 17. Automation cross-kit conformance

Consume exact Approved Testware.

Demonstrate:

```text
Automation Suitability
→ Automation Plan
→ AUT-*
→ test-automation repository write
→ commit
→ review
→ automation-only verification
→ exact Dev READY_FOR_TEST binding
→ EXECUTION_READY
```

Prove app repo remains read-only to Test Automation, automation repository is resolved from topology/policy, automation revision is exact committed Git SHA, and no real execution PASS is claimed here.

# 18. Phase 8 execution conformance

Consume exact `EXECUTION_READY`.

Run the real synthetic product command through exact Automation Plan argv.

Use exact environment/revision binding.

The public cross-kit suite must prove:

```text
command evidence
Observation
Finding
classification
Defect Handoff
Dev fix
READY_FOR_RETEST
retest
VERIFIED
```

No Delivery Manifest authority.

# 19. Defect/fix path is mandatory

Phase 9 must demonstrate a full defect cycle, not only straight PASS.

The synthetic app should contain or produce a deterministic/reproducible business-behavior mismatch that:

- is not caught by Dev-local checks;
- is caught by approved Test automation;
- is classified by authenticated Tester as DEFECT;
- targets an exact app repository;
- is fixed using the normal Dev VNext FEATURE_DELIVERY flow;
- uses `change_id = defect_id`;
- starts from the failed app revision;
- results in a new committed app SHA;
- passes Dev review/fresh verification;
- creates READY_FOR_RETEST;
- passes Tester retest;
- ends VERIFIED.

Do not hot-patch the automation/test oracle to make the defect pass.

# 20. Straight-pass path

Also prove one clean no-defect execution route, either as a second feature or a second independent scenario.

Required:

```text
EXECUTION_READY
→ execution
→ PASS Observations
→ Tester VERIFIED
```

# 21. Cross-kit trace chain

Phase 9 must assert exact trace continuity:

```text
Human Decision / approved BA
→ FR / BR
→ Test Design
→ Testcase
→ AUT
→ repository/path
→ committed automation SHA
→ execution evidence
→ Finding if any
→ Defect
→ Dev fix SHA
→ Retest
→ VERIFIED
```

No BAREF as canonical requirement identity.

No runtime artifact may silently replace canonical authority.

# 22. Multi-repository revision reproduction

Evidence must retain exact docs/Foundation authority hashes, application repository ID → SHA, automation repository ID → SHA, and framework candidate SHA.

The acceptance must demonstrate that a second clean checkout can resolve the application/automation SHAs required by the relevant handoff/evidence.

No local uncommitted state may be necessary.

# 23. Framework source immutability

Once the candidate conformance run starts, agent-skills candidate source MUST remain clean and unchanged.

The synthetic flow may mutate only synthetic project repositories.

If the framework needs a source patch during conformance:

```text
FRAMEWORK_DEFECT
→ fail Phase 9 candidate
→ patch on implementation branch
→ rerun full public conformance from a new candidate SHA
```

Do not hot-patch installed runtime in the synthetic workspace.

# 24. No private-project semantics

Scan Phase 9 production/public conformance surfaces for Digital Wedding, CR-DWC-*, PetClinic, Appointment, absolute local usernames, private hostnames and private repository paths.

Historical benchmark fixtures outside the Phase 9 public lane may remain clearly historical.

Phase 9 public acceptance must be usable by an OSS contributor without access to Digital Wedding.

# 25. Public Conformance Runner

Create a single obvious entrypoint, suggested:

```text
python -m tooling.public_conformance ...
```

or repository-consistent equivalent.

It should orchestrate preflight, fresh clone, suite Doctor, synthetic workspace, Foundation, BA, Dev, Test, Automation, Execution, Defect/Fix/Retest, fresh-clone reproduction checks and final report.

Do not hide the required flow behind a collection of undocumented test commands.

# 26. Conformance report

Generate a deterministic report as EVIDENCE, not committed runtime authority.

Minimum:

```text
schema_version
evidence_class = PUBLIC_CROSS_KIT_CONFORMANCE
framework_sha
framework_tree
suite_manifest_sha256
suite_lock_sha256
component_versions
scenario_results
trace_checks
revision_checks
doctor_results
fresh_clone
genericity
test_summary
status
```

Final status only `PASS` or `FAIL`.

No `READY_TO_MERGE`.

The report should be written to a caller-provided output path outside the clean source tree.

# 27. Suite acceptance contract

Add a suite-level acceptance contract, suggested path:

```text
tooling/sdlc-suite-acceptance.yaml
```

Distinguish:

```text
Tier A — component regression
Tier B — suite compatibility / Doctors
Tier C — installed public cross-kit flow
Tier D — fresh-clone reproducibility
```

Phase 9 completion requires all tiers.

Individual kit green tests are necessary but insufficient.

# 28. Negative cross-kit probes

At minimum prove:

### Authority
- legacy BA V1 cannot enter VNext public flow;
- validator PASS cannot replace Human approval;
- stale BA receipt blocks downstream;
- stale Test gate receipt blocks downstream.

### Suite compatibility
- mismatched component version fails suite compatibility;
- required contract version mismatch fails;
- Delivery Manifest absence does not block VNext suite;
- optional Test dependency absence does not fail core conformance.

### Repository routing
- ambiguous automation role fails;
- wrong app revision fails execution;
- wrong automation revision fails execution.

### Role separation
- Dev cannot final-VERIFY;
- Test cannot mutate app repo during Automation;
- execution command failure does not auto-create Defect.

### Fresh clone
- original developer checkout cannot satisfy installed imports accidentally.

# 29. Regression

Before final PASS run at least BA acceptance suites, Dev acceptance suites, Test Manual VNext suites, Automation V1 suites, Execution VNext suites, Project Foundation suites, Shared SDLC acceptance/contracts, suite Doctor tests, new public conformance tests, fresh clone conformance, full tooling unittest discovery and `git diff --check`.

Do not weaken assertions. Do not add skips merely to get green.

# 30. Suite Doctor / old readiness acceptance migration

Audit and update:

```text
tooling/sdlc_suite.py
tooling/readiness_acceptance.py
tooling/tests/test_sdlc_acceptance.py
docs/vi/SDLC_SUITE_CONTRACT.md only where necessary for Phase 9 execution
```

Old synthetic/Golden readiness logic may remain explicitly historical/legacy if still useful, but it must not be presented as the current VNext public conformance contract.

Do not make old Delivery Manifest/Test V1 flow the default suite acceptance.

Broad documentation cleanup is deferred to the post-Phase-9 docs lane.

# 31. Internal RC candidate identity

Phase 9 may declare:

```text
Framework Suite: 1.0.0-rc.1
Status: INTERNAL_RC_CANDIDATE
```

only after public conformance passes.

Do not create a Git tag or GitHub Release yet.

Do not claim stable release.

After Phase 9:

```text
Full Documentation Audit & Hardening
→ rerun impacted conformance/regression
→ then create first Internal/Pilot RC tag
```

# 32. Documentation quality lane is explicitly next

Do not consume Phase 9 by rewriting the full documentation corpus.

After Phase 9 merge, the next mandatory lane is:

```text
DOCUMENTATION QUALITY & STALENESS AUDIT
```

It will inventory and review the full repository documentation for stale workflow/version/status claims, obsolete Delivery Manifest/Test V1 defaults, duplicated/conflicting authority descriptions, dead/broken links, feature-branch links, outdated examples, unclear onboarding, missing role-oriented navigation, missing task-oriented guides, installation ambiguity, Doctor/readiness ambiguity, release/status ambiguity, historical docs not clearly labeled, English/Vietnamese drift, excessive implementation detail in operator docs, insufficient examples/troubleshooting, inconsistent terminology, low-quality/provisional wording, and docs that require oral knowledge transfer.

Phase 9 must leave enough machine-readable suite truth so the docs audit has a reliable source of truth.

# 33. Implementation strategy — one large Phase 9 completion attempt

Target branch:

```text
feat/public-cross-kit-conformance-phase9
```

Attempt all Phase 9 work in one branch/session.

Block A:
- suite manifest;
- suite compatibility modernization;
- suite Doctor;
- public acceptance contract.

Block B:
- neutral multi-repo fixture;
- Foundation → BA → Dev → Test → Automation → Execution;
- defect/fix/retest path;
- straight-pass path;
- trace/revision assertions.

Block C:
- fresh framework clone;
- isolated installed runtime;
- fresh-clone reproduction;
- genericity;
- report generation;
- full regression;
- minimal Phase-9-specific docs.

Do not voluntarily stop between blocks just because the task is large.

Stop only for `ARCHITECTURE_DECISION_REQUIRED` or an unrecoverable environment/tooling blocker.

# 34. Architecture STOP conditions

Stop before changing architecture if Phase 9 seems to require making Delivery Manifest authoritative again, changing BA/Dev/Test semantic contracts, a new Human semantic gate, changing Dev authority modes, changing Test Finding taxonomy, adding READY_TO_MERGE, adding automatic merge/release, making Digital Wedding required for public conformance, using private implementation internals as the only way to run cross-kit flow, requiring user-global private configuration, or changing stable package semantics merely to make the acceptance runner easier.

# 35. Packaging/version rule

Do not bump BA/Dev/Test package versions solely because suite conformance files changed outside their managed payload.

If a kit managed file/runtime must change to fix a real framework defect:
1. treat it as a real package change;
2. advance its prerelease version appropriately;
3. regenerate its package authority;
4. rerun its installed acceptance;
5. rerun full Phase 9 conformance.

Do not hide a framework defect inside the conformance fixture.

# 36. Source hygiene

Before final Phase 9 commit:
- remove temporary bootstrap spec;
- no generated conformance report inside source tree;
- no runtime synthetic workspace;
- no fresh clone directory;
- no caches/node_modules;
- no local user config;
- no secrets.

The public conformance test fixture/source code may remain, but run outputs must be ephemeral or caller-specified.

# 37. Required final report

```text
PHASE_9_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/public-cross-kit-conformance-phase9

BASE:
ddee1d2c213587f1f46486ee7ecf1723db8c524a

HEAD:
<exact SHA>

SUITE_VERSION:
1.0.0-rc.1

SUITE_STATUS:
INTERNAL_RC_CANDIDATE | NOT_READY

SUITE_MANIFEST:
<status>

SUITE_COMPATIBILITY:
<status>

DELIVERY_MANIFEST_AUTHORITY:
DEFERRED_NON_AUTHORITATIVE

SUITE_DOCTOR:
<status>

OPTIONAL_DEGRADED_POLICY:
<status>

PUBLIC_CONFORMANCE_RUNNER:
<status>

FRESH_FRAMEWORK_CLONE:
<status>

INSTALLED_ISOLATION:
<status>

PROJECT_FOUNDATION:
<status>

BA_VNEXT:
<status>

DEV_VNEXT:
<status>

TEST_MANUAL_VNEXT:
<status>

AUTOMATION_V1:
<status>

EXECUTION_VNEXT:
<status>

DEFECT_FIX_RETEST:
<status>

STRAIGHT_PASS:
<status>

TRACE_CONTINUITY:
<status>

MULTI_REPO_REVISIONS:
<status>

FRAMEWORK_SOURCE_IMMUTABILITY:
<status>

PUBLIC_BOUNDARY_ONLY:
<status>

GENERICITY:
<status>

NEGATIVE_PROBES:
<status>

CONFORMANCE_REPORT:
<status>

COMPONENT_TESTS:
<status>

FULL_REGRESSION:
<status>

DOCS_PHASE9_MINIMAL:
<status>

BROAD_DOC_AUDIT:
DEFERRED_TO_NEXT_MANDATORY_LANE

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
feat/public-cross-kit-conformance-phase9

WORKTREE:
CLEAN

RECOMMENDED_PHASE_9_STATUS:
VERIFIED_COMPLETE_CANDIDATE | NOT_READY
```

A PASS report is not permission to merge. Final Phase 9 merge requires independent remote review.