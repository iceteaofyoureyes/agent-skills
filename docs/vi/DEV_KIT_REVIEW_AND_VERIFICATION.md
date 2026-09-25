# Dev Kit V1 — Review và Verification Contract

## Mục tiêu

Review đủ sâu nhưng bounded. Quality không được tạo bằng cách nối nhiều reviewer loops.

## Consolidated review

Chỉ một full independent review cho normal/high-risk feature candidate. Reviewer nhận:
- Approved BA Baseline/ref;
- Engineering Impact summary;
- implementation plan/tasks;
- BASE/HEAD hoặc review package;
- test/build evidence.

Review axes:
1. requirement/spec fidelity;
2. correctness/error paths;
3. scope creep;
4. architecture/codebase fit;
5. simplicity/maintainability;
6. security baseline;
7. performance risk;
8. test quality and verification story.

Specialist skill có thể được consulted trong cùng review nếu risk trigger rõ; không mặc định spawn reviewer riêng.

## Finding classes

### BLOCKING
- Critical;
- correctness defect;
- security vulnerability;
- approved requirement missing/wrong;
- breaking compatibility not approved;
- verification evidence invalid.

Phải fix trước handoff.

### FOLLOW_UP / NON-BLOCKING
- optional simplification;
- unrelated cleanup;
- future improvement;
- low-confidence nit không ảnh hưởng current task.

Không được mở rộng current task để xử lý tất cả.

## Fix policy

Một implementer/fixer xử lý toàn bộ blocking findings trong **one fix wave**.

Không dùng một fixer/subagent riêng cho từng finding nếu không có lý do kỹ thuật đặc biệt.

## Scoped re-review

Chỉ chạy nếu fix materially changes logic/risk surface hoặc prior finding cần judgement confirmation.

Scope:
- verdict từng blocking finding cũ;
- inspect fix diff cho breakage mới;
- không fresh-review toàn bộ feature;
- issue hoàn toàn ngoài fix diff là out-of-scope/non-blocking.

## Final verification

Trước `READY_FOR_TEST`:
1. xác định command/evidence chứng minh claim;
2. chạy fresh repository-native build/test/static checks phù hợp;
3. đọc output/exit code;
4. report failures trung thực;
5. chỉ claim success khi evidence đủ.

`verification-before-completion` là owner của evidence-before-claim, nhưng deterministic project tooling mới là proof.

## Stop rule

```text
1 full review
→ 1 blocking fix wave
→ 0–1 scoped re-review
→ verify
→ STOP
```

Nếu vẫn còn blocker lớn: `NEEDS_REPLAN` hoặc Human/Tech Lead decision.
