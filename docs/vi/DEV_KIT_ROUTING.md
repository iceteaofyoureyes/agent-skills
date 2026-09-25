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

complex/high-risk plan
  → speckit analyze

long/multi-session/drift-risk implementation
  → speckit converge
```

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
