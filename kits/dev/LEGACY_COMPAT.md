# Dev Kit V1 compatibility surfaces

The following unsuffixed files are retained as V1 compatibility artifacts:

- `schemas/start-request.schema.json`
- `schemas/impact-manifest.schema.json`
- `schemas/dev-handoff.schema.json`
- `templates/start-request.template.json`
- `templates/impact-manifest.template.json`
- `templates/dev-handoff.template.json`
- The V1 reader/validator functions in `tooling/lib/dev_kit.py`

They are available only by explicit legacy inspection/discovery, are
`LEGACY_COMPAT`, and never supply VNext authority. New work uses the `*-v2`
schemas and templates. Do not create a V1 run from a new Dev Kit installation.
