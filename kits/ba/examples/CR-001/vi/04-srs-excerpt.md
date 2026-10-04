# Trích đoạn SRS — Ví dụ minh họa

Trích đoạn này minh họa truy vết từ yêu cầu tới Business Rules. ID và câu chữ là ví dụ, không phải đầu ra runtime bắt buộc.

| ID yêu cầu ví dụ | Yêu cầu | Truy vết |
|---|---|---|
| FR-001 | Service Staff có thể tạo Resource Request với Resource, Coordinator, thời điểm bắt đầu, thời lượng và lý do/diễn giải. Resource Request hợp lệ bắt đầu ở trạng thái Scheduled. Thời điểm bắt đầu phải sau hiện tại theo Asia/Ho_Chi_Minh; thời lượng phải lớn hơn 0. | BR-001, BR-003, BR-004, BR-005, BR-008 |
| FR-002 | Resource Request Scheduled không được chồng lấn Resource Request Scheduled khác của cùng Coordinator. Dùng khoảng [start, end); cho phép lịch chạm nhau. | BR-006 |
| FR-003 | Service Staff chỉ được chỉnh sửa hoặc đổi lịch Resource Request khi trạng thái là Scheduled. Khi đổi lịch, kiểm tra xung đột loại chính Resource Request đang đổi khỏi đối chiếu. | BR-007, BR-008 |
| FR-004 | Service Staff chỉ được hủy Resource Request khi trạng thái là Scheduled. Hủy giải phóng khung giờ; không xóa cứng Resource Request. | BR-008, BR-009, BR-011 |
| FR-005 | Service Staff chỉ được hoàn tất Resource Request khi trạng thái là Scheduled. Hoàn tất tạo chính xác một Fulfillment Record mới và chuyển Resource Request sang Completed. | BR-002, BR-008, BR-010 |
| FR-006 | Service Staff có thể xem Resource Request. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN, chờ BA quyết định. | BR-001, BR-014 |

## Ngoài phạm vi kỹ thuật của BA

SRS này không chọn repository/module, API hay event schema, thiết kế database, service boundary, locking, transaction hoặc cơ chế triển khai gửi yêu cầu đồng thời. Engineering Impact và công việc kỹ thuật hạ nguồn đưa ra các quyết định đó trong khi giữ nguyên kết quả nghiệp vụ đã duyệt.

Thời lượng Resource Request tối đa là UNKNOWN. Không tự đặt giới hạn và không xem trích đoạn này là đã giải quyết câu hỏi đó.
