# Release Status

BA Kit **1.0.0-rc.1** is a release candidate and is not yet a functionally accepted release.

Dev Kit and Test Kit remain downstream phases; they are not BA Kit RC1 capabilities.

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

## Runtime functional acceptance

Runtime preflight now **passes** on the isolated route:

~~~text
provider = codex-lb
model = gpt-6-luna
~~~

Project-local skill discovery also passed.

The first full fresh-session CR-001 acceptance completed with:

~~~text
BA_KIT_RC1_CHANGES_REQUIRED
~~~

Key findings:

- current-system discovery in that run was blocked by an HTTP 403 from codex-auto-review;
- gap analysis, Business Rules, and SRS did not meet the semantic golden;
- SRS missed several confirmed behaviors;
- SRS introduced unsupported UI/entry-flow assumptions;
- a validator behavior was reported as a regression but must be reproduced on current HEAD before modification;
- the exact tested repository SHA was not recorded in the report.

The run is therefore **defect-finding evidence**, not final acceptance for the current HEAD.

Current remediation strategy:

~~~text
Tier 1 deterministic tests
→ Tier 2 focused runtime probes
→ one final Tier 3 full fresh-session E2E
~~~

Do not rerun the full 1h+ workflow for every small fix.

## SRS/DOCX/Draw.io capability status

- canonical functional SRS capability: implemented; targeted semantic remediation is in progress;
- DOCX capability: required skill present;
- Word-template support: available through document-docx, but **no default SRS_TEMPLATE.docx is bundled**;
- Draw.io capability: required skill present;
- optional prototype/UI capability: available only when corresponding optional skills are installed.

## Redistribution readiness

BA Kit installer payload:

~~~text
BA_KIT_LICENSE_READY
~~~

Required/core/optional BA payload skills have the provenance/license status needed for redistribution.

Whole repository:

~~~text
REPO_PUBLICATION_BLOCKED
~~~

Some non-BA imports and tracked Skills Manager metadata still need audit/scope decisions.

## What is required for RC1 PASS?

Only after:

1. targeted deterministic/runtime remediation passes;
2. final full fresh-session CR-001 E2E runs against an exact recorded HEAD;
3. semantic comparison passes;
4. final independent review passes;
5. Human accepts the release candidate.

Examples, offline metadata coverage, and package-install passes are not substitutes for runtime acceptance.

---

Tiếng Việt: [Trạng thái phát hành](../vi/RELEASE.md)
