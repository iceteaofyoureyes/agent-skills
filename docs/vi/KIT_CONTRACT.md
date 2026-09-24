# Hợp đồng của Kit

- Một Kit gồm manifest, workflow entry skill và tham chiếu tới các skill nguyên tử canonical ở thư mục gốc.
- Workflow, core, dependency bắt buộc và tùy chọn được định nghĩa một lần trong **kits/<id>/kit.yaml**.
- **ba-workflow** định tuyến công việc và giữ ranh giới trạng thái/phê duyệt; không lặp lại quy trình chi tiết của skill nguyên tử.
- **workflow-state.json** và **engineering-handoff.yml** được kiểm tra bằng script Python standard library. Cấu trúc bắt buộc sai, handoff chưa được duyệt, hash không khớp hoặc có trường ownership kỹ thuật bị cấm sẽ trả mã thoát khác 0.
- Thiếu capability tùy chọn tạo trạng thái **DEGRADED**; capability/hợp đồng bắt buộc phải đạt để **READY**.
- Không thêm skill hoặc manifest placeholder cho Dev/Test trước khi các Kit đó được triển khai.

---

English: [Kit contract](../en/KIT_CONTRACT.md)
