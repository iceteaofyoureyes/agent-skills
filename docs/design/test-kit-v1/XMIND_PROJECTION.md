# Test Kit V1 — Human-facing XMind projection (optional)

## Tiếng Việt

XMind là bản chiếu một chiều, tùy chọn của **một Canonical Test Design đã được duyệt**. Human chủ động yêu cầu tạo file. Canonical Test Design vẫn là nguồn chuẩn; XMind không đổi workflow, coverage hay business semantics.

### Điều kiện và cách gọi

Production chỉ xuất khi snapshot còn hiện hành, workflow là `APPROVED_DESIGN`, và receipt Design Gate thật đã được host xác thực cho đúng revision, semantic SHA-256 và input refs. Hàm production đọc receipt đã lưu; không nhận receipt approval do caller truyền vào. `DESIGN_REVIEW` và receipt `TEST_ONLY` đều bị từ chối.

Cài dependency đã khóa chính xác trước khi sử dụng:

```powershell
npm ci --prefix tooling/xmind --ignore-scripts
```

Host gọi `export_approved_design_xmind(...)` sau khi Human yêu cầu xuất và chuyển cơ chế xác thực Human hiện có. Acceptance dùng API `export_test_only_design_xmind(...)` riêng; fixture giữ trong `benchmark/`, còn output dùng thư mục tạm hoặc `.work/benchmark-runs/`.

### Presentation profile

`HUMAN_FACING_XMIND_PROFILE` tạo root từ đúng feature ID/title trong BA đã duyệt, ví dụ `CR-001 — Appointment Scheduling`. Nhánh dưới root là nhãn chức năng thân thiện với tester, được ghép tường minh với cụm từ nguồn trong approved SRS FR-001…FR-006. Mapping nằm trong [profile config](../../../tooling/pins/xmind-human-facing-profile-v1.json); exporter kiểm tra từng cụm từ nguồn có trong BA. Priority và TEA hierarchy không dùng làm nhóm hiển thị.

Scenario hiện theo dạng `Kiểm tra ...`; canonical `scenario_title` được giữ nguyên trong projection manifest bên ngoài. Một số tên deferred có nhãn trình bày tường minh để bỏ phần tham chiếu kỹ thuật. Expected behavior hiện trực tiếp trên canvas dưới dạng `MM: <expected_behavior>` và giữ nguyên câu chữ canonical. Scenario deferred vẫn hiện với warning `⚠ Chờ BA: <unresolved topic>`. Các warning tương đương có thể gộp trên canvas; mọi open-question record đầy đủ vẫn được giữ riêng trong manifest.

Profile đặt `layout = LOGIC_CHART_RIGHT`. `machine_notes_allowed`, `machine_labels_allowed` và `machine_visible_metadata_allowed` đều là `false`; `traceability_location = EXTERNAL_PROJECTION_MANIFEST`. Scenario dùng component ID nội bộ của XMind để liên kết với `design_id`; ID không hiện trên canvas.

Nếu refs ánh xạ tới đúng một chức năng, resolver dùng nhóm đó. Mapping BR-to-function hoặc scenario override chỉ dùng theo cấu hình presentation đã kiểm tra với approved BA/canonical text. Nếu thiếu hoặc mơ hồ, xuất bị từ chối bằng `CANNOT_PROJECT_HUMAN_PROFILE`; không dùng LLM để suy luận.

### Trace và kiểm tra

Projection manifest bên ngoài XMind giữ trace đầy đủ: ID, canonical scenario title, hierarchy_path, functional group ref, expected behavior, requirement refs, trạng thái resolved/deferred và toàn bộ open-question records. Manifest cũng chứa SHA-256 của chính file `.xmind`; validator đối chiếu Canonical Test Design với manifest rồi xác nhận hash và nội dung `content.json`. XMind không chứa Notes hoặc machine labels.

Exporter mở lại `.xmind` đã tạo và so sánh từng topic với Canonical Test Design. `XMIND_SEMANTIC_DIFF` phải là `PASS`. Cùng thư mục có tree preview UTF-8 được dựng từ package `.xmind` đã serialize; preview chỉ là review evidence, không phải nguồn chuẩn. Manifest giữ `DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH`.

## English

XMind is an optional, one-way projection of **one approved Canonical Test Design**. A Human explicitly requests it. Canonical Test Design remains authoritative; XMind does not change workflow, coverage, or business semantics.

### Preconditions and trigger

Production export requires a current snapshot, workflow state `APPROVED_DESIGN`, and a real Design Gate receipt authenticated by the host for the exact revision, semantic SHA-256, and input refs. The production function reads the persisted receipt and accepts no caller-supplied approval. `DESIGN_REVIEW` and `TEST_ONLY` receipts are rejected.

Install the exactly locked dependency with `npm ci --prefix tooling/xmind --ignore-scripts`. After a Human requests export, the host calls `export_approved_design_xmind(...)` with its existing Human authenticator. Acceptance uses the separate `export_test_only_design_xmind(...)` API; fixtures stay under `benchmark/`, while output uses an OS temporary directory or `.work/benchmark-runs/`.

### Presentation profile

`HUMAN_FACING_XMIND_PROFILE` names the root from the approved BA feature ID/title, such as `CR-001 — Appointment Scheduling`. Its children use tester-facing function labels explicitly mapped to source phrases in approved SRS requirements FR-001 through FR-006. The [profile config](../../../tooling/pins/xmind-human-facing-profile-v1.json) checks each source phrase against the BA text. Priority and TEA hierarchy do not define visible groups.

Scenario topics use the `Kiểm tra ...` presentation style; the exact canonical `scenario_title` remains in the external projection manifest. Explicit deferred-title labels remove technical references. Each non-null expected behavior appears directly on the canvas as `MM: <expected_behavior>` with the canonical wording intact. Deferred scenarios remain visible with `⚠ Chờ BA: <unresolved topic>` warnings. Equivalent warnings may be deduplicated on the canvas, while every full open-question record remains separate in the manifest.

The profile sets `layout = LOGIC_CHART_RIGHT`. `machine_notes_allowed`, `machine_labels_allowed`, and `machine_visible_metadata_allowed` are `false`; `traceability_location = EXTERNAL_PROJECTION_MANIFEST`. Scenario topics use XMind component IDs for internal design identity; those IDs do not appear on the canvas.

When refs map to one function, the resolver uses that function. BR-to-function mappings and scenario overrides are explicit presentation config checked against approved BA or canonical text. Missing or ambiguous mappings fail with `CANNOT_PROJECT_HUMAN_PROFILE`; no LLM infers groups.

### Trace and validation

The external projection manifest holds the full trace: design ID, canonical scenario title, hierarchy_path, functional group ref, expected behavior, requirement refs, resolved/deferred state, and every open-question record. It also contains the generated `.xmind` SHA-256. Validation compares Canonical Test Design to the manifest, then checks the hash and parsed `content.json`. The XMind contains no Notes or machine labels.

The exporter reopens the generated `.xmind` and compares each topic with Canonical Test Design. `XMIND_SEMANTIC_DIFF` must be `PASS`. A UTF-8 tree preview is generated from the serialized `.xmind` beside it; the preview is review evidence, not an authority. The manifest classifies the map as `DERIVED_PROJECTION_NOT_SOURCE_OF_TRUTH`.
