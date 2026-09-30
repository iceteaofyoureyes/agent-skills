# Candidate manifest

## Candidate B

- **Repository:** katalon-labs/true-skills
- **Upstream URL:** https://github.com/katalon-labs/true-skills
- **Pinned revision:** e6cdd774f66ce9d45ea5904101a96203e3a37581
- **Capability:** skills/create-test-cases
- **Canonical skill file:** skills/create-test-cases/SKILL.md
- **Exact references loaded:**
  - skills/create-test-cases/references/requirement-analysis.md
  - skills/create-test-cases/references/istqb-coverage.md
  - skills/create-test-cases/references/manual-test-case-format.md
  - skills/create-test-cases/references/capability-boundaries.md
- **Checkout:** detached at the requested commit; clean; no Katalon source or skill was patched.

## Actual invocation

The runtime did not expose create-test-cases as a registered skill, and no Katalon MCP tools were available. Following the user's allowance, the pinned skill content was loaded and applied sequentially in this Codex session.

Effective invocation:

skills/create-test-cases

Prompt used:

> Generate detailed Vietnamese manual testcase semantic output from the Stage 1–2 TEA Test Design and the approved BA sources listed in input-manifest.md. Treat the Test Design as the authorized fixture even though it is marked Draft; do not change its business meaning. Preserve FR, BR, and recoverable TD references. Follow the pinned create-test-cases skill's requirement analysis, ISTQB-informed coverage, atomic runnable-flow guidance, and manual test case format. Use business/UI actions and separate test data from actions. Do not invent UI labels, error strings, response codes, authorization rules, duration units, maximum duration, list filters, sorting, pagination/page size, or Appointment-to-Visit field mappings. Keep unresolved interface details as execution dependencies. Produce Markdown semantic cases only. Do not access or write Katalon TestOps, create suites, automate, execute, export, or modify PetClinic source.

## Reuse and platform-specific behavior

- **Reusable semantic behavior:** requirement analysis from supplied text; main/alternate/negative coverage; ISTQB techniques as references; one validation intent per independently runnable case; observable expected results; manual case fields and local traceability.
- **Ignored platform behavior:** list_projects/list_repositories, synced requirement lookup, existing TestOps case search, create/update/move/link operations, folder/suite management, Run with AI, manual runs, and execution tools. They are unnecessary or explicitly out of scope.
- **Thin adapter:** map Katalon's Title/Description/Pre-condition/Steps/Expected results/Test data/Priority/Requirement IDs into local Markdown fields Name/Objective/Preconditions/Steps/Expected Result/Test Data/Priority/Requirement refs/Test Design refs.
- **Semantic mismatch:** none observed in the manual-case reasoning. The absence of a registered skill and Katalon MCP limits platform integration evidence, not the case semantics.

No testcase content was imported or written to a Katalon project.
