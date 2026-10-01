# Release Status

BA Kit **1.0.0-rc.1** is a **Public Preview**, not a fully accepted release.

Dev Kit remains **Planned**. Test Kit V1.1 is a separate committed Kit, not part of the BA Kit preview.

## Test Kit V1.1

Test Kit V1 Core, XMind Projection V1, Excel Projection V1, Packaging Cleanup, Packaging V1, and the V1.1 Project Customization & Policy Layer have been Human accepted as framework capabilities. The package manifest is `1.1.0`. The Packaging V1 baseline was committed at `55e88c39cd97945ee8c2e1b4f152599449966ddb`; subsequent documentation/package-identity revisions are tracked by repository history. **Internal Human acceptance is not a GitHub release, tag, or published artifact.** It does not approve any project's generated Design, Testcases, or Testware; those still need current authenticated Human Gate receipts. TEST_ONLY artifacts are not production testware. Project policy remains non-authoritative testing guidance and is hash/snapshot-bound to the relevant Human Gates. Automation Test V2 is not included. Start with the [Test Kit overview](TEST_KIT_README.md) and the [Vietnamese customization guide](../vi/TEST_KIT_CUSTOMIZATION.md).

## Package / installer

Evidence exists for the corresponding package checks:

- Codex project install;
- idempotent reinstall;
- Doctor READY;
- safe uninstall;
- project isolation;
- generic PowerShell/Bash structural paths;
- Claude Code structural install.

These checks prove package/install behavior, not runtime BA semantics.

## Manual preview checks

Manual checks have been exercised for Requirement, Business Rules, SRS, and Draw.io.

Final manual validation of DOCX and final validation of approval/handoff remain pending.

BA Kit 1.0.0-rc.1 remains a Public Preview and is not fully accepted.

## SRS/DOCX/Draw.io capability status

- canonical functional SRS capability: implemented; manual check exercised;
- DOCX capability: required skill present; final manual validation pending;
- Word-template support: available through document-docx, but **no default SRS_TEMPLATE.docx is bundled**;
- Draw.io capability: required skill present; manual check exercised;
- optional prototype/UI capability: available only when corresponding optional skills are installed.

## Redistribution readiness

BA Kit installer payload:

~~~text
BA_KIT_LICENSE_READY
~~~

Required/core/optional BA payload skills have the provenance/license status needed for redistribution.

## Remaining validation

Final manual validation of DOCX and final validation of approval/handoff remain pending. BA Kit 1.0.0-rc.1 must not be described as fully accepted.

---

Tiếng Việt: [Trạng thái phát hành](../vi/RELEASE.md)
