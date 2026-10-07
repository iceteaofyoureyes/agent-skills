# Agent-Assisted SDLC Toolkit

**Language:** English · [Tiếng Việt](README.vi.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](docs/en/INSTALLATION.md)
[![Status](https://img.shields.io/badge/status-internal%20RC-orange.svg)](docs/en/RELEASE.md)

A practical toolkit for software teams using AI coding agents across requirements, engineering, and testing — while keeping Human approval at the decisions that matter.

The public product name is **Agent-Assisted SDLC Toolkit**. The GitHub repository is \`agent-skills\`; the machine suite ID \`agent-assisted-sdlc-vnext\` is an internal contract identifier.

> New here? Start with [Getting Started](docs/en/GETTING_STARTED.md). Vietnamese: [Bắt đầu](docs/vi/GETTING_STARTED.md).

## What problem does it solve?

AI agents can produce useful work quickly, but teams still need clear ownership, reproducible handoffs, review gates, and evidence that later stages used the right approved inputs.

This toolkit separates responsibilities:

| Capability | Owns | Use it when |
|---|---|---|
| **Project Foundation** | Project context | Starting a new project, recovering a brownfield project, or refreshing stale system knowledge |
| **BA Kit** | **WHAT** the system must do | Requirements, business rules, SRS, ambiguity resolution, approved Engineering Handoff |
| **Dev Kit** | **WHERE / WHO OWNS / HOW** | Impact analysis, technical decisions, implementation, engineering verification |
| **Test Kit** | **PROVE IT** | Test Design, Testcases, Automation, Execution, Findings, defects, retest and verification |

You can use a Kit independently when its required authority inputs already exist, or use the full flow.

## How the full flow works

~~~text
Requirement / Change
        │
        ▼
Project Foundation ── when project context must be created or recovered
        │
        ▼
BA Kit ── defines WHAT
        │
        │ Human approves the exact business baseline
        ▼
Dev Kit ── designs and implements HOW
        │
        ▼
READY_FOR_TEST
        │
        ▼
Test Kit
   │
   ├─ all required tests PASS, no open Finding
   │      └─ Tester → VERIFIED
   │
   └─ Finding
          ├─ DEFECT → Dev Fix → READY_FOR_RETEST → Tester Retest
          │              ├─ PASS → VERIFIED
          │              └─ FINDING → REOPENED
          └─ SPEC_GAP / BUSINESS_DECISION_REQUIRED /
             TEST_ISSUE / ENVIRONMENT_ISSUE
             → route to the responsible owner
~~~

\`VERIFIED\` ends the framework's product-verification lifecycle. Merge and release remain separate Human decisions.

## Start in five minutes

1. Read [Getting Started](docs/en/GETTING_STARTED.md) or [Bắt đầu](docs/vi/GETTING_STARTED.md).
2. Choose the Kit for your role; you do **not** need to install every Kit.
3. Install from an exact committed ref and run the matching Doctor.
4. Try the [small end-to-end example](docs/en/FULL_FLOW_EXAMPLE.md).
5. Use [FAQ](docs/en/FAQ.md) if a term or boundary is unclear.

For complete commands, supported targets, upgrades, and recovery, see [Installation](docs/en/INSTALLATION.md).

## Human control is intentional

The toolkit never treats an agent-generated file, validator result, or Doctor result as Human approval.

~~~text
CONTINUE != APPROVE
ANSWER != APPROVE
validator PASS != APPROVE
generated != APPROVED
READY_FOR_TEST != VERIFIED
APPROVED_TESTWARE != EXECUTION_READY
EXECUTION_READY != PASS
~~~

Human approval is bound to exact reviewed artifacts where the workflow requires it.

## Supported path

- **Primary verified end-to-end path:** Codex-based workflow with the repository's current Spec Kit integration.
- **BA Kit:** also exposes Claude Code and generic installation targets where documented.
- **Python:** use Python **3.10+** for the documented BA/Test support baseline and the simplest full-toolkit setup.
- **Windows/Linux:** supported repository checkout behavior is controlled by \`.gitattributes\`; no hidden \`core.autocrlf=false\` prerequisite.
- **XMind / Excel projections:** optional; missing projections do not make the Test core unusable.

See [Installation](docs/en/INSTALLATION.md) for exact capability-specific requirements.

## Documentation

### I just want to use the toolkit

- [Getting Started](docs/en/GETTING_STARTED.md) · [Bắt đầu](docs/vi/GETTING_STARTED.md)
- [Full Flow Example](docs/en/FULL_FLOW_EXAMPLE.md) · [Ví dụ full flow](docs/vi/FULL_FLOW_EXAMPLE.md)
- [FAQ](docs/en/FAQ.md) · [Câu hỏi thường gặp](docs/vi/FAQ.md)
- [Installation](docs/en/INSTALLATION.md) · [Cài đặt](docs/vi/INSTALLATION.md)
- [Troubleshooting](docs/en/TROUBLESHOOTING.md) · [Khắc phục sự cố](docs/vi/TROUBLESHOOTING.md)

### I use one role/Kit

- BA: [BA workflow](docs/en/BA_KIT_WORKFLOW.md) · [Tiếng Việt](docs/vi/BA_KIT_WORKFLOW.md)
- Developer: [Dev guide](docs/en/DEV_KIT_GUIDE.md) · [Tiếng Việt](docs/vi/DEV_KIT_WORKFLOW.md)
- Tester: [Manual Test overview](docs/en/TEST_KIT_MANUAL.md) · [Tiếng Việt](docs/vi/TEST_KIT_QUICKSTART.md)
- Automation / Execution: [Automation](docs/en/TEST_AUTOMATION_V1.md) · [Execution & Retest](docs/en/TEST_EXECUTION_VNEXT.md)
- Project Owner / Tech Lead: [Project Foundation](docs/en/PROJECT_FOUNDATION.md)

### I need the contracts/reference

- [Architecture and lifecycle](docs/en/ARCHITECTURE.md)
- [Readiness states](docs/en/READINESS_STATES.md)
- [Public Cross-Kit Conformance](docs/en/SDLC_SUITE_CONTRACT.md)
- [Packaging](tooling/PACKAGING.md)
- [Legacy and history](docs/LEGACY_AND_HISTORY.md)

The detailed contracts are intentionally separate from the newcomer path.

## Current release status

This repository is still an **internal prerelease candidate**, not a stable public release. Machine-readable manifests own the exact versions:

| Component | Current candidate |
|---|---|
| Suite | \`agent-assisted-sdlc-vnext 1.0.0-rc.4\` |
| BA Kit | \`2.0.0-rc.6\` |
| Dev Kit | \`0.4.0-rc.4\` |
| Test Kit | \`2.0.0-rc.14\` |

See [Release status](docs/en/RELEASE.md). Conformance PASS is evidence for Human review; it does not authorize merge, tag, or release.
