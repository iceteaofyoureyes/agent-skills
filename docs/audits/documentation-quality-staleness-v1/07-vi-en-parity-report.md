# Vietnamese / English parity report

Classification: PARITY, MINOR_DRIFT, MATERIAL_DRIFT, AUTHORITY_DRIFT, or NO_COUNTERPART. A pair can be semantically parallel and still repeat the same stale content; that case is called out separately.

| Surface | Classification | Evidence and assessment |
|---|---|---|
| BA Quick Start | PARITY | docs/vi/BA_KIT_QUICKSTART.md and docs/en/BA_KIT_QUICKSTART.md align on inputs, Human clarification, baseline lifecycle, exact receipt and handoff. |
| BA Workflow / Human Gates | PARITY with shared stale content | docs/vi/BA_KIT_WORKFLOW.md and docs/en/BA_KIT_WORKFLOW.md express similar gates and authority, but both diagrams still label Dev planned and Test V1. See DOC-P2-001. |
| BA capabilities and usage guides | PARITY / MINOR_DRIFT | Matching BA pages exist; minor wording and link differences do not alter the core Human boundary. |
| Installation | MATERIAL_DRIFT | Vietnamese docs include Test Kit setup and additional Codex/project-owned config detail. English docs focus on BA and Foundation. Neither documents the Windows raw-byte Test checkout prerequisite. |
| Architecture | PARITY with shared stale content | Both language pages say Dev is planned and Test V1/STOP_V1; translations are similar, but both conflict with current manifests and VNext guides. |
| Release | AUTHORITY_DRIFT | Both identify Test 2.0.0-rc.11, but docs/vi/RELEASE.md repeats the version and says BA/Dev docs are historical. docs/en/RELEASE.md instead says other Kit docs retain their own versions/history. Current Dev VNext is active. |
| Test Manual VNext | NO_COUNTERPART | The detailed operator guides are Vietnamese. docs/en/README.md and docs/en/TEST_KIT_README.md disclose that the English material is an overview and routes to Vietnamese guides. |
| Test Automation V1 | PARITY | English and Vietnamese detailed guides cover ownership, clean revisions, verification, EXECUTION_READY and the stop boundary consistently. Neither explains the conformance report’s OPTIONAL_DEGRADED status. |
| Test Execution VNext | PARITY | English and Vietnamese guides align on immutable execution inputs, Tester classification, DEFECT routing, retest and VERIFIED. |
| Dev VNext role/task guides | NO_COUNTERPART | Current detailed guides are Vietnamese; there is no English counterpart or English index route. See DOC-P2-007. |
| Suite / Public Cross-Kit Conformance | NO_COUNTERPART | docs/vi/SDLC_SUITE_CONTRACT.md is the only operator conformance guide and is not linked from the English or Vietnamese indexes. |
| Project Foundation workflow | NO_COUNTERPART | docs/project-foundation.md and project-foundation/SKILL.md are English-only although the Vietnamese root README links to the workflow. |
| Provenance | PARITY with mixed history | docs/en/PROVENANCE.md and docs/vi/PROVENANCE.md give current Test pins and similar BA RC1 history, but the historical BA audit lacks a clear snapshot label. |
| Foundations | PARITY, historical snapshot | English and Vietnamese pages identify the same 2026-09-24 reference snapshot and carry the old Test V1/STOP_V1 design context as dated history. |
| Shared SDLC contract / Wave 1 | NO_COUNTERPART | The detailed current shared contract and migration map are English-only. |
| Draw.io / prototypes | PARITY with sample clarity gap | English and Vietnamese versions use the same Appointment lifecycle sample. Neither labels it synthetic/sample; the current BA example is Resource Request Submission. |

## Parity risks

1. An English-speaking Developer has no equivalent current role guide, including install, upstream gap, exact checks, routing and recovery.
2. English readers cannot find the public release-gate command from an English index.
3. Vietnamese readers see current Dev pages but the VI release page calls BA/Dev docs historical.
4. Vietnamese Installation covers Test where English Installation does not, but the index says English docs are semantically equivalent.
5. Existing Test Automation and Execution translations are strong and preserve state names/authority semantics; preserve this parity when reorganizing.

The report does not propose translating every upstream technical reference. It proposes parity for first-party operator journeys, state definitions, commands, warnings and recovery.
