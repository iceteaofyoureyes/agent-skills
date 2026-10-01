# Agent Skills Kits

Repository này dành cho **Agent Skills Kits**: các skill nguyên tử có thể tái sử dụng và các Kit kết hợp chúng thành workflow theo vai trò cho từng giai đoạn AI-assisted SDLC.

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

## Test Kit V1.1 là gì?

**Test Kit V1.1** hỗ trợ tester làm phần **HOW DO WE PROVE IT** từ BA baseline đã duyệt. V1.1 giữ nguyên workflow/gate của V1 và bổ sung project-owned testing policy có snapshot/hash để hướng dẫn agent theo convention của từng project:

~~~text
Approved BA Baseline → TEA analysis → Canonical Test Design
→ Human Design Gate → Canonical manual Testcases
→ Human Case Gate → APPROVED_TESTWARE → STOP_V1
~~~

XMind và Excel là bản chiếu tùy chọn từ canonical artifacts, không phải nguồn chuẩn. V1.1 thêm [Project Customization & Policy](docs/vi/TEST_KIT_CUSTOMIZATION.md): rule project chỉ là non-authoritative testing guidance, không override BA/Design/execution authority. Test Kit không sinh/chạy Playwright/API automation; execution, evidence và triage thuộc Automation Test V2. Xem [README đi cùng package](kits/test/README.md), rồi bắt đầu tại [Test Kit Quick Start](docs/vi/TEST_KIT_QUICKSTART.md), [customization](docs/vi/TEST_KIT_CUSTOMIZATION.md), [khả năng](docs/vi/TEST_KIT_CAPABILITIES.md), [tình huống sử dụng](docs/vi/TEST_KIT_USAGE_GUIDE.md), [workflow/Human Gates](docs/vi/TEST_KIT_WORKFLOW.md) và [ví dụ CR-001](kits/test/examples/CR-001/README.md).

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
| **BA Kit** | **1.0.0-rc.1 Public Preview** | **WHAT** |
| **Dev Kit** | Planned | Engineering Impact + **HOW** |
| **Test Kit V1.1** | V1 core + XMind/Excel + Packaging + Project Customization & Policy Layer **Human accepted**; manifest `1.1.0`, chưa có public release/tag | **HOW DO WE PROVE IT** |

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

## Cài Test Kit V1.1

Chạy từ project Codex với Python 3.10+ và Codex CLI:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
~~~

BA Kit và Test Kit có thể cùng cài. Xem [hướng dẫn cài cả hai Kit](docs/vi/INSTALLATION.md).

## Tài liệu chuyên sâu

- [SRS và DOCX](docs/vi/SRS_DOCX_GUIDE.md)
- [Draw.io, visual input và prototype](docs/vi/DIAGRAMS_PROTOTYPES.md)
- [Kiến trúc](docs/vi/ARCHITECTURE.md)
- [Nền tảng thiết kế & chuẩn tham chiếu](docs/vi/FOUNDATIONS.md)
- [Kit contract](docs/vi/KIT_CONTRACT.md)
- [Release status](docs/vi/RELEASE.md)
- [Provenance & licensing](docs/vi/PROVENANCE.md)

## Trạng thái hiện tại

Đã thực hiện kiểm tra thủ công cho Requirement, Business Rules, SRS và Draw.io. Việc validation thủ công cuối cùng cho DOCX và validation cuối cùng cho approval/handoff vẫn đang chờ. BA Kit 1.0.0-rc.1 là Public Preview, chưa được chấp nhận hoàn toàn.



## English documentation

[BA Kit documentation — English](docs/en/README.md)

[Test Kit V1.1 overview — English](docs/en/TEST_KIT_README.md)

Human acceptance của framework không tự phê duyệt Test Design/Testcases của một project thật. `TEST_ONLY` artifact không phải production testware; Human Gate vẫn phải xác thực đúng snapshot. Xem [Release status](docs/vi/RELEASE.md).
