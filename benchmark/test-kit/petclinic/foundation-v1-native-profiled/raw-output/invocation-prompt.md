$bmad-testarch-test-design

Invoke the installed project-local native skill bmad-testarch-test-design at the pinned upstream revision. Complete an epic-level Test Design for Epic 1. Do not read or copy the skill file to simulate execution.

Business authority and inputs:
- Structural epic wrapper (FR IDs and wording are copied from the approved SRS): D:\AI\agent-skills\benchmark\test-kit\petclinic\foundation-v1-native-profiled\inputs\adapter\epic-1.md
- Separate approved Business Rules context; do not merge BRs into FR acceptance criteria: D:\AI\agent-skills\benchmark\test-kit\petclinic\foundation-v1-native-profiled\inputs\adapter\business-rules.md
- BA open decisions and UNKNOWN clauses; preserve them without answering them: D:\AI\agent-skills\benchmark\test-kit\petclinic\foundation-v1-native-profiled\inputs\adapter\open-decisions.md
- CURRENT_SYSTEM / SUPPLEMENTAL only: D:\AI\agent-skills\benchmark\test-kit\petclinic\foundation-v1-native-profiled\inputs\adapter\current-system-supplemental.md
- Approved baseline handoff and source files are under D:\AI\agent-skills\benchmark\test-kit\petclinic\foundation-v1-native-profiled\inputs\baseline; use only the SRS and Business Rules as business authority.

Keep the output in Vietnamese. Preserve every FR and BR ID and the source wording. Do not infer UI/API behavior or fill an UNKNOWN. Produce testability/risk analysis and Test Coverage Plan scenarios with explicit traceability and observable outcomes. TEA priorities, risk, level, count, effort, and thresholds are advisory only. Do not generate code/automation, run tests, export XMind/Excel, access TestOps, modify PetClinic source, or give a release verdict.

For the Test Coverage Plan, use the already-approved native raw profile exactly: group rows under P0, P1, P2, P3 headings and use this six-column header without additions or renaming: `Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được`. Keep scenario title, explicit FR/BR trace, and observable outcome in their separate columns. Preserve the upstream Test ID spelling exactly; do not rename or renumber IDs.

Write the final Test Design to D:\AI\agent-skills\benchmark\test-kit\petclinic\foundation-v1-native-profiled\raw-output\test-design-epic-1.md. Intermediate outputs must remain in that run's raw-output folder.
