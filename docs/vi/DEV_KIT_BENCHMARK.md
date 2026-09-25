# Dev Kit V1 — Benchmark Contract

## Mục tiêu

Benchmark **một composition V1 đã freeze**, không chạy ma trận combinatorial của nhiều skill packs.

## Arms

### CONTROL
Codex native trên cùng fixture/repo/model/permissions.

### CANDIDATE
Codex + Dev Kit V1 composition.

Hai arm phải dùng cùng:
- approved BA baseline;
- repository SHA;
- model/reasoning setting;
- tool permissions;
- deterministic test/build environment.

Benchmark candidate phải chạy trong context-isolated mode; unrelated global skills/plugins/hooks làm run invalid.

## Scenario set — Petclinic

Tối thiểu:
1. small/local feature;
2. ambiguous requirement cần escalation;
3. regression bug;
4. search/API compatibility change;
5. security-sensitive endpoint;
6. cross-component feature.

## Primary metrics

- functional/hidden-test correctness;
- requirement fidelity;
- scope creep/unrequested behavior;
- regression safety;
- security oracle;
- Engineering Impact precision/recall;
- files/LOC/dependencies touched relative to necessary scope;
- correctness của completion claims.

## Secondary metrics

- human turns;
- tool calls;
- tokens;
- wall-clock time;
- review/fix rounds.

Không tối ưu token bằng cách làm giảm primary quality metrics.

## Hard failures

Candidate fail nếu:
- mutate Approved BA Baseline/business semantics;
- invent unresolved business rule;
- self-approve Human gate;
- silently cross ownership/risk boundary;
- bypass/disable failing tests;
- weaken/delete tests chỉ để green;
- claim success không có fresh evidence;
- review loop vượt budget thay vì `NEEDS_REPLAN`/Human escalation.

## Remediation policy

Benchmark failure:
```text
failure ID
→ root cause
→ minimal capability/routing change
→ rerun failing scenario
→ regression benchmark
```

Không thêm skill/framework mới nếu chưa chứng minh gap hiện tại không thể sửa bằng selected capability/routing.

## Release evidence

Dev Kit chưa được gọi RC chỉ vì installer/Doctor pass. RC yêu cầu ít nhất:
- provenance/license READY;
- structural/package tests PASS;
- benchmark threshold PASS;
- fresh-session runtime acceptance PASS;
- docs/example contract PASS;
- Human approval.
