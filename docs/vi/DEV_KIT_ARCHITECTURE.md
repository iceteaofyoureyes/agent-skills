# Dev Kit V1 — Kiến trúc

## Mục tiêu

Dev Kit nhận **Approved BA Baseline** và chịu trách nhiệm:

```text
BA Kit = WHAT
Dev Kit = WHERE / WHO OWNS + HOW
Test Kit = HOW DO WE PROVE IT
```

Dev Kit không được biến implementation reasoning thành business truth mới.

## Authority

| Concern | Authority |
|---|---|
| Business behavior / WHAT | Approved BA Baseline |
| Technical ownership / blast radius | Dev Engineering Impact |
| Implementation design / HOW | Dev Plan |
| Code correctness evidence | deterministic verification + consolidated review |
| Final business acceptance | Human/Test Kit downstream |

Business ambiguity làm thay đổi user-visible behavior phải trả về `NEEDS_BA_CLARIFICATION`. Technical ambiguity có thể được giải quyết trong planning nếu không thay đổi approved semantics.

## Kiến trúc capability

```text
Approved BA Baseline
        │
        ▼
Spec Readiness
        │
        ▼
Planning Preflight
  ├─ relevant code/context
  ├─ lightweight Engineering Impact
  ├─ risk classification
  ├─ implementation approach
  └─ test strategy
        │
        ▼
Risk-gated technical plan/tasks
        │
        ▼
Incremental Implementation
        │
        ▼
ONE Consolidated Review
        │
        ▼
ONE Blocking Fix Wave
        │
        ├─ low/normal fix → verify
        └─ material risk change → ONE scoped re-review → verify
        │
        ▼
Dev Handoff / READY_FOR_TEST
```

Conditional capabilities không tạo mandatory stages. Security, API, source-grounding, performance, observability, debugging và CBM chỉ được activate khi trigger/risk phù hợp.

## Community reuse

- **GitHub Spec Kit**: workflow/state/bundle engine; runtime dependency. V1 không dùng core `specify/plan/tasks/analyze/converge` vì các command đó dựa trên Spec Kit `spec.md`, có nguy cơ tạo WHAT song song với Approved BA Baseline.
- **Addy Agent Skills**: technical planning + atomic engineering behavior. `planning-and-task-breakdown` được minimal-adapt đúng 2 dòng Human-gate để tuân risk policy của Dev Kit.
- **Superpowers verification-before-completion**: final evidence-before-claim gate.
- **Superpowers review-package**: candidate utility để đóng gói BASE..HEAD cho reviewer.
- **codebase-memory-mcp**: conditional structural evidence, không phải source of truth.
- **requirements-gap-auditor**: reuse canonical skill ở Dev Intake, readiness-only.

## Project-owned phần tối thiểu

- BA→Dev authority boundary;
- risk classifier;
- Engineering Impact contract;
- routing policy;
- bounded review budget;
- Dev Handoff contract;
- Doctor/context-purity policy;
- benchmark/evals;
- release evidence.

## Nguyên tắc chống over-engineering workflow

1. Capability available không có nghĩa capability phải chạy.
2. Normal path phải ngắn hơn high-risk path.
3. Không spawn independent reviewer sau mỗi slice.
4. Không full-review lại từ đầu sau fix.
5. Nếu sau bounded fix/re-review vẫn còn blocker lớn: `NEEDS_REPLAN` hoặc Human/Tech Lead review, không loop vô hạn.
