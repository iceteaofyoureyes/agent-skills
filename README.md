# Agent-Assisted SDLC Framework

An agent-assisted workflow for teams that need traceable requirements, bounded engineering work, approved testware, execution evidence, and Human-owned decisions. It serves Project Owners, Tech Leads, BAs, Developers, Testers, Automation Testers, and maintainers.

## Current candidate

Machine-readable manifests own suite identity and package versions: [suite manifest](tooling/sdlc-suite.json) and [acceptance contract](tooling/sdlc-suite-acceptance.yaml).

| Component | Current identity | Responsibility |
|---|---|---|
| Suite | agent-assisted-sdlc-vnext 1.0.0-rc.4 · INTERNAL_RC_CANDIDATE | Integrated contracts and cross-Kit compatibility |
| Project Foundation | Shared SDLC capability | Bounded project context, recovery, bootstrap, and refresh |
| BA Kit | 2.0.0-rc.6 | Business WHAT and approved Engineering Handoff |
| Dev Kit VNext | 0.4.0-rc.4 | Engineering impact, ownership, technical decisions, implementation HOW |
| Test Kit VNext | 2.0.0-rc.14 | Manual testware, automation readiness, execution, Findings, and retest evidence |

These are internal prerelease candidates, not a stable release.

## Lifecycle

~~~
Project Foundation
→ BA
→ UX / Interaction Contract when required
→ Engineering Handoff
→ Engineering / Dev → READY_FOR_TEST
→ Test Design → APPROVED_DESIGN
→ Testcases → APPROVED_TESTWARE
→ Automation Plan → implementation/review → EXECUTION_READY
→ Execution → Observation → Finding classification
→ Dev Fix where applicable → READY_FOR_RETEST
→ Tester retest → VERIFIED or REOPENED
→ separate Human merge / release decision
~~~

Project Foundation supplies project context; it is not a fourth role Kit or business approval. BA owns WHAT. Engineering owns WHERE, WHO OWNS, and HOW. Test proves approved behavior. The Human retains final semantic authority.

CONTINUE, ANSWER, validator PASS, generation, and Doctor readiness never mean approval. READY_FOR_TEST is a Dev handoff. APPROVED_TESTWARE is not execution readiness. EXECUTION_READY is not a passing run. Only the Tester can issue VERIFIED after required evidence and retest.

## Choose a starting point

- New team member: [Vietnamese suite index](docs/vi/README.md) · [English suite index](docs/en/README.md)
- Project Owner / Tech Lead: [Project Foundation](docs/project-foundation.md) · [architecture and lifecycle](docs/en/ARCHITECTURE.md) · [readiness terms](docs/en/READINESS_STATES.md)
- BA: [BA Kit workflow](docs/vi/BA_KIT_WORKFLOW.md) · [English guide](docs/en/BA_KIT_WORKFLOW.md)
- Developer: [Dev Kit VNext](kits/dev/README.md) · [Vietnamese operator guides](docs/vi/DEV_KIT_WORKFLOW.md) · [English Dev guide](docs/en/DEV_KIT_GUIDE.md)
- Tester / QA: [Manual Test](docs/vi/TEST_KIT_QUICKSTART.md) · [English overview](docs/en/TEST_KIT_MANUAL.md)
- Automation Tester: [Automation](docs/en/TEST_AUTOMATION_V1.md) · [Vietnamese guide](docs/vi/TEST_AUTOMATION_V1.md)
- Maintainer: [Installation](docs/en/INSTALLATION.md) · [Troubleshooting](docs/en/TROUBLESHOOTING.md) · [Packaging reference](tooling/PACKAGING.md) · [Release status](docs/en/RELEASE.md)

The [Kit catalog](kits/README.md) lists current roles and entry points. Installation differs by capability; start at [English Installation](docs/en/INSTALLATION.md) or [Cài đặt](docs/vi/INSTALLATION.md).

## Public Cross-Kit Conformance

Every internal candidate must pass [Public Cross-Kit Conformance](docs/en/SDLC_SUITE_CONTRACT.md) on its exact clean commit from a fresh clone. It exercises Foundation through verification, including defect/retest and straight-pass paths. PASS is evidence for review; it does not authorize merge or release.

## Current, compatible, and historical material

Current operator guidance is indexed above. LEGACY_COMPAT material supports explicit read-only compatibility. HISTORICAL material records prior decisions or experiments. Delivery Manifest V2 is DEFERRED_NON_AUTHORITATIVE and is not required by the current lifecycle. See [Legacy and history](docs/LEGACY_AND_HISTORY.md).

Human review is the next gate for this internal RC candidate. A conformance PASS does not authorize merge, tag, GitHub Release, or stable release.
