# Kiến trúc và lifecycle hiện hành

Đây là giải thích chuẩn về lifecycle tích hợp. Các Kit liên kết về đây thay vì định nghĩa lifecycle khác. Manifest và schema là nguồn contract: [suite](../../tooling/sdlc-suite.json), [acceptance](../../tooling/sdlc-suite-acceptance.yaml).

## Quyền quyết định và ownership

Thứ tự authority: (1) quyết định Human đã duyệt, (2) invariant Shared SDLC, (3) Project Policy/chỉ dẫn dự án, (4) cơ chế Kit/atomic skill, (5) runtime defaults.

| Vai trò | Sở hữu |
|---|---|
| BA | WHAT — hành vi nghiệp vụ được duyệt |
| Engineering / Dev | WHERE, WHO OWNS, HOW — phạm vi repo, impact, technical decisions, implementation |
| Test | Bằng chứng rằng hành vi đã duyệt được kiểm thử |
| Human | Quyết định ngữ nghĩa cuối cùng và approval theo exact snapshot |

Artifact có lớp CANONICAL, DERIVED, RUNTIME, EVIDENCE, hoặc HANDOFF_MANIFEST. Derived output, runtime state, evidence và handoff không tự trở thành authority.

## Project Foundation

Project Foundation là workflow Shared SDLC, không phải Kit vai trò thứ tư. Ba mode là GREENFIELD_BOOTSTRAP, BROWNFIELD_RECOVERY, FOUNDATION_REFRESH; profile là MINIMAL, STANDARD, EXTENDED. Kiến trúc dựa trên arc42 Standard, khái niệm ISO 42010, C4 và ADR.

Brownfield phân biệt CURRENT_SYSTEM, CONFIRMED, INFERRED, UNKNOWN. Greenfield phân biệt APPROVED_TARGET, PROPOSED, DEFERRED, UNKNOWN. PROJECT_FOUNDATION_READY chỉ chứng minh Foundation readiness. Nó không duyệt nghiệp vụ, không chứng minh feature sẵn sàng hay implementation đúng, không xác nhận Tester verification và không cho phép release. Xem [Foundation workflow](PROJECT_FOUNDATION.md) và [chi tiết kỹ thuật](../project-foundation.md).

## Lifecycle chuẩn

~~~
Project Foundation
→ BA
→ UX / Interaction Contract khi cần
→ Engineering Handoff
→ Engineering / Dev → READY_FOR_TEST
→ Test Design → Human approval → APPROVED_DESIGN
→ Testcases → Human approval → APPROVED_TESTWARE
→ Automation Plan → implementation/review → automation verification → EXECUTION_READY
→ Execution → Observation
   ├─ mọi test bắt buộc PASS và không còn Finding mở → Tester VERIFIED
   └─ Finding → classification
      ├─ DEFECT → Dev Fix → READY_FOR_RETEST → Tester retest → VERIFIED / REOPENED
      └─ SPEC_GAP / BUSINESS_DECISION_REQUIRED / TEST_ISSUE / ENVIRONMENT_ISSUE
         → route tới owner phù hợp và xử lý trước verification
→ quyết định Human riêng cho merge / release
~~~

Tester có thể tạo VERIFIED trực tiếp sau lần execution đầu tiên sạch khi mọi Observation bắt buộc đều PASS và không còn Finding mở. Retest chỉ bắt buộc sau đường DEFECT → Dev Fix. Finding được phân loại thành DEFECT, SPEC_GAP, BUSINESS_DECISION_REQUIRED, TEST_ISSUE hoặc ENVIRONMENT_ISSUE. Chỉ DEFECT đi qua defect handoff tới Dev. Command failure tự nó chưa phải DEFECT. Dev sửa bằng FEATURE_DELIVERY, trả READY_FOR_RETEST, rồi Tester retest.

## Human Gates và giới hạn

CONTINUE != APPROVE; ANSWER != APPROVE; validator PASS != APPROVE; generated != APPROVED; Derived != Authority; Runtime != Authority; CURRENT_SYSTEM != confirmed target.

READY_FOR_TEST là Dev handoff, không phải VERIFIED. Dev fix không tự tạo Tester verification. APPROVED_TESTWARE không phải EXECUTION_READY; EXECUTION_READY không phải PASS. Lifecycle dừng ở VERIFIED, sau đó Human quyết định merge/release riêng. READY_TO_MERGE không phải lifecycle state.

## Trang vai trò

[BA workflow](BA_KIT_WORKFLOW.md), [Dev workflow](DEV_KIT_WORKFLOW.md), [Test workflow](TEST_KIT_WORKFLOW.md), [Automation](TEST_AUTOMATION_V1.md), [Execution/Retest](TEST_EXECUTION_VNEXT.md). Tra cứu [readiness](READINESS_STATES.md) hoặc [troubleshooting](TROUBLESHOOTING.md).

---

English: [Architecture and lifecycle](../en/ARCHITECTURE.md)
