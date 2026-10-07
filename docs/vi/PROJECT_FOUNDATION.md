# Project Foundation — hướng dẫn vận hành

Project Foundation là workflow Shared SDLC để khôi phục, khởi tạo và cập nhật context dự án. Đây không phải Kit thứ tư và không thay thế BA, Engineering, Test hay Human authority.

## Chọn mode và profile

| Mode | Dùng khi | Phân loại bằng chứng |
|---|---|---|
| GREENFIELD_BOOTSTRAP | Chưa có hệ thống hiện tại; thu thập intent và constraint cho target | APPROVED_TARGET, PROPOSED, DEFERRED, UNKNOWN |
| BROWNFIELD_RECOVERY | Dựng lại current reality từ repo và tài liệu có sẵn | CURRENT_SYSTEM, CONFIRMED, INFERRED, UNKNOWN |
| FOUNDATION_REFRESH | Đánh giá thay đổi theo exact Foundation manifest đã duyệt | So sánh manifest/revision, route impact, giữ gap tường minh |

Profile MINIMAL, STANDARD, EXTENDED chọn độ sâu evidence. Profile rộng hơn không có nghĩa Human đã approve. Kiến trúc dùng arc42 Standard, khái niệm ISO 42010, C4 và ADR; C4/arc42 views là DERIVED.

## Ownership và lifecycle

BA sở hữu product/domain/glossary. Engineering sở hữu architecture/runtime/deployment/ADR. Test sở hữu testing/automation/quality. Producer đóng góp evidence trong ownership của mình; Shared workflow gắn exact refs vào review package.

~~~
ANALYSIS → REVIEW_REQUIRED → ACCEPTED_BASELINE / APPROVED_BASELINE → PROJECT_FOUNDATION_READY
~~~

Giữ UNKNOWN, PROPOSED, DEFERRED và conflicts ở trạng thái tường minh. CURRENT_SYSTEM mô tả hiện trạng, không xác nhận target. Human review exact snapshot qua trusted host; CLI không phát receipt hay tự approve. PROJECT_FOUNDATION_READY chỉ nói Foundation readiness theo policy.

## Bắt đầu

Prerequisite: project có .sdlc/topology.json và .sdlc/project-policy.yml theo Shared v1 contract; cài Foundation/Shared runtime bằng [Installation](INSTALLATION.md). Xem [Foundation workflow core](../project-foundation.md) để biết hợp đồng và schema đầy đủ, cùng [project-foundation skill](../../project-foundation/SKILL.md).

~~~
python <skill>/scripts/project_foundation.py inventory --project-root <project>
python <skill>/scripts/project_foundation.py start --project-root <project> --run-id recovery-1 --mode BROWNFIELD_RECOVERY
python <skill>/scripts/project_foundation.py brownfield --project-root <project> --run-id recovery-1 --input analysis.json
python <skill>/scripts/project_foundation.py greenfield --project-root <project> --run-id bootstrap-1 --input analysis.json
python <skill>/scripts/project_foundation.py refresh --project-root <project> --run-id refresh-1 --revision R2 --input refresh.json
python <skill>/scripts/project_foundation.py prepare --project-root <project> --run-id recovery-1
python <skill>/scripts/project_foundation.py doctor --project-root <project> --run-id recovery-1
~~~

Lệnh phân tích và prepare chỉ tạo evidence/review package. Không tiếp tục như thể Human đã duyệt. Doctor cần xác thực snapshot qua trusted host; nếu thiếu authenticator, dừng và xử lý qua host tích hợp.

Sau PROJECT_FOUNDATION_READY, chuyển context tới BA cho WHAT, Engineering/Dev cho HOW, hoặc Test cho testing theo nhu cầu. Mỗi role vẫn chạy gate và approval riêng.
