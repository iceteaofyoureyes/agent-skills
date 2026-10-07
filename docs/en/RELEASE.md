# Suite release status

The identity below follows the [suite manifest](../../tooling/sdlc-suite.json) and component manifests. Required evidence is defined by the [suite acceptance contract](../../tooling/sdlc-suite-acceptance.yaml).

| Component | Candidate | Meaning |
|---|---|---|
| Suite | agent-assisted-sdlc-vnext 1.0.0-rc.4 · INTERNAL_RC_CANDIDATE | Internal candidate for Human review |
| BA | 2.0.0-rc.6 | Package candidate |
| Dev | 0.4.0-rc.4 | Integration candidate |
| Test | 2.0.0-rc.14 | Package candidate |

The final Public Cross-Kit Conformance evidence binds this machine candidate to an exact commit SHA and tree. Use that bound revision when reproducing or installing this candidate. A branch name is not a durable release identity. This remains an Internal RC candidate, not a stable release.

## Readiness layers

- **Package readiness:** Kit Doctors validate manifests, payloads, and required capabilities. READY does not prove project approval or Test verification.
- **Suite compatibility:** Suite Doctor checks component and contract versions, routers, runtime, and package authority.
- **Public Conformance:** run against the exact clean candidate SHA from a fresh clone. PASS is evidence for review. Policy-allowed optional projection gaps may be reported separately as OPTIONAL_DEGRADED.
- **Human integration/release decision:** after those gates, a Human decides whether to integrate the reviewed candidate and authorize release.
- **Git tag / GitHub Release:** create only after that separate Human decision, and bind it to the approved integrated commit. Neither is part of this candidate before that decision.

VERIFIED is the framework's terminal product-lifecycle state. Merge/release is a separate Human decision. Doctor READY, PROJECT_FOUNDATION_READY, READY_FOR_TEST, APPROVED_TESTWARE, EXECUTION_READY, or conformance PASS does not replace that decision. See [Readiness states](READINESS_STATES.md).

## Candidate review path

1. Verify package readiness with [installation and Kit Doctors](INSTALLATION.md).
2. Run [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md) for the exact committed SHA.
3. Bind the SHA/tree, package digests, Doctor outputs, and conformance report to the Human review.
4. Stop before merge, tag, or release until the Human makes the separate decision.

---

Tiếng Việt: [Trạng thái phát hành](../vi/RELEASE.md)
