# Troubleshooting and operator recovery

Before recovery, record the candidate revision, status, and exact error. Do not edit manifests or hashes to make a Doctor pass. Escalate only when evidence shows Human authority, policy, or package provenance cannot be validated.

## Doctor

| Symptom | Meaning | Safe diagnosis and recovery | Stop when |
|---|---|---|---|
| Kit Doctor READY | Required package/capabilities validate | Continue the Kit workflow; see [readiness states](READINESS_STATES.md) | Never treat READY as approval |
| Kit Doctor DEGRADED | An optional projection such as XMind/Excel is missing | If needed, install from the pinned lock/requirements and rerun Doctor; otherwise use the core path | The report names required integrity/capability failure |
| Kit Doctor FAIL | Manifest, authority, managed payload, or required dependency failed | Record version, Doctor output, source SHA; select the intended revision, reinstall from it, rerun Doctor | SHA/authority mismatch or unexplained install record |
| Suite Doctor FAIL | Component tuple, contract, runtime, router, package authority, or test configuration is incompatible | Read each failed check; align candidate with manifests, repair project setup, rerun from clean checkout | Required capability still fails or machine contracts conflict |

Run Suite Doctor from a framework checkout:
~~~
python -m tooling.sdlc_suite doctor --root <framework-checkout> --spec-kit-cli <Spec-Kit-v1.0.11-CLI> --docs-project <docs-project> --app-project <app-project> --automation-project <automation-project>
~~~
A Doctor reports package/capability readiness, not business or product verification.

## Install and upgrade recovery

1. Record the source SHA with git rev-parse HEAD and working changes with git status --short.
2. Compare the installed Kit version with the [suite and Kit manifests](../../tooling/sdlc-suite.json); use one committed source revision for installation and Doctor.
3. Rerun the same Kit installer, scope, and target to restore missing files. Reinstall is idempotent and preserves user-edited managed files.
4. For MODIFIED_MANAGED_FILE, review the diff/hash and decide to keep the edit outside the managed path or restore exact candidate bytes; rerun Doctor.
5. For MISSING_MANAGED_FILE, reinstall from the same candidate and confirm the path and Doctor result.
6. For authority/payload mismatch, stop. Use a clean checkout of the exact candidate. Only maintainers regenerate authority with canonical tooling; operators never edit hashes. See the [packaging contract](../../tooling/PACKAGING.md) for canonical regeneration commands.
7. Choose a fresh install only after preserving project-owned configuration and managed edits that must survive. Kit uninstall removes only unchanged files owned by that Kit.

Supported Windows checkouts use repository .gitattributes under normal Git settings. core.autocrlf=false is not a prerequisite. Do not normalize package bytes or hashes by hand.

### Version and source drift

Compare installed versions to the [suite manifest](../../tooling/sdlc-suite.json), [BA](../../kits/ba/kit.yaml), [Dev](../../kits/dev/kit.yaml), and [Test](../../kits/test/kit.yaml). A clean candidate has no uncommitted changes. Any SHA change after conformance makes that report stale; rerun on the new SHA.

### Authority or payload mismatch

Keep package manifests and authority files unchanged. Record Doctor output, source SHA, and named file. Check for a dirty source checkout, wrong revision, missing file, or modified installed managed file. Recover by selecting the intended committed package source and reinstalling. Never copy authority from another install or regenerate a hash to conceal drift.

### Modified or missing managed files

Back up and review local edits first. Reinstall preserves managed edits; keep intended changes under a project-owned path and restore the managed asset from the selected candidate when needed. For a missing file, reinstall the same candidate and verify its path and Doctor result. Do not delete the whole install directory without identifying project-owned files.

## Workflow recovery

| Symptom | Meaning | Recovery / owner | Do not continue when |
|---|---|---|---|
| Unresolved Foundation gap | Context lacks evidence or owner decision | Keep UNKNOWN/PROPOSED; route to BA, Engineering, or Test owner; Human reviews exact snapshot | Do not claim PROJECT_FOUNDATION_READY with a blocker |
| Unresolved BA WHAT | Target behavior is not decided | Ask the named question, record the Human answer, update BR/SRS revision, request new approval | Do not hand off as approved |
| Stale BA receipt | Snapshot/revision/hash changed | Create a new exact candidate and obtain a new trusted-host receipt | Do not reuse the old receipt |
| Dev UPSTREAM_GAP | Handoff/WHAT is missing or conflicting | Stop writes; route gap to BA/owner; resume only with resolution and revalidated Handoff | Do not decide business behavior in Dev |
| Dev NEEDS_REPLAN | Scope, risk, repo base, or assumptions changed | Rebuild impact/plan/snapshot; repeat any required technical Human gate | Do not proceed on a stale plan/approval |
| Dev BLOCKED | Capability, access, or dependency prevents safe progress | Record blocker, owner, evidence, and exit condition; resolve and resume | Do not publish READY_FOR_TEST |
| Automation BLOCKED | Required testcase/dependency/repository is unavailable | Revise Plan and dependency; verify repository against project policy/topology | Do not publish EXECUTION_READY |
| Wrong automation repository | Selected repository conflicts with policy/topology | Stop writes; resolve project root/topology and create a Plan for the correct repository | Do not write automation into an app repository |
| Stale execution revision | App/automation/environment revision differs from Execution Manifest | Capture current revisions and create a new manifest/evidence from current EXECUTION_READY | Do not apply old results to new source |
| Command failed | Command evidence only | Tester observes against the approved oracle and classifies with authority as DEFECT, TEST_ISSUE, ENVIRONMENT_ISSUE, or another correct class | Never create Finding/DEFECT automatically from exit code |
| Retest failed | Approved oracle still fails | Tester creates REOPENED with the same defect identity and routes to Dev | Do not self-issue VERIFIED |
| Fresh-clone conformance FAIL | Required gate failed on candidate clone | Read the report/tier, fix source, commit a new candidate, rerun at that SHA | Do not reuse old evidence or relabel required failure optional |
| Spec Kit version mismatch | Runtime tool differs from contract | Select and verify Spec Kit v1.0.11, then rerun | Do not run suite gate with another version |

### Optional degradation and conformance

Kit Doctor DEGRADED describes an optional Kit capability. CORE_READY_OPTIONAL_PROJECTIONS_UNAVAILABLE means Test core is usable while an optional projection is absent. Conformance OPTIONAL_DEGRADED is a projection setup field. All three are separate from final suite PASS/FAIL; see [Readiness states](READINESS_STATES.md). Only policy-allowed optional projections may degrade; required package/integrity failure always blocks.

## Escalation

Ask a Human for semantic decisions, approval receipts, Project Policy authority, required technical gates, risk acceptance, or release decisions. Escalate to a maintainer when an exact clean candidate still fails package/integrity/contract checks after recovery from the correct version. The normal cases above have direct recovery paths.
