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
   `greenfield`, `refresh`. `inventory` and `doctor` are independent checks.
3. Analysis uses Shared SECTION_V1 inputs, exact references and profile levels.
   Brownfield records CURRENT_SYSTEM/CONFIRMED/INFERRED/UNKNOWN. Greenfield
   proposals remain PROPOSED; DEFERRED/UNKNOWN stay explicit. Never invent BR/FR
   or historical ADR rationale from implementation evidence.
4. Present the immutable runtime review-request package under
   `.sdlc/runs/foundation/<id>/candidates/<revision>/`. STOP at the Human Gate.
   Do not generate an approval receipt or treat ANSWER, CONTINUE or validation
   PASS as approval. A material proposed target requires Engineering/Human review.
5. Only a trusted host may call the installed `workflow.prepare/accept/promote`
   APIs with a Human authenticator. The CLI intentionally has no approval flag.
   APPROVED_TARGET must bind Shared Foundation identity/revision/semantic hash.
   Brownfield acceptance preserves CURRENT_SYSTEM; it is no business approval.
6. Promote exact candidate bytes plus provenance only to snapshot paths explicitly
   declared in Policy `artifacts.optional`. Refuse different existing snapshots.
   Logs/prompts remain runtime. Readiness means PROJECT_FOUNDATION_READY, never
   feature/business approval. Doctor requires host authentication to verify a
   promoted snapshot; unauthenticated checks fail closed.

Conflicts, critical gaps, unsafe references, policy weakening and ambiguous owners
block readiness. Fix inputs through the responsible owner and start a new run;
preserve old candidates. Rich discovery, arc42 prose, C4 and ADR authoring route
to future BA/Engineering/Test capabilities. They are not provided here.
