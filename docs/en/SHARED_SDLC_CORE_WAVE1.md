# Shared SDLC Core — Wave 1

The current integration contracts physically live in `shared/sdlc`. Wave 1
preserves historical imports, artifact schemas, authority, Human approval, and
execution/retest behavior.

| Historical source/caller | Current owner | Compatibility import |
|---|---|---|
| `ba-workflow/scripts/contracts.py` | `authority/contracts.py` | `contracts` |
| `ba-workflow/scripts/approved_baseline.py` | `authority/approved_baseline.py` | `approved_baseline` |
| `ba-workflow/scripts/delivery_manifest.py` | `artifacts/delivery_manifest.py` | `delivery_manifest` |
| `tooling/lib/runtime_paths.py` | `provenance/runtime_paths.py` | `tooling.lib.runtime_paths` |
| `tooling/lib/gate_persistence.py` | `approvals/gate_persistence.py` | `tooling.lib.gate_persistence` |
| `tooling/lib/testware_promotion.py` | `tooling/lib/test_promotion.py` (Wave 2 migration) | `tooling.lib.testware_promotion` |
| `tooling/lib/execution_contract.py` | `findings/execution_contract.py` | `tooling.lib.execution_contract` |

Adapters bind the same module object, including private symbols and patched
globals. Historical module/class names support pickle; the import spec and
source location identify the physical shared owner. Parent attributes support
ordinary dotted imports in both import orders. Core path/persistence contracts
also load when the historical `tooling` package is absent. The Wave 2 ownership
migration and current project contracts are documented in
[Shared SDLC project contracts v1](SHARED_SDLC_CONTRACTS_V1.md). Test promotion
now belongs to its Test adapter above generic Shared publication primitives.

`provenance/references.py` owns two existing profiles: portable feature-relative
Delivery references and exact execution references. Their accepted syntax
remains distinct. Limited YAML parsing is unchanged. Delivery Manifest remains
V2, UX receipt remains V1/V2, and hashes bind integrity/provenance rather than
authenticating a Human.

Artifact/readiness/finding vocabulary defines exactly five/ten/five values.
Existing Doctor outputs and execution routing are unchanged. `authority_ref_ids`
includes structural `BAREF:*` locators; `coverage_ids` contains canonical FR/BR
IDs only. Tester ownership of `VERIFIED` remains unchanged.

## Installed payloads

Test's explicit manifest allowlist installs source under `.test-kit/shared`.
Dev's explicit runtime allowlist installs source under `runtime/v1/shared`.
Existing kit ownership, install records, and hash algorithms remain in use.

BA preserves workflow skill ownership through a deterministic
`ba-workflow/scripts/shared-sdlc-core.zip`, carried inside the skill tree and
loaded through standard zipimport. This archive is derived runtime payload;
canonical editable source is `shared/**`. BA composition/manifest and its
skill-level hash, Doctor, and uninstall semantics remain unchanged. Tests bind
the archive's exact allowlist/bytes to source and check deterministic rebuilds.

After Shared Core source/adapter edits, regenerate affected payloads:

```text
rtk proxy python -m tooling.regenerate_shared_sdlc_payload
rtk proxy python -m tooling.regenerate_test_package
rtk proxy python -m tooling.regenerate_dev_provenance
```

Dev provenance now also binds shared source and the three BA adapters using
the existing algorithm. Dedicated agent profiles keep their current instruction
and plugin payloads; executable runtimes remain in their kit installations.

## Wave 2 boundaries

Wave 2 adds Project Foundation, arc42, topology, shared Project Policy and
generic promotion contracts. Discovery/generation, routing commands, release
lockstep and global vocabulary/output migration remain separate scope.
Package readiness and Human acceptance remain separate gates.

Evidence includes the existing targeted SDLC suites and
`tooling/tests/test_shared_sdlc_core.py`: vocabulary, private symbols, import
orders/dotted imports, pickle, patched globals, exact references, BAREF coverage,
isolated BA/Test/Dev imports, standalone BA validation, and archive provenance.
Windows symlink checks may skip without host privileges; a skip is not PASS.
