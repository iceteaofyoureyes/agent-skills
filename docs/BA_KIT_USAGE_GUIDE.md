# BA Kit Usage Guide

Use ordinary language in the project where BA Kit is installed. You do not need to invoke a skill by name. Prompts below illustrate intent; wording and artifact IDs are not fixed.

## Start a review

~~~text
Review requirement này giúp tôi.
~~~

For a brownfield review:

~~~text
Review requirement này. Trước khi kết luận hãy discover current system và chỉ ra các điểm còn thiếu hoặc chưa rõ.
~~~

The workflow reviews the current system when relevant, labels evidence, and identifies unresolved questions. A review request is read-only.

## Continue without approving

~~~text
Tiếp tục.
~~~

This resumes the recorded stage and handles the next valid action. It does not answer a pending question or approve an artifact.

## Ask about open items

~~~text
Còn gap nào blocking?
~~~

The workflow should identify blocking gaps and preserve any unresolved non-blocking items.

## Answer a question

Give a direct answer to the named question, for example:

~~~text
Rule conflict chỉ áp dụng cho Appointment ở trạng thái Scheduled của cùng Veterinarian; hai khoảng thời gian chạm nhau thì được phép.
~~~

This is an illustrative CR-001 answer. Use it only if it is the decision the authorized BA has actually made. An answer resolves the named question; it does not approve other artifacts.

## Review the confirmed rules

~~~text
Tổng hợp lại các Business Rules đã confirmed, giữ riêng các mục UNKNOWN.
~~~

Check that the rules cite their sources and preserve the difference between confirmed decisions and current-system evidence.

## Generate an SRS

~~~text
Viết SRS từ baseline đã xác nhận.
~~~

The SRS should derive from the confirmed decisions and approved Business Rules, keep traceability, and leave unresolved items explicit.

## Explicitly approve the baseline

After reviewing the named artifacts and their revisions, a clear approval could say:

~~~text
Tôi phê duyệt Business Rules revision BR-<revision> và SRS revision SRS-<revision> làm BA baseline cho Engineering.
~~~

Replace the example revision labels with the real immutable revisions. Send an approval only when you intend to approve those named artifacts. The workflow does not infer approval from **Tiếp tục**, a complete answer set, or a successful validation.

## Create Engineering Handoff

After explicit approval and resolution of all blocking items:

~~~text
Tạo Engineering Handoff.
~~~

The handoff records the approved BA baseline, source paths and SHA-256 hashes, open items, downstream policy, and next stage. It must not assign a repository, module, frontend/backend owner, API or DB design, locking, or transaction strategy. See the [handoff contract](../ba-workflow/references/engineering-handoff.md) and [provenance record](PROVENANCE.md).

## Examples and contracts

The [CR-001 example](../kits/ba/examples/CR-001/README.md) shows one illustrative path from incomplete input to handoff. It is not a golden transcript: exact wording and sample IDs are not mandatory unless a real contract requires them. Follow the artifact contract and preserve provenance rather than matching sample prose.
