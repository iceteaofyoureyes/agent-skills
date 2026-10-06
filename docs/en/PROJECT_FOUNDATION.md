# Project Foundation operator guide

Project Foundation is a shared SDLC workflow for recovering, bootstrapping, and refreshing project context. It is not a fourth role Kit and does not replace BA, Engineering, Test, or Human authority.

## Select a mode and profile

| Mode | Use when | Evidence categories |
|---|---|---|
| GREENFIELD_BOOTSTRAP | No current system exists; capture intent and target constraints | APPROVED_TARGET, PROPOSED, DEFERRED, UNKNOWN |
| BROWNFIELD_RECOVERY | Reconstruct current reality from repositories and existing documents | CURRENT_SYSTEM, CONFIRMED, INFERRED, UNKNOWN |
| FOUNDATION_REFRESH | Reassess changes against an exact approved Foundation manifest | Compare manifest/revision, route impact, retain gaps |

Profiles MINIMAL, STANDARD, and EXTENDED set evidence depth. A wider profile does not imply Human approval. The architecture basis uses arc42 Standard, ISO 42010 concepts, C4, and ADRs. C4 and arc42 views are derived outputs.

## Ownership and lifecycle

BA owns product/domain/glossary. Engineering owns architecture/runtime/deployment/ADRs. Test owns testing/automation/quality. Producers contribute evidence within their ownership; Shared workflow binds exact references into a review package.

~~~
ANALYSIS → REVIEW_REQUIRED → ACCEPTED_BASELINE / APPROVED_BASELINE → PROJECT_FOUNDATION_READY
~~~

Keep UNKNOWN, PROPOSED, DEFERRED, and conflicts explicit. CURRENT_SYSTEM records present behavior; it does not establish the target. A trusted Human reviews the exact snapshot through the host. The CLI does not issue receipts or approve. PROJECT_FOUNDATION_READY means Foundation readiness under policy only.

## Start

Prerequisites: the project has .sdlc/topology.json and .sdlc/project-policy.yml under the Shared v1 contract, and the Foundation/Shared runtime is installed. Use the [Installation guide](INSTALLATION.md), the detailed [Project Foundation workflow core](../project-foundation.md), and the [project-foundation skill](../../project-foundation/SKILL.md).

~~~
python <skill>/scripts/project_foundation.py inventory --project-root <project>
python <skill>/scripts/project_foundation.py start --project-root <project> --run-id recovery-1 --mode BROWNFIELD_RECOVERY
python <skill>/scripts/project_foundation.py brownfield --project-root <project> --run-id recovery-1 --input analysis.json
python <skill>/scripts/project_foundation.py greenfield --project-root <project> --run-id bootstrap-1 --input analysis.json
python <skill>/scripts/project_foundation.py refresh --project-root <project> --run-id refresh-1 --revision R2 --input refresh.json
python <skill>/scripts/project_foundation.py prepare --project-root <project> --run-id recovery-1
python <skill>/scripts/project_foundation.py doctor --project-root <project> --run-id recovery-1
~~~

Analysis and prepare produce evidence and a review package. Do not continue as if the Human approved it. Doctor must authenticate the snapshot through a trusted host; if the authenticator is absent, stop and use the host integration.

After PROJECT_FOUNDATION_READY, route context to BA for WHAT, Engineering/Dev for HOW, or Test for testing. Each role still owns separate gates and approvals.
