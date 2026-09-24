# Quy trình BA Kit và Human Gate

Sơ đồ mô tả luồng thường dùng cho dự án brownfield. Yêu cầu greenfield hoặc chỉ làm tài liệu bắt đầu ở giai đoạn phù hợp sớm nhất.

~~~mermaid
flowchart TD
    A[Requirement] --> B[Khám phá hệ thống hiện tại]
    B --> C[Rà soát khoảng trống yêu cầu]
    C --> D[Human làm rõ]
    D --> E[Business Rules]
    E --> F[SRS]
    F --> G[Human phê duyệt]
    G --> H[Engineering Handoff]
    H -. Planned .-> I[Engineering Impact]
    I -. Planned .-> J[Dev Kit + Spec Kit]
    J -. Planned .-> K[Test Kit + TEA]
~~~

## Các giai đoạn

| Giai đoạn | Nội dung |
|---|---|
| Requirement | Xác định tính năng, kết quả mong muốn và tài liệu nguồn hiện có. |
| Khám phá hệ thống hiện tại | Với brownfield, kiểm tra code, hành vi, dữ liệu, API hoặc UI liên quan. Ghi nhận phát hiện là **CURRENT_SYSTEM**; hành vi hiện tại là bằng chứng, không tự động trở thành yêu cầu mới. |
| Rà soát khoảng trống yêu cầu | Tìm điểm mơ hồ, thiếu, mâu thuẫn và câu hỏi trọng yếu. Giữ nguyên các mục chưa biết. |
| Human làm rõ | BA/stakeholder có thẩm quyền trả lời câu hỏi được nêu rõ. Ghi nguồn của mỗi câu trả lời. |
| Business Rules | Rút ra quy tắc có thể truy vết từ câu trả lời đã xác nhận; giữ riêng **UNKNOWN**, **INFERRED** và **PROPOSED**. |
| SRS | Soạn tài liệu yêu cầu chuẩn từ quyết định đã xác nhận và Business Rules được duyệt. Giữ hiển thị các mục còn mở. |
| Human phê duyệt | Human phê duyệt, từ chối hoặc yêu cầu sửa một artifact/gate được nêu tên. Kiểm tra của agent chỉ là bằng chứng, không thay phê duyệt. |
| Engineering Handoff | Sau phê duyệt rõ ràng và khi không còn mục blocking, đóng gói baseline đã duyệt, đường dẫn/hash nguồn, mục còn mở, chính sách hạ nguồn và giai đoạn kế tiếp. |

## Nhãn bằng chứng

| Nhãn | Ý nghĩa |
|---|---|
| **CONFIRMED** | Được Human có thẩm quyền nói trực tiếp hoặc quyết định. |
| **CURRENT_SYSTEM** | Hành vi đã kiểm chứng của hệ thống hiện tại. |
| **INFERRED** | Kết luận suy ra từ bằng chứng nhưng chưa được xác nhận trực tiếp. |
| **PROPOSED** | Hành vi được đề xuất, đang chờ xác nhận. |
| **UNKNOWN** | Thiếu bằng chứng, có mâu thuẫn hoặc chưa kiểm tra. |

Không biến hành vi hiện tại, ảnh chụp màn hình, prototype hay suy luận thành yêu cầu nếu BA chưa xác nhận.

## Human Gate

**Human Gate** (điểm chốt để Human quyết định tiếp tục, trả lời, phê duyệt, từ chối hoặc yêu cầu sửa artifact) cần được đặt khi thông tin thiếu có thể làm thay đổi quy tắc nghiệp vụ, actor/quyền, dữ liệu bắt buộc, validation, vòng đời, kết quả xung đột, hành vi phá hủy, nguồn ngữ nghĩa hoặc artifact đích.

- **Continue** tiếp tục từ trạng thái đã ghi. **“Tiếp tục” không phải phê duyệt.**
- **Answer** chỉ giải quyết câu hỏi được nêu tên. Câu trả lời không phê duyệt SRS hay artifact khác.
- **Approve**, **Reject** và **Request Changes** áp dụng cho artifact/gate được nêu rõ.
- Trả lời hết câu hỏi blocking có thể hoàn thành gate làm rõ câu hỏi. Gate phê duyệt artifact vẫn cần Human phê duyệt rõ artifact đó.
- Chỉ tạo Engineering Handoff sau khi BA baseline được phê duyệt rõ ràng và không còn mục blocking.

## Thẩm quyền nguồn

Ý nghĩa nghiệp vụ được quản lý đồng thời bởi:

1. quyết định BA đã xác nhận;
2. Business Rules đã duyệt;
3. SRS canonical.

Ba nguồn phải nhất quán. Quyết định mới hơn không tự động cập nhật artifact dẫn xuất cũ. Hành vi hệ thống hiện tại được ghi nhận riêng và không ghi đè ngữ nghĩa nghiệp vụ đã duyệt. Ảnh, prototype, sơ đồ, DOCX sinh ra hay artifact trình bày khác cũng không tự đổi ngữ nghĩa.

## Ranh giới sau BA

| Công việc | Trách nhiệm | Trạng thái |
|---|---|---|
| BA Kit | **WHAT** — hệ thống cần làm gì | Ứng viên RC1 |
| Engineering Impact (phân tích tác động kỹ thuật) | **WHERE** — công việc thuộc đâu; **WHO** — ai sở hữu | Planned; chưa triển khai |
| Dev Kit + Spec Kit (Bộ công cụ đặc tả) | **HOW** — thiết kế và xây dựng thế nào | Planned; chưa triển khai |
| Test Kit + TEA (khả năng kiểm thử hạ nguồn) | **HOW DO WE PROVE IT** — chứng minh thế nào | Planned; chưa triển khai |

BA Kit không phân công repository/module, API, schema DB/event, locking, transaction, service boundary hay người sở hữu triển khai. Các quyết định đó thuộc giai đoạn sau. Xem [Kiến trúc](ARCHITECTURE.md), [Hướng dẫn sử dụng](BA_KIT_USAGE_GUIDE.md) và [ví dụ CR-001](../../kits/ba/examples/CR-001/README.md).

---

English: [Workflow and Human Gates](../en/BA_KIT_WORKFLOW.md)
