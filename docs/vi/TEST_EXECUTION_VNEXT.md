# Test Execution / Finding / Defect / Retest VNext

Phase 8 nối tiếp Test Kit Manual VNext và Test Automation V1. Đầu vào duy nhất là handoff Phase 7 `EXECUTION_READY` chính xác và phải được Automation V1 runtime cài đặt revalidate.

## Ràng buộc trước khi chạy

Tạo Environment Descriptor V1 canonical và Execution Manifest bất biến. Manifest ràng buộc Approved Testware, Automation Plan, Dev `READY_FOR_TEST`, từng application repository ID cùng Git SHA, automation repository cùng commit SHA, và ref môi trường đã được làm sạch. Không lưu credential, đường dẫn tuyệt đối trên máy hoặc văn xuôi expected result.

Trước và sau từng command/retest, kiểm tra lại authority bytes, environment refs, worktree sạch, application SHA chính xác và automation SHA chính xác. Drift dừng attempt với `EXECUTION_STALE`.

## Chạy và ghi nhận

Với `TEST_AUTOMATION`, chỉ chạy argv `execution_command` chính xác từ Automation Plan trong automation repository đã khai báo, dùng `shell=False`. Command evidence bất biến ràng buộc testcase refs, toàn bộ repository revisions, môi trường, thời điểm, exit code và hash stdout/stderr. Command lỗi là evidence, không tự động trở thành Defect.

Với `MANUAL_ONLY`, không tạo command giả; Tester đã xác thực ghi Observation. Với `DEV_LOCAL_REFERENCE`, dùng lại Dev evidence chính xác mà `EXECUTION_READY` đã ràng buộc. Testcase BLOCKED tùy chọn vẫn hiển thị và không được tính PASS.

Automated và manual dùng chung Observation contract. `oracle_ref` cùng `oracle_locator` trỏ đúng Approved Testcase; `actual_summary` chỉ ghi nhận evidence quan sát được. Automated PASS yêu cầu `COMMAND_PASS`. Mọi Observation FINDING tạo Finding bền vững.

## Phân loại và định tuyến

Chỉ Tester qua trusted host callback mới phân loại Finding, với đúng các giá trị:

| Phân loại | Định tuyến |
| --- | --- |
| `DEFECT` | Dev |
| `SPEC_GAP` | Upstream |
| `BUSINESS_DECISION_REQUIRED` | Upstream |
| `TEST_ISSUE` | Test |
| `ENVIRONMENT_ISSUE` | Environment |

DEFECT cần oracle chính xác đã được phê duyệt, cùng mismatch có thể tái lập HOẶC evidence mismatch deterministic chính xác. Một trong hai cơ sở proof là đủ; cả hai cùng đúng cũng hợp lệ. Tester phải phân loại Finding một cách tường minh; `COMMAND_FAIL` hoặc `FINDING` không tự động trở thành `DEFECT`. Vẫn phải loại trừ môi trường là nguyên nhân gốc và lỗi test/automation trong phạm vi evidence hỗ trợ, đồng thời xác định application targets thuộc topology. Exit code khác 0 không đủ. Route khác DEFECT không thể đóng attempt hiện tại; artifact upstream được sửa phải tạo `EXECUTION_READY` mới và attempt mới.

## Xác minh và retest

Khi mọi Testcase automated/manual bắt buộc có Observation PASS, Dev-local evidence còn hiện hành và không còn Finding mở, Tester đã xác thực tạo handoff `VERIFIED` bền vững. PASS ban đầu sạch không cần retest.

Với DEFECT, Phase 8 tạo `DEFECT_READY_FOR_DEV`. Dev dùng flow `FEATURE_DELIVERY` hiện có, `change_id` bằng defect ID ổn định, và Engineering Handoff BA ban đầu làm authority WHAT. Defect artifacts chỉ là context/evidence chỉ đọc. Sau khi Dev VNext canonical validator chấp nhận, repository base bằng SHA lỗi, có thay đổi ở target, repo ngoài target không drift, coverage hợp lệ, review PASS và fresh verification PASS, Phase 8 tạo `READY_FOR_RETEST`.

Tester chạy lại Approved Testcase đã lỗi ban đầu ở fixed app SHAs chính xác, automation SHA ban đầu và môi trường đã ràng buộc. PASS thành `VERIFIED`; FINDING thành `REOPENED` với cùng defect ID và lineage. Dev không thể tự đóng defect.

## Ranh giới

Doctor chỉ chẩn đoán package/capability. READY không có nghĩa là `EXECUTION_READY`, PASS, không có Finding, `READY_FOR_RETEST`, `VERIFIED` hay sẵn sàng merge. Delivery Manifest vẫn deferred và không authoritative. Legacy execution chỉ dùng cho compatibility. Phase 8 không merge product code và không tạo `READY_TO_MERGE`.

Host xác thực Tester qua trusted callback nhận actor ID, role/action được yêu cầu và artifact hash. Runtime API cung cấp `start`, `execute_automated`, đọc Execution Manifest/artifact, ghi Observation và classification, nhận Dev fix, retest, final verification và revalidate VERIFIED.
