# Foundation semantic producers

Wave 2A implements the owner producer layer in `shared.sdlc.foundation.producers`.
These direct Python APIs consume explicit observations, declared topology/Project
Policy and exact refs. They perform no repository scan, LLM invocation, filesystem
write, approval or publication. Installer/profile/package and workflow integration
is deferred to Wave 2B, except for the minimal runtime closure described below.

## Inputs and records

`produce(root, topology, policy, producer, artifact_id, revision, mode, observations)`
supports domain-discovery, architecture-discovery and test-foundation. `adr(...)`
and `c4_model(...)` assemble structured candidates. Public outputs always pass
`validate_artifact(...)`; renderers revalidate refs, ownership and gates on reuse.

Observations have `id`, `topic`, `statement`, `basis`, `references`, `status` and
`questions`. Exact refs use Shared `{path, revision, sha256}`. Callers can select
Foundation inventory paths/hashes and supply explicit revisions; inventory
classification alone establishes neither semantic meaning nor approval.

Records add owner, evidence label and source producer. Artifacts carry explicit
schema_version 1, identity/revision, mode, exact configuration refs and RUNTIME
classification. IDs are caller-assigned, stable within a revision and unique
without case ambiguity. FR/BR/BAREF IDs are rejected. Unknown fields, secrets and
prompt/reasoning fields fail closed. Missing required topics become UNKNOWN with
questions; alternatives and optional C4 levels are never invented to fill gaps.

Topology and Policy must match exact canonical configuration files. TEST's
automation repository role is a declared Policy value traceable through
`project_policy_ref`; it does not assert that an automation repository exists.
Semantic refs must stay inside declared roots. Shared validation rejects traversal,
external absolute paths, symlink/reparse escapes, hash drift and raw prompt/runtime
inputs. File contents are hashed/validated, never copied into records. The trusted
caller interprets what evidence supports: a valid hash proves source identity,
not the truth of a supplied interpretation.

| Basis | Label | Boundary |
| --- | --- | --- |
| OBSERVED | CURRENT_SYSTEM | Observable implementation/config/test/document fact |
| INFERRED | INFERRED | Interpretation with exact evidence |
| AUTHORITY | CONFIRMED | Exact domain Policy authority plus trusted host authentication |
| DECISION_EVIDENCE | CURRENT_SYSTEM | Explicit decision evidence, not code/config presence |
| PROPOSED | PROPOSED | Target suggestion; may have no source evidence |
| UNKNOWN | UNKNOWN | Explicit unresolved meaning plus question |
| DEFERRED | DEFERRED | Exact referenced deferral permitted by mode |
| APPROVED_TARGET | APPROVED_TARGET | Exact enclosing Foundation snapshot and authenticated Human approval |

Brownfield permits CURRENT_SYSTEM/CONFIRMED/INFERRED/UNKNOWN. Greenfield permits
APPROVED_TARGET/PROPOSED/DEFERRED/UNKNOWN. Refresh preserves the existing Shared
union. Factual records require exact refs. PROPOSED/UNKNOWN can be evidence-free
because they explicitly claim no factual or approved authority. COMPLETE cannot
mask missing evidence. Basis and label cannot be reassigned independently.

## Owner responsibilities

BA domain discovery covers product goals, glossary, actors, entities, lifecycle,
business-rule candidates and gaps. Code behavior stays CURRENT_SYSTEM; ambiguous
terminology stays INFERRED. No canonical FR/BR is generated. BA workflows and
Human decisions retain canonical business responsibility. Product goals authenticate
the product Policy domain; other BA topics authenticate domain.

Engineering discovery covers constraints, scope, solution strategy, architectural
patterns, building blocks, runtime, deployment, crosscutting concepts, quality
facts, risks, decision inventory, historical rationale and gaps. Pattern inference
cannot be an OBSERVED fact. Missing deployment/runtime facts stay UNKNOWN;
technology presence cannot establish historical rationale.

TEST discovery covers levels, ownership, unit/component vs API/integration/E2E/
system split, execution topology, fixtures/data, gates, evidence expectations,
automation role and gaps. Tool presence is CURRENT_SYSTEM; recommended strategy
is PROPOSED until reviewed. No feature Test Design/Testcases are generated. There
is no tool/vendor invariant. Test Kit retains feature testing responsibility.

## C4 model and rendering

`c4_model(..., elements, relationships)` consumes elements with an observation
`record`, `kind`, and optional `parent`; relationships have `record`, `source`,
`target`, and `level`. Topics are c4_element/c4_relationship.

Context/Container are defaults: one owned SYSTEM and at least one CONTAINER with
explicit relationships. ACTOR/EXTERNAL_SYSTEM have no ownership parent. CONTAINER
belongs to SYSTEM; optional COMPONENT belongs to CONTAINER; optional deployment
INSTANCE belongs to DEPLOYMENT_NODE. Instance statements describe what is deployed;
evidence-backed relationships can describe associations. No additional levels
are generated. Duplicate IDs/edges, invalid endpoints, orphan nodes, parent cycles
and level/ownership mismatches fail closed. Each element/relationship needs exact
architecture evidence or explicit PROPOSED/UNKNOWN.

`render_c4(...)` produces deterministic dependency-free Mermaid. IDs/edges are
sorted and labels are encoded to prevent caller text becoming diagram syntax.
The view is DERIVED with an input hash. The structured candidate stays RUNTIME;
rendering/validation cannot create authority.

## ADR recovery, proposal and approval

`adr(..., kind, observations)` supports RECOVERED, PROPOSED and APPROVED_TARGET.
It requires one context, decision, rationale, consequences and gaps record. Missing
fields become UNKNOWN, except that the chosen kind requires a known decision.
Alternatives appear only when explicitly supplied.

RECOVERED emits RECOVERED_CURRENT_SYSTEM. Rationale/alternatives remain UNKNOWN
unless backed by explicit DECISION_EVIDENCE or authenticated authority. Inference
and ordinary technology/config observations cannot establish historical rationale.
New target decisions stay PROPOSED after validation. Approved target decisions
require an exact complete ADR snapshot, not approval of another architecture text.

## Existing approval binding

The trusted host supplies `authority_authenticator(domain, exact_ref)` for CONFIRMED.
For APPROVED_TARGET, `approval_context` contains `manifest`, `approval` (exact
receipt ref), `human_actor_authenticator` and optional `previous` when the existing
receipt binds a prior Foundation revision.

The unmodified Foundation manifest must contain an APPROVED_TARGET section of the
same owner explicitly referencing the complete producer artifact's canonical JSON
bytes, revision and SHA-256. Policy paths, section owners and refs are rechecked.
Existing `_approval` authenticates the Shared Human receipt and Foundation
identity/revision/hash. The host retains Engineering approval responsibility.
Unrelated approval, validator success and artifact/receipt drift cannot approve
a target. All producer artifacts remain RUNTIME pending separate publication;
owner-approved baselines/ADRs can become CANONICAL only through governance.
No Shared schema or Human Gate extension is introduced.

## arc42 projection

`arc42(artifacts, root, topology, policy, manifest=None)` revalidates all semantic
inputs and optional existing Foundation manifest. It produces one Markdown file
representation and a structured map of all 12 Standard Profile sections. Empty
input additionally requires explicit `configuration_revision`; no revision is
guessed. Output ordering/hashes are deterministic. UNKNOWN/PARTIAL/DEFERRED remain
visible with refs, owner routes, questions and ADR decision status/rationale.
BA glossary feeds section 12; TEST foundation feeds section 10. Section 1 links
authenticated product-goal sources. Business-rule candidates stay outside arc42;
product requirements are not copied into another authority.

The artifact is DERIVED. Generation does not approve it or change evidence labels.
Architecture governance/promotion uses existing owner/Foundation workflows;
mechanical connections remain Wave 2B work.

## Conflicts and artifact classes

`conflicts(artifacts, disagreements, root, topology, policy)` consumes explicit
disagreements: domain plus two or more claims identified by producer/record ID.
Deterministic UNRESOLVED records preserve exact refs and labels. Authenticated BA
business authority gets a preferred-claim marker for business meaning, preserving
the competing claim. Competing authority, stale Engineering docs/current evidence
and TEST recommendations remain unresolved. Shared exact Policy paths across
domains are valid; no model preference ranks sources.

Candidate discovery/semantic/review artifacts are RUNTIME; C4/arc42 views and
indexes are DERIVED; source/config/test/CI observations are EVIDENCE; exact review/
promotion bindings remain HANDOFF_MANIFEST under existing workflows. Producer
validation does not relabel any of these as CANONICAL.

## Public fixtures and verification

`tooling/tests/fixtures/foundation-semantic-producers.json` composes neutral catalog
observations over the existing public synthetic fixture: brownfield domain/
architecture/testing, architecture inference, UNKNOWN ADR rationale, greenfield
proposals, C4 Context/Container candidate and visible UNKNOWN/PARTIAL arc42 sections.
Synthetic host receipts exist only in temporary test projects.

```text
python -m unittest tooling.tests.test_foundation_producers -v
python -m unittest discover -s tooling/tests -v
```

Actual Windows symlink checks may skip without privileges; simulated reparse guards
run independently. Wave 2B should wire installer/profile/package allowlists,
regenerate payload/provenance, connect orchestrator extensions, exercise installed
producer payloads and complete cross-producer public workflow acceptance.

### Unavoidable packaging exception

Existing `test_ba_archive_exact_allowlist_bytes_and_deterministic_regeneration`
requires every Python source under `shared/**` to be in the Shared runtime payload.
Adding this module without updating the closure fails full regression. Wave 2A
therefore adds one Dev runtime allowlist entry and regenerates the two existing
Shared ZIPs and Dev runtime provenance with official scripts. This makes the source
module available in those payloads, but adds no workflow commands, profile options,
Kit migration or broader package integration. Remaining Wave 2B wiring is deferred.
