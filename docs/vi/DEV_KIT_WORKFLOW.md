# Dev Kit V1 — Lean Execution Workflow

## 1. Spec Readiness

Câu hỏi duy nhất:

> Approved BA Baseline đã đủ để Dev triển khai mà không phải invent business behavior chưa?

Check nhẹ:
- contradiction;
- blocking UNKNOWN/TBD;
- missing behavior buộc Dev chọn business semantics;
- approved SRS mâu thuẫn current-system evidence theo cách cần BA quyết định.

Kết quả:

```text
READY_FOR_PLANNING
or
NEEDS_BA_CLARIFICATION
```

Technical choices không được đẩy ngược về BA nếu chúng không thay đổi WHAT.

## 2. Planning Preflight

Một planning pass thực hiện:
- inspect code/context liên quan;
- lightweight Engineering Impact;
- xác định repo/module/interface/data bị ảnh hưởng;
- classify TRIVIAL / NORMAL / HIGH_RISK;
- implementation approach;
- test strategy;
- tasks/slices.

CBM chỉ gọi nếu blast radius chưa đủ chắc.

## 3. Execution paths

### TRIVIAL

```text
Understand
→ Edit
→ Relevant deterministic check
→ Complete
```

Không ép Spec Kit plan/tasks, independent review hoặc specialist skills nếu không có risk signal.

### NORMAL

```text
Spec Readiness
→ Planning Preflight
→ Spec Kit plan/tasks
→ Incremental Implementation + focused verification
→ ONE consolidated review
→ ONE blocking-fix wave
→ fresh deterministic verification
→ Dev Handoff
```

### HIGH_RISK

Triggers điển hình:
- auth/authz;
- sensitive/regulated data;
- DB schema/migration;
- public API/event contract;
- cross-service/cross-repo change;
- concurrency/transaction semantics;
- major architecture/deployment topology.

```text
Spec Readiness
→ Deep Engineering Impact
→ plan/tasks
→ analyze when warranted
→ Human/Tech Lead gate where policy requires
→ incremental implementation + relevant specialists
→ converge when drift risk warrants
→ ONE consolidated review
→ ONE blocking-fix wave
→ optional ONE scoped re-review
→ fresh verification
→ Dev Handoff
```

## 4. Implementation discipline

Per slice:
1. implement smallest complete slice;
2. use TDD/regression test when behavior warrants;
3. run focused repository-native check;
4. continue.

Không spawn independent reviewer cho từng normal slice.

## 5. Stop conditions

- Business ambiguity → `NEEDS_BA_CLARIFICATION`.
- Plan invalidated by implementation evidence → `NEEDS_REPLAN`.
- Review budget exhausted with Critical/Important blocker → Human/Tech Lead decision, không review #3.
- Verification red → không claim READY_FOR_TEST.

## 6. Review budget

```text
max_full_reviews = 1
max_blocking_fix_waves = 1
max_scoped_rereviews = 1
```

Scoped re-review chỉ verify prior findings + breakage introduced by fix diff.
