# Phase 6 Wave 1 Baseline

Base: `ec9955f7c26cd69e2a83d56dfbfba02fb55abc44`

The baseline ran in a detached worktree at the exact semantic base. This Windows machine has global `core.autocrlf=true`; test fixtures that hash raw bytes fail under the default checkout conversion. The baseline worktree was checked out from the same Git index with `git -c core.autocrlf=false checkout-index --all --force` before the canonical-byte run. No repository source was changed.

The XMind SDK was installed from the checked-in `tooling/xmind/package-lock.json` with `npm ci` before projection tests.

| Baseline command | Result |
| --- | --- |
| `python -m unittest tooling.tests.test_test_kit_v1` | PASS, 48 tests |
| `python -m unittest tooling.tests.test_test_kit_v1_case_gate` | PASS, 18 tests |
| `python -m unittest tooling.tests.test_test_kit_v1_cases` | PASS, 57 tests |
| `python -m unittest tooling.tests.test_test_kit_policy` | PASS, 23 tests, 3 skipped |
| `python -m unittest tooling.tests.test_test_kit_policy_review` | NO TESTS RAN |
| `python -m unittest tooling.tests.test_test_kit_customization` | NO TESTS RAN |
| `python -m unittest tooling.tests.test_kit_packaging` | PASS, 32 tests, 1 skipped |
| `python -m unittest tooling.tests.test_ba_vnext` | PASS, 36 tests |
| `python -m unittest tooling.tests.test_dev_vnext` | PASS, 35 tests |
| `python -m unittest tooling.tests.test_sdlc_contracts` | PASS, 23 tests |
| `python -m unittest tooling.tests.test_test_kit_v1_xmind` | PASS, 13 tests |
| `python -m unittest discover -s tooling/tests -p "test_*.py"` | 608 tests, 2 failures, 7 skipped |

The two full-discovery failures are pre-existing Dev package provenance failures:

- `tooling.tests.test_dev_kit.DevKitTests.test_provenance_matches_frozen_component_hashes`: `Dev runtime payload provenance invalid: Dev installed payload digest mismatch`.
- `tooling.tests.test_dev_vnext_installed_acceptance.InstalledDevVNextAcceptance.test_fresh_install_doctor_isolation_flow_and_high_risk_gate`: the Doctor `provenance, licenses, notices and package hashes` check reports the same `Dev installed payload digest mismatch`.

The baseline is captured before implementation edits. Final verification must show the same failures unchanged or resolved.
