---
name: dev-kit
description: Implement an exact Engineering Handoff VNext through persisted Dev runtime, bounded engineering review and fresh native checks.
---

# Dev Kit router

New runs use Dev VNext. BA owns WHAT; Dev owns local implementation HOW.

Preserve `APPROVAL STATE != INLINE LIFECYCLE TEXT`: `APPROVED_FOR_ENGINEERING` or `PENDING_HUMAN_REVIEW` prose alone neither authenticates nor revokes an exact approval. Revalidate the canonical proof. `open_items.blocking` remains a blocker; `open_items.non_blocking` is not automatically a semantic contradiction. Historical V1 `SUPERSEDED_BY_DELIVERY_MANIFEST` classification is read-only LEGACY_COMPAT evidence and supplies no VNext authority.

1. Read workspace and target `AGENTS.md`, topology, source and native engineering checks. Resolve the exact Engineering Handoff VNext, explicit repository identities, observed Git base revisions and allowed write paths. Do not infer scope from a feature name or Delivery Manifest.
2. Use `python -m tooling.lib.dev_kit --project-root <root> --host <trusted-host-module> start --request <request.json>`. The V2 request contains `run_id`, `change_id`, `summary`, `authority_mode`, repositories, repository roots and checks. FEATURE_DELIVERY requires an exact `upstream` Handoff ref. TECHNICAL_MAINTENANCE requires one implementation repository and exact nonbehavioral maintenance evidence with `no_what_change=true`.
3. Run `validate-authority`. The trusted host must authenticate exact BA Human approval and Foundation proof when present. Local status strings, validators and Spec Kit choices cannot create Human authority. V1 is available only through `legacy inspect` with `LEGACY_COMPAT` and `vnext_authority=false`.
4. FEATURE_DELIVERY ingests Engineering Impact V2 with `impact`, then binds `dev-plan.md`, `dev-tasks.md` and exact ED refs with `plan`. Keep unknowns explicit. Blocking unknowns prevent planning; WHAT ambiguity requires `raise-gap`, which pauses at UPSTREAM_GAP and routes BA/Human. `resume-gap` requires resolution evidence and a replacement Handoff bound to a revised approved BA baseline. Rebuild impact, plan and snapshot after replacement.
5. HIGH_RISK or active material ED requires `bind-technical-approval` with an exact authenticated Human/Tech Lead receipt bound to impact, ED set, plan/tasks, bases, scope and risk. NORMAL reversible local HOW needs no extra Human gate. Use `implementation-ready`, then `begin-implementation`. TRIVIAL maintenance skips feature impact/planning and full review while retaining its exact scope snapshot.
6. Every runtime-controlled write uses `write-source` or the exact per-write `authorize-write` guard in IMPLEMENTATION_READY/IMPLEMENTING. Do not expand scope or modify upstream authority. Implement incremental slices with focused tests and regression-first TDD. New material risk uses `escalate-risk` and `replan`; behavior/security/public-contract/cross-repository maintenance discovery blocks the fast path and requires FEATURE_DELIVERY.
7. Perform one consolidated full engineering review and submit its exact evidence with `review`. WHAT/spec findings use `raise-gap`. Blocking findings permit one `begin-fix-wave` and at most one scoped `review`; the runtime can seal exact fix resolution evidence without the optional rereview. No reviewer after each slice and no second full review.
8. Run `verify` after review/fix. Checks are BUILD, STATIC, LINT, TYPECHECK, UNIT, COMPONENT or MODULE_LOCAL_INTEGRATION. Runtime records command, exit/status, exact evidence, snapshot and implementation revisions. Complete exact BR/FR coverage needs code and test evidence for every row. Use `finalize` for canonical Dev Handoff at READY_FOR_TEST. This is not system/business acceptance, Tester PASS or merge approval.

Spec Kit `1.0.11` is workflow/state/pause/resume/bundle transport only. `spec-kit` uses generated VNext workflows; `workflow normal|high-risk` prints their definitions. Do not run `speckit.specify`, `speckit.plan`, `speckit.tasks`, `speckit.analyze` or `speckit.converge`, and do not create competing `spec.md` authority. A workflow approve choice alone cannot satisfy the technical gate.

Delivery Manifest integration is DEFERRED_NON_AUTHORITATIVE. Optional `delivery` preserves an exact ref only; it cannot authorize implementation, supply WHAT or expand repository/write scope.

Persisted `.devkit/runs/<run-id>/` state, journal, snapshots and evidence support fresh-process resume. Keep `.devkit/` and `.specify/workflows/runs/` ignored. Human authentication remains a trusted deployment callback after restart; never generate trusted receipts from request files or session memory.
