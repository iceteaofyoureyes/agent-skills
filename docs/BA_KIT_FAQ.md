# BA Kit FAQ

### Do I need Skills Manager?

No. BA Kit installs and runs through the repository's scripts. Skills Manager is optional.

### Do I need to know individual skill names?

No. Ask for the BA outcome in ordinary language; the workflow routes the request internally.

### Does BA Kit write production code?

No. BA Kit prepares Business Analysis artifacts. It does not implement production changes or decide technical ownership/design.

### Can BA Kit approve requirements automatically?

No. It can record Human answers and validate artifacts, but only the Human can approve a named artifact or gate.

### Does “Tiếp tục” mean approval?

No. It resumes the saved workflow at the next valid action. It does not answer an open question or approve an artifact.

### Can it work on brownfield projects?

Yes. For brownfield requests, the workflow can discover current code, behavior, data, APIs, and UI. It records those findings as **CURRENT_SYSTEM** evidence.

### What if current code conflicts with the SRS?

Record the discrepancy. Confirmed BA decisions, approved Business Rules, and the canonical SRS govern business meaning; current code is evidence of existing behavior. The workflow should not silently rewrite either side to hide the conflict.

### Are the examples mandatory templates?

No. They are illustrative. Sample prose and IDs are not fixed; follow actual artifact contracts and preserve required source references.

### What happens after Engineering Handoff?

The intended next stage is Engineering Impact, followed by Dev Kit and Spec Kit work. Those capabilities are planned and are not implemented in this release candidate.

### How will Test use BA outputs later?

The planned Test Kit and TEA will use the approved BA baseline together with downstream engineering evidence to define and prove expected behavior. They are not available in BA Kit RC1.

### Is BA Kit publicly released or runtime-accepted?

No. It is an RC1 candidate. Packaged runtime acceptance is blocked by an isolated provider/runtime, and public distribution is blocked by unresolved provenance and licensing. See [Release Status](RELEASE.md) and [Provenance](PROVENANCE.md).
