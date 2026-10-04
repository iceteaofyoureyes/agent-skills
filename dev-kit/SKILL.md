---
name: dev-kit
description: Implement approved delivery intent through Dev Kit; resolve inputs and runtime internally, stop at material decisions and Human gates.
---

# Dev Kit router

Human nói: `Implement <feature> từ delivery manifest đã approve.`

1. Đọc workspace `AGENTS.md`, `workspace.yml`, project-docs `AGENTS.md` và target module `AGENTS.md`.
2. Resolve `features/<feature>/delivery-manifest.yml`. Dùng shared `delivery_manifest.load_delivery_manifest`; không đọc prototype thành business authority. UI feature bắt buộc manifest có approved UX. Mọi path/hash/revision phải hợp lệ. The run's validated `authority_precedence` is the approval source: `ba_baseline.status == APPROVED_FOR_ENGINEERING` plus exact BA source hashes approves the immutable BA snapshot; a valid Delivery Manifest V2 and its exact Human receipt approves the bound UX snapshot.
3. Resolve repository/module từ manifest qua workspace topology. Kiểm tra exact base revision trong Git; inspect current source, tests và repository-owned quality gate. Không đoán scope từ tên CR.
4. Derive provisional write scope và risk signals từ impact thực tế. Nhiều target, migration, auth, concurrency hoặc public contract dùng HIGH_RISK. Thiếu business/UX authority trả BA/UX clarification.
5. Gọi internal `python -m tooling.lib.dev_router --project-root <target> --delivery <manifest> --summary <intent>`. Router tự tạo/validate start request, derive deterministic checks từ quality gate, bind manifest và BA/UX hashes, tạo hoặc resume cùng run. Human không sửa JSON.
6. Theo `kits/dev/plugin/workflows/dev-normal.workflow.yml` hoặc `dev-high-risk.workflow.yml`; runtime CLI là internal API. Tạo spec-readiness và impact từ inspection, rồi preflight, technical plan/tasks, plan-check, implementation-ready. HIGH_RISK dừng ở Human plan gate; không tự approve. Apply `APPROVAL STATE != INLINE LIFECYCLE TEXT`: strings like `DRAFT_FOR_HUMAN_BASELINE_REVIEW`, `DRAFT_FOR_HUMAN_UX_REVIEW`, `PENDING_HUMAN_REVIEW`, or historical `next_stage` wording in exact approved source bytes cannot revoke validated approval. `open_items.blocking` remains a contract blocker; `open_items.non_blocking` is not a business ambiguity by itself. If later validated delivery evidence satisfies an older UX-pending item, classify it as `SUPERSEDED_BY_DELIVERY_MANIFEST`. Still stop for a semantic contradiction between approved rules, an UNKNOWN/TBD that requires Dev to choose WHAT, invalid/missing receipt or manifest evidence, hash drift, or a real blocker.
7. Implement trong approved scope; focused checks, một consolidated independent review, tối đa một blocking fix wave và một scoped re-review, fresh verification, terminal handoff. Drift ở BA/UX/delivery hoặc scope expansion phải NEEDS_REPLAN.
8. Chỉ surface material ambiguity, HIGH_RISK Human plan gate, blocking review, NEEDS_REPLAN và terminal handoff. Dev không tự VERIFIED.

Runtime `.devkit/` và `.specify/workflows/runs/` phải ignored. Golden không chạy nếu chưa có Human GO; router smoke chỉ dùng synthetic feature.
