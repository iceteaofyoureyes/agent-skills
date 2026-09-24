# Câu hỏi thường gặp về BA Kit

### BA Kit thực sự làm được những gì?

BA Kit review requirement, discover current system khi cần, tìm gap, hỗ trợ clarification, tổng hợp Business Rules, tạo/update SRS, tạo/edit DOCX, tạo/edit Draw.io business diagrams, hỗ trợ visual input và optional prototype, rồi tạo Engineering Handoff sau Human approval.

Xem [Khả năng BA Kit](BA_KIT_CAPABILITIES.md).

### Có cần Skills Manager không?

Không. Installer/Doctor của repository hoạt động độc lập. Skills Manager là tùy chọn.

### Có cần biết tên từng skill không?

Không. Hãy nói outcome cần làm; ba-workflow tự route capability.

### BA Kit có thay BA trao đổi khách hàng không?

Không. BA vẫn sở hữu elicitation, business decision, customer/stakeholder communication và approval.

### BA Kit có viết production code không?

Không. Optional prototype có thể tạo local UI code để review, nhưng đó là prototype/visual proposal, không phải production implementation.

### BA Kit có review current project không?

Có. Brownfield mode dùng codebase-discovery khi current behavior liên quan. Kết quả là CURRENT_SYSTEM evidence; không tự trở thành target requirement.

### BA Kit có đọc Figma không?

BA Kit không bundle Figma connector. Nếu runtime có Figma integration và Human cấp quyền, có thể dùng trực tiếp. Nếu không, export screenshot/image/PDF/HTML/local artifact để review.

### Từ screenshot agent có được tự ghi rule vào SRS không?

Không. Agent có thể ghi điều **quan sát được**, tìm mismatch/gap và hỏi BA. Permission, validation, hidden flow và business side effect cần Human confirmation.

### BA Kit dùng SRS template nào?

Canonical SRS hiện theo functional SRS contract và được quản lý ở Markdown; không có một Markdown form cố định cho mọi feature.

RC1 production repo **không bundle SRS_TEMPLATE.docx mặc định**.

### Có tạo SRS theo template Word công ty được không?

Có. Cung cấp file .docx và nói rõ nó là delivery template. document-docx hỗ trợ template rendering/structural editing.

Template điều khiển layout/section; nó không được override confirmed semantics.

Xem [SRS và DOCX](SRS_DOCX_GUIDE.md).

### Nếu không có Word template thì sao?

Có thể tạo generic DOCX từ canonical SRS để review, nhưng không gọi đó là “theo template công ty”.

### Nếu project chỉ có SRS.docx cũ thì sao?

Có thể dùng document-only mode để review/edit. Khi canonical Markdown đã tồn tại, semantic change phải cập nhật canonical source trước rồi đồng bộ DOCX.

### BA Kit vẽ Draw.io được những gì?

Trong BA scope: process flowchart, swimlane, user/task flow, state/lifecycle, decision tree, business context/interaction map, review/edit existing .drawio và dựng lại diagram từ image/whiteboard.

drawio-skill còn có nhiều technical capability, nhưng BA Kit không dùng nó để tự thiết kế target architecture/API/DB.

### Draw.io xuất được PNG/PDF không?

Có khi môi trường có draw.io CLI. Editable .drawio là source; PNG/SVG/PDF là derivative output.

### Diagram có thể trở thành source of truth không?

Không cho business semantics. Diagram phản ánh approved BR/SRS. Nếu diagram làm lộ một rule mới, đưa rule đó về PROPOSED/UNKNOWN và hỏi Human.

### BA Kit có tạo prototype không?

Có ở mức optional capability khi các UX/UI skills được cài. Prototype là visual proposal, cần Human visual review và không tự thay đổi Business Rules.

### Các ví dụ có phải template bắt buộc không?

Không. Ví dụ CR-001 minh họa artifact chain và Human Gate. Câu chữ/ID không phải output golden. Hãy theo contract và authority của feature thật.

### “Tiếp tục” có nghĩa là phê duyệt không?

Không.

~~~text
CONTINUE != APPROVE
ANSWER != APPROVE
~~~

### BA Kit có thể tự approve requirement/SRS không?

Không. Agent validation chỉ là evidence. Approval phải đến từ Human và gắn với artifact/revision cụ thể.

### Nếu code hiện tại mâu thuẫn SRS thì sao?

Ghi discrepancy. CURRENT_SYSTEM là as-is evidence; Confirmed Decisions + Approved BR + Canonical SRS quản lý target business meaning. Không silently sửa một bên để khớp bên kia.

### Sau Engineering Handoff là gì?

Engineering Impact — xác định WHERE / WHO OWNS. Sau đó mới tới Dev Kit + repo-local Spec Kit cho HOW.

### Runtime RC1 hiện PASS chưa?

Chưa. BA Kit 1.0.0-rc.1 là Public Preview và chưa được chấp nhận hoàn toàn. Đã thực hiện kiểm tra thủ công cho Requirement, Business Rules, SRS và Draw.io; validation thủ công cuối cùng cho DOCX và validation cuối cùng cho approval/handoff vẫn đang chờ. Lần chạy full CR-001 đầu tiên trả **BA_KIT_RC1_CHANGES_REQUIRED** và chỉ là evidence lịch sử tìm lỗi, không phải final acceptance.

### License BA Kit đã ổn chưa?

Payload BA Kit là **BA_KIT_LICENSE_READY** cho bản phân phối Public Preview đã được tuyển chọn này.

---

English: [FAQ](../en/BA_KIT_FAQ.md)
