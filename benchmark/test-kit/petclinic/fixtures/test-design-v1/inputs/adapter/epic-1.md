# Epic 1 — CR-001 Appointment Scheduling

## Acceptance criteria

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
