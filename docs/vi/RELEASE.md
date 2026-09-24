# Trạng thái phát hành

BA Kit **1.0.0-rc.1** là **Public Preview**, chưa được chấp nhận hoàn toàn.

Dev Kit và Test Kit đều **Planned**, chưa nằm trong Public Preview của BA Kit.

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
