# Public Cross-Kit Conformance

Đây là hướng dẫn vận hành hiện hành cho gate của suite candidate. Identity và acceptance lấy từ [suite manifest](../../tooling/sdlc-suite.json) và [acceptance contract](../../tooling/sdlc-suite-acceptance.yaml).

## Điều kiện và lệnh chạy

Cần candidate đã commit, working tree sạch, Python có pytest để unittest discovery chạy đủ, và Spec Kit CLI v1.0.11. Output phải nằm ngoài source checkout.

~~~powershell
python -m tooling.public_conformance --repo . --output C:\path\outside\repo\conformance-report.json --spec-kit-cli C:\path\to\specify.exe
~~~

Runner bind commit/tree, clone mới đúng SHA, dùng installed runtime cách ly và external working directory, giữ PYTHONPATH không được đặt, rồi ghi evidence ngoài source tree. Windows checkout được hỗ trợ theo .gitattributes; không yêu cầu core.autocrlf=false.

## Journey bắt buộc

~~~
Project Foundation
→ BA
→ Dev
→ Test Manual
→ Automation
→ Execution
→ Finding → DEFECT → Dev Fix → READY_FOR_RETEST → Tester VERIFIED
~~~

Có thêm straight-pass execution path. Negative probes phải bác bỏ: validator PASS được xem là approval; generated là approved; TEST_ONLY không có trusted test-only host; Dev tự claim VERIFIED; APPROVED_TESTWARE được xem là EXECUTION_READY; EXECUTION_READY được xem là PASS; Delivery Manifest là authority bắt buộc; READY_TO_MERGE là lifecycle state; command failure tự động thành DEFECT.

Synthetic Human receipts mang TEST_ONLY và not_for_production. Chỉ trusted test-only host path mới chấp nhận chúng. Chúng không phải ví dụ production approval.

## Phân biệt kết quả

- Kit Doctor DEGRADED nghĩa là capability tùy chọn như XMind/Excel chưa dùng được.
- Conformance OPTIONAL_DEGRADED ghi riêng việc setup projection tùy chọn không thành công. Nó không đồng nghĩa Kit Doctor DEGRADED và không phải suite result.
- Suite Doctor xác minh package/core compatibility; lỗi package hoặc contract bắt buộc là blocker.
- Suite cuối cùng là PASS hoặc FAIL. Optional projection gap được phép có thể đi cùng PASS; hãy báo cả hai field.

Report bind SHA/tree, phiên bản suite/Kits, authority/provenance package, Doctor results, test totals, trace, fresh clone và source immutability. Nếu source hoặc docs thay đổi, chạy lại toàn gate trên SHA sạch mới.

PASS là evidence cho Human review. PASS không cho phép merge, tag, GitHub Release hay stable publication. Xem [release status](RELEASE.md).

---

English: [Public Cross-Kit Conformance](../en/SDLC_SUITE_CONTRACT.md)
