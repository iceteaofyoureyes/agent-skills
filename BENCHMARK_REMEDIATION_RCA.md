# Benchmark V1 Remediation — Root-Cause Analysis

This report was completed before implementation changes. The evidence is from Practical Paired Benchmark V1 and synthetic reproductions; no benchmark task or oracle was edited or rerun.

## S1 Candidate — TRIVIAL completion leaves run active

- **Failure point:** `finish-trivial` after the application edit and deterministic `git diff --check`.
- **Exact input:** `change_id=S1-COPY`, `kind=mechanical`, `summary=copy`, `baseline_snapshot=null`, and one check `{name: diff-check, category: static_checks, argv: [git, diff, --check]}`. The final command was `devkit finish-trivial`.
- **Expected:** Fresh verification is recorded and the TRIVIAL lifecycle becomes `COMPLETED` on PASS (or `NEEDS_REPLAN` on failure).
- **Actual:** `TypeError: 'NoneType' object is not iterable`; the lifecycle remained `RUNNING`, and a second start was rejected because that run was still active.
- **Root cause:** `start_run` explicitly permits a TRIVIAL run without a baseline and stores `baseline_snapshot=null`. In `run_checks`, the expression passed as `protected_baselines` evaluates to `None` for that valid case. `write_artifact` iterates the argument unconditionally. `finish_trivial` therefore fails while writing its verification artifact, before the terminal lifecycle state is saved. Reproduced before code changes with a temporary TRIVIAL run and a passing Python no-op check; output was `finish_exception=TypeError: 'NoneType' object is not iterable`, `lifecycle=RUNNING`.
- **Classification:** `DEV_KIT_RUNTIME`.
- **Minimal fix:** Normalize absent protected baseline references to an empty iterable. Preserve the existing direct TRIVIAL path and add a regression that starts without a baseline, passes its deterministic check, and reaches `COMPLETED`.
- **Additional observed process gap:** The recorded source edit preceded the first successful start. The canonical agent instructions must say to start before editing and to run `finish-trivial` before reporting completion. This is not the runtime exception's cause.
- **Raw evidence:** `evidence/S1/candidate/attempt1/workflow-result.json`, `worker-final.md`, and `devkit-state.zip` (`.devkit/runs/S1-COPY/input.json`, `lifecycle.json`).

## S3 Candidate — NORMAL run stops before workflow readiness

- **Failure point:** Immediately after the successful `start` result; no Spec Readiness artifact or subsequent workflow command was produced.
- **Exact input:** `change_id=S3-OWNER-ENCODING`, `kind=bug`, summary `S3_owner_search_encoding`, approved handoff `input/ba/engineering-handoff.yml`, with `build` and `tests` checks. The successful command invoked `dev_kit.py start` after several failed PowerShell quoting attempts.
- **Expected:** Continue from `READY_FOR_PLANNING` through Spec Readiness, `preflight` (readiness plus Impact Manifest enforcement), plan/tasks, `plan-check`, and `implementation-ready` before editing application code.
- **Actual:** The CLI created `.devkit/runs/S3-OWNER-ENCODING` and returned `route.risk_level=NORMAL`, `route.status=READY_FOR_PLANNING`, and `planning_allowed=true`. The worker's final response explicitly said it did not implement, verify, or complete the lifecycle. No `preflight`, `plan-check`, or `implementation-ready` command followed the successful start; no implementation occurred.
- **Root cause:** The NORMAL runtime did not reject or fail this run. The worker stopped at the entry command after spending multiple turns trying to construct shell-escaped JSON. The documented flow describes later stages, but the agent-facing entry instruction did not enforce a single start-and-continue sequence. The quoting friction is a contributing CLI usability issue; it is distinct from the actual stopping point.
- **Classification:** `AGENT_INSTRUCTION`.
- **Minimal fix:** Provide one request-file entry path and concise mandatory continuation instructions. Add an integration regression that exercises the observed stop boundary: successful NORMAL start followed by readiness, impact/preflight, plan/task validation, and implementation boundary checks.
- **Raw evidence:** `evidence/S3/candidate/attempt3/worker-commands.json` (successful start is item 13; no later lifecycle command), `worker-messages.json`, `worker-final.md`, and `oracle-evaluation.json`.

## S4 Candidate — HIGH_RISK public API request rejected before run creation

- **Failure point:** `start` argument parsing while passing two structured checks from PowerShell.
- **Exact input:** HIGH_RISK feature request with `signal=public_api`, approved handoff, and separate Maven build/tests objects passed through repeated `--check '{...}'` shell arguments. Captured parser output: `ERROR: Expecting property name enclosed in double quotes: line 1 column 3 (char 2)`. A subsequent PowerShell hashtable attempt failed earlier with `The term '=' is not recognized`.
- **Expected:** Persist a HIGH_RISK run with `human_gate.required=true`, then continue readiness, impact, plan, plan-check, and stop at the Spec Kit Human Gate.
- **Actual:** No run ID, Impact Manifest, plan, tasks, or Human Gate existed; no implementation or checks ran.
- **Root cause:** The CLI accepted each `--check` as a JSON string and called `json.loads` after the shell had already altered quoting. The CLI provided no supported structured file input, so the error-prone data representation crossed nested PowerShell/Codex command boundaries.
- **Classification:** `DEV_KIT_CLI_UX`.
- **Minimal fix:** Add a standard-library `start --request <file>` contract with deterministic schema checks; keep the old flags for compatibility. Add a Windows invocation regression that uses a request file and proves the persisted route/gate fields.
- **Raw evidence:** `evidence/S4/candidate/attempt1/worker-commands.json`, `worker-final.md`, `run-record.json`, and `oracle-evaluation.json`.

## S5 Candidate — HIGH_RISK security/ownership request rejected before run creation

- **Failure point:** `start` argument parsing while passing structured Maven checks from PowerShell.
- **Exact input:** Feature request with `signal=public_api`, approved handoff, and Maven build/tests checks passed through `--check` JSON strings. Captured parser errors include `Expecting property name enclosed in double quotes: line 1 column 3 (char 2)` and column 2; attempts to construct values with PowerShell variables also failed before invoking the CLI.
- **Expected:** Persist the HIGH_RISK route and required Human Gate, then progress to that gate without approval.
- **Actual:** No run or workflow artifacts were created; implementation, tests, and Human Gate were not reached.
- **Root cause:** Same CLI input-boundary defect as S4: nested shell quoting corrupts JSON before `json.loads`; the start interface has no file-based structured request.
- **Classification:** `DEV_KIT_CLI_UX`.
- **Minimal fix:** Same file-based request contract as S4. Use this request shape as an independent regression fixture.
- **Raw evidence:** `evidence/S5/candidate/attempt1/worker-commands.json`, `worker-final.md`, and `oracle-evaluation.json`.

## S6 Candidate — cross-component HIGH_RISK request rejected before run creation

- **Failure point:** After an initial wrapper path error, `start` failed parsing the structured check arguments.
- **Exact input:** Feature request with `signals=public_api,cross_repo`, approved handoff, and Maven build/tests checks. The decisive attempts failed with `Expecting property name enclosed in double quotes` at columns 2–3; another attempt was parsed as a PowerShell expression and failed at `&` before reaching the CLI.
- **Expected:** Start a HIGH_RISK run covering REST and Angular, persist `human_gate.required=true`, and progress through readiness, impact, planning, and the real Human Gate. No S6 implementation is part of this remediation.
- **Actual:** No Dev Kit run or plan was persisted and no gate was reached.
- **Root cause:** The decisive failure is the same shell/JSON input boundary as S4/S5, not a separate cross-component routing defect. The initial relative wrapper path error was also present but did not explain the later JSON parse failures.
- **Classification:** `DEV_KIT_CLI_UX`.
- **Minimal fix:** Use the same file-based request path; regression must retain both signals and assert the HIGH_RISK gate in the persisted run.
- **Raw evidence:** `evidence/S6/candidate/attempt1/worker-commands.json`, `worker-final.md`, and `oracle-evaluation.json`.

## Worker `spawn EPERM` — CONTROL evidence and S1 Candidate

- **Failure point:** Angular test/build tooling launched from the Codex worker process; in S1/S3/S6 CONTROL, the supplied native check helper reached npm/Angular and esbuild failed to spawn with `spawn EPERM`.
- **Exact input:** For example, S1 CONTROL ran `python input/native_checks.py all spring-petclinic-angular --root .` and then the `build` phase. S6 CONTROL ran the same helper across REST and Angular. S3 CONTROL likewise recorded the helper's child startup failure.
- **Expected:** Angular's test/build child processes start and complete.
- **Actual:** The worker's Angular phase failed with `spawn EPERM`. The same source/evaluator checks passed in the separate evaluator process; S6 evaluator logs show successful Maven verification and Angular unit/build checks. Dev Kit's own start parser and workflow were not involved in these CONTROL runs. S1 Candidate's `finish-trivial` failed earlier during artifact writing, separately from its Angular tooling failure.
- **Root cause:** Evidence localizes the restriction to the worker/harness process context, not the command's working directory, the Dev Kit subprocess wrapper, or the application source. The precise host policy layer is not exposed in the artifacts, so this report does not claim whether it is Codex sandboxing or Windows process policy.
- **Classification:** `HOST_HARNESS`.
- **Minimal fix:** Record `EXTERNAL_HOST_LIMITATION`; keep Dev Kit independent of this environment and do not weaken its check semantics.
- **Raw evidence:** CONTROL `worker-commands.json` / `worker-checks.json` and `worker-final.md` for S1/S3/S6; corresponding evaluator-native logs and results; S1 Candidate `worker-final.md`.

## RCA conclusion

The remediation has three separate targets: fix the TRIVIAL verification artifact writer's null-baseline handling; add a file-based structured start request to remove shell JSON quoting from the supported agent path; and make the canonical workflow instructions explicitly continue after a successful start. S3's stop is not attributed to the same parser error as S4–S6. Angular `spawn EPERM` remains an external host limitation unless new evidence locates a Dev Kit contribution.
