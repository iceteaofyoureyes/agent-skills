# Test Kit Manual VNext

Test Kit turns an exact, Human-approved BA Engineering Handoff VNext into Human-reviewed manual testware.

```text
Engineering Handoff VNext
→ Canonical Test Design → Human Design Gate → APPROVED_DESIGN
→ Canonical Testcases → Human Case Gate → APPROVED_TESTWARE
```

Canonical business trace contains `BR-*` and `FR-*`; `BAREF:*` is locator/provenance only. `APPROVED_TESTWARE` is the Phase 6 manual terminal, not `EXECUTION_READY`, execution PASS, `VERIFIED`, or `READY_TO_MERGE`.

Start with the [neutral VNext example](../../kits/test/examples/vnext/neutral/README.md), then follow the Vietnamese [Quick Start](../vi/TEST_KIT_QUICKSTART.md), [capabilities](../vi/TEST_KIT_CAPABILITIES.md), [usage guide](../vi/TEST_KIT_USAGE_GUIDE.md), [workflow](../vi/TEST_KIT_WORKFLOW.md), and [customization guide](../vi/TEST_KIT_CUSTOMIZATION.md). Appointment/CR-001 material is historical V1 `LEGACY_COMPAT`, not the default.

## Install and readiness

Test Kit supports project-scope installation and requires Python 3.10+. TEA and Katalon are pinned and bundled. XMind and Excel are optional derived projections; install does not download optional dependencies.

```powershell
& '<path-to-agent-skills>\tooling\install.ps1' test --agent codex --scope project
& '<path-to-agent-skills>\tooling\doctor.ps1' test --agent codex --scope project
```

Doctor `READY` means package/core capability ready. It does not evaluate BA approval, `APPROVED_DESIGN`, `APPROVED_TESTWARE`, execution, or verification. Optional dependency gaps report `DEGRADED`; required package or integrity failures report `FAIL`.

## Authority boundaries

- BA Engineering Handoff VNext, backed by exact trusted Human proof, is required business WHAT authority.
- UX is required only when exact Test authority context sets `ux_required: true`. Consumed approved UX refs are hash-bound and revalidated; prototypes remain `REVIEW_EVIDENCE`.
- Generic prose such as “API response field”, “input payload”, or “page number” does not infer a UX requirement. Runtime validates authority identity and bytes; Human review owns free-form semantic consistency.
- Dev Handoff V2 is optional technical context and cannot redefine BA WHAT.
- TEA, Katalon and Project Test Policy are analysis, drafting or non-authoritative guidance.
- XMind derives only from `APPROVED_DESIGN`; Excel derives only from `APPROVED_TESTWARE`; neither can import authority back.
- V1 is readable only as `LEGACY_COMPAT` with `vnext_authority=false`.
- Delivery Manifest is `DEFERRED_NON_AUTHORITATIVE` and not required for Test VNext.

Automation planning and execution lifecycle work begin in Phase 7+. See [release status](../vi/RELEASE.md).
