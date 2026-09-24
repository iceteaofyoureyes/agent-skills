# Evidence model

Keep the source and status of each material statement visible in working artifacts.

| Label | Meaning | Permitted use |
|---|---|---|
| `CONFIRMED` | Directly stated or decided by the authorized BA/stakeholder | May become a target requirement, subject to the applicable approval gate |
| `CURRENT_SYSTEM` | Verified behavior in the existing system | Describes current behavior only |
| `INFERRED` | A conclusion drawn from evidence but not directly confirmed | Must remain visibly inferred and cannot silently become a requirement |
| `PROPOSED` | A suggested behavior or option | Remains a proposal until the BA confirms it |
| `UNKNOWN` | Evidence is missing, conflicting, or not yet checked | Preserve as open; ask only when material to the next safe step |

For each material rule or decision, retain a source reference and stable ID when the source has one. Do not promote a screenshot, prototype, current implementation, or generated DOCX over approved semantic sources. If evidence conflicts, record both sources and stop only the affected semantic change.
