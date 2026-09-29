# Test Kit fixtures

- `test-design-v1/` is the TEST_ONLY approved design input used by XMind and Excel projection tests.
- `test-only-approved-testware-v1/` is the TEST_ONLY terminal testware input used by Excel tests.
- `test-only-design-gate-receipt.json` is a simulated gate receipt fixture, not a production approval.
- `test-only-native-tea-output-v1/test-design-epic-1.md` is a `TEST_ONLY_EXPECTED_OUTPUT` parser fixture copied byte-exact from the prior PetClinic runtime-proof output at `benchmark/test-kit/petclinic/runtime-proof/raw-output/tea/test-design-epic-1.md`. Its SHA-256 is `1427b54a1cf9d9dfafbca0b663612e8bd30c38525d492a5c1723b42b995be37a`.

These are inputs. Generated projections and test output belong in temporary directories or `.work/benchmark-runs/`.

Absolute paths embedded in retained raw evidence identify original capture locations only; tests resolve repository-local fixtures and do not open those historical paths.
