# Agent Skills and Kits

This repository contains reusable agent skills and role-based Kits. A Kit combines a workflow entry point with the skills and tools for one stage of product work; each underlying skill remains canonical at the repository root.

## Kits

| Kit | Status | Purpose |
|---|---|---|
| **BA Kit** | Available as an RC1 candidate; functional acceptance is blocked | Helps a Business Analyst clarify **what** a system needs to do and prepare a human-approved BA baseline. |
| **Dev Kit** | Planned | Downstream engineering work after Engineering Impact. |
| **Test Kit** | Planned | Downstream verification work with TEA. |

BA Kit is not yet accepted or publicly released. See [Release Status](docs/RELEASE.md) and [Provenance](docs/PROVENANCE.md). Dev Kit and Test Kit are not implemented.

## Install BA Kit

From the project where you will use BA Kit, call the scripts from your cloned agent-skills checkout. Replace the example path with its actual location:

```powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
```

```bash
/path/to/agent-skills/tooling/install.sh ba --agent codex --scope project
/path/to/agent-skills/tooling/doctor.sh ba --agent codex --scope project
```

See [Installation](docs/INSTALLATION.md) for user scope, Claude Code, generic targets, and uninstall commands.

## New to BA Kit?

1. [Quick Start](docs/BA_KIT_QUICKSTART.md)
2. [Workflow and Human Gates](docs/BA_KIT_WORKFLOW.md)
3. [CR-001 example](kits/ba/examples/CR-001/README.md)
4. [Installation](docs/INSTALLATION.md)
5. [FAQ](docs/BA_KIT_FAQ.md)

## More

- [Usage Guide](docs/BA_KIT_USAGE_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Kit contract](docs/KIT_CONTRACT.md)
- [Release Status](docs/RELEASE.md)
- [Provenance and licensing evidence](docs/PROVENANCE.md)
