# Dev Kit VNext — operator guide

Dev starts from an exact Engineering Handoff backed by an approved BA baseline. The [kit manifest](../../kits/dev/kit.yaml) and [package README](../../kits/dev/README.md) define executable inputs and versions.

## Install and check

Requires Python 3.10+ and Spec Kit v1.0.11 for normal and high-risk workflows. From the framework checkout:

~~~powershell
python -I tooling/install_dev_kit.py --source-root . --install-home <install-home>
~~~

Add <install-home>\bin to PATH, then run devkit doctor. On Windows the installer creates devkit.cmd and devkit.ps1; on Unix-like systems it creates devkit. Doctor reports package/capability readiness only. See [installation](INSTALLATION.md).

## Modes, inputs, and outputs

- FEATURE_DELIVERY implements behavior from the exact approved Engineering Handoff and current BA proof.
- TECHNICAL_MAINTENANCE is limited to evidenced nonbehavioral maintenance; it cannot authorize new business behavior.
- Inputs include the exact handoff, Foundation proof where applicable, project policy/topology, repository bases, and declared write scope.
- Outputs include Engineering Impact, Engineering Gaps, ED-* decisions, technical snapshot/approval when policy requires it, repository-scoped checks, and Dev Handoff V2 at READY_FOR_TEST.

Dev owns repository selection, component owners, technical design, implementation, review, and fresh checks. BA owns business WHAT. A required Human/Tech Lead gate binds the exact high-risk or material technical decision snapshot. Do not reuse approval after a material snapshot changes.

## Route interruptions

| State | Meaning | Safe next step |
|---|---|---|
| UPSTREAM_GAP | Approved business input is missing, inconsistent, or insufficient for the requested technical decision | Stop writes; route a precise gap to BA/owner; resume only with resolution evidence and a replacement/revalidated Handoff |
| NEEDS_REPLAN | Scope, risk, repository bases, or technical assumptions changed enough to invalidate the current plan/snapshot | Stop implementation; revise impact/plan and repeat any required exact approval |
| BLOCKED | A declared external dependency, access, environment, or capability prevents safe progress | Record blocker, owner, evidence, and resolution condition; do not claim READY_FOR_TEST |
| READY_FOR_TEST | Dev work, review, checks, and exact handoff are complete | Hand off to Test; this is not VERIFIED or merge approval |

## Forbidden inferences

- Do not turn an unresolved BA question into a technical choice.
- Do not treat Spec Kit state, generated artifacts, or Doctor READY as business or Human approval.
- Do not write outside bound repositories and approved scope.
- Do not call Dev output VERIFIED or convert command failure directly to a DEFECT.
- Do not use a Dev fix as Tester retest evidence.

## Detailed guidance

Vietnamese primary pages cover [capabilities](../vi/DEV_KIT_CAPABILITIES.md), [workflow](../vi/DEV_KIT_WORKFLOW.md), [routing](../vi/DEV_KIT_ROUTING.md), [usage](../vi/DEV_KIT_USAGE_GUIDE.md), and [review/verification](../vi/DEV_KIT_REVIEW_AND_VERIFICATION.md). Current machine truth is in the [Dev manifest](../../kits/dev/kit.yaml), [schemas](../../kits/dev/schemas/), and [acceptance contract](../../kits/dev/acceptance.yaml).
