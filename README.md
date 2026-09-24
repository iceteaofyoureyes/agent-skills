# Agent Skills và các Kit

Repository này cung cấp các **atomic Agent Skills** và các **role Kit** ghép workflow + capability cho từng giai đoạn AI-assisted SDLC.

Tiếng Việt là tài liệu chính.

## BA Kit là gì?

**BA Kit** hỗ trợ BA làm phần **WHAT — hệ thống cần làm gì**:

~~~text
BA input / Requirement / CR
→ review + current-system discovery khi cần
→ gap / clarification
→ Business Rules
→ canonical SRS
→ Draw.io / DOCX / optional prototype
→ Human approval
→ Engineering Handoff
~~~

Human BA vẫn sở hữu business decision, stakeholder/customer communication và approval.

## BA Kit làm được gì?

| Capability | Trạng thái |
|---|---|
| Requirement review / gap / ambiguity / edge-case analysis | Required |
| Brownfield current-system discovery | Required |
| Business Rule extraction | Required |
| Canonical functional SRS create/update | Required |
| Existing SRS/DOCX review/edit | Required |
| Word/DOCX delivery + project-provided template | Required |
| Editable Draw.io business diagrams | Required |
| Screenshot/image/PDF/visual evidence review | Workflow-supported khi runtime đọc được artifact |
| Direct Figma access | Phụ thuộc runtime connector/quyền; BA Kit không bundle connector |
| UX/task/state contract | Optional |
| Local UI prototype | Optional |
| Browser/visual/accessibility review | Optional |
| Engineering Handoff | Required workflow output |

Chi tiết: [Khả năng BA Kit](docs/vi/BA_KIT_CAPABILITIES.md).

## SRS template và DOCX

BA Kit quản lý **canonical functional SRS ở Markdown** và có capability xuất/edit DOCX.

RC1 hiện **không bundle SRS_TEMPLATE.docx mặc định**. Nếu công ty/project có Word template, cung cấp file .docx và chọn nó làm delivery template; template không được override business semantics.

Xem [SRS và DOCX](docs/vi/SRS_DOCX_GUIDE.md).

## Draw.io và visual workflow

BA Kit có thể tạo/edit file .drawio editable cho business process flowchart, swimlane, user/task flow, state/lifecycle và decision tree; có thể xuất PNG/SVG/PDF khi toolchain hỗ trợ.

Visual input như screenshot/Figma export/PDF/HTML prototype được dùng làm evidence và để tìm gap; hidden permission/validation/business rule vẫn cần Human xác nhận.

Xem [Draw.io, visual input và prototype](docs/vi/DIAGRAMS_PROTOTYPES.md).

## Các Kit

| Kit | Trạng thái | Phạm vi |
|---|---|---|
| **BA Kit** | RC1 candidate; runtime remediation đang diễn ra | **WHAT** |
| **Dev Kit** | Planned | Engineering Impact + **HOW** |
| **Test Kit** | Planned | **HOW DO WE PROVE IT** |

## Bắt đầu

1. [Hướng dẫn nhanh](docs/vi/BA_KIT_QUICKSTART.md)
2. [Khả năng BA Kit](docs/vi/BA_KIT_CAPABILITIES.md)
3. [Hướng dẫn sử dụng theo tình huống](docs/vi/BA_KIT_USAGE_GUIDE.md)
4. [Workflow và Human Gates](docs/vi/BA_KIT_WORKFLOW.md)
5. [Ví dụ CR-001](kits/ba/examples/CR-001/README.md)

## Cài BA Kit

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
/path/to/agent-skills/tooling/install.sh ba --agent codex --scope project
/path/to/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Xem [Cài đặt](docs/vi/INSTALLATION.md).

## Tài liệu chuyên sâu

- [SRS và DOCX](docs/vi/SRS_DOCX_GUIDE.md)
- [Draw.io, visual input và prototype](docs/vi/DIAGRAMS_PROTOTYPES.md)
- [Kiến trúc](docs/vi/ARCHITECTURE.md)
- [Nền tảng thiết kế & chuẩn tham chiếu](docs/vi/FOUNDATIONS.md)
- [Kit contract](docs/vi/KIT_CONTRACT.md)
- [Release status](docs/vi/RELEASE.md)
- [Provenance & licensing](docs/vi/PROVENANCE.md)

## Trạng thái hiện tại

Package/install/Doctor và BA Kit redistribution licensing đã có evidence tương ứng. Runtime preflight đã PASS, nhưng full CR-001 acceptance đầu tiên trả **BA_KIT_RC1_CHANGES_REQUIRED**; current HEAD chưa được final functional acceptance.

Whole repository publication vẫn bị chặn bởi một số non-BA imports/metadata chưa audit đầy đủ.

## English documentation

[BA Kit documentation — English](docs/en/README.md)
