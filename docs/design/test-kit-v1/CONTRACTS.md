# Test Kit V1 implementation contracts

**Status: APPROVED composition; frozen V1 contract for Human implementation review.** This document defines the data and gate behavior to implement. It does not itself approve any generated product artifact.

## 1. Canonical schemas

One canonical Test Design record represents one TEA scenario row. One canonical Testcase record represents one manual case. Collections, their immutable revisions/hashes, raw files, source maps and receipts are workflow evidence stored alongside the records; they are not extra semantic fields. UTF-8 strings are trimmed only at their outer boundary; IDs and substantive wording are never rewritten. All fields below are required, including arrays that may be empty and nullable fields. No unspecified key is part of V1. `review_status` is a read-only projection of gate state, omitted from the immutable semantic payload whose exact stored UTF-8 bytes are SHA-256 hashed for receipts; changing status cannot change that hash.

### Canonical Test Design record

| Field | Exact type and rule |
|---|---|
| `design_id` | Nonempty upstream scenario ID string, unique within its design revision; preserve spelling and zero padding (`TD-01` and `TD-001` are different IDs). |
| `hierarchy_path` | Nonempty ordered array of source heading strings, from document/epic through priority/group heading to the scenario's containing section. It describes structure, not a second ID. |
| `scenario_title` | Nonempty string copied from the scenario title/cell without semantic rewrite. |
| `expected_behavior` | Nonempty observable-outcome string copied from the scenario row, or `null` only when the source explicitly leaves this outcome UNKNOWN/conditional on an unresolved BA decision. Conditional future suggestions remain in raw evidence and `open_questions`, never become pass/fail assertions. |
| `requirement_refs` | Nonempty ordered array of unique stable FR/BR ID strings explicitly present on that scenario. Expand a source range only when both ends and every member exist in the pinned BA ID inventory; otherwise `CANNOT_NORMALIZE`. |
| `open_questions` | Array of `{source_ref: string, text: string, status: "UNKNOWN"}`. `source_ref` is a valid BA FR/BR ID; `text` retains the unresolved question/condition from BA or the scenario. Empty array means none for this scenario. No inferred answer or sentinel expected result. |
| `review_status` | `DRAFT`, `IN_REVIEW`, `CHANGES_REQUESTED`, or `APPROVED`; derived solely from the collection's gate state and exact Human receipt, never from TEA's own Draft/approval text. |

Design `priority` is deliberately absent: TEA P0–P3, risk, level, count, effort and quality-gate percentages are planning metadata only. The priority heading remains in `hierarchy_path` and raw evidence, but is not a BA or design semantic field. `expected_behavior: null` requires at least one matching `open_questions` entry; it is not a failed normalization if the raw source explicitly defers the assertion. A missing or ambiguous outcome without that explicit UNKNOWN is `CANNOT_NORMALIZE`.

### Canonical Testcase record

| Field | Exact type and rule |
|---|---|
| `test_case_id` | Nonempty upstream case ID string, unique within its case-set revision; preserve spelling. |
| `name` | Nonempty manual case title string. |
| `objective` | Nonempty validation-intent string from the case description/objective. |
| `preconditions` | String copied from the case's precondition text, including explicit shared-fixture references; empty string only if source explicitly says none. Do not silently expand a fixture into invented setup. |
| `test_data` | String or `null`: source's case-level shared Test Data verbatim. This observed field is needed because both accepted Katalon outputs provide case-level data without unambiguous per-step assignment. `null` only if no case-level data is supplied. |
| `steps` | Nonempty ordered array of `{action: string, test_data: string|null, expected_result: string}`. Action and expected result are nonempty verbatim step text. Step `test_data` is non-null only when the raw step explicitly supplies step-specific data; do not distribute shared `test_data` by guessing. |
| `priority` | Required `P0`, `P1`, `P2`, or `P3`, copied from the raw case. It is advisory planning metadata and cannot alter BA behavior or a gate. Missing/ambiguous label is `CANNOT_NORMALIZE`. |
| `requirement_refs` | Nonempty ordered unique array of explicit FR/BR IDs from that raw case. |
| `test_design_refs` | Nonempty ordered unique array of explicit IDs from the exact approved design revision; many cases may cover one TD and one case may cover several TDs. |
| `execution_dependencies` | Array of `{need: string, material: boolean, status: "OPEN"|"RESOLVED", resolution_ref: string|null}`. `need` names the missing setup/action/observation contract. OPEN requires null `resolution_ref`; RESOLVED requires a pinned approved execution-oracle source ref. A dependency is material when its absence prevents deterministic setup, action or observation. If materiality cannot be established, treat it as material until Human review. |
| `review_status` | Same four-value enum as design; `APPROVED` is derived only from the matching Case Gate receipt. |

The extra top-level `test_data` is not speculative: both accepted raw case formats have a case-level Test Data field. `expected_result` on a step is never filled from a case-level summary by the adapter. Case-level summary is preserved in raw evidence and checked against the steps; disagreement is a blocking finding. If any step lacks a separable action/result, normalization fails. Execution dependencies can be copied from explicit case or globally scoped raw notes and source-linked placeholders; the validator may demand a missing dependency declaration but cannot invent a contract value.

## 2. Four field-level mappings

### Approved BA Baseline → TEA input

| Pinned source field | TEA input field/section | Rule |
|---|---|
| Approved handoff `ba_baseline.status`, revision and authoritative source paths/SHA-256 | Invocation input manifest | Require approved status and matching file hashes; handoff is a locator, not a new business oracle. |
| SRS `FR-*` ID and requirement text | Epic-level `Acceptance criteria` entries headed by the same ID | Copy ID and text verbatim in source order. `Epic 1`/title are structural wrapper labels only. |
| Approved Business Rules `BR-*` ID and rule text | Separate cited business-rule context | Copy verbatim, with stable IDs and source path/hash. Never flatten BR text into a new FR or acceptance criterion. |
| BA `open_items` and UNKNOWN clauses in FR/BR | Separate open-decision context | Preserve source wording and linked IDs; no default, limit, UI rule or outcome is supplied. |
| Current source/system evidence, if supplied | Explicit `CURRENT_SYSTEM / SUPPLEMENTAL` context | Keep separate from BA input; may describe existing stack only. |

The adapter may change headings, paths and TEA configuration needed for epic-level invocation. If the BA status, hash, ID/text pairing or required source map is missing/conflicting, stop before TEA. The Petclinic `02-gap-review.md` is decision history, not a replacement for approved BR/SRS wording.

### TEA output → Canonical Test Design

Only these observed pinned-revision profiles are recognized initially: the semantic benchmark `Test Coverage Plan` under `P0`–`P3` with columns `Scenario | Requirement | Level | Risk Link | Count | Owner | Observable expected result`, and the Petclinic native proof `Test Coverage Plan` under `P0`–`P3` with columns `Test ID | Kịch bản | Mức kiểm thử | Risk Link | Truy vết | Kết quả quan sát được`. Header/column count must match its profile; scenario row IDs, refs and cells must be unambiguous. No parser uses prose elsewhere to replace a missing row field.

| Raw location | Canonical field | Rule |
|---|---|---|
| Scenario's `TD-*` prefix in benchmark `Scenario`, or native `Test ID` | `design_id` | Preserve exact ID; do not renumber or equate `TD-01` with `TD-001`. |
| Document title and containing plan/priority headings | `hierarchy_path` | Copy ordered headings only. |
| Text after benchmark `TD-* —`, or native `Kịch bản` | `scenario_title` | Copy without adding an actor/rule. |
| `Observable expected result` or `Kết quả quan sát được` | `expected_behavior` | Copy observable assertion. For explicitly deferred row such as native `TD-35`, set null and record the unresolved maximum-duration question; retain the raw conditional text. |
| `Requirement` or `Truy vết` | `requirement_refs` | Parse explicit FR/BR IDs; validate against the pinned BA inventory. No trace inferred from prose or normalized benchmark matrix. |
| Raw assumption/open-decision text tied to the scenario and BA UNKNOWN | `open_questions` | Copy unresolved text with BA source ID; no asserted answer. |
| Workflow gate state | `review_status` | New normalized records start `DRAFT`, regardless of TEA document status. |

Risk links, test level, counts, owners, TEA priorities and thresholds remain raw/advisory. The benchmark trace matrix and runtime proof review are validation evidence, not alternate parser inputs or business authority.

### Approved Canonical Test Design → Katalon input

| Input | Katalon-consumable field/section | Rule |
|---|---|---|
| Exact Design Gate receipt and pinned design collection ID/revision/SHA-256 | Invocation manifest | Require matching Human APPROVE and current BA source hashes before invocation. A Draft benchmark fixture cannot pass this production precondition. |
| `design_id`, `hierarchy_path`, `scenario_title`, `expected_behavior`, `requirement_refs` | Scenario table/text with the same IDs and wording | Preserve grouping and every explicit coverage assertion; no new business behavior, case intent or trace link. |
| `open_questions`, including rows with `expected_behavior: null` | Explicit UNKNOWN/deferred section | Katalon must not create a pass/fail assertion for unresolved behavior. A null-outcome row is deferred until BA resolution and renewed design approval. |
| Approved BR/SRS source text and hashes | Separate BUSINESS ORACLE context | Ground expected results; does not permit changing approved design coverage. |
| Approved UI/API/Engineering/interface contract, if present | Separate EXECUTION ORACLE context | Supplies only setup, action and observation detail; missing details remain dependencies. |

Katalon may split or combine compatible case journeys only when each approved design assertion and all source refs remain traceable. Its new coverage suggestions are review findings outside the canonical case set until approved through the proper design revision. No project lookup, TestOps create/update/link, suite, execution or export is invoked in V1.

### Katalon output → Canonical Testcase

Two observed pinned-revision profiles are recognized initially: semantic benchmark case headings `## TC-*`, `Objective`, `Preconditions`, `Test Data`, `Priority`, `Requirement refs`, `Test Design refs`, and a numbered `Step | Test Step | Expected Result` table; native proof case headings `## TC-*`, `Mô tả`, `Tiền điều kiện`, `Bước và kết quả mong đợi` numbered action `→` result lines, `Test Data`, `Priority`, and `Trace`. Only these named labels and structures are accepted; any changed label/section requires a separately reviewed parser profile, otherwise `CANNOT_NORMALIZE`.

| Raw field | Canonical field | Rule |
|---|---|---|
| `TC-*` heading and title | `test_case_id`, `name` | Preserve ID/title; no deduplication or renumbering. |
| `Objective` / `Mô tả` | `objective` | Copy validation intent. |
| `Preconditions` / `Tiền điều kiện` | `preconditions` | Copy text and shared fixture tokens verbatim. |
| Case-level `Test Data` | top-level `test_data` | Copy verbatim; do not assign values to steps without explicit raw step data. |
| Numbered table rows or numbered `action → result` lines | `steps[].action`, `steps[].expected_result` | Keep order, exact action/result split and wording. `steps[].test_data` is null unless that step supplies a separate data field. |
| `Priority` | `priority` | Copy only P0–P3; no derivation from TEA priority. |
| `Requirement refs` / FR/BR tokens in `Trace` | `requirement_refs` | Parse explicit IDs only and validate against BA and referenced design rows. |
| `Test Design refs` / TD tokens in `Trace` | `test_design_refs` | Exact match to approved design IDs; no lookup by similar title. |
| Explicit local/global execution notes and referenced placeholders | `execution_dependencies` | Attach only when scope to this case is explicit or mechanically resolved by a named shared fixture. Otherwise flag missing/ambiguous declaration. |
| Workflow gate state | `review_status` | New cases start `DRAFT`, regardless of raw skill comments. |

The case-level Expected Result summary stays in raw evidence; validator compares it with step results. The semantic benchmark traceability file is not allowed to override raw case refs (its TC-012 row omits a BR present in the raw case).

## 3. Fail-closed normalization and scoped authority

Normalizer input must match a pinned upstream commit **and** one of the known raw structures above. Pin raw bytes/SHA-256, invocation, BA/design input hashes, parser profile/version, source location for every mapped field, and findings in the evidence record before emitting a canonical snapshot. Parse-only transformations are heading/field rename, explicit ID tokenization, validated range expansion and whitespace at field boundaries. No LLM inference, fuzzy ID matching, invented expected behavior, inferred trace, inferred case split/merge, or repair of malformed semantics is allowed.

If a required field is absent, two fields compete, a range is ambiguous, an explicit UNKNOWN cannot be located, a known structure changes, or a raw result conflicts with the approved source, return `CANNOT_NORMALIZE` with file/row/field and reason. Preserve raw evidence immutably and emit no approvable canonical collection or gate transition. Re-run upstream or obtain a Human-authorized source/design correction; never silently edit the raw output. Semantic consistency beyond deterministic checks remains a Human review responsibility.

Authority checks use these exact scopes: BA Baseline = `BUSINESS ORACLE`; approved design = `COVERAGE ORACLE`; approved UI/API/Engineering/interface contract = `EXECUTION ORACLE`; current source/system = `SUPPLEMENTAL`; TEA/Katalon planning metadata = `ADVISORY`. A conflict is a blocking finding with both refs, not a precedence guess. Business conflicts return to BA; coverage conflicts return to Design Gate; execution details return to their contract owner. A current implementation or an upstream priority cannot override a stronger scoped authority. Petclinic maximum duration, filters, default sorting, pagination/page size remain UNKNOWN until BA explicitly resolves them.

## 4. Human Gate state machine and receipts

| Current workflow state | Event / precondition | Next state |
|---|---|---|
| `DRAFT_DESIGN` | Complete normalized design + design validators pass; submit exact collection snapshot | `DESIGN_REVIEW` (`IN_REVIEW`) |
| `DESIGN_REVIEW` | Human `APPROVE` with valid receipt and no blocking finding | `APPROVED_DESIGN` (`APPROVED`); Katalon may now start |
| `DESIGN_REVIEW` | Human `REQUEST_CHANGES` with valid receipt and nonempty feedback | Old snapshot `CHANGES_REQUESTED`; new revision starts `DRAFT_DESIGN` |
| `APPROVED_DESIGN` | Katalon yields complete normalized case collection | `DRAFT_CASES` (`DRAFT`) |
| `DRAFT_CASES` | Normalization and structural/trace checks pass; submit exact collection snapshot with any execution-dependency findings visible | `CASE_REVIEW` (`IN_REVIEW`) |
| `CASE_REVIEW` | Human `APPROVE` with valid receipt, no blocking finding and no material OPEN execution dependency | `APPROVED_TESTWARE` (`APPROVED`) → `STOP_V1` |
| `CASE_REVIEW` | Human `REQUEST_CHANGES` with valid receipt and nonempty feedback | Old snapshot `CHANGES_REQUESTED`; new revision starts `DRAFT_CASES` |

A gate receipt is an immutable record with exactly `gate` (`DESIGN_REVIEW`/`CASE_REVIEW`), `decision` (`APPROVE`/`REQUEST_CHANGES`), `artifact_id`, `artifact_revision`, `artifact_sha256`, `input_refs` (array of `{id, revision, sha256}` for BA and, at Case Gate, approved design), `actor_id`, `actor_role: HUMAN`, `decided_at`, and `feedback` (string; nonempty for REQUEST_CHANGES). The artifact ID/revision/hash identifies the **whole collection**, not one TD/TC row. `artifact_sha256` hashes the exact immutable UTF-8 semantic payload bytes, excluding projected `review_status`; the runtime must retain those bytes. Human identity must be authenticated by the host's Human actor mechanism; typed text claiming Human status or an Agent's reproduction of a prior reply is insufficient. Receipt input refs must match current authoritative snapshots at decision time.

Only Human can issue either decision. `Continue`, `Next`, Agent PASS, validator PASS, benchmark fixture permission, and raw upstream approval text do not create receipts. An invalid/missing/stale receipt, Agent actor, unsupported decision, or wrong state rejects the event without changing state or review_status. A received Human APPROVE while Case Gate has an open material dependency is rejected without recording an approval receipt; the gate remains `CASE_REVIEW` and returns findings for a revised case or approved execution contract. New BA or design revision invalidates downstream approval/receipt applicability; affected artifacts return to their draft/review path and must be regenerated/reviewed. No receipt is rewritten or reused for a new hash.

## 5. Validators — blocking rules

Validators report `PASS` or a finding with source → TD → TC evidence; PASS never approves. They must run before each review submission and immediately before accepting a Human approval on the same immutable snapshot. Structural/trace/UNKNOWN/authority blockers prevent review submission; a declared material OPEN execution dependency may be presented in `CASE_REVIEW` for Human `REQUEST_CHANGES` but prevents `APPROVE`.

| Check | Blocking condition |
|---|---|
| Requirement → Test Design trace | Every in-scope approved FR and relevant BR has at least one TD ref or an explicit UNKNOWN question linked to its ID; every TD has ≥1 valid BA ref. A known approved behavior with no TD is a coverage gap. |
| Test Design → Testcase trace | Every approved TD with non-null expected behavior has ≥1 TC with exact TD ref and supported assertion. Null-outcome TDs remain explicitly deferred and cannot produce pass/fail cases until BA/design reapproval. A TC must have ≥1 TD ref and ≥1 BA ref. |
| Orphan and drift | Unknown, duplicated or stale FR/BR/TD/TC IDs, a TC BA ref outside the union of its referenced TD refs, or an expected result absent/contradictory in the BA+design chain blocks. Never auto-add an edge. |
| UNKNOWN preservation | A null design outcome must have linked UNKNOWN; no TD/TC assertion may supply a value, boundary, filter/order/page policy or other answer for an unresolved BA question. Missing UNKNOWN marker or leaked assertion blocks. |
| Authority conflict | Explicit BA/design/interface disagreement, use of supplemental source as target behavior, or advisory metadata as a requirement/gate blocks until the owning authority resolves it and the affected revision is renewed. |
| Execution dependency | Each needed but unapproved setup/action/observation detail must be declared on affected cases; missing declaration, ambiguous materiality, missing resolution ref, unapproved resolution, or any material OPEN dependency blocks Case Gate APPROVE. Nonmaterial OPEN items may remain visible. |
| Review transition | Wrong stage, stale artifact/input hash, invalid receipt fields, missing REQUEST_CHANGES feedback, or status inconsistent with receipts blocks and leaves state unchanged. |
| Agent self-approval | Agent/upstream/validator action cannot set APPROVED or forge/replay a Human receipt; accept only authenticated Human decision bound to the exact current snapshot. |

The validator may report semantic concerns for Human review but cannot decide a new business rule by itself. For CR-001, editable-field choice (TC-012), interval setup/end observation and relevant UI actions remain material execution dependencies until approved execution contracts make the cases deterministically runnable. The current absence of Appointment code is supplemental context, not an automatic BA requirement.
