# Dev Kit VNext — Hướng dẫn sử dụng

## Cài đặt

Cài VNext từ checkout tin cậy vào user-scope home:

```powershell
python -I tooling/install_dev_kit.py --source-root . --install-home <user-home>/.devkit
```

Runtime ở `~/.devkit/runtime/v2`; launcher ở `~/.devkit/bin/devkit` (Windows
có `devkit.ps1` và `devkit.cmd`). Installer tạo manifest với package version,
exact file hashes và Python executable. Cài lại là idempotent; V1 runtime không
bị xóa. Thêm launcher directory vào PATH nếu cần.

Doctor kiểm tra package và capability closure:

```text
devkit doctor --json
```

`READY` ở Doctor chỉ nghĩa `PACKAGE/CAPABILITY READY`. Nó không phê duyệt một
feature và không thay thế `READY_FOR_TEST`.

## Khám phá V2 schemas/templates

```text
devkit schema start-request
devkit schema engineering-impact
devkit schema engineering-gap
devkit schema engineering-decision
devkit schema dev-state
devkit schema technical-approval
devkit schema dev-handoff
devkit template start-request
devkit template engineering-impact
devkit template engineering-gap
devkit template engineering-decision
devkit template technical-approval
devkit template dev-handoff
```

Copy `kits/dev/templates/start-request-v2.template.json` vào project và thay
mọi placeholder bằng exact refs, repository identity, observed Git base, scope
và checks. Template không tạo Human authority. Technical approval template là
boundary document; host system phải xác thực real Human/Tech Lead receipt.

V1 inspection yêu cầu prefix `legacy/`, ví dụ
`devkit schema legacy/start-request`. Mọi V1 artifact được gắn
`LEGACY_COMPAT` và không cấp authority VNext.

## Chạy FEATURE_DELIVERY

Lấy exact Engineering Handoff VNext từ BA, bao gồm proof `APPROVED_BASELINE` và
Project Foundation binding nếu có. Xác nhận repository roots và Git bases bằng
Git; không suy scope từ feature name hay Delivery Manifest. Trusted host cung
cấp callback xác thực BA Human proof:

```text
devkit --project-root <project-root> --host <trusted-host-module> start --request .devkit/start-request.json
devkit --project-root <project-root> --host <trusted-host-module> validate-authority
devkit --project-root <project-root> --host <trusted-host-module> impact-template
```

Hoàn thành Engineering Impact V2 rồi ingest artifact:

```text
devkit --project-root <project-root> --host <trusted-host-module> impact --artifact <impact-v2.json>
devkit --project-root <project-root> --host <trusted-host-module> plan --plan <dev-plan.md> --tasks <dev-tasks.md> --decision-ref <ed-v2.json> --revision <exact-revision>
devkit --project-root <project-root> --host <trusted-host-module> technical-gate-required
```

Plan/tasks được snapshot cùng ED refs, risk, repository bases và write scopes.
NORMAL local HOW không cần gate thừa. HIGH_RISK hoặc active material ED cần
exact authenticated Human/Tech Lead technical receipt:

```text
devkit --project-root <project-root> --host <trusted-host-module> bind-technical-approval --artifact <host-authenticated-receipt-ref.json>
devkit --project-root <project-root> --host <trusted-host-module> implementation-ready
```

Request JSON, local receipt giả và Spec Kit `approve` choice không xác thực gate.
Human host phải bind receipt vào exact technical snapshot.

## Implementation và handoff

Sau `implementation-ready`, chạy `begin-implementation`, rồi dùng `write-source`/
`authorize-write` cho từng path. Mỗi check có repository ID và chạy tại root
tương ứng. Ghi đúng một consolidated review bằng `review --evidence-ref`; xử lý
blocking finding trong một fix wave và tối đa một scoped rereview. Chạy fresh checks:

```text
devkit --project-root <project-root> verify
devkit --project-root <project-root> finalize --coverage <exact-fr-br-coverage.json>
devkit --project-root <project-root> status
```

Coverage phải bằng exact approved BR-* và FR-* set; mỗi requirement cần code và
test refs. `BAREF:*` chỉ là locator. Dev Handoff V2 kết thúc ở
`READY_FOR_TEST`, không tuyên bố `VERIFIED`, business acceptance hay merge
readiness.

## Gap, replan và maintenance

- WHAT ambiguity: `raise-gap`; runtime dừng `UPSTREAM_GAP`. Chờ BA/Human resolution và replacement Engineering Handoff VNext trước `resume-gap`.
- Risk hoặc snapshot thay đổi: `escalate-risk`/`replan`; dựng lại Impact, plan/tasks và snapshot. Receipt cũ không authorize snapshot mới.
- Nonbehavioral maintenance: `TECHNICAL_MAINTENANCE` với exact evidence và `no_what_change=true`; phát hiện behavior/security/public-contract/cross-repo work sẽ `BLOCKED`.

Spec Kit `1.0.11` chỉ workflow state/pause/resume/bundle transport. Delivery
Manifest giữ `DEFERRED_NON_AUTHORITATIVE`. Xem [acceptance contract](../../kits/dev/acceptance.yaml)
và [neutral example](../../kits/dev/examples/neutral-vnext.md) trước khi tích hợp.
