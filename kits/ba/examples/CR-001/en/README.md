# CR-001: Appointment Scheduling

Tiếng Việt: [Ví dụ CR-001](../README.md)

**Documentation-only example.** The initial requirement is intentionally incomplete. Later files show illustrative review outputs and scenario decisions; they are not byte-for-byte expected responses or runtime-generated artifacts.

> Do not feed approved outputs from this folder into fresh-session acceptance. Give the fresh-session agent only the allowed initial input and ask it to discover gaps itself.

| File | Example status | Purpose |
|---|---|---|
| [01-input-requirement.md](01-input-requirement.md) | INPUT | Deliberately incomplete starting requirement. |
| [02-gap-review.md](02-gap-review.md) | ILLUSTRATIVE OUTPUT | Questions and a separate illustrative Human decision record. |
| [03-approved-business-rules.md](03-approved-business-rules.md) | ILLUSTRATIVE OUTPUT | Traceable example Business Rules; unresolved values stay UNKNOWN. |
| [04-srs-excerpt.md](04-srs-excerpt.md) | ILLUSTRATIVE OUTPUT | Example functional requirements and technical-scope boundary. |
| [05-engineering-handoff.yml](05-engineering-handoff.yml) | CONTRACT-VALID EXAMPLE (illustrative) | Uses the current handoff schema. Its hashes bind to the adjacent example source files. |

The decisions shown after the gap review are provided as scenario material for this example. They are not implied by the initial requirement. Sample rule/requirement IDs and prose are illustrative; follow the actual contracts, source authority, and Human Gate.

The handoff's hashes are actual SHA-256 values for the example files beside it. If you copy the handoff shape for a project, replace every source path, revision, and hash with that project's approved artifacts. The sample handoff does not prove that a real CR-001 runtime acceptance passed.

The contract-valid handoff also illustrates a Human classifying the unresolved duration maximum and list options as non-blocking for this handoff. Those values remain UNKNOWN, and downstream must not decide them. A real BA must make that classification; if either item blocks the work, do not issue the handoff.

See the [BA Kit workflow](../../../../../docs/en/BA_KIT_WORKFLOW.md), [usage guide](../../../../../docs/en/BA_KIT_USAGE_GUIDE.md), and [release status](../../../../../docs/en/RELEASE.md).
