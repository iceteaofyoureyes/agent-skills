# Workflow state

Keep one project-local `workflow-state.json` for the BA workflow. Its required top-level structure is:

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
