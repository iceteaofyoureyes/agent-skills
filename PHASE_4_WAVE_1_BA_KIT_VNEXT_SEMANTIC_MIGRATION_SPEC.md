# Phase 4 — Wave 1 Implementation Spec
## BA Kit VNext Semantic Migration

Status: READY_FOR_AGENT_EXECUTION
Required model: SOL High
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: 7e1ca52e007a444d0b6dad5b15eb3cc86654ec69
Source branch: feat/project-foundation-v1-wave2b
Suggested implementation branch: feat/ba-kit-vnext-wave1

TEMPORARY BOOTSTRAP ARTIFACT:
This file exists only so a fresh implementation session can fetch the exact approved scope.
Create the Wave 1 branch from the latest remote source branch containing this file, read it fully, then DELETE this file before final commit/report.
The final Wave 1 tree must not contain this bootstrap spec.

---

# 1. Goal

Migrate BA Kit to the approved VNext SDLC architecture without rewriting working capabilities.

Preserve and reuse what is already correct:

- Shared Core approval invariants.
- ApprovedBaseline FR/BR/BAREF semantics.
- Delivery Manifest V2.
- current BA evidence labels.
- existing SRS/BR/document/diagram atomic skills.
- existing BA-to-Engineering boundary prohibiting technical design ownership.
- existing package/install compatibility where possible.

Wave 1 is the semantic/workflow migration.

Wave 1 must establish:

1. BA VNext lifecycle and state model.
2. exact BA baseline candidate contract.
3. exact Human BA Baseline Gate.
4. stable FR/BR business identity rules.
5. explicit BA decisions authority.
6. Brownfield CURRENT_SYSTEM / target distinction.
7. Project Foundation consumption.
8. Knowledge Impact production.
9. Engineering Handoff VNext binding.
10. backward-compatible readers/adapters for current BA workflow/handoff where safe.
11. synthetic BA semantic acceptance.

Wave 1 does NOT perform broad installer/docs/example cleanup; that is Wave 2.

---

# 2. Approved architecture

Instruction precedence remains:

Human-approved decisions
> Shared SDLC invariants
> Project Policy
> Kit / atomic skill mechanics
> Runtime defaults

BA owns WHAT:

- product/feature business intent;
- actors and business permissions;
- business rules;
- functional behavior;
- functional states/lifecycle;
- validation/business outcomes;
- glossary/domain meaning as applicable;
- functional SRS;
- BA clarification decisions.

BA does NOT own HOW:

- repository/module ownership;
- API/event shapes;
- DB schema/design;
- service boundaries;
- locking/transaction strategy;
- deployment architecture;
- technical implementation plan.

Engineering Handoff may authorize downstream technical analysis but must not contain those HOW decisions.

---

# 3. Existing implementation to preserve

Current implementations are migration inputs, not disposable legacy:

- ba-workflow/SKILL.md
- ba-workflow/references/*
- ba-workflow/scripts/validate-state.py
- ba-workflow/scripts/validate-handoff.py
- ba-workflow/templates/workflow-state.json
- ba-workflow/templates/engineering-handoff.yml
- shared/sdlc/authority/contracts.py
- shared/sdlc/authority/approved_baseline.py
- shared/sdlc/artifacts/delivery_manifest.py
- tooling/lib/ba_kit.py
- existing BA atomic skills
- current BA tests

Do not flag-day rewrite installed callers.

Prefer compatibility adapters/read-old/write-new where feasible.

---

# 4. BA VNext lifecycle

Introduce one normative BA baseline lifecycle:

DRAFT
→ VALIDATED
→ HUMAN_REVIEW
→ APPROVED_BASELINE

Meaning:

DRAFT
- business semantics are still being collected/edited;
- UNKNOWN/PROPOSED may exist;
- no approval claim.

VALIDATED
- deterministic BA validators pass for the exact candidate revision;
- validator PASS is not Human approval;
- blocking semantic gaps may still force return to DRAFT rather than advance.

HUMAN_REVIEW
- exact baseline candidate is frozen for Human review;
- artifact identity/revision/hash and authoritative inputs are fixed;
- edits require a new candidate revision.

APPROVED_BASELINE
- exact Human BA approval is authenticated and binds the reviewed baseline snapshot;
- downstream may consume it;
- approval does not approve UX/technical design unless explicitly covered by separate gates.

Do not infer approval from CONTINUE, ANSWER, validation success, generation or file presence.

If existing workflow needs operational stages such as REQUIREMENT_REVIEW / BUSINESS_RULES / SRS, keep them as sub-stage/activity metadata.
Do not let sub-stage names replace the normative baseline lifecycle.

---

# 5. BA workflow state VNext

Create a versioned, fail-closed BA workflow state contract.

Minimum semantics:

- schema_version
- feature identity
- mode
- operation
- baseline lifecycle state
- current activity/sub-stage
- candidate revision
- artifacts
- authoritative input refs
- evidence/gaps
- gates
- pending items
- source-of-truth routing
- Project Foundation reference when present
- Knowledge Impact
- append-only history

Requirements:

- exact refs use Shared Core reference validation;
- unsupported schema versions fail closed;
- unknown fields fail unless explicit extension mechanism is designed/tested;
- runtime state is RUNTIME, never business authority;
- state does not contain secrets;
- state cannot claim APPROVED_BASELINE without valid approval binding.

Current workflow-state.json V1 must remain readable through compatibility logic or an explicit migration path.

Do not silently reinterpret a V1 arbitrary stage as approval.

---

# 6. BA baseline candidate contract

Create a deterministic machine-readable BA baseline candidate/manifest.

It binds the exact BA authority set for one feature/revision.

Minimum semantic inputs:

- feature id/title
- baseline revision
- confirmed Human BA decisions artifact
- Business Rules artifact
- canonical functional SRS artifact
- optional glossary/domain refs required for that feature
- non-blocking open items
- blocking open items
- Knowledge Impact
- Project Foundation snapshot/ref when consumed
- candidate semantic hash

Required rules:

- blocking open items MUST be empty before HUMAN_REVIEW / approval.
- every authoritative artifact has exact path/revision/hash.
- changed bytes require a new baseline revision.
- candidate semantic identity is deterministic.
- derived artifacts such as DOCX, Draw.io and prototype are NOT part of BA semantic authority unless an explicitly approved contract says otherwise.
- UX approval remains a separate gate.

Do not duplicate the full content of BR/SRS/decisions into the manifest.

---

# 7. Stable BA business identities

Canonical business identities:

- BR-* for Business Rules.
- FR-* for functional requirements/functional SRS statements.

Rules:

1. Stable IDs persist across edits when the same semantic item continues.
2. New semantic item gets a new ID.
3. Removed/superseded IDs are not silently reused for different meaning.
4. Duplicate IDs fail closed.
5. IDs may be normalized for Markdown formatting but not semantically rewritten.
6. BAREF:* remains a structural/provenance locator only.
7. BAREF:* MUST NOT impose mandatory coverage.
8. coverage_ids remain canonical FR/BR only.

Do not introduce feature-specific hard-coded prefixes.

Existing ApprovedBaseline behavior for authority_ref_ids vs coverage_ids must remain green.

---

# 8. BA decisions authority

Define a clear BA Decisions artifact contract.

It records explicit Human answers/decisions that affect business semantics.

Minimum semantics per decision:

- stable decision id
- question/decision topic
- decision text
- actor/human identity reference
- decision timestamp or recorded-at metadata
- evidence/input refs
- affected BR/FR IDs when known
- status/currentness
- supersedes/superseded-by when applicable

Important:

- an ANSWER may resolve only the named question.
- an answer is not automatically baseline approval.
- a newer decision may require BR/SRS update before baseline approval.
- old BR/SRS cannot remain silently authoritative when a newer confirmed decision contradicts them.
- Agent may record the supplied Human decision but cannot fabricate the Human identity/authentication.

Do not expose private reasoning/chain-of-thought.

---

# 9. Human BA Baseline Gate

Create an exact BA approval receipt/gate contract reusing Shared Core approval invariants and trusted-host authentication.

The receipt must bind at least:

- schema_version
- decision = APPROVE
- actor id
- actor role = HUMAN
- recorded timestamp
- feature id
- baseline id
- baseline revision
- baseline semantic SHA-256
- exact reviewed input refs/hashes or an exact baseline-manifest ref
- decision evidence ref
- optional previous approved baseline identity for revisions

Rules:

- hash proves integrity, not Human identity.
- host authenticator validates Human identity.
- validator PASS != approval.
- ANSWER != approval.
- CONTINUE != approval.
- generated artifact != approval.
- approval of revision R1 does not approve changed R2.
- receipt drift fails closed.
- approval must not be embedded in mutable workflow state as an unauthenticated boolean.

If a generic Shared Core approval primitive can be reused, reuse it.
Do not introduce a competing cross-kit approval model.

---

# 10. Brownfield BA behavior

BA VNext consumes Project Foundation when available.

For brownfield features:

- Project Foundation/current-system evidence may be referenced.
- code/UI/API/database behavior may establish CURRENT_SYSTEM.
- implementation inference remains INFERRED.
- stale/current-system behavior does not become target requirement automatically.
- contradictions between requested behavior, BA authority and current system become gaps/questions.
- current architecture facts belong to Engineering/Foundation, not BA semantic authority.
- BA may reference current behavior to clarify WHAT changes.

Do not duplicate repository archaeology logic already owned by Project Foundation.
BA should consume Foundation inventory/accepted current baseline where possible.
Feature-bounded discovery remains allowed when Foundation lacks enough detail.

---

# 11. Greenfield BA behavior

For greenfield:

- begin from Human intent/requirements and Project Foundation target context if available.
- Agent may propose questions/rules; proposals remain PROPOSED.
- target business semantics require Human confirmation.
- Project Foundation architecture approval does not approve business requirements.
- BA approval does not approve architecture.

Keep authority boundaries bidirectional and explicit.

---

# 12. Project Foundation integration

BA Kit must be able to consume a valid PROJECT_FOUNDATION_READY snapshot/reference without treating it as BA approval.

Expected use:

- product/domain/glossary context may seed BA analysis when owned/confirmed appropriately.
- architecture/system context may constrain or inform gaps but remains Engineering-owned.
- unresolved Foundation critical blockers relevant to the feature may block BA readiness when they prevent correct business analysis.
- noncritical Foundation UNKNOWN may remain explicit.
- BA feature work must not require a perfect/full project foundation if the relevant bounded context is sufficient.

Project Foundation reference should be exact and optional for modes where it is not applicable.

No hard-coded Digital Wedding topology.

---

# 13. Knowledge Impact from BA

Every approved BA feature baseline should carry or produce Knowledge Impact.

At minimum:

- product affected + targets
- domain affected + targets
- architecture affected + targets
- testing affected + targets

BA may authoritatively determine product/domain impact.

BA may flag architecture/testing as affected/possibly affected for downstream routing, but MUST NOT write the technical solution.

Typical examples:

- new business lifecycle -> domain affected; architecture/testing likely affected.
- wording-only SRS edit with no semantic change -> no semantic impact.
- changed permission/business rule -> domain affected; testing affected; architecture may require downstream assessment.

Use Shared Foundation Knowledge Impact contract when applicable rather than create an incompatible duplicate.

---

# 14. BA baseline validation

Introduce deterministic validation of a BA baseline candidate.

It should check at least:

- valid feature identity/revision;
- authoritative sources exist and exact hashes match;
- stable FR/BR uniqueness;
- BAREF not used as mandatory business coverage;
- no blocking open items;
- no unresolved contradiction between latest confirmed BA decisions and selected BR/SRS revision when such binding data is available;
- evidence labels valid;
- prohibited technical design ownership absent;
- Project Foundation ref valid when supplied;
- Knowledge Impact valid.

Success result may be VALIDATED.

It MUST NOT set APPROVED_BASELINE.

---

# 15. Engineering Handoff VNext

Create a VNext handoff contract or compatible extension that consumes only an APPROVED_BASELINE.

Required binding:

- feature id/title
- BA baseline id/revision/hash
- exact approval receipt ref/hash
- exact authoritative sources:
  - Business Rules
  - canonical SRS
  - BA Decisions
- Knowledge Impact
- Project Foundation ref when relevant
- blocking open items = none
- non-blocking open items explicit
- downstream policy:
  - may not change approved business semantics
  - may make technical design decisions
- next capability = Engineering Impact / Dev workflow

Forbidden:

- frontend_owner
- backend_owner
- service_owner
- implementation_owner
- API design
- DB design
- event schema
- locking strategy
- transaction strategy
- architecture decision as a BA-owned field

Handoff validation must revalidate exact baseline approval, not trust status text alone.

Current Engineering Handoff V1 must remain readable for compatibility where safe.

Do not let the string APPROVED_FOR_ENGINEERING alone become sufficient proof in the VNext write path.

---

# 16. Derived artifact governance

Preserve current behavior:

Canonical BA semantic authority:
- Human BA Decisions
- Business Rules
- canonical SRS

Derived/delivery:
- Draw.io
- DOCX generated from canonical Markdown
- optional prototype
- presentation/visual exports

Rules:

- derived artifact may expose a gap;
- gap routes back to BA semantics;
- derived artifact may not silently create a new BR/FR;
- changing approved semantics invalidates/requires refresh of affected derived artifacts;
- visual/UX approval remains separate from BA baseline approval unless exact combined scope is explicitly defined by a future contract.

Do not redesign atomic Draw.io/DOCX skills in Wave 1.

---

# 17. Operation semantics

Preserve:

REVIEW
- read-only
- no artifact mutation
- no lifecycle advancement

CREATE
- create requested candidate artifacts when inputs are sufficient

EDIT
- mutate only target scope
- preserve unaffected approved semantics/IDs

CONTINUE
- resume persisted workflow
- never approve

REQUEST_CHANGES / REJECT
- return to appropriate prior candidate state
- do not overwrite approved snapshot bytes

Define safe transitions explicitly and test them.

---

# 18. Compatibility strategy

Prefer:

old BA public/import path
→ compatibility adapter
→ VNext contract implementation

or read-old/write-new where safer.

Preserve:

- ba-workflow/scripts/contracts.py compatibility import.
- ba-workflow/scripts/approved_baseline.py compatibility import.
- ba-workflow/scripts/delivery_manifest.py compatibility import.
- existing validator CLI entry points when feasible.
- existing BA atomic skills.

Do not remove current V1 handoff/state readers until migration acceptance proves new callers.

If legacy artifacts cannot represent VNext proof, read them as LEGACY_COMPAT / insufficient-for-new-approval rather than fabricating VNext approval evidence.

---

# 19. Synthetic acceptance

Add neutral synthetic BA VNext fixtures.

Must cover at least:

A. Brownfield:
- valid Project Foundation ref/current-system evidence;
- CURRENT_SYSTEM behavior differs from requested target;
- Human clarification resolves target;
- stable BR/FR generated/selected;
- candidate validates;
- Human approves exact baseline;
- Engineering Handoff binds exact approved baseline;
- Knowledge Impact routes downstream.

B. Greenfield:
- no current-system dependency;
- PROPOSED/UNKNOWN questions;
- explicit Human answers;
- BR/FR candidate;
- exact baseline Human approval;
- valid handoff.

C. Negative:
- CONTINUE cannot approve.
- ANSWER cannot approve baseline.
- validator PASS cannot approve.
- changed SRS after approval invalidates handoff.
- changed BR after approval invalidates handoff.
- changed decisions after approval invalidates handoff.
- duplicate FR/BR fails.
- BAREF-only structural sections do not create mandatory coverage IDs.
- blocking item prevents Human review/approval.
- technical design field in BA handoff rejected.
- stale Foundation ref/hash rejected.
- approval receipt for R1 cannot approve R2.
- agent identity cannot authenticate Human approval.

Use neutral fictional domain names only.

No Digital Wedding/PetClinic/Appointment semantics in production or public conformance fixtures.

---

# 20. Tests

Before changes run full baseline at:

7e1ca52e007a444d0b6dad5b15eb3cc86654ec69

After changes run at least:

- tooling.tests.test_ba_kit
- tooling.tests.test_sdlc_contracts
- tooling.tests.test_sdlc_acceptance
- tooling.tests.test_baref_coverage
- Project Foundation tests affected by Knowledge Impact/reference reuse
- new BA VNext contract/workflow tests
- full tooling unittest discovery

Also run direct validator CLI compatibility tests.

Do not weaken existing assertions.

---

# 21. Architecture drift guards

Add targeted tests proving:

- CONTINUE != APPROVE
- ANSWER != APPROVE
- validator PASS != APPROVE
- generated != APPROVED
- CURRENT_SYSTEM != target business rule
- BA owns WHAT; technical design fields rejected
- coverage_ids = canonical FR/BR only
- BAREF is locator only
- Project Foundation READY != BA APPROVED_BASELINE
- UX approval != BA baseline approval
- Dev/Engineering handoff cannot be produced from an unapproved baseline

Do not snapshot entire source files if targeted semantic assertions are sufficient.

---

# 22. Documentation in Wave 1

Update only durable contract/workflow docs required to accurately describe the new BA VNext semantics.

At minimum likely:

- ba-workflow/SKILL.md
- ba-workflow/references/workflow-state.md
- ba-workflow/references/human-gate.md
- ba-workflow/references/source-authority.md
- ba-workflow/references/engineering-handoff.md
- docs/vi/BA_KIT_WORKFLOW.md
- English counterpart if the same contract is described there

Do not perform broad README/release/version cleanup yet.

Wave 2 will handle complete packaging/docs/examples/installation acceptance.

---

# 23. Versioning

Do not release stable framework/BA Kit 1.0/2.0 as part of this task.

If a BA workflow schema version changes, give that artifact schema its own explicit version.

Keep framework release/version migration for the later release phase.

Do not silently overload schema_version 1 with incompatible meaning.

---

# 24. Forbidden changes

Do NOT:

- touch Digital Wedding repos;
- migrate Dev Kit VNext;
- migrate Test Kit VNext;
- remove Appointment/XMind profile leak yet;
- redesign Spec Kit;
- change Shared Project Policy semantics;
- change Project Foundation ownership semantics;
- change Delivery Manifest V2;
- change UX receipt V2;
- create technical architecture decisions inside BA Kit;
- introduce framework stable lockstep version;
- merge to main.

---

# 25. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_4_WAVE_1_BA_KIT_VNEXT_SEMANTIC_MIGRATION_SPEC.md

Do not rename/copy it elsewhere.

Final tree must not contain it.

---

# 26. Required report

PHASE_4_WAVE_1_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/ba-kit-vnext-wave1

BASE:
7e1ca52e007a444d0b6dad5b15eb3cc86654ec69

HEAD:
<exact SHA>

BA_LIFECYCLE:
<state model + files>

WORKFLOW_STATE_VNEXT:
<schema/compatibility>

BASELINE_CANDIDATE:
<identity/revision/hash/source binding>

STABLE_IDS:
<FR/BR/BAREF behavior>

BA_DECISIONS:
<contract>

HUMAN_BASELINE_GATE:
<exact approval binding/authentication>

FOUNDATION_INTEGRATION:
<consumption boundary>

KNOWLEDGE_IMPACT:
<output/routing>

ENGINEERING_HANDOFF:
<VNext binding + compatibility>

DERIVED_ARTIFACT_BOUNDARY:
<status>

SYNTHETIC_ACCEPTANCE:
<brownfield/greenfield/negative>

TESTS:
<commands + pass/fail/skip counts>

SEMANTIC_CHANGES:
<expected VNext lifecycle additions; no Shared Core drift>

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
feat/ba-kit-vnext-wave1

RECOMMENDED_PHASE_4_WAVE_2:
<mechanical packaging/docs/examples/install acceptance>

If any Shared Core authority/approval/Project Foundation semantic change is required, STOP with:

ARCHITECTURE_DECISION_REQUIRED

and describe the exact decision instead of changing it silently.
