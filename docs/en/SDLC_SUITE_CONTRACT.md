# Public Cross-Kit Conformance

This is the current operational contract for the internal suite-candidate gate. Machine identity and acceptance tiers come from [tooling/sdlc-suite.json](../../tooling/sdlc-suite.json) and [tooling/sdlc-suite-acceptance.yaml](../../tooling/sdlc-suite-acceptance.yaml).

## Run against the exact candidate

Prerequisites: a clean committed candidate, Python with pytest available to unittest discovery, and Spec Kit v1.0.11 CLI. Save the report outside the source checkout.

~~~powershell
python -m tooling.public_conformance --repo . --output C:\path\outside\repo\conformance-report.json --spec-kit-cli C:\path\to\specify.exe
~~~

The runner binds the commit and tree, creates a fresh clone at that SHA, uses an isolated installed runtime and an external working directory, leaves PYTHONPATH absent, and writes evidence outside the source tree. It does not require core.autocrlf=false; repository .gitattributes preserves package source bytes on supported Windows checkouts.

## Required journey

The synthetic multi-repository run covers:

~~~
Project Foundation
→ BA
→ Dev
→ Test Manual
→ Automation
→ Execution
→ Finding → DEFECT → Dev Fix → READY_FOR_RETEST → Tester VERIFIED
~~~

It also runs a straight-pass execution path. Required negative probes reject validator PASS as approval, generated output as approved, TEST_ONLY without a trusted test-only host, Dev claiming VERIFIED, APPROVED_TESTWARE as EXECUTION_READY, EXECUTION_READY as PASS, Delivery Manifest as required authority, READY_TO_MERGE as a lifecycle state, and command failure automatically classified as DEFECT.

Synthetic Human receipts are TEST_ONLY and not_for_production. They are accepted only through trusted test-only host paths; they are not production approval examples.

## Read the result

- Kit Doctor DEGRADED means an optional Kit capability such as XMind/Excel is unavailable.
- Conformance OPTIONAL_DEGRADED records an optional projection setup gap separately. It is neither Kit Doctor DEGRADED by definition nor the suite result.
- Suite Doctor reports package/core compatibility. Required package or contract failures are blockers.
- Final suite status remains PASS or FAIL. An allowed optional projection gap can coexist with final PASS; report both fields.

The report binds candidate SHA/tree, suite and component versions, package authority/provenance, Doctors, test totals, scenario trace, fresh clone, and source immutability. If code or docs change after the run, rerun the full gate for the new clean SHA.

A PASS is evidence for Human review. It does not authorize merge, tag, GitHub Release, or stable publication. See [release status](RELEASE.md).

---

Tiếng Việt: [Public Cross-Kit Conformance](../vi/SDLC_SUITE_CONTRACT.md)
