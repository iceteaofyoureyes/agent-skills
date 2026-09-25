# Hợp đồng của Kit

- Một Kit gồm manifest/composition, workflow/orchestration contract và capability dependencies được pin rõ ràng.
- BA Kit hiện tham chiếu atomic skills canonical ở repository root.
- Kit mới có thể dùng **kit-scoped Agent Plugin payload** khi điều đó cần thiết để giữ exact upstream layout/resources; packaging mode phải được khai báo và provenance/Doctor phải kiểm chứng. Không được phụ thuộc ngầm vào user/global skills.
- Workflow, core, dependency bắt buộc và tùy chọn được định nghĩa một lần trong **kits/<id>/kit.yaml**.
- **ba-workflow** định tuyến công việc và giữ ranh giới trạng thái/phê duyệt; không lặp lại quy trình chi tiết của skill nguyên tử.
- **workflow-state.json** và **engineering-handoff.yml** được kiểm tra bằng script Python standard library. Cấu trúc bắt buộc sai, handoff chưa được duyệt, hash không khớp hoặc có trường ownership kỹ thuật bị cấm sẽ trả mã thoát khác 0.
- Thiếu capability tùy chọn tạo trạng thái **DEGRADED**; capability/hợp đồng bắt buộc phải đạt để **READY**.
- Không thêm placeholder giả vờ là capability đã triển khai. Dev Kit có thể tồn tại ở trạng thái design/assembly có nhãn rõ ràng (ví dụ `DESIGN_FROZEN_CANDIDATE`) trước runtime acceptance; trạng thái này không được mô tả là READY/RC.

---

English: [Kit contract](../en/KIT_CONTRACT.md)


## Dev Kit V1 contract extension

- Approved BA Baseline là authority cho WHAT; Dev Kit không tự mutate business semantics.
- Engineering Impact nằm trong Dev Kit và sở hữu WHERE / WHO OWNS, không sở hữu business WHAT.
- Default normal path phải bounded: planning → implementation → one consolidated review → one blocking-fix wave → fresh verification.
- Tối đa một scoped re-review, chỉ khi blocking fix materially thay đổi logic/risk; không fresh-review toàn feature lần hai.
- Conditional capability (security/API/performance/observability/debugging/code graph/analyze/converge) chỉ activate theo trigger/risk; **installed != invoked**.
- Benchmark mode phải fail khi có unrelated global methodology/plugin/hook contamination.
- Provenance/license/docs là release gate, không phải post-release polish.
