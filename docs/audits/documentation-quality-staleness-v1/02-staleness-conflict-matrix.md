# Staleness and conflict matrix

The matrix records context-qualified findings. A matching string in benchmark or legacy evidence is not treated as a current defect. Highest severity is P1. No P0 Human-authority or synthetic TEST_ONLY misuse was found.

## Findings

### DOC-P1-001 — Windows Test package source validation fails under core.autocrlf=true

- Severity / category: P1 — package integrity and installation.
- Paths / evidence: .gitattributes lines 1-53; kits/test/kit.yaml; kits/test/package-authority.json; tooling/lib/package.py lines 139-157; tooling/lib/ba_kit.py lines 561-566; tooling/public_conformance.py lines 160-163; docs/en/INSTALLATION.md; docs/vi/INSTALLATION.md.
- Current behavior: the Test authority and payload pins match the committed LF bytes. In this Windows checkout, core.autocrlf=true converts 40 manifest-selected files to CRLF. validate_source_package_integrity then fails before Test installation. The normalized LF hashes match the authority. Public conformance explicitly configures core.autocrlf=false for its fresh clone; the ordinary Windows install instructions do not state that prerequisite.
- Expected truth: raw package bytes must match the checked-in authority; the user-facing Windows install path must arrive at bytes accepted by that authority.
- Risk / affected roles: a normal documented Test Kit installation from a Windows checkout can stop at package validation. Framework maintainer and Tester/QA installation journeys are affected.
- Recommended disposition: in a future authorized remediation, close the EOL policy for every manifest-selected file or otherwise make source resolution honor the committed package bytes; document and verify the supported Windows checkout path. Regenerate authority/digest only through repository tooling and rerun installed acceptance, Doctor, and fresh-clone conformance.
- Confidence: HIGH. Direct source validation failed at the exact audited SHA; 40 working files show CRLF and their LF-normalized hashes match authority entries.

### DOC-P2-001 — Primary pages describe old kit status and lifecycle

- Severity / category: P2 — stale default / competing current guidance.
- Paths / evidence: README.md lines 84-86 and 133; kits/README.md lines 7-9 and 17-19; docs/en/ARCHITECTURE.md lines 76-87; docs/vi/ARCHITECTURE.md lines 79-91; docs/en/BA_KIT_WORKFLOW.md lines 60-62; docs/vi/BA_KIT_WORKFLOW.md lines 61-63; docs/vi/RELEASE.md line 25.
- Current behavior: these pages call Dev planned, Test V1, or describe the downstream Dev/Test flow as planned or historical. The root README also gives Test 2.0.0-rc.7. The current manifests are BA 2.0.0-rc.3, Dev 0.4.0-rc.2, Test 2.0.0-rc.11; Dev V2 and Test Automation/Execution VNext are implemented. Current Test docs use APPROVED_TESTWARE, EXECUTION_READY, VERIFIED and Phase 9 conformance.
- Expected truth: suite and kit manifests identify the current versions and release status; current overview describes the integrated lifecycle and distinguishes historical phases.
- Risk / affected roles: every newcomer and owner can choose the wrong Kit or stop at the obsolete Test V1 boundary.
- Recommended disposition: replace these status summaries with one manifest-derived suite overview; label dated V1 architecture and BA RC1 history as historical.
- Confidence: HIGH.

### DOC-P2-002 — Current Dev and release-gate guides are absent from primary navigation

- Severity / category: P2 — information architecture / workflow discoverability.
- Paths / evidence: README.md Kit table and links around lines 83-141; docs/en/README.md; docs/vi/README.md; kits/README.md lines 7-13; docs/vi/SDLC_SUITE_CONTRACT.md; kits/dev/README.md.
- Current behavior: the primary indexes link BA and Test guides but not kits/dev/README.md, the Dev role guides, or the Public Cross-Kit Conformance instructions. kits/README.md says Dev is planned. The mandatory Phase 9 release gate exists only in an unindexed Vietnamese contract page.
- Expected truth: a newcomer and release owner can find the current suite, role routing, and required public conformance command from a primary entry point.
- Risk / affected roles: Developers cannot discover their current workflow from the main docs; maintainers may not discover the required release gate.
- Recommended disposition: add a suite Start Here page and link Dev, Foundation, release/compatibility, and conformance guides from language indexes.
- Confidence: HIGH.

### DOC-P2-003 — Delivery Manifest V2 reads as active authority despite deferred status

- Severity / category: P2 — competing authority / stale default.
- Paths / evidence: docs/DELIVERY_MANIFEST_V2.md lines 1-3 and 40-46; tooling/sdlc-suite.json lines 33-37; docs/vi/SDLC_SUITE_CONTRACT.md line 5; current Test Kit README and workflow.
- Current behavior: the unindexed design page explains Delivery Manifest V2 in present tense and includes superseded BA/Dev/Test package versions. It does not label the manifest DEFERRED_NON_AUTHORITATIVE. The suite manifest and current kit guides explicitly defer it.
- Expected truth: Delivery Manifest is not a current suite prerequisite or authority.
- Risk / affected roles: a maintainer or operator who finds this page may require the manifest or treat it as current authority.
- Recommended disposition: label this page as historical/compatibility design, add the deferred status at its entry, and link only as reference where needed.
- Confidence: HIGH.

### DOC-P2-004 — READY_TO_MERGE appears in a normative readiness table

- Severity / category: P2 — readiness terminology conflict.
- Paths / evidence: docs/en/SHARED_SDLC_CONTRACTS_V1.md lines 207-221; current suite, Dev, and Test schemas.
- Current behavior: the table defines READY_TO_MERGE as a readiness claim. The next lines say it creates no alternate lifecycle or Human Gate and no state grants Human approval. Current machine contracts emit no READY_TO_MERGE lifecycle state; the suite contract instead says a conformance PASS does not authorize merge.
- Expected truth: no framework lifecycle authority state named READY_TO_MERGE exists; merge/release follows the separately owned Human decision.
- Risk / affected roles: maintainer and Tech Lead may interpret a conceptual row as a framework-issued merge state.
- Recommended disposition: remove the pseudo-state from the normative readiness vocabulary or mark it explicitly as non-framework, non-emitted terminology.
- Confidence: HIGH; the nearby caveat reduces severity below P1.

### DOC-P2-005 — Upgrade and package-recovery journeys lack a complete operator path

- Severity / category: P2 — troubleshooting and task usability.
- Paths / evidence: docs/en/INSTALLATION.md; docs/vi/INSTALLATION.md; docs/en/RELEASE.md; docs/vi/RELEASE.md; tooling/PACKAGING.md lines 14-18 and 44-48.
- Current behavior: install/reinstall and Doctor commands are documented, and the packaging reference lists error codes. No end-to-end upgrade procedure explains selecting a supported source revision, comparing installed version/authority, handling modified managed files, recovering an authority mismatch, or deciding when a fresh install is needed. The suite conformance guide says a dirty/stale candidate must be rerun but does not give a recovery sequence.
- Expected truth: an operator can upgrade/verify a package and recover normal Doctor or stale-revision failures without oral maintainer guidance.
- Risk / affected roles: New Team Member, Tester, Developer, and Maintainer.
- Recommended disposition: add a concise upgrade and recovery guide with safe diagnostics and expected outcomes; keep hash regeneration maintainer-only.
- Confidence: MEDIUM.

### DOC-P2-006 — Historical benchmark transcript contains local paths and username

- Severity / category: P2 — privacy and release hygiene.
- Paths / evidence: benchmark/test-kit/petclinic/foundation-v1-native-profiled/raw-output/invocation.jsonl, including lines 33-35 and 146-171; the surrounding manifest identifies a dated historical benchmark run.
- Current behavior: the tracked raw transcript contains D:\\AI repository/workspace paths and C:\\Users\\LENOVO paths. It is benchmark evidence rather than a current/default example, but the local account name and machine paths are still present in distributable history.
- Expected truth: published evidence should retain reproducibility details without exposing unnecessary local account names or absolute machine paths.
- Risk / affected roles: repository maintainer/distributor; no credentials were observed in the inspected path snippets.
- Recommended disposition: review whether a redacted evidence projection can preserve provenance while the original remains under the project’s chosen retention policy. Do not silently rewrite historical evidence.
- Confidence: HIGH that paths exist; MEDIUM on privacy impact.

### DOC-P2-007 — Developer guidance has no English counterpart

- Severity / category: P2 — VI/EN parity and role usability.
- Paths / evidence: docs/vi/DEV_KIT_WORKFLOW.md, DEV_KIT_USAGE_GUIDE.md, DEV_KIT_ROUTING.md, DEV_KIT_REVIEW_AND_VERIFICATION.md, DEV_KIT_CAPABILITIES.md, DEV_KIT_PROVENANCE.md; docs/en/README.md; docs/vi/README.md.
- Current behavior: the detailed Dev VNext operator guides are Vietnamese-only and absent from the English index. The English index covers BA and a Test overview, while the Vietnamese index says English docs are semantically equivalent.
- Expected truth: an English-speaking Developer can find the same prerequisites, inputs/outputs, gates, forbidden actions, next transition, and recovery guidance.
- Risk / affected roles: Developer, Tech Lead, and Framework Maintainer.
- Recommended disposition: add equivalent English Dev role/task guides or correct the parity claim and publish a clear language coverage map.
- Confidence: HIGH.

### DOC-P3-001 — OPTIONAL_DEGRADED is not explained for conformance output

- Severity / category: P3 — terminology / expected result.
- Paths / evidence: tooling/public_conformance.py lines 218-234 and 340-344; docs/vi/SDLC_SUITE_CONTRACT.md line 21; docs/vi/TEST_KIT_QUICKSTART.md line 29.
- Current behavior: Test Doctor DEGRADED and its optional XMind/Excel meaning are documented. The conformance report’s OPTIONAL_DEGRADED status is not named or explained in operator docs.
- Expected truth: operators know that optional projection degradation can coexist with core readiness and a passing suite result.
- Risk / affected roles: Maintainer and Automation Tester reading a conformance report.
- Recommended disposition: explain the field, its allowed reasons, and how it relates to Suite Doctor and final PASS.
- Confidence: HIGH.

### DOC-P3-002 — Optional skill routing contains 15 unresolved local links

- Severity / category: P3 — broken local navigation / missing optional skill references.
- Paths / evidence: product-design-and-ux/SKILL.md and references/engineering-handoff.md; web-accessibility/SKILL.md and references/routing.md.
- Current behavior: these pages link to absent sibling paths for product-discovery, product-methodology, spec-driven-development, hugo-theme, react, and vite. The references may target separately installed skills, but the repository pages present them as local links and provide no alternate URL/install route.
- Expected truth: a local link resolves inside the repository, or the page identifies the external optional skill source and recovery path.
- Risk / affected roles: BA, UX designer, accessibility reviewer.
- Recommended disposition: convert each link to a real bundled target or an explicit external dependency/reference with availability conditions.
- Confidence: HIGH that local targets are absent; MEDIUM on whether those skills are installed separately.

### DOC-P3-003 — Appointment scenario is not labelled as an illustrative sample

- Severity / category: P3 — example neutrality / genericity.
- Paths / evidence: docs/en/DIAGRAMS_PROTOTYPES.md lines 25-37 and docs/vi/DIAGRAMS_PROTOTYPES.md lines 25-38; the current BA example is Resource Request Submission at kits/ba/examples/CR-001/README.md; Test Kit explicitly labels its Appointment CR-001 example as historical V1.
- Current behavior: the diagram guide presents an Appointment lifecycle without saying it is synthetic or a sample. Appointment also appears in historical PetClinic/Test material, which can make it look like the current default domain.
- Expected truth: readers distinguish neutral examples from project-specific or historical evidence.
- Risk / affected roles: BA and newcomer.
- Recommended disposition: label the scenario as illustrative or align it with the current neutral example.
- Confidence: MEDIUM.

### DOC-P3-004 — Readiness terms are not collected with owner and next transition

- Severity / category: P3 — terminology/reference usability.
- Paths / evidence: docs/en/SHARED_SDLC_CONTRACTS_V1.md readiness table; docs/project-foundation.md; docs/vi/DEV_KIT_WORKFLOW.md; docs/vi/TEST_KIT_WORKFLOW.md; docs/vi/TEST_AUTOMATION_V1.md; docs/vi/TEST_EXECUTION_VNEXT.md.
- Current behavior: the individual guides explain many state limits, but no current reference maps READY, DEGRADED, CORE_READY, PROJECT_FOUNDATION_READY, APPROVED_BASELINE, READY_FOR_TEST, APPROVED_TESTWARE, EXECUTION_READY, READY_FOR_RETEST, VERIFIED, REOPENED, and INTERNAL_RC_CANDIDATE to owner, proof, non-proof, and allowed next transition in one place.
- Expected truth: a reader can distinguish package readiness, project readiness, workflow approval, execution readiness, verification, and release status.
- Risk / affected roles: Project Owner, Tech Lead, Tester, Maintainer.
- Recommended disposition: publish a single state/term reference sourced from manifests and schemas; role guides should link to it.
- Confidence: MEDIUM.

### DOC-P3-005 — Provenance pages mix current package facts with an undated BA RC1 audit

- Severity / category: P3 — historical labeling / maintainability.
- Paths / evidence: docs/en/PROVENANCE.md and docs/vi/PROVENANCE.md, headings “BA Kit RC1” and “Audit basis”; the same pages begin with current Test Kit VNext pin/version information.
- Current behavior: old BA candidate branch/SHA and whole-repository publication blockers appear in the same current provenance page without a snapshot date or historical label.
- Expected truth: current package pins and dated historical redistribution analysis are distinguishable.
- Risk / affected roles: Maintainer/distributor.
- Recommended disposition: date and label the BA RC1 section as a historical audit snapshot, then link current provenance to its authoritative lock/notice files.
- Confidence: HIGH.

### DOC-P4-001 — Vietnamese release page repeats the Test candidate version

- Severity / category: P4 — minor duplication.
- Paths / evidence: docs/vi/RELEASE.md lines 5 and 15 repeat 2.0.0-rc.11.
- Current behavior: the same current version is stated twice before the workflow/phase details.
- Expected truth: release identity is stated once and referenced consistently.
- Risk / affected roles: low.
- Recommended disposition: remove the duplicate during an authorized wording pass.
- Confidence: HIGH.

### DOC-P4-002 — Three unresolved local links occur only in legacy/benchmark evidence

- Severity / category: P4 — historical evidence navigation.
- Paths / evidence: benchmark/test-kit/petclinic/fixtures/test-design-v1/inputs/baseline/02-gap-review.md; benchmark/test-kit/petclinic/foundation-v1-native-profiled/inputs/baseline/02-gap-review.md; tooling/tests/fixtures/ba-v1-legacy-compat/02-gap-review.md.
- Current behavior: each links to a sibling 01-input-requirement.md that is not present in that fixture. The benchmark text says the input was not supplied to the Test Design run.
- Expected truth: evidence links resolve or explicitly identify the omitted source.
- Risk / affected roles: Maintainer/evaluator only; not current operator workflow.
- Recommended disposition: preserve the evidence and clarify or repair the reference only if the historical fixture is retained as a navigable document set.
- Confidence: HIGH.

## Finding totals and boundaries

| Severity | Count |
|---|---:|
| P0 | 0 |
| P1 | 1 |
| P2 | 7 |
| P3 | 5 |
| P4 | 2 |

The 10 conflicting documentation surfaces are the eight DOC-P2-001 paths, docs/DELIVERY_MANIFEST_V2.md, and docs/en/SHARED_SDLC_CONTRACTS_V1.md. The P2 navigation and language findings are omissions, not additional conflicting-state counts. A raw relative-link scan found 36 unresolved candidates: 16 are target-project paths in templates, 2 are regex examples misread as links, 15 are absent optional sibling skills, and 3 occur in old evidence/fixtures. Confirmed broken links: 18. Confirmed broken remote URLs: 0. Confirmed unresolved anchors after context review: 0.
