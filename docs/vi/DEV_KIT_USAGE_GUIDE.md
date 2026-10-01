# Dev Kit V1 — Hướng dẫn sử dụng

Dev Kit nhận **Approved BA Baseline** làm WHAT authority, rồi xác định phạm vi kỹ thuật, ownership, cách triển khai và evidence. Dev Kit không sửa hoặc diễn giải lại business semantics.

## 1. Yêu cầu môi trường

- Python 3.8+ và Git cho Dev Kit CLI/direct TRIVIAL path.
- GitHub Spec Kit CLI đúng `v1.0.11` và một agent integration đã khởi tạo cho NORMAL/HIGH_RISK workflow/resume. Spec Kit cần Python 3.11+; TRIVIAL direct path không cần Spec Kit.
- V1 không gọi `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.analyze` hoặc `speckit.converge` và không tạo `spec.md`.
- NORMAL/HIGH_RISK cần một BA Engineering Handoff đã được duyệt, cùng các nguồn business mà handoff tham chiếu.

## 2. Cài plugin

Repository có marketplace local tại `.agents/plugins/marketplace.json`. Từ Codex CLI ở root repository:

```powershell
codex plugin marketplace add .
codex plugin marketplace list
```

Lệnh CLI đăng ký marketplace source trong user config. Để cài và thử plugin local, mở ChatGPT desktop app → Plugins Directory → chọn marketplace và plugin → Install. Sau đó mở agent session mới. Plugin source vẫn là `kits/dev/plugin/` trong repository. Xem [OpenAI plugin marketplace documentation](https://developers.openai.com/plugins/build/plugins#marketplace-metadata).

Gỡ plugin trong Plugins Directory của ChatGPT desktop app, sau đó gỡ marketplace source khỏi Codex user config:

```powershell
codex plugin marketplace remove agent-skills-dev-kit
```

Cài runtime helper một lần từ checkout Dev Kit. Runtime nằm ngoài target project và installer chỉ chép helper,
BA contract reader dùng chung, schemas/templates và hai workflow vào user scope; không chép skill methodology:

```powershell
# Chạy trong checkout agent-skills
python tooling/install_dev_kit.py
$env:PATH = "$HOME\.devkit\bin;$env:PATH"
devkit runtime-root
```

Với Bash, thêm `$HOME/.devkit/bin` vào `PATH`. Để giữ cấu hình cho terminal mới, thêm thư mục này vào user PATH của hệ điều hành.
Agent plugin/skills được cài riêng qua marketplace như trên. Target project chỉ nhận `.devkit/` và `.specify/` state.

Khởi tạo Spec Kit một lần nếu sẽ chạy NORMAL/HIGH_RISK và project chưa có workflow state:

```powershell
specify --version
specify init
```

`specify init` chuẩn bị project/runtime integration. Không chạy các feature-spec commands bị loại trừ ở trên.

## 3. Bắt đầu một change

Chạy từ root của **target project** (có thể là repository khác checkout Dev Kit). Mỗi `--check` là JSON gồm tên, nhóm và argv;
argv được chạy trực tiếp với `shell=False`.

```powershell
devkit start `
  --change-id CR-042 `
  --kind feature `
  --summary "Add appointment search" `
  --baseline "docs/approved/engineering-handoff.yml" `
  --check '{"name":"build","category":"build","argv":["python","-m","compileall","src"]}' `
  --check '{"name":"unit","category":"tests","argv":["python","-m","unittest","discover","-s","tooling/tests"]}'
```

NORMAL/HIGH_RISK phải khai báo một build check và một tests check. `start` kiểm tra baseline approval và SHA-256 nguồn của baseline trước khi ghi `.devkit/`; Dev artifacts không chứa bản sao requirements.

Các đường dẫn baseline/check trong ví dụ là mẫu; thay bằng BA handoff đã duyệt, nguồn được hash trong handoff và lệnh build/test/static checks của repo.

## 4. Chạy theo risk depth

### TRIVIAL

Ví dụ docs, rename hoặc thay đổi cơ khí không làm đổi behavior:

```powershell
devkit start --change-id DOCS-10 --kind docs --summary "Fix README typo" `
  --check '{"name":"docs","category":"static_checks","argv":["git","diff","--check"]}'
# Make the requested edit in the active agent session, then:
devkit finish-trivial
```

Đường đi trực tiếp chỉ hiểu yêu cầu, sửa và chạy deterministic check. Không cần Spec Kit; không tạo plan/tasks, full review, CBM hoặc specialist stage.

### NORMAL

Ví dụ feature hoặc bug thông thường:

```powershell
specify workflow run (devkit workflow normal)
```

Workflow chạy Spec Readiness, planning preflight/Impact, technical plan/tasks, deterministic plan gate, implementation, focused checks,
một full review, nhiều nhất một blocking fix wave, optional một scoped re-review, fresh verification và Dev Handoff. NORMAL không có
Human plan approval gate bắt buộc. Bug phải có regression test trước fix; behavior change dùng TDD ở seam có ý nghĩa. Mỗi plan/task
file phải có one-line JSON `devkit-planning-metadata` header với `change_id`, `baseline_ref` copy chính xác từ `input.json`, và
`business_ambiguity: CLEAR`, sau đó có nội dung kỹ thuật không rỗng.

### HIGH_RISK

Ví dụ endpoint có auth hoặc thay đổi schema:

```powershell
devkit start --change-id API-17 --kind feature `
  --summary "Add authenticated appointment endpoint" --signal auth --signal public_api `
  --baseline "docs/approved/engineering-handoff.yml" `
  --check '{"name":"build","category":"build","argv":["python","-m","compileall","src"]}' `
  --check '{"name":"unit","category":"tests","argv":["python","-m","unittest","discover","-s","tests"]}'
specify workflow run (devkit workflow high-risk)
```

Router kích hoạt `security-and-hardening` cho auth/security/sensitive data/PII và `api-and-interface-design` cho public API/event contract. HIGH_RISK có Human/Tech Lead plan gate. `codebase-memory-mcp` chỉ được dùng khi source reading chưa đủ xác định blast radius.

Bug thông thường ở NORMAL depth bắt đầu bằng regression test:

```powershell
devkit start --change-id BUG-08 --kind bug `
  --summary "Prevent duplicate appointment creation" `
  --baseline "docs/approved/engineering-handoff.yml" `
  --check '{"name":"build","category":"build","argv":["python","-m","compileall","src"]}' `
  --check '{"name":"tests","category":"tests","argv":["python","-m","unittest","discover","-s","tests"]}'
specify workflow run (devkit workflow normal)
```

Cross-repository change route:

```powershell
devkit start --change-id XREPO-4 --kind feature `
  --summary "Update shared appointment event consumer" --signal cross_repo `
  --baseline "docs/approved/engineering-handoff.yml" `
  --check '{"name":"build","category":"build","argv":["python","-m","compileall","src"]}' `
  --check '{"name":"tests","category":"tests","argv":["python","-m","unittest","discover","-s","tests"]}'
specify workflow run (devkit workflow high-risk)
```

## 5. Routing signals

`--signal` nhận `auth`, `security`, `sensitive_data`, `pii`, `database_migration`, `public_api`, `event_contract`, `cross_repo`, `concurrency`, `major_architecture`, `deployment_topology`, `performance`, `observability`, `external_api_uncertainty`, `uncertain_blast_radius`. Summary text cũng được quét theo risk terms; explicit signal là cách chắc chắn hơn.

`--kind config` mặc định là non-behavioral; nếu đổi config làm đổi behavior, thêm `--behavior-change` để route sang NORMAL.

Conditional skills:

Initial route là provisional. Nếu source inspection trong NORMAL phát hiện HIGH_RISK, `preflight` dừng với
`HIGH_RISK_REENTRY_REQUIRED`; không thể tiếp tục run NORMAL vào implementation. Tạo run mới với cùng baseline và
`--signal` tương ứng Impact reasons (ví dụ `public_api`, `database_migration`, `cross_repo`), rồi chạy HIGH_RISK
workflow. Run mới áp dụng capability routing và Human/Tech Lead gate trước implementation. Impact không được hạ
HIGH_RISK xuống NORMAL.

- unexpected failure → `debugging-and-error-recovery`;
- auth/security/trust boundary/sensitive data → `security-and-hardening`;
- API/interface/event contract → `api-and-interface-design`;
- framework/API uncertainty → `source-driven-development`;
- measured/requested performance concern → `performance-optimization`;
- production endpoint/job/queue needing telemetry → `observability-and-instrumentation`;
- uncertain callers/dependencies → optional `codebase-memory-mcp`.

Installed capability không có nghĩa là workflow phải invoke capability đó. Performance và observability không tự bật chỉ vì change là HIGH_RISK.

## 6. Business ambiguity

Nếu đã biết business decision còn thiếu, chặn trước khi tạo workflow:

```powershell
devkit start --change-id CR-043 --kind feature `
  --summary "Add cancellation" --business-ambiguity "refund timing is undecided"
```

Lệnh trả `NEEDS_BA_CLARIFICATION` và exit code 12. Nếu gap auditor phát hiện ambiguity trong Spec Readiness, preflight lưu `NEEDS_BA_CLARIFICATION` rồi dừng trước planning. Sau khi BA cập nhật/duyệt baseline, tạo run mới với baseline revision mới; không tiếp tục run dựa trên baseline cũ.

## 7. Review và recovery

- Full review chỉ chạy một lần. Các `claim` step và lifecycle budget từ chối lần thứ hai.
- Fix prompt gom mọi BLOCKING finding vào một wave. FOLLOW_UP không mở rộng scope.
- Scoped re-review chỉ được claim khi fix đổi logic/risk; scope là blockers cũ và fix diff.
- Còn blocker sau fix/re-review → `NEEDS_REPLAN` hoặc `HUMAN_TECH_LEAD_REVIEW`; không bắt đầu review loop mới.
- Nếu workflow lỗi bất ngờ, xem `specify workflow status`, run ID và `.devkit/runs/<change_id>/lifecycle.json`; dùng `specify workflow resume <run-id>` để tiếp tục tại top-level step đã lưu.
- High-risk gate cần operator trả lời trong interactive terminal. Nếu run dừng ở gate vì không có TTY, resume từ terminal tương tác và chọn `approve` hoặc `reject`; workflow không nhận Human verdict qua prompt input của agent.
- Workflow definitions không đặt gate bên trong nhánh lồng nhau, để resume không chạy lại plan hoặc review trước gate.

Ví dụ consolidated review trả một BLOCKING finding và một FOLLOW_UP:

```json
{
  "full_review_performed": true,
  "blocking_findings": [
    {"id": "REV-001", "class": "BLOCKING", "description": "Authorization check is missing"}
  ],
  "followups": [
    {"id": "REV-002", "class": "FOLLOW_UP", "description": "Unrelated naming cleanup"}
  ]
}
```

REV-001 đi vào một fix wave. REV-002 được giữ ngoài scope. Nếu report chỉ có FOLLOW_UP, workflow ghi `performed=false` và không làm cleanup đó.

High-risk approval step đọc `steps.human-tech-lead-plan-gate.output.choice` và workflow run ID từ Spec Kit context, sau đó
đối chiếu verdict với `.specify/workflows/runs/<run_id>/state.json`. Handoff ghi choice, run ID, state path và hash plan/tasks.
Đây là evidence/audit trail trong workspace; người có quyền sửa local files vẫn có thể thay đổi state, nên nó không phải chữ ký
mật mã hay bảo đảm chống giả mạo.

## 8. Artifacts và state

| Nội dung | Đường dẫn |
|---|---|
| Spec Kit workflow state/log | `.specify/workflows/runs/<run-id>/` |
| Dev run inputs, route, lifecycle, budget | `.devkit/runs/<change_id>/` |
| Impact Manifest | `.devkit/runs/<change_id>/impact-manifest.json` |
| Readiness result | `.devkit/runs/<change_id>/spec-readiness.json` |
| Technical plan/tasks | `.devkit/runs/<change_id>/dev-plan.md`, `dev-tasks.md`; require one-line metadata header and non-empty content |
| Full review/fix/re-review | `review.json`, `fix-result.json`, `scoped-rereview.json` trong cùng run dir |
| Final handoff | `.devkit/runs/<change_id>/dev-handoff.json` |
| Installed JSON Schemas/templates | `devkit schema impact-manifest`, `devkit schema dev-handoff`; stored under `~/.devkit/runtime/v1/kits/dev/` |

`dev-plan.md` và `dev-tasks.md` bắt đầu bằng comment metadata một dòng JSON; copy `change_id` và `baseline_ref` từ active
`input.json`, đặt ambiguity thành CLEAR, rồi ghi phần kỹ thuật bên dưới:

```markdown
<!-- devkit-planning-metadata
{"change_id":"CR-042","baseline_ref":{"path":"docs/approved/engineering-handoff.yml","revision":"ba-rev-7","sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"},"business_ambiguity":"CLEAR"}
-->

# Technical plan or tasks
```

V1 chỉ cho phép một run Dev đang active per working tree; dùng worktree riêng nếu cần chạy changes đồng thời. `.devkit/` đã được git-ignore.

## 9. Dev Doctor

Human-readable:

```powershell
python tooling/lib/dev_kit.py doctor --mode daily --project-root <target-project>
python tooling/lib/dev_kit.py provenance
```

Machine-readable:

```powershell
python tooling/lib/dev_kit.py doctor --mode daily --project-root <target-project> --json
python tooling/lib/dev_kit.py doctor --mode benchmark --project-root <target-project> --json
```

Doctor/provenance là maintenance commands trong Dev Kit source checkout; khi gọi Doctor cho target khác, `--project-root` trỏ vào target đó. Doctor kiểm tra composition/plugin marketplace, schemas/fixtures, Spec Kit runtime, shared skills, selected blobs/licenses/notices, planner patch, review budget, workflow exclusions và context purity. Nó quét Codex `.agents/skills`, `.codex/skills`, `.codex/plugins` và `.codex/config.toml` ở project/user scope. Daily contamination là WARN/DEGRADED. Benchmark mode trả FAIL khi có relevant methodology contamination. `CONTEXT_PURITY` là `CLEAN` hoặc `DEGRADED`.

## 10. Failure/recovery examples

| Trường hợp | Kết quả / hành động |
|---|---|
| NORMAL Impact phát hiện public API/schema/cross-service risk | Dừng ở preflight; tạo run ID mới với HIGH_RISK `--signal` tương ứng và chạy high-risk gate trước implementation. |
| Build/test đỏ sau implementation | Workflow dừng; giữ output trong lifecycle/run state, dùng debugging capability nếu cần, sửa nguyên nhân rồi resume step lỗi. |
| Business behavior chưa rõ | `NEEDS_BA_CLARIFICATION`; quay lại BA, tạo run mới từ baseline được duyệt. |
| Blocking review finding | Chạy một fix wave; nếu vẫn còn blocker, `NEEDS_REPLAN`/`HUMAN_TECH_LEAD_REVIEW`. |
| FOLLOW_UP finding | Ghi follow-up, giữ ngoài scope hiện tại. |
| Baseline hash đổi giữa workflow | Runtime dừng với lỗi immutability; xác minh BA approval rồi tạo run mới. |
| Agent session/workflow bị ngắt | `specify workflow resume <run-id>`; Spec Kit giữ state theo step. |

## 11. Giới hạn và release state

- Artifact format là JSON để validator chạy bằng Python standard library; schema files là JSON Schema.
- Runtime installer cài helper/schema/workflow closure vào user scope `~/.devkit/runtime/v1`; target chỉ cần `devkit` trong PATH và ghi state vào `.devkit/` cùng `.specify/`.
- Context Doctor quét các đường dẫn Codex chuẩn; custom `CODEX_HOME` hoặc marketplace/host registry ngoài các đường dẫn này có thể chưa được nhìn thấy.
- Petclinic benchmark, fresh-session acceptance và Sol review chưa chạy trong phase này. Trạng thái là `READY_FOR_SOL_REVIEW`, không phải RC/release.
