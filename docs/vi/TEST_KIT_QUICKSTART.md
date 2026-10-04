# Bắt đầu nhanh với Test Kit Manual VNext

Test Kit nhận **Engineering Handoff VNext** đã được BA phê duyệt bằng Human receipt chính xác, rồi tạo Test Design và manual Testcases qua hai Human Gate.

```text
Engineering Handoff VNext
→ Canonical Test Design
→ DESIGN_REVIEW → Human approval → APPROVED_DESIGN
→ Canonical Testcases
→ CASE_REVIEW → Human approval → APPROVED_TESTWARE
```

Trace nghiệp vụ chuẩn chỉ gồm `BR-*` và `FR-*`. `BAREF:*` chỉ là locator/provenance. `APPROVED_TESTWARE` kết thúc manual lane Phase 6; không có nghĩa là `EXECUTION_READY`, execution PASS, `VERIFIED` hay `READY_TO_MERGE`.

## 1. Cài vào project

Từ project đích, dùng installer của Agent Skills checkout:

```powershell
& '<path-to-agent-skills>\tooling\install.ps1' test --agent codex --scope project
& '<path-to-agent-skills>\tooling\doctor.ps1' test --agent codex --scope project
```

```bash
<path-to-agent-skills>/tooling/install.sh test --agent codex --scope project
<path-to-agent-skills>/tooling/doctor.sh test --agent codex --scope project
```

Doctor `READY` xác nhận package/core capability; không đánh giá BA approval hay trạng thái feature. Thiếu dependency XMind/Excel có thể cho `DEGRADED` trong khi core vẫn dùng được. `FAIL` chỉ dành cho package/capability bắt buộc hoặc integrity lỗi.

## 2. Chuẩn bị feature

Trong phiên làm việc của agent, cung cấp đường dẫn tới **Engineering Handoff VNext** chính xác và BA Human authenticator của host. Test Kit đọc lại receipt, revision, source refs và hash; không nhận Approved BA Baseline V1 làm authority trực tiếp.

UX chỉ bắt buộc nếu context VNext ghi rõ `ux_required: true`. Nếu `false`, các từ như `field`, `input`, `page` không tự yêu cầu UX. UX được đưa vào như context tiêu thụ phải có contract/receipt được Human phê duyệt, đúng feature/revision, hash nguồn và snapshot hash; prototype chỉ là `REVIEW_EVIDENCE`. Runtime kiểm tra identity và bytes, không tuyên bố hiểu tương đương ngữ nghĩa của văn xuôi.

Dev Handoff V2 có thể cung cấp setup/action/observation kỹ thuật. Nó không thay đổi BA WHAT. Project Test Policy chỉ là guidance không có authority.

## 3. Tạo và duyệt Test Design

1. Khởi tạo run VNext từ Engineering Handoff VNext đã revalidate.
2. Chạy pinned TEA trong cùng agent session và lưu output tại vị trí run đã chuẩn bị.
3. Finalize canonical Test Design. Validator `PASS` chỉ đưa run tới `DESIGN_REVIEW`.
4. Human xem đúng snapshot, revision, hash và input refs. Chỉ trusted Human authenticator mới chấp nhận receipt `APPROVE` hoặc `REQUEST_CHANGES`.
5. `APPROVED_DESIGN` cho phép bắt đầu tạo Testcases.

Agent, TEA hay một phản hồi như `continue`, `review`, `pass` không thể tự duyệt.

## 4. Tạo và duyệt Testcases

1. Sau `APPROVED_DESIGN`, chuẩn bị testcase run với đúng Design và authority refs.
2. Chạy pinned Katalon create-test-cases trong cùng agent session; finalize canonical Testcases.
3. Validator `PASS` chỉ đưa run tới `CASE_REVIEW`. `UNKNOWN` không được biến thành kết quả cụ thể; material required execution dependency còn mở sẽ chặn approval.
4. Human xem đúng testcase snapshot và input refs rồi cấp Human receipt đã xác thực.
5. Khi hợp lệ, runtime ghi Approved Testware VNext `HANDOFF_MANIFEST` ở `APPROVED_TESTWARE`.

Sau gate, đọc lại manifest và kiểm tra refs/hash trước khi handoff. Không dùng trạng thái này làm bằng chứng test đã chạy.

## 5. XMind, Excel và tương thích

XMind chỉ là bản chiếu DERIVED từ `APPROVED_DESIGN`; Excel chỉ là bản chiếu DERIVED từ `APPROVED_TESTWARE`. Không có reverse import. Hai capability này là tùy chọn và installer không tự tải dependency.

V1 chỉ dành cho đọc/kiểm tra `LEGACY_COMPAT`, `vnext_authority=false`. [Ví dụ VNext trung tính](../../kits/test/examples/vnext/neutral/README.md) là ví dụ mặc định. Appointment/CR-001 cũ được giữ ở khu vực lịch sử V1.

Delivery Manifest là `DEFERRED_NON_AUTHORITATIVE` và không cần cho Test VNext. Automation planning/execution thuộc Phase 7+.
