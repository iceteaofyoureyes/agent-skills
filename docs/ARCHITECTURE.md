# Architecture

Atomic skills are canonical at the repository root. `kits/ba/kit.yaml` is the single source for BA Kit composition. `ba-workflow/` routes work and enforces state and approval boundaries; atomic skills provide the detailed discovery, analysis, SRS, diagram, and document procedures.

## Responsibility flow

| Stage | Question | Status |
|---|---|---|
| BA Kit | **WHAT** does the system need to do? | RC1 candidate; runtime functional acceptance is blocked. |
| Engineering Impact | **WHERE** does the work belong, and **WHO** owns it? | Planned; not implemented. |
| Dev Kit + Spec Kit | **HOW** will the approved work be designed and built? | Planned; not implemented. |
| Test Kit + TEA | **HOW DO WE PROVE IT** works? | Planned; not implemented. |

The intended downstream flow is BA Handoff → Engineering Impact → Tech Lead Gate → Spec Kit → plan and implementation → Test Kit/TEA. Only BA Kit is implemented in this repository's Kit model today. Future stages must preserve the approved BA semantics while resolving technical decisions downstream.

~~~text
Requirement → BA Kit → Approved BA Baseline → Engineering Impact → Dev Kit + Spec Kit → Test Kit + TEA
~~~

The installer reads dependencies only from `kits/ba/kit.yaml`. Codex and Claude Code use their native Agent Skills directories; generic installs require an explicit directory. Skills Manager metadata is independent and optional. See [Installation](INSTALLATION.md), [Kit contract](KIT_CONTRACT.md), and [Provenance](PROVENANCE.md).
