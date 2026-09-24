# Agent Skills và các Kit

Repository này cung cấp các skill có thể tái sử dụng và các Kit theo vai trò. Mỗi Kit ghép một workflow với những skill và công cụ cho một giai đoạn công việc; skill nguyên tử vẫn được lưu canonical ở thư mục gốc.

## Các Kit

| Kit | Trạng thái | Phạm vi |
|---|---|---|
| **BA Kit** | Có package ứng viên RC1; functional acceptance đang bị chặn | Hỗ trợ BA xác định **WHAT** — hệ thống cần làm gì — và chuẩn bị BA baseline được Human phê duyệt. |
| **Dev Kit** | Planned; chưa triển khai | Công việc kỹ thuật ở giai đoạn sau Engineering Impact. |
| **Test Kit** | Planned; chưa triển khai | Kiểm chứng ở giai đoạn sau với TEA. |

BA Kit chưa được chấp nhận hay phát hành công khai. Runtime acceptance bị chặn bởi isolated provider/runtime; phân phối công khai bị chặn bởi vấn đề giấy phép/provenance. Xem [Trạng thái phát hành](docs/vi/RELEASE.md) và [Nguồn gốc](docs/vi/PROVENANCE.md).

## Cài BA Kit

Từ thư mục dự án nơi bạn muốn dùng Kit, gọi script trong bản clone của repository. Chạy **Doctor** (lệnh kiểm tra cài đặt) sau khi cài. Thay đường dẫn ví dụ bằng vị trí thực tế:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
/path/to/agent-skills/tooling/install.sh ba --agent codex --scope project
/path/to/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Xem [Cài đặt](docs/vi/INSTALLATION.md) để biết Codex user scope, Claude Code, generic target và lệnh gỡ cài đặt.

## Mới dùng BA Kit?

1. [Hướng dẫn nhanh](docs/vi/BA_KIT_QUICKSTART.md)
2. [Quy trình và Human Gate](docs/vi/BA_KIT_WORKFLOW.md)
3. [Ví dụ CR-001](kits/ba/examples/CR-001/README.md)
4. [Cài đặt](docs/vi/INSTALLATION.md)
5. [Câu hỏi thường gặp](docs/vi/BA_KIT_FAQ.md)

## Tài liệu tham khảo

- [Hướng dẫn sử dụng](docs/vi/BA_KIT_USAGE_GUIDE.md)
- [Tổng quan kiến trúc](docs/vi/ARCHITECTURE.md)
- [Hợp đồng Kit](docs/vi/KIT_CONTRACT.md)
- [Nguồn gốc và giấy phép](docs/vi/PROVENANCE.md)
- [Trạng thái phát hành](docs/vi/RELEASE.md)

## English documentation

Tài liệu tiếng Anh là bản thứ cấp tương đương: [BA Kit documentation](docs/en/README.md).
