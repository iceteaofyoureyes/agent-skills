# Quy trình BA Kit và Human Gate

BA Kit không phải một pipeline cứng bắt mọi yêu cầu chạy từ đầu đến cuối. Workflow chọn **điểm bắt đầu an toàn nhất** theo loại công việc:

- **brownfield** — requirement liên quan hệ thống/code hiện tại;
- **greenfield** — chưa có current system cần discover;
- **document-only** — review/edit SRS/DOCX/diagram đã có;
- **visual-assisted** — có screenshot/Figma/PDF/prototype làm visual evidence.

## Core semantic flow

~~~mermaid
flowchart TD
    A[BA Input / Requirement / CR] --> B{Current system matters?}
    B -- Yes --> C[Current-System Discovery]
    B -- No --> D[Requirement Review / Gap Analysis]
    C --> D
    D --> E[Human Clarification]
    E --> F[Business Rules]
    F --> G[Canonical SRS]
    G --> H[Human BA Baseline Gate]
    H --> I[Engineering Handoff]
    I -. Planned .-> J[Engineering Impact]
    J -. Planned .-> K[Dev Kit + repo-local Spec Kit]
    K -. Planned .-> L[Test Kit + TEA]
~~~

Core flow quản lý **business semantics**. Draw.io, prototype và DOCX là derived/visual/delivery lanes; chúng không thay semantic authority.

## Derived artifact lanes

~~~mermaid
flowchart LR
    A[Confirmed Decisions + Approved BR + Canonical SRS]
    A --> B[Draw.io Business Diagrams]
    A --> C[DOCX Delivery]
    A --> D[Optional UX / Prototype]
    V[Approved visual source] --> D
    T[Selected Word template] --> C
    B --> E[Human visual/document review]
    C --> E
    D --> E
~~~

Khi semantic baseline thay đổi, derived artifact liên quan phải được review/update lại.

## Project mode

| Mode | Khi dùng | Discovery |
|---|---|---|
| Brownfield | Feature/CR trên hệ thống có sẵn | Inspect source/current behavior trước khi kết luận target |
| Greenfield | Chưa có current system | Bắt đầu từ requirement/gap clarification |
| Document-only | Review/edit artifact đã có | Không bắt buộc code discovery nếu current system không liên quan |
| Visual-assisted | Có image/Figma/PDF/HTML/prototype | Dùng visual làm evidence; hidden behavior vẫn hỏi Human |

## Operation mode

| Operation | Quy tắc |
|---|---|
| REVIEW | Read-only; không mutate artifact, không advance stage |
| CREATE | Tạo artifact được yêu cầu khi authority đủ |
| EDIT | Sửa đúng artifact/scope; giữ unaffected approved semantics |
| CONTINUE | Đọc workflow-state và đi tới next valid action; không approve |

## Giai đoạn và output

| Giai đoạn | Agent làm gì | Human làm gì | Output điển hình |
|---|---|---|---|
| Input | Xác định feature/artifact/mode | Cung cấp requirement/source | Input refs |
| Current-System Discovery | Tìm hành vi hiện tại liên quan | Xác nhận scope discovery khi cần | CURRENT_SYSTEM findings |
| Gap Analysis | Tìm missing/ambiguous/contradictory cases | Review câu hỏi | Gap list |
| Clarification | Ghi câu trả lời và evidence | Trả lời business decisions | Confirmed decisions |
| Business Rules | Cấu trúc rule và trace | Review/request changes | Business Rules |
| SRS | Tạo/update functional SRS | Review/request changes | Canonical SRS |
| Draw.io/DOCX/Prototype | Tạo derived artifacts theo nguồn đã xác định | Visual/document review | .drawio, DOCX, prototype |
| Approval | Không tự approve | APPROVE/REJECT/REQUEST_CHANGES | Gate decision |
| Handoff | Validate baseline + hashes | Xác nhận baseline đã approve | engineering-handoff.yml |

## Những gap BA Kit nên chủ động soi

Không phải checklist bắt buộc cho mọi feature, nhưng với CRUD/list/workflow thường cần xem:

- actor/role/permission;
- data fields và required/optional;
- validation/boundaries;
- state/lifecycle;
- search/filter;
- sort/default sort;
- pagination/page size;
- list columns;
- row/bulk actions;
- empty/loading/error;
- destructive action/confirmation;
- concurrency business outcome;
- timezone/date semantics;
- audit/history khi business requirement cần;
- integration outcome ở mức business.

Agent chỉ hỏi các điểm **chưa có authority**.

## Nhãn bằng chứng

| Nhãn | Ý nghĩa |
|---|---|
| CONFIRMED | Human có thẩm quyền đã quyết định target behavior |
| CURRENT_SYSTEM | Hành vi hiện tại đã được kiểm chứng |
| INFERRED | Suy ra từ evidence, chưa được Human confirm |
| PROPOSED | Đề xuất đang chờ quyết định |
| UNKNOWN | Chưa đủ evidence hoặc còn mâu thuẫn |

Không biến screenshot, current code, prototype hay template content thành CONFIRMED nếu BA chưa xác nhận.

## Human Gate

Gate types:

- **ANSWER** — trả lời câu hỏi được nêu;
- **CONTINUE** — tiếp tục next valid action;
- **APPROVE** — phê duyệt artifact/revision được nêu;
- **REQUEST_CHANGES** — yêu cầu sửa artifact/gate cụ thể;
- **REJECT** — từ chối artifact/gate cụ thể.

Invariant:

~~~text
CONTINUE != APPROVE
ANSWER != APPROVE
validation PASS != APPROVE
artifact generated != APPROVE
~~~

## SRS, diagram, prototype và DOCX liên hệ thế nào?

~~~text
Confirmed Decisions
+ Approved Business Rules
+ Canonical SRS
        │
        ├──> Draw.io business diagrams
        ├──> DOCX delivery using selected template
        └──> Optional prototype / visual contract
~~~

Nếu diagram/prototype phát hiện business question mới:

~~~text
visual finding
→ PROPOSED / UNKNOWN
→ Human clarification
→ update BR/SRS
→ regenerate/update derived artifact
~~~

Không sửa riêng derived artifact để biến nó thành source của business rule mới.

## Visual Gate

Prototype/Figma-derived output có thể cần Human visual review riêng.

Visual approval xác nhận presentation/interaction scope được nêu; nó **không tự approve BA baseline** trừ khi Human nói rõ artifact/revision và approval target.

## Engineering Handoff Gate

Chỉ tạo handoff khi:

- Business Rules/SRS đúng revision đã explicit approve;
- không còn blocking item;
- source paths/hashes hợp lệ;
- không có technical ownership/design fields.

Handoff chuyển sang **Engineering Impact**, nơi mới quyết định WHERE/WHO OWNS.

## Xem thêm

- [Khả năng BA Kit](BA_KIT_CAPABILITIES.md)
- [Hướng dẫn sử dụng](BA_KIT_USAGE_GUIDE.md)
- [SRS và DOCX](SRS_DOCX_GUIDE.md)
- [Draw.io, visual input và prototype](DIAGRAMS_PROTOTYPES.md)
- [Kit contract](KIT_CONTRACT.md)

---

English: [Workflow and Human Gates](../en/BA_KIT_WORKFLOW.md)
