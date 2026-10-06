# Suite release status

The identity below follows the [suite manifest](../../tooling/sdlc-suite.json) and component manifests. Required evidence is defined by the [suite acceptance contract](../../tooling/sdlc-suite-acceptance.yaml).

| Component | Candidate | Meaning |
|---|---|---|
| Suite | agent-assisted-sdlc-vnext 1.0.0-rc.4 · INTERNAL_RC_CANDIDATE | Internal candidate for Human review |
| BA | 2.0.0-rc.6 | Package candidate |
| Dev | 0.4.0-rc.4 | Integration candidate |
| Test | 2.0.0-rc.14 | Package candidate |

Candidate source branch: docs/full-documentation-hardening-rc-gate. The final SHA/tree is bound by Public Cross-Kit Conformance. This is not a stable release; no Git tag or GitHub Release exists for this candidate.

## Readiness layers

- **Package readiness:** Kit Doctors validate manifests, payloads, and required capabilities. READY does not prove project approval or Test verification.
- **Suite compatibility:** Suite Doctor checks component and contract versions, routers, runtime, and package authority.
- **Public Conformance:** run against the exact clean candidate SHA from a fresh clone. PASS is evidence for review. Policy-allowed optional projection gaps may be reported separately as OPTIONAL_DEGRADED.
- **Human release decision:** after those gates, a Human decides whether to integrate and release.
- **Git tag / GitHub Release:** create only after that separate Human decision; neither is part of this candidate.

VERIFIED is the framework's terminal product-lifecycle state. Merge/release is a separate Human decision. Doctor READY, PROJECT_FOUNDATION_READY, READY_FOR_TEST, APPROVED_TESTWARE, EXECUTION_READY, or conformance PASS does not replace that decision. See [Readiness states](READINESS_STATES.md).

## Candidate review path

1. Verify package readiness with [installation and Kit Doctors](INSTALLATION.md).
2. Run [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md) for the exact committed SHA.
3. Bind the SHA/tree, package digests, Doctor outputs, and conformance report to the Human review.
4. Stop before merge, tag, or release until the Human makes the separate decision.

---

Tiếng Việt: [Trạng thái phát hành](../vi/RELEASE.md)
