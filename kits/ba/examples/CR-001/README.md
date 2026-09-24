# CR-001: Appointment Scheduling

Đây là **documentation example** minh họa cách BA Kit đi từ đầu bài thiếu thông tin tới BA baseline/handoff. Nó không phải transcript runtime cố định và không được feed vào fresh-session acceptance.

## Example này chứng minh gì?

~~~text
Semantic spine:
01 Input Requirement
→ 02 Gap Review + Human decisions
→ 03 Approved Business Rules
→ 04 SRS excerpt
→ 05 Engineering Handoff

Derived lane from approved/confirmed sources:
03 / 04
→ 06 Draw.io / DOCX / visual delivery examples
→ Human visual/document review
~~~

Nó minh họa:

- input ban đầu có thể thiếu rule;
- agent phải hỏi thay vì invent;
- Human answers được tách khỏi input;
- Business Rules/SRS có traceability;
- Draw.io/DOCX là derived delivery artifacts;
- Engineering Handoff chỉ sau approval.

## Các file

| Tệp | Vai trò | Mục đích |
|---|---|---|
| [01-input-requirement.md](vi/01-input-requirement.md) | INPUT | Đầu bài intentionally incomplete |
| [02-gap-review.md](vi/02-gap-review.md) | ILLUSTRATIVE OUTPUT + Human decisions | Gap trước clarification và câu trả lời Human ví dụ |
| [03-approved-business-rules.md](vi/03-approved-business-rules.md) | ILLUSTRATIVE OUTPUT | Business Rules có evidence/UNKNOWN |
| [04-srs-excerpt.md](vi/04-srs-excerpt.md) | ILLUSTRATIVE OUTPUT | Functional requirements + traceability |
| [05-engineering-handoff.yml](vi/05-engineering-handoff.yml) | CONTRACT-VALID EXAMPLE | Handoff schema + real hashes cho adjacent sources |
| [06-delivery-and-visualization.md](vi/06-delivery-and-visualization.md) | USAGE EXAMPLE | Derived Draw.io/DOCX/prototype lane từ BR/SRS |

## Đọc example theo đúng cách

### Bước 1 — chỉ nhìn input

Mở **01-input-requirement.md**. Tự hỏi: từ input này có biết sorting, pagination, conflict rule, lifecycle, completion behavior chưa?

Câu trả lời là chưa.

### Bước 2 — xem agent cần hỏi gì

**02-gap-review.md** cho thấy loại gap BA Kit phải chủ động tìm.

Phần “Human decisions” trong file là **ngữ liệu được cung cấp sau**, không phải điều agent được suy luận từ input.

### Bước 3 — xem semantics được cấu trúc ra sao

**03-approved-business-rules.md** và **04-srs-excerpt.md** minh họa chain:

~~~text
Human decision
→ Business Rule
→ Functional Requirement
~~~

UNKNOWN vẫn phải giữ UNKNOWN.

### Bước 4 — xem derived artifacts

**06-delivery-and-visualization.md** giải thích:

- lifecycle/business flow nào có thể vẽ bằng Draw.io;
- cách xuất SRS DOCX nếu project cung cấp Word template;
- vì sao example không có sẵn company SRS template;
- visual/prototype lane hoạt động thế nào nếu có visual source.

### Bước 5 — handoff

**05-engineering-handoff.yml** dùng đúng schema hiện tại và SHA-256 thật của các source example.

Handoff không chứng minh runtime acceptance PASS.

## Điều example không chứng minh

- Không chứng minh current PetClinic behavior; brownfield run thật phải discover source.
- Không chứng minh BA Kit runtime luôn sinh đúng wording/ID.
- Không cung cấp company Word template.
- Không cung cấp Figma/screenshot/prototype vì input CR-001 không có visual source.
- Không quyết định target API/DB/architecture.

## Fresh-session acceptance rule

Không đưa các approved outputs trong thư mục này vào generation context của acceptance.

Generator chỉ được nhận input/decisions theo test protocol; evaluator mới được dùng expected semantics sau generation.

## Open items trong fixture

Handoff example phân loại maximum duration và list details là non-blocking **chỉ cho documentation fixture này**. Giá trị vẫn UNKNOWN. Project thật phải để Human quyết định item nào blocking.

English: [CR-001 example](en/README.md)
