# Test Design: Epic 1 — CR-001 Appointment Scheduling

**Ngày:** 2026-09-25  
**Tác giả:** Master Test Architect  
**Trạng thái:** Bản nháp  
**Phạm vi:** Test Design cấp Epic cho các yêu cầu FR-001–FR-006.

## Tóm tắt

Kế hoạch này lập coverage cho việc tạo, kiểm tra xung đột, chỉnh sửa/đổi lịch, hủy, hoàn tất và xem Appointment. FR được chép nguyên văn từ structural epic wrapper; Business Rules được giữ thành context riêng, không nhập vào acceptance criteria. Các UNKNOWN được giữ nguyên.

Ba rủi ro có điểm P×I bằng 6: kiểm tra xung đột, tính toàn vẹn vòng đời/Visit và đặt lịch đồng thời. Điểm số, mức ưu tiên, test level, counts, effort và thresholds là khuyến nghị lập kế hoạch của TEA; chúng không phải kết luận phát hành.

Không có Appointment implementation hoặc Appointment-named test trong CURRENT_SYSTEM/SUPPLEMENTAL. Do đó, test levels dưới đây mô tả cách xác minh kết quả nghiệp vụ ở mức khái niệm; không chỉ định route, API, UI, response, schema, locking hay transaction.

## Nguồn và ranh giới thẩm quyền

- **FR/acceptance criteria:** `inputs/adapter/epic-1.md`. Đây là wrapper cấu trúc; FR ID và wording được giữ nguyên.
- **Business Rules:** `inputs/adapter/business-rules.md`. Các BR dưới đây là context riêng, không sửa hoặc mở rộng câu chữ FR.
- **Open decisions:** `inputs/adapter/open-decisions.md`; giữ nguyên, không trả lời.
- **CURRENT_SYSTEM/SUPPLEMENTAL:** `inputs/adapter/current-system-supplemental.md`; dùng duy nhất làm stack/existing-test context. Nó không cung cấp yêu cầu Appointment hay UI/API contract.
- **Scope:** chỉ Epic 1. Baseline/legacy Visit coverage được đề cập trong regression context; không dùng để suy ra mapping Visit cho Appointment.

## FR — Acceptance criteria nguyên văn

### FR-001

Clinic Staff có thể tạo Appointment với Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải. Appointment hợp lệ bắt đầu ở trạng thái Scheduled. Thời điểm bắt đầu phải sau hiện tại theo Asia/Ho_Chi_Minh; thời lượng phải lớn hơn 0.

### FR-002

Appointment Scheduled không được chồng lấn Appointment Scheduled khác của cùng Veterinarian. Dùng khoảng [start, end); cho phép lịch chạm nhau.

### FR-003

Clinic Staff chỉ được chỉnh sửa hoặc đổi lịch Appointment khi trạng thái là Scheduled. Khi đổi lịch, kiểm tra xung đột loại chính Appointment đang đổi khỏi đối chiếu.

### FR-004

Clinic Staff chỉ được hủy Appointment khi trạng thái là Scheduled. Hủy giải phóng khung giờ; không xóa cứng Appointment.

### FR-005

Clinic Staff chỉ được hoàn tất Appointment khi trạng thái là Scheduled. Hoàn tất tạo chính xác một Visit mới và chuyển Appointment sang Completed.

### FR-006

Clinic Staff có thể xem Appointment. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định.

## BR — Business Rules context riêng

### BR-001

Clinic Staff có thể quản lý Appointment.

### BR-002

Appointment là khái niệm riêng với Visit.

### BR-003

Appointment có Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải.

### BR-004

Thời điểm bắt đầu phải sau hiện tại, tính theo Asia/Ho_Chi_Minh.

### BR-005

Thời lượng phải lớn hơn 0. Thời lượng tối đa là UNKNOWN.

### BR-006

Chỉ Appointment Scheduled của cùng Veterinarian mới được đối chiếu xung đột. Dùng khoảng nửa mở [start, end), nên lịch chạm nhau được phép.

### BR-007

Chỉ được đổi lịch khi Appointment ở Scheduled và loại chính Appointment đó khỏi kiểm tra xung đột.

### BR-008

Vòng đời gồm Scheduled, Cancelled, Completed. Khi tạo là Scheduled; chỉ Scheduled mới được chỉnh sửa, đổi lịch, hủy hoặc hoàn tất.

### BR-009

Hủy lịch giải phóng khung giờ.

### BR-010

Hoàn tất tạo chính xác một Visit mới.

### BR-011

Không xóa cứng Appointment.

### BR-012

Baseline được duyệt không cấm lịch Appointment của cùng Pet chồng lấn.

### BR-013

Kết quả nghiệp vụ khi đặt đồng thời là chỉ lưu Appointment không xung đột.

### BR-014

Cần xem Appointment. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN.

## Open decisions — giữ nguyên UNKNOWN

- Thời lượng tối đa vẫn UNKNOWN; không tự đặt giới hạn
- Bộ lọc, sắp xếp và phân trang danh sách vẫn UNKNOWN

**Điều khoản nguồn:**

- FR-006: Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định.
- BR-005: Thời lượng tối đa là UNKNOWN.
- BR-014: Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN.

Không có scenario nào kiểm tra ngưỡng tối đa hoặc hành vi filter/sort/paging cho đến khi BA chốt.

## Đánh giá khả năng kiểm thử

| FR | Khả năng kiểm chứng từ wording đã duyệt | Điều kiện / giới hạn quan sát |
|---|---|---|
| FR-001 | Trường Pet, Veterinarian, thời điểm, duration, lý do; trạng thái Scheduled; thời điểm tương lai theo timezone và duration dương đều có expected business outcome. | Cần tạo dữ liệu domain và quan sát state/result. Clock control và đường quan sát chưa được quy định. Max duration vẫn UNKNOWN. |
| FR-002 | Có thể phân biệt đúng veterinarian, Scheduled status và khoảng [start,end); gồm overlap và lịch chạm nhau. | Cần quan sát Appointment nào được lưu/giữ. Không có quy định về error message hay response. |
| FR-003 | Điều kiện trạng thái Scheduled và loại chính Appointment khỏi phép so xung đột khi đổi lịch được nêu rõ. | Cần kiểm soát trạng thái và lịch xung quanh; quan sát Appointment sau cập nhật và không phát sinh record thừa. |
| FR-004 | Hủy chỉ từ Scheduled, khung giờ được giải phóng và Appointment không bị xóa cứng. | Cần quan sát trạng thái còn tồn tại và thử dùng lại slot; cách đọc trạng thái chưa quy định. |
| FR-005 | Hoàn tất từ Scheduled phải chuyển sang Completed và tạo chính xác một Visit. | Có thể quan sát trạng thái và số Visit mới. Wording không xác định field mapping giữa Appointment và Visit. |
| FR-006 | Khả năng Clinic Staff xem Appointment là testable ở mức capability. | Bộ lọc, sắp xếp, phân trang vẫn UNKNOWN; không có expected result cho các thao tác đó. |

### Khả năng điều khiển, quan sát và độ tin cậy

- **Controllability:** test setup cần tạo Pet/Veterinarian, Appointment ở các trạng thái đã nêu, đặt thời điểm theo Asia/Ho_Chi_Minh và kích hoạt hai booking đồng thời. Cách seed/control cụ thể chưa được chọn.
- **Observability:** oracle là kết quả nghiệp vụ: Appointment có/không được lưu, trạng thái còn tồn tại, slot có thể tái sử dụng, và số Visit mới. Không giả định UI/API, route, response code/message hoặc schema.
- **Reliability:** kiểm thử cần data isolation, nguồn thời gian kiểm soát được và khả năng lặp lại kịch bản đồng thời. Cơ chế kỹ thuật để đạt điều đó là quyết định triển khai.
- **Coverage gap:** max duration, filter/sort/paging, Visit field mapping và hành vi ngoài vai trò Clinic Staff chưa được quy định; không thêm assertions cho chúng.

## Đánh giá rủi ro

Thang điểm: Probability 1 = unlikely, 2 = possible, 3 = likely; Impact 1 = minor, 2 = degraded, 3 = critical. Score = P×I. Rủi ro từ 6 trở lên được đánh dấu high để ưu tiên mitigation; điểm này không tự quyết định P0–P3 hoặc release.

| Risk ID | Category | Mô tả có truy vết | Probability | Impact | Score | Mitigation | Owner đề xuất / thời điểm |
|---|---|---|---:|---:|---:|---|---|
| R-001 | BUS | FR-002 và BR-006 giới hạn xung đột theo Appointment Scheduled cùng Veterinarian và khoảng [start,end). Sai điều kiện có thể lưu hai lịch xung đột hoặc chặn lịch chạm nhau. | 2 | 3 | 6 | Bao phủ overlap từng phần/bao hàm, cùng thời điểm bắt đầu, lịch liền kề, veterinarian khác và trạng thái không Scheduled. | Dev + QA; trước nghiệm thu logic lịch |
| R-002 | DATA | FR-004/FR-005 và BR-008–BR-011 quy định chuyển trạng thái, hủy không xóa cứng, giải phóng slot và tạo một Visit. Sai vòng đời có thể làm mất Appointment, giữ slot sai hoặc lệch số Visit. | 2 | 3 | 6 | Ma trận trạng thái; xác minh record sau hủy, tái sử dụng slot, và exactly-one Visit khi hoàn tất. | Dev + QA; trước nghiệm thu vòng đời |
| R-003 | DATA | BR-013 quy định khi đặt đồng thời chỉ lưu Appointment không xung đột. Nếu kết quả nghiệp vụ này không được giữ, lịch Scheduled xung đột có thể cùng được lưu. | 2 | 3 | 6 | Một scenario đồng thời; xác minh đúng một lịch xung đột được lưu mà không chỉ định locking/transaction. | Dev + QA; trước nghiệm thu booking đồng thời |
| R-004 | BUS | FR-001/BR-004/BR-005 quy định thời điểm sau hiện tại theo Asia/Ho_Chi_Minh và duration > 0. Sai biên có thể tạo Appointment ngoài điều kiện đã duyệt. | 2 | 2 | 4 | Kiểm tra mốc now/past/future và duration <= 0; chỉ khẳng định lower bound đã duyệt. | Dev + QA; trước nghiệm thu tạo lịch |
| R-005 | BUS | BR-005 ghi max duration UNKNOWN. Việc tự thêm một giới hạn vào validation hoặc test oracle sẽ biến giả định thành hành vi không được BA duyệt. | 2 | 2 | 4 | Giữ UNKNOWN; không test upper boundary đến khi BA quyết định. | BA + QA; trước khi chốt criteria duration |
| R-006 | BUS | FR-006/BR-014 ghi filter/sort/paging UNKNOWN. Nếu tự đặt thứ tự hoặc semantics danh sách, expected result sẽ không có authority. | 2 | 2 | 4 | Chỉ kiểm chứng capability xem Appointment; chờ BA xác định các thao tác danh sách. | BA + QA; trước khi chốt criteria danh sách |

R-001, R-002 và R-003 có score 6 theo thang TEA. Owners ở trên là vai trò đề xuất, không phải phân công đã được xác nhận. Timeline là mốc tương đối do đầu vào không có ngày delivery.

### Kế hoạch NFR

Các yêu cầu epic/BR được cung cấp không nêu NFR về security, performance, reliability, scalability, maintainability hoặc compliance; cũng không có thresholds hay evidence source được yêu cầu. Không thêm NFR risk hoặc kế hoạch perf/security test dựa trên suy đoán. Nếu NFR được bổ sung, cần lập coverage và evidence plan ở lần cập nhật Test Design sau. Không đánh giá PASS/CONCERNS/FAIL.

## Test Coverage Plan

**P0/P1/P2/P3 là mức ưu tiên, không phải thời điểm chạy.** Phân mức dưới đây là gợi ý TEA. Không có bằng chứng trong đầu vào về workaround an toàn, user reach, tần suất hoặc impact phát hành để gán P0; các scenario được xếp P1 tạm thời vì đây là các hành vi cốt lõi được Epic chấp nhận. Test ID theo quy ước native `{EPIC}.{STORY}-{LEVEL}-{SEQ}`; `1.0` biểu thị scope cấp Epic do chưa có Story ID. E2E chỉ nói đến kết quả nghiệp vụ xuyên suốt và trạng thái được quan sát; không chỉ định UI/API.

### P0

**Tiêu chí:** Tác động critical đã xác định, không có workaround an toàn.  
**Mục đích:** Ưu tiên kiểm tra trước khi mở rộng coverage.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|

Không có scenario được gán P0 do đầu vào không xác định “không có workaround an toàn”.

### P1

**Tiêu chí:** Hành vi cốt lõi của Epic; mức ưu tiên tạm thời theo TEA.  
**Mục đích:** Bao phủ các kết quả đã được quy định cho vòng đời Appointment.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|
| 1.0-UNIT-001 | Kiểm tra thời điểm bắt đầu tại/quá khứ/tương lai theo Asia/Ho_Chi_Minh | Unit | R-004 | FR-001; BR-004 | Thời điểm bằng hoặc trước hiện tại không tạo Appointment hợp lệ; thời điểm sau hiện tại thỏa điều kiện thời gian. Không khẳng định nội dung lỗi hoặc response. |
| 1.0-UNIT-002 | Kiểm tra duration dương và không dương | Unit | R-004, R-005 | FR-001; BR-005 | Duration > 0 thỏa lower bound; duration = 0 hoặc < 0 không tạo Appointment hợp lệ. Không kiểm tra upper bound vì UNKNOWN. |
| 1.0-E2E-001 | Tạo Appointment hợp lệ với Pet, Veterinarian, thời điểm, duration và lý do/diễn giải | E2E | R-004 | FR-001; BR-001, BR-003, BR-004, BR-005, BR-008 | Có đúng Appointment được tạo với các giá trị đã nhập và trạng thái Scheduled. |
| 1.0-E2E-002 | Tạo Appointment Scheduled chồng lấn Appointment Scheduled cùng Veterinarian | E2E | R-001 | FR-002; BR-006 | Appointment xung đột thứ hai không được lưu thành Scheduled; không tồn tại cặp lịch Scheduled chồng lấn của cùng Veterinarian. |
| 1.0-E2E-003 | Tạo hai Appointment cùng Veterinarian với khoảng chạm nhau | E2E | R-001 | FR-002; BR-006 | Cả hai Appointment được lưu Scheduled vì khoảng [start, end) cho phép điểm cuối lịch trước bằng thời điểm bắt đầu lịch sau. |
| 1.0-E2E-004 | Lịch cũ Cancelled hoặc Completed không chặn Appointment Scheduled mới cùng slot | E2E | R-001, R-002 | FR-002, FR-004, FR-005; BR-006, BR-008, BR-009 | Appointment mới được lưu Scheduled; Appointment cũ vẫn giữ trạng thái Cancelled hoặc Completed tương ứng. |
| 1.0-E2E-005 | Hai booking đồng thời xung đột cho cùng Veterinarian | E2E | R-003 | FR-002; BR-006, BR-013 | Chỉ một Appointment không xung đột được lưu; không có hai Appointment Scheduled chồng lấn. Không giả định booking nào thắng hoặc cơ chế xử lý. |
| 1.0-E2E-006 | Clinic Staff chỉnh sửa Appointment đang Scheduled | E2E | R-002 | FR-003; BR-008 | Thao tác chỉnh sửa được áp dụng cho Appointment đang Scheduled và trạng thái vẫn là Scheduled. Không giả định tập field hoặc giao diện chỉnh sửa. |
| 1.0-E2E-007 | Đổi lịch Appointment Scheduled; không tự xung đột với chính nó | E2E | R-001, R-002 | FR-003; BR-007, BR-008 | Thời điểm của Appointment được đổi sang slot đích dù slot mới giao với slot cũ của chính nó; chỉ còn một Appointment đích và trạng thái Scheduled. |
| 1.0-E2E-008 | Đổi lịch Appointment Scheduled vào slot có Appointment Scheduled khác cùng Veterinarian | E2E | R-001 | FR-002, FR-003; BR-006, BR-007, BR-008 | Đổi lịch xung đột không được áp dụng; Appointment đang đổi và Appointment hiện có không tạo thành cặp Scheduled chồng lấn. |
| 1.0-E2E-009 | Thử edit, reschedule, cancel, complete trên Appointment Cancelled hoặc Completed | E2E | R-002 | FR-003, FR-004, FR-005; BR-008, BR-010 | Appointment giữ nguyên trạng thái terminal; không đổi lịch, không bị xóa và không phát sinh Visit mới từ thao tác complete không hợp lệ. |
| 1.0-E2E-010 | Hủy Appointment Scheduled rồi dùng lại slot | E2E | R-002 | FR-004; BR-008, BR-009, BR-011 | Appointment ban đầu còn tồn tại với trạng thái Cancelled; slot được một Appointment Scheduled khác sử dụng được. |
| 1.0-E2E-011 | Hoàn tất Appointment Scheduled, sau đó thử hoàn tất lần nữa | E2E | R-002 | FR-005; BR-002, BR-008, BR-010 | Lần hoàn tất hợp lệ chuyển Appointment sang Completed và tạo đúng một Visit mới; lần thử lại không tạo Visit thứ hai. Không assert mapping field. |
| 1.0-E2E-012 | Cùng Pet có lịch chồng lấn với Veterinarian khác | E2E | R-001 | FR-002; BR-006, BR-012 | Appointment được lưu khi không vi phạm xung đột cùng Veterinarian; lịch cùng Pet không bị từ chối chỉ vì trùng thời gian. |
| 1.0-E2E-013 | Clinic Staff xem Appointment | E2E | R-006 | FR-006; BR-001, BR-014 | Appointment có thể được Clinic Staff xem/quan sát. Không assert filter, sort, paging hoặc thứ tự danh sách. |

### P2

**Tiêu chí:** Hành vi phụ, phạm vi hẹp hơn và có workaround chấp nhận được.  
**Mục đích:** Bổ sung hành vi ít ưu tiên khi có cơ sở đánh giá impact/workaround.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|

Không có scenario P2 riêng; đầu vào không đưa dữ liệu về usage hoặc workaround để tách một acceptance criterion cốt lõi khỏi nhóm P1.

### P3

**Tiêu chí:** Hiếm, cosmetic hoặc thử nghiệm, impact tối thiểu.  
**Mục đích:** Chỉ đưa vào nếu có requirement hỗ trợ.

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
|---|---|---|---|---|---|

Không có requirement hiếm/cosmetic/experimental trong phạm vi Epic 1.

## Chiến lược thực thi kiểm thử

Mức ưu tiên không quy định lịch chạy.

- **PR:** Chạy các functional scenario nếu bộ test hoàn chỉnh dưới 15 phút; giữ cả kiểm tra nghiệp vụ cốt lõi khi harness cho phép. Đây là mục tiêu, chưa đo.
- **Nightly:** Chuyển scenario booking đồng thời sang nightly nếu môi trường hoặc orchestration làm PR suite chậm/không ổn định.
- **Weekly:** Chưa có performance, chaos hoặc long-running scenario vì không có NFR/threshold hoặc yêu cầu tương ứng.

## Ước tính nguồn lực

Ước tính sơ bộ, gồm chuẩn bị dữ liệu và harness; chưa có implementation/test setup nên chỉ dùng để lập kế hoạch ban đầu.

| Priority | Số scenario | Effort range |
|---|---:|---:|
| P0 | 0 | 0 giờ |
| P1 | 15 | ~18–36 giờ |
| P2 | 0 | 0 giờ |
| P3 | 0 | 0 giờ |
| **Tổng** | **15** | **~18–36 giờ (~1–2 tuần)** |

## Tiêu chí cổng chất lượng — chỉ tham khảo

Các ngưỡng sau là mặc định TEA để thảo luận, chưa được project phê duyệt và không tạo release verdict:

- P0 pass rate: 100% nếu sau này có scenario P0.
- P1 pass rate: ≥95%.
- Mục tiêu traceability: tất cả FR/BR đã xác định có ít nhất một scenario; UNKNOWN không tính là expected behavior đã kiểm thử.
- Rủi ro score ≥6 cần có mitigation hoặc quyết định chấp nhận được ghi nhận nếu team dùng risk gate.
- Không có kết quả chạy test trong Test Design này.

## Ngoài phạm vi

| Hạng mục | Lý do | Cách giữ rủi ro trong tầm kiểm soát |
|---|---|---|
| Max duration validation | BR-005 giữ UNKNOWN. | Không tạo upper-bound scenario; chờ BA quyết định. |
| Filter, sort, paging | FR-006/BR-014 giữ UNKNOWN. | Chỉ test capability xem Appointment; chờ BA quyết định. |
| UI/API routes, fields, response codes/messages | Không có contract hoặc implementation Appointment trong đầu vào. | Chỉ dùng outcome nghiệp vụ đã duyệt; chọn điểm quan sát sau design. |
| Visit field mapping | FR-005/BR-002 chỉ nêu Visit riêng và tạo đúng một Visit; supplemental không định nghĩa mapping. | Chỉ assert state Completed và cardinality một Visit mới. |
| Authorization cho actor ngoài Clinic Staff | Không có role hoặc rule từ chối khác được nêu. | Không suy diễn negative permission tests. |
| Performance/security/compliance thresholds | Không có NFR hoặc ngưỡng trong epic/BR. | Không lập NFR suite cho tới khi có yêu cầu và evidence target. |
| Cơ chế concurrency | BR-013 quy định kết quả nghiệp vụ, không quy định locking/transaction. | Chỉ assert kết quả booking đồng thời. |

## Điều kiện bắt đầu kiểm thử

- FR, BR và UNKNOWN trong tài liệu nguồn được giữ làm oracle; mọi thay đổi business cần được BA duyệt trước khi sửa expected outcomes.
- Có test environment hoặc domain harness có thể tạo Pet, Veterinarian và Appointment ở trạng thái cần thiết.
- Có cách quan sát Appointment đã lưu, status và số Visit mới mà không phụ thuộc vào UI/API chưa được duyệt.
- Có cách kiểm soát thời điểm hiện tại theo Asia/Ho_Chi_Minh và điều phối booking đồng thời.
- Data setup/cleanup có thể cô lập giữa scenarios; chi tiết phụ thuộc implementation.

## Điều kiện kết thúc kiểm thử

- Các scenario được thực thi và kết quả quan sát được ghi theo từng Test ID trước khi một nhóm dùng chúng làm acceptance evidence.
- Mọi khác biệt với source wording được đưa về BA thay vì bổ sung expected behavior trong test.
- Rủi ro R-001–R-006, đặc biệt điểm 6, có owner/mitigation hoặc quyết định xử lý được ghi nhận.
- Max duration và list operations vẫn được đánh dấu UNKNOWN cho tới khi BA xác nhận.
- Các tiêu chí trên là hướng dẫn cho test planning; không phải kết luận release.

## Giả định và phụ thuộc

### Assumptions

1. Test IDs dùng native format `{EPIC}.{STORY}-{LEVEL}-{SEQ}`; phần `1.0` đánh dấu Epic-level vì chưa có Story ID.
2. Unit phù hợp cho predicate thời gian/duration; E2E được đề xuất cho outcome nghiệp vụ đầu-cuối. Các level là khuyến nghị và không chọn UI/API.
3. Các role ghi trong Risk Assessment là owner đề xuất; chưa có tên hoặc phân công trong nguồn.

### Dependencies

1. Cần implementation/harness để định nghĩa cách seed trạng thái, quan sát kết quả và cleanup.
2. Cần kiểm soát clock/timezone cho rule thời điểm.
3. Cần môi trường đồng thời để kiểm chứng BR-013.
4. Cần BA decision trước khi mở rộng coverage cho max duration và filter/sort/paging.

### Risks to Plan

- **Risk:** Interface/architecture được chọn có thể không cung cấp cách kiểm tra persistence hoặc kết quả đồng thời một cách cô lập.
  - **Impact:** Cần refine test level và test setup; không thay đổi business oracle.
  - **Contingency:** Cập nhật kế hoạch sau architecture/tech design, giữ BR-013 là kết quả cần chứng minh.

## Tương tác và kiểm thử hồi quy

CURRENT_SYSTEM/SUPPLEMENTAL ghi nhận test Angular hiện có cho Visit service/list và component/service; REST có service/controller tests, gồm Visit REST controller. Nếu Appointment completion tương tác với Visit, giữ các test Visit liên quan trong regression run. Các test hiện hữu không định nghĩa Appointment behavior hoặc field mapping.

## Tài liệu phương pháp tham chiếu

- `risk-governance.md` — phân loại và governance rủi ro.
- `probability-impact.md` — thang P×I 1–3.
- `test-levels-framework.md` — chọn Unit/E2E theo mục đích.
- `test-priorities-matrix.md` — hướng dẫn P0–P3.
