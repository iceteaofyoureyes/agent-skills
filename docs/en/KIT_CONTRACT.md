# Kit contract

Tiếng Việt: [Hợp đồng Kit](../vi/KIT_CONTRACT.md)

- A kit is a manifest plus a workflow entry skill and references to canonical root-level atomic skills.
- Workflow, core, required and optional dependencies are defined once in `kits/<id>/kit.yaml`.
- `ba-workflow` routes work and enforces state/approval boundaries. It does not repeat the detailed procedures owned by atomic skills.
- `workflow-state.json` and `engineering-handoff.yml` are validated by standard-library Python scripts. Invalid required structure, unapproved handoff, hash mismatch, or forbidden technical ownership fields return a nonzero exit.
- Optional capabilities may be missing and yield `DEGRADED`; required capabilities/contracts must be present for `READY`.
- The current Test Kit is a separate manifest-driven Kit with Manual, Automation, and Execution VNext; V1 artifacts remain LEGACY_COMPAT and read-only. Generic manifests may declare explicit skill source directories, managed files, capabilities, prerequisites, and optional local integrity anchors. An integrity-enabled installed Kit pins its authority inventory and payload digest in the local package definition; Doctor checks those identities and actual managed bytes. Legacy BA manifests remain supported. See the [Vietnamese Kit contract](../vi/KIT_CONTRACT.md) and [packaging contract](../../tooling/PACKAGING.md).
