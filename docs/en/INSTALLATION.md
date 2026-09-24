# Installation

Tiếng Việt: [Cài đặt](../vi/INSTALLATION.md)

Clone the Kit repository, then run its installer while your shell is in the project where you will use BA Kit. Project scope uses the current working directory, so a project-local install stays with that project.

~~~powershell
git clone https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

Replace the example checkout and project paths with the paths on your machine.

## Supported targets

Use the corresponding PowerShell or shell wrapper under **tooling/**. These arguments work with **install**, **doctor**, and **uninstall**; keep the same arguments for all three operations.

| Target | Arguments |
|---|---|
| Codex project | **ba --agent codex --scope project** |
| Codex user | **ba --agent codex --scope user** |
| Claude Code project | **ba --agent claude-code --scope project** |
| Claude Code user | **ba --agent claude-code --scope user** |
| Generic directory | **ba --agent generic --target PATH** |

Examples from a target project in PowerShell:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope user
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent claude-code --scope project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent generic --target C:\path\to\agent\skills
~~~

Examples from a target project in Bash:

~~~bash
~/src/agent-skills/tooling/install.sh ba --agent codex --scope user
~/src/agent-skills/tooling/install.sh ba --agent claude-code --scope project
~/src/agent-skills/tooling/install.sh ba --agent generic --target /path/to/agent/skills
~~~

To run Doctor or uninstall, use the matching **doctor.ps1** / **doctor.sh** or **uninstall.ps1** / **uninstall.sh** wrapper with the same kit and target arguments. For example:

~~~powershell
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent claude-code --scope project
& 'C:\tools\agent-skills\tooling\uninstall.ps1' ba --agent generic --target C:\path\to\agent\skills
~~~

~~~bash
~/src/agent-skills/tooling/doctor.sh ba --agent claude-code --scope project
~/src/agent-skills/tooling/uninstall.sh ba --agent generic --target /path/to/agent/skills
~~~

Codex project skills go under **.agents/skills**; Claude Code project skills go under **.claude/skills**. User scope installs under the matching directory in your home folder. Project scope is useful when you want BA Kit available only for one project. Generic mode requires **--target**. That option can also override a native target for isolated checks.

Codex project installation, repeat installation, Doctor, safe uninstall, and project isolation have been structurally checked. Generic PowerShell/Bash installation and Claude Code structural installation have also been checked; Claude runtime acceptance was not run. See [Release Status](RELEASE.md).

## Doctor status

Doctor checks the installed required and optional skills, the kit manifest, the workflow-state and source-authority contracts, and the handoff contract.

| Status | Meaning |
|---|---|
| **READY** | Required skills and contracts pass, and optional skills are present. |
| **DEGRADED** | Required skills and contracts pass, but one or more optional skills are unavailable. |
| **FAIL** | A required skill is missing or invalid, or a required contract fails. |

**FAIL** returns exit code 1. **READY** and **DEGRADED** return exit code 0. Doctor does not run a BA session or prove runtime acceptance.

## Requirements and safety

- Python 3.8 or newer is required. PowerShell looks for **python** on PATH. Bash uses **python3**, or the executable named by the **PYTHON** environment variable.
- No Python packages, Skills Manager, agent profile, or global agent configuration are required.
- Composition comes from [kit.yaml](../../kits/ba/kit.yaml). Install preserves existing same-name skills and reports conflicts; it does not merge or overwrite them.
- Repeating install is safe. Uninstall removes unchanged BA-managed skills and preserves modified or shared skills.

See the [Quick Start](BA_KIT_QUICKSTART.md) to begin a BA session.
