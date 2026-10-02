# Candidate remediation sau Golden Run 01

Base đã review: `4f2932fc85673a5cfb8aa974b30d1c2c547608e1`.
Branch: `fix/golden-g3-windows-runtime-and-gate-persistence-v1`.
Candidate dành cho review trước khi freeze Golden Run 02; không merge hoặc áp dụng vào Golden Run 01.
Exact final commit và acceptance evidence sau commit được báo trong handoff; không self-reference commit hash trong chính commit.

## Dev executable resolution

DEV-TOOL-01 xảy ra trước application check: Windows process creation không resolve bare `npm` qua PATHEXT như shell hoặc `shutil.which`. PATH và repository script đều đúng.

`resolve_executable_argv` trong generic runner dùng `shutil.which` cho bare names trên Windows, giữ exact resolved path và từng argument. Explicit paths (kể cả drive-relative) không rewrite; POSIX giữ behavior cũ. FOCUSED_CHECKS và FRESH_VERIFICATION dùng cùng helper với `shell=False`, không generic cmd.exe hoặc shell=True. Executable không tìm thấy trả FAIL với `EXECUTABLE_NOT_FOUND`; không crash hoặc giả thành application assertion failure. Recorded command vẫn là repository-declared argv, không thêm field vào Dev Handoff schema.

## Human Gate transaction

Design và Case Gate đều có hazard receipt → artifacts → state. Trước remediation, failure sau receipt làm retry bị RECEIPT_REPLAY dù state chưa transition. Cả APPROVE và REQUEST_CHANGES đã chuyển sang chung `gate_persistence`:

1. Validate current immutable inputs, exact snapshot, receipt schema/input refs, host-authenticated Human và next revision.
2. Compute tất cả output bytes và final workflow/history từ original review.
3. Preflight path budget, writable ancestor và existing immutable conflicts trước receipt consumption.
4. Publish immutable `tx.json` journal bind exact receipt SHA, original/final workflow và output digests; journal cũng được kiểm tra schema/path containment khi replay.
5. Publish receipt và derived artifacts bằng write-if-same-or-absent. Temp file được flush/fsync rồi publish bằng exclusive hard link; crash không để lại truncated canonical evidence.
6. Atomic replace workflow là commit cuối. Exact replay reconstruct từ journal nhưng vẫn revalidate inputs/auth/snapshot và toàn bộ outputs; không trust terminal state riêng lẻ.

Absent artifact được tạo; same bytes thành công; different bytes fail closed, không overwrite. Exact partial receipt recover được; exact completed replay idempotent và không thêm history/artifact. Different receipt (kể cả feedback/timestamp khác) bị reject. Journal/state/output tampering bị reject. Legacy partial receipt khi original REVIEW còn nguyên có thể được bind vào transaction mới ở candidate API; không tự recover hay migrate historical Golden.

Design REQUEST_CHANGES giữ receipt và CHANGES_REQUESTED projection của revision cũ; revision mới có semantic/canonical draft, workflow DRAFT_DESIGN/NOT_RUN và exact derived_from. APPROVE bind projection, receipt provenance và APPROVED_DESIGN/PASS. Case Gate tương đương với DRAFT_CASES hoặc STOP_V1; giữ state_history contract và thêm internal human_gate_history có đúng một Human event bind receipt. Transaction journal luôn reconstruct từ before endpoint, nên recovery không duplicate event.

## Windows path budget và layout

`runtime_paths` tập trung policy: khi Windows long paths không được hỗ trợ, file budget 259 UTF-16 code units và parent budget 247. Preflight tính cả bounded temp name và cung cấp offending path, actual length, safe budget, stage/transition/platform. Không sửa registry.

Prepare/finalize Design và Cases dùng centralized catalog; dynamic baseline destinations cũng được kiểm tra. Gate compute toàn bộ paths, gồm next revision và atomic state destination, trước receipt. Promotion preflight toàn bộ destination/conflicts trước bất kỳ publication nào. Execution contract module chỉ xử lý state objects, không có filesystem Human receipt transaction để migrate.

| Internal artifact | New runtime name | Compatibility |
|---|---|---|
| Design approved projection | canonical/approved.json | Legacy verbose file được đọc/resume tại chỗ nếu đã có |
| Design changes projection | design-gate/revisions/<rev>/changes.json | Legacy verbose file không bị rename/overwrite |
| Case approved projection | approved.json | Excel reader hỗ trợ compact và legacy naming |
| Case changes projection | case-gate/changes.json | Legacy old-snapshot projection hỗ trợ tại chỗ |
| Next revision semantic | canonical/semantic.json | Reader hỗ trợ legacy semantic-payload.json |
| Next Design/Case draft | canonical/design.json hoặc cases.json | Existing canonical names vẫn được hỗ trợ |

Nếu compact và legacy cùng tồn tại nhưng khác bytes, reject ambiguity. Public/promoted `test-design.json`, `testcases.json`, Markdown và approval names không đổi. Nếu root vẫn quá dài, fail trước receipt thay vì yêu cầu bật LongPaths. Windows smoke dùng disposable run path dài 216 ký tự; legacy changes path vượt 259 nhưng compact gate transitions vẫn chạy khi LongPathsEnabled=0.

## Case Gate và promotion audit

Case Gate cần remediation cho cả decisions; đã dùng cùng journal/preflight/atomic primitives, vẫn authenticate Human, validate approved Design/BA/execution oracles, giữ SEMANTIC_ORACLE approval blockers. TEST_ONLY path giữ isolation và không được promote production testware.

Fresh installed smoke cũng xác nhận Case Review giữ recorded policy context của invocation khi legacy caller không truyền context; supplied context khác bị reject. Metadata propagation này không thay policy/business authority.

Promotion đã có same-byte idempotency nhưng thiếu all-destination preflight và atomic immutable writes. Đã bổ sung cả hai; exact retry sau partial publication hoàn tất artifacts thiếu, late conflict không gây partial new publication. Không có receipt mới bị consume trong promotion; promotion marker chỉ xuất hiện sau semantic/Markdown/receipt publication.

## Versions và provenance

| Package | Base | Candidate |
|---|---|---|
| BA | 2.0.0-rc.2 | 2.0.0-rc.2 |
| Dev/plugin | 0.3.0-rc.2 | 0.3.0-rc.3 |
| Test | 2.0.0-rc.3 | 2.0.0-rc.4 |

BA manifest và toàn bộ selected distributed source paths không đổi. Test allowlist bổ sung hai centralized runtime modules; package authority/raw payload pins được regenerate. New selected source files được pin LF trong .gitattributes để source package hashes ổn định giữa Windows/POSIX.

Dev provenance bổ sung digest cho project-owned runtime core/kit/plugin definition, có verifier; upstream skill/license blob locks giữ nguyên. Fresh Dev install manifest vẫn bind toàn bộ installed files bằng exact hashes. `regenerate_dev_provenance.py` và `regenerate_test_package.py` tạo pins từ source. Suite lock được generate tại clean exact HEAD, cùng dedicated profile mới; lock/evidence là runtime output ignored, không copy profile hoặc credentials của Golden.

Wire contracts giữ nguyên base: BA handoff 1, Delivery Manifest 2, UX receipt 2 (V1 compatible), testware gate 2, Golden provenance 1. Không bump contract number chỉ vì runtime persistence implementation thay đổi.

## Regression và handoff

Tests-first đã tái hiện Dev executable failure, Design completed replay/partial receipt và Case completed replay failures trước fix. Regression có fault injection trước/sau mỗi immutable write, trước/sau workflow commit cho cả hai gates/decisions; exact recovery, different receipt, output/state/journal conflict; simulated supported/unsupported long paths; real Windows npm version/synthetic build; source/installed parity và isolated Python installed gate smoke.

Validation groups:

- Dev: 40 tests (8 resolver regressions + 32 existing).
- Design/Case source regressions: 123 tests.
- Recovery/path regressions: 18 tests, gồm symlink smoke có thể INFRA_BLOCKED khi Windows thiếu privilege; không coi SKIP là PASS.
- Isolated installed Test runtime: 1 test, bốn gate transitions với fault/replay.
- Package integrity/install: 32 tests; Delivery Manifest V2: 18 tests.
- Full regression chạy lại từ final candidate; exact totals và mọi skip reasons nằm trong acceptance handoff.
- Suite Doctor phải READY tại final exact HEAD, từ fresh registered profile và pinned Spec Kit; không dùng smoke fixtures làm production approval.

Delivery V2 giữ immutable UX sources/receipt raw SHA/provenance, legacy Golden V1 receipt và exact method string, V2 method UX_APPROVED_SOURCES_CANONICAL_JSON_SHA256_V2, optional Prototype, contract-only approval, declared Prototype exact bytes và REVIEW_EVIDENCE, aggregate recomputation/tampering rejection, V1 manifest rejection.

Golden Run 01 là failure evidence: không đổi registry, installed runtime, receipt, state, BA/UX/Manifest hoặc Dev working tree. Frozen local/remote integration branch vẫn `da332927e6ce19849b9bdeee9befc18130294c03`. Candidate chưa được merge, chưa được freeze hoặc bắt đầu Golden Run 02.
