# Public SDLC VNext Conformance

Suite `agent-assisted-sdlc-vnext` version `1.0.0-rc.1` is an `INTERNAL_RC_CANDIDATE`. Its manifest is [tooling/sdlc-suite.json](../../tooling/sdlc-suite.json), and its required acceptance tiers are [tooling/sdlc-suite-acceptance.yaml](../../tooling/sdlc-suite-acceptance.yaml).

The suite checks Project Foundation V1, BA Engineering Handoff V2, Dev Handoff V2, Approved Testware V1, Execution Ready V1, Finding Classification V1, Defect Handoff V1, Ready For Retest V1, and Verified Handoff V1. Component versions come from the kit manifests; public schema versions come from their executable or schema sources. Delivery Manifest stays `DEFERRED_NON_AUTHORITATIVE` and is not a VNext flow prerequisite.

## Run Phase 9 conformance

Commit the candidate on `feat/public-cross-kit-conformance-phase9` and leave the checkout clean. Then run from the repository:

```powershell
python -m tooling.public_conformance --repo . --output C:\path\outside\repo\phase9-report.json --spec-kit-cli C:\path\to\specify.exe
```

Use Spec Kit `v1.0.11` and pass its executable explicitly. The runner creates a local fresh clone at the exact candidate SHA, runs from an external working directory with isolated Python and temporary user configuration, and writes the report outside the source tree. It does not need network access. `tooling.readiness_acceptance` remains a compatibility alias for this same runner.

The runner performs the component regressions, Suite Doctor checks, installed public cross-kit flow, fresh-clone check, and full tooling unittest discovery. The public flow exercises the synthetic multi-repository path from Foundation approval through BA, Dev, manual Test, Automation, execution, defect/fix/retest, and a separate straight-pass execution. The fixture's Human receipts are explicitly `TEST_ONLY` and are accepted only through trusted host callbacks.

Suite Doctor requires BA, Dev, and Test core readiness, current package and contract compatibility, Foundation runtime availability, public routers, runtime-ignore rules, and the Test package authority. Missing optional XMind or Excel projection dependencies may produce `DEGRADED` while core Test readiness passes. Any required runtime, package, integrity, or contract failure fails the Doctor.

The report has evidence class `PUBLIC_CROSS_KIT_CONFORMANCE` and status `PASS` or `FAIL`. It binds the framework commit/tree, suite manifest and lock hashes, component and contract versions, Doctor results, scenario and trace checks, revision reproduction, fresh-clone status, and test totals. The report is evidence, not project or business authority.

## Candidate boundary

The candidate is internal only. Do not tag it or publish a GitHub Release in Phase 9. A passing report does not authorize merge; merge requires independent remote review. If source changes after the run, the lock and report are stale and the full public conformance run must be repeated.

The bootstrap specification `PHASE_9_PUBLIC_CROSS_KIT_CONFORMANCE_SPEC.md` is temporary input and is removed from the implementation branch before its candidate commit. Full repository documentation staleness review follows Phase 9 as a separate required lane.
