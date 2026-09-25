# Dev Kit V1 — Foundation

> Status: **DESIGN_FROZEN_CANDIDATE**. Chưa phải runtime/installer-ready và chưa được gọi RC.

Dev Kit chịu trách nhiệm phần **WHERE / WHO OWNS + HOW** sau khi nhận **Approved BA Baseline**. Dev Kit không sở hữu business semantics và không được tự thay đổi WHAT.

## Default execution contract

```text
Approved BA Baseline
  → Spec Readiness
  → Planning Preflight + lightweight Engineering Impact
  → Technical Plan / Tasks
  → Incremental Implementation
  → ONE consolidated review
  → ONE blocking-fix wave
  → optional ONE scoped re-review
  → fresh deterministic verification
  → Dev Handoff / READY_FOR_TEST
```

Nguyên tắc chính:

- planning hấp thụ uncertainty trước implementation;
- capability không đồng nghĩa workflow stage;
- default path phải ngắn, risk mới làm workflow sâu hơn;
- business ambiguity phải quay lại BA/Human;
- review budget bị giới hạn để tránh review spiral;
- deterministic evidence được ưu tiên hơn repeated LLM judgement;
- Human/Tech Lead gate chỉ bắt buộc khi risk surface yêu cầu.

## Tài liệu canonical

- [Kiến trúc](../../docs/vi/DEV_KIT_ARCHITECTURE.md)
- [Capability selection](../../docs/vi/DEV_KIT_CAPABILITIES.md)
- [Workflow](../../docs/vi/DEV_KIT_WORKFLOW.md)
- [Routing](../../docs/vi/DEV_KIT_ROUTING.md)
- [Review & verification](../../docs/vi/DEV_KIT_REVIEW_AND_VERIFICATION.md)
- [Benchmark](../../docs/vi/DEV_KIT_BENCHMARK.md)
- [Composition/provenance lock](provenance.lock.json)

Không vendor hoặc upgrade upstream component nếu chưa cập nhật provenance, license/notice và dependency closure trong cùng change.
