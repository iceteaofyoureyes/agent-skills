# Dev Kit V1 — Capability Selection

> Candidate selection snapshot: 2026-09-25. Runtime acceptance chưa thực hiện.

## Core/default capability owners

| Capability | Owner | Trigger | Không dùng khi |
|---|---|---|---|
| Spec readiness | requirements-gap-auditor | mọi approved BA baseline, nhưng deep audit chỉ khi có signal | không dùng để tự sửa WHAT |
| Technical planning/tasks | Addy planning-and-task-breakdown (2-line minimal adaptation) | normal/high-risk | trivial mechanical change |
| Incremental implementation | Addy incremental-implementation | multi-file/non-trivial change | tiny single-function edit |
| TDD/regression | Addy test-driven-development | behavior change/bug/legacy area being changed | docs/static/config-only |
| Consolidated code review | Addy code-review-and-quality | normal/high-risk feature complete | trivial change nếu policy không yêu cầu independent review |
| Final evidence gate | verification-before-completion | trước success/READY_FOR_TEST claim | không skip |

## Conditional capability pool

| Capability | Owner | Trigger |
|---|---|---|
| Debugging | Addy debugging-and-error-recovery | unexpected test/build/runtime failure |
| Security deep reasoning | Addy security-and-hardening | auth/authz, untrusted input, sensitive data, external trust boundary |
| API/interface | Addy api-and-interface-design | public/module/interface/API/event contract change |
| External source grounding | Addy source-driven-development | framework/library/API behavior không chắc chắn |
| Performance | Addy performance-optimization | measured/requested perf risk/regression |
| Observability | Addy observability-and-instrumentation | endpoint/job/queue/external I/O cần production diagnosability |
| Code graph | codebase-memory-mcp | blast radius/caller/dependency chưa đủ chắc bằng native code reading |
| Scoped re-review | project-owned contract informed by Superpowers | blocking fix materially changes logic/risk surface |

## Capability không chọn cho default V1

- Ponytail / ponytail-review: giữ ngoài default; chỉ reconsider nếu benchmark chứng minh persistent over-engineering.
- Superpowers full SDD/TDD/debug/review: không bundle vì overlap process owner với Spec Kit/Dev policy.
- Addy spec-driven-development: không bundle vì BA Kit đã sở hữu WHAT/spec semantics.
- Spec Kit core specify/plan/tasks/analyze/converge: không dùng trong V1 vì phụ thuộc Spec Kit `spec.md`; Dev Kit không tạo một WHAT projection song song.
- Addy using-agent-skills: không thêm second router.
- Addy constraint-driven-development: tránh tạo thêm source of truth cạnh BA baseline/Dev policy.
- BMAD/Matt full packs: không bundle V1.

## Rule bắt buộc

```text
Installed != Invoked
Available capability != Mandatory workflow stage
```

Routing policy là authority quyết định capability nào được load/call. `planning-and-task-breakdown` giữ upstream planning mechanics nhưng hai mandatory Human checkpoints được đổi thành risk-gated Human/Tech Lead approval; exact diff được pin trong provenance.
