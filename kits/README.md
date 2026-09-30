# Các Kit

Kit kết hợp workflow theo vai trò với các skill có thể tái sử dụng; skill nguyên tử được lưu canonical ở thư mục gốc.

| Kit | Trạng thái | Hướng dẫn |
|---|---|---|
| BA Kit | **1.0.0-rc.1 Public Preview** | [BA Kit](ba/README.md) |
| Dev Kit | Planned; chưa triển khai | — |
| Test Kit | Test Kit V1 Core, XMind Projection V1 và Excel Projection V1 **đã được Human chấp nhận như framework capabilities** | [Test Kit V1 status](../docs/design/test-kit-v1/README.md) |

Human acceptance áp dụng cho framework capabilities; điều đó không phê duyệt Test Design, Testcases hoặc Testware được tạo ra để dùng trong production. PetClinic hiện vẫn bị chặn bởi các execution dependency trọng yếu chưa được giải quyết.

Bắt đầu với [Hướng dẫn nhanh BA Kit](../docs/vi/BA_KIT_QUICKSTART.md), sau đó xem [Quy trình và Human Gate](../docs/vi/BA_KIT_WORKFLOW.md), [ví dụ CR-001](ba/examples/CR-001/README.md) và [Cài đặt](../docs/vi/INSTALLATION.md). Thành phần dùng chung được ghép qua manifest của BA Kit.

English: [Kit documentation](../docs/en/README.md)

## Test Kit V1

Install Test Kit independently with `tooling/install.ps1 -Kit test`. See [operator prerequisites, workflow, Human Gates, optional projections, upgrades, and removal](test/README.md). The Test Kit composition and explicit runtime file list are in [kits/test/kit.yaml](test/kit.yaml).
