# Release Status

## Test Kit Manual VNext

The current Test Kit package candidate is **`2.0.0-rc.6`**. It is a prerelease branch candidate, not stable `2.0.0`, a GitHub release, tag, or published artifact.

The default manual lane is:

```text
Engineering Handoff VNext
→ Test Design → Human Design Gate → APPROVED_DESIGN
→ Testcases → Human Case Gate → APPROVED_TESTWARE
```

`APPROVED_TESTWARE` ends the Phase 6 manual lane. It does not mean `EXECUTION_READY`, execution PASS, `VERIFIED`, or `READY_TO_MERGE`. Automation and execution lifecycle work belong to Phase 7+.

Phase 6 completion is gated by the three tiers in [`kits/test/acceptance.yaml`](../../kits/test/acceptance.yaml). Tier 3 fresh installed-runtime acceptance is mandatory; Tier 1/2 alone cannot mark Phase 6 complete. An acceptance result applies only to the exact branch and commit verified.

Doctor `READY` means package/core capability ready. Missing optional XMind/Excel dependencies report `DEGRADED`; required package, integrity, or capability failures report `FAIL`. Doctor does not evaluate BA approval, Design/Case approval, or execution state.

## Other Kits and history

Test Kit Manual VNext is a separate Kit and can coexist with BA Kit. Other repository documents retain their own Kit versions and acceptance history.

See [Test Kit overview](TEST_KIT_README.md), [Vietnamese installation guide](../vi/INSTALLATION.md), [provenance](../vi/PROVENANCE.md), and the [Vietnamese release status](../vi/RELEASE.md). TEA/Katalon pins, licenses, notices and package authority are maintained by repository tooling; hashes are regenerated, never hand-edited.
