# Test Kit V1 third-party materials

- TEA skill: MIT, BMad Code, LLC, 2025. Source commit and file hashes are in `tea-test-design-v1-provenance.md` and `tooling/pins/tea-test-design-v1.json`.
- Katalon `create-test-cases` skill: MIT, Katalon, Inc., 2026. Source commit and file hashes are in `tooling/pins/katalon-create-test-cases-v1.json`.
- XMind JavaScript SDK: optional `xmind@2.2.33`, MIT. npm integrity is pinned in `tooling/pins/xmind-sdk-v1.json` and `tooling/xmind/package-lock.json`; `npm ci` materializes its license file.
- Excel projection: optional `openpyxl==3.1.5` and `et-xmlfile==2.0.0`, both MIT, pinned with wheel hashes in `tooling/requirements-excel.lock`.
- Test Kit runtime code: repository license is included as `agent-skills.LICENSE`.

No upstream skill or package files are downloaded during ordinary Test Kit execution or installation.
