# Phase 5 — Wave 3 Implementation Spec
## Dev Kit VNext Packaging, Installation, Doctor, Documentation and Fresh-Install Acceptance

Status: READY_FOR_AGENT_EXECUTION
Required model: LUNA Medium
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: 0e0e317764b1b36dcc3ddd5df045419e1ea0bf2b
Source branch: fix/dev-vnext-repository-scoped-checks-v1
Suggested implementation branch: feat/dev-kit-vnext-wave3

TEMPORARY BOOTSTRAP ARTIFACT:
This file exists only so a fresh implementation session can fetch the exact approved Wave 3 scope.
Create the Wave 3 branch from the latest remote source branch containing this file, read it fully, implement Wave 3 only, then DELETE this file before final commit/report.
The final Wave 3 tree must not contain this bootstrap spec.

---

# 1. Goal

Complete Phase 5 by making Dev Kit VNext a coherent installable package for team use.

Behavioral semantics are frozen at:

0e0e317764b1b36dcc3ddd5df045419e1ea0bf2b

Wave 3 is mechanical integration.

Required outcomes:

1. Dev Kit package metadata describes VNext, not V1.
2. VNext schemas/templates are packaged and discoverable.
3. Existing V1 schemas/templates remain clearly LEGACY_COMPAT.
4. installer installs a complete VNext runtime without source-checkout imports.
5. installed CLI/Doctor can run from a clean external project.
6. Doctor verifies VNext capability closure only; READY does not imply feature approval.
7. package/provenance metadata is regenerated consistently.
8. acceptance contract has deterministic, runtime and fresh-install tiers.
9. public docs describe the real VNext workflow.
10. neutral examples do not teach project-specific semantics.
11. fresh-install acceptance proves a complete installed VNext feature flow.
12. full repository regression remains green.

Do not redesign any Wave 1/Wave 2 semantic contract.

---

# 2. Frozen semantics

Do NOT change:

- FEATURE_DELIVERY / TECHNICAL_MAINTENANCE;
- Dev lifecycle V2;
- Engineering Impact V2;
- Engineering Gap;
- ED-* Engineering Decisions;
- exact Human/Tech Lead technical approval;
- repository-scoped engineering checks;
- FR/BR-only coverage;
- READY_FOR_TEST semantics;
- Spec Kit boundary;
- Delivery Manifest deferred/non-authoritative rule;
- BA/Foundation/Shared Core contracts.

If packaging work requires changing any of these, STOP:

ARCHITECTURE_DECISION_REQUIRED

---

# 3. Package identity

Update Dev Kit package metadata so it reflects VNext.

Current V1-oriented values that must be removed or corrected include concepts such as:

- "Dev Kit V1 — Foundation";
- business authority = "Approved BA Baseline";
- runtime root = ~/.devkit/runtime/v1;
- V1-only output descriptions;
- V1-only run-state descriptions.

Target package authority statement:

Business WHAT authority:
Engineering Handoff VNext backed by exact APPROVED_BASELINE proof.

Engineering authority:
Engineering Impact + ED-* + exact technical snapshot/approval where required.

Terminal Dev readiness:
READY_FOR_TEST.

Do not claim VERIFIED or final business/system acceptance.

Do not publish a stable release.

If a prerelease version bump is required, use the repository's existing RC convention consistently.
Do not invent a stable 1.0 release.

---

# 4. Runtime installation layout

Install VNext into a versioned runtime directory separate from historical V1.

Preferred target:

~/.devkit/runtime/v2

Installed launcher:

~/.devkit/bin/devkit

Launcher must point to the V2 runtime after successful VNext install.

Install manifest should clearly identify:

- schema_version;
- runtime = dev-kit-v2;
- kit version;
- exact installed files/hashes;
- Python executable;
- launcher.

Do not delete an existing runtime/v1 during VNext installation.

V1 may remain for historical inspection/rollback.

The new V2 install must not depend on files from runtime/v1.

---

# 5. Installed runtime closure

Ensure the V2 installer includes all dependencies needed by Dev VNext.

At minimum inspect and include:

- tooling/lib/dev_kit.py
- tooling/lib/dev_router.py
- tooling/lib/dev_vnext.py
- tooling/lib/dev_vnext_runtime.py
- tooling/lib/dev_vnext_cli.py
- tooling/lib/dev_vnext_spec_kit.py
- BA VNext canonical reader dependencies
- Shared SDLC modules needed transitively
- Project Foundation proof dependencies
- Dev plugin/workflows
- Dev skill router
- VNext schemas/templates
- V1 compatibility schemas/templates/readers where promised
- provenance/notice/license assets

Installed VNext must not import modules from the repository checkout.

Test with:

- python -I
- PYTHONPATH removed
- CWD outside source checkout

Where practical, assert imported module paths are under installed runtime/v2.

---

# 6. Schemas

Do not overwrite V1 schema_version 1 files with incompatible V2 semantics.

Preserve current V1 schemas as LEGACY_COMPAT.

Add explicit VNext schemas, for example:

kits/dev/schemas/start-request-v2.schema.json
kits/dev/schemas/engineering-impact-v2.schema.json
kits/dev/schemas/engineering-gap-v2.schema.json
kits/dev/schemas/engineering-decision-v2.schema.json
kits/dev/schemas/dev-state-v2.schema.json
kits/dev/schemas/technical-approval-v2.schema.json
kits/dev/schemas/dev-handoff-v2.schema.json

Exact filenames may follow repository conventions.

Schemas should mirror executable contracts rather than create a second source of truth.

Add a test that detects schema/contract drift for key invariants.

At minimum schema surfaces must reflect:

- repository-scoped checks;
- authority modes;
- lifecycle values;
- exact refs;
- HANDOFF_MANIFEST V2;
- READY_FOR_TEST only;
- no BAREF coverage;
- ED-* identity;
- Human/Tech Lead receipt shape.

---

# 7. Templates

Add neutral VNext templates for team use.

Minimum:

- start request V2;
- Engineering Impact V2;
- Engineering Gap V2;
- Engineering Decision V2;
- technical Human approval receipt example/template boundary;
- Dev Handoff V2 shape or safe non-authoritative example.

Important:

- receipt template MUST NOT be a usable fake approval;
- host authentication is external;
- examples must clearly say synthetic/example-only where relevant;
- no template may contain status text that fabricates approval.

Preserve V1 templates under explicit LEGACY_COMPAT naming/location.

Default docs/CLI should point users to V2 templates.

---

# 8. CLI schema/template discovery

Update Dev CLI schema/template commands so VNext is the default discoverable contract.

Users should be able to inspect V2 contract surfaces without opening source code.

Legacy V1 inspection remains available explicitly.

Do not make ambiguous commands return V1 by default after Phase 5.

Example intent:

devkit schema start-request
→ V2 default

devkit schema legacy/start-request
→ V1

Exact command UX may follow existing conventions.

---

# 9. Doctor

Extend Dev Doctor to verify VNext installed capability closure.

Doctor must check at least:

- installed runtime is V2;
- dev_vnext semantic module exists/imports;
- dev_vnext_runtime exists/imports;
- dev_vnext_cli exists/imports;
- dev_vnext_spec_kit exists/imports;
- BA VNext canonical reader is installed;
- required Shared SDLC modules resolve;
- Project Foundation proof dependencies resolve;
- VNext schemas/templates exist;
- V1 compatibility artifacts exist where promised;
- Spec Kit pin remains 1.0.11;
- forbidden Spec Kit feature-spec commands remain excluded;
- plugin/core/conditional skills resolve;
- provenance/notice/license closure is valid.

Doctor output must distinguish:

PACKAGE/CAPABILITY READY

from:

FEATURE READY
READY_FOR_TEST
APPROVED
VERIFIED

Doctor READY must never imply those feature states.

Add regression proving this.

---

# 10. Installer safety/idempotency

Preserve existing safety properties and add V2 coverage.

Required:

- repeated install is idempotent;
- unrelated user/project files are preserved;
- symlink/reparse unsafe paths fail closed;
- partial failed install does not silently claim success;
- launcher points to the installed V2 runtime;
- V1 runtime is not removed;
- install manifest hashes match installed bytes;
- package can be installed into a temporary user-scope home.

Do not redesign global ownership/skills-manager behavior.

If no explicit uninstall path exists today, do not invent a complex package manager in Wave 3.
Only add uninstall if repository conventions already require it.

---

# 11. Kit manifest

Update kits/dev/kit.yaml to describe VNext.

It should capture at least:

- VNext authority boundary;
- lifecycle;
- authority modes;
- outputs/artifact roles;
- repository-scoped checks;
- bounded review;
- READY_FOR_TEST terminal state;
- Spec Kit role;
- V1 LEGACY_COMPAT;
- Delivery Manifest deferred/non-authoritative.

Avoid hard-coded model names/tools as semantic roles.

Do not say Spec Kit is business authority.

---

# 12. Acceptance contract

Add:

kits/dev/acceptance.yaml

Use the BA Kit acceptance contract style where useful.

At minimum:

## Tier 1 deterministic

Run for each Dev change:

- test_dev_kit
- test_dev_vnext
- test_dev_vnext_runtime
- test_dev_vnext_cli
- test_dev_vnext_spec_kit
- installed Dev VNext acceptance

## Tier 2 focused runtime

Cases:

- exact BA Handoff VNext authentication;
- Foundation proof revalidation;
- NORMAL path;
- HIGH_RISK exact technical gate;
- Engineering Gap + replacement Handoff;
- risk escalation/replan;
- repository-scoped heterogeneous checks;
- multi-repo exact bases/scopes/revisions;
- bounded review;
- fresh verification;
- FR/BR coverage;
- Delivery Manifest non-authoritative;
- V1 LEGACY_COMPAT.

## Tier 3 fresh install

Required for Phase 5 completion.

Tier 1/2 alone must not mark Phase 5 complete.

---

# 13. Fresh installed-runtime acceptance

Add a dedicated installed VNext acceptance test, analogous in rigor to BA installed acceptance.

Required flow:

1. install Dev Kit VNext into a clean temporary install home;
2. verify runtime/v2 exists;
3. verify launcher points to V2;
4. run Doctor from installed runtime;
5. create a neutral temporary Git project/repository;
6. prepare exact BA Engineering Handoff VNext fixture;
7. trusted synthetic host authenticates BA Human proof;
8. start FEATURE_DELIVERY;
9. validate authority;
10. create/ingest Engineering Impact;
11. create plan/tasks/snapshot;
12. prove NORMAL local change can reach IMPLEMENTATION_READY without unnecessary Human technical gate;
13. perform controlled source mutation;
14. perform one consolidated review;
15. run repository-scoped native checks;
16. build exact FR/BR coverage;
17. finalize Dev Handoff VNext;
18. re-read/revalidate installed Dev Handoff;
19. assert state == READY_FOR_TEST;
20. assert no VERIFIED claim;
21. inspect V1 fixture and prove LEGACY_COMPAT/vnext_authority=false.

Also include one installed HIGH_RISK negative:

- cannot reach implementation without host-authenticated technical receipt.

The test host is synthetic test infrastructure, not a claim of production identity.

---

# 14. Installed isolation

Fresh-install acceptance must ensure runtime cannot accidentally import checkout modules.

Run installed probes with:

python -I

and environment without PYTHONPATH.

CWD must not be the agent-skills source checkout.

Inspect key module __file__ paths and prove they resolve under installed runtime/v2.

This is mandatory for Phase 5 completion.

---

# 15. Public examples

Add or normalize a small neutral Dev VNext example.

Do not build a large demo project.

One compact neutral example is enough to illustrate:

Engineering Handoff VNext
→ Impact
→ Plan
→ optional ED
→ implementation
→ review
→ fresh checks
→ coverage
→ READY_FOR_TEST

Do not use:

- Digital Wedding;
- PetClinic;
- Appointment;
- CR-DWC-*;
- user-specific local paths/names.

Do not duplicate full BA semantic content.

---

# 16. Documentation

Update Dev Kit documentation to VNext.

Required durable docs:

- kits/dev/README.md
- dev-kit/SKILL.md if packaging paths/commands need correction
- docs/vi/DEV_KIT_ARCHITECTURE.md
- docs/vi/DEV_KIT_WORKFLOW.md
- docs/vi/DEV_KIT_ROUTING.md
- docs/vi/DEV_KIT_REVIEW_AND_VERIFICATION.md
- docs/vi/DEV_KIT_USAGE_GUIDE.md
- docs/vi/DEV_KIT_CAPABILITIES.md if stale
- docs/vi/DEV_KIT_PROVENANCE.md if stale

Add concise English operational documentation if current project conventions require EN/VI parity for VNext package surfaces.
Do not translate every historical benchmark document just to satisfy symmetry.

Docs must remove obsolete V1 instructions such as:

- Approved BA Baseline as direct Dev input;
- NEEDS_BA_CLARIFICATION free-text flow as the VNext path;
- runtime/v1 as default;
- Spec Kit gate choice as actual technical authority;
- old dev-plan metadata based on baseline_ref;
- V1 route/new-run semantics.

Docs must explain:

- Engineering Handoff VNext;
- authority modes;
- lifecycle V2;
- gap/resume;
- ED-*;
- exact technical Human gate;
- repository-scoped checks;
- review budget;
- READY_FOR_TEST boundary;
- V1 compatibility;
- Delivery Manifest deferred/non-authoritative.

---

# 17. Provenance and generated metadata

Regenerate/update provenance and package metadata using repository-owned tooling where available.

At minimum ensure:

- runtime dependency descriptions use Engineering Handoff VNext terminology;
- selected third-party versions/commits/licenses remain unchanged unless intentionally changed;
- no fabricated provenance;
- package file hashes reflect V2 package;
- notices/licenses remain present.

Do not upgrade third-party dependencies in this wave.

Spec Kit stays pinned to 1.0.11.

---

# 18. Versioning

No stable release.

Use a prerelease version consistent with repository conventions.

Because Dev VNext changes runtime contract materially, it is acceptable to advance the Dev Kit prerelease line, for example from 0.3.x-rc to a 0.4.x-rc candidate, if repository version policy supports that.

Whatever version is chosen:

- kit.yaml;
- install manifest;
- Doctor;
- docs;
- provenance/package assertions

must agree.

Do not use "V1" in VNext default package labels.

---

# 19. Genericity scan

Run a Dev-owned production/package/docs scan for accidental project-specific semantics.

Default Dev package guidance/examples must not contain:

- Digital Wedding;
- PetClinic;
- Appointment;
- CR-DWC-*;
- machine/user-specific absolute paths.

Historical benchmark docs may remain if clearly historical and not default operational guidance.

Do not broaden this into Test Kit cleanup.

---

# 20. Tests

Before Wave 3 modifications, record baseline at:

0e0e317764b1b36dcc3ddd5df045419e1ea0bf2b

After changes run at least:

- tooling.tests.test_dev_kit
- tooling.tests.test_dev_vnext
- tooling.tests.test_dev_vnext_runtime
- tooling.tests.test_dev_vnext_runtime_acceptance
- tooling.tests.test_dev_vnext_cli
- tooling.tests.test_dev_vnext_spec_kit
- new installed Dev VNext acceptance
- relevant package/provenance tests
- BA VNext installed acceptance
- Project Foundation tests
- Shared SDLC acceptance/contracts
- full tooling unittest discovery
- git diff --check

Expected:
0 failures / 0 errors.

Windows symlink/reparse tests may skip only when host privileges make creation impossible; guard behavior must still be covered.

Do not weaken existing assertions.

---

# 21. Phase 5 completion guard

Installed/package-level tests must prove:

- VNext new-run default;
- exact Engineering Handoff VNext proof;
- BA WHAT remains immutable;
- repository-scoped checks;
- HIGH_RISK technical gate;
- Engineering Gap path;
- bounded review;
- fresh engineering verification;
- FR/BR-only coverage;
- READY_FOR_TEST != VERIFIED;
- Doctor READY != feature readiness;
- Spec Kit != WHAT authority;
- V1 != VNext authority;
- Delivery Manifest remains non-authoritative/deferred.

---

# 22. Forbidden changes

Do NOT:

- change Dev VNext semantic contracts;
- modify Delivery Manifest V2;
- migrate Test Kit;
- implement system automation;
- implement Phase 8 defect/retest;
- touch Digital Wedding repositories;
- upgrade Spec Kit/Addy/Superpowers dependencies;
- publish stable OSS release;
- merge to main.

---

# 23. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_5_WAVE_3_DEV_KIT_VNEXT_PACKAGING_SPEC.md

Do not copy or rename it elsewhere.

Final Wave 3 tree must not contain it.

---

# 24. Required report

PHASE_5_WAVE_3_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/dev-kit-vnext-wave3

BASE:
0e0e317764b1b36dcc3ddd5df045419e1ea0bf2b

HEAD:
<exact SHA>

KIT_MANIFEST:
<VNext package metadata/version>

RUNTIME_LAYOUT:
<runtime/v2 + launcher behavior>

INSTALLER:
<closure/idempotency/safety>

SCHEMAS:
<V2 + V1 legacy>

TEMPLATES:
<V2 + legacy>

DOCTOR:
<VNext capability checks>

ACCEPTANCE_CONTRACT:
<tier 1/2/3>

FRESH_INSTALL_ACCEPTANCE:
<installed isolated full flow>

INSTALLED_ISOLATION:
<python -I / no PYTHONPATH proof>

DOCS:
<updated VNext docs>

PUBLIC_EXAMPLES:
<neutral example>

PROVENANCE:
<regenerated/updated>

GENERICITY:
<scan result>

LEGACY_COMPAT:
<V1 behavior>

DELIVERY_MANIFEST:
DEFERRED_NON_AUTHORITATIVE

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
feat/dev-kit-vnext-wave3

RECOMMENDED_PHASE_5_INTEGRATION:
<merge/audit readiness>

If packaging requires semantic contract changes, STOP:

ARCHITECTURE_DECISION_REQUIRED
