# PHASE 6 — TEST KIT MANUAL VNEXT — WAVE 2 COMPLETION SPEC

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills

Wave 1 behavioral base:
0ca448187c164597ab1ecc2707b31b65cca53608

Phase 6 semantic base:
ec9955f7c26cd69e2a83d56dfbfba02fb55abc44

Target implementation branch:
feat/test-kit-manual-vnext-wave2

Recommended model:
GPT-6 Luna Extra High while SOL High is unavailable.

This is the final large Phase 6 wave.

It intentionally combines:
1. mandatory independent-review remediation from Wave 1;
2. package/installer/Doctor completion;
3. docs and neutral example migration;
4. fresh installed-runtime acceptance;
5. final Phase 6 readiness verification.

Do not split this into another manual remediation round unless an architecture stop condition is reached.

---

# 1. Phase 6 terminal goal

At completion, Test Kit Manual VNext must be a production-quality prerelease package whose default manual flow is:

Engineering Handoff VNext
→ Canonical Test Design
→ Human Design Gate
→ APPROVED_DESIGN
→ Canonical Testcases
→ Human Case Gate
→ APPROVED_TESTWARE

APPROVED_TESTWARE is terminal for the Phase 6 manual lane.

It is NOT:
- EXECUTION_READY;
- test execution PASS;
- VERIFIED;
- READY_TO_MERGE.

Automation planning and execution begin only in Phase 7.

---

# 2. Frozen Wave 1 architecture

Do not redesign these contracts:

- BA Engineering Handoff VNext is required business WHAT authority.
- Canonical business trace is BR-* / FR-* only.
- BAREF is locator/provenance only.
- Test Design canonical semantic shape is preserved.
- Testcase canonical semantic shape is preserved.
- Human Design Gate binds exact snapshot/input refs.
- Human Case Gate binds exact snapshot/input refs.
- TEA is analysis/advisory/raw evidence only.
- Katalon create-test-cases is generator/raw evidence only.
- Project Test Policy is non-authoritative guidance.
- UX is optional unless explicitly required.
- UX prototype is REVIEW_EVIDENCE only.
- Dev Handoff V2 is optional technical/execution context only.
- Dev implementation is not business WHAT.
- XMind is a DERIVED projection from APPROVED_DESIGN.
- Excel is a DERIVED projection from APPROVED_TESTWARE.
- V1 remains LEGACY_COMPAT and cannot provide VNext authority.
- Delivery Manifest remains DEFERRED_NON_AUTHORITATIVE.
- APPROVED_TESTWARE is the terminal VNext manual-test state.
- There is no STOP_VNEXT.

If packaging or remediation requires changing one of these, STOP:

ARCHITECTURE_DECISION_REQUIRED

---

# 3. Independent-review result from Wave 1

Wave 1 implementation is broadly correct, but independent review identified two semantic correctness issues and one hygiene issue.

They MUST be fixed before packaging is considered complete.

## R1 — Remove heuristic UX authority inference

Current Wave 1 runtime uses English lexical heuristics such as:

button
control
screen
page
field
input
visible
hidden
enabled
disabled
...

to infer whether a Design/Case assertion requires UX authority.

It also uses token-subset comparison against free-form UX contract text to determine whether an assertion is supported.

This is not production-safe.

Examples of false behavior:

- an API response "field" may incorrectly require UX;
- an input payload may incorrectly require UX;
- a valid testcase may include business wording not repeated verbatim in UX markdown and be rejected;
- free-form prose token overlap is not a trustworthy authority validator.

Required remediation:

1. Do NOT infer a mandatory authority requirement from generic lexical keyword detection.
2. Do NOT use free-text token-subset matching as a blocking semantic proof.
3. Do NOT use opposite-word lexical heuristics as a blocking BA/UX contradiction detector.
4. UX authority becomes mandatory only when the VNext authority context explicitly records:
   ux_required = true
   OR a caller explicitly supplies approved UX context for a flow that consumes it.
5. If ux_required=true:
   - exact approved UX context is required;
   - exact UX contract/receipt/source bytes must validate;
   - trusted Human authentication is required;
   - stale UX input must fail closed;
   - gate input refs bind exact UX refs.
6. If UX context is supplied while ux_required=false:
   - it may be bound as consumed approved context;
   - stale/invalid context still fails closed;
   - it does not automatically turn unrelated fields into UX assertions.
7. Free-form semantic consistency between BA/UX/Test remains a Human review responsibility unless an exact structured source mapping exists.
8. If a deterministic structured contradiction is available, it may fail closed.
9. Do not claim general semantic-equivalence checking over arbitrary markdown text.

The Test framework must remain strict about authority identity and bytes, not pretend to solve natural-language entailment deterministically.

Add regressions proving:

- "API response field" does not require UX when ux_required=false;
- "input payload" does not require UX when ux_required=false;
- a no-UX feature with ordinary words such as page/field/input does not fail merely because of vocabulary;
- ux_required=true without approved UX fails;
- ux_required=true with exact approved UX passes authority validation;
- stale UX bytes fail;
- prototype-only UX fails;
- unauthenticated UX approval fails.

Delete or downgrade the lexical heuristic functions so they cannot block production VNext approval.

---

## R2 — VNext helper must never fall back to legacy BA parsing

Current VNext helper:

design_gate_input_refs(run_dir, baseline=None)

can fall back to legacy:

load_approved_baseline(vnext_handoff_path)

when baseline is omitted.

That is architecturally wrong for a VNext API.

Required remediation:

- no VNext public/helper path may silently parse a VNext Engineering Handoff using the legacy ApprovedBaseline reader;
- either require an explicit already-revalidated VNext authority/baseline argument;
- or provide a correctly authenticated VNext revalidation path with the required callbacks.

Because this helper has no authenticators today, the preferred lean fix is:

- require a baseline/authority argument;
- fail clearly if omitted;
- update all internal callers.

Do not add unauthenticated VNext authority reconstruction.

Add a regression proving omission cannot silently fall back to V1.

---

## R3 — Baseline report hygiene

Wave 1 added:

PHASE_6_WAVE1_BASELINE.md

at repository root.

This is useful evidence but should not remain as a root-level product artifact.

Either:

A. move it to a clearly historical/benchmark evidence location such as:
benchmark/test-kit/vnext/phase6-wave1-baseline.md

or:

B. remove it after its information is captured in durable acceptance/review evidence.

Do not leave temporary implementation evidence at repository root.

---

# 4. Delivery Manifest rule

Delivery Manifest remains:

DEFERRED_NON_AUTHORITATIVE

Wave 2 must NOT:

- modify Delivery Manifest V2 semantics;
- create Delivery Manifest V3;
- make Delivery Manifest required for Test VNext;
- use Delivery Manifest as BA authorization;
- use Delivery Manifest as UX authorization.

The current Test VNext module may temporarily reuse generic parser/constants from the existing module only if no Delivery Manifest authority/loading path is invoked.

Preferred cleanup if simple:
- move/copy only generic UX constants/parser to a neutral helper or local Test adapter.

But do not broaden this into Shared Core refactoring.

No Wave 2 completion test may require a Delivery Manifest.

---

# 5. Versioning

Current Test package version at Wave 1:

2.0.0-rc.5

Wave 2 must advance the prerelease package version.

Preferred:

2.0.0-rc.6

unless existing repository-owned release tooling/policy requires another prerelease version.

Do not publish stable 2.0.0.

All version surfaces must agree:

- kits/test/kit.yaml;
- package authority;
- install record expectations;
- Doctor output where applicable;
- docs that state the current package candidate;
- acceptance assertions.

Historical docs may retain historical version references when clearly labeled history.

---

# 6. Package identity

Default Test Kit package identity must describe VNext.

Do not default to:

- Test Kit V1;
- Test Kit V1.1;
- Approved BA Baseline as direct authority;
- STOP_V1.

Default VNext authority statement:

Business WHAT:
Engineering Handoff VNext backed by exact Human-approved BA baseline proof.

Optional UX:
exact approved UX context when explicitly required/consumed.

Optional technical context:
exact Dev/execution evidence, never business WHAT.

Canonical outputs:
- Canonical Test Design;
- Canonical Testcases;
- Approved Testware VNext HANDOFF_MANIFEST.

Manual terminal:
APPROVED_TESTWARE.

V1 must be described explicitly as LEGACY_COMPAT.

---

# 7. Kit manifest

Update:

kits/test/kit.yaml

to accurately describe/package VNext.

Required package closure includes all runtime dependencies needed by Test VNext, including as applicable:

- tooling/lib/test_kit_vnext.py
- tooling/lib/test_kit_v1.py
- tooling/lib/test_kit_v1_cases.py
- tooling/lib/test_kit_policy.py
- XMind/Excel optional runtime modules
- canonical BA VNext reader dependencies
- Dev VNext reader dependencies used for optional technical context
- Shared SDLC modules required transitively
- pinned TEA skill
- pinned Katalon create-test-cases skill
- package authority
- schemas/templates/examples/docs shipped by package
- licenses/provenance/notices.

Do not include benchmark fixtures in production payload.

Keep XMind and Excel optional capabilities.

Core readiness must not require Node/openpyxl.

---

# 8. Package authority and integrity

Regenerate Test package authority and payload digests with repository-owned tooling.

Must prove:

- source package integrity;
- package authority integrity;
- managed-file count matches;
- every managed file hash matches installed bytes;
- payload tree hash matches;
- repeated clean installs produce identical package authority/tree;
- VNext runtime files are included;
- V1 compatibility files promised by docs remain included.

Do not manually edit hashes as a shortcut.

---

# 9. Installer and uninstall

Preserve existing project-scope installer behavior.

Required:

- idempotent install;
- unrelated project files preserved;
- project-owned TEA config preserved;
- safe-path protections remain;
- package drift detected;
- reinstall does not silently overwrite locally modified managed files;
- uninstall removes only files still owned/matching expected package bytes;
- optional dependencies are not silently downloaded;
- BA and Test Kits can coexist.

No new general package manager is needed.

---

# 10. Doctor

Doctor must validate Test VNext capability closure.

Doctor core checks should include at least:

- Test package manifest integrity;
- package authority integrity;
- installed managed-file hashes;
- test_kit_vnext importability;
- BA VNext dependency closure;
- Dev VNext dependency closure used for optional technical context;
- Shared SDLC dependency closure;
- pinned TEA integrity;
- pinned Katalon integrity;
- project TEA config validity;
- VNext schemas/templates/examples required by the package;
- V1 LEGACY_COMPAT artifacts promised by the package;
- license/provenance/notice closure.

Doctor statuses:

READY
= core package/capability ready.

DEGRADED
= optional capability unavailable, e.g. XMind/Excel dependency missing.

FAIL
= required package/capability/integrity broken.

Doctor READY must NOT imply:

- BA approval;
- APPROVED_DESIGN;
- APPROVED_TESTWARE;
- EXECUTION_READY;
- execution PASS;
- VERIFIED;
- READY_TO_MERGE.

Add a direct regression proving this distinction.

---

# 11. Acceptance contract

Create:

kits/test/acceptance.yaml

Use the same maturity pattern as BA/Dev acceptance where useful.

## Tier 1 — deterministic

Run for every Test Kit change:

- core Test V1 compatibility suites;
- Test VNext semantic/runtime suites;
- project-policy suites;
- packaging suites;
- XMind/Excel structural/core suites where dependencies available;
- BA VNext dependency tests;
- Dev VNext dependency tests;
- Shared SDLC contract tests.

## Tier 2 — focused Test VNext runtime

Must cover:

- exact BA VNext Human authority;
- FR/BR-only trace;
- BAREF rejection;
- Design exact Human Gate;
- Case exact Human Gate;
- no self-approval;
- UNKNOWN/deferred behavior;
- explicit UX-required behavior;
- no lexical UX inference;
- UX stale/unauthenticated/prototype-only negatives;
- optional Dev technical context;
- Dev context cannot redefine WHAT;
- execution dependency fail-closed behavior;
- request-changes/new revision;
- persistence/resume;
- XMind derived boundary;
- Excel derived boundary;
- APPROVED_TESTWARE handoff manifest;
- Delivery Manifest not required/non-authoritative;
- V1 LEGACY_COMPAT.

## Tier 3 — fresh installed runtime

Mandatory for Phase 6 completion.

Tier 1/2 alone must not claim Phase 6 complete.

---

# 12. VNext schemas

Add explicit packaged VNext schemas where they materially help team usage and validation.

At minimum consider:

- Test authority context VNext;
- UX context request/binding if no existing schema covers the Test adapter;
- Approved Testware VNext HANDOFF_MANIFEST;
- Design Gate receipt if not already represented by executable contract/schema;
- Case Gate receipt if not already represented;
- Test VNext run-state/operator request surfaces if they are user-facing.

Do not create schema copies merely for documentation aesthetics.

Schemas must mirror executable contracts.

Add drift tests for key invariant surfaces.

V1 schemas/artifacts remain compatibility only.

---

# 13. VNext templates

Provide small neutral templates/examples only for surfaces an operator may reasonably author.

Do not create a fake Human approval receipt that can be used as production authority.

Any approval example must be clearly:

- illustrative;
- synthetic;
- non-production.

Do not duplicate generated canonical artifacts as huge templates.

---

# 14. Public neutral example

Default public Test VNext example must be neutral.

Create or replace default guidance with a synthetic feature that demonstrates:

Engineering Handoff VNext
→ Design
→ Human Design Gate
→ Cases
→ Human Case Gate
→ APPROVED_TESTWARE

Do not use default operational semantics from:

- Digital Wedding;
- CR-DWC-*;
- PetClinic;
- Appointment;
- user/company-specific paths.

Historical PetClinic benchmark fixtures may remain under benchmark/test-kit/ and must be labeled historical/benchmark.

Existing CR-001 example may either:
- move to a legacy/historical area;
- be clearly labeled V1 LEGACY_COMPAT;
- or be replaced by a neutral VNext example.

Default README/Quick Start should point to the neutral VNext example.

---

# 15. Documentation migration

Update current operational docs so the default path is VNext.

Required review/update surfaces include:

- kits/test/README.md
- kits/test/skills/test-kit/SKILL.md
- docs/vi/TEST_KIT_QUICKSTART.md
- docs/vi/TEST_KIT_CAPABILITIES.md
- docs/vi/TEST_KIT_USAGE_GUIDE.md
- docs/vi/TEST_KIT_WORKFLOW.md
- docs/vi/TEST_KIT_CUSTOMIZATION.md where authority wording is stale
- docs/vi/RELEASE.md
- docs/en/TEST_KIT_README.md
- docs/en/RELEASE.md if current convention maintains parity
- docs/vi/INSTALLATION.md only where Test Kit commands/semantics changed
- provenance documentation if package identity changed.

Default docs must teach:

- Engineering Handoff VNext;
- BR/FR-only trace;
- optional explicit approved UX context;
- optional Dev/execution context;
- Design Human Gate;
- Case Human Gate;
- APPROVED_TESTWARE terminal;
- XMind/Excel derived-only;
- Test Policy non-authoritative;
- V1 LEGACY_COMPAT;
- Delivery Manifest not required;
- automation/execution deferred to Phase 7+.

Remove stale default instructions such as:

- "Approved BA Baseline" as the production VNext direct input;
- ba_baseline.status=APPROVED_FOR_ENGINEERING;
- STOP_V1 as VNext terminal;
- "same approved Delivery Manifest as Dev" as required Test VNext authority;
- CR-DWC demo wording in generic operator guidance.

Historical sections may keep old wording when explicitly labeled history.

---

# 16. Fresh installed-runtime acceptance

Add a dedicated installed Test VNext acceptance test analogous in rigor to BA/Dev installed acceptance.

The test must install Test Kit into a clean temporary project-scoped target.

It must execute outside the source checkout as much as the existing installer architecture permits.

It must prove installed modules resolve from the installed Test package, not from the agent-skills source checkout.

Use isolated Python semantics where practical:

python -I

Remove PYTHONPATH from the test environment.

If project-local package loading needs an explicit installed root bootstrap, that bootstrap must point only to the installed target.

Do not let source checkout accidentally satisfy imports.

## Required installed flow

1. create clean temporary project;
2. install Test Kit;
3. run Doctor;
4. assert READY or appropriate core-ready status;
5. prepare a neutral BA Engineering Handoff VNext fixture under the synthetic test host;
6. trusted synthetic BA Human authenticator validates exact BA approval;
7. start a VNext Test Design run;
8. execute the installed TEA operator path or a fully pinned deterministic installed acceptance fixture consistent with production runtime;
9. finalize to DESIGN_REVIEW;
10. prove validator PASS does not approve;
11. apply synthetic authenticated Human Design approval;
12. reach APPROVED_DESIGN;
13. create/finalize Testcases through installed runtime;
14. reach CASE_REVIEW;
15. prove validator PASS does not approve;
16. apply synthetic authenticated Human Case approval;
17. reach APPROVED_TESTWARE;
18. re-read/revalidate Approved Testware VNext HANDOFF_MANIFEST;
19. assert BR/FR-only trace;
20. assert no BAREF;
21. assert APPROVED_TESTWARE != EXECUTION_READY/VERIFIED;
22. run Doctor again;
23. inspect a legacy V1 fixture and prove LEGACY_COMPAT/vnext_authority=false.

Use explicit TEST_ONLY / not_for_production identity for synthetic Human fixtures where the installed acceptance is not using the production host interface.

Do not claim synthetic fixture approval is real project approval.

---

# 17. Installed UX acceptance

Fresh-install acceptance does not need a full UI prototype workflow, but must include focused installed tests proving:

- ux_required=false can complete without UX;
- ux_required=false is not triggered by words like "field", "input", "page";
- ux_required=true with no approved UX fails;
- ux_required=true with exact approved UX proof proceeds;
- prototype-only fails;
- stale UX proof fails;
- unauthenticated UX approval fails.

This specifically guards R1.

---

# 18. Installed optional capabilities

Core Test Kit must remain usable without XMind/Excel dependencies.

Fresh installed acceptance should prove:

- missing optional Node/npm/xmind dependency does not invalidate core Test VNext;
- missing optional openpyxl does not invalidate core Test VNext;
- Doctor reports optional capability unavailability accurately;
- when optional dependencies are available, XMind/Excel projection smoke works from exact approved VNext artifacts.

Do not install external dependencies from the network automatically during Test Kit install.

---

# 19. Legacy compatibility

V1 must remain explicitly inspectable.

Required behavior:

mode = LEGACY_COMPAT
vnext_authority = false

Legacy V1 Design/Case/Testware cannot silently become VNext approval.

No migration utility may fabricate:

- BA VNext approval;
- UX Human approval;
- Design approval;
- Case approval;
- execution oracle approval.

Keep legacy tests green.

---

# 20. Genericity scan

Scan Test-owned production/package/operator surfaces.

No default production guidance/example may hard-code:

- Digital Wedding;
- CR-DWC-*;
- PetClinic;
- Appointment;
- local username paths;
- machine-specific absolute paths.

Historical benchmark docs/fixtures may contain PetClinic/Appointment when clearly under benchmark/history.

Do not broaden the cleanup to unrelated BA/Dev history.

---

# 21. Full regression

Before Wave 2 changes record the Wave 1 head:

0ca448187c164597ab1ecc2707b31b65cca53608

Run focused baseline from that exact commit before remediation if practical.

After changes run at least:

- tooling.tests.test_test_kit_vnext
- tooling.tests.test_test_kit_v1
- tooling.tests.test_test_kit_v1_case_gate
- tooling.tests.test_test_kit_v1_cases
- tooling.tests.test_test_kit_policy
- tooling.tests.test_test_kit_policy_doctor
- tooling.tests.test_test_kit_customization
- tooling.tests.test_test_kit_customization_excel
- tooling.tests.test_test_kit_v1_xmind
- tooling.tests.test_test_kit_v1_excel
- tooling.tests.test_kit_packaging
- new installed Test VNext acceptance
- BA VNext tests
- Dev VNext tests
- BA installed acceptance
- Dev installed acceptance where package changes can affect shared tooling
- Project Foundation tests
- Shared SDLC contract/acceptance tests
- full tooling unittest discovery
- git diff --check.

Expected final state:
0 new failures/errors.

If the two Dev payload-digest baseline failures reappear, determine whether current Test packaging changes actually caused them.
Do not hide them.

Do not weaken assertions.

---

# 22. Wave 2 hygiene

Do not leave temporary bootstrap specs in final implementation tree.

Before final commit delete:

PHASE_6_WAVE_2_TEST_KIT_VNEXT_COMPLETION_SPEC.md

Do not copy/rename it elsewhere.

Final implementation branch must not contain:
- Phase 6 temporary execution spec;
- root-level Wave 1 baseline temporary report;
- scratch acceptance files;
- local dependency directories such as node_modules;
- generated caches.

Durable historical baseline evidence may live under benchmark/test-kit/vnext/ if intentionally retained.

---

# 23. Forbidden work

Do NOT implement:

- Automation Suitability;
- Automation Plan;
- AUT-*;
- automation repository implementation;
- browser/API production automation;
- test execution framework;
- execution PASS/FAIL lifecycle;
- defect workflow;
- Dev fix/retest;
- VERIFIED lifecycle;
- Digital Wedding migration;
- Phase 7 work;
- stable OSS release;
- Delivery Manifest redesign.

Do not merge to main.

---

# 24. Phase 6 completion acceptance

Wave 2 must prove all of these together:

- BA VNext exact Human-approved authority;
- FR/BR-only canonical trace;
- BAREF rejected;
- Design exact Human Gate;
- Case exact Human Gate;
- no self-approval;
- explicit UX requirement only, no lexical authority inference;
- UX exact proof/revalidation;
- optional Dev technical context does not redefine WHAT;
- UNKNOWN remains UNKNOWN;
- required unresolved execution dependencies block Case approval;
- APPROVED_TESTWARE VNext HANDOFF_MANIFEST exact refs;
- APPROVED_TESTWARE terminal;
- XMind/Excel derived-only;
- project Test Policy non-authoritative;
- V1 LEGACY_COMPAT;
- Delivery Manifest not required;
- Doctor package/capability semantics;
- clean install;
- installed isolation;
- neutral public example;
- package integrity;
- full regression PASS.

Only then recommend:

PHASE_6_VERIFIED_COMPLETE

---

# 25. Branch workflow

Source bootstrap branch:

phase6/test-kit-manual-vnext-wave2-bootstrap

Expected source behavioral commit:

0ca448187c164597ab1ecc2707b31b65cca53608

Implementation branch:

feat/test-kit-manual-vnext-wave2

Steps:

1. git fetch origin;
2. verify bootstrap branch contains this spec and descends from exact Wave 1 HEAD;
3. create implementation branch from latest bootstrap commit;
4. record behavioral base as 0ca448187c164597ab1ecc2707b31b65cca53608;
5. implement mandatory remediation first;
6. run focused remediation tests;
7. continue packaging/fresh-install completion in the same session/branch;
8. delete temporary spec;
9. commit all final changes;
10. push branch;
11. do not merge;
12. worktree clean.

---

# 26. Required final report

PHASE_6_WAVE_2_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/test-kit-manual-vnext-wave2

BASE:
0ca448187c164597ab1ecc2707b31b65cca53608

HEAD:
<exact SHA>

WAVE1_REVIEW_REMEDIATION:
<R1/R2/R3 status>

UX_AUTHORITY_RULE:
<explicit UX behavior; no lexical blocking>

VNEXT_HELPER_AUTHORITY:
<proof no legacy fallback>

KIT_VERSION:
<prerelease version>

KIT_MANIFEST:
<VNext default package identity>

PACKAGE_AUTHORITY:
<hash/provenance status>

INSTALLER:
<idempotent/safe behavior>

UNINSTALL:
<ownership behavior>

DOCTOR:
<READY/DEGRADED/FAIL semantics>

ACCEPTANCE_CONTRACT:
<Tier 1/2/3>

SCHEMAS_TEMPLATES:
<VNext public contract surfaces>

DOCS:
<updated operational docs>

PUBLIC_EXAMPLE:
<neutral VNext example>

FRESH_INSTALL_ACCEPTANCE:
<full installed manual flow>

INSTALLED_ISOLATION:
<source-checkout isolation proof>

INSTALLED_UX_ACCEPTANCE:
<explicit ux_required tests>

OPTIONAL_PROJECTIONS:
<XMind/Excel core-optional behavior>

LEGACY_COMPAT:
<V1 compatibility>

DELIVERY_MANIFEST:
DEFERRED_NON_AUTHORITATIVE

GENERICITY:
<scan result>

TESTS:
<commands/results>

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
feat/test-kit-manual-vnext-wave2

WORKTREE:
CLEAN

RECOMMENDED_PHASE_6_STATUS:
VERIFIED_COMPLETE | NOT_READY

If a frozen architecture change is required, STOP:

ARCHITECTURE_DECISION_REQUIRED
