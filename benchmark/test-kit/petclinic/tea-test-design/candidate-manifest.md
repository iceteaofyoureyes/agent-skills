# Candidate manifest

## Candidate A

- **Upstream:** bmad-code-org/bmad-method-test-architecture-enterprise
- **Repository:** https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise
- **Branch checked:** main
- **Exact commit:** 1f53e9095061ab66f3c35abd9b98baf0f50cf8fe
- **Package version at commit:** 1.27.2
- **Capability:** bmad-testarch-test-design
- **Source used:** src/agents/bmad-tea/SKILL.md, src/workflows/testarch/bmad-testarch-test-design/SKILL.md, workflow.yaml, instructions.md, steps-c/step-01 through step-05, the epic-level template and checklist, and its required knowledge fragments.
- **Upstream run instructions:** docs/how-to/workflows/run-test-design.md
- **TEA source status:** detached at the exact commit; clean; no patch or local workflow edit.

## Invocation and prompt

Codex invocation syntax documented by the pinned upstream workflow:

$bmad-testarch-test-design

Effective invocation used for this run:

> Create an epic-level Test Design for Epic 1, CR-001 Appointment Scheduling, using the pinned bmad-testarch-test-design workflow. Use the adapter only to provide the SRS requirements in the workflow's epic-shaped input structure. Treat the approved Business Rules, SRS excerpt, and engineering handoff as the only business authority. Use current Spring Petclinic source only as supplemental CURRENT_SYSTEM evidence. Preserve source IDs and map scenarios to FR-001 through FR-006 and relevant BR-001 through BR-014. Identify observable expected outcomes. Do not infer or resolve UNKNOWN/TBD decisions. Limit work to requirement analysis, risk assessment, and test design. Do not generate tests, automate, execute tests, export XMind/Excel, or run a release gate. Write in Vietnamese.

Selected workflow options: Create → Epic-level; epic_num=1; run_key=epic-1; design_level=full.

## Adapter/configuration

- Structure adapter: input-adapter/epic-1.md, SHA-256 b902846081b5ea4e447ee84c660330514913c909581418f7e53c2b590ae6862f.
- Native TEA config path: input-adapter/_bmad/tea/config.yaml, SHA-256 d5070e702f56e09f83d6996a7266f29e9fc7a8a814872822c620302da50a54a4.
- No project-specific agent or workflow customization was supplied. The upstream base customize.toml values were used.
- Runtime capability: this session did not expose the TEA skill as a registered executable skill. The run therefore applied the source skill and workflow files directly from the pinned clean checkout, sequentially in Codex. It did not use the package's evaluation/test-design CLI as a substitute for an LLM workflow.
- Browser automation: none. No application was started or inspected.
- Tests: none generated or executed.

## Scope boundary

The run ends after TEA's risk/testability analysis and coverage-plan design. It produced the epic-level design and workflow checkpoint only. No ATDD, automation, test review, trace gate, export, or implementation workflow was invoked.
