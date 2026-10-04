# Rà soát khoảng trống và quyết định Human minh họa

Tệp này phân biệt gap phát hiện từ input chưa đầy đủ với câu trả lời Human được cung cấp sau đó. Phần trả lời dưới đây là ngữ liệu ví dụ riêng; chúng không có trong [yêu cầu ban đầu](01-input-requirement.md).

## Gap trước khi làm rõ

Chỉ từ yêu cầu ban đầu, các câu hỏi sau đều là **UNKNOWN**.

| Nhóm | Câu hỏi cần làm rõ |
|---|---|
| Actor và quyền truy cập | Vai trò Clinic Staff nào được tạo, xem, chỉnh sửa, đổi lịch, hủy hoặc hoàn tất? Có giới hạn xem bản ghi không? |
| Appointment và Visit | Appointment có phải khái niệm riêng với Visit không? Khi hoàn tất cần tạo hoặc cập nhật gì? |
| Trường bắt buộc | Pet, Veterinarian, ngày giờ, thời lượng và lý do/diễn giải nào bắt buộc? |
| Thời điểm bắt đầu | Lịch hẹn phải ở tương lai không? Dùng múi giờ nào để so sánh? |
| Thời lượng | Giá trị nào hợp lệ? Có giới hạn tối đa không? |
| Phạm vi xung đột | Trạng thái Appointment nào được tính? Xung đột theo Pet, Veterinarian hay cả hai? |
| Quy ước khoảng thời gian | Có cho phép hai lịch hẹn liền nhau nếu lịch trước kết thúc đúng lúc lịch sau bắt đầu không? |
| Đổi lịch | Trạng thái nào được đổi lịch? Khi kiểm tra có loại chính lịch hẹn đó khỏi đối chiếu không? |
| Vòng đời | Có những trạng thái nào và chuyển trạng thái nào được phép? |
| Hủy lịch | Trạng thái nào được hủy? Hủy có giải phóng khung giờ không? |
| Hoàn tất | Hoàn tất có tạo Visit không? Có thể tạo nhiều hơn một Visit không? Dữ liệu nào được chuyển tiếp? |
| Xóa | Có cho phép xóa cứng không, hay phải giữ lại bản ghi? |
| Danh sách lịch hẹn | Cần bộ lọc, thứ tự sắp xếp và phân trang nào? |
| Kết quả đặt lịch đồng thời | Nếu hai yêu cầu xung đột, kết quả nghiệp vụ nào được phép? |

Ví dụ tài liệu này không khẳng định hành vi PetClinic hiện tại. Khi review brownfield thật, cần khám phá và gắn nhãn hành vi đã kiểm chứng là bằng chứng **CURRENT_SYSTEM**.

## Quyết định Human minh họa được cung cấp sau đó

Các câu trả lời dưới đây thể hiện baseline ngữ nghĩa Appointment Scheduling được cung cấp. Đây là quyết định ví dụ, không phải kết luận agent được tự suy ra từ input ban đầu.

| Nhóm | Câu trả lời Human minh họa |
|---|---|
| Actor | Clinic Staff. |
| Appointment và Visit | Appointment là khái niệm riêng với Visit. |
| Trường bắt buộc | Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải. |
| Thời điểm bắt đầu | Phải sau thời điểm hiện tại; dùng múi giờ Asia/Ho_Chi_Minh. |
| Thời lượng | Lớn hơn 0. Thời lượng tối đa vẫn **UNKNOWN**. |
| Phạm vi xung đột | Chỉ Appointment ở trạng thái Scheduled của cùng Veterinarian mới xung đột. |
| Quy ước khoảng thời gian | Dùng khoảng nửa mở **[start, end)**; cho phép hai lịch hẹn chạm nhau. |
| Đổi lịch | Chỉ Appointment Scheduled mới được đổi lịch; loại chính Appointment đó khỏi kiểm tra xung đột. |
| Vòng đời | Scheduled, Cancelled, Completed. Khi tạo bắt đầu ở Scheduled. |
| Chỉnh sửa, hủy, hoàn tất | Chỉ Appointment Scheduled mới được chỉnh sửa, đổi lịch, hủy hoặc hoàn tất. |
| Hủy lịch | Hủy giải phóng khung giờ. |
| Hoàn tất | Hoàn tất tạo chính xác một Visit mới. |
| Xóa | Không xóa cứng. |
| Pet bị trùng lịch | Baseline được duyệt không cấm lịch hẹn của cùng Pet chồng lấn. |
| Đặt lịch đồng thời | Chỉ một Appointment không xung đột được lưu. Tính nguyên tử và locking là quyết định thiết kế kỹ thuật. |
| Danh sách lịch hẹn | Cần xem danh sách. Bộ lọc, sắp xếp và phân trang vẫn **UNKNOWN**. |

Với tính năng thật, ghi lại ai cung cấp từng câu trả lời và nguồn của câu trả lời. Nếu unknown nào ảnh hưởng trọng yếu tới bước kế tiếp, giữ nó ở trạng thái blocking và không tạo Engineering Handoff.

## Phân loại mục còn mở minh họa

Chỉ trong handoff fixture hợp lệ theo contract này, BA ví dụ phân loại thời lượng tối đa và chi tiết danh sách chưa rõ là không blocking cho việc bàn giao các quy tắc đã duyệt ở trên. Cả hai vẫn **UNKNOWN**; phân loại này không phê duyệt giới hạn thời lượng hay hành vi danh sách. Trong công việc thật, BA phải quyết định unknown nào chặn bước sau.
