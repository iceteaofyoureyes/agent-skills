# Engineering handoff

New writes use **Engineering Handoff schema_version 2** via `ba_vnext.make_handoff`. It consumes only APPROVED_BASELINE with exact authenticated proof. See [VNext contracts](baseline-vnext.md) and `templates/engineering-handoff-vnext.json`.

Bind feature id/title, baseline id/revision/semantic SHA and manifest ref, exact receipt ref, Decisions/BR/SRS refs, Shared Foundation Knowledge Impact, optional Foundation and explicit open items. Blocking items must be empty. Policy permits downstream technical design and prohibits changing business semantics; next capability remains engineering-impact-analysis (Engineering Impact / Dev workflow).

`validate_handoff` revalidates candidate, all exact source bytes, receipt and trusted-host Human authentication on every read. APPROVED_FOR_ENGINEERING or APPROVED_BASELINE text alone never proves approval. Candidate/source/Foundation/receipt drift invalidates handoff. Hashes prove integrity, not Human identity.

The handoff may authorize downstream technical design, but it must not specify implementation repository/module ownership, service ownership, API/event shapes, database design, locking, or transaction strategy. Do not add frontend/backend owner fields.

Unknown fields fail closed recursively. Knowledge Impact routes product/domain to BA and architecture/testing to downstream owners without specifying a technical solution. UX and derived delivery remain separate gates.

Refs are portable and relative to the feature root. Place the handoff at that root or invoke host APIs with the exact root. Trusted hosts call `ba_contracts.read_handoff(path, human_actor_authenticator=..., foundation_authenticator=...)`. CLI fails closed for VNext approval without a trusted authenticator; there is no approval flag.

## V1 compatibility

Schema_version 1 `engineering-handoff.yml`, its template and old Shared Core reader remain available. The BA adapter validates legacy sources and reports LEGACY_COMPAT, vnext_approval=False, insufficient evidence for new approval. Existing status text is not converted to a receipt. Historical contracts.py, approved_baseline.py and delivery_manifest.py imports retain their Shared Core identity. Delivery Manifest V2, UX receipt V2 and Dev/Test workflows are unchanged.
