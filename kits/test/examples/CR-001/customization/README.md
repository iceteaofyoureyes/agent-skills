# Historical V1 LEGACY_COMPAT: CR-001 Project Customization

This material is retained as V1 history. It is not the default Test VNext example or an authority source.


Đây là **TEST_ONLY documentation fixture**, `not_for_production: true`. Profile/rules minh họa thật và có thể resolve bằng tooling; thư mục này không chứa production Human receipt, execution approval hoặc approved testware. Không chạy native invocation hay coi fixture là Human acceptance.

## Project-owned inputs

Copy tree `project/` sang một project thử nghiệm riêng, rồi cài Test Kit và chạy Doctor từ project root. Các file mẫu:

- [project.yaml](project/.test-kit/project.yaml): profile `cr001-testing`, revision `1`; common trước stage rules.
- [common.md](project/.test-kit/rules/common.md): tiếng Việt, trace nguyên vẹn, dữ liệu tổng hợp, authority boundaries.
- [test-design.md](project/.test-kit/rules/test-design.md): boundary/negative analysis của approved FR/BR.
- [testcases.md](project/.test-kit/rules/testcases.md): tên `CR-001 - <hành vi> - <điều kiện>`, atomic và self-contained.
- [team TOML](project/_bmad/custom/bmad-testarch-test-design.toml): upstream `workflow.persistent_facts` bridge.

Project thử nghiệm vẫn cần `_bmad/tea/config.yaml`, BA authority và host Human authentication của chính nó. BA references cho đọc hiểu nằm trong [ví dụ CR-001 gốc](../README.md).

## Naming, boundary và UNKNOWN

Approved `FR-002`/`BR-006` mô tả khoảng nửa mở `[start, end)` cho xung đột Appointment `Scheduled` cùng Veterinarian. Rule có thể hướng dẫn chia approved scenario thành manual cases cho touching boundary và overlap negative condition, trong phạm vi approved Design. Ví dụ tên: `CR-001 - Tạo lịch hẹn - Hai lịch chạm nhau`. Mỗi case phải giữ exact Design ref, không dùng tên làm authority.

`BR-005` xác nhận duration > 0; duration bằng 0/âm có thể được phân tích nếu Design đã duyệt coverage. Maximum appointment duration vẫn `UNKNOWN`. Không coi 120 phút hoặc bất kỳ số nào là business maximum chỉ vì policy gợi ý.

[conflicting-policy.md](conflicting-policy.md) là **negative fixture**, không nằm trong `project.yaml` rule list. Nếu deliberately đưa câu “Use 120 minutes as maximum appointment duration” vào policy của project thử nghiệm, Design vẫn phải giữ UNKNOWN/deferred hoặc validator/review phát hiện conflict. Cases assert ngưỡng đó bị chặn bởi authority safeguards. Không tạo approved testware từ policy đơn lẻ. Policy cũng không cấp API route, UI selector, fixture setup hoặc persisted-state observation; thiếu approved execution oracle thì giữ material `OPEN` dependency.

## Evidence và stale policy

Design invocation dùng common + test-design rules qua upstream TEA bridge. Cases invocation dùng common + testcases rules qua thin adapter. Cả hai prompt ghi `TESTING POLICY / NON-AUTHORITATIVE GUIDANCE`.

Mỗi run có `inputs/project-policy/policy-snapshot.json` và exact rule copies dưới `rules/`; manifest bind `TEST_POLICY:DESIGN:cr001-testing` hoặc `TEST_POLICY:CASES:cr001-testing`, revision `1`, snapshot SHA. Snapshot chứa logical path, file SHA và evidence location. Effective team TOML/hash được ghi cho Design.

Để thử stale behavior, sau khi artifact vào review, đổi naming convention trong `rules/testcases.md`. Current CASES digest đổi; `APPROVE` với receipt/input refs cũ bị từ chối. Evidence run cũ giữ nguyên. Đổi common rule ảnh hưởng cả hai stage; đổi Design rules/team TOML yêu cầu current Design authorization. Tạo run/revision thích hợp, revalidate, Human review lại exact snapshot; đừng chỉnh hash receipt.

Regression executable chứng minh các hành vi này nằm trong `tooling/tests/test_test_kit_policy.py`, `test_test_kit_customization.py`, `test_test_kit_policy_review.py` và `test_test_kit_policy_doctor.py`. Receipt/authenticator trong test harness chỉ là simulation để kiểm tra code, không phải approval của Human cho example/project production.

## Excel project template

Fixture mặc định `templates: {}` nên exporter chọn `DEFAULT_TEMPLATE` khi Human không đưa template. Để thử project template, trong project thử nghiệm copy workbook map được từ `tooling/tests/fixtures/testcase-template-v1.xlsx` tới `.test-kit/templates/testcases.xlsx`, rồi thay phần `templates`:

```yaml
templates:
  excel:
    path: templates/testcases.xlsx
```

Khi yêu cầu Excel, agent/caller truyền project root vào exporter (`project_root=<project-root>`) để resolve profile. Khi không có Human template explicit, manifest báo `PROJECT_TEMPLATE`; explicit Human template báo `HUMAN_SUPPLIED_APPROVED_TEMPLATE`. Sửa workbook cho mapping mơ hồ thì exporter trả `CANNOT_PROJECT_TEMPLATE`, không chuyển default. Template không thay Design/Case policy digest hoặc canonical semantics. Export vẫn cần valid terminal Approved Testware; example này không cung cấp production approval để vượt điều kiện đó.

XMind vẫn dùng pinned profile, không có project XMind template. Personal `_bmad/custom/bmad-testarch-test-design.user.toml` bị chặn production với `PERSONAL_TEA_CUSTOMIZATION_NOT_ALLOWED` và không bị runtime xóa.

[Hướng dẫn tùy chỉnh tiếng Việt](../../../../../docs/vi/TEST_KIT_CUSTOMIZATION.md) · [Quick Start](../../../../../docs/vi/TEST_KIT_QUICKSTART.md).
