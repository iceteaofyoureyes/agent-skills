# Installation

Select a committed ref from [Release status](RELEASE.md). For this Internal RC candidate, use branch docs/full-documentation-hardening-rc-gate; the main branch remains at the last merged candidate until Human integration review. Run the installer from that selected checkout while your shell is in the target project.

~~~powershell
git clone --branch docs/full-documentation-hardening-rc-gate https://github.com/iceteaofyoureyes/agent-skills.git C:\tools\agent-skills
Set-Location C:\path\to\your-project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope project
& 'C:\tools\agent-skills\tooling\doctor.ps1' ba --agent codex --scope project
~~~

~~~bash
git clone --branch docs/full-documentation-hardening-rc-gate https://github.com/iceteaofyoureyes/agent-skills.git ~/src/agent-skills
cd /path/to/your-project
~/src/agent-skills/tooling/install.sh ba --agent codex --scope project
~/src/agent-skills/tooling/doctor.sh ba --agent codex --scope project
~~~

## Supported targets

| Target | Arguments |
|---|---|
| Codex project | **ba --agent codex --scope project** |
| Codex user | **ba --agent codex --scope user** |
| Claude Code project | **ba --agent claude-code --scope project** |
| Claude Code user | **ba --agent claude-code --scope user** |
| Generic directory | **ba --agent generic --target PATH** |

PowerShell:

~~~powershell
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent codex --scope user
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent claude-code --scope project
& 'C:\tools\agent-skills\tooling\install.ps1' ba --agent generic --target C:\path\to\agent\skills
~~~

Bash:

~~~bash
~/src/agent-skills/tooling/install.sh ba --agent codex --scope user
~/src/agent-skills/tooling/install.sh ba --agent claude-code --scope project
~/src/agent-skills/tooling/install.sh ba --agent generic --target /path/to/agent/skills
~~~

Doctor and uninstall use the same kit/target arguments with the matching **doctor.ps1/.sh** and **uninstall.ps1/.sh** wrappers.

## Install locations

- Codex project: **.agents/skills**
- Claude Code project: **.claude/skills**
- user scope: matching agent-native skills directory under home
- generic: explicit **--target** required

The installer preserves existing same-name skills rather than merging/overwriting them. Reinstall is idempotent. Uninstall removes BA-managed skills only when their contents remain unchanged.

## Project Foundation opt-in

Project Foundation is a standalone Shared SDLC capability, not a fourth Kit.
Install the Shared runtime and skill into an explicit install home:

~~~powershell
python C:\tools\agent-skills\tooling\install_dev_kit.py --source-root C:\tools\agent-skills --install-home C:\agent-runtime
python C:\agent-runtime\runtime\v1\project-foundation\scripts\project_foundation.py inventory --project-root C:\path\to\your-project
~~~

To include the skill in a separate Codex profile, create a fresh profile with
`python tooling/prepare_agent_profile.py --destination <fresh-profile> --foundation`.
Both the profile and Dev runtime carry the deterministic Shared payload. See the
[Project Foundation workflow](../project-foundation.md) for modes, producer
commands and the Human Gate. The CLI stops at review; approval remains with the
trusted host.

## What does Doctor check?

Doctor checks:

- manifest/composition;
- required/optional skill directories;
- Agent Skills frontmatter;
- workflow-state/source-authority contracts;
- Engineering Handoff contract;
- installed `ba_vnext.py`, `ba_contracts.py`, validators and VNext templates;
- isolated Shared SDLC payload imports from the installed skill folder;
- canonical SRS contract and required atomic BA skills.

| Status | Meaning |
|---|---|
| **READY** | Required skills/contracts pass and optional skills are present |
| **DEGRADED** | Required skills/contracts pass but optional skills are missing |
| **FAIL** | Required skill/contract failure |

FAIL exits 1; READY/DEGRADED exit 0.

### Important: READY does not mean every external runtime tool is installed

Doctor is **not an external dependency manager** and does not prove Human approval, approved baseline, feature readiness, or full runtime acceptance. READY confirms package capability closure only.

An installation may be READY while lacking tools needed for Word export, Draw.io export, or browser rendering.

For maintainers, the BA installed acceptance runs the VNext lifecycle and exact Handoff revalidation with imports isolated from the source checkout. This is package evidence, not a Human approval gate; see Release status.

## Runtime prerequisites by capability

### Core BA workflow

Requires:

- Python 3.8+ for installer/validators;
- an agent runtime with access to the project/artifacts being reviewed.

The installer does not require Skills Manager, an agent profile, or global agent configuration changes.

### DOCX / Word templates

**document-docx** selects tooling per task. Common operations may require:

- **python-docx** for structural create/edit;
- **docxtpl** for placeholder-based Word templates;
- LibreOffice or Microsoft Word for rendering/PDF/fidelity checks depending on the workflow.

BA Kit installer does **not pip-install** these packages.

Before promising a DOCX feature, the agent must check tool/library versions as required by document-docx.

See [SRS and DOCX](SRS_DOCX_GUIDE.md).

### Draw.io

Many core .drawio authoring/validation paths require only Python.

Native PNG/SVG/PDF export requires an available **draw.io/diagrams.net desktop CLI**.

Graphviz is optional for some auto-layout workflows.

If the export binary is unavailable, the agent may still create/edit the .drawio source where supported, but must report the export limitation.

See [Draw.io, visual input, and prototypes](DIAGRAMS_PROTOTYPES.md).

### Prototype / browser checks — optional

Optional browser workflows may require:

- Node.js/npm/npx;
- Playwright CLI/browser runtime;
- project frontend dependencies.

BA Kit installer does not automatically install those dependencies.

### Figma

BA Kit **does not bundle a Figma connector**.

Direct Figma access requires an external connector/integration plus Human authorization. Otherwise use screenshot/PDF/image/HTML/local exports.

## Post-install checks

After Doctor READY/DEGRADED, test the capability you actually intend to use.

### Core BA

~~~text
Open the agent in the project and ask:
Review this requirement. REVIEW only.
~~~

### DOCX

Before template output, check the Python package/tool requirements from document-docx.

### Draw.io

When native export is required:

~~~text
drawio --version
~~~

or use drawio-skill's relevant doctor/probe workflow.

### Prototype

Check project frontend dependencies plus npx/Playwright before requesting browser rendering.

## Existing package evidence

Structural evidence exists for:

- Codex project install;
- idempotent reinstall;
- Doctor;
- safe uninstall;
- project isolation;
- generic PowerShell/Bash;
- Claude Code structural install.

This is package evidence, not full runtime BA acceptance. See [Release status](RELEASE.md).

## See also

- [Quick Start](BA_KIT_QUICKSTART.md)
- [Capabilities](BA_KIT_CAPABILITIES.md)
- [SRS/DOCX](SRS_DOCX_GUIDE.md)
- [Draw.io/Visual/Prototype](DIAGRAMS_PROTOTYPES.md)

---

Tiếng Việt: [Cài đặt](../vi/INSTALLATION.md)

## Suite Kit map and Windows checkout policy

The suite installs by capability; there is no single installer that installs all Kits.

| Capability | Install path | Verify |
|---|---|---|
| BA | tooling/install.ps1 ba --agent codex --scope project (or install.sh) | tooling/doctor.ps1 ba --agent codex --scope project |
| Dev VNext and Shared runtime | python -I tooling/install_dev_kit.py --source-root <checkout> --install-home <install-home> | Add <install-home>/bin to PATH; run devkit doctor |
| Test Manual + Automation + Execution | tooling/install.ps1 test --agent codex --scope project (or install.sh) | tooling/doctor.ps1 test --agent codex --scope project |
| Project Foundation | Shared runtime installed above; follow the [Foundation guide](PROJECT_FOUNDATION.md) | Run Foundation doctor through the installed workflow/host |

BA and Test require Python 3.10+. Dev installer uses the selected Python to create an isolated runtime. Use the exact committed framework checkout selected for the work.

Normal supported Windows checkouts use repository .gitattributes to preserve package-source bytes. core.autocrlf=false is not a required operator setting. Do not edit package authority hashes.

## Upgrade and version verification

Read the [suite manifest](../../tooling/sdlc-suite.json) and individual Kit manifests before upgrading. Record the source commit with git rev-parse HEAD, rerun that Kit installer from the selected revision, then run its Doctor. Reinstall preserves modified managed files and reports drift; review local edits before restoring a managed file. For safe mismatch recovery, see [Troubleshooting](TROUBLESHOOTING.md).
