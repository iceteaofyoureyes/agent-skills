# Machine-readable framework truth

Audited source: iceteaofyoureyes/agent-skills at 25d7cb6b5b4685540bce6621fbe245fa67312298. This extraction reads the current manifests, schemas, acceptance contracts, package authority, executable contracts, and source code. Documentation claims do not override these sources.

## Repository and candidate identity

| Item | Current value | Source |
|---|---|---|
| Suite ID | agent-assisted-sdlc-vnext | tooling/sdlc-suite.json |
| Suite version | 1.0.0-rc.1 | tooling/sdlc-suite.json |
| Suite release status | INTERNAL_RC_CANDIDATE | tooling/sdlc-suite.json |
| BA Kit | 2.0.0-rc.3 | kits/ba/kit.yaml |
| Dev Kit | 0.4.0-rc.2; INTEGRATION_CANDIDATE | kits/dev/kit.yaml |
| Test Kit | 2.0.0-rc.11 | kits/test/kit.yaml |
| Delivery Manifest | DEFERRED_NON_AUTHORITATIVE | tooling/sdlc-suite.json and all three kit manifests |

The expected main checkpoint SHA exists and equals freshly fetched origin/main. The audit worktree is detached at that exact SHA. The original workspace is clean at start on fix/phase9-public-conformance-portability, SHA 1a62e1eb4d2cb575090a6eaebf88bcd2d5ee3415; git diff between it and 25d7cb6 is empty. GitHub PR #9 is merged at 25d7cb6. Its body reports the reviewed head as 1a62e1e, a fresh-clone conformance PASS, 718 tests with 7 existing skips, and no release tag. GitHub reports no attached review records or status checks, and the conformance report is not tracked in this repository.

Audit start: 2026-10-06 10:45:32 UTC. Source checkout path: C:\Users\LENOVO\orca\workspaces\agent-skills\main-2. Audit source worktree: C:\Users\LENOVO\AppData\Local\Temp\agent-skills-doc-audit-25d7cb6, detached at the expected SHA. Runtime: Git 2.50.1.windows.1, RTK 0.43.0, Python 3.13.14, Windows PowerShell 5.1.19041.6456.

## Required public contracts

| Contract | Version | Source |
|---|---:|---|
| Project Foundation | 1 | shared/sdlc/schema.py |
| BA Engineering Handoff | 2 | ba-workflow/scripts/ba_vnext.py |
| Dev Handoff | 2 | kits/dev/schemas/dev-handoff-v2.schema.json |
| Approved Testware | 1 | kits/test/schemas/approved-testware-vnext-handoff-manifest.schema.json |
| Execution Ready | 1 | kits/test/schemas/execution-ready-v1-handoff.schema.json |
| Finding Classification | 1 | kits/test/schemas/finding-classification-v1.schema.json |
| Defect Handoff | 1 | kits/test/schemas/defect-handoff-v1.schema.json |
| Ready For Retest | 1 | kits/test/schemas/ready-for-retest-v1.schema.json |
| Verified Handoff | 1 | kits/test/schemas/verified-handoff-v1.schema.json |

tooling.sdlc_suite.compatibility at the audited tree returned PASS with those nine contract versions and all three component versions. This is a manifest/source compatibility check, not a full Doctor or public conformance run.

## Acceptance contracts and release evidence

- Suite acceptance is schema 1, suite version 1.0.0-rc.1, with required tiers A component regression, B suite compatibility/Doctors, C installed public cross-kit flow, and D fresh-clone reproducibility. The result is PUBLIC_CROSS_KIT_CONFORMANCE with PASS or FAIL and an output location outside the source tree. Source: tooling/sdlc-suite-acceptance.yaml.
- Current public command documented for operators: python -m tooling.public_conformance --repo . --output C:\path\outside\repo\phase9-report.json --spec-kit-cli C:\path\to\specify.exe. It requires a clean committed candidate and Spec Kit v1.0.11; the report is written outside the source tree. Source: docs/vi/SDLC_SUITE_CONTRACT.md and tooling/public_conformance.py.
- BA Phase 4 requires Tier 3 fresh-session installed acceptance; lower tiers cannot mark completion. Source: kits/ba/acceptance.yaml.
- Dev Phase 5 requires a Tier 3 fresh installed runtime; lower tiers cannot mark completion. Source: kits/dev/acceptance.yaml.
- Test Phase 6 requires the manual installed-runtime acceptance, Phase 7 requires installed Automation V1 acceptance, and Phase 8 requires installed execution/retest acceptance. Source: kits/test/acceptance.yaml.
- No candidate suite lock is tracked. tooling.sdlc_suite lock writes a caller-selected external lock; public conformance binds the exact commit/tree, manifest hash, component versions, contract versions, Doctors, flow, fresh clone, and tests.
- PR #9 supplies a merged-PR body claim of a successful run, not a retained conformance report or attached GitHub check. The audit did not rerun conformance.

## Package authority and observed integrity

| Package | Authority model | Source |
|---|---|---|
| BA | kit.yaml composition plus installed ownership/version/file records; no durable package-authority.json | kits/ba/kit.yaml and tooling/lib/ba_kit.py |
| Dev | provenance.lock.json pins selected payload hashes; installer writes an install manifest containing version and installed file hashes | kits/dev/provenance.lock.json and tooling/install_dev_kit.py |
| Test | package-authority.json pins 194 managed entries and TEST_KIT_PACKAGE_PAYLOAD_V1 digest; kit.yaml pins authority and payload hashes | kits/test/package-authority.json and kits/test/kit.yaml |

Test package authority SHA-256 b558b870640eee47c4d335f6901c308003cd6a4bb8cc206289f5ca6796ce5c23 matches the manifest authority pin. Payload digest 78394b5d1bb7600a3c09642e35d51f01014bfaec2355417c05ca1c1a0e6123f1 matches its pin. The authority lists 11 operator documentation/example entries.

However, validate_source_package_integrity on this Windows checkout returned “source package-authority.json differs from the resolved package definition.” Git core.autocrlf is true. Forty selected Test payload files were checked out with CRLF while the authority contains hashes of their LF Git blobs; LF-normalized working bytes match the authority hashes. .gitattributes stabilizes some Test paths but omits other manifest-selected files such as kits/test/schemas, kits/test/templates, kits/test/examples, acceptance.yaml, and docs/en|vi Test Automation/Execution guides. Test install calls this validator before copying. The public-conformance fresh-clone code explicitly sets core.autocrlf=false (tooling/public_conformance.py), while the documented ordinary Windows install command does not. This is a confirmed P1 installation/package-integrity finding, not a pin mismatch in the committed Git blobs.

## Doctor and readiness states

| Surface | Current output states | Meaning and limit | Source |
|---|---|---|---|
| BA Doctor | READY, DEGRADED, FAIL | Package/capability closure; no BA approval or feature readiness | tooling/lib/ba_kit.py; docs/en/INSTALLATION.md |
| Dev Doctor | READY, FAIL | PACKAGE/CAPABILITY READY; Spec Kit v1.0.11 is required | tooling/lib/dev_vnext_doctor.py; kits/dev/kit.yaml |
| Test Doctor | READY, DEGRADED, FAIL | Core package/capability and integrity; optional XMind/Excel gaps can degrade | tooling/lib/ba_kit.py; kits/test/kit.yaml |
| Suite Doctor | READY, FAIL | Cross-kit/package/contract compatibility and required runtime checks | tooling/sdlc_suite.py |
| Suite Test readiness projection | CORE_READY or CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE | A Test Doctor DEGRADED result is acceptable only when every failure is an optional projection | tooling/sdlc_suite.py |
| Public conformance optional projection runtime | OPTIONAL_AVAILABLE or OPTIONAL_DEGRADED | XMind projection setup status; does not by itself fail suite status | tooling/public_conformance.py |
| Foundation | PROJECT_FOUNDATION_READY | Foundation evidence/readiness only; not feature or business approval | shared/sdlc/foundation/workflow.py; docs/project-foundation.md |

The operator docs explain READY and DEGRADED for kit Doctors but do not explain the conformance report’s exact OPTIONAL_DEGRADED field.

## Runtime requirements and optional dependencies

- BA installer and validators: Python 3.8+ in the installation guide; BA workflow requires an agent runtime with access to the project.
- Dev runtime: Python 3.10+; GitHub Spec Kit v1.0.11 is required for normal and high-risk operation. Codebase Memory MCP v0.11.0 is optional when blast radius is uncertain. Sources: kits/dev/kit.yaml and docs/vi/DEV_KIT_PROVENANCE.md.
- Test runtime: Python >=3.10, Codex project scope. Pinned TEA and Katalon skills are bundled and do not require a runtime network download. Optional Excel dependencies are openpyxl 3.1.5 and et-xmlfile 2.0.0; optional XMind uses Node >=18, npm >=9, and xmind 2.2.33. Legacy nested Codex invocation is optional. Source: kits/test/kit.yaml and tooling/PACKAGING.md.
- Public Cross-Kit Conformance requires the Spec Kit executable explicitly and pytest in the invoking Python user site for full discovery. Source: docs/vi/SDLC_SUITE_CONTRACT.md and tooling/public_conformance.py.

## Project Foundation, automation ownership, and Findings

- Modes: BROWNFIELD_RECOVERY, GREENFIELD_BOOTSTRAP, FOUNDATION_REFRESH. Profiles: MINIMAL, STANDARD, EXTENDED. The Arc42 profile requires product/architecture, then domain/testing/features, then operations entry points respectively. EXTENDED fails closed when the declared Policy lacks its operations authority. Sources: shared/sdlc/foundation/profiles.py and shared/sdlc/foundation/workflow.py.
- Automation ownership: DEV_LOCAL_REFERENCE reuses exact Dev UNIT/COMPONENT evidence; TEST_AUTOMATION owns CONTRACT, DB_RUNTIME, API, INTEGRATION, E2E, ACCESSIBILITY, and SYSTEM; MANUAL_ONLY remains manual; BLOCKED has no AUT. Required blocked cases prevent EXECUTION_READY. Source: tooling/lib/test_automation_v1.py and docs/vi/TEST_AUTOMATION_V1.md.
- Finding classifications are DEFECT, SPEC_GAP, BUSINESS_DECISION_REQUIRED, TEST_ISSUE, and ENVIRONMENT_ISSUE. Only a trusted Tester classifies; route is constrained by the schema/taxonomy. Source: shared/sdlc/findings/taxonomy.py and kits/test/schemas/finding-classification-v1.schema.json.

## Authority and lifecycle

The executable precedence is Human-approved decisions > Shared SDLC invariants > Project Policy > Kit / skill instructions > Runtime defaults, from shared/sdlc/approvals/invariants.py. The five artifact classes are CANONICAL, DERIVED, RUNTIME, EVIDENCE, HANDOFF_MANIFEST, from shared/sdlc/artifacts/classes.py.

Current lifecycle states verified from manifests, schemas, executable code and current operator guides:

Project Foundation context/readiness → BA DRAFT → VALIDATED → HUMAN_REVIEW → APPROVED_BASELINE → Engineering Handoff VNext → Dev V2 FEATURE_DELIVERY through IMPLEMENTATION_READY / IMPLEMENTING / ENGINEERING_REVIEW / VERIFYING → READY_FOR_TEST → Test Design / APPROVED_DESIGN → Testcases / APPROVED_TESTWARE → Automation V1 / EXECUTION_READY → Execution / Finding classification → DEFECT or upstream/test/environment route → Dev fix → READY_FOR_RETEST → Tester retest → VERIFIED or REOPENED → separate Human merge/release decision.

The exact state sets are in tooling/sdlc-suite.json, kits/dev/kit.yaml, ba-workflow/scripts/ba_vnext.py, shared/sdlc/foundation/workflow.py, tooling/schemas/execution-state.schema.json, and the public Test schemas. READY_TO_MERGE does not appear as a runtime lifecycle or authority state. CONTINUE, ANSWER, validation PASS, generation, Doctor READY, Foundation READY, and Dev READY_FOR_TEST do not create Human approval or Tester verification.

## Human Gate and TEST_ONLY safeguards

BA APPROVED_BASELINE requires an exact host-authenticated Human receipt bound to the candidate/revision/source hashes. Test Design and Case Gate approvals require exact trusted Human receipt checks. Automation verification proves automation structure/runnability only; EXECUTION_READY is a handoff manifest, not a test result. VERIFIED is a Tester-owned handoff requiring exact execution evidence.

Synthetic acceptance authority is isolated: the public schemas mark TEST_ONLY handoffs as test_only and not_for_production; production paths reject TEST_ONLY authority without the designated trusted test-only authenticator. Public Cross-Kit Conformance documents that receipts are TEST_ONLY. The neutral Test examples state that no approved handoff or Human receipt is supplied. No P0 authority misstatement was found in the sampled current operator guidance.

## Audit runtime record

- Repository identity: origin URL https://github.com/iceteaofyoureyes/agent-skills.git.
- Refreshed remote metadata with git fetch origin main; origin/main resolved to the expected SHA.
- Original workspace was clean at start. The detached audit worktree was clean at baseline. The feature workspace SHA 1a62e1e has the same tree as the expected main merge result, with no source diff.
- Commands/checks: Git identity/status/ref/history and PR #9 metadata; suite compatibility extraction; Test package authority pin comparison; source package integrity validation; public conformance --help only; local Markdown link/anchor scan; HTTP HEAD on 58 unique remote links. No unit tests or full conformance run were executed.
- The phase 9 merged-PR body claims a full conformance PASS at tree-equivalent SHA 1a62e1e; exact report artifact and attached GitHub checks were unavailable. Treat that prior pass as PR-body evidence, not a fresh audit run.
