# Neutral Automation V1 example

This directory illustrates references and field shapes only. It contains no Human approval receipt and grants no authority.

Use the installed Test Kit runtime with an exact Approved Testware VNext manifest and a project-owned `.sdlc/project-policy.yml` plus `.sdlc/project-topology.yml`. Resolve the automation repository by the policy role. Keep all paths relative in canonical artifacts.

Example API and E2E items use argv arrays. The E2E runner is a neutral `project-native` placeholder; no framework is mandatory. `execution_command` is retained for a later phase and is never run by Phase 7 verification.

`UNIT` and `COMPONENT` point to exact Dev-local evidence. `MANUAL_ONLY` remains a manual protocol. Required `BLOCKED` or `OPEN` dependencies stop `EXECUTION_READY` until a valid replan.

Phase 7 ends at `EXECUTION_READY`. This example does not represent a product execution, PASS, finding, defect or `VERIFIED` state.
