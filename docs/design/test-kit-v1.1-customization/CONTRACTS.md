# Test Kit V1.1 — Customization Contracts

## 1. Project profile

Canonical project path:

```text
<project-root>/.test-kit/project.yaml
```

Required top-level fields for V1.1:

```yaml
schema_version: 1
profile:
  id: <non-empty stable id>
  revision: <non-empty revision>
rules:
  common: []
  test_design: []
  testcases: []
templates:
  excel:
    path: <optional relative .xlsx path>
```

Unknown fields should fail validation in V1.1 rather than being silently ignored.

Rule paths must:

- be relative to `.test-kit/`;
- remain inside the project-owned `.test-kit/` tree after resolution;
- identify regular UTF-8 text files;
- be unique after normalized path resolution;
- be hashed from exact bytes.

Template paths follow the existing Excel template inspector/security policy and are not testing-policy authority.

## 2. Policy identity

Resolve two stage-specific snapshots.

### Design policy snapshot

Includes:

- profile id;
- profile revision;
- `rules.common`;
- `rules.test_design`;
- exact path + SHA-256 for every referenced file;
- project TEA team-customization file identity when it participates in the run.

### Case policy snapshot

Includes:

- profile id;
- profile revision;
- `rules.common`;
- `rules.testcases`;
- exact path + SHA-256 for every referenced file.

Each snapshot has a deterministic compact-JSON semantic payload and SHA-256.

Suggested ref IDs:

```text
TEST_POLICY:DESIGN:<profile-id>
TEST_POLICY:CASES:<profile-id>
```

These refs use existing gate `input_refs` shape:

```json
{"id":"TEST_POLICY:DESIGN:portal-testing","revision":"1","sha256":"..."}
```

## 3. TEA integration

Reuse the upstream customization mechanism.

Production Design invocation requires consistency between Test Kit policy and the project/team TEA customization surface. The implementation may validate or generate a minimal project-owned TEA bridge, but MUST NOT edit the pinned skill's `customize.toml`.

The effective TEA policy must load:

```text
.test-kit/rules/common.md
.test-kit/rules/test-design.md
```

through upstream `workflow.persistent_facts`.

A present `_bmad/custom/bmad-testarch-test-design.user.toml` is production-blocking in the initial V1.1 contract because it can create machine-specific output. TEST_ONLY use requires explicit opt-in and evidence.

## 4. Testcase integration

Before native `create-test-cases` invocation, Test Kit copies the resolved policy snapshot into the run:

```text
inputs/project-policy/
├── policy-snapshot.json
├── common/...
└── testcases/...
```

The invocation prompt identifies these files as **TESTING POLICY / NON-AUTHORITATIVE GUIDANCE** and states that BA, Design, and execution oracles override any conflicting instruction.

Policy must not expand coverage beyond the approved Design. It may change how an approved scenario is decomposed into manual cases only within existing Design/BA semantics.

## 5. Gate binding and stale behavior

Design Gate input refs become:

```text
current BA refs
+ current Design Policy ref
```

Case Gate input refs become:

```text
current BA refs
+ exact approved Design ref
+ current Case Policy ref
```

If the relevant policy digest changes after submission to review, approval fails closed and the artifact must re-enter an appropriate revision/review path.

Presentation-only Excel template changes do not invalidate Design or Case approval.

## 6. Authority-conflict behavior

V1.1 does not attempt to treat arbitrary natural-language policy text as business truth.

The safety model is layered:

1. prompt explicitly marks policy non-authoritative;
2. policy files are provenance-tracked;
3. Design normalization/validation still anchors FR/BR and UNKNOWN;
4. Case normalization/validation still anchors BA + approved Design;
5. execution details still require approved execution-oracle refs;
6. Human reviews the exact canonical snapshot.

If policy-guided output conflicts with business authority, existing validators must reject it or the Human must request changes; policy never resolves the conflict by precedence.

## 7. Excel project template

If no explicit Human template is supplied and `templates.excel.path` exists, it becomes `PROJECT_TEMPLATE`.

Precedence remains:

```text
HUMAN_SUPPLIED_APPROVED_TEMPLATE
→ PROJECT_TEMPLATE
→ DEFAULT_TEMPLATE
```

Ambiguous/unsupported project template mapping remains `CANNOT_PROJECT_TEMPLATE`; there is no silent fallback once the project template has been selected by policy.

## 8. Doctor

Doctor V1.1 checks at least:

- profile syntax/schema;
- path traversal/out-of-root refs;
- missing rule files;
- invalid UTF-8;
- duplicate resolved refs;
- rule SHA resolution;
- TEA project customization consistency;
- production-blocking `.user.toml`;
- Excel project template presence/type;
- installed Test Kit package integrity remains independent from project-owned policy.

Doctor reports project-policy findings separately from installed-package drift.
