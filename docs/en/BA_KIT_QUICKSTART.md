# BA Kit Quick Start

BA Kit supports this BA flow:

~~~text
Review input
→ discover current system when needed
→ find gaps
→ Human answers
→ Business Rules
→ SRS
→ select and validate a BA baseline candidate
→ HUMAN_REVIEW and stop for Human approval
→ Draw.io / prototype / DOCX when needed
→ authenticated approval receipt from the trusted host
→ revalidate and produce Engineering Handoff VNext
~~~

The BA still owns business decisions and stakeholder communication. The agent primarily **discovers, reviews, asks, structures, documents, visualizes, and validates**.

## What can BA Kit do?

- requirement/gap/edge-case review;
- brownfield discovery from the current project;
- screenshot/Figma export/PDF/HTML-prototype review;
- Business Rule extraction;
- canonical functional SRS create/update;
- DOCX create/edit using a project-provided Word template;
- Draw.io business flow/state/swimlane create/edit;
- optional local UI prototype and visual/accessibility review;
- Human Gates and Engineering Handoff.

See [BA Kit capabilities](BA_KIT_CAPABILITIES.md).

## Install in a project

~~~powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Doctor: **READY** = required capabilities/contracts are present; **DEGRADED** = optional capability missing; **FAIL** = required capability/contract problem.
Doctor reports installed package capability only. It does not report an approved baseline or feature readiness.

## VNext artifacts and approval boundary

- Runtime state: project `workflow-state-vnext.json` (V2); it records workflow progress and is not business authority.
- Canonical authority: Human BA Decisions, Business Rules with stable `BR-*` IDs, canonical SRS with stable `FR-*` IDs, and the selected BA Baseline Candidate/Manifest. `BAREF:*` is locator/provenance only.
- Evidence and gate: exact evidence references and a Human approval receipt supplied and authenticated by the trusted host. BA Kit CLI does not authenticate a person or create approval receipts.
- Handoff: `engineering-handoff.json` (Engineering Handoff VNext), revalidated against the exact candidate, receipt, and source refs.
- DOCX, Draw.io, and optional visual outputs are derived artifacts.

If Project Foundation is available, consume it only with its durable manifest, promotion provenance, Foundation approval receipt, and trusted Foundation host authentication. Foundation READY is context, not BA approval.

V1 `workflow-state.json` and `engineering-handoff.yml` can be read as `LEGACY_COMPAT`; they never establish VNext approval.

## Step 1 — Review the requirement

~~~text
Review this requirement.
For brownfield work, discover the current system first.
Find missing/unclear cases and ask me; do not write the SRS yet.
~~~

For list/CRUD work, expect checks around fields, search/filter, sorting, pagination/page size, actions, state/lifecycle, permissions, validation, empty/loading/error, and edge cases.

## Step 2 — Human clarification

~~~text
Default sort is createdAt DESC.
Default page size is 20.
Cancel applies only in Draft and only Supervisor may use it.
~~~

Answers resolve questions; they do not approve artifacts.

## Step 3 — Business Rules and SRS

~~~text
Build the confirmed Business Rules and keep UNKNOWN separate.
~~~

Then:

~~~text
Create the canonical functional SRS from the confirmed baseline.
Preserve traceability and do not choose technical design.
~~~

## Step 4 — Derived artifacts when needed

### DOCX using a template

~~~text
Export the SRS to DOCX.
Template: docs/templates/COMPANY_SRS_TEMPLATE.docx.
Preserve layout/styles; do not invent missing data.
~~~

The repository does not bundle a default SRS_TEMPLATE.docx. See [SRS and DOCX](SRS_DOCX_GUIDE.md).

### Draw.io

~~~text
Create an editable Draw.io business flow from approved Business Rules/SRS
and export a PNG preview. Do not add new rules.
~~~

See [Draw.io, visual input, and prototypes](DIAGRAMS_PROTOTYPES.md).

### Prototype — optional

~~~text
Create a local prototype from confirmed SRS and visual references for my review.
This is a visual proposal, not production code.
~~~

## Step 5 — Validate and stop at Human review

~~~text
Review the exact BA candidate and source revisions. Do not edit them.
~~~

or:

~~~text
Request changes for candidate revision BA-42: ...
~~~

The workflow moves `DRAFT → VALIDATED → HUMAN_REVIEW` and stops. Only a trusted host may supply the exact authenticated Human approval receipt to reach `APPROVED_BASELINE`. `CONTINUE != APPROVE`; `ANSWER != APPROVE`; validator PASS, Foundation READY, and UX approval do not approve the BA baseline.

## Step 6 — Engineering Handoff

~~~text
After the trusted host supplies approval, revalidate the exact baseline and create Engineering Handoff VNext (`engineering-handoff.json`).
~~~

Only valid from exact `APPROVED_BASELINE` proof and no blocking items. BA owns WHAT; Engineering owns technical HOW.

## Visual input

For screenshot/Figma/PDF/HTML:

~~~text
Review this visual together with the requirement.
Separate observed visual, mismatch, missing decision, and proposal.
Do not infer hidden business rules from the image.
~~~

A Figma link is only directly usable when the runtime has a connector/access; otherwise export screenshot/PDF/local artifacts.

## Example

[Neutral CR-001 example](../../kits/ba/examples/CR-001/README.md) demonstrates the candidate, review gate, BR/FR identity, derived outputs, and handoff boundary.

---

Tiếng Việt: [Hướng dẫn nhanh](../vi/BA_KIT_QUICKSTART.md)
