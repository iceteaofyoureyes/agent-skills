# Hướng dẫn nhanh BA Kit

BA Kit hỗ trợ BA theo flow:

~~~text
Review input
→ discover current system khi cần
→ tìm gap
→ Human trả lời
→ Business Rules
→ SRS
→ Draw.io / prototype / DOCX khi cần
→ Human approval
→ Engineering Handoff
~~~

BA vẫn sở hữu quyết định nghiệp vụ và trao đổi stakeholder. Agent chủ yếu **discover, review, hỏi, cấu trúc, document, visualize và validate**.

## BA Kit làm được gì?

- review requirement/gap/edge case;
- brownfield discovery từ project hiện tại;
- review screenshot/Figma export/PDF/HTML prototype;
- tổng hợp Business Rules;
- tạo/update canonical functional SRS;
- tạo/edit DOCX, bao gồm Word template do project cung cấp;
- tạo/edit Draw.io business flow/state/swimlane;
- optional local UI prototype + visual/accessibility review;
- Human Gate và Engineering Handoff.

Xem [Khả năng BA Kit](BA_KIT_CAPABILITIES.md).

## Cài cho project

~~~powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Doctor: **READY** = required capabilities/contracts đạt; **DEGRADED** = thiếu optional capability; **FAIL** = required capability/contract lỗi.

## Bước 1 — Review requirement

~~~text
Review requirement này giúp tôi.
Nếu là brownfield, discover current system trước.
Tìm case thiếu/chưa rõ và hỏi tôi; chưa viết SRS.
~~~

Với màn list/CRUD, kỳ vọng agent kiểm tra fields, search/filter, sort, pagination/page size, actions, state/lifecycle, permissions, validation, empty/loading/error và edge cases.

## Bước 2 — Human trả lời

~~~text
Sort mặc định createdAt DESC.
Page size mặc định 20.
Cancel chỉ áp dụng trạng thái Draft và chỉ Supervisor được dùng.
~~~

Câu trả lời chỉ resolve câu hỏi; không approve artifact.

## Bước 3 — Business Rules và SRS

~~~text
Tổng hợp Business Rules đã confirmed, giữ UNKNOWN riêng.
~~~

Sau khi review BR:

~~~text
Tạo canonical functional SRS từ baseline đã confirmed.
Giữ traceability và không quyết định technical design.
~~~

## Bước 4 — Derived artifact khi cần

### DOCX theo template

~~~text
Xuất SRS thành DOCX.
Template: docs/templates/COMPANY_SRS_TEMPLATE.docx.
Giữ style/layout; không invent dữ liệu thiếu.
~~~

RC1 hiện **không bundle SRS_TEMPLATE.docx mặc định**. Xem [SRS và DOCX](SRS_DOCX_GUIDE.md).

### Draw.io

~~~text
Từ Business Rules/SRS đã approved, tạo business flowchart .drawio
và PNG preview. Không thêm rule mới.
~~~

Xem [Draw.io, visual input và prototype](DIAGRAMS_PROTOTYPES.md).

### Prototype — optional

~~~text
Từ SRS đã confirmed và visual reference, tạo local prototype để tôi review.
Đây là visual proposal, không phải production code.
~~~

## Bước 5 — Review và approve

~~~text
Review SRS revision SRS-42. Không sửa file.
~~~

hoặc:

~~~text
Request changes cho SRS-42: ...
~~~

Khi thực sự chấp nhận:

~~~text
Tôi phê duyệt BR-42 và SRS-42 làm BA baseline cho Engineering.
~~~

**“Tiếp tục” không phải phê duyệt.**

## Bước 6 — Engineering Handoff

~~~text
Tạo Engineering Handoff.
~~~

Chỉ hợp lệ sau explicit approval và không còn blocking item.

## Visual input

Nếu có screenshot/Figma/PDF/HTML:

~~~text
Review visual này cùng requirement.
Tách observed visual, mismatch, missing decision và proposal.
Không suy ra business rule ẩn từ hình.
~~~

Figma link chỉ dùng trực tiếp khi runtime có connector/quyền; nếu không hãy export screenshot/PDF/local artifact.

## Ví dụ

[CR-001 Appointment Scheduling](../../kits/ba/examples/CR-001/README.md) minh họa input → gap review → Human decisions → Business Rules → SRS → diagram/DOCX delivery examples → engineering handoff.

## Trạng thái RC1 hiện tại

Package/install/Doctor và redistribution licensing đã qua các kiểm tra tương ứng. Đã thực hiện kiểm tra thủ công cho Requirement, Business Rules, SRS và Draw.io. Validation thủ công cuối cùng cho DOCX và validation cuối cùng cho approval/handoff vẫn đang chờ; BA Kit 1.0.0-rc.1 là Public Preview và chưa được chấp nhận hoàn toàn.

Xem [Release status](RELEASE.md).

---

English: [Quick Start](../en/BA_KIT_QUICKSTART.md)
