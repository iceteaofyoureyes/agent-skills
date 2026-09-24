# CR-001 — Ví dụ Draw.io, DOCX và visual delivery

File này không thêm business rule mới. Nó minh họa cách dùng các capability delivery/visual **sau khi đã có approved semantics** trong các file trước.

## 1. Draw.io lifecycle

Nguồn semantic:

- BR-008: Scheduled, Cancelled, Completed; create → Scheduled; chỉ Scheduled được action;
- BR-009: Cancel giải phóng slot;
- BR-010: Complete tạo chính xác một Visit;
- BR-011: không hard-delete.

Prompt mẫu:

~~~text
Từ BR-008..BR-011 trong 03-approved-business-rules.md,
tạo docs/diagrams/CR-001-appointment-lifecycle.drawio.

Yêu cầu:
- editable .drawio;
- PNG preview;
- label BR tương ứng;
- không thêm status/transition chưa confirmed.
~~~

Expected semantic shape:

~~~text
Create
  ↓
Scheduled
  ├── Cancel ───→ Cancelled
  │               releases slot
  └── Complete ─→ Completed
                  creates exactly one Visit
~~~

Diagram là derived artifact; nếu Human đổi lifecycle rule, BR/SRS đổi trước rồi diagram mới update.

## 2. Draw.io booking flow

Nguồn semantic: BR-003..BR-007, BR-013.

Prompt:

~~~text
Tạo business flowchart cho create/reschedule Appointment.
Chỉ thể hiện business decisions:
- validate required data;
- future start;
- duration > 0;
- same-Veterinarian Scheduled conflict;
- [start,end), touching allowed;
- reschedule excludes itself;
- only non-conflicting appointment is saved.

Không mô tả API, transaction, DB constraint hay locking.
~~~

Điểm quan trọng: “chỉ save non-conflicting appointment” là business outcome; cơ chế atomicity thuộc Engineering.

## 3. SRS DOCX theo template

Example repository **không chứa company SRS template**.

Giả sử project thật có:

~~~text
docs/templates/COMPANY_SRS_TEMPLATE.docx
~~~

và canonical SRS:

~~~text
docs/srs/CR-001.md
~~~

Prompt:

~~~text
Tạo docs/output/CR-001-SRS.docx từ docs/srs/CR-001.md.
Dùng docs/templates/COMPANY_SRS_TEMPLATE.docx.
Giữ layout/style.
Maximum duration vẫn UNKNOWN.
Không invent filter/sort/pagination đang unresolved.
~~~

Nếu template có section mà baseline không đủ dữ liệu, report/giữ UNKNOWN thay vì tự fill.

## 4. Nếu không có template

~~~text
Xuất canonical SRS thành generic DOCX để review nội bộ.
Dùng heading/table rõ ràng.
Không gọi output này là company-template SRS.
~~~

## 5. Visual/Figma lane

CR-001 fixture không cung cấp screenshot/Figma nên example **không giả lập UI**.

Nếu một project thật cung cấp screenshot màn Appointment:

~~~text
Review screenshot cùng canonical SRS.
Tách:
- observed fields/actions;
- mismatch với SRS;
- missing decisions;
- visual proposal.

Chưa update SRS cho tới khi Human trả lời.
~~~

Ví dụ nếu ảnh có nút Delete nhưng BR-011 nói no hard delete, đây là mismatch cần Human review — không được tự đổi BR.

## 6. Prototype lane — optional

Sau khi interaction semantics đủ rõ:

~~~text
Từ SRS đã confirmed và visual reference, tạo local prototype.
Render normal/empty/error states đã được xác định.
Đây là visual proposal; không thay Business Rules.
~~~

Prototype cần Human visual gate riêng.

## 7. Thứ tự authority

~~~text
Human decisions / BR / canonical SRS
        ↓
Draw.io / DOCX / prototype
~~~

Không đi ngược:

~~~text
DOCX/diagram/prototype
        ✗
tự sinh business rule mới
~~~

Xem thêm:

- [SRS và DOCX](../../../../../docs/vi/SRS_DOCX_GUIDE.md)
- [Draw.io, visual input và prototype](../../../../../docs/vi/DIAGRAMS_PROTOTYPES.md)
