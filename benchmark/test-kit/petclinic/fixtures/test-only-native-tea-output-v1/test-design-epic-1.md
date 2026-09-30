---
workflowStatus: 'completed'
totalSteps: 5
stepsCompleted:
  - step-01-detect-mode
  - step-02-load-context
  - step-03-risk-and-testability
  - step-04-coverage-plan
  - step-05-generate-output
lastStep: 'step-05-generate-output'
nextStep: ''
lastSaved: '2026-09-25'
inputDocuments:
  - benchmark/test-kit/petclinic/runtime-proof/inputs/tea/epic-1.md
  - benchmark/test-kit/petclinic/runtime-proof/inputs/baseline/03-approved-business-rules.md
  - benchmark/test-kit/petclinic/runtime-proof/inputs/baseline/04-srs-excerpt.md
  - benchmark/test-kit/petclinic/runtime-proof/inputs/baseline/05-engineering-handoff.yml
author: 'Codex — Master Test Architect'
language: 'vi'
---

# Test Design: Epic 1 — CR-001 Appointment Scheduling

**Ngày:** 2026-09-25  
**Tác giả:** Codex — Master Test Architect  
**Trạng thái:** Draft  
**Phạm vi thiết kế:** Epic-level / full design

## Tóm tắt

Thiết kế này phủ FR-001–FR-006 và BR-001–BR-014. `epic-1.md` chỉ cung cấp cấu trúc epic; nội dung nghiệp vụ được lấy duy nhất từ ba baseline được chỉ định. Mã PetClinic hiện tại chỉ được dùng làm bằng chứng bổ sung về hệ thống và phạm vi hồi quy.

- **Rủi ro:** 7 rủi ro; 3 cao (điểm ≥6), 4 trung bình.
- **Kịch bản:** 35 kịch bản nguyên tử: P0 = 2, P1 = 32, P2 = 1 đang chờ quyết định BA, P3 = 0. Có 34 kịch bản có thể chuẩn bị theo quy tắc hiện có; ca biên thời lượng tối đa bị chặn.
- **Trọng tâm rủi ro:** đặt lịch đồng thời cho cùng Veterinarian, so sánh thời điểm theo `Asia/Ho_Chi_Minh`, và tính đúng một Visit khi hoàn tất.
- **NFR:** chỉ có kết quả nhất quán dữ liệu/nghiệp vụ cho concurrency và số lượng Visit. Baseline không đặt ngưỡng hiệu năng, tải, độ sẵn sàng, tuân thủ hay vận hành.
- Đây là kế hoạch kiểm thử. Không tạo test code/automation, không chạy test, không xuất XMind/Excel, không chạy release gate và không đưa ra release verdict.

## Nguồn và ranh giới nghiệp vụ

Nguồn nghiệp vụ duy nhất:

- `benchmark/test-kit/petclinic/runtime-proof/inputs/baseline/03-approved-business-rules.md`
- `benchmark/test-kit/petclinic/runtime-proof/inputs/baseline/04-srs-excerpt.md`
- `benchmark/test-kit/petclinic/runtime-proof/inputs/baseline/05-engineering-handoff.yml`

Nguồn cấu trúc epic: `benchmark/test-kit/petclinic/runtime-proof/inputs/tea/epic-1.md`. Tên Epic, số Epic và cách nhóm FR trong adapter không bổ sung business semantics. Không dùng kết quả Test Design Stage 1–2 cũ.

Engineering Handoff để API, schema, transaction, locking và cơ chế concurrency cho quyết định kỹ thuật hạ nguồn. Thiết kế này chỉ yêu cầu kiểm chứng kết quả nghiệp vụ đã duyệt, không quy định cách triển khai.

### Bằng chứng hệ thống hiện tại

`spring-petclinic-rest` có Visit model/API và kiểm thử controller Visit; `spring-petclinic-angular` có Visit service/component specs và cấu hình Playwright Chromium cho thư mục `e2e`. Đây là điểm tham chiếu hồi quy cho luồng tạo Visit và bộ khung kiểm thử hiện có. Chúng không xác định Appointment behavior, quyền Clinic Staff, API Appointment hoặc mapping giữa Appointment và Visit. Không tìm thấy E2E spec khớp cấu hình trong lượt quét tĩnh. Không chạy test.

## Ngoài phạm vi

| Hạng mục | Lý do | Cách xử lý rủi ro |
|---|---|---|
| API, schema, route, event, locking và transaction cụ thể | Engineering Handoff để các quyết định này cho engineering; chưa có contract được duyệt. | Chọn contract trước khi dựng test environment; test theo observable state và invariant. |
| Giới hạn thời lượng tối đa | UNKNOWN trong BR-005. | Giữ ca biên ở trạng thái blocked đến khi BA quyết định. |
| Bộ lọc, default sorting, phân trang/page size | UNKNOWN trong BR-014. | Chỉ kiểm tra khả năng xem Appointment; không kiểm tra thứ tự, bộ lọc hoặc kích thước trang. |
| Requiredness, default duration, Clinic Staff permission mapping | Chưa được baseline quyết định và người dùng yêu cầu không tự suy ra. | Ca thành công nhập tường minh các giá trị hợp lệ; dùng identity đã được xác nhận là Clinic Staff khi mapping sẵn sàng. |
| HTTP status, nội dung lỗi, mapping Appointment-to-Visit | Chưa có quy tắc được duyệt. | Kiểm tra trạng thái/dữ liệu cuối và số lượng Visit; không khẳng định mã, câu chữ hoặc field mapping. |
| Performance/load/chaos và compliance | Không có workload, threshold hay yêu cầu tuân thủ trong baseline. | Chỉ lập kế hoạch khi có yêu cầu/threshold được duyệt. |

## Risk Assessment

Thang xác suất và tác động 1–3; điểm = xác suất × tác động. Đây là ước lượng lập kế hoạch, không phải tần suất lỗi đo được từ implementation. Điểm ≥6 cần mitigation. Mốc thời gian dưới đây là mốc readiness theo vai trò, không phải ngày cam kết vì baseline không cung cấp lịch dự án.

### Rủi ro cao (điểm ≥6)

| Risk ID | Loại | Rủi ro có bằng chứng | P | I | Điểm | Mitigation và kiểm chứng | Owner | Thời điểm |
|---|---|---|---:|---:|---:|---|---|---|
| R-001 | DATA | BR-006/BR-013 yêu cầu không lưu lịch chồng lấn cùng Veterinarian và chỉ lưu Appointment không xung đột. Handoff để transaction/locking cho engineering; race có thể lưu hai lịch xung đột. | 2 | 3 | 6 — Cao | Kiểm thử API/persistence với hai request đồng thời; đọc trạng thái đã commit, xác minh chỉ một lịch xung đột được lưu và cả hai lịch không xung đột đều được lưu. Không kiểm tra một cơ chế locking cụ thể. | Backend / Architecture | Trước khi sẵn sàng kiểm thử tích hợp |
| R-002 | BUS | FR-001/BR-004 đòi hỏi thời điểm bắt đầu phải sau hiện tại theo `Asia/Ho_Chi_Minh`. Sai lệch ở phép so sánh thời gian có thể nhận lịch quá khứ/hiện tại hoặc từ chối lịch hợp lệ. | 2 | 3 | 6 — Cao | Dùng đồng hồ kiểm soát; kiểm tra quá khứ, đúng hiện tại, tương lai và instant tương đương qua biểu diễn thời gian. | Backend + QA | Trước khi sẵn sàng kiểm thử acceptance |
| R-003 | DATA | FR-005/BR-010 yêu cầu Appointment chuyển Completed và tạo chính xác một Visit; BR-002 giữ Appointment là khái niệm riêng. Lặp hoặc xử lý đồng thời có thể tạo Visit thừa hoặc lệch trạng thái. | 2 | 3 | 6 — Cao | So sánh trạng thái và số Visit trước/sau; kiểm tra hoàn tất, gửi lặp tuần tự và đồng thời. Chưa kiểm tra mapping field. | Backend / Architecture | Trước khi sẵn sàng kiểm thử luồng hoàn tất |

### Rủi ro trung bình (điểm 3–4)

| Risk ID | Loại | Rủi ro có bằng chứng | P | I | Điểm | Mitigation | Owner |
|---|---|---|---:|---:|---:|---|---|
| R-004 | BUS | BR-005 xác định thời lượng >0 nhưng maximum là UNKNOWN; chưa thể chọn biên trên hoặc khẳng định fixture dương nằm dưới giới hạn. | 2 | 2 | 4 — Trung bình | BA quyết định maximum và giá trị dương hợp lệ trước ca biên; đến lúc đó không gán giá trị giới hạn. | BA / Product |
| R-005 | SEC | Các FR gọi actor là Clinic Staff nhưng không định nghĩa mapping từ actor sang identity/permission của ứng dụng. | 2 | 2 | 4 — Trung bình | Chuẩn bị identity Clinic Staff đã được phê duyệt cho luồng dương; hoãn kỳ vọng từ chối đối với vai trò khác. | BA + Security / Engineering |
| R-006 | DATA | FR-005/BR-010 yêu cầu một Visit nhưng không nói field nào của Appointment được đưa vào Visit. | 2 | 2 | 4 — Trung bình | Chỉ xác minh cardinality. Chốt data contract trước khi viết assertion mapping. | BA + Architecture |
| R-007 | BUS | FR-006 yêu cầu xem Appointment nhưng BR-014 để UNKNOWN bộ lọc, sorting và pagination/page size. Assertion tự chọn các chi tiết này có thể khóa hành vi chưa duyệt. | 2 | 2 | 4 — Trung bình | Kiểm tra xem dữ liệu cơ bản; chờ BA quyết định trước khi kiểm tra tùy chọn danh sách. | BA / Product |

### Mitigation cho rủi ro cao

**R-001 — lịch xung đột khi ghi đồng thời**

1. Engineering chọn cơ chế đảm bảo invariant sau commit; thiết kế test không áp đặt lock hay transaction cụ thể.
2. Dựng hai request độc lập có thời điểm bắt đầu đồng thời; kiểm tra trạng thái cuối cho trường hợp xung đột và không xung đột.
3. Evidence: kết quả API/integration cùng trạng thái Appointment đã lưu. Owner: Backend/Architecture. Thời điểm: trước test readiness. Trạng thái: Planned.

**R-002 — ranh giới thời gian và timezone**

1. Cung cấp đồng hồ có thể điều khiển cho test environment.
2. Dùng các instant quá khứ, bằng hiện tại và tương lai; so sánh biểu diễn cùng một instant qua boundary phù hợp.
3. Evidence: Appointment bị từ chối không tạo record; instant tương lai hợp lệ tạo record. Owner: Backend + QA. Thời điểm: trước acceptance-test readiness. Trạng thái: Planned.

**R-003 — đúng một Visit khi hoàn tất**

1. Implementation phải đảm bảo kết quả `Completed` và đúng một Visit theo FR-005/BR-010; kỹ thuật thực hiện do engineering chọn.
2. Kiểm tra lần hoàn tất đầu, lần gửi lại và request đồng thời trên cùng Appointment.
3. Evidence: trạng thái Appointment và delta số lượng Visit; không so sánh field mapping. Owner: Backend/Architecture. Thời điểm: trước test readiness của luồng hoàn tất. Trạng thái: Planned.

**Rủi ro tồn dư:** R-001–R-003 chưa được kiểm chứng vì đây là design, chưa có implementation evidence. R-004–R-007 còn tồn tại đến khi các quyết định nghiệp vụ/kỹ thuật tương ứng được chốt.

### Đánh giá testability

- **Controllability:** cần dữ liệu Pet/Veterinarian hợp lệ, đồng hồ điều khiển được theo `Asia/Ho_Chi_Minh`, duration dương do BA xác nhận, dữ liệu lịch có/không xung đột và khả năng đồng bộ request đồng thời. Appointment status `Cancelled`/`Completed` nên đạt qua lifecycle để xác minh transition, không cần giả định seed trực tiếp trạng thái.
- **Observability:** quan sát Appointment đã lưu, state và các giá trị đầu vào được duyệt; khi hoàn tất, quan sát state và số Visit tăng đúng một. Với hành động bị cấm, kiểm tra dữ liệu/status không đổi và không phát sinh Visit. Không khẳng định response status hay error text.
- **Repeatability/isolation:** dùng record riêng cho từng ca, đọc trạng thái sau commit; concurrency dùng hai request context và dữ liệu cách ly để kết quả cuối có thể phân định.
- **Kết luận:** quy tắc đã duyệt có thể kiểm thử bằng observable outcomes. Readiness phụ thuộc test clock, identity Clinic Staff, fixture duration và contract persistence. Current Visit tests là mẫu hồi quy kỹ thuật, không bổ sung semantics cho Appointment.

## NFR Planning

| Nhóm | Yêu cầu/ngưỡng từ baseline | Kiểm chứng dự kiến và evidence cho đánh giá sau này | Tình trạng |
|---|---|---|---|
| Security | Clinic Staff có thể thực hiện chức năng; permission mapping và expected denial chưa được định nghĩa. | Ca E2E/API dương với identity Clinic Staff đã duyệt; evidence là kết quả test truy cập. | Mapping và threshold UNKNOWN; R-005. |
| Reliability / data consistency | BR-013 quy định kết quả đặt lịch đồng thời; BR-010 quy định đúng một Visit. Không có availability/retry SLO. | TD-33/TD-34 và TD-28–TD-30; report test cùng state/count đã commit. | Functional invariant có thể kiểm tra; NFR threshold khác UNKNOWN. |
| Performance / scalability | Không có workload, latency, throughput hay capacity target. | Không lập load test threshold-based cho đến khi có mục tiêu và workload được duyệt. | UNKNOWN; không đặt p95/p99 hoặc số tải. |
| Compliance | Không có yêu cầu compliance trong các nguồn được phép. | Không bổ sung evidence ngoài baseline. | Không được nêu trong nguồn. |
| Maintainability / operations | Không có ngưỡng coverage, logging, monitoring, audit hoặc retention trong baseline. | Xem xét khi có requirement được duyệt. | Không được nêu trong nguồn. |

Không có NFR PASS/CONCERNS/FAIL assessment trong tài liệu này; việc đó chỉ thực hiện sau khi có implementation evidence.

## UNKNOWN cần giữ nguyên

- Maximum Appointment duration.
- Bộ lọc danh sách, default sorting, pagination và page size.
- Default duration.
- Requiredness của từng input/field.
- Mapping quyền/identity cho Clinic Staff.
- Appointment-to-Visit field mapping.
- HTTP/status code và error text.
- Performance, reliability, security, scalability, compliance và operational thresholds không có trong baseline.

Không có test nào dưới đây tự đặt giá trị mặc định hoặc kỳ vọng cho các mục trên. Luồng tạo hợp lệ luôn nhập duration tường minh; luồng hoàn tất chỉ kiểm tra số lượng Visit.

## Entry Criteria

- Ba nguồn baseline vẫn là bản được duyệt và contract kỹ thuật cho Appointment sẵn sàng ở mức cần thiết để gọi/quan sát feature.
- Môi trường test có persistence và có thể đọc Appointment/Visit cuối cùng; dữ liệu test có Pet và Veterinarian hợp lệ.
- Có clock control theo `Asia/Ho_Chi_Minh` và giá trị duration dương được Product/BA chấp thuận cho ca thành công. Ca biên maximum chỉ bắt đầu khi giới hạn/độ phân giải input được quyết định.
- Có identity đã được xác nhận là Clinic Staff cho ca dương; không suy ra từ role của hệ thống PetClinic hiện tại.
- Môi trường có thể chạy request đồng thời và phân lập record của từng ca. Cơ chế kỹ thuật dùng để đạt điều đó do engineering chọn.
- Visit có thể đếm trước/sau luồng hoàn tất mà không đưa ra assertion về Appointment-to-Visit field mapping.

## Exit Criteria cho giai đoạn kiểm thử sau này

- Tất cả FR-001–FR-006 và BR-001–BR-014 có trace tới kịch bản; các ca UNKNOWN được ghi là blocked/deferred, không tính là đã pass.
- P0 đạt 100%; P1 đạt ít nhất 95% hoặc các lỗi còn lại được triage theo quy trình nhóm.
- Evidence cho mitigation của các rủi ro cao được thu thập; kết quả concurrency và cardinality được quan sát ở persistence boundary.
- Quyết định còn mở được theo dõi với owner trước khi mở rộng assertion tương ứng. Các tiêu chí này là kế hoạch tương lai, không phải release verdict hiện tại.

## Test Coverage Plan

**P0/P1/P2/P3 là mức ưu tiên, không phải lịch chạy.** P0 chỉ dùng cho hai invariant dữ liệu có thể để lại record sai và không có recovery behavior nào được baseline nêu. Các flow chính còn lại là P1 vì baseline không cung cấp đủ bằng chứng để tự gán mức tác động/khả năng khôi phục nghiêm trọng hơn. Test level ưu tiên API/persistence cho logic và dữ liệu; E2E chỉ cho luồng người dùng chính.

### P0 — Critical

**Tiêu chí:** lỗi gây vi phạm cardinality hoặc dữ liệu đặt lịch đã lưu, không có cách khôi phục được baseline xác định.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|
| TD-28 | Hoàn tất một Appointment đang Scheduled. | API / persistence integration | R-003, R-006 | FR-005; BR-002, BR-008, BR-010 | Appointment chuyển `Completed`; tổng Visit tăng chính xác một. Không assertion field mapping. |
| TD-33 | Hai request đồng thời tạo lịch chồng lấn cho cùng Veterinarian. | API / persistence integration | R-001 | FR-002; BR-006, BR-013 | Sau commit chỉ một Appointment xung đột được lưu; không giả định request nào thắng hoặc response/error text. |

### P1 — High

**Tiêu chí:** hành vi chính/alternates/lifecycle có ảnh hưởng đáng kể tới người dùng; có thể ưu tiên sau hai invariant P0.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|
| TD-01 | Clinic Staff tạo Appointment với Pet, Veterinarian, thời điểm tương lai, duration dương được duyệt và reason được nhập tường minh. | E2E | R-003, R-005 | FR-001; BR-001–003, BR-008 | Một Appointment lưu/hiển thị ở `Scheduled` với các giá trị nhập; thao tác đặt lịch không tự tạo Visit. Identity phải được xác nhận là Clinic Staff; không suy ra field nào bắt buộc. |
| TD-02 | Tạo Appointment có thời điểm bắt đầu trước hiện tại. | API | R-002 | FR-001; BR-004 | Không có Appointment mới được lưu. |
| TD-03 | Tạo Appointment có thời điểm bắt đầu đúng bằng hiện tại của đồng hồ kiểm thử. | API | R-002 | FR-001; BR-004 | Không có Appointment mới được lưu; phép so sánh là nghiêm ngặt (`>`). |
| TD-04 | Tạo Appointment có thời điểm bắt đầu sau hiện tại; kiểm tra cùng instant qua cách biểu diễn thời gian khác nhau. | API | R-002 | FR-001; BR-004 | Thời điểm tương lai được chấp nhận theo `Asia/Ho_Chi_Minh`; không cố định cách lưu/hiển thị hay offset kỹ thuật. |
| TD-05 | Tạo Appointment với duration bằng 0. | API | R-004 | FR-001; BR-005 | Appointment không được lưu. |
| TD-06 | Tạo Appointment với duration âm. | API | R-004 | FR-001; BR-005 | Appointment không được lưu. |
| TD-07 | Tạo với duration dương, tường minh, nằm trong khoảng được Product/BA xác nhận hợp lệ. | API | R-004 | FR-001; BR-003, BR-005 | Appointment được tạo ở `Scheduled`; không dựa vào default duration. Block nếu chưa chọn được giá trị dương hợp lệ. |
| TD-08 | Lịch Scheduled mới chồng lấn lịch Scheduled khác của cùng Veterinarian; dùng Pet khác. | API / persistence integration | R-001 | FR-002; BR-006 | Lịch mới không được lưu; record cũ giữ nguyên. |
| TD-09 | Lịch mới bắt đầu đúng lúc lịch cùng Veterinarian kết thúc. | API | R-001 | FR-002; BR-006 | Cả hai Appointment được lưu vì khoảng là nửa mở `[start, end)`. |
| TD-10 | Lịch mới kết thúc đúng lúc lịch cùng Veterinarian bắt đầu. | API | R-001 | FR-002; BR-006 | Cả hai Appointment được lưu ở ranh giới tiếp giáp ngược chiều. |
| TD-11 | Hai lịch cùng Veterinarian nhưng không chồng lấn. | API | R-001 | FR-002; BR-006 | Cả hai Appointment được lưu. |
| TD-12 | Hai lịch chồng lấn nhưng khác Veterinarian. | API | R-001 | FR-002; BR-006 | Cả hai Appointment được lưu. |
| TD-13 | Cùng Pet có lịch chồng lấn với hai Veterinarian khác nhau. | API | - | BR-012 | Cả hai Appointment được lưu; không thêm kiểm tra xung đột theo Pet. |
| TD-14 | Hủy Appointment Scheduled, rồi đặt lịch cho cùng Veterinarian/time. | API / persistence integration | - | FR-004; BR-008, BR-009, BR-011 | Appointment cũ còn truy vấn được ở `Cancelled`; lịch mới ở cùng slot được lưu. |
| TD-15 | Dùng slot của Appointment đã Completed để tạo lịch Scheduled mới cùng Veterinarian. | API | R-003 | FR-002, FR-005; BR-006, BR-008, BR-010 | Lịch mới được lưu; chỉ Scheduled được tính khi kiểm tra xung đột. |
| TD-16 | Sửa các giá trị hợp lệ đã nhập của Appointment Scheduled. | API | - | FR-003; BR-007, BR-008 | Giá trị sửa được lưu, status vẫn `Scheduled`, không tạo Visit. Không thử bỏ trống field để suy ra requiredness. |
| TD-17 | Đổi lịch Appointment Scheduled sang slot rảnh, rồi dùng lại slot cũ. | API / persistence integration | R-001 | FR-003; BR-006–008 | Đổi lịch không tự xung đột với chính Appointment; status vẫn Scheduled và slot cũ dùng được. |
| TD-18 | Đổi lịch Appointment Scheduled sang slot đang bị Appointment Scheduled cùng Veterinarian chiếm. | API / persistence integration | R-001 | FR-003; BR-006–008 | Đổi lịch không được áp dụng; thời gian, dữ liệu và status ban đầu giữ nguyên. |
| TD-19 | Thử sửa Appointment Cancelled. | API | - | FR-003; BR-008 | Dữ liệu và status không đổi. |
| TD-20 | Thử đổi lịch Appointment Cancelled. | API | - | FR-003; BR-008 | Dữ liệu và status không đổi. |
| TD-21 | Thử hủy lại Appointment Cancelled. | API | - | FR-004; BR-008 | Dữ liệu và status không đổi. |
| TD-22 | Thử hoàn tất Appointment Cancelled. | API | R-003 | FR-005; BR-008, BR-010 | Không đổi status/dữ liệu và không tạo Visit. |
| TD-23 | Thử sửa Appointment Completed. | API | R-003 | FR-003; BR-008 | Appointment vẫn Completed; không đổi dữ liệu. |
| TD-24 | Thử đổi lịch Appointment Completed. | API | R-003 | FR-003; BR-008 | Appointment vẫn Completed; không đổi dữ liệu. |
| TD-25 | Thử hủy Appointment Completed. | API | R-003 | FR-004; BR-008 | Appointment vẫn Completed; không đổi dữ liệu. |
| TD-26 | Thử hoàn tất Appointment Completed lần nữa. | API | R-003 | FR-005; BR-008, BR-010 | Không phát sinh Visit thứ hai; status và dữ liệu giữ nguyên. |
| TD-27 | Xác minh invariant không hard-delete với các lifecycle operation được hỗ trợ; nếu có thao tác delete-like thì kiểm tra không xóa vật lý. | API / persistence integration | - | FR-004; BR-011 | Appointment vẫn truy vấn được sau hủy; không record Appointment nào bị xóa vật lý. Không quy định route/command/response. |
| TD-29 | Gửi hoàn tất lại sau lần hoàn tất thành công. | API | R-003 | FR-005; BR-008, BR-010 | Appointment vẫn Completed; số Visit không tăng lần nữa. |
| TD-30 | Gửi hai thao tác hoàn tất đồng thời trên cùng Appointment Scheduled. | API / persistence integration | R-003 | FR-005; BR-008, BR-010 | Trạng thái cuối Completed và chỉ có đúng một Visit mới. |
| TD-31 | Clinic Staff xem Appointment bằng khả năng đọc cơ bản đã triển khai. | E2E | R-005, R-007 | FR-006; BR-001, BR-014 | Có thể xem record/giá trị được duyệt; không assertion về filter, order, default sorting, pagination hay page size. |
| TD-32 | Xem Appointment đã Cancelled và Completed bằng khả năng đọc cơ bản. | E2E | R-005, R-007 | FR-006; BR-001, BR-008, BR-011, BR-014 | Trạng thái lưu được nhìn thấy và record vẫn truy cập được; không giả định filter, sorting, pagination hoặc page size. |
| TD-34 | Tạo đồng thời hai lịch không chồng lấn cho cùng Veterinarian. | API / persistence integration | R-001 | FR-002; BR-013 | Cả hai Appointment không xung đột đều được lưu. |

### P2 — Medium

**Tiêu chí:** ca biên của hành vi phụ thuộc quyết định còn mở; chưa được tính là runnable.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|
| TD-35 | Biên duration tối đa sau khi BA xác nhận maximum và độ phân giải input. | API | R-004 | FR-001; BR-005 | Chưa chọn giá trị hay expected boundary. Sau quyết định mới kiểm tra đúng maximum và giá trị biểu diễn kế tiếp vượt maximum. Hiện trạng: blocked. |

### P3 — Low

Không có hành vi thuộc phạm vi được phân loại P3.

## Execution Strategy

- **PR:** chạy toàn bộ ca functional P0/P1 nếu suite xác định được và dưới 15 phút. Có thể xếp smoke/API readiness trước, sau đó P0 rồi P1; mức ưu tiên không phải lịch chạy. Giữ hai invariant P0 trong tập kiểm chứng quan trọng.
- **Nightly:** chỉ chuyển lặp concurrency/persistence hoặc hồi quy dài hơn nếu môi trường khiến PR suite quá tốn thời gian hoặc không ổn định.
- **Weekly:** chưa xếp load/stress/chaos; cần workload và ngưỡng được duyệt trước. Playwright config hiện có dùng Chromium, nhưng chưa có E2E spec trong lượt quét và chưa có runtime timing evidence.
- Không có suite/test nào được chạy trong workflow này.

## Ước lượng nguồn lực

Ước lượng theo khoảng cho test preparation và validation sau khi implementation/contract sẵn sàng; gồm setup data/clock/concurrency, chưa tạo automation trong workflow này.

| Ưu tiên | Khối lượng dự kiến | Ghi chú |
|---|---|---|
| P0 | ~8–16 giờ | Hai ca cardinality/data-integrity trọng yếu và môi trường persistence. |
| P1 | ~28–45 giờ | Boundary, lifecycle, conflict, alternate và view. |
| P2 | ~2–6 giờ | Chỉ sau khi maximum/precision được quyết định. |
| P3 | ~2–5 giờ | Không có scenario hiện tại; dự phòng exploratory nếu scope được mở rộng. |
| **Tổng** | **~45–75 giờ; khoảng 1.5–3 tuần** | Khoảng gồm setup chung và độ bất định kỹ thuật; cần điều chỉnh sau khi contract/fixtures rõ. |

## Quality Criteria cho lần kiểm thử sau

Đây là tiêu chí kế hoạch, không phải kết quả gate:

- Trace coverage: 100% FR-001–FR-006 và BR-001–BR-014 được map tới scenario; ca UNKNOWN mang trạng thái blocked/deferred.
- P0 pass rate 100%; P1 pass rate ≥95% hoặc lỗi còn lại được triage.
- Mitigation cho rủi ro ≥6 cần evidence kiểm chứng trước quyết định release của nhóm.
- Mục tiêu requirement coverage là 100% cho baseline được duyệt. Không đặt ngưỡng code coverage cho Epic trước khi module/denominator tồn tại; threshold ≥80% generic chỉ có thể cân nhắc sau implementation.
- NFR evidence được nhận diện ở phần NFR Planning; đánh giá NFR cuối cùng để dành cho `nfr-assess` khi có evidence.

## Test Data, Tooling và Dependencies

**Test data:** Pet và Veterinarian hợp lệ; giá trị Appointment đầy đủ để thử luồng thành công nhưng không suy ra requiredness; positive duration được BA xác nhận; các lịch cùng/khác Veterinarian; trạng thái Cancelled/Completed đạt qua lifecycle; đồng hồ kiểm soát được; record cách ly để đếm Visit.

**Tooling/access hiện có làm tham chiếu:** Spring/JUnit/MockMvc ở REST và Angular component/service specs; Playwright config Chromium cho E2E. Chỉ dùng bộ khung phù hợp sau khi contract và quyền Clinic Staff được xác định. Không cài thêm tool, tạo test code hay yêu cầu quyền truy cập mới trong tài liệu này.

**Dependencies:** Appointment API/schema và persistence boundary; Clinic Staff test identity; đồng hồ test theo timezone; cách đọc Visit count; khả năng đồng bộ hai request trong môi trường tích hợp. Các dependency này không quyết định nghiệp vụ UNKNOWN.

## Interworking & Regression

| Thành phần hiện có | Tác động có thể kiểm chứng | Phạm vi hồi quy |
|---|---|---|
| Spring PetClinic REST — Visit model/API/controller | FR-005 yêu cầu tạo một Visit khi hoàn tất Appointment. | Hồi quy đọc/tạo Visit hiện có và kiểm tra đúng delta số lượng; không suy ra Appointment-to-Visit mapping. |
| Angular — Visit service/form/list specs | Luồng Appointment có thể liên tác với trải nghiệm xem Visit hiện tại sau completion. | Giữ Visit list/add/edit hiện có hoạt động theo contract hiện tại; không mượn Visit role mapping làm quyền Clinic Staff. |
| Angular Playwright config | Có cấu hình Chromium E2E cho `e2e/*.e2e-spec.ts`. | Dùng cho luồng người dùng chính sau khi UI/test identity sẵn sàng; chưa có spec khớp và chưa chạy test. |

## Assumptions, Clarifications và Residual Dependencies

1. Các ca dương dùng Pet/Veterinarian tồn tại và dữ liệu được chấp nhận theo contract triển khai; nguồn không quy định behavior cho reference không tồn tại.
2. Luồng hợp lệ nhập tường minh tất cả giá trị cần dùng trong ca; việc đó không khẳng định mọi field là required.
3. Với thao tác bị cấm, observable là không đổi dữ liệu/trạng thái và không phát sinh Visit. HTTP response/status và nội dung lỗi vẫn UNKNOWN.
4. BA/Product cần quyết định maximum duration, list filters/sorting/pagination/page size, default duration và requiredness trước assertion tương ứng.
5. BA/Engineering cần chốt Clinic Staff identity/permission mapping; BA/Architecture cần chốt Visit field mapping nếu muốn kiểm tra nội dung Visit.
6. Nếu workload hoặc NFR được bổ sung, cần cập nhật phạm vi, threshold và evidence trước khi thiết kế performance/security/compliance assessment tương ứng.

## Traceability Matrix

| Requirement | Kịch bản |
|---|---|
| FR-001 | TD-01–TD-07, TD-35 |
| FR-002 | TD-08–TD-15, TD-33–TD-34 |
| FR-003 | TD-16–TD-20, TD-23–TD-24 |
| FR-004 | TD-14, TD-21, TD-25, TD-27 |
| FR-005 | TD-15, TD-22–TD-23, TD-26, TD-28–TD-30 |
| FR-006 | TD-01, TD-31–TD-32 |
| BR-001 | TD-01, TD-31–TD-32 |
| BR-002 | TD-01, TD-28 |
| BR-003 | TD-01, TD-07 |
| BR-004 | TD-02–TD-04 |
| BR-005 | TD-05–TD-07, TD-35 |
| BR-006 | TD-08–TD-12, TD-15, TD-17–TD-18, TD-33–TD-34 |
| BR-007 | TD-16–TD-18 |
| BR-008 | TD-01, TD-14–TD-32 |
| BR-009 | TD-14 |
| BR-010 | TD-15, TD-22–TD-23, TD-26, TD-28–TD-30 |
| BR-011 | TD-14, TD-19–TD-27, TD-32 |
| BR-012 | TD-13 |
| BR-013 | TD-33–TD-34 |
| BR-014 | TD-31–TD-32 |

## Follow-on Workflow

Các workflow tạo test/automation hoặc đánh giá NFR là công việc riêng, không được chạy trong phạm vi này. Review rủi ro và các UNKNOWN với BA/Engineering trước khi biến kế hoạch thành test implementation.

## Approval

**Trạng thái phê duyệt Test Design:** Draft — chưa có người duyệt được nêu trong nguồn.  
**Ghi chú:** Không phải release verdict.

---

**Generated by:** BMad TEA Agent — Test Architect Module  
**Workflow:** `bmad-testarch-test-design`  
**Workflow version:** 5.0 step-file architecture / output template 4.0
