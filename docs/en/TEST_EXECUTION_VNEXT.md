# Test Execution / Finding / Defect / Retest VNext

Phase 8 extends Test Kit after Manual VNext and Test Automation V1. Its only production entry is the exact Phase 7 `EXECUTION_READY` handoff, revalidated by the installed Automation V1 runtime.

## Bind before execution

Create a canonical V1 Environment Descriptor and an immutable Execution Manifest. Bind the exact Approved Testware, Automation Plan, Dev `READY_FOR_TEST` evidence, every application repository ID and Git SHA, automation repository identity and committed SHA, and sanitized environment references. Do not persist credentials, absolute machine paths, or expected-result prose.

Before and after each command and retest, revalidate authority bytes, environment refs, clean worktrees, exact application SHAs, and exact automation SHA. Drift stops the attempt as `EXECUTION_STALE`.

## Execute and observe

For `TEST_AUTOMATION`, run only the exact Automation Plan `execution_command` argv from the exact automation repository with `shell=False`. Immutable command evidence binds testcase refs, all repository revisions, environment, timestamps, exit code, and stdout/stderr hashes. A failing command is evidence, not an automatic Defect.

For `MANUAL_ONLY`, create no automation command; an authenticated Tester records the Observation. For `DEV_LOCAL_REFERENCE`, reuse the exact Dev evidence already bound to `EXECUTION_READY`. Optional blocked cases remain visible and never count as PASS.

Automated and manual work use one Observation contract. `oracle_ref` and `oracle_locator` point to the exact approved Testcase; `actual_summary` contains observed evidence only. Automated PASS requires `COMMAND_PASS`. Any FINDING Observation creates a durable Finding.

## Classify and route

Only a trusted Tester classifies a Finding, using exactly:

| Classification | Route |
| --- | --- |
| `DEFECT` | Dev |
| `SPEC_GAP` | Upstream |
| `BUSINESS_DECISION_REQUIRED` | Upstream |
| `TEST_ISSUE` | Test |
| `ENVIRONMENT_ISSUE` | Environment |

DEFECT requires the exact approved oracle, mismatch evidence, reproducibility and deterministic evidence, environment root cause exclusion, supported exclusion of a test/automation issue, and explicit application targets from the project topology. A nonzero exit alone is insufficient. Non-DEFECT routes cannot close the current attempt; corrected upstream artifacts must produce a new valid `EXECUTION_READY` and a new attempt.

## Verify and retest

When every required automated/manual Testcase has a PASS Observation, current Dev-local evidence is accounted for, and no Finding remains open, a trusted Tester can produce a durable `VERIFIED` Handoff. No retest is required for this clean initial pass.

For DEFECT, Phase 8 creates `DEFECT_READY_FOR_DEV`. Dev uses its existing `FEATURE_DELIVERY` flow with `change_id` equal to the stable defect ID and the original BA Engineering Handoff as WHAT authority. Defect artifacts are read-only context. After canonical Dev VNext validation, exact failed repository bases, a targeted repository change, clean non-target repositories, valid coverage, passing review and fresh verification, Phase 8 creates `READY_FOR_RETEST`.

The Tester retests the original failed approved Testcase at the exact fixed app SHAs, original automation SHA, and bound environment. PASS becomes `VERIFIED`; FINDING becomes `REOPENED` with the same defect ID and lineage. Dev cannot close a defect.

## Boundaries

Doctor remains package/capability diagnostics. Its READY status does not mean `EXECUTION_READY`, PASS, no Finding, `READY_FOR_RETEST`, `VERIFIED`, or merge readiness. Delivery Manifest remains deferred and non-authoritative. Legacy execution code is compatibility-only. Phase 8 does not merge product code or create `READY_TO_MERGE`.

The host authenticates Tester actors through a trusted callback receiving the actor ID, requested role/action, and artifact hash. The runtime API exposes `start`, `execute_automated`, `execution_manifest`, `read_artifact`, Observation and classification recording, Dev-fix acceptance, retest, final verification, and VERIFIED revalidation.
