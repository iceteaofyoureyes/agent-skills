# BA Kit 1.0.0-rc.1

**BA Kit** hỗ trợ BA làm phần **WHAT**: review đầu bài, discover current system, tìm gap, làm rõ requirement, tổng hợp Business Rules, tạo/update SRS, tạo Draw.io/DOCX/optional prototype và tạo Engineering Handoff sau Human approval.

BA Kit không thay BA trao đổi khách hàng và không quyết định target architecture/API/DB/ownership.

## Capability

Required:

- requirement interrogation/gap/quality review;
- codebase discovery;
- Business Rules;
- functional SRS;
- DOCX;
- Draw.io;
- workflow state / Human Gate / handoff.

Optional:

- product-design-and-ux;
- frontend-design;
- impeccable;
- playwright;
- web-accessibility.

Xem [Khả năng BA Kit](../../docs/vi/BA_KIT_CAPABILITIES.md).

## Bắt đầu

- [Quick Start](../../docs/vi/BA_KIT_QUICKSTART.md)
- [Usage Guide](../../docs/vi/BA_KIT_USAGE_GUIDE.md)
- [Workflow/Human Gates](../../docs/vi/BA_KIT_WORKFLOW.md)
- [SRS/DOCX](../../docs/vi/SRS_DOCX_GUIDE.md)
- [Draw.io/Visual/Prototype](../../docs/vi/DIAGRAMS_PROTOTYPES.md)
- [CR-001 example](examples/CR-001/README.md)
- [Installation](../../docs/vi/INSTALLATION.md)

## Template policy

RC1 không bundle SRS_TEMPLATE.docx. Canonical SRS là functional Markdown artifact; Word template là delivery source do project/Human cung cấp.

## Composition

[kits/ba/kit.yaml](kit.yaml) là canonical composition. Atomic skills nằm ở root repository; Skills Manager là optional adapter.

## Acceptance

[kits/ba/acceptance.yaml](acceptance.yaml) mô tả release acceptance. BA Kit **1.0.0-rc.1 Public Preview** đã được kiểm tra thủ công cho Requirement, Business Rules, SRS và Draw.io. Validation thủ công cuối cùng cho DOCX và validation cuối cùng cho approval/handoff vẫn đang chờ; RC1 chưa được chấp nhận hoàn toàn. Lần chạy runtime CR-001 đầu tiên từng trả **BA_KIT_RC1_CHANGES_REQUIRED** và là evidence lịch sử.

Ví dụ CR-001 là documentation fixture, không phải runtime golden output được feed cho generator.

## Status

~~~text
BA_KIT_LICENSE_READY
~~~

Xem [Release status](../../docs/vi/RELEASE.md).

English: [BA Kit documentation](../../docs/en/README.md)
