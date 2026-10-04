# Tùy chỉnh Test Kit Manual VNext theo project

Project Test Policy cho phép nhóm ghi lại quy ước generation/review. Đây là guidance không có authority: không thể thay Engineering Handoff VNext, Human approval, Design, UX hay execution oracle.

## Khởi tạo policy

Cài Test Kit trước theo [Quick Start](TEST_KIT_QUICKSTART.md). Từ project root, dùng runtime đã cài để tạo starter nếu nhóm cần:

```powershell
$env:PYTHONPATH = (Resolve-Path '.agents\skills\.test-kit').Path
python -m tooling.lib.test_kit_policy bootstrap --project-root .
& '<path-to-agent-skills>\tooling\doctor.ps1' test --agent codex --scope project
```

```bash
export PYTHONPATH="$PWD/.agents/skills/.test-kit"
python -m tooling.lib.test_kit_policy bootstrap --project-root .
<path-to-agent-skills>/tooling/doctor.sh test --agent codex --scope project
```

Project root chứa `.test-kit/project.yaml` và các rule do nhóm sở hữu. Runtime/package đã cài nằm dưới `.agents/skills/.test-kit/`; không sửa pinned skills để cấu hình convention dự án.

Starter policy chỉ nên ghi cách trình bày, cách nhóm review, dữ liệu được phép dùng và quy ước làm việc. Không ghi thêm business rule, expected result, quyết định BA, approval receipt hoặc authority.

## Schema `project.yaml`

```yaml
schema_version: 1
profile:
  id: resource-testing
  revision: "1"
rules:
  common:
    - rules/common.md
  test_design:
    - rules/test-design.md
  testcases:
    - rules/testcases.md
templates:
  excel:
    path: templates/testcases.xlsx
```

Root chỉ nhận `schema_version`, `profile`, `rules`, `templates`. Profile gồm `id`, `revision`; categories của rules là `common`, `test_design`, `testcases`; templates chỉ hỗ trợ `excel`. Nếu chưa dùng Excel template, để `templates: {}`.

Mỗi rule path phải là relative path duy nhất trong `.test-kit/`, trỏ tới regular UTF-8 file. Absolute path, `..`, symlink/reparse escape, file thiếu hoặc duplicate đều bị từ chối. Excel template phải nằm trong cùng tree và có đuôi `.xlsx`.

## Giới hạn authority

Thứ tự authority không thay đổi:

1. Engineering Handoff VNext và exact BA Human proof quyết định business WHAT.
2. UX chỉ là authority khi context VNext ghi `ux_required: true`; context được cung cấp phải có exact Human approval, feature/revision và source/snapshot hashes.
3. Approved Design quyết định phạm vi coverage được đưa vào Cases.
4. Execution/interface oracle được duyệt quyết định chi tiết thực thi trong phạm vi được cấp.
5. Project Test Policy chỉ hướng dẫn cách làm; không override các nguồn trên.

Runtime bind bytes/ref chính xác và fail khi nguồn stale. Nó không tuyên bố dùng NLP để kết luận policy prose tương đương hoặc mâu thuẫn với BA/UX. Human review quyết định semantic consistency. Các từ như `button`, `field`, `input`, `page` không tự yêu cầu UX. Prototype luôn là `REVIEW_EVIDENCE`.

Policy không được trả lời BA `UNKNOWN`, invent expected result, thay execution oracle, bypass validator hoặc tự approve. Policy hash được snapshot vào run/gate khi được tiêu thụ; thay rule sau review làm stale input và cần review đúng revision mới.

## TEA bridge, Excel và Doctor

Team có thể dùng `_bmad/custom/bmad-testarch-test-design.toml` để truyền persistent facts cho TEA. Tránh personal override; nếu host báo restriction, project owner cần review và chuyển quy ước cần thiết sang policy team-owned. Runtime không tự xóa file cá nhân.

Excel template chỉ đổi presentation. Excel là `DERIVED` từ `APPROVED_TESTWARE`; không import ngược thành canonical testcase hoặc approval. XMind dùng pinned profile, cũng là projection một chiều từ `APPROVED_DESIGN`.

Doctor `READY` chỉ có nghĩa package/core capability sẵn sàng. Nó không có nghĩa BA approved, `APPROVED_DESIGN`, `APPROVED_TESTWARE` hay execution ready. Dependency XMind/Excel thiếu được báo `DEGRADED`; integrity/core failure được báo `FAIL`.

Nếu không có `.test-kit/project.yaml`, runtime báo `NO_PROJECT_POLICY` và vẫn có thể chạy với guidance mặc định. Xem [neutral VNext example](../../kits/test/examples/vnext/neutral/README.md), [Usage Guide](TEST_KIT_USAGE_GUIDE.md) và [Workflow/Human Gates](TEST_KIT_WORKFLOW.md). Appointment/CR-001 là nội dung V1 lịch sử, không phải ví dụ mặc định.
