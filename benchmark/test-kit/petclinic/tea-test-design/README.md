# TEA Test Design benchmark — Spring Petclinic CR-001

This benchmark covers only the approved BA baseline → TEA test analysis → TEA test design. It ran Candidate A at the pinned upstream revision in candidate-manifest.md, using one structure-only epic adapter because TEA's system-level mode requires architecture/ADR inputs that this baseline does not contain.

**Verdict:** ACCEPT_WITH_THIN_ADAPTER

The plan maps all six FRs and the relevant BRs to observable scenarios. It preserves the unresolved maximum duration, list filters, default sorting, and pagination/page size. No business-semantic hallucination was found in the raw design. The TEA workflow's generic coverage percentages and effort ranges are marked as unapproved planning values, not BA requirements.

No test code was generated, no tests were run, no application source or approved BA file was changed, and no XMind/Excel export or release gate was performed.

## Artifacts

- input-manifest.md — source revisions, authorities, supplemental evidence, and adapter/config details.
- candidate-manifest.md — upstream commit and the invocation/prompt used.
- input-adapter/ — epic-shaped, verbatim FR wrapper and TEA config.
- raw-output/test-design/test-design-epic-1.md — native TEA epic-level design.
- raw-output/test-design/test-design-progress-epic-1.md — workflow checkpoint.
- normalized-output/traceability-matrix.md — FR/BR-to-scenario mapping and oracle review.
- review.md — criterion-by-criterion benchmark review.
- findings.md — evidence-backed findings and patch candidates.

See review.md for evidence and findings.md for the detailed oracle results.
