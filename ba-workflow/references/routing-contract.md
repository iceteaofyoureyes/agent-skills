# Routing contract

Classify the operation, read workflow state, identify feature mode and artifact, resolve authority, check gates, load one matching capability, act within scope, validate, and then record the checkpoint. Ask one concise question if a material route remains ambiguous.

| Intent | Required capabilities | Gate and mutation rule |
|---|---|---|
| Requirement review | `requirements-interrogator`, `requirements-gap-auditor`; add `codebase-discovery` for brownfield | Review is read-only; stop for blocking unknowns |
| Semantic change review | `requirements-interrogator`, `requirements-gap-auditor` | No semantic or diagram mutation while a material decision is pending |
| Resume / “Tiếp tục” | `ba-workflow` state handling | Continue only to the next valid stage; never approve |
| Business Rules | `business-rule-extractor` | Create/update from confirmed evidence; preserve uncertainty |
| SRS | `srs-function-document`, `requirements-quality-check` | Resolve blocking BA questions first; keep the canonical Markdown source |
| Business diagram | `drawio-skill` | Use approved Business Rules/SRS; review-only does not write |
| DOCX | `document-docx` | Source-backed when canonical Markdown exists; otherwise use the selected standalone Word source |
| Prototype | `product-design-and-ux`, `frontend-design` | Visual proposal only; completion opens a pending visual gate |
| Browser or visual check | `playwright`, `impeccable`, or `web-accessibility` as needed | Load only when that work is requested or reached |
| Engineering handoff | `ba-workflow` | Emit only after explicit BA baseline approval; no technical ownership fields |

`REVIEW` never mutates feature artifacts or advances a stage. `CREATE` and `EDIT` touch only the selected artifact and approved derived outputs. When a canonical semantic source exists, never edit only its generated DOCX or diagram to express a new business rule.
