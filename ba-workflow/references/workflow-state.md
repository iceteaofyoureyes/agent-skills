# Workflow state

Keep one feature-local `workflow-state.json`. New writes use **schema_version 2**, class RUNTIME, through `scripts/ba_vnext.py`. Lifecycle is `DRAFT → VALIDATED → HUMAN_REVIEW → APPROVED_BASELINE`; `activity` retains operational stages. See [VNext contracts](baseline-vnext.md) and `templates/workflow-state-vnext.json`.

V2 carries feature, mode, operation, lifecycle, activity, candidate_revision, artifacts, authoritative_inputs, evidence, gaps, gates, pending, source_of_truth, optional project_foundation, knowledge_impact and append-only history. Exact refs reuse Shared Core path/revision/SHA checks. Unknown fields/versions and secrets fail closed. State is RUNTIME, never business authority. APPROVED_BASELINE requires exact external receipt plus trusted-host Human authentication.

REVIEW never writes/advances. CONTINUE/ANSWER/generated output never approve. EDIT requires explicit edit_scope and preserves unaffected semantics. Candidate edits require a new revision and prior manifest binding, preserve the business identity ledger, return to DRAFT and clear active gates/derived refs. Snapshot bytes remain immutable. Rejection/change requests return to DRAFT. `save_state` validates append-only transition history, rejects stale disk state and writes atomically; the host serializes concurrent writers.

**V1 compatibility:** the historical shape below remains readable as LEGACY_COMPAT, insufficient evidence for VNext approval regardless of arbitrary `stage`. It is never silently migrated into approved V2 state:

```json
{
  "schema_version": 1,
  "feature": {},
  "operation": "",
  "stage": "",
  "artifacts": {},
  "gates": {},
  "pending": [],
  "source_of_truth": {},
  "history": []
}
```

`feature`, `artifacts`, `gates`, and `source_of_truth` are objects; `operation` and `stage` are strings; `pending` and `history` are arrays. Store feature identity/mode, artifact locators/status/hashes, gate targets and explicit decisions, open questions/actions, semantic/visual/delivery sources, and completed actions only when known. Preserve unknown values instead of guessing. The validator checks the required shape and types; it does not infer a stage or approval.

Write state only after a successful artifact action or an explicit Human response. Keep history append-only for recorded checkpoints, and retain existing project state when adding BA Kit metadata.
