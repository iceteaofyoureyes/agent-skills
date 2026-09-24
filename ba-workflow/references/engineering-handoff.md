# Engineering handoff

`engineering-handoff.yml` is the last BA-owned boundary. Create it only after the BA baseline has an explicit approval for engineering. Include immutable revision/provenance and SHA-256 values for the approved Business Rules, canonical SRS and BA decisions. Keep blocking and non-blocking open items separate.

The handoff may authorize downstream technical design, but it must not specify implementation repository/module ownership, service ownership, API/event shapes, database design, locking, or transaction strategy. Do not add frontend/backend owner fields.

Required fields and policy are in `templates/engineering-handoff.yml`. The current validator requires `open_items.blocking` to be an empty inline list and `open_items.non_blocking` to be an inline YAML list; use the inline form shown by the template. It checks required fields and SHA-256 syntax, and when given a file verifies that each relative authoritative-source path exists and matches its recorded digest. A handoff with unresolved blocking items or without `APPROVED_FOR_ENGINEERING` must not be presented as ready.
