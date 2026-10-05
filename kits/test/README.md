# Test Kit Manual VNext

Test Kit turns the exact BA Engineering Handoff VNext into Human-reviewed manual testware. BA owns business WHAT; Test Kit owns canonical Design, canonical Testcases and the two exact Human Gates.

```text
Engineering Handoff VNext
→ Canonical Test Design
→ Human Design Gate
→ APPROVED_DESIGN
→ Canonical Testcases
→ Human Case Gate
→ APPROVED_TESTWARE
```

`APPROVED_TESTWARE` ends the Phase 6 manual lane. Test Automation V1 then creates the exact Phase 7 `EXECUTION_READY` handoff. Test Execution VNext consumes that handoff, runs the approved checks, records Findings, routes Defects through normal Dev VNext `FEATURE_DELIVERY`, and allows only a trusted Tester to create final `VERIFIED` after clean execution or retest.

## Start here

- [Neutral VNext example](examples/vnext/neutral/README.md)
- [Vietnamese Quick Start](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_KIT_QUICKSTART.md)
- [Capabilities and authority boundaries](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_KIT_CAPABILITIES.md)
- [Usage guide](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_KIT_USAGE_GUIDE.md)
- [Workflow and Human Gates](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_KIT_WORKFLOW.md)
- [Project customization](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_KIT_CUSTOMIZATION.md)
- [Installation](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/INSTALLATION.md)
- [Provenance and licenses](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/PROVENANCE.md)
- [Release status](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/RELEASE.md)
- [English overview](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/en/TEST_KIT_README.md)
- [Test Automation V1 (Vietnamese)](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_AUTOMATION_V1.md)
- [Test Automation V1 (English)](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/en/TEST_AUTOMATION_V1.md)
- [Test Execution VNext (Vietnamese)](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/TEST_EXECUTION_VNEXT.md)
- [Test Execution VNext (English)](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/en/TEST_EXECUTION_VNEXT.md)
- [Neutral Automation V1 example](examples/vnext/neutral/automation-v1/README.md)

The Appointment/CR-001 material is retained only as a historical V1 `LEGACY_COMPAT` example. It is not the default VNext flow.

## Install and Doctor

Test Kit supports project-scope installation and requires Python 3.10+. The TEA and Katalon skills are pinned and bundled; installation does not download optional dependencies. XMind and Excel are optional projections.

From the target project, run the installer from the Agent Skills checkout:

```powershell
& '<path-to-agent-skills>\tooling\install.ps1' test --agent codex --scope project
& '<path-to-agent-skills>\tooling\doctor.ps1' test --agent codex --scope project
```

```bash
<path-to-agent-skills>/tooling/install.sh test --agent codex --scope project
<path-to-agent-skills>/tooling/doctor.sh test --agent codex --scope project
```

Doctor `READY` means package/capability readiness only. It does not evaluate BA approval, `APPROVED_DESIGN`, `APPROVED_TESTWARE`, `EXECUTION_READY`, execution results, Findings, retest or verification. Missing optional XMind/Excel dependencies produce `DEGRADED`; required package or integrity failures produce `FAIL`.

Install is idempotent and project-scoped. Reinstall preserves locally edited managed files and reports drift. Uninstall removes only unchanged files owned by this Test Kit; unrelated and modified files remain.

## Authority and gates

- BA Engineering Handoff VNext, backed by exact Human-approved BA baseline proof, is required business authority.
- Canonical trace uses `BR-*` and `FR-*`; `BAREF:*` is locator/provenance only.
- UX is mandatory only when the exact VNext authority context sets `ux_required: true`. If supplied while optional, exact approved UX refs are still validated and bound. Prototype authority remains `REVIEW_EVIDENCE`.
- Test Kit checks exact identity, receipts, revisions and bytes. It does not claim to determine semantic equivalence across free-form prose; Human review owns that judgment.
- Dev Handoff V2 is optional technical context and cannot redefine BA WHAT.
- TEA, Katalon and Project Test Policy are analysis, drafting or non-authoritative guidance.
- XMind derives only from `APPROVED_DESIGN`; Excel derives only from `APPROVED_TESTWARE`. Neither imports authority back into canonical artifacts.
- V1 artifacts are readable only as `LEGACY_COMPAT` with `vnext_authority=false`.
- Delivery Manifest remains deferred and non-authoritative; Test VNext does not require it.

Run the pinned TEA and Katalon skills in the current agent session. Validators reaching `DESIGN_REVIEW` or `CASE_REVIEW` do not approve; only a trusted Human authenticator can accept an exact receipt bound to current snapshots and input refs.
