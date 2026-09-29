# Test Design: Epic 1 — CR-001 Appointment Scheduling

**Ngày:** 2026-09-26  
**Tác giả:** Codex benchmark  
**Trạng thái:** Bản nháp  
**Workflow:** `bmad-testarch-test-design` — pinned upstream commit `1f53e9095061ab66f3c35abd9b98baf0f50cf8fe`  
**Phạm vi:** Epic-level; thiết kế kiểm thử nghiệp vụ từ tài liệu được cung cấp. Đây là kế hoạch, không phải kết quả thực thi hay kết luận phát hành.

## Tóm tắt

Epic 1 định nghĩa tạo, kiểm tra xung đột, chỉnh sửa/đổi lịch, hủy, hoàn tất và xem Appointment. Kế hoạch ưu tiên kiểm tra xung đột lịch, đặt đồng thời, trạng thái vòng đời và tính duy nhất của Visit. Các mức ưu tiên, điểm rủi ro, cấp độ kiểm thử, effort và ngưỡng bên dưới chỉ là khuyến nghị TEA.

Tài liệu không cung cấp kiến trúc, giao diện, hợp đồng API, bằng chứng hệ thống hiện tại, hay danh mục kiểm thử hiện có. Vì vậy kế hoạch không gán hành vi UI/API, không khẳng định coverage hiện hữu và chọn cấp độ kiểm thử ở mức đề xuất.

## Nguồn và phạm vi authority

- `inputs/adapter/epic-1.md`: cấu trúc Epic và nguyên văn FR-001–FR-006 được duyệt.
- `inputs/adapter/business-rules.md`: BR-001–BR-014 riêng biệt với acceptance criteria.
- `inputs/adapter/open-decisions.md`: các câu UNKNOWN cần giữ nguyên.
- Các quyết định nghiệp vụ trong kế hoạch chỉ dựa trên nội dung SRS và Business Rules nói trên. Không suy diễn từ engineering handoff hoặc bằng chứng hệ thống không được cung cấp.

## Yêu cầu được duyệt

### Acceptance criteria — nguyên văn

#### FR-001

Clinic Staff có thể tạo Appointment với Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải. Appointment hợp lệ bắt đầu ở trạng thái Scheduled. Thời điểm bắt đầu phải sau hiện tại theo Asia/Ho_Chi_Minh; thời lượng phải lớn hơn 0.

#### FR-002

Appointment Scheduled không được chồng lấn Appointment Scheduled khác của cùng Veterinarian. Dùng khoảng [start, end); cho phép lịch chạm nhau.

#### FR-003

Clinic Staff chỉ được chỉnh sửa hoặc đổi lịch Appointment khi trạng thái là Scheduled. Khi đổi lịch, kiểm tra xung đột loại chính Appointment đang đổi khỏi đối chiếu.

#### FR-004

Clinic Staff chỉ được hủy Appointment khi trạng thái là Scheduled. Hủy giải phóng khung giờ; không xóa cứng Appointment.

#### FR-005

Clinic Staff chỉ được hoàn tất Appointment khi trạng thái là Scheduled. Hoàn tất tạo chính xác một Visit mới và chuyển Appointment sang Completed.

#### FR-006

Clinic Staff có thể xem Appointment. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định.

### Business Rules — nguyên văn

#### BR-001

Clinic Staff có thể quản lý Appointment.

#### BR-002

Appointment là khái niệm riêng với Visit.

#### BR-003

Appointment có Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải.

#### BR-004

Thời điểm bắt đầu phải sau hiện tại, tính theo Asia/Ho_Chi_Minh.

#### BR-005

Thời lượng phải lớn hơn 0. Thời lượng tối đa là UNKNOWN.

#### BR-006

Chỉ Appointment Scheduled của cùng Veterinarian mới được đối chiếu xung đột. Dùng khoảng nửa mở [start, end), nên lịch chạm nhau được phép.

#### BR-007

Chỉ được đổi lịch khi Appointment ở Scheduled và loại chính Appointment đó khỏi kiểm tra xung đột.

#### BR-008

Vòng đời gồm Scheduled, Cancelled, Completed. Khi tạo là Scheduled; chỉ Scheduled mới được chỉnh sửa, đổi lịch, hủy hoặc hoàn tất.

#### BR-009

Hủy lịch giải phóng khung giờ.

#### BR-010

Hoàn tất tạo chính xác một Visit mới.

#### BR-011

Không xóa cứng Appointment.

#### BR-012

Baseline được duyệt không cấm lịch Appointment của cùng Pet chồng lấn.

#### BR-013

Kết quả nghiệp vụ khi đặt đồng thời là chỉ lưu Appointment không xung đột.

#### BR-014

Cần xem Appointment. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN.

## Đánh giá khả năng kiểm thử

| Chủ đề | Bằng chứng và khả năng quan sát | Giới hạn / việc cần làm rõ |
| --- | --- | --- |
| Tạo Appointment | FR-001 và BR-003/004/005/008 nêu các trường, trạng thái ban đầu, múi giờ, và thời lượng dương; có thể kiểm tra bản ghi kết quả và trạng thái. | Không có quy tắc về định dạng, thông báo lỗi, hoặc cách nhập liệu. Thời lượng tối đa còn UNKNOWN. |
| Xung đột lịch | FR-002 và BR-006/013 xác định cùng Veterinarian, trạng thái Scheduled, khoảng nửa mở và kết quả đặt đồng thời. Có thể quan sát kết quả lưu và các Appointment còn lại. | Không quy định thuật toán, khóa, transaction, hay giao diện/API; chỉ kiểm chứng kết quả nghiệp vụ. |
| Đổi lịch | FR-003 và BR-007/008 nêu trạng thái cho phép và tự loại Appointment đang đổi khỏi so khớp. | Không có quy tắc về thông báo hay tương tác UI/API. |
| Hủy và hoàn tất | FR-004/005 cùng BR-002/008/009/010/011 nêu chuyển trạng thái, giữ Appointment, giải phóng lịch và tạo Visit chính xác một lần. | Cần dữ liệu kiểm thử để quan sát quan hệ Appointment/Visit; schema và cơ chế lưu không được cung cấp. |
| Xem danh sách | FR-006 và BR-014 xác nhận khả năng xem, đồng thời để filter/sort/pagination UNKNOWN. | Không xác định kênh hiển thị hay các hành vi danh sách chưa được BA quyết định. |
| Bằng chứng hệ thống | Không có mã nguồn, kiến trúc, môi trường, telemetry hay test inventory trong đầu vào. | Không thể nhận xét khả năng seed dữ liệu, mock/fault injection, log, tính song song, flaky test, hay coverage hiện có. Cần xác định các điểm quan sát ở thiết kế kỹ thuật. |

Các hành vi được mô tả trong bảng coverage là điều kiện nghiệp vụ để kiểm thử sau này, không chỉ định giao diện hoặc API. Mức `Unit` phù hợp với quy tắc thuần về thời gian/khoảng; `Integration` phù hợp khi phải xác minh các bản ghi và chuyển trạng thái cùng Visit. `E2E` chỉ nên chọn sau khi có kênh người dùng và môi trường xác định.

## Đánh giá rủi ro

Điểm xác suất và ảnh hưởng dùng thang 1–3; điểm = xác suất × ảnh hưởng. Các xác suất là ước lượng hoạch định dựa trên độ phức tạp của quy tắc, không dựa trên lịch sử lỗi vì không có bằng chứng hệ thống. Điểm và mitigation là khuyến nghị TEA.

| Risk ID | Nhóm | Rủi ro có căn cứ | Xác suất | Ảnh hưởng | Điểm | Giảm thiểu đề xuất | Chủ sở hữu đề xuất | Thời điểm |
| --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| R-001 | BUS | Quy tắc cùng Veterinarian, khoảng [start, end), và đặt đồng thời (FR-002; BR-006; BR-013) có thể bị xử lý sai, dẫn tới lưu hai Appointment xung đột hoặc từ chối lịch chạm nhau hợp lệ. | 2 | 3 | 6 | Kiểm tra overlap và ranh giới chạm nhau; kiểm tra kết quả đồng thời chỉ giữ lịch không xung đột, không quy định thứ tự bên thắng hay giải pháp kỹ thuật. | Phát triển + QA | Trước khi hoàn tất xác minh nghiệp vụ |
| R-002 | DATA | Hoàn tất phải chuyển Scheduled sang Completed và tạo chính xác một Visit mới; Appointment phải khác Visit (FR-005; BR-002; BR-008; BR-010). Sai lệch có thể gây Visit thiếu/thừa hoặc trạng thái không nhất quán. | 2 | 3 | 6 | Quan sát trạng thái Appointment và số Visit mới sau hoàn tất; kiểm tra lặp thao tác không làm tăng số Visit vượt quá một. | Phát triển + QA | Trước khi hoàn tất xác minh nghiệp vụ |
| R-003 | DATA | Hủy phải giải phóng slot nhưng không xóa cứng Appointment (FR-004; BR-008; BR-009; BR-011). Một trong hai hiệu ứng bị thiếu sẽ làm sai khả năng đặt lại hoặc mất dấu Appointment. | 2 | 3 | 6 | Xác minh Appointment vẫn tồn tại ở Cancelled và một Appointment khác có thể chiếm lại slot. | Phát triển + QA | Trước khi hoàn tất xác minh nghiệp vụ |
| R-004 | BUS | Khi đổi lịch, Appointment Scheduled đang đổi phải bị loại khỏi đối chiếu (FR-003; BR-007); nếu không, bản thân nó có thể tạo xung đột giả. | 2 | 2 | 4 | Kiểm tra đổi lịch sang slot không có Appointment Scheduled khác và kiểm tra đụng lịch với Appointment khác vẫn bị ngăn. | Phát triển + QA | Trong kiểm thử đổi lịch |
| R-005 | BUS | Tạo yêu cầu thời điểm sau hiện tại theo Asia/Ho_Chi_Minh và thời lượng lớn hơn 0 (FR-001; BR-004; BR-005); xử lý sai biên có thể chấp nhận dữ liệu không hợp lệ. | 2 | 2 | 4 | Kiểm tra biên bằng thời điểm hiện tại theo múi giờ đã nêu và thời lượng 0/âm; chỉ kiểm tra giới hạn tối đa sau khi BA quyết định. | Phát triển + QA | Trong kiểm thử tạo Appointment |

R-001, R-002 và R-003 có điểm từ 6 nên được đề xuất ưu tiên giảm thiểu. Không có dữ liệu để xác lập xác suất thực nghiệm; không có điểm rủi ro nào là kết luận phát hành.

## NFR và quyết định còn mở

Đầu vào không nêu yêu cầu/threshold riêng về security, performance, reliability, scalability, maintainability, compliance hoặc vận hành. Vì vậy các nhóm NFR này không được xem là acceptance criteria của Epic 1 và không có validation evidence hay risk score NFR nào được suy diễn. Nếu yêu cầu NFR được bổ sung, cần lập kế hoạch evidence riêng trước `nfr-assess`.

| Tham chiếu BA | Chưa quyết định | Cách xử lý trong kế hoạch |
| --- | --- | --- |
| BR-005; FR-001 | Thời lượng tối đa vẫn UNKNOWN; không tự đặt giới hạn. | Hàng TC-017 bị deferred. Không có kết quả pass/fail nào có thể được khẳng định trong khi quyết định BA chờ được làm rõ. |
| FR-006; BR-014 | Bộ lọc, sắp xếp và phân trang danh sách vẫn UNKNOWN. | Hàng TC-018 bị deferred. Không có kết quả pass/fail nào có thể được khẳng định trong khi quyết định BA chờ được làm rõ. |

## Ngoài phạm vi

| Hạng mục | Lý do | Cách xử lý |
| --- | --- | --- |
| Thiết kế giao diện, API, schema, transaction/locking | Không được cung cấp như authority của yêu cầu; không được suy diễn. | Đội kỹ thuật quyết định ở pha thiết kế/engineering, giữ nguyên kết quả nghiệp vụ đã duyệt. |
| Test automation, thực thi test, truy cập TestOps, export XMind/Excel | Bị loại khỏi phạm vi yêu cầu lượt này. | Thực hiện riêng khi được yêu cầu và khi có implementation/evidence phù hợp. |
| Kiểm thử PetClinic hiện trạng | Không có bằng chứng hệ thống được cung cấp. | Không tuyên bố có/không có test hoặc defect hiện tại. |

## Test Coverage Plan

Các mức P0–P3 là mức ưu tiên, không phải lịch chạy. Risk Link chỉ trỏ đến Risk ID trong sổ rủi ro. Trace chứa duy nhất ID FR/BR. Scenario deferred vẫn có Test ID nhưng chưa phải ca pass/fail có thể thực thi.

### P0

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
| --- | --- | --- | --- | --- | --- |
| TC-001 | Từ chối hai Appointment Scheduled chồng lấn của cùng Veterinarian | Integration | R-001 | FR-002;BR-006 | Appointment xung đột thứ hai không được lưu; Appointment Scheduled hiện có vẫn giữ nguyên. |
| TC-002 | Cho phép hai Appointment cùng Veterinarian chạm biên [start, end) | Unit | R-001 | FR-002;BR-006 | Nếu thời điểm kết thúc của lịch trước bằng thời điểm bắt đầu của lịch sau, cả hai Appointment được chấp nhận. |
| TC-003 | Đặt đồng thời hai Appointment có khoảng chồng lấn của cùng Veterinarian | Integration | R-001 | BR-006;BR-013 | Sau hai yêu cầu đồng thời, chỉ Appointment không xung đột được lưu; không khẳng định yêu cầu nào thắng nếu đầu vào không xác định thứ tự. |
| TC-004 | Hoàn tất Scheduled tạo một Visit mới và chuyển Appointment sang Completed | Integration | R-002 | FR-005;BR-002;BR-008;BR-010 | Có đúng một Visit mới gắn với hoạt động hoàn tất; Appointment chuyển sang Completed và vẫn là đối tượng riêng với Visit. |

### P1

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
| --- | --- | --- | --- | --- | --- |
| TC-005 | Tạo Appointment hợp lệ với đủ thông tin và trạng thái Scheduled | Integration | R-005 | FR-001;BR-001;BR-003;BR-004;BR-005;BR-008 | Appointment được ghi nhận với Pet, Veterinarian, thời điểm bắt đầu, thời lượng, lý do/diễn giải đã cung cấp và trạng thái Scheduled. |
| TC-006 | Không chấp nhận thời điểm bắt đầu bằng hoặc trước hiện tại theo Asia/Ho_Chi_Minh | Unit | R-005 | FR-001;BR-004 | Với thời điểm bằng hiện tại hoặc đã qua theo múi giờ đã nêu, không có Appointment mới được tạo. |
| TC-007 | Không chấp nhận thời lượng bằng 0 hoặc âm | Unit | R-005 | FR-001;BR-005 | Với thời lượng 0 hoặc nhỏ hơn 0, không có Appointment mới được tạo. |
| TC-008 | Chỉnh sửa Appointment ở trạng thái Scheduled | Integration | R-004 | FR-003;BR-008 | Thay đổi hợp lệ trên Appointment Scheduled được lưu; trạng thái vẫn Scheduled trừ khi có quy tắc được duyệt khác. |
| TC-009 | Không cho chỉnh sửa hoặc đổi lịch Appointment không ở Scheduled | Integration | R-004 | FR-003;BR-008 | Với Appointment Cancelled hoặc Completed, không có thay đổi trường hoặc thời điểm được lưu. |
| TC-010 | Đổi lịch Appointment Scheduled mà không tự gây xung đột với chính nó | Integration | R-004 | FR-003;BR-007 | Khi slot đích không xung đột với Appointment Scheduled khác cùng Veterinarian, lịch mới được lưu và không bị từ chối do chính Appointment đang đổi. |
| TC-011 | Từ chối đổi lịch vào khoảng chồng lấn với Appointment Scheduled khác cùng Veterinarian | Integration | R-001;R-004 | FR-002;FR-003;BR-006;BR-007 | Thay đổi xung đột không được lưu; lịch hiện có không bị thay đổi. |
| TC-012 | Hủy Appointment Scheduled, giữ lại bản ghi và giải phóng slot | Integration | R-003 | FR-004;BR-008;BR-009;BR-011 | Appointment chuyển sang Cancelled và vẫn tồn tại; một Appointment khác cùng Veterinarian có thể được đặt vào slot vừa giải phóng. |
| TC-013 | Không cho hủy Appointment đã Cancelled hoặc Completed | Integration | R-003 | FR-004;BR-008;BR-011 | Appointment không bị xóa cứng hoặc thay đổi trạng thái khi yêu cầu hủy áp dụng cho trạng thái khác Scheduled. |
| TC-014 | Không cho hoàn tất Appointment đã Cancelled hoặc Completed | Integration | R-002 | FR-005;BR-008;BR-010 | Trạng thái không chuyển lại sang Completed do yêu cầu lặp/sai trạng thái; không tạo thêm Visit. |

### P2

| Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được |
| --- | --- | --- | --- | --- | --- |
| TC-015 | Cho phép Appointment của cùng Pet chồng lấn khi Veterinarian khác nhau | Integration | R-001 | FR-002;BR-006;BR-012 | Hai Appointment chồng lấn về thời gian nhưng khác Veterinarian được chấp nhận; không thêm ràng buộc cấm cùng Pet. |
| TC-016 | Xem Appointment | E2E sau khi xác định kênh xem | - | FR-006;BR-001;BR-003;BR-014 | Appointment có thể được xem; chưa khẳng định vị trí, cách trình bày hoặc cơ chế truy cập vì chưa được chỉ định. |
| TC-017 | Xác minh biên thời lượng tối đa của Appointment — deferred theo BR-005 | Chưa xác định | - | FR-001;BR-005 | Thời lượng tối đa là UNKNOWN. Không có kết quả pass/fail nào có thể được khẳng định trong khi quyết định BA chờ được làm rõ; không tự đặt giới hạn. |
| TC-018 | Xác minh bộ lọc, sắp xếp và phân trang Appointment — deferred theo FR-006/BR-014 | Chưa xác định | - | FR-006;BR-014 | Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định. Không có kết quả pass/fail nào có thể được khẳng định trong khi quyết định BA chờ được làm rõ. |

### P3

Không có kịch bản P3 được suy ra từ yêu cầu và Business Rules đã duyệt trong phạm vi này.

## Chiến lược thực thi đề xuất

- **PR:** Chạy các kiểm tra chức năng nếu suite sau này đáp ứng mục tiêu dưới 15 phút; ưu tiên kiểm tra xác định về khoảng thời gian, trạng thái và tính nhất quán dữ liệu.
- **Nightly:** Chỉ cân nhắc cho kiểm tra đặt đồng thời nếu môi trường hoặc thời lượng khiến PR không phù hợp.
- **Weekly:** Không có kiểm tra dài hạn/NFR nào được xác định từ đầu vào hiện tại.

Không có test nào được chạy trong lượt tạo Test Design này.

## Ước lượng nguồn lực

Ước lượng dưới đây chỉ để hoạch định ban đầu, không phải cam kết effort. P0: 4–8 giờ; P1: 8–16 giờ; P2: 2–5 giờ; P3: 0 giờ theo phạm vi hiện tại. Tổng: khoảng 14–29 giờ (khoảng 2–4 ngày làm việc), chưa gồm làm rõ BA hoặc dựng môi trường/dữ liệu chưa được mô tả.

## Tiêu chí chất lượng đề xuất

Các ngưỡng sau chỉ là khuyến nghị TEA, không phải release verdict hay quyết định BA:

- P0: 100% pass trước khi chấp nhận coverage kiểm thử P0.
- P1: mục tiêu ít nhất 95%; sai khác cần được đánh giá và ghi nhận.
- Mục tiêu coverage yêu cầu: ít nhất 80% acceptance criteria được ánh xạ tới scenario có quan sát được; mọi khoảng trống phải được nêu rõ.
- Các rủi ro điểm từ 6 cần có mitigation được xác nhận trước khi xem xét phát hành.
- Không đo coverage nghiệp vụ cho kết quả còn UNKNOWN; chờ BA làm rõ rồi cập nhật Test Design.

## Dữ liệu, điều kiện bắt đầu và phụ thuộc

- Cần Pet và Veterinarian hợp lệ, Appointment ở các trạng thái Scheduled/Cancelled/Completed, và khả năng quan sát Appointment cùng Visit sau thao tác.
- Để kiểm tra biên thời gian, dữ liệu test cần xác định thời điểm tham chiếu theo Asia/Ho_Chi_Minh; cách kiểm soát đồng hồ chưa được cung cấp.
- Để kiểm tra đặt đồng thời, cần môi trường cho phép gửi yêu cầu đồng thời và xác minh kết quả cuối; không áp đặt cơ chế kỹ thuật.
- Trước khi chốt coverage cho độ dài thời lượng tối đa và hành vi danh sách, BA cần làm rõ BR-005, FR-006 và BR-014.
- Không đặt tiêu chí thoát gắn với kết quả chạy thực tế vì chưa có lần chạy test và đây không phải đánh giá phát hành.

## Giả định và giới hạn

- Chỉ dùng ngữ nghĩa và kết quả nghiệp vụ trong FR/BR nguyên văn ở trên; không xem ví dụ hoặc suy luận kỹ thuật là yêu cầu.
- Điểm rủi ro, ưu tiên, cấp độ kiểm thử, effort và ngưỡng là tư vấn để nhóm điều chỉnh theo evidence sau này.
- Truy vết trong coverage dùng chính xác FR/BR ID; mọi ô Truy vết chỉ chứa các ID ngăn cách bằng dấu chấm phẩy.
- Kế hoạch không tạo mã/automation, không chạy test, không xuất XMind/Excel, không truy cập TestOps và không sửa PetClinic source.
