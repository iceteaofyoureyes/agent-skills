# Human Gate contract

Ask the BA when unresolved information could change a business rule, lifecycle, actor or permission, required data, validation, conflict outcome, destructive behavior, semantic source, diagram meaning, or the target artifact. Group related high-value questions, show the evidence, and stop downstream semantic mutation while a blocking answer is pending.

## Decisions

| Human input | Meaning | Effect |
|---|---|---|
| `CONTINUE` | Resume from persisted state | Does not answer a question or approve an artifact |
| `ANSWER` | Answer a named open question | Records that answer; closes only the satisfied question gate |
| `APPROVE` | Approve the named exact artifact/gate/revision | Requires the external authenticated receipt for that target |
| `REJECT` | Reject the named artifact/gate | Records rejection; do not proceed past the gate |
| `REQUEST_CHANGES` | Ask for changes to the named artifact | Route back to the relevant edit stage |

An explicit answer to all blocking questions can satisfy a question-resolution gate without a second generic approval. An artifact approval gate requires an explicit approval of that artifact. Agent validation is evidence for the Human, never a substitute for the decision.

## Exact BA Baseline Gate VNext

Only HUMAN_REVIEW → APPROVED_BASELINE accepts APPROVE. The host supplies schema_version 1 BA_BASELINE receipt: Human actor id/role, UTC timestamp, feature id, baseline id/revision/semantic SHA-256, exact manifest ref and decision evidence ref. Revision receipts bind the previous baseline identity when the candidate names a prior manifest. See [VNext contracts](baseline-vnext.md).

The trusted host authenticator must return exactly True for the actor and full receipt. Hashes prove integrity, never Human identity. There is no CLI self-approval flag or fallback authenticator. Source/receipt drift fails closed. ANSWER, CONTINUE, validator PASS, generation, Foundation READY and UX approval never replace this gate.

`record_answer` records supplied, host-authenticated named Human answers and explicit supersession. It never advances baseline approval. New confirmed decisions must bind updated BR/SRS revisions before readiness succeeds. The Agent cannot fabricate Human identity/authentication.

`resolve_question` closes only the named pending topic from an exact authenticated decision artifact, records ANSWER and returns to DRAFT without approval. Persisted ANSWER transitions recheck this binding. Old candidates cannot ignore the latest Human decision; candidate selection requires the updated decision authority.
