# Release Status

## Test Kit Manual VNext

The current Test Kit package candidate is **`2.0.0-rc.12`**. It is a prerelease branch candidate, not stable `2.0.0`, a GitHub release, tag, or published artifact.

The default manual lane is:

```text
Engineering Handoff VNext
→ Test Design → Human Design Gate → APPROVED_DESIGN
→ Testcases → Human Case Gate → APPROVED_TESTWARE
```

`APPROVED_TESTWARE` ends the Phase 6 manual lane. Phase 7 Test Automation V1 proceeds through Suitability, Plan, implementation, review and automation-only verification, then stops at `EXECUTION_READY`. Phase 8 consumes that exact handoff for execution, Tester Finding classification, Dev VNext fix acceptance, retest and Tester-owned `VERIFIED`. It does not create `READY_TO_MERGE`.

Phase 6 completion is gated by the three manual tiers in [`kits/test/acceptance.yaml`](../../kits/test/acceptance.yaml). Phase 7 completion additionally requires Tier 4 fresh installed Automation V1 acceptance and the full regression. An acceptance result applies only to the exact branch and commit verified.

Doctor `READY` means required package/capability readiness only. It does not mean `APPROVED_TESTWARE`, Dev `READY_FOR_TEST`, `EXECUTION_READY`, PASS, absence of Findings, `READY_FOR_RETEST`, `VERIFIED`, or `READY_TO_MERGE`. Missing optional XMind/Excel dependencies report `DEGRADED`; required package, integrity, or capability failures report `FAIL`.

## Other Kits and history

Test Kit Manual VNext is a separate Kit and can coexist with BA Kit. Other repository documents retain their own Kit versions and acceptance history.

See [Test Kit overview](TEST_KIT_README.md), [Vietnamese installation guide](../vi/INSTALLATION.md), [provenance](../vi/PROVENANCE.md), and the [Vietnamese release status](../vi/RELEASE.md). TEA/Katalon pins, licenses, notices and package authority are maintained by repository tooling; hashes are regenerated, never hand-edited.
