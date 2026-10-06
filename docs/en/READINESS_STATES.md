# Readiness and authority reference

Executable contracts are in the [suite manifest](../../tooling/sdlc-suite.json), [Shared readiness vocabulary](../../shared/sdlc/readiness/vocabulary.py), [artifact classes](../../shared/sdlc/artifacts/classes.py), [approval invariants](../../shared/sdlc/approvals/invariants.py), and each Kit's manifests/schemas. This page explains operator meaning; it creates no state.

| State | Owner | Proves | Does not prove | Next step |
|---|---|---|---|---|
| READY | Kit Doctor | Required package and capabilities validate | Approval, feature correctness, test pass | Start the Kit workflow |
| DEGRADED | Kit Doctor | Core works while an optional capability is unavailable | That a required integrity failure may be ignored | Install the projection if needed; otherwise use the core path |
| CORE_READY | Suite Doctor / Test runtime | Test core capability is ready | XMind/Excel availability or product PASS | Use Test core; report projection separately |
| CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE | Suite Doctor / Test runtime | Test core is ready; optional projections are unavailable | Suite PASS or product verification | Continue if those projections are not required |
| PROJECT_FOUNDATION_READY | Trusted Foundation workflow | Foundation snapshot meets policy and exact review | Business approval or feature readiness | Route context to BA, Engineering, or Test |
| APPROVED_BASELINE | Human through BA trusted host | Exact WHAT baseline and source snapshot were approved | Technical design or implementation | BA creates Engineering Handoff |
| READY_FOR_TEST | Dev | Dev handoff, implementation checks, and scope are bound | Tester VERIFIED or merge approval | Test consumes the exact handoff |
| APPROVED_DESIGN | Human through Test trusted host | Exact Test Design/coverage snapshot was approved | Testcase approval or execution | Create Testcases |
| APPROVED_TESTWARE | Human through Test trusted host | Exact testcase snapshot and trace were approved | Automation or execution readiness, PASS | Plan Automation or use the manual lane under its contract |
| EXECUTION_READY | Automation workflow | Automation review/verification and execution inputs are bound | That tests ran or passed | Test Execution consumes the exact handoff |
| READY_FOR_RETEST | Dev | Fix handoff binds the defect/oracle and new revisions | Defect closure or verification | Tester retests |
| VERIFIED | Authenticated Tester | Current attempt passed the oracle after execution/retest | Human merge/release decision | End product lifecycle; await separate Human decision |
| REOPENED | Authenticated Tester | Failed retest and defect lineage are recorded | Defect closure | Return to Dev through the same defect |
| INTERNAL_RC_CANDIDATE | Suite manifest / Maintainer | Candidate is an internal prerelease identity | Package acceptance, conformance, merge, or release | Run acceptance, Doctors, conformance; request Human review |
| OPTIONAL_DEGRADED | Public Conformance runner | Optional projection setup is unavailable | Test core failure or final suite FAIL by itself | Report separately; repair when that capability is needed |

Kit Doctor DEGRADED, Test core condition CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE, and conformance OPTIONAL_DEGRADED are different fields and contexts. Final conformance PASS/FAIL is separate. See [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md).

Invariants: CONTINUE != APPROVE; ANSWER != APPROVE; validator PASS != APPROVE; generated != APPROVED; Derived != Authority; Runtime != Authority; CURRENT_SYSTEM != confirmed target; Dev READY_FOR_TEST != Tester VERIFIED; Dev fix != Tester VERIFIED; APPROVED_TESTWARE != EXECUTION_READY; EXECUTION_READY != PASS.

The current lifecycle does not emit READY_TO_MERGE. Merge/release requires a separate Human decision after VERIFIED.
