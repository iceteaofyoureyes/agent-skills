# Bắt đầu nhanh với Test Kit V1.1

Test Kit giúp tester biến **BA baseline đã được phê duyệt** thành Test Design và testcase thủ công có truy vết. Agent phân tích, tạo bản nháp và kiểm tra; Human review và quyết định ở hai gate. V1.1 giữ terminal `APPROVED_TESTWARE` → `STOP_V1`, đồng thời cho phép project khai báo testing policy versioned/hash-bound để agent follow convention của nhóm. XMind và Excel chỉ là bản chiếu tùy chọn.

```text
Approved BA Baseline → TEA → Canonical Test Design → Human Design Gate
→ Canonical Testcases → Human Case Gate → APPROVED_TESTWARE → STOP_V1
```

## 1. Cài vào project Codex

Cần Python 3.10+. Khi cài ở project scope, installer tự tạo `_bmad/tea/config.yaml` starter nếu project chưa có và giữ nguyên config hiện hữu nếu đã có; tester không cần tạo file này bằng tay. Operator flow chạy TEA/Katalon trong chính agent session hiện tại, không khởi tạo một agent session lồng bên trong. Installer không tự cài dependency qua mạng. Chạy trong thư mục project cần test:

```powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
```

Trên Linux/macOS, các wrapper Bash tương ứng được hỗ trợ khi có Python 3.10+ và Codex CLI:

```bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh test --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh test --agent codex --scope project
```

Test Kit V1.1 chỉ hỗ trợ **Codex project scope**; ba skill nằm dưới `.agents/skills/`, runtime và pin nằm dưới `.agents/skills/.test-kit/`. `_bmad/tea/config.yaml` là project-owned runtime config, không thuộc package inventory và không bị uninstall/reinstall ghi đè. Starter dùng path tương đối cố định `.test-kit/runtime` để portable giữa các máy; file này không được retarget theo CR hoặc run. Với project dùng Git, review rồi commit file này để toàn team dùng cùng một TEA runtime contract; không commit machine-local absolute paths. BA Kit có thể cài cùng project, nhưng không bắt buộc nếu project đã có BA handoff hợp lệ. `TEST_KIT_CODEX_COMMAND` là override tường minh; nếu không đặt, resolver tìm `codex` trên `PATH`. Override sai sẽ báo lỗi, không tự tìm đường cài đặt riêng của máy.

Nếu cần rule/template riêng của project, bootstrap `.test-kit/project.yaml` và rule files theo [Project Customization & Policy](TEST_KIT_CUSTOMIZATION.md). Policy chỉ là testing guidance, không thay BA/Design/execution authority. Doctor `READY` nghĩa package bắt buộc và các hợp đồng đã kiểm tra còn khớp; `DEGRADED` nghĩa có capability tùy chọn thiếu; `FAIL` nghĩa phần bắt buộc hoặc tính toàn vẹn lỗi. Doctor có thể liệt kê `DEPENDENCY_MISSING` cho XMind/Excel tùy chọn trong khi core vẫn dùng được. Xem [cài đặt và xử lý lỗi](INSTALLATION.md).

## 2. UX vận hành giống BA Kit

Sau install + doctor, Human chỉ cần nói mục tiêu, ví dụ:

```text
Tạo Test Design cho CR-DWC-DEMO-001 từ BA baseline đã được approve.
```

Agent tự tìm approved handoff, tạo internal run dưới `.test-kit/runs/<feature-id>/...`, chạy Test Kit `prepare-design`, thực thi TEA trong cùng session bằng run-local resolved config, rồi chạy `finalize-design`. Human không cần biết Python module, run directory, TEA flag, adapter manifest hay launcher nội bộ.

```text
Human request
→ Test Kit PREPARE
→ TEA capability (same session)
→ Test Kit FINALIZE
→ Canonical Test Design
→ DESIGN_REVIEW
→ Human Gate
```

Nếu preflight, capability, normalizer hoặc validator lỗi, agent dừng và báo lỗi. Không tạo compatibility shim hay sửa runtime trong run.

## 3. Cung cấp BA baseline đã duyệt

Cung cấp `engineering-handoff.yml` với `ba_baseline.status: APPROVED_FOR_ENGINEERING` và đúng ba nguồn có đường dẫn/SHA-256: Business Rules, functional SRS, BA decisions. Test Kit kiểm tra các file hiện tại khớp handoff. Bản nháp, một câu trả lời chưa được approve hoặc chỉ có requirement rời rạc chưa phải đầu vào production hợp lệ.

```text
Tạo Test Design cho feature này từ approved BA baseline tại <đường dẫn engineering-handoff.yml>.
Chọn run directory riêng trong project. Không invent behavior chưa được BA approve.
Giữ UNKNOWN và nêu rõ scenario nào phải deferred.
```

TEA là skill phân tích/tư vấn được bundle cùng Kit. Adapter chuyển BA baseline sang đầu vào TEA, giữ output gốc làm evidence, rồi chuẩn hóa/validate thành **Canonical Test Design**. TEA không tự approve Design. Nếu chuẩn hóa hoặc validator lỗi, agent báo finding và không đẩy qua gate.

## 4. Review Test Design, rồi quyết định rõ ràng

```text
REVIEW only Canonical Test Design của run này.
Đối chiếu từng scenario với FR/BR, expected_behavior và open_questions.
Không sửa artifact và không chuyển gate.
```

Nếu cần sửa: `REQUEST_CHANGES cho Design revision <revision>: <feedback cụ thể>.` Nếu chấp nhận:

```text
Tôi APPROVE Canonical Test Design <artifact_id>, revision <revision>,
đúng snapshot đang ở DESIGN_REVIEW, làm coverage baseline cho testcase.
```

Host phải xác thực Human và lưu receipt gắn **artifact ID, revision, semantic SHA-256 và BA input refs hiện tại**. Câu nói `Tiếp tục`, `OK`, `PASS` hoặc kết quả validator `PASS` không tạo approval. Agent không thể tự ký receipt. Chỉ sau gate hợp lệ workflow mới là `APPROVED_DESIGN`.

## 5. Tạo và review testcase

```text
Từ APPROVED_DESIGN của run này, dùng create-test-cases để tạo canonical manual testcases.
Giữ requirement_refs và test_design_refs; tách Test Data ở testcase/step đúng nguồn.
Báo execution dependency nào còn thiếu contract được duyệt.
```

Katalon `create-test-cases` là skill nguồn đã pin; output của nó là đầu vào adapter, không phải canonical artifact hay quyết định Human. Adapter chuẩn hóa và kiểm tra testcase trước `CASE_REVIEW`.

```text
REVIEW only Canonical Testcases trong CASE_REVIEW.
Kiểm tra Precondition, action/Expected Result theo thứ tự, Test Data,
traceability, UNKNOWN và execution_dependencies. Không approve lúc này.
```

Nếu có lỗi, yêu cầu `REQUEST_CHANGES cho testcase revision <revision>: <feedback>`. Khi thực sự chấp nhận:

```text
Tôi APPROVE Canonical Testcases <artifact_id>, revision <revision>,
đúng snapshot đang ở CASE_REVIEW làm manual testware cho feature này.
```

Case Gate yêu cầu receipt của Human đã xác thực, đúng BA/Design refs hiện hành và không còn **material OPEN execution dependency**. Nếu điều kiện thiếu, approval bị từ chối; không suy ra testware đã sẵn sàng chạy. Khi hợp lệ, runtime ghi `APPROVED_TESTWARE` rồi chuyển `STOP_V1`.

## 6. Xuất bản chiếu khi Human yêu cầu

- Từ **Canonical Test Design đã duyệt**: yêu cầu XMind. Cài Node.js 18+/npm 9+ rồi chạy `npm ci` trong `.agents/skills/.test-kit/tooling/xmind/`. XMind V1 dùng profile trình bày đã pin, chưa có input template XMind do Human cung cấp.
- Từ **Canonical Testcases đã duyệt** sau Case Gate: yêu cầu Excel. Cài dependency vào đúng Python environment: `python -m pip install --require-hashes -r .agents/skills/.test-kit/tooling/requirements-excel.lock`. Có thể đưa template `.xlsx` hợp lệ; xem [chính sách template](TEST_KIT_CAPABILITIES.md#template-và-bản-chiếu).

Projection ghi vào output directory do caller chọn, cạnh run artifact tương ứng; trace và hash nằm trong manifest bên ngoài (`*.projection.json`). Không sửa file XMind/Excel để thay canonical semantics. Muốn chỉnh nội dung test, quay lại canonical source/revision và Human Gate thích hợp.

## 7. Dừng ở V1

`APPROVED_TESTWARE` là sự chấp nhận **testware thủ công của chính feature/snapshot đã review**, không phải kết quả chạy test hay approval cho mọi project. `TEST_ONLY` là fixture/evidence dùng cho kiểm thử Kit, có `not_for_production: true`; nó không thay receipt Human production. Playwright/API automation, thực thi, evidence, flaky management và triage thuộc **Automation Test V2**.

Đi tiếp: [Khả năng](TEST_KIT_CAPABILITIES.md) · [Tình huống sử dụng](TEST_KIT_USAGE_GUIDE.md) · [Workflow/Human Gates](TEST_KIT_WORKFLOW.md) · [Ví dụ CR-001](../../kits/test/examples/CR-001/README.md).
