# Input manifest

**Run date:** 2026-09-25  
**Petclinic workspace root:** D:/AI/petclinic

## Spring Petclinic base

The workspace contains two clean source repositories:

| Repository | Path | Git SHA |
|---|---|---|
| Spring Petclinic Angular | D:/AI/petclinic/spring-petclinic-angular | 1978a75eab0c803595d5cde75acc6a0a9bcff4de |
| Spring Petclinic REST | D:/AI/petclinic/spring-petclinic-rest | 4cd8e1b0cd42578e882247d8801f6be5d402f118 |

Both SHAs were rechecked for this Stage 3 run. Current source is supplemental evidence only; no source scan was used to add appointment behavior.

## agent-skills and approved BA baseline

The agent-skills checkout is at cb2b834b45d5a9aadebf5627d7bb966401b1c5f5, matching origin/main when checked.

| Authority | Exact path | SHA-256 |
|---|---|---|
| Approved Business Rules | D:/AI/agent-skills/kits/ba/examples/CR-001/vi/03-approved-business-rules.md | 665127107a9cd764bb3d5d6c610b0de1cebd2f2e3b74d038b1aa8ce454104032 |
| Approved SRS excerpt | D:/AI/agent-skills/kits/ba/examples/CR-001/vi/04-srs-excerpt.md | f8a3aa2ed7d8c2aae57f49b919afcf40c26c905493628429da94b9440d33fc32 |
| Engineering handoff | D:/AI/agent-skills/kits/ba/examples/CR-001/vi/05-engineering-handoff.yml | 54c93b5118afa47be3d374a2c42ebdc6c378936bdfb6f4f228dd539624f7f990 |

The supporting/history files 01-input-requirement.md and 02-gap-review.md were not used to define or override behavior.

## Stage 1–2 Test Design fixture

The previous benchmark's Test Design is used as the Stage 3 fixture under the user's explicit instruction. Its status marker remains unchanged.

| Input | Exact path | SHA-256 |
|---|---|---|
| TEA Test Design | D:/AI/agent-skills/benchmark/test-kit/petclinic/tea-test-design/raw-output/test-design/test-design-epic-1.md | 5022bf91d38a4a0c2b816a6d0065ec74d54d3198c4c39a88211e124b1621c0ab |
| Normalized FR/BR and UNKNOWN matrix | D:/AI/agent-skills/benchmark/test-kit/petclinic/tea-test-design/normalized-output/traceability-matrix.md | 29ffdd5f67576a1e0f5d5fc610804d35b2c2c3cf6c2307888ccecb64e2f32253 |

The raw Test Design contains 14 scenario groups and 28 planned cases (27 P1, 1 P2). Stage 3 decomposes those scenarios into independently runnable cases and merges the overlapping create/view intent where that avoids duplicate coverage. No Test Design business semantics were edited.

## Case-generation boundary

- Testcases are future-feature manual cases; the Appointment feature is not present in the supplied source checkout.
- The test design's unknown maximum duration, list filters, default sorting, and pagination/page size remain unknown. No case asserts an outcome for those items.
- Exact screen labels/routes, editable-field choices, and the interface mapping from duration to interval end are not present in the approved sources. Cases retain business-language actions and mark these details as execution dependencies.
- No Katalon project or requirement repository was queried. FR/BR IDs are source references, not claimed Katalon-synced requirement IDs.
- No testcase was written to Katalon TestOps; no PetClinic source or BA baseline was changed.
