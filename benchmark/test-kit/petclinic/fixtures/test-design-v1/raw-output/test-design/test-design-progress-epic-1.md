---
runScope: 'epic'
runKey: 'epic-1'
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted: ['step-01-detect-mode', 'step-02-load-context', 'step-03-risk-and-testability', 'step-04-coverage-plan', 'step-05-generate-output']
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-09-26'
---

# Tiến độ Test Design Epic 1

- Chế độ: Epic-level theo yêu cầu rõ ràng của người dùng.
- Epic: 1 — CR-001 Appointment Scheduling.
- Đầu vào tối thiểu: epic và tiêu chí FR-001–FR-006 đã có; kiến trúc hiện trạng không được cung cấp.
- Phạm vi authority: SRS và Business Rules được duyệt; BA UNKNOWN giữ nguyên, không trả lời.
- Đường dẫn checkpoint theo yêu cầu của lượt chạy: raw-output/test-design/test-design-progress-epic-1.md.
- Cấu hình: fullstack; Playwright utils=false; Pact.js utils=false; Pact MCP=none; browser automation=none; execution mode=sequential.
- Tài liệu authority đã nạp: inputs/adapter/epic-1.md; inputs/adapter/business-rules.md; inputs/adapter/open-decisions.md.
- Nguồn nền đối chiếu: baseline SRS excerpt và Business Rules; không dùng baseline gap review hay engineering handoff làm business authority.
- Knowledge fragments: risk-governance.md; probability-impact.md; test-levels-framework.md; test-priorities-matrix.md.
- Không có architecture, current-system evidence, prior system-level design hay test inventory được cung cấp trong raw-output; không kiểm tra source/test suite, không duyệt browser và không chạy test.
- NFR thresholds và contract-testing artifacts không được cung cấp; không nạp NFR/contract fragments.
- Đánh giá rủi ro: các luồng ngày/giờ và thời lượng; phát hiện xung đột và lưu đồng thời; vòng đời/hủy/hoàn tất và Visit; đổi lịch tự loại khỏi so khớp. Mọi xác suất/ảnh hưởng là ước lượng hoạch định, không phải bằng chứng hệ thống.
- Coverage được chia atomic theo yêu cầu và rủi ro; FR-001/BR-005 (thời lượng tối đa) và FR-006/BR-014 (filter/sort/pagination) giữ hàng chờ quyết định BA, không có kết quả pass/fail.
- Ưu tiên, mức kiểm thử, effort và thresholds được đánh dấu khuyến nghị; kiểm thử logic dự kiến Unit/Integration, kiểm thử hành trình chỉ dùng E2E nếu có kênh UI được xác định sau.
- Tài liệu hoàn tất tại raw-output/test-design-epic-1.md; không có test thực thi, release verdict hoặc mã automation.
- Hoàn tất validation checklist bằng rà soát tài liệu và trace; Epic 1 không có architecture/NFR/current-system evidence nên các nội dung đó được nêu rõ là chưa có.
