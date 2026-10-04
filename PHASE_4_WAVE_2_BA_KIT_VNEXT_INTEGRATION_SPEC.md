# Phase 4 — Wave 2 Implementation Spec
## BA Kit VNext Packaging, Documentation, Examples and Installation Acceptance

Status: READY_FOR_AGENT_EXECUTION
Required model: LUNA Medium
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: d812d2e9e338482ec8d621a849f6c0e2fa3e3c25
Source branch: fix/ba-vnext-foundation-promotion-proof-v1
Suggested implementation branch: feat/ba-kit-vnext-wave2

TEMPORARY BOOTSTRAP ARTIFACT:
This file exists only so a fresh implementation session can fetch the exact approved scope.
Create the Wave 2 branch from the latest remote source branch containing this file, read it fully, then DELETE this file before final commit/report.
The final Wave 2 tree must not contain this bootstrap spec.

---

# 1. Goal

Finish Phase 4 by making the already-approved BA Kit VNext semantics a coherent, installable and documented BA Kit capability.

Behavioral base:

d812d2e9e338482ec8d621a849f6c0e2fa3e3c25

Wave 2 is mechanical integration.

Required outcomes:

1. BA Kit package/install surfaces include all VNext runtime files.
2. BA Doctor verifies VNext capability closure.
3. VNext templates/examples are canonical and discoverable.
4. Legacy V1 compatibility remains explicit and read-only with no fabricated approval.
5. Public BA examples/fixtures are neutral and no longer teach project-specific Appointment/PetClinic semantics.
6. Documentation consistently describes the VNext lifecycle/authority model.
7. Fresh install and isolated runtime acceptance prove the kit works without source-checkout imports.
8. Package manifests/provenance are regenerated deterministically.
9. Full repository regression remains green.

Do not redesign BA VNext semantics.

---

# 2. Frozen semantics

The following are already approved and MUST NOT change:

BA baseline lifecycle:

DRAFT
→ VALIDATED
→ HUMAN_REVIEW
→ APPROVED_BASELINE

Human invariants:

- CONTINUE != APPROVE
- ANSWER != APPROVE
- validator PASS != APPROVE
- generated != APPROVED
- Foundation READY != BA APPROVED_BASELINE
- UX approval != BA baseline approval

Authority:

- Human BA Decisions
- Business Rules with BR-* IDs
- canonical functional SRS with FR-* IDs

BAREF:* remains provenance/structural locator only.

Engineering Handoff VNext must revalidate:
- exact BA candidate;
- exact approval receipt;
- exact authoritative source refs;
- Human authentication;
- Foundation durable proof when present.

Project Foundation consumption requires:
- durable manifest;
- promotion provenance;
- Foundation approval receipt;
- trusted Foundation host authentication.

BA owns WHAT.
Engineering owns HOW.

No Wave 2 task may alter these contracts.

---

# 3. Model boundary

This task uses LUNA Medium because architecture/semantics are frozen.

If ANY task appears to require:
- changing BA lifecycle;
- changing approval receipt semantics;
- changing FR/BR/BAREF identity rules;
- changing Foundation proof semantics;
- changing authority ownership;
- changing Shared Core;
- changing Delivery Manifest V2;
- changing UX receipt V2;

STOP with:

ARCHITECTURE_DECISION_REQUIRED

Do not solve semantic ambiguity inside Wave 2.

---

# 4. BA Kit composition

Inspect and update the BA Kit composition so VNext is represented accurately.

Current package surfaces include:
- kits/ba/kit.yaml
- kits/ba/acceptance.yaml
- kits/ba/README.md
- ba-workflow/
- atomic BA skills
- tooling/lib/ba_kit.py

Requirements:

1. ba-workflow remains the BA orchestrator.
2. VNext runtime files under ba-workflow/scripts are included automatically/explicitly as required by current installer mechanics.
3. Shared SDLC payload required by VNext is present in installed ba-workflow.
4. Do not create a separate ba-vnext Kit.
5. Do not create a fourth SDLC Kit.
6. Atomic skills remain independently routed by ba-workflow.
7. Optional UX/design skills stay optional.

Update kit outputs/capability descriptions to reflect VNext durable outputs without implying runtime state is canonical authority.

Do not remove V1 compatibility artifacts yet.

---

# 5. Canonical BA VNext artifact set

Document and package the expected VNext artifact roles.

RUNTIME:
- workflow-state V2

CANONICAL CANDIDATE / authority inputs:
- BA Decisions
- Business Rules
- canonical SRS
- BA Baseline Candidate/Manifest

EVIDENCE / GATE:
- BA Human approval receipt
- exact evidence refs

HANDOFF_MANIFEST:
- Engineering Handoff VNext

DERIVED:
- DOCX
- Draw.io
- optional prototype/visual outputs

The package must not suggest workflow-state.json itself is business authority.

Templates/examples must reflect these classes clearly.

---

# 6. Templates

Provide/normalize canonical VNext templates or safe examples for:

- workflow state V2;
- BA Decisions V1;
- baseline candidate V1;
- BA approval receipt V1 example/template boundary;
- Engineering Handoff V2.

Important:

- A receipt template MUST NOT contain a usable fake approval.
- Human identity/authentication is host-provided.
- Placeholder/example receipts must be clearly non-authoritative and fail production validation until exact refs/authentication are supplied.
- Do not create a CLI that fabricates receipts.
- Existing V1 templates remain for compatibility if needed, but docs must mark them LEGACY_COMPAT.

Use JSON/YAML according to the executable contract and current repository conventions.

---

# 7. Public examples cleanup

Review BA public examples, especially kits/ba/examples/CR-001 and related docs.

Replace project-specific or PetClinic/Appointment semantics with a neutral fictional feature while preserving the instructional structure.

Neutral example should demonstrate:

- input requirement;
- gap review;
- Human BA Decisions;
- BR-* stable IDs;
- FR-* stable IDs;
- baseline candidate;
- explicit Human review boundary;
- Engineering Handoff VNext;
- non-blocking item behavior;
- Knowledge Impact.

Do not include:
- PetClinic;
- Appointment;
- Digital Wedding;
- CR-DWC-*;
- real user/company identities.

If example directory naming CR-001 is generic and harmless, it may remain.
Content must be neutral.

Do NOT touch Test Kit XMind/Appointment production-profile cleanup in this phase unless BA package directly owns the file.

---

# 8. BA workflow skill documentation

Update ba-workflow/SKILL.md so an installed agent is routed through VNext by default.

It must explain:

1. consume Project Foundation when available;
2. start/resume Workflow State V2;
3. distinguish operation from baseline lifecycle;
4. discovery/gap/clarification;
5. build/update BA Decisions + BR + SRS;
6. construct/select candidate baseline;
7. validate;
8. move to HUMAN_REVIEW;
9. stop for Human approval;
10. consume host-supplied approval;
11. produce Engineering Handoff VNext.

Legacy V1 artifacts:
- may be read/validated through compatibility;
- must not be treated as VNext approved proof.

Do not bury approval semantics in prose; make the gate explicit.

---

# 9. Doctor

Extend BA Kit Doctor so it verifies the VNext capability is actually installed.

Doctor should check at least:

- ba-workflow/SKILL.md exists;
- ba_vnext.py exists;
- ba_contracts.py exists;
- validate-state.py exists;
- validate-handoff.py exists;
- VNext templates exist;
- Shared SDLC payload exists and can import required modules;
- canonical SRS contract still exists;
- required atomic BA skills resolve.

Doctor semantics remain package/capability readiness only.

Doctor READY/DEGRADED/FAIL MUST NOT imply:
- Human approval;
- approved BA baseline;
- feature readiness.

Add regression for that distinction.

---

# 10. Installer / uninstall behavior

Ensure BA Kit installer:

- installs VNext files deterministically;
- remains idempotent;
- preserves unrelated/user-modified skills;
- preserves shared files owned by another kit when appropriate;
- fails closed on unsafe links/reparse paths;
- supports project/user/generic target behavior already promised;
- does not require Skills Manager;
- does not rely on local source checkout.

Uninstall must:
- remove only unchanged BA-managed files;
- preserve edited/shared/unrelated content;
- not remove Shared Core payload needed by another installed capability if current ownership model marks it shared.

Do not redesign the installer ownership model unless required; if a semantic ownership decision is needed, STOP.

---

# 11. Shared payload / generated artifacts

Regenerate derived payloads with repository-provided tools.

At minimum inspect whether BA VNext changes require regeneration of:

- ba-workflow/scripts/shared-sdlc-core.zip;
- shared SDLC package archives;
- install manifests/hashes;
- provenance records;
- package authority files.

Use canonical regeneration tools.

Do not hand-edit generated hashes if generators exist.

No unrelated generated drift.

---

# 12. Installation documentation

Normalize EN/VI installation/usage docs so users can answer:

- how to install BA Kit;
- what BA Kit installs;
- how to run Doctor;
- how BA VNext differs from V1 compatibility;
- where workflow state lives;
- where canonical BA artifacts live;
- how Project Foundation is consumed;
- where Human approval occurs;
- how Engineering Handoff is produced;
- what remains downstream Engineering/Test responsibility.

Do not claim a stable release if not released.

Do not claim Human authentication is implemented by a CLI if it is host integration.

---

# 13. BA Kit README / capability docs

Update relevant durable docs for VNext consistency.

Inspect/update where applicable:

- kits/ba/README.md
- docs/vi/BA_KIT_WORKFLOW.md
- docs/en/BA_KIT_WORKFLOW.md
- BA capability/quickstart/usage docs
- source authority/human gate/handoff references
- root docs links only if stale

Remove statements that imply the old V1 status string alone establishes approval.

Keep legacy documentation clearly marked historical/compatibility where retained.

Do not perform general repository release-doc cleanup beyond BA-related correctness.

---

# 14. Acceptance contract

Update kits/ba/acceptance.yaml for VNext.

Tier 1 deterministic must include appropriate VNext tests.

Tier 2 focused runtime should cover:
- Foundation context consumption;
- CURRENT_SYSTEM vs target distinction;
- named Human ANSWER;
- stable BR/FR;
- exact candidate validation;
- approval-negative behavior;
- handoff exact proof.

Tier 3 fresh-session/install acceptance remains mandatory for Phase 4 completion.

Do not allow Tier 1/Tier 2 alone to claim final BA VNext completion if Tier 3 is required by the acceptance contract.

---

# 15. Fresh-install acceptance

Create/extend automated acceptance using a temporary installation target.

Required flow:

1. install BA Kit into a clean temporary target;
2. prevent imports from repository source checkout;
3. run BA Doctor;
4. create/read a VNext workflow state;
5. construct or consume neutral BA Decisions/BR/SRS;
6. create/select baseline candidate;
7. validate candidate;
8. move to HUMAN_REVIEW;
9. prove no approval without trusted host;
10. inject a synthetic trusted-host Human approval in the test harness;
11. reach APPROVED_BASELINE;
12. create Engineering Handoff VNext;
13. re-read/revalidate the handoff from installed runtime;
14. prove V1 state/handoff remain LEGACY_COMPAT and never VNext-approved.

If practical, include a bounded Project Foundation promoted-context case.
Do not duplicate the entire Phase 3 E2E suite unnecessarily.

The installed runtime must not accidentally import:
- checkout ba-workflow;
- checkout shared/sdlc;
- developer-local PYTHONPATH.

---

# 16. Fresh-session behavioral acceptance

Add or update a neutral agent-facing acceptance scenario proving an agent following installed BA workflow instructions does not:

- invent approvals;
- invent technical design;
- turn CURRENT_SYSTEM into target;
- reuse retired IDs;
- create BAREF coverage obligations;
- skip HUMAN_REVIEW;
- mutate in REVIEW mode.

This may be deterministic instruction/fixture acceptance if external model execution is not part of repository CI.

Do not pretend a synthetic script is an independent Human.

---

# 17. Versioning

Do not publish a stable release.

Do not invent final framework lockstep versioning in this wave.

If current kit manifest version must change solely to represent a new packaging candidate, use the repository's existing prerelease convention and document the reason.

Prefer not to bump version unless packaging/release machinery requires it.

Do not leave contradictory version labels in BA docs if a version does change.

---

# 18. Backward compatibility

Preserve:

- V1 workflow-state validation/read;
- V1 Engineering Handoff validation/read;
- old import adapters;
- current atomic BA skill entry points.

Compatibility must remain explicit:

V1 artifact
→ LEGACY_COMPAT
→ vnext_approval = false

No migration helper may fabricate:
- Human receipt;
- candidate hash;
- approval status.

If an explicit migration utility is added, it may create a DRAFT VNext candidate only when exact source evidence exists.
It may never create APPROVED_BASELINE.

A migration utility is optional in Wave 2; do not add one unless it materially improves clean upgrade behavior.

---

# 19. Public genericity

Run a BA-owned production/example scan for forbidden domain leakage.

Production and canonical BA examples must not teach:
- Digital Wedding;
- PetClinic;
- Appointment;
- user-specific paths/names.

Historical benchmark/evidence fixtures outside BA-owned public package may remain if intentionally historical and not shipped as BA production guidance.

Do not broaden this into Test Kit cleanup.

---

# 20. Tests

Before changes run full baseline at:

d812d2e9e338482ec8d621a849f6c0e2fa3e3c25

After changes run at least:

- tooling.tests.test_ba_kit
- tooling.tests.test_ba_vnext
- tooling.tests.test_srs_function_document
- relevant SDLC contract/acceptance tests
- BA install/uninstall/Doctor tests
- fresh installed-runtime isolation acceptance
- full tooling unittest discovery

Also validate:
- V1 validator CLIs;
- VNext validator CLIs;
- package regeneration;
- git diff --check.

Expected:
0 failures / 0 errors.

Windows symlink tests may skip when privilege is unavailable; reparse guards must still execute/pass.

Do not weaken assertions.

---

# 21. Phase 4 completion guard

Add/retain targeted tests proving the packaged installed capability preserves:

- lifecycle DRAFT → VALIDATED → HUMAN_REVIEW → APPROVED_BASELINE;
- exact Human authentication;
- V1 never fabricates VNext approval;
- FR/BR stable identity rules;
- BAREF locator-only rule;
- Foundation durable promotion proof;
- BA WHAT / Engineering HOW boundary;
- Handoff exact proof;
- Doctor/package readiness != business approval.

These should test installed/package surfaces, not only source modules.

---

# 22. Forbidden changes

Do NOT:

- change BA VNext semantic contracts;
- change Shared Core;
- change Project Foundation semantics;
- change Delivery Manifest V2;
- change UX receipt V2;
- migrate Dev Kit;
- migrate Test Kit;
- change Test execution/defect lifecycle;
- remove Test Kit Appointment/XMind leak unless BA-owned;
- redesign Spec Kit;
- touch Digital Wedding repositories;
- introduce stable OSS release;
- merge to main.

---

# 23. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_4_WAVE_2_BA_KIT_VNEXT_INTEGRATION_SPEC.md

Do not rename/copy it elsewhere.

Final tree must not contain it.

---

# 24. Required report

PHASE_4_WAVE_2_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
feat/ba-kit-vnext-wave2

BASE:
d812d2e9e338482ec8d621a849f6c0e2fa3e3c25

HEAD:
<exact SHA>

KIT_COMPOSITION:
<manifest/capability>

TEMPLATES:
<VNext + legacy status>

PUBLIC_EXAMPLES:
<neutralization/update>

SKILL_ROUTING:
<VNext default routing>

DOCTOR:
<VNext capability checks>

INSTALLER:
<install/uninstall/idempotency>

PACKAGING_PROVENANCE:
<regenerated payloads/hashes>

DOCS:
<EN/VI/capability/quickstart>

ACCEPTANCE_CONTRACT:
<tier updates>

FRESH_INSTALL_ACCEPTANCE:
<isolated runtime proof>

BACKWARD_COMPATIBILITY:
<V1 LEGACY_COMPAT proof>

GENERICITY:
<BA production/example leakage scan>

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
feat/ba-kit-vnext-wave2

RECOMMENDED_PHASE_5:
<Dev Kit VNext prerequisites>

If implementation requires changing any frozen BA/Shared/Foundation semantic contract, STOP with:

ARCHITECTURE_DECISION_REQUIRED

and describe the exact decision.
