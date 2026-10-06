# Kit catalog

The suite combines three role Kits with the shared Project Foundation capability. Machine manifests own versions and package contracts: [suite](../tooling/sdlc-suite.json), [BA](ba/kit.yaml), [Dev](dev/kit.yaml), [Test](test/kit.yaml).

| Component | Current version | Responsibility and boundary | Start here |
|---|---|---|---|
| BA Kit | 2.0.0-rc.6 | Owns business WHAT through APPROVED_BASELINE and Engineering Handoff | [BA guide](../docs/vi/BA_KIT_WORKFLOW.md) · [package README](ba/README.md) |
| Dev Kit VNext | 0.4.0-rc.4 | Owns engineering impact, repository scope, technical decisions, implementation; hands off at READY_FOR_TEST | [Dev guide](dev/README.md) · [workflow](../docs/vi/DEV_KIT_WORKFLOW.md) |
| Test Kit Manual + Automation + Execution VNext | 2.0.0-rc.14 | Owns approved Design/Testcases, automation readiness, execution, Finding classification, retest, and Tester verification | [Test README](test/README.md) · [Manual](../docs/vi/TEST_KIT_QUICKSTART.md) |
| Project Foundation | Shared capability; not a role Kit | Recovers or bootstraps project context and routes owned evidence for review | [Foundation workflow](../docs/project-foundation.md) |

## Lifecycle boundary

~~~
Foundation → BA → Engineering Handoff → Dev → READY_FOR_TEST
→ Test Design → APPROVED_DESIGN → Testcases → APPROVED_TESTWARE
→ Automation → EXECUTION_READY → Execution → Findings
→ Dev fix where applicable → READY_FOR_RETEST → Tester VERIFIED / REOPENED
→ separate Human merge / release decision
~~~

Manual Test, Automation, and Execution are separate Test lanes. APPROVED_TESTWARE does not authorize execution, EXECUTION_READY does not prove a passing run, and Dev does not issue VERIFIED.

## Install

Use [Installation](../docs/en/INSTALLATION.md) for prerequisites, Kit-specific commands, Doctors, upgrades, and recovery. Project Foundation has its own Shared runtime installation and review-only CLI; it does not create Human receipts.

## Compatibility and history

Older BA/Test/Dev material is labeled LEGACY_COMPAT or HISTORICAL. It is not current default guidance. See [Legacy and history](../docs/LEGACY_AND_HISTORY.md).
