# Testcases thủ công — CR-001 Appointment Scheduling

**Nguồn sinh:** skills/create-test-cases tại commit e6cdd774f66ce9d45ea5904101a96203e3a37581  
**Phạm vi:** semantic testcases từ Test Design Stage 1–2; không import vào Katalon.

## Quy ước dữ liệu và tiền điều kiện chung

- BASE: Appointment feature có trong test build; phiên thao tác đại diện cho Clinic Staff đã đăng nhập; Pet-A, Pet-B, Vet-A, Vet-B là bản ghi hợp lệ có thể chọn; mỗi testcase dùng fixture cô lập hoặc dữ liệu riêng, không phụ thuộc kết quả testcase khác.
- CLOCK: Với kiểm tra thời điểm, môi trường cung cấp clock kiểm soát được ở T0 = 2030-06-15 08:00 theo Asia/Ho_Chi_Minh. T+1m và T−1m là đúng một phút quanh T0. Đây là điều kiện môi trường, không phải yêu cầu sản phẩm.
- D+: giá trị dương 1 trong đơn vị hiển thị của trường thời lượng; chỉ là test data, không phải thời lượng mặc định hay giới hạn.
- REASON-A: “Tái khám” là dữ liệu nhập ví dụ. Không kiểm tra requiredness hoặc thông báo lỗi của trường này.
- INTERVAL-A: fixture hiển thị một Appointment trong khoảng [2030-06-15 10:00, 10:15). Các khoảng B được ghi cụ thể theo từng testcase. Nếu UI yêu cầu nhập thời lượng, dùng dữ liệu fixture tạo ra khoảng hiển thị đó theo hợp đồng giao diện đã duyệt; testcase không tự định nghĩa công thức chuyển thời lượng thành end.
- Tên màn hình, nút, thông báo, route, đơn vị thời lượng và trường có thể sửa chưa được đặc tả. Tên hành động dưới đây là mô tả nghiệp vụ để gắn với giao diện khi được duyệt; không phải literal UI text.
- Các testcase không đặt expected result cho maximum duration, list filters, default sorting, pagination/page size, status code/message, authorization mapping, hoặc field mapping Appointment → Visit.

---

## TC-001 Tạo và xem Appointment hợp lệ

**Objective:** Xác nhận Clinic Staff có thể tạo một Appointment hợp lệ ở trạng thái Scheduled và xem được bản ghi vừa tạo.

**Preconditions:** BASE; chưa có Scheduled Appointment của Vet-A chồng lấn thời điểm kiểm tra.

**Test Data:** Pet-A; Vet-A; thời điểm ngày kế tiếp lúc 10:00 theo Asia/Ho_Chi_Minh; D+; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, FR-006, BR-001, BR-003, BR-008, BR-014  
**Test Design refs:** TD-001, TD-014

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở khu vực quản lý Appointment. | Khu vực Appointment được hiển thị. |
| 2 | Bắt đầu tạo Appointment mới. | Form tạo Appointment được hiển thị. |
| 3 | Chọn Pet-A và Vet-A; nhập thời điểm, D+ và REASON-A. | Các giá trị đã chọn/nhập được hiển thị trong form. |
| 4 | Lưu Appointment. | Một Appointment mới được tạo ở trạng thái Scheduled; bản ghi không bị từ chối. |
| 5 | Mở bản ghi vừa tạo từ kết quả hoặc khu vực xem Appointment. | Appointment vừa tạo có thể được xem; Pet, Veterinarian, thời điểm, thời lượng và reason/description khớp dữ liệu đã nhập. Không kiểm tra thứ tự hoặc phân trang. |

**Expected Result:** Appointment hợp lệ được tạo ở Scheduled và có thể xem; không suy ra giá trị mặc định hoặc requiredness.

## TC-002 Chấp nhận thời điểm bắt đầu ngay sau hiện tại

**Objective:** Xác nhận thời điểm bắt đầu lớn hơn T0 được chấp nhận.

**Preconditions:** BASE, CLOCK; không có Appointment chồng lấn với Vet-A.

**Test Data:** Pet-A; Vet-A; start = T+1m; D+; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, BR-004  
**Test Design refs:** TD-002

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment. | Form tạo Appointment được hiển thị. |
| 2 | Nhập Pet-A, Vet-A, start = T+1m, D+ và REASON-A. | Giá trị start được giữ đúng như đã nhập. |
| 3 | Lưu Appointment. | Appointment được tạo ở trạng thái Scheduled. |

**Expected Result:** Start lớn hơn T0 theo Asia/Ho_Chi_Minh được chấp nhận.

## TC-003 Từ chối thời điểm bắt đầu đúng hiện tại

**Objective:** Xác nhận start bằng đúng T0 không được chấp nhận.

**Preconditions:** BASE, CLOCK; không có Appointment chồng lấn với Vet-A.

**Test Data:** Pet-A; Vet-A; start = T0; D+; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, BR-004  
**Test Design refs:** TD-002

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment. | Form tạo Appointment được hiển thị. |
| 2 | Nhập dữ liệu hợp lệ, đặt start = T0. | Start bằng đúng clock hiện tại trong fixture. |
| 3 | Thử lưu Appointment. | Appointment không được tạo. Không yêu cầu thông báo lỗi cụ thể. |

**Expected Result:** Start không strictly-after T0 bị từ chối.

## TC-004 Từ chối thời điểm bắt đầu trong quá khứ

**Objective:** Xác nhận start nhỏ hơn T0 không được chấp nhận.

**Preconditions:** BASE, CLOCK; không có Appointment chồng lấn với Vet-A.

**Test Data:** Pet-A; Vet-A; start = T−1m; D+; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, BR-004  
**Test Design refs:** TD-002

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment. | Form tạo Appointment được hiển thị. |
| 2 | Nhập dữ liệu hợp lệ, đặt start = T−1m. | Start được giữ đúng như đã nhập. |
| 3 | Thử lưu Appointment. | Appointment không được tạo. Không yêu cầu thông báo lỗi cụ thể. |

**Expected Result:** Start trong quá khứ bị từ chối.

## TC-005 Chấp nhận thời lượng dương

**Objective:** Xác nhận một giá trị thời lượng dương được chấp nhận.

**Preconditions:** BASE; không có Appointment chồng lấn với Vet-A.

**Test Data:** Pet-A; Vet-A; thời điểm tương lai; duration = D+; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, BR-005  
**Test Design refs:** TD-003

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment. | Form tạo Appointment được hiển thị. |
| 2 | Nhập dữ liệu hợp lệ với duration = D+. | Trường duration hiển thị giá trị dương đã nhập. |
| 3 | Lưu Appointment. | Appointment được tạo ở trạng thái Scheduled. |

**Expected Result:** Giá trị duration dương này được chấp nhận. Đây không phải kiểm tra maximum.

## TC-006 Từ chối thời lượng bằng 0

**Objective:** Xác nhận duration bằng 0 không được chấp nhận.

**Preconditions:** BASE; không có Appointment chồng lấn với Vet-A.

**Test Data:** Pet-A; Vet-A; thời điểm tương lai; duration = 0; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, BR-005  
**Test Design refs:** TD-003

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment. | Form tạo Appointment được hiển thị. |
| 2 | Nhập dữ liệu hợp lệ, đặt duration = 0. | Giá trị 0 được nhập hoặc được form biểu diễn để gửi. |
| 3 | Thử lưu Appointment. | Appointment không được tạo. Không yêu cầu thông báo lỗi cụ thể. |

**Expected Result:** Duration không lớn hơn 0 bị từ chối.

## TC-007 Từ chối thời lượng âm

**Objective:** Xác nhận duration nhỏ hơn 0 không được chấp nhận.

**Preconditions:** BASE; không có Appointment chồng lấn với Vet-A.

**Test Data:** Pet-A; Vet-A; thời điểm tương lai; duration = −1 trong đơn vị trường; REASON-A.

**Priority:** P1  
**Requirement refs:** FR-001, BR-005  
**Test Design refs:** TD-003

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment. | Form tạo Appointment được hiển thị. |
| 2 | Nhập dữ liệu hợp lệ, đặt duration = −1. | Giá trị âm được nhập hoặc được form biểu diễn để gửi. |
| 3 | Thử lưu Appointment. | Appointment không được tạo. Không yêu cầu thông báo lỗi cụ thể. |

**Expected Result:** Duration âm bị từ chối.

## TC-008 Từ chối overlap với Scheduled Appointment cùng Veterinarian

**Objective:** Xác nhận hai khoảng Scheduled chồng lấn của cùng Veterinarian không thể cùng được đặt.

**Preconditions:** BASE; INTERVAL-A tồn tại ở Scheduled với Vet-A.

**Test Data:** Appointment mới cho Vet-A, khoảng hiển thị [10:14, 10:29), Pet-B; khoảng này chồng lấn INTERVAL-A.

**Priority:** P1  
**Requirement refs:** FR-002, BR-006  
**Test Design refs:** TD-004

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment mới. | Form tạo Appointment được hiển thị. |
| 2 | Nhập Pet-B, Vet-A và dữ liệu tạo khoảng [10:14, 10:29). | Dữ liệu biểu diễn một khoảng chồng lấn INTERVAL-A. |
| 3 | Thử lưu Appointment. | Appointment chồng lấn không được tạo; không có hai Scheduled Appointment cùng Vet-A trong hai khoảng này. |

**Expected Result:** Overlap với Scheduled Appointment cùng Veterinarian bị từ chối; không kiểm tra mã hoặc nội dung lỗi.

## TC-009 Cho phép Appointment mới bắt đầu đúng lúc Appointment cũ kết thúc

**Objective:** Xác nhận hai khoảng chạm nhau tại end/start được phép.

**Preconditions:** BASE; INTERVAL-A tồn tại ở Scheduled với Vet-A.

**Test Data:** Pet-B; Vet-A; requested interval bắt đầu đúng tại 10:15, là end của INTERVAL-A.

**Priority:** P1  
**Requirement refs:** FR-002, BR-006  
**Test Design refs:** TD-004

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment mới. | Form tạo Appointment được hiển thị. |
| 2 | Nhập Pet-B, Vet-A và khoảng bắt đầu tại 10:15. | Start mới bằng đúng end của INTERVAL-A. |
| 3 | Lưu Appointment. | Appointment mới được tạo ở Scheduled. |

**Expected Result:** [start, end) cho phép khoảng mới bắt đầu đúng tại end của khoảng cũ.

## TC-010 Cho phép Appointment mới kết thúc đúng lúc Appointment cũ bắt đầu

**Objective:** Xác nhận khoảng mới có end bằng start của Appointment cũ được phép.

**Preconditions:** BASE; INTERVAL-A tồn tại ở Scheduled với Vet-A.

**Test Data:** Pet-B; Vet-A; requested interval kết thúc đúng tại 10:00, là start của INTERVAL-A.

**Priority:** P1  
**Requirement refs:** FR-002, BR-006  
**Test Design refs:** TD-004

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment mới. | Form tạo Appointment được hiển thị. |
| 2 | Nhập Pet-B, Vet-A và khoảng kết thúc tại 10:00. | End mới bằng đúng start của INTERVAL-A. |
| 3 | Lưu Appointment. | Appointment mới được tạo ở Scheduled. |

**Expected Result:** [start, end) cho phép khoảng mới kết thúc đúng tại start của khoảng cũ.

## TC-011 Cho phép cùng Pet có lịch overlap với Veterinarian khác

**Objective:** Xác nhận conflict được xác định theo Veterinarian; cùng Pet với Veterinarian khác không bị từ chối chỉ vì Pet trùng.

**Preconditions:** BASE; INTERVAL-A tồn tại ở Scheduled cho Pet-A và Vet-A.

**Test Data:** Pet-A; Vet-B; requested interval chồng lấn INTERVAL-A.

**Priority:** P1  
**Requirement refs:** FR-002, BR-006, BR-012  
**Test Design refs:** TD-005

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở form tạo Appointment mới. | Form tạo Appointment được hiển thị. |
| 2 | Chọn Pet-A, chọn Vet-B và nhập khoảng chồng lấn INTERVAL-A. | Pet giống bản ghi cũ; Veterinarian khác. |
| 3 | Lưu Appointment. | Appointment mới được tạo ở Scheduled. |

**Expected Result:** Overlap của cùng Pet nhưng khác Veterinarian không bị từ chối chỉ vì Pet giống nhau.

## TC-012 Cho phép sửa Appointment khi đang Scheduled

**Objective:** Xác nhận một trường được hợp đồng giao diện duyệt cho phép sửa có thể được cập nhật khi Appointment ở Scheduled.

**Preconditions:** BASE; có Appointment A ở Scheduled; hợp đồng giao diện đã xác định trường EDIT_FIELD có thể sửa.

**Test Data:** Appointment A; EDIT_FIELD và EDIT_VALUE lấy từ hợp đồng giao diện đã duyệt. Chưa có tên trường cụ thể trong BA/Test Design.

**Priority:** P1  
**Requirement refs:** FR-003, BR-007, BR-008  
**Test Design refs:** TD-006

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Chi tiết Appointment A đang ở Scheduled được hiển thị. |
| 2 | Mở hành động sửa Appointment. | Form sửa bản ghi được hiển thị. |
| 3 | Cập nhật EDIT_FIELD thành EDIT_VALUE và lưu. | Thay đổi được lưu; Appointment vẫn ở Scheduled. |
| 4 | Mở lại Appointment A. | Giá trị EDIT_VALUE được hiển thị. |

**Expected Result:** Một sửa đổi được hợp đồng giao diện cho phép được chấp nhận khi trạng thái là Scheduled. Trường cụ thể phải được chốt trước khi chạy.

## TC-013 Reschedule không tự conflict với Appointment đang đổi

**Objective:** Xác nhận Appointment đang reschedule được loại khỏi phép kiểm tra conflict.

**Preconditions:** BASE; chỉ có Appointment A ở Scheduled cho Vet-A trong vùng thời gian liên quan; không có Scheduled Appointment khác của Vet-A chồng lấn mục tiêu.

**Test Data:** Appointment A cũ có khoảng [10:00, 10:15); mục tiêu mới [10:05, 10:20), chồng lấn khoảng cũ của chính A.

**Priority:** P1  
**Requirement refs:** FR-003, BR-006, BR-007, BR-008  
**Test Design refs:** TD-006

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A đang Scheduled. | Chi tiết Appointment A được hiển thị. |
| 2 | Chọn đổi lịch và nhập mục tiêu [10:05, 10:20). | Mục tiêu overlap khoảng cũ của A; không có Appointment khác gây conflict. |
| 3 | Lưu thay đổi. | Reschedule được chấp nhận. |
| 4 | Mở lại Appointment A. | Chỉ một Appointment A ở Scheduled tồn tại tại khoảng mới. |

**Expected Result:** A không tự bị coi là conflict với chính dữ liệu cũ của nó.

## TC-014 Từ chối reschedule vào khoảng conflict với Appointment khác

**Objective:** Xác nhận reschedule không được chấp nhận khi đích overlap Scheduled Appointment khác cùng Veterinarian.

**Preconditions:** BASE; Appointment A và B đều Scheduled với Vet-A; khoảng hiện tại của A không conflict với B.

**Test Data:** B có khoảng [10:20, 10:35); mục tiêu reschedule A là [10:25, 10:40).

**Priority:** P1  
**Requirement refs:** FR-002, FR-003, BR-006, BR-007  
**Test Design refs:** TD-007

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A đang Scheduled. | Chi tiết A được hiển thị. |
| 2 | Chọn đổi lịch và nhập mục tiêu [10:25, 10:40). | Mục tiêu chồng lấn Appointment B đang Scheduled của Vet-A. |
| 3 | Thử lưu reschedule. | Mục tiêu conflict không được chấp nhận; không tạo thêm Scheduled Appointment ở khoảng conflict. |

**Expected Result:** Reschedule conflict bị từ chối. Không khẳng định error message, status code hoặc cách khôi phục dữ liệu cũ.

## TC-015 Không cho sửa Appointment ở Cancelled

**Objective:** Xác nhận edit không làm thay đổi Appointment đã Cancelled.

**Preconditions:** BASE; Appointment A ở Cancelled; giao diện/hợp đồng edit xác định EDIT_FIELD.

**Test Data:** Appointment A; EDIT_FIELD và EDIT_VALUE theo hợp đồng giao diện đã duyệt.

**Priority:** P1  
**Requirement refs:** FR-003, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Cancelled được hiển thị. |
| 2 | Thử mở hoặc thực hiện hành động sửa theo luồng giao diện hiện có. | Hành động không cho phép thay đổi Appointment; không yêu cầu control phải ẩn hay hiện. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Cancelled; EDIT_VALUE không được lưu. |

**Expected Result:** Appointment Cancelled không được sửa.

## TC-016 Không cho reschedule Appointment ở Cancelled

**Objective:** Xác nhận reschedule không làm thay đổi Appointment đã Cancelled.

**Preconditions:** BASE; Appointment A ở Cancelled.

**Test Data:** Appointment A; mục tiêu reschedule là một khoảng tương lai không conflict.

**Priority:** P1  
**Requirement refs:** FR-003, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Cancelled được hiển thị. |
| 2 | Thử đổi lịch A qua luồng nghiệp vụ hiện có. | Reschedule không được thực hiện. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Cancelled; thời điểm không đổi. |

**Expected Result:** Appointment Cancelled không được reschedule.

## TC-017 Không cho hủy Appointment đã Cancelled

**Objective:** Xác nhận không thể thực hiện lại hành động cancel trên Appointment đã Cancelled.

**Preconditions:** BASE; Appointment A ở Cancelled.

**Test Data:** Appointment A.

**Priority:** P1  
**Requirement refs:** FR-004, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Cancelled được hiển thị. |
| 2 | Thử thực hiện hành động cancel qua luồng nghiệp vụ hiện có. | Trạng thái không chuyển sang trạng thái khác. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Cancelled. |

**Expected Result:** Appointment Cancelled không thể bị hủy lần nữa; không yêu cầu thông báo cụ thể.

## TC-018 Không cho hoàn tất Appointment đã Cancelled

**Objective:** Xác nhận Appointment đã Cancelled không thể chuyển sang Completed.

**Preconditions:** BASE; Appointment A ở Cancelled.

**Test Data:** Appointment A.

**Priority:** P1  
**Requirement refs:** FR-005, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Cancelled được hiển thị. |
| 2 | Thử thực hiện hành động complete qua luồng nghiệp vụ hiện có. | Trạng thái không chuyển sang Completed. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Cancelled. |

**Expected Result:** Appointment Cancelled không thể hoàn tất.

## TC-019 Không cho sửa Appointment ở Completed

**Objective:** Xác nhận edit không làm thay đổi Appointment đã Completed.

**Preconditions:** BASE; Appointment A ở Completed; giao diện/hợp đồng edit xác định EDIT_FIELD.

**Test Data:** Appointment A; EDIT_FIELD và EDIT_VALUE theo hợp đồng giao diện đã duyệt.

**Priority:** P1  
**Requirement refs:** FR-003, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Completed được hiển thị. |
| 2 | Thử mở hoặc thực hiện hành động sửa theo luồng giao diện hiện có. | Hành động không cho phép thay đổi Appointment; không yêu cầu control phải ẩn hay hiện. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Completed; EDIT_VALUE không được lưu. |

**Expected Result:** Appointment Completed không được sửa.

## TC-020 Không cho reschedule Appointment ở Completed

**Objective:** Xác nhận reschedule không làm thay đổi Appointment đã Completed.

**Preconditions:** BASE; Appointment A ở Completed.

**Test Data:** Appointment A; mục tiêu reschedule là một khoảng tương lai không conflict.

**Priority:** P1  
**Requirement refs:** FR-003, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Completed được hiển thị. |
| 2 | Thử đổi lịch A qua luồng nghiệp vụ hiện có. | Reschedule không được thực hiện. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Completed; thời điểm không đổi. |

**Expected Result:** Appointment Completed không được reschedule.

## TC-021 Không cho hủy Appointment đã Completed

**Objective:** Xác nhận Appointment Completed không thể chuyển sang Cancelled.

**Preconditions:** BASE; Appointment A ở Completed.

**Test Data:** Appointment A.

**Priority:** P1  
**Requirement refs:** FR-004, BR-008  
**Test Design refs:** TD-008

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Completed được hiển thị. |
| 2 | Thử thực hiện hành động cancel qua luồng nghiệp vụ hiện có. | Trạng thái không chuyển sang Cancelled. |
| 3 | Mở lại Appointment A. | Trạng thái vẫn Completed. |

**Expected Result:** Appointment Completed không thể bị hủy.

## TC-022 Không cho hoàn tất Appointment đã Completed lần nữa

**Objective:** Xác nhận lặp lại hành động complete không tạo thêm kết quả hoàn tất.

**Preconditions:** BASE; Appointment A ở Completed; số Visit hiện có của fixture đã được ghi nhận là N.

**Test Data:** Appointment A; baseline Visit count = N.

**Priority:** P1  
**Requirement refs:** FR-005, BR-008, BR-010  
**Test Design refs:** TD-008, TD-011

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | Trạng thái Completed được hiển thị. |
| 2 | Thử thực hiện lại hành động complete qua luồng nghiệp vụ hiện có. | Appointment không thực hiện thêm một lần chuyển trạng thái. |
| 3 | Mở lại Appointment A và xem Visit count của fixture. | Appointment vẫn Completed; Visit count vẫn là N. |

**Expected Result:** Appointment Completed không thể complete lần nữa và không tạo Visit bổ sung.

## TC-023 Hủy Appointment nhưng giữ lại bản ghi

**Objective:** Xác nhận cancel chuyển Scheduled sang Cancelled mà không xóa cứng Appointment.

**Preconditions:** BASE; Appointment A ở Scheduled và đang mở được bằng tham chiếu bản ghi.

**Test Data:** Appointment A.

**Priority:** P1  
**Requirement refs:** FR-004, BR-008, BR-009, BR-011  
**Test Design refs:** TD-009

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A. | A được hiển thị ở trạng thái Scheduled. |
| 2 | Thực hiện hành động cancel theo luồng giao diện. | Appointment chuyển sang Cancelled. |
| 3 | Mở lại cùng bản ghi bằng tham chiếu của A. | Bản ghi A vẫn tồn tại và trạng thái là Cancelled. |

**Expected Result:** Cancel giải phóng trạng thái lịch nhưng không hard-delete cùng bản ghi. Không kiểm tra A có xuất hiện trong danh sách mặc định hay không.

## TC-024 Đặt lại khoảng thời gian sau khi hủy

**Objective:** Xác nhận khoảng của Appointment Cancelled được giải phóng cho Appointment mới cùng Veterinarian.

**Preconditions:** BASE; Appointment A ở Scheduled với Vet-A và INTERVAL-A.

**Test Data:** Hủy A; sau đó tạo Appointment B cho Pet-B, Vet-A, cùng INTERVAL-A.

**Priority:** P1  
**Requirement refs:** FR-002, FR-004, BR-006, BR-009  
**Test Design refs:** TD-010

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A và hủy lịch. | A chuyển sang Cancelled. |
| 2 | Bắt đầu tạo Appointment B cho Vet-A. | Form tạo Appointment được hiển thị. |
| 3 | Nhập Pet-B và cùng INTERVAL-A, rồi lưu. | B được tạo ở Scheduled; A vẫn Cancelled. |

**Expected Result:** Khoảng đã hủy có thể được dùng cho lịch mới của cùng Veterinarian.

## TC-025 Hoàn tất Appointment tạo chính xác một Visit

**Objective:** Xác nhận hoàn tất Appointment Scheduled chuyển trạng thái và tạo đúng một Visit.

**Preconditions:** BASE; Appointment A ở Scheduled; fixture Visit có baseline count N.

**Test Data:** Appointment A; Visit count trước thao tác = N.

**Priority:** P1  
**Requirement refs:** FR-005, BR-002, BR-008, BR-010  
**Test Design refs:** TD-011

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Ghi nhận Visit count N trong fixture. | Baseline count N được xác nhận. |
| 2 | Mở Appointment A và thực hiện complete. | Appointment A chuyển sang Completed. |
| 3 | Xem Visit count sau thao tác. | Có đúng một Visit mới so với baseline, tức N+1. |
| 4 | Mở lại Appointment A. | Appointment vẫn là bản ghi riêng và ở Completed. |

**Expected Result:** Một lần complete tạo chính xác một Visit mới. Không kiểm tra dữ liệu nào của Appointment được sao chép sang Visit.

## TC-026 Appointment Completed không chặn lịch mới

**Objective:** Xác nhận chỉ Scheduled Appointment tham gia kiểm tra conflict.

**Preconditions:** BASE; Appointment A ở Completed với Vet-A và INTERVAL-A.

**Test Data:** Appointment B mới dùng Vet-A và cùng INTERVAL-A.

**Priority:** P1  
**Requirement refs:** FR-002, BR-006, BR-008  
**Test Design refs:** TD-012

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment A và xác nhận trạng thái Completed. | A được hiển thị là Completed. |
| 2 | Mở form tạo Appointment B. | Form tạo Appointment được hiển thị. |
| 3 | Nhập Pet-B, Vet-A và INTERVAL-A, rồi lưu. | B được tạo ở Scheduled; A vẫn Completed. |

**Expected Result:** Appointment Completed không tạo conflict với lịch Scheduled mới cùng Veterinarian và khoảng thời gian.

## TC-027 Hai yêu cầu đặt lịch đồng thời chỉ lưu kết quả không conflict

**Objective:** Xác nhận kết quả nghiệp vụ khi hai lịch chồng lấn cho cùng Veterinarian được gửi đồng thời.

**Preconditions:** BASE; có thể mở hai phiên Clinic Staff độc lập; không có Scheduled Appointment conflict trong khoảng kiểm tra. Dữ liệu mỗi phiên được chuẩn bị trước khi submit.

**Test Data:** Phiên 1: Pet-A/Vet-A/interval I; Phiên 2: Pet-B/Vet-A/interval chồng lấn I; cả hai start hợp lệ trong tương lai và duration dương.

**Priority:** P1  
**Requirement refs:** FR-002, BR-006, BR-013  
**Test Design refs:** TD-013

| Step | Test Step | Expected Result |
|---:|---|---|
| 1 | Mở Appointment creation trong hai phiên độc lập và nhập hai bộ dữ liệu. | Cả hai form đều sẵn sàng; hai khoảng có overlap với cùng Vet-A. |
| 2 | Gửi hai form đồng thời. | Hai yêu cầu được gửi cùng lúc; không yêu cầu response code/message cụ thể. |
| 3 | Xem các Appointment được ghi nhận trong fixture bằng tham chiếu bản ghi hiện có. | Chỉ một trong hai Appointment conflict được lưu ở Scheduled. |

**Expected Result:** Persisted business state không chứa cả hai Appointment Scheduled conflict. Nếu không thể tạo hai phiên thủ công, cần người kiểm thử thứ hai; không thay bằng automation trong benchmark này.

## Deferred theo UNKNOWN

- Không có testcase xác định Appointment maximum duration hoặc expected result vượt một ngưỡng tối đa.
- Không có testcase xác định list filters, default sorting, pagination hoặc page size.
- View case không khẳng định Appointment Cancelled/Completed có xuất hiện trong danh sách mặc định.
- Không có expected status code, error text, role/permission mapping, duration unit, hoặc Appointment-to-Visit field mapping.
