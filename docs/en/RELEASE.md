# Release Status

BA Kit **1.0.0-rc.1** is a **Public Preview**, not a fully accepted release.

Dev Kit and Test Kit are **Planned**; neither is included in this BA Kit preview.

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
