# Phase 4 — Wave 1 Remediation Spec
## Require durable Project Foundation promotion proof

Status: READY_FOR_AGENT_EXECUTION
Required model: LUNA Medium
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: a2192ca2f3a688dbc69b590a0ee16674a01ce9b8
Source branch: feat/ba-kit-vnext-wave1
Suggested implementation branch: fix/ba-vnext-foundation-promotion-proof-v1

TEMPORARY BOOTSTRAP ARTIFACT:
Read this file from the latest remote source branch, implement exactly this remediation, then DELETE this file from the remediation branch before final commit/report.

---

# 1. Problem

BA VNext currently accepts an optional Project Foundation binding shaped as:

- manifest
- root
- optional approval
- optional previous

and validates it primarily by calling Shared Core foundation_readiness().

That is insufficient proof that the supplied Foundation snapshot is the durable PROJECT_FOUNDATION_READY snapshot produced by the Project Foundation workflow.

foundation_readiness() is intentionally a pure structural validator. For a brownfield manifest containing no APPROVED_TARGET section it can return PROJECT_FOUNDATION_READY without proving that:

- Human review occurred;
- accept() occurred;
- immutable promote() occurred;
- the supplied manifest is the promoted durable snapshot.

Phase 3 explicitly distinguishes:

valid candidate / structural readiness
!=
workflow PROJECT_FOUNDATION_READY after Human review + immutable promotion.

BA VNext must consume a promoted Foundation snapshot, not an arbitrary structurally-ready candidate.

This is a Phase 4 integration bug. Do not change Shared Core semantics to make foundation_readiness() mean promotion.

---

# 2. Required behavior

When project_foundation is supplied to a BA VNext baseline, it MUST prove a durable Project Foundation publication.

The binding must include enough exact evidence to validate:

1. exact durable Foundation manifest bytes;
2. exact promotion provenance bytes;
3. exact Human review receipt referenced by that provenance;
4. manifest identity/revision/hash matches provenance source;
5. provenance manifest_sha256 matches the supplied Foundation manifest;
6. provenance mode and Knowledge Impact, when present, match the promoted manifest/publication data;
7. approval receipt bytes/hash match provenance;
8. trusted Foundation host authenticates the Human receipt;
9. previous Foundation binding/receipt rules remain valid when prior evidence is declared;
10. foundation_readiness() still validates the semantic Foundation manifest.

A structurally valid but unpromoted candidate MUST fail BA VNext Foundation binding.

A copied/fabricated provenance document without trusted-host receipt authentication MUST fail.

PROJECT_FOUNDATION_READY still does NOT imply BA APPROVED_BASELINE.

---

# 3. Preferred contract shape

Extend the BA VNext project_foundation binding with an exact provenance ref.

Conceptually:

{
  "root": "foundation-project",
  "manifest": { exact ref },
  "provenance": { exact ref },
  "approval": { exact ref },
  "previous": { exact ref } // optional where applicable
}

The exact field naming may follow repository conventions, but provenance proof is mandatory for VNext Foundation consumption.

Do not silently infer provenance by filename adjacency.

All refs remain feature-relative and are safely rebased into the nested Foundation project root.

---

# 4. Validation rules

The BA adapter must validate the existing Project Foundation promotion record shape rather than inventing a second promotion format.

Reuse existing Shared Core helpers/contracts where practical.

For the supplied durable manifest:

- validate exact ref/path/revision/SHA;
- parse and validate Foundation manifest;
- call foundation_readiness() for semantic readiness;
- verify provenance exact ref/path/revision/SHA;
- provenance source.id == manifest.id;
- provenance source.revision == manifest.revision;
- provenance source.sha256 == SHA-256 of exact durable manifest bytes;
- provenance manifest_sha256 == Foundation manifest semantic hash;
- provenance approval_receipt exactly matches supplied Foundation approval ref;
- receipt bytes match approval ref SHA;
- Human receipt is authenticated by foundation_authenticator;
- receipt binds the exact Foundation manifest id/revision/hash;
- if previous is supplied, prior binding must be validated according to existing Foundation approval semantics.

Do NOT trust:
- filename conventions;
- status strings;
- provenance.human_approval boolean;
- actor_role string alone;
- a hash alone;
- foundation_readiness() alone.

---

# 5. Brownfield requirement

Add a negative regression proving:

A brownfield Foundation candidate that:
- structurally passes foundation_readiness();
- has no APPROVED_TARGET;
- has never gone through accept()/promote();

MUST NOT be accepted as BA project_foundation context.

Then prove the same semantic Foundation snapshot DOES become acceptable after:
- trusted-host Human review;
- immutable promotion;
- exact provenance binding.

This is the primary bug being fixed.

---

# 6. Greenfield requirement

Preserve current nested greenfield behavior:

- APPROVED_TARGET requires exact authenticated Foundation approval;
- promoted manifest + provenance + approval are accepted;
- BA validation remains only VALIDATED until its own BA Human Gate;
- Foundation approval does not approve BA baseline.

Add a negative case where:
- promoted manifest bytes are valid;
- provenance or receipt is changed;
- BA validation fails closed.

---

# 7. Compatibility

Do not rewrite BA VNext lifecycle.

Existing BA VNext candidates without project_foundation remain valid.

For VNext candidates that include project_foundation:
- new durable promotion proof is required.

This is acceptable because Wave 4.1 has not been released as a stable external contract yet.

Do not reinterpret V1 BA artifacts as promoted Foundation proof.

Do not change current legacy BA V1 compatibility semantics.

---

# 8. Scope

Required code likely includes:
- ba-workflow/scripts/ba_vnext.py
- BA VNext docs/contracts
- BA VNext tests/fixtures

Regenerate packaged Shared payload/provenance only if repository test closure requires it.

Do NOT perform Phase 4 Wave 2 packaging/docs/example migration beyond changes needed to keep Wave 4.1 coherent.

---

# 9. Forbidden changes

Do NOT:
- change Shared Core foundation_readiness() semantics;
- change Project Foundation workflow lifecycle;
- change Project Foundation promote() semantics;
- change BA lifecycle;
- change BA Human Gate;
- change FR/BR/BAREF semantics;
- change Delivery Manifest V2;
- change UX receipt V2;
- migrate Dev/Test kits;
- touch Digital Wedding;
- merge to main.

---

# 10. Tests

Run at least:

python -m unittest tooling.tests.test_ba_vnext -v
python -m unittest tooling.tests.test_project_foundation -v
python -m unittest discover -s tooling/tests -q

Mandatory focused cases:

1. structurally-ready unpromoted brownfield Foundation is rejected;
2. promoted brownfield Foundation with exact provenance + authenticated receipt is accepted;
3. missing provenance rejected;
4. manifest/provenance SHA mismatch rejected;
5. provenance source id/revision mismatch rejected;
6. provenance approval ref mismatch rejected;
7. modified receipt rejected;
8. false/missing Foundation authenticator rejected;
9. promoted greenfield APPROVED_TARGET remains accepted only with exact proof;
10. Foundation proof never sets BA APPROVED_BASELINE;
11. existing BA VNext baseline without Foundation still works;
12. legacy BA V1 compatibility unchanged.

Do not weaken existing tests.

---

# 11. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_4_WAVE_1_REMEDIATION_FOUNDATION_PROMOTION_PROOF_SPEC.md

Do not rename or copy it elsewhere.

Final tree must not contain it.

---

# 12. Required report

PHASE_4_WAVE_1_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/ba-vnext-foundation-promotion-proof-v1

BASE:
a2192ca2f3a688dbc69b590a0ee16674a01ce9b8

HEAD:
<exact SHA>

FIX:
<summary>

FOUNDATION_BINDING:
<manifest + provenance + approval proof>

BROWNFIELD_PROOF:
<unpromoted reject / promoted accept>

GREENFIELD_PROOF:
<approved target exact proof>

HUMAN_AUTHENTICATION:
<foundation host authentication>

BA_GATE_ISOLATION:
<Foundation proof does not approve BA baseline>

COMPATIBILITY:
<no-Foundation VNext + legacy V1>

TESTS:
<commands + pass/fail/skip counts>

SEMANTIC_CHANGES:
NONE — integration corrected to approved Phase 3 durable readiness contract
or explain

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

Do not merge.
