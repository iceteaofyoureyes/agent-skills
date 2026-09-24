# Câu hỏi thường gặp về BA Kit

### Có cần Skills Manager không?

Không. BA Kit cài và chạy qua script của repository. Skills Manager là tùy chọn.

### Có cần biết tên từng skill không?

Không. Hãy yêu cầu kết quả BA bằng ngôn ngữ tự nhiên; workflow tự định tuyến nội bộ.

### BA Kit có viết mã production không?

Không. BA Kit chuẩn bị artifact Phân tích nghiệp vụ. Kit không triển khai thay đổi production và không quyết định thiết kế kỹ thuật hay ownership.

### BA Kit có thể tự động phê duyệt yêu cầu không?

Không. Kit có thể ghi nhận câu trả lời của Human và validation artifact, nhưng chỉ Human mới phê duyệt được artifact hoặc gate được nêu tên.

### “Tiếp tục” có nghĩa là phê duyệt không?

Không. Lệnh này tiếp tục workflow đã lưu tới hành động hợp lệ kế tiếp. Nó không trả lời câu hỏi đang mở hay phê duyệt artifact.

### BA Kit có dùng cho dự án brownfield không?

Có. Với yêu cầu brownfield, workflow có thể khám phá code, hành vi, dữ liệu, API và UI hiện tại rồi ghi nhận là bằng chứng **CURRENT_SYSTEM**.

### Nếu code hiện tại mâu thuẫn với SRS thì sao?

Ghi nhận chênh lệch. Quyết định BA đã xác nhận, Business Rules đã duyệt và SRS canonical cùng quản lý ý nghĩa nghiệp vụ; code hiện tại là bằng chứng về hành vi đang có. Workflow không âm thầm sửa một phía để che mâu thuẫn.

### Các ví dụ có phải template bắt buộc không?

Không. Chúng chỉ để minh họa. Câu chữ và ID mẫu không cố định; hãy tuân theo hợp đồng artifact thật và giữ tham chiếu nguồn bắt buộc.

### Sau Engineering Handoff sẽ thế nào?

Giai đoạn dự kiến kế tiếp là Engineering Impact, sau đó là Dev Kit và Spec Kit. Các khả năng này đang Planned, chưa được triển khai trong RC1.

### Test sẽ dùng đầu ra BA thế nào trong tương lai?

Test Kit và TEA dự kiến dùng BA baseline đã duyệt cùng bằng chứng kỹ thuật hạ nguồn để xác định và chứng minh hành vi mong đợi. Chúng chưa có trong BA Kit RC1.

### BA Kit đã public hoặc được runtime chấp nhận chưa?

Chưa. Đây là ứng viên RC1. Runtime acceptance cho package bị chặn bởi isolated provider/runtime; phân phối công khai bị chặn bởi provenance và giấy phép chưa được giải quyết. Xem [Trạng thái phát hành](RELEASE.md) và [Nguồn gốc](PROVENANCE.md).

---

English: [FAQ](../en/BA_KIT_FAQ.md)
