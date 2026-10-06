# Legacy and historical classification

Classification preserves useful history. Old material is not a defect merely because it is old; the risk is presenting it as current default or authority.

| Surface | Classification | Evidence / current use | Recommended disposition |
|---|---|---|---|
| BA VNext workflow/quickstart and current BA example | CURRENT | Exact BA lifecycle, receipt boundary, BR/FR and Engineering Handoff VNext are described. | Keep as role guides; link to one canonical lifecycle/authority reference. |
| Dev Kit VNext manifests, README, plugin and current Dev guides | CURRENT | kits/dev/kit.yaml is 0.4.0-rc.2; guides document V2, FEATURE_DELIVERY, TECHNICAL_MAINTENANCE and READY_FOR_TEST. | Keep; index the guides; add English role/task coverage. |
| Test Kit Manual/Automation/Execution VNext | CURRENT | kits/test/kit.yaml is 2.0.0-rc.11; current guides cover APPROVED_TESTWARE through VERIFIED. | Keep as defaults; label manual/automation/execution lanes and link from both locale indexes. |
| kits/dev/LEGACY_COMPAT.md | LEGACY_COMPAT | Explicitly says V1 surfaces are read-only and never supply VNext authority. | Keep; link from Dev compatibility reference. |
| kits/test/examples/legacy-v1 and kits/test/examples/CR-001 | LEGACY_COMPAT | Test README and example title explicitly mark Appointment/CR-001 as historical V1, vnext_authority=false. | Keep as compatibility/evidence; keep out of default Start Here path. |
| tooling/tests/fixtures/ba-v1-legacy-compat | LEGACY_COMPAT / EVIDENCE | Deliberately exercises old BA state/handoff reading. | Keep as test evidence; repair/label only within a future fixture change. |
| benchmark/test-kit/petclinic/** | HISTORICAL_VALID / EVIDENCE | Dated Test Kit benchmark records, inputs, outputs and reviews; paths identify the benchmark lane. | Retain and index under benchmark/history. Do not present as current neutral examples. |
| docs/design/test-kit-v1 and test-kit-v1.1-customization | HISTORICAL_VALID | Versioned design/implementation contracts for earlier Test Kit lanes; V1 stop states are scoped by their directories. | Retain in Legacy/Historical with an explicit status header and links from current compatibility docs. |
| docs/en/FOUNDATIONS.md and docs/vi/FOUNDATIONS.md | HISTORICAL_VALID snapshot | Both declare a 2026-09-24 reference snapshot and preserve the claims for that snapshot. | Keep dated; avoid describing the snapshot as current suite status. |
| docs/vi/GOLDEN_G3_RUNTIME_REMEDIATION.md and docs/vi/DEV_KIT_BENCHMARK.md | HISTORICAL_VALID | Candidate remediation/benchmark evidence with branch and version history. | Retain under dated maintainer history; do not use for current install decisions. |
| BENCHMARK_REMEDIATION_RCA.md | HISTORICAL_VALID | Root-level remediation analysis, not current operator instructions. | Move/index as historical evidence in a future IA pass; retain evidence. |
| docs/DELIVERY_MANIFEST_V2.md | SUPERSEDED_UNLABELED / STALE_DEFAULT | Current suite manifest marks Delivery Manifest DEFERRED_NON_AUTHORITATIVE, while this page explains it in present tense and lists older Kit versions. | Label as historical/deferred compatibility design and remove it from any current-authority route. Do not delete blindly. |
| docs/en/ARCHITECTURE.md and docs/vi/ARCHITECTURE.md | STALE_DEFAULT | Both describe Test V1/STOP_V1 and Dev as planned. | Replace the current summary after Human review; preserve old phase diagram under history if needed. |
| docs/en/BA_KIT_WORKFLOW.md and docs/vi/BA_KIT_WORKFLOW.md | STALE_DEFAULT in downstream diagram | The BA lifecycle is current, but the diagram routes to planned Dev/Test stages. | Keep BA-specific procedure; update only the downstream map under a separate approved change. |
| README.md and kits/README.md | DUPLICATE_CURRENT_AUTHORITY / STALE_DEFAULT | They independently declare current kit statuses and versions that conflict with manifests. | Use one manifest-derived status summary; link other indexes to it. |
| docs/en/PROVENANCE.md and docs/vi/PROVENANCE.md BA RC1 section | HISTORICAL_VALID but unlabeled | Current Test pins precede an old BA RC1 audit basis/branch/HEAD without a date or historical label. | Date and label the historical section; preserve its provenance evidence. |
| benchmark raw invocation transcript | HISTORICAL_VALID with local path exposure | It is clearly benchmark evidence but includes local usernames and absolute paths. | Review a redacted distribution view while preserving original history according to retention policy. |

## Example neutrality

- Current BA example: Resource Request Submission; the README says it is illustrative and contains no usable Human receipt or approval.
- Current Test VNext example: Resource reservation; it is marked synthetic and supplies no approved handoff or receipt.
- Old Test Appointment/CR-001: explicitly historical V1, not the default.
- Draw.io guide Appointment lifecycle: useful as a compact rule example, but lacks a synthetic/sample label and resembles the historical Test/benchmark domain. Add a label or use the current neutral example.
- PetClinic benchmark names and raw results are contained under benchmark paths and were not treated as current guidance.
- Golden/CR-DWC identifiers occur in Delivery Manifest/G3 remediation history, not in current BA/Test default examples.

No historical file was moved, deleted or changed during this audit.
