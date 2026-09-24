# Architecture

## Goal

BA Kit composes atomic skills into a BA workflow while keeping the Human as business authority.

~~~text
BA Kit = WHAT
Engineering Impact = WHERE / WHO OWNS
Dev Kit + repo-local Spec Kit = HOW
Test Kit + TEA = HOW DO WE PROVE IT
~~~

## Layers

~~~text
User intent
    ↓
ba-workflow
    ↓
state / authority / gate / route
    ↓
atomic capabilities
    ├── discovery
    ├── requirement review
    ├── Business Rules
    ├── SRS
    ├── DOCX
    ├── Draw.io
    └── optional UX/UI/prototype
~~~

Atomic skills are canonical at repository root. **kits/ba/kit.yaml** is the single source for BA Kit composition.

## Semantic, visual, and delivery authority

The workflow separates these layers so presentation artifacts do not overwrite business truth:

~~~text
SEMANTIC
Confirmed BA Decisions
+ Approved Business Rules
+ Canonical SRS

VISUAL
Approved Figma / screenshot / diagram / prototype
(confirmed visual/interaction meaning only)

DELIVERY
Selected Word template

AS-IS
CURRENT_SYSTEM evidence
~~~

DOCX, Draw.io, and prototypes are derived artifacts; semantic changes return to semantic authority first.

## Project modes

- brownfield;
- greenfield;
- document-only;
- visual-assisted.

The workflow starts at the earliest safe checkpoint rather than forcing every request through the full pipeline.

## Responsibility flow

| Stage | Question | Status |
|---|---|---|
| BA Kit | **WHAT**? | RC1 candidate; remediation |
| Engineering Impact | **WHERE / WHO OWNS**? | Planned |
| Dev Kit + Spec Kit | **HOW**? | Planned |
| Test Kit + TEA | **HOW DO WE PROVE IT**? | Planned |

~~~text
Requirement
→ BA Kit
→ Approved BA Baseline
→ Engineering Impact
→ Dev Kit + repo-local Spec Kit
→ Test Kit + TEA
→ Human Final Acceptance
~~~

## Required vs optional

Required BA Kit capabilities include discovery, requirement review, Business Rules, SRS, DOCX, and Draw.io. UX/UI/prototype/browser/accessibility capabilities are optional.

See [BA Kit capabilities](BA_KIT_CAPABILITIES.md).

## Installer architecture

The installer reads dependencies from **kits/ba/kit.yaml**.

- Codex/Claude Code: native Agent Skills directories;
- generic: explicit target directory;
- Skills Manager: optional, not a runtime dependency.

## Handoff boundary

Engineering Handoff appears only after explicit BA approval and contains no:

- repository/module owner;
- FE/BE/service owner;
- API/event shape;
- DB schema;
- architecture choice;
- locking/transaction strategy.

It becomes input to Engineering Impact.

## Foundations

Claim levels and standards/framework references live in [FOUNDATIONS.md](FOUNDATIONS.md). Exact upstream revisions/licenses live in [PROVENANCE.md](PROVENANCE.md).

---

Tiếng Việt: [Kiến trúc](../vi/ARCHITECTURE.md)
