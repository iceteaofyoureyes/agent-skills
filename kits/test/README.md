# Test Kit V1

**Test Kit = HOW DO WE PROVE IT.** Test Kit V1 chuyển một BA baseline đã được phê duyệt thành manual testware có Human review. Human sở hữu cả hai approval gate.

```text
Approved BA Baseline
→ TEA analysis
→ Canonical Test Design
→ Human Design Gate
→ Canonical Testcases
→ Human Case Gate
→ APPROVED_TESTWARE
→ STOP_V1
```

Các projection tùy chọn chỉ được tạo khi Human yêu cầu và là view một chiều từ canonical artifacts:

```text
Canonical Test Design → XMind projection
Canonical Testcases   → Excel projection
```

Automation planning, execution, triage và automated evidence thuộc **Automation Test V2**, không nằm trong V1.

## Bắt đầu

Bộ operator guide đầy đủ được duy trì trong source repository và không được copy toàn bộ vào package cài đặt. README này đủ ngữ cảnh cơ bản khi được cài thành `.test-kit/README.md`.

Trong repository, xem:

- Project customization & policy (V1.1) — `docs/vi/TEST_KIT_CUSTOMIZATION.md`
- Quick Start — `docs/vi/TEST_KIT_QUICKSTART.md`
- Capabilities và boundary — `docs/vi/TEST_KIT_CAPABILITIES.md`
- Usage Guide theo tình huống — `docs/vi/TEST_KIT_USAGE_GUIDE.md`
- Workflow và Human Gates — `docs/vi/TEST_KIT_WORKFLOW.md`
- Ví dụ CR-001 — `kits/test/examples/CR-001/README.md`
- [Installation và troubleshooting](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/INSTALLATION.md) — `docs/vi/INSTALLATION.md`
- [Provenance và license](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/PROVENANCE.md) — `docs/vi/PROVENANCE.md`
- [Release status](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/RELEASE.md) — `docs/vi/RELEASE.md`
- English overview — `docs/en/TEST_KIT_README.md`

Repository: https://github.com/iceteaofyoureyes/agent-skills

## Điều kiện và cài đặt

Test Kit V1 hỗ trợ Codex ở project scope. Core cần Python 3.10+ và project có `_bmad/tea/config.yaml` tương thích với TEA skill đã pin. TEA và Katalon skills đã được bundle; install không tải lại chúng. Production operator flow chạy các capability ngay trong agent session hiện tại; nested Codex launcher không còn là UX vận hành chuẩn. Project TEA config là stable team config; Test Kit sinh run-local resolved config và không được sửa project config theo CR/run.

Từ project đích, chạy script từ Agent Skills checkout:

```powershell
& '<path-to-agent-skills>\tooling\install.ps1' test --agent codex --scope project
& '<path-to-agent-skills>\tooling\doctor.ps1' test --agent codex --scope project
```

```bash
<path-to-agent-skills>/tooling/install.sh test --agent codex --scope project
<path-to-agent-skills>/tooling/doctor.sh test --agent codex --scope project
```

Doctor kiểm tra integrity của package đã cài và phát hiện local drift hoặc metadata hỏng. Reinstall giữ lại managed files đã bị local edit; các edit đó không tự trở thành expected package bytes. Uninstall xóa các file do Test Kit sở hữu nếu chúng vẫn khớp expected bytes và giữ nguyên file không thuộc Test Kit. Xem [Installation](https://github.com/iceteaofyoureyes/agent-skills/blob/main/docs/vi/INSTALLATION.md) để biết chi tiết.

## Workflow và authority

**TEA là analysis/advisory**, không phải Test Design authority. Test Kit chuẩn bị input, agent hiện tại chạy TEA cùng session, rồi runtime finalize/validate **Canonical Test Design** và dừng ở `DESIGN_REVIEW` để Human review. Chỉ approval hợp lệ cho đúng snapshot mới cho phép chuyển sang testcase generation.

Pinned Katalon skill hỗ trợ sinh testcase; adapter validate **Canonical Testcases** rồi dừng ở `CASE_REVIEW`. Chỉ Human approval receipt hợp lệ cho đúng snapshot, đồng thời không còn material open execution dependency, mới tạo trạng thái `APPROVED_TESTWARE` và `STOP_V1`.

`ANSWER`, `REVIEW`, `REQUEST_CHANGES`, `CONTINUE` và `APPROVE` là các ý định khác nhau. `Continue`, `Next`, `OK` hoặc `PASS` không tự động có nghĩa là approval. Agent không tự approve.

Nếu BA baseline còn behavior chưa được quyết định, Test Kit giữ `UNKNOWN`/open question; không invent expected behavior để làm testcase trông hoàn chỉnh.

## Human Gate persistence trên Windows

Design/Case APPROVE và REQUEST_CHANGES preflight toàn bộ output trước receipt. Persistence dùng
immutable transaction journal, write-if-same-or-absent và atomic workflow commit. Host có thể
resume exact authenticated receipt sau internal failure; không cần Human submit decision lần hai.
Exact completed replay chỉ success sau khi xác minh artifacts/state; receipt khác hoặc byte conflict
bị reject. Không xóa receipt hay hand-edit state để recover.

Path budget mặc định Windows là 259 UTF-16 code units cho file, 247 cho parent directory; preflight
không yêu cầu bật registry LongPaths. Projection nội bộ mới dùng approved.json/changes.json và
draft revisions dùng semantic.json/design.json/cases.json. Existing legacy files được đọc/resume
in-place; tên canonical promoted artifacts không đổi. Không chạy recovery trên frozen Golden cũ.

## XMind và Excel

XMind là projection một chiều từ Canonical Test Design. V1 dùng pinned presentation profile và **không nhận Human-supplied XMind template**; mapping/grouping mơ hồ trả `CANNOT_PROJECT_HUMAN_PROFILE`.

Excel là projection một chiều từ Canonical Testcases và hỗ trợ precedence:

```text
HUMAN_SUPPLIED_APPROVED_TEMPLATE
→ PROJECT_TEMPLATE
→ DEFAULT_TEMPLATE
```

Mapping template mơ hồ trả `CANNOT_PROJECT_TEMPLATE`.

XMind cần Node.js/npm và pinned SDK; Excel cần các Python projection dependencies đã hash-lock. Chỉ bootstrap capability tùy chọn khi thực sự được yêu cầu. Cả hai projection không thay đổi canonical artifacts hay gate state và không có reverse-import authority trong V1.

## Phạm vi V1

V1 tạo Human-reviewed Test Design và manual testcases, kèm XMind/Excel projection tùy chọn. V1 **không**:

- chạy automated tests;
- tạo execution evidence tự động;
- quản lý flaky tests;
- triage failure tự động;
- tự động hóa defect handling.

Các capability đó thuộc **Automation Test V2**.

`TEST_ONLY` artifact không phải production-approved testware. Project thật vẫn cần Human gate hợp lệ cho snapshot hiện hành trước khi coi testware là approved.


## Integrated production contract
Same-session prepare-design → current-session pinned TEA → finalize-design; prepare-cases → current-session create-test-cases → finalize-cases. Nested Codex is legacy benchmark only, not a production core dependency.
UI features start from the same approved Delivery Manifest as Dev. Agent supplies --delivery internally during Design preparation; Case preparation inherits that exact manifest.
Typed SEMANTIC_ORACLE gaps block testware approval; environment, fixture, locator, tooling and observation needs block execution only.
After a valid Human gate, promote exact semantic snapshots with tooling.lib.testware_promotion. See docs/vi/SDLC_SUITE_CONTRACT.md for the project execution extension and profile/ignore setup.
