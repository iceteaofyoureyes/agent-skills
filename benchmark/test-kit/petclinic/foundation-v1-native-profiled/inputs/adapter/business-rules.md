# Separate approved business-rule context

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
