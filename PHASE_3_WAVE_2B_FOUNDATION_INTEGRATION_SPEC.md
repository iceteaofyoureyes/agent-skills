# Phase 3 — Wave 2B Implementation Spec
## Project Foundation Integration, Packaging and End-to-End Acceptance

Status: READY_FOR_AGENT_EXECUTION
Required model: LUNA Medium
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: 2778985c68fa51c117019cd77a576a1396d48534
Source branch: fix/project-foundation-context-scope-owner-v1
Suggested implementation branch: feat/project-foundation-v1-wave2b

TEMPORARY BOOTSTRAP ARTIFACT:
This file exists only so a fresh implementation session can fetch the exact approved scope.
Create the Wave 2B branch from the latest remote source branch containing this file, read it fully, then DELETE this file before final commit/report.
The final Wave 2B tree must not contain this bootstrap spec.

---

# 1. Goal

Finish Phase 3 by integrating the already-approved Project Foundation workflow and semantic producers into the framework's operational surfaces.

Wave 2B is primarily mechanical integration.

The semantic implementation already exists and is approved at behavioral base:

2778985c68fa51c117019cd77a576a1396d48534

Wave 2B must NOT redesign it.

Required outcomes:

1. Project Foundation orchestrator exposes owner-specific producers coherently.
2. Installed runtime/profile contains all required Foundation source modules and skills.
3. Package/provenance/allowlists include all required Foundation files deterministically.
4. Clean-installed Foundation capability works without source-checkout imports.
5. Synthetic brownfield and greenfield workflows exercise the integrated producer path end-to-end.
6. Durable docs/indexes accurately describe the capability.
7. Full repository regression remains green.
8. Phase 3 ends with one coherent, installable Project Foundation capability.

---

# 2. Model boundary

This task uses LUNA Medium because architecture and semantics are already frozen.

If implementation requires ANY of the following, STOP and report:

ARCHITECTURE_DECISION_REQUIRED

Examples:

- changing Shared Core schemas;
- changing Human Gate semantics;
- changing evidence labels;
- changing section ownership;
- changing approval binding;
- changing Project Policy semantics;
- changing artifact classes;
- inventing new lifecycle states;
- moving semantic ownership between BA / ENGINEERING / TEST.

Do not solve architecture ambiguity inside Wave 2B.

---

# 3. Behavioral contracts that must remain unchanged

Do not change:

- Shared Project Policy V1 semantics.
- Project Topology V1 semantics.
- Project Foundation Manifest V1 semantics.
- Foundation modes:
  - GREENFIELD_BOOTSTRAP
  - BROWNFIELD_RECOVERY
  - FOUNDATION_REFRESH
- Human approval binding.
- PROJECT_FOUNDATION_READY meaning.
- BA / ENGINEERING / TEST ownership boundaries.
- context_scope owner = ENGINEERING.
- Introduction & Goals owner = BA/product.
- Glossary owner = BA/domain.
- Quality Requirements owner = TEST.
- domain-discovery semantics.
- architecture-discovery semantics.
- C4 semantics.
- ADR semantics.
- test-foundation semantics.
- arc42 projection semantics.
- FR/BR/BAREF behavior.
- Delivery Manifest V2.
- Test Kit feature-level Test Design/Testcases semantics.

Wave 2B wires existing contracts together.

---

# 4. Orchestrator integration

Extend Project Foundation operator/orchestrator surfaces so owner-specific semantic producers can be used through the installed capability.

The integrated workflow should support the equivalent of:

- inventory
- brownfield
- greenfield
- refresh
- domain-discovery
- architecture-discovery
- c4-modeling
- adr-management
- test-foundation
- arc42-projection
- conflicts / validation where appropriate
- doctor

Exact CLI subcommands/API shape should follow current project conventions.

Important:

- CLI MUST NOT expose a fake Human approval flag.
- CLI MUST NOT generate approval receipts.
- trusted-host-only APIs may remain Python/runtime APIs rather than unsafe CLI commands.
- producer inputs must remain explicit JSON/YAML semantic observations/exact refs.
- no hidden source scanning beyond Foundation inventory behavior.
- no prompt or reasoning-trace persistence.

If adding direct CLI commands creates unnecessary duplication, use a thin adapter over existing producer/workflow functions.

---

# 5. Runtime candidate integration

Owner-specific producers generate RUNTIME semantic artifacts.

Wave 2B should provide a deterministic project-runtime location and naming convention for integrated producer outputs.

Conceptually:

.sdlc/runs/foundation/<run-id>/semantic/
  domain.json
  architecture.json
  c4.json
  adr/
  testing.json
  arc42.json-or-md
  conflicts.json

Exact names may follow repository conventions.

Rules:

- runtime producer outputs remain RUNTIME or DERIVED as defined;
- no automatic promotion to canonical owner docs;
- C4 text rendering remains DERIVED;
- arc42 projection remains DERIVED;
- raw logs/prompts are not canonical;
- exact hashes/revisions must be retained in run state/review artifacts where integrated.

Do not create a second authority store.

---

# 6. Foundation review-package integration

Where owner-specific semantic artifacts are used in a Foundation run, update the deterministic review package to reference them explicitly.

Review package should be able to expose:

- semantic artifact identity/revision/hash;
- owner;
- producer type;
- unresolved conflicts;
- unknowns/gaps;
- proposed targets;
- C4/arc42 derived projections when present;
- required owner/Human decisions.

Do not duplicate full semantic content if exact references suffice.

Do not change the existing rule that the agent cannot approve.

---

# 7. Knowledge impact integration

Integrate existing Knowledge Impact with owner-specific outputs mechanically.

Expected routing remains:

- product/domain -> BA
- architecture/context_scope/C4/ADR -> ENGINEERING
- testing -> TEST

Do not invent semantic change-detection algorithms in this wave.

Use explicit affected inputs/known changed semantic records where available.

Refresh still returns:

- NO_FOUNDATION_CHANGE
- FOUNDATION_UPDATE_REQUIRED

Neither outcome implies approval.

---

# 8. Skill packaging

Project Foundation must remain one coherent Shared SDLC capability.

Update project-foundation/SKILL.md and supporting script entry points only as needed so users/agents can discover the integrated producer capabilities.

Do NOT create a fourth Kit.

Do NOT create standalone duplicate semantic skills if they merely bypass Project Foundation governance.

If atomic helper skills/files are introduced, Project Foundation remains the orchestrator and Shared Core remains semantic owner.

---

# 9. Installed runtime and profile integration

Ensure clean installed runtime includes all required Phase 3 files, including at least:

- shared/sdlc/foundation/workflow.py
- inventory.py
- impact.py
- producers.py
- cli.py
- Foundation contracts/profiles dependencies
- project-foundation/SKILL.md
- project-foundation scripts
- required neutral examples/configs if intentionally packaged

Update:

- runtime allowlists;
- installer file sets;
- agent profile preparation;
- package manifests;
- provenance locks;
- deterministic shared ZIP payloads;

as required by repository conventions.

Do not manually edit generated hashes when repository regeneration tools exist.

Run the canonical regeneration commands.

---

# 10. Installed-runtime isolation

Add/extend tests proving a clean install can execute the integrated Project Foundation capability when:

- repository source checkout is unavailable or intentionally blocked from import;
- PYTHONPATH does not point to source checkout;
- only installed runtime/profile payload is available.

At minimum verify installed runtime can:

1. inventory a neutral project;
2. run a brownfield candidate to REVIEW_REQUIRED;
3. run domain-discovery;
4. run architecture-discovery;
5. create and validate a C4 candidate + DERIVED view;
6. create an ADR candidate;
7. create Test Foundation candidate;
8. generate DERIVED arc42 projection;
9. run doctor/readiness checks.

Do not require installed CLI to perform trusted Human approval.

---

# 11. Synthetic end-to-end brownfield acceptance

Create or extend a neutral public synthetic brownfield acceptance lane.

End-to-end flow must cover:

Project configuration
→ inventory
→ brownfield Foundation run
→ domain discovery
→ architecture discovery
→ Test Foundation
→ recovered ADR with unknown rationale
→ C4 Context/Container model
→ cross-producer conflict handling
→ arc42 DERIVED projection
→ deterministic review package
→ explicit Human review simulation through trusted-host test harness
→ immutable promotion
→ PROJECT_FOUNDATION_READY

Required assertions:

- code-derived business behavior remains CURRENT_SYSTEM and does not become BR/FR;
- architecture inference remains INFERRED;
- recovered ADR rationale may remain UNKNOWN;
- conflict remains explicit until resolved/accepted by correct workflow;
- Context & Scope section owner is ENGINEERING;
- BA actor/entity records remain BA-owned inputs;
- Test Foundation does not create feature Test Design/Testcases;
- arc42/C4 views stay DERIVED;
- current-state acceptance does not become APPROVED_TARGET.

Use neutral fictional project names only.

---

# 12. Synthetic end-to-end greenfield acceptance

Create or extend a neutral public synthetic greenfield lane.

Flow should cover:

project intent/constraints
→ greenfield Foundation run
→ BA/domain candidate
→ architecture proposed target
→ proposed ADR
→ proposed C4 Context/Container
→ proposed Test Foundation
→ arc42 DERIVED projection
→ Human review package
→ trusted-host exact approval for selected target snapshot
→ immutable promotion
→ PROJECT_FOUNDATION_READY

Required assertions:

- PROPOSED never self-promotes;
- APPROVED_TARGET requires exact authenticated binding;
- agent/validator/CONTINUE/PASS cannot approve;
- unknown/deferred sections remain visible;
- unapproved proposed ADR is not labeled approved;
- approved ADR/architecture snapshot binds exact bytes;
- arc42 remains a projection even when its source Foundation baseline is approved.

---

# 13. Full cross-producer validation

Add tests that integrate producer artifacts rather than only unit-test them in isolation.

Cover at least:

- producer artifact exact hash/reference binding in a Foundation run;
- policy/topology drift invalidates integrated artifacts;
- semantic artifact byte drift fails;
- conflicting artifacts fail/route as expected;
- shared Project Policy paths remain valid;
- owner mismatches fail;
- unsupported schema versions fail closed;
- secret-bearing structured inputs fail;
- temporary runtime data is not promoted accidentally.

---

# 14. Packaging/provenance consistency

After all source changes:

Run repository-provided regeneration tools for:

- Shared SDLC payload ZIP(s);
- Test package if affected by shared payload closure;
- Dev provenance if affected;
- other package authority/manifests required by tests.

Do not introduce generated drift unrelated to Phase 3.

Package metadata should reflect actual files, not manually maintained stale lists.

If a package still requires explicit allowlists, include producers.py and all integrated Foundation files exactly once.

---

# 15. Documentation/index cleanup

Update durable docs so the framework accurately exposes Phase 3 capability.

At minimum inspect/update where appropriate:

- root README
- docs/project-foundation.md
- docs/foundation-semantic-producers.md
- docs/en/SHARED_SDLC_CONTRACTS_V1.md if integration status wording is stale
- docs/vi/ARCHITECTURE.md
- installation/usage docs that enumerate available capabilities
- agent/profile docs if Foundation is opt-in

Do not perform Phase 4 BA Kit migration in this wave.

Do not claim stable OSS release.

Do not rewrite all stale release/version docs yet unless directly needed to avoid false Foundation capability claims.

---

# 16. Generic/public-only rule

Production source and public synthetic acceptance must not hard-code:

- Digital Wedding
- PetClinic
- Appointment
- CR-DWC-*
- real user/company identities
- user-specific Windows paths

Temporary test paths must use temp directories.

---

# 17. Required tests

Before changes run the full baseline at:

2778985c68fa51c117019cd77a576a1396d48534

After changes run at least:

- tooling.tests.test_project_foundation
- tooling.tests.test_foundation_producers
- all new Wave 2B integration tests
- install/profile tests
- package/provenance tests
- full tooling unittest discovery

Also run clean-installed-runtime isolation acceptance.

Expected result:
0 failures / 0 errors.

Symlink tests may skip on Windows when privilege is unavailable, but reparse-path guards must still pass.

Do not weaken existing assertions.

---

# 18. Architecture drift guard

Add or retain a mechanical guard proving Wave 2B did not change semantic constants/contracts unexpectedly.

At minimum compare/assert:

- SECTION_DOMAINS ownership mapping;
- semantic producer owner/topic map;
- evidence label map;
- Foundation modes;
- artifact class of C4/arc42 projections;
- Human approval required for APPROVED_TARGET.

The goal is to catch accidental semantic edits during packaging/wiring.

Do not snapshot huge source files unnecessarily if targeted contract assertions suffice.

---

# 19. Forbidden changes

Do NOT:

- touch Digital Wedding repos;
- create digital-wedding-automation;
- normalize Digital Wedding docs;
- migrate BA Kit VNext;
- migrate Dev Kit VNext;
- migrate Test Kit VNext;
- remove Appointment/XMind production profile yet;
- redesign Spec Kit integration;
- change Shared Core contracts;
- change Human Gate semantics;
- change Delivery Manifest V2;
- change FR/BR/BAREF semantics;
- introduce stable framework lockstep version;
- merge to main.

---

# 20. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_3_WAVE_2B_FOUNDATION_INTEGRATION_SPEC.md

Do not rename/copy it elsewhere.

Final tree must not contain it.

---

# 21. Required report

PHASE_3_WAVE_2B_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/project-foundation-v1-wave2b

BASE:
2778985c68fa51c117019cd77a576a1396d48534

HEAD:
<exact SHA>

ORCHESTRATOR_INTEGRATION:
<commands/APIs/wiring>

RUNTIME_ARTIFACT_INTEGRATION:
<paths + classifications>

REVIEW_PACKAGE:
<semantic refs/conflicts/decisions>

KNOWLEDGE_IMPACT:
<routing integration>

SKILL_PACKAGING:
<status>

INSTALLED_RUNTIME:
<clean install/isolation proof>

BROWNFIELD_E2E:
<status + assertions>

GREENFIELD_E2E:
<status + assertions>

PACKAGING_PROVENANCE:
<regeneration + integrity>

DOCS:
<updated durable docs>

TESTS:
<commands + pass/fail/skip counts>

SEMANTIC_DRIFT:
NONE
or exact list

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
feat/project-foundation-v1-wave2b

RECOMMENDED_PHASE_4:
<BA Kit VNext migration prerequisites>

If any contract/ownership/approval semantic change is required, STOP with:

ARCHITECTURE_DECISION_REQUIRED

and describe the exact decision instead of changing it.
