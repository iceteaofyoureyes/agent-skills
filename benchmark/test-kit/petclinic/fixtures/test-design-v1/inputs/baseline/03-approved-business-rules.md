# Business Rules đã duyệt — Ví dụ minh họa

Đây là đầu ra minh họa dựa trên câu trả lời Human riêng trong [02-gap-review.md](02-gap-review.md). Các quy tắc này không có trong yêu cầu ban đầu và không phải nội dung runtime cố định. ID ví dụ không bắt buộc.

| ID ví dụ | Quy tắc | Bằng chứng |
|---|---|---|
| BR-001 | Clinic Staff có thể quản lý Appointment. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-002 | Appointment là khái niệm riêng với Visit. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-003 | Appointment có Pet, Veterinarian, thời điểm bắt đầu, thời lượng và lý do/diễn giải. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-004 | Thời điểm bắt đầu phải sau hiện tại, tính theo Asia/Ho_Chi_Minh. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-005 | Thời lượng phải lớn hơn 0. Thời lượng tối đa là UNKNOWN. | Ngưỡng tối thiểu CONFIRMED; tối đa vẫn UNKNOWN. |
| BR-006 | Chỉ Appointment Scheduled của cùng Veterinarian mới được đối chiếu xung đột. Dùng khoảng nửa mở [start, end), nên lịch chạm nhau được phép. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-007 | Chỉ được đổi lịch khi Appointment ở Scheduled và loại chính Appointment đó khỏi kiểm tra xung đột. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-008 | Vòng đời gồm Scheduled, Cancelled, Completed. Khi tạo là Scheduled; chỉ Scheduled mới được chỉnh sửa, đổi lịch, hủy hoặc hoàn tất. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-009 | Hủy lịch giải phóng khung giờ. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-010 | Hoàn tất tạo chính xác một Visit mới. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-011 | Không xóa cứng Appointment. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-012 | Baseline được duyệt không cấm lịch Appointment của cùng Pet chồng lấn. | CONFIRMED trong bản ghi quyết định ví dụ. |
| BR-013 | Kết quả nghiệp vụ khi đặt đồng thời là chỉ lưu Appointment không xung đột. | CONFIRMED trong bản ghi quyết định; tính nguyên tử/locking nằm ngoài BA. |
| BR-014 | Cần xem Appointment. Bộ lọc, sắp xếp và phân trang vẫn UNKNOWN. | Việc xem là CONFIRMED; chi tiết còn lại của danh sách UNKNOWN. |

ID, thứ tự và câu chữ chỉ để minh họa. Với baseline BA thật, giữ tham chiếu nguồn và nhãn bằng chứng thực tế.
