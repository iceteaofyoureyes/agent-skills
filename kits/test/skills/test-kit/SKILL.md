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

1. Choose a fresh internal run directory under `.test-kit/runs/<feature-id>/design-<run-id>/`. This directory is harness evidence, not canonical project documentation; do not ask the Human to choose it.
2. Add `.agents/skills/.test-kit` to Python import path and run the installed runtime's `prepare-design` command with:
   - approved engineering handoff;
   - run directory;
   - project root;
   - project-local `.agents/skills/bmad-testarch-test-design`.
3. `prepare-design` is the authority/integrity boundary. It verifies the BA baseline, pinned TEA skill, project config/policy, freezes adapter inputs, and writes `same-session-instructions.md`.
4. Read the prepared instructions and the installed `bmad-testarch-test-design/SKILL.md`. Execute the TEA workflow **directly in this current session** using the prepared adapter inputs.
5. Do **not** invoke `codex`, `codexapi`, another agent process, nested model session, or the legacy `invoke_native_tea` path.
6. In same-session mode, Test Kit has already resolved project policy and created a run-local TEA runtime config. Use that prepared config as the effective config source for this run. Never edit `_bmad/tea/config.yaml` to point at a CR/run directory.
7. Write TEA's raw completed Test Design exactly to the path prepared by Test Kit.
8. Run `finalize-design`. It must normalize, validate, create the Canonical Test Design, and transition only to `DESIGN_REVIEW`.
9. Present the canonical Design to the Human and stop. Do not create testcases until an explicit valid Human Design Gate decision has been persisted.

If `prepare-design`, TEA execution, normalization, or validation fails, report the exact blocker and stop. A failed run is evidence, not permission to improvise another execution architecture.

## Human Design Gate

- `REVIEW` is read-only.
- `REQUEST_CHANGES` applies only to the exact Design snapshot/revision named by the Human.
- `APPROVE` is valid only for the exact current `DESIGN_REVIEW` artifact and must be persisted through Test Kit's gate logic.
- Never infer approval from `OK`, `continue`, validator `PASS`, or a generated artifact.

### Persistence recovery

Human decisions are immutable transactions. Validate all transition destinations before consumption.
On an internal persistence failure, retain the exact receipt and transaction evidence; the host may
resume the same authenticated receipt through the public gate API without another Human decision.
An exact completed replay validates outputs and returns idempotent success; different receipt bytes
or conflicting immutable artifacts fail closed. Never delete receipts, overwrite evidence, edit
workflow state, or apply candidate recovery to a frozen historical Golden run.

Runtime path preflight reports `WINDOWS_PATH_BUDGET_EXCEEDED` before consuming a receipt on default
Windows. New internal projections use compact names; existing legacy evidence is read in place.

## Testcase route — same session only

After the exact Canonical Test Design is `APPROVED_DESIGN`:

1. Run the installed testcase runtime's `prepare-cases` command with the approved BA handoff, approved Design run, a fresh internal run directory under `.test-kit/runs/<feature-id>/cases-<run-id>/`, project root, and project-local `create-test-cases` skill.
2. `prepare-cases` validates the persisted Human Design Gate receipt, current BA hashes, pinned Katalon skill, and project policy; it writes the approved testcase input and same-session instructions.
3. Read those prepared instructions and the installed `create-test-cases/SKILL.md`. Execute that capability **inside this current agent session**.
4. Do not invoke `codex`, `codexapi`, another agent process, nested model session, or the legacy native Katalon invocation path.
5. Preserve exact BA refs and exact approved Test Design IDs. Do not expand coverage beyond the approved Design.
6. Write the raw completed testcase Markdown exactly to the path prepared by Test Kit, then run `finalize-cases`.
7. `finalize-cases` normalizes and validates the testcase output and transitions only to `CASE_REVIEW`.
8. Present the exact Canonical Testcases and stop for the Human Case Gate.
9. Only an explicit valid Human `APPROVE` for that exact snapshot may produce `APPROVED_TESTWARE` and `STOP_V1`.

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

Do not ask the Human to manage Python modules, run directories, TEA/Katalon CLI flags, nested agent launchers, adapter shims, internal manifests, or project config retargeting. `_bmad/tea/config.yaml` is stable project configuration; per-run paths live only under `.test-kit/runs/`.

## Optional projections

Run XMind or Excel only after explicit Human request. Projection never changes canonical semantics or gate state.

## V1 boundary

V1 stops at `APPROVED_TESTWARE` / `STOP_V1`. Automated execution, flaky management, triage, and defect automation belong to Automation Test V2.


## Suite routing
Đọc workspace/docs AGENTS. UI feature bắt đầu từ features/<feature>/delivery-manifest.yml đã qua Human gates. Validate shared Delivery Manifest, dùng handoff được resolve; prepare-design với --delivery internal. Không yêu cầu Human nhập runtime path/hash. Chỉ same-session production, nested invocation là legacy benchmark.
Case run phải inherit Design delivery snapshot; BA/UX/delivery drift phải reject trước gate. SEMANTIC_ORACLE OPEN required chặn approval; typed execution needs chỉ chặn execution readiness. Sau gate gọi testware_promotion.promote để lưu exact snapshots/receipt ở features/<feature>/test/. STOP_V1 không tự chạy execution; project execution_contract router sở hữu readiness/finding/defect/retest. Tester sở hữu VERIFIED.
