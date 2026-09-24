# Trạng thái phát hành

BA Kit 1.0.0-rc.1 là package release candidate, chưa phải bản phát hành công khai hay bản functional release đã được chấp nhận. Dev Kit và Test Kit đang Planned, chưa triển khai.

## Trạng thái kỹ thuật/package

Các kiểm tra package và installer đã đạt với Codex project install, cài lặp idempotent, Doctor READY, gỡ cài đặt an toàn và cô lập dự án. Generic PowerShell/Bash và cấu trúc cài Claude Code cũng đã được kiểm tra. Runtime Claude chưa được chạy. Các kiểm tra này xác nhận cấu trúc và hành vi cài đặt, không chứng minh workflow BA hoạt động trên runtime.

## Runtime functional acceptance

Fresh-session CR-001 acceptance cho package đang **BLOCKED** vì isolated Codex provider/runtime không trả lời. Đây là chặn do môi trường, không phải functional PASS. Không xem benchmark trước đây hay ví dụ tài liệu là acceptance của package này. Khi runtime cô lập có thể trả lời, chạy các case trong [kits/ba/acceptance.yaml](../../kits/ba/acceptance.yaml) và ghi chính xác runtime cùng kết quả.

## Trạng thái quyền phân phối

Trạng thái license của payload BA Kit là **BA_KIT_LICENSE_READY**. Mọi skill required, core và optional được installer phân phối đã có provenance đã xác minh cùng license hoặc ghi công cần thiết. Trạng thái này không có nghĩa runtime functional acceptance đã đạt.

Trạng thái công bố toàn repository là **REPO_PUBLICATION_BLOCKED**. Các import ngoài BA vẫn cần kiểm toán nội dung và license theo revision; metadata .skills-manager đang được track cũng cần quyết định về ownership/license hoặc phạm vi công bố. Không mô tả repository là sẵn sàng phát hành công khai trước khi giải quyết các blocker này.

---

English: [Release status](../en/RELEASE.md)
