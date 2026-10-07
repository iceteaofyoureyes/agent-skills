# Documentation Hardening & Internal RC Gate

Status of the remediation candidate: `PASS`; final branch head is the report-only follow-up commit containing this file and is independently rebound by the final exact-candidate conformance run.

## Identity and source of truth

- Repository: `iceteaofyoureyes/agent-skills`
- Required starting `origin/main`: `e4c51a964cfb6b0a929ab81d131d3c823ef7bf98`
- Branch: `docs/full-documentation-hardening-rc-gate`
- Remediation candidate (before this evidence-only report): `78a1bb3ef7085f37cf63f01614e23b3bbd0fdded`
- Remediation tree: `fe738baaf95bf9eacb16dec66bc419dc41d87a86`
- Frozen documentation audit: `audit/documentation-quality-staleness-v1` at `94e7ab7b5a19bb4d4b2a8789b9704a13a21cbc83`, audited against pre-A0 `25d7cb6b5b4685540bce6621fbe245fa67312298`.
- The final branch head includes this report; its exact SHA/tree are emitted by the final Public Cross-Kit Conformance JSON outside the source tree and recorded in the final handoff. The report cannot contain its own commit hash without changing that hash.
- Machine manifests, schemas, runtime and package provenance remain authoritative. No Human approval, business authority, or release semantics were changed.

## Candidate identity and package impact

| Component | Final candidate | Package impact and rationale |
|---|---|---|
| Suite | `1.0.0-rc.4`, `INTERNAL_RC_CANDIDATE` | Advanced because the component tuple changed. |
| BA | `2.0.0-rc.6` | Installed skill payload changed in product-design-and-ux, web-accessibility, and document-docx anchor routing. BA payload: 279 files; SHA-256 `086d77ce565c6e11be922918e3723d8aaf67e2cc8b7933214c8fdcf07c9ea62e`. |
| Dev | `0.4.0-rc.4` | `tooling/lib/dev_vnext.py` now memoizes only positive exact repo/revision/path/digest proofs. Dev provenance regenerated; aggregate SHA-256 `1dbb71e5cc30d40d59580f4b33eb0c9a4c42b9def0b79b6013e812788847581e`. |
| Test | `2.0.0-rc.14` | Packaged README and Dev runtime closure changed. Authority regenerated for 194 managed files; authority SHA-256 `d27013c9f74ee167af04a9c90fe43b7482f44f7d788891eb61e21d0efe840410`; payload SHA-256 `c39ea2710fcf6ef7babcb3f37015d9cd364553a9fbbde99e622c26ae768bcab6`. |

These are unmerged prerelease candidates; no tag or stable release is created. BA, Dev, and Test were bumped only for affected package inputs; Suite was advanced for the new tuple.

## Documentation remediation

- Replaced the root README with the suite landing page, current tuple, authority principle, lifecycle, installation, role routes, conformance and release state. Updated `kits/README.md` to expose BA, Dev VNext, Test Manual + Automation + Execution VNext, and shared Project Foundation.
- Made `docs/vi/README.md` the primary Vietnamese suite index and `docs/en/README.md` the English suite index with truthful `FULL ENGLISH GUIDE`, `ENGLISH OVERVIEW`, and `VIETNAMESE PRIMARY GUIDE` coverage labels.
- Replaced VI/EN architecture pages with the integrated lifecycle, one canonical lifecycle route, and clear role/authority boundaries. BA retains `DRAFT ? VALIDATED ? HUMAN_REVIEW ? APPROVED_BASELINE` and stops at WHAT; downstream routing now points to Engineering/Dev/Test.
- Added English Dev VNext, Project Foundation, Test Manual overview, readiness and troubleshooting guides. Current primary indexes expose all required VI Dev pages and all three Test lanes: Manual, Automation, Execution/Finding/Defect/Retest.
- Hardened install/upgrade/recovery instructions for each Kit, Doctors, managed edits, package authority drift, clean/stale candidates, optional degradation, and supported Windows checkout behavior. `core.autocrlf=false` is not a prerequisite; operators are never told to edit hashes.
- Rewrote VI/EN release pages as suite-level internal candidate status. Updated the current Public Cross-Kit Conformance guide in VI and added its English counterpart with the exact Spec Kit, clean clone, external-output, two-flow, negative-probe, optional-degradation and non-authorization requirements.
- Marked Delivery Manifest V2 visibly `DEFERRED_NON_AUTHORITATIVE`, historical/deferred, non-business authority, and unnecessary to current Foundation ? BA ? Dev ? Test operation.
- Added `docs/LEGACY_AND_HISTORY.md`; dated old Foundation and BA RC1 provenance material; preserved raw benchmark evidence and its local paths as historical-only. Any future shareable projection must redact usernames/home paths while retaining stable repository-relative provenance and hashes.
- Replaced 15 absent optional-sibling links with explicit optional capability guidance; labeled the Appointment diagram sample illustrative; corrected three verified GitHub heading slugs in the packaged document-docx skill; removed phase-only current operator wording.

## Audit disposition

| Finding | Prior severity | Final disposition |
|---|---:|---|
| DOC-P1-001 | P1 | SUPERSEDED_BY_A0 |
| DOC-P2-001 | P2 | CLOSED |
| DOC-P2-002 | P2 | CLOSED |
| DOC-P2-003 | P2 | CLOSED |
| DOC-P2-004 | P2 | SUPERSEDED_BY_A0 |
| DOC-P2-005 | P2 | CLOSED |
| DOC-P2-006 | P2 | HISTORICAL_ACCEPTED |
| DOC-P2-007 | P2 | CLOSED |
| DOC-P3-001 | P3 | CLOSED |
| DOC-P3-002 | P3 | CLOSED |
| DOC-P3-003 | P3 | CLOSED |
| DOC-P3-004 | P3 | CLOSED |
| DOC-P3-005 | P3 | CLOSED |
| DOC-P4-001 | P4 | CLOSED |
| DOC-P4-002 | P4 | HISTORICAL_ACCEPTED |

A0 owns portable Test source bytes and the removal of current `READY_TO_MERGE` vocabulary. No current P0/P1 remains. Current residual counts: P0 0, P1 0, P2 0, P3 0, P4 0. Historical acceptance retains five non-mandatory links only: three omitted fixture inputs and two machine-local links in an immutable benchmark transcript.

## Role journeys

| Role | Result |
|---|---|
| New Team Member | PASS |
| Project Owner / Tech Lead | PASS |
| BA | PASS |
| Developer | PASS |
| Tester / QA | PASS |
| Automation Tester | PASS |
| Framework Maintainer | PASS |

## Task journeys

All PASS: install required components; run Kit Doctor; run Suite Doctor; bootstrap Foundation; recover a brownfield project; start a BA feature; obtain Human BA approval; create Engineering Handoff; start Dev FEATURE_DELIVERY; handle UPSTREAM_GAP; handle NEEDS_REPLAN/BLOCKED; create/approve Test Design; create/approve Testcases; plan and implement Automation; reach EXECUTION_READY; execute tests and record Observations; classify DEFECT, SPEC_GAP, BUSINESS_DECISION_REQUIRED, TEST_ISSUE and ENVIRONMENT_ISSUE; route DEFECT; complete Dev fix; create READY_FOR_RETEST; perform Tester retest; create VERIFIED/REOPENED; run Public Cross-Kit Conformance; interpret optional degradation; recover package authority/payload mismatch; handle modified/missing managed files, dirty source, stale candidate SHA and stale approval receipts; upgrade/reinstall and verify version.

## Links, parity and stale scan

- 442 Markdown pages scanned before this report; 774 local links checked; 0 broken current links, 0 broken mandatory links, 0 broken anchors.
- 16 project-template paths are expected consumer outputs and are not repository defects. 5 historical-only broken links remain accepted as above. 60 external references (59 after removing fragments): 0 HTTP 404; 2 ISO.org references returned HTTP 403 and remain `NETWORK_UNVERIFIED`.
- No current `Dev planned`, Test V1/STOP_V1, `APPROVED_FOR_ENGINEERING`, old current component versions, or emitted `READY_TO_MERGE` claim remains. Negative statements and explicitly historical snapshots are retained.
- VI/EN operator-path parity covers start/index, installation, lifecycle/authority, Dev, Test Manual overview, Automation, Execution/Findings/Retest, conformance, release, recovery, and readiness states. English Test Manual deep steps remain explicitly routed to the Vietnamese primary guide.

## Verification on the remediation candidate

- Targeted exact-ref cache regression: PASS. Its pre-fix run failed (`8 != 4`); post-fix verifies exact-ref reuse, new-revision cache miss, and non-cached negative proof.
- BA installed acceptance: PASS. Test Execution installed acceptance: PASS.
- Suite Doctor: READY. Kit Doctors: BA READY; Dev READY; Test DEGRADED only for missing optional XMind, with `CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE`.
- Public Cross-Kit Conformance: PASS on fresh clone at the SHA/tree above. Foundation ? BA ? Dev ? Manual Test ? Automation ? Execution ? Finding/DEFECT ? Dev fix ? READY_FOR_RETEST ? Tester VERIFIED and straight-pass routes both PASS. All 12 required negative probes PASS.
- Regression: 721 total, 714 passed, 0 failed, 0 errors, 7 skipped. These are environment-guarded existing skips; no skip directive was added or widened by this change. `pytest` 9.1.1; diff check PASS.
- Conformance reported `OPTIONAL_DEGRADED` for XMind separately from Test Doctor DEGRADED and final suite PASS. Test Doctor's only failing dependency check is optional XMind; required package/integrity checks PASS.
- Test package source authority validates; full-suite packaging coverage includes clean `core.autocrlf=true` and `false` clones. GitHub CI status was not inferred from this locally executed evidence.

## Gate and next decision

The remediation candidate is suitable for Human Internal/Pilot RC integration review after the final report-only commit is pushed and its exact SHA/tree receives the final required fresh-clone conformance run. This report does not authorize merge, tag, GitHub Release, stable release, or product acceptance.

## Follow-up blocker disposition

- `temporary-branch current-doc blocker = CLOSED`: current installation guidance selects an authorized exact ref, prints and records its resolved SHA, and uses that checkout for installation and Doctor. Release guidance binds the candidate to the exact SHA/tree in Public Cross-Kit Conformance and places tagging/release after the Human integration/release decision. The branch identity recorded above is historical execution evidence only.
