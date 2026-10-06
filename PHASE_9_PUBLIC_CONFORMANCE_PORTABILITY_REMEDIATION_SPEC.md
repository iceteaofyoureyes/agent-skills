# PHASE 9 — PUBLIC CONFORMANCE PORTABILITY REMEDIATION

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills

Phase 9 candidate base:
c3240162a280c86e910daea9f39ff9e74dee7c00

Framework main base:
ddee1d2c213587f1f46486ee7ecf1723db8c524a

Target branch:
fix/phase9-public-conformance-portability

Recommended model:
GPT-6 Luna Extra High when available.

This is a narrow Phase 9 remediation. Preserve all Phase 0–8 semantics and all successful Phase 9 cross-kit behavior.

---

## 1. Independent-review blockers

### P9-R1 — feature-branch hard-code

Current public conformance runner contains:

```text
BRANCH = "feat/public-cross-kit-conformance-phase9"
```

and rejects any checkout whose current branch is not that exact feature branch.

This makes the supposedly public conformance runner unusable after Phase 9 is merged to `main`, unusable from a detached candidate checkout, and unusable after the mandatory Documentation Quality & Staleness Audit when conformance must be rerun on a new candidate commit.

This violates the Phase 9 contract. Conformance authority is the exact clean candidate commit/tree + suite manifest/lock, not a branch name.

### P9-R2 — optional projection dependency promoted to mandatory

The Suite Doctor correctly treats missing XMind/Excel projection dependencies as optional degradation.

However `tooling/public_conformance.py` currently runs optional projection setup and then forces:

```text
optional projection runtime != PASS
→ entire public conformance FAIL
```

This contradicts the frozen Phase 9 policy:

```text
optional Test projection dependency absence
→ OPTIONAL_DEGRADED / unavailable
→ core public conformance may still PASS
```

A public/OSS contributor must not need npm/XMind optional runtime merely to prove the core framework lifecycle.

---

## 2. Frozen semantics

Do NOT change:

- Project Foundation authority;
- BA VNext authority/Human approval;
- Dev VNext FEATURE_DELIVERY semantics;
- Test Manual VNext gates;
- Automation V1 authority or repository ownership;
- Execution VNext;
- Finding taxonomy;
- Defect proof;
- Dev fix/retest/VERIFIED;
- multi-repo revision binding;
- Delivery Manifest = DEFERRED_NON_AUTHORITATIVE;
- Test-only synthetic authority safety;
- suite version 1.0.0-rc.1;
- BA version 2.0.0-rc.3;
- Dev version 0.4.0-rc.2;
- Test version 2.0.0-rc.11.

If remediation requires a managed BA/Dev/Test runtime/package change:

```text
ARCHITECTURE_DECISION_REQUIRED
```

and STOP unless it is only a direct regression caused by these two suite-runner defects.

This remediation should normally touch suite/public-conformance code and its tests only.

---

## 3. Candidate identity must be commit-based, not branch-based

Remove the fixed Phase 9 feature branch requirement.

`run_candidate()` must authorize a conformance candidate from:

- exact current Git HEAD;
- clean working tree;
- valid VNext suite manifest;
- current component/contract compatibility;
- generated exact suite lock;
- fresh local clone of that exact HEAD.

The branch name is non-authoritative metadata.

Valid invocation contexts must include at least:

```text
main branch
arbitrary feature/candidate branch
detached HEAD
```

provided the checkout is clean, committed and contains a valid current suite candidate manifest.

Do not weaken exact SHA/tree validation.

Do not allow dirty or uncommitted framework source.

Do not silently switch branches.

Do not require a Git tag.

---

## 4. Fresh clone remains exact

After removing branch-name gating, preserve:

```text
candidate SHA
candidate tree
clean source
local fresh clone
exact checkout
core.autocrlf=false for byte reproduction
suite lock
clean fresh clone
```

The runner must still prove that the child process executes from the exact fresh clone.

The original developer checkout must not satisfy child imports.

---

## 5. Optional projection policy

XMind/Excel projections are optional capabilities.

Public core conformance must distinguish:

```text
CORE_REQUIRED
OPTIONAL_AVAILABLE
OPTIONAL_DEGRADED
FAIL_REQUIRED
```

or repository-equivalent status vocabulary.

For optional projection setup:

### Available

If required optional tooling/cache is present and setup succeeds:

```text
status = OPTIONAL_AVAILABLE
```

The optional projection tests may run normally.

### Unavailable / absent

If npm, Node, offline cache, XMind SDK runtime or optional projection dependency is absent:

```text
status = OPTIONAL_DEGRADED
```

Core conformance continues.

This must NOT make:

```text
test_summary.status = FAIL
```

by itself.

### Real core/integrity failure

Do not classify these as optional:

- Test package authority mismatch;
- corrupted package metadata;
- required Test runtime missing;
- required execution/automation runtime missing;
- malformed optional dependency metadata/lock that violates package integrity.

Those remain hard failures through Suite Doctor/package validation.

---

## 6. Do not auto-install a hidden mandatory dependency

The runner may attempt an **offline optional** XMind runtime setup when tooling exists.

But:

- no network is required;
- failure to materialize the optional projection runtime is not a core failure;
- the result must be reported transparently;
- no user-global Node/npm environment may become an undeclared authority.

If the optional runtime is unavailable, existing tests that are designed to skip without optional dependencies may skip.

Do not add broad skips or weaken core assertions.

---

## 7. Conformance report

The report must retain an explicit optional-projection status.

Suggested:

```json
{
  "optional_projection_runtime": {
    "status": "OPTIONAL_AVAILABLE | OPTIONAL_DEGRADED",
    "reason": "..."
  }
}
```

or equivalent existing compact structure.

Overall PASS logic:

```text
required suite Doctor PASS
required component tests PASS
installed cross-kit flow PASS
fresh clone PASS
genericity PASS
negative probes PASS
diff check PASS

optional projection unavailable
→ does not change PASS to FAIL
```

Do not hide optional degradation.

---

## 8. Mandatory regression tests — branch portability

Add direct tests proving:

### A. Arbitrary clean branch

A clean committed repo on a non-Phase-9 feature branch is accepted as a candidate.

### B. Main

A clean committed checkout on `main` is accepted.

### C. Detached HEAD

A clean detached HEAD at an exact commit is accepted.

### D. Dirty checkout

Reject.

### E. Exact SHA/tree

Fresh clone still equals candidate SHA/tree.

### F. Source changes after candidate start

Still invalidate the run.

No test may depend on the literal string:

```text
feat/public-cross-kit-conformance-phase9
```

as authorization.

---

## 9. Mandatory regression tests — optional dependency

Add direct tests proving:

### A. npm/Node unavailable

```text
optional projection = OPTIONAL_DEGRADED
core conformance status can remain PASS
```

### B. optional offline install unavailable/fails

```text
OPTIONAL_DEGRADED
not full FAIL
```

### C. optional runtime available

```text
OPTIONAL_AVAILABLE
```

### D. required Test package/integrity failure

Still hard FAIL.

### E. Suite Doctor DEGRADED due only optional projection

Still core-ready.

The Phase 9 negative probe:

```text
optional Test dependency absence does not fail core conformance
```

must be proved at the **public runner level**, not only by a unit test of `test_core_readiness()`.

---

## 10. Full public conformance rerun

After remediation is committed:

Run the real public conformance runner again from the remediation candidate itself.

It must:

- create a fresh local clone of exact remediation HEAD;
- run complete Foundation → BA → Dev → Test → Automation → Execution;
- run mandatory defect/fix/retest path;
- run straight-pass path;
- run all negative probes;
- produce a PASS external report;
- keep framework source clean.

Do not rely only on focused unit tests.

---

## 11. Component versions

Expected final versions remain:

```text
BA   2.0.0-rc.3
Dev  0.4.0-rc.2
Test 2.0.0-rc.11
Suite 1.0.0-rc.1
```

Do not bump kit versions for suite-only remediation.

If a managed kit file changes unexpectedly, investigate before proceeding.

---

## 12. Documentation scope

Only minimal Phase-9-specific documentation may be changed if it currently claims a fixed branch or mandatory optional projections.

Do not begin the broad docs audit here.

The next mandatory lane remains:

```text
FULL DOCUMENTATION QUALITY & STALENESS AUDIT
```

after Phase 9 merge.

---

## 13. Hygiene

Before final commit delete:

```text
PHASE_9_PUBLIC_CONFORMANCE_PORTABILITY_REMEDIATION_SPEC.md
```

Do not rename/copy it elsewhere.

No generated conformance report, fresh clone, synthetic workspace, caches, node_modules, temporary HOME/CODEX_HOME or runtime evidence in source tree.

---

## 14. Tests minimum

Run at least:

```text
python -m unittest tooling.tests.test_public_conformance_runner -v
python -m unittest tooling.tests.test_public_conformance_flow -v
python -m unittest tooling.tests.test_sdlc_suite_vnext -v
python -m unittest tooling.tests.test_sdlc_acceptance -v
python -m unittest tooling.tests.test_kit_packaging -v
python -m unittest tooling.tests.test_test_kit_policy_doctor -v

full public conformance from exact remediation candidate
full tooling unittest discovery
git diff --check
```

Also run any focused suite tests added by the remediation.

No new skip merely to make the task green.

---

## 15. Git workflow

Source bootstrap:

```text
phase9/public-conformance-portability-remediation-bootstrap
```

Behavioral base:

```text
c3240162a280c86e910daea9f39ff9e74dee7c00
```

Target:

```text
fix/phase9-public-conformance-portability
```

Push target.

Do not merge.

Worktree clean.

---

## 16. Required final report

```text
PHASE_9_PORTABILITY_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/phase9-public-conformance-portability

BASE:
c3240162a280c86e910daea9f39ff9e74dee7c00

HEAD:
<exact SHA>

BRANCH_INDEPENDENCE:
<status>

MAIN_CANDIDATE:
<status>

DETACHED_HEAD_CANDIDATE:
<status>

DIRTY_SOURCE_NEGATIVE:
<status>

FRESH_CLONE_EXACTNESS:
<status>

OPTIONAL_PROJECTION_POLICY:
<status>

OPTIONAL_MISSING_RUNNER_ACCEPTANCE:
<status>

OPTIONAL_AVAILABLE_RUNNER_ACCEPTANCE:
<status>

REQUIRED_FAILURES_STILL_FAIL:
<status>

SUITE_VERSION:
1.0.0-rc.1

COMPONENT_VERSIONS:
BA 2.0.0-rc.3 | Dev 0.4.0-rc.2 | Test 2.0.0-rc.11

FULL_PUBLIC_CONFORMANCE:
<status + candidate SHA/tree + report path>

FULL_REGRESSION:
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
fix/phase9-public-conformance-portability

WORKTREE:
CLEAN

RECOMMENDED_PHASE_9_STATUS:
VERIFIED_COMPLETE_CANDIDATE | NOT_READY
```

A PASS report is not permission to merge. Independent remote review remains required.
