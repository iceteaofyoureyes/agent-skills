# Test Automation V1

Tài liệu này hướng dẫn Phase 7 của Test Kit. Phase 7 bắt đầu từ `APPROVED_TESTWARE` VNext chính xác và kết thúc tại `EXECUTION_READY`.

## Luồng và ranh giới

```text
APPROVED_TESTWARE
→ Automation Suitability
→ Automation Plan
→ Automation Implementation
→ Automation Review
→ Automation Verification
→ EXECUTION_READY
```

Không có Human Gate thứ ba. Automation Plan mô tả HOW kỹ thuật, không bổ sung business meaning. Testcase đã duyệt vẫn là oracle duy nhất cho expected behavior. Delivery Manifest giữ trạng thái `DEFERRED_NON_AUTHORITATIVE`.

Test Automation chỉ ghi repository được resolve từ `.sdlc/project-policy.yml` và `.sdlc/project-topology.yml`. Không chọn repository theo tên thư mục. Mọi canonical artifact lưu repository ID/role và relative path; local root chỉ là runtime data.

Application repository chỉ đọc. `UNIT`/`COMPONENT` phải reference evidence chính xác từ Dev Handoff hiện hành. Thiếu evidence thì route về Dev, không tự thêm test vào app.

## Phân loại và ownership

| Class | Owner |
| --- | --- |
| `UNIT`, `COMPONENT` | `DEV_LOCAL_REFERENCE` |
| `CONTRACT`, `DB_RUNTIME`, `API`, `INTEGRATION`, `E2E`, `ACCESSIBILITY`, `SYSTEM` | `TEST_AUTOMATION` |
| `MANUAL_ONLY` | `MANUAL` |
| `BLOCKED` | `BLOCKED` |

Suitability phải có mỗi Testcase chính xác một lần; từ chối duplicate, missing, orphan và trace `BAREF`. Không dùng AI confidence để quyết định authority. Không sao chép objective, preconditions hay expected-result prose vào automation artifact.

`MANUAL_ONLY` giữ nguyên Testcase làm execution protocol và không cần AUT source. `BLOCKED` không tạo AUT; trường hợp không required vẫn được handoff tham chiếu exact Testcase collection. Required `BLOCKED` ngăn readiness. Dependency `OPEN` phải được xử lý; `RESOLVED` phải trỏ tới ref chính xác.

## Automation Plan và source

AUT ID có dạng `AUT-*`, duy nhất trong feature và giữ ổn định qua resume/replan khi testcase mapping còn nguyên. Mỗi item gắn Testcase, class, owner, repository ID, suite, planned paths, runner, execution argv, verification argv, dependencies và trace BR/FR → TD → TC → AUT.

Commands phải là argv arrays, ví dụ:

```json
["python", "-m", "pytest", "tests/api/test_resource.py", "--collect-only"]
```

Không lưu shell command string, không bật shell và không bắt buộc Playwright. Framework do project sở hữu.

Trước mỗi write, runtime kiểm tra lifecycle, Plan revision/hash, identity và base revision của automation repository, AUT/path scope và symlink/reparse escape. Sau implementation, runtime kiểm tra diff, từ chối path ngoài plan và bind exact revision/hash. Guard này không giả vờ chặn được mọi lần editor ghi tùy ý.

Sau khi implementation bắt đầu, material change phải chuyển `NEEDS_REPLAN`, tạo Plan revision mới và xóa evidence implementation/review/verification cũ. Không sửa Plan đã chạy tại chỗ.

Project hoặc agent chịu trách nhiệm commit automation theo Git workflow thông thường; runtime không tự tạo commit. Trước khi ghi nhận implementation, HEAD phải kế thừa đúng `base_revision` của Plan, có commit mới nếu Plan yêu cầu automation, worktree/index phải sạch, không có untracked file, và diff commit `base..HEAD` chỉ chứa các path trong Plan với đầy đủ mọi path bắt buộc. Source chỉ staged, unstaged hoặc untracked phải bị từ chối bằng `AUTOMATION_COMMIT_REQUIRED`. Implementation evidence lưu `base_revision`, `repository_revision`, `changed_paths` đã commit, SHA-256 từng path và ánh xạ AUT → path. `automation_revision` là Git HEAD commit SHA chính xác; tree digest chỉ là evidence bổ sung.

Review, verification và `EXECUTION_READY` cùng bind một committed HEAD sạch. Verification không chạy nếu checkout dirty hoặc HEAD khác revision đã ghi nhận, và fail closed nếu nó thay đổi automation source. `revalidate_handoff()` kiểm tra repository identity, HEAD hiện tại, checkout sạch, source hash đã commit và revision của review/verification; sửa file hoặc tạo commit mới sau readiness làm handoff stale và cần replan. Fresh clone phải checkout được handoff SHA và khôi phục đủ mọi AUT path.

## Review và verification

Chỉ một consolidated full review, bao gồm trace, ownership, business-oracle duplication, fixtures, secrets, setup/cleanup, flakiness, selectors/interfaces, dependencies, conventions và write scope. Budget tối đa: một full review, một blocking fix wave, một scoped rereview. Nếu thiếu WHAT, route upstream; không tự đổi expected behavior.

Automation Verification chỉ xác minh automation implementation bằng một trong các nhóm: `SYNTAX`, `STATIC`, `LINT`, `TYPECHECK`, `TEST_DISCOVERY`, `TEST_LIST`, `CONFIG_VALIDATE`, `HARNESS_SELF_TEST`, `FIXTURE_VALIDATE`. Không chạy execution command hay real SUT.

`PASS` tại đây chỉ có nghĩa automation artifacts sẵn sàng về cấu trúc/runnability. Nó không có nghĩa API/E2E/SYSTEM/feature PASS, WCAG conformance hay `VERIFIED`.

## Điều kiện `EXECUTION_READY`

Trước khi tạo handoff, phải bind:

- Approved Testware VNext và tất cả gate/authority refs hiện hành;
- mọi Testcase vào đúng một disposition;
- automation items, Dev-local evidence và manual Testcases;
- Dev Handoff V2 chính xác với `READY_FOR_TEST`;
- application revisions và automation repository/source revision chính xác;
- dependencies bắt buộc đã xử lý;
- review PASS, automation verification PASS, không có scope drift.

`EXECUTION_READY` không phải kết quả chạy test. Phase 7 dừng ở đó. Tiếp tục với [Test Execution VNext](TEST_EXECUTION_VNEXT.md) để chạy product, ghi Finding, chuyển Defect qua Dev VNext, retest và để Tester tạo `VERIFIED`.
