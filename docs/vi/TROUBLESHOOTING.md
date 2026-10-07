# Troubleshooting — operator recovery

Trước khi khôi phục, ghi revision, status và thông báo lỗi gốc. Không sửa manifest/hash để làm Doctor pass. Dùng recovery bình thường dưới đây; chỉ escalation khi evidence cho thấy Human authority, policy hoặc package provenance không thể xác minh.

## Doctor

| Triệu chứng | Ý nghĩa | Chẩn đoán và khôi phục an toàn | Dừng khi |
|---|---|---|---|
| Kit Doctor READY | Package/capability bắt buộc hợp lệ | Tiếp tục workflow Kit; xem [readiness](READINESS_STATES.md) | Không dùng READY làm approval |
| Kit Doctor DEGRADED | Optional XMind/Excel hoặc projection khác thiếu | Nếu cần projection, cài theo lock/requirements đã pin rồi chạy Doctor lại; nếu không, dùng core path | Report nêu integrity/required capability lỗi |
| Kit Doctor FAIL | Manifest, authority, managed payload hoặc dependency bắt buộc lỗi | Ghi version, Doctor output, source SHA; kiểm tra package candidate và cài lại đúng revision | SHA/authority không khớp hoặc install record không giải thích được |
| Suite Doctor FAIL | Component tuple, contract, runtime, router, package authority hoặc test config không tương thích | Đọc từng check lỗi; đồng bộ candidate theo manifests, sửa project setup theo check, chạy lại từ clean checkout | Required capability vẫn FAIL hoặc machine contracts mâu thuẫn |

Suite Doctor chạy từ framework checkout:

~~~
python -m tooling.sdlc_suite doctor --root <framework-checkout> --spec-kit-cli <Spec-Kit-v1.0.11-CLI> --docs-project <docs-project> --app-project <app-project> --automation-project <automation-project>
~~~

Doctor xác minh package/capability readiness, không xác minh business hay product.

<a id=package></a>

## Cài đặt và nâng cấp

1. Ghi source SHA bằng git rev-parse HEAD; ghi thay đổi bằng git status --short.
2. So sánh version Kit đã cài với [suite và Kit manifests](../../tooling/sdlc-suite.json); dùng một committed revision cho cài đặt và Doctor.
3. Chạy lại installer cùng Kit/scope/target để khôi phục file thiếu. Reinstall idempotent và giữ managed file người dùng đã sửa.
4. Với MODIFIED_MANAGED_FILE, review diff/hash rồi quyết định giữ edit ngoài managed path hoặc khôi phục exact candidate bytes; chạy Doctor lại.
5. Với MISSING_MANAGED_FILE, cài lại cùng candidate và kiểm tra path, Doctor result.
6. Với authority/payload mismatch, dừng. Dùng clean checkout đúng candidate. Chỉ Maintainer regen authority bằng canonical tooling; operator không sửa hash.
7. Chỉ fresh install sau khi đã giữ project-owned config và managed edits cần bảo tồn. Kit uninstall chỉ xóa file chưa sửa do Kit sở hữu.

Windows checkout mặc định được hỗ trợ nhờ .gitattributes. core.autocrlf=false không phải prerequisite. Không normalize package bytes/hash bằng tay.

### Version và source drift

So version đã cài với [suite manifest](../../tooling/sdlc-suite.json), [BA](../../kits/ba/kit.yaml), [Dev](../../kits/dev/kit.yaml), [Test](../../kits/test/kit.yaml). Candidate sạch không có thay đổi chưa commit. SHA đổi sau conformance làm report stale; chạy lại trên SHA mới.

### Authority hoặc payload mismatch

Giữ nguyên manifest và package authority. Ghi Doctor output, source SHA và file bị nêu. Kiểm tra source checkout bẩn, revision sai, thiếu file hoặc installed managed file bị sửa. Khôi phục bằng committed package source đúng rồi cài lại. Không lấy authority từ install khác, không regen hash để che drift.

### Managed file bị sửa hoặc thiếu

Backup và review local edit trước. Reinstall giữ managed edit; đưa thay đổi cần bảo tồn vào project-owned path rồi khôi phục managed asset từ candidate khi cần. Với file thiếu, cài lại đúng candidate và xác nhận file/Doctor. Không xóa cả install directory khi chưa phân biệt file project-owned.

## Workflow recovery

| Triệu chứng | Ý nghĩa | Khôi phục / owner | Không tiếp tục khi |
|---|---|---|---|
| Foundation gap unresolved | Context thiếu evidence hoặc owner decision | Giữ UNKNOWN/PROPOSED; route tới BA, Engineering hoặc Test owner; Human duyệt exact snapshot | Không claim PROJECT_FOUNDATION_READY khi blocker còn |
| BA WHAT chưa rõ | Target behavior chưa được quyết định | Hỏi câu cụ thể, ghi Human answer, cập nhật BR/SRS revision và xin approval mới | Không handoff như thể đã approved |
| BA receipt stale | Snapshot/revision/hash đổi | Tạo candidate exact mới và xin trusted-host receipt mới | Không tái dùng receipt cũ |
| Dev UPSTREAM_GAP | Handoff/WHAT thiếu hoặc xung đột | Dừng writes; route gap về BA/owner; resume khi resolution và Handoff mới được xác thực | Không tự quyết business behavior |
| Dev NEEDS_REPLAN | Scope, risk, repo base hoặc assumptions đổi | Tạo lại impact/plan/snapshot; lặp technical Human gate nếu cần | Không đi tiếp với plan/approval stale |
| Dev BLOCKED | Capability, access hoặc dependency ngăn progress an toàn | Ghi blocker, owner, evidence, điều kiện gỡ; xử lý rồi resume | Không phát READY_FOR_TEST |
| Automation BLOCKED | Testcase/dependency/repository bắt buộc chưa sẵn sàng | Cập nhật Plan/dependency; kiểm tra automation repository theo project policy/topology | Không phát EXECUTION_READY |
| Sai automation repository | Repo chọn không khớp policy/topology | Dừng writes; giải quyết root/topology và tạo Plan bind đúng repo | Không ghi automation vào app repo |
| Execution stale revision | App/automation/environment revision khác Execution Manifest | Ghi revision mới và tạo manifest/evidence mới từ EXECUTION_READY hiện hành | Không áp kết quả cũ cho source mới |
| Command failed | Chỉ là command evidence/failure | Tester quan sát theo approved oracle rồi phân loại đúng DEFECT, TEST_ISSUE, ENVIRONMENT_ISSUE hoặc loại phù hợp | Không tự tạo Finding/DEFECT từ exit code |
| Retest failed | Approved oracle vẫn fail | Tester tạo REOPENED giữ defect identity rồi route Dev | Không tự phát VERIFIED |
| Fresh-clone conformance FAIL | Gate bắt buộc fail trên clone candidate | Đọc report/tier, sửa source, commit candidate mới, rerun trên SHA đó | Không tái dùng report cũ hoặc đổi FAIL thành optional |
| Spec Kit version mismatch | Runtime tool khác contract | Chọn/xác minh Spec Kit v1.0.11 rồi rerun | Không chạy suite gate với version khác |

### Optional degradation và conformance

Kit Doctor DEGRADED nói về optional capability. CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE nghĩa Test core dùng được nhưng projection tùy chọn thiếu. Conformance OPTIONAL_DEGRADED là field setup projection. Ba kết quả này khác final suite PASS/FAIL; xem [Readiness](READINESS_STATES.md). Chỉ optional projection được policy cho phép mới degrade; lỗi package/integrity bắt buộc luôn blocker.

## Escalation

Hỏi Human khi cần semantic decision, approval receipt, Project Policy authority, technical gate, risk acceptance hoặc release decision. Escalate Maintainer khi exact clean candidate vẫn fail package/integrity/contract sau recovery từ đúng version. Các trường hợp thông thường có recovery cụ thể.
