# Dev Kit V1 — Routing và Risk Policy

## Mục tiêu

Giữ default path gọn nhưng tăng depth theo evidence/risk. Router không được kích hoạt skill chỉ vì skill đang installed.

## Risk level

### TRIVIAL

Điển hình:
- docs;
- rename;
- mechanical mapping;
- tiny config;
- non-behavioral local edit.

Không có public contract/security/schema/cross-component risk.

### NORMAL

Feature/bug thông thường trong một repo/module, có behavior change nhưng không chạm high-risk boundaries.

### HIGH_RISK

Một hoặc nhiều:
- auth/authz/security boundary;
- sensitive data/PII;
- schema/migration;
- public API/event compatibility;
- cross-service/repo;
- concurrency/locking/transaction;
- deployment topology;
- major architecture change.

Runtime nhận các signal có cấu trúc qua `--signal` (`auth`, `security`, `sensitive_data`, `pii`, `database_migration`, `public_api`, `event_contract`, `cross_repo`, `concurrency`, `major_architecture`, `deployment_topology`). Summary cũng được dò từ khóa high-risk; explicit signal được ưu tiên vì ít mơ hồ hơn.

`docs`, `rename`, `mechanical` và `config` chỉ được xếp TRIVIAL khi không có behavior change hoặc high-risk signal. Các kind còn lại mặc định NORMAL.

## Conditional routing

```text
failure/test red
  → debugging-and-error-recovery

security-sensitive
  → security-and-hardening

API/interface/event contract
  → api-and-interface-design

external framework/API uncertainty
  → source-driven-development

performance requirement/regression
  → performance-optimization

production endpoint/job/queue/external I/O where telemetry matters
  → observability-and-instrumentation

uncertain blast radius
  → codebase-memory-mcp
  → verify important findings against source
```

Route và capability list được kiểm tra bởi `devkit start`; TRIVIAL chạy direct `start → edit → finish-trivial`, còn NORMAL/HIGH_RISK chọn workflow YAML tương ứng. NORMAL không có Human gate. Mỗi HIGH_RISK route yêu cầu plan gate theo V1 policy.

Initial route là provisional. Engineering Impact có thể nâng NORMAL lên HIGH_RISK, nhưng không được hạ HIGH_RISK xuống NORMAL. Vì Spec Kit workflows có gate khác nhau, escalation dừng run NORMAL với `HIGH_RISK_REENTRY_REQUIRED`; tạo run HIGH_RISK mới với cùng Approved BA Baseline và các `--signal` tương ứng trước implementation.

## Human gates

Human/Tech Lead gate không bắt buộc cho mọi normal task. Mandatory gate policy nên áp dụng ít nhất cho:
- breaking public contract;
- schema migration có migration/rollback risk;
- security/auth boundary;
- cross-service architecture;
- deployment topology;
- plan/design thay đổi đáng kể sau implementation discovery.

## Context purity

Daily mode:
- unrelated global skills/hooks/plugins → WARN/DEGRADED.

Benchmark mode:
- unrelated global methodology skills/hooks/plugins → FAIL.

Dev Doctor sau này phải inventory project/user skills, hooks, plugins và MCP servers để phát hiện overlap.
