# BA Kit Quick Start

BA Kit is an AI-assisted Business Analysis workflow. It helps a BA discover current-system behavior, find requirement gaps, record Human decisions, prepare Business Rules and an SRS, and create an Engineering Handoff after approval. It assists the BA; it does not replace BA ownership, customer communication, or Human approval.

BA Kit owns **WHAT** the system needs to do. It does not design APIs or databases, choose implementation owners, or write production code. See [Architecture](ARCHITECTURE.md) and [Workflow and Human Gates](BA_KIT_WORKFLOW.md).

## Install for one project

Clone the repository, then run the scripts from the project where you want BA Kit available. The project scope uses the current directory; replace these example paths with your actual checkout and project paths.

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

Project scope places skills in that project's **.agents/skills** directory. It is useful for isolating BA Kit from other projects. [Installation](INSTALLATION.md) covers Codex user scope, Claude Code, generic directories, and uninstall.

Doctor reports:

- **READY**: required and optional skills and package contracts pass.
- **DEGRADED**: required skills and contracts pass, but optional skills are unavailable.
- **FAIL**: a required skill is missing/invalid or a contract check fails.

## Start a BA review

Open the target project in your agent and write naturally:

~~~text
Review requirement này giúp tôi.
~~~

For brownfield work, you can be explicit:

~~~text
Hãy rà soát requirement này trên hệ thống hiện tại và chỉ ra các điểm còn thiếu hoặc chưa rõ.
~~~

You do not need to know skill names or invoke them. BA Kit routes the request, discovers the current system when it matters, separates evidence from decisions, and asks about material unknowns.

## What to expect

Depending on the request and Human decisions, BA work may produce a gap review, open questions, a decision record, approved Business Rules, a canonical SRS, or diagrams and document exports. The project-local **workflow-state.json** tracks the work. An Engineering Handoff is produced only after explicit Human approval of the BA baseline and resolution of blocking items.

**Tiếp tục** resumes the workflow. It never means approval. See the [Workflow](BA_KIT_WORKFLOW.md), [Usage Guide](BA_KIT_USAGE_GUIDE.md), [CR-001 example](../kits/ba/examples/CR-001/README.md), and [FAQ](BA_KIT_FAQ.md).

## Current status

BA Kit is an RC1 candidate. Packaged runtime acceptance is blocked by an isolated provider/runtime that returned no response; public distribution is blocked by unresolved licensing and provenance. See [Release Status](RELEASE.md) and [Provenance](PROVENANCE.md).
