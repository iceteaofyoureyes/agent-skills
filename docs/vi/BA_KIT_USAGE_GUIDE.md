# Hướng dẫn sử dụng BA Kit

Dùng ngôn ngữ tự nhiên trong dự án đã cài BA Kit. Bạn không cần gọi tên skill. Prompt bên dưới minh họa ý định; câu chữ và ID artifact không cố định.

## Bắt đầu rà soát

~~~text
Review requirement này giúp tôi.
~~~

Với dự án brownfield:

~~~text
Review requirement này. Trước khi kết luận hãy discover current system và chỉ ra các điểm còn thiếu hoặc chưa rõ.
~~~

Khi cần, workflow xem xét hệ thống hiện tại, gắn nhãn bằng chứng và nêu câu hỏi còn mở. Yêu cầu review chỉ đọc, không sửa artifact.

## Tiếp tục nhưng không phê duyệt

~~~text
Tiếp tục.
~~~

Lệnh này tiếp tục từ giai đoạn đã lưu và thực hiện hành động hợp lệ kế tiếp. Nó không trả lời câu hỏi đang mở và không phê duyệt artifact.

## Hỏi về mục còn mở

~~~text
Còn gap nào blocking?
~~~

Workflow cần nêu rõ khoảng trống blocking và giữ lại các mục chưa giải quyết nhưng không blocking.

## Trả lời câu hỏi

Trả lời trực tiếp câu hỏi được nêu tên, ví dụ:

~~~text
Rule conflict chỉ áp dụng cho Appointment ở trạng thái Scheduled của cùng Veterinarian; hai khoảng thời gian chạm nhau thì được phép.
~~~

Đây là câu trả lời minh họa cho CR-001. Chỉ dùng nếu đó thực sự là quyết định của BA có thẩm quyền. Câu trả lời chỉ giải quyết câu hỏi đó, không phê duyệt các artifact khác.

## Tổng hợp quy tắc đã xác nhận

~~~text
Tổng hợp lại các Business Rules đã confirmed, giữ riêng các mục UNKNOWN.
~~~

Kiểm tra quy tắc có trích nguồn và phân biệt quyết định đã xác nhận với bằng chứng từ hệ thống hiện tại.

## Tạo SRS

~~~text
Viết SRS từ baseline đã xác nhận.
~~~

SRS phải dựa trên quyết định đã xác nhận và Business Rules được duyệt, giữ traceability và nêu rõ mục còn chưa giải quyết.

## Phê duyệt baseline rõ ràng

Sau khi xem các artifact và revision được nêu tên, có thể phê duyệt rõ như sau:

~~~text
Tôi phê duyệt Business Rules revision BR-<revision> và SRS revision SRS-<revision> làm BA baseline cho Engineering.
~~~

Thay revision ví dụ bằng revision bất biến thực tế. Chỉ gửi câu này khi bạn thực sự muốn phê duyệt đúng các artifact đó. Workflow không suy diễn phê duyệt từ **“Tiếp tục”**, việc trả lời đủ câu hỏi hay kết quả validation thành công.

## Tạo Engineering Handoff

Sau khi phê duyệt rõ ràng và giải quyết mọi mục blocking:

~~~text
Tạo Engineering Handoff.
~~~

Handoff ghi BA baseline đã duyệt, đường dẫn/hash SHA-256 của nguồn, mục còn mở, chính sách hạ nguồn và bước kế tiếp. Handoff không chỉ định repository, module, frontend/backend owner, API/DB, locking hoặc transaction. Xem [hợp đồng handoff](../../ba-workflow/references/engineering-handoff.md) và [provenance](PROVENANCE.md).

## Ví dụ và hợp đồng

[Ví dụ CR-001](../../kits/ba/examples/CR-001/README.md) minh họa một luồng từ input chưa đầy đủ tới handoff. Đây không phải transcript golden: câu chữ và ID mẫu không bắt buộc trừ khi hợp đồng thật yêu cầu. Hãy theo hợp đồng artifact và giữ provenance thay vì cố khớp văn mẫu.

---

English: [Usage Guide](../en/BA_KIT_USAGE_GUIDE.md)
