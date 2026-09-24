# CR-001 acceptance feedback loop

Use three tiers. Tiers 1 and 2 are the normal remediation loop; only Tier 3 can establish `BA_KIT_RC1_PASS`.

## Tier 1: deterministic checks

Run the targeted package, workflow, validator, and semantic-evaluator tests after every relevant change:

```text
python -m unittest tooling.tests.test_ba_kit -v
python -m unittest tooling.tests.test_srs_function_document -v
```

The CR-001 evaluator consumes generated Business Rules and SRS files after generation. It reports each semantic ID as `MATCH`, `MISSING_REQUIRED_BEHAVIOR`, `UNSUPPORTED_INVENTION`, `CONTRADICTION`, or `UNKNOWN_PRESERVED`.

Evaluate the initial gap review separately with case `cr001-gap-review`; missing questions are a `MISSING_QUESTION` finding, while unavailable local source remains an environment/harness dependency.

## Tier 2: focused runtime probes

Run one bounded, fresh ephemeral Codex session per probe. Reuse only the working provider route and credential environment-variable reference. Do not reuse previous session state, memories, or CR-001 artifacts.

| Probe | Input fixture | Required result |
|---|---|---|
| Local discovery | `tooling/fixtures/ba_local_discovery/src/visit.py` | Read the local source directly, label observed facts `CURRENT_SYSTEM`, and leave target appointment rules `UNKNOWN`. |
| SRS preservation | `srs_preservation` in `cr001-semantic-contract.json` | Keep self-exclusion, exactly one new Visit, and maximum-duration `UNKNOWN`; select no technical design. |
| SRS invention guard | `srs_invention_guard` in `cr001-semantic-contract.json` | Add no Pet-context or standalone management flow, screen/navigation, API, schema, locking, transaction, or ownership design. |
| Business Rules completeness | `business_rules` in `cr001-semantic-contract.json` | Preserve six confirmed decisions, including required Description and 1–255 bounds, with exactly the six supplied rule IDs. |

The local fixture/source must be readable inside the project or through a read-only project directory. Inspect it with local filesystem tools. An optional automatic review service is secondary and must not block local discovery. If local source is genuinely inaccessible, classify that probe as an environment or harness block rather than a BA Kit failure.

Generate first; evaluate second. Do not provide benchmark answers, golden Business Rules, golden SRS, or prior runtime output to a generator. Run `tooling/lib/ba_semantic_evaluator.py` in the host/evaluator context only after the generated artifacts are closed.

## Tier 3: fresh-session release acceptance

Run the complete CR-001 workflow once for release acceptance, in a fresh semantic context. Stage the legitimate current-system source locally and read-only. Do not depend on `codex-auto-review`. Keep the generator isolated from golden answers; compare artifacts only after generation.

Tier 1 or Tier 2 passing is remediation evidence only. Neither tier may declare BA Kit RC1 accepted.
