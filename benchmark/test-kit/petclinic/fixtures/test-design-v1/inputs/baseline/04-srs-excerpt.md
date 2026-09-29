# Trích đoạn SRS — Ví dụ minh họa

Trích đoạn này minh họa truy vết từ yêu cầu tới Business Rules. ID và câu chữ là ví dụ, không phải đầu ra runtime bắt buộc.

| ID yêu cầu ví dụ | Yêu cầu | Truy vết |
|---|---|---|
| FR-001 | Clinic Staff có thể tạo Appointment với Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải. Appointment hợp lệ bắt đầu ở trạng thái Scheduled. Thời điểm bắt đầu phải sau hiện tại theo Asia/Ho_Chi_Minh; thời lượng phải lớn hơn 0. | BR-001, BR-003, BR-004, BR-005, BR-008 |
| FR-002 | Appointment Scheduled không được chồng lấn Appointment Scheduled khác của cùng Veterinarian. Dùng khoảng [start, end); cho phép lịch chạm nhau. | BR-006 |
| FR-003 | Clinic Staff chỉ được chỉnh sửa hoặc đổi lịch Appointment khi trạng thái là Scheduled. Khi đổi lịch, kiểm tra xung đột loại chính Appointment đang đổi khỏi đối chiếu. | BR-007, BR-008 |
| FR-004 | Clinic Staff chỉ được hủy Appointment khi trạng thái là Scheduled. Hủy giải phóng khung giờ; không xóa cứng Appointment. | BR-008, BR-009, BR-011 |
| FR-005 | Clinic Staff chỉ được hoàn tất Appointment khi trạng thái là Scheduled. Hoàn tất tạo chính xác một Visit mới và chuyển Appointment sang Completed. | BR-002, BR-008, BR-010 |
| FR-006 | Clinic Staff có thể xem Appointment. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định. | BR-001, BR-014 |

## Ngoài phạm vi kỹ thuật của BA

SRS này không chọn repository/module, API hay event schema, thiết kế database, service boundary, locking, transaction hoặc cơ chế triển khai đặt lịch đồng thời. Engineering Impact và công việc kỹ thuật hạ nguồn đưa ra các quyết định đó trong khi giữ nguyên kết quả nghiệp vụ đã duyệt.

Thời lượng Appointment tối đa là UNKNOWN. Không tự đặt giới hạn và không xem trích đoạn này là đã giải quyết câu hỏi đó.
