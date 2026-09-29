# Stage 3 benchmark — Katalon create-test-cases

**Scope:** Approved BA baseline and Stage 1–2 Test Design → detailed manual testcase semantic output.

**Verdict:** ACCEPT_WITH_THIN_ADAPTER

The pinned skill's requirement analysis, ISTQB-informed coverage, atomic case design, and manual testcase format were reusable. A thin output adapter maps the cases to local Markdown fields and retains BA FR/BR plus TEA TD references. Katalon project discovery, TestOps writes, requirement linking, suites, execution, and exports were not used.

The Stage 1–2 Test Design is the authorized fixture under the user's instruction. Its Draft label was not changed. Cases preserve its semantics and keep maximum duration, list filters, sorting, and pagination/page size unresolved.

The appointment feature and its UI are absent from the current PetClinic checkout. Cases therefore use business-language UI actions and explicitly mark exact labels, editable fields, and interval test-data setup as execution dependencies. No exact error message, status code, permission mapping, duration maximum, or Visit field mapping is invented.

## Files

- input-manifest.md — source SHAs, approved baseline, and exact Stage 1–2 fixture.
- candidate-manifest.md — pinned Katalon revision, loaded upstream files, invocation, and runtime limitations.
- raw-output/test-cases.md — generated manual cases in the upstream manual-case shape.
- raw-output/coverage-note.md — coverage techniques and deferred UNKNOWNs.
- normalized-output/traceability.md — case counts and FR/BR/TD mapping.
- review.md — review against the requested criteria.
- findings.md — evidence-backed findings and verdict.

No PetClinic source or BA baseline was changed. No Katalon TestOps write, test execution, automation, or export occurred.
