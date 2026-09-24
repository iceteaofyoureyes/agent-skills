# Trạng thái phát hành

BA Kit **1.0.0-rc.1** là release candidate. Chưa được coi là functional release đã accepted.

Dev Kit và Test Kit vẫn ở phase sau; chưa phải capability của BA Kit RC1.

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

## Runtime functional acceptance

Runtime preflight trên isolated route đã **PASS** với:

~~~text
provider = codex-lb
model = gpt-6-luna
~~~

Project-local skill discovery cũng PASS.

Full fresh-session CR-001 acceptance đầu tiên đã chạy và kết luận:

~~~text
BA_KIT_RC1_CHANGES_REQUIRED
~~~

Các finding chính:

- current-system discovery trong run đó bị chặn bởi HTTP 403 từ codex-auto-review;
- gap analysis/Business Rules/SRS chưa đạt semantic golden;
- SRS bỏ sót một số confirmed behaviors;
- SRS thêm một số unsupported UI/entry-flow assumptions;
- một validator behavior được report là regression nhưng cần reproduce trên current HEAD trước khi sửa;
- exact tested repository SHA không được ghi trong report.

Vì vậy run này là **evidence tìm ra lỗi**, không phải final acceptance của current HEAD.

Chiến lược remediation hiện tại:

~~~text
Tier 1 deterministic tests
→ Tier 2 focused runtime probes
→ one final Tier 3 full fresh-session E2E
~~~

Không chạy lại full 1h+ cho mỗi thay đổi nhỏ.

## SRS/DOCX/Draw.io capability status

- canonical functional SRS capability: implemented, targeted semantic remediation đang diễn ra;
- DOCX capability: required skill có sẵn;
- Word template support: có qua document-docx, nhưng **không có bundled default SRS_TEMPLATE.docx**;
- Draw.io capability: required skill có sẵn;
- optional prototype/UI capabilities: chỉ có khi optional skills tương ứng được cài.

## Redistribution readiness

BA Kit installer payload:

~~~text
BA_KIT_LICENSE_READY
~~~

Required/core/optional skills trong BA payload đã có provenance/license status cần thiết cho redistribution.

Whole repository:

~~~text
REPO_PUBLICATION_BLOCKED
~~~

Một số non-BA imports và tracked Skills Manager metadata vẫn cần audit/scope decision.

## Khi nào mới gọi RC1 PASS?

Chỉ sau khi:

1. targeted deterministic/runtime remediation PASS;
2. final full fresh-session CR-001 E2E chạy trên exact recorded HEAD;
3. semantic comparison PASS;
4. final independent review PASS;
5. Human chấp nhận release candidate.

Không dùng example docs, offline metadata coverage hoặc package install PASS thay cho runtime acceptance.

---

English: [Release status](../en/RELEASE.md)
