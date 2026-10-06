# Khả năng và ranh giới Test Kit Manual VNext

## Authority và input

| Input | Vai trò trong VNext |
|---|---|
| Engineering Handoff VNext + exact Human approval proof | Business WHAT bắt buộc; BA VNext reader kiểm tra lại receipt, nguồn, revision và bytes |
| BR/FR từ baseline | Trace nghiệp vụ chuẩn duy nhất trong Test Design/Testcases |
| `BAREF:*` | Locator/provenance; không được xuất hiện trong canonical `requirement_refs` |
| UX context được duyệt | Tùy chọn; chỉ bắt buộc khi context chính xác ghi `ux_required: true` |
| Dev Handoff V2 | Technical/execution context tùy chọn; không thể định nghĩa BA WHAT |
| Project Test Policy | Guidance không có authority; không thể override BA, Design hay Human Gate |
| TEA và Katalon | Analysis/generation và raw evidence; không phải nguồn approval |

Nếu UX context được cung cấp thì receipt, feature/revision, contract/source hashes, snapshot hash và Human authentication đều phải hợp lệ. Stale bytes hoặc prototype-only UX bị từ chối. Khi `ux_required: false`, từ như `field`, `input`, `page` trong văn xuôi không suy ra UX requirement. Runtime không làm semantic matching tùy tiện giữa văn xuôi; Human chịu trách nhiệm review consistency.

## Manual lifecycle

| Trạng thái | Ý nghĩa |
|---|---|
| `DESIGN_REVIEW` | Canonical Design đã validate; chưa được approve |
| `APPROVED_DESIGN` | Trusted Human đã approve exact Design snapshot/input refs |
| `CASE_REVIEW` | Canonical Testcases đã validate; chưa được approve |
| `APPROVED_TESTWARE` | Trusted Human đã approve exact Case snapshot/input refs; điểm kết thúc của Manual lane |

`APPROVED_TESTWARE` không có nghĩa là `EXECUTION_READY`, test PASS, `VERIFIED` hay `READY_TO_MERGE`. Đây là điểm dừng của Manual lane; flow tiếp tục qua [Automation V1](TEST_AUTOMATION_V1.md) đến `EXECUTION_READY` và [Test Execution VNext](TEST_EXECUTION_VNEXT.md) qua Finding, Dev fix, retest tới `VERIFIED` hoặc `REOPENED`.

## Canonical artifacts và projection

- Canonical Test Design giữ scenario, priority, expected behavior, FR/BR trace và open questions.
- Canonical Testcases giữ objective, preconditions, data, steps/expected results, priority, Design refs và execution dependencies.
- Approved Testware VNext là `HANDOFF_MANIFEST` có exact input refs, BA/Design/Case proof và BR/FR trace summary.
- XMind là `DERIVED` từ `APPROVED_DESIGN`; Excel là `DERIVED` từ `APPROVED_TESTWARE`. Cả hai một chiều, không reverse import.

UNKNOWN/deferred BA behavior tiếp tục là UNKNOWN. Material required execution dependency còn unresolved sẽ chặn Case approval. Implementation hiện tại và Dev evidence không trở thành business oracle.

## Gói và readiness

Package hiện hành gồm Manual, Automation và Execution VNext, prerelease `2.0.0-rc.14`. V1 vẫn được đóng gói để đọc/kiểm tra theo `LEGACY_COMPAT`, `vnext_authority=false`.

- Python 3.10+ và các pinned TEA/Katalon skills thuộc core.
- XMind cần Node/npm và SDK đã pin; Excel cần `openpyxl`/`et-xmlfile` đã pin. Installer không tải dependency tùy chọn.
- Doctor `READY` nghĩa là package/core capability sẵn sàng. Human approval, Design/Testware state và execution không được đánh giá.
- Doctor `DEGRADED` nghĩa là capability tùy chọn không có; `FAIL` nghĩa là package, integrity hoặc capability bắt buộc lỗi.

Delivery Manifest là `DEFERRED_NON_AUTHORITATIVE`, không phải BA/UX authority và không bắt buộc cho flow này. Xem [neutral VNext example](../../kits/test/examples/vnext/neutral/README.md) và [workflow](TEST_KIT_WORKFLOW.md).
