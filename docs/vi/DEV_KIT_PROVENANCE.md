# Dev Kit V1 — Provenance Audit

> Snapshot: 2026-09-25  
> Status: **ASSEMBLED_WITH_ONE_MINIMAL_UPSTREAM_ADAPTATION**. Selected payload is vendored with license evidence, but Dev Kit is still not runtime-accepted or RC.

## 1. Audit policy

Dev Kit uses these classifications:

- **EXACT_UPSTREAM** — vendored content must match the pinned upstream blob/tree.
- **MODIFIED_UPSTREAM** — any local content modification requires an explicit diff/patch record.
- **PROJECT_OWNED** — authored in this repository.
- **RUNTIME_DEPENDENCY** — required or optional external tool/framework; not redistributed by the Dev Kit payload.
- **DESIGN_INFLUENCE** — concept/pattern only; no source copied.

Selection priority:

```text
EXACT_UPSTREAM
→ MINIMAL_ADAPTATION
→ PROJECT_OWNED only when the integration contract is genuinely specific to this AI-SDLC
```

Every vendored component must record repo, source path, release/tag, exact commit, license, included files, excluded files, dependency closure and blob/hash evidence.

## 2. GitHub Spec Kit

- Repository: `github/spec-kit`
- Release: `v1.0.11`
- Commit: `8147943512404afb9d99c6252cb9bf84369fd0b0`
- License: MIT
- License blob: `28a50fa22639e32febe14e4ffc7a732b0ba8c90a`
- Classification: **RUNTIME_DEPENDENCY**
- Distribution: not vendored into Dev Kit in this phase.

Selected usage:

- workflow execution;
- persisted run state / resume;
- bundle and distribution primitives.

Dev Kit V1 deliberately does **not** call core `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.analyze` or `speckit.converge`. Those commands depend on Spec Kit's feature `spec.md` semantics. Generating a second feature spec from the Approved BA Baseline would create another WHAT representation and is outside the V1 authority model.

## 3. Addy Agent Skills

- Repository: `addyosmani/agent-skills`
- Release: `0.6.10`
- Commit: `c004a74784a08295d52749b04cda634125b9a581`
- License: MIT
- Copyright: Copyright (c) 2025 Addy Osmani
- License blob: `d67778ada6b9cda6227e9130da182c13e73c8b2e`
- Classification: **EXACT_UPSTREAM** candidate.

### Technical planner — minimal adaptation

`planning-and-task-breakdown` was selected after comparing the pinned Addy planner with Superpowers `writing-plans` and Matt Pocock `to-tickets`.

- Upstream source: `skills/planning-and-task-breakdown/SKILL.md`
- Upstream blob: `296249b64334bcfd1aeaefd27b9e3e5494e38ec0`
- Local blob: `670508158bb832d58266deebc833ea9859e2bc2d`
- Classification: **MODIFIED_UPSTREAM**
- Shared reference: `references/definition-of-done.md` (already in the selected closure)

Exactly two policy lines changed:

1. an unconditional “Review with human before proceeding” checkpoint became conditional on the Dev Kit risk policy;
2. unconditional final Human plan approval became a Human/Tech Lead gate only when risk policy requires it.

Planning mechanics, dependency mapping, vertical slicing, sizing, plan/task templates, acceptance criteria and verification instructions are otherwise unchanged.

Reason: the upstream planner is the closest fit for an already-approved external spec, but its mandatory Human checkpoints conflict with the Dev Kit bounded-autonomy contract for normal-risk work.

### Selected skill blobs

| Skill | Upstream blob |
|---|---|
| incremental-implementation | `9c4f49bc841adb3c0f98baaa9eabd435a5b64ef9` |
| test-driven-development | `8898bcbba4c4f6acca473ece95e82105bd9cfea0` |
| debugging-and-error-recovery | `356da20365a7cd6825b4ffad14be39280c92cdfc` |
| code-review-and-quality | `7dfa56362fa65fff450ee5aa02393b85b9c26d85` |
| security-and-hardening | `c168e65e0d8e2ce1ec48bdaf0c1a76c0a4aa9d30` |
| api-and-interface-design | `820d6d981f90b7802e0ea8b75bb966a3d78b8d0f` |
| source-driven-development | `2704f0e130bc4659951aa552373914b2d63d18c9` |
| performance-optimization | `cbc7e950a6f376d25ac88cf310d5a48555db2ec1` |
| observability-and-instrumentation | `84d9cb373467fe0e15236e190833ecc90f840c38` |

### Shared reference closure

The selected upstream skills reference shared repository-level files. These are part of the selected dependency closure:

| Reference | Blob |
|---|---|
| references/definition-of-done.md | `35e39f9e15f6dd0ff4725a6e5cbce7f2aa69064a` |
| references/testing-patterns.md | `bc96e271ad241ca567f06d21c6ecc001455b80f1` |
| references/security-checklist.md | `b7df3eb04178e4a24bfa405431bf8dee6a89a8c4` |
| references/performance-checklist.md | `ba9744fe60dbe4f04f3f907029638d923158d7a2` |
| references/observability-checklist.md | `ad40d7aa3fca5d2091fa45be234c14aee22c3588` |

### Soft references deliberately not bundled

The selected skills mention these other upstream skills:

- `git-workflow-and-versioning`;
- `browser-testing-with-devtools`;
- `shipping-and-launch`.

They are guidance/“see also” references, not required execution dependencies for the selected V1 capabilities. V1 does not expand the skill set solely to satisfy those soft references. If benchmark/runtime evidence shows a real missing capability, selection is revisited explicitly.

### Packaging decision

Do **not** flatten selected Addy skills into repository root.

Upstream paths such as `../../references/security-checklist.md` are correct under this preserved shape:

```text
kits/dev/plugin/
├── plugin.json
├── skills/
│   ├── code-review-and-quality/
│   │   └── SKILL.md
│   └── ...
└── references/
    ├── security-checklist.md
    └── ...
```

This preserves skill contents as **EXACT_UPSTREAM** instead of rewriting relative paths and creating modified forks.

## 4. Superpowers verification

Existing canonical repository copy:

- Repository: `obra/superpowers`
- Source: `skills/verification-before-completion`
- Provenance commit currently recorded by BA Kit: `3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b`
- License: MIT
- Classification: **EXACT_UPSTREAM_EXISTING_CANONICAL**

V1 policy: reuse the existing canonical behavior; do not silently upgrade it just for Dev Kit. An upgrade requires BA + Dev cross-kit regression.

## 5. Superpowers review-package

Candidate utility:

- Repository: `obra/superpowers`
- Release: `v6.4.1`
- Commit: `5bf4e78011075bcfc0dc295f0724994cd123ee71`
- Source path: `skills/subagent-driven-development/scripts/review-package`
- Source blob: `fa7625f053dc852200ddd497662508ff1ae40bb1`
- License: MIT
- License blob: `abf0390320aa14406af7a520b9b0739fdda9bf08`
- Classification: **EXACT_UPSTREAM_CANDIDATE**

If vendored, Dev Kit passes an explicit output path so the script does not require the rest of Superpowers SDD workspace helpers.

The upstream scoped re-review prompt is **DESIGN_INFLUENCE** only for V1; Dev Kit authors its own bounded re-review contract instead of copying the full Superpowers task-controller assumptions.

## 6. codebase-memory-mcp

- Repository: `DeusData/codebase-memory-mcp`
- Release: `v0.11.0`
- Commit: `8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798`
- License: MIT
- License blob: `0b95352746a97a8cf2d1f3ba568bc7bb5e514d1f`
- Classification: **RUNTIME_DEPENDENCY**
- Distribution: not vendored.

CBM is conditional structural evidence. Important graph findings must be verified against source before they become Impact Manifest facts.

## 7. requirements-gap-auditor

Existing canonical repository capability:

- Repository: `45ck/business-analysis-skills`
- Source path: `.agents/skills/requirements-gap-auditor/SKILL.md`
- Commit: `1fe1950bc4759e732b036c562b0cff99675e1695`
- License: MIT
- Classification: **EXACT_UPSTREAM_EXISTING_CANONICAL**

Dev Kit use is readiness-only:

```text
Approved BA Baseline
→ implementable without inventing business semantics?
→ READY_FOR_PLANNING | NEEDS_BA_CLARIFICATION
```

It must not silently rewrite the approved business baseline.

## 8. Redistribution gate

Before any Dev Kit RC claim:

- vendored Addy files must match the blobs above;
- Addy MIT license/attribution must travel with the distributed payload;
- any vendored Superpowers utility must carry its applicable license/notice;
- `THIRD_PARTY_NOTICES.md` must list the actual Dev Kit payload, not just candidate dependencies;
- runtime-only dependencies must remain clearly marked as not redistributed;
- Doctor must verify expected selected-content hashes;
- any local edit changes classification from EXACT_UPSTREAM to MODIFIED_UPSTREAM and requires a recorded diff.

Current status:

```text
DESIGN / INPUT AUDIT: PASS
VENDORED PAYLOAD: ASSEMBLED
ADDY EXACT FILE CHECKS: PASS
PLANNING MINIMAL PATCH: RECORDED
REDISTRIBUTION EVIDENCE FOR PLUGIN PAYLOAD: READY_WITH_ATTRIBUTION
RUNTIME ACCEPTANCE: NOT RUN
```
