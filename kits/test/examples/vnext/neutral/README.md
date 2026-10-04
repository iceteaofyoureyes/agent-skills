# Neutral Test Kit VNext example

This synthetic feature demonstrates the operator path from an existing BA Engineering Handoff VNext through the two Test Kit Human Gates. It contains no approved handoff, Human receipt, or production authority fixture.

## Synthetic feature: Resource reservation

Business rule `BR-001`: only an eligible member may reserve an available resource.

Functional requirement `FR-001`: an eligible member can submit a reservation request and receive the business outcome defined by the approved handoff.

The wording is illustrative. The BA Engineering Handoff VNext from the target project remains the only business WHAT authority. Replace the synthetic IDs and wording with the exact approved handoff content before running a real feature.

## Manual lane

1. Start Test Kit VNext with the exact BA Engineering Handoff VNext and its trusted Human authenticator.
2. Produce the canonical Test Design and finalize it to `DESIGN_REVIEW`.
3. Review the exact snapshot and input refs. Only the authenticated Human can issue the Design Gate decision; validation `PASS` does not approve it.
4. After `APPROVED_DESIGN`, prepare and finalize canonical Testcases to `CASE_REVIEW`.
5. Review the exact snapshot, Design Gate receipt, BA authority, and any consumed optional context. Only the authenticated Human can approve.
6. Re-read the Approved Testware VNext `HANDOFF_MANIFEST` at `APPROVED_TESTWARE`.

`APPROVED_TESTWARE` ends the Phase 6 manual lane. It does not mean `EXECUTION_READY`, `VERIFIED`, or that a test passed. Automation and execution lifecycle work are deferred to Phase 7+.

UX is required only when the exact Test authority context sets `ux_required: true`. When supplied, approved UX refs are revalidated and bound by hash; prototypes remain `REVIEW_EVIDENCE`. Optional Dev context is technical evidence and cannot redefine BA WHAT. XMind and Excel are derived projections only. V1 artifacts are `LEGACY_COMPAT` with `vnext_authority=false`.
