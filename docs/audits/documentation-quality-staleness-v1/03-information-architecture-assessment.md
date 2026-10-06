# Information architecture assessment

## Newcomer questions

| Question | Assessment | Evidence and gap |
|---|---|---|
| What is this framework? | PARTIAL | README.md introduces Agent Skills Kits and Project Foundation, then focuses on BA and Test. It does not define the current suite identity or full integrated lifecycle. |
| Who is it for? | PARTIAL | Role-specific BA, Dev and Test guides imply the users, but no suite-level audience statement exists at an entry point. |
| What problem does it solve? | PARTIAL | Individual Kit capability pages explain local value; the cross-kit coordination and evidence problem is not stated once. |
| What is the high-level lifecycle? | FAIL | docs/en/ARCHITECTURE.md, docs/vi/ARCHITECTURE.md and both BA workflow pages show Dev as planned and Test V1/STOP_V1. Current detailed flow is distributed across later Test pages and the unindexed suite contract. |
| What are BA / Dev / Test Kits? | PARTIAL | BA and Test have entry pages. Dev has a strong kits/dev/README.md, but kits/README.md says planned and primary indexes do not link the Dev page. |
| What is Project Foundation? | PASS | README.md links docs/project-foundation.md and the skill; modes, ownership, output classes, review boundary and invocations are described. |
| How do I install it? | PARTIAL | BA and Test commands are present; Dev/Shared is separately installed. There is no suite installation map or package upgrade procedure. Windows Test package byte requirements are missing. |
| What do I run first? | PARTIAL | BA and Test quickstarts say where to begin. Dev and Foundation starts are not routed from a current suite entry point. |
| What requires Human approval? | PASS | BA/Test workflows bind approval to exact receipts and trusted host authentication; Dev specifies conditional technical gates. |
| What does Doctor mean? | PARTIAL | Per-kit READY/DEGRADED/FAIL scopes are described. Suite Doctor and the conformance OPTIONAL_DEGRADED report field lack an operator runbook. |
| What does READY mean? | PARTIAL | Several kits explain package readiness, but the terms vary by Doctor and the shared contract adds an un-emitted READY_TO_MERGE row. |
| What does VERIFIED mean? | PASS | Test Execution VNext states Tester ownership, required execution/retest evidence, and that Dev cannot close a defect. |
| How do BA / Dev / Test hand off? | PARTIAL | Exact handoff contracts are detailed, but current architecture pages show obsolete stage relationships. |
| How do automation and execution work? | PASS | Test Automation V1 and Test Execution VNext explain repository ownership, revisions, execution, findings, defect routing, retest and verification. |
| How do I troubleshoot? | PARTIAL | Packaging lists error codes and installation pages describe some failures, but no single recovery map connects diagnostic to safe next action. |
| What is legacy/historical? | PARTIAL | Test V1 examples and design folders are labelled. Delivery Manifest V2 and BA RC1 provenance/history need stronger labels. |
| What version am I reading? | PARTIAL | Kit pages show versions but primary README and kits/README conflict with current manifests. No suite version is surfaced in the entry pages. |
| How do I run Public Cross-Kit Conformance? | PARTIAL | docs/vi/SDLC_SUITE_CONTRACT.md has the command and prerequisites, but no primary README or release page links it. |
| What optional dependencies exist? | PARTIAL | XMind/Excel and Dev optional services are listed locally; OPTIONAL_DEGRADED is not explained for conformance output. |

## Entry points and navigation

- Root README.md is the strongest start page, but its Kit status table is stale and does not link to Dev guidance or Public Cross-Kit Conformance.
- docs/vi/README.md and docs/en/README.md are organized around BA and Test. Neither routes a reader to the current Dev guides or suite release gate.
- kits/README.md is a competing entry point with obsolete BA 1.0.0-rc.1, Dev planned, and Test V1.1 claims.
- kits/dev/README.md contains usable Dev instructions, but it is not linked from the primary indexes.
- docs/vi/SDLC_SUITE_CONTRACT.md contains the release command but is not indexed from README or release docs.
- docs/DELIVERY_MANIFEST_V2.md is both unindexed and presented without the current deferred status.
- The 89 inventory ORPHAN labels include 10 actionable first-party operator/reference surfaces absent from primary indexes, plus historical, evidence, templates, and progressive-disclosure material.

## Duplication and source relationships

The root README, kits/README.md, docs locale indexes, Kit READMEs and architecture pages repeat Kit status and lifecycle. Their values disagree. Current kit versions should be read from kits/*/kit.yaml and tooling/sdlc-suite.json; the prose pages should summarize and link to those authorities.

BA, Dev and Test workflows repeat the Human Gate and READY/VERIFIED boundaries for role-specific use. That repetition is useful when it links to one canonical authority explanation. The current state is not linked: old architecture prose competes with accurate operator guides.

There is no consolidated concept-to-task route from suite overview to role guide, task procedure, prerequisites, result interpretation and recovery. Operator-versus-maintainer instructions are mostly separate by directory, but the primary indexes do not expose that separation.

## Recommended disposition

Keep the detailed Kit guides and machine contracts. Add one suite entry that names the exact current suite/version and routes to a canonical lifecycle, role guides, install map, release gate, compatibility matrix and troubleshooting index. Replace only the stale summaries after Human review. Keep historical benchmark/design material labelled and separately indexed.
