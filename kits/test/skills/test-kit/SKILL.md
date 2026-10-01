---
name: test-kit
description: >-
  Run Test Kit V1 from an approved BA baseline through Human-gated Test Design,
  manual testcase generation, and approved testware. Use the installed runtime.
---

# Test Kit V1 workflow

Use the installed Test Kit package under the active project's `.agents/skills/` tree. Read `.agents/skills/.test-kit/README.md` for operator setup and dependencies. Do not load runtime modules or fixtures from the source repository.

1. Confirm the user supplied an approved BA handoff and its three authoritative sources. Check that the project has `_bmad/tea/config.yaml` for the pinned TEA skill. If `.test-kit/project.yaml` exists, resolve and persist the matching DESIGN or CASES policy before invocation; read the project customization guide when setting it up.
2. Choose a new project-owned run directory. Keep all raw invocations, canonical artifacts, validations, state, and receipts inside it.
3. Adapt the BA baseline and invoke the installed `bmad-testarch-test-design` skill through the shared Codex resolver. Normalize and validate its output before presenting the exact canonical Test Design to the Human.
4. Stop at `DESIGN_REVIEW`. Apply only a Human decision bound to that exact artifact snapshot. Do not continue on a missing, stale, or invalid receipt.
5. After an approved Design Gate, adapt the approved design for the installed `create-test-cases` skill. Invoke Katalon through the shared Codex resolver, normalize and validate the cases, then present the exact canonical testcase snapshot.
6. Stop at `CASE_REVIEW`. Apply only a Human decision bound to that exact snapshot. Produce `APPROVED_TESTWARE` only after the case gate accepts it; material unresolved execution dependencies block approval.
7. Run XMind or Excel projection only after an explicit Human request. Projections do not change canonical artifacts or gate state.

The installed runtime is in `.agents/skills/.test-kit`. Add that directory to Python's import path before importing `tooling.lib.test_kit_v1`, `tooling.lib.test_kit_v1_cases`, or `tooling.lib.test_kit_policy`. The policy module resolves project-owned rules and snapshots; it cannot supply business behavior. `tooling.lib.test_kit_v1` owns BA adaptation, TEA invocation, canonical Design, and Design Gate. `tooling.lib.test_kit_v1_cases` owns Katalon adaptation, canonical cases, and Case Gate. Excel export may resolve `.test-kit/project.yaml`'s `templates.excel.path`; XMind stays on its pinned profile.

Keep business behavior anchored to the approved BA baseline, coverage anchored to the approved Test Design, and execution details anchored to approved project contracts. Record conflicts and return them to the Human who owns that authority. Never use source code or TEA/Katalon planning text to settle a missing Human decision.

V1 stops at approved manual testware and optional projections. Automation execution, triage, and evidence automation are V2 and out of scope.
