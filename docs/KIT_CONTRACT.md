# Kit contract

- A kit is a manifest plus a workflow entry skill and references to canonical root-level atomic skills.
- Workflow, core, required and optional dependencies are defined once in `kits/<id>/kit.yaml`.
- `ba-workflow` routes work and enforces state/approval boundaries. It does not repeat the detailed procedures owned by atomic skills.
- `workflow-state.json` and `engineering-handoff.yml` are validated by standard-library Python scripts. Invalid required structure, unapproved handoff, hash mismatch, or forbidden technical ownership fields return a nonzero exit.
- Optional capabilities may be missing and yield `DEGRADED`; required capabilities/contracts must be present for `READY`.
- No Dev/Test placeholder skills or manifests are allowed until those products are implemented.
