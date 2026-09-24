# BA Kit 1.0.0-rc.1

**BA Kit** (Bộ công cụ Phân tích nghiệp vụ) hỗ trợ làm rõ yêu cầu, phân loại bằng chứng, đặt câu hỏi, chuẩn bị **Business Rules** và **SRS**, rồi tạo **Engineering Handoff** sau khi Human phê duyệt rõ ràng. BA Kit sở hữu phần **WHAT** — hệ thống cần làm gì — chứ không quyết định thiết kế kỹ thuật hay ownership triển khai.

Đây là ứng viên RC1, chưa phải bản được chấp nhận hay phát hành công khai. Runtime functional acceptance cho package bị chặn bởi isolated provider/runtime. Xem [Trạng thái phát hành](../../docs/vi/RELEASE.md) và [Nguồn gốc](../../docs/vi/PROVENANCE.md).

## Bắt đầu

- [Hướng dẫn nhanh](../../docs/vi/BA_KIT_QUICKSTART.md)
- [Quy trình và Human Gate](../../docs/vi/BA_KIT_WORKFLOW.md)
- [Hướng dẫn sử dụng](../../docs/vi/BA_KIT_USAGE_GUIDE.md)
- [Ví dụ CR-001](examples/CR-001/README.md)
- [FAQ](../../docs/vi/BA_KIT_FAQ.md)
- [Cài đặt](../../docs/vi/INSTALLATION.md)

Nguồn duy nhất mô tả thành phần là [kit.yaml](kit.yaml). Package có một workflow entry skill **ba-workflow** cùng các skill canonical ở thư mục gốc. Skills Manager là tùy chọn.

## Bằng chứng acceptance

Xem [acceptance.yaml](acceptance.yaml) và [các probe CR-001](../../ba-workflow/evals/cr001-acceptance.md). Ví dụ tài liệu không phải bằng chứng runtime acceptance cho package. Không đưa các đầu ra CR-001 đã duyệt vào phiên fresh-session acceptance.

English: [BA Kit documentation](../../docs/en/README.md)
