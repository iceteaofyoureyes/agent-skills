# Dev Kit VNext — Workflow V2

## 1. Start từ authority chính xác

Tạo Start Request V2 với `run_id`, `change_id`, `summary`, `authority_mode`,
repository identities, observed Git base revisions, write/read-only scopes,
repository-scoped checks và exact refs. `FEATURE_DELIVERY` bắt buộc có
Engineering Handoff VNext. Trusted host xác thực exact BA Human proof và
Project Foundation proof nếu Handoff có ràng buộc Foundation.

`TECHNICAL_MAINTENANCE` chỉ nhận maintenance evidence với
`no_what_change=true`. Không dùng nó cho behavioral, public-contract,
security-sensitive hoặc cross-repository feature work.

## 2. Validate, Impact và plan

Sau `start`, chạy `validate-authority`. FEATURE_DELIVERY tạo Engineering Impact
V2 ràng buộc upstream, từng repository base, write scope, affected components,
risk và technical unknowns. Tiếp theo `plan` lưu `dev-plan.md`, `dev-tasks.md`,
ED refs và exact technical snapshot. Snapshot là write authorization boundary;
không suy scope từ feature name hoặc Delivery Manifest.

Lifecycle chính:

```text
INTAKE → AUTHORITY_VALIDATED → IMPACT_ANALYZED → TECHNICAL_PLANNED
→ IMPLEMENTATION_READY → IMPLEMENTING → ENGINEERING_REVIEW → VERIFYING
→ READY_FOR_TEST
```

`UPSTREAM_GAP`, `NEEDS_REPLAN` và `BLOCKED` là trạng thái stop/recovery; chúng
không cấp quyền sửa.

## 3. Engineering Gap và ED-*

Nếu WHAT mơ hồ, dùng `raise-gap`. Runtime ghi Engineering Gap V2, chuyển sang
`UPSTREAM_GAP` và chặn write. Không biến câu hỏi BA thành đề xuất business mới.
Chỉ `resume-gap` với exact resolution evidence và replacement Engineering
Handoff VNext đã xác thực; sau đó tạo lại Impact, plan/tasks và snapshot.

ED-* ghi technical decision, evidence refs, upstream refs, repository/component
scope, risk, alternatives và consequences. Material ED với
`approval_requirement=HUMAN` cần receipt riêng được host xác thực.

## 4. Technical Human gate

NORMAL reversible local HOW có thể đi tới `IMPLEMENTATION_READY` mà không cần
approval thêm. HIGH_RISK hoặc active material ED cần exact Human/Tech Lead
receipt gắn run, change, snapshot revision/hash và decision evidence. Thiếu
authenticator, receipt giả, receipt cũ hoặc snapshot drift đều chặn gate.

Spec Kit `1.0.11` chỉ điều phối workflow/pause/resume/bundle. `approve` trong
workflow không phải technical authority và không thay thế receipt.

## 5. Implementation, review, verify

Runtime kiểm tra exact bases và scope trước mỗi write. Dùng `write-source` hoặc
`authorize-write`; từng engineering check khai báo `repository_id` và chạy
trong repository đã bound. Check categories: `BUILD`, `STATIC`, `LINT`,
`TYPECHECK`, `UNIT`, `COMPONENT`, `MODULE_LOCAL_INTEGRATION`.

FEATURE_DELIVERY có tối đa một consolidated full review, một blocking-fix wave
và một optional scoped rereview. Không review lặp lại mỗi slice. Sau review/fix,
`verify` chạy lại các check mới trên implementation revision hiện tại.

## 6. Finalize Dev Handoff

Coverage phải khớp exact BR-* và FR-* của approved BA baseline; mỗi hàng cần
code refs và test refs. `BAREF:*` là locator/provenance, không phải coverage
identity. `finalize` tạo HANDOFF_MANIFEST V2 và xác thực lại Dev Handoff:

```text
READY_FOR_TEST
```

Đây là Dev handoff readiness. Nó không khẳng định `VERIFIED`, Tester PASS,
business/system acceptance hay `READY_TO_MERGE`.

## 7. Recovery và compatibility

- `NEEDS_REPLAN`: risk, bases, task binding hoặc scope thay đổi; Impact/plan/snapshot phải được xác lập lại.
- `UPSTREAM_GAP`: chờ BA/Human resolution và replacement Engineering Handoff VNext.
- `BLOCKED`: dừng writes cho đến khi authority mode và scope hợp lệ; maintenance discovery không tự nâng quyền.
- V1 state/schema/template: chỉ `LEGACY_COMPAT`; không cấp VNext authority.
- Delivery Manifest: `DEFERRED_NON_AUTHORITATIVE`; không làm upstream hoặc write scope.
