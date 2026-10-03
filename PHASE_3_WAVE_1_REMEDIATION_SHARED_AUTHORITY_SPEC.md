# Phase 3 — Wave 1 Remediation Spec
## Shared Authority Path Compatibility

Status: READY_FOR_AGENT_EXECUTION
Required model: LUNA Medium
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: 431a62c0bb68f050ff1cc092f47935f7462ef4cc
Source branch: feat/project-foundation-v1-wave1
Suggested implementation branch: fix/project-foundation-shared-authority-path-v1

TEMPORARY BOOTSTRAP ARTIFACT:
Read this file from the latest remote source branch, implement exactly this remediation, then DELETE this file from the remediation branch before final commit/report.

---

# 1. Problem

Phase 2 Shared Project Policy contract explicitly permits multiple authority domains to share the same document/location.

The current Phase 3 Wave 1 workflow contradicts that contract.

Current offending behavior in:

shared/sdlc/foundation/workflow.py

start() currently computes all policy authority paths and rejects any duplicate path:

authority_paths = [...]
if len(set(authority_paths)) != len(authority_paths):
    raise ValueError('duplicate/conflicting project authority locations')

This incorrectly treats intentional shared authority entry points as conflicts.

A Wave 3.1 test also encodes this wrong behavior by expecting a shared product/domain path to fail.

This is a Shared Core contract compatibility violation.

---

# 2. Required behavior

A project MUST be allowed to declare the same exact authority entry-point document for more than one semantic authority domain when Project Policy does so explicitly.

Examples that MUST be valid:

- product and domain both point to one canonical project knowledge index/document.
- architecture and testing may share an approved project-level index if the project deliberately declares it.

Do NOT infer shared authority automatically.
Only accept it when the exact same path is explicitly declared by Project Policy.

This does NOT weaken conflict detection.

Still surface/block when:

- the same authority domain has multiple competing explicit claims;
- an authority claim differs from the Project Policy canonical path for that domain;
- current-system evidence contradicts canonical authority;
- repository ownership is ambiguous;
- a claimed reference is unsafe/missing/hash-drifted.

"Shared exact canonical path across domains" is not itself a conflict.

---

# 3. Scope

Make the smallest compatible change.

Required:

1. Remove the blanket duplicate-authority-path rejection from Foundation start logic.
2. Preserve all existing policy/topology/path/reference validation.
3. Correct tests that currently expect shared exact authority paths to fail.
4. Add positive regression proving two or more authority domains may intentionally share one exact policy path.
5. Add/retain negative regressions proving competing claims for the SAME domain still surface as AUTHORITY_CONFLICT.
6. Update durable Project Foundation docs only if they currently imply authority paths must be unique.

Do NOT redesign authority schemas.

---

# 4. Contract source of truth

The approved Phase 2 contract remains authoritative.

In particular:

- Shared Project Policy locations are routing declarations.
- Authority locations may share a document.
- Validation does not make the document approved.
- Duplicate/conflicting evidence is about ambiguity/competing claims, not intentional shared routing.

Do not modify Phase 2 semantics to match the Wave 3.1 implementation.

Fix Wave 3.1 to conform to Phase 2.

---

# 5. Forbidden changes

Do NOT:

- alter Human Gate semantics;
- alter Foundation approval binding;
- alter Foundation manifest schema;
- change FR/BR/BAREF behavior;
- change Delivery Manifest V2;
- change inventory boundaries;
- change promotion behavior;
- change model/role ownership;
- perform Phase 3 Wave 2 work;
- touch Digital Wedding;
- merge to main.

---

# 6. Tests

Before change, reproduce the failing contract scenario logically/currently:

- Project Policy with product and domain pointing to the same exact canonical document is rejected by current workflow.

After change:

- same exact shared path is accepted;
- Foundation workflow can proceed to review according to normal rules;
- competing authority claims for one domain still create AUTHORITY_CONFLICT;
- full existing test suite remains green.

Run at least:

python -m unittest tooling.tests.test_project_foundation -v
python -m unittest discover -s tooling/tests -q

Do not weaken unrelated assertions.

---

# 7. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_3_WAVE_1_REMEDIATION_SHARED_AUTHORITY_SPEC.md

Do not copy or rename it elsewhere.

Final tree must not contain it.

---

# 8. Required report

PHASE_3_WAVE_1_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/project-foundation-shared-authority-path-v1

BASE:
431a62c0bb68f050ff1cc092f47935f7462ef4cc

HEAD:
<exact SHA>

FIX:
<summary>

CONTRACT_COMPATIBILITY:
<proof intentional shared paths allowed and competing same-domain claims still conflict>

TESTS:
<commands + counts>

SEMANTIC_CHANGES:
NONE — implementation corrected to approved Phase 2 contract
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
