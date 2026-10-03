# Phase 2 — Wave 2 Implementation Spec
## Shared SDLC Core Contract Completion

**Status:** READY_FOR_AGENT_EXECUTION  
**Required model:** SOL High  
**Repository:** `iceteaofyoureyes/agent-skills`  
**Base branch:** `refactor/shared-sdlc-core-v1-wave1`  
**Base commit:** `a83e71274fba9189c130cc7152d2e640a7e98df5`  
**Suggested branch:** `refactor/shared-sdlc-core-v1-wave2`

> **Temporary bootstrap artifact.** This file is intentionally committed to the Wave 1 branch only so the implementation agent can fetch and read the exact approved scope. The behavioral implementation baseline remains `a83e71274fba9189c130cc7152d2e640a7e98df5`. Create Wave 2 from the latest remote Wave 1 branch (which includes this bootstrap file), then DELETE this file from the Wave 2 branch before the final implementation commit/report. The final Wave 2 tree must not contain this file.

---

# 1. Goal

Complete the Shared SDLC Core contract surface required before Project Foundation skills are implemented.

Wave 2 must add generic contracts for:

1. Project topology.
2. Shared Project Policy.
3. Project Foundation profile/manifest.
4. Readiness normalization/compatibility.
5. Generic promotion primitives.
6. Removal of the Shared Core -> Test Kit dependency inversion.

This wave defines contracts and validators only.

It does NOT implement brownfield/greenfield discovery skills yet.

---

# 2. Normative architecture

Approved precedence:

```text
Human-approved decisions
    >
Shared SDLC invariants
    >
Project Policy
    >
Kit / atomic skill instructions
    >
Runtime defaults
```

Shared Core MUST remain project/domain agnostic.

Forbidden hard-coding:

- Digital Wedding.
- PetClinic.
- Appointment.
- CR-DWC-*.
- specific local machine paths.
- specific harness/model names as semantic roles.

---

# 3. Wave 1 acceptance baseline

Wave 1 at:

```text
a83e71274fba9189c130cc7152d2e640a7e98df5
```

is the behavioral baseline.

Do not regress:

- BA approval/handoff semantics.
- FR/BR vs BAREF coverage semantics.
- Delivery Manifest V2.
- UX approval receipt behavior.
- runtime path safety.
- Human gate persistence/recovery.
- execution/finding/defect/retest lifecycle.
- old import compatibility.

---

# 4. Required Shared Core modules

Add logical ownership under `shared/sdlc/` for:

```text
topology/
policy/
foundation/
```

Existing areas remain:

```text
authority/
artifacts/
approvals/
provenance/
promotion/
readiness/
findings/
compatibility/
```

Exact filenames may follow repository conventions, but responsibilities must remain explicit.

---

# 5. Project Topology Contract

Create a generic machine-readable topology contract.

Minimum semantic model:

```yaml
schema_version: 1

project:
  id: example-project

repositories:
  - id: project-docs
    path: example-docs
    repository: owner/example-docs
    role: project_documentation_authority

  - id: web-application
    path: example-app
    repository: owner/example-app
    role: application_implementation

  - id: automation
    path: example-automation
    repository: owner/example-automation
    role: project_test_automation
```

Requirements:

- repository IDs unique;
- local paths unique and portable;
- repository names valid `owner/name`;
- no absolute/traversal paths;
- roles are semantic strings, not hard-coded to Digital Wedding;
- contract must support additional implementation/service repositories;
- topology is data, not duplicated Python/PowerShell constants.

The validator must fail closed on malformed or ambiguous topology.

Do not modify Digital Wedding workspace in this wave.

---

# 6. Shared Project Policy Contract

Create a generic project policy schema/reader/validator.

Canonical conceptual location:

```text
.sdlc/project-policy.yml
```

Minimum semantic areas:

```yaml
schema_version: 1

project:
  language: vi

foundation:
  profile: arc42-standard-v1

authority:
  product: ...
  domain: ...
  architecture: ...
  testing: ...
  features: ...

workflow:
  feature_root: ...
  branch_convention: ...

testing:
  automation_repository_role: project_test_automation

artifacts:
  optional: ...
```

Important:

- exact physical paths are project-owned data;
- Project Policy is non-authoritative with respect to Human-approved semantics;
- policy MUST NOT be able to weaken Shared Core invariants;
- policy MUST NOT invent business behavior;
- unknown fields should fail closed unless explicitly namespaced/extensions are designed and tested;
- credentials/secrets are forbidden;
- portable relative paths only where paths are accepted.

Existing `.test-kit` project testing policy remains valid as a subordinate Test-specific compatibility layer.

Do NOT delete or replace it in Wave 2.

---

# 7. Project Foundation Contract

Create:

```text
PROJECT_FOUNDATION_PROFILE_ARC42_V1
```

The contract must represent all 12 arc42 semantic sections:

```text
01 Introduction & Goals
02 Constraints
03 Context & Scope
04 Solution Strategy
05 Building Block View
06 Runtime View
07 Deployment View
08 Crosscutting Concepts
09 Architecture Decisions
10 Quality Requirements
11 Risks & Technical Debt
12 Glossary
```

Do NOT require twelve physical Markdown files.

Foundation manifest must be machine-readable.

Minimum concept:

```yaml
schema_version: 1

profile:
  id: arc42-standard-v1

mode: BROWNFIELD_RECOVERY

sections:
  introduction_goals:
    status: PARTIAL
    owner: BA

  context_scope:
    status: COMPLETE
    owner: ENGINEERING

  ...
```

Supported modes:

```text
GREENFIELD_BOOTSTRAP
BROWNFIELD_RECOVERY
FOUNDATION_REFRESH
```

Supported section statuses should cover at least:

```text
COMPLETE
PARTIAL
UNKNOWN
NOT_APPLICABLE
DEFERRED
```

Evidence semantics:

### Brownfield

```text
CURRENT_SYSTEM
CONFIRMED
INFERRED
UNKNOWN
```

### Greenfield

```text
APPROVED_TARGET
PROPOSED
DEFERRED
UNKNOWN
```

Do not allow a Brownfield `CURRENT_SYSTEM` observation to become an `APPROVED_TARGET` without an explicit decision/approval reference.

Do not fabricate historical ADRs.

---

# 8. Foundation readiness

Introduce a pure validator for:

```text
PROJECT_FOUNDATION_READY
```

It must NOT mean “all sections COMPLETE”.

Readiness should fail only when:

- required profile/manifest structure is invalid;
- required entry points are missing;
- a critical unresolved blocker exists;
- authority ownership is missing/ambiguous;
- an invalid evidence/status transition is claimed;
- references/hashes required by the manifest fail validation.

PARTIAL/UNKNOWN may remain when explicitly allowed and non-blocking.

The exact minimal/standard/extended profile rules should be represented as data/contracts, not scattered conditionals.

Digital Wedding will later use `STANDARD@, but this wave must not mention it.

---

# 9. Readiness compatibility

The Shared Core vocabulary already includes:

```text
PACKAGE_READY
PROJECT_CONFIG_READY
PROJECT_FOUNDATION_READY
CAPABILITY_READY
FEATURE_READY
READY_FOR_TEST
EXECUTION_READY
READY_FOR_RETEST
VERIFIED
READY_TO_MERGE
```

Wave 2 must:

- document normative meaning;
- add compatibility mapping for current Doctor `READY/DEGRADED/FAIL` where appropriate;
- NOT globally rename current Doctor outputs yet;
- avoid conflating package readiness with Human approval or feature readiness.

Add regression tests ensuring package `READY` cannot be interpreted as business approval.

---

# 10. Promotion dependency inversion — MUST FIX

Current Wave 1 temporary debt:

```text
shared/sdlc/promotion/testware_promotion.py
    imports
tooling.lib.test_kit_v1
tooling.lib.test_kit_v1_cases
```

This is acceptable only as Wave 1 compatibility debt.

Wave 2 must eliminate the architectural dependency:

```text
Shared Core
    -> Test Kit runtime
```

Target:

```text
Shared Core
    owns generic promotion primitives/contracts

Test Kit
    owns Test Design/Testcase-specific gate validation
    and calls generic promotion primitives
```

Possible generic Shared Core responsibilities:

- immutable exact-byte promotion;
- destination safety;
- promotion record structure;
- source artifact identity/hash binding;
- approval receipt reference binding;
- no overwrite of different approved snapshot.

Test-specific responsibilities remain outside Shared Core:

- loading Test Design/Testcase snapshots;
- TEA/Katalon-specific behavior;
- validating Test Kit-specific receipt structures;
- Test workflow state names specific to the Kit.

Historical import:

```text
tooling.lib.testware_promotion
```

must remain compatible.

Do not break installed Test Kit behavior.

---

# 11. Promotion architecture test

Add a dependency-direction test ensuring generic Shared Core modules do not import:

```text
tooling.lib.test_kit_v1
tooling.lib.test_kit_v1_cases
kits.test...
```

The Test-specific compatibility adapter may import both Shared Core and Test Kit.

Shared Core itself must not.

---

# 12. Schemas and versioning

Add explicit schema files or equivalent authoritative schema definitions for:

- project topology v1;
- project policy v1;
- foundation manifest v1.

Requirements:

- `schema_version` explicit;
- fail closed on unsupported major/current versions;
- migrations are not required yet, but code organization must leave a clear migration boundary;
- no silent coercion of unknown future versions.

Do not introduce framework stable version `1.0.0` yet.

---

# 13. No discovery/generation in Wave 2

Do NOT implement:

- repository scanning;
- codebase archaeology;
- arc42 Markdown generation;
- C4 generation;
- ADR generation;
- domain discovery;
- Foundation bootstrap commands.

Those belong to Phase 3.

Wave 2 is contract/schema/validation only.

---

# 14. Tests

Before change:

Run Wave 1 regression baseline.

After change:

Run all relevant repository tests, including:

```text
tooling.tests.test_shared_sdlc_core
tooling.tests.test_sdlc_contracts
tooling.tests.test_sdlc_acceptance
tooling.tests.test_baref_coverage
tooling.tests.test_gate_recovery
tooling.tests.test_gate_recovery_faults
tooling.tests.test_runtime_path_safety
tooling.tests.test_test_kit_customization
tooling.tests.test_kit_packaging
```

Add dedicated tests for:

- topology validation;
- project policy fail-closed behavior;
- policy cannot weaken invariants;
- foundation profile modes/statuses;
- Brownfield vs Greenfield evidence semantics;
- Foundation readiness with allowed PARTIAL/UNKNOWN;
- invalid evidence promotion between CURRENT_SYSTEM and APPROVED_TARGET;
- readiness compatibility;
- Shared Core has no Test Kit import dependency;
- old Test promotion import still works.

Run directly affected package/installed-runtime tests.

Do not weaken existing assertions.

---

# 15. Documentation

Add/update framework docs covering:

- Shared Project Policy.
- Topology contract.
- Project Foundation contract.
- readiness semantics.
- promotion dependency direction.
- Wave 2 migration map.

Do not perform the full OSS documentation/version cleanup yet.

---

# 16. Forbidden changes

Do NOT:

- touch Digital Wedding repos;
- create `digital-wedding-automation`;
- remove Appointment/XMind production profile yet;
- change BA business semantics;
- change Delivery Manifest V2;
- change Human Gate meaning;
- introduce a second requirements authority;
- redesign Spec Kit integration;
- run lockstep version migration;
- merge to `main`.

---

# 17. Required report

Return:

```text
PHASE_2_WAVE_2_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
<name>

BASE:
a83e71274fba9189c130cc7152d2e640a7e98df5

HEAD:
<exact SHA>

TOPOLOGY_CONTRACT:
<files + status>

PROJECT_POLICY_CONTRACT:
<files + status>

FOUNDATION_CONTRACT:
<files + status>

READINESS:
<changes>

PROMOTION_DEPENDENCY:
<proof Shared Core no longer imports Test Kit>

COMPATIBILITY:
<legacy paths preserved>

TESTS:
<commands and pass/fail/skip counts>

SEMANTIC_CHANGES:
NONE
or explicit list

BLOCKERS:
<list>

RECOMMENDED_PHASE_3:
<list>
```

If a material architecture decision beyond this approved scope is required, STOP with:

```text
ARCHITECTURE_DECISION_REQUIRED
```

and explain the exact decision.
