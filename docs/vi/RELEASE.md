# Trạng thái phát hành

## Test Kit Manual VNext

Package candidate hiện tại là **`2.0.0-rc.6`**. Đây là prerelease branch candidate, không phải stable `2.0.0`, GitHub release, tag hay published artifact.

Default manual lane:

```text
Engineering Handoff VNext
→ Test Design → Human Design Gate → APPROVED_DESIGN
→ Testcases → Human Case Gate → APPROVED_TESTWARE
```

`APPROVED_TESTWARE` kết thúc Phase 6 manual lane; nó không có nghĩa `EXECUTION_READY`, test PASS, `VERIFIED` hoặc `READY_TO_MERGE`. Automation và execution thuộc Phase 7+.

Phase 6 completion được kiểm tra bằng ba tầng trong [`kits/test/acceptance.yaml`](../../kits/test/acceptance.yaml). Tier 3 fresh installed-runtime acceptance là bắt buộc; Tier 1/2 không đủ để đánh dấu Phase 6 complete. Báo cáo acceptance chỉ áp dụng đúng branch/commit được xác minh.

Doctor `READY` xác nhận package/core capability. Optional XMind/Excel dependency thiếu cho `DEGRADED`; required package, integrity hoặc capability lỗi cho `FAIL`. Doctor không đánh giá BA approval, Design/Case approval hay execution.

## Các Kit khác và lịch sử

Test Kit Manual VNext là Kit riêng, cài được cùng BA Kit. Tài liệu BA/Dev lịch sử trong các phần còn lại của repository tiếp tục ghi theo phiên bản và acceptance của từng Kit.

## Provenance và phân phối

Xem [Provenance](PROVENANCE.md), [Installation](INSTALLATION.md) và [English release status](../en/RELEASE.md). Các pin TEA/Katalon, license, notices và package authority được quản lý trong repository; hash được sinh bằng repository tooling, không cập nhật thủ công.
