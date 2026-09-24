# Draw.io, visual input và prototype

BA Kit có required capability **drawio-skill** và optional UX/UI capabilities. Trang này mô tả cách dùng chúng đúng ranh giới BA.

## 1. Draw.io trong BA Kit dùng để làm gì?

drawio-skill có capability rất rộng, nhưng trong BA phase nên dùng chủ yếu để biểu diễn **business behavior đã có authority**.

Các loại phù hợp:

| Loại | Dùng khi |
|---|---|
| Business process flowchart | Mô tả các bước và decision trong nghiệp vụ |
| Swimlane | Làm rõ actor/role nào thực hiện bước nào |
| User/task flow | Mô tả đường đi người dùng ở mức functional |
| State/lifecycle | Mô tả trạng thái và transition đã confirmed |
| Decision tree | Mô tả rule/nhánh quyết định |
| Context/interaction map | Mô tả interaction ở mức nghiệp vụ, không phải target architecture |
| Existing diagram review | Review/edit/sync .drawio hiện có |
| Image/whiteboard → editable | Dựng lại screenshot/ảnh bảng trắng thành .drawio để review |

## 2. Ví dụ flowchart từ Business Rules

Giả sử baseline confirmed:

~~~text
- Create Appointment → Scheduled
- Only Scheduled can be cancelled/completed
- Cancel → Cancelled and releases slot
- Complete → Completed and creates exactly one Visit
~~~

Có thể yêu cầu:

~~~text
Từ các Business Rules đã approved, tạo Draw.io lifecycle cho Appointment.
Output editable: docs/diagrams/appointment-lifecycle.drawio.
Thêm PNG preview.
Không thêm transition chưa được confirmed.
~~~

Expected semantic shape:

~~~text
          ┌───────────┐
Create ──▶│ Scheduled │
          └─────┬─────┘
                │
        ┌───────┴────────┐
        │                │
      Cancel          Complete
        │                │
        ▼                ▼
  ┌───────────┐     ┌───────────┐
  │ Cancelled │     │ Completed │
  └───────────┘     └───────────┘
      releases          creates
        slot          exactly 1 Visit
~~~

Draw.io phải phản ánh nguồn semantic; diagram không được tự thêm Rescheduled/No-show/Pending nếu BA chưa xác nhận.

## 3. Output của drawio-skill

Output chính:

~~~text
diagram.drawio
~~~

Có thể export thêm khi tool/runtime hỗ trợ:

~~~text
diagram.png
diagram.svg
diagram.pdf
~~~

Skill có structural validation và workflow kiểm tra visual. File .drawio là editable source; PNG/PDF chỉ là derivative delivery artifact.

## 4. Review và update diagram

Review-only:

~~~text
Review appointment-flow.drawio so với Business Rules hiện tại.
Chỉ report mismatch và ambiguous edge, chưa sửa file.
~~~

Update:

~~~text
BR-012 đã được Human approve.
Update appointment-flow.drawio chỉ ở phần liên quan BR-012.
Giữ layout/style khác nếu không cần đổi.
~~~

Nếu một thay đổi trong diagram tạo business rule mới, **không update semantics từ diagram một cách âm thầm**. Đưa nó thành PROPOSED/UNKNOWN và hỏi Human trước.

## 5. Technical diagrams và BA boundary

drawio-skill bản thân có thể tạo architecture, ERD, C4, network, API diagram...

Nhưng BA Kit không được dùng capability đó để quyết định target:

- service boundary;
- API shape;
- DB schema;
- event architecture;
- deployment;
- locking/transaction.

Có thể diagram **CURRENT_SYSTEM** nếu đang document as-is và có evidence, nhưng target technical design thuộc Engineering Impact/Dev.

## 6. Visual input: Figma, screenshot, image, PDF, HTML

Visual source có thể dùng để:

- nhận diện screen/section;
- field/label/control nhìn thấy;
- action nhìn thấy;
- trạng thái/empty/error/loading nếu artifact thể hiện;
- navigation relationship nhìn thấy;
- so sánh với requirement;
- tạo danh sách gap cần BA xác nhận;
- viết UI behavior vào SRS;
- dựng visual/prototype.

### Figma

BA Kit không bundle Figma connector.

Nếu runtime có Figma integration và Human đã cấp quyền, có thể dùng link/file tương ứng.

Nếu không:

~~~text
Figma
→ export screenshot / image / PDF / HTML reference
→ đưa local artifact cho agent
~~~

Đừng để một link Figma không truy cập được trở thành lý do agent tự đoán UI.

## 7. Visual evidence không phải business authority

Từ screenshot có nút **Delete**, agent có thể nói:

~~~text
OBSERVED VISUAL:
Có action Delete trong ảnh.
~~~

Agent không được tự kết luận:

~~~text
CONFIRMED:
User được hard-delete record.
~~~

Cần hỏi BA xem action là gì, ai có quyền, soft/hard delete, confirmation, trạng thái nào áp dụng.

Tương tự với:

- required field;
- validation;
- role/permission;
- sort default;
- page size;
- backend side effect.

## 8. Từ visual source sang SRS

Prompt:

~~~text
Đây là screenshot màn danh sách công văn và requirement CR-208.

1. Liệt kê các UI element nhìn thấy.
2. Đối chiếu requirement.
3. Hỏi các gap: search/filter, sort, pagination/page size, row action, permission, empty/error/loading.
4. Chỉ sau khi tôi trả lời, update phần UI Behavior của canonical SRS.
~~~

Đây là use case đã chốt của BA Kit: agent hỗ trợ BA nhìn ra case chưa cover, không thay BA quyết định.

## 9. Prototype — optional capability

Khi optional skills có sẵn:

~~~text
Approved BA semantics
        ↓
product-design-and-ux
        ↓
interaction/task/state contract
        ↓
frontend-design
        ↓
local prototype
        ↓
Playwright / visual review
        ↓
Human visual gate
~~~

Prototype có thể là local HTML/React hoặc hình thức phù hợp với project, nhưng phải được coi là **prototype**, không phải production implementation.

Nếu visual direction chưa được xác nhận, output là **PROPOSED**.

## 10. Các trạng thái nên prototype

Với một màn functional, đừng chỉ dựng happy path. Khi requirement có liên quan, nên review:

- normal/data state;
- empty state;
- loading;
- validation error;
- permission/disabled state;
- destructive confirmation;
- success/error feedback;
- desktop/mobile/reflow khi in scope.

Không tự thêm state nghiệp vụ không có evidence; state UI cần thiết nhưng chưa rõ phải được đưa thành question/proposal.

## 11. Prompt mẫu

### Draw.io flowchart

~~~text
Tạo Draw.io business flow từ Business Rules BR-001..BR-008.
Output .drawio editable + PNG preview.
Gắn label BR ở node/edge phù hợp.
Không thêm business rule mới.
~~~

### Swimlane

~~~text
Tạo swimlane cho quy trình duyệt công văn theo actor đã confirmed.
Nếu chưa rõ actor nào sở hữu một bước, để UNKNOWN và report thay vì tự gán.
~~~

### Visual review

~~~text
Review screenshot/Figma export này so với SRS hiện tại.
Tách: observed visual / mismatch / missing decision / proposal.
Chưa sửa SRS.
~~~

### Prototype

~~~text
Từ SRS đã confirmed và screenshot tham chiếu, tạo local prototype cho desktop/mobile.
Đây là visual proposal; không thay đổi business rules.
Render các state chính để tôi review.
~~~

---

English: [Draw.io, visual input, and prototypes](../en/DIAGRAMS_PROTOTYPES.md)
