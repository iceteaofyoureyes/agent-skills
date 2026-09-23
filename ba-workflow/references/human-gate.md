# Human Gate contract

Ask the BA when unresolved information could change a business rule, lifecycle, actor or permission, required data, validation, conflict outcome, destructive behavior, semantic source, diagram meaning, or the target artifact. Group related high-value questions, show the evidence, and stop downstream semantic mutation while a blocking answer is pending.

## Decisions

| Human input | Meaning | Effect |
|---|---|---|
| `CONTINUE` | Resume from persisted state | Does not answer a question or approve an artifact |
| `ANSWER` | Answer a named open question | Records that answer; closes only the satisfied question gate |
| `APPROVE` | Approve the named artifact/gate | Records explicit approval for that target |
| `REJECT` | Reject the named artifact/gate | Records rejection; do not proceed past the gate |
| `REQUEST_CHANGES` | Ask for changes to the named artifact | Route back to the relevant edit stage |

An explicit answer to all blocking questions can satisfy a question-resolution gate without a second generic approval. An artifact approval gate requires an explicit approval of that artifact. Agent validation is evidence for the Human, never a substitute for the decision.
