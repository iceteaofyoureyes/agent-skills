# Dev Kit V1 — Foundation

> Status: **READY_FOR_SOL_REVIEW**. Chưa phải RC/release.

Dev Kit chịu trách nhiệm phần **WHERE / WHO OWNS + HOW** sau khi nhận **Approved BA Baseline**. Dev Kit không sở hữu business semantics và không được tự thay đổi WHAT.

## Default execution contract

```text
Approved BA Baseline
  → Spec Readiness
  → Planning Preflight + lightweight Engineering Impact
  → Technical Plan / Tasks (risk-gated Addy planner)
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
- [Usage Guide](../../docs/vi/DEV_KIT_USAGE_GUIDE.md)
- [Composition/provenance lock](provenance.lock.json)

## Runtime paths

- Codex local marketplace: [`.agents/plugins/marketplace.json`](../../.agents/plugins/marketplace.json)
- NORMAL/HIGH_RISK workflows are installed at user scope and listed by `devkit workflow normal|high-risk`; their source is `plugin/workflows/dev-normal.workflow.yml`, `dev-high-risk.workflow.yml`
- Các bước shell của Spec Kit cần `devkit_command` tương thích với shell; trên Windows dùng launcher `.cmd` đã cài (`.ps1` dành cho lệnh PowerShell trực tiếp).
- Entry path chuẩn cho agent: sao chép `templates/start-request.template.json` thành `.devkit/start-request.json`, chỉnh sửa, chạy `devkit validate-start-request .devkit/start-request.json`, rồi `devkit start --request .devkit/start-request.json`.
- TRIVIAL: start trước khi sửa; chạy `finish-trivial` sau khi sửa. Lệnh chạy lại deterministic checks và kết thúc với `COMPLETED` hoặc `NEEDS_REPLAN`; không có Spec Kit workflow, formal plan hay full review.
- NORMAL: sau `READY_FOR_PLANNING`, tiếp tục Spec Readiness → preflight/Impact → plan/tasks → `plan-check` → `implementation-ready normal` rồi mới sửa.
- HIGH_RISK: tiếp tục qua readiness, impact, plan/tasks, `plan-check` và Human/Tech Lead gate thật của Spec Kit. Không tự approve.
- External-project runtime installer: `../../tooling/install_dev_kit.py`; it installs only the runtime helper/BA contract parser, schemas, templates and workflow definitions under `~/.devkit/runtime/v1`
- JSON schemas/templates: `schemas/`, `templates/`; inspect them with `devkit schema start-request|impact-manifest|dev-handoff`
- Run state/evidence: `.specify/workflows/runs/` and `.devkit/runs/`
- Doctor/validators: `../../tooling/lib/dev_kit.py`

Nếu request validation thất bại, sửa tệp JSON rồi xác thực lại; chưa có run nào được tạo. Nếu `start` thất bại trước khi trả về run directory, sửa request rồi thử lại. Sau khi start thành công, tiếp tục cùng run thay vì tạo thêm một active run. Lỗi Angular `spawn EPERM` trong worker là giới hạn bên ngoài của host; giữ nguyên bằng chứng và không làm yếu check đã cấu hình.

Không vendor hoặc upgrade upstream component nếu chưa cập nhật provenance, license/notice và dependency closure trong cùng change.

## Spec Kit V1 boundary

Spec Kit is reused as workflow/state/bundle infrastructure. Dev Kit V1 deliberately does not call core `speckit.specify/plan/tasks/analyze/converge`; those commands assume Spec Kit's own `spec.md` semantics. The Approved BA Baseline remains the only WHAT authority.
