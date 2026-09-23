# CR-001 acceptance probes

Use the benchmark repository's CR-001 input, decisions, approved Business Rules, canonical SRS and Stage 6C routing fixture as immutable evidence. These probes are acceptance expectations, not permission to change the benchmark.

| Probe | Expected behavior |
|---|---|
| Review the requirement | Inspect brownfield evidence, separate `CURRENT_SYSTEM` from `CONFIRMED`, and identify material gaps |
| Answer a blocking question | Record only the BA's answer, preserving its source and stable requirement/rule IDs |
| “Tiếp tục” with a pending gate | Resume/checkpoint; keep the gate pending and do not generate downstream semantic artifacts |
| Extract Business Rules | Keep confirmed rules distinct from current implementation; preserve `UNKNOWN`, `INFERRED`, and `PROPOSED` |
| Write SRS | Derive it from confirmed answers and Business Rules; preserve TBD and traceability |
| Request engineering handoff | Require explicit final BA approval; include revision and source hashes; omit technical ownership/design |

For independent routing, use a fresh session and provide only the installed BA Kit, the allowed CR-001 artifacts, and one probe prompt. Do not include expected routes. Record exact command, model/runtime version, inputs, output, and PASS/FAIL/INCONCLUSIVE. A prior Stage 6C run tested seven of fifteen cases in separate ephemeral sessions; it does not replace a fresh review of this packaged version.
