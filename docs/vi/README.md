# Tài liệu bộ Agent-Assisted SDLC

Đây là mục lục vận hành tiếng Việt của cả suite. Suite có ba Kit theo vai trò và capability Project Foundation dùng chung. Manifest máy là nguồn chuẩn cho phiên bản và contract: [suite](../../tooling/sdlc-suite.json), [catalog Kit](../../kits/README.md).

## Bắt đầu và chọn vai trò

- Mới vào nhóm: [tổng quan suite](../../README.md), [kiến trúc và lifecycle](ARCHITECTURE.md), [quyền quyết định và readiness](READINESS_STATES.md).
- Project Owner / Tech Lead: [Project Foundation](PROJECT_FOUNDATION.md), [Human Gate và kiến trúc](ARCHITECTURE.md), [trạng thái phát hành](RELEASE.md).
- BA: [workflow và Engineering Handoff](BA_KIT_WORKFLOW.md), [quick start](BA_KIT_QUICKSTART.md).
- Developer: [Dev Kit VNext](../../kits/dev/README.md), [workflow](DEV_KIT_WORKFLOW.md), [routing](DEV_KIT_ROUTING.md), [review/xác minh](DEV_KIT_REVIEW_AND_VERIFICATION.md).
- Tester / QA: [Manual Test quick start](TEST_KIT_QUICKSTART.md), [capabilities](TEST_KIT_CAPABILITIES.md), [workflow và approvals](TEST_KIT_WORKFLOW.md).
- Automation Tester: [Automation V1](TEST_AUTOMATION_V1.md), [execution, Finding, defect và retest](TEST_EXECUTION_VNEXT.md).
- Maintainer: [cài đặt, nâng cấp và phục hồi](INSTALLATION.md), [troubleshooting](TROUBLESHOOTING.md), [packaging](../../tooling/PACKAGING.md), [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md), [release](RELEASE.md).

## Project Foundation

[Foundation workflow](PROJECT_FOUNDATION.md) giải thích ba mode GREENFIELD_BOOTSTRAP, BROWNFIELD_RECOVERY, FOUNDATION_REFRESH; ba profile MINIMAL, STANDARD, EXTENDED; và Human Gate. Bản kỹ thuật chi tiết hiện được duy trì bằng tiếng Anh tại [Project Foundation workflow core](../project-foundation.md).

## Cài đặt và kiểm tra

- [Cài BA, Dev, Test và Shared Foundation](INSTALLATION.md)
- [Kit Doctor và Suite Doctor](TROUBLESHOOTING.md#doctor)
- [Nâng cấp và khôi phục package](TROUBLESHOOTING.md#package)

## Các nhiệm vụ theo lifecycle

- BA WHAT, baseline approval và handoff: [BA workflow](BA_KIT_WORKFLOW.md)
- Dev delivery, UPSTREAM_GAP, NEEDS_REPLAN, BLOCKED, READY_FOR_TEST: [Dev workflow](DEV_KIT_WORKFLOW.md), [decision routing](DEV_KIT_ROUTING.md)
- Test Design → APPROVED_DESIGN → Testcases → APPROVED_TESTWARE: [Test workflow](TEST_KIT_WORKFLOW.md)
- Automation Plan → implementation/review → EXECUTION_READY: [Automation](TEST_AUTOMATION_V1.md)
- Execute → Observation → Finding → Dev fix → READY_FOR_RETEST → VERIFIED / REOPENED: [Execution and retest](TEST_EXECUTION_VNEXT.md)

## Reference và release

- [Canonical lifecycle và authority](ARCHITECTURE.md)
- [Readiness/state glossary](READINESS_STATES.md)
- [Public Cross-Kit Conformance](SDLC_SUITE_CONTRACT.md)
- [Release status](RELEASE.md)
- [Current, compatible, historical, deferred](../LEGACY_AND_HISTORY.md)
- [Provenance](PROVENANCE.md)

Tiếng Việt là đường vận hành chính. Counterpart tiếng Anh ghi rõ mức hỗ trợ trong [English index](../en/README.md); nơi chưa có bản đầy đủ sẽ dẫn tới hướng dẫn tiếng Việt.
