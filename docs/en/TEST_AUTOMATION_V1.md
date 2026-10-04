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

Verification covers automation structure/runnability only. It must not execute the stored product execution command or a real SUT. Its `PASS` does not claim API/E2E/SYSTEM/feature PASS, WCAG conformance or `VERIFIED`.

Final readiness requires the exact current Dev Handoff V2 `READY_FOR_TEST`, exact application and automation revisions, resolved required dependencies, exact local references, a passing review, passing automation verification and no scope drift. Phase 7 ends at `EXECUTION_READY`; product execution and defect/retest outcomes are later work.
