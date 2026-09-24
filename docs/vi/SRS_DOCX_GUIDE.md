# SRS và DOCX trong BA Kit

Trang này làm rõ hai khái niệm thường bị nhầm:

1. **Canonical SRS** — nội dung/ngữ nghĩa BA dùng để quản lý requirement.
2. **DOCX delivery** — bản Word dùng để review, gửi nội bộ/khách hàng hoặc theo template của tổ chức.

Hai lớp này không giống nhau.

## 1. Canonical SRS dùng template nào?

BA Kit RC1 hiện dùng **functional SRS contract**, không ép mọi feature vào một file Markdown template cố định.

Skill **srs-function-document** tạo SRS từ:

~~~text
Confirmed BA Decisions
+
Approved Business Rules
+
current canonical SRS (nếu update)
+
source evidence / workflow state
~~~

Các section được tạo khi phù hợp, ví dụ:

~~~text
Feature / Scope
Actors
Preconditions
Functional Requirements
Business Rules
Validation
States / Lifecycle
Error & Edge Behavior
List / Filter / Sort / Pagination
UI Behavior
Open Items / UNKNOWN
Traceability
~~~

Không phải feature nào cũng cần mọi section. Agent không được thêm section chỉ để lấp template bằng nội dung suy đoán.

## 2. Repository có sẵn SRS_TEMPLATE.docx không?

**Không.**

BA Kit RC1 production repository hiện **không bundle một SRS_TEMPLATE.docx mặc định**.

Điều này cần được hiểu rõ:

- BA Kit có capability tạo SRS Markdown;
- BA Kit có capability tạo/edit DOCX và dùng Word template;
- nhưng template Word chính thức của công ty/project phải được **Human cung cấp hoặc chọn**.

Nếu sau này repository bundle một default SRS template, template đó cần được version/provenance/license riêng và tài liệu này phải cập nhật.

## 3. Khi có template Word của công ty

Ưu tiên file **.docx** do BA/tổ chức sở hữu layout.

Ví dụ project:

~~~text
docs/
├── srs/
│   └── CR-123.md
└── templates/
    └── COMPANY_SRS_TEMPLATE.docx
~~~

Yêu cầu:

~~~text
Tạo SRS DOCX cho CR-123 từ docs/srs/CR-123.md.
Dùng templates/COMPANY_SRS_TEMPLATE.docx làm delivery template.
Không thay đổi business semantics; nếu section trong template chưa có dữ liệu confirmed thì giữ UNKNOWN hoặc báo tôi.
~~~

### Lane A — template có placeholder

Nếu template Word được chuẩn bị cho **docxtpl**, có thể có Jinja placeholder như:

~~~text
{{ feature_name }}
{{ scope }}
{{ actor }}
{% for requirement in requirements %}
...
{% endfor %}
~~~

document-docx có thể render context vào template và giữ style/layout do Word định nghĩa.

### Lane B — template Word không có placeholder

Nếu template chỉ là một DOCX có heading/table/style nhưng không có Jinja placeholder:

- inspect structure/style của file;
- map canonical SRS content vào section/table tương ứng;
- dùng structural editing;
- preserve formatting càng nhiều càng tốt;
- báo section không map được thay vì tự nhét nội dung.

Lane này cần review render kỹ hơn vì cấu trúc Word có thể phức tạp.

## 4. Nếu không có template

Có thể yêu cầu BA Kit tạo DOCX từ canonical SRS bằng style/document structure hợp lý.

Tuy nhiên output đó là **generic delivery DOCX**, không được gọi là “theo template công ty”.

Ví dụ:

~~~text
Xuất canonical SRS hiện tại thành DOCX để review nội bộ.
Không có company template; dùng style Word chuẩn, heading rõ ràng và table cho traceability.
~~~

## 5. Khi existing SRS chỉ có DOCX

Routing contract cho phép document-only workflow.

Nếu chưa có canonical Markdown và Human chọn DOCX hiện tại làm standalone Word source:

~~~text
Review file Existing-SRS.docx.
Chỉ report gap/inconsistency trước, chưa sửa file.
~~~

Sau đó Human có thể yêu cầu edit.

Khi project đã có canonical Markdown, không được sửa riêng Word để đổi business rule. Phải:

~~~text
Confirmed decision / BR
        ↓
Canonical SRS Markdown
        ↓
Regenerate / update DOCX
~~~

## 6. Template không phải semantic authority

Ví dụ template có section:

~~~text
Maximum duration: 60 minutes
~~~

nhưng BA baseline chưa xác nhận maximum duration.

Không được copy 60 phút thành requirement chỉ vì template có wording đó.

Phải coi là:

~~~text
UNKNOWN / template content requiring BA confirmation
~~~

Tương tự template không được tự tạo:

- permission;
- state transition;
- validation;
- default sort;
- page size;
- API/DB behavior.

## 7. SRS update

Khi update SRS:

- giữ nguyên confirmed content không liên quan;
- thay đổi đúng semantics có authority mới;
- giữ UNKNOWN;
- báo conflict;
- giữ traceability;
- không tự set APPROVED_FOR_ENGINEERING.

Ví dụ:

~~~text
Update SRS CR-123 theo các quyết định mới trong decisions.md.
Chỉ thay phần pagination; giữ nguyên các Business Rules đã approved khác.
Sau đó report diff semantic cho tôi review.
~~~

## 8. Quality gate cho DOCX

document-docx có các workflow/script để kiểm tra:

- unresolved template tags;
- parseability;
- comment/revision/OOXML;
- structure;
- cross-viewer rendering;
- accessibility hygiene.

Với tài liệu gửi ra ngoài, nên:

1. validate document;
2. mở/render bằng Microsoft Word nếu có;
3. kiểm tra thêm ít nhất một viewer khác khi portability quan trọng;
4. Human review nội dung trước release.

## 9. Mapping thường dùng từ canonical SRS sang Word

| Canonical BA content | Word section thường gặp |
|---|---|
| Feature identity / scope | Introduction / Scope |
| Actors | Actors / User roles |
| Functional requirements | Functional Requirements |
| Business Rules | Business Rules |
| Validation | Validation / Constraints |
| State/lifecycle | State / Workflow |
| UI behavior | Screen / UI Specification |
| Draw.io diagram | Business Flow / Process Diagram |
| UNKNOWN/open items | Open Questions / TBD |
| Traceability | Traceability Matrix |

Tên section thật phải theo template được chọn; bảng này chỉ là mapping gợi ý.

## 10. Prompt mẫu

### Tạo SRS Markdown

~~~text
Từ Business Rules đã confirmed, tạo canonical functional SRS.
Giữ UNKNOWN rõ ràng, thêm traceability và không quyết định technical design.
~~~

### Tạo DOCX theo template

~~~text
Dùng canonical SRS docs/srs/CR-123.md để tạo docs/output/CR-123-SRS.docx.
Template: docs/templates/COMPANY_SRS_TEMPLATE.docx.
Giữ nguyên layout/style của template.
Nếu thiếu dữ liệu cho section nào, report trước hoặc giữ UNKNOWN; không tự invent.
~~~

### Review DOCX

~~~text
Review SRS.docx theo canonical SRS hiện tại.
Chỉ report semantic mismatch, missing section và formatting issue.
Không sửa file cho tới khi tôi yêu cầu.
~~~

---

English: [SRS and DOCX guide](../en/SRS_DOCX_GUIDE.md)
