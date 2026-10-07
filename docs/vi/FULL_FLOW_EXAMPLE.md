# Ví dụ Full Flow

Ví dụ này cố ý nhỏ. Mục tiêu là thấy **ai quyết định việc gì**, không phải trình diễn toàn bộ schema.

## Change request

> Thêm text search và multi-status filter cho Project List.

Giả sử đây là một web application đang chạy.

## 1. Foundation — khôi phục đủ context

Project chưa có tài liệu đáng tin cho Project List.

Foundation ghi nhận:

- screen/service hiện tại nằm ở đâu;
- điều gì đã xác nhận về current system;
- điều gì mới là inference;
- điều gì vẫn UNKNOWN;
- repository boundary liên quan.

Foundation **không** quyết định behavior search mới.

## 2. BA Kit — chốt WHAT

BA review có thể tìm ra các câu hỏi:

- Search những field nào?
- Có phân biệt hoa/thường không?
- Có chọn nhiều status không?
- Text + status kết hợp AND hay OR?
- Empty state có ý nghĩa gì?

Human trả lời. BA biến các quyết định thành Business Rules / Functional Requirements có trace và tạo exact approved baseline.

~~~text
Requirement
→ clarification
→ BR / FR
→ canonical SRS
→ Human approval
→ Engineering Handoff
~~~

WHAT đã được duyệt. Repository ownership và implementation design vẫn thuộc Engineering.

## 3. Dev Kit — quyết định HOW và implement

Dev nhận Engineering Handoff đã approved rồi xác định:

- repository/component bị ảnh hưởng;
- ownership triển khai;
- technical risk;
- engineering decision quan trọng;
- build/static/unit/integration checks.

Nếu Dev phát hiện business rule chưa rõ, Dev route \`UPSTREAM_GAP\`, không tự đoán WHAT.

Sau implementation và engineering verification:

~~~text
Dev → READY_FOR_TEST
~~~

Điều này chỉ có nghĩa engineering work đã sẵn sàng cho Test, không có nghĩa feature đã VERIFIED.

## 4. Test Kit — thiết kế bằng chứng

Test tạo coverage từ BR/FR đã approved:

~~~text
Test Design
→ Human Design Gate
→ APPROVED_DESIGN
→ Testcases
→ Human Case Gate
→ APPROVED_TESTWARE
~~~

Automation chỉ được plan sau approved testware.

~~~text
APPROVED_TESTWARE
→ Automation Plan
→ implementation/review
→ EXECUTION_READY
~~~

\`EXECUTION_READY\` nghĩa execution input đã được bind; không có nghĩa test đã chạy hoặc PASS.

## 5A. Initial execution sạch

Nếu mọi Testcase bắt buộc đều có Observation PASS và không còn Finding mở:

~~~text
EXECUTION_READY
→ Execution
→ mọi required observation PASS
→ authenticated Tester
→ VERIFIED
~~~

Nhánh initial PASS sạch **không cần retest**.

## 5B. Nhánh defect

Giả sử status filter trả về archived item sai.

Tester ghi Observation và classify Finding. Nếu đó là product defect:

~~~text
Finding
→ DEFECT
→ DEFECT_READY_FOR_DEV
→ Dev Fix
→ fresh engineering verification
→ READY_FOR_RETEST
→ Tester retest
   ├─ PASS → VERIFIED
   └─ FINDING → REOPENED
~~~

Command fail tự nó không tự động thành DEFECT. Test phải classify observation theo approved oracle.

## Các loại Finding khác

Không phải Finding nào cũng route Dev:

- \`SPEC_GAP\` → requirement/spec authority;
- \`BUSINESS_DECISION_REQUIRED\` → Human/business authority;
- \`TEST_ISSUE\` → Test owner;
- \`ENVIRONMENT_ISSUE\` → environment/operations owner.

## Human vẫn kiểm soát gì?

Human authority được yêu cầu tại các gate mà workflow định nghĩa:

- business baseline;
- Test Design;
- Testcases;
- material technical decision khi policy/risk yêu cầu;
- quyết định merge/release cuối.

Agent, validator, Doctor hoặc generated artifact không thể tự approve.

## Đọc tiếp

- [Bắt đầu](GETTING_STARTED.md)
- [Kiến trúc](ARCHITECTURE.md)
- [Readiness states](READINESS_STATES.md)
