# Dev Kit VNext — Review và Verification

## Consolidated review

FEATURE_DELIVERY có review budget cố định:

| Bước | Tối đa |
|---|---:|
| Consolidated full engineering review | 1 |
| Blocking-fix wave | 1 |
| Optional scoped rereview | 1 |

Review kiểm tra implementation so với exact technical snapshot, Engineering
Impact, ED decisions, repository bases và scope. Chuyển phát hiện WHAT thành
Engineering Gap; không để review tự sửa business authority. Chỉ mở blocking-fix
wave cho blocking finding. Runtime kiểm soát snapshot drift và giới hạn số lượt.

## Repository-scoped fresh checks

Mỗi check có `name`, `repository_id`, `category` và `command`. Runtime chạy
command ở root của repository tương ứng và ghi lại exact bases, implementation
revision, command, result, snapshot và evidence ref. Một check không được đổi
source hoặc scope. Hỗ trợ `BUILD`, `STATIC`, `LINT`, `TYPECHECK`, `UNIT`,
`COMPONENT` và `MODULE_LOCAL_INTEGRATION`.

Fresh verification chạy sau consolidated review/fix trên implementation revision
đã được review. Thay đổi source sau review buộc phải review lại theo giới hạn;
thay đổi bases/scope/risk yêu cầu replan. Chỉ deterministic PASS cùng exact
evidence mới đủ điều kiện cho handoff.

## FR/BR coverage

Coverage phải bằng exact set approved BR-* và FR-* của upstream baseline. Mỗi
hàng `COVERED` cần ít nhất một code ref và một test ref. ID thiếu/thừa, trùng,
hoặc BAREF locator đều không thể thay thế BR/FR identity.

## READY_FOR_TEST

Dev Handoff V2 chỉ được phát hành sau authority/snapshot validation, required
technical gate, review budget, fresh check results và exact coverage. Runtime
đọc lại và validate Handoff trước khi công bố trạng thái.

`READY_FOR_TEST` nghĩa là engineering work đã bàn giao Tester. Nó không có nghĩa
`VERIFIED`, Tester PASS, business/system acceptance, hay `READY_TO_MERGE`.
Doctor kiểm tra PACKAGE/CAPABILITY READY và không quyết định trạng thái feature.

## Spec Kit và compatibility

GitHub Spec Kit `1.0.11` vận chuyển workflow state và bundle. Feature-spec
commands bị loại trừ; Human choice trong workflow không phải technical receipt.
V1 review/handoff artifacts chỉ là `LEGACY_COMPAT`. Delivery Manifest giữ
`DEFERRED_NON_AUTHORITATIVE`.
