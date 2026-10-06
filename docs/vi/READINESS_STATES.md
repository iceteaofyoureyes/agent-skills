# Readiness và authority — tra cứu nhanh

Contract thực thi nằm trong [suite manifest](../../tooling/sdlc-suite.json), [Shared readiness vocabulary](../../shared/sdlc/readiness/vocabulary.py), [artifact classes](../../shared/sdlc/artifacts/classes.py), [approval invariants](../../shared/sdlc/approvals/invariants.py), manifests và schemas của từng Kit. Bảng này giải thích cho operator; không tạo trạng thái mới.

| Trạng thái | Owner | Chứng minh | Không chứng minh | Bước tiếp theo |
|---|---|---|---|---|
| READY | Kit Doctor | Package và capability bắt buộc kiểm tra được | Approval, feature correctness, test pass | Bắt đầu workflow Kit |
| DEGRADED | Kit Doctor | Core dùng được nhưng optional capability thiếu | Lỗi integrity bắt buộc có thể bỏ qua | Cài projection nếu cần; nếu không, dùng core path |
| CORE_READY | Suite Doctor / Test runtime | Test core capability sẵn sàng | XMind/Excel sẵn sàng hoặc product PASS | Dùng Test core; theo dõi projection riêng |
| CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE | Suite Doctor / Test runtime | Test core sẵn sàng; optional projection unavailable | Suite PASS hay product verification | Tiếp tục nếu projection không bắt buộc |
| PROJECT_FOUNDATION_READY | Foundation trusted workflow | Foundation snapshot đáp ứng policy và exact review | Business approval hoặc feature readiness | Route context tới BA, Engineering hoặc Test |
| APPROVED_BASELINE | Human qua BA trusted host | WHAT baseline và source snapshot chính xác được duyệt | Technical design hoặc implementation | BA tạo Engineering Handoff |
| READY_FOR_TEST | Dev | Dev handoff, implementation checks và scope đã bind | Tester VERIFIED, merge approval | Test nhận đúng handoff |
| APPROVED_DESIGN | Human qua Test trusted host | Exact Test Design/coverage snapshot được duyệt | Testcase approval hay execution | Tạo Testcases |
| APPROVED_TESTWARE | Human qua Test trusted host | Exact testcase snapshot và trace được duyệt | Automation readiness, execution readiness, PASS | Lập Automation Plan hoặc chạy manual theo contract |
| EXECUTION_READY | Automation workflow | Automation review/verification và execution inputs được bind | Test đã chạy hoặc PASS | Test Execution dùng exact handoff |
| READY_FOR_RETEST | Dev | Fix handoff bind defect/oracle và revision mới | Defect đã đóng hoặc verified | Tester retest |
| VERIFIED | Authenticated Tester | Current attempt đạt oracle sau run/retest | Human merge/release decision | Kết thúc product lifecycle; chờ quyết định Human riêng |
| REOPENED | Authenticated Tester | Retest thất bại và defect lineage được giữ | Defect đã đóng | Trả lại Dev qua cùng defect |
| INTERNAL_RC_CANDIDATE | Suite manifest / Maintainer | Candidate là identity internal prerelease | Package acceptance, conformance, merge hay release | Chạy acceptance, Doctors, conformance; Human review |
| OPTIONAL_DEGRADED | Public Conformance runner | Optional projection setup không sẵn sàng | Test core failure hoặc final suite FAIL tự nó | Báo riêng; xử lý khi cần capability đó |

Kit Doctor DEGRADED, Test core condition CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE và conformance OPTIONAL_DEGRADED là ba field/ngữ cảnh khác nhau. Final conformance PASS/FAIL là kết quả riêng. Xem [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md).

Invariant: CONTINUE != APPROVE; ANSWER != APPROVE; validator PASS != APPROVE; generated != APPROVED; Derived != Authority; Runtime != Authority; CURRENT_SYSTEM != confirmed target; Dev READY_FOR_TEST != Tester VERIFIED; Dev fix != Tester VERIFIED; APPROVED_TESTWARE != EXECUTION_READY; EXECUTION_READY != PASS.

Lifecycle hiện hành không phát ra READY_TO_MERGE. Merge/release cần Human quyết định riêng sau VERIFIED.
