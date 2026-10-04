---
name: project-foundation
description: Orchestrate Shared SDLC Project Foundation inventory, brownfield recovery, greenfield bootstrap, incremental refresh, exact Human review and immutable promotion.
---

# Project Foundation

This is one Shared SDLC capability. BA owns product/domain/glossary; ENGINEERING
owns architecture/runtime/deployment/ADR; TEST owns testing/automation/quality.
Use the bundled `scripts/project_foundation.py` with Python; never import from a
developer checkout when using an installed skill.

1. Read declared topology and `.sdlc/project-policy.yml`. Ask the Human to supply
   missing ownership/authority decisions; never infer a repository owner.
2. Invoke `python <skill>/scripts/project_foundation.py <mode> --project-root <root>
   --run-id <id> --input <relative-analysis-file>`. Modes: `brownfield`,
   `greenfield`, `refresh`. Use `start --mode ...` followed by owner producer
   commands and `prepare` when building a multi-producer review package.
3. Analysis uses Shared SECTION_V1 inputs, exact references and profile levels.
   Brownfield records CURRENT_SYSTEM/CONFIRMED/INFERRED/UNKNOWN. Greenfield
   proposals remain PROPOSED; DEFERRED/UNKNOWN stay explicit. Never invent BR/FR
   or historical ADR rationale from implementation evidence.
4. Present the immutable runtime review-request package under
   `.sdlc/runs/foundation/<id>/candidates/<revision>/`. STOP at the Human Gate.
   Do not generate an approval receipt or treat ANSWER, CONTINUE or validation
   PASS as approval. A material proposed target requires Engineering/Human review.
5. Only a trusted host may call installed workflow APIs, including
   `produce_semantic` and `prepare/accept/promote`, with a Human authenticator.
   The CLI intentionally has no approval flag.
   APPROVED_TARGET must bind Shared Foundation identity/revision/semantic hash.
   Brownfield acceptance preserves CURRENT_SYSTEM; it is no business approval.
6. Owner producer commands include `domain-discovery`, `architecture-discovery`,
   `test-foundation`, `adr-management`, `c4-modeling`, `render-c4`,
   `arc42-projection` and `conflicts`. Inputs are explicit JSON/YAML observations
   and exact refs. Outputs stay under `.sdlc/runs/foundation/<id>/semantic/`;
   semantic candidates are RUNTIME and C4/arc42 views are DERIVED. The review
   package binds their exact hashes, owners, unknowns, proposals, conflicts and
   Knowledge Impact routes.
7. Promote exact candidate bytes plus provenance only to snapshot paths explicitly
   declared in Policy `artifacts.optional`. Refuse different existing snapshots.
   Logs/prompts remain runtime. Readiness means PROJECT_FOUNDATION_READY, never
   feature/business approval. Doctor requires host authentication to verify a
   promoted snapshot; unauthenticated checks fail closed.

Conflicts, critical gaps, unsafe references, policy weakening and ambiguous owners
block readiness. Fix inputs through the responsible owner and start a new run;
preserve old candidates. Owner producers remain bounded semantic observations;
they do not scan source trees, persist prompts, create approval receipts or
promote their own output.
