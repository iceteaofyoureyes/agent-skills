# Dev Kit V1 — Lean Execution Workflow

## Runtime files

- Spec Kit definitions: `kits/dev/plugin/workflows/dev-normal.workflow.yml`, `dev-high-risk.workflow.yml`.
- TRIVIAL: `start` → edit → `finish-trivial`; không dùng Spec Kit, plan, review hoặc gate.
- Dev policy/state adapter: `tooling/lib/dev_kit.py`.
- Change inputs/evidence: `.devkit/runs/<change_id>/`; Spec Kit pause/resume state: `.specify/workflows/runs/<run_id>/`.
- Operator commands/examples: [DEV_KIT_USAGE_GUIDE.md](DEV_KIT_USAGE_GUIDE.md).

Each workflow uses only top-level persisted steps. The HIGH_RISK gate is top-level so resume does not rerun planning; review/fix/re-review steps are also top-level. Static shell commands take no untrusted interpolated values.

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

Không ép formal plan/tasks, independent review hoặc specialist skills nếu không có risk signal.

### NORMAL

```text
Spec Readiness
→ Planning Preflight
→ Technical plan/tasks
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
→ technical plan/tasks
→ Human/Tech Lead gate where policy requires
→ incremental implementation + relevant specialists
→ ONE consolidated review
→ ONE blocking-fix wave
→ optional ONE scoped re-review
→ fresh verification
→ Dev Handoff
```

Routing starts from `tooling/lib/dev_kit.py start`. It records the route and required deterministic commands in `.devkit/runs/<change_id>/input.json`; the matching workflow begins with `assert-workflow` and refuses a mismatched risk depth.

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
- Approved BA Baseline SHA-256 thay đổi → workflow dừng; BA phải duyệt revision mới và Dev tạo run mới.

## 6. Review budget

```text
max_full_reviews = 1
max_blocking_fix_waves = 1
max_scoped_rereviews = 1
```

Scoped re-review chỉ verify prior findings + breakage introduced by fix diff.
