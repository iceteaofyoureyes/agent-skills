# PHASE 8 — DEFECT PROOF SEMANTICS REMEDIATION

Status: HUMAN APPROVED FOR IMPLEMENTATION
Repository: iceteaofyoureyes/agent-skills

Phase 8 candidate base:
7a860166db6b37573e96133a6515dec91e6dde29

Framework main base:
3075b6c51ef7a3ee58e9b11eedf57bb7ba7a8645

Target branch:
fix/phase8-defect-proof-semantics

Recommended model:
GPT-6 Luna Extra High when available.

This is a narrow semantic remediation. Preserve every other Phase 8 contract.

---

## 1. Independent-review finding

The Human-approved Phase 8 execution spec states that classifying a Finding as DEFECT requires:

- an exact approved oracle;
- an exact Finding Observation;
- behavior that is reproducible **or** exact deterministic evidence proving the mismatch;
- environment root cause excluded;
- test/automation issue excluded to the supported extent;
- exact in-topology application target(s);
- authenticated Tester classification.

The current Phase 8 candidate instead requires both:

```text
reproducible = true
AND
deterministic = true
```

in:
- `tooling/lib/test_execution_vnext.py`;
- `kits/test/schemas/finding-classification-v1.schema.json`;
- docs/tests.

That is semantic drift.

It incorrectly rejects valid intermittent/flaky implementation defects that are repeatedly reproducible but not deterministic on every run.

It may also reject a one-shot but exact deterministic evidence case where reproducibility cannot practically be repeated.

---

## 2. Required Defect proof rule

Keep the existing proof object fields:

```text
reproducible
deterministic
environment_root_cause_excluded
test_issue_excluded
mismatch_evidence_refs
```

Do not redesign the artifact shape.

Change semantics to:

```text
(reproducible == true OR deterministic == true)
AND environment_root_cause_excluded == true
AND test_issue_excluded == true
AND mismatch_evidence_refs non-empty
AND target_repository_ids non-empty/in topology
```

Both booleans may be true.

Both booleans false must fail.

---

## 3. Semantics

### Reproducible defect

Valid example:

```json
{
  "reproducible": true,
  "deterministic": false,
  "environment_root_cause_excluded": true,
  "test_issue_excluded": true,
  "mismatch_evidence_refs": ["..."]
}
```

This covers intermittent/flaky product defects for which repeated runs demonstrate the product issue, even if each individual run is not deterministic.

### Deterministic-evidence defect

Valid example:

```json
{
  "reproducible": false,
  "deterministic": true,
  "environment_root_cause_excluded": true,
  "test_issue_excluded": true,
  "mismatch_evidence_refs": ["..."]
}
```

This covers exact deterministic evidence sufficient to prove a product mismatch when repeated reproduction is not required/available.

### Strong case

Also valid:

```text
reproducible = true
deterministic = true
```

### Invalid

Reject:

```text
reproducible = false
deterministic = false
```

Reject if:
- environment root cause is not excluded;
- test/automation issue is not excluded;
- mismatch evidence is absent;
- target repository is absent/outside exact application topology;
- Tester identity is not authenticated.

---

## 4. No auto-classification

This remediation must NOT weaken the core boundary:

```text
COMMAND_FAIL != DEFECT
FINDING != DEFECT
```

An authenticated Tester still explicitly classifies the Finding.

Exit code alone remains insufficient.

---

## 5. Runtime contract

Update `validate_classification()` so DEFECT accepts the OR rule.

`classify_finding()` should continue:
- exact Finding/Observation binding;
- exact approved testcase oracle;
- trusted Tester authentication;
- evidence-ref validation;
- target repo topology validation;
- immutable Classification artifact;
- exact Defect Handoff.

Do not change the finding taxonomy or routes.

---

## 6. JSON Schema

Update:

```text
kits/test/schemas/finding-classification-v1.schema.json
```

Requirements:

- `reproducible` is boolean;
- `deterministic` is boolean;
- schema enforces at least one is true;
- environment/test exclusion remain const true for DEFECT;
- mismatch_evidence_refs minItems >= 1;
- target_repository_ids minItems >= 1;
- non-DEFECT classifications still cannot carry defect_proof.

Use JSON Schema 2020-12 idioms already used in the repository.

Do not create schema v2 just for this correction.

---

## 7. Tests

Add direct contract tests for:

### A. Reproducible non-deterministic

```text
reproducible=true
deterministic=false
→ PASS
```

### B. Deterministic non-reproduced

```text
reproducible=false
deterministic=true
→ PASS
```

### C. Both true

```text
→ PASS
```

### D. Both false

```text
→ FAIL
```

### E. Root-cause exclusions

Either:
```text
environment_root_cause_excluded=false
```
or:
```text
test_issue_excluded=false
```
must fail.

### F. Missing mismatch evidence

→ FAIL.

### G. No target repository

→ FAIL.

### H. Runtime classification

At least one full runtime/acceptance case should classify a DEFECT with:

```text
reproducible=true
deterministic=false
```

to prove the executable contract is not accidentally stricter than the schema.

---

## 8. Documentation

Update wording in:

```text
docs/vi/TEST_EXECUTION_VNEXT.md
docs/en/TEST_EXECUTION_VNEXT.md
kits/test/skills/test-execution-vnext/SKILL.md
neutral Phase 8 example if it states both are mandatory
```

Normative wording:

```text
reproducible mismatch OR exact deterministic mismatch evidence
```

Do not describe every product defect as necessarily deterministic.

---

## 9. Frozen Phase 8 architecture

Do NOT change:

- exact EXECUTION_READY authority;
- environment binding;
- Execution Manifest;
- command execution rules;
- shell=False;
- Observation contract;
- five Finding classifications;
- Tester-only classification;
- Defect Handoff structure except no shape change is expected;
- Dev fix via normal FEATURE_DELIVERY;
- READY_FOR_RETEST;
- Tester retest;
- VERIFIED / REOPENED;
- multi-repo revision binding;
- Delivery Manifest deferred/non-authoritative;
- legacy execution compatibility;
- no READY_TO_MERGE;
- Test Kit package version line.

If this small remediation requires changing those boundaries:

```text
ARCHITECTURE_DECISION_REQUIRED
```

and stop.

---

## 10. Package version

Keep:

```text
2.0.0-rc.8
```

This correction is part of the not-yet-merged Phase 8 candidate.

Do not bump to rc.9 solely for this pre-merge remediation unless repository-owned tooling explicitly requires it.

---

## 11. Package integrity

Because schema/docs/skill/runtime/tests may change:

- regenerate package authority through repository-owned tooling/algorithm;
- regenerate payload tree SHA;
- update kit integrity pins;
- verify managed file hashes;
- rerun package/Doctor tests after final docs changes.

Do not hand-edit hashes without canonical regeneration.

---

## 12. Tests minimum

Run:

```text
python -m unittest tooling.tests.test_test_execution_vnext -v
python -m unittest tooling.tests.test_test_execution_vnext_acceptance -v
python -m unittest tooling.tests.test_test_execution_vnext_installed_acceptance -v
python -m unittest tooling.tests.test_test_execution_vnext_schemas -v
python -m unittest tooling.tests.test_kit_packaging -v
python -m unittest tooling.tests.test_test_kit_policy_doctor -v
python -m unittest discover -s tooling/tests -p "test_*.py"
git diff --check
```

No new skips to bypass the issue.

---

## 13. Hygiene

Before final commit delete:

```text
PHASE_8_DEFECT_PROOF_SEMANTICS_REMEDIATION_SPEC.md
```

Do not copy/rename it elsewhere.

No temporary Phase 8 specs in final target tree.

No scratch/cache/runtime artifacts.

---

## 14. Git workflow

Source:

```text
phase8/defect-proof-remediation-bootstrap
```

Expected behavioral base:

```text
7a860166db6b37573e96133a6515dec91e6dde29
```

Target:

```text
fix/phase8-defect-proof-semantics
```

Do not merge.

Push target.

Worktree clean.

---

## 15. Required report

```text
PHASE_8_DEFECT_PROOF_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/phase8-defect-proof-semantics

BASE:
7a860166db6b37573e96133a6515dec91e6dde29

HEAD:
<exact SHA>

DEFECT_PROOF_RULE:
<reproducible OR deterministic>

RUNTIME_VALIDATION:
<status>

SCHEMA:
<status>

REPRODUCIBLE_NONDETERMINISTIC:
<status>

DETERMINISTIC_NONREPRODUCED:
<status>

BOTH_FALSE_NEGATIVE:
<status>

ROOT_CAUSE_EXCLUSION_NEGATIVES:
<status>

RUNTIME_ACCEPTANCE:
<status>

DOCS:
<status>

KIT_VERSION:
2.0.0-rc.8

PACKAGE_AUTHORITY:
<hashes/status>

TESTS:
<results>

SEMANTIC_DRIFT:
NONE
or exact list

BLOCKERS:
NONE
or exact list

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

REMOTE_BRANCH:
fix/phase8-defect-proof-semantics

WORKTREE:
CLEAN

RECOMMENDED_PHASE_8_STATUS:
VERIFIED_COMPLETE_CANDIDATE | NOT_READY
```
