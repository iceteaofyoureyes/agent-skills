# Test Kit VNext theo tình huống

Hướng dẫn này áp dụng cho Test Kit Manual VNext. Luôn bắt đầu từ Engineering Handoff VNext hiện hành và để runtime revalidate BA Human proof.

## 1. Bắt đầu feature mới

Yêu cầu agent tạo manual Test Design từ đường dẫn Engineering Handoff VNext chính xác. BA WHAT và canonical `BR-*`/`FR-*` trace không được mở rộng bằng Dev Handoff, code hiện tại, TEA hay Project Test Policy.

Chỉ cung cấp approved UX context khi nó thuộc phạm vi feature. Context đó cần trusted Human authentication và byte/snapshot recheck. Authority context chỉ yêu cầu UX khi `ux_required: true`; từ `field`, `input` hay `page` không tạo requirement. Human review quyết định consistency ngữ nghĩa trong văn xuôi.

## 2. Review Test Design

Khi run tới `DESIGN_REVIEW`, xem canonical Design, unresolved questions, `BR/FR` refs, source hashes và toàn bộ input refs. Validator `PASS` không phải approval. Human có thể yêu cầu thay đổi hoặc approve exact snapshot bằng receipt được host xác thực.

`REQUEST_CHANGES` tạo revision mới và giữ snapshot/review evidence cũ. Không sửa trực tiếp artifact đã review hoặc dùng receipt cũ cho revision mới.

## 3. Tạo và review Testcases

Chỉ sau `APPROVED_DESIGN` mới chạy pinned Katalon create-test-cases. Review objective, preconditions, test data, từng action/expected result, priority, Design refs và dependencies ở `CASE_REVIEW`.

Nếu BA để UNKNOWN, giữ câu hỏi mở; không tự thêm expected result. Nếu dependency bắt buộc cho execution còn `OPEN`, Case approval bị chặn. `PASS` của validator chỉ xác nhận dữ liệu có cấu trúc hợp lệ.

## 4. Human Case Gate và handoff

Human approve hoặc yêu cầu sửa đúng Case snapshot và refs. Khi approve, runtime tạo Approved Testware VNext `HANDOFF_MANIFEST` với Testcase collection, Approved Design, hai gate receipts, BA handoff/baseline, optional contexts và trace summary. Đọc lại manifest và kiểm tra các ref/hash trước handoff.

`APPROVED_TESTWARE` là điểm kết thúc của manual lane. Không suy ra `EXECUTION_READY`, kết quả chạy test, `VERIFIED` hoặc merge readiness.

## 5. Tiếp tục run đã lưu

Resume từ run directory đã persist. Runtime xác thực lại BA, UX/Dev context nếu có, gate receipts, bytes và exact refs trước khi tiếp tục. Nếu nguồn đã đổi, dừng và tạo revision/review mới; không hand-edit state hoặc receipt để bỏ qua stale evidence.

## 6. Xuất bản chiếu

- Yêu cầu XMind chỉ sau `APPROVED_DESIGN`; kết quả là `DERIVED` và không sửa canonical Design.
- Yêu cầu Excel chỉ sau `APPROVED_TESTWARE`; kết quả là `DERIVED` và không sửa canonical Testcases.
- Nếu dependency không có, core VNext vẫn dùng được và Doctor báo capability tùy chọn `DEGRADED`.

## 7. Doctor, policy và V1

Doctor `READY` chỉ xác nhận package/core capability; nó không cấp Human approval. Project Test Policy là guidance không authority và được ràng buộc hash khi được tiêu thụ. Lỗi integrity/capability bắt buộc phải xử lý trước khi tạo run mới.

V1 được đọc trong chế độ `LEGACY_COMPAT`, `vnext_authority=false`; không migrate V1 thành VNext approval. Delivery Manifest không cần cho Test VNext. Automation planning/execution thuộc Phase 7+.

Ví dụ mặc định: [Neutral Resource Reservation VNext](../../kits/test/examples/vnext/neutral/README.md).
