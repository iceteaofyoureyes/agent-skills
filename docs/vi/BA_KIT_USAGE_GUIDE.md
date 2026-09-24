# Hướng dẫn sử dụng BA Kit theo tình huống

BA Kit được dùng bằng **ý định tự nhiên**. Không cần nhớ tên từng skill. Workflow tự route capability dựa trên operation, project mode, artifact và Human Gate.

## Quy tắc trước khi dùng

BA Kit phân biệt:

~~~text
CREATE   tạo artifact mới
EDIT     cập nhật artifact
REVIEW   chỉ review, không mutate
CONTINUE tiếp tục workflow, không approve
~~~

Với mọi mode, Human vẫn là business authority.

## Tình huống 1 — Review đầu bài trước khi viết tài liệu

~~~text
Review requirement này giúp tôi.
Tìm ambiguity, missing rule, edge case và các điểm BA cần hỏi lại.
Chưa viết SRS.
~~~

Expected: gap list, evidence classification, blocking/non-blocking questions; không mutate artifact.

## Tình huống 2 — Review brownfield dựa trên project hiện tại

~~~text
Review CR-123 trên codebase hiện tại.
Discover current system trước.
Tách rõ CURRENT_SYSTEM, INFERRED và UNKNOWN.
Sau đó hỏi tôi các decision còn thiếu.
~~~

Agent kiểm tra source trong phạm vi runtime có quyền đọc. Current behavior không tự thành target requirement.

## Tình huống 3 — Review một màn CRUD/list còn thiếu rule

~~~text
Review chức năng danh sách công văn này.
Kiểm tra giúp tôi còn thiếu:
- search/filter;
- sort/default sort;
- pagination và page size;
- fields hiển thị;
- row actions;
- state;
- permission;
- empty/loading/error;
- validation và destructive action.
Chỉ hỏi những điểm chưa có evidence.
~~~

## Tình huống 4 — Input là screenshot/Figma/PDF/HTML prototype

Nếu Figma connector không có, export artifact thành file agent đọc được.

~~~text
Review screenshot này cùng CR-208.
Liệt kê UI element quan sát được, đối chiếu requirement và hỏi gap.
Không suy ra permission/validation/business rule chỉ từ hình.
~~~

Sau khi BA trả lời:

~~~text
Update phần UI Behavior trong canonical SRS từ các quyết định vừa confirmed.
~~~

## Tình huống 5 — Trả lời clarification và tổng hợp Business Rules

~~~text
Sort mặc định theo createdAt giảm dần.
Page size mặc định 20, cho phép 20/50/100.
Chỉ role Supervisor có action Cancel.
~~~

Sau đó:

~~~text
Tổng hợp Business Rules đã CONFIRMED.
Giữ các mục chưa trả lời là UNKNOWN.
Report rule nào còn blocking.
~~~

**ANSWER không đồng nghĩa APPROVE.**

## Tình huống 6 — Tạo canonical SRS

~~~text
Tạo canonical functional SRS từ decisions và Business Rules đã confirmed.
Giữ traceability.
Không tự quyết định API/DB/architecture.
Để UNKNOWN hiển thị rõ.
~~~

## Tình huống 7 — Update SRS hiện có

~~~text
Update SRS CR-123 theo các quyết định mới trong decisions.md.
Chỉ thay phần sort/pagination.
Giữ nguyên các rule approved khác.
Report semantic diff sau khi sửa.
~~~

## Tình huống 8 — Xuất SRS DOCX theo template công ty

~~~text
Tạo DOCX từ docs/srs/CR-123.md.
Dùng docs/templates/COMPANY_SRS_TEMPLATE.docx.
Giữ style/layout của template.
Section nào chưa có dữ liệu confirmed thì để UNKNOWN hoặc report; không tự invent.
~~~

BA Kit RC1 **không bundle template SRS Word mặc định**.

## Tình huống 9 — Review/edit existing DOCX

Review-only:

~~~text
Review Existing-SRS.docx so với requirement và Business Rules hiện tại.
Chỉ report mismatch/missing/format issue.
Không sửa file.
~~~

Nếu đã có canonical Markdown, semantic change phải cập nhật Markdown trước rồi mới đồng bộ DOCX.

## Tình huống 10 — Tạo Draw.io flowchart/state/swimlane

~~~text
Từ Business Rules đã approved, tạo business flowchart .drawio.
Output editable + PNG preview.
Gắn BR reference khi hữu ích.
Không thêm transition/rule chưa confirmed.
~~~

## Tình huống 11 — Review/update Draw.io có sẵn

~~~text
Review process.drawio so với canonical SRS.
Chỉ report mismatch, chưa sửa.
~~~

Sau approval:

~~~text
Update process.drawio theo BR-022 vừa approved.
Giữ layout/style khác.
~~~

## Tình huống 12 — Tạo prototype UI — optional

~~~text
Từ SRS đã confirmed và screenshot tham chiếu, tạo local prototype.
Bao gồm desktop/mobile và các state đã được xác định.
Đây là visual proposal; không thay đổi Business Rules.
~~~

## Tình huống 13 — Review artifact mà không thay đổi workflow

~~~text
Review SRS hiện tại về completeness và consistency.
REVIEW only. Không edit file và không advance workflow.
~~~

## Tình huống 14 — Request changes sau review

~~~text
Request changes cho SRS revision SRS-42:
- FR-12 chưa nêu behavior khi empty;
- BR-08 trace sai;
- chưa chốt page size.
Không approve.
~~~

## Tình huống 15 — Approve BA baseline

~~~text
Tôi phê duyệt Business Rules revision BR-42
và SRS revision SRS-42
làm BA baseline cho Engineering.
~~~

Approval phải explicit. **“Tiếp tục” không phải approval.**

## Tình huống 16 — Tạo Engineering Handoff

~~~text
Tạo Engineering Handoff từ baseline vừa approved.
~~~

Expected: immutable revision, source path + SHA-256, open items, downstream policy, next stage; không có technical ownership/design.

## Tình huống 17 — Continue session

~~~text
Tiếp tục.
~~~

Workflow đọc **workflow-state.json**, xác định next valid action và tiếp tục. Nó không trả lời câu hỏi thay Human, tự approve hoặc bỏ qua blocking gate.

## Một flow làm việc đầy đủ

~~~text
BA input
→ REVIEW
→ brownfield/visual discovery khi cần
→ gap/questions
→ Human ANSWER
→ Business Rules
→ canonical SRS
→ Draw.io / prototype draft khi cần
→ DOCX delivery theo template khi cần
→ Human REQUEST_CHANGES / APPROVE
→ Engineering Handoff
~~~

Derived artifacts nên được regenerate/update từ canonical sources sau khi semantic baseline đổi.

## Xem thêm

- [Khả năng BA Kit](BA_KIT_CAPABILITIES.md)
- [Workflow và Human Gates](BA_KIT_WORKFLOW.md)
- [SRS và DOCX](SRS_DOCX_GUIDE.md)
- [Draw.io, visual input và prototype](DIAGRAMS_PROTOTYPES.md)
- [Ví dụ CR-001](../../kits/ba/examples/CR-001/README.md)

---

English: [Usage guide](../en/BA_KIT_USAGE_GUIDE.md)
