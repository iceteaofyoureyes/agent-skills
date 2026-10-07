# Agent-Assisted SDLC Toolkit

**Ngôn ngữ:** [English](README.md) · Tiếng Việt

Bộ toolkit thực tế dành cho team phát triển phần mềm sử dụng AI coding agents xuyên suốt requirement, engineering và testing — nhưng vẫn giữ **Human authority** tại những quyết định quan trọng.

**Agent-Assisted SDLC Toolkit** là tên sản phẩm public-facing. \`agent-skills\` là tên repository; \`agent-assisted-sdlc-vnext\` là machine suite ID dùng cho contract nội bộ.

> Mới bắt đầu? Đọc [Bắt đầu](docs/vi/GETTING_STARTED.md).  
> New here? Read [Getting Started](docs/en/GETTING_STARTED.md).

## Bộ này giải quyết vấn đề gì?

AI agent có thể làm việc rất nhanh, nhưng team vẫn cần:

- phân định rõ ai sở hữu WHAT / HOW / verification;
- handoff có trace và bind đúng input đã được duyệt;
- Human Gate ở các quyết định cần authority;
- evidence để biết stage sau đang dùng đúng requirement / implementation / testcase;
- fail-closed khi context, approval hoặc revision không còn hợp lệ.

Toolkit tách trách nhiệm thành bốn capability chính:

| Capability | Sở hữu | Dùng khi |
|---|---|---|
| **Project Foundation** | Project context | Project mới, brownfield recovery hoặc cần refresh context hệ thống |
| **BA Kit** | **WHAT** hệ thống cần làm | Requirement, Business Rules, SRS, clarification, Engineering Handoff |
| **Dev Kit** | **WHERE / WHO OWNS / HOW** | Impact analysis, technical decisions, implementation, engineering verification |
| **Test Kit** | **PROVE IT** | Test Design, Testcases, Automation, Execution, Finding, defect, retest, verification |

Không bắt buộc phải dùng cả ba Kit. Có thể dùng từng Kit độc lập nếu authority input bắt buộc đã tồn tại.

## Full flow hoạt động như nào?

~~~text
Requirement / Change
        │
        ▼
Project Foundation ── khi cần tạo hoặc khôi phục project context
        │
        ▼
BA Kit ── chốt WHAT
        │
        │ Human approve exact business baseline
        ▼
Dev Kit ── thiết kế và implement HOW
        │
        ▼
READY_FOR_TEST
        │
        ▼
Test Kit
   │
   ├─ mọi required test PASS, không còn Finding
   │      └─ Tester → VERIFIED
   │
   └─ Finding
          ├─ DEFECT → Dev Fix → READY_FOR_RETEST → Tester Retest
          │              ├─ PASS → VERIFIED
          │              └─ FINDING → REOPENED
          └─ SPEC_GAP / BUSINESS_DECISION_REQUIRED /
             TEST_ISSUE / ENVIRONMENT_ISSUE
             → route tới owner phù hợp
~~~

\`VERIFIED\` kết thúc product-verification lifecycle của framework. **Merge/release vẫn là quyết định Human riêng.**

## Bắt đầu trong 5 phút

1. Đọc [Bắt đầu](docs/vi/GETTING_STARTED.md).
2. Chọn đúng Kit cho vai trò; **không cần cài tất cả**.
3. Cài từ exact committed ref và chạy Doctor tương ứng.
4. Xem [Ví dụ Full Flow](docs/vi/FULL_FLOW_EXAMPLE.md).
5. Nếu còn thuật ngữ chưa rõ, đọc [FAQ](docs/vi/FAQ.md).

Command cài đặt, supported targets, upgrade và recovery: [Cài đặt](docs/vi/INSTALLATION.md).

English: [Getting Started](docs/en/GETTING_STARTED.md) · [Installation](docs/en/INSTALLATION.md)

## Human vẫn giữ quyền quyết định

Toolkit không xem output do agent sinh ra, validator PASS hay Doctor READY là approval.

~~~text
CONTINUE != APPROVE
ANSWER != APPROVE
validator PASS != APPROVE
generated != APPROVED
READY_FOR_TEST != VERIFIED
APPROVED_TESTWARE != EXECUTION_READY
EXECUTION_READY != PASS
~~~

Khi workflow yêu cầu Human Gate, approval được bind với đúng artifact/revision đã review.

## Supported path hiện tại

- **Primary verified end-to-end path:** Codex + integration hiện tại của toolkit.
- **BA Kit:** có thêm Claude Code và generic installation targets ở những nơi tài liệu ghi rõ.
- **Python:** dùng Python **3.10+** cho documented BA/Test baseline và cấu hình full-toolkit ít bất ngờ nhất.
- **Windows/Linux:** checkout behavior được kiểm soát bằng \`.gitattributes\`; không có hidden prerequisite \`core.autocrlf=false\`.
- **XMind / Excel projection:** optional; thiếu projection không làm Test core unusable.

Chi tiết: [Cài đặt](docs/vi/INSTALLATION.md).

## Tài liệu

### Tôi chỉ muốn dùng Toolkit

- [Bắt đầu](docs/vi/GETTING_STARTED.md) · [Getting Started](docs/en/GETTING_STARTED.md)
- [Ví dụ Full Flow](docs/vi/FULL_FLOW_EXAMPLE.md) · [Full Flow Example](docs/en/FULL_FLOW_EXAMPLE.md)
- [FAQ](docs/vi/FAQ.md) · [English FAQ](docs/en/FAQ.md)
- [Cài đặt](docs/vi/INSTALLATION.md) · [Installation](docs/en/INSTALLATION.md)
- [Troubleshooting](docs/vi/TROUBLESHOOTING.md) · [English](docs/en/TROUBLESHOOTING.md)

### Tôi dùng một role/Kit cụ thể

- BA: [BA workflow](docs/vi/BA_KIT_WORKFLOW.md) · [English](docs/en/BA_KIT_WORKFLOW.md)
- Developer: [Dev workflow](docs/vi/DEV_KIT_WORKFLOW.md) · [English guide](docs/en/DEV_KIT_GUIDE.md)
- Tester: [Test Quick Start](docs/vi/TEST_KIT_QUICKSTART.md) · [English overview](docs/en/TEST_KIT_MANUAL.md)
- Automation / Execution: [Automation](docs/vi/TEST_AUTOMATION_V1.md) · [Execution & Retest](docs/vi/TEST_EXECUTION_VNEXT.md)
- Project Owner / Tech Lead: [Project Foundation](docs/vi/PROJECT_FOUNDATION.md)

### Tôi cần đọc contract/reference sâu hơn

- [Kiến trúc và lifecycle](docs/vi/ARCHITECTURE.md)
- [Readiness states](docs/vi/READINESS_STATES.md)
- [Public Cross-Kit Conformance](docs/vi/SDLC_SUITE_CONTRACT.md)
- [Packaging](tooling/PACKAGING.md)
- [Legacy và history](docs/LEGACY_AND_HISTORY.md)

Các contract chi tiết được tách khỏi newcomer path có chủ đích để người mới không phải học vocabulary nội bộ trước khi dùng Kit.

## Trạng thái release hiện tại

Repository vẫn là **internal prerelease candidate**, chưa phải stable public release. Machine-readable manifests là authority cho version chính xác:

| Component | Current candidate |
|---|---|
| Suite | \`agent-assisted-sdlc-vnext 1.0.0-rc.4\` |
| BA Kit | \`2.0.0-rc.6\` |
| Dev Kit | \`0.4.0-rc.4\` |
| Test Kit | \`2.0.0-rc.14\` |

Xem [Release status](docs/vi/RELEASE.md). Conformance PASS là evidence cho Human review; nó không tự authorize merge, tag hoặc release.
