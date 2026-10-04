# BA VNext executable contracts

Implementation: `scripts/ba_vnext.py`. Compatibility: `scripts/ba_contracts.py`.
Shared Core exact refs, schemas, FR/BR parser, approval invariants, Foundation
readiness and Knowledge Impact are reused without changing their contracts.

## Versioned schemas

| Artifact | Version / constant | Purpose |
|---|---|---|
| Workflow state | 2 / STATE_V2 | RUNTIME routing, lifecycle, append-only history |
| Baseline candidate | 1 / CANDIDATE_V1 | BA_BASELINE_CANDIDATE immutable authority manifest |
| BA Decisions | 1 / DECISIONS_V1 | Named supplied Human business decisions |
| Approval receipt | 1 / RECEIPT_V1 | BA_BASELINE exact host-authenticated APPROVE |
| Engineering Handoff | 2 / HANDOFF_V2 | Exact baseline + receipt + sources + impact |

Fields are enumerated in the executable schemas. Unknown fields/versions fail
closed; no implicit extension mechanism. Exact refs use Shared Core
`validate_reference(..., revision=True)`: portable relative path, revision and
SHA-256, no traversal/symlinks/reparse paths. Secrets are forbidden.

## Baseline candidate

Fields: feature id/title, baseline id/revision, mode, sources (business_rules,
srs, decisions), domain_refs for required glossary/domain inputs, blocking and
non_blocking items, contradictions, evidence, business_identities, coverage_ids,
knowledge_impact, optional project_foundation/previous_baseline and semantic_sha256.
The manifest references source content instead of duplicating BR/SRS/decisions.
BR and functional SRS are canonical Markdown. DOCX/Draw.io/prototypes cannot
replace semantic authority. Duplicate/empty source identities fail closed.

Identity method: BA_BASELINE_CANONICAL_JSON_V1, UTF-8 sorted JSON keys, compact
separators, ensure_ascii=False, allow_nan=False, exclude only semantic_sha256.
The external receipt separately binds the manifest's exact byte SHA-256.
Changed candidate bytes/inputs require a new revision. Revision selection binds
the prior exact manifest and preserves the business identity ledger.

Each identity has id, semantic_key and ACTIVE/RETIRED status. Continuing semantic
items preserve IDs across edits; new meaning gets new IDs. Removed IDs remain
RETIRED and cannot reactivate or acquire new meaning. Active identities exactly
match canonical FR/BR in selected sources. BAREF remains authority_ref_ids
structural provenance only and never appears in coverage_ids.

## BA Decisions

Each row: id, topic, text, Human actor_id/actor_role, UTC recorded_at, exact
input_refs, affected_ids (FR/BR), status (CONFIRMED/SUPERSEDED/PROPOSED/UNKNOWN),
reciprocal supersedes/superseded_by and implemented_sources (BR/SRS refs).
Confirmed current decisions require Human evidence and must bind selected BR/SRS
before readiness succeeds. Named answers resolve only their question. Supersession
preserves history. No private reasoning is recorded.

`record_answer` accepts supplied Human content after trusted-host authentication
and returns a copy; it never approves a baseline. Draft candidates can represent
unresolved questions. Readiness rejects unresolved PROPOSED/UNKNOWN decisions,
blocking items and explicit contradictions. Contradictions beyond supplied
binding metadata require BA/Human semantic review; deterministic validators do
not infer agreement between natural-language documents.

`resolve_question` consumes an exact decisions ref and authenticates the current
Human answer for one pending topic. It closes only that topic, records ANSWER in
history, returns to DRAFT and clears approval. Old candidates cannot ignore the
latest decision; selection/readiness require its content in the selected decision
artifact (mechanical implemented_sources refresh is allowed). Persisting ANSWER
rechecks Human authentication and the exact named-topic transition.

## Lifecycle and operations

| Action | Required state | Result |
|---|---|---|
| Select candidate (CREATE/EDIT scope) | Editable state | DRAFT; new revision for changes; clear gate/derived refs |
| VALIDATE | DRAFT, deterministic checks PASS | VALIDATED, no approval |
| REQUEST_REVIEW | VALIDATED, no blockers | HUMAN_REVIEW, frozen exact refs/revision |
| APPROVE | HUMAN_REVIEW + exact authenticated receipt | APPROVED_BASELINE |
| REJECT / REQUEST_CHANGES | Candidate state | DRAFT; snapshot bytes retained |
| CONTINUE / ANSWER / GENERATED | Valid persisted state | Same lifecycle; no implicit approval |
| REVIEW | Valid state | Read-only copy; no write/advance |

Activity names never replace lifecycle states. `advance` returns a new validated
state. `publish_candidate` writes immutable bytes with byte-identical replay;
it cannot generate approval. `save_state` checks the previous disk state and
append-only transition history, then writes atomically. The host must serialize
concurrent writers. REVIEW cannot select/persist edits or advance lifecycle.
EDIT requires explicit edit_scope (artifact/manifest fields or canonical FR/BR
IDs); selection rejects changes to unaffected semantics/decisions/manifest fields.
Mechanical decision source-binding refresh may accompany selected BR/SRS edits.

## Exact Human Gate

Receipt: schema_version=1, artifact_type=BA_BASELINE, decision=APPROVE, actor_id,
actor_role=HUMAN, recorded_at, feature_id, baseline_id, baseline_revision,
baseline_semantic_sha256, baseline_manifest exact ref and decision_ref exact ref.
Optional previous_baseline must equal the prior manifest's id/revision/hash.

`validate_approval` validates candidate/sources, exact receipt binding, then invokes
`human_actor_authenticator(actor_id, parsed_receipt)`. Only a literal True from
the trusted host succeeds. The Agent cannot supply its own identity mechanism as
proof. Tests use clearly marked synthetic hosts; production supplies its trusted
identity boundary. Hashes prove integrity only. Validator PASS, ANSWER, CONTINUE,
generation, Foundation READY and UX approval cannot grant baseline approval.

## Foundation and Knowledge Impact

Optional Foundation binding: exact manifest ref, root relative to feature root
(`.` allowed), optional Foundation approval/previous refs. Existing Foundation
readiness revalidates it; target approval requires foundation_authenticator.
All binding refs are feature-relative; the BA adapter validates and rebases the
Foundation approval ref to its project root. Hosts pass foundation_authenticator
through candidate creation/selection, question resolution, validation and handoff.
Foundation context never establishes BA approval. Architecture remains Engineering
authority. Brownfield CURRENT_SYSTEM may differ from target; target_decision_id
links that topic to a current confirmed decision. INFERRED stays inferred.
Greenfield has no current-system dependency. Full Foundation is optional when
bounded feature evidence suffices; do not duplicate its repository archaeology.

Every candidate/handoff carries Shared Foundation knowledge_impact schema 1:
product/domain/architecture/testing each have affected and targets. Product/domain
are BA-owned; architecture/testing flags route assessment downstream without HOW
decisions. Existing `routes`/`refresh_outcome` remain unchanged.

## Host flow and compatibility

`new_state` → `make_candidate` → `publish_candidate` → `select_candidate` →
`advance(VALIDATE)` → `advance(REQUEST_REVIEW)` → Human decision →
`advance(APPROVE, approval=exact_ref, human_actor_authenticator=host)` →
`make_handoff`. Consumption calls `validate_handoff` to revalidate exact proof.
JSON and existing bounded Shared Core YAML are supported.

Existing validator paths dispatch through ba_contracts. Old Shared Core import
adapters retain identity/behavior. V1 state/handoff reads report LEGACY_COMPAT,
insufficient evidence for VNext approval. Arbitrary stages/status strings are not
migrated into receipts. Read-only CLI fails closed for approved VNext state/handoff
without a trusted host authenticator and offers no self-approval option.

Atomic SRS/BR/Draw.io/DOCX skills remain. New candidate revisions clear active
derived routing refs; bytes/history remain and affected outputs require refresh.
UX review remains separate. Packaging/docs/examples/install cleanup is Wave 2.
