# Dev Kit VNext — Routing và Authority Modes

Dev routing dựa trên exact Engineering Handoff VNext, repository identities,
observed Git bases, write scopes, checks và risk. Feature title, Delivery
Manifest, local approval text hoặc workflow choice không tạo authority.

## Authority modes

| Mode | Điều kiện | Phạm vi |
|---|---|---|
| `FEATURE_DELIVERY` | Exact authenticated Engineering Handoff VNext | Engineering Impact, planning, ED-*, implementation, review, checks, coverage và Dev Handoff |
| `TECHNICAL_MAINTENANCE` | Exact nonbehavioral maintenance evidence; `no_what_change=true` | Mechanical/docs/config change trong một implementation repository |

Nếu maintenance phát hiện business behavior, security, public contract hoặc
cross-repository change, runtime chuyển `BLOCKED`. Tạo FEATURE_DELIVERY bằng
authority chính xác trước khi tiếp tục.

## Risk và gate

- NORMAL reversible local HOW: lập plan, xác nhận snapshot rồi implementation; không có Human gate thừa.
- HIGH_RISK category hoặc active material ED: exact Human/Tech Lead receipt cần được host xác thực, gắn toàn bộ snapshot.
- Multi-repository work nâng risk và vẫn giữ exact base, scope, owner và check theo từng repository.
- Risk escalation buộc replan; approval cũ không thể authorize snapshot mới.

Human gate không phải bước chọn `approve` trong Spec Kit. Spec Kit `1.0.11`
chỉ vận chuyển workflow state/bundle; chỉ trusted host mới xác thực exact
technical receipt. BA Human approval là proof của Engineering Handoff VNext,
không được Dev tạo hoặc diễn giải lại.

## Gap và sở hữu WHAT

WHAT ambiguity dùng Engineering Gap V2, dừng ở `UPSTREAM_GAP` và quay về BA/Human.
Resume cần resolution evidence cùng replacement Engineering Handoff VNext được
xác thực. Không dùng V1 `NEEDS_BA_CLARIFICATION` làm workflow VNext.

ED-* giữ kỹ thuật trong phạm vi Dev. Nếu một quyết định thay đổi business WHAT,
không biến nó thành ED; ghi Engineering Gap và chờ BA authority cập nhật.

## Terminal route

Sau một consolidated review theo bounded budget, fresh repository-scoped checks
và exact FR/BR coverage, Dev tạo Handoff V2 ở `READY_FOR_TEST`. Đây không phải
`VERIFIED`, Tester PASS hay merge approval.

V1 artifacts chỉ đọc dưới `LEGACY_COMPAT` và luôn có
`vnext_authority=false`. Delivery Manifest giữ
`DEFERRED_NON_AUTHORITATIVE`.
