# Trạng thái phát hành

BA Kit **1.0.0-rc.1** là **Public Preview**, chưa được chấp nhận hoàn toàn.

Dev Kit vẫn **Planned**. Test Kit V1 là Kit riêng, **không** nằm trong BA Kit Public Preview.

## Test Kit V1

| Phần | Trạng thái |
|---|---|
| Test Kit V1 Core | Human accepted như framework capability |
| XMind Projection V1 | Human accepted như optional framework capability |
| Excel Projection V1 | Human accepted như optional framework capability |
| Packaging Cleanup / Packaging V1 | Human accepted |
| Packaging V1 baseline | Đã commit tại `55e88c39cd97945ee8c2e1b4f152599449966ddb`; các revision documentation/package identity tiếp theo được theo dõi bằng lịch sử repository |

**Human accepted nội bộ ≠ GitHub release/tag/published artifact.** Không có claim rằng Test Kit V1 đã được phát hành công khai dưới một release/tag. Framework acceptance cũng không phê duyệt Test Design/Testcases/Testware của project thật; production Case Gate cần Human receipt đã xác thực cho snapshot hiện hành và không còn material OPEN execution dependency. `TEST_ONLY` output không dùng cho production. Automation Test V2 chưa nằm trong package V1.

Bắt đầu tại [Test Kit Quick Start](TEST_KIT_QUICKSTART.md), [workflow](TEST_KIT_WORKFLOW.md) hoặc [package README](../../kits/test/README.md).

## Package / installer

Đã có evidence PASS cho các kiểm tra package tương ứng:

- Codex project install;
- idempotent reinstall;
- Doctor READY;
- safe uninstall;
- project isolation;
- generic PowerShell/Bash structural path;
- Claude Code structural install.

Các kiểm tra này chứng minh package/install behavior, không tự chứng minh runtime BA semantics.

## Kiểm tra thủ công cho Public Preview

Đã thực hiện kiểm tra thủ công cho Requirement, Business Rules, SRS và Draw.io.

Việc validation thủ công cuối cùng cho DOCX và validation cuối cùng cho approval/handoff vẫn đang chờ.

BA Kit 1.0.0-rc.1 vẫn là Public Preview và chưa được chấp nhận hoàn toàn.

## SRS/DOCX/Draw.io capability status

- canonical functional SRS capability: implemented; đã thực hiện kiểm tra thủ công;
- DOCX capability: required skill có sẵn; validation thủ công cuối cùng đang chờ;
- Word template support: có qua document-docx, nhưng **không có bundled default SRS_TEMPLATE.docx**;
- Draw.io capability: required skill có sẵn; đã thực hiện kiểm tra thủ công;
- optional prototype/UI capabilities: chỉ có khi optional skills tương ứng được cài.

## Redistribution readiness

BA Kit installer payload:

~~~text
BA_KIT_LICENSE_READY
~~~

Required/core/optional skills trong BA payload đã có provenance/license status cần thiết cho redistribution.

## Validation còn chờ

Việc validation thủ công cuối cùng cho DOCX và validation cuối cùng cho approval/handoff vẫn đang chờ. Không mô tả BA Kit 1.0.0-rc.1 là đã được chấp nhận hoàn toàn.

---

English: [Release status](../en/RELEASE.md)
