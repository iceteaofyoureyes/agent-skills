# Khả năng và ranh giới Test Kit V1

**Test Kit = HOW DO WE PROVE IT.** Kit tạo Test Design và testcase thủ công từ BA baseline đã được phê duyệt, rồi dừng ở Human Gate. BA giữ quyền quyết định **WHAT**; Test Kit không thiết kế API/DB/architecture và không biến TEA/Katalon thành nguồn business rule.

## Đầu vào được hỗ trợ

| Đầu vào | Điều kiện thực tế | Cách dùng |
|---|---|---|
| `engineering-handoff.yml` + approved Business Rules, functional SRS, BA decisions | `ba_baseline.status: APPROVED_FOR_ENGINEERING`; đường dẫn và SHA-256 khớp | BA authority cho Test Design |
| Output native của `bmad-testarch-test-design` | Skill đã pin và project có `_bmad/tea/config.yaml`; adapter chuẩn hóa/validate | Raw analysis evidence, chưa là canonical |
| Canonical Test Design + Design Gate receipt | Revision/hash/BA refs hiện hành; Human đã xác thực | Coverage authority cho testcase và XMind |
| Output native của `create-test-cases` | Chỉ sau Design Gate; adapter chuẩn hóa/validate | Raw testcase evidence, chưa là canonical |
| Approved execution/interface contract | Khi cần setup, action hoặc observation cụ thể | Resolution ref cho execution dependency; không đổi BA rule |
| Canonical Testcases + Case Gate receipt | `APPROVED_TESTWARE`, state `STOP_V1`, refs hiện hành | Authority cho Excel production projection |
| Human/project `.xlsx` template | Inspector ánh xạ không mơ hồ, template đủ trường semantic cần thiết | Trình bày Excel, không đổi testcase |

XMind V1 **không** nhận Human-supplied hoặc project XMind template. Nó dùng profile trình bày đã pin. Một screenshot, XMind hay Excel do người dùng sửa không thay thế approved BA input hoặc canonical artifact.

## Ai sở hữu điều gì?

| Lớp | Vai trò |
|---|---|
| Approved BA Baseline | Business oracle: hành vi được xác nhận, UNKNOWN và nguồn FR/BR |
| TEA | Analysis/advisory; P0–P3 và risk là gợi ý lập kế hoạch |
| Canonical Test Design | Coverage oracle sau Human Design Gate |
| Canonical Testcases | Manual testcase authority sau Human Case Gate |
| Approved execution/interface contract | Execution oracle cho setup/action/observation được phép khẳng định |
| XMind / Excel | Human-facing derived projection, không phải source of truth |

`review_status` là projection của trạng thái review, không phải bằng chứng tự thân về approval. `P0/P1/P2/P3` là **advisory testing priority**: không xác lập business authority, trạng thái approval, kết quả chạy test hay production readiness. Design canonical không có field `priority`; heading priority của TEA chỉ ở `hierarchy_path`/raw evidence. Testcase canonical có `priority` vì raw case có nhãn này.

Nếu BA còn UNKNOWN, giữ câu hỏi và ref; scenario có thể deferred với `expected_behavior: null` khi nguồn nêu rõ điều đó. Không tự điền maximum duration, filter/sort/pagination hoặc expected result thuận tiện. Testcase không được khẳng định kết quả cho Design deferred. Execution dependency khác UNKNOWN nghiệp vụ: đó là thiếu contract thực thi/quan sát, được khai báo rõ trên testcase và có thể chặn Case Gate nếu material.

## Capability chính

1. **TEA analysis và canonical Test Design:** chuyển approved BA source thành input TEA, giữ raw output, chuẩn hóa từng scenario, validate trace/UNKNOWN/authority và trình Human review đúng snapshot.
2. **Canonical manual testcases:** dùng `create-test-cases` sau Design Gate, giữ thứ tự step và phạm vi Test Data, kiểm tra trace `FR/BR → TD → TC` và execution dependencies.
3. **Human Gates:** `DESIGN_REVIEW` và `CASE_REVIEW` nhận `APPROVE` hoặc `REQUEST_CHANGES` bằng receipt đã xác thực, gắn artifact ID/revision/semantic SHA-256/input refs. `ANSWER`, `REVIEW`, `CONTINUE` không phải approval.
4. **Optional XMind:** một chiều từ approved Canonical Test Design; Logic Chart Right, nhóm chức năng được kiểm tra với BA, Expected Behavior/BA warning dễ đọc, trace/hash ở external manifest. Không reverse import.
5. **Optional Excel:** một chiều từ approved Canonical Testcases; một testcase/một row mặc định, step theo thứ tự trong cell nhiều dòng, trace/hash ở external manifest. Không reverse import.
6. **Package lifecycle:** `install`, `doctor`, reinstall và `uninstall` quản lý file thuộc Kit. Doctor kiểm tra package definition, authority, payload, managed-file drift và dependency bắt buộc; BA và Test có thể cùng cài trong một project.

## Hình dạng canonical

### Test Design

```text
design_id, hierarchy_path, scenario_title, expected_behavior,
requirement_refs, open_questions, review_status
```

`hierarchy_path` có thứ tự. `requirement_refs` trỏ tới FR/BR đã duyệt. `open_questions` là danh sách `{source_ref, text, status: "UNKNOWN"}`. `expected_behavior` chỉ `null` khi nguồn nêu rõ outcome bị hoãn do BA UNKNOWN và có open question tương ứng. `review_status` nhận `DRAFT`, `IN_REVIEW`, `CHANGES_REQUESTED`, `APPROVED`, nhưng không nằm trong immutable semantic payload dùng để gắn receipt.

### Testcase

```text
test_case_id, name, objective, preconditions, test_data,
steps: [{action, test_data, expected_result}], priority,
requirement_refs, test_design_refs, execution_dependencies, review_status
```

Step có thứ tự; `test_data` ở cấp testcase là dữ liệu dùng chung, ở cấp step chỉ có khi raw step ghi rõ. `requirement_refs` truy lên FR/BR; `test_design_refs` truy về exact approved Design. Mỗi `execution_dependencies` ghi `{need, material, status, resolution_ref}`; `OPEN` material ngăn Case Gate APPROVE. Thiếu ID, ref, field bắt buộc, kết quả quan sát hoặc mapping không rõ ràng thì chuẩn hóa/validation fail closed; agent không tự chữa bằng suy đoán. Xem [Workflow](TEST_KIT_WORKFLOW.md) để biết trạng thái và nguồn phê duyệt.

## Template và bản chiếu

**Excel** chọn `HUMAN_SUPPLIED_APPROVED_TEMPLATE → PROJECT_TEMPLATE → DEFAULT_TEMPLATE`. Template do Human chỉ quyết định trình bày. Inspector phải tìm được sheet/header/row model và mapping semantic duy nhất; thiếu trường bắt buộc hoặc mơ hồ trả `CANNOT_PROJECT_TEMPLATE`. Nếu đã yêu cầu template Human mà nó không hợp lệ, không rơi về default. Default profile `DEFAULT_TESTCASE_EXCEL_V1 1.0.0` dùng `ONE_TESTCASE_PER_ROW_WITH_MULTILINE_ORDERED_STEPS`; `Key` để trống, **không** gán `test_case_id` vào Key. Canonical ID và đầy đủ trace ở `<workbook>.projection.json`, không ở hidden sheet/column/comment.

Các cột tester cần đọc ở workbook mặc định:

| Cột | Ý nghĩa |
|---|---|
| `Name`, `Objective`, `Precondition` | Title, ý định kiểm tra và điều kiện của một canonical testcase |
| `Status` | Bản chiếu trạng thái review đã được duyệt; không phải kết quả execution |
| `Folder` | Nhóm chức năng có thể xác định từ BA/Design đã duyệt; để trống khi không rõ |
| `Priority` | P0–P3 advisory từ case |
| `Step`, `Test Data`, `Expected Result` | Các bước có thứ tự trong cell nhiều dòng; giữ case-level và explicit step-level Test Data khác nhau |

`Key`, `Component`, `Labels`, `Owner`, `Estimated Time`, `Coverage (Issues)`, `Coverage (Pages)` và `Test Script (Plain Text)` không có nguồn V1 chắc chắn nên để trống trong default workbook. Không đọc các ô trống này như mất canonical data: external projection manifest giữ testcase ID, ordered steps, refs, execution dependencies và review status. Manifest chứa SHA của workbook; exporter mở lại file đã serialize để so semantic. Workbook xuất ra và manifest được seal làm evidence snapshot; cần chỉnh bản dùng cá nhân thì tạo copy.

**XMind** không có nhánh chọn template trong V1. Profile `HUMAN_FACING_XMIND_PROFILE` đã pin xác định layout/functional mapping. Nếu nhóm hiển thị không xác định được, exporter trả `CANNOT_PROJECT_HUMAN_PROFILE`, không đoán bằng LLM. Human-supplied XMind template cần capability mới; V1 hiện không có `CANNOT_PROJECT_TEMPLATE` cho XMind.

XMind dùng **Logic Chart Right** với feature đã duyệt làm root và các nhánh nhóm chức năng được kiểm tra với BA. Resolved scenario hiển thị tiêu đề thân thiện và `MM: <expected_behavior>`; deferred scenario có cảnh báo `⚠ Chờ BA: ...`. Canonical `design_id`, title gốc, refs, open questions và hash nằm trong external projection manifest. Map không chứa machine notes/labels ẩn để truyền semantic riêng. Nếu presentation mapping mơ hồ, không sửa canonical Design để ép nó khớp bản đồ.

Cả hai projection đều cần Human yêu cầu rõ ràng; production export kiểm tra approved canonical snapshot và receipt hiện hành. File projection đã xuất là evidence snapshot, không phải canonical input. Chỉnh semantic trong bản sao XMind/Excel phải quay về canonical revision và gate liên quan.

## Required, optional và provenance

[Manifest Test Kit](../../kits/test/kit.yaml) v`1.0.0` cài required workflow `test-kit`, TEA `bmad-testarch-test-design`, Katalon `create-test-cases` và Python core. Python 3.10+ cùng Codex CLI là prerequisite cho native generation. Optional XMind cần Node.js 18+/npm 9+ và SDK từ `package-lock.json`; optional Excel cần `openpyxl==3.1.5` và `et-xmlfile==2.0.0` từ hash-locked `requirements-excel.lock`. Installer không tự bootstrap dependency tùy chọn. Pin, license và nguồn upstream: [Provenance](PROVENANCE.md) và [notices](../../THIRD_PARTY_NOTICES.md).

## Không thuộc V1

Automation planning, automation code generation, Playwright/API execution, execution evidence, flaky management, failure triage và automated defect handling thuộc **Automation Test V2**. V1 không có XMind/Excel → canonical import, bidirectional sync, Jira/TestOps/Xray write hoặc claim production testware từ `TEST_ONLY` fixture.

Xem [Quick Start](TEST_KIT_QUICKSTART.md) · [Usage Guide](TEST_KIT_USAGE_GUIDE.md) · [Ví dụ CR-001](../../kits/test/examples/CR-001/README.md).
