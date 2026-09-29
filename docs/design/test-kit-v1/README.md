# Test Kit V1 — approved composition and frozen implementation contracts

**Current status: Test Kit V1 Core, XMind Projection V1, and Excel Projection V1 are HUMAN_ACCEPTED framework capabilities. This acceptance does not approve generated Test Design, Testcases, or Testware for production.**

```text
Approved BA Baseline
→ TEA bmad-testarch-test-design
→ Canonical Test Design
→ Human Design Gate
→ Katalon create-test-cases
→ Canonical Testcases
→ Human Case Gate
→ Approved Testware
→ STOP V1
```

- [Composition and ownership](COMPOSITION.md)
- [Frozen schemas, mappings, normalization, gates, validators](CONTRACTS.md)
- [Implementation order and deferred work](IMPLEMENTATION_PLAN.md)

| Capability | Pinned upstream | Semantic benchmark | Native runtime proof | Patch |
|---|---|---|---|---|
| TEA `bmad-testarch-test-design` | `1f53e9095061ab66f3c35abd9b98baf0f50cf8fe` | `ACCEPT_WITH_THIN_ADAPTER` ([evidence](../../../benchmark/test-kit/petclinic/tea-test-design/README.md)) | `PASS` | None |
| Katalon `create-test-cases` | `e6cdd774f66ce9d45ea5904101a96203e3a37581` | `ACCEPT_WITH_THIN_ADAPTER` ([evidence](../../../benchmark/test-kit/petclinic/katalon-create-test-cases/README.md)) | `PASS` | None |

The local native TEA parser fixture is [test-design-epic-1.md](../../../benchmark/test-kit/petclinic/fixtures/test-only-native-tea-output-v1/test-design-epic-1.md); Katalon output is retained under [katalon-create-test-cases](../../../benchmark/test-kit/petclinic/katalon-create-test-cases/). The native TEA output has 35 atomic TD rows and a documented post-output closeout caveat; Katalon produced 28 cases. The older semantic fixtures have 14 grouped TD rows and 27 cases. These are observed output shapes, not fixed counts or an instruction to merge their IDs. Benchmark permission to consume a Draft design was fixture-only; production Katalon input requires the Design Gate receipt.

XMind and Excel are optional, on-demand projections outside the V1 core, and each V1 projection is HUMAN_ACCEPTED as a framework capability. Their only trigger is `HUMAN_EXPLICIT_REQUEST`; they do not alter canonical data or gate state. Generated projections remain derived outputs, not source-of-truth artifacts or production approvals.

The optional XMind and Excel projection interfaces and Human trigger are documented in [XMind projection](XMIND_PROJECTION.md) and [Excel projection](EXCEL_PROJECTION.md).

## Native invocation dependency

Native TEA and Katalon runs use the shared Codex CLI resolver. A normal installation needs `codex` on `PATH`; `TEST_KIT_CODEX_COMMAND` is an optional executable command name or launcher path override. An explicit override is authoritative and fails closed if invalid. A `.js` override runs through `node` on `PATH`; standard Windows npm `.cmd` and `.ps1` Codex shims resolve to their adjacent pinned-package entrypoint without invoking a shell command string.

Petclinic's current Case Review remains blocked by material OPEN execution dependencies. The TEST_ONLY success path is acceptance evidence only.
