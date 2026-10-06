# Task-based usability assessment

Status definitions: PASS means a newcomer can follow the documented task and identify its boundary; PARTIAL means key navigation, prerequisite, expected result, or recovery is missing; FAIL means the normal task cannot be completed safely from the documented path.

| Journey | Status | Evidence and reason |
|---|---|---|
| Install framework | PARTIAL | BA/Test and separate Dev/Shared commands exist; no suite install map; Windows Test checkout prerequisite is missing. docs/vi/INSTALLATION.md, docs/en/INSTALLATION.md, DOC-P1-001. |
| Run Doctor | PARTIAL | Per-kit Doctor scopes/statuses are explained; standalone Suite Doctor and its expected result are not routed from the main docs. docs/vi/INSTALLATION.md, kits/test/README.md, docs/vi/SDLC_SUITE_CONTRACT.md. |
| Bootstrap Project Foundation | PASS | Modes, topology/policy prerequisites, commands, runtime paths and Human stop point are documented. docs/project-foundation.md, project-foundation/SKILL.md. |
| Run brownfield recovery | PASS | BROWNFIELD_RECOVERY evidence labels, run command, UNKNOWN handling, review package and Human boundary are documented. docs/project-foundation.md. |
| Start BA feature | PASS | Quick Start identifies earliest safe checkpoint, input review, current-system discovery and clarification. docs/vi/BA_KIT_QUICKSTART.md. |
| Approve BA baseline | PASS | Exact candidate and trusted-host receipt are required; workflow stops at HUMAN_REVIEW. docs/vi/BA_KIT_WORKFLOW.md, ba-workflow/references/human-gate.md. |
| Create Engineering Handoff | PASS | Exact approved baseline proof, source hashes, and revalidation are required. docs/vi/BA_KIT_QUICKSTART.md, ba-workflow/references/engineering-handoff.md. |
| Start Dev Feature Delivery | PARTIAL | Detailed Start Request, authority, repository bases, Impact and plan steps exist, but Dev is undiscoverable from primary indexes and has no English counterpart. kits/dev/README.md, docs/vi/DEV_KIT_WORKFLOW.md. |
| Handle upstream business gap | PASS | raise-gap, UPSTREAM_GAP, Human/BA resolution and replacement Handoff are documented. docs/vi/DEV_KIT_WORKFLOW.md, docs/vi/DEV_KIT_ROUTING.md. |
| Create Test Design | PASS | Exact BA authority intake, pinned TEA, validation and DESIGN_REVIEW steps are documented. docs/vi/TEST_KIT_QUICKSTART.md. |
| Approve Test Design | PASS | Exact snapshot/refs and trusted Human receipt create APPROVED_DESIGN; validator PASS does not approve. docs/vi/TEST_KIT_WORKFLOW.md. |
| Create Testcases | PASS | Exact approved Design refs, pinned Katalon, UNKNOWN preservation and dependency rules are documented. docs/vi/TEST_KIT_QUICKSTART.md. |
| Approve Testware | PASS | Human Case Gate binds testcase snapshot/inputs and creates APPROVED_TESTWARE. docs/vi/TEST_KIT_WORKFLOW.md. |
| Plan Automation | PASS | Suitability, ownership, disposition and Automation Plan are detailed. docs/vi/TEST_AUTOMATION_V1.md. |
| Implement Automation | PASS | Repository identity, committed HEAD, path scope, review, verification and replan conditions are documented. docs/vi/TEST_AUTOMATION_V1.md. |
| Reach EXECUTION_READY | PASS | Exact testware, Dev READY_FOR_TEST, revisions, dependencies, review and automation verification requirements are listed. docs/vi/TEST_AUTOMATION_V1.md. |
| Execute tests | PASS | Environment, immutable manifest, command argv, observations, stale revision stop and manual execution are documented. docs/vi/TEST_EXECUTION_VNEXT.md. |
| Classify Finding | PASS | Tester-only classifications and evidence conditions are explicit. docs/vi/TEST_EXECUTION_VNEXT.md. |
| Route DEFECT | PASS | DEFECT routes to Dev; other categories route upstream/Test/Environment and do not close the attempt. docs/vi/TEST_EXECUTION_VNEXT.md. |
| Perform Dev Fix | PASS | Dev uses FEATURE_DELIVERY with original BA authority and failed app SHAs; fix evidence is bounded. docs/vi/TEST_EXECUTION_VNEXT.md, docs/vi/DEV_KIT_WORKFLOW.md. |
| Create READY_FOR_RETEST | PASS | Exact target/base, coverage, review and fresh verification are required. docs/vi/TEST_EXECUTION_VNEXT.md. |
| Tester retest | PASS | Tester repeats the approved failed case at fixed app/automation revisions; FAIL reopens the same defect lineage. docs/vi/TEST_EXECUTION_VNEXT.md. |
| Reach VERIFIED | PASS | Clean pass/retest evidence and trusted Tester ownership are stated; Dev cannot close the defect. docs/en/TEST_EXECUTION_VNEXT.md, docs/vi/TEST_EXECUTION_VNEXT.md. |
| Run Public Cross-Kit Conformance | PARTIAL | Exact command, Spec Kit pin, clean candidate and output are documented, but the guide is unindexed; no release page points to it. docs/vi/SDLC_SUITE_CONTRACT.md. |
| Handle optional XMind/Excel degradation | PARTIAL | Test Doctor DEGRADED and optional projections are explained; conformance OPTIONAL_DEGRADED is not. docs/vi/TEST_KIT_QUICKSTART.md; DOC-P3-001. |
| Diagnose package authority mismatch | FAIL | Packaging lists error names and integrity domains, but there is no recovery sequence; the tested Windows source validation fails under core.autocrlf=true. tooling/PACKAGING.md, DOC-P1-001 and DOC-P2-005. |
| Handle dirty/stale repository | PARTIAL | Conformance requires a clean exact commit and says stale reports must be rerun; it does not provide a complete clean/commit/re-run decision tree. docs/vi/SDLC_SUITE_CONTRACT.md. |
| Upgrade / verify package version | PARTIAL | Manifests/Doctor and reinstall are described, but no upgrade path explains supported version selection, local drift, post-upgrade verification or rollback. docs/vi/INSTALLATION.md, docs/en/INSTALLATION.md, kits/test/README.md. |

## Journey summary

The BA and Test production paths are documented in enough detail to follow their Human Gates and handoffs. The main failures sit before and after those procedures: installing the integrated suite, finding Dev/conformance guidance, interpreting optional degradation, and recovering from package/version problems.
