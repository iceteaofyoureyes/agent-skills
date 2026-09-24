# Design Foundations, Standards, and Lineage

This document explains **why Agent Skills / BA Kit architecture and workflows are designed as they are**, which standards, frameworks, and community projects are used as references, and the exact level of adoption claimed by this repository.

It is intentionally separate from [Provenance and licensing](PROVENANCE.md):

- **PROVENANCE.md** answers where a particular skill/file came from, at which revision, and under which license.
- **FOUNDATIONS.md** answers which standards, practices, or reference projects support a workflow or architecture decision.

The goal is an auditable design lineage, not borrowed credibility through names or logos without a concrete mapping.

> Reference snapshot: **2026-09-24**. External sources may continue to evolve; the claims below apply to the state verified on this date.

## Claim-level policy

| Level | Meaning in this repository |
|---|---|
| **ADOPTED** | The repository intentionally implements an external format/contract within the stated scope. |
| **ALIGNED** | Selected principles/practices are explicitly mapped, but the repository does **not** claim certification or full conformance. |
| **UPSTREAM CAPABILITY SOURCE** | Code/skill content is actually reused or modified from upstream; exact revision/license belongs in PROVENANCE.md. |
| **DESIGN INFLUENCE** | Ideas or methods informed the design without creating a dependency or full compatibility claim. |
| **PLANNED INTEGRATION** | Selected for a downstream phase but not yet an implemented/accepted BA Kit RC1 capability. |
| **INTERNAL DESIGN** | Project-owned decisions that must be justified by this repository's own contracts, tests, benchmarks, and Human review. |

The repository does **not** claim:

- ISO/IEC/IEEE 29148 certification or full conformance;
- IIBA/BABOK certification or full methodology compliance;
- that BA Kit is a fork or implementation of GitHub Spec Kit or BMad Method;
- that Test Kit/TEA is implemented in BA Kit RC1;
- endorsement by any standards body or upstream project referenced here.

## Foundations matrix

| Source | Claim level | Repository area | What is adopted / referenced | What remains project-owned |
|---|---|---|---|---|
| [Agent Skills](https://agentskills.io/) | **ADOPTED** | Atomic skill packaging | Skill folder with `SKILL.md`; metadata + instructions; optional scripts/references/assets; progressive disclosure | `kit.yaml`, BA/Dev/Test Kit model, installer, Doctor, Human Gates, handoff contracts |
| [ISO/IEC/IEEE 29148:2018](https://www.iso.org/standard/72089.html) | **ALIGNED** | Requirements/SRS discipline | Lifecycle requirements engineering, well-formed requirements, requirements information items/SRS, requirements management | Evidence labels, BA semantic authority, WHAT/WHERE/HOW split, concrete artifact schemas |
| [IIBA BABOK / Requirements Life Cycle Management](https://www.iiba.org/knowledgehub/business-analysis-body-of-knowledge-babok-guide/5-requirements-life-cycle-management/5-1-trace-requirements/) | **ALIGNED** | Traceability and Human approval | Trace, maintain, assess changes, approve requirements; specify/model, verify, validate requirements | Human Gate state machine, immutable handoff revision/hash policy, agent routing |
| [45ck/business-analysis-skills](https://github.com/45ck/business-analysis-skills) | **UPSTREAM CAPABILITY SOURCE** | Selected BA atomic skills | Gap audit, interrogation, quality check, business-rule extraction | BA workflow orchestration, semantic authority, Human Gates, project-owned SRS replacement |
| [DiUS/agent-toolkit](https://github.com/DiUS/agent-toolkit) | **UPSTREAM CAPABILITY SOURCE** | `codebase-discovery` | Brownfield/current-code discovery capability | BA Kit's CURRENT_SYSTEM semantics and protection against silently promoting current behavior into target requirements |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | **PLANNED INTEGRATION** | Downstream Dev Kit | Spec-driven development: specification → plan → tasks → implementation/convergence; separate what/why before how | Engineering Impact before Spec Kit; central BA truth; Spec Kit per affected repository |
| [BMad Method](https://docs.bmad-method.org/) | **DESIGN INFLUENCE** | Cross-session/project workflow thinking | Human keeps decision authority; existing-codebase-first; deliberate project/context preservation | Three-Kit product model, BA semantic authority, Impact contract, installer architecture |
| [BMad Test Architect (TEA)](https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise) | **PLANNED INTEGRATION / DESIGN INFLUENCE** | Downstream Test Kit | Risk-based test design, traceability, quality/release gates; stack-neutral verification core separated from execution targets | Direct BA→Test business trace, enterprise manual-test-first workflow, final Test Kit composition |

## 1. Agent Skills — adopted packaging format

The [Agent Skills specification](https://agentskills.io/specification) defines a skill as, at minimum, a directory containing a `SKILL.md` file with YAML frontmatter and Markdown instructions. `scripts/`, `references/`, and `assets/` are optional resources. The specification also defines progressive disclosure: metadata is discovered first, instructions are loaded when the skill activates, and detailed resources are loaded on demand.

This repository directly follows that model for atomic skills:

~~~text
<skill-name>/
├── SKILL.md
├── references/   # when needed
├── scripts/      # when needed
├── assets/       # when needed
└── LICENSE       # when redistribution requires it
~~~

The following are **not part of the Agent Skills standard** and are project-owned design:

- role Kits (`ba`, later `dev`, `test`);
- `kits/<id>/kit.yaml`;
- installer/Doctor/uninstall;
- workflow state;
- Human Gate semantics;
- Engineering Handoff;
- BA semantic authority.

The accurate claim is therefore **“atomic skills adopt/follow the Agent Skills format”**, not “the entire framework is the Agent Skills standard.”

## 2. ISO/IEC/IEEE 29148 — requirements/SRS alignment

ISO currently lists **ISO/IEC/IEEE 29148:2018, Edition 2** as the published International Standard, reviewed and confirmed in 2024. At the 2026-09-24 snapshot, **Edition 3 is a Draft International Standard (DIS)** intended to replace the 2018 edition, so this repository does not use the draft as its normative baseline.

BA Kit is **aligned** with selected 29148 principles:

- requirements are managed across a lifecycle rather than produced once as a document;
- business/requirement meaning is separated from implementation design;
- requirements should be clear, checkable, and source-grounded;
- the SRS/information item is prepared from a clarified baseline;
- requirement changes are controlled rather than silently overwritten.

The following are **internal guardrails**, not ISO 29148 terminology:

~~~text
CONFIRMED
CURRENT_SYSTEM
INFERRED
PROPOSED
UNKNOWN
~~~

Likewise, **“Continue != Approve”**, Human Gates, and BA→Engineering Handoff are repository-specific contracts.

Because no full conformance audit has been performed, the repository uses **ALIGNED**, never “ISO compliant,” “ISO certified,” or “conformant to ISO/IEC/IEEE 29148.”

## 3. IIBA BABOK — lifecycle, traceability, and approval alignment

IIBA publicly presents Requirements Life Cycle Management tasks including:

- Trace Requirements;
- Maintain Requirements;
- Prioritize Requirements;
- Assess Requirements Changes;
- Approve Requirements.

The BABOK KnowledgeHub also separates Requirements Analysis and Design Definition activities such as Specify and Model, Verify, and Validate Requirements.

BA Kit maps selected practices into:

~~~text
Requirement
→ clarification / confirmed decisions
→ Business Rules
→ SRS
→ explicit Human approval
→ Engineering Handoff
~~~

with a target downstream trace:

~~~text
CR
→ BR / FR / AC
→ Test Case
→ Execution
→ Automation
→ Result
~~~

BA Kit does not attempt to implement every BABOK knowledge area, technique, or governance model. The claim is **selected-practice alignment**, not “BABOK implementation.”

## 4. Community BA capability — provenance is different from design lineage

Some BA Kit atomic capabilities genuinely come from community repositories, notably:

- [45ck/business-analysis-skills](https://github.com/45ck/business-analysis-skills): requirements gap auditor, interrogator, quality check, and business-rule extractor;
- [DiUS/agent-toolkit](https://github.com/DiUS/agent-toolkit): `codebase-discovery`.

These are **UPSTREAM CAPABILITY SOURCE** relationships, not merely inspiration. Exact source paths, revisions, local changes, and licenses are recorded in [PROVENANCE.md](PROVENANCE.md).

Conversely, `ba-workflow`, the Kit contract, the Human Gate model, and the current `srs-function-document` implementation are project-owned. They are not attributed to an upstream project without evidence.

## 5. GitHub Spec Kit — downstream HOW, not BA source of truth

GitHub Spec Kit describes Spec-Driven Development as defining **what and why before deciding how**, then moving through specification → plan → tasks → implement → converge.

That supports the boundary intended by this framework:

~~~text
BA Kit
WHAT
  ↓
Engineering Impact
WHERE / WHO OWNS
  ↓
repo-local Spec Kit / Dev
HOW
~~~

The claim must remain precise:

- Spec Kit is **not integrated** into BA Kit RC1;
- Engineering Impact before Spec Kit is this framework's decision, not a claim that Spec Kit mandates that stage;
- the BA business baseline does not become a repo-local implementation spec;
- Spec Kit is intended to run **per affected implementation repository** after Impact resolves scope.

The current status is therefore **PLANNED INTEGRATION**.

## 6. BMad Method — design influence for Human control and brownfield work

Current BMad documentation emphasizes that the Human makes the calls, supports existing codebases, and favors verified project context over stale duplicated descriptions. Those patterns are consistent with this framework's decisions:

- Human keeps approval/accountability;
- brownfield work should inspect current source;
- important decisions/context should be durable;
- not every change needs the same amount of ceremony.

BA Kit does not use BMad's runtime/workflow engine and is not a derivative implementation of BMad Method. The claim is **DESIGN INFLUENCE**.

## 7. TEA — planned Test Kit foundation

BMad Test Architect (TEA) currently documents a two-layer verification architecture:

1. **TEA Core** decides what must be verified, at what depth, with which evidence, and whether evidence is sufficient for release;
2. **Execution targets** translate those decisions into runnable tests for a concrete stack.

TEA also provides risk-based test design, traceability, and release/quality gates. These characteristics fit the target Test Kit:

~~~text
BA Approved Baseline
        +
Dev Technical Evidence
        ↓
TEA/Test Design
        ↓
Risk
        ↓
Manual Test Cases
        ↓
Human Tester Review
        ↓
Execution
        ↓
Automation / Regression
        ↓
Quality Evidence
~~~

Test Kit has not yet been implemented or frozen. TEA is currently only **PLANNED INTEGRATION / DESIGN INFLUENCE**, not a BA Kit RC1 capability.

## 8. INTERNAL DESIGN decisions must stand on local evidence

The repository does not borrow ISO, BABOK, Spec Kit, or BMad authority for these project-owned decisions:

- BA Kit / Dev Kit / Test Kit as three role products;
- Core Skills as a shared layer rather than a fourth Kit;
- flat root-level atomic skills;
- `kit.yaml` as canonical composition;
- `"Continue" != "Approve"`;
- evidence labels and semantic authority;
- Engineering Impact = WHERE / WHO OWNS;
- Impact before repo-local Spec Kit;
- central BA baseline as business truth;
- Test trace directly to BA IDs;
- manual testing as first-class.

These decisions must be evaluated through this project's own evidence: contract validation, benchmarks, regression tests, fresh-session acceptance, and Human review.

## 9. Repository evidence hierarchy

Framework credibility is not based on stars or upstream logos. Evidence is prioritized as:

~~~text
External standard / documented methodology
        ↓
Exact upstream provenance where code is reused
        ↓
Project-owned contracts and explicit boundaries
        ↓
Automated validation / Doctor / regression tests
        ↓
Benchmark and semantic comparison
        ↓
Fresh-session runtime acceptance
        ↓
Human approval
~~~

Current BA Kit RC1 evidence:

- package/installer/Doctor/isolation: evidenced;
- BA Kit payload provenance/license: READY;
- offline BA/SRS contract tests: PASS;
- CR-001 documentation examples: illustrative/contract-valid, not runtime proof;
- packaged fresh-session CR-001 runtime acceptance: **not PASS** at this snapshot because the isolated provider/runtime remains blocked.

See [Release status](RELEASE.md) so package/test evidence is not overstated as functional acceptance.

## 10. Primary references

These upstream/official references were checked when this document was written:

1. **Agent Skills**
   - Overview: https://agentskills.io/
   - Specification: https://agentskills.io/specification
2. **ISO/IEC/IEEE 29148**
   - Published 2018 standard: https://www.iso.org/standard/72089.html
   - Edition 3 DIS under development: https://www.iso.org/standard/94091.html
3. **IIBA**
   - Requirements Life Cycle Management / Trace Requirements: https://www.iiba.org/knowledgehub/business-analysis-body-of-knowledge-babok-guide/5-requirements-life-cycle-management/5-1-trace-requirements/
   - Business Analysis Standard — Requirements and Designs Life Cycle Management: https://www.iiba.org/knowledgehub/the-business-analysis-standard/5-applying-business-analysis-tasks/5-3-business-analysis-knowledge-areas/requirements-and-designs-life-cycle-management/
4. **GitHub Spec Kit**
   - https://github.com/github/spec-kit
5. **BMad Method**
   - https://docs.bmad-method.org/
   - Existing codebases: https://docs.bmad-method.org/existing-codebases/start-in-an-existing-codebase/
6. **BMad Test Architect (TEA)**
   - https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise
   - Verification architecture: https://github.com/bmad-code-org/bmad-method-test-architecture-enterprise/blob/main/docs/explanation/verification-architecture.md
7. **Upstream BA/discovery capability**
   - https://github.com/45ck/business-analysis-skills
   - https://github.com/DiUS/agent-toolkit

Product names, standards, and trademarks belong to their respective owners. Reference here does not imply endorsement, certification, or affiliation.

---

Tiếng Việt: [Nền tảng thiết kế, chuẩn tham chiếu và design lineage](../vi/FOUNDATIONS.md)
