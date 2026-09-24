# Trạng thái phát hành

BA Kit **1.0.0-rc.1** là package release candidate, chưa phải bản phát hành công khai hay bản functional release đã được chấp nhận. Dev Kit và Test Kit đang Planned, chưa triển khai.

## Trạng thái kỹ thuật/package

Các kiểm tra package và installer đã đạt với Codex project install, cài lặp idempotent, Doctor **READY**, gỡ cài đặt an toàn và cô lập dự án. Generic PowerShell/Bash và cấu trúc cài Claude Code cũng đã được kiểm tra. Runtime Claude chưa được chạy. Các kiểm tra này xác nhận cấu trúc và hành vi cài đặt, không chứng minh workflow BA hoạt động trên runtime.

## Runtime functional acceptance

Fresh-session CR-001 acceptance cho package đang **BLOCKED** vì isolated Codex provider/runtime không trả lời. Đây là chặn do môi trường, không phải functional PASS. Không xem benchmark trước đây hay ví dụ tài liệu là acceptance của package này. Khi runtime cô lập có thể trả lời, chạy các case trong [kits/ba/acceptance.yaml](../../kits/ba/acceptance.yaml) và ghi chính xác runtime cùng kết quả.

## Phân phối công khai

Phân phối công khai đang **BLOCKED** cho tới khi giải quyết quyền sở hữu, giấy phép, nguồn và thông báo bắt buộc được đánh dấu **UNKNOWN** trong [PROVENANCE.md](PROVENANCE.md). Chưa mô tả repository là sẵn sàng phát hành công khai.

---

English: [Release status](../en/RELEASE.md)
