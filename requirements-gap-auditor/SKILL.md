---
name: "requirements-gap-auditor"
description: Review requirements for missing actors, flows, data, validation, permissions, lifecycle and operational needs. Report evidence-based gaps and preserve unresolved decisions instead of inventing answers.
pack: "requirements-discovery-pack"
purpose: "Audit a requirement set for what is missing relative to common engineering needs: actors, flows, data, validation, security, operations, and lifecycle."
inputs: ["requirements", "problem statement", "constraints", "assumptions", "acceptance criteria if any"]
outputs: ["gap audit report", "missing topic checklist", "remediation suggestions"]
handoffs: ["requirements-interrogator", "constraint-detector", "definition-of-done-drafter"]
---
# requirements-gap-auditor

## Purpose
Audit a requirement set for what is missing relative to common engineering needs: actors, flows, data, validation, security, operations, and lifecycle.

## Trigger this skill when
- A draft spec feels thin but the exact gaps are unclear.
- Before sign-off, estimation, architecture, or build.
- After a large edit or merge of multiple requirement sources.

## Expected inputs
- requirements
- problem statement
- constraints
- assumptions
- acceptance criteria if any

## Deliverables
- gap audit report
- missing topic checklist
- remediation suggestions

## Operating procedure
1. Check for normal completeness categories: actors, triggers, preconditions, postconditions, data, validation, permissions, error handling, NFRs, support/ops, reporting, auditability, rollout, and maintenance.
2. Flag absent or weak areas.
3. Suggest the next best artifact or question to close each major gap.

## Approved authority and historical lifecycle wording

When Dev uses this capability after a valid Approved BA Baseline or Delivery Manifest V2, determine approval from
the validated machine-readable authority and its exact hashes/receipt. APPROVAL STATE != INLINE LIFECYCLE TEXT.
`ba_baseline.status == APPROVED_FOR_ENGINEERING` and exact BA source hashes establish the approved BA snapshot;
a valid Delivery Manifest V2 plus its exact Human receipt establishes approved UX. Do not infer that BA/UX is
unapproved because an immutable approved source still contains `DRAFT_FOR_HUMAN_BASELINE_REVIEW`,
`DRAFT_FOR_HUMAN_UX_REVIEW`, or `PENDING_HUMAN_REVIEW` wording, or because a handoff's historical `next_stage`
describes an earlier gate.
An approved Business Rule with a semantic contradiction against another approved rule remains a real ambiguity and
must stop readiness; this precedence applies only to approval/lifecycle metadata.

Keep `open_items.blocking` as a blocker by contract. `open_items.non_blocking` is not automatically a business
ambiguity. If a later validated Delivery Manifest V2 proves the referenced UX snapshot and receipt are approved,
classify that earlier UX-pending item as SUPERSEDED_BY_DELIVERY_MANIFEST. Do not change approved source bytes.

Readiness still stops for an UNKNOWN/TBD that forces Dev to choose WHAT, conflicting approved semantics, missing or
invalid approval evidence, hash drift, or a genuine blocking item. Technical design choices do not become BA gaps.

## Quality gates
- Gaps are categorized and evidence-based.
- Findings distinguish absent, weak, and deferred.
- Suggestions are actionable.

## Handoff targets
- requirements-interrogator
- constraint-detector
- definition-of-done-drafter

## Output style
- Be explicit about uncertainty.
- Prefer short, testable statements over long prose.
- Surface risk and ambiguity instead of guessing.
- Separate facts, assumptions, constraints, and open questions.

## Failure modes to avoid
- Do not invent stakeholder intent.
- Do not convert preferences into mandatory requirements without evidence.
- Do not hide unresolved ambiguity behind polished wording.
- Do not collapse functional, non-functional, and business rule concerns into one blob.

## Minimum output skeleton
```md
## Summary
## Findings
## Structured outputs
## Assumptions
## Constraints
## Open questions
## Recommended next skill
```
