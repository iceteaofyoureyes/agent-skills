# Historical V1 LEGACY_COMPAT: CR-001 Appointment Scheduling

This material is retained as V1 history. It is not the default Test VNext example or an authority source.


Đây là **documentation example**, không phải raw TEA/Katalon output, runtime golden fixture, Human receipt thật hay production approval. Nó dùng đúng semantic spine của [BA Kit CR-001](../../../ba/examples/CR-001/README.md) để một tester thấy luồng từ BA authority tới manual testware. ID `TD-DOC-*`/`TC-DOC-*` bên dưới chỉ là minh họa; runtime giữ nguyên ID thực tế từ output đã chuẩn hóa.

## 01 — Approved BA Baseline là đầu vào

Đọc [Business Rules](../../../ba/examples/CR-001/vi/03-approved-business-rules.md), [SRS excerpt](../../../ba/examples/CR-001/vi/04-srs-excerpt.md) và [handoff example](../../../ba/examples/CR-001/vi/05-engineering-handoff.yml) cùng BA decisions được handoff tham chiếu. Handoff documentation này có `APPROVED_FOR_ENGINEERING` và hash cho adjacent example sources; **không** là approval cho một project production thật.

Các fact đã nêu trong BA example:

- `FR-001`/`BR-008`: Appointment hợp lệ được tạo ở `Scheduled`.
- `FR-002`/`BR-006`: chỉ xung đột với Appointment `Scheduled` cùng Veterinarian theo khoảng nửa mở `[start, end)`; lịch chạm nhau được phép.
- `FR-005`/`BR-010`: hoàn tất Appointment `Scheduled` tạo chính xác một Visit.
- `BR-005`: thời lượng phải lớn hơn 0 nhưng **maximum duration UNKNOWN**.
- `FR-006`/`BR-014`: xem Appointment được xác nhận; filter, sort và pagination vẫn **UNKNOWN**.

Không tự suy ra max duration, default sort, page size, API hay UI control từ ví dụ này.

## 02 — TEA analysis và Design draft

Adapter chuyển BR/SRS/decisions đã duyệt sang TEA, giữ raw analysis làm evidence rồi chuẩn hóa Canonical Test Design. Ví dụ hai **loại** scenario mà Human cần thấy:

| Design minh họa | Truy vết | Expected Behavior | Open question |
|---|---|---|---|
| Kiểm tra hai lịch chạm nhau của cùng Veterinarian | `FR-002`, `BR-006` | Lịch chạm nhau theo `[start, end)` được phép | Không |
| Kiểm tra giới hạn tối đa của duration | `BR-005` | `null` — deferred | Maximum duration là bao nhiêu? `UNKNOWN` |
| Kiểm tra bộ lọc danh sách Appointment | `FR-006`, `BR-014` | `null` — deferred | Filter/sort/pagination được quyết định thế nào? `UNKNOWN` |

Một row canonical chứa `design_id`, `hierarchy_path`, `scenario_title`, `expected_behavior`, `requirement_refs`, `open_questions`, `review_status`. P0–P3 từ TEA chỉ là advisory. Actual row IDs/titles phải lấy từ raw output hiện hành; bảng trên không cấp ID thay cho TEA.

## 03 — Human Design Gate

Agent trình exact Design collection ở `DESIGN_REVIEW` với validator findings. Human kiểm tra resolved vs deferred, trace và wording. Nếu TEA đã điền một giới hạn duration chưa được BA quyết định, Human gửi `REQUEST_CHANGES`; nếu Design đúng, Human `APPROVE` **artifact ID/revision/snapshot hiện tại**. Host xác thực Human và lưu receipt cùng BA refs/semantic SHA-256. `ANSWER` về duration là BA clarification, không phải Design approval. Chỉ sau receipt hợp lệ state thành `APPROVED_DESIGN`.

## 04 — Canonical Testcases

Katalon nhận approved Design, rồi adapter chuẩn hóa manual cases. Một case minh họa cho `FR-002`/`BR-006` có:

```text
name: Hai lịch chạm nhau của cùng Veterinarian
objective: Kiểm tra rule [start, end) đã duyệt
preconditions: Có một Appointment Scheduled dùng làm dữ liệu đối chiếu
test_data: Dữ liệu Appointment hợp lệ cho cùng Veterinarian
steps:
  1. action: Đặt lịch thứ hai bắt đầu đúng thời điểm lịch thứ nhất kết thúc
     test_data: null (nếu raw step không ghi dữ liệu step riêng)
     expected_result: Hai Appointment chạm nhau được phép theo BR-006
priority: P1 (chỉ minh họa; giá trị thật phải theo raw case, chỉ advisory)
requirement_refs: [FR-002, BR-006]
test_design_refs: [ID của exact approved Design scenario]
execution_dependencies: chỉ rõ setup/action/observation contract còn thiếu
```

Đây là **phác thảo đọc hiểu**, không phải case có thể chạy ngay: BA rule không chỉ rõ API/UI thao tác, fixture, hoặc cách quan sát lưu trữ. Mỗi thiếu hụt material phải được ghi `OPEN`, không tự invent. Case cho maximum duration hoặc list filter vẫn deferred cho tới khi BA giải quyết UNKNOWN; không tạo assertion giả.

## 05 — Human Case Gate

Human review `CASE_REVIEW` theo thứ tự step, test data, expected result, trace và execution dependencies. Nếu một material dependency còn `OPEN`, `APPROVE` bị từ chối; Human có thể `REQUEST_CHANGES` hoặc đưa approved execution contract đúng scope rồi review revision mới. Ví dụ hiện tại **không có** execution contract hoặc production Human receipt để tuyên bố Case Gate đã qua.

## 06 — `APPROVED_TESTWARE` và `STOP_V1` là điểm đến có điều kiện

Khi một project thật đã có Design approval, testcase validation `PASS`, không còn material `OPEN` dependency và Human Case Gate receipt hợp lệ, runtime tạo `approved-testware.json` và state `STOP_V1`. Đó là manual testware của **snapshot đó**, không phải kết quả thực thi hay production approval cho fixture trong thư mục ví dụ này.

```text
Approved BA → Canonical Design → Human Design Gate
→ Canonical Testcases → Human Case Gate
→ APPROVED_TESTWARE → STOP_V1
```

## 07 — XMind và Excel là nhánh trình bày

- Sau `APPROVED_DESIGN`, Human có thể yêu cầu XMind. Map Logic Chart Right hiển thị scenario resolved và cảnh báo `⚠ Chờ BA` cho deferred; external manifest giữ ID/ref/hash. XMind V1 dùng profile đã pin, không nhận Human-supplied XMind template.
- Sau `APPROVED_TESTWARE`/`STOP_V1`, Human có thể yêu cầu Excel. Default là một testcase/một row; Step/Test Data/Expected Result theo thứ tự, `Key` để trống. `*.xlsx.projection.json` giữ canonical ID và trace. Template Excel hợp lệ chỉ đổi presentation.

Chỉnh file XMind/Excel không sửa canonical source. Nếu semantics đổi, quay lại Design/Testcases và gate thích hợp. [Quick Start](../../../../docs/vi/TEST_KIT_QUICKSTART.md) · [Usage Guide](../../../../docs/vi/TEST_KIT_USAGE_GUIDE.md) · [Workflow](../../../../docs/vi/TEST_KIT_WORKFLOW.md).

## 08 — Project customization V1.1

[Ví dụ policy CR-001](customization/README.md) có profile/rule/TEA bridge project-owned cho naming tiếng Việt, atomic cases và boundary/negative guidance. Ví dụ giữ maximum duration `UNKNOWN`, chỉ rõ exact policy snapshot/evidence, stale-policy rejection và Excel project-template precedence. Toàn bộ example là `TEST_ONLY`, không cấp production Human approval.
