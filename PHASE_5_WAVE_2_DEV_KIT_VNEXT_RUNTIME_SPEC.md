# Phase 5 — Wave 2 Implementation Spec
## Dev Kit VNext Runtime and Workflow Integration

Status: READY_FOR_AGENT_EXECUTION
Required model: SOL High
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: 42e4e974b30d16a445e5aa236698009cce8d2f0c
Source branch: feat/dev-kit-vnext-wave1
Suggested implementation branch: feat/dev-kit-vnext-wave2

TEMPORARY BOOTSTRAP ARTIFACT:
This file exists only so a fresh implementation session can fetch the exact approved Wave 2 scope.
Create the Wave 2 branch from the latest remote source branch containing this file, read it fully, implement Wave 2 only, then DELETE this file before the final commit/report.
The final Wave 2 tree must not contain this bootstrap spec.

---

# 1. Goal

Integrate the already-approved Dev Kit VNext semantic contracts from Wave 1 into the actual Dev Kit runtime/workflow.

Wave 1 is frozen at behavioral base:

42e4e974b30d16a445e5aa236698009cce8d2f0c

Wave 2 must make those contracts executable through real Dev Kit orchestration while preserving the existing useful V1 infrastructure.

Required outcomes:

1. new Dev runs use VNext by default;
2. V1 remains read-only LEGACY_COMPAT;
3. runtime persistence uses Dev State V2;
4. NORMAL / HIGH_RISK / TECHNICAL_MAINTENANCE flows are executable;
5. Spec Kit remains workflow/state infrastructure only;
6. exact technical gate proof is enforced where required;
7. source mutation is guarded by IMPLEMENTATION_READY, base revision and write scope;
8. Engineering Gap can pause and resume against a replacement Engineering Handoff VNext;
9. bounded engineering review is integrated;
10. fresh repository-native engineering verification is captured as exact evidence;
11. Dev Handoff VNext is emitted only at READY_FOR_TEST;
12. neutral synthetic runtime acceptance covers normal/high-risk/gap/multi-repo/maintenance.

Wave 2 does NOT perform full installer/package/docs migration; that is Wave 3.

---

# 2. Frozen Wave 1 semantics

Do NOT change:

- FEATURE_DELIVERY / TECHNICAL_MAINTENANCE authority modes;
- lifecycle V2;
- Engineering Impact V2;
- Engineering Gap contract;
- ED-* Engineering Decision contract;
- technical Human/Tech Lead approval contract;
- FR/BR-only requirements coverage;
- Dev Handoff VNext;
- V1 LEGACY_COMPAT semantics;
- BA VNext proof;
- Project Foundation proof;
- Shared Finding taxonomy;
- READY_FOR_TEST meaning.

If runtime integration reveals a semantic defect requiring those contracts to change, STOP with:

ARCHITECTURE_DECISION_REQUIRED

Do not silently redesign Wave 1.

---

# 3. Deferred Delivery Manifest rule

Delivery Manifest V2 integration is deliberately deferred.

For Wave 2:

- Engineering Handoff VNext is the only feature-delivery authorization proof.
- state.delivery remains optional exact metadata only.
- delivery metadata MUST NOT authorize implementation.
- runtime MUST NOT use Delivery Manifest targets to expand repository/write scope.
- runtime MUST NOT treat Delivery Manifest as a replacement for Engineering Handoff VNext.
- do not modify Shared Delivery Manifest V2.
- do not introduce Delivery Manifest V3.
- do not add legacy/VNext Delivery adapters in this wave.

If delivery is supplied, preserve its exact ref in state/handoff and fail on ref drift.
Nothing more is required in Wave 2.

---

# 4. Runtime architecture

Do not keep expanding tooling/lib/dev_vnext.py into a monolithic orchestration file.

Preferred separation:

- tooling/lib/dev_vnext.py
  - frozen semantic contracts from Wave 1

- tooling/lib/dev_vnext_runtime.py or equivalent
  - persistence
  - CLI orchestration adapters
  - repository observations
  - command execution
  - evidence writing
  - workflow routing
  - Spec Kit integration

Existing tooling/lib/dev_kit.py may:
- dispatch VNext operations;
- retain legacy V1 CLI/read compatibility;
- reuse existing safe helpers where appropriate.

Avoid duplicating Wave 1 validators.

Runtime must call canonical dev_vnext functions.

---

# 5. Runtime storage

Use existing Dev Kit runtime root:

.devkit/

VNext runs should use a deterministic layout, for example:

.devkit/
  current.json
  runs/
    <run-id>/
      state.json
      start-request.json
      impact.json
      gaps/
      decisions/
      snapshots/
      evidence/
        review/
        checks/
      dev-plan.md
      dev-tasks.md
      dev-handoff.json

Exact naming may follow existing repository conventions.

Rules:

- state.json is RUNTIME;
- plan/tasks are RUNTIME planning artifacts;
- evidence is EVIDENCE;
- final Dev Handoff is HANDOFF_MANIFEST;
- do not copy BA authority content into .devkit;
- exact refs point to upstream authority bytes outside runtime where applicable.

Writes must be atomic where practical.

---

# 6. Start / intake routing

Add a VNext start path.

For FEATURE_DELIVERY require:

- change_id
- summary
- exact Engineering Handoff VNext ref
- repositories with exact base revisions
- explicit write scope
- repository-native engineering checks
- optional exact delivery ref
- explicit risk signals when supplied

For TECHNICAL_MAINTENANCE require:

- change_id
- summary
- maintenance kind
- no_what_change=true
- maintenance evidence refs
- exactly one implementation repository
- explicit write scope
- engineering checks

The runtime creates state V2 in INTAKE.

No source mutation is allowed during start/intake.

---

# 7. Authority validation

FEATURE_DELIVERY:

INTAKE
→ AUTHORITY_VALIDATED

must call the canonical Wave 1 BA VNext reader and trusted-host callbacks.

It must:

- authenticate BA Human approval;
- revalidate exact BA baseline/source bytes;
- revalidate Foundation durable proof when present;
- reject V1 upstream authority;
- protect BA transitive authority paths from write scope overlap.

TECHNICAL_MAINTENANCE:

- validate maintenance evidence;
- enforce no upstream feature authority;
- enforce TRIVIAL;
- reject behavior/public-contract/data/security/cross-repo discovered changes.

Do not infer trusted Human identity from local files/status strings.

---

# 8. Impact integration

FEATURE_DELIVERY runtime must support creation/ingestion/validation of Engineering Impact V2.

Flow:

AUTHORITY_VALIDATED
→ IMPACT_ANALYZED

Use exact:

- repositories
- base revisions
- write scope
- risk
- Knowledge Impact
- technical unknowns
- upstream gaps

Runtime may offer a deterministic template/skeleton generator.

Template generation MUST NOT fabricate answers.

Blocking technical unknowns or upstream gaps prevent technical planning.

Risk may escalate but never downgrade.

---

# 9. Engineering Gap runtime

When a WHAT contradiction or missing business decision appears:

- create or ingest exact Engineering Gap V2;
- validate affected BR/FR;
- persist exact evidence refs;
- transition to UPSTREAM_GAP;
- clear technical authorization/gates for affected downstream work;
- block source mutation.

Resume requires:

- resolution evidence;
- replacement Engineering Handoff VNext;
- revised BA baseline bound to previous baseline;
- trusted Human authentication;
- exact replacement binding.

Resume transition:

UPSTREAM_GAP
→ AUTHORITY_VALIDATED

Existing technical plan/snapshot/gates are not reused after upstream replacement.

---

# 10. Planning integration

FEATURE_DELIVERY:

IMPACT_ANALYZED
→ TECHNICAL_PLANNED

Runtime must produce or ingest:

- dev-plan.md
- dev-tasks.md
- Engineering Decision refs
- exact technical snapshot V2

Plan/tasks must bind:

- upstream Handoff VNext;
- impact;
- ED set;
- repositories/base revisions;
- write scope;
- risk.

Do not duplicate BR/FR prose as a new requirements authority.

Spec Kit may orchestrate plan/task workflow but cannot own semantic authority.

---

# 11. Spec Kit integration

Preserve existing pinned Spec Kit runtime and workflow infrastructure.

Allowed:

- pause/resume;
- workflow run identity;
- deterministic phase orchestration;
- human interaction transport;
- bundle execution.

Forbidden:

- creating spec.md business authority;
- running/re-enabling speckit.specify;
- running/re-enabling speckit.plan;
- running/re-enabling speckit.tasks;
- running/re-enabling speckit.analyze;
- running/re-enabling speckit.converge;
- treating a Spec Kit approve choice as technical approval by itself.

If current workflow YAML uses a gate choice, adapt it so the choice is only orchestration evidence unless an exact authenticated VNext technical receipt is supplied.

---

# 12. Technical gate runtime

For HIGH_RISK or material ED runs:

TECHNICAL_PLANNED
→ IMPLEMENTATION_READY

requires:

- exact technical snapshot;
- exact technical approval receipt;
- trusted Human/Tech Lead authentication.

Runtime must fail on:

- missing authenticator;
- false authenticator;
- snapshot drift;
- plan/task drift;
- ED drift;
- impact drift;
- base revision drift;
- write-scope drift;
- replayed receipt.

NORMAL reversible runs with no active material ED do not require a Human technical gate.

Do not add unnecessary approval for routine local choices.

---

# 13. Source mutation guard

Every runtime-controlled source write must call Wave 1 authorization.

Allowed only in:

- IMPLEMENTATION_READY
- IMPLEMENTING

Before each write/relevant mutation verify:

- exact state;
- exact upstream proof;
- current base revisions;
- technical gate if required;
- repository id;
- approved write path.

Source writes outside approved scope must fail closed.

The runtime must not silently expand scope.

---

# 14. Risk escalation / replan

If implementation discovers new technical risk:

- risk can only stay equal or escalate;
- HIGH_RISK categories cannot be removed;
- invalidate stale gate/snapshot as required;
- transition to NEEDS_REPLAN;
- re-enter AUTHORITY_VALIDATED;
- rebuild impact/plan/snapshot;
- get new exact Human technical approval when required.

Do not preserve stale approval across material changes.

---

# 15. Implementation workflow

Preserve the useful current discipline:

- incremental slices;
- focused tests;
- TDD/regression where behavior changes;
- no unrelated cleanup;
- no BA authority mutation;
- no unauthorized path expansion.

Do not add an independent full reviewer after every slice.

One consolidated review remains the default.

---

# 16. Engineering review runtime

Integrate bounded review:

- full_reviews <= 1
- blocking_fix_waves <= 1
- scoped_rereviews <= 1

Required feature path:

IMPLEMENTING
→ ENGINEERING_REVIEW
→ VERIFYING

One consolidated full review is required before READY_FOR_TEST.

If blocking findings exist:

- one blocking fix wave;
- optional scoped rereview;
- no second full review.

A WHAT/spec finding routes to Engineering Gap, not a code-only fix.

---

# 17. Fresh engineering verification

Runtime executes configured repository-native checks fresh after review/fix activity.

Supported categories remain:

- BUILD
- STATIC
- LINT
- TYPECHECK
- UNIT
- COMPONENT
- MODULE_LOCAL_INTEGRATION

Capture for each check:

- name
- category
- argv
- exit code
- PASS/FAIL
- evidence ref

Evidence must be bound to:

- exact technical snapshot
- exact implementation repository revisions

Do not classify system/browser/golden-journey/tester acceptance as Dev engineering verification.

Failing required checks block READY_FOR_TEST.

---

# 18. Repository revision observation

The runtime host must observe exact repository revisions.

For each implementation repository:

- record base revision at intake;
- verify base revision before IMPLEMENTATION_READY/source mutation;
- record exact final revision for handoff.

Cross-repository feature delivery:

- automatically HIGH_RISK;
- every repository has exact base revision;
- every repository has explicit allowed write paths;
- every implementation repository has exact final revision.

Do not let repository id/path ambiguity pass.

---

# 19. Requirements coverage runtime

At finalization, construct/validate exact coverage rows for the approved BA coverage set.

Only:

- BR-*
- FR-*

Every required ID must be COVERED.

Each coverage row requires:

- code refs
- test refs

No BAREF.

No invented requirement IDs.

No partial/incomplete feature coverage at READY_FOR_TEST.

---

# 20. Dev Handoff runtime

VERIFYING
→ READY_FOR_TEST

must call canonical make_handoff()/validate_handoff().

Runtime writes Dev Handoff VNext only after:

- upstream still valid;
- no unresolved gap;
- exact base/write-scope integrity;
- required technical gate valid;
- exact implementation revisions;
- bounded review complete;
- fresh engineering checks pass;
- FR/BR coverage complete.

Do not hand-build a second VNext handoff implementation in dev_kit.py.

---

# 21. V1 compatibility

Existing V1 commands/artifacts may remain available for explicit legacy inspection.

New runs default to VNext.

Rules:

- V1 handoff cannot authorize VNext feature delivery;
- V1 runtime cannot be silently resumed as VNext;
- V1 status strings do not create VNext lifecycle states;
- no V1 Human gate data can fabricate VNext technical receipt.

Clearly mark legacy runtime output as LEGACY_COMPAT where surfaced.

---

# 22. CLI

Provide a coherent VNext CLI surface using existing project style.

Exact command names may follow current conventions, but required capabilities should cover equivalent operations:

- start
- validate authority
- impact
- raise-gap
- resume-gap
- plan
- bind-technical-approval
- implementation-ready
- authorize-write / implementation guard
- review
- verify
- finalize / handoff
- status
- validate artifact

Avoid a giant number of thin commands if one structured command family is clearer.

CLI must not generate trusted Human receipts.

---

# 23. Neutral runtime acceptance

Add neutral synthetic runtime acceptance.

## NORMAL

Engineering Handoff VNext
→ start
→ authority
→ impact
→ plan
→ implementation ready
→ implementation evidence
→ full review
→ verification
→ READY_FOR_TEST

Assert BA bytes unchanged.

## HIGH_RISK

Use one material category such as PUBLIC_API.

Assert:

- implementation blocked before exact authenticated technical approval;
- Spec Kit approve choice alone fails;
- exact receipt succeeds;
- drift invalidates approval.

## GAP

Assert:

- exact gap artifact;
- transition to UPSTREAM_GAP;
- source mutation blocked;
- replacement Handoff VNext required;
- stale plan/gate discarded;
- resumed run re-enters AUTHORITY_VALIDATED.

## MULTI_REPO

Assert:

- HIGH_RISK;
- exact base revisions;
- explicit write scopes;
- exact output revisions.

## MAINTENANCE

Assert:

- no BA Handoff needed;
- TRIVIAL fast path works;
- behavior/security/public-contract/cross-repo discovery blocks and requires FEATURE_DELIVERY.

---

# 24. Persistence / crash-resume acceptance

Add deterministic tests proving persisted V2 state can be reloaded safely.

Must reject:

- truncated/invalid state;
- modified lifecycle without matching history;
- changed artifact refs;
- changed upstream;
- changed repository scope;
- stale technical receipt;
- unsupported schema version.

Resume must not depend on in-memory session context.

---

# 25. Tests

Before Wave 2 changes record baseline at:

42e4e974b30d16a445e5aa236698009cce8d2f0c

Run at least:

- tooling.tests.test_dev_vnext
- tooling.tests.test_dev_kit
- BA VNext tests
- Project Foundation tests
- Shared SDLC acceptance/contracts
- full tooling unittest discovery

After changes run:

- all above;
- new runtime orchestration tests;
- Spec Kit adapter tests;
- persistence/crash-resume tests;
- neutral normal/high-risk/gap/multi-repo/maintenance acceptance;
- git diff --check.

Expected: 0 failures / 0 errors.

Do not weaken Wave 1 tests.

---

# 26. Structure guard

Wave 1 dev_vnext.py is already a large semantic module.

Wave 2 MUST NOT put workflow persistence, process execution, Spec Kit orchestration and CLI command bodies into that file.

Use a runtime/orchestrator module.

Prefer reuse of canonical helpers over duplicate near-copies.

Do not refactor Wave 1 contracts for style unless required for correctness.

---

# 27. Genericity

Production/runtime tests must not hard-code:

- Digital Wedding
- PetClinic
- Appointment
- CR-DWC-*
- user-specific paths/names

Use neutral synthetic repositories/features.

---

# 28. Wave 2 non-goals

Do NOT:

- modify Delivery Manifest V2;
- implement Delivery Manifest VNext adapters;
- migrate Test Kit;
- implement system automation;
- implement final defect/retest lifecycle;
- make Dev final verifier;
- perform full installer/package/provenance migration;
- publish stable release;
- touch Digital Wedding repositories;
- merge to main.

---

# 29. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_5_WAVE_2_DEV_KIT_VNEXT_RUNTIME_SPEC.md

Do not copy or rename it elsewhere.

Final Wave 2 tree must not contain it.

---

# 30. Required report

PHASE_5_WAVE_2_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/dev-kit-vnext-wave2

BASE:
42e4e974b30d16a445e5aa236698009cce8d2f0c

HEAD:
<exact SHA>

RUNTIME_ARCHITECTURE:
<modules/adapters>

V2_DEFAULT_ROUTING:
<new-run behavior>

PERSISTENCE:
<state layout + crash/resume>

AUTHORITY_REVALIDATION:
<BA/Foundation exact proof>

IMPACT_AND_GAP:
<runtime flow>

PLANNING_AND_SNAPSHOT:
<binding>

SPEC_KIT_INTEGRATION:
<workflow-only proof>

TECHNICAL_GATE:
<authenticated exact binding>

SOURCE_MUTATION_GUARD:
<base/write-scope enforcement>

RISK_REPLAN:
<escalation behavior>

ENGINEERING_REVIEW:
<bounded integration>

FRESH_VERIFICATION:
<repository-native evidence>

MULTI_REPO:
<exact revisions/scopes>

REQUIREMENTS_COVERAGE:
<FR/BR>

DEV_HANDOFF:
<READY_FOR_TEST>

DELIVERY_MANIFEST:
DEFERRED_NON_AUTHORITATIVE

LEGACY_COMPAT:
<V1 status>

SYNTHETIC_RUNTIME_ACCEPTANCE:
<normal/high-risk/gap/multi-repo/maintenance>

TESTS:
<commands + pass/fail/skip>

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
feat/dev-kit-vnext-wave2

RECOMMENDED_WAVE_3:
<packaging/docs/fresh-install tasks>

If runtime work requires changing frozen Wave 1/BA/Foundation/Shared contracts, STOP with:

ARCHITECTURE_DECISION_REQUIRED
and describe the exact decision instead of changing it silently.
