# Getting Started

This page is for people who want to **use** the Agent-Assisted SDLC Toolkit without first learning its schemas or internal vocabulary.

## 1. Choose what you need

You do not need every Kit.

| Your situation | Start with |
|---|---|
| "I need to turn a requirement into an approved business baseline." | **BA Kit** |
| "I already have approved requirements and need engineering work." | **Dev Kit** |
| "I need Test Design / Testcases / automation / execution." | **Test Kit** |
| "This project is new or its current architecture/business context is undocumented." | **Project Foundation** |
| "I want the whole lifecycle." | Foundation when needed → BA → Dev → Test |

The full Kit catalog is [here](../../kits/README.md).

## 2. Prerequisites

Use an exact committed toolkit revision for installation.

| Requirement | Current public guidance |
|---|---|
| Git | Required |
| Python | **3.10+** for the documented BA/Test baseline; use 3.10+ for the simplest full-toolkit setup |
| OS | Windows and Linux workflows are supported |
| Codex | Primary verified end-to-end path |
| Claude Code | BA installation target where documented; do not assume every cross-Kit path is verified on Claude Code |
| Spec Kit | Required by the current integrated Dev/public-conformance path; exact release-gate version is documented in the conformance guide |
| XMind / Excel | Optional Test projections |

For capability-specific prerequisites, read [Installation](INSTALLATION.md).

## 3. Select an exact source revision

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git
cd agent-skills
git checkout "<approved-ref>"
git rev-parse HEAD
~~~

Keep the resolved SHA with your installation/review evidence.

## 4. Install only the Kit you need

### BA Kit

PowerShell:

~~~powershell
& 'C:\path\to\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\path\to\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

Linux/macOS-style shell:

~~~bash
/path/to/agent-skills/tooling/install.sh ba --agent codex --scope project
/path/to/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

### Test Kit

~~~powershell
& 'C:\path\to\agent-skills\tooling\install.ps1' test --agent codex --scope project
& 'C:\path\to\agent-skills\tooling\doctor.ps1' test --agent codex --scope project
~~~

### Dev Kit / shared runtime

~~~powershell
python -I C:\path\to\agent-skills\tooling\install_dev_kit.py --source-root C:\path\to\agent-skills --install-home C:\agent-runtime
~~~

Then use the installed Dev runtime/Doctor described in [Installation](INSTALLATION.md) and [Dev Kit README](../../kits/dev/README.md).

A Doctor result proves package/capability readiness only. It is not Human approval and not product verification.

## 5. Give the agent a bounded first task

These are orientation prompts, not special commands.

### BA

> Review this requirement in REVIEW mode. Identify ambiguity, missing business rules, and questions. Do not approve anything and stop before any Human Gate.

### Developer

> Start FEATURE_DELIVERY from this approved Engineering Handoff. Analyze repositories and technical impact. Do not invent missing WHAT; stop on UPSTREAM_GAP or any required Human technical gate.

### Tester

> Create Test Design from the approved authority inputs. Preserve BR/FR traceability and stop at the Human Design Gate.

The Kit workflow decides the valid next transition. A prompt never substitutes for required authority.

## 6. Brownfield or greenfield?

### Existing / brownfield project

Start with Project Foundation when the team does not have reliable system context. The recovery workflow records what is confirmed, inferred, current-system evidence, and unknown instead of pretending the existing code is the desired target.

Read [Project Foundation](PROJECT_FOUNDATION.md).

### New / greenfield project

Use Foundation when you need a reviewed target architecture/project context. Business behavior is still owned by BA/Human approval; Foundation does not approve requirements.

## 7. Understand the one rule that prevents most mistakes

Each stage owns a different question:

~~~text
BA          → WHAT
Engineering → WHERE / WHO OWNS / HOW
Test        → prove approved behavior
Human       → final semantic authority
~~~

If Dev discovers unclear WHAT, route upstream. If Test discovers a spec gap, classify and route it; do not silently invent expected behavior.

## 8. See one complete example

Read [Full Flow Example](FULL_FLOW_EXAMPLE.md). It shows both outcomes:

- clean initial PASS → VERIFIED;
- DEFECT → Dev Fix → READY_FOR_RETEST → retest → VERIFIED / REOPENED.

## Next

- [FAQ](FAQ.md)
- [Architecture](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [Release status](RELEASE.md)
