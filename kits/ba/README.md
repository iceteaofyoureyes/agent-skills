# BA Kit packaging candidate

The manifest version follows the repository prerelease convention. This is not a stable release. BA Kit packages the VNext workflow runtime and keeps V1 artifacts available only through `LEGACY_COMPAT`.

**BA Kit** hỗ trợ BA làm phần **WHAT**: review đầu bài, discover current system, tìm gap, làm rõ requirement, tổng hợp BA Decisions, Business Rules (`BR-*`), canonical SRS (`FR-*`), chọn và validate baseline candidate, dừng tại `HUMAN_REVIEW` để chờ trusted host cung cấp approval receipt, rồi revalidate trước Engineering Handoff VNext.

BA Kit không thay BA trao đổi khách hàng và không quyết định target architecture/API/DB/ownership.

`workflow-state-vnext.json` là runtime progress, không phải business authority. `CONTINUE != APPROVE`; `ANSWER != APPROVE`; validator PASS, Foundation READY và UX approval không phê duyệt BA baseline. Project Foundation chỉ được consume với durable manifest, promotion provenance, Foundation approval receipt và trusted Foundation host authentication.

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

Repository không bundle SRS_TEMPLATE.docx. Canonical SRS là functional Markdown artifact; Word template là delivery source do project/Human cung cấp.

## Composition

[kits/ba/kit.yaml](kit.yaml) là canonical composition. Atomic skills nằm ở root repository; Skills Manager là optional adapter.

## Acceptance

[kits/ba/acceptance.yaml](acceptance.yaml) là acceptance contract. Tier 3 installed-runtime acceptance là bắt buộc để Phase 4 hoàn tất; Tier 1/Tier 2 không thể thay thế. Doctor READY chỉ xác nhận package capability, không xác nhận approval hay feature readiness.

Ví dụ CR-001 là documentation fixture, không phải runtime golden output được feed cho generator.

## Status

~~~text
BA_VNEXT_PACKAGING_CANDIDATE
~~~

Không có stable release được công bố.

English: [BA Kit documentation](../../docs/en/README.md)
