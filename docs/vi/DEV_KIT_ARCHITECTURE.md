# Dev Kit VNext — Kiến trúc

Dev Kit VNext biến một **Engineering Handoff VNext** đã được xác thực thành
thay đổi kỹ thuật có phạm vi, review, kiểm tra mới nhất và Dev Handoff. BA giữ
quyền sở hữu WHAT; Dev chỉ quyết định HOW trong các repository và write scope
đã khai báo.

## Ranh giới authority

| Trách nhiệm | Authority / bằng chứng |
|---|---|
| Business WHAT | Engineering Handoff VNext gắn với exact `APPROVED_BASELINE` proof |
| Engineering Impact | Engineering Impact V2 gắn upstream, repository bases, write scope và risk |
| Quyết định kỹ thuật | ED-*; quyết định có material approval requirement cần receipt riêng |
| Quyền bắt đầu sửa | Dev lifecycle V2 và exact technical snapshot |
| Kết quả Dev | Dev Handoff V2 ở `READY_FOR_TEST` |
| Quyết định tiếp theo | Tester, Human và quy trình tích hợp sở hữu ngoài Dev Kit |

Request, tên trạng thái, workflow choice hoặc Doctor không tự xác thực Human.
Trusted host xác thực exact BA Human proof và Project Foundation proof nếu có.
Human/Tech Lead receipt kỹ thuật phải gắn với snapshot cụ thể khi risk hoặc ED
yêu cầu.

## Hai authority mode

- `FEATURE_DELIVERY` yêu cầu Engineering Handoff VNext exact. Dev phân tích
  Engineering Impact V2, lập plan/tasks và chỉ sửa trong repository scope đã
  ràng buộc.
- `TECHNICAL_MAINTENANCE` yêu cầu bằng chứng maintenance chính xác và
  `no_what_change=true`. Nó không thể mở rộng thành thay đổi business behavior.

Engineering Gap dừng write và planning khi nội dung WHAT chưa rõ. Chỉ resume khi
có resolution evidence và Engineering Handoff VNext thay thế được xác thực lại;
Impact, plan và snapshot được dựng lại. ED-* lưu lựa chọn kỹ thuật, evidence,
phạm vi ảnh hưởng và trạng thái approval.

## Runtime V2

Runtime nằm tại `~/.devkit/runtime/v2`, launcher tại `~/.devkit/bin/devkit`.
V2 đóng gói Dev runtime, BA VNext reader, Shared SDLC, Project Foundation proof
dependencies, schemas/templates, plugin skills và provenance. Launcher dùng
`python -I`; runtime không import từ checkout hoặc `runtime/v1`.

V1 schemas/templates và readers còn dùng cho inspection tương thích với nhãn
`LEGACY_COMPAT`. Chúng không tạo authority VNext. Cài V2 không xóa
`~/.devkit/runtime/v1`.

GitHub Spec Kit `1.0.11` là workflow state/pause/resume/bundle transport.
`speckit.specify`, `plan`, `tasks`, `analyze` và `converge` bị loại khỏi Dev
workflow vì không phải WHAT authority. Workflow choice không phải technical
approval.

## Readiness và ownership

Mọi engineering check gắn với một implementation repository và chạy tại root
của repository đó. Runtime ghi nhận exact Git base, implementation revision,
write scope, command và evidence. Coverage chứa chính xác các `BR-*` và `FR-*`
được duyệt; `BAREF:*` chỉ là locator.

Dev giới hạn công việc review ở một consolidated review, một blocking-fix wave
và tối đa một scoped rereview. Sau đó fresh repository-scoped checks và coverage
được gắn vào Dev Handoff V2. `READY_FOR_TEST` nghĩa là Dev handoff đã đủ
engineering evidence; nó không có nghĩa `VERIFIED`, approved business result,
hoặc `READY_TO_MERGE`.

Delivery Manifest giữ nguyên:

```text
DEFERRED_NON_AUTHORITATIVE
```

## Discovery

- V2 schema: `devkit schema start-request|engineering-impact|engineering-gap|engineering-decision|dev-state|technical-approval|dev-handoff`
- V2 template/boundary: `devkit template start-request|engineering-impact|engineering-gap|engineering-decision|technical-approval|dev-handoff`
- V1 compatibility: `devkit schema legacy/start-request` và các tên `legacy/*` tương ứng
- Acceptance contract: [`kits/dev/acceptance.yaml`](../../kits/dev/acceptance.yaml)
- Package/provenance: [`kits/dev/kit.yaml`](../../kits/dev/kit.yaml), [`kits/dev/provenance.lock.json`](../../kits/dev/provenance.lock.json)
