# Implementation order and deferred work

**Current status: Test Kit V1 Core, XMind Projection V1, and Excel Projection V1 are HUMAN_ACCEPTED framework capabilities.** This does not approve PetClinic production testware. The frozen data and gate contracts are in [CONTRACTS.md](CONTRACTS.md).

1. BA source hashes and upstream TEA/Katalon revisions are pinned; invocation and output evidence are retained.
2. BA → TEA adapter, known-shape Test Design normalization, immutable snapshot, validators, and Design Gate are implemented.
3. Approved-design → Katalon adapter, known-shape testcase normalization, immutable snapshot, validators, and Case Gate are implemented.
4. Case Gate emits reference-only Approved Testware and reaches terminal `STOP_V1` only after a valid approval with no material OPEN execution dependency.

The runtime must choose its existing persistence mechanism for immutable snapshots, hashes, raw evidence, findings and receipts while preserving the contract. No new service or storage file layout is specified here. The exact UI/API/fixture contracts needed to run Petclinic cases are separate product decisions: TC-012 needs an approved editable-field contract; interval cases need approved setup/observation mapping; UI-dependent steps need the approved interface. These are execution dependencies that block final Testware approval while material and unresolved, not blockers to freezing this implementation contract.

Deferred by the approved V1 boundary: automation, automation, test execution, TestOps writes, upstream patches, release decisions and Petclinic product changes. XMind/Excel renderers remain outside core implementation; each future projection requires `HUMAN_EXPLICIT_REQUEST`, reads an approved canonical snapshot and cannot change its approval. No separate traceability/testing skill is planned.
