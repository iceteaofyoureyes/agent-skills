# Quy trình BA Kit và Human Gate

BA Kit không phải một pipeline cứng bắt mọi yêu cầu chạy từ đầu đến cuối. Workflow chọn **điểm bắt đầu an toàn nhất** theo loại công việc:

- **brownfield** — requirement liên quan hệ thống/code hiện tại;
- **greenfield** — chưa có current system cần discover;
- **document-only** — review/edit SRS/DOCX/diagram đã có;
- **visual-assisted** — có screenshot/Figma/PDF/prototype làm visual evidence.

## Core semantic flow

BA VNext dùng lifecycle chuẩn cho mọi baseline mới:

```text
DRAFT → VALIDATED → HUMAN_REVIEW → APPROVED_BASELINE
```

Validator PASS chỉ là bằng chứng kiểm tra. HUMAN_REVIEW đóng băng đúng manifest,
revision và input hashes. APPROVED_BASELINE yêu cầu receipt bên ngoài bind đúng
identity/revision/semantic SHA-256 và được trusted host xác thực Human.
ANSWER, CONTINUE, artifact được tạo, Foundation READY và UX approval không phải
BA baseline approval. Candidate đổi bytes phải có revision mới và approval mới.

Workflow state schema 2 là RUNTIME; các bước Business Rules/SRS bên dưới là
activity/sub-stage. Handoff schema 2 bind đúng candidate + receipt + Decisions/BR/SRS,
Shared Foundation Knowledge Impact và Foundation ref nếu có; mỗi lần consume
phải revalidate proof. State/handoff V1 vẫn đọc được dưới LEGACY_COMPAT và không
đủ bằng chứng để cấp approval VNext. Các import Shared Core cũ, Delivery Manifest V2,
UX receipt V2 và atomic skills giữ nguyên contract.

BR-* là Business Rule; FR-* là Functional Requirement. Giữ ID cho cùng semantic
item, lưu ID đã retired và không tái sử dụng cho ý nghĩa mới. BAREF:* chỉ là
structural/provenance locator, tuyệt đối không tạo mandatory coverage. Human
decision mới phải bind BR/SRS đã cập nhật trước readiness. BA sở hữu WHAT;
technical owner, API/event/DB design, service boundaries, locking/transaction và
architecture decisions thuộc downstream.

Consume Foundation inventory/context khi có. CURRENT_SYSTEM/INFERRED không tự
thành target requirement; mâu thuẫn thành gap cho Human clarification. Greenfield
bắt đầu từ Human intent và câu hỏi/quyết định rõ ràng. Không bắt buộc Foundation
hoàn hảo nếu bounded feature evidence đủ. Knowledge Impact bind affected/targets
cho product/domain/architecture/testing vào baseline/handoff và route đánh giá
kỹ thuật cho Engineering/Test mà không mô tả giải pháp HOW.

Trusted host dùng [VNext executable contracts](../../ba-workflow/references/baseline-vnext.md).
CLI read-only không xác thực Human và fail closed với approved state/handoff
VNext khi thiếu trusted authenticator. Candidate mới làm mất hiệu lực derived refs;
snapshot đã approve vẫn giữ nguyên bytes và output liên quan phải refresh.

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
    I --> L[Test Kit V1: trực tiếp từ Approved BA Baseline]
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
| Handoff | Revalidate đúng baseline/receipt/sources | Xác thực quyết định đúng baseline | engineering-handoff.json (VNext) |

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

Visual approval xác nhận presentation/interaction scope được nêu. BA baseline approval yêu cầu receipt riêng bind đúng snapshot và được trusted host xác thực Human.

## Engineering Handoff Gate

Chỉ tạo handoff khi:

- candidate đúng revision đã APPROVED_BASELINE với receipt được trusted host xác thực Human;
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
