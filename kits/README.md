# Các Kit

Kit kết hợp workflow theo vai trò với các skill có thể tái sử dụng; skill nguyên tử được lưu canonical ở thư mục gốc.

| Kit | Trạng thái | Hướng dẫn |
|---|---|---|
| BA Kit | **1.0.0-rc.1 Public Preview** | [BA Kit](ba/README.md) |
| Dev Kit | Planned; chưa triển khai | — |
| Test Kit V1.1 | V1 core, XMind, Excel, package và Project Customization & Policy Layer **đã được Human chấp nhận**; manifest `1.1.0`, chưa public release/tag | [Test Kit](test/README.md) · [Quick Start](../docs/vi/TEST_KIT_QUICKSTART.md) · [Customization](../docs/vi/TEST_KIT_CUSTOMIZATION.md) |

Human acceptance của framework không phê duyệt Test Design, Testcases hoặc Testware của một project. Production Case Gate vẫn cần receipt Human đã xác thực và không còn material OPEN execution dependency.

Bắt đầu với [BA Quick Start](../docs/vi/BA_KIT_QUICKSTART.md) hoặc [Test Quick Start](../docs/vi/TEST_KIT_QUICKSTART.md). Test Kit có [customization](../docs/vi/TEST_KIT_CUSTOMIZATION.md), [khả năng](../docs/vi/TEST_KIT_CAPABILITIES.md), [tình huống](../docs/vi/TEST_KIT_USAGE_GUIDE.md), [workflow/Human Gates](../docs/vi/TEST_KIT_WORKFLOW.md), [CR-001 example](test/examples/CR-001/README.md) và [cài đặt](../docs/vi/INSTALLATION.md).

English: [Kit documentation](../docs/en/README.md)

## Test Kit V1.1

Install Test Kit independently with `tooling/install.ps1 test --agent codex --scope project`. Its [manifest](test/kit.yaml) lists the exact installed assets. The packaged [operator README](test/README.md) remains part of the accepted package payload; detailed onboarding lives in the linked guides above.
