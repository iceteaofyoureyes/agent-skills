# Khả năng của BA Kit

BA Kit là bộ capability hỗ trợ **BA làm việc với requirement và artifact**, không phải agent tự thay BA quyết định nghiệp vụ. Human BA vẫn sở hữu việc trao đổi stakeholder/khách hàng, trả lời câu hỏi nghiệp vụ, xác nhận Business Rules và phê duyệt baseline.

BA Kit chịu trách nhiệm phần **WHAT — hệ thống cần làm gì**. Technical ownership và cách triển khai thuộc các phase sau.

## BA Kit có thể nhận đầu vào gì?

| Đầu vào | BA Kit dùng để làm gì | Lưu ý |
|---|---|---|
| Requirement, CR, user notes, meeting notes | Review gap, ambiguity, edge case, rule còn thiếu | Không tự biến wording mơ hồ thành quyết định |
| Source code/project hiện tại | Brownfield discovery, xác định CURRENT_SYSTEM | Current behavior là evidence, không tự thành target requirement |
| SRS/BR/Markdown hiện có | Review, update có kiểm soát | Giữ nguyên phần đã approved nếu không có quyết định mới |
| DOCX hiện có | Review/edit document-only hoặc delivery | Nếu đã có canonical Markdown thì không sửa riêng DOCX để đổi nghiệp vụ |
| Word template .docx | Xuất SRS/DOCX theo layout/template của tổ chức | RC1 **không bundle SRS_TEMPLATE.docx mặc định** |
| Screenshot/image/PDF export | Visual evidence, mô tả UI, tìm gap, dựng lại sơ đồ | Chỉ kết luận điều nhìn thấy; hidden rules vẫn phải hỏi Human |
| Figma | Visual source khi runtime có connector/quyền truy cập | Nếu không có connector, dùng screenshot/PDF export/local artifact |
| HTML prototype/UI hiện có | Review interaction/state, mô tả lại trong SRS | Không coi prototype là business authority |
| .drawio hiện có | Review, edit, sync, restyle | Semantic change phải quay lại BR/SRS trước |
| Business Rules/SRS đã duyệt | Tạo Draw.io, DOCX và Engineering Handoff | Derived artifact không được đổi ngữ nghĩa nguồn |

## Capability chính

### 1. Review requirement và tìm gap

BA Kit có thể:

- đọc đầu bài BA đã nhận;
- tìm ambiguity, contradiction và missing case;
- hỏi các nhóm thường bị bỏ sót như actor/permission, field bắt buộc, validation, state/lifecycle, search/filter, sort, pagination/page size, row action, error/edge case, destructive behavior;
- phân loại điểm nào blocking và non-blocking;
- giữ **UNKNOWN** thay vì tự chọn một giá trị hợp lý.

Ví dụ:

~~~text
Review requirement này giúp tôi. Chỉ ra các case còn thiếu/chưa rõ.
Chưa viết SRS cho tới khi tôi trả lời các câu hỏi blocking.
~~~

### 2. Brownfield/current-system discovery

Với dự án có code sẵn, BA Kit có thể dùng **codebase-discovery** để kiểm tra hành vi hiện tại có liên quan rồi ghi dưới nhãn **CURRENT_SYSTEM**.

Ví dụ:

~~~text
Review CR này trên project hiện tại.
Trước khi hỏi tôi, hãy discover các màn/API/model liên quan và tách rõ:
- CURRENT_SYSTEM
- UNKNOWN
- câu hỏi cần BA xác nhận.
~~~

Discovery không được thay BA quyết định target behavior.

### 3. Business Rules

Từ câu trả lời Human đã xác nhận, BA Kit có thể tổng hợp Business Rules có traceability và giữ riêng:

- CONFIRMED;
- CURRENT_SYSTEM;
- INFERRED;
- PROPOSED;
- UNKNOWN.

### 4. Tạo hoặc cập nhật SRS

BA Kit có thể tạo/update **canonical functional SRS ở Markdown** từ Confirmed BA Decisions và Approved Business Rules.

SRS có thể chứa các phần phù hợp với feature như:

- scope/actor;
- precondition;
- functional requirements;
- Business Rules;
- validation;
- state/lifecycle;
- error/edge behavior;
- list/filter/sort/pagination;
- UI behavior đã được xác nhận;
- open items/UNKNOWN;
- traceability.

SRS không được tự quyết định API, DB schema, event schema, locking, transaction hay service architecture.

Xem [SRS và DOCX](SRS_DOCX_GUIDE.md).

### 5. Xuất SRS/DOCX theo template

**document-docx** hỗ trợ:

- tạo DOCX mới;
- chỉnh sửa DOCX hiện có;
- dùng Word-authored template;
- render template bằng docxtpl khi template có placeholder;
- structural edit bằng python-docx;
- comments/review workflows;
- quality gate và kiểm tra OOXML.

BA Kit RC1 **không có một company SRS Word template mặc định trong repository**. Nếu tổ chức có template, hãy cung cấp file .docx và chọn nó làm delivery template.

Semantic source vẫn là canonical BA baseline; Word template chỉ điều khiển cấu trúc/trình bày.

### 6. Tạo và chỉnh Draw.io

**drawio-skill** tạo file **.drawio editable**, không chỉ ảnh tĩnh. Trong BA scope nên ưu tiên:

- business process flowchart;
- swimlane theo actor/role;
- user/task flow;
- state/lifecycle diagram;
- decision tree;
- context/interaction map ở mức nghiệp vụ;
- dựng lại flow từ screenshot/whiteboard;
- review/edit một .drawio có sẵn.

Có thể export PNG/SVG/PDF khi môi trường có draw.io CLI.

BA Kit không dùng capability này để tự thiết kế target technical architecture/ERD/service boundary ở BA phase.

Xem [Draw.io, visual input và prototype](DIAGRAMS_PROTOTYPES.md).

### 7. Review Figma/image/UI và mô tả UI trong SRS

Khi visual source có thể truy cập, BA Kit có thể:

- liệt kê screen/section;
- field/label/control nhìn thấy;
- action/state nhìn thấy;
- responsive/state differences nếu có evidence;
- đối chiếu visual với requirement;
- tìm gap giữa visual và business semantics;
- viết UI behavior vào SRS sau khi BA xác nhận.

Không suy ra permission, validation, backend rule hoặc hidden navigation chỉ từ pixels.

### 8. Prototype/UI hỗ trợ — optional

Khi optional skills được cài, BA Kit có thể dùng:

- **product-design-and-ux** để model task flow, state, recovery và interface contract;
- **frontend-design** để tạo local visual prototype;
- **playwright** để render/check UI;
- **impeccable** để critique/polish;
- **web-accessibility** để review accessibility.

Prototype là **visual proposal** và cần Human visual review. Nó không tự trở thành business requirement hay production implementation.

### 9. Review/edit artifact có sẵn

Operation được phân biệt:

| Operation | Ý nghĩa |
|---|---|
| REVIEW | Chỉ review, không mutate artifact hay advance stage |
| CREATE | Tạo artifact mới từ authority đã đủ |
| EDIT | Sửa artifact được chọn, giữ semantics approved không liên quan |
| CONTINUE | Tiếp tục workflow từ state; **không phải approval** |

### 10. Engineering Handoff

Sau khi Human phê duyệt rõ ràng BA baseline và không còn blocking item, BA Kit tạo **engineering-handoff.yml** gồm:

- feature identity;
- approved immutable revision;
- Business Rules/SRS/decision source path + SHA-256;
- open items;
- downstream policy;
- next stage = engineering-impact-analysis.

Handoff không chứa repo/module owner, FE/BE owner, API/DB/event design, locking hoặc transaction strategy.

## Source of truth theo loại artifact

~~~text
Business semantics:
Confirmed BA Decisions
+ Approved Business Rules
+ Canonical SRS

Visual evidence:
Approved Figma / screenshot / prototype / diagram
(chỉ phần visual/interaction đã được xác nhận)

Delivery formatting:
Selected Word template

Current implementation:
CURRENT_SYSTEM evidence
~~~

Một artifact derived như DOCX, Draw.io hay prototype **không được tự thay đổi business semantics**.

## Required và optional capability

Required trong BA Kit RC1:

- verification-before-completion
- codebase-discovery
- requirements-gap-auditor
- requirements-interrogator
- requirements-quality-check
- business-rule-extractor
- srs-function-document
- document-docx
- drawio-skill

Optional:

- product-design-and-ux
- frontend-design
- impeccable
- playwright
- web-accessibility

Doctor có thể báo **DEGRADED** nếu optional capability thiếu; core BA workflow vẫn cần required capabilities để READY.

## Không thuộc BA Kit

BA Kit không:

- tự trao đổi thay BA với khách hàng;
- tự approve requirement/SRS;
- quyết định architecture;
- gán repo/module/service owner;
- thiết kế API/DB/event;
- quyết định locking/transaction;
- viết production implementation.

Các phần đó được chuyển sang Human/Engineering Impact/Dev Kit/Test Kit theo phase tương ứng.

---

English: [BA Kit capabilities](../en/BA_KIT_CAPABILITIES.md)
