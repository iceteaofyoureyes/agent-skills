# CR-001: Resource Request Submission

This is a **documentation example** showing how BA Kit can move from an incomplete brief to a BA baseline/handoff. It is not a fixed runtime transcript and must not be fed into fresh-session acceptance.

## What does this example demonstrate?

~~~text
Semantic spine:
01 Input Requirement
→ 02 Gap Review + Human decisions
→ 03 Approved Business Rules
→ 04 SRS excerpt
→ baseline candidate → VALIDATED → HUMAN_REVIEW
→ trusted host supplies exact Human approval receipt
→ 05 Engineering Handoff VNext boundary example
→ Knowledge Impact in the candidate/handoff

Derived lane from approved/confirmed sources:
03 / 04
→ 06 Draw.io / DOCX / visual delivery examples
→ Human visual/document review
~~~

It demonstrates:

- an initial requirement can be incomplete;
- the agent asks instead of inventing;
- Human answers are separate from the original input;
- Business Rules/SRS preserve traceability;
- Draw.io/DOCX are derived delivery artifacts;
- VNext handoff requires exact `APPROVED_BASELINE` proof and installed-runtime revalidation.
- the example contains no usable receipt or fabricated approval.

## Files

| File | Role | Purpose |
|---|---|---|
| [01-input-requirement.md](01-input-requirement.md) | INPUT | Intentionally incomplete brief |
| [02-gap-review.md](02-gap-review.md) | ILLUSTRATIVE OUTPUT + Human decisions | Pre-clarification gaps and example Human answers |
| [03-approved-business-rules.md](03-approved-business-rules.md) | ILLUSTRATIVE OUTPUT | Stable BR-* identity, evidence and UNKNOWN |
| [04-srs-excerpt.md](04-srs-excerpt.md) | ILLUSTRATIVE OUTPUT | Stable FR-* identity and traceability |
| [05-engineering-handoff.yml](05-engineering-handoff.yml) | NON-AUTHORITATIVE BOUNDARY EXAMPLE | VNext fields; no approval receipt or usable proof |
| [06-delivery-and-visualization.md](06-delivery-and-visualization.md) | USAGE EXAMPLE | Derived Draw.io/DOCX/prototype lane from BR/SRS |
| [knowledge-impact-v1.json](../knowledge-impact-v1.json) | DERIVED CANDIDATE METADATA | Affected product/domain/testing targets; no technical HOW |

## How to read it

1. Start with **01-input-requirement.md** and note what is still unknown.
2. **02-gap-review.md** shows the kinds of questions BA Kit should surface. The Human decisions are later supplied evidence, not agent inference.
3. **03** and **04** show Human decision → Business Rule → Functional Requirement.
4. **06** explains derived Draw.io/DOCX/visual lanes.
5. **05** shows the VNext handoff boundary only. Placeholders intentionally fail production validation; the trusted host supplies the approval receipt.

## What this example does not prove

- It does not assert current SamplePlatform behavior; real brownfield work must discover source.
- It does not prove runtime wording/IDs or approval.
- It does not include a company Word template.
- It does not include Figma/screenshots because CR-001 input has no visual source.
- It does not decide target API/DB/architecture.

## Fresh-session acceptance rule

Do not put approved example outputs into the generator context. Expected semantics belong to the evaluator after generation.

## Open items in this fixture

The documentation fixture classifies maximum duration and list details as non-blocking only for this example handoff. They remain UNKNOWN; a real project requires Human classification.

Tiếng Việt: [CR-001 example](../README.md)
