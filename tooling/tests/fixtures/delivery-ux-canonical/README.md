# Canonical Golden receipt structure, synthetic contents

Modeled on `GR-DWC-DEMO-001-20261002-01`, `features/CR-DWC-DEMO-001/ux/approval-receipt.json`, read from the Golden docs without mutation. The production field names, decision metadata, immutable revision, declared aggregate method, two-path sources map, prototype authority, and provenance structure are retained. Feature, revision, commit, branch, semantic text, and hashes here are synthetic; this is not a real Human approval receipt.

The aggregate hashes UTF-8 `json.dumps(sources, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`. `.gitattributes` pins these fixture bytes to LF on all platforms. Tests copy them into temporary feature directories and use fresh installed BA/Dev/Test validators; they never access or edit Golden evidence.
