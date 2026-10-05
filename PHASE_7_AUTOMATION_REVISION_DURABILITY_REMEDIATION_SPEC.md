# PHASE 7 — AUTOMATION REVISION DURABILITY REMEDIATION

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills

Phase 7 candidate base:
7e6b142ddc84f2d705fce64f01c5f160d2ece866

Authoritative framework base:
44617175f1c441811f7bf4f64672964d7446ac39

Target implementation branch:
fix/phase7-automation-revision-durability

Recommended model:
GPT-6 Luna Extra High

This is a narrow remediation. Preserve all other Phase 7 semantics.

---

## 1. Independent-review finding

Current Phase 7 can reach EXECUTION_READY while automation source exists only as staged/uncommitted working-tree changes.

The synthetic and installed acceptance paths currently:
- write automation files;
- git add them;
- do not create a Git commit;
- record implementation;
- review;
- verify;
- finalize EXECUTION_READY.

Current handoff records:

AUTOMATION_TREE_SHA256:<digest>

as automation_revision.

That digest is calculated from local base/head/file state, but the durable handoff does not carry enough information to let a fresh clone:
- checkout the exact automation source;
- independently reproduce the source state from Git;
- bind Phase 8 execution to a durable repository revision.

The VNext roadmap requires exact application and automation repository SHAs for execution/reproduction.

Therefore Phase 7 is not yet merge-ready.

---

## 2. Required outcome

EXECUTION_READY must bind an exact committed automation Git revision.

For Test-owned automation:

automation_repository
+
automation_revision = exact Git commit SHA
+
planned paths
+
review/verification refs

must be enough for a Phase 8 consumer/fresh clone to checkout the exact automation source.

A local working-tree digest may remain supplementary evidence, but it may not replace the Git revision in the durable handoff.

---

## 3. Frozen semantics

Do NOT change:

- Approved Testware VNext authority;
- Automation Suitability;
- Automation Plan;
- AUT identity/trace;
- repository routing;
- app repo read-only boundary;
- DEV_LOCAL_REFERENCE;
- MANUAL_ONLY;
- BLOCKED;
- dependency rules;
- review budgets;
- automation-only verification;
- exact Dev READY_FOR_TEST requirement;
- no third Human Gate;
- Delivery Manifest deferred/non-authoritative;
- tool-agnostic behavior;
- Phase 7 terminal = EXECUTION_READY;
- Phase 8 boundary.

If this remediation requires changing those semantics:

ARCHITECTURE_DECISION_REQUIRED

and STOP.

---

## 4. Repository commit boundary

Test Automation runtime must not silently create Git commits on behalf of the project.

The implementation agent/operator remains responsible for committing automation repository changes using normal project Git workflow.

Runtime responsibility:

1. authorize writes while automation repository is at the exact planned base revision;
2. allow project/agent to stage and commit those planned changes;
3. before recording implementation/final readiness, validate the resulting committed repository state.

Do not add automatic push/merge behavior.

---

## 5. record_implementation requirements

For TEST_AUTOMATION items, record_implementation must require:

- automation repository exists;
- current HEAD descends from exact plan base_revision;
- current HEAD is not the planned base when executable TEST_AUTOMATION items require new implementation;
- worktree is clean;
- index is clean;
- no untracked files;
- diff from plan base_revision to current HEAD contains only planned automation paths;
- every planned automation path is present in the committed diff;
- every changed path is a regular safe file;
- no app repository mutation;
- exact source file bytes/hashes are captured as implementation evidence.

If the automation repository still has staged, unstaged or untracked implementation changes:

fail closed with a clear code such as:

AUTOMATION_COMMIT_REQUIRED

Do not produce implementation evidence from uncommitted working-tree state.

---

## 6. Automation revision

The canonical durable automation revision must be:

current automation repository Git HEAD commit SHA

Expected form:
- 40-hex SHA-1 repositories; or
- future compatible 64-hex repository hash where supported by existing framework conventions.

Do not prefix the primary handoff revision with AUTOMATION_TREE_SHA256.

A supplementary content/tree digest may remain inside runtime/evidence if useful.

The handoff field:

automation_revision

must mean repository revision, not a local synthetic digest.

Each automation item revision must equal the same exact automation Git revision unless future multi-automation-repository architecture explicitly changes this contract.

Phase 7 currently has one declared automation repository.

---

## 7. Implementation evidence

Preserve exact evidence sufficient to detect drift.

Implementation runtime/evidence should retain at least:

- base_revision;
- repository_revision;
- changed_paths;
- exact path SHA-256 values;
- AUT → paths mapping.

This may remain in runtime/evidence and does not need to duplicate into every canonical artifact.

The EXECUTION_READY handoff must contain the repository identity, exact automation_revision and AUT paths.

That combination must be independently checkable against the repository checkout.

---

## 8. Review and verification binding

Automation Review and Automation Verification must bind the committed automation revision.

They must not bind a pre-commit working-tree digest as their primary source revision.

Verification must run against the exact committed automation HEAD with a clean worktree.

If verification mutates source/worktree:

fail closed.

If HEAD changes after review or verification:

stale evidence must fail/replan.

---

## 9. EXECUTION_READY finalization

Before EXECUTION_READY:

- automation repo HEAD must equal recorded implementation repository_revision;
- worktree/index/untracked state must be clean;
- exact diff base..HEAD must still match planned paths;
- current source hashes must match implementation evidence;
- review must PASS for this revision;
- automation verification must PASS for this revision;
- exact Dev Handoff READY_FOR_TEST remains current;
- required dependencies remain resolved.

Handoff:

automation_revision

must equal exact automation Git HEAD.

Schema must reflect the Git revision format.

---

## 10. Durable revalidation

revalidate_handoff must independently confirm:

- declared automation repository identity;
- current automation repository HEAD == handoff automation_revision;
- worktree clean;
- AUT paths exist at that revision/current checkout;
- implementation evidence still matches exact committed bytes where runtime evidence is present;
- review and verification still bind that revision;
- Dev/application revisions remain current.

A local unstaged/staged edit after EXECUTION_READY must invalidate readiness.

A new automation commit after EXECUTION_READY must invalidate readiness until valid replan/review/verification.

---

## 11. Fresh-clone acceptance

Update installed/fresh acceptance to prove repository durability.

The synthetic automation flow must:

1. write planned automation files;
2. stage them;
3. commit them in the synthetic automation repository;
4. record implementation only after the commit;
5. review;
6. verify;
7. finalize EXECUTION_READY;
8. assert handoff automation_revision == automation repo HEAD commit;
9. clone or create a second clean checkout of the automation repository at that exact commit;
10. prove the handoff revision can be checked out/resolved there;
11. prove planned AUT paths exist with the expected committed content;
12. prove no local working-tree state is required to reconstruct the exact automation source.

Do not require network access. Use local Git clone/file URL or another deterministic local mechanism.

This is mandatory.

---

## 12. Negative acceptance

Add direct regressions:

### A. Staged-only implementation

planned files written + git add but no commit

→ record_implementation or readiness must fail:
AUTOMATION_COMMIT_REQUIRED

### B. Unstaged implementation

→ fail.

### C. Untracked implementation

→ fail.

### D. Commit contains out-of-plan file

→ WRITE_SCOPE_VIOLATION.

### E. Commit misses a planned path

→ IMPLEMENTATION_INCOMPLETE.

### F. Commit source then mutate working tree

→ review/verify/finalize or revalidation fails.

### G. Commit source, review/verify, then create another commit

→ EXECUTION_READY evidence becomes stale / NEEDS_REPLAN.

### H. Fresh clone at exact handoff SHA

→ succeeds and contains the exact automation paths.

---

## 13. Schema/docs

Update only the surfaces affected by revision semantics.

At minimum inspect/update:

- execution-ready-v1-handoff schema;
- Automation V1 docs;
- Test Automation skill;
- neutral example;
- tests/templates if they currently show AUTOMATION_TREE_SHA256 as the durable revision.

Terminology:

automation_revision
= exact Git repository commit SHA.

A content digest may be described separately as implementation evidence.

Do not introduce feature-branch links.

---

## 14. Package integrity

Because Test package managed files will change:

- regenerate package authority using repository-owned tooling/algorithm;
- update payload tree digest;
- update kit manifest pinned integrity;
- keep version 2.0.0-rc.7 unless repository-owned versioning policy requires another RC for this remediation.

This remediation does not require a new semantic package major/minor version.

Do not hand-edit hashes without recomputing canonical package authority.

---

## 15. Tests

Run at minimum:

- tooling.tests.test_test_automation_v1
- tooling.tests.test_test_automation_v1_acceptance
- tooling.tests.test_test_automation_v1_installed_acceptance
- tooling.tests.test_test_automation_v1_schemas
- tooling.tests.test_kit_packaging
- tooling.tests.test_test_kit_policy_doctor
- Dev VNext tests relevant to READY_FOR_TEST binding
- Shared SDLC contract tests
- full tooling unittest discovery
- git diff --check

No new skips to bypass remediation.

---

## 16. Hygiene

Before final commit delete:

PHASE_7_AUTOMATION_REVISION_DURABILITY_REMEDIATION_SPEC.md

Do not copy/rename it elsewhere.

Final tree must contain no temporary Phase 7 spec.

No scratch clones, local runtime dirs, caches or generated node_modules.

---

## 17. Git workflow

Source bootstrap branch:

phase7/automation-v1-revision-remediation-bootstrap

Source candidate:
7e6b142ddc84f2d705fce64f01c5f160d2ece866

Target:
fix/phase7-automation-revision-durability

Do not merge.

Push target branch.

Worktree clean.

---

## 18. Required report

PHASE_7_REVISION_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/phase7-automation-revision-durability

BASE:
7e6b142ddc84f2d705fce64f01c5f160d2ece866

HEAD:
<exact SHA>

COMMIT_REQUIRED_BOUNDARY:
<status>

AUTOMATION_REVISION:
<exact Git revision semantics>

IMPLEMENTATION_EVIDENCE:
<base/revision/path hashes>

REVIEW_BINDING:
<status>

VERIFICATION_BINDING:
<status>

EXECUTION_READY_BINDING:
<status>

REVALIDATION:
<status>

FRESH_CLONE_REVISION_ACCEPTANCE:
<status>

UNCOMMITTED_NEGATIVES:
<status>

OUT_OF_SCOPE_COMMIT:
<status>

STALE_COMMIT_NEGATIVE:
<status>

SCHEMAS_DOCS:
<status>

PACKAGE_AUTHORITY:
<hashes/status>

TESTS:
<results>

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
fix/phase7-automation-revision-durability

WORKTREE:
CLEAN

RECOMMENDED_PHASE_7_STATUS:
VERIFIED_COMPLETE_CANDIDATE | NOT_READY
