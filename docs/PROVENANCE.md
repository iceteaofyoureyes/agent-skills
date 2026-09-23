# BA Kit migration inventory and provenance

Inventory captured before production changes. The source of BA behavior is the benchmark branch `benchmark/agent-skills-v1-vi` at `b7d8d63c80c8fb2156b5267804f4081e60b51f76`; the benchmark worktree had one pre-existing untracked `SRS_TEMPLATE.docx`, which was left untouched. The requested `BA_AGENT_CURRENT_STATUS_2026-09-23.md` was absent. The latest delivery reports instead say DOCX structural/content QA passed while final DOCX visual QA remains pending.

## Migration inventory

| Skill | Benchmark source / purpose | Proven evidence | Ownership evidence | Target action |
|---|---|---|---|---|
| `codebase-discovery` | `.agents/skills/codebase-discovery`; brownfield system/domain discovery | CR-001 Stage 1 `project-context.md` | Skill credits Bryan Signey for DiUS; upstream URL/revision/license not recorded | MIGRATE; Core |
| `requirements-gap-auditor` | `.agents/skills/requirements-gap-auditor`; completeness/gap review | Stage 2 `review.md` | Benchmark-local source; no upstream attribution or license declared | MIGRATE |
| `requirements-interrogator` | `.agents/skills/requirements-interrogator`; clarification and question flow | Stage 2 `open-questions.md` and BA answers | Benchmark-local source; no upstream attribution or license declared | MIGRATE |
| `requirements-quality-check` | `.agents/skills/requirements-quality-check`; SRS and traceability review | Stage 7 `quality-review.md` verdict `PASS` | Benchmark-local source; no upstream attribution or license declared | MIGRATE |
| `business-rule-extractor` | `.agents/skills/business-rule-extractor`; rules register | Stage 3 register contains 59 rules traced to confirmed evidence | Benchmark-local source; no upstream attribution or license declared | MIGRATE |
| `srs-function-document` | `.agents/skills/srs-function-document`; Vietnamese function-level SRS | Stage 5 SRS and Stage 7/9 content checks | Benchmark-local source; no upstream attribution or license declared | MIGRATE |
| `document-docx` | `.agents/skills/document-docx`; source-backed Word delivery/edit/review | Stage 9 structural/content QA; Stage 6a DOCX edit cases; visual QA pending | Skill says version 1.1; no source repository/license recorded | MIGRATE; omitted benchmark-local learning notes |
| `drawio-skill` | `.agents/skills/drawio-skill`; editable business diagrams and safe edits | Stage 6/6b structure and template-conformance checks passed | MIT text credits Agents365-ai; upstream URL/revision not recorded | MIGRATE; retain `LICENSE` |
| `verification-before-completion` | No benchmark-local folder; evidence/completion gate | Existing target root skill | Present at target baseline | REUSE_EXISTING; Core |
| `product-design-and-ux` | Optional user-facing behavior/prototype capability | Optional; not required by semantic BA contract | Present at target baseline | REUSE_EXISTING; optional |
| `frontend-design` | Optional visual design capability | Optional; not required by semantic BA contract | Present at target baseline | REUSE_EXISTING; optional |
| `impeccable` | Optional visual review/refinement capability | Optional; not required by semantic BA contract | Present at target baseline | REUSE_EXISTING; optional |
| `playwright` | Optional browser validation | Optional; not required by semantic BA contract | Present at target baseline | REUSE_EXISTING; optional |
| `web-accessibility` | Optional accessibility review | Optional; not required by semantic BA contract | Present at target baseline | REUSE_EXISTING; optional |

The target also has `product-discovery`, `product-methodology` and `to-spec`. They were inspected but do not replace brownfield system discovery, risk-based requirements gap/interrogation, BA source-authority controls, or the Vietnamese function-level SRS used in this benchmark.

## Dependency provenance

`OWNED`, `UPSTREAM` and `FORKED_UPSTREAM` describe the recorded source relationship, not a legal conclusion. A missing permission/license remains `UNKNOWN` and blocks public release until resolved. “Local-canonical” means the files are the current canonical copy in `agent-skills`; it does not assert copyright ownership when the original source is unknown.

| Skill | Class | Source repository, path, revision/version | License evidence | Local packaging changes |
|---|---|---|---|---|
| `ba-workflow` | OWNED | `iceteaofyoureyes/agent-skills`, `ba-workflow/`; new on `feature/ba-kit-rc1-packaging` | No repository root license | New project-owned orchestration and contracts based on cited benchmark evidence |
| `verification-before-completion` | OWNED (local-canonical; original source unknown) | `iceteaofyoureyes/agent-skills@a54ac14f48d762dbcbee044ab245b6a86e21b7b8`, `verification-before-completion/` | No skill license/front-matter license; no root license | Reused unchanged |
| `codebase-discovery` | UPSTREAM | Benchmark source `.agents/skills/codebase-discovery/` at `709916a0e530e3df2982192d1ad4c06752111585`; credits Bryan Signey for DiUS; upstream repo/revision unavailable | No license file or declared license found | Copied as-is; author credit retained |
| `requirements-gap-auditor` | OWNED (benchmark-local; authorship not declared) | `iceteaofyoureyes/ai-sdlc-framework-benchmark@709916a0e530e3df2982192d1ad4c06752111585`, `.agents/skills/requirements-gap-auditor/SKILL.md` | No skill license; benchmark repo has no root license | Added required Agent Skills `description` frontmatter; retained body; `requirements-discovery-pack` origin is not recorded |
| `requirements-interrogator` | OWNED (benchmark-local; authorship not declared) | Same benchmark revision, `.agents/skills/requirements-interrogator/SKILL.md` | No skill license; benchmark repo has no root license | Added required Agent Skills `description` frontmatter; retained body; `requirements-discovery-pack` origin is not recorded |
| `requirements-quality-check` | OWNED (benchmark-local; authorship not declared) | `iceteaofyoureyes/ai-sdlc-framework-benchmark@457bfa18d6e9ffe246d9ab2940c036996ec365a4`, `.agents/skills/requirements-quality-check/SKILL.md` | No skill license; benchmark repo has no root license | Copied as-is |
| `business-rule-extractor` | OWNED (benchmark-local; authorship not declared) | Same benchmark revision, `.agents/skills/business-rule-extractor/SKILL.md` | No skill license; benchmark repo has no root license | Added required Agent Skills `description` frontmatter; retained body; `business-analysis-pack` origin is not recorded |
| `srs-function-document` | OWNED (benchmark-local; authorship not declared) | Same benchmark revision, `.agents/skills/srs-function-document/SKILL.md` | No skill license; benchmark repo has no root license | Copied as-is |
| `document-docx` | OWNED (benchmark-local; upstream provenance not recorded) | `iceteaofyoureyes/ai-sdlc-framework-benchmark@2c4355dcb4233e6af3328a55820054f6a1b4d39e`, `.agents/skills/document-docx/`; declared version 1.1 | No skill license; benchmark repo has no root license. The linked documentation sources are not a redistribution license. | Excluded benchmark-local learning notes, made related skills and learning workflow optional, removed unavailable sibling links, excluded generated cache files, and normalized trailing blank lines in two scripts |
| `drawio-skill` | UPSTREAM | Benchmark source `.agents/skills/drawio-skill/` at `457bfa18d6e9ffe246d9ab2940c036996ec365a4`; copyright notice credits Agents365-ai; source URL/revision unavailable | MIT license included in full | Copied without editing; `LICENSE` retained |
| `product-design-and-ux` | UPSTREAM (remote origin unavailable) | Target baseline `agent-skills@a54ac14f48d762dbcbee044ab245b6a86e21b7b8`, `product-design-and-ux/`; benchmark provenance points to local `.skills-manager` copy | `MIT` in `SKILL.md` | Reused unchanged |
| `frontend-design` | UPSTREAM (remote origin unavailable) | Target baseline, `frontend-design/`; benchmark provenance points to local `.skills-manager` copy | Apache-2.0 `LICENSE.txt` retained | Reused unchanged |
| `impeccable` | UPSTREAM (remote origin and license unavailable) | Target baseline, `impeccable/`; benchmark records local `.skills-manager` source and version 4.3.1 | No license file or declared license found | Reused unchanged; licensing is unresolved |
| `playwright` | FORKED_UPSTREAM | Target baseline, `playwright/`; NOTICE identifies `microsoft/playwright-cli`, `skills/playwright-cli/SKILL.md`; upstream revision unavailable | Apache-2.0 `LICENSE.txt` and Microsoft `NOTICE.txt` retained | Existing Codex adaptation reused unchanged |
| `web-accessibility` | UPSTREAM (remote origin unavailable) | Target baseline, `web-accessibility/`; benchmark provenance points to local `.skills-manager` copy | `MIT` in `SKILL.md` | Reused unchanged |

## Public-release blockers

- This repository has no root `LICENSE`; do not assume the project-owned workflow or benchmark-local skills are licensed for redistribution.
- `codebase-discovery` credits an author/company but includes no license; obtain the upstream license/permission and exact source repository/revision.
- `business-rule-extractor`, the three requirements skills, `srs-function-document`, and `document-docx` have no declared license in the benchmark source. Confirm ownership and license before public distribution.
- `business-rule-extractor` and the requirements skills name pack IDs in front matter (`business-analysis-pack`, `requirements-discovery-pack`) without source repositories or revisions; confirm whether these are project-local packs or identify their upstream origins.
- `verification-before-completion` and `impeccable` are local-canonical/reused without a recorded upstream source license. Confirm redistribution rights.
- `drawio-skill` has an MIT license and named copyright holder, but its upstream repository/revision is missing from the source record.
- `frontend-design` and `playwright` preserve Apache-2.0 license files; `playwright` also preserves its NOTICE. Confirm upstream revision when practical.

No license facts were inferred from filenames, external documentation links, or the existence of a public GitHub repository.
