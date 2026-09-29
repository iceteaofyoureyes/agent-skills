# Approved composition and ownership

**Status: APPROVED for Test Kit V1.** The sequence in [README](README.md) is fixed. No source code, automation, test execution, TestOps write, release gate, or new testing/traceability skill is part of V1.

| Responsibility | Owner | Boundary |
|---|---|---|
| Route stages, pin revisions, retain raw evidence and receipts | Project-owned thin workflow | Orchestration only; cannot decide business behavior or approve artifacts. |
| Test analysis and Test Design | Exact pinned TEA | BA input is shape-adapted; TEA planning metadata is advisory. |
| Design normalization and validation | Project-owned thin adapter/validator | Deterministic extraction of known structures; `CANNOT_NORMALIZE` on ambiguity. |
| Design Gate | Human | Only explicit `APPROVE`/`REQUEST_CHANGES` on the exact canonical snapshot. |
| Manual testcase generation | Exact pinned Katalon skill | Receives approved design and BA oracle; no TestOps operations. |
| Case normalization and validation | Project-owned thin adapter/validator | Deterministic extraction, trace and dependency checks; no semantic repair. |
| Case Gate and Approved Testware | Human decision enforced by workflow | Material unresolved execution dependencies block approval. |

Authority is scoped, never ranked as a single global source: Approved BA Baseline is the **BUSINESS ORACLE**; Approved Test Design is the **COVERAGE ORACLE**; approved UI/API/Engineering/interface contract is the **EXECUTION ORACLE**. Current source/system is **SUPPLEMENTAL**; TEA/Katalon planning metadata is **ADVISORY**. A conflict is recorded and returned to the authority that owns its scope. Interface details cannot change BA behavior; source code cannot silently define a missing contract.

Project-owned metadata for source paths/hashes, upstream commits, raw locations, normalizer profile and version, findings, and Human receipts is stored beside canonical snapshots. It is required evidence, but not extra semantic fields in either canonical schema. A new revision preserves its prior raw and canonical snapshot; it does not overwrite a prior Human decision.

XMind/Excel are optional on-demand projections of a pinned canonical snapshot, triggered only by `HUMAN_EXPLICIT_REQUEST`. They are outside the core capability set, are not gate input, and cannot make core status `DEGRADED` merely by being absent. The general optional-capability rule in `docs/vi/KIT_CONTRACT.md` applies only to capabilities included in a kit's declared set; these projections are not included in Test Kit V1. Any future promotion into the core capability set requires an explicit contract change.
