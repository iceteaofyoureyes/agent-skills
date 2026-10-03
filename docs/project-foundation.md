# Project Foundation workflow core

Project Foundation is a Shared SDLC capability for inventory, evidence recovery,
target bootstrap, incremental refresh, Human review and immutable publication.
BA owns product/domain/glossary; ENGINEERING owns architecture/runtime/deployment/
ADR; TEST owns testing/automation/quality. It is not another Kit or a semantic
authority. Shared schemas, profiles, exact approvals and promotion own semantics.

## Modes

| Mode | Evidence | Purpose |
| --- | --- | --- |
| BROWNFIELD_RECOVERY | CURRENT_SYSTEM, authenticated CONFIRMED, INFERRED, UNKNOWN | Bounded reconstruction of current reality |
| GREENFIELD_BOOTSTRAP | PROPOSED, authenticated APPROVED_TARGET, DEFERRED, UNKNOWN | Intent/constraint-based target review |
| FOUNDATION_REFRESH | Exact prior manifest, changes, generic knowledge impact | NO_FOUNDATION_CHANGE or FOUNDATION_UPDATE_REQUIRED; neither is approval |

Inventory deterministically classifies **candidate** knowledge by paths and Policy.
It captures repository identity, relative path, Shared artifact class, owner/source
candidates, hash and byte size; no file contents are copied. Policy declares a
canonical location, not approval of its bytes. Recovery takes explicit section
evidence; it does not invent BR/FR from code. CONFIRMED requires a trusted host's
exact-reference policy authority check. Historical ADR rationale cannot be INFERRED.
Explicit authority claims/contradictions become conflicts. Filename similarity
alone cannot prove two documents claim the same authority; callers supply claims.
Unknowns remain explicit without requiring reconstruction of the whole system.

## Lifecycle, runtime and durable artifacts

`ANALYSIS → REVIEW_REQUIRED → ACCEPTED_BASELINE / APPROVED_BASELINE → PROJECT_FOUNDATION_READY`.

Run state includes project/mode/profile, topology/policy references, inputs,
artifacts, open items and history. Work stays under `.sdlc/runs/foundation/<id>/`:
inventory, immutable candidate manifest/evidence/gaps/questions, impact and review
request. Config, source evidence, candidate and receipts bind exact hashes and
revisions. Input drift blocks reuse. Changed inputs/requested changes need a new
run, preserving prior candidates. Exact partial publication can replay and commit
state last. This filesystem workflow expects one trusted host writer per run.

Durable manifest/provenance destinations must be declared in Project Policy
`artifacts.optional`, inside explicit topology roots. Existing `authority` locations
retain their semantic ownership. No product/domain/architecture/testing path is
hard-coded. Traversal, symlink/reparse escapes, ambiguous ownership and different
existing snapshots fail closed. Raw prompts/logs cannot become semantic inputs or
promoted payloads. All promoted bytes are the exact validated candidate snapshot.

## Human boundary and readiness

CONTINUE, ANSWER, validator PASS and generation never approve. The deterministic
review package binds manifest id/revision/Shared semantic hash and includes critical
blockers, unknowns, conflicts, proposed decisions, evidence, impact and owner routes.
The workflow emits no Human receipt; it verifies and retains externally supplied bytes.

The trusted host owns Human identity, authorization and semantic review, including
Engineering approval for material architecture targets. It authenticates the exact
Shared `APPROVAL_RECEIPT_V1`; accepting actor names, `actor_role: HUMAN`, hashes or
flags alone is insufficient. `authority_authenticator(domain, exact_ref)` verifies
existing canonical source approval. No credentials/authenticator settings are stored.

`candidate_manifest` is pure structural assembly for host preview, not approval.
`prepare` refuses to persist APPROVED_TARGET without exact authenticated approval.
Transition from a prior observed baseline binds its revision/hash as well. PROPOSED
remains PROPOSED. Blocking material proposals cannot become ready baselines.
Brownfield acceptance preserves CURRENT_SYSTEM, never target/business approval.

`accept` rechecks receipt binding and Shared readiness. `promote` checks again,
publishes exact semantic bytes and source/receipt provenance, then commits READY.
Doctor requires host authentication to verify accepted/promoted snapshots; without
it, checks fail closed. A valid unreviewed candidate is NOT_READY. Critical gaps
and conflicts BLOCK readiness; nonblocking PARTIAL/UNKNOWN/DEFERRED may remain
READY when the Shared profile allows. PROJECT_FOUNDATION_READY is not feature or
business approval. Existing Kit Doctor outputs and defect/retest contracts remain.

## Invocation and installation

Use the [project-foundation skill](../project-foundation/SKILL.md):

```text
python <skill>/scripts/project_foundation.py inventory --project-root <project>
python <skill>/scripts/project_foundation.py brownfield --project-root <project> --run-id recovery-1 --input analysis.json
python <skill>/scripts/project_foundation.py greenfield --project-root <project> --run-id bootstrap-1 --input analysis.json
python <skill>/scripts/project_foundation.py refresh --project-root <project> --run-id refresh-1 --revision R2 --input refresh.json
python <skill>/scripts/project_foundation.py doctor --project-root <project> --run-id recovery-1
```

The project supplies `.sdlc/topology.json` and `.sdlc/project-policy.yml` using
Shared v1 contracts. Analysis input accepts `sections` (SECTION_V1), `blockers`,
`impact`, exact `previous_ref`, `authority_claims` and `contradictions`. Refresh
requires an exact previous manifest. Impact v1 has `areas.product/domain/architecture/
testing`, each with boolean `affected` and a project-relative `targets` list.
Observed section/source changes add owner routes without clearing supplied impact.
MINIMAL/STANDARD use existing profile rules. EXTENDED fails closed when the existing
Policy cannot declare its required operations entry point; no location is invented.

CLI stops at review, with no approve switch. Trusted host integrations import the
installed `shared.sdlc.foundation.workflow`: `start`, `candidate_manifest`, `prepare`,
`accept`, `promote`, `doctor`. Inventory and impact modules are independently usable.
Authenticators are in-process host callbacks; project-provided code is not loaded.

`tooling.prepare_agent_profile --foundation` copies the skill and deterministic
Shared payload to an explicitly expanded fresh profile. The default Dev-only
profile and its context-purity rules are preserved. `tooling.install_dev_kit`
installs the capability beside Shared runtime. A
standalone skill copy needs `scripts/shared-sdlc-core.zip`; missing payload fails
closed. Canonical source is `shared/**`; archives are derived installation payloads.
Regenerate via `python -m tooling.regenerate_shared_sdlc_payload` then
`python -m tooling.regenerate_dev_provenance`. Kit versions/ownership do not change.

## Synthetic acceptance and Wave 2 extensions

`tooling/tests/fixtures/synthetic-greenfield-foundation` supplies neutral intent,
constraints, material PROPOSED architecture and DEFERRED deployment, without code.
`synthetic-brownfield-foundation` separates docs/module roots with existing code/config,
CURRENT_SYSTEM, INFERRED, UNKNOWN and duplicate product authority claims. Fixtures
have no receipt. Tests inject synthetic host decisions only in temporary projects,
prove refusal before review and exact promotion after authentication. Installed
probes run with Python isolation outside the checkout and assert imported paths.

Run `python -m unittest tooling.tests.test_project_foundation -v` plus
`python -m unittest discover -s tooling/tests -v`. Actual symlink checks may skip
when Windows privileges are unavailable; a separate reparse-attribute guard test runs.

Evidence records, SECTION_V1 and impact owner routes are extension interfaces for
BA domain discovery, Engineering architecture discovery/C4/arc42 projection and
evidence-backed ADR authoring, and TEST foundation discovery. Owner-specific direct
APIs are documented in [Foundation semantic producers](foundation-semantic-producers.md).
Installer/package and workflow extension integration remains Wave 2B work.
Extensions preserve Shared semantic ownership, exact Human Gates and runtime separation.
