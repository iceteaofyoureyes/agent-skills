# BA Kit RC1 provenance and redistribution

## Audit basis

- Required checkout: feature/ba-kit-rc1-packaging. The task began at HEAD 31dd25333fdcd9d3763ebba7b60ee6c37d42c8e1 with a dirty worktree containing localization, provenance, and license changes. No original change was discarded.
- The benchmark was inspected read-only at benchmark/agent-skills-v1-vi, commit b7d8d63c80c8fb2156b5267804f4081e60b51f76. Its pre-existing untracked benchmark/input/templates/SRS_TEMPLATE.docx was left untouched.
- Git history in both repositories was checked before comparing public candidates. Candidate content was compared by commit, file tree, hashes, normalized text, and distinctive content where applicable.
- The BA manifest is kits/ba/kit.yaml. tooling/lib/ba_kit.py installs ba-workflow, both core skills, all required skills, and available optional skills by copying each skill directory. The repository notices index is THIRD_PARTY_NOTICES.md.
- Classifications: EXACT_UPSTREAM, MODIFIED_UPSTREAM, PROJECT_OWNED, UNKNOWN. Redistribution statuses: READY, READY_WITH_ATTRIBUTION, BLOCKED_UNKNOWN_ORIGIN, BLOCKED_LICENSE, NOT_DISTRIBUTED.

## BA Kit required and core

| Component; role; local path | Origin and upstream source | License and copyright | Local changes; license / notice files | Evidence | Redistribution |
|---|---|---|---|---|---|
| ba-workflow; workflow; ba-workflow/ | PROJECT_OWNED; authored in this repository in commits 524f7f8, 982b1b6, and 31dd253; no upstream source | MIT approved by the Human; root LICENSE and standalone workflow license have not yet been added | Project-authored workflow, references, templates, and validators. No license file is present yet. | Target Git history and kit manifest; installer copies this directory as a skill. | BLOCKED_LICENSE |
| verification-before-completion; core; verification-before-completion/ | EXACT_UPSTREAM; obra/superpowers, skills/verification-before-completion; content commit 3be5aad3dd2400ef23b15680969f4bcd3b6d7b8b; current upstream HEAD 5bf4e78011075bcfc0dc295f0724994cd123ee71 | MIT; Copyright (c) 2025 Jesse Vincent | Content unchanged after line-ending normalization. Upstream LICENSE is present. | .skills-manager records repository and path; local content matches the upstream blob. | READY_WITH_ATTRIBUTION |
| codebase-discovery; core; codebase-discovery/ | EXACT_UPSTREAM; DiUS/agent-toolkit, skills/codebase-discovery; d43b664e2860f7a5dd5b8ae892c44fdfc5ae9dfc | MIT; Copyright (c) 2026 DiUS | All 31 files match. Bryan Signey attribution remains in SKILL.md. Upstream LICENSE is present. | Benchmark first adds the tree at 709916a0; local files match the candidate tree and content revision. | READY_WITH_ATTRIBUTION |
| requirements-gap-auditor; required; requirements-gap-auditor/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, .agents/skills/requirements-gap-auditor/SKILL.md; 1fe1950bc4759e732b036c562b0cff99675e1695 | MIT; upstream LICENSE says Copyright (c) 2026 and names no holder | Agent Skills description frontmatter only; normalized body is identical. Per-skill LICENSE is present. | Benchmark first adds the skill at 709916a0; normalized local body matches the upstream file. | READY_WITH_ATTRIBUTION |
| requirements-interrogator; required; requirements-interrogator/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, .agents/skills/requirements-interrogator/SKILL.md; 1fe1950bc4759e732b036c562b0cff99675e1695 | MIT; upstream LICENSE says Copyright (c) 2026 and names no holder | Agent Skills description frontmatter only; normalized body is identical. Per-skill LICENSE is present. | Benchmark first adds the skill at 709916a0; normalized local body matches the upstream file. | READY_WITH_ATTRIBUTION |
| requirements-quality-check; required; requirements-quality-check/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, quality/requirements-quality-check/SKILL.md; 6114b14d939622ff38b971198e2f064ac1aa11df | MIT; upstream LICENSE says Copyright (c) 2026 and names no holder | Name and description frontmatter only; normalized body is identical. Per-skill LICENSE is present. | Benchmark first adds the skill at 457bfa1; local body matches the source and benchmark mirror. | READY_WITH_ATTRIBUTION |
| business-rule-extractor; required; business-rule-extractor/ | EXACT_UPSTREAM; 45ck/business-analysis-skills, .agents/skills/business-rule-extractor/SKILL.md; 1fe1950bc4759e732b036c562b0cff99675e1695 | MIT; upstream LICENSE says Copyright (c) 2026 and names no holder | Agent Skills description frontmatter only; normalized body is identical. Per-skill LICENSE is present. | Benchmark first adds the skill at 457bfa1; normalized local body matches the upstream file. | READY_WITH_ATTRIBUTION |
| srs-function-document; required; srs-function-document/ | UNKNOWN; benchmark path .agents/skills/srs-function-document/SKILL.md first appears at 457bfa18d6e9ffe246d9ab2940c036996ec365a4; no upstream source revision established | License and copyright holder unknown | No LICENSE or source attribution is present. The existing implementation is not cleared for redistribution. | Target and benchmark blobs match at fe6b2c9086acd232ac6fe4c8d0d14c66faa714c2. No .skills-manager source record or install URL exists. History establishes first tracked appearance only, not authorship. Public exact searches did not establish a source. | BLOCKED_UNKNOWN_ORIGIN |
| document-docx; required; document-docx/ | MODIFIED_UPSTREAM; vasilyu1983/AI-Agents-public, frameworks/shared-skills/skills/document-docx; da9d28fd0f5427f18a15d3fb363ab3651e6625ca | MIT; Copyright (c) 2025-2026 Vasiliy Uvarov | Learning files and generated caches removed; learning workflow and related skills made optional; unavailable sibling links removed; two scripts differ only by a trailing blank line. Per-skill LICENSE is present. | Benchmark introduction at 2c4355d contains 23 files; 22 blob IDs match the candidate snapshot. | READY_WITH_ATTRIBUTION |
| drawio-skill; required; drawio-skill/ | EXACT_UPSTREAM; Agents365-ai/drawio-skill, skills/drawio-skill; 7aa92f73819766eb914fffac66762cf2adb5d828 | MIT; Copyright (c) 2026 Agents365-ai | Tree matches release 3.4.0. Existing LICENSE and author/homepage metadata are retained. | Benchmark first adds the skill at 457bfa1; upstream path and version are in skill metadata; tree comparison matches. | READY_WITH_ATTRIBUTION |

## BA Kit optional skills

| Component; role; local path | Origin and upstream source | License and copyright | Local changes; license / notice files | Evidence | Redistribution |
|---|---|---|---|---|---|
| product-design-and-ux; optional; product-design-and-ux/ | EXACT_UPSTREAM; magnus919/agent-skills, product-design-and-ux; 035e58d3e39690361596901ab8f17222ab9baf02 | MIT; Copyright (c) 2026 Magnus Hedemark | All 19 files match. Per-skill LICENSE is present. | .skills-manager records source repository and path; each local file matches. | READY_WITH_ATTRIBUTION |
| frontend-design; optional; frontend-design/ | EXACT_UPSTREAM; anthropics/skills, skills/frontend-design; 34040c9c568585f6929bedeaad110ad08f079624 | Apache-2.0; LICENSE.txt names no copyright holder | Both files, including LICENSE.txt, match. | .skills-manager records source path; two-file tree and blobs match. | READY_WITH_ATTRIBUTION |
| impeccable; optional; impeccable/ | MODIFIED_UPSTREAM; pbakaus/impeccable, .agents/skills/impeccable; 53 files from cd12f8660e2dde57b9615c8a6b8ea674101f9cfc (4.3.1), three references from 6a93a352936ac7fbb1898a239ddae1f8c3828150 (4.4.0) | Apache-2.0; Copyright 2025 Paul Bakaus. Upstream NOTICE attributes ios.md and android.md reference material to ehmo’s platform-design-skills under MIT. | adapt.md, audit.md, and harden.md contain documented local additions. Upstream LICENSE and NOTICE are present. | .skills-manager records upstream path and version 4.3.1; 53/56 files match 4.3.1 and the remainder match 4.4.0. | READY_WITH_ATTRIBUTION |
| playwright; optional; playwright/ | EXACT_UPSTREAM; openai/skills, skills/.curated/playwright; 49f948faa9258a0c61caceaf225e179651397431 | Apache-2.0; Copyright (c) Microsoft Corporation | Nine-file tree matches; LICENSE.txt differs only in line endings. Upstream NOTICE.txt is retained and attributes microsoft/playwright-cli and skills/playwright-cli/SKILL.md; that dependency revision is not stated in the notice. | .skills-manager records OpenAI source path; local SKILL.md and remaining files match the source tree. | READY_WITH_ATTRIBUTION |
| web-accessibility; optional; web-accessibility/ | EXACT_UPSTREAM; magnus919/agent-skills, web-accessibility; f7819d0f2048d1b71e0c261c660476965aa26602 | MIT; Copyright (c) 2026 Magnus Hedemark | All 17 files match. Per-skill LICENSE is present. | .skills-manager records source repository and path; each local file matches. | READY_WITH_ATTRIBUTION |

## Other repository content

The project-owned scope selected by the Human is ba-workflow/, kits/, tooling/, docs/, core/, repository-owned READMEs, and project-owned examples. Target Git history records this material in commits 524f7f8, 982b1b6, and 31dd253. MIT is approved, but the root LICENSE and the standalone ba-workflow/LICENSE have not yet been added; these project-owned copies remain BLOCKED_LICENSE in this audit snapshot. The root license will not change any third-party license.

The webapp-testing/ skill is outside BA Kit. Its six-file tree, including LICENSE.txt, matches anthropics/skills at 34040c9c568585f6929bedeaad110ad08f079624; the Apache-2.0 file names Copyright 2026 Anthropic, PBC.

Whole-repository publication remains blocked by non-BA imports whose content and license packaging have not completed commit-bound audits:

- addyosmani/agent-skills: api-and-interface-design, ci-cd-and-automation, code-review-and-quality, constraint-driven-development, documentation-and-adrs, observability-and-instrumentation, performance-optimization, security-and-hardening, shipping-and-launch, and test-driven-development.
- vercel-labs/agent-skills: web-design-guidelines and vercel-react-best-practices. web-design-guidelines matches current upstream commit 063bee94c3f4df8453406c830b0a7df0f2860278 and its repository README declares MIT, but the local skill has no LICENSE file.
- magnus919/agent-skills: product-discovery and product-methodology.
- obra/superpowers: systematic-debugging.
- nextlevelbuilder/ui-ux-pro-max-skill: ui-ux-pro-max.
- mattpocock/skills: to-spec.

The tracked .skills-manager/ tree was introduced and updated in auto-backup commits, including 9ea9b6d through 3ea1b84. Its schema says created_by: skills-manager. It contains source references and scenario/skill metadata, but its authorship and license scope are not established and its source records do not pin content revisions. The BA Kit installer does not copy this tree, so it is outside the BA Kit payload; because Git tracks it, it remains a whole-repository publication blocker pending an ownership/license decision or an explicit publication-scope decision.

## Current blockers

- srs-function-document is BLOCKED_UNKNOWN_ORIGIN. The Human has authorized a project-owned behavioral reimplementation from the BA Kit contract; it has not yet replaced the existing implementation in this audit snapshot.
- Project-owned BA Kit content is BLOCKED_LICENSE until the approved MIT license files are added.
- Non-BA imported skills listed above block whole-repository publication.

No third-party skill is relicensed by the project MIT license.
