# Input manifest

**Run date:** 2026-09-25  
**Petclinic workspace root:** D:/AI/petclinic

## Spring Petclinic base

The workspace root is an aggregate folder, not a Git worktree. It contains these clean source checkouts:

| Repository | Path | Branch | Git SHA |
|---|---|---|---|
| Spring Petclinic Angular | D:/AI/petclinic/spring-petclinic-angular | master | 1978a75eab0c803595d5cde75acc6a0a9bcff4de |
| Spring Petclinic REST | D:/AI/petclinic/spring-petclinic-rest | master | 4cd8e1b0cd42578e882247d8801f6be5d402f118 |

No source files were changed.

## Approved BA baseline

These files were read from the clean agent-skills checkout at cb2b834b45d5a9aadebf5627d7bb966401b1c5f5, which matched origin/main when checked:

| Authority | Exact path | SHA-256 |
|---|---|---|
| Approved Business Rules | D:/AI/agent-skills/kits/ba/examples/CR-001/vi/03-approved-business-rules.md | 665127107a9cd764bb3d5d6c610b0de1cebd2f2e3b74d038b1aa8ce454104032 |
| Approved SRS excerpt | D:/AI/agent-skills/kits/ba/examples/CR-001/vi/04-srs-excerpt.md | f8a3aa2ed7d8c2aae57f49b919afcf40c26c905493628429da94b9440d33fc32 |
| Engineering handoff | D:/AI/agent-skills/kits/ba/examples/CR-001/vi/05-engineering-handoff.yml | 54c93b5118afa47be3d374a2c42ebdc6c378936bdfb6f4f228dd539624f7f990 |

01-input-requirement.md and 02-gap-review.md were not supplied to TEA. They remain supporting/history only and cannot override the approved rules or SRS.

The separate Petclinic workspace file docs/srs/CR-ST-001-SRS.md is a DRAFT about Veterinarian search. It was excluded as unrelated and unapproved for CR-001.

## Supplemental CURRENT_SYSTEM evidence

Current source was used only for stack and existing-test context:

- No Appointment implementation or Appointment-named test was found in either source checkout.
- Angular test inventory includes existing Visit service/list specs and Angular component/service specs.
- REST test inventory includes service and controller tests, including src/test/java/org/springframework/samples/petclinic/rest/controller/VisitRestControllerV1Tests.java.
- src/main/java/org/springframework/samples/petclinic/model/Visit.java currently models Visit with date, description, and Pet. This does not define Appointment business behavior or the field mapping of a future Visit.

These observations did not supply requirements, expected results, API contracts, permission rules, or Visit field-mapping rules.

## Input adapter and configuration

TEA's system-level workflow requires PRD plus ADR/architecture material. The supplied approved baseline has an SRS excerpt and no appointment architecture/ADR. To run the feature-level design through TEA's supported epic-level mode, input-adapter/epic-1.md adds only the structural labels Epic 1 and Acceptance criteria; its six FR statements are copied verbatim from the approved SRS with their stable IDs. It adds no actor, rule, scenario, or behavior.

TEA project configuration was placed at the expected path:

- input-adapter/_bmad/tea/config.yaml
- test_stack_type: fullstack reflects the two current-system repositories.
- tea_browser_automation: none because Appointment is not implemented and no browser observation can inform its behavior.
- Playwright utilities and Pact utilities are disabled; Pact MCP is set to none.
- tea_execution_mode: sequential; no subagents or parallel output generation.
- test_artifacts and output_folder point into this benchmark's raw-output/.
- Communication and document language are Vietnamese.

No TEA source, workflow, template, methodology, Spring Petclinic source, or approved BA baseline was patched.
