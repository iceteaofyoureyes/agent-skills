# Phase 3 — Wave 1 Implementation Spec
## Project Foundation Workflow Core

Status: READY_FOR_AGENT_EXECUTION
Required model: SOL High
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: f43da319673d34e7b43bf5042368b7ee36cd77ea
Source branch: refactor/shared-sdlc-core-v1-wave2
Suggested implementation branch: feat/project-foundation-v1-wave1

TEMPORARY BOOTSTRAP ARTIFACT:
This file exists only so the implementation agent can fetch the exact approved scope.
Create the Wave 1 branch from the latest remote source branch that contains this file, read it completely, then DELETE this file from the Phase 3 Wave 1 branch before the final implementation commit/report.
The final Wave 1 tree must not contain this bootstrap spec.

---

# 1. Goal

Implement the generic Project Foundation workflow core on top of the approved Shared SDLC Core contracts.

Wave 1 must make these modes operational:

- GREENFIELD_BOOTSTRAP
- BROWNFIELD_RECOVERY
- FOUNDATION_REFRESH

Wave 1 must provide:

1. Foundation run lifecycle and runtime artifacts.
2. Project knowledge inventory.
3. Brownfield evidence recovery mechanics.
4. Greenfield target bootstrap mechanics.
5. Refresh/change-impact entry logic.
6. Candidate Foundation Manifest creation from validated inputs.
7. Human review/approval routing without agent self-approval.
8. Promotion of accepted/approved durable foundation artifacts.
9. Public synthetic greenfield and brownfield acceptance fixtures.
10. Installed-runtime integration sufficient to expose the capability safely.

Wave 1 does NOT yet implement rich domain-specific or architecture-specific document generation.

---

# 2. Normative architecture

Approved precedence:

Human-approved decisions
> Shared SDLC invariants
> Project Policy
> Kit / atomic skill instructions
> Runtime defaults

Mandatory invariants:

- CONTINUE != APPROVE
- ANSWER != APPROVE
- validator PASS != APPROVE
- artifact generated != APPROVED
- derived artifact != authority
- CURRENT_SYSTEM != approved target business rule
- Dev fix PASS != Tester VERIFIED

Project Foundation MUST consume the contracts already implemented in shared/sdlc.
Do not duplicate their schemas or semantics in the workflow layer.

---

# 3. Capability boundary

Project Foundation is a Shared SDLC capability, not a fourth Kit.

Semantic ownership remains:

- BA: product, domain, glossary, business knowledge.
- ENGINEERING: architecture, runtime, deployment, ADR.
- TEST: test strategy, automation architecture, quality model.

The Project Foundation workflow may orchestrate, inventory, classify evidence, record gaps/unknowns, route work, validate candidates and promote accepted outputs.

It MUST NOT become an alternate semantic authority.

---

# 4. Required Wave 1 capabilities

Implement the equivalent of:

- foundation-inventory
- brownfield-recovery
- greenfield-bootstrap
- foundation-refresh
- foundation-validation
- foundation-promotion
- knowledge-impact-core

Exact names/paths may follow repository conventions, but each semantic capability must be independently testable.

Do NOT yet implement:

- domain-discovery
- architecture-discovery
- c4-modeling
- adr-management
- test-foundation rich discovery
- rich arc42 Markdown projection

Wave 1 may expose extension points/routes for those Wave 2 capabilities.

---

# 5. Runtime vs durable artifacts

Runtime work MUST live outside durable project authority.

Use a Shared SDLC hidden runtime location, conceptually equivalent to:

.sdlc/runs/foundation/<run-id>/

Runtime artifacts may include:

- run-state.json
- inventory.json
- evidence.json
- gaps.json
- questions.json
- candidate-foundation-manifest
- candidate-knowledge-impact
- review-request
- logs

These remain RUNTIME/EVIDENCE until explicitly promoted.

Durable Project Foundation artifact locations are project-owned and declared through Project Policy.
Do not hard-code product/domain/architecture/testing paths.

Promotion MUST use Shared Core immutable promotion primitives.
Raw prompts/logs MUST NOT be promoted as canonical authority.

---

# 6. Foundation run lifecycle

Introduce a machine-readable Foundation run state with at least:

- run_id
- project_id
- mode
- foundation_profile
- topology_ref
- project_policy_ref
- state
- inputs
- artifacts
- open_items
- history

The workflow must distinguish:

- input/inventory/analysis
- review required
- accepted or approved baseline
- PROJECT_FOUNDATION_READY

Validation success may make a candidate review-ready.
Only explicit Human decisions may cross required Human Gates.

PROJECT_FOUNDATION_READY is readiness, not feature/business approval.

---

# 7. Project knowledge inventory

Implement deterministic inventory over explicitly declared topology/project roots.

Classify at least:

- PRODUCT
- DOMAIN
- ARCHITECTURE
- ADR
- TEST_STRATEGY
- AUTOMATION_ARCHITECTURE
- OPERATIONS
- FEATURE
- MODULE_LOCAL
- RUNTIME
- EVIDENCE
- HISTORICAL
- UNKNOWN

Capture at least:

- repository id
- relative path
- artifact class
- candidate knowledge class
- hash/content metadata
- source kind
- owner candidate

Wave 1 does not need semantic NLP extraction from all files.

Do not read outside declared roots.
Reject traversal and symlink/reparse escapes.
Do not persist secret content into durable outputs.

---

# 8. Brownfield recovery semantics

Brownfield is reconstruction of current reality, not target design.

Allowed evidence labels:

- CURRENT_SYSTEM
- CONFIRMED
- INFERRED
- UNKNOWN

Rules:

1. Code/config/CI/runtime evidence may establish CURRENT_SYSTEM.
2. Existing approved project docs may establish CONFIRMED only when authority is valid under Project Policy.
3. Agent inference must be INFERRED.
4. Missing or ambiguous facts must be UNKNOWN.
5. Source behavior MUST NOT automatically become BR/FR.
6. Existing technology MUST NOT produce fabricated historical ADR rationale.
7. Conflicting sources MUST become explicit conflicts/gaps.
8. Brownfield recovery MUST NOT require reconstruction of the whole legacy system before bounded feature work.
9. Critical unknowns may block Foundation readiness; noncritical unknowns may remain when profile permits.

Wave 1 should produce evidence records and candidate manifest entries, not rich final architecture prose.

---

# 9. Greenfield bootstrap semantics

Greenfield starts from intent and approved inputs, not code archaeology.

Allowed target labels:

- APPROVED_TARGET
- PROPOSED
- DEFERRED
- UNKNOWN

Rules:

1. Agent may propose candidate target statements.
2. Proposed statements remain PROPOSED.
3. Material architecture decisions require explicit Human/Engineering approval.
4. APPROVED_TARGET must use exact Shared Core approval binding.
5. No agent proposal may self-promote.
6. Unknown constraints remain UNKNOWN.
7. Deferred areas remain explicit.

Wave 1 may create a candidate Foundation Manifest and deterministic review package.
Rich architecture option analysis belongs to Wave 2 or downstream Engineering capabilities.

---

# 10. Foundation refresh and knowledge impact

Refresh is incremental.

Provide a versioned generic knowledge-impact artifact that covers at least:

- product
- domain
- architecture
- testing

Each area must support:

- affected boolean
- target list

Refresh outcomes:

- NO_FOUNDATION_CHANGE
- FOUNDATION_UPDATE_REQUIRED

Neither outcome is Human approval.

Wave 1 only needs core categories and routing, not rich semantic document updates.

---

# 11. Conflict and gap handling

Surface explicitly and fail closed or require review for:

- duplicate project-level authority
- conflicting authority locations
- current-system evidence contradicting canonical approved docs
- missing required Project Policy authority entry points
- ambiguous repository ownership
- broken exact references/hashes
- unsupported Foundation schema versions
- attempted CURRENT_SYSTEM to APPROVED_TARGET promotion without approval
- historical ADR rationale with no evidence
- project policy attempting to weaken Shared Core invariants

Do not silently choose a source based on recency, proximity to code or parse convenience.

---

# 12. Human review package

Create a deterministic Human review package containing at least:

- mode
- candidate manifest identity/revision/hash
- critical blockers
- noncritical unknowns
- conflicts
- proposed target decisions
- evidence references
- knowledge impact
- required decisions

The agent MUST NOT emit a Human approval receipt.

Reuse Shared Core approval/gate primitives.

---

# 13. Promotion

After valid review/approval where required:

- promote exact candidate semantic bytes
- bind source evidence and manifest hash
- refuse overwrite of different durable approved snapshots
- retain provenance
- keep runtime/logs outside canonical authority

Brownfield accepted current-state documentation MUST remain current-state evidence.
Acceptance MUST NOT turn CURRENT_SYSTEM into target/business approval.

Greenfield APPROVED_TARGET requires Shared Foundation approval binding.

---

# 14. Foundation validation / capability Doctor

Expose a Project Foundation capability check that can return at least:

- PROJECT_FOUNDATION_READY
- NOT_READY
- BLOCKED

Do not globally rename current package Doctor outputs.

A project with explicit nonblocking PARTIAL/UNKNOWN may be PROJECT_FOUNDATION_READY when allowed by the profile.

---

# 15. Public synthetic fixtures

Add:

- synthetic-greenfield-foundation
- synthetic-brownfield-foundation

Brownfield fixture must contain:

- separated project/module roots or multi-repo shape
- existing code/config/docs
- at least one CURRENT_SYSTEM fact
- at least one INFERRED fact
- at least one UNKNOWN
- at least one authority conflict or duplicate candidate requiring explicit handling
- no Digital Wedding, PetClinic or Appointment semantics

Greenfield fixture must contain:

- project intent/constraints
- proposed target architecture evidence
- at least one Human-approval-required target
- at least one DEFERRED or UNKNOWN
- no implementation code requirement

Acceptance must prove no fabricated approval occurs.

---

# 16. Generic semantics only

Forbidden production hard-coding:

- Digital Wedding
- PetClinic
- Appointment
- CR-DWC-*
- FR-DASH-*
- specific company/team/user names
- specific Windows usernames

Synthetic fixtures may use neutral fictional identifiers.

---

# 17. Skill/instruction packaging

Project Foundation must be discoverable/invokable as one coherent framework capability.

Conceptual operator modes:

- project-foundation brownfield
- project-foundation greenfield
- project-foundation refresh

Exact command/skill syntax may follow repository conventions.

Do not create a fourth Kit.
Atomic skills own mechanics; orchestrator owns sequencing; Shared Core owns semantics.

---

# 18. Installed-runtime behavior

Capability must work after clean install/profile setup.

Do not rely on:

- source checkout being present
- hidden global config
- developer temp files
- untracked files
- user-specific absolute paths

Installed-runtime tests must prove the capability uses installed payload, not accidental source imports.

---

# 19. Tests

Before change run the Phase 2 regression baseline at:

f43da319673d34e7b43bf5042368b7ee36cd77ea

After change run:

- Shared Core tests
- directly affected BA/Dev/Test packaging tests
- installed-runtime tests
- Foundation workflow unit tests
- synthetic greenfield acceptance
- synthetic brownfield acceptance
- runtime/canonical separation tests
- approval-negative tests
- path/symlink escape tests where supported

Mandatory negative tests:

1. Agent cannot self-approve APPROVED_TARGET.
2. CURRENT_SYSTEM cannot become APPROVED_TARGET without receipt.
3. Validator PASS cannot mean Human approval.
4. Duplicate/conflicting authority is surfaced.
5. Critical unresolved blocker prevents PROJECT_FOUNDATION_READY.
6. Noncritical UNKNOWN may remain READY when profile permits.
7. Runtime artifacts are not written into durable authority paths before promotion.
8. Promotion refuses different existing approved bytes.
9. Temporary bootstrap spec is absent from final tree.
10. No project-specific domain leak exists in new production capability.

Do not weaken existing assertions.

---

# 20. Documentation

Add durable framework docs for:

- Project Foundation purpose and ownership
- Brownfield vs Greenfield vs Refresh
- evidence labels
- runtime vs durable artifacts
- Human review/approval boundary
- Foundation readiness
- public synthetic fixtures
- extension points for Phase 3 Wave 2

Do not claim rich arc42/C4/ADR generation exists yet if it does not.

---

# 21. Forbidden changes

Do NOT:

- touch Digital Wedding repos
- create digital-wedding-automation
- normalize Digital Wedding docs
- implement rich C4 generation
- fabricate ADRs
- migrate BA Kit workflow
- migrate Dev Kit workflow
- migrate Test Kit workflow
- remove Appointment XMind production profile yet
- redesign Spec Kit integration
- perform lockstep release versioning
- merge to main

---

# 22. Temporary spec cleanup

Before the final Wave 1 implementation commit/report:

DELETE:

PHASE_3_WAVE_1_PROJECT_FOUNDATION_WORKFLOW_SPEC.md

Do not rename/copy it elsewhere.
Verify final tree does not contain it.

---

# 23. Required report

Return:

PHASE_3_WAVE_1_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
<name>

BEHAVIORAL_BASE:
f43da319673d34e7b43bf5042368b7ee36cd77ea

HEAD:
<exact SHA>

FOUNDATION_WORKFLOW:
<files + states/modes>

INVENTORY:
<files + behavior>

BROWNFIELD_RECOVERY:
<files + semantics>

GREENFIELD_BOOTSTRAP:
<files + semantics>

FOUNDATION_REFRESH:
<files + semantics>

HUMAN_REVIEW:
<approval boundary>

PROMOTION:
<runtime to durable behavior>

SYNTHETIC_ACCEPTANCE:
<greenfield + brownfield>

INSTALLED_RUNTIME:
<status>

TESTS:
<commands + pass/fail/skip counts>

SEMANTIC_CHANGES:
NONE
or explicit list

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
feat/project-foundation-v1-wave1

RECOMMENDED_PHASE_3_WAVE_2:
<list>

If implementation requires changing an approved Shared Core architecture/authority contract, STOP with:

ARCHITECTURE_DECISION_REQUIRED

and describe the exact decision instead of silently changing the contract.
