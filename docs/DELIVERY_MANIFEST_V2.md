# Delivery Manifest V2: immutable UX approval

V2 replaces the V1 inline `revision:` / `status: APPROVED` UX gate. It accepts immutable UX semantic source bytes together with an external Human approval receipt as approved UX authority. V1 manifests are rejected explicitly; migration requires a V2 manifest and a receipt from the Human approval workflow. Do not modify frozen Golden evidence to migrate it.

The manifest uses `schema_version: 2`. Artifact paths are relative to the manifest's feature directory. `ux.contract` requires `path`, `revision`, and lowercase SHA-256 `sha256`; `ux.approval_receipt` requires `path` and its own exact-byte `sha256`. Both references are mandatory when `ux.required` is true or when a contract is supplied. A receipt without a contract is invalid.

The receipt uses the canonical model already produced by the Golden Human UX workflow. [Its single schema](../tooling/schemas/ux-approval-receipt.schema.json) describes that production contract, not a parallel approval format. The [synthetic regression fixture](../tooling/tests/fixtures/delivery-ux-canonical/ux/approval-receipt.json) preserves the actual Golden receipt structure, including provenance; its contents are synthetic and do not record a real Human approval.

```json
{
  "schema_version": 1,
  "feature_id": "CR-001",
  "decision": "APPROVE",
  "decision_type": "HUMAN_EXPLICIT_EXACT_SNAPSHOT_APPROVAL",
  "approved_by": "Human",
  "recorded_at_utc": "2026-10-02T17:04:17Z",
  "revision": "UX-001",
  "immutable": true,
  "semantic_snapshot_sha256": "<aggregate SHA-256>",
  "semantic_snapshot_sha256_method": "SHA-256 of UTF-8 canonical JSON mapping the two relative UX artifact paths to individual SHA-256 values; keys sorted, compact separators.",
  "sources": {
    "ux/ux-contract.md": "<UX Contract SHA-256>",
    "ux/prototype.html": "<Prototype SHA-256>"
  },
  "source_commit": "<40 lowercase hexadecimal characters>",
  "source_branch": "synthetic/canonical-ux-approval",
  "prototype_authority": "REVIEW_EVIDENCE",
  "formal_browser_AT_WCAG_testing": "NOT_RUN",
  "conformance_PASS_claimed": false,
  "reapproval_required_if_source_bytes_change": true
}
```

Receipt feature and immutable revision must match the manifest. Its `sources` mapping must contain the exact `ux.contract` path/hash and, when present, the exact manifest prototype path/hash. It always contains the two distinct artifacts reviewed by the canonical workflow; both files are verified even if the manifest omits its optional prototype reference. Prototype authority must be `REVIEW_EVIDENCE` in both documents. The semantic source needs no inline revision or approval marker, and its bytes remain unchanged after approval.

The validator hashes raw source and receipt bytes, checks the source mapping and manifest hashes, and recomputes the aggregate as `sha256(json.dumps(sources, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))`. This matches the declared Golden method; unknown method declarations fail closed. Sorting makes the result independent of receipt key order. The aggregate covers the Prototype's reviewed bytes without granting it semantic authority. Missing/tampered receipts or sources, wrong revisions, aggregate mismatches, non-Human approval, and non-APPROVE decisions are rejected. Runtime validation checks cross-document equality and file integrity beyond schema shape.

The Human approval workflow must persist a receipt for the exact source reviewed before producing the manifest. A hash proves byte integrity against a trusted manifest; it is not a signature or authentication mechanism. These files do not themselves authenticate the named Human or authorize an agent to create Human approval. Host-authenticated Human provenance remains the responsibility of the approval workflow and audit evidence.

`ux.prototype`, when present, requires `path`, `sha256`, and `authority: REVIEW_EVIDENCE`. It remains review evidence and never substitutes for the semantic source or its Human receipt.

Golden Run `GR-DWC-DEMO-001-20261002-01` exposed the regression: an approved immutable source lacks the inline markers demanded by V1. V2 validates that source unchanged through its external receipt. Active Golden workspace, docs, app, and frozen integration evidence remain untouched.

All three distributed kits carry `delivery_manifest.py`: BA inside its workflow skill, Dev in the external runtime installer, and Test in its explicit package allowlist. BA advances `1.0.0-rc.1` → `2.0.0-rc.1` for the breaking downstream authority contract; pre-1.0 Dev advances `0.2.0-rc.1` → `0.3.0-rc.1` (including its plugin); Test advances its unreleased major candidate `2.0.0-rc.1` → `2.0.0-rc.2`. These identify distinct payloads. The Dev install manifest records `kit_version` plus exact file hashes; BA install records retain version/skill hashes; Test package authority and both integrity pins are regenerated after the runtime/version changes. Suite locks bind all three new versions, Delivery Manifest V2, and canonical UX receipt V1 to the exact committed source tree. Upstream vendored skill provenance remains unchanged.
