# Agent Skills Kits

**Project Foundation:** capability Shared SDLC cho brownfield, greenfield và refresh.
Xem [workflow core](docs/project-foundation.md), [semantic producers](docs/foundation-semantic-producers.md)
và [skill](project-foundation/SKILL.md). Producer artifacts được giữ trong runtime
review package; C4 và arc42 là derived views.

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

## Test Kit Manual VNext

Test Kit nhận **Engineering Handoff VNext** có exact BA Human approval proof và tạo manual testware qua hai Human Gate:

~~~text
Engineering Handoff VNext → Canonical Test Design → Human Design Gate
→ APPROVED_DESIGN → Canonical Testcases → Human Case Gate → APPROVED_TESTWARE
~~~

Trace chuẩn chỉ gồm `BR-*`/`FR-*`; `BAREF:*` chỉ là locator/provenance. `APPROVED_TESTWARE` kết thúc manual lane Phase 6, không đồng nghĩa `EXECUTION_READY`, test PASS, `VERIFIED` hay `READY_TO_MERGE`. Automation/execution bắt đầu từ Phase 7+.

UX chỉ bắt buộc khi VNext authority context ghi rõ `ux_required: true`; từ `field`, `input`, `page` không suy ra UX. UX context được tiêu thụ phải có exact Human approval và source/snapshot hash. Dev Handoff V2 là technical context tùy chọn, không định nghĩa BA WHAT. Project Test Policy và TEA/Katalon không cấp authority. XMind/Excel là projection một chiều. V1 đọc theo `LEGACY_COMPAT`, `vnext_authority=false`; Delivery Manifest không bắt buộc.

Bắt đầu tại [Quick Start VNext](docs/vi/TEST_KIT_QUICKSTART.md), [capabilities](docs/vi/TEST_KIT_CAPABILITIES.md), [usage](docs/vi/TEST_KIT_USAGE_GUIDE.md), [workflow](docs/vi/TEST_KIT_WORKFLOW.md), [customization](docs/vi/TEST_KIT_CUSTOMIZATION.md) và [neutral VNext example](kits/test/examples/vnext/neutral/README.md). Appointment/CR-001 là lịch sử V1, không phải ví dụ mặc định.

## SRS template và DOCX

BA Kit quản lý **canonical functional SRS ở Markdown** và có capability xuất/edit DOCX.

Repository không bundle SRS_TEMPLATE.docx mặc định. Nếu công ty/project có Word template, cung cấp file .docx và chọn nó làm delivery template; template không được override business semantics.

Xem [SRS và DOCX](docs/vi/SRS_DOCX_GUIDE.md).

## Draw.io và visual workflow

BA Kit có thể tạo/edit file .drawio editable cho business process flowchart, swimlane, user/task flow, state/lifecycle và decision tree; có thể xuất PNG/SVG/PDF khi toolchain hỗ trợ.

Visual input như screenshot/Figma export/PDF/HTML prototype được dùng làm evidence và để tìm gap; hidden permission/validation/business rule vẫn cần Human xác nhận.

Xem [Draw.io, visual input và prototype](docs/vi/DIAGRAMS_PROTOTYPES.md).

## Các Kit

| Kit | Trạng thái | Phạm vi |
|---|---|---|
| **BA Kit** | **VNext packaging candidate; Tier 3 fresh-install acceptance required; not a stable release** | **WHAT** |
| **Dev Kit** | Planned | Engineering Impact + **HOW** |
| **Test Kit Manual + Automation V1** | `2.0.0-rc.7` prerelease candidate; Phase 7 requires fresh installed Automation acceptance and full regression | **HOW DO WE PROVE IT** |

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

## Cài Test Kit Manual VNext

Chạy từ project Codex với Python 3.10+:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
~~~

Doctor `READY` chỉ xác nhận package/core capability; không có nghĩa BA/Design/Case approval hoặc execution readiness. `DEGRADED` chỉ capability tùy chọn thiếu; `FAIL` là package/core integrity lỗi. BA Kit và Test Kit có thể cùng cài. Xem [Installation](docs/vi/INSTALLATION.md).

## Tài liệu chuyên sâu

- [SRS và DOCX](docs/vi/SRS_DOCX_GUIDE.md)
- [Draw.io, visual input và prototype](docs/vi/DIAGRAMS_PROTOTYPES.md)
- [Kiến trúc](docs/vi/ARCHITECTURE.md)
- [Nền tảng thiết kế & chuẩn tham chiếu](docs/vi/FOUNDATIONS.md)
- [Kit contract](docs/vi/KIT_CONTRACT.md)
- [Release status](docs/vi/RELEASE.md)
- [Provenance & licensing](docs/vi/PROVENANCE.md)

## Trạng thái hiện tại

BA Kit đang ở trạng thái packaging candidate, không phải stable release. Phase 4 completion yêu cầu Tier 3 fresh-install acceptance với runtime import được cách ly khỏi source checkout. Doctor READY chỉ xác nhận package capability; approval vẫn do trusted host xác thực theo đúng BA candidate.



## English documentation

[BA Kit documentation — English](docs/en/README.md)

[Test Kit Manual VNext overview — English](docs/en/TEST_KIT_README.md)

Framework/package readiness không tự phê duyệt Test Design/Testcases của project. Mỗi gate cần trusted Human receipt cho đúng snapshot và input refs. Xem [Release status](docs/vi/RELEASE.md).
