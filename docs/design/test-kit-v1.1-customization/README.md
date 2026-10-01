# Test Kit V1.1 — Project Customization & Policy Layer

Status: **DESIGN OPEN**

V1.1 is a thin extension on top of the Human-accepted Test Kit V1. It adds a project-owned customization surface for testers without changing the V1 canonical Test Design schema, canonical Testcase schema, XMind semantics, or the meaning of Human approval.

## Goal

Allow a project/test team to define version-controlled testing conventions that agents must carry through Test Design and testcase generation, for example:

- testcase naming and language;
- atomicity/self-contained case conventions;
- preferred coverage techniques;
- project-specific priority conventions;
- data-safety constraints;
- required negative/boundary considerations;
- test documentation conventions;
- project Excel template selection.

The policy layer is **testing guidance**, not business authority.

## Authority model

Precedence is not "last rule wins". Each source owns a different semantic domain:

1. **Approved BA Baseline** — business behavior and unresolved UNKNOWNs.
2. **Approved Canonical Test Design** — coverage authority after Design Gate.
3. **Approved Execution/Interface Oracle** — approved setup/action/observation details.
4. **Project Test Policy** — testing/generation conventions only.
5. **XMind/Excel projection configuration** — presentation only.

Project policy MUST NOT:

- answer a BA UNKNOWN;
- override or invent FR/BR behavior;
- add pass/fail expectations absent from approved authority;
- replace an execution oracle;
- change canonical schemas;
- grant or imply Human approval.

Existing V1 validators and authority checks remain authoritative when policy-guided output conflicts with BA/Design/execution sources.

## Proposed project surface

Project-owned files:

```text
<project-root>/
└── .test-kit/
    ├── project.yaml
    ├── rules/
    │   ├── common.md
    │   ├── test-design.md
    │   └── testcases.md
    └── templates/
        └── testcases.xlsx       # optional
```

Example `.test-kit/project.yaml`:

```yaml
schema_version: 1

profile:
  id: portal-testing
  revision: "1"

rules:
  common:
    - rules/common.md
  test_design:
    - rules/test-design.md
  testcases:
    - rules/testcases.md

templates:
  excel:
    path: templates/testcases.xlsx
```

Paths resolve relative to the project-owned `.test-kit/` directory.

## Upstream TEA customization

The pinned upstream TEA skill already supports project customization through:

```text
_bmad/custom/bmad-testarch-test-design.toml
_bmad/custom/bmad-testarch-test-design.user.toml
```

with `workflow.persistent_facts`, `activation_steps_prepend`, `activation_steps_append`, and file references such as:

```toml
[workflow]
persistent_facts = [
  "file:{project-root}/.test-kit/rules/common.md",
  "file:{project-root}/.test-kit/rules/test-design.md"
]
```

V1.1 will **reuse** this upstream extension point rather than fork TEA.

Production Test Kit will treat project/team customization as reproducible input. Machine-local `bmad-testarch-test-design.user.toml` is not accepted silently for production runs. Initial V1.1 policy is to fail closed when that personal override is present; TEST_ONLY experiments may opt in explicitly.

## Testcase customization

The pinned `create-test-cases` upstream skill has no equivalent project-policy contract in Test Kit V1.

V1.1 will inject the resolved project policy into the Katalon/manual-testcase invocation as a clearly subordinate **TESTING POLICY** input, while retaining:

- Approved Design as coverage oracle;
- BA baseline as business oracle;
- execution-oracle refs as execution authority;
- current V1 normalization and validators.

Policy files used by the invocation are copied into the run and SHA-256 recorded.

## Policy snapshot and gates

Every production run resolves an immutable policy snapshot.

Initial contract:

```text
TEST_KIT_PROJECT_POLICY_V1
= profile id/revision
+ common rule file paths + SHA-256
+ stage-specific rule file paths + SHA-256
```

The policy digest excludes presentation-only template bytes.

Design path:

```text
Approved BA
+ Design Policy Snapshot
→ TEA
→ Canonical Test Design
→ Human Design Gate
```

Case path:

```text
Approved BA
+ Approved Design
+ Case Policy Snapshot
+ Approved Execution Oracle(s)
→ create-test-cases
→ Canonical Testcases
→ Human Case Gate
```

A policy snapshot used to create/review an artifact must be persisted in run evidence. A stale policy snapshot cannot be silently reused at a gate.

The implementation should preserve the existing receipt object shape by binding policy identity through existing `input_refs: [{id, revision, sha256}]` rather than adding ad-hoc approval fields.

## Template policy

Excel remains:

```text
HUMAN_SUPPLIED_APPROVED_TEMPLATE
→ PROJECT_TEMPLATE
→ DEFAULT_TEMPLATE
```

V1.1 wires `.test-kit/project.yaml -> templates.excel.path` into `PROJECT_TEMPLATE`.

XMind remains unchanged in V1.1:

- pinned Human-facing profile;
- no Human/project XMind template;
- no reverse import.

## Non-goals

V1.1 does not add:

- test execution;
- Playwright/API automation generation;
- automated evidence;
- flaky management;
- failure triage;
- defect automation;
- new canonical Design/Testcase fields;
- XMind templates;
- personal untracked production policy overrides.

Those remain outside this lane or belong to Automation Test V2.

## Acceptance target

V1.1 is ready for Human acceptance only when:

- a project can bootstrap or author a policy profile;
- Design invocation consumes and records the correct policy snapshot;
- testcase invocation consumes and records the correct policy snapshot;
- personal/untracked override behavior is explicit and fail-closed in production;
- policy cannot override BA UNKNOWN or bypass V1 validators;
- policy changes are detected as stale where relevant;
- Excel project-template resolution works from the profile;
- Doctor reports missing, malformed, drifted, or unsafe customization;
- TEST_ONLY fixtures prove behavior without creating production approval;
- full existing Test Kit V1 regression remains green;
- Vietnamese operator docs explain customization with a real example.

Automation Test V2 MUST NOT start as part of this lane.
