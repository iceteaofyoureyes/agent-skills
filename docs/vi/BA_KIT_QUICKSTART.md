# Hướng dẫn nhanh BA Kit

BA Kit hỗ trợ BA theo flow:

~~~text
Review input
→ discover current system khi cần
→ tìm gap
→ Human trả lời
→ Business Rules
→ SRS
→ chọn và validate BA baseline candidate
→ HUMAN_REVIEW và dừng chờ Human approval
→ Draw.io / prototype / DOCX khi cần
→ nhận approval receipt đã xác thực từ trusted host
→ revalidate và tạo Engineering Handoff VNext
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
Doctor chỉ báo capability package đã cài; không xác nhận baseline đã approved hay feature đã sẵn sàng.

## Artifact VNext và ranh giới approval

- Runtime state: `workflow-state-vnext.json` (V2) trong project; ghi tiến độ workflow, không phải business authority.
- Canonical authority: Human BA Decisions, Business Rules có ID ổn định `BR-*`, canonical SRS có ID ổn định `FR-*`, và BA Baseline Candidate/Manifest được chọn. `BAREF:*` chỉ là locator/provenance.
- Evidence và gate: exact evidence refs và Human approval receipt do trusted host cung cấp/xác thực. CLI BA Kit không xác thực danh tính và không tạo receipt approval.
- Handoff: `engineering-handoff.json` (Engineering Handoff VNext), được revalidate theo candidate, receipt và source refs chính xác.
- DOCX, Draw.io và visual output tùy chọn là derived artifact.

Nếu có Project Foundation, chỉ consume khi có durable manifest, promotion provenance, Foundation approval receipt và trusted Foundation host authentication. Foundation READY chỉ cung cấp context, không phải BA approval.

V1 `workflow-state.json` và `engineering-handoff.yml` chỉ được đọc ở chế độ `LEGACY_COMPAT`; không bao giờ chứng minh VNext approval.

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

Repository hiện **không bundle SRS_TEMPLATE.docx mặc định**. Xem [SRS và DOCX](SRS_DOCX_GUIDE.md).

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

## Bước 5 — Validate và dừng ở Human review

~~~text
Review đúng BA candidate và source revision. Không sửa file.
~~~

hoặc:

~~~text
Request changes cho candidate revision BA-42: ...
~~~

Workflow chuyển `DRAFT → VALIDATED → HUMAN_REVIEW` rồi dừng. Chỉ trusted host mới cung cấp Human approval receipt chính xác đã xác thực để chuyển sang `APPROVED_BASELINE`. `CONTINUE != APPROVE`; `ANSWER != APPROVE`; validator PASS, Foundation READY và UX approval không phê duyệt BA baseline.

## Bước 6 — Engineering Handoff

~~~text
Sau khi trusted host cung cấp approval, revalidate đúng baseline rồi tạo Engineering Handoff VNext (`engineering-handoff.json`).
~~~

Chỉ hợp lệ khi có proof `APPROVED_BASELINE` chính xác và không còn blocking item. BA sở hữu WHAT; Engineering sở hữu technical HOW.

## Visual input

Nếu có screenshot/Figma/PDF/HTML:

~~~text
Review visual này cùng requirement.
Tách observed visual, mismatch, missing decision và proposal.
Không suy ra business rule ẩn từ hình.
~~~

Figma link chỉ dùng trực tiếp khi runtime có connector/quyền; nếu không hãy export screenshot/PDF/local artifact.

## Ví dụ

[Ví dụ CR-001 trung tính](../../kits/ba/examples/CR-001/README.md) minh họa candidate, review gate, BR/FR identity, derived output và ranh giới handoff.

---

English: [Quick Start](../en/BA_KIT_QUICKSTART.md)
