# Resource Reservation: execution and defect retest

This neutral example begins with an exact Test Automation V1 `EXECUTION_READY` handoff. Approved Testcases remain the behavior oracle.

## Straight pass

1. Bind a sanitized test environment and exact application/automation revisions in an immutable Execution Manifest.
2. Run each exact Automation Plan argv command in the declared automation repository. Record manual-only cases directly with a trusted Tester Observation and retain Dev-local evidence refs.
3. Record PASS Observations against exact approved Testcase refs.
4. A trusted Tester creates the durable `VERIFIED` Handoff. No retest is needed for this initial pass.

## Defect and retest

1. A testcase command fails and the Tester records a FINDING Observation. The command failure alone does not create a Defect.
2. The Tester classifies `DEFECT` only with reproducible mismatch evidence, an exact approved oracle, environment/test issue exclusion, and a target repository from topology.
3. Test Kit creates `DEFECT_READY_FOR_DEV`. Dev starts normal `FEATURE_DELIVERY` with the stable defect ID as `change_id`, the original BA Engineering Handoff as WHAT authority, and the failed app SHA as repository base.
4. Dev completes Impact, Plan, Implementation, Review and fresh Verification, commits the targeted fix and returns V2 `READY_FOR_TEST`.
5. Phase 8 validates the exact Dev handoff and creates `READY_FOR_RETEST`.
6. The Tester reruns the original approved testcase at the fixed app SHA, original automation SHA and exact environment. PASS closes as `VERIFIED`; another FINDING creates `REOPENED` with the same defect ID.

The example contains no product-specific expected result and does not use Delivery Manifest as authority.
