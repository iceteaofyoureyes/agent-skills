# Test Kit V1 theo tình huống của tester

Dùng ngôn ngữ tự nhiên với agent đã cài `test-kit` trong project. Nêu artifact/revision, operation và output directory khi cần; agent phải dựa vào run state và receipt hiện hành, không suy ra approval từ lời nói mơ hồ. Xem [Quick Start](TEST_KIT_QUICKSTART.md) để cài đặt và [Workflow](TEST_KIT_WORKFLOW.md) để hiểu gate.

## 1. Tạo Test Design từ approved BA baseline

```text
Tạo Test Design cho CR-001 từ approved engineering-handoff.yml này.
Đối chiếu BR/SRS/decisions theo SHA trong handoff. Dùng TEA đã cài.
Giữ UNKNOWN và trace FR/BR; dừng ở DESIGN_REVIEW cho tôi review.
```

Kết quả mong đợi: raw TEA evidence, Canonical Test Design và validator findings trong run directory mới. Không có Design approval tự động.

## 2. Chỉ review Test Design

```text
REVIEW only Canonical Test Design revision <revision>.
Kiểm tra từng scenario, FR/BR ref, expected_behavior và open_questions.
Không sửa artifact, không advance gate.
```

`REVIEW` là inspect, không đổi semantic payload hay `review_status`.

## 3. Yêu cầu sửa Design

```text
REQUEST_CHANGES cho Design <artifact_id> revision <revision>:
TD-... đang khẳng định maximum duration dù BR-005 còn UNKNOWN.
Giữ câu hỏi BA và mở revision mới; không approve.
```

Host ghi Human receipt và feedback cho snapshot cũ; revision mới bắt đầu `DRAFT_DESIGN`. Không sửa đè revision đã review.

## 4. Explicitly approve Design

```text
Tôi APPROVE Canonical Test Design <artifact_id> revision <revision>
đúng snapshot đang ở DESIGN_REVIEW làm coverage baseline cho testcase.
```

Host phải xác thực Human, kiểm tra semantic SHA và BA input refs hiện tại rồi ghi receipt. `APPROVED_DESIGN` mới cho phép production testcase generation và XMind projection.

## 5. Tạo canonical Testcases

```text
Từ APPROVED_DESIGN hiện tại, tạo manual testcases bằng create-test-cases.
Giữ đúng thứ tự step, Test Data theo scope nguồn và trace FR/BR/TD.
Khai báo execution dependency còn thiếu; dừng ở CASE_REVIEW.
```

Adapter chuẩn hóa raw Katalon output. Trường hợp action/Expected Result không tách được hoặc trace mơ hồ sẽ fail closed, không phát minh step.

## 6. Chỉ review testcase

```text
REVIEW only Canonical Testcases revision <revision>.
So Precondition, Objective, Test Data, từng action/Expected Result,
priority, refs và execution_dependencies. Không mutate/approve.
```

## 7. Yêu cầu sửa testcase

```text
REQUEST_CHANGES cho Testcases revision <revision>:
TC-... thiếu cách quan sát việc tạo đúng một Visit.
Ghi execution dependency material OPEN nếu chưa có approved contract.
```

Human feedback mở revision `DRAFT_CASES` mới. Không tự đổi business requirement hoặc gán contract chưa được duyệt.

## 8. Phê duyệt manual testware

```text
Tôi APPROVE Canonical Testcases <artifact_id> revision <revision>
đúng snapshot ở CASE_REVIEW làm manual testware cho feature này.
```

Receipt phải gắn BA + approved Design refs hiện hành. Material `OPEN` execution dependency hoặc validator failure chặn approval; Human cần xử lý contract/revision trước. Khi hợp lệ, runtime ghi `APPROVED_TESTWARE` và chuyển `STOP_V1`.

## 9. BA baseline có UNKNOWN

```text
BR-005 chưa xác định maximum appointment duration.
Giữ UNKNOWN và open question; deferred scenario phụ thuộc ngưỡng này.
Không tự đặt một maximum. Các scenario dùng rule đã rõ vẫn có thể review riêng.
```

`deferred` nghĩa chưa có observable expected behavior được BA xác nhận để khẳng định pass/fail. Ví dụ CR-001 còn UNKNOWN về maximum duration và filter/sort/pagination của danh sách. Không biến câu hỏi thành testcase kết quả cụ thể.

## 10. Xuất XMind từ Design đã duyệt

```text
Tôi yêu cầu XMind projection cho APPROVED_DESIGN hiện tại.
Đặt output trong <run-dir>/projections/xmind và giữ external projection manifest.
```

V1 dùng Logic Chart Right và profile nhóm chức năng đã pin. Resolved scenario hiển thị Expected Behavior; deferred scenario hiện cảnh báo chờ BA. Nếu nhóm chức năng thiếu/mơ hồ, exporter trả `CANNOT_PROJECT_HUMAN_PROFILE`. XMind không phải canonical input.

## 11. Human cung cấp XMind template

XMind V1 **chưa có** tham số template hoặc inspector cho workbook/map Human cung cấp. Hãy nói rõ rằng yêu cầu này không được V1 hỗ trợ và giữ nguyên canonical Design; đừng tự dùng template đó hoặc ngầm đổi sang default như thể đã đáp ứng yêu cầu. Quy tắc `HUMAN_SUPPLIED_APPROVED_TEMPLATE → PROJECT_TEMPLATE → DEFAULT_TEMPLATE` hiện chỉ được triển khai cho **Excel**. Với XMind, lỗi mapping của profile đã pin là `CANNOT_PROJECT_HUMAN_PROFILE`, không phải `CANNOT_PROJECT_TEMPLATE`.

## 12. Xuất Excel testcase

```text
Tôi yêu cầu Excel projection cho APPROVED_TESTWARE hiện tại.
Đặt output trong <run-dir>/projections/excel và giữ *.xlsx.projection.json.
```

Default là một testcase trên mỗi row, Step/Test Data/Expected Result theo thứ tự trong cell nhiều dòng. `Key` mặc định để trống; `TC-xxx` vẫn ở canonical artifact và external manifest.

## 13. Dùng Excel template do Human cung cấp

```text
Xuất Excel theo template C:\project\templates\testcases.xlsx đã được tôi chọn.
Inspect và báo mapping trước khi dùng. Nếu template thiếu field hoặc mơ hồ,
dừng với CANNOT_PROJECT_TEMPLATE; không fallback sang default.
```

Precedence của Excel là `HUMAN_SUPPLIED_APPROVED_TEMPLATE → PROJECT_TEMPLATE → DEFAULT_TEMPLATE`. Template chỉ điều khiển sheet/headers/row model/style được hỗ trợ; name, preconditions, ordered actions, Test Data đúng scope và expected results phải còn biểu diễn được. Objective vẫn ở external manifest nếu template không có cột tương ứng. Đọc [template policy](TEST_KIT_CAPABILITIES.md#template-và-bản-chiếu).

## 14. Review XMind/Excel đã xuất

```text
REVIEW only projection và manifest cạnh nó so với canonical snapshot hiện tại.
Report missing/deferred/trace mismatch; không dùng chỉnh sửa file projection làm approval.
```

Nếu nội dung test sai, quay lại Canonical Test Design/Testcases và Human Gate. File XMind/Excel bị sửa không tự import ngược. Workbook xuất ra được seal như evidence snapshot; muốn chỉnh cho công việc cá nhân, Human tạo bản sao riêng.

## 15. Tiếp tục session cũ

```text
CONTINUE run <run-dir>. Cho biết state hiện tại và next valid action.
Không tự approve hoặc bỏ qua gate.
```

`CONTINUE`, “Next”, “OK”, “PASS” chỉ định hướng tiếp tục; không phải receipt `APPROVE`.

## 16. Doctor báo drift/missing/dependency

```text
Doctor báo MODIFIED_MANAGED_FILE cho TEA checklist.md.
Cho tôi biết file nào đổi và cách khôi phục từ đúng package version; không ghi đè edit của tôi.
```

`MODIFIED_MANAGED_FILE`/`MISSING_MANAGED_FILE`: kiểm tra file, khôi phục từ cùng package đã pin, chạy doctor lại. Reinstall giữ local edit và vẫn báo drift. `PACKAGE_DEFINITION_INVALID`, `PACKAGE_AUTHORITY_INVALID`, `PACKAGE_METADATA_INVALID`: kiểm tra bộ cài/manifest, không tự sửa hash trong install record để làm doctor xanh. `DEPENDENCY_MISSING`: phân biệt Codex bắt buộc với dependency XMind/Excel tùy chọn.

## 17. XMind dependency chưa cài

Core Test Design/Testcase vẫn dùng được. Nếu cần XMind, cài Node.js 18+/npm 9+, chạy `npm ci` trong `.agents/skills/.test-kit/tooling/xmind/`, rồi thử lại. Không coi lỗi `XMIND_SDK_UNAVAILABLE` là lỗi business rule.

## 18. Excel dependency chưa cài

Core vẫn dùng được. Cài vào **đúng Python environment** đang chạy exporter bằng `python -m pip install --require-hashes -r .agents/skills/.test-kit/tooling/requirements-excel.lock`. Không sửa dependency pin chỉ để che lỗi import.

## 19. Yêu cầu Playwright/API automation trong V1

```text
Test Kit V1 đã dừng ở APPROVED_TESTWARE → STOP_V1.
Không chạy/sinh Playwright hoặc API automation trong run này.
Automation Test V2 là công việc hạ nguồn riêng.
```

V1 không tạo execution result, flaky report, triage, automated defect handling hoặc production approval thay Human.

## 20. TEST_ONLY fixture có vẻ “approved”

Receipt mô phỏng và output `TEST_ONLY`/`not_for_production: true` chứng minh đường thử của framework, không phải phê duyệt thật cho project. Production chỉ dùng current canonical snapshot và Human receipt do host xác thực. Đừng tái sử dụng TEST_ONLY artifact để vượt gate.

Xem [Khả năng và template policy](TEST_KIT_CAPABILITIES.md) · [Workflow/Human Gates](TEST_KIT_WORKFLOW.md) · [Ví dụ CR-001](../../kits/test/examples/CR-001/README.md) · [Cài đặt](INSTALLATION.md).
