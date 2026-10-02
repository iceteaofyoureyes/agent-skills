---
name: test-kit
description: >-
  Route approved BA baselines through Human-gated Test Design and manual
  testcase creation. Use the current agent session; never spawn a nested agent
  for TEA or Katalon.
---

# Test Kit V1 Workflow

You own routing, authority checks, canonicalization, and Human Gate safety. The installed TEA and Katalon skills own testing analysis and testcase drafting. Execute those capabilities **inside the current agent session**, the same way BA Workflow routes atomic skills.

## Start every request

1. Read project `AGENTS.md` and the feature's approved `engineering-handoff.yml`.
2. Classify the request as `CREATE`, `CONTINUE`, `REVIEW`, or a Human Gate decision.
3. Locate existing Test Kit run state when continuing. Never create a new run when an active run already owns the requested gate.
4. Verify the approved BA handoff and source hashes before semantic work.
5. Use project-owned `_bmad/tea/config.yaml` and optional `.test-kit/project.yaml` only as project configuration/guidance. Neither can override BA authority.
6. Stop immediately on a real preflight/runtime/validator failure. Do not create compatibility shims, patch installed skills, or silently bypass validation.
7. `ANSWER != APPROVE`, `CONTINUE != APPROVE`, `PASS != APPROVE`, artifact generation `!= APPROVE`.

## Design route — same session only

For a new Test Design:

1. Choose a fresh project-owned run directory under the project's test artifact area. Do not ask the Human to choose a run directory unless project rules make the destination ambiguous.
2. Add `.agents/skills/.test-kit` to Python import path and run the installed runtime's `prepare-design` command with:
   - approved engineering handoff;
   - run directory;
   - project root;
   - project-local `.agents/skills/bmad-testarch-test-design`.
3. `prepare-design` is the authority/integrity boundary. It verifies the BA baseline, pinned TEA skill, project config/policy, freezes adapter inputs, and writes `same-session-instructions.md`.
4. Read the prepared instructions and the installed `bmad-testarch-test-design/SKILL.md`. Execute the TEA workflow **directly in this current session** using the prepared adapter inputs.
5. Do **not** invoke `codex`, `codexapi`, another agent process, nested model session, or the legacy `invoke_native_tea` path.
6. In same-session mode, Test Kit has already resolved project policy. Do not retry missing customization resolvers through `uv` or shell wrappers. Use the prepared policy context and the installed skill files directly.
7. Write TEA's raw completed Test Design exactly to the path prepared by Test Kit.
8. Run `finalize-design`. It must normalize, validate, create the Canonical Test Design, and transition only to `DESIGN_REVIEW`.
9. Present the canonical Design to the Human and stop. Do not create testcases until an explicit valid Human Design Gate decision has been persisted.

If `prepare-design`, TEA execution, normalization, or validation fails, report the exact blocker and stop. A failed run is evidence, not permission to improvise another execution architecture.

## Human Design Gate

- `REVIEW` is read-only.
- `REQUEST_CHANGES` applies only to the exact Design snapshot/revision named by the Human.
- `APPROVE` is valid only for the exact current `DESIGN_REVIEW` artifact and must be persisted through Test Kit's gate logic.
- Never infer approval from `OK`, `continue`, validator `PASS`, or a generated artifact.

## Testcase route — same session only

After the exact Canonical Test Design is `APPROVED_DESIGN`:

1. Validate the persisted Human Design Gate receipt against the current Design and BA baseline.
2. Use `tooling.lib.test_kit_v1_cases` to adapt the approved Design into the pinned `create-test-cases` input.
3. Execute the installed `create-test-cases` capability **inside this current agent session**. Do not spawn Codex or another agent process.
4. Preserve exact BA refs and exact approved Test Design IDs. Do not expand coverage beyond the approved Design.
5. Normalize and validate the raw testcase output through Test Kit runtime.
6. Transition only to `CASE_REVIEW`, present the exact Canonical Testcases, then stop for the Human Case Gate.
7. Only an explicit valid Human `APPROVE` for that exact snapshot may produce `APPROVED_TESTWARE` and `STOP_V1`.

Until the testcase runtime exposes the same `prepare/finalize` convenience commands as Design, call its existing library functions in-process from the current session. **Never use its nested Codex invocation functions for production operator flow.**

## Authority model

- Approved BA baseline = business behavior authority.
- Approved Canonical Test Design = coverage authority.
- Approved execution contracts = execution-detail authority.
- TEA/Katalon analysis is advisory input to adapters; it is never canonical authority by itself.
- Project testing policy is non-authoritative guidance.
- Source code/current behavior may provide `CURRENT_SYSTEM` evidence but cannot settle missing target behavior.

Preserve `UNKNOWN` and unresolved BA decisions. Do not invent expected behavior to make testware complete.

## Operator UX

The Human-facing interface should look like BA Kit. Typical requests are enough:

`Tạo Test Design cho CR-...`

`REVIEW Test Design hiện tại.`

`APPROVE.`

`Tiếp tục tạo testcases.`

Do not ask the Human to manage Python modules, run directories, TEA/Katalon CLI flags, nested agent launchers, adapter shims, or internal manifests.

## Optional projections

Run XMind or Excel only after explicit Human request. Projection never changes canonical semantics or gate state.

## V1 boundary

V1 stops at `APPROVED_TESTWARE` / `STOP_V1`. Automated execution, flaky management, triage, and defect automation belong to Automation Test V2.
