# Phase 3 — Wave 2A Remediation Spec
## arc42 Context & Scope Ownership Alignment

Status: READY_FOR_AGENT_EXECUTION
Required model: LUNA Medium
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: ebf4ca36d5e6a474f0f57404087105e9672c3a94
Source branch: feat/project-foundation-v1-wave2a
Suggested implementation branch: fix/project-foundation-context-scope-owner-v1

TEMPORARY BOOTSTRAP ARTIFACT:
Read this file from the latest remote source branch, implement exactly this remediation, then DELETE this file from the remediation branch before final commit/report.

---

# 1. Problem

Project Foundation core currently defines:

SECTION_DOMAINS.update(
    introduction_goals='product',
    context_scope='domain',
    glossary='domain',
    quality_requirements='testing'
)

That makes the arc42 Context & Scope section BA/domain-owned.

This conflicts with the approved architecture model:

- BA owns product/domain/glossary/business semantics.
- ENGINEERING owns System Context / architecture / runtime / deployment.
- TEST owns testing/automation/quality strategy.

It also conflicts with Phase 3 Wave 2A architecture-discovery, where topic context_scope is correctly ENGINEERING-owned.

If left unchanged, a Foundation Manifest will expect context_scope owner BA while the architecture producer emits ENGINEERING-owned context_scope records.

---

# 2. Required behavior

arc42 section ownership must be:

- introduction_goals -> product -> BA
- glossary -> domain -> BA
- quality_requirements -> testing -> TEST
- context_scope -> architecture -> ENGINEERING
- all other architecture sections -> architecture -> ENGINEERING

BA-owned actors/entities/domain concepts MAY contribute evidence/content to an arc42 Context & Scope projection.

That does NOT transfer semantic ownership of the arc42 section itself to BA.

System Context / Context & Scope remains ENGINEERING-owned.

---

# 3. Required fix

Make the smallest compatible change.

At minimum:

1. Correct SECTION_DOMAINS so context_scope resolves to architecture.
2. Ensure candidate Foundation manifests default context_scope owner to ENGINEERING.
3. Ensure CONFIRMED context_scope checks against Project Policy architecture authority, not domain authority.
4. Ensure knowledge-impact routing for a changed context_scope marks architecture affected, not domain.
5. Ensure Wave 2A arc42/architecture producer can integrate with a Foundation manifest whose context_scope owner is ENGINEERING.
6. Preserve BA domain producer records for actors/entities as valid input into arc42 context projection; do not reassign those record owners.
7. Add regression tests for all above.
8. Update durable docs only where ownership is stated or implied incorrectly.

---

# 4. Do not overcorrect

Do NOT:

- change BA ownership of glossary/domain/business rules;
- change product Introduction & Goals ownership;
- change TEST ownership of Quality Requirements;
- remove actors/entities from arc42 context projection;
- make architecture-discovery own BA domain semantics;
- modify Shared Project Policy schema;
- modify Human Gate/approval semantics;
- modify Delivery Manifest V2;
- modify FR/BR/BAREF semantics;
- perform Wave 2B integration work;
- touch Digital Wedding;
- merge to main.

---

# 5. Tests

Add focused tests proving:

1. candidate_manifest defaults context_scope owner to ENGINEERING.
2. context_scope with owner BA is rejected.
3. CONFIRMED context_scope must authenticate exact architecture authority.
4. confirmed domain authority alone cannot authenticate context_scope.
5. Foundation refresh changing context_scope marks architecture impact.
6. architecture-discovery context_scope can be projected with a matching Foundation manifest.
7. BA-owned actor/entity records remain usable in the arc42 Context & Scope projection while section ownership stays ENGINEERING.
8. full Project Foundation and producer regressions remain green.

Run at least:

python -m unittest tooling.tests.test_project_foundation -v
python -m unittest tooling.tests.test_foundation_producers -v
python -m unittest discover -s tooling/tests -q

Do not weaken existing assertions.

---

# 6. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_3_WAVE_2A_REMEDIATION_CONTEXT_SCOPE_OWNER_SPEC.md

Do not copy/rename it elsewhere.

Final tree must not contain it.

---

# 7. Required report

PHASE_3_WAVE_2A_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/project-foundation-context-scope-owner-v1

BASE:
ebf4ca36d5e6a474f0f57404087105e9672c3a94

HEAD:
<exact SHA>

FIX:
<summary>

OWNERSHIP_PROOF:
<context_scope is ENGINEERING; BA actor/domain inputs remain BA-owned inputs>

AUTHORITY_BINDING:
<architecture authority used for CONFIRMED context_scope>

KNOWLEDGE_IMPACT:
<context_scope changes route to architecture>

INTEGRATION:
<architecture-discovery + arc42 manifest compatibility>

TESTS:
<commands + pass/fail/skip counts>

SEMANTIC_CHANGES:
NONE — implementation corrected to approved architecture ownership
or explain if not NONE

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

Do not merge.
