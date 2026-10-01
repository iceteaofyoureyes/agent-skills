# Tùy chỉnh Test Kit V1.1 theo project

V1.1 bổ sung rule và Excel template do project sở hữu. Agent dùng rule trong Test Design và manual testcase generation, lưu đúng bytes vào run evidence và bind policy SHA-256 vào Human Gate. Canonical schemas, authority và điểm dừng `APPROVED_TESTWARE` → `STOP_V1` giữ nguyên.

## 1. Khởi tạo

Cài Test Kit vào project theo [Quick Start](TEST_KIT_QUICKSTART.md). Từ project root, dùng runtime đã cài:

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

Bootstrap tạo các file starter còn thiếu và bridge TEA project-owned; giữ nguyên nội dung đã có. Starter chỉ là guidance bảo thủ, không đặt business rule. Đọc và sửa starter theo conventions của nhóm, rồi commit cùng project.

```text
<project-root>/
├── .test-kit/
│   ├── project.yaml
│   └── rules/
│       ├── common.md
│       ├── test-design.md
│       └── testcases.md
└── _bmad/custom/bmad-testarch-test-design.toml
```

`.test-kit/` ở project root chứa policy của nhóm. `.agents/skills/.test-kit/` chứa runtime/package đã cài. Không sửa pinned skill để cấu hình project.

Không có `.test-kit/project.yaml` thì runtime dùng `NO_PROJECT_POLICY`, giữ luồng V1 và không tự tìm arbitrary local rules. Personal TEA override vẫn bị chặn trong production.

## 2. Hợp đồng `project.yaml`

```yaml
schema_version: 1
profile:
  id: portal-testing
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

`profile.id` và `profile.revision` là chuỗi không rỗng; quote revision để tránh số YAML. Giữ ID ổn định, tăng revision khi nhóm thay đổi policy. Khi chưa dùng Excel template, viết `templates: {}`.

Root chỉ nhận `schema_version`, `profile`, `rules`, `templates`; profile chỉ có `id`, `revision`; rules chỉ có `common`, `test_design`, `testcases`; templates chỉ có `excel`, với `path`. Field/category lạ bị từ chối. V1.1 không hỗ trợ `templates.xmind`.

Mỗi rule path là relative path từ `.test-kit/`, trỏ tới regular file UTF-8. Absolute path, `..`, symlink/reparse escape, file thiếu và duplicate resolved file đều fail closed. Template nằm trong cùng tree, tồn tại và có đuôi `.xlsx`. Giữ thứ tự danh sách: runtime không tự sort rule.

## 3. Viết rules

`common.md` áp dụng cho cả Design và Cases. Ví dụ:

```markdown
# Quy ước chung
- Viết tiếng Việt; giữ nguyên FR/BR IDs và thuật ngữ nghiệp vụ từ BA.
- Chỉ dùng dữ liệu tổng hợp hoặc fixture đã được project cho phép.
- Giữ UNKNOWN và báo conflict; không tự điền business behavior.
```

`test-design.md` hướng dẫn cách phân tích/biểu diễn coverage:

```markdown
# Test Design
- Xem xét boundary và negative coverage của FR/BR đã duyệt.
- Giữ riêng expected behavior và câu hỏi BA còn mở.
- Với boundary chưa được BA quyết định, giữ deferred/UNKNOWN.
```

`testcases.md` hướng dẫn generation trong semantic boundary của approved Design:

```markdown
# Manual testcases
- Giữ ID theo raw profile TC-...; đặt name theo CR-001 - <hành vi> - <điều kiện>.
- Viết objective, preconditions, actions và expected results bằng tiếng Việt.
- Mỗi case kiểm tra một điều kiện, nhưng phải có đủ flow để tự thực hiện.
- Chỉ decomposition scenario đã duyệt; không thêm business coverage.
- Giữ material OPEN execution dependency nếu thiếu approved oracle.
```

Rule có thể định hướng priority trong P0–P3, naming, atomicity, boundary/negative coverage và data safety. Rule không thay field set hoặc raw profile; naming convention áp dụng vào `name`, còn IDs và trace giữ hợp đồng runtime.

## 4. Authority và conflict

| Nguồn | Quyền quyết định |
|---|---|
| Approved BA Baseline | Business authority, FR/BR, UNKNOWN |
| Approved Canonical Test Design | Coverage authority |
| Approved Execution / Interface Oracle | Setup, action, observation details |
| Project Test Policy | Testing/generation guidance không có authority |

Invocation ghi rõ `TESTING POLICY / NON-AUTHORITATIVE GUIDANCE`. Authoritative source thắng khi có conflict. Policy không được trả lời UNKNOWN, invent expected result, thay execution oracle, bypass validator hay auto-approve. Không có cơ chế “last rule wins”.

Ví dụ BA CR-001 nói maximum appointment duration còn `UNKNOWN`. Rule “Use 120 minutes as maximum appointment duration” không cấp authority cho ngưỡng 120. Design phải giữ câu hỏi/deferred; testcase không được assert ngưỡng đó. Validator findings hoặc Human review chặn conflict. Runtime giữ các validator V1, không dùng NLP để chứng nhận mọi câu natural-language policy đều an toàn.

## 5. TEA project bridge và personal override

Design dùng upstream `workflow.persistent_facts` trong:

```text
_bmad/custom/bmad-testarch-test-design.toml
```

Bridge cho profile ở trên:

```toml
[workflow]
persistent_facts = [
  "file:{project-root}/.test-kit/rules/common.md",
  "file:{project-root}/.test-kit/rules/test-design.md"
]
```

Bridge phải giữ common trước Design-specific và khớp rule list của profile. Runtime không sửa pinned `customize.toml`, không ghi đè team customization có sẵn, không làm mất persistent facts khác. Customization có sẵn phải qua kiểm tra consistency; nếu thiếu/sai/ambiguous, sửa project-owned TOML theo finding rồi chạy Doctor lại. Khi đổi đường dẫn hoặc thứ tự Design rules, cập nhật bridge cùng profile.

File `_bmad/custom/bmad-testarch-test-design.user.toml` bị chặn với `PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED`, kể cả project chưa có profile. Runtime không delete/overwrite file. Muốn production run, Human/project owner cần xử lý personal customization, chuyển convention cần thiết sang team policy có kiểm soát và review bridge. V1.1 không có production opt-in để bỏ qua restriction này.

## 6. Snapshot, evidence và stale policy

Runtime resolve hai snapshot độc lập:

| Stage | Thứ tự rules | Ref ID |
|---|---|---|
| DESIGN | common → test_design | `TEST_POLICY:DESIGN:<profile-id>` |
| CASES | common → testcases | `TEST_POLICY:CASES:<profile-id>` |

Mỗi entry giữ logical path và SHA-256 của exact file bytes. Identity profile, stage, ordered entries được serialize deterministic compact JSON rồi SHA-256. Design còn ghi identity của effective team customization; thay đổi team input phải được kiểm tra lại. Templates chỉ là presentation, không vào testing-policy digest.

Đổi nội dung, newline, revision hoặc thứ tự rule có thể đổi snapshot SHA dù ID không đổi. Cùng identity, ordered paths và exact bytes cho cùng SHA. Đừng tự tính lại hash để làm receipt cũ hợp lệ.

Run evidence:

```text
<run-dir>/inputs/project-policy/
├── policy-snapshot.json
└── rules/...
```

Snapshot/manifest ghi profile ID/revision, stage, policy ref/SHA, logical rule path, evidence path và từng file SHA; Design ghi team TOML/hash khi effective. Rule được copy bằng exact bytes. File project đổi sau invocation không mutate bản copy của run. Persistence idempotent khi bytes giống hệt và từ chối overwrite khác bytes.

Design Gate bind current BA refs + DESIGN policy ref. Case Gate bind current BA refs + exact approved Design ref + CASES policy ref; approved execution-oracle contract vẫn được kiểm tra riêng như V1.

Nếu policy liên quan đổi sau `DESIGN_REVIEW`/`CASE_REVIEW`, `APPROVE` bị từ chối stale. Quay lại generation/revalidation/revision/review thích hợp với policy hiện hành trong run mới; không sửa evidence cũ hoặc tái dùng receipt. Sửa `common.md` ảnh hưởng cả hai stage; sửa `testcases.md` ảnh hưởng Cases; sửa Design rules/team customization ảnh hưởng Design và cần current Design authorization khi đi tiếp. `PASS`, `OK`, `CONTINUE`, `Next` không có nghĩa `APPROVE`.

## 7. Excel project template

Copy workbook nhóm vào `.test-kit/templates/testcases.xlsx` rồi khai báo `templates.excel.path`. Exporter chọn:

```text
HUMAN_SUPPLIED_APPROVED_TEMPLATE → PROJECT_TEMPLATE → DEFAULT_TEMPLATE
```

Human template explicit thắng; nếu không có, workbook trong project profile được dùng; chỉ khi không có cả hai mới dùng default. Workbook được chọn mà missing/type/path/semantic mapping không an toàn sẽ fail closed; projection báo `CANNOT_PROJECT_TEMPLATE`, không silent fallback.

Existing Excel inspector vẫn kiểm tra unambiguous headers và supported row model; presentation không đổi canonical semantics, ordered steps, scoped Test Data, trace hoặc gate state. Template byte/hash được giữ trong projection evidence; sửa template không thay policy SHA hoặc cấp business authority. Core Doctor chỉ kiểm tra path/type; Excel mapping inspection cần optional Excel dependencies và diễn ra khi xuất. XMind giữ pinned profile, không có project/Human XMind template hoặc reverse import.

## 8. Doctor và troubleshooting

Chạy từ project root hoặc truyền `--project-root <project-root>` khi inspect target ở nơi khác. Doctor hiển thị nhóm `Project policy (project-owned inputs)` riêng với package integrity.

| Finding/tình huống | Cách xử lý |
|---|---|
| `NO_PROJECT_POLICY` | Luồng V1 hợp lệ; bootstrap nếu nhóm muốn policy |
| YAML/schema error, unknown field | Sửa theo schema 1; không thêm XMind category |
| Missing/invalid UTF-8 rule | Tạo đúng file, lưu UTF-8, commit cùng profile |
| Duplicate/path traversal/escape | Dùng unique relative path nằm trong `.test-kit/` |
| `TEA_BRIDGE_MISSING` hoặc bridge inconsistency | Bootstrap nếu chưa có bridge; sửa TOML đã có theo ordered Design rules |
| `PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED` | Project owner xử lý file personal; runtime không xóa file |
| Stale policy tại gate | Review artifact với current policy trong revision/run thích hợp |
| `CANNOT_PROJECT_TEMPLATE` | Sửa mapping/type workbook đã chọn, rồi export lại; không fallback |
| `MODIFIED_MANAGED_FILE` | Drift trong installed package; khôi phục đúng pinned package, không sửa hash |

User edit rule hợp lệ có thể đổi policy SHA nhưng không phải package drift. Doctor không approve policy text hoặc testware; Human vẫn review canonical snapshot và authority conflicts.

Xem [ví dụ CR-001](../../kits/test/examples/CR-001/customization/README.md), [Usage Guide](TEST_KIT_USAGE_GUIDE.md) và [Workflow/Human Gates](TEST_KIT_WORKFLOW.md). V1.1 dừng ở readiness cho Human acceptance; Automation Test V2 là lane riêng.
