# BA Kit Quick Start

BA Kit supports this BA flow:

~~~text
Review input
→ discover current system when needed
→ find gaps
→ Human answers
→ Business Rules
→ SRS
→ Draw.io / prototype / DOCX when needed
→ Human approval
→ Engineering Handoff
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

RC1 **does not bundle a default SRS_TEMPLATE.docx**. See [SRS and DOCX](SRS_DOCX_GUIDE.md).

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

## Step 5 — Review and approve

~~~text
Review SRS revision SRS-42. Do not edit it.
~~~

or:

~~~text
Request changes for SRS-42: ...
~~~

When truly accepted:

~~~text
I approve BR-42 and SRS-42 as the BA baseline for Engineering.
~~~

**Continue is not approval.**

## Step 6 — Engineering Handoff

~~~text
Create the Engineering Handoff.
~~~

Only valid after explicit approval and no blocking items.

## Visual input

For screenshot/Figma/PDF/HTML:

~~~text
Review this visual together with the requirement.
Separate observed visual, mismatch, missing decision, and proposal.
Do not infer hidden business rules from the image.
~~~

A Figma link is only directly usable when the runtime has a connector/access; otherwise export screenshot/PDF/local artifacts.

## Example

[CR-001 Appointment Scheduling](../../kits/ba/examples/CR-001/README.md) demonstrates input → gap review → Human decisions → Business Rules → SRS → diagram/DOCX delivery examples → engineering handoff.

## Current RC1 status

Package/install/Doctor and redistribution licensing have passed their respective checks. Manual checks for Requirement, Business Rules, SRS, and Draw.io have been exercised. Final manual validation of DOCX and final approval/handoff validation remain pending; BA Kit 1.0.0-rc.1 is a Public Preview and is not fully accepted.

See [Release status](RELEASE.md).

---

Tiếng Việt: [Hướng dẫn nhanh](../vi/BA_KIT_QUICKSTART.md)
