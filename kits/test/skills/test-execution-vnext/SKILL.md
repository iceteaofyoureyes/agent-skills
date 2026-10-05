---
name: test-execution-vnext
description: Execute exact Test Automation V1 EXECUTION_READY, record approved-testcase observations, route Findings, accept normal Dev VNext fixes, and close or reopen through Tester retest.
---

# Test Execution / Finding / Defect / Retest VNext

## Authority and entry

Start only from the exact Phase 7 Automation V1 `EXECUTION_READY` handoff. Revalidate it through the installed `test_automation_v1.AutomationRuntime.revalidate_handoff()` path. Do not infer readiness from workflow-state text, a runtime status, Delivery Manifest, automation verification, or current product behavior.

For an explicitly TEST_ONLY conformance run, pass the same trusted `test_only_authority_authenticator` to `ExecutionRuntime`. It revalidates the Test-only authority through Automation V1; the canonical Execution Manifest carries `test_only: true` and `not_for_production: true`. This evidence cannot authorize a production execution.

Create a canonical V1 Environment Descriptor and immutable Execution Manifest before running product tests. Bind every application repository ID to its exact Git SHA, plus the automation repository identity and committed SHA. Keep environment references portable and secret-free. Do not copy expected-result prose into runtime artifacts.

## Execution

- `TEST_AUTOMATION`: invoke only `execution_command` from the exact bound Automation Plan. Use its argv array, the declared automation repository as `cwd`, and `shell=False`. The runtime checks every bound repository revision and cleanliness before and after each command.
- `MANUAL_ONLY`: do not create a command. A trusted host authenticates the Tester who records the Observation against the exact approved Testcase.
- `DEV_LOCAL_REFERENCE`: reuse the exact Dev evidence bound by `EXECUTION_READY`; do not rerun it automatically.
- Optional blocked Testcases remain visible and do not count as PASS.

Every invocation creates immutable command evidence with exit status and output hashes. `COMMAND_FAIL` does not classify a Finding or Defect. One unified Observation binds `oracle_ref` and `oracle_locator` to the exact Approved Testcase. `actual_summary` contains observed evidence only. Automated PASS requires `COMMAND_PASS`.

## Pass and Findings

After all required automated and manual Testcases have PASS Observations, current Dev-local evidence is accounted for and no Finding remains open, an authenticated TESTER may create the durable `VERIFIED` Handoff. Clean initial PASS needs no retest. Dev cannot authenticate final verification.

Every `FINDING` Observation creates a durable Finding. A TESTER classifies it with exactly one of:

```text
DEFECT
SPEC_GAP
BUSINESS_DECISION_REQUIRED
TEST_ISSUE
ENVIRONMENT_ISSUE
```

Routes are `DEFECT → DEV`, `SPEC_GAP` and `BUSINESS_DECISION_REQUIRED → UPSTREAM`, `TEST_ISSUE → TEST`, and `ENVIRONMENT_ISSUE → ENVIRONMENT`. Classification is never inferred from a command exit code or Finding alone; an authenticated Tester explicitly classifies the Finding. DEFECT requires exact approved-oracle evidence, a reproducible mismatch OR exact deterministic mismatch evidence, evidence excluding environment and test/automation causes, and explicit application repository targets from the project topology. Either proof basis is sufficient, and both may be true.

Non-DEFECT routes cannot become VERIFIED in the current attempt. Corrected authority and a new exact `EXECUTION_READY` start a new attempt.

## Dev fix and retest

For DEFECT, create a `DEFECT_READY_FOR_DEV` Handoff with the stable defect ID. The Dev Kit starts its normal `FEATURE_DELIVERY` flow with `change_id = defect_id`, the original Engineering Handoff as WHAT authority, and the failed application SHAs as repository bases. Defect evidence is read-only context. Dev performs Impact, Plan, Implementation, Review and fresh Verification and returns V2 `READY_FOR_TEST`.

Accept that handoff only after canonical Dev VNext validation, exact BA authority and repository bases, at least one targeted revision change, no non-target drift, valid coverage, passing review and fresh verification, and an unchanged automation SHA. Then create `READY_FOR_RETEST`; it is readiness only.

The Tester reruns the original failed approved Testcase at exact fixed application SHAs, unchanged automation SHA and the bound environment. PASS creates final `VERIFIED`; FINDING creates `REOPENED` with the same defect ID and incremented lineage. A reopened defect may enter another normal Dev VNext fix cycle.

## Host and package boundaries

The embedding host supplies Tester authentication through a callback receiving `(actor_id, {role, action, artifact_sha256})`. It returns `{authenticated: true, actor_id, role: "TESTER"}` only after trusted identity verification. Workflow fields do not authenticate actors. The runtime API exposes `start`, `execute_automated`, `execution_manifest`, `read_artifact`, `record_observation`, `classify_finding`, `accept_dev_fix`, `execute_retest`, `record_retest_observation`, `finalize_verified`, and `revalidate_verified`.

Doctor reports package/capability integrity only; READY does not imply execution readiness, PASS, absence of Findings, retest readiness, VERIFIED, or merge readiness. Delivery Manifest stays deferred and non-authoritative. Legacy execution helpers remain compatibility only.
