---
name: ba-workflow
description: Route BA requests through evidence discovery, clarification, business rules, SRS and approved handoff. Use when the user asks to review a requirement, continue BA work, write or update an SRS, review a BA artifact, or prepare engineering handoff.
---

# BA Workflow

You own routing and checkpoint safety. Atomic skills own detailed discovery, analysis, SRS, diagram and document procedures. Load only the capability needed for the current request.

## Start every request

1. Read the project `workflow-state.json` if present. If it is absent, classify the request and start at the earliest safe checkpoint; do not invent prior approvals.
2. Classify the request as `CREATE`, `EDIT`, `REVIEW`, or a continuation. A continuation resumes the recorded operation and stage.
3. Identify the feature mode: brownfield, greenfield, or document-only. Use `codebase-discovery` when current system behavior matters.
4. Resolve the requested artifact and its semantic, visual, or delivery source of truth.
5. Check pending questions, actions and Human Gates before writing. A review is read-only.
6. Route through `references/routing-contract.md`; ask one concise clarification only when the target or a material business decision is unknown.
7. Validate the result with the relevant quality skill and validator. Update state only after a successful action or a recorded Human decision.
8. Name the next valid action and preserve all still-open items.

## Authority and gates

- Use only `CONFIRMED`, `CURRENT_SYSTEM`, `INFERRED`, `PROPOSED`, and `UNKNOWN` for evidence classification. See `references/evidence-model.md`.
- Confirmed BA decisions, approved Business Rules, and the canonical SRS jointly govern business meaning. Current behavior is evidence about the existing system, not a new requirement.
- `CONTINUE` resumes work. It never means `APPROVE`.
- `ANSWER` resolves the named question only. `APPROVE`, `REJECT`, and `REQUEST_CHANGES` apply only to the named approval gate or artifact.
- Do not route into implementation ownership, API/DB/event design, service boundaries, locking, or transaction decisions. Those belong downstream.

## State and handoff

The canonical state shape and safe update rules are in `references/workflow-state.md`. Run the validator script from this skill's installed folder (for example, `.agents/skills/ba-workflow` for Codex project scope):

```text
python <ba-workflow-skill-folder>/scripts/validate-state.py <workflow-state.json>
```

Create `engineering-handoff.yml` only after the BA baseline is explicitly approved for engineering. The format, integrity checks and downstream boundary are in `references/engineering-handoff.md`; validate it with:

```text
python <ba-workflow-skill-folder>/scripts/validate-handoff.py <engineering-handoff.yml>
```

## Capability routes

| Request | Route |
|---|---|
| Review or clarify a requirement | `codebase-discovery` when brownfield; then `requirements-interrogator` and `requirements-gap-auditor` |
| Continue | Read state, resolve pending work and gate; do not infer approval |
| Extract Business Rules | `business-rule-extractor` from confirmed evidence and current-system evidence with separate labels |
| Write or update SRS | `srs-function-document`, then `requirements-quality-check` |
| Create or edit a business diagram | `drawio-skill` from approved semantic sources |
| Create, edit or review DOCX | `document-docx`; use canonical Markdown first when it exists |
| Design a prototype | `product-design-and-ux` and `frontend-design`; load `playwright`, `impeccable`, or `web-accessibility` only when needed |

Never load every skill just because it is in the kit. The full routing table is `references/routing-contract.md`.
