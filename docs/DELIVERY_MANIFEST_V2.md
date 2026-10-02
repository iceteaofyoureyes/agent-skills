# Delivery Manifest V2: immutable UX approval

V2 replaces the V1 inline `revision:` / `status: APPROVED` UX gate. It accepts immutable UX semantic source bytes together with an external Human approval receipt as approved UX authority. V1 manifests are rejected explicitly; migration requires a V2 manifest and a receipt from the Human approval workflow. Do not modify frozen Golden evidence to migrate it.

The manifest uses `schema_version: 2`. Artifact paths are relative to the manifest's feature directory. `ux.contract` requires `path`, `revision`, and lowercase SHA-256 `sha256`; `ux.approval_receipt` requires `path` and its own exact-byte `sha256`. Both references are mandatory when `ux.required` is true or when a contract is supplied. A receipt without a contract is invalid.

The receipt is a separate JSON or supported YAML mapping document:

```json
{
  "schema_version": 1,
  "feature_id": "DWC-DEMO-001",
  "source": {
    "path": "ux/semantic-contract.md",
    "revision": "UX-R1",
    "sha256": "<64 lowercase hexadecimal characters>"
  },
  "approver": {"role": "HUMAN", "identity": "human-identity"},
  "decision": "APPROVE"
}
```

`source` must exactly equal the manifest's `ux.contract` reference, including path, revision, and hash. The receipt feature must match the manifest feature. The receipt must name a nonblank Human identity and the explicit decision `APPROVE`. The semantic source does not need any inline approval or revision marker, and its bytes must remain unchanged after approval. Revision is an immutable external identifier bound by the receipt, not a marker injected into source content.

The validator hashes raw source bytes and raw receipt bytes, checks both against the manifest, then validates feature, source, revision, approver, and decision bindings. Missing receipts, changed bytes, mismatched revisions or hashes, and any other decision fail closed. Schema definitions describe document shape; runtime validation additionally verifies files, hashes, and cross-document equality.

The Human approval workflow must persist a receipt for the exact source reviewed before producing the manifest. A hash proves byte integrity against a trusted manifest; it is not a signature or authentication mechanism. These files do not themselves authenticate the named Human or authorize an agent to create Human approval. Host-authenticated Human provenance remains the responsibility of the approval workflow and audit evidence.

`ux.prototype`, when present, requires `path`, `sha256`, and `authority: REVIEW_EVIDENCE`. It remains review evidence and never substitutes for the semantic source or its Human receipt.

Golden Run `GR-DWC-DEMO-001-20261002-01` exposed the regression: an approved immutable source lacks the inline markers demanded by V1. V2 validates that source unchanged through its external receipt. Active Golden workspace, docs, app, and frozen integration evidence remain untouched.
