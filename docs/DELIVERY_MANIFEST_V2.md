# Delivery Manifest V2: immutable UX approval

V2 replaces the V1 inline `revision:` / `status: APPROVED` UX gate. It accepts immutable UX semantic source bytes together with an external Human approval receipt as approved UX authority. V1 manifests are rejected explicitly; migration requires a V2 manifest and a receipt from the Human approval workflow. Do not modify frozen Golden evidence to migrate it.

The manifest uses `schema_version: 2`. Artifact paths are relative to the manifest's feature directory. `ux.contract` requires `path`, `revision`, and lowercase SHA-256 `sha256`; `ux.approval_receipt` requires `path` and its own exact-byte `sha256`. Both references are mandatory when `ux.required` is true or when a contract is supplied. A receipt without a contract is invalid.

The receipt retains the canonical Human UX approval model. [Its single schema](../tooling/schemas/ux-approval-receipt.schema.json) supports unchanged Golden V1 receipts and generalized V2 receipts. The [synthetic V1 regression fixture](../tooling/tests/fixtures/delivery-ux-canonical/ux/approval-receipt.json) preserves the actual Golden receipt structure, including provenance; its contents are synthetic and do not record a real Human approval. Future contract-only approvals use V2:

```json
{
  "schema_version": 2,
  "feature_id": "CR-001",
  "decision": "APPROVE",
  "decision_type": "HUMAN_EXPLICIT_EXACT_SNAPSHOT_APPROVAL",
  "approved_by": "Human",
  "recorded_at_utc": "2026-10-02T17:04:17Z",
  "revision": "UX-001",
  "immutable": true,
  "semantic_snapshot_sha256": "<aggregate SHA-256>",
  "semantic_snapshot_sha256_method": "UX_APPROVED_SOURCES_CANONICAL_JSON_SHA256_V2",
  "sources": {
    "ux/ux-contract.md": "<UX Contract SHA-256>"
  },
  "source_commit": "<40 lowercase hexadecimal characters>",
  "source_branch": "synthetic/canonical-ux-approval",
  "formal_browser_AT_WCAG_testing": "NOT_RUN",
  "conformance_PASS_claimed": false,
  "reapproval_required_if_source_bytes_change": true
}
```

Receipt feature and immutable revision must match the manifest. Its nonempty `sources` mapping must contain the exact `ux.contract` path/hash and, when present, the exact manifest prototype path/hash. UX Contract is mandatory whenever UX is required; Prototype is optional. A contract-only V2 receipt needs one source and no prototype file or `prototype_authority` field. If review evidence is included in the receipt, `prototype_authority: REVIEW_EVIDENCE` is required; any supplied authority must have that value. Every receipt source is verified even when its optional manifest prototype reference is omitted. Declaring an optional prototype makes its exact approved bytes mandatory for that snapshot. The semantic source needs no inline revision or approval marker, and its bytes remain unchanged after approval.

The validator hashes raw source and receipt bytes, checks the source mapping and manifest hashes, and recomputes the aggregate over the exact approved source set as `sha256(json.dumps(sources, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))`. Sorting makes the result independent of receipt key order. Receipt V2 declares method `UX_APPROVED_SOURCES_CANONICAL_JSON_SHA256_V2` and supports any nonempty approved source set. Receipt V1 preserves the exact Golden method string `SHA-256 of UTF-8 canonical JSON mapping the two relative UX artifact paths to individual SHA-256 values; keys sorted, compact separators.` and its two-source snapshot. Version/method mismatches and unknown declarations fail closed. Existing Golden bytes and aggregate remain valid without reapproval or mutation. Prototype bytes enter the aggregate only when approved as part of that source set, without becoming semantic authority. Missing/tampered receipts or declared sources, wrong revisions, aggregate mismatches, non-Human approval, and non-APPROVE decisions are rejected.

The Human approval workflow must persist a receipt for the exact source reviewed before producing the manifest. A hash proves byte integrity against a trusted manifest; it is not a signature or authentication mechanism. These files do not themselves authenticate the named Human or authorize an agent to create Human approval. Host-authenticated Human provenance remains the responsibility of the approval workflow and audit evidence.

`ux.prototype`, when present, requires `path`, `sha256`, and `authority: REVIEW_EVIDENCE`. It remains review evidence and never substitutes for the semantic source or its Human receipt.

Golden Run `GR-DWC-DEMO-001-20261002-01` exposed the regression: an approved immutable source lacks the inline markers demanded by V1. V2 validates that source unchanged through its external receipt. Active Golden workspace, docs, app, and frozen integration evidence remain untouched.

All three distributed kits carry `delivery_manifest.py`: BA inside its workflow skill, Dev in the external runtime installer, and Test in its explicit package allowlist. The initial breaking V2 contract advanced BA to major 2 and pre-1.0 Dev to minor 0.3. This optional-prototype remediation advances BA `2.0.0-rc.1` → `2.0.0-rc.2`, Dev/plugin `0.3.0-rc.1` → `0.3.0-rc.2`, and Test `2.0.0-rc.2` → `2.0.0-rc.3`, keeping each distributed payload version distinct. Dev install manifests record `kit_version` and exact file hashes; BA install records retain version/skill hashes; Test package authority and both integrity pins are regenerated. Suite locks bind those versions, Delivery Manifest V2, and latest UX receipt V2 (with V1 compatibility) to the exact committed source tree. Upstream vendored skill provenance remains unchanged.

Candidate Windows/G3 remediation advances Dev/plugin to 0.3.0-rc.3 and Test to 2.0.0-rc.4; BA remains 2.0.0-rc.2 with unchanged distributed payload. Delivery V2 and UX receipt guarantees remain unchanged. See docs/vi/GOLDEN_G3_RUNTIME_REMEDIATION.md.
