# Test Automation V1

Test Automation V1 extends the Test Kit from exact `APPROVED_TESTWARE` VNext to a durable `EXECUTION_READY` handoff.

```text
APPROVED_TESTWARE
→ Automation Suitability
→ Automation Plan
→ Automation Implementation
→ Automation Review
→ Automation Verification
→ EXECUTION_READY
```

The Plan is technical HOW and adds no business approval gate. Approved Testcases remain the expected-behavior oracle. Delivery Manifest stays `DEFERRED_NON_AUTHORITATIVE`.

Resolve the automation repository only through `.sdlc/project-policy.yml` and `.sdlc/project-topology.yml`. Canonical artifacts contain repository identity and relative paths; local roots are runtime inputs. Test Automation never writes an application repository. `UNIT` and `COMPONENT` reference exact evidence from the current Dev Handoff; missing evidence routes to Dev.

Support `UNIT`, `COMPONENT`, `CONTRACT`, `DB_RUNTIME`, `API`, `INTEGRATION`, `E2E`, `ACCESSIBILITY`, `SYSTEM`, `MANUAL_ONLY` and `BLOCKED`. Manual-only Testcases stay as manual protocols. Optional blocked cases remain explicitly referenced to the exact approved Testcase collection in the handoff. Required blocked cases and required open dependencies prevent readiness.

Plan items use stable `AUT-*` IDs and bind exact testcase refs, owner, class, repository, suite, relative paths, project-owned runner, argv arrays, dependencies and BR/FR → TD → TC → AUT trace. No shell command strings or mandatory Playwright.

After implementation starts, material Plan changes require `NEEDS_REPLAN`, a new Plan revision and clearing stale implementation/review/verification evidence. Review is consolidated with a maximum of one full review, one blocking fix wave and one scoped rereview.

The project or implementation agent commits automation changes through its normal Git workflow; the runtime never creates commits. Before recording implementation, require HEAD to descend from the exact Plan `base_revision`, a new commit when automation is planned, a clean worktree/index, no untracked files, and a committed base..HEAD diff containing every planned path and no other paths. Staged-only, unstaged or untracked source fails with `AUTOMATION_COMMIT_REQUIRED`. Implementation evidence records `base_revision`, `repository_revision`, committed `changed_paths`, path SHA-256 hashes and the AUT-to-path mapping. `automation_revision` is the exact Git HEAD commit SHA; any tree digest is supplementary evidence.

Review, verification and `EXECUTION_READY` bind that same clean committed HEAD. Verification does not run if the checkout is dirty or HEAD differs, and it fails closed if it changes automation source. `revalidate_handoff()` checks the declared repository identity, current HEAD, clean checkout, committed source hashes and the review/verification revision bindings, so later edits or commits invalidate readiness and require replan. A fresh clone must be able to checkout the handoff SHA and reconstruct every AUT path.

Verification covers automation structure/runnability only. It must not execute the stored product execution command or a real SUT. Its `PASS` does not claim API/E2E/SYSTEM/feature PASS, WCAG conformance or `VERIFIED`.

Final readiness requires the exact current Dev Handoff V2 `READY_FOR_TEST`, exact application and automation revisions, resolved required dependencies, exact local references, a passing review, passing automation verification and no scope drift. Phase 7 ends at `EXECUTION_READY`; product execution and defect/retest outcomes are later work.
