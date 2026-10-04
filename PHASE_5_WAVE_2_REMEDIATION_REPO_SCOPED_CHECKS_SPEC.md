# Phase 5 — Wave 2 Remediation Spec
## Repository-Scoped Engineering Checks

Status: READY_FOR_AGENT_EXECUTION
Required model: SOL High
Repository: iceteaofyoureyes/agent-skills
Behavioral base commit: 2085778f6225b378f70a445c26c913e1b7d693f6
Source branch: feat/dev-kit-vnext-wave2
Suggested implementation branch: fix/dev-vnext-repository-scoped-checks-v1

TEMPORARY BOOTSTRAP ARTIFACT:
Read this file from the latest remote source branch, implement only this remediation, then DELETE this file before final commit/report.
The final remediation tree must not contain this file.

---

# 1. Problem

Wave 2 claims production-grade multi-repository verification, but Dev VNext CHECK currently has only:

- name
- category
- command

It has no repository binding.

The runtime therefore executes every engineering check in every implementation repository.

That only works when every repository happens to use the same toolchain/command.

A real multi-repo feature may look like:

- frontend -> npm test
- backend -> mvn test
- worker -> pytest

The current contract cannot represent that safely.

The existing multi-repo synthetic test uses the same Python check command in both repositories, so it does not catch this limitation.

This remediation must make engineering checks explicitly repository-scoped without redesigning the rest of Dev VNext.

---

# 2. Required contract

Each VNext engineering check must resolve to exactly one implementation repository.

Preferred V2 check shape:

{
  "name": "...",
  "repository_id": "backend",
  "category": "UNIT",
  "command": ["..."]
}

Keep the contract simple.

Do NOT introduce:
- workflow matrices;
- generic execution graphs;
- cross-repo check DSLs;
- check inheritance;
- arbitrary cwd fields.

repository_id is the execution target.

---

# 3. Single-repository compatibility

To avoid needless verbosity for a one-repository run, one of these approaches is acceptable:

A. repository_id is always required; runtime/templates fill it explicitly.

or

B. repository_id may be omitted only when the run has exactly one IMPLEMENTATION repository, and runtime canonicalizes it immediately to that repository before persisted V2 state/snapshot.

Preferred approach: A if migration impact is small.

The persisted canonical VNext state/snapshot/handoff verification should not be ambiguous.

For multi-repository runs, repository_id MUST always be explicit and valid.

---

# 4. Validation rules

For every check:

1. repository_id exists in the run repository set.
2. repository_id refers to role IMPLEMENTATION.
3. check name uniqueness is enforced in a way that remains unambiguous.
   Preferred: name unique across the run.
4. command remains non-empty argv.
5. category remains one of the existing engineering categories.
6. unsupported fields fail closed.
7. READ_ONLY repositories cannot receive engineering execution checks.

The technical snapshot continues to bind the exact check set.

Any change to:
- repository_id;
- command;
- category;
- name

after technical approval invalidates the exact snapshot/gate as it already does.

---

# 5. Runtime execution

Update DevRuntime.verify() so each check executes only in:

check.repository_id

Do NOT iterate each check across all implementation repositories.

Evidence for each check must record the repository identity explicitly.

Expected evidence should contain enough information to prove:

- repository_id
- command
- exit code
- PASS/FAIL
- exact snapshot
- exact implementation revision for that repository
- evidence ref

The overall verification object may continue binding all implementation repository revisions.

---

# 6. Multi-repository coverage

Add a real heterogeneous multi-repo regression.

Example neutral fixture:

repo A:
- check command A that succeeds only in repo A

repo B:
- check command B that succeeds only in repo B

If either command is executed in the wrong repository, the test must fail.

The final runtime acceptance must prove:

- repo A check only ran in A;
- repo B check only ran in B;
- both exact output revisions are bound;
- READY_FOR_TEST succeeds when both pass.

Also add negatives:

1. unknown repository_id rejected;
2. READ_ONLY repository_id rejected;
3. missing repository_id rejected/canonicalized only according to the chosen single-repo rule;
4. check repository binding drift after planning invalidates exact authorization;
5. two repositories with heterogeneous commands work;
6. failing check in one repository blocks READY_FOR_TEST.

---

# 7. Legacy V1

Do not change V1 check schema or V1 LEGACY_COMPAT behavior.

This remediation applies to Dev VNext only.

Do not rewrite old V1 fixtures just to mimic VNext.

---

# 8. Scope

Expected files include:

- tooling/lib/dev_vnext.py
- tooling/lib/dev_vnext_runtime.py
- tooling/lib/dev_vnext_cli.py if start/request normalization is needed
- Wave 1 / Wave 2 VNext tests
- VNext runtime examples/templates only if already present in source scope

Do not perform Wave 3 full packaging/docs migration.

Update installer/provenance only if the current repository's tests require regeneration for changed runtime bytes.

---

# 9. Frozen contracts

Do NOT change:

- BA VNext semantics;
- Project Foundation;
- Delivery Manifest;
- Dev lifecycle;
- authority modes;
- Engineering Gap;
- ED-* semantics;
- technical Human gate semantics;
- FR/BR coverage;
- READY_FOR_TEST meaning;
- Spec Kit boundary.

This remediation only corrects engineering check-to-repository binding.

---

# 10. Tests

Run at least:

python -m unittest tooling.tests.test_dev_vnext -v
python -m unittest tooling.tests.test_dev_vnext_runtime -v
python -m unittest tooling.tests.test_dev_vnext_runtime_acceptance -v
python -m unittest tooling.tests.test_dev_vnext_cli -v
python -m unittest discover -s tooling/tests -q

Mandatory regression:
heterogeneous multi-repo commands that fail if executed in the wrong repository.

Do not weaken existing tests.

git diff --check must pass.

---

# 11. Temporary spec cleanup

Before final commit/report DELETE:

PHASE_5_WAVE_2_REMEDIATION_REPO_SCOPED_CHECKS_SPEC.md

Do not copy or rename it elsewhere.

Final tree must not contain it.

---

# 12. Required report

PHASE_5_WAVE_2_REMEDIATION_STATUS:
PASS | BLOCKED | FAIL

BRANCH:
fix/dev-vnext-repository-scoped-checks-v1

BASE:
2085778f6225b378f70a445c26c913e1b7d693f6

HEAD:
<exact SHA>

CHECK_CONTRACT:
<repository binding shape>

SINGLE_REPO_BEHAVIOR:
<explicit/canonicalized rule>

RUNTIME_EXECUTION:
<one check -> one repository>

EVIDENCE_BINDING:
<repository-specific evidence>

HETEROGENEOUS_MULTI_REPO:
<proof>

LEGACY_COMPAT:
<V1 unchanged>

TESTS:
<commands + pass/fail/skip>

SEMANTIC_CHANGES:
Repository-scoped VNext engineering checks only.

BLOCKERS:
<list>

TEMP_SPEC_CLEANUP:
REMOVED

TEMP_SPEC_PRESENT_IN_FINAL_TREE:
NO

REMOTE_PUSH:
PASS | FAIL

Do not merge.
