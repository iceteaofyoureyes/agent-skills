# Shared SDLC project contracts v1

Shared contracts validate project declarations and evidence. They do not scan
repositories, generate architecture documents, supply business rules, or advance
workflow state. Canonical Python sources live under `shared/sdlc`; installed kits
carry those same sources. The authoritative v1 definitions are
`PROJECT_TOPOLOGY_V1`, `PROJECT_POLICY_V1`, `FOUNDATION_MANIFEST_V1`, and
`APPROVAL_RECEIPT_V1` in their contract modules. `schema.py` implements their
strict, dependency-free JSON Schema vocabulary.

The precedence is Human-approved decisions > Shared SDLC invariants > Project
Policy > Kit / skill instructions > runtime defaults. A valid declaration is
not an approval. Policies cannot override these invariants, resolve business
UNKNOWN, or substitute for approved requirements.

## Format, versions and references

Every document has integer `schema_version: 1`; booleans, floats, strings and
future versions fail. Unknown fields fail at every nesting level. There is no
extension namespace or automatic migration in v1. A later version must define
a separate schema and explicit reader boundary.

`read_document(text)` accepts strict JSON and a bounded YAML subset: two-space
indented mappings, lists, mapping list items, quoted strings, integer scalars,
`true`, `false`, `null`, and JSON inline arrays/objects. YAML single-quoted
scalars decode doubled apostrophes and keep backslashes literal; unmatched or
unescaped quotes and adjacent literal concatenation fail. Double-quoted scalars
use JSON string decoding. Duplicate keys and non-finite numbers, including
numeric exponent overflow, fail in top-level and inline JSON. Finite JSON
floats retain normal float values; current v1 schema fields still reject floats.
Anchors, aliases, tags, block strings,
inline comments, YAML implicit booleans and numeric/date-like plain strings are
unsupported. Quote such strings or use JSON. A JSON document is valid at a
`.yml` location. Existing kit parsers are unaffected.

Portable paths use `/` separated ASCII letter/digit/underscore/dot/hyphen
components. Empty, `.` and `..` components, absolute paths, drive letters,
backslashes, reserved Windows device names, trailing dots, spaces and encoded
separators fail. Case-insensitive duplicates fail where distinct locations are
required. References have `{path, sha256}` and an optional `revision`; SHA-256 is lowercase hex.
Foundation references require an immutable revision. Reference checks reject
missing files, symlinks/reparse points (including ancestors) and byte drift.
Checks read declared files only and write nothing. Hashes prove integrity,
not Human identity or the truth of referenced contents.

## Project topology

`topology/contract.py` owns `validate_topology(data)` and `read_topology(text)`.
The contract has `project: {id}` and a nonempty `repositories` list with
`{id, path, repository, role}` per row. A repository name is `owner/name` and
roles are semantic identifiers chosen by the project. Multiple implementation
or service repositories and repeated semantic roles are supported.

V1 choices: IDs, checkout paths and remote names are unique without regard to
case. Nested repository checkout roots are rejected because they make ownership
ambiguous. The contract does not verify remote access or alter repository
ownership. No Python or PowerShell repository roster is generated.

```yaml
schema_version: 1
project:
  id: example-project
repositories:
  - id: docs
    path: example-docs
    repository: owner/example-docs
    role: project_documentation_authority
  - id: service
    path: services/api
    repository: owner/example-api
    role: service_implementation
```

## Shared Project Policy

`policy/contract.py` owns `validate_policy(data)` and the read-only
`read_policy(project_root)`. The canonical project-owned location is
`.sdlc/project-policy.yml`. All seven areas are required:

| Area | Required fields and meaning |
|---|---|
| `schema_version` | Integer 1 |
| `project` | `language`: language identifier |
| `foundation` | `profile`: `arc42-standard-v1` |
| `authority` | `product`, `domain`, `architecture`, `testing`, `features`: portable source locations |
| `workflow` | `feature_root`: portable directory; `branch_convention`: naming guidance |
| `testing` | `automation_repository_role`: semantic repository role |
| `artifacts` | `optional`: list of portable artifact paths, including an empty list |

Authority locations may share a document. They are routing declarations;
validation does not make the locations or their contents approved. Optional
artifacts remain optional and cannot replace canonical authority. Credential
fields and recognizable credential transport values (password assignments,
Bearer credentials, private keys, credential-bearing URLs and API tokens) are
forbidden. V1 has no field for business behavior or weakening gates/invariants.
Arbitrary prose or referenced file contents are not automatically trusted.

The existing `.test-kit` project testing policy is unchanged. It remains a
subordinate Test-specific guidance layer. Shared Policy does not bootstrap,
delete, rewrite or replace it.

## Project Foundation

`foundation/profiles.py` owns the deeply immutable
`PROJECT_FOUNDATION_PROFILE_ARC42_V1` (`id: arc42-standard-v1`). Twelve semantic
sections are required in every manifest; they need not be twelve physical files.

| Section key | Arc42 section |
|---|---|
| `introduction_goals` | 01 Introduction & Goals |
| `constraints` | 02 Constraints |
| `context_scope` | 03 Context & Scope |
| `solution_strategy` | 04 Solution Strategy |
| `building_block_view` | 05 Building Block View |
| `runtime_view` | 06 Runtime View |
| `deployment_view` | 07 Deployment View |
| `crosscutting_concepts` | 08 Crosscutting Concepts |
| `architecture_decisions` | 09 Architecture Decisions |
| `quality_requirements` | 10 Quality Requirements |
| `risks_technical_debt` | 11 Risks & Technical Debt |
| `glossary` | 12 Glossary |

`foundation/contract.py` exposes `validate_manifest(data)`,
`read_manifest(text)`, `manifest_sha256(data)`, `validate_transition(...)` and
`foundation_readiness(...)`. A manifest has these required fields:

| Field | V1 definition |
|---|---|
| `schema_version`, `id`, `revision` | Version 1 and stable immutable artifact identity/revision |
| `profile` | `{id: arc42-standard-v1, level: MINIMAL / STANDARD / EXTENDED}` |
| `mode` | `GREENFIELD_BOOTSTRAP`, `BROWNFIELD_RECOVERY`, `FOUNDATION_REFRESH` |
| `authority` | One semantic owner string for each product/domain/architecture/testing/features area |
| `entry_points` | Named exact file references; operations is additionally supported |
| `sections` | All twelve keys, each `{status, owner, evidence, blocking, references}` |
| `blockers` | List of `{id, critical, resolved}`; booleans are explicit |

Section owners must match a declared authority owner. Multiple domains may
share an owner; one section cannot declare multiple conflicting owners. Blocker
IDs and section reference paths are unique without regard to case. Statuses are
`COMPLETE`, `PARTIAL`, `UNKNOWN`, `NOT_APPLICABLE`, `DEFERRED`. Known evidence
requires exact references; `COMPLETE` also requires evidence other than UNKNOWN.
An observed/inferred architecture section remains descriptive evidence. It does
not become business requirements or a historical ADR by being listed here.

| Mode | Permitted evidence classifications |
|---|---|
| Brownfield recovery | `CURRENT_SYSTEM`, `CONFIRMED`, `INFERRED`, `UNKNOWN` |
| Greenfield bootstrap | `APPROVED_TARGET`, `PROPOSED`, `DEFERRED`, `UNKNOWN` |
| Foundation refresh | Union of the above |

Refresh can retain observations and record targets together. Target approval
requires explicit evidence; changing mode does not convert observations into
approved decisions.

### Readiness profile choices

The level rules are profile data, applied identically to all modes:

| Level | Required entry points |
|---|---|
| MINIMAL | product, architecture |
| STANDARD | product, domain, architecture, testing, features |
| EXTENDED | standard entry points plus operations |

All levels require twelve owned section declarations. In all levels PARTIAL,
UNKNOWN, NOT_APPLICABLE and DEFERRED are explicitly permitted when `blocking`
is false. An incomplete blocking section or unresolved critical blocker fails
readiness. Resolved critical and unresolved noncritical items remain recorded.
These v1 choices do not require every section to be COMPLETE.

`foundation_readiness(data, root, *, approval=None, previous=None,
human_actor_authenticator=None)` validates the structure, required entry points,
every declared reference/hash, ownership and blockers. Any supplied previous
manifest is validated and checked for identity/revision consistency, regardless
of evidence classification. A changed manifest needs a new revision.
Success returns `PROJECT_FOUNDATION_READY` and its semantic manifest SHA,
with `human_approval: false` and `feature_ready: false`.

### Explicit target approval binding

`validate_transition(previous, current, root, *, approval=None,
human_actor_authenticator=None)` checks both manifests and their exact source
references. Any APPROVED_TARGET claim requires a separate exact approval
reference and a trusted host authentication callback returning exactly `True`.
The callback validates the named Human against the complete receipt; a declared
`actor_role: HUMAN` or a matching hash cannot authenticate the actor.

The v1 receipt has `schema_version`, `decision: APPROVE`, `actor_id`,
`actor_role: HUMAN`, `artifact_id`, `artifact_revision`, `manifest_sha256`, and
an exact `decision_ref` with revision. The approval reference revision must
match the current manifest. When prior evidence is supplied, the receipt also
requires `previous_revision` and `previous_manifest_sha256` bound to that exact
prior manifest. Unbound prior claims fail. ANSWER, CONTINUE, validator success,
generated documents and Agent identities cannot approve a target.

Manifest hashing is explicitly `FOUNDATION_MANIFEST_CANONICAL_JSON_V1`: UTF-8
JSON with sorted keys, compact separators, unescaped Unicode and no NaN.
Receipt/file references hash exact bytes. The receipt is separate from the
manifest so its reference does not create a circular semantic hash.
The caller must supply recorded prior evidence when claiming an observation
transition; a standalone greenfield approval binds only its declared target.
This API validates approval evidence; it persists no receipt and approves no
feature or business behavior.

## Readiness vocabulary and Doctor compatibility

This page defines Shared compatibility claims, not the suite lifecycle. The current integrated flow is in [Architecture](ARCHITECTURE.md); the current readiness vocabulary has no READY_TO_MERGE state. See [Readiness states](READINESS_STATES.md).

| Readiness | Normative scope |
|---|---|
| PACKAGE_READY | Installed package integrity and prerequisites are available |
| PROJECT_CONFIG_READY | Project routing and required configuration are valid |
| PROJECT_FOUNDATION_READY | Declared profile/manifest meets the checks above |
| CAPABILITY_READY | The requested capability's own prerequisite checks succeed |
| FEATURE_READY | The feature's applicable authorities, handoff and gates are satisfied |
| READY_FOR_TEST | Approved feature inputs support the intended testing scope |
| EXECUTION_READY | Approved cases/oracle, environment and execution inputs are available |
| READY_FOR_RETEST | The fix/handoff and retest inputs support the assigned scope |
| VERIFIED | Tester verification evidence satisfies the existing lifecycle |

The vocabulary defines separate claims, not an automatic readiness ladder.
It adds no alternate lifecycle or Human Gate. No state grants Human approval.
Merge/release remains a separate Human decision after verification.
Existing producers retain their current output formats.

`readiness/compatibility.py:normalize_doctor(status)` maps current Doctor
READY to a positive PACKAGE_READY assessment. DEGRADED and FAIL map to a
negative PACKAGE_READY assessment while retaining the original status.
DEGRADED is conservative because the intended optional capability is not
specified by this compatibility function. The mapping never emits feature
readiness or Human approval; it does not rename current Doctor outputs.

## Promotion ownership and migration

`promotion/immutable.py` owns generic `publish_immutable(writes, *, stage,
transition, writer=None)` and `promotion_record(source, content,
approval_receipt, receipt_bytes)`. Source identity/revision/hash and approval
reference/hash bind exact bytes. A generic record asserts no Human approval.
Publication checks the entire write set before publishing, rejects duplicate
destinations and unsafe paths, permits exact replay after interruption, and
refuses overwriting different snapshots. It does not commit workflow state.
Output filenames and newly created directory components use the portable path
profile, rejecting reserved Windows names, ADS and illegal components before
any write. Existing absolute root directories may contain legitimate spaces
or Unicode. Traversal, aliases, file/ancestor collisions and reparse destinations
fail preflight.
Every existing ancestor must be a directory. An existing destination must be a
regular file with identical bytes for replay; an occupied directory position
cannot cause an earlier output to publish before the operation is rejected.

Test-specific loading, receipt authentication, Test Design/Case states and
rendering now belong to `tooling/lib/test_promotion.py`. That adapter calls
generic Shared publication only after its unchanged Test gates validate.
Historical `tooling.lib.testware_promotion` aliases the same adapter module,
including private globals, fault injection hooks and pickle identity. The
old Shared Test-specific module is removed to enforce the dependency direction.
Other Wave 1 historical imports and BA/Delivery/UX/execution semantics remain.

| Responsibility | Current owner | Historical compatibility |
|---|---|---|
| Test Design/Case promotion gates | `tooling.lib.test_promotion` | `tooling.lib.testware_promotion` |
| Immutable generic publication | `shared.sdlc.promotion.immutable` | Called by the Test adapter |
| Project topology/policy | `shared.sdlc.topology` / `policy` | New, no output migration |
| Foundation profile/manifest and producer orchestration | `shared.sdlc.foundation` | Shared schemas/ownership unchanged |
| Doctor normalization | `shared.sdlc.readiness.compatibility` | Existing Doctor output preserved |

Generic Shared code imports no Test Kit runtime. Tests check static imports,
including lazy function imports/literal dynamic imports, and import all shared
modules with Test imports blocked in an isolated subprocess. Ownership tests
retain module/symbol/import-order/pickle assertions and locate the migrated
Test owner under tooling instead of Shared.

BA's existing deterministic zip closure and Test/Dev explicit allowlists carry
all new schema definitions and profile data. Positive kit ownership, existing
hash algorithms and versions are preserved. After editing sources, regenerate:

```text
rtk proxy python -m tooling.regenerate_shared_sdlc_payload
rtk proxy python -m tooling.regenerate_test_package
rtk proxy python -m tooling.regenerate_dev_provenance
```

Project Foundation wires explicit BA, Engineering and Test producer observations
into immutable RUNTIME artifacts and deterministic review packages. C4 and arc42
renderings remain DERIVED. Installed profile/runtime packaging carries this shared
capability; trusted Human approval remains host-only.
