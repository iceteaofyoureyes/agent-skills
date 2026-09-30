# PetClinic Test Kit benchmark assets

- `tea-test-design/` and `katalon-create-test-cases/` are stable benchmark inputs, captured outputs, and review documentation.
- `foundation-v1-native-profiled/` contains the canonical design fixture and its source evidence used by Test Kit tests.
- `fixtures/` contains stable projection and TEST_ONLY gate inputs, plus a parser-only native TEA input; generated projections are not stored here.
- `tea-test-design/` is the retained copy of the TEA benchmark assets. The redundant ZIP duplicate was removed.

Tests write generated output to OS temporary directories. Manual TEST_ONLY runs should use `.work/benchmark-runs/<run-name>`; `.work/` is ignored.

## Foundation cleanup evidence

`FOUNDATION_LEGACY_DELETION_EVIDENCE: UNVERIFIABLE_AFTER_CLEANUP`

- `foundation-v1/` and `foundation-v1-native/` were untracked and were deleted during the earlier cleanup; no before-hash inventory remains.
- No current test, documentation, or runtime reference requires those directories.
- `foundation-v1-native-profiled/` is the retained supported durable fixture.
- No byte-equivalence claim is made.
