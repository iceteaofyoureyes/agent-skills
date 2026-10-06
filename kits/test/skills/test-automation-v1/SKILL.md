---
name: test-automation-v1
description: Build, review and structurally verify project-owned automation from exact Approved Testware VNext; stop at EXECUTION_READY.
---

# Test Automation V1

## Boundary

Consume only the exact `APPROVED_TESTWARE` VNext handoff. Revalidate its testcase collection, approved Design, both exact Human Gate receipts, BA VNext handoff and baseline identity, optional UX/Dev context, project-policy context, execution-oracle refs, canonical BR/FR trace and terminal state.

Production Automation rejects Test-only evidence. An internal conformance host may opt in through `AutomationRuntime(test_only_authority_authenticator=...)`; after revalidating the exact Test-only Design and Case receipts, the callback returns `{"authenticated": true, "case_gate_fixture_path": "<project-relative host evidence path>"}`. Automation passes that path through the Test Kit's TEST_ONLY Case Gate API, checks that the path is inside the project, and revalidates authority bytes afterward. The resulting `EXECUTION_READY` handoff remains marked `test_only: true` and `not_for_production: true`. Never use that handoff to authorize a production run.

Do not accept V1/legacy artifacts as authority. Do not create a Human Automation Plan Gate. The plan describes technical HOW and adds no business meaning. Delivery Manifest remains `DEFERRED_NON_AUTHORITATIVE`.

## Suitability and ownership

Create one Suitability row for every approved Testcase, exactly once. Preserve only IDs, class, owner, required flag, technical rationale and typed dependency refs. Never copy the expected result into automation artifacts or use confidence scores as authority.

| Class | Owner |
| --- | --- |
| `UNIT`, `COMPONENT` | `DEV_LOCAL_REFERENCE` |
| `CONTRACT`, `DB_RUNTIME`, `API`, `INTEGRATION`, `E2E`, `ACCESSIBILITY`, `SYSTEM` | `TEST_AUTOMATION` |
| `MANUAL_ONLY` | `MANUAL` |
| `BLOCKED` | `BLOCKED` |

Resolve the automation repository only from `.sdlc/project-policy.yml` and `.sdlc/project-topology.yml`. Never infer it from a directory or repository name. Canonical artifacts store repository identity and relative paths; local roots are runtime inputs.

UNIT/COMPONENT cases reference exact current Dev-local evidence. If it is missing, route the gap to Dev. Never write an application repository.

## Plan and implementation

Use stable `AUT-*` IDs. Every item binds its exact Testcase, class, owner, repository ID, suite, relative planned paths, project-owned runner, execution argv, verification argv, typed dependencies and BR/FR → TD → TC → AUT trace.

Commands are argv arrays. Do not store shell command strings or `shell=true`. Playwright and other frameworks are optional project choices.

Before each write, confirm the current lifecycle, exact Plan revision, automation repository identity, Git base revision, AUT path scope and safe physical path. Reject application repositories and symlink/reparse escapes. The project or implementation agent commits changes through normal Git workflow; the runtime never creates commits. Before recording implementation, require HEAD to descend from the exact Plan base, a new commit when TEST_AUTOMATION items exist, a clean worktree/index, no untracked files, only planned paths in the committed base..HEAD diff, and every planned path in that diff. Reject staged-only, unstaged or untracked source with `AUTOMATION_COMMIT_REQUIRED`. Bind committed blob bytes and SHA-256 evidence, `base_revision`, `repository_revision`, `changed_paths` and AUT-to-path mapping. Do not claim the editor itself is intercepted.

After implementation starts, material Plan edits require `NEEDS_REPLAN`, a new Plan revision, and clearing stale implementation, review and verification evidence. Preserve AUT IDs when their testcase mapping remains.

## Review and verification

Record one consolidated review covering trace, ownership, oracle duplication, fixtures, secrets, cleanup, flakiness, selector/interface stability, dependencies, project conventions and write scope. Limits: one full review, one blocking fix wave and one scoped rereview. Route missing WHAT to BA/Design; never invent expected behavior.

Review and verification bind the exact committed automation Git HEAD. Run verification only against that clean committed revision; fail closed if it changes source. Do not run the stored execution command or a real SUT. A verification `PASS` means only that automation artifacts are structurally/runnably ready. It does not mean API/E2E/SYSTEM/feature PASS, WCAG conformance or `VERIFIED`.

Required `OPEN` dependencies and required `BLOCKED` cases prevent readiness. `RESOLVED` dependencies bind an exact reference. `MANUAL_ONLY` cases remain exact approved execution protocols and do not need AUT source.

## Terminal binding

Before `EXECUTION_READY`, bind the exact current Dev Handoff V2 `READY_FOR_TEST`, canonical Dev validation, current application revisions, exact Dev-local evidence, automation repository identity and exact Git commit SHA, resolved required dependencies, one passing review and automation-only verification for that same SHA. Revalidation checks the clean checkout, committed AUT paths and source hashes. A later local edit or automation commit invalidates readiness and requires replan/review/verification. A fresh clone at the handoff SHA must reproduce the AUT source. If Dev changes a consumed implementation locator, replan.

Produce a durable `HANDOFF_MANIFEST` in state `EXECUTION_READY`. Keep Testcase expected-result prose in the authoritative Approved Testcase. Stop there: real execution, PASS/FINDING, defects, fixes, retest and `VERIFIED` belong to later phases.
