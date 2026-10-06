# Documentation Quality & Staleness Audit

Repository: iceteaofyoureyes/agent-skills
Audited revision: 25d7cb6b5b4685540bce6621fbe245fa67312298
Expected checkpoint: 25d7cb6b5b4685540bce6621fbe245fa67312298
Terminal status: READY_FOR_HUMAN_DOCS_ARCHITECTURE_REVIEW
Highest severity: P1
Existing tracked docs modified: NO
Framework semantics modified: NO
Remediation performed: NO

Audit target was freshly fetched origin/main at the expected SHA. The original workspace is a clean feature branch at 1a62e1eb4d2cb575090a6eaebf88bcd2d5ee3415; its tree matches the audited main tree. The audit ran in a temporary detached worktree at the expected SHA and wrote only the new audit directory into the original workspace.

## Inventory and finding counts

- Documentation surfaces inventoried: 444 Markdown/RST/TXT files plus 8 operator CLI/help surfaces, 452 total.
- CURRENT: 333.
- LEGACY_COMPAT: 8 documentation-role surfaces.
- HISTORICAL_VALID: 95.
- STALE: 10.
- PARTIALLY_STALE: 6.
- CONFLICTING: 10 file-level surfaces with direct current-truth conflicts.
- ORPHAN: 89 raw inventory surfaces; 10 actionable first-party operator/reference pages are absent from primary indexes.
- Confirmed broken local links: 18 (15 optional sibling-skill references, 3 historical/fixture references).
- Confirmed broken anchors: 0.
- Remote links: 58 unique checked; 56 reachable, 0 404, 2 NETWORK_UNVERIFIED due HTTP 403 from ISO.org.

Finding counts: P0 0, P1 1, P2 7, P3 5, P4 2.

## Top findings

The P1 finding is DOC-P1-001: the documented Windows Test Kit install path can fail package source validation when Git core.autocrlf=true. Forty manifest-selected files are checked out as CRLF although the Test package authority hashes LF bytes. Public conformance explicitly disables autocrlf in its fresh clone; ordinary Windows install instructions do not state the requirement. The committed authority and payload pins themselves match their manifest values.

P2 findings cover stale root/Kit/architecture status pages; missing primary navigation to current Dev and mandatory Public Cross-Kit Conformance guidance; an active-looking Delivery Manifest V2 document despite DEFERRED_NON_AUTHORITATIVE; a READY_TO_MERGE row that is not emitted by the runtime; missing package upgrade/recovery instructions; local usernames and absolute paths in a historical benchmark transcript; and missing English Dev role/task guides.

No current operator guide was found to equate validator PASS, generation, Doctor READY, Foundation readiness, READY_FOR_TEST, APPROVED_TESTWARE, EXECUTION_READY or Dev fix completion with Human approval or Tester VERIFIED. TEST_ONLY safeguards are explicit. The main risk is stale route/status material, not a current Human Gate bypass.

## Machine truth conflicts

Suite/Kit versions, public contract versions, authority precedence, artifact classes and Delivery Manifest status match machine-readable sources. Suite compatibility extraction returned PASS for the nine public contracts. The Test authority file SHA and payload digest match their manifest pins.

One environment-sensitive package conflict remains: the source package authority validation fails on this Windows checkout under core.autocrlf=true because 40 selected files have CRLF working bytes. This is recorded as DOC-P1-001; no files or hashes were changed.

GitHub PR #9 is merged at the audited SHA. Its body reports a fresh-clone conformance PASS and 718 tests with 7 existing skips at a tree-identical head. No report artifact, review record or status check is attached in GitHub metadata, and this audit did not rerun conformance.

## Largest usability gaps

- The main README and Kit catalog give outdated versions/status and an obsolete Test V1/STOP_V1 lifecycle.
- Dev role/task material and the required Public Cross-Kit Conformance command are not reachable from primary indexes.
- English coverage has no current Dev guide and only a Test overview; the detailed Test Manual and suite conformance paths are Vietnamese-only.
- Package mismatch, upgrade, dirty/stale source and optional conformance degradation lack end-to-end recovery instructions.

## Proposed architecture and remediation waves

The proposed target IA includes Start Here, Concepts, Install, Workflow, Role Guides, Task Guides, Reference, Troubleshooting, Release / Compatibility, Legacy / Historical, and Maintainer Documentation. It keeps schemas/manifests/contracts as the source of truth and routes each operator guide to those sources.

Recommended order:

1. Wave A — package/install correctness and current authority/status.
2. Wave B — entry points and information architecture.
3. Wave C — role and task guides.
4. Wave D — troubleshooting and reference.
5. Wave E — legacy and historical separation.
6. Wave F — VI/EN parity and polish.

## Package integrity impact

Test package authority covers 194 entries, including Test README, Automation/Execution operator docs, examples, schemas, templates and runtime. Changes to those files require generated authority and payload digest regeneration, kit pin updates, installed acceptance and Test Doctor checks; a prerelease version decision may be required. Dev plugin changes affect provenance.lock and Dev installed acceptance. BA workflow skill changes affect installed BA hashes/acceptance. Standalone docs outside allowlists do not automatically change package digests.

No authority, digest, pin, version or manifest was edited. No Doctor, unit-test suite or full Public Cross-Kit Conformance run was executed.

## Commands and checks

- rtk git status, rev-parse, branch, remote, fetch, log, diff, worktree status.
- rtk gh run list, gh pr list, and gh pr view for merged PR #9 metadata/body.
- Python 3.13.14 read-only manifest, suite compatibility and Test package-authority checks.
- rtk proxy python -B -m tooling.public_conformance --help only; the conformance run itself was not invoked.
- Local Markdown link/anchor candidate scan and HTTP HEAD checks for 58 unique external links.
- Test source package validation returned the documented P1 failure under core.autocrlf=true.
- Final rtk git status and git diff review; only new files under the audit output directory differ.

## Audit artifacts created

1. 01-documentation-inventory.md
2. 02-staleness-conflict-matrix.md
3. 03-information-architecture-assessment.md
4. 04-role-based-usability-assessment.md
5. 05-task-based-usability-assessment.md
6. 06-authority-readiness-terminology-audit.md
7. 07-vi-en-parity-report.md
8. 08-link-navigation-audit.md
9. 09-legacy-historical-classification.md
10. 10-remediation-priority-plan.md
11. 11-target-documentation-architecture-proposal.md
12. 12-docs-hardening-acceptance-criteria.md
13. machine-truth.md
14. AUDIT_SUMMARY.md

## Repository state and next Human decision

Existing tracked documentation and framework semantics remain unchanged. No remediation, commit, merge, tag or release was performed. The workspace should contain only the new untracked audit directory; tracked git diff is expected to be empty.

Next Human decision: review or revise 11-target-documentation-architecture-proposal.md and 10-remediation-priority-plan.md, especially the supported Windows source-checkout policy and Test package integrity/version gate, before authorizing a separate remediation phase.

READY_FOR_HUMAN_DOCS_ARCHITECTURE_REVIEW
