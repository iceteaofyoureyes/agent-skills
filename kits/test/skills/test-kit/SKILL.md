---
name: test-kit
description: >-
  Route approved BA Engineering Handoff VNext through Human-gated Test Design
  and manual testcase creation. V1 is inspection-only compatibility.
---

# Test Kit VNext Workflow

Test Kit owns exact authority ingestion, canonicalization, persistence and Human Gates. The pinned TEA and Katalon skills own analysis and drafting. Execute both skills inside the current agent session.

The host runtime calls the public functions from `tooling.lib.test_kit_vnext` and supplies trusted BA, UX, technical and Human authenticators. Never replace a host authenticator with a callback constructed from receipt fields or an operator response.

## New manual test request

1. Read project `AGENTS.md`, the feature's exact Engineering Handoff VNext and any project Test Policy. Do not require a Delivery Manifest.
2. Revalidate the BA handoff through the canonical BA VNext reader and trusted Human authenticator. Reject legacy BA V1 as production authority.
3. Start a persisted VNext run with `prepare_vnext_design`. It records the exact BA baseline, approval receipt and source refs. UX is required only when the exact authority context explicitly sets `ux_required: true`. If optional UX is supplied and consumed, validate and bind its exact approved contract, receipt, feature/revision, source bytes and snapshot hash. A prototype remains `REVIEW_EVIDENCE`.
4. Read the prepared instructions and pinned `bmad-testarch-test-design/SKILL.md`. Run TEA in this agent session and save its raw completed output only at the prepared path.
5. Run `finalize_vnext_design`. It preserves canonical Test Design fields and raw TEA evidence, validates FR/BR-only trace, and reaches `DESIGN_REVIEW` only on validator PASS. PASS is not approval.
6. Present the exact persisted Design and stop for an explicit Human Gate receipt. The receipt binds the exact artifact ID, revision, hash and current input refs. `REQUEST_CHANGES` creates a new immutable revision.
7. After `APPROVED_DESIGN`, start Cases with `prepare_vnext_cases`. An exact Dev Handoff V2 may supply technical setup/action/observation context. It cannot change BA or approved UX behavior.
8. Read the prepared instructions and pinned `create-test-cases/SKILL.md`. Run Katalon in this agent session and save its raw completed output only at the prepared path.
9. Run `finalize_vnext_cases`. It preserves the canonical testcase fields, exact Design refs and execution dependencies, then reaches `CASE_REVIEW` only on validator PASS.
10. Present the exact testcase collection and stop for an explicit Human Case Gate receipt. Approval creates the VNext `HANDOFF_MANIFEST` at terminal state `APPROVED_TESTWARE`.

Never infer approval from `CONTINUE`, `ANSWER`, `REVIEW`, `PASS`, generated output or lifecycle prose. The Human Gate host callback authenticates the receipt, then Test Kit rechecks all exact authority bytes.

## Authority and expected behavior

- BA owns business WHAT; canonical trace contains only `BR-*` and `FR-*`.
- `BAREF:*` is locator evidence and cannot appear in canonical `requirement_refs`.
- Exact approved UX context supplies optional/required UX authority, but cannot override BA behavior. Generic words in Design or testcase prose never infer a UX requirement. Free-form BA/UX/Test semantic consistency remains Human review responsibility; the runtime validates exact identities and bytes, not natural-language equivalence.
- Dev Handoff V2 and implementation are technical context, not business or UX oracles.
- TEA, Katalon and project Test Policy are advisory/guidance only.
- Preserve unresolved BA `UNKNOWN` outcomes. Do not invent a concrete testcase result.
- `APPROVED_TESTWARE` is not `EXECUTION_READY`, execution PASS or `VERIFIED`.
- Delivery Manifest is not required VNext authority.

## Resume and derived projections

Resume Design and Case runs from their persisted run directories and revalidate every bound input. Do not depend on conversation history.

On explicit Human request, export `APPROVED_DESIGN` to XMind or `APPROVED_TESTWARE` to Excel. Each output is a one-way `DERIVED` projection and cannot change canonical artifacts or gate state.

## V1 compatibility

V1 artifacts remain readable through explicit `LEGACY_COMPAT` inspection. They have `vnext_authority=false` and cannot approve a VNext Design or Case run. Do not write `STOP_V1` for a new VNext run.
